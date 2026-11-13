"""Filesystem campaign store: events JSONL + state snapshot + catalog."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from sdl.models import CampaignState


class CampaignStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog_path = self.root / "catalog.json"
        if not self.catalog_path.is_file():
            self._write_json(self.catalog_path, {"campaigns": []})

    def campaign_dir(self, campaign_id: str) -> Path:
        path = self.root / campaign_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_state(self, state: CampaignState) -> Path:
        path = self.campaign_dir(state.campaign_id) / "state.json"
        self._write_json(path, state.model_dump(mode="json"))
        self._upsert_catalog(state)
        return path

    def load_state(self, campaign_id: str) -> CampaignState:
        path = self.campaign_dir(campaign_id) / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return CampaignState.model_validate(data)

    def append_event(self, campaign_id: str, event: str, payload: dict[str, Any]) -> Path:
        path = self.campaign_dir(campaign_id) / "events.jsonl"
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "payload": payload,
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        return path

    def read_events(self, campaign_id: str) -> list[dict[str, Any]]:
        path = self.campaign_dir(campaign_id) / "events.jsonl"
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
        return events

    def _upsert_catalog(self, state: CampaignState) -> None:
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        campaigns: list[dict[str, Any]] = list(catalog.get("campaigns") or [])
        entry = {
            "campaign_id": state.campaign_id,
            "status": state.status,
            "step": state.step,
            "n_points": len(state.points),
            "stop_reason": state.stop_reason,
            "path": str(self.campaign_dir(state.campaign_id)),
        }
        campaigns = [c for c in campaigns if c.get("campaign_id") != state.campaign_id]
        campaigns.append(entry)
        catalog["campaigns"] = campaigns
        self._write_json(self.catalog_path, catalog)

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def new_campaign_id(prefix: str = "tonic") -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}"


def default_runs_root(explicit: Optional[Path | str] = None) -> Path:
    if explicit is not None:
        return Path(explicit)
    return Path.cwd() / "runs"
