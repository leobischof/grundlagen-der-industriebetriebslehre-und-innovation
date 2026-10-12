"""Frequency statistics of the exam questions per topic, task type and competency.

The priority score is a deliberately simple, fully printed heuristic - not a
probability. Its three terms and their weights live here as constants so that the
report (pipeline/exam_report.py) prints exactly what is computed:

    score = W_DATES * T  +  P_SCALE * (Punkte / Gesamtpunkte)  +  A

    T  number of distinct exam dates in which the topic was asked
       (a topic asked twice on one date counts once)
    P  share of the points of all questions with a known score that touch the topic
       (only the Klausur 2026-04-29 carries points; a question with several topics
       counts its full points for each of them)
    A  recency bonus: number of the RECENT_DATES newest exam dates that asked the topic
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .exam_model import COMPETENCIES, TASK_TYPES

W_DATES = 2          # weight per exam date: breadth over time is the strongest signal
P_SCALE = 10         # a topic that carries all known points would earn this many score points
RECENT_DATES = 3     # how many of the newest exam dates give a +1 recency bonus


def formula() -> str:
    return (f"Score = {W_DATES} · T + {P_SCALE} · (Punkte / Gesamtpunkte) + A")


def _known_points_total(questions: list[dict]) -> int:
    return sum(q["points"] for q in questions if q["points"] is not None)


def topic_stats(questions: list[dict], exams: list[dict], topics: list[dict]) -> list[dict]:
    """One row per curated topic (also those never asked), sorted by score, then title."""
    newest = {e["date"] for e in sorted(exams, key=lambda e: e["date"], reverse=True)[:RECENT_DATES]}
    total = _known_points_total(questions)
    dates: dict[str, set[str]] = defaultdict(set)
    count: Counter = Counter()
    points: Counter = Counter()
    for q in questions:
        for t in q["topics"]:
            dates[t].add(q["exam_date"])
            count[t] += 1
            points[t] += q["points"] or 0
    rows = []
    for t in topics:
        d = sorted(dates[t["id"]])
        p_term = P_SCALE * points[t["id"]] / total if total else 0.0
        a_term = len(set(d) & newest)
        rows.append({
            "id": t["id"], "title": t["title"], "dates": d, "n_dates": len(d),
            "n_questions": count[t["id"]], "points": points[t["id"]],
            "last": d[-1] if d else None, "p_term": round(p_term, 2), "a_term": a_term,
            "score": round(W_DATES * len(d) + p_term + a_term, 1),
        })
    return sorted(rows, key=lambda r: (-r["score"], r["title"]))


def counts(questions: list[dict], key: str, vocabulary: tuple[str, ...]) -> list[tuple[str, int, int]]:
    """(value, number of questions, number of questions in the Klausur with known points).

    Values of the controlled vocabulary appear even with count 0 so gaps stay visible."""
    total, graded = Counter(), Counter()
    for q in questions:
        for v in (q[key] if isinstance(q[key], list) else [q[key]]):
            total[v] += 1
            graded[v] += q["points"] is not None
    return [(v, total[v], graded[v]) for v in vocabulary]


def task_type_counts(questions: list[dict]) -> list[tuple[str, int, int]]:
    return counts(questions, "task_type", TASK_TYPES)


def competency_counts(questions: list[dict]) -> list[tuple[str, int, int]]:
    return counts(questions, "competencies", COMPETENCIES)
