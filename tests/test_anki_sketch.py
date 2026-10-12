"""Sketch deck: only exam-relevant figures, never tables or formula boxes."""
from __future__ import annotations

import pytest

# genanki belongs to the `pipeline` extra, which CI does not install.
anki_sketch = pytest.importorskip("pipeline.anki_sketch")


def _fig(fid: str, kind: str = "figure", relevance: str | None = None) -> dict:
    return {"id": fid, "kind": kind, "exam_relevance": relevance, "title": f"Titel {fid}",
            "label": "Abbildung 1", "pdf_page": 30, "section": "2.1", "subsection": "2.1.1",
            "chapter": "02", "files": {"original": f"figures/originals/{fid}.png"}}


def test_select_keeps_asked_and_curated_figures_only():
    figures = [_fig("abb-01"), _fig("abb-02", relevance="hoch"), _fig("abb-03", relevance="mittel"),
               _fig("abb-04"), _fig("tab-01", kind="table"), _fig("formel-x", kind="formula")]
    by_figure = {"abb-01": ["frage-1"], "tab-01": ["frage-2"], "formel-x": ["frage-3"]}
    chosen = [f["id"] for f in anki_sketch.select(figures, by_figure)]
    assert chosen == ["abb-01", "abb-02", "abb-03"]


def test_card_shows_prompt_image_points_and_questions():
    meta = {"drawing": {"must_know": ["Achsen beschriften"]}}
    asked = [{"date": "2026-04-29", "wording": "Skizzieren Sie …"}]
    c = anki_sketch.card(_fig("abb-01"), meta, asked)
    assert c["prompt"] == "Skizziere: Titel abb-01"
    assert c["image"] == "abb-01.png"
    assert c["must_know"] == ["Achsen beschriften"]
    assert c["questions"] == ["29.04.2026: Skizzieren Sie …"]
    assert "Abschnitt 2.1.1" in c["meta"]
