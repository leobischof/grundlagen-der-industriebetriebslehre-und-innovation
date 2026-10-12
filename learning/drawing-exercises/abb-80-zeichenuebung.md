<!-- Generiert von `python -m pipeline exercises` aus curation/figures/abb-80.yaml – nicht von Hand bearbeiten. -->

# Zeichenübung: Dilemma der Ablaufplanung am Bsp. der Maschinenauslastung und Bestand

*Abbildung 80 – Skript S. 168 (PDF 178)*

## Aufgabe

Zeichne die Abbildung „Dilemma der Ablaufplanung am Bsp. der Maschinenauslastung und Bestand“ aus dem Gedächtnis und beschrifte alle Elemente. Als Vorlage dient die [leere Übung](../../figures/exercises/abb-80-blank.svg): Die gestrichelten Kästen markieren, wo Text hingehört.

- Schwierigkeit: leicht
- Prüfungsrelevanz: mittel – In exams/topic-mapping.json keiner Frage direkt zugeordnet; laut Notiz zu frage-2025-04-09-3 vertieft die Abbildung aber das zweimal geprüfte Dilemma der Ablaufplanung und eignet sich als Beispiel in der Erklärung.

## Worum es geht

Laut Skript (9.2.2) lassen sich bei hohem Bestand (Work-in-Process, WIP) hohe Auslastungen der Betriebsmittel erreichen; die Produkte müssen dann aber vor den Maschinen warten, was ihre Durchlaufzeiten erhöht. Werden Durchlaufzeiten und Bestände reduziert, sind die Betriebsmittel geringer ausgelastet. Die Abbildung veranschaulicht so das Dilemma der Ablaufplanung.

## Schritt-für-Schritt-Anleitung

1. Lege zuerst die Reihenfolge der Schritte fest und zeichne die Kästen in Leserichtung.
2. Kästen einzeichnen:
   - „Betriebsmittel (Fertigungsmaschine)“ – links, dunkles Quadrat mit Produkt in Bearbeitung
   - „Betriebsmittel (Fertigungsmaschine)“ – rechts, keine Warteschlange davor
3. Beschriftungen einzeichnen:
   - „Hoher Bestand (Wartend)“ – über der Warteschlange links
   - „Hoher Auslastung“ – über der Maschine links (Wortlaut des Originals, grammatisch „Hohe Auslastung“)
   - „Produkte“ – Klammer unter den fünf wartenden Produkten
   - „Geringe Auslastung (Wartend)“ – über der Maschine rechts; hier wartet die Maschine
4. Beziehungen und Verbindungen einzeichnen:
   - „Produkte“ fluss „Betriebsmittel (Fertigungsmaschine)“ (Produkte warten vor der Maschine; ein bearbeitetes Produkt verlässt sie nach rechts)
   - „Betriebsmittel (Fertigungsmaschine)“ zustand „Geringe Auslastung (Wartend)“ (keine wartenden Produkte, ein Produkt verlässt die Maschine nach rechts)
5. Mit den Muss-Inhalten unten abgleichen und erst dann die Lösung ansehen.

## Muss-Inhalte

- [ ] Links: viele wartende Produkte vor der Maschine → hoher Bestand, hohe Auslastung, lange Durchlaufzeit
- [ ] Rechts: keine Warteschlange → geringer Bestand, kurze Durchlaufzeit, aber Maschine wartet (geringe Auslastung)

## Typische Fehler

- „Wartend“ links den Produkten und rechts der Maschine zuordnen vergessen (rechts wartet die Maschine, nicht das Produkt)

## Selbstkontrolle

- [Originalabbildung aus dem Skript](../../figures/originals/abb-80.png) – maßgeblich
- [Rekonstruktion (Vektorgrafik)](../../figures/reconstructed/abb-80.svg)
- [Leere Übung](../../figures/exercises/abb-80-blank.svg)

Prüfe: Sind alle Muss-Inhalte abgehakt? Stimmen Reihenfolge, Anordnung und Beschriftungen mit dem Original überein?
