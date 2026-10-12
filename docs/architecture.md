# Architektur der Wissensbasis

Dieses Dokument beschreibt, **was wo liegt, wer es schreibt und welche Formate gelten**. Die
Formate sind zusätzlich maschinenlesbar als JSON-Schemas in [`schemas/`](../schemas/) hinterlegt;
`python -m pipeline validate` prüft jede Datei dagegen. Weicht dieses Dokument von einem Schema
ab, gilt das Schema.

## Grundsätze

1. **Lokal und deterministisch zuerst.** Text, Seitenstruktur, Abbildungsausschnitte, Verknüpfungen
   und Prüfungen erzeugt Python ohne KI. Ein Modell wird nur für Interpretation eingesetzt
   (Abbildungen beschreiben, SVGs rekonstruieren, visuelle Kontrolle) – und jeder solche Aufruf wird
   in [`curation/ai-log.jsonl`](../curation/ai-log.jsonl) protokolliert. Details: [pipeline.md](pipeline.md).
2. **Eine Quelle der Wahrheit (SSOT).** Jeder Pfad und jede Konstante steht in
   [`pipeline/config.py`](../pipeline/config.py), jede kuratierte Tatsache in genau einer Datei unter
   `curation/`. Generierte Dateien werden nie von Hand bearbeitet, sondern neu erzeugt.
3. **Kuratiert vor generiert.** Dateien unter `curation/` schreibt ein Mensch oder ein
   protokollierter KI-Durchgang; die Pipeline liest sie nur. Alles andere ist aus ihnen und aus den
   Originalen reproduzierbar.
4. **Originale bleiben lokal.** Skript, Prüfungsunterlagen und Anki-Decks werden nie committet;
   [`sources/manifest.yaml`](../sources/manifest.yaml) hält Dateiname, Größe und SHA-256 fest.
   Siehe [sources-and-rights.md](sources-and-rights.md).
5. **Ehrlichkeit vor Vollständigkeit.** Was fehlt oder unsicher ist, steht in den Berichten
   ([`reports/validation.md`](../reports/validation.md), [`reports/coverage.md`](../reports/coverage.md))
   und in den Metadaten (`needs_review`, `quality.status`), nie stillschweigend weggelassen.

## Vier Schichten des Inhalts

Die Aufgabenstellung verlangt, vier Arten von Text strikt zu trennen. Jede hat ihren eigenen Ort:

| Schicht | Bedeutung | Ort | Erzeugt von |
|---|---|---|---|
| 1 · **original** | das Skript selbst (Scan) | `sources/original-pdfs/skript-2024-25-v2.0.pdf` (nur lokal); Abbildungen als Ausschnitt in `figures/originals/` | Lehrstuhl |
| 2 · **ocr** | Textschicht des Scans, Zeile für Zeile mit Koordinaten und Qualitätsmaß | `sources/ocr/skript-pages.jsonl` | `extract-text` |
| 3 · **bereinigt** | redaktionell bereinigte Fassung: OCR-Fehler korrigiert (nur über `curation/ocr-corrections.yaml`), Überschriften, Fußnoten, Formeln (LaTeX), Abbildungen eingebunden, Fettdruck des Skripts als `**…**` – **Wortlaut des Skripts** | `content/` | `build-content` |
| 4 · **ki-erklaerung** | zusätzliche Erklärungen, Beispiele, Übungen eines Modells oder Lernagenten | `learning/` (nie in `content/`) | Lernagent, gekennzeichnet |

Regeln:

- Die Frontmatter jeder Inhaltsdatei nennt ihre Schicht (`layer:`). In `content/` steht nur `bereinigt`.
- Fachliche Aussagen werden beim Bereinigen nie verändert. Ist eine Stelle unsicher, bleibt der
  OCR-Wortlaut stehen und die Stelle wird markiert; der Abschnitt behält
  `quality.status: maschinell-bereinigt-ungeprueft`, bis ein Mensch ihn gegen das Original gelesen hat.
- KI-Erklärungen (Schicht 4) tragen sichtbar die Kennzeichnung **„Zusatzwissen, nicht im Skript“**,
  sobald sie über das Skript hinausgehen, und verweisen sonst auf die Skriptstelle.

## Verzeichnisse

| Pfad | Inhalt | Art |
|---|---|---|
| `input/` | Ablage für neue Originale | lokal, git-ignoriert |
| `sources/original-pdfs/` | kanonische Kopien der Originale | lokal, git-ignoriert |
| `sources/manifest.yaml` | Quellen: Datei, Größe, SHA-256, Seiten, Art, Vertrauensstufe | generiert (`ingest`), Handschlüssel bleiben erhalten |
| `sources/ocr/skript-pages.jsonl` | OCR-Schicht je PDF-Seite | generiert |
| `curation/structure.yaml` | kanonisches Inhaltsverzeichnis: Kapitel, Abschnitte, PDF-Seiten, übersprungene Seiten | kuratiert |
| `curation/figures.yaml` | jede Abbildung, Tabelle, Formel: ID, Titel, Seite, Bounding Box | kuratiert |
| `curation/figures/<id>.yaml` | strukturierte Beschreibung einer Abbildung (Schicht B, unten) | kuratiert (KI, protokolliert) |
| `curation/ocr-corrections.yaml`, `topics.yaml`, `exams.yaml` | OCR-Korrekturen, Themenkatalog, Prüfungsquellen | kuratiert |
| `curation/ai-log.jsonl` | jeder KI-Aufruf mit geschätzten Tokens | nur anhängen |
| `content/` | bereinigter Skripttext, eine Datei je Abschnitt X.Y; `skript-inhalt.md`, je Kapitel `<kapitel>-ueberblick.md` und `<kapitel>-literatur.md` | generiert (`build-content`) |
| `figures/originals/<id>.png` | Originalausschnitt jeder Abbildung (200 dpi) | generiert (`extract-figures`) |
| `figures/reconstructed/<id>.svg` | Vektor-Rekonstruktion (Schicht C) | kuratiert (KI, protokolliert) |
| `figures/exercises/<id>-blank.svg` | Zeichenübung: Rekonstruktion ohne Antworten (Schicht D) | generiert (`exercises`) |
| `figures/manifest.json` | alle Schichten je Abbildung auf einen Blick | generiert (`extract-figures`) |
| `exams/questions.json`, `questions.md` | Prüfungsfragen-Datenbank | generiert (`exams`) |
| `exams/topic-mapping.json` | Themen ↔ Abschnitte ↔ Abbildungen ↔ Fragen | generiert (`exams`/`link`) |
| `exams/frequency-analysis.md` | Häufigkeit und Priorität der Themen | generiert (`exams`) |
| `learning/drawing-exercises/<id>-zeichenuebung.md` | Zeichenanleitung je Schwerpunkt-Abbildung | generiert (`exercises`) |
| `learning/flashcards/<deck>.*` | Anki-Karten der Studierenden, **unverifiziert** | generiert (`flashcards`) |
| `learning/flashcards/skizzieren.md` | Skizzierkarten: „Skizziere …“ → Originalabbildung | generiert (`anki`) |
| `learning/chapters/<kapitel>-leitfaden.md` | Lernleitfaden je Kapitel (Übersicht: `leitfaeden-uebersicht.md`) | kuratiert (KI, protokolliert) |
| `learning/exercises/<kapitel>-musterloesungen.md` | Musterlösungen je Kapitel (Übersicht: `musterloesungen-uebersicht.md`) | kuratiert (KI, protokolliert) |
| `learning/progress/` | persönlicher Lernfortschritt | lokal, git-ignoriert (außer `lernfortschritt-anleitung.md`, Beispiel) |
| `reports/` | Validierung, Abdeckung, Bilderkennung, Beschriftungsabgleich | generiert |
| `schemas/` | JSON-Schemas der Formate | von Hand, versioniert |
| `build/` | Cache, Stempel, PDF-Export | lokal, git-ignoriert, reproduzierbar |
| `pipeline/` | Python-Code, eine Stufe je Modul | Code |
| `tests/` | pytest, läuft offline auf einem Mini-Baum | Code |

### Dateinamen: jeder Name nur einmal

Jede Datei im Repository hat einen Namen, den es sonst nirgends gibt – auch nicht in einem
anderen Ordner und auch nicht in anderer Groß-/Kleinschreibung. Wer Dateien ohne ihre Ordner
lädt (NotebookLM, Gist, flacher Download), sieht nur den Namen; zwei `README.md` oder zwei
`abb-08.md` wären dort nicht zu unterscheiden oder würden einander überschreiben.

- Der unterscheidende Zusatz steht **hinten**: `<kapitel>-ueberblick.md`, `<kapitel>-leitfaden.md`,
  `<kapitel>-musterloesungen.md`, `<id>-zeichenuebung.md`, `<id>-blank.svg`. So bleiben die Dateien
  eines Kapitels bzw. einer Abbildung alphabetisch beieinander.
- Einzige `README.md` ist die im Wurzelverzeichnis; Ordnerübersichten heißen nach ihrem Inhalt
  (`skript-inhalt.md`, `leitfaeden-uebersicht.md`).
- Gleiche Stämme mit verschiedener Endung (`abb-08.png`, `abb-08.svg`, `abb-08.yaml`) sind erlaubt;
  der Name ist samt Endung eindeutig.
- Generierte Namen entstehen nur in `pipeline/config.py` (`chapter_overview_name`,
  `chapter_literature_name`, `drawing_guide_name`, `CONTENT_INDEX_NAME`).
- `validate` prüft das (Gruppe „Dateinamen“, [`qa_checks_names.py`](../pipeline/qa_checks_names.py))
  und meldet jede Doppelung als Fehler.

## Formate (Verträge)

### Abschnittsdatei `content/<kapitel>/<X.Y>-<slug>.md`

Eine Datei je Abschnitt X.Y; tiefere Gliederungsebenen sind Überschriften darin. Je Kapitel
zusätzlich `README.md` (`id: kap-NN`, Einleitung und Inhaltsverzeichnis) und `literatur.md`
(`id: lit-NN`), dazu `content/skript-inhalt.md` als Gesamtübersicht.
Schema: [`section-frontmatter.schema.json`](../schemas/section-frontmatter.schema.json).

```yaml
---
id: sec-2.5
title: Arten der Innovation
chapter: "02"
chapter_title: Industrielle Innovation
section: "2.5"
subsections: ["2.5.1", "2.5.2"]
pdf_pages: [39, 40, 41]        # jede PDF-Seite, die der Abschnitt berührt
printed_pages: [29, 30, 31]    # gedruckte Seite = PDF-Seite − 10 (ab PDF-Seite 11)
figures: [abb-08, abb-09]
related_sections: [sec-2.4]
exam_questions: [frage-2026-04-29-1]
layer: bereinigt
source: skript-2024-25-v2.0
quality:
  status: maschinell-bereinigt-ungeprueft
  ocr_suspicious_ratio: 0.031
  footnotes_unanchored: 1
---
```

Rumpf: `# 2.5 …`, `## 2.5.1 …`; Seitenmarken `<!-- Seite 29 (PDF 39) -->`; Abbildungen als
`![Abbildung 8: Produktlebenszyklus](../../figures/originals/abb-08.png)` mit Bildunterschrift und
Quellenangabe; Formeln als `$$ … $$`; Fußnoten `[^12]` mit Definition am Dateiende; Fußnoten, deren
Verweisstelle nicht sicher zu finden war, unter `## Fußnoten ohne sicheren Textanker`.

### Abbildungen: vier Schichten A–D

| Schicht | Datei | Pflicht |
|---|---|---|
| A · Original | `figures/originals/<id>.png` | jede kuratierte Abbildung |
| B · Metadaten | `curation/figures/<id>.yaml` | die prüfungsrelevanten Schwerpunkt-Abbildungen (`PRIORITY_FIGURES` in `pipeline/qa_checks_figures.py`), sonst optional |
| C · Rekonstruktion | `figures/reconstructed/<id>.svg` | sobald die Metadaten `reconstruction.status: faithful` oder `needs_review` nennen |
| D · Übung | `figures/exercises/<id>-blank.svg` + `learning/drawing-exercises/<id>-zeichenuebung.md` | erwartet für jede geprüfte (`faithful`) Rekonstruktion |

IDs: `abb-NN` (Abbildung NN), `tab-NN` (Tabelle), `formel-*`, `abb-u<Seite>` (unbeschriftete Grafik).

**Was ein Export zeigen darf.** Schicht A ist eine Kopie aus dem Skript und bleibt Arbeitsmaterial im
privaten Repository. Kein Export – PDF, Markdown/Gist, NotebookLM – enthält je einen solchen
Ausschnitt (Urheberrecht): Er zeigt die Rekonstruktion (C) oder, solange es keine gibt, einen
Platzhaltertext „Bild des Skripts hier nicht abgedruckt (Urheberrecht) – siehe Original-Skript“ mit
der Beschreibung aus B, falls vorhanden. Der NotebookLM-Export ist reiner Text: Er zeigt auch keine
SVG, sondern Platzhalter, Beschreibung und Aussage (`meaning`) in Worten. Diese Regel steht einmal in
`pipeline/figure_publish.py`; jeder Export ruft sie auf. Je mehr Abbildungen und Tabellen rekonstruiert sind, desto weniger
Platzhalter bleiben.

**Metadaten (B)** – Schema [`figure-metadata.schema.json`](../schemas/figure-metadata.schema.json):
`type`, `description`, `axes`, `elements` (jedes Kästchen, jede Beschriftung im Originalwortlaut),
`relations`, `curves`, `meaning`, `exam_relevance` (Stufe, Begründung, Fragen-IDs),
`drawing` (`difficulty`, `must_know`, `common_mistakes`), `reconstruction` (`status`, `svg`, `notes`),
`source` (PDF-/Druckseite, OCR-Text der Beschriftungen).

**SVG-Konventionen (C)** – von Hand als SVG-Code geschrieben, nie von einem Bildgenerator:

- Wurzelelement mit `data-figure-id="<id>"` und `data-status="faithful|needs_review"`, `<title>` = Titel;
  `viewBox` im Seitenverhältnis des PNG; Schrift `Arial, Helvetica, sans-serif`.
- **Keine eingebetteten Rasterbilder** (`<image>` ist verboten).
- Alles, was in der Prüfung gezeichnet und beschriftet werden muss (Achsentitel, Phasen, Kästchentexte),
  trägt `class="answer"`; Rahmen, Achsenlinien und Hilfslinien nicht. Die Übung (D) entsteht, indem
  `exercises` diese Elemente durch gestrichelte Platzhalter ersetzt.
- `faithful` heißt: mit dem Original nebeneinander gerendert verglichen und inhaltlich deckungsgleich.
  Bleibt etwas unsicher → `needs_review` und Begründung in `reconstruction.notes`.

### Prüfungsfragen

`exams/questions.json` = `{"questions": [...], "exams": [...]}`; jede Frage nach
[`exam-question.schema.json`](../schemas/exam-question.schema.json). Pflicht: `id`
(`frage-<Prüfungsdatum>-<Nr>`), `source` (Quellen-ID aus dem Manifest), `date`, `text`
(Originalwortlaut). Empfohlen (sonst Warnung): `sections`, `task_types`, `competencies`, `points`
(`null` = Punktzahl unbekannt). Aufgabentypen: `definition`, `verstaendnis`, `aufzaehlung`,
`erklaerung`, `vergleich`, `berechnung`, `zeichnung` – dieselbe Liste ist das Kompetenz-Vokabular
des Lernfortschritts. `competencies` beschreibt dagegen die geforderte Denkleistung (`wissen`,
`verstehen`, `anwenden`, `zeichnen`, `vergleichen`, `berechnen`; Liste in `pipeline/exam_model.py`).
Jede Frage trägt außerdem `trust` (Vertrauensstufe ihrer Quelle, siehe
[sources-and-rights.md](sources-and-rights.md)).

Neben dem Originalwortlaut (`text`/`wording`, oft nur ein Stichwort wie „ABC und Bestandsdilemma“)
trägt jede Frage `prompt`: die ausformulierte Aufgabe mit Operatorverb, wie sie in einer Klausur
stünde („Erklären Sie das Bestandsdilemma und die ABC-Analyse. Skizzieren Sie …“). `prompt` ist eine
Bearbeitung (Schicht *bereinigt*), nie die Quelle. `exams/questions.md` zeigt `prompt` groß und fett,
alles andere (Originalwortlaut, Thema, Abschnitte, Abbildungen, Kennung) klein darunter; Abbildungen
verlinken nur auf unsere SVG-Rekonstruktion, nie auf den Ausschnitt aus dem Skript. Der
Prüfungsmodus laut Studierenden (`exam_mode:` in `curation/exams.yaml`) steht vor den Fragen.

`exams/topic-mapping.json` = `{"topics": [...], "by_section": {"2.5": [Fragen-IDs]}, "by_figure":
{"abb-08": [Fragen-IDs]}}`, Schema [`topic-mapping.schema.json`](../schemas/topic-mapping.schema.json).

### Lernfortschritt

Lokal, je Thema und Kompetenz: [`learning/progress/lernfortschritt-anleitung.md`](../learning/progress/lernfortschritt-anleitung.md),
Schema [`progress.schema.json`](../schemas/progress.schema.json), Verfahren
[learning-method.md](learning-method.md).

### Abbildungs-Manifest

`figures/manifest.json` verbindet je Abbildung Seite, Kapitel/Abschnitt und die Pfade aller vier
Schichten (`null`, wo eine Schicht fehlt). Schema
[`figure-manifest-entry.schema.json`](../schemas/figure-manifest-entry.schema.json). Nach neuen
SVGs oder Metadaten `python -m pipeline extract-figures` erneut ausführen – sonst meldet `validate`
ein veraltetes Manifest.

## Code-Aufbau

Eine Stufe je Modul unter `pipeline/`, jede mit `run(pages=None, dry_run=False, force=False) -> int`,
registriert in `pipeline/__main__.py`. Geteilte Bausteine: `config` (Pfade, Konstanten), `catalog`
(Zugriff auf `curation/`), `cache` (SHA-256-Cache, `write_if_changed`). Die Qualitätsprüfung ist in
kleine Module je Belang geteilt (`qa_checks_structure`, `qa_checks_figures`, `qa_checks_exams`,
`qa_checks_links`, `qa_checks_names`) und arbeitet über `qa_repo.RepoView`, damit die Tests sie auf einem Mini-Baum
ausführen können.
