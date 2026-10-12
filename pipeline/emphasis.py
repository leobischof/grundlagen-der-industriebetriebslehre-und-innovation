"""Bold print of the script carried into the cleaned text as markdown `**…**`.

extract-text records, per OCR line, which words the scan sets in bold (bold_print). textclean
turns them into bold runs per row and joins runs that continue on the next row of the same
block. What is left here is pure text work: clean a run into a phrase and find that phrase
in the finished, corrected item text, which differs from the raw OCR row by hyphenation,
footnote anchors and curated corrections. A phrase that cannot be found is reported, never
guessed into place.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

LETTER = r"\wÄÖÜäöüß"
MIN_ALNUM = 3                  # a shorter phrase ("ee", "A.") is a bullet glyph or OCR noise
_NUMBERED = re.compile(r"^\(?\d{1,2}[.)]$")          # "3." / "(2)" of a numbered item
# Footnote numbers glued to the punctuation after a word ("wachsen.32", "Barrieren:80:81",
# "Bilanz:85,"); a letter-digit word like "CO2" stays as it is.
_GLUED_NOTE = re.compile(r"^(.*[^\W\d_][.,;:!?“”\"')]+)(?:\d{1,3}[.,;:]?)+$")
_REF = r"(?:\[\^\d+\])?"


@dataclass
class Run:
    """Consecutive bold words of one row; does it touch the row's start or end?"""
    text: str
    at_start: bool
    at_end: bool


def _alnum(text: str) -> int:
    return sum(c.isalnum() for c in text)


def runs(words: list[str], bold: set[int], skip: int = 0) -> list[Run]:
    """Bold runs of a row, ignoring its first `skip` words (a bullet glyph).

    Short non-bold tokens at the row edges ("Joseph A." | "Schumpeter") still count as
    touching the edge, so a run can continue across the line break.
    """
    out: list[Run] = []
    i = skip
    while i < len(words):
        if i not in bold:
            i += 1
            continue
        j = i
        while j < len(words) and j in bold:
            j += 1
        tail = all(_alnum(w) < 2 for w in words[j:])
        head = all(_alnum(w) < 2 for w in words[skip:i])
        out.append(Run(" ".join(words[i:] if tail else words[i:j]), head, tail))
        i = j
    return out


def clean_phrase(text: str) -> str:
    """Trim a run to the phrase worth marking; "" if nothing is left."""
    tokens = text.split()
    tokens = [_GLUED_NOTE.sub(r"\1", t) for t in tokens]
    while tokens and (_alnum(tokens[0]) < 2 or _NUMBERED.match(tokens[0])):
        tokens.pop(0)
    while tokens and _alnum(tokens[-1]) < 2:
        tokens.pop()
    if not tokens:
        return ""
    while not tokens[0][0].isalnum() and tokens[0][0] != "(":
        tokens[0] = tokens[0][1:]
    tokens[-1] = _rstrip_punct(tokens[-1])
    phrase = " ".join(tokens)
    if phrase.count("(") > phrase.count(")"):          # run ends inside a parenthesis: cut before it
        phrase = phrase[:phrase.rindex("(")].rstrip()
    elif phrase.count(")") > phrase.count("("):
        phrase = phrase[phrase.index(")") + 1:].lstrip()
    return phrase if _alnum(phrase) >= MIN_ALNUM else ""


def _rstrip_punct(token: str) -> str:
    """Drop trailing quotes and sentence marks; keep ")" (balanced later) and "." of "bzw."."""
    while token and not token[-1].isalnum() and token[-1] != ")":
        token = token[:-1]
    return token


def _pattern(phrase: str) -> re.Pattern:
    tokens = [re.escape(t) for t in phrase.split()]
    body = (_REF + r"\s+").join(tokens)
    return re.compile(rf"(?<![{LETTER}]){body}(?![{LETTER}])")


def _inside_bold(text: str, start: int) -> bool:
    return text.count("**", 0, start) % 2 == 1


def apply(text: str, phrases: list[str]) -> tuple[str, list[str]]:
    """Wrap each phrase (reading order) in `**`; returns the text and the phrases not found.

    The search starts after the previously marked phrase, so a term that occurs twice is
    marked where the script sets it in bold; only if it is not found there does it fall
    back to the start. A phrase already inside bold (a run-in label) counts as found.
    """
    missed = []
    cursor = 0
    for phrase in phrases:
        pattern = _pattern(phrase)
        matches = [m for m in pattern.finditer(text) if "**" not in m.group(0)]
        free = [m for m in matches if not _inside_bold(text, m.start())]
        ahead = [m for m in free if m.start() >= cursor]
        if not ahead and len(free) < len(matches):
            continue                                   # already bold (a run-in label)
        if not free:
            missed.append(phrase)
            continue
        m = (ahead or free)[0]
        text = f"{text[:m.start()]}**{m.group(0)}**{text[m.end():]}"
        cursor = m.end() + 4
    return text.replace("****", ""), missed           # two touching phrases become one
