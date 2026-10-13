import json
import re

from pipeline.package_reader import render_html


def test_singlefile_has_no_external_scripts_or_styles_and_escapes_payload():
    template='<html><head><link rel="stylesheet" href="reader.css"><link rel="manifest" href="reader.webmanifest"></head><body><script type="module" src="reader-app.mjs"></script></body></html>'
    payload={"timeline":{"label":"</script><script>alert(1)</script>"},"pdf":"cGRm","audio":"YXVkaW8="}
    result=render_html(template,"body{margin:0}","globalThis.started=true;",payload,{"license":"ISC"})
    assert '<script type="module" src=' not in result
    assert '<link' not in result
    data=re.search(r'id="gil-payload">(.*?)</script>',result).group(1)
    assert '</script>' not in data and json.loads(data)==payload
    assert 'body{margin:0}' in result and 'globalThis.started=true' in result
