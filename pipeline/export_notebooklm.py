"""Stage "export-notebooklm": one self-contained Markdown file per chapter → build/notebooklm/.

  build/notebooklm/GIL-NotebookLM-Kontext-Kapitel-N-<Titel>.md   one file per chapter with a learning guide
  build/notebooklm/GIL-NotebookLM-Kontext.zip                    all of them in one folder
  build/notebooklm/release-assets.tsv                            zip and chapter files with labels (content_files)

Made for NotebookLM and other learning tools that take a document as their only context: one
chapter's file is all a tool needs to teach that chapter (e.g. one audio overview per chapter).
Each file has four parts, in this order:

  instructions  what the file is: one chapter, to be treated as fully as possible; the rest of
                the script is background; links to the chapter's sections in part 3
  part 1        the chapter's learning guide (learning/chapters/), its links into the script
                rewritten to anchors in part 3
  part 2        every exam question that touches the chapter (by section, plus those the
                guide names), with links to the sections in part 3
  part 3        the whole script as text, every content file behind an anchor ("sec-2-5"),
                the chapter itself framed as the learning subject

A text tool sees no picture, so every figure is words (figure_publish.in_words) - never the
script's PNG crop, not even our SVG. Links to files outside the document keep their label only.
The script is repeated in every file on purpose: each file must stand alone. Build output, not
committed (nine copies of the script would only bloat the repository).
"""
from __future__ import annotations

import datetime
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import catalog, config, content_files, figure_publish
from .cache import write_bytes_if_changed, write_if_changed
from .content_files import FOOTER, NOTEBOOKS, ChapterFiles
from .exam_report import COVERAGE_LABEL, SOURCE_LABEL, TRUST_LABEL, german_date
from .export_markdown import EXTERNAL, LINK
from .qa_markdown import split_frontmatter

OUT_DIR = config.BUILD / "notebooklm"
_HEADING = re.compile(r"^(#{1,6})(?=\s)", re.M)
_FIRST_H1 = re.compile(r"\A\s*# .*\n+")
_ZIP_TIME = (2024, 1, 1, 0, 0, 0)            # fixed: an unchanged export gives a byte-identical zip


def anchor(content_id: str) -> str:
    """Frontmatter id → HTML anchor ('sec-2.5' → 'sec-2-5'; dots break some Markdown viewers)."""
    return content_id.replace(".", "-")


@dataclass(frozen=True)
class Script:
    """The content layer once, with what every chapter file needs to link into it."""
    chapters: list[ChapterFiles]
    anchors: dict[Path, str]                 # resolved content file → its anchor
    sections: dict[str, str]                 # section number ('2.5') → anchor
    titles: dict[Path, str]                  # content file → heading text for the section list
    questions_md: Path                       # exams/questions.md: its question anchors live in part 2


def load_script(content_root: Path, guides_root: Path | None = None,
                questions_md: Path | None = None) -> Script:
    chapters = content_files.discover(content_root, guides_root)
    anchors, sections, titles = {}, {}, {}
    for chapter in chapters:
        for path in chapter.files:
            meta = split_frontmatter(path.read_text(encoding="utf-8"))[0] or {}
            key = anchor(str(meta.get("id") or path.stem))
            anchors[path.resolve()] = key
            if meta.get("section"):
                sections[str(meta["section"])] = key
                titles[path] = f"{meta['section']} {meta.get('title', '')}".strip()
            elif key.startswith("kap-"):
                titles[path] = f"Überblick: {meta.get('title') or chapter.title}"
            else:
                titles[path] = str(meta.get("title") or path.stem)
    return Script(chapters, anchors, sections, titles, (questions_md or config.EXAMS / "questions.md").resolve())


def section_anchor(script: Script, number: str) -> str | None:
    """'2.5.1' → anchor of the file that holds it (sections are files, subsections are not)."""
    parts = number.split(".")
    for n in range(len(parts), 0, -1):
        found = script.sections.get(".".join(parts[:n]))
        if found:
            return found
    return None


def rewrite_links(text: str, source: Path, script: Script, question_ids: set[str]) -> str:
    """Links of one file (guide or content) → anchors inside the NotebookLM document.

    A script file becomes its anchor, an exam question its anchor in part 2 (if it is there),
    a picture its description in words; anything else is outside the document and keeps
    only its label (a " · " link-list item goes entirely)."""
    def repl(m: re.Match) -> str:
        sep, bang, label, target = m.groups()
        if EXTERNAL.match(target):
            return m.group(0)
        fig_id = figure_publish.original_id(target)
        if fig_id and bang:
            return f"*{figure_publish.in_words(fig_id)}*"
        path, _, fragment = target.partition("#")
        resolved = (source.parent / path).resolve()
        if resolved in script.anchors:
            return f"{sep or ''}[{label}](#{script.anchors[resolved]})"
        if resolved == script.questions_md:
            target_anchor = fragment if fragment in question_ids else "teil-2"
            return f"{sep or ''}[{label}](#{target_anchor})"
        return "" if sep else label
    return LINK.sub(repl, text)


def shift_headings(text: str, by: int) -> str:
    """'# 2.5 …' → '### 2.5 …' for by=2; capped at h6. Code fences do not occur in the KB."""
    return _HEADING.sub(lambda m: "#" * min(len(m.group(1)) + by, 6), text) if by else text


def _body(path: Path) -> str:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1].strip()


# --- the four parts ------------------------------------------------------------

def instructions(chapter: ChapterFiles, script: Script, n_questions: int, today: str) -> str:
    n = content_files.chapter_number(chapter.slug)
    name = f"Kapitel {n} – {chapter.title}"
    sections = "\n".join(f"- [{script.titles[p]}](#{script.anchors[p.resolve()]})" for p in chapter.files)
    return f"""<a id="anleitung"></a>

# {content_files.notebook_export(chapter.slug, chapter.title).label}

> {FOOTER.format(today=today)}. Lernunterlage zur Lehrveranstaltung „Grundlagen der
> Industriebetriebslehre und Innovation“ (TU Graz), maschinell aus dem Skript 2024/25 erstellt;
> keine offizielle Unterlage. Maßgeblich ist das Original-Skript.

## Anleitung für NotebookLM und andere Lernwerkzeuge

Diese Datei ist der **vollständige und einzige Kontext**, um **{name}** zu lernen. Sie hat drei Teile:

1. [Teil 1 – Lernleitfaden {name}](#teil-1): Überblick, Lernziele, Kernbegriffe, Zusammenhänge,
   Abbildungen, Prüfungsfokus, typische Fehler, Selbsttest. Eine KI-Erklärung, nicht geprüft.
2. [Teil 2 – Prüfungsfragen zu Kapitel {n}](#teil-2): alle {n_questions} bekannten Prüfungsfragen, die
   dieses Kapitel betreffen. Aus Studierenden-Quellen, nicht verifiziert.
3. [Teil 3 – Gesamtskript](#teil-3): der Skripttext **aller** Kapitel als Rahmenwissen. Kapitel {n}
   steht dort zwischen den Markierungen „Beginn des Lernthemas“ und „Ende des Lernthemas“.

So ist diese Datei zu verwenden:

- **Das Thema ist ausschließlich Kapitel {n}.** Jede Zusammenfassung, jede Audio-Zusammenfassung
  (Hörspiel, Podcast), jedes Quiz, jede Karteikarte und jede Mindmap behandelt nur {name} – und
  zwar **so ausführlich und vollständig wie möglich**: jeden Abschnitt, jeden Fachbegriff, jede
  Aufzählung, jede Abbildung und jede Prüfungsfrage aus Teil 2. Lieber zu ausführlich als zu knapp;
  nichts weglassen, weil es selbstverständlich scheint.
- **Die anderen Kapitel sind nur Rahmenwissen.** Sie stehen in Teil 3, damit Querverweise und
  Zusammenhänge erklärt werden können („das wird in Kapitel 5 vertieft“). Selbst ausführlich
  behandelt werden sie nicht.
- **Maßgeblich ist der Skripttext** von Kapitel {n} in Teil 3. Der Lernleitfaden kann Fehler
  enthalten; bei einem Widerspruch gilt das Skript. Was nicht im Skript steht, als Ergänzung
  kennzeichnen.
- **Prüfungsnah lernen:** Jede Frage aus Teil 2 soll sich mit diesem Material beantworten lassen,
  mit Fundstelle (Abschnittsnummer). Abbildungen werden in der Prüfung abgefragt und müssen
  gezeichnet und erklärt werden können.
- **Abbildungen** sind nicht als Bild enthalten (Urheberrecht). Wo es eine Beschreibung gibt, steht
  sie in Worten an der Stelle der Abbildung; beim Erklären die Abbildung in Worten aufbauen
  (Kästen, Achsen, Pfeile, Beschriftungen).
- **Abschnittsnummern** wie „2.5“ verweisen auf den gleichnamigen Abschnitt in Teil 3.
- **Sprache:** Deutsch, Fachbegriffe wie im Skript.

### Kapitel {n} im Gesamtskript

{sections}
"""


def guide_part(chapter: ChapterFiles, script: Script, question_ids: set[str]) -> str:
    """The guide without its own h1 (the part heading replaces it)."""
    body = _FIRST_H1.sub("", _body(chapter.guide), count=1)
    title = split_frontmatter(chapter.guide.read_text(encoding="utf-8"))[0].get("title") or chapter.title
    return (f'<a id="teil-1"></a>\n\n# Teil 1 – {title}\n\n'
            + rewrite_links(body, chapter.guide, script, question_ids))


def chapter_questions(chapter: ChapterFiles, questions: list[dict]) -> list[dict]:
    """Questions on any section of the chapter plus those its guide names; by the first section
    of the chapter they touch, newest first within a section; guide-only questions last."""
    n = str(content_files.chapter_number(chapter.slug))
    named = set(split_frontmatter(chapter.guide.read_text(encoding="utf-8"))[0].get("exam_questions") or [])
    picked = [q for q in questions if q["id"] in named or any(s.split(".")[0] == n for s in q["sections"])]

    def order(q: dict) -> tuple:
        mine = [s for s in q["sections"] if s.split(".")[0] == n] or ["999"]
        newest_first = tuple(-int(x) for x in q["date"].split("-"))
        return tuple(int(x) for x in mine[0].split(".")), newest_first, q["id"]
    return sorted(picked, key=order)


def _question(q: dict, topics: dict[str, str], script: Script) -> str:
    def section_link(s: str) -> str:
        target = section_anchor(script, s)
        return f"[{s}](#{target})" if target else s
    pts = f" ({q['points']} Punkte)" if q["points"] is not None else ""
    lines = [f'<a id="{q["id"]}"></a>', "",
             f"### {q['prompt']}{pts}", "",
             f"- Prüfung vom {german_date(q['exam_date'])} – Quelle: {SOURCE_LABEL[q['source']]}; "
             f"{TRUST_LABEL[q['trust']]}",
             f"- Originalwortlaut: „{q['wording']}“",
             "- Thema: " + ", ".join(topics.get(t, t) for t in q["topics"])]
    if q["sections"]:
        lines.append("- Im Skript: " + ", ".join(section_link(s) for s in q["sections"]))
    if q["figures"]:
        lines.append("- Abbildungen: " + ", ".join(_figure_name(f) for f in q["figures"]))
    lines.append("- Verlangt: " + ", ".join(q["competencies"]))
    if q["script_coverage"] != "voll":
        lines.append(f"- Achtung: {COVERAGE_LABEL[q['script_coverage']]}")
    if q["notes"]:
        lines.append(f"- Anmerkung: {q['notes']}")
    return "\n".join(lines)


def _figure_name(fig_id: str) -> str:
    """'Abbildung 45 (Skript S. 140): Typologie …' - where to find it, never the picture."""
    f = catalog.figure(fig_id)
    printed = catalog.printed_page(f["pdf_page"])
    where = f" (Skript S. {printed})" if printed else ""
    return f"{catalog.figure_label(f)}{where}: {f['title']}"


def questions_part(chapter: ChapterFiles, picked: list[dict], exam_mode: dict | None,
                   topics: dict[str, str], script: Script) -> str:
    n = content_files.chapter_number(chapter.slug)
    out = ['<a id="teil-2"></a>', "", f"# Teil 2 – Prüfungsfragen zu Kapitel {n}", "",
           f"> {len(picked)} Fragen, nach Abschnitt geordnet, je Abschnitt die neueste zuerst. Alle stammen aus "
           "Studierenden-Quellen (Gedächtnisprotokolle, Abschrift einer Klausur) und sind nicht verifiziert; "
           "Wortlaut und Punkte können abweichen. Die Zuordnung zu Abschnitten ist eine fachliche Einschätzung.",
           ""]
    if exam_mode:
        out += [f"## Prüfungsmodus (laut Wiki der Studierenden, Stand {german_date(exam_mode['as_of'])})", "",
                *(f"- {p}" for p in exam_mode["points"]), ""]
    out += ["## Die Fragen", ""]
    out += [_question(q, topics, script) + "\n" for q in picked]
    return "\n".join(out).rstrip() + "\n"


def script_part(focus: ChapterFiles, script: Script, question_ids: set[str]) -> str:
    """Every chapter, every file behind its anchor; the focus chapter is framed."""
    n = content_files.chapter_number(focus.slug)
    out = ['<a id="teil-3"></a>', "", "# Teil 3 – Gesamtskript (Rahmenwissen; Lernthema ist Kapitel "
           f"{n})", "",
           "> Bereinigte Textschicht des Skripts 2024/25 (v2.0), alle Kapitel. Abbildungen sind in Worten "
           "beschrieben, soweit eine Beschreibung vorliegt."]
    for chapter in script.chapters:
        is_focus = chapter.slug == focus.slug
        if is_focus:
            out.append(f"> **Beginn des Lernthemas: Kapitel {n} – {chapter.title}.** Alles bis zur Markierung "
                       "„Ende des Lernthemas“ ist ausführlich zu behandeln.")
        for i, path in enumerate(chapter.files):
            body = rewrite_links(_body(path), path, script, question_ids)
            out.append(f'<a id="{script.anchors[path.resolve()]}"></a>\n\n' + shift_headings(body, 1 if i == 0 else 2))
        if is_focus:
            out.append(f"> **Ende des Lernthemas Kapitel {n}.** Ab hier wieder Rahmenwissen.")
    return "\n\n".join(out) + "\n"


# --- assembly --------------------------------------------------------------------

def _exam_data(exams_file: Path, mapping_file: Path) -> tuple[list[dict], dict | None, dict[str, str]]:
    data = json.loads(exams_file.read_text(encoding="utf-8")) if exams_file.exists() else {}
    mapping = json.loads(mapping_file.read_text(encoding="utf-8")) if mapping_file.exists() else {}
    topics = {t["id"]: t["title"] for t in mapping.get("topics", [])}
    return data.get("questions", []), data.get("exam_mode"), topics


def build(today: str, content_root: Path | None = None, guides_root: Path | None = None,
          exams_file: Path | None = None, mapping_file: Path | None = None) -> dict[str, str]:
    """File name → Markdown, one per chapter that has a learning guide."""
    exams_file = exams_file or config.EXAMS / "questions.json"
    script = load_script(content_root or config.CONTENT, guides_root, exams_file.with_suffix(".md"))
    questions, exam_mode, topics = _exam_data(exams_file, mapping_file or config.EXAMS / "topic-mapping.json")
    files = {}
    for chapter in (c for c in script.chapters if c.guide):
        picked = chapter_questions(chapter, questions)
        ids = {q["id"] for q in picked}
        parts = [instructions(chapter, script, len(picked), today), guide_part(chapter, script, ids),
                 questions_part(chapter, picked, exam_mode, topics, script), script_part(chapter, script, ids)]
        name = content_files.notebook_export(chapter.slug, chapter.title)
        files[f"{name.stem}.md"] = "\n\n".join(p.strip() for p in parts) + "\n"
    return files


def zip_bytes(files: dict[str, str]) -> bytes:
    """All files in one folder of the zip; fixed timestamps so equal input gives equal bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(f"{NOTEBOOKS.stem}/{name}", date_time=_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, files[name].encode("utf-8"))
    return buf.getvalue()


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    files = build(datetime.date.today().strftime("%d.%m.%Y"))
    zip_name = f"{NOTEBOOKS.stem}.zip"
    if dry_run:
        print(f"[export-notebooklm] würde {len(files)} Kapiteldateien und {zip_name} nach "
              f"{OUT_DIR.relative_to(config.ROOT)} schreiben")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    keep = set(files) | {zip_name, content_files.ASSET_LIST}
    for stale in [p for p in OUT_DIR.iterdir() if p.is_file() and p.name not in keep]:
        stale.unlink()                       # renamed chapter: the old file must not be released
    changed = sum(write_if_changed(OUT_DIR / name, text) for name, text in files.items())
    write_bytes_if_changed(OUT_DIR / zip_name, zip_bytes(files))
    # The zip is the folder of every chapter's file; each file is released on its own as well,
    # so a single chapter can be added to NotebookLM without unpacking anything.
    names = (content_files.notebook_export(c.slug, c.title) for c in content_files.discover(config.CONTENT))
    labels = {f"{n.stem}.md": n.label for n in names}
    content_files.write_asset_list(OUT_DIR, [(zip_name, f"{NOTEBOOKS.label} – alle Kapitel (Ordner)"),
                                             *((name, labels.get(name, Path(name).stem)) for name in sorted(files))])
    size = max((len(t.encode("utf-8")) for t in files.values()), default=0)
    print(f"[export-notebooklm] {len(files)} Kapiteldateien ({changed} geändert, größte {size // 1024} KB) "
          f"+ {zip_name}")
    return 0
