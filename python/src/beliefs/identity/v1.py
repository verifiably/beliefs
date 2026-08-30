"""``science.identity.v1`` — the canonical value contract.

Specified by the computation-reproducibility design §4.3. The requirement is not
strictness but **injectivity**: a value's type must survive its encoding. §4.3
records four collisions that had to be closed and notes that two of them were
introduced by the fixes for the other two, which is why each rule below is
stated as an encoding that preserves type rather than value.

Six kinds depend on this (world §4.2 assigns content-derived bases to
``dataset``, ``analysis-spec``, ``run``, ``verification``, ``assessment`` and
``source-assertion`` and specifies canonicalization for none of them), and the
formal model adds a seventh position: ``I_claim`` is this encoding under the
``tag_claim`` domain.

Two rules below are **not** in §4.3, which says "canonical JSON" without pinning
what that means. Both are recorded as amendments in the design; they are noted
here because a reader comparing the code to §4.3 will not find them there:

* **String escaping is pinned exactly** (``_encode_string``). "Canonical JSON"
  does not determine it — Python and JavaScript disagree by default on non-ASCII
  and on control characters — and an unpinned escape rule is a silent
  cross-language identity fork.
* **Object keys sort by code point, never by UTF-16 code unit.** These orders
  differ above U+FFFF, and JavaScript's default sort uses the wrong one.
"""

from __future__ import annotations

import json
import re
import unicodedata
from decimal import Decimal
from hashlib import sha256

from beliefs.errors import (
    BinaryFloatRefused,
    CanonicalTextRefused,
    IdentityError,
    KeyCollision,
    LoneSurrogate,
    MalformedDomain,
    NonFiniteDecimal,
    NonStringKey,
    NullRefused,
    UnsupportedValueType,
)

__all__ = ["check_domain", "decode", "digest", "encode"]

# `science.<kind>.v<n>`, with at least one kind segment and a positive version.
# The grammar is enforced rather than assumed for two reasons. A domain carrying
# a newline would forge the separator below and let one payload digest as
# another. And §4.3 requires that "v2 domains are disjoint from v1 by
# construction" — a shape only a checked grammar delivers.
_DOMAIN = re.compile(r"^science\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*\.v[1-9][0-9]*$")

# The JSON escapes with a short form. Every other C0 control takes `\u00xx`.
_SHORT_ESCAPE = {0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r"}


def check_domain(domain: str) -> None:
    """Refuse a domain that is not a well-formed versioned domain name."""
    if not _DOMAIN.fullmatch(domain):
        raise MalformedDomain(
            f"{domain!r} is not a well-formed identity domain; "
            "expected `science.<kind>.v<n>`, lowercase, with a positive version"
        )


def _encode_string(value: str, path: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    out = ['"']
    for char in normalized:
        code_point = ord(char)
        if 0xD800 <= code_point <= 0xDFFF:
            raise LoneSurrogate(f"at {path}: U+{code_point:04X} is an unpaired surrogate and has no UTF-8 encoding")
        if char == '"':
            out.append('\\"')
        elif char == "\\":
            out.append("\\\\")
        elif code_point in _SHORT_ESCAPE:
            out.append(_SHORT_ESCAPE[code_point])
        elif code_point < 0x20:
            out.append(f"\\u{code_point:04x}")
        else:
            # Everything else is literal UTF-8. Non-ASCII is never escaped, and
            # `/` is never escaped: both are optional in JSON, and an option is
            # a place two implementations can differ.
            out.append(char)
    out.append('"')
    return "".join(out)


def _encode_decimal(value: Decimal, path: str) -> str:
    if not value.is_finite():
        raise NonFiniteDecimal(
            f"at {path}: {value} has no JSON encoding, and every substitute collides — "
            "a bare token with a string, `null` is already refused, and a sentinel number with that number"
        )
    if value == 0:
        # One spelling of zero, which also folds negative zero. Two spellings of
        # one value would break well-definedness even though neither collides.
        return "0.0"
    text = format(value, "f")  # never exponent notation
    if "." not in text:
        return text + ".0"  # a decimal always retains a fractional part
    integer, fraction = text.split(".")
    return f"{integer}.{fraction.rstrip('0') or '0'}"


def _encode_value(value: object, path: str) -> str:
    if value is None:
        raise NullRefused(f"at {path}: null is refused, not pruned")
    # bool before int: in Python `bool` is a subclass of `int`, so an int check
    # first would encode True as 1 and collapse two types into one encoding.
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        raise BinaryFloatRefused(
            f"at {path}: binary floats are refused at the boundary; supply a Decimal and own the rounding"
        )
    if isinstance(value, int):
        return str(value)  # an integer never contains a point
    if isinstance(value, Decimal):
        return _encode_decimal(value, path)
    if isinstance(value, str):
        return _encode_string(value, path)
    if isinstance(value, list):
        return "[" + ",".join(_encode_value(item, f"{path}[{i}]") for i, item in enumerate(value)) + "]"
    if isinstance(value, dict):
        return _encode_object(value, path)
    raise UnsupportedValueType(
        f"at {path}: {type(value).__name__} is not an identity value; "
        "admissible are str, bool, int, Decimal, list and dict"
    )


def _encode_object(value: dict[object, object], path: str) -> str:
    normalized: dict[str, object] = {}
    for key, member in value.items():
        if not isinstance(key, str):
            raise NonStringKey(f"at {path}: object key {key!r} is {type(key).__name__}, not a string")
        normalized_key = unicodedata.normalize("NFC", key)
        if normalized_key in normalized:
            raise KeyCollision(
                f"at {path}: keys {key!r} and an earlier key are distinct before NFC normalization "
                f"and identical after it ({normalized_key!r}); refused, never merged"
            )
        normalized[normalized_key] = member
    # `sorted` on `str` orders by code point, which is the required order.
    parts = [
        _encode_string(key, path) + ":" + _encode_value(normalized[key], f"{path}.{key}") for key in sorted(normalized)
    ]
    return "{" + ",".join(parts) + "}"


def encode(value: object) -> bytes:
    """Canonical bytes for an identity value, or a refusal."""
    return _encode_value(value, "$").encode("utf-8")


def _refuse_constant(token: str) -> object:
    raise CanonicalTextRefused(f"refused constant {token!r}: NaN and Infinity never parse")


def decode(data: bytes) -> object:
    """The exported inverse: parse canonical bytes back to the typed value.

    Validity is canonical re-encoding equality — `encode(parsed)` must equal
    `data` byte-for-byte — which also refuses non-canonical ordering and
    collapsed duplicate keys. Every failure is `CanonicalTextRefused`; a
    re-encoding `IdentityError` is wrapped with its cause preserved.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as caught:
        raise CanonicalTextRefused(f"malformed UTF-8: {caught}") from caught
    try:
        parsed: object = json.loads(
            text,
            parse_int=int,
            parse_float=Decimal,
            parse_constant=_refuse_constant,
        )
    except CanonicalTextRefused:
        raise
    except ValueError as caught:
        raise CanonicalTextRefused(f"malformed JSON: {caught}") from caught
    try:
        reencoded = encode(parsed)
    except CanonicalTextRefused:
        raise
    except IdentityError as caught:
        raise CanonicalTextRefused(
            f"re-encoding refused ({type(caught).__name__}): {caught}"
        ) from caught
    if reencoded != data:
        raise CanonicalTextRefused(
            "bytes are not canonical: re-encoding differs from the input"
        )
    return parsed


def digest(domain: str, value: object) -> str:
    """``sha256(domain + "\\n" + canonical bytes)``, hex, domain-separated per kind."""
    check_domain(domain)
    return sha256(domain.encode("utf-8") + b"\n" + encode(value)).hexdigest()
