"""Sketch cards: only exam-relevant figures, never tables or formula boxes, never the script's picture."""
from __future__ import annotations

from pipeline import anki_sketch


def _fig(fid: str, kind: str = "figure", relevance: str | None = None) -> dict:
    return {"id": fid, "kind": kind, "exam_relevance": relevance, "title": f"Titel {fid}",
            "label": "Abbildung 8", "pdf_page": 30, "section": "2.1", "subsection": "2.1.1",
            "chapter": "02", "files": {"original": f"figures/originals/{fid}.png"}}


def test_select_keeps_asked_and_curated_figures_only():
    figures = [_fig("abb-01"), _fig("abb-02", relevance="hoch"), _fig("abb-03", relevance="mittel"),
               _fig("abb-04"), _fig("tab-01", kind="table"), _fig("formel-x", kind="formula")]
    by_figure = {"abb-01": ["frage-1"], "tab-01": ["frage-2"], "formel-x": ["frage-3"]}
    chosen = [f["id"] for f in anki_sketch.select(figures, by_figure)]
    assert chosen == ["abb-01", "abb-02", "abb-03"]


def test_card_shows_task_our_svg_and_the_exam_questions():
    asked = [{"date": "2026-04-29", "prompt": "Skizzieren Sie …", "figures": ["abb-08"]}]
    (sketch,) = anki_sketch.sketches([_fig("abb-08")], {"abb-08": ["frage-1"]}, asked, {"02": "02-x"})
    card = sketch.card()
    assert (card.kind, card.chapter, card.key) == ("skizze", "02-x", "abb-08")
    assert card.front == "Skizzieren Sie „Titel abb-08“ (Abbildung 8)."
    assert "](gil-abb-08.svg)" in card.back and ".png" not in card.back
    assert "29.04.2026: Skizzieren Sie …" in card.back
    assert [p.name for p in card.media] == ["abb-08.svg"] and "Abschnitt 2.1.1" in card.source


def test_figure_without_reconstruction_gets_the_stand_in_text():
    (sketch,) = anki_sketch.sketches([_fig("abb-nicht-da", relevance="hoch")], {}, [], {"02": "02-x"})
    card = sketch.card()
    assert card.media == () and "nicht abgedruckt" in card.back and "<img" not in card.back
