"""Stage "anki": Anki deck "Abbildungen skizzieren" -> build/anki/ + learning/flashcards/skizzieren.md.

One card per exam-relevant figure of the script: the front asks to sketch it, the back
shows the original crop from figures/originals/ plus the curated "must know" points and
the exam questions that asked for it. Exam-relevant means a figure (not a table or a
formula box) that an exam question maps to (exams/topic-mapping.json by_figure) or whose
curated metadata rates it "hoch"/"mittel".

The .apkg holds crops of the script, so it goes to build/ (git-ignored) and is published
only as an asset of the private repository's release. The Markdown overview in learning/
links the same crops and is committed. Cached by the hash of every input: a second run
with unchanged inputs writes nothing.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import genanki
import yaml

from . import config
from .cache import dump_json, key_for, sha256_file, write_if_changed
from .content_render import page_label

OUT_DIR = config.BUILD / "anki"
APKG = OUT_DIR / "industriebetriebslehre-abbildungen-skizzieren.apkg"
OVERVIEW = config.LEARNING / "flashcards" / "skizzieren.md"
STAMP = config.STAMPS / "anki.json"
VERSION = 1                       # bump after changing card layout or selection
RELEVANT = ("hoch", "mittel")
DECK_NAME = "Industriebetriebslehre::Abbildungen skizzieren"
# Fixed ids: Anki recognises a re-imported deck/model as the same one and updates it
# instead of creating a duplicate. Never change them once published.
DECK_ID = 1_712_604_215
MODEL_ID = 1_712_604_216
MEDIA_PREFIX = "gib-skizze-"      # Anki media share one namespace per collection

CSS = """.card { font-family: Arial, sans-serif; font-size: 18px; text-align: left; color: #222; background: #fff; }
.prompt { font-size: 22px; font-weight: bold; margin-bottom: 6px; }
.meta { color: #666; font-size: 14px; }
.figure img { max-width: 100%; height: auto; border: 1px solid #ccc; margin: 8px 0; }
ul { margin: 4px 0 10px 18px; padding: 0; }
.night_mode .card { color: #eee; background: #1e1e1e; }
.night_mode .meta { color: #aaa; }"""

MODEL = genanki.Model(
    MODEL_ID, "GIB Abbildung skizzieren",
    fields=[{"name": "Id"}, {"name": "Prompt"}, {"name": "Meta"}, {"name": "Image"},
            {"name": "MustKnow"}, {"name": "Questions"}],
    templates=[{
        "name": "Skizze",
        "qfmt": '<div class="prompt">{{Prompt}}</div><div class="meta">{{Meta}}</div>',
        "afmt": ('{{FrontSide}}<hr id="answer"><div class="figure">{{Image}}</div>'
                 '{{#MustKnow}}<b>Das musst du können</b>{{MustKnow}}{{/MustKnow}}'
                 '{{#Questions}}<b>Gefragt in Prüfungen (Studierenden-Quellen, unverifiziert)</b>'
                 '{{Questions}}{{/Questions}}'),
    }],
    css=CSS,
    sort_field_index=0,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _meta(fid: str) -> dict:
    path = config.FIGURE_META_DIR / f"{fid}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def select(figures: list[dict], by_figure: dict) -> list[dict]:
    """Figures (no tables, no formulas) that an exam asked for or that are curated as relevant."""
    return [f for f in figures
            if f["kind"] == "figure" and (f["id"] in by_figure or f.get("exam_relevance") in RELEVANT)]


def _date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def card(fig: dict, meta: dict, questions: list[dict]) -> dict:
    """Everything one card shows, as plain data (used for the .apkg and the Markdown overview)."""
    source = "Skript " + page_label(fig["pdf_page"]).replace("Seite", "S.")
    return {
        "id": fig["id"],
        "prompt": f"Skizziere: {fig['title']}",
        "meta": f"{fig['label']} · Abschnitt {fig['subsection'] or fig['section']} · {source}",
        "image": Path(fig["files"]["original"]).name,
        "must_know": list((meta.get("drawing") or {}).get("must_know") or []),
        "questions": [f"{_date(q['date'])}: {q['wording']}" for q in questions],
        "chapter": fig["chapter"],
    }


def _html_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>" if items else ""


def _note(c: dict) -> genanki.Note:
    return genanki.Note(
        model=MODEL,
        fields=[c["id"], html.escape(c["prompt"]), html.escape(c["meta"]),
                f'<img src="{MEDIA_PREFIX}{c["image"]}">',
                _html_list(c["must_know"]), _html_list(c["questions"])],
        guid=genanki.guid_for("gib-skizze", c["id"]),
        tags=["skizzieren", f"kapitel-{c['chapter']}", c["id"]],
    )


def write_apkg(cards: list[dict], media_dir: Path) -> None:
    """Anki takes the media file name as given, so the crops are staged under prefixed names."""
    deck = genanki.Deck(DECK_ID, DECK_NAME,
                        description="Skizzierkarten zu den prüfungsrelevanten Abbildungen des Skripts. "
                                    "Rückseite: Originalabbildung aus dem Skript.")
    media_dir.mkdir(parents=True, exist_ok=True)
    media = []
    for c in cards:
        deck.add_note(_note(c))
        staged = media_dir / f"{MEDIA_PREFIX}{c['image']}"
        staged.write_bytes((config.FIG_ORIGINALS / c["image"]).read_bytes())
        media.append(str(staged))
    APKG.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck, media_files=media).write_to_file(str(APKG))


def overview_md(cards: list[dict]) -> str:
    out = ["# Karteikarten: Abbildungen skizzieren", "",
           f"{len(cards)} Karten, eine je prüfungsrelevanter Abbildung des Skripts (keine Tabellen, keine "
           "Formeln). Vorderseite: „Skizziere …“; Rückseite: die Originalabbildung, die Merkpunkte aus der "
           "Zeichenübung und die Prüfungsfragen dazu.", "",
           "Das importierbare Anki-Paket (`.apkg`) liegt im Release dieses Repositorys; es wird mit "
           "`python -m pipeline anki` nach `build/anki/` erzeugt. Die Prüfungsfragen stammen aus "
           "Studierenden-Quellen und sind nicht verifiziert.", ""]
    for c in cards:
        out += [f"## {c['prompt']}", "", f"*{c['meta']}*", "",
                "<details><summary>Lösung</summary>", "",
                f"![{c['prompt']}](../../figures/originals/{c['image']})", ""]
        guide = config.DRAWING_GUIDES / f"{c['id']}.md"
        if guide.exists():
            out += [f"[Zeichenübung](../drawing-exercises/{c['id']}.md)", ""]
        if c["must_know"]:
            out += ["**Das musst du können:**", "", *[f"- {m}" for m in c["must_know"]], ""]
        if c["questions"]:
            out += ["**Gefragt in Prüfungen:**", "", *[f"- {q}" for q in c["questions"]], ""]
        out += ["</details>", ""]
    return "\n".join(out).rstrip() + "\n"


def build() -> list[dict]:
    figures = _load_json(config.FIG_MANIFEST)["figures"]
    by_figure = _load_json(config.EXAMS / "topic-mapping.json")["by_figure"]
    questions = _load_json(config.EXAMS / "questions.json")["questions"]
    cards = []
    for fig in select(figures, by_figure):
        asked = [q for q in questions if fig["id"] in (q.get("figures") or [])]
        cards.append(card(fig, _meta(fig["id"]), sorted(asked, key=lambda q: q["date"])))
    return cards


def _inputs_key(cards: list[dict]) -> str:
    files = [config.FIG_MANIFEST, config.EXAMS / "topic-mapping.json", config.EXAMS / "questions.json",
             *(config.FIG_ORIGINALS / c["image"] for c in cards),
             *sorted(config.FIGURE_META_DIR.glob("*.yaml"))]
    return key_for(VERSION, *(sha256_file(p) for p in files))


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    cards = build()
    key = _inputs_key(cards)
    stamp = json.loads(STAMP.read_text(encoding="utf-8")) if STAMP.exists() else {}
    if not force and stamp.get("key") == key and APKG.exists() and OVERVIEW.exists():
        print(f"[anki] {len(cards)} Karten, unverändert (Cache)")
        return 0
    if dry_run:
        print(f"[anki] würde {len(cards)} Karten nach {APKG.relative_to(config.ROOT)} schreiben")
        return 0
    write_apkg(cards, OUT_DIR / "media")
    changed = write_if_changed(OVERVIEW, overview_md(cards))
    dump_json(STAMP, {"key": key, "cards": len(cards)})
    print(f"[anki] {len(cards)} Karten → {APKG.relative_to(config.ROOT)}"
          f"{', Übersicht aktualisiert' if changed else ''}")
    return 0
