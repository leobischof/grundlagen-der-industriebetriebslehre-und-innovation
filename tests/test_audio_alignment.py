import copy

import pytest

from pipeline.audio_sync import align
from pipeline.build_interactive import validate_timeline


def test_alignment_can_go_backward_and_omits_unrelated_speech():
    blocks = [dict(page=2,text="Produktion Maschine Material Durchlaufzeit",rect=[.1,.2,.7,.1]),
              dict(page=8,text="Innovation Neuheit Wert Markt Produkt",rect=[.1,.3,.7,.1])]
    segments = [dict(start=0,end=12,text="Innovation Neuheit Wert Markt"),
                dict(start=30,end=42,text="Produktion Maschine Material"),
                dict(start=60,end=72,text="Wetter Spaziergang Geburtstag")]
    cues = align(segments,blocks)
    assert [a["page"] for a in cues] == [8,2]
    assert all(a["status"] == "unreviewed" and 0 <= a["confidence"] <= 1.001 for a in cues)


def test_package_refuses_stale_identity_or_broken_coordinates():
    timeline = dict(version=1,chapter=2,audio_sha256="a",pdf_sha256="p",annotations=[dict(
        id="x",start=0,end=12,page=1,type="rect",rect=[.1,.2,.4,.3],status="unreviewed")])
    validate_timeline(timeline,2,"a","p")
    with pytest.raises(ValueError,match="verändert"):
        validate_timeline(timeline,2,"a","new-pdf")
    for delta in (dict(rect=[.8,.2,.5,.2]),dict(end=-1),dict(start=float("nan")),dict(page=0)):
        broken = copy.deepcopy(timeline)
        broken["annotations"][0].update(delta)
        with pytest.raises(ValueError):
            validate_timeline(broken,2,"a","p")
