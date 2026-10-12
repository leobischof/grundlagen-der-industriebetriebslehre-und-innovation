"""`validate` on the fixture tree: clean → no findings; each defect → exactly the expected error."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import QUESTION, STRUCTURE, write
from pipeline import config, validate
from pipeline.qa_findings import ERROR, WARNING
from pipeline.qa_repo import RepoView


def findings(root: Path, severity: str = ERROR) -> list[str]:
    return [f.message for f in validate.collect(RepoView(root)) if f.severity == severity]


def test_clean_tree_has_no_errors_and_no_warnings(repo):
    assert findings(repo) == []
    assert findings(repo, WARNING) == []


def test_run_writes_report_and_exit_code(repo, capsys):
    assert validate.run(root=repo) == 0
    report = (repo / "reports" / "validation.md").read_text(encoding="utf-8")
    assert report.startswith("#")
    (repo / "content" / "01-test" / "1.2-zweiter-abschnitt.md").unlink()
    assert validate.run(root=repo) == 1
    assert "FEHLER" in capsys.readouterr().out


def _unassigned_page(root):
    write(root, config.STRUCTURE_YAML, {**STRUCTURE, "skipped_pages": {1: "Titelseite"}})


def _missing_section(root):
    (root / "content" / "01-test" / "1.2-zweiter-abschnitt.md").unlink()


def _missing_png(root):
    (root / "figures" / "originals" / "abb-02.png").unlink()


def _missing_svg(root):
    (root / "figures" / "reconstructed" / "abb-01.svg").unlink()


def _raster_in_svg(root):
    path = root / "figures" / "reconstructed" / "abb-01.svg"
    path.write_text(path.read_text(encoding="utf-8").replace("<path", '<image href="x.png"/><path'), encoding="utf-8")


def _duplicate_question(root):
    write(root, config.EXAMS / "questions.json", [QUESTION, QUESTION])


def _unknown_question_section(root):
    write(root, config.EXAMS / "questions.json", [{**QUESTION, "sections": ["9.9"]}])


def _missing_questions(root):
    (root / "exams" / "questions.json").unlink()


def _broken_link(root):
    path = root / "content" / "README.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n[weg](gibt-es-nicht.md)\n", encoding="utf-8")


def _link_outside(root):
    path = root / "content" / "README.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n[raus](../../ausserhalb.md)\n", encoding="utf-8")


def _footnote_without_definition(root):
    path = root / "content" / "01-test" / "1.2-zweiter-abschnitt.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nNoch eine Fußnote[^7].\n", encoding="utf-8")


def _invalid_frontmatter(root):
    path = root / "content" / "01-test" / "1.1-erster-abschnitt.md"
    path.write_text(path.read_text(encoding="utf-8").replace("layer: bereinigt", "layer: erfunden"),
                    encoding="utf-8")


def _invalid_figure_meta(root):
    path = root / "curation" / "figures" / "abb-01.yaml"
    meta = yaml.safe_load(path.read_text(encoding="utf-8"))
    del meta["drawing"]
    path.write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")


def _stale_manifest(root):
    path = root / "figures" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["figures"].reverse()
    path.write_text(json.dumps(data), encoding="utf-8")


def _figure_not_embedded(root):
    path = root / "content" / "01-test" / "1.2-zweiter-abschnitt.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("figures:\n- abb-02", "figures: []").replace("![Abbildung 2", "[Abbildung 2"),
                    encoding="utf-8")


def _unknown_mapping_question(root):
    write(root, config.EXAMS / "topic-mapping.json",
          {"topics": [], "by_section": {"1.1": ["frage-2020-01-01-1"]}, "by_figure": {}})


@pytest.mark.parametrize("breakage, expected", [
    (_unassigned_page, "weder einem Abschnitt zugeordnet"),
    (_missing_section, "Abschnitt 1.2"),
    (_missing_png, "figures/originals/abb-02.png"),
    (_missing_svg, "als `faithful` markiert"),
    (_raster_in_svg, "Rasterbild"),
    (_duplicate_question, "mehrfach vergeben"),
    (_unknown_question_section, "unbekannte Abschnitte ['9.9']"),
    (_missing_questions, "questions.json fehlt"),
    (_broken_link, "gibt-es-nicht.md` – Ziel existiert nicht"),
    (_link_outside, "aus dem Repository heraus"),
    (_footnote_without_definition, "Fußnotenverweise ohne Definition ['7']"),
    (_invalid_frontmatter, "layer"),
    (_invalid_figure_meta, "'drawing' is a required property"),
    (_stale_manifest, "manifest.json ist veraltet"),
    (_figure_not_embedded, "`abb-02` ist in keiner Datei"),
    (_unknown_mapping_question, "unbekannte Fragen"),
], ids=lambda v: v.__name__.lstrip("_") if callable(v) else "")
def test_defect_is_reported_as_error(repo, breakage, expected):
    breakage(repo)
    errors = findings(repo)
    assert any(expected in e for e in errors), errors


def test_crashing_check_becomes_finding(repo, monkeypatch):
    def boom(view):
        raise RuntimeError("kaputt")
    monkeypatch.setattr(validate, "CHECKS", [("Test", boom)])
    assert findings(repo) == ["Prüfung `boom` abgebrochen: RuntimeError: kaputt"]


def test_missing_metadata_of_priority_figure_is_error(repo):
    figs = yaml.safe_load((repo / "curation" / "figures.yaml").read_text(encoding="utf-8"))["figures"]
    figs[1]["id"] = "abb-70"        # an exam-priority figure without metadata (B)
    write(repo, config.FIGURES_YAML, {"figures": figs})
    assert any("`abb-70` (prüfungsrelevant)" in e for e in findings(repo))
