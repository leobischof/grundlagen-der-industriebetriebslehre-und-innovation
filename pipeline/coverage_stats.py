"""Numbers for the coverage report – counted from the committed files, never assumed.

Each function returns plain dicts/lists so the renderer (coverage.py) only
formats. Everything that does not exist yet counts as 0 / "fehlt"; nothing is
inferred from the plan.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import ailog, config
from .progress_store import DRAWING
from .qa_checks_figures import PRIORITY_FIGURES, embedded_ids
from .qa_checks_structure import content_pages, toc_pages
from .qa_markdown import footnotes
from .qa_repo import RepoView


def pages(view: RepoView) -> dict:
    total = view.total_pages or 0
    skipped = set(view.skipped_pages)
    assigned = toc_pages(view) - skipped
    covered = content_pages(view) & assigned
    return {
        "total": total,
        "skipped": len(skipped),
        "assigned": len(assigned),
        "ocr_layer": len(view.ocr_pages),
        "ocr_weak": sorted(r["page"] for r in view.ocr_pages if (r.get("quality") or {}).get("low")),
        "in_content": len(covered),
        "missing_in_content": sorted(assigned - covered),
    }


def sections(view: RepoView) -> dict:
    expected = [e for e in view.entries if e.kind in ("section", "frontmatter") and e.level == 2]
    have = {str(f.meta["id"]): f for f in view.section_files}
    statuses = Counter(str((f.meta.get("quality") or {}).get("status", "–")) for f in view.section_files)
    per_chapter = []
    for ch in view.structure.get("chapters", []):
        exp = [e for e in expected if e.chapter_id == str(ch["id"])]
        files = [have[f"sec-{e.number}"] for e in exp if f"sec-{e.number}" in have]
        per_chapter.append({
            "id": str(ch["id"]), "title": ch["title"], "expected": len(exp), "files": len(files),
            "figures": sum(len(f.meta.get("figures") or []) for f in files),
            "questions": len({q for f in files for q in f.meta.get("exam_questions") or []}),
        })
    return {
        "expected": len(expected),
        "files": sum(1 for e in expected if f"sec-{e.number}" in have),
        "missing": [f"{e.number} {e.title}" for e in expected if f"sec-{e.number}" not in have],
        "status": dict(statuses),
        "per_chapter": per_chapter,
    }


def _layer(view: RepoView, configured: Path, name: str) -> bool:
    return (view.path(configured) / name).exists()


def figures(view: RepoView) -> dict:
    figs = view.figures
    rows = []
    embedded = embedded_ids(view)
    for f in figs:
        fid = f["id"]
        meta = view.figure_meta(fid)
        status = (meta.get("reconstruction") or {}).get("status", "not-started")
        rows.append({
            "id": fid, "kind": f["kind"], "title": f["title"],
            "png": _layer(view, config.FIG_ORIGINALS, f"{fid}.png"),
            "meta": bool(meta),
            "svg": _layer(view, config.FIG_RECONSTRUCTED, f"{fid}.svg"),
            "status": status,
            "exercise": _layer(view, config.FIG_EXERCISES, f"{fid}-blank.svg"),
            "guide": _layer(view, config.DRAWING_GUIDES, config.drawing_guide_name(fid)),
            "embedded": fid in embedded,
            "exam": (meta.get("exam_relevance") or {}).get("level"),
        })
    count = lambda key: sum(1 for r in rows if r[key])  # noqa: E731
    return {
        "total": len(rows),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "png": count("png"), "meta": count("meta"), "svg": count("svg"),
        "faithful": sum(1 for r in rows if r["svg"] and r["status"] == "faithful"),
        "needs_review": sorted(r["id"] for r in rows if r["status"] == "needs_review"),
        "exercise": count("exercise"), "guide": count("guide"), "embedded": count("embedded"),
        "priority": [r for r in rows if r["id"] in PRIORITY_FIGURES],
        "rows": rows,
    }


def footnote_stats(view: RepoView) -> dict:
    refs = defs = anchored = 0
    for f in view.content_files:
        r, d = footnotes(f.body)
        refs += len(set(r))
        defs += len(set(d))
        anchored += len(set(r) & set(d))
    unanchored_meta = sum(int((f.meta.get("quality") or {}).get("footnotes_unanchored") or 0)
                          for f in view.section_files)
    return {"refs": refs, "defs": defs, "anchored": anchored, "unanchored_meta": unanchored_meta}


def questions(view: RepoView) -> dict:
    qs = view.questions
    if qs is None:
        return {"built": False}
    by_section = (view.topic_mapping or {}).get("by_section", {})
    mapped = {q for ids in by_section.values() for q in ids}
    return {
        "built": True,
        "total": len(qs),
        "by_source": dict(Counter(str(q.get("source")) for q in qs)),
        "with_sections": sum(1 for q in qs if q.get("sections") or q.get("id") in mapped),
        "with_figures": sum(1 for q in qs if q.get("figures")),
        "drawing": sum(1 for q in qs if DRAWING in (q.get("task_types") or [])),
        "task_types": dict(Counter(t for q in qs for t in q.get("task_types") or [])),
        "sections_with_questions": len({".".join(k.split(".")[:2]) for k, v in by_section.items() if v}),
        "unmapped": sorted(str(q.get("id")) for q in qs
                           if not q.get("sections") and q.get("id") not in mapped),
    }


def flashcards(view: RepoView) -> dict:
    folder = view.path(config.LEARNING) / "flashcards"
    if not folder.exists():
        return {"built": False}
    cards, files = 0, 0
    for p in sorted(folder.rglob("*")):
        if p.suffix == ".jsonl":
            files += 1
            cards += sum(1 for s in p.read_text(encoding="utf-8").splitlines() if s.strip())
        elif p.suffix == ".json":
            files += 1
            data = json.loads(p.read_text(encoding="utf-8"))
            items = data.get("cards", []) if isinstance(data, dict) else data
            cards += len(items) if isinstance(items, list) else 0
    return {"built": True, "files": files, "cards": cards}


def ai_calls(view: RepoView) -> dict:
    return ailog.summarize(ailog.read(view.path(config.AI_LOG)))


def topic_gaps(view: RepoView, fig: dict) -> list[str]:
    """Topics of the exam mapping whose sections lack content or whose figures lack a reconstruction."""
    mapping = view.topic_mapping or {}
    have = {str(f.meta["id"]) for f in view.section_files}
    svg = {r["id"] for r in fig["rows"] if r["svg"]}
    out = []
    for t in mapping.get("topics", []):
        secs = {".".join(str(s).split(".")[:2]) for s in t.get("sections") or []}
        no_text = sorted(s for s in secs if f"sec-{s}" not in have)
        no_svg = sorted(f for f in t.get("figures") or [] if f not in svg)
        if no_text or no_svg:
            parts = ([f"Text fehlt: {', '.join(no_text)}"] if no_text else []) + \
                    ([f"ohne SVG: {', '.join(no_svg)}"] if no_svg else [])
            out.append(f"{t.get('title', t.get('id'))} – {'; '.join(parts)}")
    return out


def collect(view: RepoView) -> dict:
    fig = figures(view)
    return {"pages": pages(view), "sections": sections(view), "figures": fig,
            "footnotes": footnote_stats(view), "questions": questions(view),
            "flashcards": flashcards(view), "ai": ai_calls(view), "topic_gaps": topic_gaps(view, fig)}
