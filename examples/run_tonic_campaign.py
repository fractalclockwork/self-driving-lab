#!/usr/bin/env python3
"""Run a tonic dilution / IFE campaign (fixture or live LS 55 console)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running without install: repo_root/src on path.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdl.data.store import CampaignStore, new_campaign_id
from sdl.decision.policy import ClipSNRDilutionPolicy
from sdl.integration.ls55_client import FixtureLS55Client, LS55HttpClient
from sdl.models import CampaignState
from sdl.orchestration.runner import AutoAckGate, CampaignRunner, StdinOperatorGate
from sdl.orchestration.sops.tonic_dilution import TonicDilutionSOP


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("fixture", "http"),
        default="fixture",
        help="fixture = offline double; http = spectrometer-lab FastAPI",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8055")
    parser.add_argument(
        "--fixture-dir",
        default=None,
        help="Optional spectrometer-lab fixture dir when --mode http",
    )
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    parser.add_argument("--start-dilution", type=float, default=50.0)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument(
        "--auto-ack",
        action="store_true",
        help="Skip stdin prompts (implied for --mode fixture unless --interactive)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force stdin operator prompts even in fixture mode",
    )
    args = parser.parse_args(argv)

    if args.mode == "fixture":
        client = FixtureLS55Client()
    else:
        client = LS55HttpClient(args.base_url)
        # Connect up-front so fixture_dir / gates are applied once.
        client.connect(
            gate_a_pass=True,
            compartment_closed=True,
            fixture_dir=args.fixture_dir,
        )

    auto = args.auto_ack or (args.mode == "fixture" and not args.interactive)
    gate = AutoAckGate() if auto else StdinOperatorGate()
    store = CampaignStore(args.runs_dir)
    policy = ClipSNRDilutionPolicy(max_steps=args.max_steps)
    sop = TonicDilutionSOP(client, policy=policy, auto_connect=(args.mode == "fixture"))
    if args.mode == "http":
        sop.mark_connected()
        client.setup(ex_nm=350.0, em_nm=447.0, ex_slit=5.0, em_slit=5.0)

    campaign_id = new_campaign_id("tonic")
    state = CampaignState(
        campaign_id=campaign_id,
        current_dilution_ratio=args.start_dilution,
        guide_nm=447.0,
        meta={"mode": args.mode},
    )

    def on_event(event: str, payload: dict) -> None:
        if event == "proposal":
            action = payload.get("action")
            msg = payload.get("message", "")
            print(f"→ {action}: {msg}")
        elif event == "stopped":
            print(f"■ stopped: {payload.get('reason')}")
        elif event == "error":
            print(f"✗ error: {payload.get('error')}")

    runner = CampaignRunner(sop, store, gate, on_event=on_event)
    try:
        final = runner.run(state)
    finally:
        sop.shutdown()
        if hasattr(client, "close"):
            client.close()
        elif hasattr(client, "disconnect"):
            try:
                client.disconnect()
            except Exception:
                pass

    print()
    print(f"campaign: {final.campaign_id}")
    print(f"status:   {final.status} ({final.stop_reason})")
    print(f"points:   {len(final.points)}")
    for p in sorted(final.points, key=lambda x: x.relative_concentration):
        print(
            f"  1:{p.dilution_ratio:.0f}  c={p.relative_concentration:.4f}  "
            f"I={p.peak_intensity:.0f}  SNR={p.snr}"
        )
    print(f"store:    {store.campaign_dir(final.campaign_id)}")
    return 0 if final.status == "stopped" else 1


if __name__ == "__main__":
    raise SystemExit(main())
