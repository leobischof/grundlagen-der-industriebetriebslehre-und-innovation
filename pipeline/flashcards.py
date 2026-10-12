"""Stage "flashcards": Anki decks -> learning/flashcards/<deck>.json + <deck>.md.

The three decks in sources/original-pdfs/anki/ were made by students. They are useful
for drill but nobody has checked them against the script, so every card carries
`trust: unverified-student` and every output file a German disclaimer. Only text is
exported: HTML is flattened, images are dropped (not copied - the originals are
git-ignored and must never be published) and the card is flagged `had_image` so a
learner knows the original card had a picture.

Cached by the SHA-256 of each .apkg: unchanged package + existing outputs = skipped.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from . import apkg_reader, config
from .cache import dump_json, key_for, sha256_file, write_if_changed

OUT_DIR = config.LEARNING / "flashcards"
STAMP = config.STAMPS / "flashcards.json"
VERSION = 1      # bump to re-export everything after changing the rendering below
TRUST = "unverified-student"
DISCLAIMER = ("Diese Karten stammen aus Anki-Decks von Studierenden. Sie sind nicht vom Lehrstuhl geprüft "
              "und nicht gegen das Skript verifiziert und können Fehler oder veraltete Inhalte enthalten. "
              "Im Zweifel gilt das Skript (`content/`).")

_IMG = re.compile(r"<img\b[^>]*>", re.I)
_SOUND = re.compile(r"\[sound:[^\]]*\]")
_BREAK = re.compile(r"<\s*(?:br\s*/?|/div|/p|/ul|/ol|/tr|/h[1-6])\s*>", re.I)
_ITEM = re.compile(r"<\s*li\b[^>]*>", re.I)
_TAG = re.compile(r"<[^>]+>")
_CLOZE = re.compile(r"\{\{c\d+::(.*?)(?:::(.*?))?\}\}", re.S)


def clean(text: str) -> tuple[str, bool]:
    """Plain text of an Anki field and whether it contained an image."""
    had_image = bool(_IMG.search(text))
    text = _SOUND.sub("", _IMG.sub("", text))
    text = _ITEM.sub("\n- ", _BREAK.sub("\n", text))
    text = html.unescape(_TAG.sub("", text)).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip(), had_image


def _front_back(fields: tuple[str, ...]) -> tuple[str, str]:
    """Basic notes: field 1 is the front, field 2 the back (extra fields join the back).
    Cloze notes: hide the answer on the front, show it on the back."""
    if _CLOZE.search(fields[0]):
        return (_CLOZE.sub(lambda m: f"[{m.group(2) or '...'}]", fields[0]),
                _CLOZE.sub(lambda m: m.group(1), fields[0]))
    return fields[0], "<br>".join(f for f in fields[1:] if f.strip())


def build_cards(deck: str, source_id: str, notes: list[apkg_reader.RawNote]) -> list[dict]:
    cards = []
    for n, note in enumerate(notes, 1):
        raw_front, raw_back = _front_back(note.fields)
        front, img_front = clean(raw_front)
        back, img_back = clean(raw_back)
        if not front and not back:
            continue          # an image-only card has nothing left to show as text
        cards.append({"id": f"{deck}-{n:03d}", "front": front, "back": back, "tags": list(note.tags),
                      "had_image": img_front or img_back, "trust": TRUST, "source": source_id})
    return cards


def _side(label: str, text: str) -> str:
    """One card side; multi-line text (lists) starts on its own line so Markdown renders it."""
    return f"**{label}:**\n\n{text}" if "\n" in text else f"**{label}:** {text}"


def deck_md(deck: str, title: str, cards: list[dict]) -> str:
    out = [f"# Karteikarten: {title}", "", f"> **Nicht verifiziert (`{TRUST}`):** {DISCLAIMER}", "",
           f"{len(cards)} Karten aus dem Anki-Deck `{deck}`. Bilder der Original-Karten sind nicht übernommen "
           "(Kennzeichen „Bild im Original“).", ""]
    for c in cards:
        mark = " *(Bild im Original)*" if c["had_image"] else ""
        out += [f"## {c['id']}{mark}", "", _side("Vorderseite", c["front"]), "",
                _side("Rückseite", c["back"]), ""]
        if c["tags"]:
            out += [f"*Tags: {', '.join(c['tags'])}*", ""]
    return "\n".join(out).rstrip() + "\n"


def _decks() -> list[tuple[str, str, Path]]:
    """(deck name, source id, canonical .apkg path) for every flashcard source (SSOT: config.SOURCES)."""
    return [(canonical.rsplit("/", 1)[-1].removesuffix(".apkg"), sid, config.ORIGINALS_DIR / canonical)
            for sid, (_, canonical, kind, _) in config.SOURCES.items() if kind == "flashcards"]


def _export(deck: str, source_id: str, apkg: Path) -> tuple[int, bool]:
    notes, deck_names = apkg_reader.read(apkg)
    cards = build_cards(deck, source_id, notes)
    title = ", ".join(deck_names) or deck
    payload = {"deck": deck, "title": title, "source": source_id, "trust": TRUST,
               "disclaimer": DISCLAIMER, "count": len(cards), "cards": cards}
    changed = dump_json(OUT_DIR / f"{deck}.json", payload)
    changed |= write_if_changed(OUT_DIR / f"{deck}.md", deck_md(deck, title, cards))
    return len(cards), changed


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    stamps = json.loads(STAMP.read_text(encoding="utf-8")) if STAMP.exists() else {}
    status = 0
    for deck, source_id, apkg in _decks():
        if not apkg.exists():
            print(f"[flashcards] {deck}: {apkg.name} fehlt in {config.ORIGINALS_DIR.relative_to(config.ROOT)}/ - übersprungen")
            status = 1
            continue
        key = key_for(sha256_file(apkg), VERSION)
        done = (OUT_DIR / f"{deck}.json").exists() and (OUT_DIR / f"{deck}.md").exists()
        if not force and done and stamps.get(deck) == key:
            print(f"[flashcards] {deck}: unverändert (Cache)")
            continue
        if dry_run:
            print(f"[flashcards] {deck}: würde exportiert")
            continue
        n, changed = _export(deck, source_id, apkg)
        stamps[deck] = key
        print(f"[flashcards] {deck}: {n} Karten, {'geschrieben' if changed else 'Ausgabe unverändert'}")
    if not dry_run:
        dump_json(STAMP, stamps)
    return status
