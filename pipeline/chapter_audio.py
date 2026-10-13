"""Local chapter recordings: canonical names, no uploads, no Git storage."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import config, content_files


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def discover(root: Path | None = None) -> dict[int, Path]:
    root = root or config.AUDIO_DIR
    found = {}
    if not root.exists():
        return found
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in config.AUDIO_EXTENSIONS:
            continue
        match = re.match(r"^(?:GIL-|Kap)(\d+)(?:-|\.)", path.name, re.I)
        if not match:
            raise ValueError(f"Audio ohne Kapitelnummer: {path.name}")
        n = int(match[1])
        if n in found:
            raise ValueError(f"Mehrere Audios für Kapitel {n}: {found[n].name}, {path.name}")
        found[n] = path
    return found


def rename(root: Path | None = None, chapters=None) -> dict[int, Path]:
    root = root or config.AUDIO_DIR
    chapters = chapters if chapters is not None else content_files.discover(config.CONTENT)
    names = {content_files.chapter_number(c.slug): content_files.audio_export(c.slug, c.title).stem for c in chapters}
    planned = []
    for n, source in discover(root).items():
        if n not in names:
            raise ValueError(f"Audio für unbekanntes Kapitel {n}")
        target = root / f"{names[n]}{source.suffix.lower()}"
        if target != source and target.exists():
            raise FileExistsError(f"Ziel existiert bereits: {target}")
        planned.append((n, source, target))
    for n, source, target in planned:
        if source != target:
            source.rename(target)
            print(f"[audio] {source.name} -> {target.name}", flush=True)
    return {n: target for n, _, target in planned}


if __name__ == "__main__":
    rename()
