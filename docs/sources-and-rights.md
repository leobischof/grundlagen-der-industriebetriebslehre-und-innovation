# Quellen, Vertrauensstufen und Rechte

## Quellen

Alle Quellen stehen in [`sources/manifest.yaml`](../sources/manifest.yaml), geschrieben von
`python -m pipeline ingest`. Je Quelle: kanonischer Dateiname, Originalname, **SHA-256**, Größe in
Bytes, Seitenzahl, Art und Vertrauensstufe. Von Hand ergänzte Schlüssel (z. B. Rechte, Notizen)
bleiben bei jedem Lauf erhalten. Die Quellen-IDs und Suchmuster selbst sind in `SOURCES`
(`pipeline/config.py`) festgelegt.

| ID | Art | Vertrauensstufe |
|---|---|---|
| `skript` | Skriptum 2024/25, Version 2.0 (Scan mit OCR-Schicht, 190 Seiten) | `primary` |
| `fragensammlung-uware` | Fragensammlung aus Gedächtnisprotokollen | `student-recollection` |
| `klausur-2026-04-29` | Abschrift einer Klausurangabe mit Punkten | `student-transcript` |
| `anki-benneb1001`, `anki-uware`, `anki-fri1703` | Anki-Decks von Studierenden | `unverified-student` |

## Vertrauensstufen

| Stufe | Bedeutung | Umgang |
|---|---|---|
| `primary` | Lehrunterlage des Lehrstuhls | maßgeblich für jede fachliche Aussage |
| `student-transcript` | Abschrift einer echten Prüfung durch Studierende | Fragen und Punkte vermutlich nahe am Original, Wortlaut nicht garantiert |
| `student-recollection` | Gedächtnisprotokoll | Thema verlässlich, Wortlaut und Umfang ungefähr, keine Punkte |
| `unverified-student` | selbst erstellte Lernkarten | **nie** als Quelle zitieren; nur als Übungsmaterial, Antworten gegen das Skript prüfen |

Jede Prüfungsfrage trägt die Stufe ihrer Quelle im Feld `trust`; die Lernkarten in
`learning/flashcards/` sind als `unverified-student` gekennzeichnet. Widerspricht eine Karte oder eine
Musterlösung dem Skript, gilt das Skript.

## Rechte

Die Nutzungs- und Weitergaberechte an Skript, Prüfungsunterlagen und Lernkarten sind **nicht
geklärt**. Daraus folgt:

- **Originale bleiben lokal.** `input/`, `sources/original-pdfs/`, alle `*.pdf` und `*.apkg` sind
  git-ignoriert. Das Repository trägt stattdessen das Manifest – genug, um zu prüfen, ob eine lokale
  Kopie exakt dieselbe Datei ist (gleicher SHA-256).
- **Privat heißt nicht erlaubt.** Ein privates Repository ist keine Veröffentlichung, ersetzt aber
  kein Nutzungsrecht. Das Repository bleibt privat und wird nicht weitergegeben, solange die Rechte
  ungeklärt sind.
- **Abgeleitete Inhalte sind trotzdem nah am Original.** `sources/ocr/`, `content/` und
  `figures/originals/` enthalten den Wortlaut und Bildausschnitte des Skripts. Sie dienen dem
  persönlichen Lernen; vor jeder Weitergabe an Dritte sind die Rechte zu klären.
- **PDF-Exporte** (`render-pdf`, GitHub-Release) sind aus dem Markdown der Wissensbasis gebaute
  Lernunterlagen – nie die Original-PDFs. Für sie gilt dasselbe wie für `content/`, ebenso für die
  Anki-Pakete (`anki`). Kein Export zeigt Bildausschnitte des Skripts, nur unsere eigenen
  SVG-Neuzeichnungen oder einen Platzhaltertext (`pipeline/figure_publish.py`). Eine automatische
  Umwandlung eines Ausschnitts in SVG (Vektorisieren) zählt nicht als eigene Zeichnung: Sie bleibt
  dasselbe Bild.
- **Keine persönlichen Daten, keine Geheimnisse.** Lernfortschritt (`learning/progress/`), API-Schlüssel,
  Zugangsdaten und `.env`-Dateien werden nie committet.

## Neue Quelle aufnehmen

1. Datei nach `input/` legen.
2. In `SOURCES` (`pipeline/config.py`) eine ID mit Suchmuster, kanonischem Namen, Art und
   Vertrauensstufe ergänzen.
3. `python -m pipeline ingest` ausführen und das aktualisierte Manifest committen.
4. Prüfungsunterlagen zusätzlich in `curation/exams.yaml` erfassen und danach
   `python -m pipeline all` ausführen (mindestens die Stufen `exams`, `link`, `build-content`,
   `validate`, `report`).
