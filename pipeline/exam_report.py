"""Markdown rendering of the exam database (German prose for learners).

Pure functions from data to text: exams/questions.md (questions grouped by date) and
exams/frequency-analysis.md (topic ranking with the formula printed in full).
"""
from __future__ import annotations

from . import catalog, exam_stats

SOURCE_LABEL = {"fragensammlung-uware": "Fragensammlung (Gedächtnisprotokoll)",
                "klausur-2026-04-29": "Klausur-Abschrift"}
TRUST_LABEL = {"student-recollection": "Gedächtnisprotokoll von Studierenden, unverifiziert",
               "student-transcript": "Abschrift der Angabe durch Studierende, unverifiziert"}
COVERAGE_LABEL = {"voll": "durch das Skript abgedeckt", "teilweise": "nur teilweise im Skript",
                  "keine": "nicht im Skript"}
DISCLAIMER = ("> **Hinweis:** Alle Fragen stammen aus Studierenden-Quellen (Gedächtnisprotokolle bzw. "
              "Abschrift einer Klausur) und sind weder amtlich noch verifiziert. Wortlaut, Punkte und "
              "Vollständigkeit können abweichen. Themen-, Abschnitts- und Abbildungszuordnung sind "
              "eine fachliche Einschätzung.")


def german_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def short_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y[2:]}"


def _figure_link(fid: str) -> str:
    f = catalog.figure(fid)
    return f"[{catalog.figure_label(f)}: {f['title']}](../figures/originals/{fid}.png)"


def _question_block(q: dict, titles: dict[str, str]) -> str:
    pts = f"{q['points']}" if q["points"] is not None else "unbekannt"
    topics = "; ".join(f"{titles[t]} (`{t}`)" for t in q["topics"])
    lines = [f"### Frage {q['number']} · `{q['id']}`", "", f"> {q['wording']}", "",
             f"- **Punkte:** {pts}",
             f"- **Aufgabentyp:** {q['task_type']} · **Kompetenzen:** {', '.join(q['competencies'])}",
             f"- **Themen:** {topics}",
             f"- **Skript-Abschnitte:** {', '.join(q['sections']) or '–'}"]
    if q["figures"]:
        lines.append("- **Abbildungen:** " + "; ".join(_figure_link(f) for f in q["figures"]))
    lines.append(f"- **Skriptabdeckung:** {COVERAGE_LABEL[q['script_coverage']]}")
    if q["notes"]:
        lines.append(f"- **Anmerkung:** {q['notes']}")
    return "\n".join(lines)


def questions_md(questions: list[dict], exams: list[dict], topics: list[dict]) -> str:
    titles = {t["id"]: t["title"] for t in topics}
    out = ["# Prüfungsfragen", "", DISCLAIMER, "",
           f"{len(questions)} Fragen aus {len(exams)} Prüfungsterminen, neueste zuerst. "
           "Maschinenlesbar: `questions.json`; Quelle der Wahrheit: `curation/exams.yaml`.", ""]
    for e in sorted(exams, key=lambda e: e["date"], reverse=True):
        group = [q for q in questions if q["exam_date"] == e["date"]]
        pts = f", {e['total_points']} Punkte" if e.get("total_points") is not None else ""
        out += [f"## {german_date(e['date'])} – {SOURCE_LABEL[e['source']]}{pts}", "",
                f"*Vertrauensstufe: {TRUST_LABEL[e['trust']]}.* {(e.get('notes') or '').strip()}", ""]
        out += [_question_block(q, titles) + "\n" for q in group]
    return "\n".join(out).rstrip() + "\n"


def _topic_table(rows: list[dict]) -> list[str]:
    out = ["| Rang | Thema | Termine (T) | Fragen | Punkte | zuletzt | P | A | Score | gefragt am |",
           "|---:|---|---:|---:|---:|---|---:|---:|---:|---|"]
    for i, r in enumerate(rows, 1):
        last = german_date(r["last"]) if r["last"] else "–"
        pts = r["points"] or "–"
        dates = ", ".join(short_date(d) for d in reversed(r["dates"])) or "–"
        out.append(f"| {i} | {r['title']} | {r['n_dates']} | {r['n_questions']} | {pts} | {last} "
                   f"| {r['p_term']:.1f} | {r['a_term']} | **{r['score']:.1f}** | {dates} |")
    return out


def _method(n_exams: int, questions: list[dict]) -> list[str]:
    graded = sum(q["points"] for q in questions if q["points"] is not None)
    newest = exam_stats.RECENT_DATES
    return ["## Methode und Formel", "",
            "Der Prioritäts-Score ist eine **Heuristik zum Sortieren der Lernreihenfolge**, keine "
            "Wahrscheinlichkeit und keine Prognose: Er zählt nur, was in den vorliegenden "
            "Studierenden-Quellen vorkam.", "",
            f"`{exam_stats.formula()}`", "",
            f"- **T** – Anzahl der verschiedenen Prüfungstermine (von {n_exams}), an denen das Thema gefragt wurde. "
            "Mehrere Fragen desselben Termins zählen einmal.",
            f"- **Punkte / Gesamtpunkte** – Anteil der Punkte, die das Thema trägt, an allen Punkten mit bekannter "
            f"Bewertung ({graded} P). Nur die Klausur vom 29.04.2026 nennt Punkte; die elf Gedächtnisprotokolle "
            "liefern hier nichts. Eine Frage mit mehreren Themen zählt ihre vollen Punkte für jedes Thema.",
            f"- **P** – dieser Anteil mal {exam_stats.P_SCALE} (ein Thema, das alle bekannten Punkte trägt, bekäme "
            f"{exam_stats.P_SCALE}).",
            f"- **A** – Aktualitätsbonus: +1 für jeden der {newest} neuesten Prüfungstermine, an dem das Thema gefragt wurde "
            f"(0 bis {newest}).",
            f"- Gewichte: {exam_stats.W_DATES} je Prüfungstermin, damit die Breite über die Zeit am stärksten zählt. "
            "Die Gewichte sind eine Setzung des Autors, nicht aus Daten geschätzt.", ""]


def _gaps(questions: list[dict]) -> list[str]:
    partial = [q for q in questions if q["script_coverage"] != "voll"]
    out = ["## Aktualitätslücken", "",
           "Das Skript ist die Fassung 2024/25 (v2.0); die Prüfungen reichen bis 2026. Was dort gefragt wird, "
           "muss nicht vollständig im Skript stehen. Der Abgleich ist eine Einschätzung beim Kuratieren "
           "(`script_coverage` in `curation/exams.yaml`).", "",
           f"- Vollständig durch das Skript gedeckt: {len(questions) - len(partial)} von {len(questions)} Fragen.",
           f"- Nur teilweise oder nicht gedeckt: {len(partial)} Fragen (unten).", ""]
    for q in partial:
        out += [f"- `{q['id']}` ({german_date(q['exam_date'])}): „{q['wording']}“ – {COVERAGE_LABEL[q['script_coverage']]}. "
                f"{q['notes'] or ''}".rstrip()]
    out.append("")
    return out


def _count_table(title: str, head: str, rows: list[tuple[str, int, int]]) -> list[str]:
    out = [f"### {title}", "", f"| {head} | Fragen | davon mit Punkteangabe (Klausur 29.04.2026) |", "|---|---:|---:|"]
    out += [f"| {v} | {n} | {g} |" for v, n, g in rows]
    return out + [""]


def frequency_md(questions: list[dict], exams: list[dict], rows: list[dict]) -> str:
    asked = [r for r in rows if r["n_dates"]]
    never = [r for r in rows if not r["n_dates"]]
    out = ["# Häufigkeitsanalyse der Prüfungsfragen", "", DISCLAIMER, "",
           f"Datenbasis: {len(questions)} Fragen aus {len(exams)} Terminen "
           f"({german_date(exams[0]['date'])} bis {german_date(exams[-1]['date'])}), "
           f"{len(asked)} von {len(rows)} Themen wurden mindestens einmal gefragt.", ""]
    out += _method(len(exams), questions)
    out += ["## Themen nach Priorität", "", "Sortiert nach Score; bei Gleichstand alphabetisch.", ""]
    out += _topic_table(asked) + [""]
    out += ["## Themen ohne bekannte Prüfungsfrage", "",
            "Diese Themen kamen in den vorliegenden Quellen nicht vor. Das heißt nicht, dass sie nie gefragt werden: "
            "Die Quellen sind lückenhaft (Gedächtnisprotokolle, nur 12 Termine).", ""]
    out += [f"- {r['title']} (`{r['id']}`)" for r in never] + [""]
    out += _gaps(questions)
    out += ["## Aufgabentypen und Kompetenzen", "",
            "Aufgabentyp = erstes Operatorverb der Frage; Kompetenzen = alles, was die Frage verlangt "
            "(Mehrfachnennung möglich). Einstufung durch den Kurator; bei Stichwort-Fragen ohne Verb ist sie eine Annahme.", ""]
    out += _count_table("Aufgabentypen", "Aufgabentyp", exam_stats.task_type_counts(questions))
    out += _count_table("Kompetenzen", "Kompetenz", exam_stats.competency_counts(questions))
    out += ["## Grenzen der Auswertung", "",
            "- Elf der zwölf Termine sind Gedächtnisprotokolle: Fragen können fehlen, verkürzt oder verfälscht sein.",
            "- Punkte sind nur für eine Klausur bekannt; der Punkteanteil ist daher ein schwaches Signal.",
            "- Laut Abschrift der Klausur 2026 werden aktuell tendenziell eher Grafiken und Diagramme abgefragt "
            "(Aussage von Studierenden, nicht verifiziert) – Zeichnen üben lohnt sich.", ""]
    return "\n".join(out).rstrip() + "\n"
