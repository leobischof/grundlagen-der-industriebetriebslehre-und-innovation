# Grundlagen der Industriebetriebslehre und Innovation – Wissensbasis

Multimodale, agentenfreundliche Wissensbasis zur Lehrveranstaltung *Grundlagen der
Industriebetriebslehre und Innovation* (TU Graz, Skriptum 2024/25).

> **Privates Repository.** Die Originale (Skriptum, Fragensammlung, Klausur, Anki-Decks) liegen
> nur lokal in `input/` bzw. `sources/original-pdfs/` und werden nie committet;
> `sources/manifest.yaml` hält Dateiname, Größe und SHA-256 fest.

## Stand

Im Aufbau. Fertig sind die Infrastruktur und die deterministische Vorverarbeitung:

| Bereich | Inhalt |
|---|---|
| `sources/manifest.yaml` | 6 Quellen mit Hash und Vertrauensstufe |
| `sources/ocr/skript-pages.jsonl` | Textschicht aller 190 Seiten mit Layout-Band, Druckfarbe und Qualitätsmaß |
| `curation/figures.yaml` | kuratierte Liste: Abb. 1–85, Tab. 1–7, 6 Formelkästen (Quelle der Wahrheit) |
| `curation/structure.yaml` | Kapitelstruktur, Seitenversatz (gedruckte Seite = PDF-Seite − 10) |
| `figures/originals/` | 98 PNG-Ausschnitte (200 dpi) |
| `figures/manifest.json` | Abbildungs-Manifest mit Seiten, Kapitel/Abschnitt und Status |
| `reports/` | Abgleich Bilderkennung ↔ Kuratierung, Gegenprobe der Beschriftungen |
| `curation/ai-log.jsonl` | jeder KI-Aufruf mit geschätzten Tokens |

Folgt: bereinigter Text je Abschnitt (`content/`), Prüfungsdatenbank (`exams/`), SVG-Rekonstruktionen
und Zeichenübungen, Lernsystem (`learning/`, `AGENTS.md`), Validierung und Abdeckungsbericht.

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
