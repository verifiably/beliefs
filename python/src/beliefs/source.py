"""The `source` basis projection (slice 2b design §3).

A source's basis is an identifier issued by the world, normalized. This module
owns the per-scheme form rules, the precedence that selects the basis when a
record carries several, and the address digest.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping

from beliefs.errors import IdentifierMalformed
from beliefs.identity import v1

__all__ = ["SCHEMES", "SOURCE_ADDRESS_DOMAIN", "basis", "normalize", "normalized_identifiers", "source_address"]

SCHEMES = ("doi", "pmid", "isbn", "accession")
SOURCE_ADDRESS_DOMAIN = "science.source-address.v1"

_DOI_PREFIX = re.compile(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", re.IGNORECASE)
_DOI = re.compile(r"^10\.[0-9]{4,9}/[^\s]+$")
_PMID_PREFIX = re.compile(r"^pmid:", re.IGNORECASE)
_PMID = re.compile(r"^[1-9][0-9]*$")
_ISBN_PREFIX = re.compile(r"^isbn:", re.IGNORECASE)
_ISBN10 = re.compile(r"^[0-9]{9}[0-9X]$")
_ISBN13 = re.compile(r"^97[89][0-9]{10}$")
_ACCESSION = re.compile(r"^[A-Z]+[A-Z0-9_.]*$")


def _refuse(scheme: str, value: object, reason: str, detail: str) -> IdentifierMalformed:
    return IdentifierMalformed(f"{scheme} identifier {value!r}: {detail}", scheme=scheme, value=value, reason=reason)


def _remainder(scheme: str, value: object, prefix: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise _refuse(scheme, value, "not-a-string", "an identifier is text")
    remainder = prefix.sub("", unicodedata.normalize("NFC", value).strip(), count=1)
    if not remainder:
        raise _refuse(scheme, value, "empty", "nothing remains after trimming and prefix stripping")
    return remainder


def _doi(value: object) -> str:
    remainder = _remainder("doi", value, _DOI_PREFIX).lower()
    if not _DOI.match(remainder):
        raise _refuse("doi", value, "malformed", "a DOI is 10.<4-9 digits>/<suffix> with no whitespace")
    return remainder


def _pmid(value: object) -> str:
    remainder = _remainder("pmid", value, _PMID_PREFIX)
    if not _PMID.match(remainder):
        raise _refuse("pmid", value, "malformed", "a PMID is a positive integer with no leading zero")
    return remainder


def _isbn13_check(digits12: str) -> str:
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits12))
    return str((10 - total % 10) % 10)


def _isbn(value: object) -> str:
    remainder = _remainder("isbn", value, _ISBN_PREFIX).replace("-", "").replace(" ", "").upper()
    if not remainder:
        raise _refuse("isbn", value, "empty", "nothing remains after trimming and prefix stripping")
    if _ISBN10.match(remainder):
        total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(remainder))
        if total % 11 != 0:
            raise _refuse("isbn", value, "malformed", "the ISBN-10 check digit fails")
        body = "978" + remainder[:9]
        return body + _isbn13_check(body)
    if len(remainder) == 13 and remainder.isdigit():
        if not _ISBN13.match(remainder):
            raise _refuse("isbn", value, "malformed", "an ISBN-13 begins 978 or 979")
        if _isbn13_check(remainder[:12]) != remainder[12]:
            raise _refuse("isbn", value, "malformed", "the ISBN-13 check digit fails")
        return remainder
    raise _refuse("isbn", value, "malformed", "an ISBN is ten or thirteen characters")


def _accession(value: object) -> str:
    remainder = _remainder("accession", value, re.compile(r"^$")).upper()
    if not _ACCESSION.match(remainder):
        raise _refuse("accession", value, "malformed", "an accession is letters then letters, digits, `_` or `.`")
    return remainder


_RULES: Mapping[str, Callable[[object], str]] = {"doi": _doi, "pmid": _pmid, "isbn": _isbn, "accession": _accession}


def normalize(scheme: str, value: object) -> str:
    if scheme not in _RULES:
        raise _refuse(scheme, value, "unknown-scheme", f"accepted schemes are {SCHEMES}")
    return _RULES[scheme](value)


def normalized_identifiers(identifiers: Mapping[str, object]) -> dict[str, str]:
    return {scheme: normalize(scheme, identifiers[scheme]) for scheme in sorted(identifiers)}


def basis(identifiers: Mapping[str, str]) -> tuple[str, str] | None:
    for scheme in SCHEMES:
        if scheme in identifiers:
            return scheme, identifiers[scheme]
    return None


def source_address(identifiers: Mapping[str, str]) -> str | None:
    selected = basis(identifiers)
    if selected is None:
        return None
    scheme, value = selected
    return f"source:{v1.digest(SOURCE_ADDRESS_DOMAIN, {'scheme': scheme, 'value': value})}"
