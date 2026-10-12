"""Stage "extract-text": the raw OCR layer of the script, page by page.

Source of the text is the OCR layer embedded in the scanned PDF (it is better
than a fresh Tesseract pass – measured, see docs/pipeline.md). Nothing is
corrected here: this is the *OCR layer* of the four-layer model
(original → OCR → cleaned → AI explanation). Each line keeps its bounding box
and an ink class, because the scan prints body text black and captions grey,
which later separates prose from figure labels without any model, and the
indices of its words set in bold print (bold_print).

Output: sources/ocr/skript-pages.jsonl (one JSON object per PDF page).
"""
from __future__ import annotations

import json
import re

import pymupdf

from . import bold_print, catalog, config
from .cache import JsonCache, key_for, sha256_file, write_if_changed
from .ingest import source_path
from .layout import CAPTION_MAX_HEIGHT, CAPTION_MIN_DARKEST, PROSE_MAX_DARKEST, darkest_ink, footnote_top
from .pages import parse_pages
from .pdfpage import render_gray, visual_lines

OUT = config.OCR_DIR / "skript-pages.jsonl"
# Characters that occur in correct German text of the script. Anything else in
# a token (e.g. "¬", "|", "©") is a typical OCR artefact.
_GOOD = re.compile(r"^[\wÄÖÜäöüß.,;:!?()\[\]\-–—/%&'\"„“”‚‘’§+=*<>°€$#@…]+$")
_MIXED = re.compile(r"[A-Za-zÄÖÜäöüß]+\d+[A-Za-zÄÖÜäöüß]+")   # "Inno4vation"
LOW_QUALITY = 0.08          # share of suspicious tokens that marks a page as weak
# Footnote block without a separator rule: starts with a number-like token ("43", "1u6")
# or a garbled number before "Vgl."/"ibidem", after a clear gap, low on the page, left-aligned.
# Numbered headings ("9.1.4 Das Bestandsdilemma") look alike and are excluded.
_NOTE_START = re.compile(r"^\s*(?!\d+[.\-]\d)(?:\S{0,3}\d\S{0,2}\s+\S|\S{1,3}\s+(?:Vg|vg|[\]Ii1l]bid))")
NOTE_MIN_GAP = 28.0         # pt between the last body line and the first footnote
NOTE_MAX_X0 = 90.0
NOTE_REGION = 0.7           # footnote blocks start below this fraction of the page height


def _band(bbox, top: float, body_bottom: float, bottom: float) -> str:
    if bbox[3] <= top:
        return "header"
    if bbox[1] >= bottom:
        return "footer"
    if bbox[1] >= body_bottom - 1:
        return "footnote"
    return "body"


def _ink(dark: int, height: float) -> str:
    if dark < PROSE_MAX_DARKEST:
        return "black"
    if dark >= CAPTION_MIN_DARKEST and height <= CAPTION_MAX_HEIGHT:
        return "grey"
    return "mid"


def _quality(words: list[str]) -> dict:
    """Cheap, deterministic OCR plausibility metrics (no dictionary needed)."""
    if not words:
        return {"words": 0, "suspicious": 0, "suspicious_ratio": 0.0, "low": False}
    bad = [w for w in words if not _GOOD.match(w) or _MIXED.search(w)]
    ratio = round(len(bad) / len(words), 3)
    return {"words": len(words), "suspicious": len(bad), "suspicious_ratio": ratio,
            "low": ratio > LOW_QUALITY, "examples": bad[:8]}


def _footer_footnotes(lines: list[dict]) -> None:
    """Footnotes printed so low that they fall into the footer band.

    The footer holds only the page number, the institute line and the professor's
    name; a left-aligned footer line longer than a page number is a footnote.
    """
    for ln in lines:
        if ln["band"] == "footer" and ln["bbox"][0] < NOTE_MAX_X0 and len(ln["text"].strip()) > 5:
            ln["band"] = "footnote"


def _late_footnotes(lines: list[dict], H: float) -> None:
    """Re-band the footnote block of pages where the separator rule was not detected.

    `footnote_top` finds the short rule above the footnotes; on some scans it is too
    faint and the footnotes end up in the body band. They are recognised by layout
    instead: a clear gap, then only left-aligned lines down to the footer, the first
    one starting with a (garbled) footnote number. Line heights are not used: on some
    pages the OCR layer reports them inflated (p. 148: 23 pt for 12 pt type).
    """
    body = [ln for ln in lines if ln["band"] == "body"]
    for i in range(1, len(body)):
        ln, prev = body[i], body[i - 1]
        if ln["bbox"][1] < NOTE_REGION * H or ln["bbox"][1] - prev["bbox"][1] < NOTE_MIN_GAP:
            continue
        block = body[i:]
        if _NOTE_START.match(ln["text"]) and all(b["bbox"][0] < NOTE_MAX_X0 for b in block):
            for b in block:
                b["band"] = "footnote"
            return


def page_record(page: pymupdf.Page) -> dict:
    H = page.rect.height
    gray = render_gray(page, config.RENDER_DPI)
    top, bottom = config.HEADER_BAND * H, config.FOOTER_BAND * H
    body_bottom = footnote_top(gray, top, bottom)
    lines = []
    visual = visual_lines(page)
    for ln, bold in zip(visual, bold_print.bold_words(gray, visual, config.RENDER_DPI / 72)):
        b = ln.bbox
        lines.append({
            "bbox": [round(v, 1) for v in b],
            "text": ln.text,
            "band": _band(b, top, body_bottom, bottom),
            "ink": _ink(darkest_ink(gray, b), b[3] - b[1]),
            "size": round(b[3] - b[1], 1),
        })
        if bold:
            lines[-1]["bold"] = bold         # indices into text.split(): words set in bold print
    _late_footnotes(lines, H)
    _footer_footnotes(lines)
    words = [w for ln in lines if ln["band"] == "body" for w in ln["text"].split()]
    pno = page.number + 1
    return {
        "page": pno,
        "printed_page": catalog.printed_page(pno),
        "width": round(page.rect.width, 1),
        "height": round(H, 1),
        "body_top": round(top, 1),
        "body_bottom": round(body_bottom, 1),
        "lines": lines,
        "quality": _quality(words),
    }


def load_pages() -> dict[int, dict]:
    """The OCR layer as {pdf_page: record}; empty if the stage has not run."""
    if not OUT.exists():
        return {}
    recs = (json.loads(s) for s in OUT.read_text(encoding="utf-8").splitlines() if s.strip())
    return {r["page"]: r for r in recs}


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    pdf_path = source_path(config.SKRIPT)
    pdf_hash = sha256_file(pdf_path)
    doc = pymupdf.open(pdf_path)
    selected = parse_pages(pages, doc.page_count)
    cache = JsonCache("extract-text", force=force)
    version = config.STAGE_VERSIONS["extract-text"]
    records = load_pages()
    if dry_run:
        todo = [p for p in selected if force or not cache.has(key_for(pdf_hash, p, version))]
        print(f"[extract-text] würde {len(todo)} von {len(selected)} Seiten neu lesen: {todo[:20]}")
        return 0
    for pno in selected:
        key = key_for(pdf_hash, pno, version)
        records[pno] = cache.get_or_compute(key, lambda p=pno: page_record(doc[p - 1]))
    text = "".join(json.dumps(records[p], ensure_ascii=False) + "\n" for p in sorted(records))
    changed = write_if_changed(OUT, text)
    weak = [p for p in sorted(records) if records[p]["quality"]["low"]]
    print(cache.summary(), "| geschrieben" if changed else "| unverändert",
          f"| Seiten mit schwacher OCR: {weak or 'keine'}")
    return 0
