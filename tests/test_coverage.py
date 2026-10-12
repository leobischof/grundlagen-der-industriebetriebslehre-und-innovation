"""`report` counts what exists and says "nein" as soon as something is missing."""
from __future__ import annotations

from pipeline import coverage
from pipeline.coverage_stats import collect
from pipeline.qa_repo import RepoView


def _report(root) -> str:
    assert coverage.run(root=root) == 0
    return (root / "reports" / "coverage.md").read_text(encoding="utf-8")


def test_complete_tree_is_reported_complete(repo):
    text = _report(repo)
    assert "**Skript vollständig verarbeitet:** ja" in text
    stats = collect(RepoView(repo))
    assert stats["pages"] == {"total": 6, "skipped": 2, "assigned": 4, "ocr_layer": 0, "ocr_weak": [],
                              "in_content": 4, "missing_in_content": []}
    assert (stats["sections"]["files"], stats["sections"]["expected"]) == (2, 2)
    fig = stats["figures"]
    assert (fig["png"], fig["meta"], fig["svg"], fig["faithful"], fig["exercise"]) == (2, 1, 1, 1, 1)
    assert stats["questions"]["drawing"] == 1
    assert stats["footnotes"]["anchored"] == 1


def test_missing_section_and_figure_make_verdict_no(repo):
    (repo / "content" / "01-test" / "1.2-zweiter-abschnitt.md").unlink()
    (repo / "figures" / "originals" / "abb-02.png").unlink()
    text = _report(repo)
    assert "**Skript vollständig verarbeitet: nein**" in text
    assert "1 Abschnitte ohne Datei" in text and "1 Abbildungen ohne Original" in text
    assert "1.2 Zweiter Abschnitt" in text


def test_report_is_stable(repo):
    """No timestamps: a second run must not rewrite the file (quiet git diffs)."""
    first = _report(repo)
    path = repo / "reports" / "coverage.md"
    mtime = path.stat().st_mtime_ns
    assert _report(repo) == first
    assert path.stat().st_mtime_ns == mtime
