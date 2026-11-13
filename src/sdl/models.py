"""Shared campaign / decision models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionKind(str, Enum):
    CONNECT = "connect"
    BLANK = "blank"
    SCOUT = "scout"
    SCAN = "scan"
    DILUTE = "dilute"
    CONCENTRATE = "concentrate"
    REMEASURE = "remeasure"
    ACCEPT = "accept"
    STOP = "stop"


class ExperimentProposal(BaseModel):
    """Next action proposed by the decision engine."""

    action: ActionKind
    message: str
    dilution_ratio: Optional[float] = Field(
        default=None,
        description="Parts total volume per part tonic (e.g. 450 means 1:450).",
    )
    relative_concentration: Optional[float] = Field(
        default=None,
        description="1 / dilution_ratio when dilution is set.",
    )
    optics: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    requires_operator: bool = True


class MeasurementResult(BaseModel):
    """Normalized metrology metrics (SOPs never parse raw serial)."""

    kind: str  # scout | scan | blank
    peak_nm: Optional[float] = None
    peak_intensity: Optional[float] = None
    snr: Optional[float] = None
    clipped: bool = False
    overload: bool = False
    dilution_ratio: Optional[float] = None
    relative_concentration: Optional[float] = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    ok: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SurrogatePoint(BaseModel):
    relative_concentration: float
    peak_intensity: float
    dilution_ratio: float
    clipped: bool = False
    peak_nm: Optional[float] = None
    snr: Optional[float] = None


class CampaignState(BaseModel):
    campaign_id: str
    status: str = "running"  # running | stopped | failed
    step: int = 0
    current_dilution_ratio: float = 50.0
    guide_nm: float = 447.0
    points: list[SurrogatePoint] = Field(default_factory=list)
    last_proposal: Optional[ExperimentProposal] = None
    last_measurement: Optional[MeasurementResult] = None
    stop_reason: Optional[str] = None
    blank_ref: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)

    def relative_concentration(self) -> float:
        return 1.0 / float(self.current_dilution_ratio)
