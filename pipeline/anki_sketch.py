"""Sketch cards: one per exam-relevant figure of the script – pure data work, no genanki.

Exam-relevant means a figure (not a table or a formula box) that an exam question maps to
(exams/topic-mapping.json by_figure) or whose curated metadata rates it "hoch"/"mittel".
Front: the task to sketch it. Back: our own reconstruction (figures/reconstructed/<id>.svg)
or, where there is none yet, the stand-in text that names and describes the figure – never
the script's picture (figure_publish) – plus the curated "must know" points and the exam
questions that asked for it.

The same sketches also make the Markdown overview learning/flashcards/skizzieren.md; that file
stays in the private repository and may link the original crop for comparison.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import catalog, config, figure_publish
from .anki_cards import MEDIA_PREFIX, Card
from .content_render import page_label
from .exam_report import german_date

RELEVANT = ("hoch", "mittel")
OVERVIEW = config.LEARNING / "flashcards" / "skizzieren.md"
QUESTIONS_HEAD = "Gefragt in Prüfungen (Studierenden-Quellen, unverifiziert)"


@dataclass(frozen=True)
class Sketch:
    id: str
    chapter: str              # chapter slug
    title: str
    label: str                # "Abbildung 45"
    where: str                # "Abbildung 45 · Abschnitt 7.2 · Skript S. 151 (PDF 161)"
    svg: Path | None
    must_know: tuple[str, ...]
    questions: tuple[str, ...]

    @property
    def task(self) -> str:
        return f"Skizzieren Sie „{self.title}“ ({self.label})."

    def back(self, image_base: str) -> str:
        """Answer side as Markdown; `image_base` is where the SVG is found from the reader."""
        picture = (f"![{self.label}]({image_base}{self.svg.name})" if self.svg
                   else f"*{figure_publish.stand_in(self.id)}*")
        parts = [picture]
        if self.must_know:
            parts.append("**Das müssen Sie können:**\n\n" + "\n".join(f"- {m}" for m in self.must_know))
        if self.questions:
            parts.append(f"**{QUESTIONS_HEAD}:**\n\n" + "\n".join(f"- {q}" for q in self.questions))
        return "\n\n".join(parts)

    def card(self) -> Card:
        return Card("skizze", self.chapter, self.id, self.task, self.back(MEDIA_PREFIX), self.where,
                    (self.svg,) if self.svg else ())


def select(figures: list[dict], by_figure: dict) -> list[dict]:
    """Figures (no tables, no formulas) that an exam asked for or that are curated as relevant."""
    return [f for f in figures
            if f["kind"] == "figure" and (f["id"] in by_figure or f.get("exam_relevance") in RELEVANT)]


def sketches(figures: list[dict], by_figure: dict, questions: list[dict], slugs: dict[str, str]) -> list[Sketch]:
    """`slugs` maps a chapter number ("05") to its slug; figures of an unknown chapter are skipped."""
    out = []
    for fig in select(figures, by_figure):
        if fig["chapter"] not in slugs:
            continue
        asked = sorted((q for q in questions if fig["id"] in (q.get("figures") or [])), key=lambda q: q["date"])
        must_know = (catalog.figure_meta(fig["id"]).get("drawing") or {}).get("must_know") or []
        where = (f"{fig['label']} · Abschnitt {fig['subsection'] or fig['section']} · Skript "
                 + page_label(fig["pdf_page"]).replace("Seite", "S."))
        out.append(Sketch(fig["id"], slugs[fig["chapter"]], fig["title"], fig["label"], where,
                          figure_publish.reconstruction(fig["id"]), tuple(str(m) for m in must_know),
                          tuple(f"{german_date(q['date'])}: {q['prompt']}" for q in asked)))
    return out


def overview_md(items: list[Sketch]) -> str:
    drawn = sum(1 for s in items if s.svg)
    out = ["# Karteikarten: Abbildungen skizzieren", "",
           f"{len(items)} Karten, eine je prüfungsrelevanter Abbildung des Skripts (keine Tabellen, keine "
           "Formeln). Vorderseite: „Skizzieren Sie …“; Rückseite: unsere eigene Nachzeichnung der Abbildung "
           f"(bisher für {drawn} Abbildungen, sonst eine Beschreibung in Worten), die Merkpunkte aus der "
           "Zeichenübung und die Prüfungsfragen dazu. Die Bilder des Skripts selbst sind nie auf den Karten "
           "(Urheberrecht); hier im Repository ist das Original zum Vergleich verlinkt.", "",
           "Die Karten sind Teil der Anki-Karteikarten im Release (Unterdeck „4 Abbildungen skizzieren“ je "
           "Kapitel), erzeugt mit `python -m pipeline anki`. Die Prüfungsfragen stammen aus "
           "Studierenden-Quellen und sind nicht verifiziert.", ""]
    for s in items:
        out += [f"## {s.task}", "", f"*{s.where}*", "", "<details><summary>Lösung</summary>", "",
                s.back("../../figures/reconstructed/"), "",
                f"[Original im Skript](../../figures/originals/{s.id}.png)"]
        guide = config.DRAWING_GUIDES / config.drawing_guide_name(s.id)
        if guide.exists():
            out[-1] += f" · [Zeichenübung](../drawing-exercises/{guide.name})"
        out += ["", "</details>", ""]
    return "\n".join(out).rstrip() + "\n"
