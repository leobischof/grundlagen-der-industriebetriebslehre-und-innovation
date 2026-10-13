"""Release packing: whole-course files alone, per-chapter files one zip per kind, everything in folders."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from pipeline import content_files, release_bundle
from pipeline.content_files import ChapterFiles

CHAPTERS = [ChapterFiles("01-a", "Die Industrie", []), ChapterFiles("02-b", "Industrielle Innovation", [])]


def _build(tmp_path: Path, extra: str = "") -> Path:
    """A build/ tree with what render-pdf, export-notebooklm and anki list."""
    lists = {
        "pdf": ["GIL-Gesamtskript.pdf", "GIL-1-Skriptkapitel-Die-Industrie.pdf",
                "GIL-2-Skriptkapitel-Industrielle-Innovation.pdf", "GIL-2-Zusammenfassung-Industrielle-Innovation.pdf",
                "GIL-Pruefungsfragen.pdf"],
        "notebooklm": ["GIL-2-NotebookLM-Kontext-Industrielle-Innovation.md"],
        "anki": ["GIL-Anki-Karteikarten.apkg", "GIL-Anki-Sammlung-ersetzt-alles.colpkg", "GIL-1-Anki-Die-Industrie.apkg", *([extra] if extra else [])],
    }
    root = tmp_path / "build"
    for source, names in lists.items():
        (root / source).mkdir(parents=True)
        for name in names:
            (root / source / name).write_bytes(name.encode())
        content_files.write_asset_list(root / source, [(n, Path(n).stem) for n in names])
    return root


def _plan(root: Path) -> release_bundle.Release:
    return release_bundle.plan(release_bundle.listed(root), release_bundle.places(CHAPTERS))


def test_whole_course_files_stay_single_and_chapter_files_go_into_one_zip_per_kind(tmp_path: Path):
    release = _plan(_build(tmp_path))
    assert [p.name for p, _ in release.singles] == ["GIL-Gesamtskript.pdf", "GIL-Pruefungsfragen.pdf",
                                                    "GIL-Anki-Karteikarten.apkg", "GIL-Anki-Sammlung-ersetzt-alles.colpkg"]
    assert {b.stem: len(paths) for b, paths in release.bundles.items()} == {
        "GIL-Skriptkapitel-je-Kapitel": 2, "GIL-Zusammenfassung-je-Kapitel": 1,
        "GIL-NotebookLM-Kontext-je-Kapitel": 1, "GIL-Anki-je-Kapitel": 1}


def test_complete_zip_holds_every_file_once_sorted_into_folders(tmp_path: Path):
    built = release_bundle.assets(_plan(_build(tmp_path)))
    label, data = built["GIL-Wissensbasis-komplett.zip"]
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert len(names) == 9 and all(n.startswith("GIL-Wissensbasis-komplett/") for n in names)
    assert "GIL-Wissensbasis-komplett/1-Skript/Skriptkapitel/GIL-1-Skriptkapitel-Die-Industrie.pdf" in names
    assert "GIL-Wissensbasis-komplett/5-Anki/GIL-Anki-Karteikarten.apkg" in names
    assert "GIL-Wissensbasis-komplett/4-NotebookLM-Kontext/GIL-2-NotebookLM-Kontext-Industrielle-Innovation.md" in names
    chapter_zip = zipfile.ZipFile(io.BytesIO(built["GIL-Skriptkapitel-je-Kapitel.zip"][1])).namelist()
    assert chapter_zip == ["GIL-Skriptkapitel-je-Kapitel/GIL-1-Skriptkapitel-Die-Industrie.pdf",
                           "GIL-Skriptkapitel-je-Kapitel/GIL-2-Skriptkapitel-Industrielle-Innovation.pdf"]
    assert len(built) == 9 and label.startswith("GIL Wissensbasis komplett")


def test_zips_are_byte_identical_for_equal_input(tmp_path: Path):
    root = _build(tmp_path)
    assert release_bundle.assets(_plan(root)) == release_bundle.assets(_plan(root))


def test_a_listed_file_without_a_place_stops_the_release(tmp_path: Path):
    with pytest.raises(ValueError, match="GIL-Neu.apkg"):
        _plan(_build(tmp_path, extra="GIL-Neu.apkg"))


def test_a_missing_stage_listing_is_named(tmp_path: Path):
    root = _build(tmp_path)
    (root / "anki" / content_files.ASSET_LIST).unlink()
    with pytest.raises(FileNotFoundError, match="anki"):
        release_bundle.listed(root)


def test_release_labels_carry_the_file_ending(tmp_path: Path):
    built = release_bundle.assets(_plan(_build(tmp_path)))
    assert content_files.asset_label("GIL-Anki-je-Kapitel.zip", built["GIL-Anki-je-Kapitel.zip"][0]) == \
        "GIL Anki – je Kapitel.zip"
