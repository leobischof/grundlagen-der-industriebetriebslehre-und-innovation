"""Cards → Anki packages (.apkg): note models, Markdown → HTML, deck hierarchy, media.

Only the anki stage imports this module (genanki and markdown are in the `pipeline` extra).

Identity is what makes re-importing safe: the note models have fixed ids, a deck's id is
derived from its name and a note's guid from the card's kind and key. So the collection and
a single chapter's package share decks and notes – importing both, or a newer release over an
older one, updates the cards instead of duplicating them.
"""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

import genanki
import markdown

from .anki_cards import KINDS, MEDIA_PREFIX, Card
from .content_files import PREFIX, chapter_number

# Fixed ids: never change them once published, or Anki sees new note types.
CLOZE_MODEL_ID = 1_712_604_301
BASIC_MODEL_ID = 1_712_604_302
ROOT_DECK = PREFIX

CSS = """.card { font-family: Arial, sans-serif; font-size: 19px; text-align: left; color: #222; background: #fff;
  max-width: 46em; margin: 0 auto; line-height: 1.4; }
.frage { font-size: 21px; font-weight: bold; }
.cloze { font-weight: bold; color: #1565c0; }
.quelle { color: #777; font-size: 13px; margin-top: 14px; border-top: 1px solid #ddd; padding-top: 6px; }
img { max-width: 100%; height: auto; background: #fff; }
ul, ol { margin: 4px 0 10px 0; padding-left: 22px; }
.night_mode .card { color: #eee; background: #1e1e1e; }
.night_mode .cloze { color: #90caf9; }
.night_mode .quelle { color: #aaa; border-color: #444; }"""

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID, "GIL Lückentext",
    fields=[{"name": "Text"}, {"name": "Quelle"}],
    templates=[{"name": "Lücke",
                "qfmt": "{{cloze:Text}}",
                "afmt": '{{cloze:Text}}<div class="quelle">{{Quelle}}</div>'}],
    css=CSS, model_type=genanki.Model.CLOZE,
)
BASIC_MODEL = genanki.Model(
    BASIC_MODEL_ID, "GIL Frage und Antwort",
    fields=[{"name": "Vorderseite"}, {"name": "Rückseite"}, {"name": "Quelle"}],
    templates=[{"name": "Karte",
                "qfmt": '<div class="frage">{{Vorderseite}}</div>',
                "afmt": '{{FrontSide}}<hr id="answer">{{Rückseite}}<div class="quelle">{{Quelle}}</div>'}],
    css=CSS,
)

_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def html(text: str) -> str:
    """Card Markdown → HTML. Python-Markdown only starts a list after a blank line; the
    students' cards and the script often put "Ziele:" directly above "- …", so add one."""
    lines = text.splitlines()
    fixed = []
    for prev, line in zip([""] + lines, lines):
        if _LIST_ITEM.match(line) and prev.strip() and not _LIST_ITEM.match(prev) and not prev.startswith(" "):
            fixed.append("")
        fixed.append(line)
    return markdown.markdown("\n".join(fixed))


def deck_name(chapter_title: str, slug: str, kind: str) -> str:
    return f"{ROOT_DECK}::Kapitel {chapter_number(slug)} – {chapter_title}::{KINDS[kind]}"


def deck_id(name: str) -> int:
    """Stable id from the deck name (Anki needs < 2^63)."""
    return int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:15], 16)


def parent_names(names: list[str]) -> list[str]:
    """"GIL" and "GIL::Kapitel N – …" above the card decks. Importing an .apkg creates missing
    parents, restoring a .colpkg takes the collection as it is: without them the tree breaks."""
    parents = {"::".join(name.split("::")[:depth]) for name in names for depth in range(1, name.count("::") + 1)}
    return sorted(parents - set(names))


def note(card: Card) -> genanki.Note:
    tags = [f"kapitel-{chapter_number(card.chapter)}", card.kind]
    guid = genanki.guid_for("gil", card.kind, card.key)
    source = html(card.source)
    if card.kind == "luecke":
        return genanki.Note(model=CLOZE_MODEL, fields=[html(card.front), source], guid=guid, tags=tags)
    return genanki.Note(model=BASIC_MODEL, fields=[html(card.front), html(card.back), source], guid=guid, tags=tags)


def stage_media(cards: list[Card], media_dir: Path) -> list[str]:
    """Copy each SVG a card shows under the name the card refers to (MEDIA_PREFIX + file name)."""
    media_dir.mkdir(parents=True, exist_ok=True)
    staged = {}
    for path in (p for c in cards for p in c.media):
        target = media_dir / f"{MEDIA_PREFIX}{path.name}"
        if target not in staged:
            shutil.copyfile(path, target)
            staged[target] = None
    return [str(p) for p in staged]


def write_package(cards: list[Card], titles: dict[str, str], descriptions: dict[str, str],
                  target: Path, media_dir: Path) -> int:
    """One .apkg with a sub-deck per chapter and kind; returns the number of notes.
    `titles` maps a chapter slug to its title, `descriptions` a deck kind to its description."""
    decks: dict[tuple[str, int], genanki.Deck] = {}
    kind_order = list(KINDS)
    for card in cards:
        slot = (card.chapter, kind_order.index(card.kind))
        if slot not in decks:
            name = deck_name(titles[card.chapter], card.chapter, card.kind)
            decks[slot] = genanki.Deck(deck_id(name), name, description=descriptions.get(card.kind, ""))
        decks[slot].add_note(note(card))
    target.parent.mkdir(parents=True, exist_ok=True)
    names = [d.name for d in decks.values()]
    parents = [genanki.Deck(deck_id(name), name) for name in parent_names(names)]
    package = genanki.Package([*parents, *(decks[s] for s in sorted(decks))], media_files=stage_media(cards, media_dir))
    package.write_to_file(str(target))
    return len(cards)
