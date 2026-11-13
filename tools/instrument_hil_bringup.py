#!/usr/bin/env python3
"""Stage-0 HIL bring-up: LS 55 RS-232 identity, Marlin M115, C310 one-shot capture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python tools/instrument_hil_bringup.py` without install.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdl.hil.bringup import run_hil_bringup  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--ls55-port",
        default=None,
        help="LS 55 Prolific serial path (default: by-id glob or LS55_PORT)",
    )
    p.add_argument(
        "--spectrometer-lab-root",
        type=Path,
        default=None,
        help="spectrometer-lab checkout (default: SPECTROMETER_LAB_ROOT or ~/src/spectrometer-lab)",
    )
    p.add_argument("--marlin-port", default=None, help="override Mega serial path")
    p.add_argument("--marlin-baud", type=int, default=250000, help="Marlin serial baud")
    p.add_argument("--video-device", default=None, help="override V4L device path")
    p.add_argument(
        "--camera-out",
        type=Path,
        default=None,
        help=(
            "Dev-Host path for one-shot capture "
            "(default: runs/hil_<utc>/c310.jpg; gateway /tmp is temporary only)"
        ),
    )
    p.add_argument(
        "--ssh-gateway",
        default=None,
        help="run LS 55 + Marlin + camera probes on gateway (e.g. pi@cede-pi.local)",
    )
    p.add_argument(
        "--skip",
        action="append",
        default=[],
        choices=("ls55", "marlin", "camera"),
        help="omit a check (repeatable)",
    )
    p.add_argument(
        "--fixture",
        action="store_true",
        help="no hardware; fake PASS for CI",
    )
    args = p.parse_args(argv)

    report = run_hil_bringup(
        ls55_port=args.ls55_port,
        spectrometer_lab_root=args.spectrometer_lab_root,
        marlin_port=args.marlin_port,
        video_device=args.video_device,
        camera_out=args.camera_out,
        ssh_gateway=args.ssh_gateway,
        skip=args.skip,
        fixture=args.fixture,
        marlin_baud=args.marlin_baud,
    )
    for line in report.summary_lines():
        print(line)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
