"""Self-contained HTML per chapter: inline code/CSS, PDF, audio, timeline and PDF.js worker.

Desktop/Android browsers can run the HTML locally. iOS users should use the HTTPS PWA package;
Files/Quick Look is not a full browser and may not execute a downloaded HTML application.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path

from . import config, content_files
from .cache import key_for, sha256_file, write_if_changed


def encoded(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def inline_css(text: str, directory: Path) -> str:
    def replace(match):
        target = match[2].strip()
        if target.startswith(("data:","#")):
            return match[0]
        path = (directory / target).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            raise ValueError(f"CSS-Ressource kann nicht eingebettet werden: {target}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return f'url("data:{mime};base64,{encoded(path)}")'
    return re.sub(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)",replace,text)


def render_html(template: str,css: str,boot: str,payload: dict,licenses: dict) -> str:
    template = re.sub(r'\s*<link[^>]+rel="(?:stylesheet|manifest|apple-touch-icon)"[^>]*>',"",template)
    template = template.replace("</head>",f"<style>{css}</style>\n</head>")
    template = template.replace('href="reader.html"','href="#"')
    data = json.dumps(payload,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
    rights = json.dumps(licenses,ensure_ascii=False).replace("<","\\u003c")
    return template.replace('<script type="module" src="reader-app.mjs"></script>',
        f'<script type="application/json" id="gil-licenses">{rights}</script>\n'
        f'<script type="application/json" id="gil-payload">{data}</script>\n'
        f'<script type="module">{boot}</script>')


def run(pages=None,dry_run: bool = False,force: bool = False) -> int:
    root,out = config.INTERACTIVE_BUILD,config.STANDALONE_BUILD
    if not (root / "reader-manifest.json").is_file():
        print("[package-reader] Reader fehlt; zuerst python -m pipeline audio-reader")
        return 1
    manifest = json.loads((root / "reader-manifest.json").read_text(encoding="utf-8"))
    chapters = {content_files.chapter_number(c.slug):c for c in content_files.discover(config.CONTENT)}
    if dry_run:
        print(f"[package-reader] würde {len(manifest['chapters'])} vollständige HTML-Kapiteldateien erzeugen")
        return 0
    out.mkdir(parents=True,exist_ok=True)
    boot = (config.INTERACTIVE_SOURCE / "reader-singlefile-boot.mjs").read_text(encoding="utf-8")
    sources = dict(core=root/"vendor/build/pdf.mjs",viewer=root/"vendor/web/pdf_viewer.mjs",
                   worker=root/"vendor/build/pdf.worker.mjs",app=root/"reader-app.mjs",timeline=root/"reader-timeline.mjs",
                   navigation=root/"reader-navigation.mjs",offline=root/"reader-offline.mjs")
    common_files = [*sources.values(),root/"reader.css",root/"reader.html",root/"vendor/web/pdf_viewer.css",
                    config.INTERACTIVE_SOURCE/"reader-singlefile-boot.mjs",root/"reader-offline-index.json"]
    modules = {name:encoded(path) for name,path in sources.items()}
    binary = {kind:{p.name:encoded(p) for p in (root/"vendor"/directory).iterdir() if p.is_file()}
              for kind,directory in [("cMapUrl","cmaps"),("standardFontDataUrl","standard_fonts"),("wasmUrl","wasm")]}
    css = inline_css((root/"vendor/web/pdf_viewer.css").read_text(encoding="utf-8"),root/"vendor/web")+"\n"+(root/"reader.css").read_text(encoding="utf-8")
    template = (root/"reader.html").read_text(encoding="utf-8")
    licenses = {p.name:p.read_text(encoding="utf-8") for p in [root/"vendor/PDFJS-LICENSE",config.ICON_LICENSES] if p.exists()}
    stamp_path = out/".singlefile-stamps.json"
    stamps = json.loads(stamp_path.read_text(encoding="utf-8")) if stamp_path.exists() else {}
    assets = []
    for record in manifest["chapters"]:
        chapter = chapters[record["number"]]
        name = content_files.standalone_export(chapter.slug,chapter.title)
        target = out/f"{name.stem}.html"
        files = [*common_files,root/record["pdf"],root/record["timeline"]]
        if record["audio"]: files.append(root/record["audio"])
        key = key_for([(str(p),sha256_file(p)) for p in files],record,licenses)
        assets.append((target.name,name.label))
        if not force and target.exists() and stamps.get(target.name) == key:
            continue
        payload = dict(manifest=dict(version=1,chapters=[record]),timeline=json.loads((root/record["timeline"]).read_text(encoding="utf-8")),
                       modules=modules,binary=binary,pdf=encoded(root/record["pdf"]),
                       audio=encoded(root/record["audio"]) if record["audio"] else None,
                       audio_mime=mimetypes.guess_type(record["audio"] or "")[0] or "audio/mp4")
        target.write_text(render_html(template,css,boot,payload,licenses),encoding="utf-8",newline="\n")
        stamps[target.name] = key
        print(f"[package-reader] {target.name}: {target.stat().st_size//1024//1024} MB",flush=True)
    content_files.write_asset_list(out,assets)
    write_if_changed(stamp_path,json.dumps(stamps,sort_keys=True,indent=2)+"\n")
    print(f"[package-reader] {len(assets)} Kapiteldateien; PDF, Audio, Timeline und Reader vollständig eingebettet")
    return 0
