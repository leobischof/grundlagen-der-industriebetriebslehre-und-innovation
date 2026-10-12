"""Stage "anki": every Anki card of the knowledge base → build/anki/ (release assets).

  build/anki/GIL-Anki-Karteikarten.apkg              collection: every chapter, one sub-deck per kind
  build/anki/GIL-Anki-Kapitel-N-<Titel>.apkg         the same cards, one chapter per package
  build/anki/GIL-Anki-Sammlung-ersetzt-alles.colpkg  the collection as a whole Anki collection: its
                                                     import replaces everything in Anki, hence the name
  build/anki/release-assets.tsv                      packages with labels (content_files)
  learning/flashcards/skizzieren.md                  overview of the sketch cards (committed)

Per chapter (1–9; the introduction is course organisation) the cards come from:
  1 Begriffe / 2 Lückentexte   the script's bold print (anki_cards)
  3 Prüfungsfragen             the worked exam answers, AI-written and marked so (anki_exam_cards)
  4 Abbildungen skizzieren     exam-relevant figures, our SVG or a stand-in text (anki_sketch)
  5 Karten von Studierenden    the students' decks, sorted into chapters (anki_student)

No card carries a picture of the script (figure_publish). Deck ids and note guids are the same
in the collection and the chapter packages, so importing both never duplicates a card.
Cached by the hash of every input: a second run with unchanged inputs writes nothing.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import anki_package, config, content_files
from .anki_cards import KINDS, Card, section_cards
from .anki_exam_cards import solution_cards
from .anki_sketch import OVERVIEW, overview_md, sketches
from .anki_student import ChapterIndex, deck_cards
from .cache import dump_json, key_for, sha256_file, write_if_changed

OUT_DIR = config.BUILD / "anki"
STAMP = config.STAMPS / "anki.json"
VERSION = 2                       # bump after changing card layout or selection
FLASHCARDS = config.LEARNING / "flashcards"
EXERCISES = config.LEARNING / "exercises"
DESCRIPTIONS = {
    "begriff": "Begriffe, die das Skript fett hervorhebt, mit der Erklärung aus dem Skript.",
    "luecke": "Lückentexte: jede Lücke ist eine Stelle, die das Skript fett setzt.",
    "pruefung": "Prüfungsfragen mit Musterlösung. Die Fragen stammen aus Studierenden-Quellen, die "
                "Lösungen sind KI-erstellt und nicht geprüft – im Zweifel gilt das Skript.",
    "skizze": "Prüfungsrelevante Abbildungen skizzieren. Rückseite: unsere eigene Nachzeichnung oder eine "
              "Beschreibung – nie das Bild des Skripts.",
    "studierende": "Karten aus Anki-Decks von Studierenden, automatisch einem Kapitel zugeordnet. Nicht vom "
                   "Lehrstuhl geprüft und nicht gegen das Skript verifiziert.",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _chapters() -> list[content_files.ChapterFiles]:
    return [c for c in content_files.discover(config.CONTENT) if content_files.chapter_number(c.slug) > 0]


def _student_decks() -> list[Path]:
    return sorted(p for p in FLASHCARDS.glob("*.json"))


def build() -> tuple[list[Card], list, dict[str, bool]]:
    """All cards in chapter and kind order, the sketches (for the overview) and, per student
    deck, whether it was sorted as an ordered deck."""
    chapters = _chapters()
    slugs = [c.slug for c in chapters]
    questions = {q["id"]: q for q in _json(config.EXAMS / "questions.json")["questions"]}
    cards: list[Card] = []
    for chapter in chapters:
        for path in chapter.files:
            cards += section_cards(path, chapter.slug)
        solutions = EXERCISES / f"{chapter.slug}-musterloesungen.md"
        if solutions.is_file():
            cards += solution_cards(solutions, chapter.slug, questions)
    sketched = sketches(_json(config.FIG_MANIFEST)["figures"], _json(config.EXAMS / "topic-mapping.json")["by_figure"],
                        list(questions.values()), {c.slug[:2]: c.slug for c in chapters})
    cards += [s.card() for s in sketched]
    index = ChapterIndex(["\n".join(p.read_text(encoding="utf-8") for p in c.files) for c in chapters])
    ordered = {}
    for path in _student_decks():
        deck = _json(path)
        found, ordered[deck["deck"]] = deck_cards(deck, slugs, index)
        cards += found
    kinds = list(KINDS)
    cards.sort(key=lambda c: (slugs.index(c.chapter), kinds.index(c.kind)))    # stable: reading order inside
    return cards, sketched, ordered


def _inputs_key() -> str:
    chapters = _chapters()
    files = [*(p for c in chapters for p in c.files), *sorted(EXERCISES.glob("*.md")), *_student_decks(),
             config.FIG_MANIFEST, config.EXAMS / "questions.json", config.EXAMS / "topic-mapping.json",
             *sorted(config.FIGURE_META_DIR.glob("*.yaml")), *sorted(config.FIG_RECONSTRUCTED.glob("*.svg")),
             *sorted(Path(__file__).parent.glob("anki_*.py"))]
    return key_for(VERSION, *(f"{p.name}:{sha256_file(p)}" for p in files))


def _targets() -> list[tuple[str, str, str | None]]:
    """(file name, label, chapter slug or None for the collection) of every package."""
    out = [(f"{content_files.ANKI_COMPLETE.stem}.apkg", f"{content_files.ANKI_COMPLETE.label} – alle Kapitel", None),
           # genanki writes the legacy package layout (collection.anki2 + media), which Anki also
           # reads as a collection package: the same writer serves .apkg and .colpkg.
           (f"{content_files.ANKI_PROFILE.stem}.colpkg", content_files.ANKI_PROFILE.label, None)]
    for c in _chapters():
        name = content_files.anki_export(c.slug, c.title)
        out.append((f"{name.stem}.apkg", name.label, c.slug))
    return out


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    key = _inputs_key()
    targets = _targets()
    stamp = _json(STAMP) if STAMP.exists() else {}
    if not force and stamp.get("key") == key and all((OUT_DIR / t[0]).exists() for t in targets) and OVERVIEW.exists():
        print(f"[anki] {stamp.get('cards')} Karten, unverändert (Cache)")
        return 0
    cards, sketched, ordered = build()
    if dry_run:
        print(f"[anki] würde {len(cards)} Karten in {len(targets)} Pakete nach {OUT_DIR.relative_to(config.ROOT)} schreiben")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    keep = {t[0] for t in targets} | {content_files.ASSET_LIST}
    for stale in [p for p in OUT_DIR.iterdir() if p.is_file() and p.name not in keep]:
        stale.unlink()                       # renamed chapter or old package: must not be released
    titles = {c.slug: c.title for c in _chapters()}
    media = OUT_DIR / "media"
    for name, _, slug in targets:
        chosen = [c for c in cards if slug is None or c.chapter == slug]
        anki_package.write_package(chosen, titles, DESCRIPTIONS, OUT_DIR / name, media)
    content_files.write_asset_list(OUT_DIR, [(name, label) for name, label, _ in targets])
    changed = write_if_changed(OVERVIEW, overview_md(sketched))
    dump_json(STAMP, {"key": key, "cards": len(cards)})
    _report(cards, ordered, changed)
    return 0


def _report(cards: list[Card], ordered: dict[str, bool], overview_changed: bool) -> None:
    per = Counter((content_files.chapter_number(c.chapter), c.kind) for c in cards)
    print(f"[anki] {len(cards)} Karten → {OUT_DIR.relative_to(config.ROOT)} (Sammlung + je Kapitel)"
          f"{', Skizzier-Übersicht aktualisiert' if overview_changed else ''}")
    for n in sorted({n for n, _ in per}):
        print(f"  Kapitel {n}: " + ", ".join(f"{KINDS[k]} {per[(n, k)]}" for k in KINDS if per[(n, k)]))
    print("  Studierenden-Decks: " + ", ".join(f"{d} ({'Reihenfolge' if o else 'je Karte'})" for d, o in ordered.items()))
