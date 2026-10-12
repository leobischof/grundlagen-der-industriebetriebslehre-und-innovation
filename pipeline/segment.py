"""Turn the OCR layer into an ordered stream of content items, assigned to TOC entries.

Per page: drop everything that is not running text (header/footer bands, the
inside of curated figures/tables/formula boxes, figure captions), turn located
headings into heading items, clean the rest into paragraphs (textclean), anchor
footnote markers (footnotes) and insert figure/formula items where the graphic
sits. Every item is then assigned to the TOC entry whose heading precedes it.
The result is still layout-free data; build_content renders it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import catalog, footnotes, outline, textclean
from .catalog import Entry
from .textclean import Block

FIGURE_PAD = 3.0               # pt around a curated bbox that still counts as "inside"
CAPTION_REACH = 45.0           # pt below a graphic in which its caption starts
CAPTION_LINE_GAP = 16.0        # pt between caption lines
# "Abbildung 12:" and its OCR variants ("Ahbildung", "\bhildung", "bbilduneg", "78*").
CAPTION = re.compile(r"^[\W\d]{0,3}(?:A?b?b?ildung|ildung|Abb\w*|Tab\w*|abelle|[A\\]?[bh]{1,2}i?l?d\w{0,4})"
                     r"\s*[\dIıl|]{1,3}\s*[:.;*]", re.I)


@dataclass
class Item:
    kind: str                  # heading | paragraph | bullet | numbered | subheading | figure | formula
    page: int
    y: float
    text: str = ""
    entry: Entry | None = None
    figure_id: str | None = None
    pages: set[int] = field(default_factory=set)
    notes: list[int] = field(default_factory=list)   # footnotes anchored in a caption or heading


@dataclass
class Document:
    items: list[Item]
    notes: footnotes.FootnoteIndex
    removed_captions: int = 0
    dropped_grey: list[tuple[int, str]] = field(default_factory=list)   # figure labels outside a bbox


def _inside(bbox, box, pad: float = FIGURE_PAD) -> bool:
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return box[0] - pad <= cx <= box[2] + pad and box[1] - pad <= cy <= box[3] + pad


def _caption_lines(lines: list[dict], graphics: list[dict]) -> list[list[int]]:
    """Caption line groups: a "Abbildung N:" line below a graphic (or at the top of the
    page after one that ends a page) plus its continuation lines."""
    out: list[list[int]] = []
    order = sorted(range(len(lines)), key=lambda i: lines[i]["bbox"][1])
    taken: set[int] = set()
    for pos, i in enumerate(order):
        ln = lines[i]
        if i in taken or not CAPTION.match(_row_text(lines, ln)):
            continue
        near = any(0 <= ln["bbox"][1] - g["bbox"][3] <= CAPTION_REACH for g in graphics) or ln["bbox"][1] < 100
        if not near and ln["ink"] == "black":
            continue
        group = [i]
        last_y = ln["bbox"][1]
        for j in order[pos + 1:]:
            nxt = lines[j]
            if nxt["bbox"][1] - last_y > CAPTION_LINE_GAP or nxt["ink"] == "black" and nxt["size"] > 10:
                break
            group.append(j)
            last_y = nxt["bbox"][1]
        taken.update(group)
        out.append(group)
    return out


def _row_text(lines: list[dict], ln: dict) -> str:
    """Text of the whole visual row of `ln` – the OCR often splits "Abbildung" from "35: Titel"."""
    row = sorted((o for o in lines if abs(o["bbox"][1] - ln["bbox"][1]) < textclean.ROW_TOLERANCE
                  and o["bbox"][0] >= ln["bbox"][0]), key=lambda o: o["bbox"][0])
    return " ".join(o["text"].strip() for o in row).strip()


def _caption_owner(y: float, graphics: list[dict]) -> str | None:
    """The graphic a caption at height y belongs to: the nearest one ending above it."""
    above = [g for g in graphics if g["kind"] != "formula" and g["bbox"][3] <= y + 2]
    return max(above, key=lambda g: g["bbox"][3])["id"] if above else None


def _anchor(rows, items: list[Item], caption_groups, lines, headings, graphics, notes) -> None:
    """Anchor footnote markers in body rows, captions and headings, all in reading order.

    Captions and headings are not part of the cleaned text, so a marker found
    there is stored on the figure or heading item instead (`Item.notes`).
    """
    slots = [(r.y, "row", r) for r in rows]
    for group in caption_groups:
        y = lines[group[0]]["bbox"][1]
        owner = _caption_owner(y, graphics)
        fig = next((it for it in items if it.figure_id and it.figure_id == owner), None)
        if fig is not None:
            slots.append((y, "item", (fig, " ".join(lines[k]["text"].strip() for k in group))))
    for it in items:
        if it.kind == "heading":
            idx = [k for k, e in headings.items() if e is it.entry]
            slots.append((it.y, "item", (it, " ".join(lines[k]["text"].strip() for k in sorted(idx)))))
    slots.sort(key=lambda s: s[0])
    texts = [s[2].text if s[1] == "row" else s[2][1] for s in slots]
    for (y, kind, ref), text in zip(slots, footnotes.anchor_page(texts, notes)):
        if kind == "row":
            ref.text = text
        else:
            ref[0].notes += [int(n) for n in re.findall(r"\[\^(\d+)\]", text)]


def _heading_lines(page: int) -> dict[int, Entry]:
    """{line index: entry} for headings located on this page (wrapped headings use two lines)."""
    out = {}
    for loc in outline.located():
        if loc.page == page and loc.line_index is not None:
            for k in range(loc.lines_used):
                out[loc.line_index + k] = loc.entry
    return out


def page_items(rec: dict, notes: list[footnotes.Footnote], doc: Document) -> list[Item]:
    page = rec["page"]
    lines = rec["lines"]
    graphics = [f for f in catalog.figures() if f["pdf_page"] == page]
    # The script repeats a few figures; the repeat is shown again under the original's id.
    graphics += [{**catalog.figure(d["duplicate_of"]), "bbox": d["bbox"], "pdf_page": page}
                 for d in catalog.duplicates() if d["pdf_page"] == page]
    headings = _heading_lines(page)
    caption_groups = _caption_lines([ln if ln["band"] == "body" else {**ln, "text": ""} for ln in lines], graphics)
    captions = {i for g in caption_groups for i in g}
    doc.removed_captions += len(captions)
    items: list[Item] = []
    seen_entries = set()
    for i, entry in headings.items():
        if entry.number not in seen_entries:
            seen_entries.add(entry.number)
            items.append(Item("heading", page, lines[i]["bbox"][1], entry.title, entry, pages={page}))
    body = [ln for i, ln in enumerate(lines)
            if ln["band"] == "body" and i not in headings and i not in captions
            and not any(_inside(ln["bbox"], g["bbox"]) for g in graphics)]
    # The scan prints running text black; grey lines are captions or figure labels that
    # stick out of a bbox. They never belong to the cleaned text.
    doc.dropped_grey += [(page, ln["text"]) for ln in body if ln["ink"] == "grey"]
    body = [ln for ln in body if ln["ink"] != "grey"]
    rows = textclean.to_rows(body, page)
    for g in graphics:
        items.append(Item("formula" if g["kind"] == "formula" else "figure", page, g["bbox"][1],
                          g.get("latex", ""), figure_id=g["id"], pages={page}))
    _anchor(rows, items, caption_groups, lines, headings, graphics, notes)
    # Rows are split at headings and graphics so no paragraph runs across them.
    cuts = sorted(it.y for it in items)
    margin = min((r.x0 for r in rows), default=66.0)
    pitch = textclean.line_pitch(rows)
    run: list = []
    for row in rows + [None]:
        if row is None or (run and any(run[-1].y < c <= row.y for c in cuts)):
            for b in textclean.blocks_from_rows(run, margin, pitch):
                items.append(Item(b.kind, b.page, b.y, b.text, pages=b.pages))
            run = []
        if row is not None:
            run.append(row)
    return sorted(items, key=lambda it: it.y)


def _assign(items: list[Item]) -> None:
    current: Entry | None = None
    for it in items:
        if it.kind == "heading":
            current = it.entry
        else:
            it.entry = current


def _merge_page_breaks(items: list[Item]) -> list[Item]:
    """Re-join paragraphs that a page break split (figures in between stay after the paragraph)."""
    out: list[Item] = []
    for it in items:
        prev_text = next((o for o in reversed(out) if o.kind not in ("figure", "formula")), None)
        if (prev_text is not None and it.kind == "paragraph" and it.page == prev_text.page + 1
                and prev_text.entry is it.entry and _is_first_text_on_page(it, items)
                and textclean.continues(Block(prev_text.kind, prev_text.page, prev_text.y, prev_text.text),
                                        Block(it.kind, it.page, it.y, it.text))):
            prev_text.text = textclean.join_lines(prev_text.text, it.text)
            prev_text.pages |= it.pages
            continue
        out.append(it)
    return out


def _is_first_text_on_page(it: Item, items: list[Item]) -> bool:
    first = next((o for o in items if o.page == it.page and o.kind not in ("figure", "formula")), None)
    return first is it


def build() -> Document:
    from .extract_text import load_pages      # local import: keeps CI-only stages free of pymupdf
    pages = load_pages()
    skipped = set(catalog.skipped_pages())
    doc = Document(items=[], notes=footnotes.parse(pages, skipped))
    for pno in sorted(pages):
        if pno in skipped:
            continue
        doc.items += page_items(pages[pno], doc.notes.by_page.get(pno, []), doc)
    _assign(doc.items)
    doc.items = _merge_page_breaks(doc.items)
    for it in doc.items:
        if it.kind not in ("figure", "formula", "heading"):
            it.text = textclean.correct(it.text, it.pages)
    return doc
