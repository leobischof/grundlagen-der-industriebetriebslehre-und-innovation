"""Stage "link": topics <-> script sections <-> figures <-> exam questions.

Writes exams/topic-mapping.json, the lookup table the content builder uses to fill
`exam_questions` in each section file's frontmatter and the learning stages use to
find the questions of a topic. Inputs are the curated exam database and topics only.

Mapping rules (kept conservative on purpose):
  * by_section / by_figure follow the *question's own* sections and figures - the
    curator's judgement per question - never the topic's wider lists, so a content
    file only advertises questions that really need it.
  * A question on "8.2.5.3" also counts for every ancestor section down to X.Y
    ("8.2.5", "8.2"): content files are per X.Y and must see it.
"""
from __future__ import annotations

import re

from . import catalog, config, exam_model
from .cache import dump_json

OUT = config.EXAMS / "topic-mapping.json"
_XY = re.compile(r"^\d+\.\d+$")


def _num_key(number: str) -> list[int]:
    return [int(p) for p in number.split(".")]


def _with_ancestors(section: str) -> list[str]:
    """"8.2.5.3" -> ["8.2.5.3", "8.2.5", "8.2"]; chapter level is left out (no chapter files)."""
    parts = section.split(".")
    return [".".join(parts[:n]) for n in range(len(parts), 1, -1)] or [section]


def _group(pairs: list[tuple[str, str]], sort_key=None) -> dict[str, list[str]]:
    out: dict[str, set[str]] = {}
    for key, qid in pairs:
        out.setdefault(key, set()).add(qid)
    return {k: sorted(out[k]) for k in sorted(out, key=sort_key)}


def uncovered_sections(topics: list[dict]) -> list[str]:
    """X.Y sections of the script that no topic lists (itself or a subsection)."""
    listed = {str(s) for t in topics for s in t.get("sections", [])}
    xy = [e.number for e in catalog.entries() if e.kind == "section" and _XY.match(e.number)]
    return [n for n in xy if not any(s == n or s.startswith(n + ".") for s in listed)]


def build(data: exam_model.ExamData) -> dict:
    qs = data.questions
    by_topic = _group([(t, q["id"]) for q in qs for t in q["topics"]])
    sec_pairs = [(a, q["id"]) for q in qs for s in q["sections"] for a in _with_ancestors(s)]
    topics = [{"id": t["id"], "title": t["title"], "sections": [str(s) for s in t.get("sections", [])],
               "figures": list(t.get("figures", [])), "keywords": list(t.get("keywords", [])),
               "question_ids": by_topic.get(t["id"], [])} for t in data.topics]
    by_section = _group(sec_pairs, sort_key=_num_key)
    xy_sections = [e.number for e in catalog.entries() if e.kind == "section" and _XY.match(e.number)]
    return {
        "topics": topics,
        "by_section": by_section,
        "by_figure": _group([(f, q["id"]) for q in qs for f in q["figures"]]),
        "by_question": {q["id"]: {"topics": q["topics"], "sections": q["sections"], "figures": q["figures"]}
                        for q in qs},
        "sections_without_topic": uncovered_sections(data.topics),
        "sections_without_questions": [n for n in xy_sections if n not in by_section],
    }


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    data = exam_model.load()
    if data.problems:
        print("[link] Fehler in curation/exams.yaml bzw. topics.yaml:")
        print("\n".join(f"  - {p}" for p in data.problems))
        return 1
    mapping = build(data)
    print(f"[link] {len(mapping['topics'])} Themen, {len(mapping['by_section'])} Abschnitte, "
          f"{len(mapping['by_figure'])} Abbildungen mit Fragen")
    if mapping["sections_without_topic"]:
        print(f"[link] WARNUNG: Abschnitte ohne Thema: {', '.join(mapping['sections_without_topic'])}")
    print(f"[link] {len(mapping['sections_without_questions'])} X.Y-Abschnitte ohne bekannte Prüfungsfrage")
    if dry_run:
        print("[link] --dry-run: nichts geschrieben")
        return 0
    changed = dump_json(OUT, mapping)
    print(f"[link] {OUT.relative_to(config.ROOT)} {'geschrieben' if changed else 'unverändert'}")
    return 0
