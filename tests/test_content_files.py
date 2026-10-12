"""Export names: one convention ("GIL …") for PDFs, Markdown, NotebookLM and release assets."""
from __future__ import annotations

from pipeline import content_files, figure_publish


def test_chapter_names_are_ascii_stems_with_a_readable_label():
    name = content_files.chapter_export("06-ausgewaehlte-innovationsprozesse", "Ausgewählte Innovationsprozesse")
    assert name.stem == "GIL-Skriptkapitel-6-Ausgewaehlte-Innovationsprozesse"
    assert name.label == "GIL Skriptkapitel 6 – Ausgewählte Innovationsprozesse"


def test_summary_and_notebook_names_follow_the_same_pattern():
    assert content_files.summary_export("02-x", "Industrielle Innovation").stem == \
        "GIL-Zusammenfassung-Kapitel-2-Industrielle-Innovation"
    assert content_files.notebook_export("02-x", "Industrielle Innovation").stem == \
        "GIL-NotebookLM-Kontext-Kapitel-2-Industrielle-Innovation"


def test_collection_names():
    assert content_files.COMPLETE.stem == "GIL-Gesamtskript"
    assert content_files.SUMMARY_COMPLETE.stem == "GIL-Zusammenfassung-gesamt"
    assert (content_files.EXAMS.stem, content_files.EXAMS.label) == ("GIL-Pruefungsfragen", "GIL Prüfungsfragen")


def test_original_figure_ids_and_stand_in_text():
    assert figure_publish.original_id("../../figures/originals/abb-45.png") == "abb-45"
    assert figure_publish.original_id("../../figures/reconstructed/abb-45.svg") is None
    assert figure_publish.reconstruction("abb-45") is not None
    assert figure_publish.stand_in("abb-23").startswith(figure_publish.NOT_PRINTED)
