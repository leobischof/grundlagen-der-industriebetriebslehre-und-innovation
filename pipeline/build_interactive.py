"""Build a local, offline PDF.js chapter reader; media remain outside Git."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import chapter_audio, config, content_files
from .cache import write_if_changed


def validate_timeline(value: dict, chapter: int, audio_hash: str | None, pdf_hash: str) -> None:
    if value.get("version") != 1 or value.get("chapter") != chapter or not isinstance(value.get("annotations"), list):
        raise ValueError(f"Ungültige Timeline für Kapitel {chapter}")
    if value.get("pdf_sha256") != pdf_hash or value.get("audio_sha256") != audio_hash:
        raise ValueError(f"Timeline Kapitel {chapter}: PDF/Audio wurde verändert; Zuordnung neu vorbereiten oder prüfen")
    import math
    ids = set()
    for a in value["annotations"]:
        if not isinstance(a.get("id"),str) or not a["id"] or a["id"] in ids:
            raise ValueError("Annotation ohne eindeutige ID")
        ids.add(a["id"])
        if not all(isinstance(a.get(k),(int,float)) and not isinstance(a[k],bool) and math.isfinite(a[k]) for k in ("start","end")) or not 0 <= a["start"] < a["end"]:
            raise ValueError("Ungültige Annotationszeit")
        if not isinstance(a.get("page"),int) or isinstance(a["page"],bool) or a["page"] < 1:
            raise ValueError("Ungültige PDF-Seite")
        if a.get("type") not in {"rect","highlight","arrow"} or a.get("status") not in {"unreviewed","reviewed"}:
            raise ValueError("Unbekannter Annotationstyp oder Prüfstatus")
        values = a.get("points" if a["type"] == "arrow" else "rect")
        if not isinstance(values,list) or len(values) != 4 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0 <= v <= 1 for v in values):
            raise ValueError("Ungültige normalisierte Koordinaten")
        if a["type"] != "arrow" and (values[2] <= 0 or values[3] <= 0 or values[0]+values[2] > 1.00001 or values[1]+values[3] > 1.00001):
            raise ValueError("Rechteck liegt außerhalb der PDF-Seite")


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or chapter_audio.digest(source) != chapter_audio.digest(target):
        shutil.copy2(source,target)


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    vendor = config.INTERACTIVE_SOURCE / "node_modules" / "pdfjs-dist"
    if not (vendor / "build" / "pdf.mjs").is_file():
        print("[interactive] PDF.js fehlt: in interactive/ zuerst npm ci --ignore-scripts ausführen")
        return 1
    recordings = chapter_audio.discover()
    chapters = content_files.discover(config.CONTENT)
    planned = []
    for c in chapters:
        n = content_files.chapter_number(c.slug)
        if n == 0:
            continue
        pdf = config.BUILD / "pdf" / f"{c.export.stem}.pdf"
        if not pdf.is_file():
            print(f"[interactive] {pdf.name} fehlt; zuerst python -m pipeline render-pdf")
            return 1
        audio = recordings.get(n)
        canonical = f"{content_files.audio_export(c.slug,c.title).stem}{audio.suffix.lower()}" if audio else None
        if audio and audio.name != canonical:
            print("[interactive] Audionamen nicht kanonisch; zuerst python -m pipeline.chapter_audio")
            return 1
        pdf_hash, audio_hash = chapter_audio.digest(pdf), chapter_audio.digest(audio) if audio else None
        timeline_name = f"GIL-{n}-Timeline.json"
        timeline_source = config.INTERACTIVE_CURATION / timeline_name
        timeline = json.loads(timeline_source.read_text(encoding="utf-8")) if timeline_source.exists() else dict(
            version=1,chapter=n,pdf_sha256=pdf_hash,audio_sha256=audio_hash,annotations=[])
        try:
            validate_timeline(timeline,n,audio_hash,pdf_hash)
        except ValueError as error:
            print(f"[interactive] {error}")
            return 1
        folder = f"GIL-{n}-Kapitel"
        record = dict(number=n,title=c.title,pdf=f"{folder}/{pdf.name}",audio=f"audio/{audio.name}" if audio else None,
                      media_type="video" if audio and audio.suffix.lower() in {".mp4",".webm"} else "audio",
                      pdf_sha256=pdf_hash,audio_sha256=audio_hash,timeline=f"{folder}/{timeline_name}")
        planned.append((record,pdf,audio,timeline))
    if dry_run:
        print(f"[interactive] würde {len(planned)} Kapitel mit {len(recordings)} Audios bauen")
        return 0
    out = config.INTERACTIVE_BUILD
    out.mkdir(parents=True,exist_ok=True)
    for name in ("reader.html","reader.css","reader-app.mjs","reader-timeline.mjs"):
        _copy(config.INTERACTIVE_SOURCE / name,out / name)
    _copy(config.ROOT / "pipeline" / "reader_serve.py",out / "reader_serve.py")
    # Only redistributable viewer assets, never original-script PDFs or crops.
    for name in ("pdf.mjs","pdf.worker.mjs"):
        _copy(vendor / "build" / name,out / "vendor" / "build" / name)
    for directory in ("web","cmaps","standard_fonts","wasm"):
        shutil.copytree(vendor / directory,out / "vendor" / directory,dirs_exist_ok=True)
    _copy(vendor / "LICENSE",out / "vendor" / "PDFJS-LICENSE")
    if config.ICON_LICENSES.is_file():
        _copy(config.ICON_LICENSES,out / config.ICON_LICENSES.name)
    for record,pdf,audio,timeline in planned:
        _copy(pdf,out / record["pdf"])
        if audio:
            _copy(audio,out / record["audio"])
        write_if_changed(out / record["timeline"],json.dumps(timeline,ensure_ascii=False,indent=2)+"\n")
    write_if_changed(out / "reader-manifest.json",json.dumps(dict(version=1,chapters=[r for r,_,_,_ in planned]),ensure_ascii=False,indent=2)+"\n")
    write_if_changed(out / "Reader-starten.cmd","@echo off\ncd /d \"%~dp0\"\npy -3 reader_serve.py --open\nif errorlevel 1 pause\n")
    write_if_changed(out / "Reader-Anleitung.txt","GIL – Interaktiver Kapitelreader\n\nStart: Reader-starten.cmd (Windows mit Python) oder python reader_serve.py --open\nAdresse: http://127.0.0.1:8765/reader.html\n\nPDF und Audio bleiben getrennt. Rechtecke/Pfeile sind nur eine Darstellungsebene.\nAutomatische Vorschläge sind ungeprüft. Im Reader korrigieren und die Timeline herunterladen.\nZum Übernehmen die passende Datei in curation/interactive/ ersetzen und neu bauen.\nKeine Original-PDFs enthalten; Kapitel-PDFs sind bereinigte Skriptexporte mit eigenen SVGs.\n")
    allowed = ["reader.html","reader.css","reader-app.mjs","reader-timeline.mjs","reader_serve.py",
               "reader-manifest.json","Reader-starten.cmd","Reader-Anleitung.txt","vendor/PDFJS-LICENSE",
               "vendor/build/pdf.mjs","vendor/build/pdf.worker.mjs"]
    if config.ICON_LICENSES.is_file():
        allowed.append(config.ICON_LICENSES.name)
    for directory in ("web","cmaps","standard_fonts","wasm"):
        allowed.extend(f"vendor/{directory}/{p.relative_to(vendor / directory).as_posix()}"
                       for p in (vendor / directory).rglob("*") if p.is_file())
    for record,_,_,_ in planned:
        allowed.extend([record["pdf"],record["timeline"]])
        if record["audio"]:
            allowed.append(record["audio"])
    write_if_changed(out / "reader-assets.txt","\n".join(sorted(allowed))+"\n")
    print(f"[interactive] {len(planned)} Kapitel, {len(recordings)} Audios -> {out}")
    return 0
