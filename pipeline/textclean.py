"""Deterministic cleaning of OCR lines into rows, paragraphs and list items.

This is the step from the *OCR layer* to the *cleaned layer*. Every rule here is
mechanical and conservative: it joins what the line layout split (rows, hyphens,
paragraphs, bullets) and applies the hand-curated replacements from
curation/ocr-corrections.yaml. It never rewrites wording – typos of the script
itself stay, only OCR misreadings are corrected.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from functools import lru_cache

from . import catalog

ROW_TOLERANCE = 4.0            # pt: fragments whose tops differ less belong to one visual row
PARAGRAPH_GAP = 1.22           # × typical line pitch: a larger gap starts a new paragraph
                               # (measured: line gaps ≤ 19.5 pt, paragraph gaps ≥ 23 pt at 17.7 pt pitch)
HANGING_INDENT = 6.0           # pt: bullet text sits right of the bullet glyph
BULLET_GLYPHS = {"e", "°", "«", "»", "®", "©", "•", "o", "O", "*", "■", "▪", "-", "–", "+"}  # "Oo" = ring bullet
# Words that follow a hyphen at line end *without* being part of the hyphenated word
# ("Produkt- und Prozessentwicklung").
KEEP_HYPHEN_BEFORE = {"und", "oder", "bzw.", "sowie", "als", "bis", "noch", "wie"}
SENTENCE_END = re.compile(r"[.!?:]\)?[“”\"]?$|\[\^\d+\]$")
PAGE_NUMBER = re.compile(r"^\d{1,3}$")     # a printed page number that slipped into the body band
NUMBERED_ITEM = re.compile(r"^\(?\d{1,2}[.)]\s+\S")
# Run-in labels ("Organisations- und Informationsmanagement:") open a paragraph; finite verbs
# mark an ordinary sentence ending in a colon ("Folgende Punkte sind zu beachten:").
LABEL_MAX_WORDS = 6
SUBHEADING_MAX_WORDS = 5
FINITE_VERBS = {"ist", "sind", "wird", "werden", "kann", "können", "hat", "haben", "gilt", "gelten",
                "lässt", "lassen", "zeigt", "zeigen", "folgt", "folgen", "unterscheidet", "gibt"}


@dataclass
class Row:
    """One visual line of body text (fragments of the same baseline joined)."""
    page: int
    y: float
    x0: float
    text: str
    first_fragment: str = ""


@dataclass
class Block:
    """A unit of the cleaned layer, in reading order."""
    kind: str                  # paragraph | bullet | numbered | subheading
    page: int
    y: float
    text: str
    pages: set[int] = field(default_factory=set)


def to_rows(lines: list[dict], page: int) -> list[Row]:
    """Group line fragments into visual rows, left to right."""
    rows: list[list[dict]] = []
    for ln in sorted(lines, key=lambda l: (l["bbox"][1], l["bbox"][0])):
        if rows and abs(rows[-1][0]["bbox"][1] - ln["bbox"][1]) < ROW_TOLERANCE:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    out = []
    for frags in rows:
        frags.sort(key=lambda l: l["bbox"][0])
        text = " ".join(f["text"].strip() for f in frags if f["text"].strip())
        if text and not PAGE_NUMBER.match(text):
            out.append(Row(page, frags[0]["bbox"][1], frags[0]["bbox"][0], text, frags[0]["text"].strip()))
    return out


def line_pitch(rows: list[Row]) -> float:
    """Typical distance between consecutive lines of one paragraph (lower quartile of gaps)."""
    gaps = sorted(b.y - a.y for a, b in zip(rows, rows[1:]) if 8 < b.y - a.y < 40)
    if len(gaps) < 3:
        return 17.7          # measured body pitch of the script (12 pt type)
    return statistics.quantiles(gaps, n=4)[0]


def is_bullet(row: Row) -> bool:
    """A row starting with a bullet glyph; OCR sometimes reads one bullet as two glyphs ("®*")."""
    first = row.text.split(" ", 1)
    glyph = first[0]
    return (len(first) == 2 and (first[1][:1].isalnum() or first[1][:1] in "(„\"")
            and (glyph in BULLET_GLYPHS or len(glyph) == 2 and all(c in BULLET_GLYPHS for c in glyph)))


def strip_bullet(text: str) -> str:
    return text.split(" ", 1)[1]


def join_lines(a: str, b: str) -> str:
    """Join two consecutive lines, undoing end-of-line hyphenation."""
    if not a:
        return b
    if a.endswith("-") and len(a) > 1 and a[-2].isalpha():
        nxt = b.split(" ", 1)[0]
        if nxt[:1].islower() and nxt not in KEEP_HYPHEN_BEFORE:
            return a[:-1] + b                    # "Unter-" + "nehmen"
        if nxt in KEEP_HYPHEN_BEFORE:
            return f"{a} {b}"                    # "Produkt- und"
        return a + b                             # "Ist-" + "Einsatz"
    return f"{a} {b}"


def is_subheading(row: Row, gap_before: float, gap_after: float, pitch: float,
                  previous: Row | None = None, following: Row | None = None) -> bool:
    """A short, unpunctuated line standing alone ("Produktivität").

    Either it sits between two paragraph gaps, or – the scan sometimes sets a
    subheading with an ordinary line gap above it – it is at most SUBHEADING_MAX_WORDS
    words long, follows a finished sentence and is followed by a paragraph gap.
    A line whose successor starts in lowercase is never a heading: the sentence goes on.
    """
    t = row.text
    if (len(t) > 80 or not t[:1].isupper() or re.search(r"[.,;:!?\]]$", t) or NUMBERED_ITEM.match(t)
            or following is not None and following.text[:1].islower()):
        return False
    if gap_before > PARAGRAPH_GAP * pitch and gap_after > PARAGRAPH_GAP * pitch:
        return True
    return (len(t.split()) <= SUBHEADING_MAX_WORDS and previous is not None
            and bool(SENTENCE_END.search(previous.text)) and gap_after > PARAGRAPH_GAP * pitch)


def is_label(row: Row, previous: Row | None) -> bool:
    """A short row ending in ":" right after a finished sentence starts a new paragraph."""
    t = row.text
    return (previous is not None and t.endswith(":") and len(t) <= 70 and t[:1].isupper()
            and bool(SENTENCE_END.search(previous.text)))


def label_text(text: str) -> str:
    """Bold a noun-phrase label; leave colon-terminated sentences as they are."""
    words = text.split()
    if len(words) <= LABEL_MAX_WORDS and not FINITE_VERBS & {w.lower() for w in words}:
        return f"**{text}**"
    return text


def blocks_from_rows(rows: list[Row], margin: float, pitch: float) -> list[Block]:
    """Paragraphs, list items and unnumbered subheadings of one run of rows (no page break inside)."""
    blocks: list[Block] = []
    for i, row in enumerate(rows):
        gap_before = row.y - rows[i - 1].y if i else 99.0
        gap_after = rows[i + 1].y - row.y if i + 1 < len(rows) else 99.0
        current = blocks[-1] if blocks else None
        if is_bullet(row):
            blocks.append(Block("bullet", row.page, row.y, strip_bullet(row.text), {row.page}))
        elif NUMBERED_ITEM.match(row.text) and (gap_before > PARAGRAPH_GAP * pitch or row.x0 > margin + HANGING_INDENT
                                                 or (current and current.kind == "numbered")):
            blocks.append(Block("numbered", row.page, row.y, row.text, {row.page}))
        elif is_subheading(row, gap_before, gap_after, pitch, rows[i - 1] if i else None,
                           rows[i + 1] if i + 1 < len(rows) else None):
            blocks.append(Block("subheading", row.page, row.y, row.text, {row.page}))
        elif is_label(row, rows[i - 1] if i else None) and not (current and current.kind in ("bullet", "numbered")
                                                                 and row.x0 > margin + HANGING_INDENT):
            blocks.append(Block("paragraph", row.page, row.y, label_text(row.text), {row.page}))
        elif (current and current.kind in ("bullet", "numbered") and gap_before <= PARAGRAPH_GAP * pitch
              and row.x0 > margin + HANGING_INDENT):
            current.text = join_lines(current.text, row.text)         # continuation of a list item
        elif current and current.kind != "subheading" and (
                gap_before <= PARAGRAPH_GAP * pitch
                or row.text[:1].islower() and not SENTENCE_END.search(current.text)):
            current.text = join_lines(current.text, row.text)        # a wide gap inside a sentence
        else:
            blocks.append(Block("paragraph", row.page, row.y, row.text, {row.page}))
    return blocks


def continues(prev: Block, nxt: Block) -> bool:
    """Does `nxt` (first block of a new page) continue `prev` (last block of the previous page)?"""
    if prev.kind not in ("paragraph", "bullet", "numbered") or nxt.kind != "paragraph":
        return False
    return not SENTENCE_END.search(prev.text) and (nxt.text[:1].islower() or prev.text.endswith("-"))


@lru_cache(maxsize=1)
def _corrections() -> tuple[list[tuple[re.Pattern, str]], list[tuple[str, str, set[int] | None]]]:
    data = catalog.ocr_corrections()
    words = [(re.compile(rf"(?<![\wÄÖÜäöüß]){re.escape(k)}(?![\wÄÖÜäöüß])"), v)
             for k, v in (data.get("words") or {}).items()]
    literal = [(e["from"], e["to"], set(e["pages"]) if e.get("pages") else None)
               for e in (data.get("literal") or [])]
    return words, literal


def correct(text: str, pages: set[int]) -> str:
    """Apply the curated OCR corrections (whole words everywhere, literals optionally per page)."""
    words, literal = _corrections()
    for src, dst, only in literal:
        if only is None or pages & only:
            text = text.replace(src, dst)
    for pattern, dst in words:
        text = pattern.sub(dst, text)
    return re.sub(r"\s{2,}", " ", text).strip()
