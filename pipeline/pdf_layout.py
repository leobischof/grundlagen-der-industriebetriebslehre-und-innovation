"""Page layout for the PDF renderer: CSS, HTML→pages (pymupdf.Story), title page, TOC,
running header/footer and bookmarks. Knows nothing about the knowledge base's file layout
(that is `render_pdf.py`) nor about markdown (that is `pdf_html.py`).
"""
from __future__ import annotations

import html
import io
import re
from dataclasses import dataclass

import pymupdf

from .pdf_geometry import CONTENT, PAGE
from .pdf_html import Assets

TITLE = "Grundlagen der Industriebetriebslehre und Innovation – Wissensbasis"
NOTE = ("Inoffizielle, maschinell erstellte Lernunterlage auf Basis des Skripts 2024/25 (v2.0). "
        "Keine offizielle Unterlage der TU Graz.")
TOC_MAX_LEVEL = 2                                         # chapters + sections in the printed TOC
BOOKMARK_MAX_LEVEL = 4

# Story understands a CSS subset; fonts fall back to MuPDF's built-in Nimbus Sans/Mono
# (Helvetica/Courier metrics, full Latin incl. umlauts) so output is identical on every machine.
CSS = """
body { font-family: sans-serif; font-size: 10pt; line-height: 1.35; color: #1c1c1c; }
h1, h2, h3, h4, h5, h6 { page-break-after: avoid; }
h1 { font-size: 23pt; color: #14375e; margin: 0 0 8pt 0; border-bottom: 1.5pt solid #14375e; }
h2 { font-size: 15.5pt; color: #14375e; margin: 18pt 0 4pt 0; }
h3 { font-size: 12.5pt; color: #1f4e79; margin: 12pt 0 3pt 0; }
h4 { font-size: 11pt; color: #1f4e79; margin: 9pt 0 2pt 0; }
h5, h6 { font-size: 10pt; margin: 8pt 0 2pt 0; }
p { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 6pt 0; }
li { margin: 0 0 2pt 0; }
table { border-collapse: collapse; margin: 4pt 0 8pt 0; }
th, td { border: 0.6pt solid #8a8a8a; padding: 3pt 5pt; }
th { border-bottom: 1.4pt solid #1f4e79; }   /* no background: Story repeats cell fills on the next page */
.fig { text-align: center; margin: 8pt 0 2pt 0; }
.fig h1, .fig h2, .fig h3, .fig h4, .fig h5, .fig h6 { text-align: left; }
.caption { font-size: 8.5pt; color: #444444; text-align: center; margin-bottom: 8pt; }
.stand-in { font-size: 8.5pt; color: #444444; text-align: left; border: 0.6pt dashed #9a9a9a;
            padding: 5pt 7pt; margin: 0 0 2pt 0; }
blockquote { margin: 4pt 0 10pt 0; padding: 2pt 0 2pt 8pt; border-left: 2pt solid #1f4e79; color: #333333; }
blockquote p { margin: 0 0 3pt 0; }
.task { font-size: 10.5pt; margin: 13pt 0 2pt 0; }       /* numbered exam task: the important line */
.small { font-size: 8pt; color: #666666; margin: 0 0 3pt 0; }   /* source, topic, sections of a task */
.meta { font-size: 8.5pt; color: #666666; margin: 0 0 8pt 0; }
.formula { text-align: center; margin: 6pt 0; }
.url { font-size: 8.5pt; color: #444444; }
pre { font-family: monospace; font-size: 8.5pt; background-color: #f1f1f1; padding: 4pt; margin: 4pt 0 8pt 0; }
code { font-family: monospace; font-size: 9pt; }
.footnotes { margin-top: 14pt; border-top: 0.5pt solid #999999; padding-top: 3pt; font-size: 8pt; color: #333333; }
.fn { margin: 0 0 2pt 0; }
.fn-title { font-weight: bold; margin: 2pt 0 2pt 0; }
sup { font-size: 70%; }
.title { margin-top: 200pt; text-align: center; }
.title h1 { border: none; font-size: 28pt; }
.title p { font-size: 11pt; color: #444444; }
.toc td { border: none; padding: 1.5pt 2pt; font-size: 9.5pt; }
.toc .t1 td { font-weight: bold; padding-top: 7pt; }
.toc .t2 td.name { padding-left: 14pt; }
.toc .pg { text-align: right; }
"""


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    page: int                                # 1-based page within its own document


def tag_headings(body: str) -> tuple[str, dict[str, tuple[int, str]]]:
    """Give every heading an id so `positionfn` can report its page (the text it hands
    back is mis-decoded for non-ASCII characters, ids are reliable)."""
    found: dict[str, tuple[int, str]] = {}

    def repl(m: re.Match) -> str:
        key = f"h{len(found)}"
        found[key] = (int(m.group(1)), html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip())
        return f'<h{m.group(1)} id="{key}">{m.group(2)}</h{m.group(1)}>'
    return re.sub(r"<h([1-6])>(.*?)</h\1>", repl, body, flags=re.S), found


MAX_BREAK_ROUNDS = 8
SQUEEZE_TOLERANCE_PT = 1.5        # rendered image height below `wanted - tolerance` = squeezed


# No document of this knowledge base comes near this; more pages means MuPDF is looping (it can
# emit blank pages forever, e.g. for a bare <table> ending at a page bottom before a heading -
# hence pdf_html wraps every table in a div). An error beats a renderer that never returns.
MAX_PAGES = 1500


def _layout(body: str, assets: Assets) -> tuple[pymupdf.Document, dict[str, int], dict[str, float]]:
    """One Story run. Returns the document, the page of every id'd element and its block height."""
    story = pymupdf.Story(f"<body>{body}</body>", user_css=CSS, archive=assets.archive())
    pages: dict[str, int] = {}
    heights: dict[str, float] = {}

    page = 0

    def on_position(pos) -> None:            # pymupdf insists on exactly one parameter
        if not pos.id or pos.id in pages:
            return
        if pos.heading and pos.open_close & 1:
            pages[pos.id] = page
        elif pos.id in assets.heights and pos.rect[2] - pos.rect[0] > 1:     # the image itself
            heights[pos.id] = pos.rect[3] - pos.rect[1]

    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    more = 1
    while more:                              # Story.write's own loop, with a page limit
        if page >= MAX_PAGES:
            raise RuntimeError(f"PDF-Layout bricht nach {MAX_PAGES} Seiten ab – MuPDF erzeugt Leerseiten in Schleife")
        page += 1                            # 1-based number of the page being placed
        device = writer.begin_page(PAGE)
        more, _ = story.place(CONTENT)
        story.element_positions(on_position)
        story.draw(device)
        writer.end_page()
    writer.close()
    return pymupdf.open("pdf", buf.getvalue()), pages, heights


def render_story(body: str, assets: Assets | None = None) -> tuple[pymupdf.Document, list[Heading]]:
    """HTML → paginated PDF document plus every heading with the page it landed on.

    MuPDF squeezes an image into whatever space is left on the page instead of moving it to
    the next one. Figures and formulas are therefore measured after layout; every squeezed one
    gets `page-break-before` and the story is laid out again (usually 1-3 rounds)."""
    assets = assets or Assets()
    tagged, found = tag_headings(body)
    forced: set[str] = set()
    for _ in range(MAX_BREAK_ROUNDS):
        current = tagged
        for key in forced:                       # every image sits in a wrapper div "<id>b"
            current = current.replace(f'id="{key}b"', f'id="{key}b" style="page-break-before: always"')
        doc, pages, heights = _layout(current, assets)
        squeezed = {k for k, want in assets.heights.items()
                    if k in heights and heights[k] < want - SQUEEZE_TOLERANCE_PT} - forced
        if not squeezed:
            break
        forced |= squeezed
    return doc, [Heading(lvl, text, pages.get(key, 1)) for key, (lvl, text) in found.items()]


def title_page(today: str, subtitle: str = "") -> pymupdf.Document:
    sub = f"<p><b>{html.escape(subtitle)}</b></p>" if subtitle else ""
    body = (f'<div class="title"><h1>{html.escape(TITLE)}</h1>{sub}<p>{html.escape(NOTE)}</p>'
            f"<p>Erstellt am {html.escape(today)}</p></div>")
    return render_story(body)[0]


def toc_html(entries: list[tuple[int, str, int]]) -> str:
    """entries: (level, title, page). Only levels ≤ TOC_MAX_LEVEL are printed."""
    rows = "".join(
        f'<tr class="t{lvl}"><td class="name">{html.escape(text)}</td><td class="pg">{page}</td></tr>'
        for lvl, text, page in entries if lvl <= TOC_MAX_LEVEL)
    return f'<h1>Inhaltsverzeichnis</h1><table class="toc" style="width:100%">{rows}</table>'


def bookmarks(entries: list[tuple[int, str, int]]) -> list[list]:
    """PDF outline: levels must start at 1 and never jump by more than one."""
    out: list[list] = []
    previous = 0
    for level, text, page in entries:
        if level > BOOKMARK_MAX_LEVEL:
            continue
        level = min(level, previous + 1)
        out.append([level, text, page])
        previous = level
    return out


def _running_headers(headings: list[Heading], count: int) -> list[str]:
    """Header text per page: the latest chapter/section heading that started on or before it.
    Pages carrying a chapter heading (level 1) get none - the big heading is the header."""
    result, current = [], ""
    for page in range(1, count + 1):
        starting = [h for h in headings if h.page == page and h.level <= 2]
        if starting:
            current = starting[-1].text
        result.append("" if any(h.level == 1 for h in starting) else current)
    return result


def stamp(doc: pymupdf.Document, headings: list[Heading], footer_left: str, skip: int = 0) -> None:
    """Running header (section title), rule, footer (left note, right 'Seite n von N').
    `headings` use absolute page numbers of `doc`; the first `skip` pages (title page) stay bare."""
    headers = _running_headers(headings, doc.page_count)
    css = "body { font-family: sans-serif; font-size: 7.5pt; color: #666666; }"
    for i, page in enumerate(doc):
        if i < skip:
            continue
        if headers[i]:
            page.insert_htmlbox(pymupdf.Rect(CONTENT.x0, 28, CONTENT.x1, 52), html.escape(headers[i]), css=css)
        page.draw_line((CONTENT.x0, 800), (CONTENT.x1, 800), color=(0.6, 0.6, 0.6), width=0.4)
        page.insert_htmlbox(pymupdf.Rect(CONTENT.x0, 803, CONTENT.x1 - 90, 825), html.escape(footer_left), css=css)
        number = f"Seite {i + 1} von {doc.page_count}"
        page.insert_htmlbox(pymupdf.Rect(CONTENT.x1 - 90, 803, CONTENT.x1, 825),
                            f'<div style="text-align:right">{number}</div>', css=css)
