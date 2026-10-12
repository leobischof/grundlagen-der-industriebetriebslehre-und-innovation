"""Stage "exams": curation/exams.yaml + topics.yaml -> exams/questions.json, questions.md,
frequency-analysis.md.

Everything is derived from the curated YAML (single source of truth); the stage never
reads the exam PDFs, never calls an AI model and is deterministic, so a second run
writes nothing. Validation problems (unknown topic/section/figure, bad points sum, ...)
stop the stage before any output is touched - a half-consistent database is worse than
a stale one.
"""
from __future__ import annotations

from . import config, exam_model, exam_report, exam_stats
from .cache import dump_json, write_if_changed

QUESTIONS_JSON = config.EXAMS / "questions.json"
QUESTIONS_MD = config.EXAMS / "questions.md"
FREQUENCY_MD = config.EXAMS / "frequency-analysis.md"


def _outputs(data: exam_model.ExamData) -> dict:
    rows = exam_stats.topic_stats(data.questions, data.exams, data.topics)
    return {
        "json": {"questions": data.questions,
                 "exams": [{k: e.get(k) for k in ("date", "source", "trust", "total_points", "notes")}
                           for e in data.exams]},
        "questions_md": exam_report.questions_md(data.questions, data.exams, data.topics),
        "frequency_md": exam_report.frequency_md(data.questions, data.exams, rows),
    }


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    data = exam_model.load()
    if data.problems:
        print("[exams] Fehler in curation/exams.yaml bzw. topics.yaml:")
        print("\n".join(f"  - {p}" for p in data.problems))
        return 1
    out = _outputs(data)
    n_exams = len(data.exams)
    print(f"[exams] {len(data.questions)} Fragen, {n_exams} Termine, {len(data.topics)} Themen")
    if dry_run:
        print("[exams] --dry-run: nichts geschrieben")
        return 0
    changed = [dump_json(QUESTIONS_JSON, out["json"]),
               write_if_changed(QUESTIONS_MD, out["questions_md"]),
               write_if_changed(FREQUENCY_MD, out["frequency_md"])]
    print(f"[exams] {sum(changed)} von 3 Dateien geändert in {config.EXAMS.relative_to(config.ROOT)}/")
    return 0
