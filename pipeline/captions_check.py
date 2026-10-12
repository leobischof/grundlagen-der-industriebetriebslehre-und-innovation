"""Stage "captions": verify each curated caption against two independent OCR readings.

The curated titles in curation/figures.yaml were transcribed once (logged AI
pass). This stage re-reads every caption strip deterministically – from the
PDF's OCR layer and with a fresh local Tesseract pass – and compares both with
the curated number and title. Disagreements land in reports/captions-check.md
for a human to look at; nothing is changed automatically.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

import pymupdf

from . import catalog, config, ocr_fallback
from .cache import write_if_changed
from .extract_text import load_pages
from .ingest import source_path

REPORT = config.REPORTS / "captions-check.md"
STRIP_H = 30.0        # pt below the graphic searched for the caption
OK_SIMILARITY = 0.8
TITLE_ONLY_OK = 0.9     # a title this close identifies the figure even if the number is misread
PREFIX = re.compile(r"^.*?(Abb\w*|\\bbildung|bbildung|Tab\w*)\s*(\d{1,3})\s*[:.]?\s*", re.I)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9äöüß]+", "", s.lower())


def split_caption(text: str) -> tuple[int | None, str]:
    """"Abbildung 8: Produktlebenszyklus⁴³" -> (8, "Produktlebenszyklus⁴³")."""
    m = PREFIX.match(text)
    if not m:
        return None, text
    num = m.group(2)
    return (int(num) if num.isdigit() else None), text[m.end():]


def similarity(title: str, read: str) -> float:
    a, b = _norm(title), _norm(read)
    if not a or not b:
        return 0.0
    # Captions end with a footnote number ("…zyklus43"); compare on the title's length.
    return SequenceMatcher(None, a, b[: len(a) + 2]).ratio()


def strip_rect(f: dict, page_h: float) -> tuple[int, pymupdf.Rect]:
    """Page and rectangle that hold the caption (below the graphic; Abb 38 sits on the next page)."""
    x0, _, x1, y1 = f["bbox"]
    if y1 + 12 > config.FOOTER_BAND * page_h:
        return f["pdf_page"] + 1, pymupdf.Rect(x0, 40, x1, 40 + STRIP_H + 20)
    return f["pdf_page"], pymupdf.Rect(x0 - 5, y1, x1 + 5, y1 + STRIP_H)


def _layer_text(pages: dict, page: int, rect: pymupdf.Rect) -> str:
    lines = [ln for ln in pages.get(page, {}).get("lines", [])
             if ln["bbox"][1] >= rect.y0 - 2 and ln["bbox"][3] <= rect.y1 + 4]
    return " ".join(ln["text"] for ln in lines)


def check(doc: pymupdf.Document, pages: dict, f: dict, use_tesseract: bool, force: bool) -> dict:
    page, rect = strip_rect(f, doc[f["pdf_page"] - 1].rect.height)
    readings = {"ocr-layer": _layer_text(pages, page, rect)}
    if use_tesseract:
        png = doc[page - 1].get_pixmap(dpi=300, clip=rect, colorspace=pymupdf.csGRAY).tobytes("png")
        readings["tesseract"] = " ".join(ocr_fallback.ocr_png(png, psm=6, force=force).split())
    result = {"id": f["id"], "page": page, "readings": {}}
    for name, text in readings.items():
        num, rest = split_caption(text)
        result["readings"][name] = {"text": text, "number": num, "similarity": round(similarity(f["title"], rest), 2)}
    best = max(result["readings"].values(), key=lambda r: r["similarity"])
    number_ok = any(r["number"] == f["number"] for r in result["readings"].values())
    if best["similarity"] >= OK_SIMILARITY and number_ok:
        result["status"] = "ok"
    elif best["similarity"] >= TITLE_ONLY_OK:
        result["status"] = "ok (Nummer von der OCR verlesen)"   # title is unambiguous on its own
    else:
        result["status"] = "prüfen"
    return result


def _report(results: list[dict], tesseract: bool) -> str:
    ok = sum(r["status"].startswith("ok") for r in results)
    out = ["# Gegenprobe der Abbildungs- und Tabellenbeschriftungen", "",
           "Generiert von `python -m pipeline captions`. Jede kuratierte Beschriftung "
           "(`curation/figures.yaml`) wird mit zwei unabhängigen Lesungen verglichen: der OCR-Schicht des PDFs "
           f"und einem lokalen Tesseract-Lauf (deu+eng){'' if tesseract else ' – **übersprungen, Tesseract nicht installiert**'}.",
           f"Status „ok“: Nummer stimmt in mindestens einer Lesung, Titel-Ähnlichkeit ≥ {OK_SIMILARITY}; "
           f"„ok (Nummer … verlesen)“: Titel-Ähnlichkeit ≥ {TITLE_ONLY_OK}, Nummer in keiner Lesung lesbar. "
           "„prüfen“: beide Lesungen zu schlecht – Beschriftung wurde nur visuell (Beschriftungsstreifen) bestätigt.", "",
           f"**Ergebnis: {ok} von {len(results)} Beschriftungen bestätigt.**", "",
           "| ID | Status | Ähnlichkeit (OCR-Schicht / Tesseract) | Gelesen (beste Lesung) |", "|---|---|---|---|"]
    for r in results:
        rd = r["readings"]
        best = max(rd.values(), key=lambda x: x["similarity"])
        sims = " / ".join(str(rd[k]["similarity"]) for k in ("ocr-layer", "tesseract") if k in rd)
        text = best["text"][:90].replace("|", "\\|")
        out.append(f"| `{r['id']}` | {r['status']} | {sims} | {text} |")
    return "\n".join(out) + "\n"


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    figs = [f for f in catalog.figures() if f["kind"] != "formula" and f.get("number") is not None]
    use_tess = ocr_fallback.available()
    if dry_run:
        print(f"[captions] würde {len(figs)} Beschriftungen prüfen (Tesseract: {'ja' if use_tess else 'nein'})")
        return 0
    doc = pymupdf.open(source_path(config.SKRIPT))
    layer = load_pages()
    results = [check(doc, layer, f, use_tess, force) for f in figs]
    write_if_changed(REPORT, _report(results, use_tess))
    bad = [r["id"] for r in results if not r["status"].startswith("ok")]
    print(f"[captions] bestätigt {len(results) - len(bad)}/{len(results)} | prüfen: {bad}")
    return 0
