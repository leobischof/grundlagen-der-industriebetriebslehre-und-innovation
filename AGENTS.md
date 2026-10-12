# AGENTS.md – Anleitung für Lern- und Pflegeagenten

Diese Wissensbasis bereitet die Lehrveranstaltung *Grundlagen der Industriebetriebslehre und
Innovation* (TU Graz, Skriptum 2024/25) für KI-gestütztes Lernen auf. Dieses Dokument sagt dir,
**wo was liegt, welchen Quellen du trauen darfst und wie du in jedem Lernmodus vorgehst**.
Sprache gegenüber der lernenden Person: **Deutsch**.

> **Änderungen am Repository nur über Pull Requests – für alle, auch den Eigentümer.** Niemand
> pusht direkt auf `main`, niemand force-pusht. Jede Änderung: Feature-Branch → Conventional
> Commits → PR mit grüner CI → Squash-Merge. Details in
> [Abschnitt 7](#7--beiträge-branches-und-pull-requests).

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

## 7 · Beiträge: Branches und Pull Requests

`main` ist geschützt, und zwar für **alle** – auch für den Eigentümer @leobischof und für Agenten,
die mit seinem Zugang arbeiten. Jede Änderung, ob Inhalt, Code oder Doku, läuft über einen
Feature-Branch und einen Pull Request. Lies diese Regeln, bevor du committest.

### 7.1 Was GitHub erzwingt

Diese Regeln setzt GitHub serverseitig durch, ohne Ausnahme für Admins:

| Regel | Wo |
|---|---|
| Kein direkter Push auf `main`, Änderungen nur per Pull Request | Branch Protection `main` |
| CI-Jobs `qa` und `konventionen` grün, Branch auf dem Stand von `main` | Branch Protection `main` |
| Alle Diskussionen im PR aufgelöst | Branch Protection `main` |
| Lineare Historie: nur Squash-Merge, keine Merge-Commits | Branch Protection + Repo-Einstellung |
| `main` kann nicht gelöscht werden | Branch Protection + Ruleset |
| **Kein Force-Push auf irgendeinen Branch** | Ruleset „alle Branches: kein Force-Push“ |
| Neue Branches nur mit erlaubtem Präfix (siehe 7.2) | Ruleset „Branch-Namen“ |
| Branch wird nach dem Merge automatisch gelöscht | Repo-Einstellung |

@leobischof ist Code Owner ([`.github/CODEOWNERS`](.github/CODEOWNERS)) und wird zu jedem PR als
Reviewer angefragt. Eine Freigabe ist nicht Pflicht, weil GitHub niemandem erlaubt, den eigenen PR
freizugeben – sonst könnte der Eigentümer selbst nichts mehr mergen.

### 7.2 Konventionen (geprüft vom CI-Job `konventionen`)

Quelle der Wahrheit ist [`.github/scripts/conventions.py`](.github/scripts/conventions.py); was dort
steht, gilt – diese Liste ist nur die Zusammenfassung.

- **Branch-Name:** `präfix/kurz-beschreibung`, nur Kleinbuchstaben, Ziffern und `-._`, z. B.
  `fix/ocr-seite-51`, `content/abbildung-12`, `feature/neue-uebung`. Präfixe: `feat`, `fix`,
  `docs`, `content`, `refactor`, `test`, `perf`, `build`, `ci`, `chore`, `style`, `revert`,
  `feature`, `hotfix`, `release`.
- **Commit-Titel und PR-Titel** nach Conventional Commits: `typ: beschreibung` oder
  `typ(bereich): beschreibung`, höchstens 72 Zeichen, kein Punkt am Ende. Typen wie oben ohne
  `feature`/`hotfix`/`release`; `content` steht für Änderungen an der Wissensbasis selbst, `!` nach
  dem Typ markiert einen Bruch (`refactor!: …`).
- Ein Branch hat **ein** Anliegen. Der PR-Titel wird beim Squash-Merge zum Commit auf `main`.

Selbst prüfen, bevor du pushst:

```bash
python .github/scripts/conventions.py branch "$(git branch --show-current)"
python .github/scripts/conventions.py commits origin/main HEAD
```

### 7.3 Ablauf

```bash
git switch main && git pull --ff-only
git switch -c fix/ocr-seite-51          # Feature-Branch, nie auf main arbeiten
# … ändern an der Quelle der Wahrheit (Abschnitt 6), Pipeline laufen lassen …
python -m pipeline offline && python -m pytest
git add <dateien>                       # gezielt, nie Originale, Fortschritt oder Zugangsdaten
git commit -m "fix: OCR-Fehler auf Seite 51"
git push -u origin fix/ocr-seite-51
gh pr create --base main --fill         # PR öffnen
gh pr checks --watch                    # qa und konventionen abwarten
gh pr merge --squash                    # nur wer mergen darf (siehe unten)
```

Ist `main` inzwischen weitergelaufen, den Branch mit `git merge origin/main` (oder in GitHub mit
„Update branch“) aktualisieren, nicht per Rebase – ein Rebase bräuchte einen Force-Push, und der ist
gesperrt. Der Squash-Merge hält die Historie auf `main` trotzdem linear. Ein schon gepushter Commit
wird nicht umgeschrieben, sondern mit einem neuen Commit korrigiert.

**Release und Gist** ([docs/pipeline.md](docs/pipeline.md#veröffentlichen-release-und-gist)) erst,
wenn die Änderung per PR auf `main` ist; das Tag zeigt immer auf einen Commit von `main`.

### 7.4 Für Agenten zusätzlich

- **Nie** auf `main` committen, nie `--force`/`--force-with-lease`, nie Branch Protection,
  Rulesets oder Repository-Einstellungen ändern – außer @leobischof verlangt es ausdrücklich.
- Den eigenen PR nur mergen, wenn @leobischof das erlaubt hat. Seine eigenen Agenten (Claude Code in
  seinem Auftrag) dürfen per `gh pr merge --squash` mergen, sobald `qa` und `konventionen` grün sind;
  Agenten anderer Personen mergen nie.
- Im PR-Text sagen, was geändert wurde, welche Quelle es belegt und dass `pipeline offline` und
  `pytest` grün sind; jeden KI-Durchgang wie in Abschnitt 6 protokollieren.
- Das Repository ist **privat** und bleibt es. Nichts daraus veröffentlichen (kein Fork in ein
  öffentliches Konto, keine öffentlichen Gists, keine Originale anhängen).
