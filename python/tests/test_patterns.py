"""The portable identifier-pattern subset, against the shared fixture."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from beliefs.errors import MalformedContract
from beliefs.patterns import IdentifierClass, check_portable_pattern, compile_portable

_FIXTURE = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures" / "identifier-patterns-v1.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("row", _FIXTURE["rows"], ids=lambda r: r["name"])
def test_row(row: dict[str, object]) -> None:
    compiled = compile_portable(str(row["pattern"]))
    term = unicodedata.normalize("NFC", str(row["term"]))
    assert (compiled.fullmatch(term) is not None) == row["matches"]


@pytest.mark.parametrize("row", _FIXTURE["malformed"], ids=lambda r: r["name"])
def test_malformed(row: dict[str, str]) -> None:
    with pytest.raises(MalformedContract):
        check_portable_pattern(row["pattern"], where="test")


def test_identifier_class_prefix_is_literal() -> None:
    assert IdentifierClass("HGNC", "HGNC:[1-9][0-9]*").matches("HGNC:5")
    with pytest.raises(MalformedContract):
        IdentifierClass("HGNC", "[H]GNC:1")
    with pytest.raises(MalformedContract):
        IdentifierClass("H.", "H.:1")
