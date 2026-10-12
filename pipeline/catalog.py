"""Read access to the curated files (curation/*.yaml) – the only place that parses them.

The curated files are written by people (or by an AI pass that is logged) and
are never overwritten by the pipeline. Every stage asks this module instead of
opening the YAML itself, so a format change touches one file.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from . import config


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    # The C loader is ~10x faster; figures.yaml alone is ~300 KB of bboxes and labels.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=loader) or {}


@dataclass(frozen=True)
class Entry:
    """One heading of the canonical table of contents."""
    number: str
    title: str
    pdf_page: int
    kind: str                 # chapter | section | literature | frontmatter
    chapter_id: str
    chapter_slug: str
    end_page: int | None = None
    number_printed: str | None = None
    note: str | None = None

    @property
    def level(self) -> int:
        """1 = chapter, 2 = X.Y, 3 = X.Y.Z … (literature/frontmatter count as level 2)."""
        if self.kind in ("literature", "frontmatter"):
            return 2
        return self.number.count(".") + 1

    @property
    def section_number(self) -> str:
        """Number of the X.Y file this entry belongs to ("4.2.3" -> "4.2")."""
        if self.level <= 2:
            return self.number
        return ".".join(self.number.split(".")[:2])


@lru_cache(maxsize=1)
def structure() -> dict:
    return _load(config.STRUCTURE_YAML)


@lru_cache(maxsize=1)
def entries() -> tuple[Entry, ...]:
    """All TOC entries in document order."""
    out = []
    for ch in structure().get("chapters", []):
        for e in ch["entries"]:
            out.append(Entry(number=str(e["number"]), title=e["title"], pdf_page=int(e["pdf_page"]),
                             kind=e.get("kind", "section"), chapter_id=str(ch["id"]),
                             chapter_slug=ch["slug"], end_page=e.get("end_page"),
                             number_printed=e.get("number_printed"), note=e.get("note")))
    return tuple(out)


def chapters() -> list[dict]:
    return structure().get("chapters", [])


def skipped_pages() -> dict[int, str]:
    return {int(k): v for k, v in (structure().get("skipped_pages") or {}).items()}


def printed_page(pdf_page: int) -> int | None:
    """Printed page number, or None for the unnumbered front matter."""
    if pdf_page < config.FIRST_ARABIC_PDF_PAGE:
        return None
    return pdf_page - config.PRINTED_PAGE_OFFSET


@lru_cache(maxsize=1)
def _figures_file() -> dict:
    return _load(config.FIGURES_YAML)


def figures() -> tuple[dict, ...]:
    return tuple(_figures_file().get("figures", []))


def duplicates() -> list[dict]:
    return _figures_file().get("duplicates", [])


def figure(fig_id: str) -> dict:
    for f in figures():
        if f["id"] == fig_id:
            return f
    raise KeyError(fig_id)


def figure_meta(fig_id: str) -> dict:
    """Rich metadata (B) of one figure from curation/figures/<id>.yaml, {} if not curated yet."""
    return _load(config.FIGURE_META_DIR / f"{fig_id}.yaml")


def figure_label(f: dict) -> str:
    """Human label as printed in the script: "Abbildung 8", "Tabelle 5", "Formel"."""
    if f["kind"] == "formula":
        return "Formel"
    if f.get("number") is None:
        return "Abbildung (unbeschriftet)"
    return f"{'Abbildung' if f['kind'] == 'figure' else 'Tabelle'} {f['number']}"


@lru_cache(maxsize=1)
def exams() -> dict:
    return _load(config.EXAMS_YAML)


@lru_cache(maxsize=1)
def topics() -> dict:
    return _load(config.TOPICS_YAML)


@lru_cache(maxsize=1)
def ocr_corrections() -> dict:
    return _load(config.OCR_CORRECTIONS_YAML)
