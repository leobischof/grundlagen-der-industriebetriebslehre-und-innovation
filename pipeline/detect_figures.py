"""Stage "detect-figures": deterministic figure detection, cross-checked against the curation.

curation/figures.yaml is the truth; detection is the safety net that keeps it
honest. Every detected region must be explained by a curated figure or a
listed duplicate, every curated figure should be found by detection (or carry
`bbox_source: manual`). Differences go to reports/figure-detection.md, which
`validate` turns into findings.
"""
from __future__ import annotations

import pymupdf

from . import catalog, config
from .cache import JsonCache, dump_json, key_for, sha256_file, write_if_changed
from .ingest import source_path
from .layout import analyse
from .pages import parse_pages

OUT_JSON = config.BUILD / "detected-figures.json"
REPORT = config.REPORTS / "figure-detection.md"
MIN_OVERLAP = 0.5      # share of the smaller box covered by the other one


def overlap(a, b) -> float:
    """Intersection area divided by the smaller box's area (1.0 = one contains the other)."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return w * h / small if small > 0 else 0.0


def compare(detected: dict[int, list[dict]]) -> dict:
    """Match detected regions with curated figures and duplicates, page by page."""
    curated = list(catalog.figures()) + [dict(d, id=f"dup:{d['duplicate_of']}") for d in catalog.duplicates()]
    skipped = catalog.skipped_pages()
    unexplained, found = [], set()
    for page, regions in sorted(detected.items()):
        if page in skipped:
            continue
        here = [c for c in curated if c["pdf_page"] == page]
        for r in regions:
            hits = [c["id"] for c in here if overlap(r["bbox"], c["bbox"]) >= MIN_OVERLAP]
            found.update(hits)
            if not hits:
                unexplained.append({"page": page, "bbox": [round(v) for v in r["bbox"]],
                                    "caption": (r.get("caption") or {}).get("text", "")})
    undetected = [c["id"] for c in catalog.figures()
                  if c["id"] not in found and c["pdf_page"] in detected]
    manual = {c["id"] for c in catalog.figures() if c.get("bbox_source") == "manual"}
    return {"unexplained_regions": unexplained,
            "undetected_curated": [i for i in undetected if i not in manual],
            "manual_only": sorted(manual)}


def _report(result: dict, pages_checked: int) -> str:
    lines = ["# Abgleich Bilderkennung ↔ kuratierte Abbildungsliste", "",
             "Generiert von `python -m pipeline detect-figures`. Quelle der Wahrheit ist "
             "`curation/figures.yaml`; die deterministische Erkennung (`pipeline/layout.py`) dient als Gegenprobe.", "",
             f"- Geprüfte Seiten: {pages_checked} (ohne Titel-/Leerseiten aus `structure.yaml`)",
             f"- Kuratierte Einträge: {len(catalog.figures())}, gelistete Duplikate: {len(catalog.duplicates())}",
             f"- Nur manuell gesetzt (von der Erkennung prinzipbedingt nicht gefunden): "
             f"{', '.join(result['manual_only']) or '–'}", ""]
    lines += ["## Erkannte Regionen ohne kuratierten Eintrag", ""]
    if not result["unexplained_regions"]:
        lines.append("Keine – jede erkannte Region ist einer Abbildung, Tabelle, Formel oder einem Duplikat zugeordnet.")
    for r in result["unexplained_regions"]:
        lines.append(f"- PDF S. {r['page']}, bbox {r['bbox']}, Beschriftung (OCR): „{r['caption'] or '–'}“")
    lines += ["", "## Kuratierte Einträge, die die Erkennung nicht findet", ""]
    if not result["undetected_curated"]:
        lines.append("Keine.")
    lines += [f"- `{i}`" for i in result["undetected_curated"]]
    return "\n".join(lines) + "\n"


def run(pages: str | None = None, dry_run: bool = False, force: bool = False) -> int:
    pdf_path = source_path(config.SKRIPT)
    pdf_hash = sha256_file(pdf_path)
    doc = pymupdf.open(pdf_path)
    selected = parse_pages(pages, doc.page_count)
    cache = JsonCache("detect-figures", force=force)
    version = (config.STAGE_VERSIONS["analyze"], config.STAGE_VERSIONS["detect-figures"])
    if dry_run:
        todo = [p for p in selected if force or not cache.has(key_for(pdf_hash, p, version))]
        print(f"[detect-figures] würde {len(todo)} Seiten analysieren")
        return 0
    detected = {}
    for pno in selected:
        lay = cache.get_or_compute(key_for(pdf_hash, pno, version), lambda p=pno: analyse(doc[p - 1]).to_json())
        detected[pno] = lay["regions"]
    dump_json(OUT_JSON, {str(k): v for k, v in detected.items()})
    result = compare(detected)
    if pages is None:                       # the report only makes sense for the whole document
        write_if_changed(REPORT, _report(result, len([p for p in detected if p not in catalog.skipped_pages()])))
    print(cache.summary(), f"| unerklärte Regionen={len(result['unexplained_regions'])}",
          f"nicht erkannt={result['undetected_curated']}")
    return 0
