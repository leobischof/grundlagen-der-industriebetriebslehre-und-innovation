"""Stage "build-content": the cleaned text layer as markdown files under content/.

  content/skript-inhalt.md                            overview of all chapters
  content/<chapter_slug>/<chapter_slug>-ueberblick.md chapter intro text + table of contents
  content/<chapter_slug>/<X.Y>-<slug>.md              one file per X.Y section (deeper = headings)
  content/<chapter_slug>/<chapter_slug>-literatur.md  the chapter's reference list
(names from config: unique across the repository)

Input is segment.build() (OCR layer → ordered items assigned to TOC entries), the
curated catalog, and – when the exams stage already ran – exams/topic-mapping.json
for the `exam_questions` of each section. Purely deterministic, no AI: the files
are the *bereinigt* layer, their wording is the script's. Files are only written
when their text changed.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from . import catalog, config, segment
from .cache import write_if_changed
from .catalog import Entry
from .content_render import (footnote_section, frontmatter, heading_text, render_items,
                             section_filename)
from .footnotes import Footnote

SOURCE_ID = "skript-2024-25-v2.0"
STATUS = "maschinell-bereinigt-ungeprueft"
# "vgl. Kapitel 4.2", "siehe Abschnitt 5.3.1" – explicit cross references in the script text.
_CROSS_REF = re.compile(r"(?:Kapitel|Abschnitt|Kap\.)\s+(\d+\.\d+)")
# A reference list entry starts with "Autor … (2012)"; lines without a year continue it.
_REFERENCE_START = re.compile(r"^.{0,140}?\((?:\d{4,5}\s?[a-z]?|o\.\s?J\.|Hrsg\.)\)")


def _topic_mapping() -> dict:
    path = config.EXAMS / "topic-mapping.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _questions_for(section: str, mapping: dict) -> list[str]:
    by_section = mapping.get("by_section") or {}
    ids = [q for key, qs in by_section.items() if key == section or key.startswith(section + ".") for q in qs]
    return sorted(set(ids), key=_question_order)


def _question_order(qid: str) -> tuple:
    head, _, n = qid.rpartition("-")
    return (head, int(n) if n.isdigit() else 0)


def _related(section: str, text: str, mapping: dict, known: set[str]) -> list[str]:
    """Sections the script refers to explicitly, plus sections sharing an exam topic."""
    found = {m for m in _CROSS_REF.findall(text)}
    for topic in mapping.get("topics") or []:
        secs = {".".join(str(s).split(".")[:2]) for s in topic.get("sections") or []}
        if section in secs:
            found |= secs
    return [f"sec-{s}" for s in sorted(found - {section}, key=_number_key) if s in known]


def _number_key(number: str) -> tuple:
    return tuple(int(p) if p.isdigit() else 0 for p in number.split("."))


def _quality(pages: set[int], page_quality: dict[int, dict], unanchored: int) -> dict:
    words = sum(page_quality.get(p, {}).get("words", 0) for p in pages)
    bad = sum(page_quality.get(p, {}).get("suspicious", 0) for p in pages)
    return {"status": STATUS, "ocr_suspicious_ratio": round(bad / words, 3) if words else 0.0,
            "footnotes_unanchored": unanchored}


def _unanchored_by_owner(doc: segment.Document) -> dict[str, list[Footnote]]:
    """Notes without a text anchor go to the file holding the last text item of their page."""
    owner_of_page: dict[int, Entry] = {}
    for it in doc.items:
        if it.entry is not None:
            owner_of_page[it.page] = it.entry
    out: dict[str, list[Footnote]] = defaultdict(list)
    referenced = {int(n) for it in doc.items for n in re.findall(r"\[\^(\d+)\]", it.text)}
    referenced |= {n for it in doc.items for n in it.notes}
    for note in doc.notes.all():
        if note.number in referenced or note.page not in owner_of_page:
            continue
        out[_file_key(owner_of_page[note.page])].append(note)
    return out


def _file_key(entry: Entry) -> str:
    """Which output file an entry's items belong to: a section number, "kap-NN" or "lit-NN"."""
    if entry.kind == "chapter":
        return f"kap-{entry.chapter_id}"
    if entry.kind == "literature":
        return f"lit-{entry.chapter_id}"
    return entry.section_number


class Builder:
    """Collects all files in memory, then writes the changed ones."""

    def __init__(self, doc: segment.Document, page_quality: dict[int, dict]):
        self.doc = doc
        self.page_quality = page_quality
        self.mapping = _topic_mapping()
        self.by_number = {n.number: n for n in doc.notes.all()}
        self.unanchored = _unanchored_by_owner(doc)
        self.groups: dict[str, list[segment.Item]] = defaultdict(list)
        for it in doc.items:
            self.groups[_file_key(it.entry)].append(it)
        self.entries = {e.number: e for e in catalog.entries()}
        self.known = {e.number for e in catalog.entries() if e.level == 2 and e.kind in ("section", "frontmatter")}
        self.files: dict[str, str] = {}      # path relative to content/ -> text
        self.summary: dict[str, dict] = {}    # section number -> frontmatter (for the overviews)

    def section(self, entry: Entry, chapter: dict) -> None:
        items = self.groups.get(entry.number, [])
        if not items:
            return
        notes = self.unanchored.get(entry.number, [])
        body = render_items(items, heading_level=2)
        pages = body.pages | {n.page for n in notes}
        text_all = "\n".join(it.text for it in items)
        meta = {
            "id": f"sec-{entry.number}",
            "title": entry.title,
            "chapter": entry.chapter_id,
            "chapter_title": chapter["title"],
            "section": entry.number,
            "subsections": [e.number for e in catalog.entries()
                            if e.level > 2 and e.section_number == entry.number and e.chapter_id == entry.chapter_id],
            "pdf_pages": sorted(pages),
            "printed_pages": [p for p in (catalog.printed_page(x) for x in sorted(pages)) if p is not None],
            "figures": body.figures,
            "related_sections": _related(entry.number, text_all, self.mapping, self.known),
            "exam_questions": _questions_for(entry.number, self.mapping),
            "layer": "bereinigt",
            "source": SOURCE_ID,
            "quality": _quality(pages, self.page_quality, len(notes)),
        }
        lines = body.lines + footnote_section(body.refs, notes, self.by_number) + self._exam_footer(meta)
        rel = f"{chapter['slug']}/{section_filename(entry)}"
        self.files[rel] = frontmatter(meta) + "\n" + "\n".join(lines).rstrip() + "\n"
        self.summary[entry.number] = {**meta, "file": section_filename(entry)}

    def _exam_footer(self, meta: dict) -> list[str]:
        if not meta["exam_questions"]:
            return []
        ids = ", ".join(f"`{q}`" for q in meta["exam_questions"])
        n = len(meta["exam_questions"])
        return ["## Prüfungsfragen zu diesem Abschnitt", "",
                f"{n} {'Frage' if n == 1 else 'Fragen'} aus der [Prüfungsfragen-Datenbank]"
                f"(../../exams/questions.md): {ids}", ""]

    def chapter_readme(self, chapter: dict) -> None:
        cid = chapter["id"]
        intro = self.groups.get(f"kap-{cid}", [])
        body = render_items([it for it in intro if it.kind != "heading"], heading_level=2) if intro else None
        sections = _sections_of(cid)
        pages = sorted(body.pages) if body else []
        meta = {"id": f"kap-{cid}", "title": chapter["title"], "chapter": cid,
                "part": chapter.get("part"), "sections": [f"sec-{e.number}" for e in sections],
                "pdf_pages": pages, "layer": "bereinigt", "source": SOURCE_ID}
        title = f"Kapitel {int(cid)}: {chapter['title']}" if cid != "00" else chapter["title"]
        lines = [f"# {title}", ""]
        if body and body.lines:
            lines += ["## Einleitung des Kapitels (Skripttext)", ""] + body.lines
            lines += footnote_section(body.refs, self.unanchored.get(f"kap-{cid}", []), self.by_number)
        lines += ["## Inhalt", ""] + self._toc_lines(chapter, sections)
        self.files[f"{chapter['slug']}/{config.chapter_overview_name(chapter['slug'])}"] = frontmatter(meta) + "\n" + "\n".join(lines).rstrip() + "\n"

    def _toc_lines(self, chapter: dict, sections: list[Entry]) -> list[str]:
        out = []
        for e in sections:
            info = self.summary.get(e.number)
            if info is None:
                out.append(f"- {heading_text(e)} *(noch keine Datei)*")
                continue
            extra = []
            if info["figures"]:
                extra.append(f"{len(info['figures'])} Abb./Formeln")
            if info["exam_questions"]:
                extra.append(f"{len(info['exam_questions'])} Prüfungsfragen")
            suffix = f" – {', '.join(extra)}" if extra else ""
            out.append(f"- [{heading_text(e)}]({info['file']}) · {_pages_text(info['pdf_pages'])}{suffix}")
            out += [f"  - {heading_text(self.entries[s])}" for s in info["subsections"] if s in self.entries]
        if any(x.get("kind") == "literature" for x in chapter["entries"]):
            out.append(f"- [Literatur]({config.chapter_literature_name(chapter['slug'])})")
        return out + [""]

    def literature(self, chapter: dict) -> None:
        cid = chapter["id"]
        entry = next((e for e in chapter["entries"] if e.get("kind") == "literature"), None)
        items = [it for it in self.groups.get(f"lit-{cid}", []) if it.kind != "heading"]
        if entry is None:
            return
        pages = sorted({p for it in items for p in it.pages | {it.page}}) or [int(entry["pdf_page"])]
        meta = {"id": f"lit-{cid}", "title": entry["title"], "chapter": cid, "pdf_pages": pages,
                "printed_pages": [catalog.printed_page(p) for p in pages], "layer": "bereinigt",
                "source": SOURCE_ID, "quality": _quality(set(pages), self.page_quality, 0)}
        lines = [f"# {entry['title']}", "",
                 "Literaturverzeichnis des Skripts (OCR, bereinigt). Zeilenumbrüche des Scans wurden "
                 "zu einem Eintrag je Quelle zusammengeführt; Schreibweisen wie gedruckt. Internetadressen "
                 "fehlen: Die OCR hat sie im Scan nicht erfasst („online unter:“ ohne Adresse).", ""]
        lines += [f"- {ref}" for ref in join_references([it.text for it in items])]
        self.files[f"{chapter['slug']}/{config.chapter_literature_name(chapter['slug'])}"] = frontmatter(meta) + "\n" + "\n".join(lines).rstrip() + "\n"

    def overview(self) -> None:
        lines = ["---", "id: inhalt", "title: Inhalt der Wissensbasis", "layer: bereinigt",
                 f"source: {SOURCE_ID}", "---", "", "# Inhalt – Skript „Grundlagen der Industriebetriebslehre "
                 "und Innovation“ (2024/25, v2.0)", "",
                 "Bereinigte Textschicht des Skripts: je Abschnitt X.Y eine Datei, Abbildungen als Ausschnitt "
                 "aus dem Scan, Formeln in LaTeX, Fußnoten am Dateiende. Der Text ist maschinell aus dem Scan "
                 "gewonnen und nicht Korrektur gelesen (`quality.status` im Kopf jeder Datei).", ""]
        parts = {p["id"]: p["title"] for p in catalog.structure().get("parts", [])}
        current_part = None
        for ch in catalog.chapters():
            if ch.get("part") != current_part and ch.get("part"):
                current_part = ch["part"]
                lines += ["", f"## Teil {current_part[-1]}: {parts.get(current_part, '')}", ""]
            label = f"Kapitel {int(ch['id'])}: {ch['title']}" if ch["id"] != "00" else ch["title"]
            lines.append(f"- [{label}]({ch['slug']}/{config.chapter_overview_name(ch['slug'])})")
            for e in _sections_of(ch["id"]):
                info = self.summary.get(e.number)
                if info is not None:
                    lines.append(f"  - [{heading_text(e)}]({ch['slug']}/{info['file']})")
        self.files[config.CONTENT_INDEX_NAME] = "\n".join(lines).rstrip() + "\n"


def _pages_text(pages: list[int]) -> str:
    printed = [catalog.printed_page(p) for p in pages]
    if not pages:
        return ""
    if printed[0] is None:
        return f"PDF {pages[0]}–{pages[-1]}" if len(pages) > 1 else f"PDF {pages[0]}"
    return f"S. {printed[0]}–{printed[-1]}" if len(pages) > 1 else f"S. {printed[0]}"


def join_references(fragments: list[str]) -> list[str]:
    """Rejoin reference-list entries that the scan's line layout split into fragments."""
    refs: list[str] = []
    for frag in fragments:
        frag = frag.strip().strip("*").strip()
        if not frag:
            continue
        if refs and not _REFERENCE_START.match(frag):
            refs[-1] = f"{refs[-1]} {frag}"
        else:
            refs.append(frag)
    return refs


def _sections_of(chapter_id: str) -> list[Entry]:
    return [e for e in catalog.entries()
            if e.chapter_id == chapter_id and e.level == 2 and e.kind in ("section", "frontmatter")]


def build(builder: Builder) -> None:
    for ch in catalog.chapters():
        for e in _sections_of(ch["id"]):
            builder.section(e, ch)
        builder.literature(ch)
        builder.chapter_readme(ch)
    builder.overview()


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    """`pages` is ignored: sections span pages and footnote numbering is global, so the
    stage always rebuilds the whole tree in memory (≈ seconds) and writes only changes."""
    from .extract_text import load_pages      # local import: keeps CI-only stages free of pymupdf
    if pages:
        print("[build-content] Hinweis: --pages wird ignoriert, die Stufe baut immer alle Abschnitte")
    page_quality = {p: rec.get("quality", {}) for p, rec in load_pages().items()}
    doc = segment.build()
    builder = Builder(doc, page_quality)
    build(builder)
    print(f"[build-content] Fettdruck: {doc.bold_marked} Stellen markiert, "
          f"{len(doc.unmatched_bold)} nicht im Text gefunden")
    for page, phrase in doc.unmatched_bold:
        print(f"[build-content]   PDF-Seite {page}: {phrase}")
    changed = [rel for rel, text in sorted(builder.files.items())
               if force or not (config.CONTENT / rel).exists()
               or (config.CONTENT / rel).read_text(encoding="utf-8") != text]
    if dry_run:
        print(f"[build-content] würde {len(changed)} von {len(builder.files)} Dateien schreiben")
        return 0
    for rel in changed:
        write_if_changed(config.CONTENT / rel, builder.files[rel])
    stale = sorted(p.relative_to(config.CONTENT).as_posix() for p in config.CONTENT.rglob("*.md")
                   if p.relative_to(config.CONTENT).as_posix() not in builder.files)
    for rel in stale:
        print(f"[build-content] Hinweis: {rel} wird nicht mehr erzeugt (nicht gelöscht)")
    print(f"[build-content] {len(builder.files)} Dateien, {len(changed)} geändert")
    return 0
