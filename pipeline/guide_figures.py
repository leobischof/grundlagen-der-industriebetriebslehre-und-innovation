"""The pictures of a chapter, placed into its learning guide for every export (SSOT).

The learning guides (learning/chapters/) are curated prose: they name figures ("Abbildung 35",
"Tabelle 6") but embed none. A summary without its pictures is half a summary, so the exports
(PDF, Markdown/gist) read a guide through `guide_text`, which adds every picture of the
chapter – the figures and tables its script files show:

- after the block (paragraph, whole list, table) that first names it in the explanatory part
  ("Zusammenhänge und Strukturen"), else in another content section (glossary, figure list);
- a picture named only in the learning goals, the exam focus, the typical mistakes or the
  self-test – where it would give the answer away or interrupt a list of tasks – or not named
  at all goes to a closing "Weitere Abbildungen des Kapitels" part of the figure section.

The embed links the script's PNG crop like every content file does; figure_publish then
swaps in our own SVG in each export, so the original never leaves the repository. The guide
file itself stays as written: this is a view, not an edit of curated text.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import catalog

ORIGINAL_EMBED = re.compile(r"!\[[^\]]*\]\((?:[^)\s]*/)?figures/originals/([^/)\s]+)\.png\)")
_ORIGINAL_LINK = re.compile(r"figures/originals/([^/)\s#]+)\.png")
_LABEL = re.compile(r"\b(Abbildung|Abb\.|Tabelle|Tab\.)\s*(\d+)\b")
_FULL = {"Abb.": "Abbildung", "Tab.": "Tabelle"}
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
# Sections where a picture must not appear: it would spoil a task or split a list of tasks.
NO_PICTURE_SECTIONS = ("Überblick", "Lernziele", "Prüfungsfokus", "Typische Fehler", "Selbsttest")
FIGURE_SECTION = "Abbildungen"
MAIN_SECTION = "Zusammenhänge"            # explains the figures: their first choice of place
REST_HEADING = "### Weitere Abbildungen des Kapitels"   # a heading: the PDF keeps it with the picture


def chapter_figures(files: list[Path]) -> list[str]:
    """Ids of the pictures (figures and tables, no formulas) the chapter's script files show."""
    ids: list[str] = []
    for path in files:
        for fig_id in ORIGINAL_EMBED.findall(path.read_text(encoding="utf-8")):
            if fig_id not in ids:
                ids.append(fig_id)
    return ids


def picture(fig_id: str) -> list[str]:
    """Embed plus caption, in the form content_render.figure_block gives the script files."""
    fig = catalog.figure(fig_id)
    label = catalog.figure_label(fig)
    printed = catalog.printed_page(fig["pdf_page"])
    source = f"Skript S. {printed} (PDF {fig['pdf_page']})" if printed else f"Skript PDF-Seite {fig['pdf_page']}"
    return [f"![{label}: {fig['title']}](../../figures/originals/{fig_id}.png)", "",
            f"*{label}: {fig['title']} – {source}*", ""]


def _mentions(line: str, by_label: dict[str, str]) -> list[str]:
    found = [(m.start(), by_label.get(f"{_FULL.get(m.group(1), m.group(1))} {m.group(2)}")) for m in _LABEL.finditer(line)]
    found += [(m.start(), m.group(1)) for m in _ORIGINAL_LINK.finditer(line)]
    return [fig_id for _, fig_id in sorted(found, key=lambda f: f[0]) if fig_id]


def _block_end(lines: list[str], i: int) -> int:
    """Index after the block holding line i: a heading's block is the one below it, a list
    runs on across blank lines while items or indented continuations follow."""
    if lines[i].startswith("#"):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
    in_list = i < len(lines) and bool(_LIST_ITEM.match(lines[i]))
    while True:
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
            i += 1
        nxt = i
        while nxt < len(lines) and not lines[nxt].strip():
            nxt += 1
        if not (in_list and nxt < len(lines) and (_LIST_ITEM.match(lines[nxt]) or lines[nxt].startswith("  "))):
            return i
        i = nxt


def _section(line: str) -> str | None:
    return line[3:].strip() if line.startswith("## ") else None


def embed(text: str, fig_ids: list[str]) -> str:
    """`text` (a guide, frontmatter allowed) with a picture for each of `fig_ids`."""
    head = _FRONTMATTER.match(text)
    front, lines = (head.group(0) if head else ""), text[head.end() if head else 0:].split("\n")
    wanted = [f for f in fig_ids if f not in set(ORIGINAL_EMBED.findall(text))]
    by_label = {catalog.figure_label(catalog.figure(f)): f for f in wanted}
    first: dict[str, int] = {}                # figure → line of its first mention
    main: dict[str, int] = {}                 # … within the explanatory section
    section, figure_section_end = "", None
    for i, line in enumerate(lines):
        section = _section(line) or section
        if section.startswith(FIGURE_SECTION):
            figure_section_end = i + 1
        if section.startswith(NO_PICTURE_SECTIONS):
            continue
        for fig_id in (f for f in _mentions(line, by_label) if f in by_label.values()):
            first.setdefault(fig_id, i)
            if section.startswith(MAIN_SECTION):
                main.setdefault(fig_id, i)
    after: dict[int, list[str]] = {}
    for fig_id, i in sorted({**first, **main}.items(), key=lambda f: f[1]):
        after.setdefault(_block_end(lines, i), []).append(fig_id)
    rest = [f for f in wanted if f not in first]
    if rest:
        at = _block_end(lines, figure_section_end - 1) if figure_section_end else len(lines)
        after.setdefault(at, []).append(REST_HEADING)
        after[at] += rest
    out: list[str] = []
    for i, line in enumerate(lines + [""]):
        if i in after:
            if out and out[-1].strip():
                out.append("")
            for item in after[i]:
                out += [item, ""] if item == REST_HEADING else picture(item)
        if i < len(lines):
            out.append(line)
    return front + "\n".join(out).rstrip("\n") + "\n"


def guide_text(guide: Path, chapter_files: list[Path]) -> str:
    """The guide as the exports show it: as written, plus the chapter's pictures."""
    return embed(guide.read_text(encoding="utf-8"), chapter_figures(chapter_files))
