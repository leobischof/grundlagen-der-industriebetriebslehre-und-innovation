# Abdeckungsbericht

Generiert von `python -m pipeline report` aus den versionierten Dateien – nicht von Hand bearbeiten. Gezählt wird nur, was tatsächlich vorliegt.

**Skript vollständig verarbeitet:** ja – jede zugeordnete Seite, jeder Abschnitt und jede Abbildung liegt vor (Qualitätsstufen siehe unten).

## Seiten

| Kennzahl | Wert |
|---|---:|
| PDF-Seiten des Skripts | 190 |
| bewusst übersprungen (Titel-, Inhaltsverzeichnis-, Leerseiten; `structure.yaml`) | 19 |
| im Inhaltsverzeichnis einem Abschnitt zugeordnet | 171 |
| mit gespeicherter OCR-Textschicht | 190 |
| davon mit schwacher OCR | 1 [176] |
| in Abschnittsdateien enthalten (`pdf_pages`) | 171 / 171 (100 %) |

## Abschnitte

Abschnittsdateien (X.Y): 32 / 32 (100 %).

Qualitätsstatus: `maschinell-bereinigt-ungeprueft` 32

| Kapitel | Abschnitte | Dateien | eingebundene Abb. | verknüpfte Fragen |
|---|---:|---:|---:|---:|
| 00 Zielsetzung und Inhalte der Lehrveranstaltung | 1 | 1 | 0 | 0 |
| 01 Die Industrie | 3 | 3 | 7 | 0 |
| 02 Industrielle Innovation | 5 | 5 | 7 | 13 |
| 03 Industrie Management | 3 | 3 | 13 | 5 |
| 04 Grundlagen der Innovation | 2 | 2 | 6 | 4 |
| 05 Produktentstehung | 6 | 6 | 11 | 3 |
| 06 Ausgewählte Innovationsprozesse | 3 | 3 | 4 | 5 |
| 07 Grundlagen des Industrie Managements | 3 | 3 | 3 | 1 |
| 08 Ausgewählte Kapitel des strategischen Produktionsmanagements | 3 | 3 | 17 | 17 |
| 09 Das operative Produktionsmanagement | 3 | 3 | 28 | 13 |

## Abbildungen

Kuratiert (`curation/figures.yaml`): 98 (85 figure, 6 formula, 7 table).

| Schicht | Anzahl |
|---|---:|
| (A) Original-PNG | 98 / 98 (100 %) |
| in `content/` eingebunden | 98 / 98 (100 %) |
| (B) strukturierte Metadaten | 92 / 98 (94 %) |
| (C) SVG-Rekonstruktion | 92 / 98 (94 %) |
| … davon geprüft (`faithful`) | 92 |
| … noch zu prüfen (`needs_review`) | 0  |
| (D) Zeichenübung (`-blank.svg`) | 56 |
| Zeichenanleitung | 56 |

### Prüfungsrelevante Schwerpunkt-Abbildungen

| ID | Titel | Original | Metadaten | SVG | Status | Übung |
|---|---|:-:|:-:|:-:|---|:-:|
| `abb-08` | Produktlebenszyklus | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-11` | Ansoff Matrix | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-15` | Industriebetrieb als Arbeitssystem | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-35` | Integrationsbereiche der Themen Innovationsprozess & Produktentwicklung | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-37` | Stage-Gate-Prozess nach Cooper | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-38` | Aufbau eines Gates | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-44` | Planungsgrundfälle nach Grundig | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-45` | Typologisierung von Produktionssystemen | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-46` | Einordnung der Produktionsarten | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-47` | Punktfertigung | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-48` | Gruppenfertigung | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-49` | Reihenfertigung | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-50` | Zusammenhang - Produktionsart & Fertigungsform | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-51` | Planungsvorgehen nach Grundig | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-57` | Einfluss von Effizienz, Konsistenz und Suffizienz auf Aufwand und Ertrag | ✓ | ✓ | ✓ | faithful | ✓ |
| `abb-70` | ABC Analyse | ✓ | ✓ | ✓ | faithful | ✓ |

## Fußnoten

- Verweise `[^N]` im Text: 131
- Definitionen: 136, davon mit Textanker: 131
- laut Frontmatter ohne sicheren Textanker: 59

## Prüfungsfragen

- Fragen gesamt: 61 (fragensammlung-uware: 55, klausur-2026-04-29: 6)
- einem Abschnitt zugeordnet: 61 / 61 (100 %)
- mit Abbildungsbezug: 47, davon Zeichenaufgaben: 4
- Aufgabentypen: aufzaehlung 22, definition 7, erklaerung 28, zeichnung 4
- Abschnitte (X.Y) mit mindestens einer Frage: 17
- ohne Zuordnung: keine

## Lernkarten (Anki, unverified-student)

- 413 Karten in 3 Dateien

## KI-Aufrufe (aus `curation/ai-log.jsonl`)

Gesamt: 26 protokollierte Aufrufe, geschätzt 2489700 Eingabe- und 514100 Ausgabe-Tokens (2026-10-11 bis 2026-10-13).

| Stufe | Aufrufe | Eingabe-Tokens | Ausgabe-Tokens |
|---|---:|---:|---:|
| audio-alignment | 1 | 0 | 0 |
| caption-transcription | 1 | 6000 | 4000 |
| crop-qc | 1 | 11500 | 1500 |
| exam-prompts | 1 | 602000 | 13000 |
| exams | 1 | 5200 | 600 |
| export-naming | 1 | 10000 | 3500 |
| figure-icons | 1 | 11000 | 7000 |
| figure-reconstruction | 12 | 1475000 | 276000 |
| figures-batch-b | 1 | 80000 | 45000 |
| interactive-reader | 2 | 27000 | 17500 |
| layout-qc | 1 | 22000 | 3000 |
| learning-guides | 3 | 240000 | 143000 |

Die Pipeline selbst ruft nie ein Modell auf; ein zweiter Lauf erzeugt 0 neue Einträge.

## Lücken

- Abschnitte ohne Datei (0): keine
- Schwerpunkt-Abbildungen ohne Metadaten: keine
- Schwerpunkt-Abbildungen ohne SVG: keine
- Themen mit Lücken (2):
  - Ökonomische Kennzahlen (Produktivität, Wirtschaftlichkeit, Rentabilität, Liquidität) – ohne SVG: formel-liquiditaet, formel-produktivitaet, formel-rentabilitaet, formel-spezifische-kosten, formel-spezifischer-mitteleinsatz, formel-wirtschaftlichkeit
  - Produktentstehung (Ziele, Effektivität/Effizienz, Produktplanung, -entwicklung, Produktionssystem-Entwicklung) – Text fehlt: 5
