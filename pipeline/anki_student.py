"""The students' Anki cards (learning/flashcards/<deck>.json) sorted into the script's chapters.

The decks carry no tags, so each card's chapter is inferred from its words, deterministically
and without a model: a card scores against every chapter by how characteristic its words are
for that chapter's text (tf-idf over word stems). Two of the three decks follow the script
from chapter 1 to 9; for them the order is strong evidence, and a dynamic programme finds the
best assignment that moves forward through the chapters (going back costs PENALTY × the deck's
median card score), which corrects cards whose words alone point elsewhere ("Was ist
Effizienz?"). A deck whose best per-card chapters agree with that path for less than ORDERED
of its cards is not in script order (fri1703 mixes its second half), and there each card simply
takes its best-scoring chapter.

The cards stay what they are: unverified student material, text only (flashcards dropped the
pictures, which may have been script screenshots). A card whose answer was only a picture has
nothing left to show and is left out.
"""
from __future__ import annotations

import math
import re
import statistics
from collections import Counter

from .anki_cards import Card

STEM = 6                      # letters of a word that count (Innovation/Innovationen → innova)
PENALTY = 1.0                 # × median card score: cost of stepping back a chapter in an ordered deck
ORDERED = 0.8                 # share of cards on the ordered path that marks a deck as ordered
IMAGE_NOTE = "*Die Originalkarte enthielt ein Bild, das hier fehlt.*"
TRUST_NOTE = "Karte von Studierenden (Deck „{deck}“), nicht gegen das Skript geprüft"


def stems(text: str) -> list[str]:
    return [w.lower()[:STEM] for w in re.findall(r"[A-Za-zÄÖÜäöüß]{4,}", text)]


class ChapterIndex:
    """tf-idf weights of word stems per chapter."""

    def __init__(self, texts: list[str]):
        self.docs = [Counter(stems(t)) for t in texts]
        self.totals = [max(sum(d.values()), 1) for d in self.docs]
        self.df = Counter(s for d in self.docs for s in d)

    def scores(self, text: str) -> list[float]:
        words = set(stems(text))
        n = len(self.docs)
        return [sum(math.log(n / self.df[w]) * math.log1p(1e4 * d[w] / total) for w in words if self.df.get(w))
                for d, total in zip(self.docs, self.totals)]


def _forward_path(scores: list[list[float]], penalty: float) -> list[int]:
    """Chapter per card maximising the total score, each step back costing `penalty` (Viterbi)."""
    n_ch = len(scores[0])
    best, back = [scores[0][:]], [[0] * n_ch]
    for row in scores[1:]:
        prev = best[-1]
        cur, ptr = [], []
        for j in range(n_ch):
            value, k = max((prev[k] - (penalty if k > j else 0.0), k) for k in range(n_ch))
            cur.append(value + row[j])
            ptr.append(k)
        best.append(cur)
        back.append(ptr)
    j = max(range(n_ch), key=lambda c: best[-1][c])
    path = [j]
    for ptr in reversed(back[1:]):
        j = ptr[j]
        path.append(j)
    return path[::-1]


def assign(scores: list[list[float]]) -> tuple[list[int], bool]:
    """Chapter index per card and whether the deck was treated as ordered."""
    if not scores:
        return [], False
    top = [max(range(len(s)), key=lambda j: s[j]) for s in scores]
    path = _forward_path(scores, PENALTY * statistics.median(max(s) for s in scores))
    ordered = sum(a == b for a, b in zip(top, path)) >= ORDERED * len(scores)
    if ordered:
        return path, True
    out, last = [], path[0]
    for s, t in zip(scores, top):
        last = t if max(s) > 0 else last          # a card without any known word keeps its neighbour's chapter
        out.append(last)
    return out, False


def deck_cards(deck: dict, chapters: list[str], index: ChapterIndex) -> tuple[list[Card], bool]:
    """Cards of one student deck (learning/flashcards/<deck>.json) with their chapters."""
    usable = [c for c in deck["cards"] if c["front"].strip() and c["back"].strip()]
    picks, ordered = assign([index.scores(f"{c['front']} {c['back']}") for c in usable])
    note = TRUST_NOTE.format(deck=deck["deck"])
    cards = [Card("studierende", chapters[j], c["id"], c["front"],
                  f"{c['back']}\n\n{IMAGE_NOTE}" if c["had_image"] else c["back"], note)
             for c, j in zip(usable, picks)]
    return cards, ordered
