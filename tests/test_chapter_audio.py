from pathlib import Path

import pytest

from pipeline import chapter_audio, release_bundle
from pipeline.content_files import ChapterFiles

CHAPTERS = [ChapterFiles("02-x","Industrielle Innovation",[])]


def test_rename_keeps_audio_bytes_and_release_uses_audio_folder(tmp_path: Path):
    original = tmp_path / "Kap2.m4a"
    original.write_bytes(b"recording")
    before = chapter_audio.digest(original)
    renamed = chapter_audio.rename(tmp_path,CHAPTERS)[2]
    assert renamed.name == "GIL-2-Audio-Industrielle-Innovation.m4a"
    assert chapter_audio.digest(renamed) == before
    assert chapter_audio.rename(tmp_path,CHAPTERS)[2] == renamed
    assets = release_bundle.audio_assets(tmp_path,CHAPTERS)
    release = release_bundle.plan(assets,release_bundle.places(CHAPTERS))
    assert list(release.complete) == ["GIL-Wissensbasis-komplett/6-Audio/GIL-2-Audio-Industrielle-Innovation.m4a"]
    assert list(release.bundles)[0].stem == "GIL-Audio-je-Kapitel"


def test_ambiguous_audio_stops_before_any_rename(tmp_path: Path):
    (tmp_path / "Kap2.m4a").write_bytes(b"one")
    (tmp_path / "GIL-2-Audio-Industrielle-Innovation.mp3").write_bytes(b"two")
    with pytest.raises(ValueError,match="Mehrere Audios"):
        chapter_audio.rename(tmp_path,CHAPTERS)
    assert (tmp_path / "Kap2.m4a").read_bytes() == b"one"


def test_unknown_chapter_and_noncanonical_release_name_are_rejected(tmp_path: Path):
    (tmp_path / "Kap2.m4a").write_bytes(b"one")
    with pytest.raises(ValueError,match="umbenennen"):
        release_bundle.audio_assets(tmp_path,CHAPTERS)
    with pytest.raises(ValueError,match="unbekanntes Kapitel"):
        chapter_audio.rename(tmp_path,[])
    assert release_bundle.audio_assets(tmp_path / "missing",CHAPTERS) == []
