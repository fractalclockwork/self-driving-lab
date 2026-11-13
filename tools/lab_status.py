#!/usr/bin/env python3
"""Layered lab status snapshot (gateway / attach / IOP) as JSON or text lines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdl.hil.status import (  # noqa: E402
    DEFAULT_GANTRY_NOTE,
    DEFAULT_GATEWAY,
    collect_lab_status,
    format_status_lines,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--ssh-gateway",
        default=None,
        help=f"probe attach/IOP on gateway (e.g. {DEFAULT_GATEWAY})",
    )
    p.add_argument("--ls55-port", default=None, help="override LS 55 serial path")
    p.add_argument("--marlin-port", default=None, help="override Mega serial path")
    p.add_argument("--marlin-baud", type=int, default=250000, help="Marlin serial baud")
    p.add_argument("--video-device", default=None, help="override V4L device path")
    p.add_argument(
        "--spectrometer-lab-root",
        type=Path,
        default=None,
        help="spectrometer-lab checkout (default: SPECTROMETER_LAB_ROOT or ~/src/spectrometer-lab)",
    )
    p.add_argument(
        "--probe-camera-capture",
        action="store_true",
        help="also run a one-shot C310 capture (slow; off by default)",
    )
    p.add_argument(
        "--note",
        action="append",
        default=None,
        help=(
            "operator note (repeatable). No automatic gantry note; "
            f"pass --note {DEFAULT_GANTRY_NOTE!r} when mains are off"
        ),
    )
    p.add_argument(
        "--skip",
        action="append",
        default=[],
        choices=("ls55", "marlin", "camera"),
        help="omit an instrument (repeatable)",
    )
    p.add_argument(
        "--fixture",
        action="store_true",
        help="no hardware; synthetic ADAPTER / CTRL OK / ATTACH for CI",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="print JSON snapshot (default: text lines)",
    )
    args = p.parse_args(argv)

    status = collect_lab_status(
        ssh_gateway=args.ssh_gateway,
        ls55_port=args.ls55_port,
        marlin_port=args.marlin_port,
        video_device=args.video_device,
        spectrometer_lab_root=args.spectrometer_lab_root,
        marlin_baud=args.marlin_baud,
        probe_camera_capture=args.probe_camera_capture,
        notes=args.note,
        skip=args.skip,
        fixture=args.fixture,
    )
    if args.json:
        print(json.dumps(status.to_dict(), indent=2))
    else:
        for line in format_status_lines(status):
            print(line)
    return 0 if status.gateway.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
