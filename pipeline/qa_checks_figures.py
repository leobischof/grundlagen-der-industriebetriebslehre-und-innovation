"""Checks: every curated figure exists in all layers it claims, and is embedded somewhere.

Layers per figure (see pipeline/extract_figures.py): (A) PNG original – always
required; (B) metadata – required for the exam-priority figures, schema-checked
wherever present; (C) SVG – required as soon as the metadata calls the
reconstruction faithful/needs_review; (D) exercise – expected for faithful SVGs.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from . import config, sketch_scope
from .qa_findings import Finding, error, info, warning
from .qa_markdown import image_targets
from .qa_repo import RepoView
from .qa_schema import FIGURE_MANIFEST_ENTRY, FIGURE_META, problems

FIGURES = "Abbildungen"
DETECTION = "Bilderkennung und Beschriftungen"
# Figures the exams ask for most (drawing tasks, see exams/frequency-analysis.md):
# their metadata (B) is mandatory, not optional.
PRIORITY_FIGURES = ("abb-08", "abb-11", "abb-15", "abb-35", "abb-37", "abb-38", "abb-44",
                    *(f"abb-{n}" for n in range(45, 52)), "abb-57", "abb-70")
RECONSTRUCTED = ("faithful", "needs_review")


def _svg_attr(svg_text: str, name: str) -> str | None:
    """Attribute of the root <svg> element (the first one in the file)."""
    m = re.search(rf'<svg\b[^>]*?\b{re.escape(name)}="([^"]*)"', svg_text, re.S)
    return m.group(1) if m else None


def embedded_ids(view: RepoView) -> set[str]:
    """Figure ids embedded in content/: as an image or in a frontmatter `figures` list."""
    out = set()
    for f in view.content_files:
        out |= {Path(t).stem for t in image_targets(f.body)}
        if f.meta:
            out |= {str(x) for x in (f.meta.get("figures") or [])}
    return out


def check_figures(view: RepoView) -> list[Finding]:
    figs = view.figures
    if not figs:
        return [error(FIGURES, "curation/figures.yaml fehlt oder enthält keine Abbildungen")]
    ids = [f["id"] for f in figs]
    out = [error(FIGURES, f"Abbildungs-ID `{i}` mehrfach in curation/figures.yaml")
           for i, n in Counter(ids).items() if n > 1]
    originals = view.path(config.FIG_ORIGINALS)
    out += [error(FIGURES, f"`{i}`: Originalausschnitt `figures/originals/{i}.png` fehlt")
            for i in ids if not (originals / f"{i}.png").exists()]
    if view.section_files:
        embedded = embedded_ids(view)
        out += [error(FIGURES, f"`{i}` ist in keiner Datei unter content/ eingebunden")
                for i in ids if i not in embedded]
    else:
        out.append(info(FIGURES, "content/ noch leer – Einbindung der Abbildungen nicht prüfbar"))
    out += _metadata(view, set(ids))
    out += _reconstructions(view, set(ids))
    out += _manifest(view, ids)
    return out


def _metadata(view: RepoView, ids: set[str]) -> list[Finding]:
    out = []
    for i in PRIORITY_FIGURES:
        if i in ids and not view.figure_meta(i):
            out.append(error(FIGURES, f"`{i}` (prüfungsrelevant): Metadaten `curation/figures/{i}.yaml` fehlen"))
    titles = {f["id"]: f["title"] for f in view.figures}
    for path in view.figure_meta_files:
        meta = view.figure_meta(path.stem)
        rel = view.rel(path)
        out += [error(FIGURES, f"`{rel}`: {p}") for p in problems(FIGURE_META, meta)]
        if meta.get("id") != path.stem:
            out.append(error(FIGURES, f"`{rel}`: `id: {meta.get('id')}` passt nicht zum Dateinamen"))
        elif path.stem not in ids:
            out.append(error(FIGURES, f"`{rel}`: `{path.stem}` steht nicht in curation/figures.yaml"))
        elif meta.get("title") and meta["title"] != titles[path.stem]:
            out.append(warning(FIGURES, f"`{rel}`: Titel weicht von curation/figures.yaml ab"))
    missing = len(ids) - sum(1 for i in ids if view.figure_meta(i))
    if missing:
        out.append(info(FIGURES, f"{missing} von {len(ids)} Abbildungen haben noch keine Metadaten (B)"))
    return out


def _reconstructions(view: RepoView, ids: set[str]) -> list[Finding]:
    out = []
    rec_dir = view.path(config.FIG_RECONSTRUCTED)
    ex_dir = view.path(config.FIG_EXERCISES)
    by_figure = (view.json(sketch_scope.TOPIC_MAPPING, {}) or {}).get("by_figure", {})
    kinds = {f["id"]: f.get("kind", "figure") for f in view.figures}
    sketchable = {i for i in ids if sketch_scope.worth_sketching(
        i, kinds.get(i, "figure"), (view.figure_meta(i).get("exam_relevance") or {}).get("level"), by_figure)}
    for fid in sorted(ids):
        status = (view.figure_meta(fid).get("reconstruction") or {}).get("status", "not-started")
        svg = rec_dir / f"{fid}.svg"
        if status in RECONSTRUCTED and not svg.exists():
            out.append(error(FIGURES, f"`{fid}`: Rekonstruktion als `{status}` markiert, "
                                      f"aber `figures/reconstructed/{fid}.svg` fehlt"))
            continue
        if not svg.exists():
            continue
        out += _svg_problems(fid, svg.read_text(encoding="utf-8"), status)
        if status == "faithful" and fid in sketchable and not (ex_dir / f"{fid}-blank.svg").exists():
            out.append(warning(FIGURES, f"`{fid}`: geprüfte Rekonstruktion ohne Zeichenübung "
                                        f"(`python -m pipeline exercises`)"))
    stray = sorted(p.stem for p in rec_dir.glob("*.svg") if p.stem not in ids) if rec_dir.exists() else []
    out += [error(FIGURES, f"`figures/reconstructed/{s}.svg` gehört zu keiner kuratierten Abbildung")
            for s in stray]
    return out


def _svg_problems(fid: str, text: str, status: str) -> list[Finding]:
    out = []
    where = f"`figures/reconstructed/{fid}.svg`"
    if status not in RECONSTRUCTED:
        out.append(warning(FIGURES, f"{where} existiert, Metadaten nennen aber Status `{status}`"))
    if _svg_attr(text, "data-figure-id") != fid:
        out.append(error(FIGURES, f"{where}: `data-figure-id` fehlt oder ist falsch"))
    svg_status = _svg_attr(text, "data-status")
    if svg_status not in RECONSTRUCTED:
        out.append(error(FIGURES, f"{where}: `data-status` fehlt oder ist ungültig"))
    elif status in RECONSTRUCTED and svg_status != status:
        out.append(warning(FIGURES, f"{where}: `data-status={svg_status}`, Metadaten sagen `{status}`"))
    if re.search(r"<image\b", text):
        out.append(error(FIGURES, f"{where}: enthält ein eingebettetes Rasterbild (nicht erlaubt)"))
    if 'class="answer"' not in text:
        out.append(warning(FIGURES, f"{where}: keine `class=\"answer\"`-Elemente – keine Übung ableitbar"))
    return out


def _manifest(view: RepoView, ids: list[str]) -> list[Finding]:
    entries = view.figures_manifest.get("figures")
    if entries is None:
        return [error(FIGURES, "figures/manifest.json fehlt (`python -m pipeline extract-figures`)")]
    out = []
    for e in entries:
        out += [error(FIGURES, f"manifest.json `{e.get('id')}`: {p}")
                for p in problems(FIGURE_MANIFEST_ENTRY, e)]
    if [e.get("id") for e in entries] != ids:
        out.append(error(FIGURES, "figures/manifest.json ist veraltet (IDs weichen von curation/figures.yaml "
                                  "ab) – `python -m pipeline extract-figures`"))
    stale = [e["id"] for e in entries if any(
        (v is None) == (view.root / k_path).exists()
        for k_path, v in _manifest_files(view, e))]
    if stale:
        out.append(warning(FIGURES, f"figures/manifest.json kennt neue/entfernte Dateien noch nicht "
                                    f"({len(stale)} Abbildungen, z. B. {stale[:5]}) – "
                                    f"`python -m pipeline extract-figures` erneut ausführen"))
    return out


def _manifest_files(view: RepoView, entry: dict) -> list[tuple[str, str | None]]:
    """(expected path, manifest value) for every layer file of one manifest entry."""
    fid = entry["id"]
    expected = {
        "original": config.FIG_ORIGINALS / f"{fid}.png",
        "reconstructed": config.FIG_RECONSTRUCTED / f"{fid}.svg",
        "exercise": config.FIG_EXERCISES / f"{fid}-blank.svg",
        "drawing_guide": config.DRAWING_GUIDES / config.drawing_guide_name(fid),
        "metadata": config.FIGURE_META_DIR / f"{fid}.yaml",
    }
    files = entry.get("files") or {}
    return [(view.rel(view.path(p)), files.get(k)) for k, p in expected.items()]


def check_detection(view: RepoView) -> list[Finding]:
    """Turn the two figure cross-check reports (detect-figures, captions) into findings."""
    out = []
    det = view.path(config.REPORTS) / "figure-detection.md"
    if not det.exists():
        out.append(info(DETECTION, "reports/figure-detection.md fehlt (`python -m pipeline detect-figures`)"))
    else:
        for heading, body in re.findall(r"^## (.+?)\n+(.*?)(?=^## |\Z)", det.read_text(encoding="utf-8"),
                                        re.S | re.M):
            if not body.strip().startswith("Keine"):
                out.append(warning(DETECTION, f"reports/figure-detection.md – „{heading}“ ist nicht leer"))
    cap = view.path(config.REPORTS) / "captions-check.md"
    if cap.exists():
        doubtful = re.findall(r"^\| `([^`]+)` \| prüfen \|", cap.read_text(encoding="utf-8"), re.M)
        if doubtful:
            out.append(warning(DETECTION, f"{len(doubtful)} Beschriftungen nur visuell bestätigt "
                                          f"(reports/captions-check.md): {doubtful}"))
    return out
