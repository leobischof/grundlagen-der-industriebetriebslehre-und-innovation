<!-- Generiert von `python -m pipeline exercises` aus curation/figures/abb-66.yaml – nicht von Hand bearbeiten. -->

# Zeichenübung: Gozintograph

*Abbildung 66 – Skript S. 155 (PDF 165)*

## Aufgabe

Zeichne die Abbildung „Gozintograph“ aus dem Gedächtnis und beschrifte alle Elemente. Als Vorlage dient die [leere Übung](../../figures/exercises/abb-66-blank.svg): Die gestrichelten Kästen markieren, wo Text hingehört.

- Schwierigkeit: mittel
- Prüfungsrelevanz: mittel – Laut exams/topic-mapping.json einmal abgefragt (2025-02-04, nur als Stichwort „Gozintograph“ überliefert, Gedächtnisprotokoll): Erklären bzw. Zeichnen eines Gozintographen ist wahrscheinlich, eine Bedarfsrechnung ist nicht ausgeschlossen.
- Prüfungsfragen: `frage-2025-02-04-2`

## Worum es geht

Laut Skript (9.1.3) müssen Endprodukte für die Materialbedarfsplanung in Baugruppen und Komponenten untergliedert werden; die Stückliste nennt die je Produkteinheit benötigten Mengen. Zur Veranschaulichung der Stückliste kann ein Gozintograph („goes into“) gezeichnet werden: Er zeigt, welche Teile (P) in welche Montagen/Baugruppen (A) und schließlich in das Produkt eingehen, gegliedert nach Produktionsphasen. Begriffe laut Skript (DIN 199): Produkt (endgültiges Produktionsergebnis), Baugruppe (aus zwei oder mehr Teilen/Baugruppen niedrigerer Ordnung), Einzelteil (nicht zerstörungsfrei zerlegbar), Rohmaterial (Ausgangsmaterial). Mengenangaben an den Pfeilen enthält diese Abbildung nicht.

## Schritt-für-Schritt-Anleitung

1. Setze zuerst den zentralen Begriff und ordne die Unterpunkte darum oder darunter an.
2. Kästen einzeichnen:
   - „Produkt A“ – Endprodukt, abgerundetes dunkles Rechteck
   - „P5“ – Teil, Phase 2
   - „P6“ – Teil, Phase 2
   - „P7“ – Teil, Phase 2
   - „P1“ – Teil, Phase 3
   - „P2“ – Teil, Phase 3
   - „P3“ – Teil, Phase 3
   - „P4“ – Teil, Phase 3
3. Ebene einzeichnen:
   - „0. Produktionsphase“
   - „1. Produktionsphase“
   - „2. Produktionsphase“
   - „3. Produktionsphase“
4. Knoten einzeichnen:
   - „A3“ – Montage (dunkler Kreis), Phase 1
   - „A4“ – Montage, Phase 1
   - „A1“ – Montage, Phase 2
   - „A2“ – Montage, Phase 2
5. Legende einzeichnen:
   - „P....Teil“
   - „A....Montage“
6. Beziehungen und Verbindungen einzeichnen:
   - „A3“ geht_ein_in „Produkt A“
   - „A4“ geht_ein_in „Produkt A“
   - „A1“ geht_ein_in „A3“
   - „P5“ geht_ein_in „A3“
   - „P6“ geht_ein_in „A3“
   - „A2“ geht_ein_in „A4“
   - „P7“ geht_ein_in „A4“
   - „P1“ geht_ein_in „A1“
   - „P2“ geht_ein_in „A1“
   - „P2“ geht_ein_in „A2“ (Mehrfachverwendung von P2)
   - „P3“ geht_ein_in „A2“
   - „P4“ geht_ein_in „A2“
7. Mit den Muss-Inhalten unten abgleichen und erst dann die Lösung ansehen.

## Muss-Inhalte

- [ ] Endprodukt oben, Teile unten; Pfeile zeigen von unten nach oben in das übergeordnete Element
- [ ] Unterscheidung Teil (P, Kasten) und Montage/Baugruppe (A, Kreis) mit Legende
- [ ] Gliederung nach Produktionsphasen 0 bis 3
- [ ] Ein Teil kann in mehrere Montagen eingehen (P2 → A1 und A2)

## Typische Fehler

- Pfeilrichtung umgekehrt (vom Produkt zu den Teilen)
- Teile und Baugruppen nicht unterschieden
- Mehrfachverwendung eines Teils (P2) nicht dargestellt

## Selbstkontrolle

- [Originalabbildung aus dem Skript](../../figures/originals/abb-66.png) – maßgeblich
- [Rekonstruktion (Vektorgrafik)](../../figures/reconstructed/abb-66.svg)
- [Leere Übung](../../figures/exercises/abb-66-blank.svg)

Prüfe: Sind alle Muss-Inhalte abgehakt? Stimmen Reihenfolge, Anordnung und Beschriftungen mit dem Original überein?
