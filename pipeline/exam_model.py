"""Exam database model: load curation/exams.yaml + topics.yaml, validate, derive records.

The curated YAML is the single source of truth; every exam stage (`exams`, `link`)
reads it through `load()` so both see the same validated data. Validation is strict
about references (topics, TOC sections, figures) because a typo there would silently
drop a question from the frequency analysis or from a content file's frontmatter.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import catalog

TASK_TYPES = ("definition", "erklaerung", "aufzaehlung", "zeichnung", "vergleich", "berechnung", "anwendung")
COMPETENCIES = ("wissen", "verstehen", "anwenden", "zeichnen", "vergleichen", "berechnen")
COVERAGE = ("voll", "teilweise", "keine")
TRUST = ("student-recollection", "student-transcript")
REQUIRED = ("id", "exam_date", "source", "trust", "wording", "prompt", "points", "task_type",
            "competencies", "topics", "sections", "figures")
_ID = re.compile(r"^frage-(\d{4}-\d{2}-\d{2})-(\d+)$")


@dataclass(frozen=True)
class ExamData:
    exams: list[dict]          # one per exam date (metadata)
    mode: dict | None          # exam mode as reported by students (`exam_mode:`), None if absent
    questions: list[dict]      # output records, sorted by (date, number)
    topics: list[dict]         # curated topics in file order
    problems: list[str]        # validation messages (empty = consistent)


def question_number(qid: str) -> int:
    return int(qid.rsplit("-", 1)[1])


def _check_refs(q: dict, topic_ids: set[str], toc: set[str], figure_ids: set[str]) -> list[str]:
    qid = q["id"]
    out = []
    out += [f"{qid}: unbekanntes Thema `{t}`" for t in q["topics"] if t not in topic_ids]
    out += [f"{qid}: unbekannter Abschnitt `{s}`" for s in q["sections"] if str(s) not in toc]
    out += [f"{qid}: unbekannte Abbildung `{f}`" for f in q["figures"] if f not in figure_ids]
    return out


def _check_question(q: dict, exam_dates: set[str]) -> list[str]:
    qid = q.get("id", "?")
    missing = [k for k in REQUIRED if k not in q]
    if missing:
        return [f"{qid}: Pflichtfelder fehlen: {', '.join(missing)}"]
    out = []
    m = _ID.match(qid)
    if not m or m.group(1) != q["exam_date"]:
        out.append(f"{qid}: ID passt nicht zum Prüfungsdatum {q['exam_date']}")
    if q["exam_date"] not in exam_dates:
        out.append(f"{qid}: Prüfungstermin {q['exam_date']} fehlt unter `exams:`")
    if q["task_type"] not in TASK_TYPES:
        out.append(f"{qid}: ungültiger task_type `{q['task_type']}`")
    out += [f"{qid}: ungültige Kompetenz `{c}`" for c in q["competencies"] if c not in COMPETENCIES]
    if q["trust"] not in TRUST:
        out.append(f"{qid}: ungültiger trust `{q['trust']}`")
    if q.get("script_coverage", "voll") not in COVERAGE:
        out.append(f"{qid}: ungültige script_coverage `{q['script_coverage']}`")
    if not q["wording"].strip():
        out.append(f"{qid}: leerer Wortlaut")
    if not str(q["prompt"]).strip():
        out.append(f"{qid}: leere Aufgabenstellung (prompt)")
    if not q["topics"]:
        out.append(f"{qid}: kein Thema zugeordnet")
    return out


def _check_points(exams: list[dict], questions: list[dict]) -> list[str]:
    out = []
    for e in exams:
        if e.get("total_points") is None:
            continue
        got = sum(q["points"] or 0 for q in questions if q["exam_date"] == e["date"])
        if got != e["total_points"]:
            out.append(f"{e['date']}: Punktesumme {got} weicht von total_points {e['total_points']} ab")
    return out


def _record(q: dict, topic_title: dict[str, str]) -> dict:
    """Output record. `date`/`text`/`task_types` repeat `exam_date`/`wording`/`task_type`
    because schemas/exam-question.schema.json (used by `validate`) names them that way."""
    first = q["topics"][0] if q["topics"] else None
    return {
        "id": q["id"], "number": question_number(q["id"]),
        "date": q["exam_date"], "exam_date": q["exam_date"],
        "source": q["source"], "trust": q["trust"],
        "text": q["wording"], "wording": q["wording"], "prompt": q["prompt"].strip(),
        "points": q["points"],
        "task_type": q["task_type"], "task_types": [q["task_type"]],
        "competencies": list(q["competencies"]),
        "topic": topic_title.get(first), "topics": list(q["topics"]),
        "sections": [str(s) for s in q["sections"]], "figures": list(q["figures"]),
        "script_coverage": q.get("script_coverage", "voll"),
        "notes": (q.get("notes") or "").strip() or None,
    }


def load() -> ExamData:
    raw = catalog.exams()
    exams = sorted(raw.get("exams", []), key=lambda e: e["date"])
    mode = raw.get("exam_mode")
    topics = catalog.topics().get("topics", [])
    exam_dates = {e["date"] for e in exams}
    topic_ids = {t["id"] for t in topics}
    toc = {e.number for e in catalog.entries()}
    figure_ids = {f["id"] for f in catalog.figures()}

    problems = [f"Thema `{t}` mehrfach vergeben" for t in sorted(topic_ids) if sum(x["id"] == t for x in topics) > 1]
    ids = [q.get("id") for q in raw.get("questions", [])]
    problems += [f"Fragen-ID `{i}` mehrfach vergeben" for i in sorted(set(ids)) if ids.count(i) > 1]
    for q in raw.get("questions", []):
        found = _check_question(q, exam_dates)
        problems += found or _check_refs(q, topic_ids, toc, figure_ids)
    if problems:
        return ExamData(exams, mode, [], topics, problems)

    titles = {t["id"]: t["title"] for t in topics}
    records = sorted((_record(q, titles) for q in raw["questions"]), key=lambda r: (r["exam_date"], r["number"]))
    return ExamData(exams, mode, records, topics, _check_points(exams, records))
