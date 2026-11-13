"""Campaign runner: Predict → operator gate → Experiment → Update."""

from __future__ import annotations

from typing import Callable, Optional, Protocol

from sdl.data.store import CampaignStore
from sdl.models import ActionKind, CampaignState, ExperimentProposal


class OperatorGate(Protocol):
    def confirm(self, proposal: ExperimentProposal) -> bool:
        """Return True to proceed, False to abort campaign."""
        ...


class AutoAckGate:
    """Dry-run / fixture gate that always acknowledges operator steps."""

    def confirm(self, proposal: ExperimentProposal) -> bool:
        return True


class StdinOperatorGate:
    """Prompt a human operator on stdin."""

    def confirm(self, proposal: ExperimentProposal) -> bool:
        print()
        print(f"[{proposal.action.value}] {proposal.message}")
        if proposal.reason:
            print(f"  reason: {proposal.reason}")
        if not proposal.requires_operator:
            return True
        raw = input("Acknowledge and continue? [Y/n/q] ").strip().lower()
        if raw in {"q", "quit", "abort"}:
            return False
        return raw in {"", "y", "yes"}


class CampaignRunner:
    def __init__(
        self,
        sop: object,
        store: CampaignStore,
        gate: OperatorGate,
        *,
        on_event: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self.sop = sop
        self.store = store
        self.gate = gate
        self.on_event = on_event

    def run(self, state: CampaignState) -> CampaignState:
        self.store.save_state(state)
        self._emit(state, "campaign_started", state.model_dump(mode="json"))

        while state.status == "running":
            proposal = self.sop.propose(state)
            state.last_proposal = proposal
            state.step += 1
            self.store.append_event(
                state.campaign_id,
                "proposal",
                proposal.model_dump(mode="json"),
            )
            self._emit(state, "proposal", proposal.model_dump(mode="json"))

            if proposal.action == ActionKind.STOP:
                state.status = "stopped"
                state.stop_reason = proposal.reason or proposal.message
                self.store.save_state(state)
                self.store.append_event(
                    state.campaign_id,
                    "stopped",
                    {"reason": state.stop_reason},
                )
                self._emit(state, "stopped", {"reason": state.stop_reason})
                break

            if proposal.requires_operator and not self.gate.confirm(proposal):
                state.status = "stopped"
                state.stop_reason = "operator_abort"
                self.store.save_state(state)
                self.store.append_event(
                    state.campaign_id,
                    "operator_abort",
                    proposal.model_dump(mode="json"),
                )
                break

            try:
                state = self.sop.execute(state, proposal)
            except Exception as exc:  # noqa: BLE001 - persist failure
                state.status = "failed"
                state.stop_reason = str(exc)
                self.store.append_event(
                    state.campaign_id,
                    "error",
                    {"error": str(exc)},
                )
                self.store.save_state(state)
                self._emit(state, "error", {"error": str(exc)})
                raise

            self.store.save_state(state)
            self.store.append_event(
                state.campaign_id,
                "state",
                {
                    "step": state.step,
                    "dilution_ratio": state.current_dilution_ratio,
                    "n_points": len(state.points),
                    "last_measurement": (
                        state.last_measurement.model_dump(mode="json")
                        if state.last_measurement
                        else None
                    ),
                },
            )

        return state

    def _emit(self, state: CampaignState, event: str, payload: dict) -> None:
        if self.on_event is not None:
            self.on_event(event, payload)
