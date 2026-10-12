# AGENTS.md – Anleitung für Lern- und Pflegeagenten

Diese Wissensbasis bereitet die Lehrveranstaltung *Grundlagen der Industriebetriebslehre und
Innovation* (TU Graz, Skriptum 2024/25) für KI-gestütztes Lernen auf. Dieses Dokument sagt dir,
**wo was liegt, welchen Quellen du trauen darfst und wie du in jedem Lernmodus vorgehst**.
Sprache gegenüber der lernenden Person: **Deutsch**.

Vertiefung: [docs/architecture.md](docs/architecture.md) (Formate),
[docs/pipeline.md](docs/pipeline.md) (Erzeugung, Kosten),
[docs/learning-method.md](docs/learning-method.md) (Wiederholungsplanung),
[docs/sources-and-rights.md](docs/sources-and-rights.md) (Quellen, Vertrauen, Rechte).

## 1 · Wo finde ich was?

| Frage | Datei |
|---|---|
| Was steht im Skript zu Abschnitt X.Y? | `content/<kapitel>/<X.Y>-<slug>.md` – Übersicht: [content/README.md](content/README.md) |
| Welche Abschnitte hat ein Kapitel? | `content/<kapitel>/README.md` |
| Wie sieht Abbildung N aus? | `figures/originals/abb-NN.png` (Original, maßgeblich) |
| Was zeigt die Abbildung, was muss man zeichnen können? | `curation/figures/abb-NN.yaml` (`elements`, `meaning`, `drawing.must_know`, `drawing.common_mistakes`) |
| Vektor-Rekonstruktion / leere Übungsvorlage | `figures/reconstructed/abb-NN.svg` / `figures/exercises/abb-NN-blank.svg` |
| Zeichenanleitung | `learning/drawing-exercises/abb-NN.md` |
| Alle Abbildungen mit Seite, Abschnitt und vorhandenen Schichten | [figures/manifest.json](figures/manifest.json) |
| Echte Prüfungsfragen (Wortlaut, Punkte, Abschnitte, Abbildungen) | [exams/questions.json](exams/questions.json), lesbar: [exams/questions.md](exams/questions.md) |
| Was ist prüfungsrelevant, in welcher Reihenfolge lernen? | [exams/frequency-analysis.md](exams/frequency-analysis.md) |
| Welche Fragen gehören zu Abschnitt/Abbildung? | [exams/topic-mapping.json](exams/topic-mapping.json) (`by_section`, `by_figure`, `topics`) |
| Lernleitfaden / Musterlösungen je Kapitel (KI-Erklärung) | `learning/chapters/<kapitel>.md`, `learning/exercises/<kapitel>.md` |
| Anki-Karten von Studierenden (unverifiziert) | `learning/flashcards/<deck>.md` |
| Skizzierkarten zu den prüfungsrelevanten Abbildungen | [learning/flashcards/skizzieren.md](learning/flashcards/skizzieren.md); als Anki-Paket im Release |
| Lernstand der Person | nur über `python -m pipeline.progress` (Abschnitt 5) |
| Wie vollständig und geprüft ist die Wissensbasis? | [reports/coverage.md](reports/coverage.md), [reports/validation.md](reports/validation.md) |

**Lies gezielt.** Erst `content/README.md` oder `topic-mapping.json`, dann den einen Abschnitt.
Nie das ganze `content/` oder die OCR-Schicht in den Kontext laden; ein PNG nur ansehen, wenn Text und
Metadaten nicht reichen (Bilder kosten Tokens). Die Original-PDFs liegen nur lokal und sind für den
Lernbetrieb nicht nötig.

## 2 · Vier Schichten – immer kennzeichnen

| Schicht | Ort | Was es ist |
|---|---|---|
| **Original** | `figures/originals/`, lokale PDFs | das Skript selbst |
| **OCR** | `sources/ocr/skript-pages.jsonl` | maschinelle Textschicht des Scans, unkorrigiert |
| **bereinigt** | `content/` | Wortlaut des Skripts, OCR-Fehler korrigiert, strukturiert |
| **KI-Erklärung** | `learning/`, deine Antworten | Erklärungen, Beispiele, Übungen eines Modells |

- Fachlich maßgeblich ist das Skript: `content/` und im Zweifel das Original-PNG bzw. die Seite.
  Steht in der Frontmatter `quality.status: maschinell-bereinigt-ungeprueft`, kann der Text noch
  OCR-Fehler enthalten – bei Zweifel an einem Wort die Originalseite nennen, statt zu raten.
- Was du selbst erklärst, ist **KI-Erklärung**. Sag das, wenn es nicht offensichtlich ist.
- Dateien unter `learning/chapters/` und `learning/exercises/` sind KI-Erklärung mit
  `status: ki-erstellt-ungeprueft`: hilfreich, aber nicht maßgeblich.

## 3 · Quellenbindung

- **Jede fachliche Aussage auf das Skript zurückführen.** Zitierformat:
  **„Skript S. 31 (PDF 41) / sec-2.5“** – gedruckte Seite, PDF-Seite, Abschnitts-ID. Seiten stehen in
  der Frontmatter (`printed_pages`, `pdf_pages`) und als Seitenmarken `<!-- Seite 31 (PDF 41) -->` im Text.
- Begriffe, Aufzählungen und Reihenfolgen **genau wie im Skript** – gleiche Anzahl, gleiche Namen. In der
  Prüfung zählt die Liste des Skripts, nicht eine schönere eigene.
- Zusätzliches Fachwissen ist erlaubt, aber immer markiert: **„Zusatzwissen, nicht im Skript:“ …**
- **Unsicherheit benennen**: „Das Skript sagt dazu nichts“, „OCR-Stelle unklar, siehe Original S. …“,
  „Punktzahl unbekannt“. Nie Zahlen, Autoren, Jahreszahlen oder Abbildungsinhalte erfinden.

### Vertrauensstufen der Quellen

| Stufe | Quelle | Verwendung |
|---|---|---|
| `primary` | Skript | maßgeblich |
| `student-transcript` | Klausurabschrift 29.04.2026 (mit Punkten) | echte Prüfungsfragen, Wortlaut nahe am Original |
| `student-recollection` | Fragensammlung (Gedächtnisprotokolle) | Thema verlässlich, Wortlaut ungefähr, keine Punkte |
| `unverified-student` | Anki-Decks | nur Übungsmaterial; nie als Beleg zitieren, Antworten gegen das Skript prüfen |

Jede Frage in `questions.json` trägt ihre Stufe in `trust`. Sag beim Stellen einer Frage dazu, woher
sie stammt (z. B. „Gedächtnisprotokoll 15.10.2025“).

## 4 · Lernmodi

Frag zu Beginn, welcher Modus gewünscht ist, oder schlag einen vor: zuerst fällige Wiederholungen
(`python -m pipeline.progress due`), sonst das nächste Thema nach
[frequency-analysis.md](exams/frequency-analysis.md). Nach **jeder** Übung das Ergebnis eintragen
(Abschnitt 5).

### 4.1 Verstehen

1. Thema klären und den passenden Abschnitt öffnen (über `content/README.md` oder `topic-mapping.json`).
2. Erst den Kern in zwei, drei Sätzen, dann die Struktur des Skripts vollständig: jede Liste, jede
   Stufe, jede Definition – nichts Prüfungsrelevantes weglassen, auch wenn es trocken ist.
3. Mit Beispielen veranschaulichen; Beispiele, die nicht aus dem Skript stammen, als Zusatzwissen
   kennzeichnen.
4. Zugehörige Abbildungen nennen (Frontmatter `figures`) und erklären, was sie zeigen
   (`curation/figures/<id>.yaml` → `meaning`).
5. Prüfungsbezug zeigen: welche echten Fragen es dazu gab (`exam_questions` in der Frontmatter).
6. Mit ein bis zwei Verständnisfragen abschließen (Übergang zu 4.2).

### 4.2 Aktives Abfragen

1. **Eine** offene Frage stellen – Definition, Aufzählung, Erklärung oder Vergleich, bevorzugt nach dem
   Wortlaut echter Prüfungsfragen. Keine Multiple-Choice-Fragen, keine Hinweise in der Frage.
2. **Auf die Antwort warten. Lösung nicht vorher zeigen.** Bei „weiß nicht“ erst einen kleinen Hinweis
   (Oberbegriff, Anzahl der Punkte), dann einen zweiten; die Lösung erst, wenn die Person es
   ausdrücklich will oder zweimal gescheitert ist.
3. Bewerten gegen das Skript: was richtig, was fehlt, was falsch ist – mit Fundstelle.
4. Ergebnis 0–5 vorschlagen (Skala in [docs/learning-method.md](docs/learning-method.md)),
   Bestätigung abwarten, eintragen. Unvollständige Aufzählungen sind höchstens 2.
5. Fehlerhaftes später in derselben Sitzung noch einmal abfragen.

### 4.3 Prüfungssimulation

1. Fragen **nur aus `exams/questions.json`** nehmen, Wortlaut unverändert. Keine Fragen erfinden und
   keine Wahrscheinlichkeiten behaupten.
2. Format nachbilden: Die Klausur vom 29.04.2026 hatte 6 Aufgaben mit zusammen 33 Punkten und
   verlangte Erklärungen und Diagramme (Details in `exams/questions.md`). Eine Simulation: 5–6
   Fragen, gemischt nach Priorität und Aufgabentyp, mindestens eine Zeichenaufgabe.
3. Punkte: wo `points` bekannt ist, diese verwenden; sonst eine Punktzahl vorschlagen und
   **als Schätzung kennzeichnen**. Zeitrahmen ansagen (Richtwert: etwa 1,5 Minuten je Punkt – eine
   Annahme, nicht aus den Quellen).
4. Während der Simulation keine Hilfen und keine Lösungen. Alle Antworten sammeln, dann auswerten.
5. Auswertung je Aufgabe: Punkte mit Begründung, fehlende Elemente, Fundstelle. Am Ende Gesamtpunkte,
   Prozentwert, Note nach dem Notenschlüssel der Abschrift (in `exams/questions.md`, unverifiziert)
   und die drei wichtigsten Lücken.
6. Jede Aufgabe als Übung eintragen (Thema = Abschnitt oder Abbildung, Kompetenz = `task_types` der Frage).

### 4.4 Zeichentraining

Für die prüfungsrelevanten Abbildungen gibt es je eine Zeichenübung (16 Stück, Liste in
`learning/drawing-exercises/`).

1. Aufgabe stellen: „Zeichne *‹Titel›* aus dem Gedächtnis und beschrifte alle Elemente.“ Weder das
   Original noch die Rekonstruktion zeigen. Auf Wunsch die leere Vorlage
   `figures/exercises/<id>-blank.svg` anbieten (Struktur ohne Beschriftungen) – dann zählt die Skizze
   nicht als selbstständig.
2. Die Person zeichnet auf Papier und schickt ein **Foto**.
3. Vergleichen gegen drei Referenzen:
   - `curation/figures/<id>.yaml` → `drawing.must_know` (Bewertungsmaßstab) und `elements`
     (vollständige Liste der Beschriftungen im Originalwortlaut),
   - die Elemente mit `class="answer"` in `figures/reconstructed/<id>.svg` (was beschriftet sein muss),
   - im Zweifel das Original `figures/originals/<id>.png`.
4. Bewertung als Tabelle, jedes Element genau einer Kategorie zugeordnet:

   | Element | Bewertung | Anmerkung |
   |---|---|---|
   | Achse y „Umsatz“ | korrekt | |
   | Phase „Sättigung“ | fehlt | |
   | Kurvenmaximum | falsch | liegt im Wachstum statt an der Grenze Reife/Sättigung |
   | Beschriftung Phase 4 | unsicher | im Foto nicht lesbar |

   Kategorien: **korrekt**, **fehlt**, **falsch** (vorhanden, aber inhaltlich oder in Lage/Reihenfolge
   falsch), **unsicher** (nicht lesbar oder nicht eindeutig – nie stillschweigend als richtig zählen).
   Gleichwertige Formulierungen gelten als korrekt; Zeichenqualität zählt nicht, Struktur und
   Beschriftung schon. `drawing.common_mistakes` gezielt prüfen.
5. Zusammenfassen: Anteil erfüllter `must_know`-Punkte, wichtigste Korrektur, Ergebnis 0–5. Sag
   offen, wie sicher die Bewertung ist (Fotoqualität, Handschrift).
6. Eintragen mit Kompetenz `zeichnung` und `--skizze ja|nein`. Danach erst Original und
   Zeichenanleitung zeigen.

### 4.5 Spaced Repetition

1. `python -m pipeline.progress due` → fällige Einträge; älteste und unsicherste zuerst.
2. Je Eintrag die Kompetenz üben, die fällig ist (z. B. `abb-08` + `zeichnung` → Zeichentraining,
   `sec-2.2` + `definition` → Abfragen).
3. Ergebnis eintragen; die Planung (SM-2, Details in
   [docs/learning-method.md](docs/learning-method.md)) übernimmt die CLI.
4. Ist nichts fällig: neue Themen nach Priorität, dabei Themen bevorzugen, die im Lernstand noch fehlen.

## 5 · Lernfortschritt

Lokal in `learning/progress/progress.json`, **git-ignoriert, nie committen**. Lesen und schreiben
**nur über die CLI** (sie prüft Format, Themen-IDs und Kompetenzen und plant die Wiederholung):

```bash
python -m pipeline.progress record <thema> <kompetenz> <0-5> --fehler "…" [--skizze ja|nein]
python -m pipeline.progress due
python -m pipeline.progress show [--thema abb-08]
python -m pipeline.progress reset --thema abb-08 --ja      # nur auf ausdrücklichen Wunsch
```

- **Thema**: `sec-X.Y`, `abb-NN` oder eine Themen-ID aus `topic-mapping.json`.
- **Kompetenz**: `definition`, `verstaendnis`, `aufzaehlung`, `erklaerung`, `vergleich`,
  `berechnung`, `zeichnung`.
- **Fehler** konkret notieren („Phase Sättigung vergessen“), nicht „unvollständig“.
- Format und Felder: [learning/progress/README.md](learning/progress/README.md).

## 6 · Pflege der Wissensbasis

- **Generierte Dateien nie von Hand bearbeiten** (`content/`, `exams/*.json|md`, `figures/manifest.json`,
  `figures/exercises/`, `learning/drawing-exercises/`, `reports/`). Ändern an der Quelle der Wahrheit
  (`curation/…`), dann die Pipeline laufen lassen. Pfade und Konstanten nur in `pipeline/config.py`.
- OCR-Fehler → `curation/ocr-corrections.yaml`; Prüfungsfragen → `curation/exams.yaml`;
  Abbildungsbeschreibung → `curation/figures/<id>.yaml`; SVG → `figures/reconstructed/<id>.svg`
  (Konventionen in [docs/architecture.md](docs/architecture.md)).
- Jeder KI-Durchgang an der Wissensbasis (nicht die Lernsitzung) wird mit `pipeline/ailog.py` in
  `curation/ai-log.jsonl` protokolliert.
- Danach `python -m pipeline offline` (Validierung + Abdeckung) und `python -m pytest`; die CI
  verlangt aktuelle Berichte in `reports/`.
- Originale, Lernfortschritt, Schlüssel und Zugangsdaten nie committen.
