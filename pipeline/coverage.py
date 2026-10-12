"""Stage "report": honest coverage numbers → reports/coverage.md.

Offline (CI-safe) like `validate`: it counts what is committed – pages,
sections, figure layers, footnotes, exam questions, flashcards, logged AI
calls – and lists the gaps by name. The verdict line says "vollständig" only
when no TOC section, assigned page or curated figure original is missing.
"""
from __future__ import annotations

from pathlib import Path

from . import config
from .cache import write_if_changed
from .coverage_stats import collect
from .qa_repo import RepoView


def _pct(part: int, whole: int) -> str:
    return f"{part} / {whole} ({100 * part / whole:.0f} %)" if whole else f"{part} / 0"


def _yn(flag: bool) -> str:
    return "✓" if flag else "–"


def _verdict(s: dict) -> str:
    gaps = []
    if s["sections"]["missing"]:
        gaps.append(f"{len(s['sections']['missing'])} Abschnitte ohne Datei")
    if s["pages"]["missing_in_content"]:
        gaps.append(f"{len(s['pages']['missing_in_content'])} zugeordnete Seiten ohne Inhalt")
    if s["figures"]["png"] < s["figures"]["total"]:
        gaps.append(f"{s['figures']['total'] - s['figures']['png']} Abbildungen ohne Original")
    if not gaps:
        return "**Skript vollständig verarbeitet:** ja – jede zugeordnete Seite, jeder Abschnitt und jede " \
               "Abbildung liegt vor (Qualitätsstufen siehe unten)."
    return f"**Skript vollständig verarbeitet: nein** – {'; '.join(gaps)}."


def _pages(p: dict) -> list[str]:
    return ["## Seiten", "", "| Kennzahl | Wert |", "|---|---:|",
            f"| PDF-Seiten des Skripts | {p['total']} |",
            f"| bewusst übersprungen (Titel-, Inhaltsverzeichnis-, Leerseiten; `structure.yaml`) | {p['skipped']} |",
            f"| im Inhaltsverzeichnis einem Abschnitt zugeordnet | {p['assigned']} |",
            f"| mit gespeicherter OCR-Textschicht | {p['ocr_layer']} |",
            f"| davon mit schwacher OCR | {len(p['ocr_weak'])} {p['ocr_weak'] or ''} |",
            f"| in Abschnittsdateien enthalten (`pdf_pages`) | {_pct(p['in_content'], p['assigned'])} |", ""]


def _sections(s: dict) -> list[str]:
    out = ["## Abschnitte", "", f"Abschnittsdateien (X.Y): {_pct(s['files'], s['expected'])}.", ""]
    if s["status"]:
        out += ["Qualitätsstatus: " + ", ".join(f"`{k}` {v}" for k, v in sorted(s["status"].items())), ""]
    out += ["| Kapitel | Abschnitte | Dateien | eingebundene Abb. | verknüpfte Fragen |", "|---|---:|---:|---:|---:|"]
    out += [f"| {c['id']} {c['title']} | {c['expected']} | {c['files']} | {c['figures']} | {c['questions']} |"
            for c in s["per_chapter"]]
    return out + [""]


def _figures(f: dict) -> list[str]:
    kinds = ", ".join(f"{v} {k}" for k, v in sorted(f["by_kind"].items()))
    t = f["total"]
    out = ["## Abbildungen", "", f"Kuratiert (`curation/figures.yaml`): {t} ({kinds}).", "",
           "| Schicht | Anzahl |", "|---|---:|",
           f"| (A) Original-PNG | {_pct(f['png'], t)} |",
           f"| in `content/` eingebunden | {_pct(f['embedded'], t)} |",
           f"| (B) strukturierte Metadaten | {_pct(f['meta'], t)} |",
           f"| (C) SVG-Rekonstruktion | {_pct(f['svg'], t)} |",
           f"| … davon geprüft (`faithful`) | {f['faithful']} |",
           f"| … noch zu prüfen (`needs_review`) | {len(f['needs_review'])} {f['needs_review'] or ''} |",
           f"| (D) Zeichenübung (`-blank.svg`) | {f['exercise']} |",
           f"| Zeichenanleitung | {f['guide']} |", "",
           "### Prüfungsrelevante Schwerpunkt-Abbildungen", "",
           "| ID | Titel | Original | Metadaten | SVG | Status | Übung |", "|---|---|:-:|:-:|:-:|---|:-:|"]
    out += [f"| `{r['id']}` | {r['title']} | {_yn(r['png'])} | {_yn(r['meta'])} | {_yn(r['svg'])} | "
            f"{r['status']} | {_yn(r['exercise'])} |" for r in f["priority"]]
    return out + [""]


def _footnotes(n: dict) -> list[str]:
    return ["## Fußnoten", "",
            f"- Verweise `[^N]` im Text: {n['refs']}",
            f"- Definitionen: {n['defs']}, davon mit Textanker: {n['anchored']}",
            f"- laut Frontmatter ohne sicheren Textanker: {n['unanchored_meta']}", ""]


def _questions(q: dict) -> list[str]:
    if not q["built"]:
        return ["## Prüfungsfragen", "", "Noch nicht erzeugt (`exams/questions.json` fehlt).", ""]
    src = ", ".join(f"{k}: {v}" for k, v in sorted(q["by_source"].items()))
    types = ", ".join(f"{k} {v}" for k, v in sorted(q["task_types"].items())) or "–"
    return ["## Prüfungsfragen", "",
            f"- Fragen gesamt: {q['total']} ({src})",
            f"- einem Abschnitt zugeordnet: {_pct(q['with_sections'], q['total'])}",
            f"- mit Abbildungsbezug: {q['with_figures']}, davon Zeichenaufgaben: {q['drawing']}",
            f"- Aufgabentypen: {types}",
            f"- Abschnitte (X.Y) mit mindestens einer Frage: {q['sections_with_questions']}",
            f"- ohne Zuordnung: {q['unmapped'] or 'keine'}", ""]


def _flashcards(c: dict) -> list[str]:
    if not c["built"]:
        return ["## Lernkarten (Anki, unverified-student)", "", "Noch nicht erzeugt (`learning/flashcards/` fehlt).", ""]
    return ["## Lernkarten (Anki, unverified-student)", "", f"- {c['cards']} Karten in {c['files']} Dateien", ""]


def _ai(a: dict) -> list[str]:
    t = a["total"]
    out = ["## KI-Aufrufe (aus `curation/ai-log.jsonl`)", "",
           f"Gesamt: {t['calls']} protokollierte Aufrufe, geschätzt {t['input']} Eingabe- und "
           f"{t['output']} Ausgabe-Tokens"
           + (f" ({a['first']} bis {a['last']})." if a["first"] else "."), "",
           "| Stufe | Aufrufe | Eingabe-Tokens | Ausgabe-Tokens |", "|---|---:|---:|---:|"]
    out += [f"| {k} | {v['calls']} | {v['input']} | {v['output']} |" for k, v in sorted(a["per_stage"].items())]
    return out + ["", "Die Pipeline selbst ruft nie ein Modell auf; ein zweiter Lauf erzeugt 0 neue Einträge.", ""]


def _gaps(s: dict) -> list[str]:
    out = ["## Lücken", ""]
    missing = s["sections"]["missing"]
    out.append(f"- Abschnitte ohne Datei ({len(missing)}): {', '.join(missing) if missing else 'keine'}")
    prio = s["figures"]["priority"]
    out.append("- Schwerpunkt-Abbildungen ohne Metadaten: "
               + (", ".join(r["id"] for r in prio if not r["meta"]) or "keine"))
    out.append("- Schwerpunkt-Abbildungen ohne SVG: " + (", ".join(r["id"] for r in prio if not r["svg"]) or "keine"))
    out.append(f"- Themen mit Lücken ({len(s['topic_gaps'])}):" if s["topic_gaps"]
               else "- Themen mit Lücken: keine (oder `exams/topic-mapping.json` fehlt)")
    out += [f"  - {g}" for g in s["topic_gaps"]]
    return out + [""]


def render(s: dict) -> str:
    lines = ["# Abdeckungsbericht", "",
             "Generiert von `python -m pipeline report` aus den versionierten Dateien – nicht von Hand "
             "bearbeiten. Gezählt wird nur, was tatsächlich vorliegt.", "", _verdict(s), ""]
    for part in (_pages(s["pages"]), _sections(s["sections"]), _figures(s["figures"]), _footnotes(s["footnotes"]),
                 _questions(s["questions"]), _flashcards(s["flashcards"]), _ai(s["ai"]), _gaps(s)):
        lines += part
    return "\n".join(lines).rstrip() + "\n"


def run(pages: str | None = None, dry_run: bool = False, force: bool = False,
        root: Path | None = None) -> int:
    view = RepoView(root)
    out = view.path(config.REPORTS) / "coverage.md"
    if dry_run:
        print(f"[report] würde {view.rel(out)} schreiben")
        return 0
    stats = collect(view)
    changed = write_if_changed(out, render(stats))
    print(f"[report] Abschnitte {stats['sections']['files']}/{stats['sections']['expected']} · "
          f"Abbildungen PNG {stats['figures']['png']}/{stats['figures']['total']}, "
          f"SVG {stats['figures']['svg']} · {view.rel(out)} {'geschrieben' if changed else 'unverändert'}")
    return 0
