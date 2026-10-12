"""One rule decides which figures get a drawing exercise and a sketch card: figures only, asked or relevant."""
from __future__ import annotations

from pipeline import generate_exercises
from pipeline.sketch_scope import worth_sketching


def test_asked_or_relevant_figures_are_worth_sketching():
    asked = {"abb-01": ["frage-1"]}
    assert worth_sketching("abb-01", "figure", None, asked)
    assert worth_sketching("abb-02", "figure", "hoch", asked)
    assert worth_sketching("abb-03", "figure", "mittel", asked)
    assert not worth_sketching("abb-04", "figure", "niedrig", asked)
    assert not worth_sketching("abb-05", "figure", None, asked)


def test_tables_and_formulas_never_even_when_asked():
    asked = {"tab-01": ["frage-1"], "formel-x": ["frage-2"]}
    assert not worth_sketching("tab-01", "table", "hoch", asked)
    assert not worth_sketching("formel-x", "formula", "hoch", asked)


def test_exercise_stage_reads_relevance_from_the_curated_metadata(monkeypatch):
    levels = {"abb-10": "mittel", "abb-11": "niedrig"}
    monkeypatch.setattr(generate_exercises.catalog, "figure_meta",
                        lambda fid: {"exam_relevance": {"level": levels[fid]}})
    assert generate_exercises.in_scope({"id": "abb-10", "kind": "figure"}, {})
    assert not generate_exercises.in_scope({"id": "abb-11", "kind": "figure"}, {})
    assert generate_exercises.in_scope({"id": "abb-11", "kind": "figure"}, {"abb-11": ["frage-1"]})
