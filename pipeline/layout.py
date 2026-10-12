"""Deterministic layout analysis of one scanned page (no OCR, no model calls).

Measured properties of the scan that this module relies on (150 dpi render):
* body text is printed black – the darkest 3 % of a line's pixels are < 90;
* figure / table captions are printed light grey – darkest 3 % ≥ 135 and the
  line is small (≤ 10.5 pt high);
* diagrams consist of connected components far larger than a glyph (frames,
  axes, curves, arrows, table rules, photos).

The result is a list of figure regions with their caption line, in visual PDF
points, plus the band boundaries (header, footnotes, footer) of the page.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

import cv2
import numpy as np
import pymupdf

from . import config
from .pdfpage import Line, render_gray, visual_lines

DPI = config.RENDER_DPI
S = DPI / 72.0                    # px per pt
CAPTION_MIN_DARKEST = 135         # grey caption ink
PROSE_MAX_DARKEST = 90            # black body ink
CAPTION_MAX_HEIGHT = 10.5         # pt
GLYPH_MAX = 22                    # pt – bigger components are graphics
MIN_FIG_W, MIN_FIG_H = 45, 28     # pt – smaller clusters are rules/underlines
CAPTION_RE = re.compile(r"^\W{0,2}(A|\\)?b+i?l?d?u?n?g?|^Tab", re.I)


@dataclass
class Caption:
    bbox: list[float]
    text: str                     # OCR text layer ("" if the OCR missed the line)
    kind: str                     # "figure" | "table" | "unknown"
    number: int | None = None


@dataclass
class Region:
    bbox: list[float]
    caption: Caption | None = None
    labels: list[str] = field(default_factory=list)   # raw OCR words inside the region
    has_graphics: bool = True


@dataclass
class PageLayout:
    page: int
    width: float
    height: float
    body_top: float
    body_bottom: float            # above footnotes / footer
    regions: list[Region]
    prose_lines: int

    def to_json(self) -> dict:
        return asdict(self)


def darkest_ink(gray: np.ndarray, bbox) -> int:
    x0, y0, x1, y1 = (int(round(v * S)) for v in bbox)
    patch = gray[max(y0, 0):max(y1, y0 + 1), max(x0, 0):max(x1, x0 + 1)]
    return int(np.percentile(patch, 3)) if patch.size else 255


def caption_kind(text: str) -> tuple[str, int | None]:
    m = re.search(r"(Abb\w*|\\bbildung|bbildung|Tab\w*)\s*(\d{1,3})", text)
    if not m:
        return ("unknown", None)
    kind = "table" if m.group(1).lower().startswith("tab") else "figure"
    return (kind, int(m.group(2)))


def footnote_top(gray: np.ndarray, top: float, bottom: float) -> float:
    """y (pt) of the footnote separator rule, or `bottom` if the page has none.

    The rule is a short (≈ 100–170 pt) dark horizontal line starting at the left
    text margin with blank rows above and below it.
    """
    h = gray.shape[0]
    y_from = int(max(top, 0.45 * h / S) * S)
    ink = gray < 160
    for y in range(int(bottom * S) - 1, y_from, -1):
        row = ink[y]
        n = int(row.sum())
        if not (0.12 * row.size < n < 0.35 * row.size):
            continue
        xs = np.flatnonzero(row)
        contiguous = xs[-1] - xs[0] + 1 <= n * 1.15
        quiet = ink[max(y - 4, 0)].sum() < 5 and ink[min(y + 5, h - 1)].sum() < row.size * 0.3
        if contiguous and quiet and xs[0] < 0.2 * row.size:
            return y / S - 2
    return bottom


def _graphic_mask(gray: np.ndarray, lines: list[Line]) -> np.ndarray:
    """Pixels belonging to non-glyph connected components."""
    ink = (gray < 200).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    big = np.zeros(n, dtype=bool)
    lim = GLYPH_MAX * S
    word_boxes = [w for ln in lines for w in ln.words]
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if w <= lim and h <= lim:
            continue
        # Oversized glyphs (titles) sit inside one OCR word box → still text.
        cx0, cy0, cx1, cy1 = x / S, y / S, (x + w) / S, (y + h) / S
        inside_word = any(wd.x0 - 2 <= cx0 and wd.y0 - 2 <= cy0 and cx1 <= wd.x1 + 2 and cy1 <= wd.y1 + 2
                          for wd in word_boxes)
        big[i] = not inside_word
    return big[lab].astype(np.uint8)


def _clusters(mask: np.ndarray, gap_pt: float) -> list[list[float]]:
    k = max(int(gap_pt * S), 1)
    dil = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(dil, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, _ = stats[i]
        # undo the dilation margin
        out.append([(x + k / 2) / S, (y + k / 2) / S, (x + w - k / 2) / S, (y + h - k / 2) / S])
    return out


def _overlaps(a, b, pad=0.0) -> bool:
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def _union(a, b):
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def analyse(page: pymupdf.Page) -> PageLayout:
    gray = render_gray(page, DPI)
    W, H = page.rect.width, page.rect.height
    lines = visual_lines(page)
    top, bottom = config.HEADER_BAND * H, config.FOOTER_BAND * H
    body_bottom = footnote_top(gray, top, bottom)

    in_body = [ln for ln in lines if ln.bbox[1] >= top and ln.bbox[3] <= body_bottom + 1]
    darkest = {id(ln): darkest_ink(gray, ln.bbox) for ln in in_body}
    captions = [ln for ln in in_body
                if darkest[id(ln)] >= CAPTION_MIN_DARKEST and ln.height <= CAPTION_MAX_HEIGHT
                and ln.bbox[2] - ln.bbox[0] > 40]
    prose = [ln for ln in in_body if darkest[id(ln)] < PROSE_MAX_DARKEST
             and ln.bbox[2] - ln.bbox[0] > 0.3 * W and ln.height >= 10.5]

    mask = _graphic_mask(gray, lines)
    mask[: int(top * S)] = 0
    mask[int(body_bottom * S):] = 0
    regions = [Region(bbox=b) for b in _clusters(mask, gap_pt=14)
               if b[2] - b[0] >= MIN_FIG_W and b[3] - b[1] >= MIN_FIG_H]
    regions = _merge(regions)
    # grey legend text inside a diagram is a label, not a caption
    captions = [c for c in captions if not any(_overlaps(r.bbox, c.bbox) for r in regions)]

    # Grow each region by the non-prose OCR lines that touch it (labels, legends).
    cap_ids = {id(c) for c in captions}
    prose_ids = {id(p) for p in prose}
    for reg in regions:
        changed = True
        while changed:
            changed = False
            for ln in in_body:
                if id(ln) in cap_ids or id(ln) in prose_ids:
                    continue
                if _overlaps(reg.bbox, ln.bbox, pad=4) and not _contains(reg.bbox, ln.bbox):
                    reg.bbox = _union(reg.bbox, list(ln.bbox))
                    changed = True
        reg.labels = [ln.text for ln in in_body if _contains(reg.bbox, ln.bbox, pad=2)
                      and id(ln) not in cap_ids]
    regions = _merge(regions)
    _attach_captions(regions, captions, prose)
    for reg in regions:
        if reg.caption is None:
            reg.caption = _grey_caption_below(gray, reg, lines, W, body_bottom)
    regions.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
    return PageLayout(page=page.number + 1, width=W, height=H, body_top=top,
                      body_bottom=body_bottom, regions=regions, prose_lines=len(prose))


def _contains(outer, inner, pad=0.0) -> bool:
    return (outer[0] - pad <= inner[0] and outer[1] - pad <= inner[1]
            and inner[2] <= outer[2] + pad and inner[3] <= outer[3] + pad)


def _merge(regions: list[Region]) -> list[Region]:
    merged = True
    while merged:
        merged = False
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                if _overlaps(regions[i].bbox, regions[j].bbox, pad=3):
                    regions[i].bbox = _union(regions[i].bbox, regions[j].bbox)
                    regions[i].labels += regions[j].labels
                    del regions[j]
                    merged = True
                    break
            if merged:
                break
    return regions


def _attach_captions(regions: list[Region], captions: list[Line], prose: list[Line]) -> None:
    """Pair every caption line with the region directly above (figures) or below
    (tables); captions without a graphic region get a text-only region spanning
    up to the previous prose line."""
    # merge caption lines that continue on the next line
    groups: list[list[Line]] = []
    for c in sorted(captions, key=lambda ln: ln.bbox[1]):
        if groups and 0 <= c.bbox[1] - groups[-1][-1].bbox[3] < 6 and not caption_kind(c.text)[1]:
            groups[-1].append(c)
        else:
            groups.append([c])
    for grp in groups:
        bbox = list(grp[0].bbox)
        for c in grp[1:]:
            bbox = _union(bbox, list(c.bbox))
        text = " ".join(c.text for c in grp)
        kind, number = caption_kind(text)
        cap = Caption(bbox=bbox, text=text, kind=kind, number=number)
        above = [r for r in regions if r.caption is None and r.bbox[3] <= bbox[1] + 4
                 and bbox[1] - r.bbox[3] < 45]
        below = [r for r in regions if r.caption is None and r.bbox[1] >= bbox[3] - 4
                 and r.bbox[1] - bbox[3] < 30]
        if kind == "table" and below:
            min(below, key=lambda r: r.bbox[1] - bbox[3]).caption = cap
        elif above:
            min(above, key=lambda r: bbox[1] - r.bbox[3]).caption = cap
        elif below:
            min(below, key=lambda r: r.bbox[1] - bbox[3]).caption = cap
        else:
            prev = [p.bbox[3] for p in prose if p.bbox[3] <= bbox[1]]
            y0 = max(prev) + 4 if prev else bbox[1] - 120
            regions.append(Region(bbox=[60, y0, 530, bbox[1] - 2], caption=cap, has_graphics=False))


def _grey_caption_below(gray: np.ndarray, reg: Region, lines: list[Line], W: float,
                        body_bottom: float) -> Caption | None:
    """Image fallback for captions the OCR layer missed: the first ink strip
    below the region that is grey-only (no black pixel) and text-line sized."""
    y_from, y_to = reg.bbox[3] + 1, min(reg.bbox[3] + 45, body_bottom)
    x0, x1 = int(40 * S), int((W - 40) * S)
    band = gray[int(y_from * S):int(y_to * S), x0:x1]
    if band.size == 0:
        return None
    rows_ink = (band < 225).sum(axis=1)
    strips, start = [], None
    for i, n in enumerate(list(rows_ink) + [0]):
        if n > 2 and start is None:
            start = i
        elif n <= 2 and start is not None:
            strips.append((start, i))
            start = None
    for a, b in strips:
        strip = band[a:b]
        h_pt = (b - a) / S
        if not (3.5 <= h_pt <= 12):
            return None                    # first thing below is not a text line
        if (strip < 110).sum() > 3:
            return None                    # black ink → body text, not a caption
        cols = np.flatnonzero((strip < 225).sum(axis=0))
        bbox = [(x0 + cols[0]) / S, y_from + a / S, (x0 + cols[-1]) / S, y_from + b / S]
        if bbox[2] - bbox[0] < 40:
            return None
        text = " ".join(w.text for ln in lines for w in ln.words
                        if _contains([bbox[0] - 3, bbox[1] - 3, bbox[2] + 3, bbox[3] + 3],
                                     [w.x0, w.y0, w.x1, w.y1]))
        kind, number = caption_kind(text)
        return Caption(bbox=bbox, text=text, kind=kind, number=number)
    return None
