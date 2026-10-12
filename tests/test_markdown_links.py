"""Link extraction ignores code, external URLs and anchors; resolve() stays inside the repo."""
from __future__ import annotations

from pipeline.qa_checks_links import resolve
from pipeline.qa_markdown import footnotes, image_targets, local_links, split_frontmatter

TEXT = """---
id: sec-1.1
---
Siehe [A](a.md#anker) und ![Bild](../fig/x.png "Titel") und [web](https://example.org).
`[nicht](code.md)` und <img src="html.png">

```
[auch nicht](block.md)
```

[ref]: <ziel%20mit%20leer.md>
Fußnote[^1] und [Anker](#oben).

[^1]: Definition mit [Link](fn.md).
"""


def test_local_links():
    targets = [link.target for link in local_links(TEXT)]
    assert targets == ["a.md", "../fig/x.png", "html.png", "ziel mit leer.md", "fn.md"]


def test_line_numbers_count_from_file_start():
    assert local_links(TEXT)[0].line == 4


def test_frontmatter_footnotes_and_images():
    meta, body, err = split_frontmatter(TEXT)
    assert meta == {"id": "sec-1.1"} and err is None
    assert footnotes(body) == (["1"], ["1"])
    assert image_targets(body) == ["../fig/x.png"]


def test_resolve():
    assert resolve("content/01/a.md", "../README.md") == "content/README.md"
    assert resolve("content/a.md", "/docs/x.md") == "docs/x.md"
    assert resolve("README.md", "../x.md") is None
