"""Rule-based dilution / IFE policy (BayBE-ready DecisionEngine protocol)."""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from sdl.models import (
    ActionKind,
    CampaignState,
    ExperimentProposal,
    MeasurementResult,
    SurrogatePoint,
)


@runtime_checkable
class DecisionEngine(Protocol):
    def propose(
        self,
        state: CampaignState,
        measurement: Optional[MeasurementResult] = None,
    ) -> ExperimentProposal: ...


class ClipSNRDilutionPolicy:
    """
    Human-in-the-loop tonic dilution policy.

    Scout → if clipped/overload dilute 2×; if too weak concentrate 2×;
    else full Em scan. After accepted scans, stop when IFE roll-off is
    detected or the measurement budget is exhausted.
    """

    def __init__(
        self,
        *,
        weak_intensity: float = 5_000.0,
        min_snr: float = 10.0,
        dilute_factor: float = 2.0,
        min_dilution: float = 20.0,
        max_dilution: float = 1280.0,
        min_points: int = 3,
        max_steps: int = 12,
        ife_residual_frac: float = 0.25,
    ) -> None:
        self.weak_intensity = weak_intensity
        self.min_snr = min_snr
        self.dilute_factor = dilute_factor
        self.min_dilution = min_dilution
        self.max_dilution = max_dilution
        self.min_points = min_points
        self.max_steps = max_steps
        self.ife_residual_frac = ife_residual_frac

    def propose(
        self,
        state: CampaignState,
        measurement: Optional[MeasurementResult] = None,
    ) -> ExperimentProposal:
        if state.step >= self.max_steps:
            return ExperimentProposal(
                action=ActionKind.STOP,
                message="Measurement budget exhausted.",
                dilution_ratio=state.current_dilution_ratio,
                relative_concentration=state.relative_concentration(),
                reason="max_steps",
                requires_operator=False,
            )

        ife = self._detect_ife(state)
        if ife is not None:
            return ife

        if measurement is None:
            return ExperimentProposal(
                action=ActionKind.SCOUT,
                message=(
                    f"Load tonic dilution 1:{state.current_dilution_ratio:.0f}, "
                    "close compartment, then acknowledge for Single-Read scout."
                ),
                dilution_ratio=state.current_dilution_ratio,
                relative_concentration=state.relative_concentration(),
                reason="initial_scout",
                requires_operator=True,
            )

        if measurement.kind == "scout":
            return self._after_scout(state, measurement)

        if measurement.kind == "scan":
            return self._after_scan(state, measurement)

        return ExperimentProposal(
            action=ActionKind.STOP,
            message=f"Unhandled measurement kind {measurement.kind}.",
            reason="unhandled",
            requires_operator=False,
        )

    def _after_scout(
        self, state: CampaignState, measurement: MeasurementResult
    ) -> ExperimentProposal:
        intensity = measurement.peak_intensity
        if measurement.clipped or measurement.overload:
            new_ratio = min(state.current_dilution_ratio * self.dilute_factor, self.max_dilution)
            if new_ratio <= state.current_dilution_ratio + 1e-9:
                return ExperimentProposal(
                    action=ActionKind.STOP,
                    message="Still clipped at maximum dilution.",
                    dilution_ratio=state.current_dilution_ratio,
                    relative_concentration=state.relative_concentration(),
                    reason="clip_at_max_dilution",
                    requires_operator=False,
                )
            return ExperimentProposal(
                action=ActionKind.DILUTE,
                message=(
                    f"Signal clipped/overloaded. Dilute to 1:{new_ratio:.0f} "
                    "and reload the cuvette."
                ),
                dilution_ratio=new_ratio,
                relative_concentration=1.0 / new_ratio,
                reason="scout_clipped",
                requires_operator=True,
            )

        if intensity is None or intensity < self.weak_intensity:
            new_ratio = max(state.current_dilution_ratio / self.dilute_factor, self.min_dilution)
            if new_ratio >= state.current_dilution_ratio - 1e-9:
                return ExperimentProposal(
                    action=ActionKind.SCAN,
                    message=(
                        "Signal weak at minimum dilution; acquiring full Em scan anyway."
                    ),
                    dilution_ratio=state.current_dilution_ratio,
                    relative_concentration=state.relative_concentration(),
                    reason="weak_at_min_dilution",
                    requires_operator=True,
                )
            return ExperimentProposal(
                action=ActionKind.CONCENTRATE,
                message=(
                    f"Signal too weak (I={intensity}). Prepare stronger sample "
                    f"1:{new_ratio:.0f} and reload."
                ),
                dilution_ratio=new_ratio,
                relative_concentration=1.0 / new_ratio,
                reason="scout_weak",
                requires_operator=True,
            )

        return ExperimentProposal(
            action=ActionKind.SCAN,
            message=(
                f"Scout OK (I={intensity:.0f}). Keep 1:{state.current_dilution_ratio:.0f} "
                "loaded and acknowledge for full Em scan."
            ),
            dilution_ratio=state.current_dilution_ratio,
            relative_concentration=state.relative_concentration(),
            reason="scout_ok",
            requires_operator=True,
        )

    def _after_scan(
        self, state: CampaignState, measurement: MeasurementResult
    ) -> ExperimentProposal:
        if measurement.clipped or measurement.overload:
            new_ratio = min(state.current_dilution_ratio * self.dilute_factor, self.max_dilution)
            return ExperimentProposal(
                action=ActionKind.DILUTE,
                message=(
                    f"Scan clipped. Dilute to 1:{new_ratio:.0f} and reload for rescout."
                ),
                dilution_ratio=new_ratio,
                relative_concentration=1.0 / new_ratio,
                reason="scan_clipped",
                requires_operator=True,
            )

        if (
            measurement.snr is not None
            and measurement.snr < self.min_snr
            and (measurement.peak_intensity or 0) < self.weak_intensity
        ):
            new_ratio = max(state.current_dilution_ratio / self.dilute_factor, self.min_dilution)
            return ExperimentProposal(
                action=ActionKind.CONCENTRATE,
                message=(
                    f"Scan SNR too low ({measurement.snr:.1f}). "
                    f"Prepare 1:{new_ratio:.0f} and reload."
                ),
                dilution_ratio=new_ratio,
                relative_concentration=1.0 / new_ratio,
                reason="scan_weak_snr",
                requires_operator=True,
            )

        # Point will be accepted by SOP; propose next dilution step down the ladder.
        if len(state.points) + 1 >= self.min_points:
            # Peek IFE with hypothetical inclusion handled by SOP before next propose;
            # here suggest next lower concentration (higher dilution).
            pass

        new_ratio = min(state.current_dilution_ratio * self.dilute_factor, self.max_dilution)
        if new_ratio <= state.current_dilution_ratio + 1e-9:
            return ExperimentProposal(
                action=ActionKind.STOP,
                message="Reached maximum dilution after accepted scan.",
                dilution_ratio=state.current_dilution_ratio,
                relative_concentration=state.relative_concentration(),
                reason="ladder_complete",
                requires_operator=False,
            )

        return ExperimentProposal(
            action=ActionKind.DILUTE,
            message=(
                f"Accepted scan at 1:{state.current_dilution_ratio:.0f}. "
                f"Prepare next ladder step 1:{new_ratio:.0f} and reload."
            ),
            dilution_ratio=new_ratio,
            relative_concentration=1.0 / new_ratio,
            reason="next_ladder_step",
            requires_operator=True,
        )

    def _detect_ife(self, state: CampaignState) -> Optional[ExperimentProposal]:
        pts = [p for p in state.points if not p.clipped and p.peak_intensity > 0]
        if len(pts) < self.min_points:
            return None
        # Fit I ≈ a * c through origin using lowest-concentration half as linear refs.
        ordered = sorted(pts, key=lambda p: p.relative_concentration)
        n_ref = max(2, len(ordered) // 2)
        refs = ordered[:n_ref]
        num = sum(p.relative_concentration * p.peak_intensity for p in refs)
        den = sum(p.relative_concentration ** 2 for p in refs)
        if den <= 0:
            return None
        slope = num / den
        # Check highest-concentration point for roll-off vs linear prediction.
        hi = ordered[-1]
        predicted = slope * hi.relative_concentration
        if predicted <= 0:
            return None
        residual_frac = (predicted - hi.peak_intensity) / predicted
        if residual_frac >= self.ife_residual_frac:
            return ExperimentProposal(
                action=ActionKind.STOP,
                message=(
                    f"IFE onset detected: high-c point under-linear by "
                    f"{residual_frac:.0%} (need ≥{self.ife_residual_frac:.0%})."
                ),
                dilution_ratio=state.current_dilution_ratio,
                relative_concentration=state.relative_concentration(),
                reason="ife_onset",
                requires_operator=False,
            )
        return None

    @staticmethod
    def accept_point(state: CampaignState, measurement: MeasurementResult) -> SurrogatePoint:
        if measurement.relative_concentration is None or measurement.peak_intensity is None:
            raise ValueError("accepted scan missing concentration or intensity")
        if measurement.dilution_ratio is None:
            raise ValueError("accepted scan missing dilution_ratio")
        return SurrogatePoint(
            relative_concentration=float(measurement.relative_concentration),
            peak_intensity=float(measurement.peak_intensity),
            dilution_ratio=float(measurement.dilution_ratio),
            clipped=bool(measurement.clipped or measurement.overload),
            peak_nm=measurement.peak_nm,
            snr=measurement.snr,
        )
