"""Parse page selections such as "11-20,41,48" (1-based PDF page numbers)."""
from __future__ import annotations


def parse_pages(spec: str | None, last: int) -> list[int]:
    """Return the sorted, de-duplicated pages of `spec`, or all pages when `spec` is empty.

    Open ranges are allowed ("150-" = 150..last). Pages outside 1..last are an
    error rather than silently dropped: a typo should not process nothing.
    """
    if not spec:
        return list(range(1, last + 1))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lo, sep, hi = part.partition("-")
        start = int(lo) if lo else 1
        end = (int(hi) if hi else last) if sep else start
        if not (1 <= start <= end <= last):
            raise SystemExit(f"Seitenangabe '{part}' liegt außerhalb von 1–{last}.")
        pages.update(range(start, end + 1))
    return sorted(pages)
