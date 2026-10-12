"""Which content/ files make up a chapter, in reading order (shared by every export).

A chapter directory is `NN-slug`; its files are README, the sections in numeric order
(2.1, 2.2, … 2.10 – not string order) and literatur.md. Deliberately free of PDF and
image libraries, so light stages and CI tests can use it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .qa_markdown import split_frontmatter

# Base names of the export files (PDF and Markdown), and the line every export carries.
COMPLETE_NAME = "grundlagen-industriebetriebslehre-und-innovation"
EXAMS_NAME = "pruefungsfragen"
FOOTER = "Inoffizielle Lernunterlage · Skript 2024/25 (v2.0) · Stand {today}"
_SECTION_FILE = re.compile(r"^(\d+)\.(\d+)-.*\.md$")
_CHAPTER_DIR = re.compile(r"^\d\d-")


@dataclass
class ChapterFiles:
    slug: str
    title: str
    files: list[Path]                        # README, sections in numeric order, literatur


def _section_order(path: Path) -> tuple[int, int]:
    m = _SECTION_FILE.match(path.name)
    return (int(m.group(1)), int(m.group(2))) if m else (10**6, 0)


def discover(content_root: Path) -> list[ChapterFiles]:
    """Chapter directories in slug order; files in reading order; empty chapters skipped."""
    chapters = []
    for directory in sorted(p for p in content_root.iterdir() if p.is_dir() and _CHAPTER_DIR.match(p.name)):
        readme, literature = directory / "README.md", directory / "literatur.md"
        sections = sorted((p for p in directory.glob("*.md") if _SECTION_FILE.match(p.name)), key=_section_order)
        files = [p for p in (readme, *sections, literature) if p.exists()]
        if not files:
            continue
        meta = split_frontmatter(readme.read_text(encoding="utf-8"))[0] if readme.exists() else None
        chapters.append(ChapterFiles(directory.name, str((meta or {}).get("title") or directory.name), files))
    return chapters
