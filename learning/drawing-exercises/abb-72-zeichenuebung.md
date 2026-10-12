<!-- Generiert von `python -m pipeline exercises` aus curation/figures/abb-72.yaml – nicht von Hand bearbeiten. -->

# Zeichenübung: Planungsabhängigkeiten

*Abbildung 72 – Skript S. 161 (PDF 171)*

## Aufgabe

Zeichne die Abbildung „Planungsabhängigkeiten“ aus dem Gedächtnis und beschrifte alle Elemente. Als Vorlage dient die [leere Übung](../../figures/exercises/abb-72-blank.svg): Die gestrichelten Kästen markieren, wo Text hingehört.

- Schwierigkeit: schwer
- Prüfungsrelevanz: mittel – In exams/topic-mapping.json ist der Abbildung keine Frage zugeordnet. Die Abbildung zeigt aber die Planungshierarchie mit Änderungszeiträumen und Rückkopplung, die zum Verständnis von Planung und Steuerung (Abbildung 76, Produktionsregelkreis) gebraucht wird; daher mittel.

## Worum es geht

Skript 9.1.5.1: Die Terminierung plant die zeitliche Zuordnung der Arbeitsaufgaben; Ergebnis ist der auftrags- und einrichtungsspezifische Produktionsplan als „Zielzustand“, von dem der tatsächliche Zustand durch Störungen abweicht. Die Abbildung zeigt, wie die Planung vom Produktionsprogramm (jährlich änderbar) über die mittelfristige (monatlich) zur kurzfristigen Terminplanung (wöchentlich) verfeinert wird und wie Rückmeldungen aus dem Betrieb die übergeordneten Ebenen korrigieren. Haupttreiber der Planung: Art, Menge, Termine und Qualität der Aufträge, Personal- und Maschinenkapazitäten, geplante Durchlaufzeiten.

## Schritt-für-Schritt-Anleitung

1. Lege zuerst die Reihenfolge der Bausteine fest und zeichne sie in Leserichtung.
2. Kästen einzeichnen:
   - „Produkionsprogramm“ – Tippfehler im Original (statt Produktionsprogramm); darunter Änderungszeitraum: 1 Jahr
   - „Mittelfristige Terminplanung“ – darunter Änderungszeitraum: 1 Monat
   - „Kurzfristige Terminplanung“ – darunter Änderungszeitraum: 1 Woche
   - „Materialversorgung / Produktionsplan“
   - „Betrieb“ – dunkel hinterlegt
3. Pfeile einzeichnen:
   - „Input“ – Band links in den Betrieb
   - „Output“ – Band rechts aus dem Betrieb
4. Beschriftungen einzeichnen:
   - „Verkaufsplanung“ – Eingang von oben in das Produktionsprogramm
   - „Programmzuweisung“ – Pfeil Produktionsprogramm → mittelfristige Terminplanung
   - „Versand der Bestellung“ – Pfeil mittelfristige → kurzfristige Terminplanung
   - „Feedback“ – zum Produktionsprogramm
   - „Grobe Terminplanung“ – rechts zwischen Produktionsprogramm und mittelfristiger Ebene, mit gepunkteter Linie und kleinem Pfeil nach unten
   - „Feedback“ – zur mittelfristigen Terminplanung
   - „Feedback (z.B. täglich, pro Bestellung)“ – vom Betrieb zur kurzfristigen Terminplanung
5. Beziehungen und Verbindungen einzeichnen:
   - „Verkaufsplanung“ fließt „Produkionsprogramm“
   - „Produkionsprogramm“ fließt „Mittelfristige Terminplanung“ (Programmzuweisung)
   - „Mittelfristige Terminplanung“ fließt „Kurzfristige Terminplanung“ (Versand der Bestellung)
   - „Kurzfristige Terminplanung“ fließt „Materialversorgung / Produktionsplan“
   - „Materialversorgung / Produktionsplan“ fließt „Betrieb“
   - „Input“ fließt „Betrieb“
   - „Betrieb“ fließt „Output“
   - „Betrieb“ rückkopplung „Kurzfristige Terminplanung“ (Feedback (z.B. täglich, pro Bestellung))
   - „Kurzfristige Terminplanung“ rückkopplung „Mittelfristige Terminplanung“ (Feedback)
   - „Mittelfristige Terminplanung“ rückkopplung „Produkionsprogramm“ (Feedback)
6. Mit den Muss-Inhalten unten abgleichen und erst dann die Lösung ansehen.

## Muss-Inhalte

- [ ] Drei Ebenen mit Änderungszeitraum: Produktionsprogramm 1 Jahr, mittelfristige Terminplanung 1 Monat, kurzfristige Terminplanung 1 Woche
- [ ] Abwärts: Verkaufsplanung, Programmzuweisung, Versand der Bestellung, Materialversorgung / Produktionsplan, Betrieb
- [ ] Aufwärts: Feedback je Ebene (unten z.B. täglich, pro Bestellung)
- [ ] Betrieb zwischen Input und Output

## Typische Fehler

- Feedback-Schleifen weggelassen (Planung nur von oben nach unten)
- Änderungszeiträume den falschen Ebenen zugeordnet

## Selbstkontrolle

- [Originalabbildung aus dem Skript](../../figures/originals/abb-72.png) – maßgeblich
- [Rekonstruktion (Vektorgrafik)](../../figures/reconstructed/abb-72.svg)
- [Leere Übung](../../figures/exercises/abb-72-blank.svg)

Prüfe: Sind alle Muss-Inhalte abgehakt? Stimmen Reihenfolge, Anordnung und Beschriftungen mit dem Original überein?
