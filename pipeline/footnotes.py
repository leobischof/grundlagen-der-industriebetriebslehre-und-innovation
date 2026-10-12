"""Footnotes of the script: parse them, number them, anchor them in the body text.

The script numbers footnotes continuously through the whole document (1 … N).
The OCR layer garbles both ends: the leading number of a footnote line ("ss Vgl.",
"#6 Vgl.", "161Vg].") and the superscript marker in the body text ("Preisen.?7",
"Unternehmensstrategien®9"). Two deterministic rules make this tractable:

1. Numbering by sequence. Footnotes are counted in reading order; a *readable*
   leading number re-synchronises the counter. Every disagreement between the
   counter and a readable number is reported, so a skipped footnote cannot hide.
2. Anchoring by count. On each page, superscript-like candidates in the body are
   collected in reading order. Only if their count equals the number of footnotes
   on the page are they replaced by `[^N]` – otherwise only exact numeric
   matches are anchored and the rest is listed as "ohne sicheren Textanker".
   A wrong anchor would be worse than a missing one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Continuation lines of a footnote start with an ordinary lowercase word ("tive Companies")
# or a URL; anything else (digits, "=", "»", "ss", "Vgl.") starts a new footnote.
_GARBLED_NUMBER = {"ss", "so", "ao", "u", "w", "»s", "»o"}
_CONTINUATION = re.compile(r"^(?:[a-zäöüß]{3,}\b|https?:|www\.|[a-zäöüß]+[-/.]\w)")
_LEADING = re.compile(r"^\s*([0-9ı?»=#%”\"'*u]{1,4}|ss|so|ao)\s*(?=\S)")
_LEADING_DIGITS = re.compile(r"^([0-9ı]{1,3})(?![0-9])")
# "5.198" in a footnote is the OCR reading of "S.198" (Seite); "Vg]." is "Vgl.".
_FIXES = [(re.compile(r"\bVg[l\]1I|][\.,]?\]?\.?"), "Vgl."),
          (re.compile(r"(?<=[\),]\s)5\.\s?(?=\d)"), "S. "),
          (re.compile(r"(?<=\d\s)5\.\s?(?=\d)"), "S. "),
          (re.compile(r"(?<=ibidem\s)5\.\s?(?=\d)"), "S. ")]

# A superscript marker glued to a word or punctuation: digits or their usual OCR misreadings.
# GLYPH_DIGITS lists, per misread glyph, the digits it was observed to stand for
# (measured on the script: "!9" = 19, "?°" = 20, "!®%" = 183, "4®" = 48 ...).
GLYPH_DIGITS = {"!": "1", "ı": "1", "?": "27", "°": "069",
                "®": "869", "%": "358", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
                "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0"}
NOISE = set("*‘’“'")             # glyphs that accompany a garbled marker but carry no digit
_MARK = "0-9?®°%!ı¹²³⁴⁵⁶⁷⁸⁹⁰*‘’“'"
_GLUED = re.compile(rf"(?<=[A-Za-zÄÖÜäöüß.,;:)\]“”\"'«»&])([{_MARK}]{{1,4}})(?=[\s,.;:)]|$)")
_STANDALONE = re.compile(rf"(?<=\s)([{_MARK}]{{1,4}})(?=[\s,.;:]|$)")
_CHEMICAL = re.compile(r"[A-Z]{1,2}\d$")   # "CO2" is a formula, not a marker
PUNCT_BEFORE = set(".,;:)“”\"")
STRONG_GLYPHS = set("®°¹²³⁴⁵⁶⁷⁸⁹⁰")   # never ordinary text: a truncated marker even after a letter


@dataclass
class Footnote:
    number: int
    page: int
    text: str
    readable: int | None          # number as read by OCR, None if garbled
    anchored: bool = False


@dataclass
class FootnoteIndex:
    by_page: dict[int, list[Footnote]] = field(default_factory=dict)
    discrepancies: list[str] = field(default_factory=list)

    def all(self) -> list[Footnote]:
        return [n for p in sorted(self.by_page) for n in self.by_page[p]]


def _is_start(text: str, previous: str | None) -> bool:
    if previous is not None and previous.rstrip().endswith("-"):
        return False
    first = text.split()[0] if text.split() else ""
    if _CONTINUATION.match(text) and first not in _GARBLED_NUMBER:
        return False
    return True


def _clean(text: str) -> str:
    for pattern, repl in _FIXES:
        text = pattern.sub(repl, text)
    return " ".join(text.split())


def _join(a: str, b: str) -> str:
    if a.endswith("-") and b[:1].islower():
        return a[:-1] + b
    return f"{a} {b}"


def parse(pages: dict[int, dict], skipped: set[int]) -> FootnoteIndex:
    """All footnotes in document order, numbered by sequence and checked against readable numbers."""
    index, counter = FootnoteIndex(), 0
    for pno in sorted(pages):
        if pno in skipped:
            continue
        lines = [ln for ln in pages[pno]["lines"] if ln["band"] == "footnote" and ln["text"].strip()]
        notes: list[Footnote] = []
        previous = None
        for ln in lines:
            text = ln["text"].strip()
            if notes and not _is_start(text, previous):
                notes[-1].text = _join(notes[-1].text, text)
                previous = text
                continue
            m = _LEADING_DIGITS.match(text)
            readable = int(m.group(1).replace("ı", "1")) if m else None
            expected = counter + 1
            if readable is not None and readable != expected:
                index.discrepancies.append(
                    f"PDF S. {pno}: gelesen {readable}, erwartet {expected} – "
                    + ("Zähler übernommen" if expected < readable <= expected + 5 else "Lesung verworfen"))
                if expected < readable <= expected + 5:
                    expected = readable          # we missed a footnote earlier: trust the print
                else:
                    readable = None
            counter = expected
            body = _LEADING.sub("", text, count=1) if not m else text[m.end():]
            notes.append(Footnote(number=counter, page=pno, text=body.strip(), readable=readable))
            previous = text
        for n in notes:
            n.text = _clean(n.text)
        if notes:
            index.by_page[pno] = notes
    return index


def _compatible(core: str, digits: str) -> bool:
    return len(core) == len(digits) and all(
        c == d or d in GLYPH_DIGITS.get(c, "") for c, d in zip(core, digits))


def _score(raw: str, before: str, number: int) -> int:
    """How well a marker candidate fits a footnote number: 0 = not at all.

    Full-length readings score 2 plus one per exactly read digit; truncated
    readings ("2" for 23) score 1 and only count right after punctuation,
    where a marker is the only plausible reading.
    """
    core = "".join(c for c in raw if c not in NOISE)
    digits = str(number)
    if not core:
        return 0
    if _compatible(core, digits):
        if not core.isdigit() and len(core) == 1 and before not in PUNCT_BEFORE:
            return 0                  # "neu?" / "Grundig!" – real punctuation is more likely
        return 2 + sum(c == d for c, d in zip(core, digits))
    if len(core) < len(digits) and (before in PUNCT_BEFORE or core[0] in STRONG_GLYPHS) and (
            _compatible(core, digits[:len(core)]) or _compatible(core, digits[-len(core):])):
        return 1
    return 0


def _candidates(text: str) -> list[tuple[int, int, str, str]]:
    """(start, end, raw, char before) of marker candidates in reading order."""
    found = []
    for rx in (_GLUED, _STANDALONE):
        for m in rx.finditer(text):
            raw, s = m.group(1), m.start(1)
            if rx is _STANDALONE and (len(raw) < 2 and not raw.isdigit() or text[s - 2:s - 1] not in PUNCT_BEFORE):
                continue              # a free-standing marker follows punctuation ("Preisen. 27")
            if _CHEMICAL.search(text[max(0, s - 2):s] + raw[:1]):
                continue
            found.append((s, m.end(1), raw, text[s - 1] if s else " "))
    return sorted(set(found))


def _align(cands: list, notes: list[Footnote]) -> list[tuple[int, int]]:
    """Order-preserving best matching of candidates to notes (classic DP over both sequences)."""
    n, m = len(cands), len(notes)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            sc = _score(cands[i][3], cands[i][4], notes[j].number)
            take = sc + best[i + 1][j + 1] if sc else -1
            best[i][j] = max(best[i + 1][j], best[i][j + 1], take)
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        sc = _score(cands[i][3], cands[i][4], notes[j].number)
        if sc and best[i][j] == sc + best[i + 1][j + 1]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif best[i][j] == best[i + 1][j]:
            i += 1
        else:
            j += 1
    return pairs


def anchor_page(rows: list[str], notes: list[Footnote]) -> list[str]:
    """Replace footnote markers in a page's text rows (reading order) by `[^N]`.

    Marks anchored notes in place. A marker is only replaced when it fits the
    footnote's number glyph by glyph – a wrong anchor would be worse than none.
    """
    if not notes:
        return rows
    cands = [(i, s, e, raw, before) for i, row in enumerate(rows) for s, e, raw, before in _candidates(row)]
    out = list(rows)
    chosen = [(cands[ci], notes[nj]) for ci, nj in _align(cands, notes)]
    for (i, s, e, _raw, _b), note in sorted(chosen, key=lambda x: (x[0][0], -x[0][1])):
        out[i] = out[i][:s] + f"[^{note.number}]" + out[i][e:]
        note.anchored = True
    return out
