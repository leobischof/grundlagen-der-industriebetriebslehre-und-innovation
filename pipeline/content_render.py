"""Markdown rendering of segmented items (segment.Item) for the cleaned layer in content/.

Pure functions, no file access except "does this figure file exist?" (for links).
build_content decides *which* items go into which file; this module decides how
they look: headings by TOC level, list items, figure blocks with caption and
source page, display formulas, page markers and footnotes. The format is the
contract in docs/architecture.md – render_pdf and the QA checks parse it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from . import catalog, config
from .catalog import Entry
from .footnotes import Footnote
from .segment import Item

LIST_KINDS = ("bullet", "numbered")
_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_REF = re.compile(r"\[\^(\d+)\]")
# Line starts that markdown would read as structure although the OCR text is prose.
_BLOCK_START = re.compile(r"^(#|>|[-+] |\d{1,3}[.)] )")
_LONE_STAR = re.compile(r"(?<!\*)\*(?!\*)")


@dataclass
class Rendered:
    """Body markdown of one file plus what it references (for frontmatter and footnotes)."""
    lines: list[str] = field(default_factory=list)
    refs: list[int] = field(default_factory=list)          # footnote numbers in order of first use
    figures: list[str] = field(default_factory=list)       # figure/table/formula ids in order
    pages: set[int] = field(default_factory=set)


def slugify(text: str) -> str:
    """"Arten der Innovation" -> "arten-der-innovation" (ASCII, stable across platforms)."""
    s = text.lower().translate(_UMLAUTS)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def section_filename(entry: Entry) -> str:
    return f"{entry.number}-{slugify(entry.title)}.md"


def page_label(pdf_page: int) -> str:
    printed = catalog.printed_page(pdf_page)
    return f"Seite {printed} (PDF {pdf_page})" if printed else f"PDF-Seite {pdf_page}"


def heading_text(entry: Entry) -> str:
    """Curated wording, not the OCR line: headings are the one place we trust the TOC more."""
    if entry.kind == "frontmatter":
        return entry.title.capitalize() if entry.title.isupper() else entry.title
    return f"{entry.number} {entry.title}"


def escape(text: str, kind: str) -> str:
    """Keep OCR prose from turning into markdown structure (stray "*", "<", "# …")."""
    text = text.replace("<", "&lt;")
    text = _LONE_STAR.sub(r"\*", text)
    if kind in ("paragraph", "subheading") and _BLOCK_START.match(text):
        text = "\\" + text
    return text


def frontmatter(meta: dict) -> str:
    """YAML frontmatter: scalars and lists on one line each, nested mappings as blocks."""
    out = ["---"]
    for key, value in meta.items():
        if isinstance(value, dict):
            out.append(f"{key}:")
            out += [f"  {k}: {_scalar(v)}" for k, v in value.items()]
        elif isinstance(value, list):
            out.append(f"{key}: {_flow(value)}")
        else:
            out.append(f"{key}: {_scalar(value)}")
    return "\n".join(out + ["---", ""])


def _scalar(value) -> str:
    return yaml.safe_dump(value, allow_unicode=True, width=10**6).removesuffix("\n...\n").strip()


def _flow(values: list) -> str:
    return yaml.safe_dump(values, default_flow_style=True, allow_unicode=True, width=10**6).strip()


def _note_refs(numbers: list[int]) -> str:
    return "".join(f"[^{n}]" for n in numbers)


def figure_block(item: Item, notes: list[int]) -> list[str]:
    """Image (or display formula) plus a caption line naming the source page and extra layers."""
    fig = catalog.figure(item.figure_id)
    fid = fig["id"]
    label = catalog.figure_label(fig)
    source = f"Skript {page_label(item.page).replace('Seite', 'S.')}"
    original = f"../../figures/originals/{fid}.png"
    links = []
    if (config.FIG_RECONSTRUCTED / f"{fid}.svg").exists():
        links.append(f"[Rekonstruktion](../../figures/reconstructed/{fid}.svg)")
    if (config.DRAWING_GUIDES / config.drawing_guide_name(fid)).exists():
        links.append(f"[Zeichenübung](../../learning/drawing-exercises/{config.drawing_guide_name(fid)})")
    if fig["kind"] == "formula":
        body = ["$$", item.text or fig.get("latex", ""), "$$", ""]
        links.insert(0, f"[Original]({original})")
    else:
        body = [f"![{label}: {fig['title']}]({original})", ""]
    caption = f"*{label}: {fig['title']} – {source}*{_note_refs(notes)}"
    return body + [" · ".join([caption, *links]), ""]


def _block(item: Item, heading_level: int) -> list[str]:
    if item.kind == "heading":
        level = max(1, min(item.entry.level - heading_level + 1, 3))
        return ["#" * level + " " + heading_text(item.entry) + _note_refs(item.notes), ""]
    text = escape(item.text, item.kind)
    if item.kind == "subheading":
        return [f"**{text}**", ""]
    if item.kind == "bullet":
        return [f"- {text}"]
    if item.kind == "numbered":
        return [text]
    return [text, ""]


def render_items(items: list[Item], heading_level: int = 2) -> Rendered:
    """Markdown for a run of items. `heading_level` is the TOC level that becomes `#`."""
    out = Rendered()
    page = None
    previous = None
    for it in items:
        out.pages |= it.pages | {it.page}
        if it.page != page:
            _end_list(out.lines)
            out.lines += [f"<!-- {page_label(it.page)} -->", ""]
            page = it.page
        if previous in LIST_KINDS and it.kind != previous:
            _end_list(out.lines)
        if it.kind in ("figure", "formula"):
            _end_list(out.lines)
            out.lines += figure_block(it, it.notes)
            if it.figure_id not in out.figures:
                out.figures.append(it.figure_id)
            refs = it.notes
        else:
            block = _block(it, heading_level)
            out.lines += block
            refs = [int(n) for n in _REF.findall("\n".join(block))]
        out.refs += [n for n in refs if n not in out.refs]
        previous = it.kind
    _end_list(out.lines)
    return out


def _end_list(lines: list[str]) -> None:
    """A list ends with a blank line; consecutive list items stay together."""
    if lines and lines[-1] != "":
        lines.append("")


def footnote_section(refs: list[int], unanchored: list[Footnote], by_number: dict[int, Footnote]) -> list[str]:
    """Footnote definitions for every reference, then the notes without a reliable anchor."""
    out: list[str] = []
    for n in refs:
        note = by_number.get(n)
        if note is not None:
            out.append(f"[^{n}]: {escape(note.text, 'footnote')}")
    if out:
        out.append("")
    if unanchored:
        out += ["## Fußnoten ohne sicheren Textanker", "",
                "Diese Fußnoten stehen auf den Seiten dieses Abschnitts, ihr Verweiszeichen im Text "
                "ließ sich aus dem Scan aber nicht eindeutig zuordnen (oft Quellenangaben zu Abbildungen).", ""]
        out += [f"- **{n.number}** – {page_label(n.page)}: {escape(n.text, 'footnote')}" for n in unanchored]
        out.append("")
    return out
