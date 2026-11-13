#!/usr/bin/env python3
"""Generate printable prep-area ChArUco calibration PDFs (Dev-Host only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdl.calibration.charuco_card import (  # noqa: E402
    PrepAreaCharucoCard,
    calibration_deps_available,
    default_geometry,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=_ROOT / "docs" / "calibration",
        help="directory for PDFs + prep_area_charuco.json (default: docs/calibration)",
    )
    args = p.parse_args(argv)

    if not calibration_deps_available():
        print(
            "missing calibration deps; install with: uv sync --extra calibration",
            file=sys.stderr,
        )
        return 1

    geom = default_geometry()
    card = PrepAreaCharucoCard(geom)
    manifest = card.generate(args.out_dir)
    print(f"wrote {args.out_dir / 'prep_area_charuco.json'}")
    print(f"  card_id={manifest['card_id']}")
    print(f"  board={manifest['board_width_mm']}x{manifest['board_height_mm']} mm")
    print(f"  sha256={manifest['board_png_sha256'][:16]}...")
    print(f"  letter={manifest['artifacts']['letter_pdf']}")
    print(f"  a4={manifest['artifacts']['a4_pdf']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
