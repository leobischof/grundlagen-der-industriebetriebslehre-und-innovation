"""Locate every curated heading (curation/structure.yaml) on its page.

The TOC says on which page a heading is; this module finds the OCR line that
holds it, so text, figures and footnotes can be assigned to the right section
by position (page, y). Matching is fuzzy because the OCR layer garbles some
headings ("4.1.3 lnnovationsbarrieren"). Pure function of the OCR layer – cheap,
deterministic, no cache needed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache

from . import catalog
from .catalog import Entry

RUNNING_HEADER_MAX_Y = 45      # pt – running header lines sit above this
MIN_SCORE = 0.6


@dataclass(frozen=True)
class Located:
    entry: Entry
    page: int
    y: float                   # top of the heading line (pt); 0.0 if not found
    line_index: int | None     # index into the page's OCR lines, None if not found
    lines_used: int            # 1, or 2 when the heading wraps onto a second line
    score: float


def _norm(s: str) -> str:
    s = s.lower().replace("ß", "ss")
    return re.sub(r"[^a-z0-9äöü]+", "", s)


def _score(entry: Entry, text: str) -> float:
    """Similarity of an OCR line to "<number> <title>", tolerant to a garbled number."""
    t = _norm(text)
    full = _norm(f"{entry.number_printed or entry.number} {entry.title}")
    title = _norm(entry.title)
    best = max(SequenceMatcher(None, full, t).ratio(), SequenceMatcher(None, title, t).ratio())
    return best


def _find(entry: Entry, lines: list[dict], after_y: float) -> tuple[int | None, int, float]:
    best = (None, 1, 0.0)
    for i, ln in enumerate(lines):
        if ln["bbox"][1] < max(RUNNING_HEADER_MAX_Y, after_y) or ln["band"] in ("footer", "footnote"):
            continue
        s1 = _score(entry, ln["text"])
        if s1 > best[2]:
            best = (i, 1, s1)
        if i + 1 < len(lines):                        # heading wrapped onto a second line
            s2 = _score(entry, ln["text"] + " " + lines[i + 1]["text"])
            if s2 > best[2] + 0.05:
                best = (i, 2, s2)
    return best


def locate(pages: dict[int, dict]) -> list[Located]:
    """All TOC entries with their position, in document order."""
    out: list[Located] = []
    last_on_page: dict[int, float] = {}
    for e in catalog.entries():
        lines = pages.get(e.pdf_page, {}).get("lines", [])
        after = last_on_page.get(e.pdf_page, 0.0)
        idx, used, score = _find(e, lines, after)
        if idx is None or score < MIN_SCORE:
            out.append(Located(e, e.pdf_page, after, None, 0, round(score, 2)))
            continue
        y = lines[idx]["bbox"][1]
        last_on_page[e.pdf_page] = y + 1
        out.append(Located(e, e.pdf_page, y, idx, used, round(score, 2)))
    return out


@lru_cache(maxsize=1)
def _located_cached() -> tuple[Located, ...]:
    from .extract_text import load_pages      # local import: avoids a cycle at import time
    return tuple(locate(load_pages()))


def section_at(page: int, y: float) -> Entry | None:
    """The level-≤2 entry (= content file) that a point on a page belongs to."""
    current = None
    for loc in _located_cached():
        if loc.entry.level > 2 or loc.entry.kind == "chapter":
            continue
        if (loc.page, loc.y) <= (page, y):
            current = loc.entry
    return current


def subsection_at(page: int, y: float) -> Entry | None:
    """The deepest entry whose heading precedes the point (for finer links)."""
    current = None
    for loc in _located_cached():
        if (loc.page, loc.y) <= (page, y):
            current = loc.entry
    return current


def located() -> tuple[Located, ...]:
    return _located_cached()
