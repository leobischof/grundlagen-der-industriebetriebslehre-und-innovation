"""Markdown → print HTML: script pictures never reach the PDF, layout details of the converter.

Needs the `pipeline` extra (PyMuPDF, markdown); skipped where only the core is installed (CI)."""
from __future__ import annotations

import pytest

pytest.importorskip("pymupdf")
pytest.importorskip("markdown")

from pipeline import config, figure_publish  # noqa: E402
from pipeline.pdf_html import Assets, convert  # noqa: E402

SOURCE = config.CONTENT / "08-x" / "8.2-x.md"        # figure links resolve against content/<chapter>/


def _html(text: str, assets: Assets | None = None) -> str:
    return convert(text, SOURCE, assets or Assets()).html


def test_reconstructed_figure_embeds_the_svg_never_the_png():
    assets = Assets()
    out = _html("![Abbildung 45: Typologie](../../figures/originals/abb-45.png)\n*Abbildung 45*\n", assets)
    assert '<div class="fig"' in out and 'class="caption"' in out
    assert all(name.endswith(".svg") for name in assets.files)
    assert len(assets.files) == 1


def test_figure_without_reconstruction_becomes_a_stand_in(monkeypatch):
    # every figure may be redrawn by now: pretend this one is not
    monkeypatch.setattr(figure_publish, "reconstruction", lambda fig_id: None)
    assets = Assets()
    out = _html("![Abbildung 23: Geschichte](../../figures/originals/abb-23.png)\n", assets)
    assert 'class="stand-in"' in out and figure_publish.NOT_PRINTED in out
    assert assets.files == {}


def test_ordered_lists_keep_their_start_number():
    out = _html("2. zwei\n\nText\n\n3. drei\n")
    assert '<ol start="2">' in out and '<ol start="3">' in out


def test_list_right_after_a_text_line_is_a_list():
    assert "<ul>" in _html("Die Aufgaben:\n- eins\n- zwei\n")


def test_sub_paragraph_is_small_print_and_numbered_bold_line_is_a_task():
    out = _html("**1. Erklären Sie X.**\n\n<sub>Quelle · Thema</sub>\n")
    assert '<p class="task"><strong>1. ' in out
    assert '<p class="small">Quelle · Thema</p>' in out


def test_dead_link_list_items_vanish_and_prose_links_keep_their_label():
    out = _html("*Abb. 45* · [Rekonstruktion](../x.svg) · [Zeichenübung](../y.md)\n\nSiehe [2.5](2.5-a.md).\n")
    assert "Rekonstruktion" not in out and "Zeichenübung" not in out
    assert "Siehe 2.5." in out


def test_tables_are_wrapped_against_the_story_blank_page_loop():
    out = _html("| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert '<div class="table"><table>' in out and "</table></div>" in out
