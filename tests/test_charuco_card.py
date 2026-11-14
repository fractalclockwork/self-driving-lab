"""Tests for prep-area ChArUco card geometry and printable PDFs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdl.calibration.charuco_card import (
    PAGE_A4,
    PAGE_LETTER,
    SCALE_BAR_MM,
    CardGeometry,
    PrepAreaCharucoCard,
    board_sha256,
    calibration_deps_available,
    default_geometry,
    layout_card,
    pdf_mediabox_mm,
    render_board_png,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CAL_DIR = REPO_ROOT / "docs" / "project" / "calibration"
MANIFEST = CAL_DIR / "prep_area_charuco.json"
LETTER_PDF = CAL_DIR / "prep_area_charuco_letter.pdf"
A4_PDF = CAL_DIR / "prep_area_charuco_a4.pdf"


def test_default_geometry_valid():
    g = default_geometry()
    assert g.marker_length_mm < g.square_length_mm
    assert g.board_width_mm == 120.0
    assert g.board_height_mm == 168.0
    assert g.marker_count == (5 * 7) // 2
    assert g.marker_count <= g.dictionary_capacity()


def test_geometry_rejects_bad_marker():
    with pytest.raises(ValueError, match="marker_length"):
        CardGeometry(marker_length_mm=24.0).validate()


def test_layout_fits_letter_and_a4():
    g = default_geometry()
    for page in (PAGE_LETTER, PAGE_A4):
        layout = layout_card(g, page)
        assert layout.bar_length_mm == SCALE_BAR_MM
        assert layout.board_w_mm == g.board_width_mm
        assert layout.board_h_mm == g.board_height_mm
        assert layout.board_x_mm >= layout.margin_mm - 1e-6
        assert (
            layout.board_x_mm + layout.board_w_mm
            <= page.width_mm - layout.margin_mm + 1e-6
        )
        assert layout.bar_x_mm >= layout.margin_mm - 1e-6
        assert (
            layout.bar_x_mm + layout.bar_length_mm
            <= page.width_mm - layout.margin_mm + 1e-6
        )


def test_committed_pdf_mediaboxes():
    assert LETTER_PDF.is_file()
    assert A4_PDF.is_file()
    lw, lh = pdf_mediabox_mm(LETTER_PDF)
    aw, ah = pdf_mediabox_mm(A4_PDF)
    assert lw == pytest.approx(PAGE_LETTER.width_mm, abs=0.2)
    assert lh == pytest.approx(PAGE_LETTER.height_mm, abs=0.2)
    assert aw == pytest.approx(PAGE_A4.width_mm, abs=0.2)
    assert ah == pytest.approx(PAGE_A4.height_mm, abs=0.2)


def test_committed_manifest_geometry():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    g = default_geometry()
    assert data["card_id"] == g.card_id
    assert data["dictionary"] == g.dictionary
    assert data["squares_x"] == g.squares_x
    assert data["squares_y"] == g.squares_y
    assert data["square_length_mm"] == g.square_length_mm
    assert data["marker_length_mm"] == g.marker_length_mm
    assert data["scale_bar_mm"] == SCALE_BAR_MM
    assert data["board_png_sha256"]
    assert len(data["board_png_sha256"]) == 64


@pytest.mark.skipif(
    not calibration_deps_available(),
    reason="uv sync --extra calibration required",
)
def test_regenerate_board_matches_manifest_hash(tmp_path: Path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    png = render_board_png(default_geometry())
    assert board_sha256(png) == data["board_png_sha256"]

    # Round-trip generate into a temp dir and check PDFs are non-empty.
    out = tmp_path / "cal"
    manifest = PrepAreaCharucoCard().generate(out)
    assert (out / "prep_area_charuco_letter.pdf").stat().st_size > 1000
    assert (out / "prep_area_charuco_a4.pdf").stat().st_size > 1000
    assert manifest["board_png_sha256"] == data["board_png_sha256"]
