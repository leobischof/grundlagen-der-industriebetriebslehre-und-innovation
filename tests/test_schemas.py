"""The JSON schemas are valid, their examples pass, and committed example data conforms."""
from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator

from pipeline import config
from pipeline.qa_schema import PROGRESS, problems

SCHEMA_FILES = sorted(config.SCHEMAS.glob("*.schema.json"))


def test_all_contract_schemas_exist():
    names = {p.name.removesuffix(".schema.json") for p in SCHEMA_FILES}
    assert {"section-frontmatter", "figure-metadata", "figure-manifest-entry", "exam-question",
            "topic-mapping", "progress"} <= names


@pytest.mark.parametrize("path", SCHEMA_FILES, ids=lambda p: p.name)
def test_schema_is_valid_and_examples_pass(path):
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    name = path.name.removesuffix(".schema.json")
    for example in schema.get("examples", []):
        assert problems(name, example) == []


def test_progress_example_conforms():
    example = json.loads((config.LEARNING / "progress" / "example.json").read_text(encoding="utf-8"))
    assert problems(PROGRESS, example) == []
