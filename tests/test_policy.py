"""Unit tests for ClipSNRDilutionPolicy."""

from __future__ import annotations

from sdl.decision.policy import ClipSNRDilutionPolicy
from sdl.models import ActionKind, CampaignState, MeasurementResult, SurrogatePoint


def _state(**kwargs) -> CampaignState:
    base = dict(campaign_id="test", current_dilution_ratio=80.0)
    base.update(kwargs)
    return CampaignState(**base)


def test_initial_propose_is_scout():
    policy = ClipSNRDilutionPolicy()
    prop = policy.propose(_state(), None)
    assert prop.action == ActionKind.SCOUT


def test_scout_clipped_proposes_dilute():
    policy = ClipSNRDilutionPolicy()
    m = MeasurementResult(
        kind="scout",
        peak_intensity=900_000,
        clipped=True,
        overload=True,
        dilution_ratio=80.0,
        relative_concentration=1 / 80,
    )
    prop = policy.propose(_state(current_dilution_ratio=80.0), m)
    assert prop.action == ActionKind.DILUTE
    assert prop.dilution_ratio == 160.0


def test_scout_weak_proposes_concentrate():
    policy = ClipSNRDilutionPolicy(weak_intensity=5_000)
    m = MeasurementResult(
        kind="scout",
        peak_intensity=100.0,
        clipped=False,
        dilution_ratio=640.0,
        relative_concentration=1 / 640,
    )
    prop = policy.propose(_state(current_dilution_ratio=640.0), m)
    assert prop.action == ActionKind.CONCENTRATE
    assert prop.dilution_ratio == 320.0


def test_scout_ok_proposes_scan():
    policy = ClipSNRDilutionPolicy()
    m = MeasurementResult(
        kind="scout",
        peak_intensity=50_000.0,
        clipped=False,
        dilution_ratio=200.0,
        relative_concentration=1 / 200,
    )
    prop = policy.propose(_state(current_dilution_ratio=200.0), m)
    assert prop.action == ActionKind.SCAN


def test_ife_detection_stops():
    policy = ClipSNRDilutionPolicy(min_points=3, ife_residual_frac=0.25)
    # Linear at low c: I = 1e6 * c; high-c point rolls off.
    points = [
        SurrogatePoint(relative_concentration=0.0025, peak_intensity=2500, dilution_ratio=400),
        SurrogatePoint(relative_concentration=0.005, peak_intensity=5000, dilution_ratio=200),
        SurrogatePoint(relative_concentration=0.02, peak_intensity=8000, dilution_ratio=50),
    ]
    state = _state(points=points)
    prop = policy.propose(state, None)
    assert prop.action == ActionKind.STOP
    assert prop.reason == "ife_onset"


def test_max_steps_stops():
    policy = ClipSNRDilutionPolicy(max_steps=3)
    prop = policy.propose(_state(step=3), None)
    assert prop.action == ActionKind.STOP
    assert prop.reason == "max_steps"
