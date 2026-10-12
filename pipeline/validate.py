"""Stage "validate": automated quality checks over the committed files → reports/validation.md.

Offline by design (runs in CI): it reads only files that are in the repository –
curation, content, figures, exams, reports – and never opens a PDF, runs OCR or
calls a model. Parts of the knowledge base that are not built yet are reported
as findings, never as a crash, so the report is honest at every stage of the
build. Exit code 1 if any check found an ERROR; warnings never fail the run.

Checks (one module per concern):
  qa_checks_structure – PDF pages, TOC sections, chapter files, sources, OCR quality
  qa_checks_figures   – PNG/metadata/SVG/exercise per figure, manifest, detection reports
  qa_checks_exams     – exam questions and topic mapping
  qa_checks_links     – relative links in every committed .md file, footnotes
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from . import config
from .cache import write_if_changed
from .qa_checks_exams import EXAMS, check_questions, check_topic_mapping
from .qa_checks_figures import DETECTION, FIGURES, check_detection, check_figures
from .qa_checks_links import FOOTNOTES, LINKS, check_footnotes, check_links
from .qa_checks_structure import (OCR, PAGES, SECTIONS, SOURCES, check_ocr, check_pages,
                                  check_sections, check_sources)
from .qa_findings import ERROR, WARNING, Finding, count, error, render
from .qa_repo import RepoView

MAX_PRINTED_ERRORS = 30

# (report group, check). Order = order in the report.
CHECKS: list[tuple[str, Callable[[RepoView], list[Finding]]]] = [
    (SOURCES, check_sources),
    (PAGES, check_pages),
    (SECTIONS, check_sections),
    (OCR, check_ocr),
    (FIGURES, check_figures),
    (DETECTION, check_detection),
    (EXAMS, check_questions),
    (EXAMS, check_topic_mapping),
    (LINKS, check_links),
    (FOOTNOTES, check_footnotes),
]


def collect(view: RepoView) -> list[Finding]:
    """Run every check; a crashing check becomes an ERROR finding instead of aborting the run."""
    findings: list[Finding] = []
    for group, check in CHECKS:
        try:
            findings += check(view)
        except Exception as exc:  # noqa: BLE001 – one broken input must not hide all other findings
            findings.append(error(group, f"Prüfung `{check.__name__}` abgebrochen: "
                                         f"{type(exc).__name__}: {exc}"))
    return findings


def groups() -> list[str]:
    return list(dict.fromkeys(group for group, _ in CHECKS))


def run(pages: str | None = None, dry_run: bool = False, force: bool = False,
        root: Path | None = None) -> int:
    """`pages`/`force` are accepted for the common stage interface; validation is always complete."""
    view = RepoView(root)
    if dry_run:
        print(f"[validate] würde {len(CHECKS)} Prüfungen über {view.root} ausführen: {', '.join(groups())}")
        return 0
    findings = collect(view)
    report = view.path(config.REPORTS) / "validation.md"
    changed = write_if_changed(report, render(findings, groups()))
    errors, warnings = count(findings, ERROR), count(findings, WARNING)
    print(f"[validate] {errors} Fehler, {warnings} Warnungen | "
          f"{view.rel(report)} {'geschrieben' if changed else 'unverändert'}")
    # The console only gets a taste – a fresh tree can have hundreds of errors; the report has all.
    shown = [f for f in findings if f.severity == ERROR][:MAX_PRINTED_ERRORS]
    for f in shown:
        print(f"  FEHLER [{f.check}] {f.message}")
    if errors > len(shown):
        print(f"  … {errors - len(shown)} weitere Fehler, siehe {view.rel(report)}")
    return 1 if errors else 0
