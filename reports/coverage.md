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
| (B) strukturierte Metadaten | 16 / 98 (16 %) |
| (C) SVG-Rekonstruktion | 16 / 98 (16 %) |
| … davon geprüft (`faithful`) | 16 |
| … noch zu prüfen (`needs_review`) | 0  |
| (D) Zeichenübung (`-blank.svg`) | 16 |
| Zeichenanleitung | 16 |

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

Gesamt: 9 protokollierte Aufrufe, geschätzt 429700 Eingabe- und 222100 Ausgabe-Tokens (2026-10-11 bis 2026-10-12).

| Stufe | Aufrufe | Eingabe-Tokens | Ausgabe-Tokens |
|---|---:|---:|---:|
| caption-transcription | 1 | 6000 | 4000 |
| crop-qc | 1 | 11500 | 1500 |
| exams | 1 | 5200 | 600 |
| figure-reconstruction | 1 | 65000 | 25000 |
| figures-batch-b | 1 | 80000 | 45000 |
| layout-qc | 1 | 22000 | 3000 |
| learning-guides | 3 | 240000 | 143000 |

Die Pipeline selbst ruft nie ein Modell auf; ein zweiter Lauf erzeugt 0 neue Einträge.

## Lücken

- Abschnitte ohne Datei (0): keine
- Schwerpunkt-Abbildungen ohne Metadaten: keine
- Schwerpunkt-Abbildungen ohne SVG: keine
- Themen mit Lücken (37):
  - Historische Entwicklung der Industrie (Industrie 1.0 bis 4.0) – ohne SVG: abb-01, abb-02
  - Wirtschaftliche Bedeutung der Industrie (Zahlen, Fertigung, Österreich) – ohne SVG: abb-03, tab-01, tab-02, tab-03
  - Aktuelle Herausforderungen der Industriebetriebe – ohne SVG: abb-04
  - Generische Wettbewerbsstrategien nach Porter (Kostenführerschaft, Differenzierung, Fokussierung) – ohne SVG: abb-05, abb-06
  - Begriffe und Definitionen (Invention, Innovation, Imitation, Modifikation) – ohne SVG: abb-07
  - Produktinnovation (Kategorien neuer Produkte, Portfolio) – ohne SVG: abb-09, abb-10
  - Abgrenzung der Industriebetriebe (Merkmale, Dienstleistung, Handwerk, Wirtschaftseinheiten) – ohne SVG: abb-12, abb-13, abb-14, abb-18
  - Ökonomische Kennzahlen (Produktivität, Wirtschaftlichkeit, Rentabilität, Liquidität) – ohne SVG: formel-liquiditaet, formel-produktivitaet, formel-rentabilitaet, formel-spezifische-kosten, formel-spezifischer-mitteleinsatz, formel-wirtschaftlichkeit
  - Produktion als Kernaufgabe (Produktionsprozess und seine Elemente) – ohne SVG: abb-16, abb-17
  - Innovationsstrategie (Kriterien) – ohne SVG: tab-04
  - Innovationsbarrieren und deren Überwindung – ohne SVG: abb-19
  - Entrepreneurship (Definition, Haupttypen SME/IDE, Persönlichkeitsmerkmale) – ohne SVG: abb-20, abb-21, tab-05
  - Entrepreneurship-Prozess (Erkennungs-, Entwicklungs-, Umsetzungsphase) – ohne SVG: abb-22
  - Produktentstehung (Ziele, Effektivität/Effizienz, Produktplanung, -entwicklung, Produktionssystem-Entwicklung) – Text fehlt: 5; ohne SVG: abb-23, abb-24, abb-25
  - Integrierte Produktentstehung (Arten der Integration, Kosten, Rahmenstruktur) – ohne SVG: abb-26, abb-27, abb-28, abb-34
  - Simultaneous / Concurrent Engineering (Prinzipien, magisches Dreieck) – ohne SVG: abb-29, abb-30, abb-31, abb-32, abb-33
  - Innovationsprozess nach Thom – ohne SVG: abb-36
  - Design Thinking Methode (IDEO, 5-Step-Prozess) – ohne SVG: abb-39
  - Funktionen und Kenngrößen des Industrie Managements – ohne SVG: abb-40, abb-41
  - Konzept des integrierten Managements – ohne SVG: abb-42
  - Standortplanung (strategisch, Raumsicht; interne und externe Treiber) – ohne SVG: abb-43
  - Planungsvorgehen der Fabrikplanung nach Grundig (Zielplanung bis Ausführung) – ohne SVG: abb-52, abb-53, abb-54
  - Nachhaltigkeit (Brundtland-Definition, drei Prinzipien, SDGs) – ohne SVG: abb-55
  - Strategische Bedeutung der Nachhaltigkeit (drei Dimensionen, Spannungsfeld unternehmerischen Wirkens) – ohne SVG: abb-56
  - Dekarbonisierung und Materialeffizienz in der Industrie – ohne SVG: abb-58, abb-59
  - Planung und Absatzplanung (Zeitreihenanalyse, Kausalmodell) – ohne SVG: abb-60, abb-61, abb-62
  - Kurzfristige Produktionsprogrammplanung (Produktfeld, Optimierung) – ohne SVG: abb-63, abb-64, abb-65
  - Materialbedarfsplanung und Gozintograph – ohne SVG: abb-66, abb-67
  - Materialklassen und Bedarfsarten (primär, sekundär, tertiär, Brutto-/Nettobedarf) – ohne SVG: abb-68, abb-69
  - Zeit- und Kapazitätsplanung (Terminierung, Kapazität, ERP) – ohne SVG: abb-71, abb-72, abb-73, abb-75
  - Gesamtanlageneffektivität (OEE) – ohne SVG: abb-74
  - Produktionssteuerung (Regelkreis, Starten/Überwachen, Auftragsfreigabe, Maschinenbelegung) – ohne SVG: abb-76, abb-77, abb-78, tab-06
  - Dilemma der Ablaufplanung (Auslastung vs. Durchlaufzeit/Bestand) – ohne SVG: abb-79, abb-80, abb-81, abb-82
  - Kontrolle und Leistungskennzahlen (Überblick) – ohne SVG: abb-83
  - Qualität und Qualitätsmanagement (Ziele, TQM, Six Sigma, SPC) – ohne SVG: abb-84
  - Geschwindigkeit und Zuverlässigkeit/Liefertreue (Entkopplungspunkt) – ohne SVG: abb-85
  - Flexibilität (Arten der Flexibilität) – ohne SVG: tab-07
