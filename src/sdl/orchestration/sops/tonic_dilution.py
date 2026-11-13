"""Tonic-water dilution / IFE-onset SOP (Expt 1 closed loop)."""

from __future__ import annotations

from typing import Any, Optional

from sdl.decision.policy import ClipSNRDilutionPolicy, DecisionEngine
from sdl.integration.ls55_client import LS55Client
from sdl.models import ActionKind, CampaignState, ExperimentProposal


class TonicDilutionSOP:
    """
    Predict → Select → Experiment → Update loop for tonic dilution linearity / IFE.

    Instrument settings follow spectrometer-lab Expt 1 defaults:
    Ex 350 nm, Em 400–550 nm, 5 nm slits, guide ~447 nm.
    """

    def __init__(
        self,
        client: LS55Client,
        policy: Optional[DecisionEngine] = None,
        *,
        ex_nm: float = 350.0,
        em_lo: float = 400.0,
        em_hi: float = 550.0,
        guide_nm: float = 447.0,
        ex_slit: float = 5.0,
        em_slit: float = 5.0,
        scout_em_nm: float = 447.0,
        blank_csv: Optional[str] = None,
        auto_connect: bool = True,
    ) -> None:
        self.client = client
        self.policy = policy or ClipSNRDilutionPolicy()
        self.ex_nm = ex_nm
        self.em_lo = em_lo
        self.em_hi = em_hi
        self.guide_nm = guide_nm
        self.ex_slit = ex_slit
        self.em_slit = em_slit
        self.scout_em_nm = scout_em_nm
        self.blank_csv = blank_csv
        self.auto_connect = auto_connect
        self._connected = False

    def propose(self, state: CampaignState) -> ExperimentProposal:
        return self.policy.propose(state, state.last_measurement)

    def mark_connected(self) -> None:
        """Use when the caller already connected the client (e.g. HTTP + fixture_dir)."""
        self._connected = True

    def ensure_connected(self, state: CampaignState) -> None:
        if self._connected:
            return
        if not self.auto_connect:
            raise RuntimeError("instrument not connected and auto_connect=False")
        self.client.connect(gate_a_pass=True, compartment_closed=True)
        self.client.setup(
            ex_nm=self.ex_nm,
            em_nm=self.scout_em_nm,
            ex_slit=self.ex_slit,
            em_slit=self.em_slit,
        )
        self._connected = True
        state.meta["connected"] = True

    def execute(self, state: CampaignState, proposal: ExperimentProposal) -> CampaignState:
        self.ensure_connected(state)

        if proposal.action in {ActionKind.DILUTE, ActionKind.CONCENTRATE}:
            if proposal.dilution_ratio is None:
                raise ValueError("dilution proposal missing dilution_ratio")
            state.current_dilution_ratio = float(proposal.dilution_ratio)
            # Clear last measurement so next propose triggers a fresh scout.
            state.last_measurement = None
            state.last_proposal = proposal
            return state

        if proposal.action == ActionKind.REMEASURE:
            state.last_measurement = None
            return state

        if proposal.action == ActionKind.SCOUT:
            result = self.client.single_read(
                ex_nm=self.ex_nm,
                em_nm=self.scout_em_nm,
                dilution_ratio=state.current_dilution_ratio,
            )
            state.last_measurement = result
            return state

        if proposal.action == ActionKind.SCAN:
            result = self.client.scan(
                ex_nm=self.ex_nm,
                em_lo=self.em_lo,
                em_hi=self.em_hi,
                ex_slit=self.ex_slit,
                em_slit=self.em_slit,
                dilution_ratio=state.current_dilution_ratio,
                guide_nm=self.guide_nm,
                blank_csv=self.blank_csv or state.blank_ref,
                experiment="tonic-dilution",
                role="sample",
            )
            state.last_measurement = result
            if result.ok and not result.clipped and not result.overload:
                point = ClipSNRDilutionPolicy.accept_point(state, result)
                # Avoid duplicate concentration points.
                state.points = [
                    p
                    for p in state.points
                    if abs(p.relative_concentration - point.relative_concentration) > 1e-12
                ]
                state.points.append(point)
            return state

        if proposal.action == ActionKind.BLANK:
            result = self.client.scan(
                ex_nm=self.ex_nm,
                em_lo=self.em_lo,
                em_hi=self.em_hi,
                ex_slit=self.ex_slit,
                em_slit=self.em_slit,
                dilution_ratio=None,
                guide_nm=self.guide_nm,
                experiment="tonic-dilution-blank",
                role="blank",
            )
            state.last_measurement = result
            csv = (result.artifacts or {}).get("csv")
            if csv:
                state.blank_ref = str(csv)
            return state

        if proposal.action == ActionKind.ACCEPT:
            # No-op marker; points are accepted on successful SCAN.
            return state

        if proposal.action == ActionKind.CONNECT:
            self._connected = False
            self.ensure_connected(state)
            return state

        if proposal.action == ActionKind.STOP:
            return state

        raise ValueError(f"unsupported action: {proposal.action}")

    def shutdown(self) -> dict[str, Any]:
        try:
            return self.client.shutter_off()
        except Exception:
            return {"ok": False}
