"""A learning guide is exported with every picture of its chapter, placed where it is explained."""
from __future__ import annotations

import pytest

from pipeline import guide_figures

FIGURES = {
    "abb-01": {"id": "abb-01", "kind": "figure", "number": 1, "title": "Eins", "pdf_page": 10},
    "abb-02": {"id": "abb-02", "kind": "figure", "number": 2, "title": "Zwei", "pdf_page": 11},
    "tab-01": {"id": "tab-01", "kind": "table", "number": 1, "title": "Tafel", "pdf_page": 12},
}

GUIDE = """---
title: Leitfaden
---
# Lernleitfaden

## Lernziele

1. Abbildung 1 zeichnen.
2. Tabelle 1 nennen.

## Kernbegriffe

| Begriff | Erklärung |
|---|---|
| Eins | siehe Abbildung 1 |

## Zusammenhänge und Strukturen

**Eins (Abbildung 1)**: erster Satz,
zweite Zeile.

- Punkt mit Abbildung 2
- zweiter Punkt

- dritter Punkt nach Leerzeile

Schluss.

## Abbildungen, die du zeichnen können solltest

- Abbildung 1 – Eins

## Selbsttest

1. Erkläre Tabelle 1.
"""


@pytest.fixture(autouse=True)
def fake_catalog(monkeypatch):
    monkeypatch.setattr(guide_figures.catalog, "figure", lambda fid: FIGURES[fid])
    monkeypatch.setattr(guide_figures.catalog, "printed_page", lambda page: page - 2)


def _embed() -> list[str]:
    return guide_figures.embed(GUIDE, ["abb-01", "abb-02", "tab-01"]).split("\n")


def test_picture_follows_the_explaining_paragraph_not_the_glossary():
    lines = _embed()
    at = lines.index("![Abbildung 1: Eins](../../figures/originals/abb-01.png)")
    assert lines[at - 2] == "zweite Zeile."
    assert lines[at + 2] == "*Abbildung 1: Eins – Skript S. 8 (PDF 10)*"
    assert lines.count("![Abbildung 1: Eins](../../figures/originals/abb-01.png)") == 1


def test_picture_after_the_whole_list_even_across_blank_lines():
    lines = _embed()
    at = lines.index("![Abbildung 2: Zwei](../../figures/originals/abb-02.png)")
    assert lines[at - 2] == "- dritter Punkt nach Leerzeile"


def test_picture_named_only_in_tasks_goes_to_the_rest_of_the_figure_section():
    lines = _embed()
    rest = lines.index(guide_figures.REST_HEADING)
    assert lines.index("- Abbildung 1 – Eins") < rest < lines.index("## Selbsttest")
    assert lines[rest + 2] == "![Tabelle 1: Tafel](../../figures/originals/tab-01.png)"


def test_guide_keeps_frontmatter_and_text_and_skips_embedded_pictures():
    out = guide_figures.embed(GUIDE, ["abb-01"])
    assert out.startswith("---\ntitle: Leitfaden\n---\n# Lernleitfaden\n")
    assert guide_figures.embed(out, ["abb-01"]) == out


def test_chapter_figures_are_the_embeds_of_its_script_files(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text("![x](../../figures/originals/abb-02.png)\n[Original](../../figures/originals/formel-x.png)\n",
                 encoding="utf-8")
    b.write_text("![y](../../figures/originals/abb-01.png)\n![x](../../figures/originals/abb-02.png)\n",
                 encoding="utf-8")
    assert guide_figures.chapter_figures([a, b]) == ["abb-02", "abb-01"]
