"""Blank exercises: answers go, structure and placeholders stay."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from pipeline.svg_blank import SVG_NS, blank_svg

SVG = f"""<svg xmlns="{SVG_NS}" viewBox="0 0 400 200" data-figure-id="abb-99" font-size="20">
  <title>Test</title>
  <desc>Verrät die Lösung</desc>
  <!-- structure -->
  <rect x="0" y="0" width="400" height="200"/>
  <path class="answer" d="M0 200 L400 0"/>
  <g text-anchor="middle" font-weight="bold">
    <text class="answer" x="200" y="50"><tspan x="200">Zwei</tspan><tspan x="200" dy="1.5em">Zeilen</tspan></text>
  </g>
  <g class="answer" transform="translate(10 0)">
    <text x="0" y="150">Gruppe</text>
  </g>
</svg>
"""


def _root(text: str) -> ET.Element:
    return ET.fromstring(text.split("\n", 1)[1])


def test_answers_removed_structure_kept():
    out, removed = blank_svg(SVG)
    root = _root(out)
    assert removed == 3
    assert "Zwei" not in out and "Gruppe" not in out and "Verrät" not in out
    assert root.find(f"{{{SVG_NS}}}path") is None
    assert root.get("data-exercise") == "blank" and root.get("data-figure-id") == "abb-99"
    assert "<!-- structure -->" in out
    assert not out.count("ns0:")


def test_placeholder_per_text_with_estimated_extent():
    root = _root(blank_svg(SVG)[0])
    boxes = [r for r in root.iter(f"{{{SVG_NS}}}rect") if r.get("class") == "placeholder"]
    assert len(boxes) == 2
    two_lines, group = boxes
    # centred bold text: 6 chars * 20 px * 0.6 = 72 px wide around x=200, two lines 30 px apart
    assert float(two_lines.get("x")) < 200 - 36 and float(two_lines.get("x")) + float(two_lines.get("width")) > 236
    assert float(two_lines.get("height")) > 30 + 20
    assert group.get("transform") == "translate(10 0)"


def test_deterministic():
    assert blank_svg(SVG) == blank_svg(SVG)
