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
| `extract-text` | `extract_text` | Skript-PDF | `sources/ocr/skript-pages.jsonl` (Zeilen mit Box, Layout-Band, Druckfarbe, fett gedruckten Wörtern, Qualitätsmaß) |
| `detect-figures` | `detect_figures` | Skript-PDF, `curation/figures.yaml` | `reports/figure-detection.md` (Abgleich Bilderkennung ↔ Kuratierung) |
| `extract-figures` | `extract_figures` | Skript-PDF, `curation/figures*.yaml`, `figures/reconstructed/` | `figures/originals/*.png`, `figures/manifest.json` |
| `captions` | `captions_check` | OCR-Schicht, Tesseract (optional) | `reports/captions-check.md` (Gegenprobe der Bildunterschriften) |
| `exams` | `process_exams` | `curation/exams.yaml` | `exams/questions.json`, `questions.md`, `frequency-analysis.md` |
| `flashcards` | `flashcards` | Anki-Decks (`*.apkg`) | `learning/flashcards/` |
| `link` | `link_topics` | `curation/exams.yaml`, `curation/topics.yaml` | `exams/topic-mapping.json` |
| `exercises` | `generate_exercises` | `figures/reconstructed/`, `curation/figures/` | `figures/exercises/*-blank.svg`, `learning/drawing-exercises/` |
| `build-content` | `build_content` | OCR-Schicht, `curation/structure.yaml`, `ocr-corrections.yaml`, Abbildungen, Fragen | `content/` |
| `render-pdf` | `render_pdf` (Leitfaden-Bilder: `guide_figures`) | `content/`, `learning/chapters/`, `figures/reconstructed/`, `curation/figures/`, `exams/questions.md` | `build/pdf/` (`GIL-…`-PDFs: Kapitel, Gesamtskript, Zusammenfassungen je Kapitel und gesamt, Prüfungsfragen) + `release-assets.tsv` |
| `export-md` | `export_markdown` (Leitfaden-Bilder: `guide_figures`) | `content/`, `learning/chapters/`, `figures/reconstructed/`, `curation/figures/`, `exams/questions.md` | `build/markdown/` (dieselben `GIL-…`-Dateien als flaches Markdown, dazu die gezeigten SVGs) |
| `export-notebooklm` | `export_notebooklm` | `content/`, `learning/chapters/`, `curation/figures/`, `exams/questions.json`, `exams/topic-mapping.json` | `build/notebooklm/` (je Kapitel mit Leitfaden eine `GIL-N-NotebookLM-Kontext-…md`) + `release-assets.tsv` |
| `anki` | `anki_deck` (Karten: `anki_cards`, `anki_exam_cards`, `anki_sketch`, `anki_student`; Pakete: `anki_package`) | `content/`, `learning/exercises/`, `learning/flashcards/*.json`, `figures/manifest.json`, `figures/reconstructed/`, `curation/figures/`, `exams/` | `build/anki/` (`GIL-Anki-Karteikarten.apkg`, dieselbe Sammlung als `.colpkg`, je Kapitel ein `.apkg`) + `release-assets.tsv`, `learning/flashcards/skizzieren.md` |
| `release` | `release_bundle` | `release-assets.tsv` aus `build/pdf/`, `build/notebooklm/`, `build/anki/` | `build/release/` (Gesamtdateien, je Art ein Kapitel-Zip, Alles-Zip) + `release-assets.tsv` |
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

**Fettdruck.** Die Textschicht kennt keine Schriftstärke, darum misst `pipeline/bold_print.py` sie
im Bild: die mittlere Länge waagrechter Tintenläufe in der Wortbox ≈ Strichstärke (Normalschrift
≈ 2,7 px, fett ≈ 4,2 px bei 150 dpi). Fett ist ein Wort ab dem 1,3-Fachen des Seitenmedians; der
Median ist auf 2,45–2,9 px begrenzt, weil Abbildungsbeschriftungen ihn sonst verfälschen.
`extract-text` speichert je Zeile die Indizes der fetten Wörter (`bold`). `build-content` setzt
die fetten Läufe über Zeilenumbrüche hinweg zusammen (`textclean`) und markiert sie im
bereinigten Text als `**…**` (`pipeline/emphasis.py`) – nur in Absätzen und Listen, nicht im
Literaturverzeichnis. Eine Phrase, die im Text nicht wiederzufinden ist, wird nicht geraten,
sondern von `build-content` gemeldet. Ohne die `**` ist der Text Wort für Wort derselbe.
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

## Veröffentlichen (Release und Gist)

Beides läuft lokal und von Hand, nie in der CI, und nie mit den Original-PDFs der Lehrveranstaltung.
Veröffentlicht wird nur, was per Pull Request auf `main` gemergt ist (AGENTS.md Abschnitt 7): vorher
`git switch main && git pull --ff-only`. Vor jedem Schritt prüfen, dass das Repository privat ist:
`gh api repos/<owner>/<repo> --jq .visibility` muss `private` liefern.

**Namen.** Jede veröffentlichte Datei heißt `GIL-…` (GIL = Grundlagen der Industriebetriebslehre);
bei kapitelbezogenen Dateien steht die Kapitelnummer unmittelbar nach `GIL`: **`GIL-<N>-<Art>-<Titel>`**
(z. B. `GIL-2-NotebookLM-Kontext-Industrielle-Innovation.md`). Gesamtdateien und Sammel-Zips
tragen keine einzelne Kapitelnummer. Die Regel steht einmal in `pipeline/content_files.py`. Dateiname nur ASCII mit Bindestrichen (GitHub
macht aus Leerzeichen, Umlauten und Gedankenstrichen in Asset-Namen Punkte), die lesbare Fassung ist
das Label des Release-Assets. Das Label trägt immer die Dateiendung (`content_files.asset_label`),
damit man im Release sieht, was ein PDF, ein Zip, eine Markdown-Datei oder ein Anki-Paket ist.

**Aufbau des Releases** (Regel, Stufe `release`): Kapitelweises kommt nie als einzelne Assets ins
Release, sondern je Art in **ein Zip**; Dateien für den ganzen Kurs bleiben einzeln; dazu **ein
Alles-Zip** mit dem gesamten Release in Ordnern. Ohne optionale Medien hat ein Release zehn Assets:

| Asset | Label | Inhalt |
|---|---|---|
| `GIL-Wissensbasis-komplett.zip` | GIL Wissensbasis komplett (alles in Ordnern).zip | alles unten, in `1-Skript/` (darin `Skriptkapitel/`), `2-Zusammenfassungen/` (darin `Kapitel/`), `3-Pruefungsfragen/`, `4-NotebookLM-Kontext/`, `5-Anki/` (darin `Kapitel/`) |
| `GIL-Skriptkapitel-je-Kapitel.zip` | GIL Skriptkapitel – je Kapitel.zip | je Kapitel `GIL-N-Skriptkapitel-<Titel>.pdf` (Textschicht des Skripts) |
| `GIL-Zusammenfassung-je-Kapitel.zip` | GIL Zusammenfassung – je Kapitel.zip | je Kapitel `GIL-N-Zusammenfassung-<Titel>.pdf` (Lernleitfaden) |
| `GIL-NotebookLM-Kontext-je-Kapitel.zip` | GIL NotebookLM-Kontext – je Kapitel.zip | je Kapitel `GIL-N-NotebookLM-Kontext-<Titel>.md` |
| `GIL-Anki-je-Kapitel.zip` | GIL Anki – je Kapitel.zip | je Kapitel `GIL-N-Anki-<Titel>.apkg` |
| `GIL-Gesamtskript.pdf` | GIL Gesamtskript.pdf | alle Kapitel mit Inhaltsverzeichnis |
| `GIL-Zusammenfassung-gesamt.pdf` | GIL Zusammenfassung gesamt.pdf | alle Lernleitfäden |
| `GIL-Pruefungsfragen.pdf` | GIL Prüfungsfragen.pdf | Fragensammlung |
| `GIL-Anki-Karteikarten.apkg` | GIL Anki-Karteikarten – alle Kapitel.apkg | alle Karten: je Kapitel ein Unterdeck, darin je Kartenart eines |
| `GIL-Anki-Sammlung-ersetzt-alles.colpkg` | GIL Anki-Sammlung (ersetzt alles).colpkg | dieselben Karten als ganze Anki-Sammlung – **der Import ersetzt alles in Anki**, nur für ein leeres oder eigenes Profil |

Jede Datei, die eine Stufe in ihrer `release-assets.tsv` nennt, braucht einen Platz in
`release_bundle.SINGLES` oder `PER_CHAPTER`; sonst bricht `release` ab, statt sie still wegzulassen.

**Optionale Audios und interaktiver Reader.** Lokale Kapitelaufnahmen unter `audio/` sind
git-ignoriert und heißen `GIL-<N>-Audio-<Titel>.<Endung>`. `release` nimmt vorhandene Aufnahmen
als `GIL-Audio-je-Kapitel.zip` sowie im Gesamt-Zip unter `6-Audio/` auf. Ein gebauter Reader
kommt zusätzlich als eigenständiges `GIL-Interaktiver-Kapitelreader.zip` mit PDF, Audio-Ordner,
Timeline-Dateien und lokalem PDF.js dazu. Einrichtung, automatische Vorbereitung und Korrektur:
[interactive-reader.md](interactive-reader.md). Diese optionalen Dateien fehlen bewusst in CI.

**NotebookLM-Dateien.** Jede Datei ist der vollständige Kontext für ein Kapitel – für NotebookLM
(eine Datei als einzige Quelle, z. B. eine Audio-Zusammenfassung je Kapitel) und jedes andere
Lernwerkzeug. Aufbau: Anleitung (nur dieses Kapitel, so ausführlich wie möglich; Links auf seine
Abschnitte), Teil 1 Lernleitfaden, Teil 2 alle Prüfungsfragen zum Kapitel (nach Abschnitt bzw. aus
`exam_questions` des Leitfadens), Teil 3 das Gesamtskript als Rahmenwissen, das Kapitel darin markiert.
Alle Verweise sind Anker innerhalb der Datei (`#sec-2-5`, `#frage-…`). Kapitel 0 (Einführung) hat
keinen Leitfaden und deshalb keine eigene Datei. Die Dateien sind Build-Ausgabe, nicht im Git-Baum:
jede enthält das ganze Skript. Ist genau diese Kapiteldatei die einzige ausgewählte Quelle und
behandelt das Audio nur dieses Kapitel, verlangt die Anleitung ausdrücklich einen Audiotitel mit
dem exakten Präfix **`GIL-<N>-`**, z. B. `GIL-2-Industrielle Innovation – Audio-Zusammenfassung`.
Das eingebettete Gesamtskript zählt dabei als Rahmenwissen, nicht als zusätzliche Quelle. Bei
mehreren ausgewählten Quellen oder kapitelübergreifenden Audios gilt diese Titelvorgabe nicht.

**Anki-Karteikarten** (`anki`, ohne Modellaufruf). Je Kapitel 1–9 ein Unterdeck
`GIL::Kapitel N – Titel` mit bis zu fünf Unterdecks: *1 Begriffe* und *2 Lückentexte* aus dem
Fettdruck des Skripts (ein fett gesetzter Begriff vor seiner Erklärung wird zur Frage, jede fette
Stelle eines Absatzes zur Lücke), *3 Prüfungsfragen* mit den Musterlösungen aus
`learning/exercises/` (KI-erstellt, so gekennzeichnet), *4 Abbildungen skizzieren* und *5 Karten von
Studierenden (unverifiziert)* aus den drei Decks in `input/`. Deren Karten tragen keine Kapitel; die
Zuordnung rechnet `anki_student` aus den Wörtern der Karte (tf-idf je Kapitel) und, bei Decks in
Skript-Reihenfolge, aus der Reihenfolge – sie ist gut, aber nicht fehlerfrei. Jede Karte nennt ihre
Quelle (Skriptseite, Prüfung, Deck). Deck-Ids und Notiz-Guids sind stabil: Sammlung und
Kapitelpakete enthalten dieselben Notizen, ein erneuter Import aktualisiert statt zu verdoppeln.
Die Elterndecks (`GIL`, `GIL::Kapitel N – …`) stehen ausdrücklich im Paket: Anki legt sie beim
Import einer `.apkg` selbst an, beim Wiederherstellen der `.colpkg` aber nicht.

Abbildungen erscheinen nur als unsere SVG-Rekonstruktion, sonst als Platzhaltertext – nie als
Ausschnitt aus dem Skript ([architecture.md](architecture.md#abbildungen-vier-schichten-ad)). Das gilt
auch für die Anki-Karten; Bilder aus den Decks der Studierenden sind schon in `flashcards` entfallen.

**Release** (je Meilenstein ein neues Tag `vX.Y`). `render-pdf`, `export-notebooklm` und `anki` schreiben je eine
`release-assets.tsv` (`Datei<TAB>Label` je Zeile, LF); `release` packt daraus `build/release/` mit eigener
Liste, und `gh release upload` übernimmt das Label hinter `#`:

```bash
python -m pipeline render-pdf && python -m pipeline export-notebooklm && python -m pipeline anki && python -m pipeline release
gh release create vX.Y --target main --title "Wissensbasis vX.Y" --notes-file <notizen.md>
while IFS=$'\t' read -r file label; do gh release upload vX.Y "build/release/$file#$label"; done < build/release/release-assets.tsv
```

Antwortet GitHub beim Anlegen mit HTTP 500, existiert das Release meist schon als Entwurf ohne
Dateien: dann die Schleife oben mit `--clobber` und `gh release edit vX.Y --draft=false`.

**Geheimes Gist** (dieselben `GIL-…`-Dateien als Markdown, die gezeigten SVGs, die PDFs). Ein Gist hat
keine Ordner und zeigt Bilder nur über absolute URLs, deshalb erzeugt `export-md` flache Dateien und
setzt die Bild-URL aus `GIB_IMAGE_BASE_URL`:

```bash
GIB_IMAGE_BASE_URL=https://gist.githubusercontent.com/<owner>/<gist-id>/raw python -m pipeline export-md
git clone https://gist.github.com/<gist-id>.git gist && cp build/markdown/* build/pdf/*.pdf gist/
cd gist && git add -A && git commit -m "…" && git push
```

`gh gist create` legt Gists standardmäßig geheim an (nie `--public`) und nimmt keine Binärdateien;
die PDFs kommen deshalb über das Git-Remote des Gists. Ein geheimes Gist ist **nicht privat**,
sondern nur ungelistet: Wer die URL kennt, kann es lesen. Bei späteren Ständen dasselbe Gist
aktualisieren statt ein neues anzulegen. Die Studierenden-Karteikarten gehören nicht hinein.
