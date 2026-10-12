"""Flat Markdown export: only our SVGs leave the repository, links into it disappear cleanly."""
from __future__ import annotations

from pathlib import Path

from pipeline import content_files, export_markdown, figure_publish

# abb-45 has a reconstruction (figures/reconstructed/abb-45.svg), abb-23 has none.
CAPTION = ("![Abbildung 45: Typologie](../../figures/originals/abb-45.png)\n\n"
           "*Abbildung 45 – Skript S. 119* · [Rekonstruktion](../../figures/reconstructed/abb-45.svg)"
           " · [Zeichenübung](../../learning/drawing-exercises/abb-45-zeichenuebung.md)")


def test_figures_show_the_svg_next_to_the_file_and_dead_link_items_vanish():
    used: set[str] = set()
    out = export_markdown.flatten(CAPTION, "", used)
    assert out == ("![Abbildung 45: Typologie](abb-45.svg)\n\n"
                   "*Abbildung 45 – Skript S. 119* · [Rekonstruktion](abb-45.svg)")
    assert used == {"abb-45.svg"}


def test_figure_without_reconstruction_becomes_stand_in_text_never_png():
    used: set[str] = set()
    out = export_markdown.flatten("![Abbildung 23: Geschichte](../../figures/originals/abb-23.png)", "", used)
    assert out == f"*{figure_publish.stand_in('abb-23')}*"
    assert ".png" not in out and used == set()


def test_text_link_to_an_original_keeps_only_its_label():
    out = export_markdown.flatten("([Original](../../figures/originals/abb-45.png))", "", set())
    assert out == "(Original)"


def test_base_url_makes_figure_links_absolute():
    out = export_markdown.flatten("![Abb. 45](../figures/originals/abb-45.png)", "https://x.test/raw/", set())
    assert out == "![Abb. 45](https://x.test/raw/abb-45.svg)"


def test_prose_links_keep_their_text_and_external_links_and_footnotes_stay():
    text = "Siehe [Abschnitt 2.5](2.5-arten.md#a), [DOI](https://doi.org/1) und Fußnote.[^58]"
    assert export_markdown.flatten(text, "", set()) == "Siehe Abschnitt 2.5, [DOI](https://doi.org/1) und Fußnote.[^58]"


def test_export_never_names_a_png():
    files, used = export_markdown.build("", "2026-01-01")
    assert all(name.startswith("GIL-") for name in files)
    assert {"GIL-Gesamtskript.md", "GIL-Pruefungsfragen.md"} <= set(files)
    assert all(name.endswith(".svg") for name in used)
    assert not any("figures/originals" in text or ".png)" in text for text in files.values())


def test_sections_are_ordered_numerically(tmp_path: Path):
    chapter = tmp_path / "02-innovation"
    chapter.mkdir()
    for name in ("2.10-z.md", "2.2-b.md", "02-innovation-literatur.md", "02-innovation-ueberblick.md"):
        (chapter / name).write_text("---\ntitle: Innovation\n---\n# x\n", encoding="utf-8")
    (found,) = content_files.discover(tmp_path, guides_root=tmp_path)
    assert found.title == "Innovation"
    assert found.guide is None
    assert [p.name for p in found.files] == ["02-innovation-ueberblick.md", "2.2-b.md", "2.10-z.md", "02-innovation-literatur.md"]
