import xml.etree.ElementTree as ET

import pytest

from pipeline.figure_icons import NS, populate, safe_body, search


def fixture_library():
    return dict(prefix="lucide",version="test",license="ISC",source="https://example.test/icons",license_text="Copyright and permission",
                icons={"width":24,"height":24,"icons":{"cog":{"body":'<circle cx="12" cy="12" r="5" fill="currentColor"/>'},"cog-outline":{"body":""}}})


def test_exact_search_preferred_and_unknown_search_has_no_fake_fallback():
    lib=fixture_library()
    assert search("cog",[lib])[1] == "cog"
    assert search("not-a-real-icon",[lib]) is None


def test_populate_keeps_label_embeds_license_and_is_idempotent():
    lib=fixture_library()
    slot=ET.fromstring(f'<g xmlns="{NS}" data-icon-query="cog" data-icon-box="10 20 48 48"><text>Zahnrad</text></g>')
    record=populate(slot,lib,"cog",lib["icons"]["icons"]["cog"])
    populate(slot,lib,"cog",lib["icons"]["icons"]["cog"])
    assert slot.find(f"{{{NS}}}text").text == "Zahnrad"
    assert len([n for n in slot if n.get("data-library-icon")]) == 1
    assert "Copyright and permission" in ET.tostring(slot,encoding="unicode")
    assert record["license"] == "ISC"


def test_active_or_external_icon_content_is_rejected():
    for body in ['<script>alert(1)</script>','<path onload="test"/>','<use href="https://example.test/x"/>','<path fill="url(https://example.test/x)"/>']:
        with pytest.raises(ValueError):
            safe_body(body)
