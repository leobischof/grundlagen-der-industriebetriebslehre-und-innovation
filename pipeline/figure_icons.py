"""Search pinned free icon libraries and embed offline SVGs; retain semantic labels.

Only this explicit stage downloads. Offline/render/exercises never contact icon services.
Slots are source SVG groups with data-icon-query and data-icon-box="x y width height".
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

from . import config
from .cache import write_if_changed

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("",NS)
SAFE_TAGS = {"g","path","circle","ellipse","rect","line","polygon","polyline"}


def _download(url: str) -> bytes:
    request = urllib.request.Request(url,headers={"User-Agent":"GIL-Icon-Importer/1.0"})
    with urllib.request.urlopen(request,timeout=45) as response:
        return response.read()


def library(prefix: str, version: str, spdx: str, license_url: str) -> dict:
    cache = config.ICON_CACHE / f"{prefix}-{version}.json"
    if cache.is_file():
        return json.loads(cache.read_text(encoding="utf-8"))
    metadata = json.loads(_download(f"https://registry.npmjs.org/@iconify-json/{prefix}/{version}"))
    if metadata["license"] != spdx:
        raise ValueError(f"Unerwartete Lizenz für {prefix}: {metadata['license']}")
    dist = metadata["dist"]
    blob = _download(dist["tarball"])
    algorithm,expected = dist["integrity"].split("-",1)
    if algorithm != "sha512" or base64.b64encode(hashlib.sha512(blob).digest()).decode() != expected:
        raise ValueError(f"Integrität des Iconpakets {prefix} stimmt nicht")
    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as archive:
        icons = json.load(archive.extractfile("package/icons.json"))
        info = json.load(archive.extractfile("package/info.json"))
    if info["license"]["spdx"] != spdx:
        raise ValueError("Icon- und Paketlizenz widersprechen sich")
    value = dict(prefix=prefix,version=version,license=spdx,license_url=license_url,
                 license_text=_download(license_url).decode("utf-8"),icons=icons,
                 source=dist["tarball"],integrity=dist["integrity"])
    write_if_changed(cache,json.dumps(value,ensure_ascii=False))
    return value


def search(query: str, libraries: list[dict]) -> tuple[dict,str,dict] | None:
    """Search names with conservative exact/prefix matches; no fabricated geometry fallback."""
    query = query.lower().strip()
    tokens = set(query.split("-"))
    candidates = []
    for priority,lib in enumerate(libraries):
        for name,icon in lib["icons"]["icons"].items():
            parts = set(name.split("-"))
            score = 100 if query == name else 70 if name.startswith(query+"-") else 50 if tokens <= parts else 0
            if score:
                candidates.append((score,-priority,-len(name),name,lib,icon))
    if not candidates:
        return None
    _,_,_,name,lib,icon = max(candidates,key=lambda item:item[:4])
    return lib,name,icon


def safe_body(body: str) -> list[ET.Element]:
    root = ET.fromstring(f'<svg xmlns="{NS}">{body}</svg>')
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if node is not root and tag not in SAFE_TAGS:
            raise ValueError(f"Unzulässiges Element im Bibliotheksicon: {tag}")
        if any(key.lower().startswith("on") or "href" in key.lower() or "url(" in value.lower() for key,value in node.attrib.items()):
            raise ValueError("Externe Referenz oder aktiver Inhalt im Bibliotheksicon")
    return list(root)


def populate(slot: ET.Element, lib: dict, name: str, icon: dict) -> dict:
    box = [float(v) for v in slot.attrib["data-icon-box"].split()]
    x,y,w,h = box
    if w <= 0 or h <= 0:
        raise ValueError("Ungültiger Iconbereich")
    width = icon.get("width",lib["icons"].get("width",24))
    height = icon.get("height",lib["icons"].get("height",24))
    scale = min(w/width,h/height)
    color = slot.get("data-icon-color","#555555")
    body = icon["body"].replace("currentColor",color)
    group = ET.Element(f"{{{NS}}}g",{"data-library-icon":f"{lib['prefix']}:{name}",
        "transform":f"translate({x+(w-width*scale)/2:g} {y+(h-height*scale)/2:g}) scale({scale:g})"})
    meta = ET.SubElement(group,f"{{{NS}}}metadata")
    meta.text = f"{lib['prefix']}:{name}; {lib['version']}; {lib['license']}; {lib['source']}\n{lib['license_text']}"
    group.extend(safe_body(body))
    for previous in list(slot):
        if previous.get("data-library-icon"):
            slot.remove(previous)
    slot.insert(0,group)
    return dict(query=slot.get("data-icon-query"),icon=f"{lib['prefix']}:{name}",version=lib["version"],
                license=lib["license"],source=lib["source"],body_sha256=hashlib.sha256(icon["body"].encode()).hexdigest())


def run(pages=None,dry_run: bool = False,force: bool = False) -> int:
    files = []
    for path in sorted(config.FIG_RECONSTRUCTED.glob("*.svg")):
        root = ET.fromstring(path.read_bytes(),parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
        slots = [node for node in root.iter() if node.get("data-icon-query")]
        if slots:
            files.append((path,root,slots))
    if dry_run:
        print(f"[figure-icons] {sum(len(s) for _,_,s in files)} Suchfelder in {len(files)} SVGs; kein Download")
        return 0
    libraries = [library(*spec) for spec in config.ICON_LIBRARIES]
    records = []
    for path,root,slots in files:
        for slot in slots:
            match = search(slot.get("data-icon-query"),libraries)
            if match is None:
                print(f"[figure-icons] Kein Treffer: {path.name}: {slot.get('data-icon-query')}; Beschriftung bleibt")
                continue
            record = populate(slot,*match)
            records.append(dict(figure=path.stem,**record))
        ET.indent(root,space="  ")
        write_if_changed(path,ET.tostring(root,encoding="unicode")+"\n")
    licenses = "\n\n".join(f"{lib['prefix']} {lib['version']} · {lib['license']}\nQuelle: {lib['source']}\nLizenz: {lib['license_url']}\n\n{lib['license_text']}" for lib in libraries)
    write_if_changed(config.ICON_LICENSES,licenses+"\n")
    write_if_changed(config.ICON_PROVENANCE,json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    print(f"[figure-icons] {len(records)} freie Icons in {len(files)} SVGs; Beschriftungen erhalten")
    return 0
