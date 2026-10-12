"""Anki cards from the worked exam answers (learning/exercises/<chapter>-musterloesungen.md).

Each `## …` block of a chapter's file is one card. Front: the exam question as a full task
(exams/questions.json `prompt`, the operator wording the question collection uses) or, for a
practice task without a real exam question, the task quoted under its heading. Back: the
worked answer, the places in the script and the marking notes, as written – they are an AI
explanation, not the script, and the card says so.

Links into the repository mean nothing inside Anki and keep only their label; a link to a
script picture ("[Original](…/abb-22.png)") goes entirely (figure_publish). A figure the
question asks about is shown below the answer where we have our own SVG of it.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import figure_publish
from .anki_cards import Card, figure_image, plain
from .exam_report import SOURCE_LABEL, german_date

_BLOCK = re.compile(r"^## (.+)$", re.M)
_QUESTION_ID = re.compile(r"`(frage-[\d-]+)`")
_QUOTE = re.compile(r"\A\s*((?:^>.*\n?)+)", re.M)
_ORIGINAL_LINK = re.compile(r"[,:]?\s*(?:im\s+)?\[[^\]]*\]\(([^)\s]+)\)")
_EMPTY_PARENS = re.compile(r"\s*\(\s*\)")
_SUBHEAD = re.compile(r"^### (.+)$", re.M)
AI_NOTE = "Musterlösung KI-erstellt, nicht geprüft"


def without_originals(text: str) -> str:
    """Drop links to script pictures; '(Abbildung 22, [Original](…png))' → '(Abbildung 22)'."""
    text = _ORIGINAL_LINK.sub(lambda m: "" if figure_publish.original_id(m.group(1)) else m.group(0), text)
    return _EMPTY_PARENS.sub("", text)


def _quote(text: str) -> str:
    """The blockquote right below a heading, without '>' and outer quotation marks."""
    m = _QUOTE.match(text)
    if not m:
        return ""
    lines = [ln.lstrip(">").strip() for ln in m.group(1).splitlines()]
    return " ".join(ln for ln in lines if ln).strip("„“\"")


def _answer(text: str) -> str:
    """Everything from the first '###' on; sub-headings become bold lead lines."""
    start = _SUBHEAD.search(text)
    if not start:
        return ""
    body = re.sub(r"\n-{3,}\s*\Z", "", text[start.start():].rstrip())
    return plain(_SUBHEAD.sub(lambda m: f"**{m.group(1).strip()}**", without_originals(body)))


def solution_cards(path: Path, chapter: str, questions: dict[str, dict]) -> list[Card]:
    """Cards of one chapter's worked answers; `questions` maps a question id to its record."""
    text = path.read_text(encoding="utf-8")
    heads = list(_BLOCK.finditer(text))
    cards = []
    for head, nxt in zip(heads, heads[1:] + [None]):
        block = text[head.end():nxt.start() if nxt else len(text)]
        answer = _answer(block)
        if not answer:
            continue
        found = _QUESTION_ID.search(head.group(1))
        record = questions.get(found.group(1)) if found else None
        if record:
            front = record["prompt"]
            source = (f"Prüfung {german_date(record['date'])} · "
                      f"{SOURCE_LABEL.get(record['source'], record['source'])}, unverifiziert · {AI_NOTE}")
            key = f"{chapter}:{record['id']}"
            pictures = [figure_image(fid, f"Abbildung {fid.removeprefix('abb-')}") for fid in record.get("figures") or []]
            answer = "\n\n".join([answer, *(md for md, _ in pictures if md)])
            media = tuple(p for _, files in pictures for p in files)
        else:
            front = _quote(block) or head.group(1).strip()
            source = f"Übungsaufgabe im Prüfungsstil (keine echte Prüfungsfrage) · {AI_NOTE}"
            key = f"{chapter}:{head.group(1).strip()}"
            media = ()
        cards.append(Card("pruefung", chapter, key, plain(front), answer, source, media))
    return cards
