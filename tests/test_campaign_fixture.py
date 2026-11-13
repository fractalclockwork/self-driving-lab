"""End-to-end offline campaign against FixtureLS55Client."""

from __future__ import annotations

from pathlib import Path

from sdl.data.store import CampaignStore
from sdl.decision.policy import ClipSNRDilutionPolicy
from sdl.integration.ls55_client import FixtureLS55Client
from sdl.models import ActionKind, CampaignState, MeasurementResult
from sdl.orchestration.runner import AutoAckGate, CampaignRunner
from sdl.orchestration.sops.tonic_dilution import TonicDilutionSOP


def test_normalize_scout_clip_flag():
    client = FixtureLS55Client(clip_onset=1 / 40)
    client.connect()
    # 1:20 is above clip onset.
    result = client.single_read(ex_nm=350, em_nm=447, dilution_ratio=20.0)
    assert result.clipped is True
    assert result.overload is True
    assert result.kind == "scout"


def test_fixture_campaign_completes(tmp_path: Path):
    client = FixtureLS55Client()
    policy = ClipSNRDilutionPolicy(max_steps=20, min_points=3, ife_residual_frac=0.20)
    sop = TonicDilutionSOP(client, policy=policy)
    store = CampaignStore(tmp_path)
    runner = CampaignRunner(sop, store, AutoAckGate())

    state = CampaignState(
        campaign_id="fixture-tonic",
        current_dilution_ratio=50.0,
    )
    final = runner.run(state)

    assert final.status == "stopped"
    assert final.stop_reason in {"ife_onset", "ladder_complete", "max_steps"}
    assert len(final.points) >= 1
    assert (tmp_path / "fixture-tonic" / "state.json").is_file()
    assert (tmp_path / "fixture-tonic" / "events.jsonl").is_file()
    events = store.read_events("fixture-tonic")
    assert any(e["event"] == "proposal" for e in events)
    assert any(e["event"] == "stopped" for e in events)


def test_sop_scout_then_scan_accepts_point():
    client = FixtureLS55Client()
    sop = TonicDilutionSOP(client, policy=ClipSNRDilutionPolicy())
    state = CampaignState(campaign_id="unit", current_dilution_ratio=200.0)

    scout_prop = sop.propose(state)
    assert scout_prop.action == ActionKind.SCOUT
    state = sop.execute(state, scout_prop)
    assert state.last_measurement is not None
    assert state.last_measurement.kind == "scout"
    assert not state.last_measurement.clipped

    scan_prop = sop.propose(state)
    assert scan_prop.action == ActionKind.SCAN
    state = sop.execute(state, scan_prop)
    assert len(state.points) == 1
    assert state.points[0].dilution_ratio == 200.0


def test_policy_after_scan_dilutes():
    policy = ClipSNRDilutionPolicy()
    state = CampaignState(campaign_id="x", current_dilution_ratio=100.0)
    m = MeasurementResult(
        kind="scan",
        peak_nm=447.0,
        peak_intensity=80_000.0,
        snr=40.0,
        clipped=False,
        dilution_ratio=100.0,
        relative_concentration=0.01,
        ok=True,
    )
    prop = policy.propose(state, m)
    assert prop.action == ActionKind.DILUTE
    assert prop.dilution_ratio == 200.0
