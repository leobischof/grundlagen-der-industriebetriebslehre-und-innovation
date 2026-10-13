import copy

from pipeline.audio_topics import add_topic_context, annotation_digest, untouched_generated


def test_topic_remains_during_example_but_specific_does_not_stick_to_unrelated_audio():
    sections = [dict(id="2.1",title="2.1 Erstes Thema",page=1,y=.1,last_page=2,end_y=.3),
                dict(id="2.2",title="2.2 Zweites Thema",page=2,y=.3,last_page=3,end_y=.94)]
    details = [dict(id="a",start=10,end=28,page=1,rect=[.1,.2,.7,.1],confidence=.4,status="unreviewed",origin="local-asr-lexical"),
               dict(id="b",start=180,end=198,page=2,rect=[.1,.5,.7,.1],confidence=.4,status="unreviewed",origin="local-asr-lexical")]
    cues = add_topic_context(details,sections,300)
    assert next(c for c in cues if c["id"] == "a")["end"] == 28
    assert any(c["scope"] == "topic" and c["topic_id"] == "2.1" and c["start"] <= 120 < c["end"] for c in cues)
    assert any(c["scope"] == "topic" and c["topic_id"] == "2.2" and c["start"] <= 250 < c["end"] for c in cues)


def test_automatic_refresh_protects_edited_and_reviewed_timelines():
    value = {"annotations":[dict(id="a",status="unreviewed",origin="local-asr-lexical",label="Original") ]}
    value["generated_annotations_sha256"] = annotation_digest(value["annotations"])
    assert untouched_generated(value)
    for change in [dict(label="Manuell geändert"),dict(status="reviewed")]:
        edited=copy.deepcopy(value);edited["annotations"][0].update(change)
        assert not untouched_generated(edited)
    assert not untouched_generated({"annotations":[]})
