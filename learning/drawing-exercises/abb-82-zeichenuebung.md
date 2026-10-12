<!-- Generiert von `python -m pipeline exercises` aus curation/figures/abb-82.yaml – nicht von Hand bearbeiten. -->

# Zeichenübung: Visualisierung des Dilemmas der Ablaufplanung mit Produktionskennlinien

*Abbildung 82 – Skript S. 170 (PDF 180)*

## Aufgabe

Zeichne die Abbildung „Visualisierung des Dilemmas der Ablaufplanung mit Produktionskennlinien“ aus dem Gedächtnis und beschrifte alle Elemente. Als Vorlage dient die [leere Übung](../../figures/exercises/abb-82-blank.svg): Die gestrichelten Kästen markieren, wo Text hingehört.

- Schwierigkeit: schwer
- Prüfungsrelevanz: mittel – In exams/topic-mapping.json keiner Frage direkt zugeordnet; vertieft laut Notiz zu frage-2025-04-09-3 das zweimal geprüfte Dilemma der Ablaufplanung und begründet es mit Produktionskennlinien.

## Worum es geht

Laut Skript (9.2.2) zeigen Produktionskennlinien, wie sich ein Arbeitssystem bei sonst unveränderten Randbedingungen verhält, wenn ein anderer Bestand (WIP) eingestellt wird. Sie charakterisieren das logistische Verhalten bezüglich Leistung/Auslastung, Durchlaufzeit und Termintreue bei einer Bestandsveränderung. Die Linien zeigen, dass kein gleichzeitiges Optimum für alle Zielgrößen existiert: Eine hohe Auslastung erfordert hohe Bestände, die ihrerseits lange Durchlaufzeiten verursachen. Geringer Bestand, geringe Durchlaufzeit und hohe Termineinhaltung unterstützen sich, konkurrieren aber mit hoher Leistung/Auslastung.

## Schritt-für-Schritt-Anleitung

1. Zeichne zuerst das Achsenkreuz mit Pfeilspitzen und lass oben genug Platz für Beschriftungen.
2. x-Achse beschriften: „Bestand (WIP)“, Richtung rechts.
3. y-Achse beschriften: „(unbeschriftet; Leistung, Durchlaufzeit bzw. Termineinhaltung)“, Richtung oben.
4. Kästen einzeichnen:
   - „hohe Termineinhaltung“ – oben
   - „geringe Durchlaufzeit“ – links, senkrecht
   - „geringer Bestand“ – unten
   - „hohe Leistung/ Auslastung“ – rechts, senkrecht
5. Legende einzeichnen:
   - „Teilziele unterstützen sich“ – schwarzer Doppelpfeil
   - „Teilziele konkurrieren“ – grauer Zickzack-Doppelpfeil
6. Kurve „Leistung“ zeichnen: steiler, fast linearer Anstieg bei kleinem Bestand, dann Abknicken und Sättigung auf hohem Niveau.
   - beginnt nahe null links unten
   - ab mittlerem Bestand nahezu waagerecht
7. Kurve „Durchlaufzeit“ zeichnen: anfangs flach auf niedrigem Niveau, danach annähernd linear steigend.
   - startet über der Leistungskurve, wird früh von ihr gekreuzt
   - endet rechts knapp unter dem Leistungsniveau
8. Kurve „Termineinhaltung“ zeichnen: glockenförmig: steigt ab mittlerem Bestand steil an, Maximum bei mittlerem Bestand, fällt danach wieder stark ab.
   - beginnt erst rechts vom Nullpunkt
   - Maximum etwa in der Mitte der x-Achse
   - kreuzt die Durchlaufzeitkurve auf beiden Flanken
9. Beziehungen und Verbindungen einzeichnen:
   - „geringe Durchlaufzeit“ unterstützt „hohe Termineinhaltung“ (schwarzer gebogener Doppelpfeil)
   - „geringe Durchlaufzeit“ unterstützt „geringer Bestand“ (schwarzer gebogener Doppelpfeil)
   - „hohe Termineinhaltung“ konkurriert „hohe Leistung/ Auslastung“ (grauer Zickzack-Doppelpfeil)
   - „geringer Bestand“ konkurriert „hohe Leistung/ Auslastung“ (grauer Zickzack-Doppelpfeil)
10. Mit den Muss-Inhalten unten abgleichen und erst dann die Lösung ansehen.

## Muss-Inhalte

- [ ] x-Achse: Bestand (WIP)
- [ ] Leistung: steil steigend, dann Sättigung; Durchlaufzeit: flach, dann linear steigend; Termineinhaltung: Glockenkurve
- [ ] Vier Ziele: hohe Termineinhaltung, geringe Durchlaufzeit, geringer Bestand, hohe Leistung/ Auslastung
- [ ] Geringer Bestand und geringe Durchlaufzeit sowie geringe Durchlaufzeit und hohe Termineinhaltung unterstützen sich
- [ ] Hohe Leistung/ Auslastung konkurriert mit geringem Bestand und mit hoher Termineinhaltung

## Typische Fehler

- Leistung linear weiter steigend statt sättigend gezeichnet
- Durchlaufzeit fallend statt mit dem Bestand steigend gezeichnet
- Unterstützende und konkurrierende Zielpaare vertauscht

## Selbstkontrolle

- [Originalabbildung aus dem Skript](../../figures/originals/abb-82.png) – maßgeblich
- [Rekonstruktion (Vektorgrafik)](../../figures/reconstructed/abb-82.svg)
- [Leere Übung](../../figures/exercises/abb-82-blank.svg)

Prüfe: Sind alle Muss-Inhalte abgehakt? Stimmen Reihenfolge, Anordnung und Beschriftungen mit dem Original überein?
