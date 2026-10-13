"""Command line entry point: `python -m pipeline <command> [--pages 11-20] [--dry-run] [--force]`.

Every stage is a module with `run(pages=..., dry_run=..., force=...)`. Stages are
imported lazily so that e.g. `validate` (used in CI) never needs OpenCV or the PDFs.
All stages are cached: running `all` twice with unchanged inputs does no OCR,
no rendering and never calls an AI model (the pipeline never calls one at all).
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time

# command -> (module, one-line help). Order = order of `all`.
COMMANDS: dict[str, tuple[str, str]] = {
    "ingest": ("ingest", "Eingabedateien kopieren und sources/manifest.yaml schreiben"),
    "extract-text": ("extract_text", "OCR-Textschicht je Seite → sources/ocr/skript-pages.jsonl"),
    "detect-figures": ("detect_figures", "Bildregionen erkennen und mit curation/figures.yaml abgleichen"),
    "extract-figures": ("extract_figures", "Abbildungen ausschneiden → figures/originals + manifest.json"),
    "captions": ("captions_check", "Beschriftungen per Tesseract gegen die kuratierten Titel prüfen"),
    "exams": ("process_exams", "Prüfungsfragen-Datenbank und Häufigkeitsanalyse → exams/"),
    "flashcards": ("flashcards", "Anki-Decks → learning/flashcards (unverified-student)"),
    "link": ("link_topics", "Themen ↔ Abschnitte ↔ Abbildungen ↔ Fragen verknüpfen"),
    "exercises": ("generate_exercises", "Zeichenübungen aus den SVG-Rekonstruktionen erzeugen"),
    # after exams/link/exercises: section frontmatter lists the exam questions
    # from topic-mapping.json and figure captions link the drawing exercises
    "build-content": ("build_content", "Kapitel-/Abschnitts-Markdown → content/"),
    "render-pdf": ("render_pdf", "Kapitel- und Gesamt-PDFs aus content/ → build/pdf"),
    "export-md": ("export_markdown", "flacher Markdown-Export (Kapitel, Gesamt, Prüfungsfragen) → build/markdown"),
    "export-notebooklm": ("export_notebooklm", "je Kapitel eine NotebookLM-Datei (Anleitung, Leitfaden, Fragen, Gesamtskript) → build/notebooklm"),
    "anki": ("anki_deck", "Anki-Karteikarten (Sammlung + je Kapitel) → build/anki"),
    "interactive": ("build_interactive", "Lokaler PDF-/Audio-Kapitelreader mit Timeline → build/interactive"),
    # after render-pdf/export-notebooklm/anki: packs what they listed for the release
    "release": ("release_bundle", "Release packen: Gesamtdateien, je Art ein Kapitel-Zip, Alles-Zip → build/release"),
    "validate": ("validate", "Qualitätsprüfungen → reports/validation.md"),
    "report": ("coverage", "Abdeckungsbericht → reports/coverage.md"),
}
# Stages that only need committed files (safe for CI: no PDFs, no OCR, no AI).
OFFLINE = ("validate", "report")


def _run(name: str, args: argparse.Namespace) -> int:
    module = importlib.import_module(f"pipeline.{COMMANDS[name][0]}")
    t0 = time.perf_counter()
    result = module.run(pages=args.pages, dry_run=args.dry_run, force=args.force)
    print(f"[{name}] fertig in {time.perf_counter() - t0:.1f} s")
    return int(result or 0)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # umlauts on Windows consoles
    parser = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=[*COMMANDS, "all", "offline"],
                        help="; ".join(f"{k}: {v[1]}" for k, v in COMMANDS.items()))
    parser.add_argument("--pages", help="PDF-Seiten, z. B. 11-20,41 (nur seitenbasierte Stufen)")
    parser.add_argument("--dry-run", action="store_true", help="nur anzeigen, was passieren würde")
    parser.add_argument("--force", action="store_true", help="Cache ignorieren und neu berechnen")
    args = parser.parse_args(argv)

    if args.command == "all":
        names = list(COMMANDS)
    elif args.command == "offline":
        names = list(OFFLINE)
    else:
        names = [args.command]
    status = 0
    for name in names:
        status |= _run(name, args)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
