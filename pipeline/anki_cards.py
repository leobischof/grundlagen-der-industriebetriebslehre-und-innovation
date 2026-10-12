"""Anki cards from the script's own bold print – pure text work, no genanki, no image libraries.

The script sets its key terms and key sentences in bold, and build-content carries that into
content/ as `**…**`. That is the one signal of "what matters" the script gives itself, so it
drives the automatic cards without any model call:

- a paragraph (or list) with bold phrases becomes a cloze note: each bold phrase is one gap,
  the same phrase twice is the same gap;
- a bold term that stands alone as a run-in heading ("**Modifikation**") and is followed by a
  plain paragraph becomes a question card: "Erklären Sie den Begriff …" → that paragraph.

Cards hold Markdown; anki_deck turns it into HTML. Front and back never carry a picture of the
script (see figure_publish).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import figure_publish
from .content_render import APPENDIX_HEADINGS
from .export_markdown import EXTERNAL, LINK
from .qa_markdown import split_frontmatter

# Note kinds, each its own sub-deck of a chapter (order = order in the deck list).
KINDS = {"begriff": "1 Begriffe", "luecke": "2 Lückentexte", "pruefung": "3 Prüfungsfragen",
         "skizze": "4 Abbildungen skizzieren", "studierende": "5 Karten von Studierenden (unverifiziert)"}
MEDIA_PREFIX = "gil-"         # Anki keeps all media of a collection in one folder

_PAGE = re.compile(r"<!--\s*Seite (\S+) \(PDF (\d+)\)\s*-->")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_NOTE_REF = re.compile(r"\[\^\d+\]")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_SKIP_BLOCK = re.compile(r"^(?:#|!\[|\*[^*]|\||\$\$|\[\^|---|>)")   # headings, figures, captions, tables …
MIN_CONTEXT = 4               # words outside the gaps: fewer and the gap cannot be inferred
MAX_TERM_WORDS = 6            # a longer bold-only line is a statement, not a term
MIN_TERM_ANSWER = 8          # words a definition needs at least ("Abbildung 38 dargestellt." is none)
MAX_GAPS = 8                  # more gaps in one note: the text is a bold list, every gap a guess
# A bold run that ends on one of these words is a sentence fragment ("Ziel dieses Innovationstyps
# ist"), not a term – as a gap it asks for grammar, not for knowledge.
_DANGLING = {"ist", "sind", "wird", "werden", "hat", "haben", "der", "die", "das", "den", "dem", "des",
             "und", "oder", "zu", "von", "mit", "in", "im", "auf", "für", "ein", "eine", "einer", "dass"}


@dataclass(frozen=True)
class Card:
    kind: str                 # key of KINDS
    chapter: str              # chapter slug, e.g. '02-industrielle-innovation'
    key: str                  # stable identity → note guid (re-import updates, never duplicates)
    front: str                # Markdown; a cloze note's text with {{c1::…}} gaps
    back: str = ""            # Markdown
    source: str = ""          # "Skript S. 24 (PDF 34) · 2.2 Begriffe und Definitionen"
    media: tuple[Path, ...] = field(default=())   # our SVGs the card shows


def figure_image(fig_id: str, title: str) -> tuple[str, tuple[Path, ...]]:
    """Our SVG of a figure as card Markdown plus the media file, or ("", ()) if there is none.
    Never the script's own picture (figure_publish)."""
    svg = figure_publish.reconstruction(fig_id)
    return (f"![{title}]({MEDIA_PREFIX}{svg.name})", (svg,)) if svg else ("", ())


def plain(text: str) -> str:
    """Inline Markdown of the script → card text: no footnote anchors, links keep their label."""
    text = _NOTE_REF.sub("", text)
    text = LINK.sub(lambda m: m.group(0) if EXTERNAL.match(m.group(4)) and not m.group(2) else m.group(3), text)
    return re.sub(r"[ \t]+", " ", text).strip()


@dataclass
class Block:
    text: str
    page: str                 # "S. 24 (PDF 34)"


def _heading(text: str) -> str | None:
    return text.lstrip("#").strip() if text.startswith("#") else None


def blocks(body: str) -> list[Block]:
    """Paragraphs and lists of a content file in reading order, each with the page it starts on.

    Headings, figures, captions, tables, formulas and footnote definitions are not text to learn
    from and are left out; a heading still separates a bold-only term from what follows (an
    empty block). Reading stops at the first heading the pipeline appended (footnote list,
    exam questions, contents)."""
    out, page = [], ""
    for raw in re.split(r"\n\s*\n", body):
        pages = _PAGE.findall(raw)
        text = _COMMENT.sub("", raw).strip()
        if _heading(text) in APPENDIX_HEADINGS:
            break
        if text and not _SKIP_BLOCK.match(text):
            out.append(Block(plain(text), page or (f"S. {pages[0][0]} (PDF {pages[0][1]})" if pages else "")))
        elif _heading(text) is not None:
            out.append(Block("", page))
        if pages:
            page = f"S. {pages[-1][0]} (PDF {pages[-1][1]})"
    return out


def _words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _letters(text: str) -> int:
    return sum(c.isalpha() for c in text)


def bold_only(text: str) -> str | None:
    """'**Modifikation**' / '**Die Rentabilität:**' → the phrase, if the block is nothing but one
    short bold phrase; None for a formula or a long statement."""
    m = re.fullmatch(r"\*\*(.+?)\*\*[:.]?", text)
    if not m or "**" in m.group(1) or re.search(r"[=\\]", m.group(1)):
        return None
    term = m.group(1).rstrip(":. ")
    return term if 0 < _words(term) <= MAX_TERM_WORDS and _letters(term) >= 3 else None


def cloze(text: str) -> str | None:
    """Bold phrases → {{cN::…}} gaps; None if there is nothing to ask or too little context.

    A phrase without letters (a footnote number) or ending on a function word (a fragment
    such as "Ziel dieses Innovationstyps ist") makes the whole note useless: skipped."""
    phrases: list[str] = []
    for m in _BOLD.finditer(text):
        phrase = m.group(1).strip()
        if phrase not in phrases:
            phrases.append(phrase)
    if not phrases or len(phrases) > MAX_GAPS:
        return None
    if any(_letters(p) < 3 or p.split()[-1].lower() in _DANGLING for p in phrases):
        return None
    if _words(_BOLD.sub("", text)) < MIN_CONTEXT:
        return None
    return _BOLD.sub(lambda m: f"**{{{{c{phrases.index(m.group(1).strip()) + 1}::{m.group(1).strip()}}}}}**", text)


def explains(term: str, text: str) -> bool:
    """Does the block after a bold-only line talk about that term? A quote's author set in bold
    ("**Steve Jobs**") is followed by unrelated text. Compared by word stem (5 letters), so
    "Merkmale einer Innovation" matches "Innovationen können … Merkmale …"."""
    stems = {w[:5].lower() for w in re.findall(r"\w{4,}", term)}
    return _words(text) >= MIN_TERM_ANSWER and bool(stems & {w[:5].lower() for w in re.findall(r"\w{4,}", text)})


def term_card(term: str, answer: str) -> tuple[str, str] | None:
    """Front and back for a bold-only line and the block after it, None if they do not belong together.

    A term followed by its definition asks "Erklären Sie …"; a lead-in ("Haupttreiber für die
    Planung sind", "… verfolgt 3 Ziele") followed by a list asks to complete it."""
    lead_in = term.split()[-1].lower() in _DANGLING or answer.startswith("- ") or re.search(r"\d", term)
    if lead_in and answer.startswith("- ") and _words(answer) >= 3:
        return f"Vervollständigen Sie: „{term} …“", answer
    if lead_in or not explains(term, answer):
        return None
    term = re.sub(r"^(?:Der|Die|Das) ", "", term)        # the term, not the phrase: "Die Rentabilität"
    return f"Erklären Sie den Begriff „{term}“.", answer


def section_cards(path: Path, chapter: str) -> list[Card]:
    """All bold-print cards of one content file (overview or section)."""
    meta, body, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    meta = meta or {}
    where = f"{meta.get('section') or ''} {meta.get('title', '')}".strip()
    ident = str(meta.get("id") or path.stem)
    items = blocks(body)
    cards = []
    for i, block in enumerate(items):
        if not block.text:
            continue
        source = f"Skript {block.page} · {where}" if block.page else f"Skript · {where}"
        term = bold_only(block.text)
        if term:
            nxt = items[i + 1].text if i + 1 < len(items) else ""
            sides = term_card(term, nxt) if nxt and not bold_only(nxt) else None
            if sides:
                cards.append(Card("begriff", chapter, f"{ident}:{term}", *sides, source))
            continue
        gaps = cloze(block.text)
        if gaps:
            cards.append(Card("luecke", chapter, f"{ident}:{block.text[:80]}", gaps, "", source))
    return cards
