"""Generate the values-level parity fixture for `science.identity.v1` (facet-contracts §7.3).
**Run by hand, never by tests:** `uv run python tools/generate_identity_fixture.py`.

Every row carries a **tagged** component tree, because JSON numbers cannot say
whether they meant an integer, a decimal or a binary float; the reader rebuilds
`int`/`Decimal`/`float` (Python) and `bigint`/`Decimal`/`number` (TypeScript).
Successful rows pin canonical bytes **and** digest; refusal rows pin the refusal.
The file is pure ASCII so an editor cannot normalize the decomposed row away.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from beliefs.errors import BinaryFloatRefused, LoneSurrogate, NullRefused
from beliefs.identity import v1

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT = REPO_ROOT / "fixtures" / "identity-v1.json"
DOMAIN = "science.parity-fixture.v1"


def tagged(value: object) -> object:
    if value is None:
        return {"t": "null"}
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    if isinstance(value, int):
        return {"t": "int", "v": str(value)}
    if isinstance(value, Decimal):
        return {"t": "decimal", "v": str(value)}
    if isinstance(value, float):
        return {"t": "float", "v": repr(value)}
    if isinstance(value, str):
        return {"t": "str", "v": value}
    if isinstance(value, list):
        return {"t": "list", "v": [tagged(v) for v in value]}
    if isinstance(value, dict):
        return {"t": "obj", "v": {k: tagged(v) for k, v in value.items()}}
    raise TypeError(type(value).__name__)


@dataclass(frozen=True)
class Row:
    name: str
    covers: str
    value: object
    refusal: type[Exception] | None = None


ESCAPES = "".join(chr(c) for c in range(0x20)) + '"\\'

VECTOR = [
    Row("integer", "an integer never contains a point", 12),
    Row("integer-zero", "one spelling of integer zero", 0),
    Row("negative-integer", "sign preserved", -7),
    Row("big-integer", "beyond 2^53, so a JavaScript number cannot carry it", 9007199254740993),
    Row("decimal-zero", "one spelling of decimal zero, folding -0", Decimal("-0.0")),
    Row("decimal-retains-fraction", "a decimal always retains a fractional part", Decimal(3)),
    Row("decimal-strips-trailing-zeros", "trailing zeros stripped", Decimal("1.2300")),
    Row("decimal-no-exponent", "never exponent notation", Decimal("1E+6")),
    Row("decimal-small", "small magnitudes spelled positionally", Decimal("1E-7")),
    Row("boolean-and-integer-distinct", "true is not 1", [True, 1]),
    Row("escape-table", "every C0 control, the quote and the backslash", ESCAPES),
    Row("non-ascii-unescaped", "non-ASCII is never escaped", "éβ😀"),
    Row("nfc-at-encode", "decomposed input, NFC-composed canonical output", "café"),
    Row("astral-key-order", "an astral key sorts after a high BMP key by code point", {"𐀀": 1, "￿": 2}),
    Row("plain-key-order", "keys sort by code point", {"b": 1, "a": 2, "B": 3}),
    Row("namespaced-facet-key", "D4's parity arm: a namespaced facet key round-trips", {"facets": {"biology/gene-axis": {"axis": "rows"}}}),
    Row("nested", "arrays and objects nest", {"a": [1, {"b": [Decimal("2.5"), "c"]}]}),
    Row("binary-float-refused", "binary floats are refused at the boundary", 0.1, BinaryFloatRefused),
    Row("null-refused", "null is refused, not pruned", {"a": None}, NullRefused),
    Row("lone-surrogate-refused", "an unpaired surrogate has no UTF-8 encoding", "\ud800", LoneSurrogate),
]


def main() -> None:
    rows = []
    for row in VECTOR:
        entry: dict[str, object] = {"name": row.name, "covers": row.covers, "domain": DOMAIN, "value": tagged(row.value)}
        if row.refusal is None:
            entry["canonical_bytes"] = v1.encode(row.value).decode("utf-8")
            entry["digest"] = v1.digest(DOMAIN, row.value)
        else:
            entry["refusal"] = row.refusal.__name__
            try:
                v1.encode(row.value)
            except row.refusal:
                pass
            else:
                raise SystemExit(f"{row.name}: expected {row.refusal.__name__}, got an encoding")
        rows.append(entry)
    OUTPUT.write_text(
        json.dumps({"fixture": "identity-v1", "identity_contract": "science.identity.v1", "note": "A conformance oracle, frozen. Regenerate deliberately with tools/generate_identity_fixture.py and review the diff.", "vector": rows}, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
