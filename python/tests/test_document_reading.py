"""The shared document reading, against the fixture TypeScript also reads.

Each row is a whole contract document, read to the same typed value by both
readers or refused by both (`fixtures/document-reading-v1.json`). A value is
written typed — `{"int": 10}`, `{"str": "yes"}`, `{"bool": true}`,
`{"null": true}`, `{"map": {...}}`, `{"seq": [...]}` — so an integer and a
string of the same digits, or `true` and `"true"`, cannot pass for each other.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from beliefs.contract.document import parse_document
from beliefs.errors import MalformedContract

_FIXTURE = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures" / "document-reading-v1.json").read_text(encoding="utf-8")
)


def _typed(value: object) -> object:
    if value is None:
        return {"null": True}
    if isinstance(value, bool):
        return {"bool": value}
    if isinstance(value, int):
        return {"int": value}
    if isinstance(value, str):
        return {"str": value}
    if isinstance(value, dict):
        return {"map": {key: _typed(item) for key, item in value.items()}}
    if isinstance(value, list):
        return {"seq": [_typed(item) for item in value]}
    raise AssertionError(f"the reader produced a {type(value).__name__}, which no row expects")


@pytest.mark.parametrize("row", [r for r in _FIXTURE["rows"] if "value" in r], ids=lambda r: r["name"])
def test_a_row_reads_to_its_typed_value(row: dict[str, object]) -> None:
    assert _typed(parse_document(str(row["text"]), source="<row>")) == row["value"]


@pytest.mark.parametrize("row", [r for r in _FIXTURE["rows"] if r.get("refused")], ids=lambda r: r["name"])
def test_a_row_is_refused(row: dict[str, object]) -> None:
    with pytest.raises(MalformedContract):
        parse_document(str(row["text"]), source="<row>")


def test_every_row_says_what_it_expects() -> None:
    assert _FIXTURE["domain"] == "beliefs.document-reading.v1"
    for row in _FIXTURE["rows"]:
        assert ("value" in row) != bool(row.get("refused")), row["name"]


def test_the_core_reading_does_not_leak_into_pyyaml_safe_loader() -> None:
    # The resolvers are the reader's own class's; PyYAML's SafeLoader is untouched.
    import yaml

    assert yaml.safe_load("x: 010") == {"x": 8}
