"""Which picture of a script figure may leave the repository (SSOT for every export).

The PNG crops under figures/originals/ are copies of the script's pictures. They stay in the
private repository as working material, but no export – PDF, Markdown/gist, NotebookLM – ever
carries one (copyright). An export shows our own reconstruction (figures/reconstructed/<id>.svg)
where there is one; otherwise a short stand-in text that names the figure, points to the
original script and – where curated – describes the figure in our own words.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import catalog, config

_ORIGINAL = re.compile(r"(?:^|/)figures/originals/([^/#?]+)\.png$")
NOT_PRINTED = "Bild des Skripts hier nicht abgedruckt (Urheberrecht) – siehe Original-Skript"


def original_id(target: str) -> str | None:
    """Figure id of a link into figures/originals/ ('../../figures/originals/abb-45.png' → 'abb-45')."""
    m = _ORIGINAL.search(target.split("#", 1)[0])
    return m.group(1) if m else None


def reconstruction(fig_id: str) -> Path | None:
    """Our own SVG of the figure, the only picture an export may show."""
    path = config.FIG_RECONSTRUCTED / f"{fig_id}.svg"
    return path if path.is_file() else None


def _meta_text(fig_id: str, key: str) -> str:
    return " ".join(str(catalog.figure_meta(fig_id).get(key) or "").split())


def description(fig_id: str) -> str:
    """Curated description in our own words (curation/figures/<id>.yaml), '' if none yet."""
    return _meta_text(fig_id, "description")


def stand_in(fig_id: str) -> str:
    """One line of plain text in place of a figure that has no reconstruction."""
    text = description(fig_id)
    return f"{NOT_PRINTED}. Beschreibung: {text}" if text else f"{NOT_PRINTED}."


def in_words(fig_id: str) -> str:
    """The figure for a text-only export (NotebookLM, other learning tools): no picture at all,
    not even our SVG, so the stand-in plus what the figure says (curated `meaning`)."""
    meaning = _meta_text(fig_id, "meaning")
    return f"{stand_in(fig_id)} Aussage: {meaning}" if meaning else stand_in(fig_id)


def input_files(fig_id: str) -> list[Path]:
    """Files whose change alters what an export shows for this figure (for render caches)."""
    svg = reconstruction(fig_id)
    meta = config.FIGURE_META_DIR / f"{fig_id}.yaml"
    return [p for p in (svg, meta) if p is not None and p.is_file()]
