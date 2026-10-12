# Grundlagen der Industriebetriebslehre und Innovation – Wissensbasis

Multimodale, agentenfreundliche Wissensbasis zur Lehrveranstaltung *Grundlagen der
Industriebetriebslehre und Innovation* (TU Graz, Skriptum 2024/25).

> **Privates Repository.** Die Originale (Skriptum, Fragensammlung, Klausur, Anki-Decks) liegen
> nur lokal in `input/` bzw. `sources/original-pdfs/` und werden nie committet;
> `sources/manifest.yaml` hält Dateiname, Größe und SHA-256 fest.

## Inhalt

| Bereich | Inhalt |
|---|---|
| [`content/`](content/skript-inhalt.md) | bereinigter Skripttext: 9 Kapitel, 32 Abschnitte, 52 Markdown-Dateien mit Frontmatter, Abbildungen, Fußnoten und Prüfungsbezug |
| [`exams/`](exams/questions.md) | 61 Prüfungsfragen im exakten Wortlaut (12 Termine), Themen-Zuordnung und [Häufigkeitsanalyse](exams/frequency-analysis.md) mit transparentem Score |
| `figures/originals/` | 98 PNG-Ausschnitte aus dem Skript (Abb. 1–85, Tab. 1–7, 6 Formelkästen), [Manifest](figures/manifest.json) |
| `figures/reconstructed/`, `figures/exercises/` | 16 SVG-Rekonstruktionen der Schwerpunkt-Abbildungen und je eine Blanko-Vorlage zum Nachzeichnen |
| [`learning/chapters/`](learning/chapters/leitfaeden-uebersicht.md) | Lernleitfaden je Kapitel (KI-Erklärung, quellengebunden) |
| [`learning/exercises/`](learning/exercises/musterloesungen-uebersicht.md) | Musterlösungen zu jeder echten Prüfungsfrage, je Kapitel |
| `learning/drawing-exercises/` | 16 Zeichenübungen mit Merkpunkten |
| `learning/flashcards/` | 413 Studierenden-Karten (unverifiziert) und 32 [Skizzierkarten](learning/flashcards/skizzieren.md) |
| [`learning/progress/`](learning/progress/lernfortschritt-anleitung.md) | lokaler Lernfortschritt mit Wiederholungsplanung (nie committet) |
| [`AGENTS.md`](AGENTS.md) | Anleitung für Lernagenten: vier Schichten, Quellenbindung, fünf Lernmodi |
| [`docs/`](docs/architecture.md) | [Architektur](docs/architecture.md), [Pipeline](docs/pipeline.md), [Lernmethode](docs/learning-method.md), [Quellen und Rechte](docs/sources-and-rights.md) |
| [`reports/`](reports/coverage.md) | [Abdeckung](reports/coverage.md), [Validierung](reports/validation.md), Abgleich Bilderkennung ↔ Kuratierung |
| `curation/` | Quelle der Wahrheit für Struktur, Abbildungen und Abbildungs-Metadaten; [KI-Protokoll](curation/ai-log.jsonl) |
| `schemas/` | JSON-Schemas für Frontmatter, Fragen, Abbildungen und Lernfortschritt |

**Aktualität:** Das Skript ist die Fassung 2024/25, die Prüfungsfragen reichen bis 2026. 56 von 61
Fragen deckt das Skript vollständig, 5 nur teilweise – siehe
[Aktualitätslücken](exams/frequency-analysis.md#aktualitätslücken).

**Downloads:** Im Release dieses Repositorys (nicht im Git-Baum) liegen als `GIL-…`-PDFs jedes
Kapitel, das Gesamtskript, die Zusammenfassung je Kapitel und gesamt sowie die Prüfungsfragen;
Markdown und PDFs zusätzlich in einem geheimen Gist
([Veröffentlichen](docs/pipeline.md#veröffentlichen-release-und-gist)). Abbildungen erscheinen dort
nur als unsere SVG-Rekonstruktion oder als Platzhalter, nie als Ausschnitt aus dem Skript.

## Mitarbeit

`main` ist für alle geschützt, auch für den Eigentümer: Jede Änderung kommt über einen
Feature-Branch und einen Pull Request mit grüner CI (`qa`, `konventionen`) und wird per Squash
gemergt. Force-Push ist auf allen Branches gesperrt; Branch-Namen und Commit-Titel folgen
Conventional Commits. Ablauf und Regeln für Menschen und Agenten:
[AGENTS.md, Abschnitt 7](AGENTS.md#7--beiträge-branches-und-pull-requests).

## Pipeline

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[pipeline,dev]"     # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m pipeline --help
.venv/Scripts/python -m pipeline all                # alle Stufen, gecacht (SHA-256)
.venv/Scripts/python -m pipeline extract-figures --pages 21-30 --dry-run
```

Alle Stufen laufen lokal und deterministisch; ein zweiter Lauf mit unveränderten Eingaben macht
keine OCR- und keine KI-Aufrufe. `--force` ignoriert den Cache.

Weitere Befehle:

```bash
.venv/Scripts/python -m pipeline offline            # Validierung + Abdeckungsbericht (wie in CI)
.venv/Scripts/python -m pipeline render-pdf         # GIL-PDFs (Kapitel, Gesamtskript, Zusammenfassungen, Fragen) → build/pdf/
.venv/Scripts/python -m pipeline anki               # Anki-Skizzierkarten → build/anki/ (nur lokal, nicht ins Release)
.venv/Scripts/python -m pipeline export-md          # flacher Markdown-Export → build/markdown/
.venv/Scripts/python -m pipeline.progress due       # heute fällige Wiederholungen
.venv/Scripts/python -m pytest                      # Tests
```

Die CI (`.github/workflows/ci.yml`) führt nur Tests, Validierung und Abdeckungsbericht aus – ohne
OCR, ohne PDFs und ohne KI. Details in [`docs/pipeline.md`](docs/pipeline.md).
