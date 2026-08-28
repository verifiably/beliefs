"""`v1.decode` — the exported inverse of the canonical codec (spec §2.6 item 5)."""

from decimal import Decimal

import pytest

from science.errors import CanonicalTextRefused, IdentityError
from science.identity import v1


def test_decode_round_trips_a_canonical_object() -> None:
    value = {"a": 1, "b": Decimal("0.5"), "c": ["x", True]}
    data = v1.encode(value)
    parsed = v1.decode(data)
    assert parsed == value
    assert v1.encode(parsed) == data


def test_decode_preserves_types_int_and_decimal_are_distinct() -> None:
    assert v1.decode(b"1") == 1 and type(v1.decode(b"1")) is int
    assert v1.decode(b"1.0") == Decimal("1.0") and type(v1.decode(b"1.0")) is Decimal
    assert v1.decode(b'"0.5"') == "0.5"
    assert v1.decode(b"0.5") == Decimal("0.5")


def test_decode_refuses_the_constants() -> None:
    for payload in (b"NaN", b"Infinity", b"-Infinity", b"[NaN]"):
        with pytest.raises(CanonicalTextRefused):
            v1.decode(payload)


def test_decode_refuses_malformed_utf8_and_malformed_json() -> None:
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"\xff\xfe")
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"{not json")


def test_decode_refuses_non_canonical_ordering_and_duplicate_keys() -> None:
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b'{"b":1,"a":2}')  # canonical order is a first
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b'{"a":1,"a":2}')  # collapsed duplicate re-encodes shorter


def test_decode_wraps_reencoding_identity_errors_cause_preserved() -> None:
    with pytest.raises(CanonicalTextRefused) as caught:
        v1.decode(b"null")  # NullRefused inside encode
    assert isinstance(caught.value, IdentityError)
    assert isinstance(caught.value.__cause__, IdentityError)
    assert "NullRefused" in str(caught.value)


def test_decode_refuses_a_float_producing_spelling() -> None:
    # 1e2 parses as Decimal under parse_float and re-encodes as "100" != b"1e2".
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"1e2")
