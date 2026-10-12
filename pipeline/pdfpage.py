"""Page model of the scanned script: OCR words and lines in *visual* coordinates.

Every page of the script is stored with /Rotate 270 – the OCR text layer lives
in unrotated space while a reader sees the page upright. All downstream code
works in visual coordinates (origin top-left, y down, units = PDF points) so
that "top of the page", crops and reading order mean what they look like.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pymupdf


@dataclass
class Word:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def h(self) -> float:
        return self.y1 - self.y0


@dataclass
class Line:
    words: list[Word] = field(default_factory=list)
    block: int = 0

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (min(w.x0 for w in self.words), min(w.y0 for w in self.words),
                max(w.x1 for w in self.words), max(w.y1 for w in self.words))

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def height(self) -> float:
        b = self.bbox
        return b[3] - b[1]


def visual_words(page: pymupdf.Page) -> list[Word]:
    m = page.rotation_matrix
    out = []
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        r = pymupdf.Rect(x0, y0, x1, y1) * m
        r.normalize()
        out.append(Word(r.x0, r.y0, r.x1, r.y1, text))
    return out


def visual_lines(page: pymupdf.Page) -> list[Line]:
    """OCR lines (as segmented by the OCR engine) in reading order."""
    m = page.rotation_matrix
    lines: list[Line] = []
    for b_no, block in enumerate(page.get_text("rawdict")["blocks"]):
        for ln in block.get("lines", []):
            line = Line(block=b_no)
            for span in ln["spans"]:
                # rawdict gives characters; regroup them into words on spaces
                cur: list = []
                for ch in span["chars"] + [None]:
                    if ch is None or ch["c"].isspace():
                        if cur:
                            r = pymupdf.Rect(cur[0]["bbox"]) | pymupdf.Rect(cur[-1]["bbox"])
                            for c in cur:
                                r |= pymupdf.Rect(c["bbox"])
                            r = r * m
                            r.normalize()
                            line.words.append(Word(r.x0, r.y0, r.x1, r.y1, "".join(c["c"] for c in cur)))
                        cur = []
                    else:
                        cur.append(ch)
            if line.words:
                lines.append(line)
    lines.sort(key=lambda ln: (round(ln.bbox[1] / 4), ln.bbox[0]))
    return lines


def render_gray(page: pymupdf.Page, dpi: int, clip: pymupdf.Rect | None = None) -> np.ndarray:
    """Upright grayscale render (uint8, H×W). `clip` is in visual coordinates."""
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, clip=clip)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)


def render_png(page: pymupdf.Page, dpi: int, clip: pymupdf.Rect | None = None) -> bytes:
    return page.get_pixmap(dpi=dpi, clip=clip).tobytes("png")
