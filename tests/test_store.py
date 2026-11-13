"""CampaignStore round-trip tests."""

from __future__ import annotations

from pathlib import Path

from sdl.data.store import CampaignStore
from sdl.models import CampaignState, SurrogatePoint


def test_store_round_trip(tmp_path: Path):
    store = CampaignStore(tmp_path)
    state = CampaignState(
        campaign_id="tonic-test",
        current_dilution_ratio=100.0,
        points=[
            SurrogatePoint(
                relative_concentration=0.01,
                peak_intensity=1e5,
                dilution_ratio=100.0,
                snr=20.0,
            )
        ],
    )
    store.save_state(state)
    store.append_event("tonic-test", "proposal", {"action": "scout"})

    loaded = store.load_state("tonic-test")
    assert loaded.campaign_id == "tonic-test"
    assert loaded.current_dilution_ratio == 100.0
    assert len(loaded.points) == 1
    assert loaded.points[0].peak_intensity == 1e5

    events = store.read_events("tonic-test")
    assert len(events) == 1
    assert events[0]["event"] == "proposal"

    catalog = (tmp_path / "catalog.json").read_text(encoding="utf-8")
    assert "tonic-test" in catalog
