"""The local learning-progress file: format, load/save and one review record.

Progress is personal data and lives only on the learner's machine
(learning/progress/progress.json, git-ignored). It is kept strictly apart from
the immutable sources: nothing here ever writes outside learning/progress/.
Format (schema: schemas/progress.schema.json, example: learning/progress/example.json):

  {"version": 1, "topics": {"<topic>": {"<competency>": {
      "last_practiced", "last_result", "errors", "mastery", "mastery_level",
      "sketch_independent", "repetitions", "interval_days", "ease", "next_due",
      "history": [{"date", "result", "errors", "sketch_independent"}]}}}}

A topic is any id of the knowledge base (sec-2.5, abb-08, a topic id from
exams/topic-mapping.json); competencies are the task types of the exam schema.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from . import config, srs
from .cache import write_if_changed

PROGRESS_DIR = config.LEARNING / "progress"
PROGRESS_FILE = PROGRESS_DIR / "progress.json"
FORMAT_VERSION = 1
HISTORY_LIMIT = 50          # keep the file small; scheduling needs only the last state
DRAWING = "zeichnung"       # the task type whose reviews record sketch_independent


@lru_cache(maxsize=1)
def competencies() -> tuple[str, ...]:
    """The competency vocabulary = task types of schemas/exam-question.schema.json (SSOT)."""
    schema = json.loads((config.SCHEMAS / "exam-question.schema.json").read_text(encoding="utf-8"))
    return tuple(schema["properties"]["task_types"]["items"]["enum"])


def empty() -> dict:
    return {"version": FORMAT_VERSION, "topics": {}}


def load(path: Path = PROGRESS_FILE) -> dict:
    if not path.exists():
        return empty()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != FORMAT_VERSION:
        raise SystemExit(f"{path}: unbekannte Formatversion {data.get('version')!r}")
    return data


def save(data: dict, path: Path = PROGRESS_FILE) -> None:
    write_if_changed(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def schedule_of(item: dict) -> srs.Schedule:
    if not item:
        return srs.Schedule()
    return srs.Schedule(repetitions=item["repetitions"], interval_days=item["interval_days"],
                        ease=item["ease"], mastery=item["mastery"])


def record(data: dict, topic: str, competency: str, result: int, when: date,
           errors: list[str] | None = None, sketch_independent: bool | None = None) -> dict:
    """Apply one review to `data` (in place) and return the updated item."""
    if competency not in competencies():
        raise ValueError(f"Unbekannte Kompetenz {competency!r}; erlaubt: {', '.join(competencies())}")
    if competency != DRAWING and sketch_independent is not None:
        raise ValueError(f"--skizze gilt nur für die Kompetenz '{DRAWING}'")
    item = data["topics"].setdefault(topic, {}).get(competency, {})
    sched = srs.review(schedule_of(item), result, sketch_independent)
    errors = list(errors or [])
    history = (item.get("history") or []) + [{"date": when.isoformat(), "result": result, "errors": errors,
                                              "sketch_independent": sketch_independent}]
    item = {
        "last_practiced": when.isoformat(),
        "last_result": result,
        "errors": errors,
        "mastery": sched.mastery,
        "mastery_level": srs.level(sched),
        "sketch_independent": sketch_independent if competency == DRAWING else None,
        "repetitions": sched.repetitions,
        "interval_days": sched.interval_days,
        "ease": sched.ease,
        "next_due": srs.next_due(when, sched).isoformat(),
        "history": history[-HISTORY_LIMIT:],
    }
    data["topics"][topic][competency] = item
    return item


def rows(data: dict) -> list[tuple[str, str, dict]]:
    """(topic, competency, item), soonest due first."""
    out = [(t, c, item) for t, comps in data["topics"].items() for c, item in comps.items()]
    return sorted(out, key=lambda r: (r[2]["next_due"], r[0], r[1]))


def due(data: dict, on: date) -> list[tuple[str, str, dict]]:
    return [r for r in rows(data) if r[2]["next_due"] <= on.isoformat()]


def reset(data: dict, topic: str | None = None) -> int:
    """Forget one topic (or everything); returns the number of removed items."""
    if topic is None:
        removed = sum(len(c) for c in data["topics"].values())
        data["topics"] = {}
        return removed
    return len(data["topics"].pop(topic, {}))
