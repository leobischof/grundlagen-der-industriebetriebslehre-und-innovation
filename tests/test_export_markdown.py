"""Flat Markdown export: figures stay visible, links into the repository disappear cleanly."""
from __future__ import annotations

from pathlib import Path

from pipeline import content_files, export_markdown

CAPTION = ("![Abbildung 45: Typologie](../../figures/originals/abb-45.png)\n\n"
           "*Abbildung 45 – Skript S. 119* · [Rekonstruktion](../../figures/reconstructed/abb-45.svg)"
           " · [Zeichenübung](../../learning/drawing-exercises/abb-45-zeichenuebung.md)")


def test_figures_point_next_to_the_file_and_dead_link_items_vanish():
    used: set[str] = set()
    out = export_markdown.flatten(CAPTION, "", used)
    assert out == "![Abbildung 45: Typologie](abb-45.png)\n\n*Abbildung 45 – Skript S. 119*"
    assert used == {"abb-45.png"}


def test_base_url_makes_figure_links_absolute():
    out = export_markdown.flatten("[Abb. 8](../figures/originals/abb-08.png)", "https://x.test/raw/", set())
    assert out == "[Abb. 8](https://x.test/raw/abb-08.png)"


def test_prose_links_keep_their_text_and_external_links_and_footnotes_stay():
    text = "Siehe [Abschnitt 2.5](2.5-arten.md#a), [DOI](https://doi.org/1) und Fußnote.[^58]"
    assert export_markdown.flatten(text, "", set()) == "Siehe Abschnitt 2.5, [DOI](https://doi.org/1) und Fußnote.[^58]"


def test_sections_are_ordered_numerically(tmp_path: Path):
    chapter = tmp_path / "02-innovation"
    chapter.mkdir()
    for name in ("2.10-z.md", "2.2-b.md", "02-innovation-literatur.md", "02-innovation-ueberblick.md"):
        (chapter / name).write_text("---\ntitle: Innovation\n---\n# x\n", encoding="utf-8")
    (found,) = content_files.discover(tmp_path)
    assert found.title == "Innovation"
    assert [p.name for p in found.files] == ["02-innovation-ueberblick.md", "2.2-b.md", "2.10-z.md", "02-innovation-literatur.md"]
