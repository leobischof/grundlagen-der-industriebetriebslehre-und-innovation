"""Stage "exercises": drawing exercises from the vector reconstructions (layer D).

For every figures/reconstructed/<id>.svg worth sketching (sketch_scope) this writes
  figures/exercises/<id>-blank.svg        – answers removed, placeholders kept (svg_blank)
  learning/drawing-exercises/<id>-zeichenuebung.md – German step-by-step guide (drawing_guide)
Both are pure functions of the committed SVG and curation/figures/<id>.yaml, so
no cache is needed: outputs are rewritten only when their text changes. A figure that is
not (or no longer) worth sketching loses its two outputs – they are this stage's own
derived files, so the selection rule alone decides whether they exist.
Exercises whose SVG has disappeared are left alone and reported, never deleted:
the QA stage flags them and a human decides.
"""
from __future__ import annotations

from . import catalog, config, drawing_guide, sketch_scope
from .cache import write_if_changed
from .svg_blank import blank_svg

GUIDES = config.DRAWING_GUIDES


def _wanted_ids(pages: str | None) -> set[str] | None:
    """Figure ids on the selected PDF pages, None when no selection was given."""
    if not pages:
        return None
    from .pages import parse_pages
    last = max(f["pdf_page"] for f in catalog.figures())
    selected = set(parse_pages(pages, last))
    return {f["id"] for f in catalog.figures() if f["pdf_page"] in selected}


def _paths(fid: str) -> list:
    return [config.FIG_EXERCISES / f"{fid}-blank.svg", GUIDES / config.drawing_guide_name(fid)]


def in_scope(fig: dict, by_figure: dict) -> bool:
    level = (catalog.figure_meta(fig["id"]).get("exam_relevance") or {}).get("level")
    return sketch_scope.worth_sketching(fig["id"], fig["kind"], level, by_figure)


def _outputs(fid: str, svg_text: str) -> list[tuple]:
    blank, removed = blank_svg(svg_text)
    blank_path, guide_path = _paths(fid)
    return [(blank_path, blank, removed), (guide_path, drawing_guide.render(fid), None)]


def _drop(fid: str, dry_run: bool) -> int:
    """Remove the exercise of a figure not worth sketching; returns the number of files."""
    gone = 0
    for path in _paths(fid):
        if not path.exists():
            continue
        if dry_run:
            print(f"[exercises] würde {path.relative_to(config.ROOT).as_posix()} entfernen")
        else:
            path.unlink()
        gone += 1
    return gone


def _orphans() -> list[str]:
    svgs = {p.stem for p in config.FIG_RECONSTRUCTED.glob("*.svg")}
    blanks = {p.stem.removesuffix("-blank") for p in config.FIG_EXERCISES.glob("*-blank.svg")}
    return sorted(blanks - svgs)


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    # `force` has nothing to bypass: every run recomputes and compares the text.
    known = {f["id"]: f for f in catalog.figures()}
    by_figure = sketch_scope.by_figure()
    wanted = _wanted_ids(pages)
    written = unchanged = removed_files = 0
    problems = []
    for svg in sorted(config.FIG_RECONSTRUCTED.glob("*.svg")):
        fid = svg.stem
        if wanted is not None and fid not in wanted:
            continue
        if fid not in known:
            problems.append(f"{fid}: keine kuratierte Abbildung in curation/figures.yaml – übersprungen")
            continue
        if not in_scope(known[fid], by_figure):
            removed_files += _drop(fid, dry_run)
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
        print(f"[exercises] geschrieben={written} unverändert={unchanged} entfernt={removed_files}")
    return 0
