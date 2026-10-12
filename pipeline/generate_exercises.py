"""Stage "exercises": drawing exercises from the vector reconstructions (layer D).

For every figures/reconstructed/<id>.svg this writes
  figures/exercises/<id>-blank.svg        – answers removed, placeholders kept (svg_blank)
  learning/drawing-exercises/<id>.md      – German step-by-step guide (drawing_guide)
Both are pure functions of the committed SVG and curation/figures/<id>.yaml, so
no cache is needed: outputs are rewritten only when their text changes.
Exercises whose SVG has disappeared are left alone and reported, never deleted:
the QA stage flags them and a human decides.
"""
from __future__ import annotations

from . import catalog, config, drawing_guide
from .cache import write_if_changed
from .svg_blank import blank_svg

GUIDES = config.LEARNING / "drawing-exercises"


def _wanted_ids(pages: str | None) -> set[str] | None:
    """Figure ids on the selected PDF pages, None when no selection was given."""
    if not pages:
        return None
    from .pages import parse_pages
    last = max(f["pdf_page"] for f in catalog.figures())
    selected = set(parse_pages(pages, last))
    return {f["id"] for f in catalog.figures() if f["pdf_page"] in selected}


def _outputs(fid: str, svg_text: str) -> list[tuple]:
    blank, removed = blank_svg(svg_text)
    return [(config.FIG_EXERCISES / f"{fid}-blank.svg", blank, removed),
            (GUIDES / f"{fid}.md", drawing_guide.render(fid), None)]


def _orphans() -> list[str]:
    svgs = {p.stem for p in config.FIG_RECONSTRUCTED.glob("*.svg")}
    blanks = {p.stem.removesuffix("-blank") for p in config.FIG_EXERCISES.glob("*-blank.svg")}
    return sorted(blanks - svgs)


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    # `force` has nothing to bypass: every run recomputes and compares the text.
    known = {f["id"] for f in catalog.figures()}
    wanted = _wanted_ids(pages)
    written = unchanged = 0
    problems = []
    for svg in sorted(config.FIG_RECONSTRUCTED.glob("*.svg")):
        fid = svg.stem
        if wanted is not None and fid not in wanted:
            continue
        if fid not in known:
            problems.append(f"{fid}: keine kuratierte Abbildung in curation/figures.yaml – übersprungen")
            continue
        for path, text, removed in _outputs(fid, svg.read_text(encoding="utf-8")):
            if removed == 0:
                problems.append(f"{fid}: keine `class=\"answer\"`-Elemente – Übung wäre identisch")
            rel = path.relative_to(config.ROOT).as_posix()
            if dry_run:
                print(f"[exercises] würde {rel} schreiben")
                continue
            if write_if_changed(path, text):
                written += 1
            else:
                unchanged += 1
    for fid in _orphans():
        problems.append(f"{fid}: Übung ohne Rekonstruktion (figures/exercises/{fid}-blank.svg) – bitte prüfen")
    for p in problems:
        print(f"[exercises] Hinweis: {p}")
    if not dry_run:
        print(f"[exercises] geschrieben={written} unverändert={unchanged}")
    return 0
