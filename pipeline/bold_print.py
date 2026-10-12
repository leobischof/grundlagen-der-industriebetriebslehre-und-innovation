"""Bold print in the scan, measured from the pixels (the OCR text layer carries no font weight).

The script sets key terms and key sentences in bold. The scan is an image, so the weight is
measured: the mean horizontal run length of dark pixels in a word's box approximates its stroke
width. Measured on the 150 dpi analysis render: regular body text ≈ 2.7 px, bold ≈ 4.2 px
(ratio ≈ 1.6); everything above STROKE_RATIO × the page median counts as bold. A page full of
figure labels skews that median (thin grey labels: 2.0 px on PDF page 78; white type on a dark
panel: 4.5 px on page 93), so it is clamped to the range body text spans across the script.
"""
from __future__ import annotations

import statistics

import numpy as np

from .pdfpage import Line

STROKE_RATIO = 1.3            # × page median stroke width
DARK = 128                    # grey value below which a pixel is ink
MIN_ALNUM = 2                 # a shorter token ("A.", "-", a bullet glyph) is never bold by itself
BODY_HEIGHT = (8.0, 16.0)     # pt: word boxes that set the page median (body type, no headings)
BODY_STROKE = (2.45, 2.9)     # px at 150 dpi: page medians of body-text pages (all 190 pages measured)


def _alnum(text: str) -> int:
    return sum(c.isalnum() for c in text)


def stroke_width(gray: np.ndarray, bbox, scale: float) -> float:
    """Dark pixels per horizontal dark run inside bbox (visual pt; `scale` px per pt), 0 if blank."""
    x0, y0, x1, y1 = bbox
    box = gray[int(y0 * scale):int(y1 * scale) + 1, int(x0 * scale):int(x1 * scale) + 1] < DARK
    if not box.any():
        return 0.0
    starts = np.diff(box.astype(np.int8), axis=1, prepend=0) == 1
    return float(box.sum()) / max(int(starts.sum()), 1)


def _fill_gaps(flags: list[bool], words: list[str]) -> list[bool]:
    """A short token between two bold words is bold too ("Joseph A. Schumpeter", "1883 - 1950")."""
    out = list(flags)
    for i in range(1, len(words) - 1):
        if not out[i] and _alnum(words[i]) < MIN_ALNUM and out[i - 1] and flags[i + 1]:
            out[i] = True
    return out


def bold_words(gray: np.ndarray, lines: list[Line], scale: float) -> list[list[int]]:
    """Per line, the indices of its bold words (Line.words order)."""
    widths = [[stroke_width(gray, (w.x0, w.y0, w.x1, w.y1), scale) for w in ln.words] for ln in lines]
    body = [s for ln, row in zip(lines, widths) for w, s in zip(ln.words, row)
            if BODY_HEIGHT[0] < w.h < BODY_HEIGHT[1] and _alnum(w.text) > 3]
    if not body:
        return [[] for _ in lines]
    median = min(max(statistics.median(body), BODY_STROKE[0]), BODY_STROKE[1])
    out = []
    for ln, row in zip(lines, widths):
        texts = [w.text for w in ln.words]
        flags = [s > STROKE_RATIO * median and _alnum(t) >= MIN_ALNUM for s, t in zip(row, texts)]
        out.append([i for i, f in enumerate(_fill_gaps(flags, texts)) if f])
    return out
