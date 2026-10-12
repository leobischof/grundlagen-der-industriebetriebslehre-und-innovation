"""Checks: every PDF page and every TOC section is accounted for; sources; OCR quality.

"Accounted for" has two levels. The curated TOC (structure.yaml) must assign
every page to a heading or list it as skipped – otherwise a page would silently
fall out of the knowledge base. Once content/ exists, every assigned page must
also appear in some section file's `pdf_pages`, and every X.Y heading must have
its own file.
"""
from __future__ import annotations

from collections import Counter

from . import config
from .qa_findings import Finding, error, info, warning
from .qa_repo import RepoView
from .qa_schema import SECTION, problems

PAGES = "Seiten"
SECTIONS = "Kapitel und Abschnitte"
SOURCES = "Quellen"
OCR = "OCR-Qualität"
# A section whose cleaned text still has more than this share of implausible tokens
# is worth a human look. Pages are flagged by extract-text at 0.08 per page; a
# section average is smoother, so its bar is lower.
SECTION_OCR_WARN_RATIO = 0.05


def _ranges(view: RepoView) -> list[tuple[str, int, int]]:
    """(number, first, last) PDF page of every TOC entry; an entry ends where the next starts."""
    entries = view.entries
    out = []
    for i, e in enumerate(entries):
        last = e.end_page
        if last is None:
            nxt = entries[i + 1].pdf_page if i + 1 < len(entries) else e.pdf_page
            last = max(e.pdf_page, nxt)
        out.append((e.number, e.pdf_page, int(last)))
    return out


def toc_pages(view: RepoView) -> set[int]:
    return {p for _, first, last in _ranges(view) for p in range(first, last + 1)}


def content_pages(view: RepoView) -> set[int]:
    """Pages claimed by any content file – sections (sec-*), but also chapter overviews (kap-*)
    and reference lists (lit-*), which carry the chapter title and literature pages."""
    return {int(p) for f in view.content_files if f.meta for p in (f.meta.get("pdf_pages") or [])
            if isinstance(p, int)}


def check_pages(view: RepoView) -> list[Finding]:
    total = view.total_pages
    if not total:
        return [error(PAGES, "Seitenzahl des Skripts unbekannt (weder sources/manifest.yaml "
                             "noch sources/ocr/skript-pages.jsonl vorhanden)")]
    skipped = set(view.skipped_pages)
    assigned = toc_pages(view)
    out = []
    unassigned = sorted(set(range(1, total + 1)) - assigned - skipped)
    if unassigned:
        out.append(error(PAGES, f"PDF-Seiten weder einem Abschnitt zugeordnet noch als übersprungen "
                                f"gelistet (structure.yaml): {unassigned}"))
    both = sorted(assigned & skipped)
    if both:
        out.append(warning(PAGES, f"Seiten sind zugeordnet *und* als übersprungen gelistet: {both}"))
    beyond = sorted(p for p in assigned | skipped if p > total)
    if beyond:
        out.append(error(PAGES, f"structure.yaml nennt Seiten jenseits von Seite {total}: {beyond}"))
    if not view.section_files:
        out.append(info(PAGES, "content/ enthält noch keine Abschnittsdateien – Seitenabdeckung "
                               "der Inhalte nicht prüfbar"))
        return out
    missing = sorted(assigned - skipped - content_pages(view))
    if missing:
        out.append(error(PAGES, f"{len(missing)} zugeordnete PDF-Seiten kommen in keiner "
                                f"Abschnittsdatei (pdf_pages) vor: {missing}"))
    return out


def _expected_sections(view: RepoView) -> list:
    return [e for e in view.entries if e.kind in ("section", "frontmatter") and e.level == 2]


def check_sections(view: RepoView) -> list[Finding]:
    out: list[Finding] = []
    ids = [str(f.meta.get("id")) for f in view.content_files if f.meta and f.meta.get("id")]
    out += [error(SECTIONS, f"ID `{i}` mehrfach in content/ vergeben")
            for i, n in Counter(ids).items() if n > 1]
    for f in view.content_files:
        if f.meta_error:
            out.append(error(SECTIONS, f"`{f.rel}`: {f.meta_error}"))
    for f in view.section_files:
        out += [error(SECTIONS, f"`{f.rel}` Frontmatter: {p}") for p in problems(SECTION, f.meta)]
    if not view.section_files:
        return out + [error(SECTIONS, "content/ enthält keine Abschnittsdateien – Stufe "
                                      "`build-content` ist noch nicht gelaufen")]
    have = {str(f.meta["id"]) for f in view.section_files}
    for e in _expected_sections(view):
        if f"sec-{e.number}" in have:
            continue
        make = error if e.kind == "section" else warning
        out.append(make(SECTIONS, f"Abschnitt {e.number} „{e.title}“ (PDF S. {e.pdf_page}) hat "
                                  f"keine Datei mit `id: sec-{e.number}`"))
    toc = {f"sec-{e.number}" for e in view.entries}
    out += [error(SECTIONS, f"`{f.rel}`: `id: {f.meta['id']}` steht nicht im Inhaltsverzeichnis")
            for f in view.section_files if str(f.meta["id"]) not in toc]
    out += _chapter_files(view)
    out += _cross_references(view, toc)
    return out


def _chapter_files(view: RepoView) -> list[Finding]:
    out = []
    content = view.path(config.CONTENT)
    if not (content / config.CONTENT_INDEX_NAME).exists():
        out.append(error(SECTIONS, f"`content/{config.CONTENT_INDEX_NAME}` fehlt"))
    for ch in view.structure.get("chapters", []):
        folder = content / ch["slug"]
        if ch["id"] == "00":
            continue
        overview = config.chapter_overview_name(ch["slug"])
        if not (folder / overview).exists():
            out.append(error(SECTIONS, f"Kapitelüberblick fehlt: `content/{ch['slug']}/{overview}`"))
        has_lit = any(e.get("kind") == "literature" for e in ch.get("entries", []))
        literature = config.chapter_literature_name(ch["slug"])
        if has_lit and not (folder / literature).exists():
            out.append(error(SECTIONS, f"Literaturverzeichnis fehlt: `content/{ch['slug']}/{literature}`"))
    return out


def _cross_references(view: RepoView, toc: set[str]) -> list[Finding]:
    """related_sections must name existing sections; quality block must be plausible."""
    out = []
    for f in view.section_files:
        for ref in f.meta.get("related_sections") or []:
            if ref not in toc:
                out.append(warning(SECTIONS, f"`{f.rel}`: verwandter Abschnitt `{ref}` existiert nicht"))
    return out


def check_sources(view: RepoView) -> list[Finding]:
    sources = view.manifest.get("sources") or {}
    if not sources:
        return [error(SOURCES, "sources/manifest.yaml fehlt oder ist leer")]
    out = []
    for sid in config.SOURCES:
        entry = sources.get(sid)
        if not entry:
            out.append(error(SOURCES, f"Quelle `{sid}` fehlt im Manifest"))
            continue
        for key in ("file", "sha256", "bytes", "kind", "trust"):
            if not entry.get(key):
                out.append(error(SOURCES, f"Quelle `{sid}`: Feld `{key}` fehlt im Manifest"))
        local = view.root / str(entry.get("file", ""))
        if entry.get("file") and local.is_file() and local.stat().st_size != entry.get("bytes"):
            out.append(error(SOURCES, f"Quelle `{sid}`: lokale Datei weicht in der Größe vom Manifest ab "
                                      "(anderer Stand? `python -m pipeline ingest`)"))
    known = known_source_refs(view)
    for f in view.section_files:
        src = f.meta.get("source")
        if src and src not in known:
            out.append(error(SOURCES, f"`{f.rel}`: unbekannte Quelle `source: {src}`"))
    return out


def known_source_refs(view: RepoView) -> set[str]:
    """Valid values of a `source` field: a manifest id or its canonical file stem."""
    out = set()
    for sid, entry in (view.manifest.get("sources") or {}).items():
        out.add(sid)
        if entry.get("file"):
            out.add(str(entry["file"]).rsplit("/", 1)[-1].rsplit(".", 1)[0])
    return out


def check_ocr(view: RepoView) -> list[Finding]:
    out = []
    if not view.ocr_pages:
        out.append(info(OCR, "sources/ocr/skript-pages.jsonl fehlt – OCR-Qualität je Seite nicht prüfbar"))
    weak = [r["page"] for r in view.ocr_pages if (r.get("quality") or {}).get("low")]
    if weak:
        out.append(warning(OCR, f"{len(weak)} Seiten mit schwacher OCR-Textschicht: {weak}"))
    for f in view.section_files:
        ratio = (f.meta.get("quality") or {}).get("ocr_suspicious_ratio")
        if isinstance(ratio, (int, float)) and ratio > SECTION_OCR_WARN_RATIO:
            out.append(warning(OCR, f"`{f.rel}`: Anteil auffälliger Tokens {ratio:.3f} "
                                    f"> {SECTION_OCR_WARN_RATIO} – Text gegen das Original prüfen"))
    return out
