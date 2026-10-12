# Lernmethode und Wiederholungsplanung

Wie der Lernagent mit der Wissensbasis arbeitet, steht in [AGENTS.md](../AGENTS.md). Dieses Dokument
begründet das **Verfahren dahinter**: was gespeichert wird, wie Wiederholungen geplant werden und
warum. Code: `pipeline/srs.py` (Planung, reine Funktionen), `pipeline/progress_store.py` (Datei),
`pipeline/progress.py` (Kommandozeile). Format und Befehle: [learning/progress/lernfortschritt-anleitung.md](../learning/progress/lernfortschritt-anleitung.md).

## Didaktische Grundlage

Die Prüfung verlangt drei Dinge: Begriffe und Listen **exakt wiedergeben** (Definitionen,
Aufzählungen in der Reihenfolge des Skripts), Zusammenhänge **erklären** und Diagramme **aus dem
Gedächtnis zeichnen und beschriften**. Daraus folgen vier Prinzipien:

1. **Abrufen statt Wiederlesen** (*retrieval practice*). Wer eine Antwort selbst formuliert, behält
   sie deutlich besser als nach erneutem Lesen. Deshalb fragt der Agent zuerst und zeigt die Lösung
   erst nach dem eigenen Versuch.
2. **Verteiltes Wiederholen** (*spacing*). Wiederholungen kurz vor dem Vergessen sind am
   wirksamsten; der Abstand wächst mit jedem Erfolg. Das plant SM-2 (unten).
3. **Kompetenz statt Thema.** „Produktlebenszyklus“ kann man erklären können und trotzdem nicht
   zeichnen. Fortschritt wird daher **je Thema und Kompetenz** gespeichert.
4. **Priorität nach Prüfungsrelevanz.** Die Lernreihenfolge folgt dem Prioritäts-Score in
   [`exams/frequency-analysis.md`](../exams/frequency-analysis.md) – einer Heuristik aus
   Studierenden-Quellen, keiner Prognose.

## Was gespeichert wird

Je **Thema** (eine ID der Wissensbasis: `sec-2.5`, `abb-08` oder eine Themen-ID aus
`exams/topic-mapping.json`) und **Kompetenz** (ein Aufgabentyp der Prüfungsfragen: `definition`,
`verstaendnis`, `aufzaehlung`, `erklaerung`, `vergleich`, `berechnung`, `zeichnung` – die Liste wird
aus `schemas/exam-question.schema.json` gelesen, nicht kopiert):

| Anforderung | Feld |
|---|---|
| letzte Übung | `last_practiced` |
| Ergebnis | `last_result` (0–5) |
| Fehler | `errors` (konkret, z. B. „Phase Sättigung vergessen“) |
| Beherrschungsgrad | `mastery` (0–1) und `mastery_level` |
| nächste Wiederholung | `next_due` |
| Skizze selbstständig gezeichnet? | `sketch_independent` (nur Kompetenz `zeichnung`) |

Dazu der Planungszustand (`repetitions`, `interval_days`, `ease`) und die letzten 50 Übungen in
`history`. Die Datei `learning/progress/progress.json` ist **lokal und git-ignoriert**: persönliche
Lerndaten sind strikt von den unveränderlichen Quellen getrennt, und nichts im Lernsystem schreibt
außerhalb von `learning/progress/`.

## Ergebnis-Skala

| Ergebnis | Bedeutung |
|---:|---|
| 5 | perfekt |
| 4 | richtig, kurz gezögert |
| 3 | richtig, aber mühsam |
| 2 | falsch, Lösung kam bekannt vor |
| 1 | falsch |
| 0 | keine Ahnung |

Ab 3 (`PASS`) gilt ein Inhalt als erinnert. Der Agent schlägt das Ergebnis mit Begründung vor; die
lernende Person darf es korrigieren. Bei Aufzählungen ist „richtig“ nur die vollständige Liste – drei
von fünf Punkten sind höchstens 2.

## Planung: SM-2 mit zwei Abweichungen

Grundlage ist SM-2 (Wozniak 1990): einfach, gut dokumentiert und für einige hundert Einträge völlig
ausreichend.

- **Ergebnis < 3:** Wiederholungszähler auf 0, nächste Wiederholung **morgen**.
- **Ergebnis ≥ 3:** Intervall beim ersten Erfolg **1 Tag**, beim zweiten **6 Tage**, danach
  bisheriges Intervall × Leichtigkeitsfaktor (`ease`), gerundet.
- **Leichtigkeitsfaktor:** Start 2,5, Untergrenze 1,3; nach jeder Übung
  `ease ← ease + 0,1 − (5 − q) · (0,08 + (5 − q) · 0,02)` mit Ergebnis `q`.
  Das ergibt +0,10 bei 5, ±0 bei 4, −0,14 bei 3, −0,32 bei 2, −0,54 bei 1, −0,80 bei 0.

Abweichungen vom Original:

1. **Zeichnungen:** Wurde eine Skizze **nicht** selbstständig aus dem Gedächtnis gezeichnet
   (`--skizze nein`), ist das Intervall auf **3 Tage** begrenzt (`SKETCH_CAP_DAYS`), auch wenn die
   Erklärung dazu gut war. In der Prüfung zählt nur die eigene Zeichnung.
2. **Obergrenze 365 Tage** (`MAX_INTERVAL_DAYS`). Reines SM-2 wächst ohne Grenze; für eine
   Prüfungsvorbereitung ist ein Eintrag, der ein Jahr nicht geübt wurde, ohnehin wieder neu.

## Beherrschungsgrad

`mastery` ist ein gleitender Mittelwert von Ergebnis/5 mit Gewicht 0,5 auf der neuesten Übung
(`MASTERY_ALPHA`). Ein einzelner Glückstreffer hebt ein Thema damit nicht auf „beherrscht“, ein
einzelner Ausrutscher wirft es nicht ganz zurück. Die Stufe verlangt zusätzlich ein Mindestintervall
– wer ein Thema erst gestern zum ersten Mal richtig hatte, beherrscht es noch nicht:

| Stufe | Bedingung |
|---|---|
| `beherrscht` | mastery ≥ 0,9 und Intervall ≥ 21 Tage |
| `gefestigt` | mastery ≥ 0,8 und Intervall ≥ 6 Tage |
| `lernend` | mastery ≥ 0,5 |
| `unsicher` | darunter |
| `neu` | noch nie geübt (nur Anzeige) |

## Sitzungsplanung

Eine Sitzung beginnt mit `python -m pipeline.progress due`: zuerst die fälligen Wiederholungen
(älteste Fälligkeit zuerst, `unsicher` vor `lernend`), danach neue Themen in der Reihenfolge der
Häufigkeitsanalyse. Zeichenaufgaben werden eingestreut, weil sie am meisten Wiederholung brauchen.
Jede Übung wird **sofort** eingetragen (`record`), damit ein Abbruch keinen Fortschritt verliert.

## Grenzen

- Die Ergebnisse sind Selbst- bzw. Agenten-Einschätzungen, keine objektive Messung.
- Der Prioritäts-Score stützt sich auf Gedächtnisprotokolle und eine Klausurabschrift von
  Studierenden; Themen ohne bekannte Prüfungsfrage können trotzdem geprüft werden.
- Die Bewertung von Handskizzen aus Fotos ist unsicher (Bildqualität, Handschrift). Der Agent nennt
  diese Unsicherheit und vergibt im Zweifel das niedrigere Ergebnis.
