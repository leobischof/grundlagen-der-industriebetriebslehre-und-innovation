"""Content-addressed JSON cache.

A cache entry is keyed by the SHA-256 of everything that determines its value
(input file hash, page number, stage version, parameters). Re-running a stage
with unchanged inputs therefore costs one dictionary lookup per page and never
re-does OCR, rendering or detection. `--force` bypasses lookups but still writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from . import config


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_for(*parts: Any) -> str:
    """Stable key from arbitrary JSON-serialisable parts."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class JsonCache:
    """One directory per stage, one small JSON file per key."""

    def __init__(self, stage: str, force: bool = False):
        self.stage = stage
        self.force = force
        self.dir = config.CACHE / stage
        self.hits = 0
        self.misses = 0

    def _path(self, key: str) -> Path:
        return self.dir / key[:2] / f"{key}.json"

    def has(self, key: str) -> bool:
        """True when `key` is cached (used by --dry-run to report pending work)."""
        return self._path(key).exists()

    def get_or_compute(self, key: str, compute: Callable[[], Any]) -> Any:
        path = self._path(key)
        if not self.force and path.exists():
            self.hits += 1
            return json.loads(path.read_text(encoding="utf-8"))
        self.misses += 1
        value = compute()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return value

    def summary(self) -> str:
        return f"[{self.stage}] cache hits={self.hits} computed={self.misses}"


def write_if_changed(path: Path, text: str) -> bool:
    """Write only when content differs, so mtimes and git diffs stay quiet."""
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def write_bytes_if_changed(path: Path, data: bytes) -> bool:
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def dump_json(path: Path, value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return write_if_changed(path, text)
