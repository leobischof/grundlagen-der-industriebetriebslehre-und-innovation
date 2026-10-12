"""Stage "release": the release as a few downloads → build/release/ (what `gh release upload` takes).

render-pdf, export-notebooklm and anki each list what they built in their release-assets.tsv.
This stage gives every listed file its place (SINGLES, PER_CHAPTER below) and packs the release:

  whole-course files   one asset each: Gesamtskript, Zusammenfassung gesamt, Prüfungsfragen,
                       the Anki collection (.apkg, and as a whole Anki collection .colpkg)
  per-chapter files    one zip per kind ("GIL Skriptkapitel – je Kapitel.zip", …), never one
                       asset per chapter: nobody should have to click forty downloads
  everything           "GIL Wissensbasis komplett.zip": every file once, sorted into folders

  build/release/<asset>              the assets, nothing else
  build/release/release-assets.tsv   file <TAB> label, the label with the file ending (content_files)

A listed file without a place stops the stage: a new export must be given a folder here, not be
left out silently. Zips carry fixed timestamps, so unchanged inputs give byte-identical assets.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import config, content_files
from .cache import write_bytes_if_changed
from .content_files import (ANKI_CHAPTERS, ANKI_COMPLETE, ANKI_PROFILE, ASSET_LIST, COMPLETE, EXAMS, NOTEBOOKS,
                            RELEASE_COMPLETE, SCRIPT_CHAPTERS, SUMMARY_CHAPTERS, SUMMARY_COMPLETE,
                            ExportName)

OUT_DIR = config.BUILD / "release"
SOURCES = ("pdf", "notebooklm", "anki")          # build/ directories whose listings make the release
_ZIP_TIME = (2024, 1, 1, 0, 0, 0)               # fixed: an unchanged release gives byte-identical zips

# Folders of the complete zip; the numbers keep them in learning order in every file browser.
SINGLES = ((COMPLETE, "1-Skript"), (SUMMARY_COMPLETE, "2-Zusammenfassungen"),
           (EXAMS, "3-Pruefungsfragen"), (ANKI_COMPLETE, "5-Anki"), (ANKI_PROFILE, "5-Anki"))
PER_CHAPTER = ((content_files.chapter_export, SCRIPT_CHAPTERS, "1-Skript/Skriptkapitel"),
               (content_files.summary_export, SUMMARY_CHAPTERS, "2-Zusammenfassungen/Kapitel"),
               (content_files.notebook_export, NOTEBOOKS, "4-NotebookLM-Kontext"),
               (content_files.anki_export, ANKI_CHAPTERS, "5-Anki/Kapitel"))


@dataclass(frozen=True)
class Place:
    folder: str                              # folder in the complete zip
    bundle: ExportName | None                # zip it is released in; None = an asset of its own


@dataclass
class Release:
    singles: list[tuple[Path, str]]          # (file, label) released as they are
    bundles: dict[ExportName, list[Path]]    # per-chapter zips, in SOURCES order
    complete: dict[str, Path]                # path inside the complete zip → file


def places(chapters: list[content_files.ChapterFiles]) -> dict[str, Place]:
    """File stem → its place, for every name an export may produce."""
    out = {name.stem: Place(folder, None) for name, folder in SINGLES}
    for chapter in chapters:
        for namer, bundle, folder in PER_CHAPTER:
            out[namer(chapter.slug, chapter.title).stem] = Place(folder, bundle)
    return out


def listed(build_root: Path) -> list[tuple[Path, str]]:
    """(file, label) of every asset the source stages listed; a missing listing is an error."""
    out = []
    for source in SOURCES:
        listing = build_root / source / ASSET_LIST
        if not listing.is_file():
            raise FileNotFoundError(f"{listing.relative_to(build_root.parent)} fehlt – erst die Stufe für "
                                    f"build/{source} laufen lassen")
        for line in listing.read_text(encoding="utf-8").splitlines():
            name, label = line.split("\t")
            out.append((build_root / source / name, label))
    return out


def plan(assets: list[tuple[Path, str]], where: dict[str, Place]) -> Release:
    unknown = sorted(path.name for path, _ in assets if path.stem not in where)
    if unknown:
        raise ValueError("ohne Platz im Release (release_bundle.SINGLES/PER_CHAPTER): " + ", ".join(unknown))
    release = Release([], {}, {})
    for path, label in assets:
        place = where[path.stem]
        if place.bundle is None:
            release.singles.append((path, label))
        else:
            release.bundles.setdefault(place.bundle, []).append(path)
        release.complete[f"{RELEASE_COMPLETE.stem}/{place.folder}/{path.name}"] = path
    return release


def zip_bytes(files: dict[str, Path]) -> bytes:
    """files: path inside the zip → file. Sorted, fixed timestamps: equal input, equal bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname in sorted(files):
            info = zipfile.ZipInfo(arcname, date_time=_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, files[arcname].read_bytes())
    return buf.getvalue()


def assets(release: Release) -> dict[str, tuple[str, bytes]]:
    """Asset file name → (label, bytes), the complete zip first."""
    out = {f"{RELEASE_COMPLETE.stem}.zip": (f"{RELEASE_COMPLETE.label} (alles in Ordnern)",
                                            zip_bytes(release.complete))}
    for bundle, paths in release.bundles.items():
        out[f"{bundle.stem}.zip"] = (bundle.label, zip_bytes({f"{bundle.stem}/{p.name}": p for p in paths}))
    for path, label in release.singles:
        out[path.name] = (label, path.read_bytes())
    return out


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    try:
        release = plan(listed(config.BUILD), places(content_files.discover(config.CONTENT)))
    except (FileNotFoundError, ValueError) as err:
        print(f"[release] Fehler: {err}")
        return 1
    built = assets(release)
    if dry_run:
        print(f"[release] würde {len(built)} Assets nach {OUT_DIR.relative_to(config.ROOT)} schreiben")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in [p for p in OUT_DIR.iterdir() if p.is_file() and p.name not in {*built, ASSET_LIST}]:
        stale.unlink()                       # renamed asset: the old one must not be released
    changed = sum(write_bytes_if_changed(OUT_DIR / name, data) for name, (_, data) in built.items())
    content_files.write_asset_list(OUT_DIR, [(name, label) for name, (label, _) in built.items()])
    print(f"[release] {len(built)} Assets ({changed} geändert) aus {len(release.complete)} Dateien → "
          f"{OUT_DIR.relative_to(config.ROOT)}")
    return 0
