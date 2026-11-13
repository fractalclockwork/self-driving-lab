"""Printable prep-area ChArUco card (Dev-Host generation; detection later)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

# Locked geometry for sdl-prep-charuco-v1 (OpenCV CharucoBoard constructor args).
CARD_ID = "sdl-prep-charuco-v1"
DICTIONARY_NAME = "DICT_4X4_50"
SQUARES_X = 5
SQUARES_Y = 7
SQUARE_LENGTH_MM = 24.0
MARKER_LENGTH_MM = 18.0
BOARD_DPI = 600
SCALE_BAR_MM = 100.0
PRINTER_MARGIN_MM = 12.0
FOOTER_GAP_MM = 8.0
BAR_GAP_MM = 10.0
BAR_THICKNESS_MM = 2.0

# Page sizes in millimeters.
PAGE_LETTER_MM = (215.9, 279.4)
PAGE_A4_MM = (210.0, 297.0)

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0


@dataclass(frozen=True)
class CardGeometry:
    """ChArUco board constructor arguments and derived sizes."""

    card_id: str = CARD_ID
    dictionary: str = DICTIONARY_NAME
    squares_x: int = SQUARES_X
    squares_y: int = SQUARES_Y
    square_length_mm: float = SQUARE_LENGTH_MM
    marker_length_mm: float = MARKER_LENGTH_MM
    dpi: int = BOARD_DPI

    @property
    def board_width_mm(self) -> float:
        return self.squares_x * self.square_length_mm

    @property
    def board_height_mm(self) -> float:
        return self.squares_y * self.square_length_mm

    @property
    def marker_count(self) -> int:
        # ChArUco places markers on black squares of a checkerboard.
        return (self.squares_x * self.squares_y) // 2

    def dictionary_capacity(self) -> int:
        # DICT_NxN_M → M unique marker IDs.
        if self.dictionary.startswith("DICT_") and "_" in self.dictionary:
            try:
                return int(self.dictionary.rsplit("_", 1)[-1])
            except ValueError:
                pass
        raise ValueError(f"unknown dictionary capacity for {self.dictionary}")

    def validate(self) -> None:
        if self.marker_length_mm >= self.square_length_mm:
            raise ValueError("marker_length_mm must be < square_length_mm")
        if self.marker_count > self.dictionary_capacity():
            raise ValueError(
                f"need {self.marker_count} markers but {self.dictionary} "
                f"only has {self.dictionary_capacity()}"
            )
        if self.squares_x < 2 or self.squares_y < 2:
            raise ValueError("ChArUco needs at least 2x2 squares")


@dataclass(frozen=True)
class PageSpec:
    name: str
    width_mm: float
    height_mm: float

    @property
    def width_pt(self) -> float:
        return mm_to_pt(self.width_mm)

    @property
    def height_pt(self) -> float:
        return mm_to_pt(self.height_mm)


PAGE_LETTER = PageSpec("letter", *PAGE_LETTER_MM)
PAGE_A4 = PageSpec("a4", *PAGE_A4_MM)


@dataclass(frozen=True)
class CardLayout:
    """Positions for board, scale bar, and footer on a page (mm from bottom-left)."""

    page: PageSpec
    board_x_mm: float
    board_y_mm: float
    board_w_mm: float
    board_h_mm: float
    bar_x_mm: float
    bar_y_mm: float
    bar_length_mm: float
    bar_thickness_mm: float
    footer_y_mm: float
    margin_mm: float


def default_geometry() -> CardGeometry:
    g = CardGeometry()
    g.validate()
    return g


def mm_to_pt(mm: float) -> float:
    return mm * PT_PER_INCH / MM_PER_INCH


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm / MM_PER_INCH * dpi))


def layout_card(
    geometry: CardGeometry,
    page: PageSpec,
    *,
    margin_mm: float = PRINTER_MARGIN_MM,
) -> CardLayout:
    """Place board (top), 100 mm bar, and footer inside printer margins."""
    geometry.validate()
    bw = geometry.board_width_mm
    bh = geometry.board_height_mm
    usable_w = page.width_mm - 2 * margin_mm
    usable_h = page.height_mm - 2 * margin_mm
    if bw > usable_w or bh > usable_h:
        raise ValueError(
            f"board {bw}x{bh} mm does not fit {page.name} "
            f"usable {usable_w:.1f}x{usable_h:.1f} mm"
        )

    # Content stack from bottom of usable area: footer gap → bar → gap → board.
    footer_block_mm = 14.0
    stack_h = bh + BAR_GAP_MM + BAR_THICKNESS_MM + FOOTER_GAP_MM + footer_block_mm
    if stack_h > usable_h:
        raise ValueError(
            f"board + scale bar + footer ({stack_h:.1f} mm) exceed "
            f"{page.name} usable height {usable_h:.1f} mm"
        )

    board_x = margin_mm + (usable_w - bw) / 2.0
    # Align stack near the top of the page (more white space below footer is fine).
    top = page.height_mm - margin_mm
    board_y = top - bh
    bar_y = board_y - BAR_GAP_MM - BAR_THICKNESS_MM
    bar_x = margin_mm + (usable_w - SCALE_BAR_MM) / 2.0
    if bar_x < margin_mm or bar_x + SCALE_BAR_MM > page.width_mm - margin_mm:
        raise ValueError("100 mm scale bar does not fit page width inside margins")
    footer_y = margin_mm + 4.0

    return CardLayout(
        page=page,
        board_x_mm=board_x,
        board_y_mm=board_y,
        board_w_mm=bw,
        board_h_mm=bh,
        bar_x_mm=bar_x,
        bar_y_mm=bar_y,
        bar_length_mm=SCALE_BAR_MM,
        bar_thickness_mm=BAR_THICKNESS_MM,
        footer_y_mm=footer_y,
        margin_mm=margin_mm,
    )


def _aruco_dictionary(name: str) -> Any:
    import cv2

    if not hasattr(cv2.aruco, name):
        raise ValueError(f"OpenCV aruco has no dictionary {name}")
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name))


def render_board_png(geometry: CardGeometry | None = None) -> bytes:
    """Rasterize the ChArUco board at geometry.dpi; return PNG bytes."""
    import cv2

    geometry = geometry or default_geometry()
    geometry.validate()
    dictionary = _aruco_dictionary(geometry.dictionary)
    board = cv2.aruco.CharucoBoard(
        (geometry.squares_x, geometry.squares_y),
        geometry.square_length_mm,
        geometry.marker_length_mm,
        dictionary,
    )
    w_px = mm_to_px(geometry.board_width_mm, geometry.dpi)
    h_px = mm_to_px(geometry.board_height_mm, geometry.dpi)
    img = board.generateImage((w_px, h_px))
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("cv2.imencode failed for ChArUco board")
    return bytes(buf)


def board_sha256(png_bytes: bytes) -> str:
    return hashlib.sha256(png_bytes).hexdigest()


def write_pdf(
    path: Path,
    *,
    page: PageSpec,
    geometry: CardGeometry,
    board_png: bytes,
    layout: CardLayout | None = None,
) -> CardLayout:
    """Write a print-ready PDF with board image, vector 100 mm bar, and footer."""
    from reportlab.lib.units import mm as rl_mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    layout = layout or layout_card(geometry, page)
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(path), pagesize=(page.width_pt, page.height_pt))
    img = ImageReader(BytesIO(board_png))
    c.drawImage(
        img,
        layout.board_x_mm * rl_mm,
        layout.board_y_mm * rl_mm,
        width=layout.board_w_mm * rl_mm,
        height=layout.board_h_mm * rl_mm,
        preserveAspectRatio=True,
        mask="auto",
    )

    # Vector scale bar (exact 100 mm in PDF user space).
    bx = layout.bar_x_mm * rl_mm
    by = layout.bar_y_mm * rl_mm
    bl = layout.bar_length_mm * rl_mm
    bt = layout.bar_thickness_mm * rl_mm
    c.setFillColorRGB(0, 0, 0)
    c.rect(bx, by, bl, bt, fill=1, stroke=0)
    # End ticks.
    tick = 6 * rl_mm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.line(bx, by, bx, by + tick)
    c.line(bx + bl, by, bx + bl, by + tick)
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        bx + bl / 2.0,
        by + bt + 2 * rl_mm,
        f"{layout.bar_length_mm:.0f} mm  (ruler must read {layout.bar_length_mm:.0f} mm)",
    )

    footer_lines = [
        f"{geometry.card_id}  |  {geometry.dictionary}  |  "
        f"{geometry.squares_x}x{geometry.squares_y} squares  |  "
        f"square={geometry.square_length_mm:g} mm  marker={geometry.marker_length_mm:g} mm",
        "PRINT AT 100% / ACTUAL SIZE — do not fit to page or scale.",
    ]
    c.setFont("Helvetica", 8)
    y = layout.footer_y_mm * rl_mm
    for line in footer_lines:
        c.drawCentredString(page.width_pt / 2.0, y, line)
        y += 10

    c.showPage()
    c.save()
    return layout


def opencv_version() -> str:
    import cv2

    return cv2.__version__


def build_manifest(
    geometry: CardGeometry,
    *,
    board_png: bytes,
    letter_pdf: Path,
    a4_pdf: Path,
) -> dict[str, Any]:
    return {
        "card_id": geometry.card_id,
        "dictionary": geometry.dictionary,
        "squares_x": geometry.squares_x,
        "squares_y": geometry.squares_y,
        "square_length_mm": geometry.square_length_mm,
        "marker_length_mm": geometry.marker_length_mm,
        "board_width_mm": geometry.board_width_mm,
        "board_height_mm": geometry.board_height_mm,
        "marker_count": geometry.marker_count,
        "dpi": geometry.dpi,
        "scale_bar_mm": SCALE_BAR_MM,
        "board_png_sha256": board_sha256(board_png),
        "opencv_version": opencv_version(),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifacts": {
            "letter_pdf": letter_pdf.name,
            "a4_pdf": a4_pdf.name,
        },
        "constructor": {
            "opencv": "cv2.aruco.CharucoBoard",
            "size": [geometry.squares_x, geometry.squares_y],
            "squareLength": geometry.square_length_mm,
            "markerLength": geometry.marker_length_mm,
            "dictionary": geometry.dictionary,
        },
        "notes": (
            "Print Letter or A4 PDF at 100% / actual size. "
            "Ruler-check the 100 mm vector scale bar before use. "
            "Detection must rebuild the same CharucoBoard on the Dev-Host; "
            "cede-gateway is attach/temporary capture only."
        ),
    }


class PrepAreaCharucoCard:
    """Generate committed prep-area ChArUco PDFs + JSON manifest."""

    def __init__(self, geometry: CardGeometry | None = None) -> None:
        self.geometry = geometry or default_geometry()
        self.geometry.validate()

    def generate(self, out_dir: Path) -> dict[str, Any]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        board_png = render_board_png(self.geometry)
        letter_pdf = out_dir / "prep_area_charuco_letter.pdf"
        a4_pdf = out_dir / "prep_area_charuco_a4.pdf"
        write_pdf(
            letter_pdf,
            page=PAGE_LETTER,
            geometry=self.geometry,
            board_png=board_png,
        )
        write_pdf(
            a4_pdf,
            page=PAGE_A4,
            geometry=self.geometry,
            board_png=board_png,
        )
        manifest = build_manifest(
            self.geometry,
            board_png=board_png,
            letter_pdf=letter_pdf,
            a4_pdf=a4_pdf,
        )
        manifest_path = out_dir / "prep_area_charuco.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        # Optional PNG for inspection / hash re-check without re-encoding PDF.
        (out_dir / "prep_area_charuco_board.png").write_bytes(board_png)
        return manifest


def pdf_mediabox_mm(path: Path) -> tuple[float, float]:
    """Return PDF MediaBox width/height in mm (requires pypdf or reportlab parse)."""
    data = path.read_bytes()
    # Minimal parse: /MediaBox [0 0 W H]
    import re

    m = re.search(
        rb"/MediaBox\s*\[\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*\]",
        data,
    )
    if not m:
        raise ValueError(f"no MediaBox in {path}")
    x0, y0, x1, y1 = (float(m.group(i)) for i in range(1, 5))
    w_pt = x1 - x0
    h_pt = y1 - y0
    return (
        w_pt * MM_PER_INCH / PT_PER_INCH,
        h_pt * MM_PER_INCH / PT_PER_INCH,
    )


def calibration_deps_available() -> bool:
    try:
        import cv2  # noqa: F401
        import reportlab  # noqa: F401

        return hasattr(__import__("cv2").aruco, "CharucoBoard")
    except Exception:  # noqa: BLE001
        return False
