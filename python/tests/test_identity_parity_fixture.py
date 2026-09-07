"""The second parity fixture, Python half: components → encode → digest, bytes and digest both compared."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from beliefs import errors
from beliefs.identity import v1

FIXTURE = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "identity-v1.json").read_text(encoding="utf-8"))


def rebuild(component):
    tag = component["t"]
    if tag == "null":
        return None
    if tag == "bool":
        return component["v"]
    if tag == "int":
        return int(component["v"])
    if tag == "decimal":
        return Decimal(component["v"])
    if tag == "float":
        return float(component["v"])
    if tag == "str":
        return component["v"]
    if tag == "list":
        return [rebuild(v) for v in component["v"]]
    if tag == "obj":
        return {k: rebuild(v) for k, v in component["v"].items()}
    raise AssertionError(tag)


def test_the_fixture_is_about_this_encoding():
    assert FIXTURE["identity_contract"] == "science.identity.v1"
    assert {row["name"] for row in FIXTURE["vector"]} >= {"decimal-zero", "integer-zero", "escape-table", "astral-key-order", "namespaced-facet-key", "binary-float-refused"}


@pytest.mark.parametrize("row", [r for r in FIXTURE["vector"] if "refusal" not in r], ids=lambda r: r["name"])
def test_bytes_and_digest_agree(row):
    value = rebuild(row["value"])
    assert v1.encode(value).decode("utf-8") == row["canonical_bytes"]
    assert v1.digest(row["domain"], value) == row["digest"]


@pytest.mark.parametrize("row", [r for r in FIXTURE["vector"] if "refusal" in r], ids=lambda r: r["name"])
def test_refusals_agree(row):
    with pytest.raises(getattr(errors, row["refusal"])):
        v1.encode(rebuild(row["value"]))
