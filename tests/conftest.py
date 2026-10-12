"""A tiny but complete knowledge-base tree for the offline QA tests.

Six PDF pages, one chapter with two sections and a literature list, two
figures (abb-01 fully reconstructed with exercise, abb-02 original only), one
exam question. `validate` must find zero errors and zero warnings in it, so
every test can break exactly one thing and expect exactly that finding.
Layout comes from config.py via RepoView, so the fixture mirrors the real repo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from pipeline import config

QUESTION_ID = "frage-2026-04-29-1"

STRUCTURE = {
    "chapters": [{
        "id": "01", "slug": "01-test", "title": "Testkapitel",
        "entries": [
            {"number": "1", "title": "TESTKAPITEL", "pdf_page": 3, "kind": "chapter"},
            {"number": "1.1", "title": "Erster Abschnitt", "pdf_page": 3},
            {"number": "1.2", "title": "Zweiter Abschnitt", "pdf_page": 4, "end_page": 5},
            {"number": "L1", "title": "Literatur Kapitel 1", "pdf_page": 6, "kind": "literature", "end_page": 6},
        ],
    }],
    "skipped_pages": {1: "Titelseite", 2: "Inhaltsverzeichnis"},
}

FIGURES = [
    {"id": "abb-01", "kind": "figure", "number": 1, "title": "Testkurve", "pdf_page": 3, "bbox": [0, 0, 10, 10]},
    {"id": "abb-02", "kind": "figure", "number": 2, "title": "Testmatrix", "pdf_page": 5, "bbox": [0, 0, 10, 10]},
]

FIGURE_META = {
    "id": "abb-01", "title": "Testkurve", "type": "kurvendiagramm",
    "description": "Eine Testkurve, die über der Zeit ansteigt und danach wieder abfällt.",
    "axes": [{"axis": "x", "label": "Zeit", "unit": None, "direction": "rechts"}],
    "elements": [{"id": "e1", "kind": "kurve", "text": "Umsatz"}],
    "meaning": "Die Testkurve zeigt, dass alles, was steigt, auch wieder fällt.",
    "exam_relevance": {"level": "hoch", "reason": "Zeichenaufgabe", "question_ids": [QUESTION_ID]},
    "drawing": {"difficulty": "leicht", "must_know": ["Achsen beschriften"]},
    "reconstruction": {"status": "faithful", "svg": "figures/reconstructed/abb-01.svg"},
    "source": {"pdf_page": 3, "printed_page": None},
}

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" data-figure-id="abb-01" '
       'data-status="faithful"><path d="M0 10 L10 0"/><text class="answer" x="1" y="9">Zeit</text></svg>\n')

QUESTION = {
    "id": QUESTION_ID, "source": "klausur-2026-04-29", "date": "2026-04-29",
    "text": "Zeichnen Sie die Testkurve.", "points": 4, "sections": ["1.1"], "figures": ["abb-01"],
    "task_types": ["zeichnung"], "competencies": ["zeichnen"],
}

TOPIC_MAPPING = {
    "topics": [{"id": "testkurve", "title": "Testkurve", "sections": ["1.1"], "figures": ["abb-01"],
                "question_ids": [QUESTION_ID]}],
    "by_section": {"1.1": [QUESTION_ID]},
    "by_figure": {"abb-01": [QUESTION_ID]},
}


def _section(number: str, title: str, pages: list[int], figures: list[str], body: str,
             questions: list[str] = ()) -> str:
    meta = {"id": f"sec-{number}", "title": title, "chapter": "01", "section": number,
            "pdf_pages": pages, "printed_pages": [None] * len(pages), "figures": figures,
            "exam_questions": list(questions), "layer": "bereinigt", "source": config.SKRIPT,
            "quality": {"status": "maschinell-bereinigt-ungeprueft"}}
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n" + body


SECTION_11 = _section("1.1", "Erster Abschnitt", [3, 4], ["abb-01"], (
    "# 1.1 Erster Abschnitt\n\nText mit Fußnote[^1].\n\n"
    "![Abbildung 1: Testkurve](../../figures/originals/abb-01.png)\n\n"
    "Weiter in [1.2](1.2-zweiter-abschnitt.md).\n\n[^1]: Eine Fußnote.\n"), [QUESTION_ID])
SECTION_12 = _section("1.2", "Zweiter Abschnitt", [4, 5], ["abb-02"], (
    "# 1.2 Zweiter Abschnitt\n\n![Abbildung 2: Testmatrix](../../figures/originals/abb-02.png)\n"))
LITERATURE = ("---\nid: lit-01\ntitle: Literatur Kapitel 1\nchapter: '01'\npdf_pages: [6]\n---\n"
              "# Literatur Kapitel 1\n\n- Autor, A. (2020): Ein Buch.\n")


def _manifest_entry(fig: dict, files: dict, status: str, meta: bool) -> dict:
    return {"id": fig["id"], "kind": fig["kind"], "label": f"Abbildung {fig['number']}", "number": fig["number"],
            "title": fig["title"], "pdf_page": fig["pdf_page"], "printed_page": None, "bbox": fig["bbox"],
            "chapter": "01", "section": "1.1", "subsection": "1.1", "files": files,
            "reconstruction_status": status, "exam_relevance": "hoch" if meta else None,
            "drawing_difficulty": "leicht" if meta else None,
            "metadata_status": "curated" if meta else "missing"}


def _figures_manifest() -> dict:
    full = {"original": "figures/originals/abb-01.png", "reconstructed": "figures/reconstructed/abb-01.svg",
            "exercise": "figures/exercises/abb-01-blank.svg", "drawing_guide": None,
            "metadata": "curation/figures/abb-01.yaml"}
    bare = {"original": "figures/originals/abb-02.png", "reconstructed": None, "exercise": None,
            "drawing_guide": None, "metadata": None}
    return {"figures": [_manifest_entry(FIGURES[0], full, "faithful", True),
                        _manifest_entry(FIGURES[1], bare, "not-started", False)]}


def _sources() -> dict:
    out = {sid: {"file": f"sources/original-pdfs/{sid}.pdf", "sha256": "0" * 64, "bytes": 1,
                 "kind": "test", "trust": "test"} for sid in config.SOURCES}
    out[config.SKRIPT]["pages"] = 6
    return {"sources": out}


def write(root: Path, configured: Path, content) -> Path:
    """Write `content` (str → text, dict/list → JSON or YAML by suffix) at a config path rebased on root."""
    path = root / configured.relative_to(config.ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = (yaml.safe_dump(content, allow_unicode=True, sort_keys=False) if path.suffix == ".yaml"
                   else json.dumps(content, ensure_ascii=False, indent=2))
    path.write_text(content, encoding="utf-8")
    return path


def build_tree(root: Path) -> Path:
    write(root, config.STRUCTURE_YAML, STRUCTURE)
    write(root, config.FIGURES_YAML, {"figures": FIGURES})
    write(root, config.FIGURE_META_DIR / "abb-01.yaml", FIGURE_META)
    write(root, config.MANIFEST, _sources())
    for fig in FIGURES:
        write(root, config.FIG_ORIGINALS / f"{fig['id']}.png", "PNG-Platzhalter")
    write(root, config.FIG_RECONSTRUCTED / "abb-01.svg", SVG)
    write(root, config.FIG_EXERCISES / "abb-01-blank.svg", SVG.replace('class="answer"', 'class="answer" opacity="0"'))
    write(root, config.FIG_MANIFEST, _figures_manifest())
    write(root, config.CONTENT / "README.md", "# Inhalt\n\n- [Kapitel 1](01-test/README.md)\n")
    write(root, config.CONTENT / "01-test" / "README.md", "# Kapitel 1\n\n- [1.1](1.1-erster-abschnitt.md)\n")
    write(root, config.CONTENT / "01-test" / "1.1-erster-abschnitt.md", SECTION_11)
    write(root, config.CONTENT / "01-test" / "1.2-zweiter-abschnitt.md", SECTION_12)
    write(root, config.CONTENT / "01-test" / "literatur.md", LITERATURE)
    write(root, config.EXAMS / "questions.json", [QUESTION])
    write(root, config.EXAMS / "topic-mapping.json", TOPIC_MAPPING)
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Root of a fresh, valid fixture tree."""
    return build_tree(tmp_path / "repo")
