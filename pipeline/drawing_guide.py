"""Render the German drawing guide learning/drawing-exercises/<id>-zeichenuebung.md for one figure.

Everything figure-specific comes from the curated metadata (B) in
curation/figures/<id>.yaml; this module only knows the *types* of figures
(how to start a curve diagram vs. a matrix) and the order in which a learner
should build a drawing up: frame, axes, shapes, texts, curves, connections.
A figure without metadata still gets a minimal guide pointing to the files.
"""
from __future__ import annotations

import re

from . import catalog

# Paths from learning/drawing-exercises/ to the figure layers.
REL = "../../figures"

# How to lay out the drawing before any detail, per metadata `type`.
TYPE_START = {
    "kurvendiagramm": "Zeichne zuerst das Achsenkreuz mit Pfeilspitzen und lass oben genug Platz für Beschriftungen.",
    "matrix": "Zeichne zuerst das Raster (Zeilen × Spalten) und lass links und oben Platz für die Kopfzeilen.",
    "portfolio": "Zeichne zuerst das Achsenkreuz und teile die Fläche in die Felder des Portfolios.",
    "prozess": "Lege zuerst die Reihenfolge der Schritte fest und zeichne die Kästen in Leserichtung.",
    "flussdiagramm": "Lege zuerst die Reihenfolge der Bausteine fest und zeichne sie in Leserichtung.",
    "venn": "Zeichne zuerst die Kreise so, dass sich jede Kombination von Bereichen überschneidet.",
    "system": "Zeichne zuerst die Systemgrenze und darin die Bestandteile, dann die Flüsse von außen nach innen.",
    "hierarchie": "Setze zuerst den zentralen Begriff und ordne die Unterpunkte darum oder darunter an.",
    "tabelle": "Zeichne zuerst das Tabellengerüst mit Kopfzeile und Kopfspalte.",
    "sonstiges": "Verschaffe dir zuerst einen Überblick über die Grundform der Abbildung.",
}
# Order in which element kinds are drawn, with their German group label.
KIND_ORDER = [
    ("kreis", "Kreise / Bereiche"), ("box", "Kästen"), ("phase", "Phasen"),
    ("pfeil", "Pfeile"), ("kurve", "Kurven"), ("label", "Beschriftungen"),
]
RELATION_VERB = {"pfeil": "→", "folgt": "→", "enthält": "enthält", "überlappt": "überschneidet sich mit"}


def _q(text) -> str:
    return f"„{str(text).strip()}“"


def _element_line(e: dict) -> str:
    text, note = e.get("text"), e.get("note")
    if text and note:
        return f"{_q(text)} – {note}"
    return _q(text) if text else str(note or e["id"])


def _axis_steps(meta: dict) -> list[str]:
    out = []
    for a in meta.get("axes") or []:
        direction = f", Richtung {a['direction']}" if a.get("direction") else ""
        unit = f" [{a['unit']}]" if a.get("unit") else ""
        out.append(f"{a['axis']}-Achse beschriften: {_q(a['label'])}{unit}{direction}.")
    return out


def _element_steps(meta: dict) -> list[str]:
    """One step per element kind, in drawing order; unknown kinds come last."""
    # Axes and curves get their own, more detailed steps when the metadata describes them.
    covered = {kind for kind, key in (("achse", "axes"), ("kurve", "curves")) if meta.get(key)}
    elements = [e for e in meta.get("elements") or [] if e.get("kind") not in covered]
    known = [k for k, _ in KIND_ORDER]
    groups = KIND_ORDER + [(k, k.capitalize()) for k in
                           dict.fromkeys(e.get("kind") for e in elements) if k not in known]
    out = []
    for kind, label in groups:
        members = [e for e in elements if e.get("kind") == kind]
        if members:
            items = "\n".join(f"   - {_element_line(e)}" for e in members)
            out.append(f"{label} einzeichnen:\n{items}")
    return out


def _curve_steps(meta: dict) -> list[str]:
    out = []
    for c in meta.get("curves") or []:
        points = c.get("key_points") or []
        points = [points] if isinstance(points, str) else points
        extra = "".join(f"\n   - {p}" for p in points)
        out.append(f"Kurve {_q(c['name'])} zeichnen: {c['shape']}.{extra}")
    return out


def _relation_step(meta: dict) -> list[str]:
    names = {e["id"]: (e.get("text") or e.get("note") or e["id"]) for e in meta.get("elements") or []}
    lines = []
    for r in meta.get("relations") or []:
        verb = RELATION_VERB.get(r["kind"], r["kind"])
        text = f" ({r['text']})" if r.get("text") else ""
        lines.append(f"   - {_q(names.get(r['from'], r['from']))} {verb} {_q(names.get(r['to'], r['to']))}{text}")
    return [f"Beziehungen und Verbindungen einzeichnen:\n" + "\n".join(lines)] if lines else []


def _steps(meta: dict) -> list[str]:
    start = TYPE_START.get(meta.get("type"), TYPE_START["sonstiges"])
    steps = [start, *_axis_steps(meta), *_element_steps(meta), *_curve_steps(meta), *_relation_step(meta)]
    steps.append("Mit den Muss-Inhalten unten abgleichen und erst dann die Lösung ansehen.")
    return [f"{n}. {s}" for n, s in enumerate(steps, 1)]


def _header(fid: str, figure: dict) -> list[str]:
    printed = catalog.printed_page(figure["pdf_page"])
    where = f"Skript S. {printed} (PDF {figure['pdf_page']})" if printed else f"PDF-Seite {figure['pdf_page']}"
    return [
        f"<!-- Generiert von `python -m pipeline exercises` aus curation/figures/{fid}.yaml "
        f"– nicht von Hand bearbeiten. -->",
        "", f"# Zeichenübung: {figure['title']}", "",
        f"*{catalog.figure_label(figure)} – {where}*", "",
    ]


def _task(fid: str, figure: dict, meta: dict) -> list[str]:
    out = ["## Aufgabe", "",
           f"Zeichne die Abbildung {_q(figure['title'])} aus dem Gedächtnis und beschrifte alle Elemente. "
           f"Als Vorlage dient die [leere Übung]({REL}/exercises/{fid}-blank.svg): "
           "Die gestrichelten Kästen markieren, wo Text hingehört.", ""]
    drawing = meta.get("drawing") or {}
    relevance = meta.get("exam_relevance") or {}
    if drawing.get("difficulty"):
        out.append(f"- Schwierigkeit: {drawing['difficulty']}")
    if relevance.get("level"):
        out.append(f"- Prüfungsrelevanz: {relevance['level']} – {relevance.get('reason', '').strip()}")
    if relevance.get("question_ids"):
        out.append("- Prüfungsfragen: " + ", ".join(f"`{q}`" for q in relevance["question_ids"]))
    return out + [""]


def _section(title: str, lines: list[str]) -> list[str]:
    return [f"## {title}", "", *lines, ""] if lines else []


def _self_check(fid: str, meta: dict) -> list[str]:
    status = (meta.get("reconstruction") or {}).get("status")
    out = [f"- [Originalabbildung aus dem Skript]({REL}/originals/{fid}.png) – maßgeblich",
           f"- [Rekonstruktion (Vektorgrafik)]({REL}/reconstructed/{fid}.svg)",
           f"- [Leere Übung]({REL}/exercises/{fid}-blank.svg)",
           "", "Prüfe: Sind alle Muss-Inhalte abgehakt? Stimmen Reihenfolge, Anordnung und "
           "Beschriftungen mit dem Original überein?"]
    if status != "faithful":
        out += ["", "> **Achtung:** Die Rekonstruktion ist noch nicht als originalgetreu geprüft "
                    "(`needs_review`) – im Zweifel gilt die Originalabbildung."]
    return out


def render(fid: str) -> str:
    """Markdown guide for figure `fid` (metadata optional)."""
    figure = catalog.figure(fid)
    meta = catalog.figure_meta(fid)
    lines = _header(fid, figure) + _task(fid, figure, meta)
    if not meta:
        lines += ["> Für diese Abbildung gibt es noch keine kuratierten Metadaten "
                  f"(`curation/figures/{fid}.yaml`) – nutze das Original zur Selbstkontrolle.", ""]
    drawing = meta.get("drawing") or {}
    lines += _section("Worum es geht", [meta["meaning"].strip()] if meta.get("meaning") else [])
    lines += _section("Schritt-für-Schritt-Anleitung", _steps(meta) if meta else [])
    lines += _section("Muss-Inhalte", [f"- [ ] {m}" for m in drawing.get("must_know") or []])
    lines += _section("Typische Fehler", [f"- {m}" for m in drawing.get("common_mistakes") or []])
    lines += _section("Selbstkontrolle", _self_check(fid, meta))
    # Sections are optional, so collapse the blank lines they may leave behind.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).rstrip() + "\n"
