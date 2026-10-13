"""Which content/ files make up a chapter, in reading order (shared by every export).

A chapter directory is `NN-slug`; its files are the overview (`NN-slug-ueberblick.md`), the
sections in numeric order (2.1, 2.2, … 2.10 – not string order) and `NN-slug-literatur.md`. Deliberately free of PDF and
image libraries, so light stages and CI tests can use it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import config
from .qa_markdown import split_frontmatter

FOOTER = "Inoffizielle Lernunterlage · Skript 2024/25 (v2.0) · Stand {today}"
_SECTION_FILE = re.compile(r"^(\d+)\.(\d+)-.*\.md$")
_CHAPTER_DIR = re.compile(r"^\d\d-")


# --- export names (PDF, Markdown, NotebookLM, release assets) ------------------
# "GIL" = Grundlagen der Industriebetriebslehre. The label is what a person reads (PDF title,
# release asset label); the stem is the file name. Stems are plain ASCII with hyphens because
# GitHub rewrites spaces, umlauts and dashes in release asset names to dots.
PREFIX = "GIL"
_ASCII = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss", "–": "-"})


@dataclass(frozen=True)
class ExportName:
    stem: str                                # file name without extension
    label: str                               # human title


def _named(label: str) -> ExportName:
    stem = re.sub(r"[^A-Za-z0-9]+", "-", label.translate(_ASCII)).strip("-")
    return ExportName(stem, label)


def chapter_number(slug: str) -> int:
    """'02-industrielle-innovation' → 2 (chapter 0 is the introduction)."""
    return int(slug[:2])


def chapter_export(slug: str, title: str) -> ExportName:
    """'GIL-2-Skriptkapitel – Industrielle Innovation' / GIL-2-Skriptkapitel-Industrielle-Innovation."""
    return _named(f"{PREFIX}-{chapter_number(slug)}-Skriptkapitel – {title}")


def summary_export(slug: str, title: str) -> ExportName:
    return _named(f"{PREFIX}-{chapter_number(slug)}-Zusammenfassung – {title}")


def notebook_export(slug: str, title: str) -> ExportName:
    return _named(f"{PREFIX}-{chapter_number(slug)}-NotebookLM-Kontext – {title}")


def anki_export(slug: str, title: str) -> ExportName:
    return _named(f"{PREFIX}-{chapter_number(slug)}-Anki – {title}")


COMPLETE = _named(f"{PREFIX} Gesamtskript")
SUMMARY_COMPLETE = _named(f"{PREFIX} Zusammenfassung gesamt")
EXAMS = _named(f"{PREFIX} Prüfungsfragen")
ANKI_COMPLETE = _named(f"{PREFIX} Anki-Karteikarten")   # collection: every chapter, one sub-deck each
# The same cards as a whole Anki collection (.colpkg). Importing one REPLACES the user's
# collection, so the name says so: only for an empty or a separate Anki profile.
ANKI_PROFILE = _named(f"{PREFIX} Anki-Sammlung (ersetzt alles)")

# Release bundles (stage "release"): the per-chapter files of one kind in one zip, and the
# whole release in one zip sorted into folders.
SCRIPT_CHAPTERS = _named(f"{PREFIX} Skriptkapitel – je Kapitel")
SUMMARY_CHAPTERS = _named(f"{PREFIX} Zusammenfassung – je Kapitel")
NOTEBOOKS = _named(f"{PREFIX} NotebookLM-Kontext – je Kapitel")
ANKI_CHAPTERS = _named(f"{PREFIX} Anki – je Kapitel")
RELEASE_COMPLETE = _named(f"{PREFIX} Wissensbasis komplett")

# Each stage that produces release assets lists them in its build directory, one
# "file<TAB>label" per line; `gh release upload "<dir>/<file>#<label>"` takes the label.
ASSET_LIST = "release-assets.tsv"


def asset_label(name: str, label: str) -> str:
    """The label a download shows, with the file's ending: a reader must see that
    "GIL-2-Skriptkapitel – Industrielle Innovation" is a .pdf and the Anki package an .apkg."""
    suffix = Path(name).suffix
    return label if not suffix or label.endswith(suffix) else f"{label}{suffix}"


def write_asset_list(out_dir: Path, assets: list[tuple[str, str]]) -> None:
    """assets: (file name in out_dir, human label); the label gets the file's ending."""
    text = "".join(f"{name}\t{asset_label(name, label)}\n" for name, label in assets)
    (out_dir / ASSET_LIST).write_bytes(text.encode("utf-8"))


@dataclass
class ChapterFiles:
    slug: str
    title: str
    files: list[Path]                        # overview, sections in numeric order, literature
    guide: Path | None = None                # learning guide (summary), None if not written yet

    @property
    def export(self) -> ExportName:
        return chapter_export(self.slug, self.title)

    @property
    def summary(self) -> ExportName:
        return summary_export(self.slug, self.title)


def _section_order(path: Path) -> tuple[int, int]:
    m = _SECTION_FILE.match(path.name)
    return (int(m.group(1)), int(m.group(2))) if m else (10**6, 0)


def discover(content_root: Path, guides_root: Path | None = None) -> list[ChapterFiles]:
    """Chapter directories in slug order; files in reading order; empty chapters skipped.
    `guides_root` (default learning/chapters) holds the chapters' learning guides."""
    guides_root = guides_root or config.CHAPTER_GUIDES
    chapters = []
    for directory in sorted(p for p in content_root.iterdir() if p.is_dir() and _CHAPTER_DIR.match(p.name)):
        readme = directory / config.chapter_overview_name(directory.name)
        literature = directory / config.chapter_literature_name(directory.name)
        sections = sorted((p for p in directory.glob("*.md") if _SECTION_FILE.match(p.name)), key=_section_order)
        files = [p for p in (readme, *sections, literature) if p.exists()]
        if not files:
            continue
        meta = split_frontmatter(readme.read_text(encoding="utf-8"))[0] if readme.exists() else None
        guide = guides_root / config.chapter_guide_name(directory.name)
        chapters.append(ChapterFiles(directory.name, str((meta or {}).get("title") or directory.name), files,
                                     guide if guide.is_file() else None))
    return chapters
