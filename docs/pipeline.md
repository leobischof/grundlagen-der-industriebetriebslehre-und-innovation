# Verarbeitungspipeline

Die Pipeline macht aus den lokalen Originalen die versionierte Wissensbasis. Sie ist **lokal,
deterministisch und gecacht**: gleiche Eingaben ergeben byte-gleiche Ausgaben, und ein zweiter Lauf
ohne Änderungen macht weder OCR noch Rendering noch Bilderkennung. **Die Pipeline ruft nie ein
KI-Modell auf** – Interpretationsarbeit (Abbildungen beschreiben, SVGs rekonstruieren, visuelle
Kontrolle) erledigt ein Agent außerhalb der Pipeline und legt das Ergebnis als kuratierte Datei unter
`curation/` bzw. `figures/reconstructed/` ab. Dateiformate: [architecture.md](architecture.md).

## Aufruf

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[pipeline,dev]"    # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m pipeline --help
.venv/Scripts/python -m pipeline all              # alle Stufen in der Reihenfolge unten
.venv/Scripts/python -m pipeline offline          # nur validate + report (wie die CI)
.venv/Scripts/python -m pipeline extract-figures --pages 21-30 --dry-run
```

| Schalter | Wirkung |
|---|---|
| `--pages 11-20,41` | nur diese PDF-Seiten (seitenbasierte Stufen: `extract-text`, `detect-figures`, `extract-figures`, `captions`) |
| `--dry-run` | nur anzeigen, was neu berechnet oder geschrieben würde |
| `--force` | Cache ignorieren und neu berechnen (schreibt den Cache trotzdem) |

Das Extra `pipeline` bringt PyMuPDF, OpenCV, NumPy und Pillow; `dev` nur pytest und jsonschema.
`validate` und `report` brauchen nur `dev` – deshalb laufen sie in der CI ohne Original-PDFs.

## Stufen

Reihenfolge von `all` = Reihenfolge in `COMMANDS` (`pipeline/__main__.py`):

| Befehl | Modul | Liest | Schreibt |
|---|---|---|---|
| `ingest` | `ingest` | `input/` | `sources/original-pdfs/`, `sources/manifest.yaml` |
| `extract-text` | `extract_text` | Skript-PDF | `sources/ocr/skript-pages.jsonl` (Zeilen mit Box, Layout-Band, Druckfarbe, Qualitätsmaß) |
| `detect-figures` | `detect_figures` | Skript-PDF, `curation/figures.yaml` | `reports/figure-detection.md` (Abgleich Bilderkennung ↔ Kuratierung) |
| `extract-figures` | `extract_figures` | Skript-PDF, `curation/figures*.yaml`, `figures/reconstructed/` | `figures/originals/*.png`, `figures/manifest.json` |
| `captions` | `captions_check` | OCR-Schicht, Tesseract (optional) | `reports/captions-check.md` (Gegenprobe der Bildunterschriften) |
| `exams` | `process_exams` | `curation/exams.yaml` | `exams/questions.json`, `questions.md`, `frequency-analysis.md` |
| `flashcards` | `flashcards` | Anki-Decks (`*.apkg`) | `learning/flashcards/` |
| `link` | `link_topics` | `curation/exams.yaml`, `curation/topics.yaml` | `exams/topic-mapping.json` |
| `exercises` | `generate_exercises` | `figures/reconstructed/`, `curation/figures/` | `figures/exercises/*-blank.svg`, `learning/drawing-exercises/` |
| `build-content` | `build_content` | OCR-Schicht, `curation/structure.yaml`, `ocr-corrections.yaml`, Abbildungen, Fragen | `content/` |
| `render-pdf` | `render_pdf` | `content/`, `figures/`, `exams/questions.md` | `build/pdf/` (Kapitel-PDFs, Gesamt-PDF, Fragen-PDF) |
| `anki` | `anki_sketch` | `figures/manifest.json`, `figures/originals/`, `curation/figures/`, `exams/` | `build/anki/*.apkg` (Skizzierkarten), `learning/flashcards/skizzieren.md` |
| `validate` | `validate` | alles Versionierte | `reports/validation.md` |
| `report` | `coverage` | alles Versionierte, `curation/ai-log.jsonl` | `reports/coverage.md` |

`build-content` läuft nach `exams`, `link` und `exercises`, weil die Frontmatter jedes Abschnitts die
Prüfungsfragen aus `topic-mapping.json` nennt und Bildunterschriften auf die Zeichenübungen verweisen.

## Cache und Kosten

- **Inhaltsadressierter Cache** (`pipeline/cache.py`): `JsonCache` legt je Stufe unter
  `build/cache/<stufe>/` eine kleine JSON-Datei je Schlüssel ab. Der Schlüssel ist der SHA-256 über
  alles, was das Ergebnis bestimmt (Hash der Eingabedatei, Seitennummer, Stufenversion, Parameter).
- **Stempel** unter `build/stamps/` merken für ganze Stufen (`extract-figures`, `flashcards`) den
  Hash ihrer Eingaben; stimmt er, wird die Stufe übersprungen.
- **Nur bei Änderung schreiben**: `write_if_changed` fasst unveränderte Dateien nicht an – `git
  status` bleibt nach einem Lauf ohne Eingabeänderung leer, und die CI kann prüfen, ob die
  committeten Berichte aktuell sind.
- **Ungültig machen**: Nach einer Codeänderung, die Ergebnisse einer Stufe verändert, die Zahl der
  Stufe in `STAGE_VERSIONS` (`pipeline/config.py`) erhöhen. Das macht genau diesen Cache ungültig;
  `--force` ist dafür nicht nötig.
- `build/` ist git-ignoriert und jederzeit reproduzierbar.

**Kostenregel.** Ein zweiter Lauf von `all` mit unveränderten Eingaben macht **0 OCR-Aufrufe und 0
KI-Aufrufe**. Jeder KI-Durchgang, den ein Agent für die Wissensbasis macht, wird als eine Zeile in
`curation/ai-log.jsonl` protokolliert – über `pipeline/ailog.py` (`ailog.append({...})`), nie von Hand
zusammengebastelt. Pflichtfelder: `date`, `stage`, `model`, `purpose`, `inputs`,
`est_input_tokens`, `est_output_tokens`, `result`. Tokens sind Schätzungen; ein Bild zählt mit
`ailog.image_tokens(b, h)` ≈ 1600 Tokens je Megapixel. Zusammenfassung:
`python -m pipeline.ailog`; `report` übernimmt die Summen in `reports/coverage.md`.

## Text: warum die OCR-Schicht des PDFs

Das Skript ist ein Scan mit eingebetteter OCR-Textschicht. Gemessen auf Stichprobenseiten (u. a.
PDF-Seite 87):

- Die **eingebettete Textschicht ist besser** als ein frischer Tesseract-Lauf: weniger Fehler bei
  Fachbegriffen, Umlaute korrekt, Zeilen mit Koordinaten.
- **Tesseract 5.4** (ganze Seite, 300 dpi) braucht ≈ 14 s je Seite und ist nicht besser; mit
  `deu+eng` gehen zudem Umlaute verloren.

Darum ist die PDF-Textschicht die **primäre** Quelle (`extract-text`). Tesseract (`pipeline/ocr_fallback.py`)
dient nur als optionale, gecachte **Gegenprobe**: für Bildunterschriften (`captions`) und für Seiten,
die das Qualitätsmaß als schwach markiert. Das deutsche Modell `deu.traineddata` liegt oft nicht im
System-`tessdata`; gesucht wird zuerst `TESSDATA_PREFIX`, dann `%LOCALAPPDATA%\tessdata`. Fehlt
Tesseract, melden die Stufen die Prüfung als übersprungen statt abzubrechen.

**Qualitätsmaß.** Je Seite der Anteil verdächtiger Tokens (Zeichen, die in korrektem deutschem
Skripttext nicht vorkommen, z. B. `¬`, `|`, oder Ziffern mitten im Wort wie „Inno4vation“).

| Schwelle | Wert | Wirkung |
|---|---|---|
| `LOW_QUALITY` (`extract_text.py`) | 0.08 | Seite gilt als schwach (`low: true`), Tesseract-Gegenprobe sinnvoll |
| `SECTION_OCR_WARN_RATIO` (`qa_checks_structure.py`) | 0.05 | `validate` warnt: Abschnitt gegen das Original lesen |

Korrekturen am Text gehören ausschließlich nach `curation/ocr-corrections.yaml`; die OCR-Schicht
selbst wird nie verändert.

## Layout des Scans (gemessen)

Konstanten in `pipeline/config.py`:

| Konstante | Wert | Bedeutung |
|---|---|---|
| `PRINTED_PAGE_OFFSET`, `FIRST_ARABIC_PDF_PAGE` | 10, 11 | gedruckte Seite = PDF-Seite − 10, ab PDF-Seite 11 („1“); davor römisch/ohne Nummer |
| `HEADER_BAND` | 0.075 | oberer Seitenanteil mit dem laufenden Kolumnentitel |
| `FOOTER_BAND` | 0.905 | darunter Logo und Seitenzahl |
| `RENDER_DPI` | 150 | Analyse-Renderings (Bilderkennung) |
| `CROP_DPI` | 200 | Abbildungsausschnitte ≈ native Scanauflösung (2320 px / 11,7 in) – mehr wäre nur hochskaliert |

Fließtext ist schwarz, Bildbeschriftungen sind grau gedruckt. `extract-text` speichert die
Druckfarbe je Zeile; damit trennt `build-content` Fließtext von Beschriftungen ohne Modell.
Fußnoten stehen im Fußbereich und werden ihrem Verweis im Text zugeordnet; gelingt das nicht
sicher, landen sie sichtbar unter „Fußnoten ohne sicheren Textanker“.

## Qualitätssicherung

- `python -m pipeline validate` → [`reports/validation.md`](../reports/validation.md): Fehler und
  Warnungen, gruppiert. Geprüft werden u. a. fehlende Seiten und Abschnitte, fehlende Abbildungen und
  Schichten, defekte Bild- und Markdown-Links, fehlende Originalquellen im Manifest, unvollständige
  Prüfungsfragen, doppelte IDs, inkonsistente Quellen- und Seitenverweise, Frontmatter und JSON gegen
  die Schemas in `schemas/`, SVG-Konventionen. Exit-Code 1 bei Fehlern; Warnungen brechen nicht ab.
- `python -m pipeline report` → [`reports/coverage.md`](../reports/coverage.md): wie vollständig die
  Wissensbasis ist (Seiten, Abschnitte, Abbildungsschichten, Fußnoten, Fragen, Lernkarten,
  KI-Aufrufe) und was fehlt.
- `python -m pytest`: Tests auf einem Mini-Baum (`tests/conftest.py`), brauchen keine Originale.
- **CI** (`.github/workflows/ci.yml`): installiert nur `.[dev]`, führt Tests und `offline` aus und
  schlägt fehl, wenn die committeten Berichte nicht dem frischen Ergebnis entsprechen. Nach jeder
  Änderung an der Wissensbasis daher `python -m pipeline offline` ausführen und `reports/` mit
  committen.
