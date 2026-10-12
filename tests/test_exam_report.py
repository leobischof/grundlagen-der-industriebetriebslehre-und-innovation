"""Question collection layout: the full task is the main text, everything else stays small."""
from __future__ import annotations

from pipeline import catalog, config, exam_report

QUESTION = {"id": "frage-2025-04-09-2", "number": 2, "exam_date": "2025-04-09",
            "wording": "PLZ", "prompt": "Skizzieren Sie den Produktlebenszyklus.", "points": None,
            "topics": ["plz"], "sections": ["2.5.1"], "figures": ["abb-08"],
            "competencies": ["zeichnen"], "script_coverage": "voll", "notes": None}


def test_prompt_is_the_bold_main_line_and_the_source_wording_is_small():
    block = exam_report._question_block(QUESTION, {"plz": "Produktlebenszyklus"})
    first, _, meta = block.split("\n")
    assert first == "**2. Skizzieren Sie den Produktlebenszyklus.**"
    assert meta.startswith("<sub>Originalwortlaut: „PLZ“") and meta.endswith("</sub>")
    assert "Thema: Produktlebenszyklus" in meta and "Skript 2.5.1" in meta


def test_figures_never_link_the_script_screenshot():
    with_svg = next(f["id"] for f in catalog.figures()
                    if (config.FIG_RECONSTRUCTED / f"{f['id']}.svg").exists())
    without_svg = next(f["id"] for f in catalog.figures()
                       if not (config.FIG_RECONSTRUCTED / f"{f['id']}.svg").exists())
    assert exam_report._figure_ref(with_svg).endswith(f"(../figures/reconstructed/{with_svg}.svg)")
    assert "](" not in exam_report._figure_ref(without_svg)
    assert "figures/originals" not in exam_report._figure_ref(with_svg) + exam_report._figure_ref(without_svg)
