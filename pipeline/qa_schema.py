"""JSON-Schema validation against the files in schemas/ (the format contracts).

The schemas are the machine-readable form of the contracts in
docs/architecture.md; each check validates its documents against one of them
and turns every violation into one readable German line.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from . import config

SECTION = "section-frontmatter"
FIGURE_META = "figure-metadata"
FIGURE_MANIFEST_ENTRY = "figure-manifest-entry"
EXAM_QUESTION = "exam-question"
TOPIC_MAPPING = "topic-mapping"
PROGRESS = "progress"


@lru_cache(maxsize=None)
def validator(name: str, schemas_dir: Path = config.SCHEMAS) -> Draft202012Validator:
    schema = json.loads((schemas_dir / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def problems(name: str, document, schemas_dir: Path = config.SCHEMAS) -> list[str]:
    """Human-readable violations, empty when `document` is valid."""
    out = []
    for err in sorted(validator(name, schemas_dir).iter_errors(document), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(Wurzel)"
        out.append(f"{where}: {err.message}")
    return out
