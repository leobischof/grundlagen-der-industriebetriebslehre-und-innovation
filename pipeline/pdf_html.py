"""Knowledge-base markdown → print HTML for the PDF renderer (pymupdf.Story dialect).

Why a dedicated converter instead of plain `markdown`: the content files carry YAML
frontmatter (must not be printed), HTML comments (page markers), footnotes whose printed
numbers must match the script (python-markdown would renumber them), `$$ … $$` display
formulas (rendered to images), relative image/figure links (resolved to real files; a script
picture is replaced by our SVG or a stand-in text, see `figure_publish`) and links to sibling
.md/.svg files (meaningless on paper). Each concern is one small function.
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import pymupdf
import yaml
from PIL import Image

from . import content_render, figure_publish, pdf_math, svg_mupdf
from .pdf_geometry import MAX_FIGURE_HEIGHT_PT, TEXT_WIDTH_PT

UNANCHORED_HEADING = re.compile(rf"^#{{1,6}}\s*{re.escape(content_render.UNANCHORED_HEADING)}\s*$", re.M)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
_DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
_INLINE = re.compile(r"(?<![\\$])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)")
_FN_DEF = re.compile(r"^\[\^([^\]\s]+)\]:[ \t]*(.*(?:\n(?:[ ]{2,}|\t)\S.*)*)", re.M)
_FN_REF = re.compile(r"\[\^([^\]\s]+)\](?!:)")
_IMG_PARA = re.compile(r'<p>\s*(<img [^>]*?/?>)\s*</p>')
_LINK = re.compile(r'(\s*·\s*)?<a href="([^"]*)"[^>]*>(.*?)</a>', re.S)
# sane_lists: an ordered list keeps its first number ("2. …" after a paragraph prints 2, not 1).
_EXTENSIONS = ["tables", "sane_lists"]
_TEX_SYMBOLS = {r"\cdot": "·", r"\times": "×", r"\%": "%", r"\,": " ", r"\;": " ",
                r"\leq": "≤", r"\geq": "≥", r"\approx": "≈", r"\rightarrow": "→", r"\to": "→"}


@dataclass
class Assets:
    """Binary resources referenced by the HTML (figures, formula PNGs), keyed by archive name."""
    files: dict[str, bytes] = field(default_factory=dict)
    # <img> id → height in pt of every block-level image. MuPDF's Story squeezes an image into the
    # space left on the page instead of moving it, so the layout compares these to the rendered
    # heights and forces a page break before each squeezed one (see pdf_layout.render_story).
    # Figures wrap the img in a div "<id>b" (image + caption) - that div takes the break.
    heights: dict[str, float] = field(default_factory=dict)

    def block_id(self, height_pt: float) -> str:
        key = f"fig{len(self.heights)}"
        self.heights[key] = height_pt
        return key

    def add(self, data: bytes, suffix: str = "png") -> str:
        name = f"a{hashlib.sha256(data).hexdigest()[:16]}.{suffix}"
        self.files[name] = data
        return name

    def archive(self) -> pymupdf.Archive:
        arch = pymupdf.Archive()
        for name, data in self.files.items():
            arch.add(data, name)
        return arch


@dataclass
class Converted:
    html: str
    title: str                               # frontmatter title or first heading
    problems: list[str] = field(default_factory=list)   # formula fallbacks, missing images


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, text[m.end():]
    return (meta if isinstance(meta, dict) else {}), text[m.end():]


def pages_label(printed_pages) -> str:
    """[29, 30, 31] → 'Skript S. 29–31' (the script's own page numbers, not PDF pages)."""
    pages = sorted(p for p in (printed_pages or []) if isinstance(p, int))
    if not pages:
        return ""
    return f"Skript S. {pages[0]}" if len(pages) == 1 else f"Skript S. {pages[0]}–{pages[-1]}"


def _inline_html(text: str) -> str:
    out = markdown.markdown(text.strip(), extensions=_EXTENSIONS)
    return re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)


def _footnotes_html(defs: list[tuple[str, str]], unanchored: list[tuple[str, str]]) -> str:
    def block(title: str, items: list[tuple[str, str]]) -> str:
        rows = "".join(f'<p class="fn"><sup>{html.escape(k)}</sup> {_inline_html(v)}</p>' for k, v in items)
        return f'<p class="fn-title">{title}</p>{rows}' if items else ""
    body = block("Fußnoten", defs) + block("Fußnoten ohne sicheren Textanker", unanchored)
    return f'<div class="footnotes">{body}</div>' if body else ""


def _take_footnote_defs(text: str) -> tuple[str, list[tuple[str, str]]]:
    defs = [(m.group(1), " ".join(m.group(2).split())) for m in _FN_DEF.finditer(text)]
    return _FN_DEF.sub("", text), defs


def _simple_tex(latex: str) -> str:
    """Inline `$x$` → readable italic text (images would break the line baseline in Story)."""
    for tex, char in _TEX_SYMBOLS.items():
        latex = latex.replace(tex, char)
    latex = re.sub(r"\\(?:text|mathrm|mathit)\{([^}]*)\}", r"\1", latex)
    latex = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", latex)
    latex = re.sub(r"_\{([^}]*)\}|_(\w)", lambda m: f"<sub>{html.escape(m.group(1) or m.group(2))}</sub>", latex)
    return latex.replace("{", "").replace("}", "")


class _Raw:
    """Placeholders for HTML that must survive the markdown pass untouched."""

    def __init__(self):
        self.items: list[str] = []

    def put(self, fragment: str) -> str:
        self.items.append(fragment)
        return f"@@RAW{len(self.items) - 1}@@"

    def restore(self, text: str) -> str:
        for i in range(len(self.items) - 1, -1, -1):
            text = text.replace(f"@@RAW{i}@@", self.items[i])
        return text


def _formula_html(latex: str, assets: Assets, source: str, problems: list[str]) -> str:
    images = pdf_math.render_formula(latex)
    if images is None:
        problems.append(f"{source}: Formel nicht per mathtext darstellbar, Monospace-Fallback: {latex.strip()[:70]}")
        return f'<pre class="tex">{html.escape(latex.strip())}</pre>'
    parts = []
    for img in images:
        width = min(img.width_pt, TEXT_WIDTH_PT)
        key = assets.block_id(img.height_pt * width / img.width_pt)
        parts.append(f'<div class="formula" id="{key}b"><img id="{key}" src="{assets.add(img.png)}" style="width:{width:.1f}pt"/></div>')
    return "".join(parts)


def _block_image(data: bytes, suffix: str, w: float, h: float, assets: Assets, natural: float) -> str:
    """Scale to the text width (never beyond the frame height, never enlarging below `natural`)."""
    width = min(TEXT_WIDTH_PT, max(natural, TEXT_WIDTH_PT * 0.6))
    width = min(width, MAX_FIGURE_HEIGHT_PT * w / h)
    key = assets.block_id(width * h / w)
    return f'<div class="fig" id="{key}b"><img id="{key}" src="{assets.add(data, suffix)}" style="width:{width:.1f}pt"/></div>'


def _svg_tag(path: Path, assets: Assets) -> str:
    data = svg_mupdf.for_mupdf(path.read_bytes())   # MuPDF ignores dashes, markers, <g> text props
    with pymupdf.open("svg", data) as svg:
        rect = svg[0].rect
    return _block_image(data, "svg", rect.width, rect.height, assets, natural=TEXT_WIDTH_PT)


def _stand_in_tag(fig_id: str) -> str:
    """No reconstruction yet: a framed note instead of the script's picture (figure_publish)."""
    return f'<div class="fig"><p class="stand-in">{html.escape(figure_publish.stand_in(fig_id))}</p></div>'


def _image_tag(match: re.Match, base: Path, assets: Assets, problems: list[str]) -> str:
    tag = match.group(1)
    src = html.unescape(re.search(r'src="([^"]*)"', tag).group(1))
    fig_id = figure_publish.original_id(src)
    if fig_id:                                   # a script picture: never printed itself
        svg = figure_publish.reconstruction(fig_id)
        return _svg_tag(svg, assets) if svg else _stand_in_tag(fig_id)
    path = (base / src).resolve()
    if not path.is_file():
        problems.append(f"{base.name}: Bild fehlt: {src}")
        return f'<p class="missing">[Bild nicht gefunden: {html.escape(src)}]</p>'
    if path.suffix == ".svg":
        return _svg_tag(path, assets)
    with Image.open(path) as im:
        w_px, h_px = im.size
    # 200 dpi crops: natural width is w_px*72/200 pt.
    return _block_image(path.read_bytes(), "png", w_px, h_px, assets, natural=w_px * 72 / 200)


def _attach_captions(text: str) -> str:
    """Keep a figure together with its caption (and a heading right above it) in one div, so a
    page break can never strand the heading or the caption away from the image.
    Story ignores `page-break-after: avoid`, hence the manual grouping."""
    text = re.sub(r'(<h[1-6]>(?:(?!</h).)*</h[1-6]>)\s*(<div class="fig"[^>]*>)', r'\2\1', text, flags=re.S)
    return re.sub(r'(<div class="fig"[^>]*>(?:(?!</div>).)*)</div>\s*<p>(<em>.*?)</p>',
                  r'\1<p class="caption">\2</p></div>', text, flags=re.S)


def _links(text: str) -> str:
    """Paper has no sibling files: keep the label, show external URLs, drop reconstruction links.
    An item of a " · " link list (caption lines: "… · Rekonstruktion · Zeichenübung") goes
    entirely - on paper it would be a word pointing nowhere."""
    def repl(m: re.Match) -> str:
        sep, href, label = m.group(1), html.unescape(m.group(2)), m.group(3)
        external = href.startswith(("http://", "https://"))
        if href.endswith(".svg") or (sep and not external):
            return ""
        if external and href not in label:
            return f'{sep or ""}{label} (<span class="url">{html.escape(href)}</span>)'
        return f'{sep or ""}{label}'
    text = _LINK.sub(repl, text)
    return re.sub(r"\s*·\s*(?=</p>)", "", text)


def _emphasis_classes(text: str) -> str:
    """A paragraph that is only `<sub>…</sub>` is secondary information (exam question meta):
    small print, not a lowered baseline. A paragraph opening with a bold "N. …" is a numbered
    task (question collection): it gets air above it so each task stands on its own."""
    text = re.sub(r"<p><sub>(.*?)</sub></p>", r'<p class="small">\1</p>', text, flags=re.S)
    return re.sub(r"<p><strong>(\d+\. )", r'<p class="task"><strong>\1', text)


def _wrap_tables(text: str) -> str:
    """A bare <table> that ends at a page bottom right before a heading makes MuPDF's Story emit
    blank pages forever (seen with the chapter-5 learning guide); inside a div it does not."""
    return text.replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")


def _classify_footnotes(body: str) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Body without definitions, notes in order of first reference, and notes nobody references.

    Classified by reference, not by position: it does not matter whether the unanchored notes
    sit below their heading or between the anchored ones - the heading line itself is dropped."""
    body = UNANCHORED_HEADING.sub("", body)
    body, defs = _take_footnote_defs(body)
    order: list[str] = []
    for label in _FN_REF.findall(body):
        if label not in order:
            order.append(label)
    by_label = dict(defs)
    anchored = [(label, by_label[label]) for label in order if label in by_label]
    return body, anchored, [(k, v) for k, v in defs if k not in order]


_LIST_LINE = re.compile(r"^( *)(?:[-*+]|\d+[.)]) ", re.M)
_IMAGE_LINE = re.compile(r"^(!\[[^\]]*\]\([^)]*\))[ \t]*\n(?=[^\n])", re.M)
# A paragraph line directly followed by a top-level list item (no blank line in between).
_LIST_AFTER_TEXT = re.compile(r"^((?![-*+] |\d+[.)] |\|)\S.*)\n(?=(?:[-*+]|\d+[.)]) )", re.M)


def _prepare_markdown(text: str) -> str:
    """Make the text digestible for python-markdown: a figure line is followed by its caption
    line without a blank line (→ own paragraphs), a list that follows its lead-in line without
    a blank line (GitHub renders it as a list, python-markdown as run-on text), and nested lists
    indented by 2 spaces (as most editors write them) need 4."""
    text = _IMAGE_LINE.sub(r"\1\n\n", text)
    text = _LIST_AFTER_TEXT.sub(r"\1\n\n", text)
    indents = [len(m.group(1)) for m in _LIST_LINE.finditer(text)]
    if any(i % 4 == 2 for i in indents):
        text = _LIST_LINE.sub(lambda m: " " * (len(m.group(1)) * 2) + m.group(0).lstrip(" "), text)
    return text


def _protect_math_and_refs(text: str, raw: _Raw, assets: Assets, source: str, problems: list[str]) -> str:
    """Swap formulas and footnote refs for placeholders so markdown cannot mangle `_`, `*`, `[^1]`."""
    text = _DISPLAY.sub(
        lambda m: f"\n\n{raw.put(_formula_html(m.group(1), assets, source, problems))}\n\n", text)
    text = _INLINE.sub(lambda m: raw.put(f"<i>{_simple_tex(m.group(1))}</i>"), text)
    return _FN_REF.sub(lambda m: raw.put(f'<sup class="fnref">{html.escape(m.group(1))}</sup>'), text)


def convert(text: str, source: Path, assets: Assets, heading_shift: int = 0, h1_shift: int | None = None) -> Converted:
    """One content file → HTML. `source` is the file path (relative links resolve against it).
    `h1_shift` overrides the shift of `# ` headings only (chapter overview: h1 stays, rest moves down)."""
    meta, body = split_frontmatter(text)
    anchored, defs, unanchored = _classify_footnotes(_prepare_markdown(_COMMENT.sub("", body)))
    problems: list[str] = []
    raw = _Raw()
    anchored = _protect_math_and_refs(anchored, raw, assets, source.name, problems)
    out = markdown.markdown(anchored, extensions=_EXTENSIONS)
    out = _IMG_PARA.sub(lambda m: _image_tag(m, source.parent, assets, problems), out)
    out = _wrap_tables(_emphasis_classes(_links(out)))
    out = re.sub(r"<p>(@@RAW\d+@@)</p>", r"\1", out)
    out = _shift_headings(out, heading_shift, h1_shift)
    out = _attach_captions(out)
    note = pages_label(meta.get("printed_pages"))
    if note:
        out = re.sub(r"(</h\d>)", lambda m: f'{m.group(1)}<p class="meta">{html.escape(note)}</p>', out, count=1)
    out += _footnotes_html(defs, unanchored)
    return Converted(raw.restore(out), str(meta.get("title") or ""), problems)


def _shift_headings(text: str, shift: int, h1_shift: int | None = None) -> str:
    """Shift `<hN>…</hN>` pairs by `shift` levels (cap h6); h1 uses `h1_shift` when given.
    A chapter overview's h1 stays chapter level, a section's `# 2.5` becomes h2, so bookmarks
    nest chapter > section > subsection."""
    def repl(m: re.Match) -> str:
        own = h1_shift if (m.group(1) == "1" and h1_shift is not None) else shift
        level = min(int(m.group(1)) + own, 6)
        return f"<h{level}>{m.group(2)}</h{level}>"
    return re.sub(r"<h([1-6])>(.*?)</h\1>", repl, text, flags=re.S)
