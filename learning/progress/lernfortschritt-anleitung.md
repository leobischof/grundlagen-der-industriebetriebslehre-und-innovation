# Lernfortschritt (lokal, privat)

Dieser Ordner hält deinen **persönlichen** Lernstand. Er wird **nie committet**: `.gitignore`
schließt alles hier aus außer dieser Datei und [`example.json`](example.json). Der Fortschritt ist
damit strikt von den unveränderlichen Quellen (Skript, Prüfungsfragen, Abbildungen) getrennt.

## Datei und Format

- Datei: `learning/progress/progress.json` (wird beim ersten Eintrag angelegt)
- Schema: [`schemas/progress.schema.json`](../../schemas/progress.schema.json)
- Beispiel: [`example.json`](example.json) (erzeugt mit genau den Befehlen unten)

Gespeichert wird **je Thema und Kompetenz**:

| Feld | Bedeutung |
|---|---|
| `last_practiced` | Datum der letzten Übung |
| `last_result` | Ergebnis der letzten Übung, 0–5 (Selbst- oder Tutor-Einschätzung) |
| `errors` | konkrete Fehler der letzten Übung (frühere stehen in `history`) |
| `mastery`, `mastery_level` | Beherrschungsgrad 0–1 und Stufe `unsicher` · `lernend` · `gefestigt` · `beherrscht` |
| `sketch_independent` | nur Kompetenz `zeichnung`: Skizze selbstständig aus dem Gedächtnis gezeichnet? |
| `next_due` | nächste Wiederholung |
| `repetitions`, `interval_days`, `ease` | interner Zustand der Wiederholungsplanung (SM-2) |
| `history` | die letzten 50 Übungen mit Datum, Ergebnis, Fehlern |

**Thema** ist eine ID der Wissensbasis: Abschnitt (`sec-2.5`), Abbildung (`abb-08`) oder ein
Thema aus `exams/topic-mapping.json`. **Kompetenz** ist ein Aufgabentyp der Prüfungsfragen:
`definition`, `verstaendnis`, `aufzaehlung`, `erklaerung`, `vergleich`, `berechnung`, `zeichnung`.

## Befehle

```bash
# Übung eintragen: Thema, Kompetenz, Ergebnis 0–5
python -m pipeline.progress record abb-08 zeichnung 2 --fehler "Achsenbeschriftung vergessen" --skizze nein
python -m pipeline.progress record sec-2.5 aufzaehlung 3 --fehler "nur 3 von 5 Arten genannt"

python -m pipeline.progress due                    # was ist heute fällig?
python -m pipeline.progress show                   # alles, nach Fälligkeit sortiert
python -m pipeline.progress show --thema abb-08
python -m pipeline.progress reset --thema abb-08 --ja   # ein Thema vergessen
python -m pipeline.progress reset --ja                  # alles löschen
```

Ergebnis-Skala: 0 keine Ahnung · 1 falsch · 2 falsch, Lösung kam bekannt vor · 3 richtig, aber
mühsam · 4 richtig, kurz gezögert · 5 perfekt.

## Planung der Wiederholungen

SM-2-Variante (Details und Begründung: [`docs/learning-method.md`](../../docs/learning-method.md),
Code: `pipeline/srs.py`): Ergebnis < 3 → morgen wieder; sonst 1 Tag, 6 Tage, dann jeweils
Intervall × Leichtigkeitsfaktor. Eine Zeichnung, die **nicht** selbstständig gelang, kommt
spätestens nach 3 Tagen wieder.
