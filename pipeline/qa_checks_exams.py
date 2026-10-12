"""Checks: exam questions are complete, unique and point at things that exist.

Required fields (schema errors) are what makes a question usable at all: id,
source, date and the original wording. The fields that make it *useful*
(sections, task types, points, competencies) are only warnings when missing –
a remembered question without a known score is still worth keeping.
"""
from __future__ import annotations

from collections import Counter

from .qa_checks_structure import known_source_refs
from .qa_findings import Finding, error, warning
from .qa_repo import RepoView
from .qa_schema import EXAM_QUESTION, TOPIC_MAPPING, problems

EXAMS = "Prüfungsfragen"
RECOMMENDED = ("sections", "task_types", "competencies", "points")


def _incomplete(q: dict) -> list[str]:
    """Recommended fields that are missing. `points: null` means "score not known" and
    counts as answered; only an absent key is reported."""
    return [k for k in RECOMMENDED
            if k not in q or (k != "points" and q[k] in (None, [], ""))]


def _section_numbers(view: RepoView) -> set[str]:
    return {e.number for e in view.entries}


def check_questions(view: RepoView) -> list[Finding]:
    questions = view.questions
    if questions is None:
        return [error(EXAMS, "exams/questions.json fehlt – Stufe `exams` ist noch nicht gelaufen")]
    out = []
    ids = [str(q.get("id")) for q in questions]
    out += [error(EXAMS, f"Fragen-ID `{i}` mehrfach vergeben") for i, n in Counter(ids).items() if n > 1]
    toc = _section_numbers(view)
    figures = {f["id"] for f in view.figures}
    sources = known_source_refs(view)
    for q in questions:
        qid = q.get("id", "?")
        out += [error(EXAMS, f"`{qid}`: {p}") for p in problems(EXAM_QUESTION, q)]
        missing = _incomplete(q)
        if missing:
            out.append(warning(EXAMS, f"`{qid}` unvollständig – fehlt: {', '.join(missing)}"))
        bad_secs = [s for s in q.get("sections") or [] if str(s) not in toc]
        if bad_secs:
            out.append(error(EXAMS, f"`{qid}`: unbekannte Abschnitte {bad_secs}"))
        bad_figs = [f for f in q.get("figures") or [] if f not in figures]
        if bad_figs:
            out.append(error(EXAMS, f"`{qid}`: unbekannte Abbildungen {bad_figs}"))
        if q.get("source") and q["source"] not in sources:
            out.append(error(EXAMS, f"`{qid}`: unbekannte Quelle `{q['source']}`"))
    out += _section_links(view, set(ids))
    return out


def _section_links(view: RepoView, question_ids: set[str]) -> list[Finding]:
    """exam_questions in content frontmatter must exist in questions.json."""
    out = []
    for f in view.section_files:
        unknown = [q for q in f.meta.get("exam_questions") or [] if q not in question_ids]
        if unknown:
            out.append(error(EXAMS, f"`{f.rel}`: verweist auf unbekannte Fragen {unknown}"))
    return out


def check_topic_mapping(view: RepoView) -> list[Finding]:
    mapping = view.topic_mapping
    if mapping is None:
        return [error(EXAMS, "exams/topic-mapping.json fehlt – Stufe `exams`/`link` ist noch nicht gelaufen")]
    out = [error(EXAMS, f"topic-mapping.json: {p}") for p in problems(TOPIC_MAPPING, mapping)]
    if out:
        return out
    topic_ids = [str(t.get("id")) for t in mapping["topics"]]
    out += [error(EXAMS, f"Themen-ID `{i}` mehrfach vergeben") for i, n in Counter(topic_ids).items() if n > 1]
    toc = _section_numbers(view)
    figures = {f["id"] for f in view.figures}
    known_q = {str(q.get("id")) for q in view.questions or []}
    bad_secs = sorted(k for k in mapping["by_section"] if k not in toc)
    if bad_secs:
        out.append(error(EXAMS, f"topic-mapping.json `by_section`: unbekannte Abschnitte {bad_secs}"))
    bad_figs = sorted(k for k in mapping["by_figure"] if k not in figures)
    if bad_figs:
        out.append(error(EXAMS, f"topic-mapping.json `by_figure`: unbekannte Abbildungen {bad_figs}"))
    referenced = {q for group in ("by_section", "by_figure") for qs in mapping[group].values() for q in qs}
    unknown = sorted(referenced - known_q) if view.questions is not None else []
    if unknown:
        out.append(error(EXAMS, f"topic-mapping.json nennt unbekannte Fragen: {unknown[:10]}"
                                + (" …" if len(unknown) > 10 else "")))
    unmapped = sorted(known_q - {q for qs in mapping["by_section"].values() for q in qs})
    if unmapped:
        out.append(warning(EXAMS, f"{len(unmapped)} Fragen keinem Abschnitt zugeordnet: {unmapped[:10]}"
                                  + (" …" if len(unmapped) > 10 else "")))
    return out
