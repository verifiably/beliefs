# World Resolution Slice 2b Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derive every `source` address from its normalized external identifier, build the one seam through which a source's identifiers change, and make the write and read boundaries check both — closing W1, W2 and W5a as conformance cut 25.

**Architecture:** A new `beliefs/source.py` owns per-scheme normalization, precedence and the address digest (the `dataset.py` precedent). `stored.source_node` loses its slug and derives its id; a `_refuse_source` boundary check runs on every write path; `CorpusWriter.correct_identifier` is a session-mediated `corpus-write` that appends an attributed entry to an identity-inert `identifier-correction` facet and renames through `deprecated_ids` without touching any referrer. No new operation kind, no act-report.

**Tech Stack:** Python 3.13, `uv`, pytest, pyright, ruff; `nodes` (the record substrate) and `atoms` (the executor); the repo's N2 sabotage audit (`tests/n2_arms.py`, `tests/test_n2.py`) and cut runners (`tools/acceptance_runner.py`).

**Spec:** `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` — every task cites its section. Read the spec first; the plan argues from it.

## Global Constraints

- Run everything from `python/` with the project venv: `uv run --frozen pytest ...` and `uv run --frozen pyright`; system python lacks `beliefs`.
- Pytest count claims need the summary line: do not pass `-q` (addopts already sets it); read the final `N passed` line.
- Frozen declarations that a task's line change displaces are never edited. Two mechanisms, and the task that moves the line uses the right one in the same commit: a **cited-not-run** guard (`python/tests/cited_not_run.py`, e.g. cut 4) gets the displaced arm recorded in its `stale_arms`; a **live** guard (e.g. cut 16) gets a dated re-target in its `_LIVE_SABOTAGES`. `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py` must pass after every task that touches a matched line; run it in Tasks 3, 4, 5, 6.
- The closeout gate is the root-level `just check` and `just test` (both from the repository root), then the cut runner. The python-only invocations inside tasks are per-task feedback, not the gate.
- Frozen files (`n2_arms_cut*.py`, cut documents, declaration tables of cuts ≤ 24) are never edited. Live phase modules of earlier cuts receive only the documented fixture migration (Task 3).
- Every DOI fixture is valid under spec §3.1: registrant of 4–9 digits, e.g. `10.1234/abc`. Never `10.1/abc`.
- Conventional commits; no AI-attribution trailer (the pre-commit hook refuses one).
- N2 rows are named `<unit>-<letter>` (`W1-a`, `W5a-c`); cut 25's `unit_of` parses exactly that (Task 10). Never copy cut 24's parser unchanged.
- Paths in this plan are relative to the repository root; the worktree is `.worktrees/slice-2b/`.
- The pre-commit gate runs ruff, pyright, biome and `tasks check`; `ts/node_modules` must exist in the worktree (`cd ts && npm ci` once).

---

## File map

| file | responsibility |
|---|---|
| `python/src/beliefs/source.py` (new) | `SCHEMES`, `SOURCE_ADDRESS_DOMAIN`, `normalize`, `normalized_identifiers`, `basis`, `source_address` — the basis projection; `stored` re-exports `SCHEMES` as `ACCEPTED_EXTERNAL_IDENTIFIERS` |
| `python/src/beliefs/errors.py` | `IdentifierMalformed`, `SourceAddressDisagreement`, `CorrectionRefused`, `HistoryDisagreement` |
| `python/src/beliefs/stored.py` | `source_node` (new signature), `source_basis`, `source_address_of`, `IdentifierCorrection`, `identifier_corrections`, `validate_source_history` (the one history/redirect validator), `IDENTIFIER_CORRECTION_FACET` |
| `contracts/science/CONTRACT.yaml`, `python/src/beliefs/contracts/science/CONTRACT.yaml` | the `identifier-correction` facet declaration (both copies, identical) |
| `python/src/beliefs/corpus.py` | `_refuse_source`, `_refuse_dataset_basis`, `correct_identifier`, `OperationWrites.correct_identifier`, `validated_node`, the finding loop |
| `python/src/beliefs/session/writer.py` | `ScopedWriter.correct_identifier` |
| `python/src/beliefs/relocation.py` | `consolidate` history comparison |
| `python/tests/test_source_address.py` (new) | normalization, precedence, digest pin, builder, readers, history shapes |
| `python/tests/test_identifier_correction.py` (new) | the seam, session layers, relocation, read side |
| `python/tests/acceptance/test_source_address_acceptance.py` (new) | W1, W2, W5a, failure boundary, lifecycle |
| `python/tests/cited_not_run.py` | cut 4's `stale_arms` gains `W3[6]` and `W3[8]` |
| `python/tests/acceptance/test_n2_cut16.py` | `_LIVE_SABOTAGES` re-targets `M3a` |
| `python/tests/acceptance/n2_arms_cut25.py`, `test_n2_cut25.py` (new) | sabotage declarations and audit |
| `python/tools/cut25_acceptance.py` (new) | the runner |
| `docs/designs/2026-09-10-conformance-cut-25.md` (new) | the cut document |

---

### Task 1: `source.py` — normalization, precedence and the address digest

**Files:**
- Create: `python/src/beliefs/source.py`
- Modify: `python/src/beliefs/errors.py` (append after `CoreferenceEndpointRefused`, ~line 1025)
- Test: `python/tests/test_source_address.py` (new)

**Interfaces:**
- Produces: `source.SCHEMES: tuple[str, ...]`, `source.SOURCE_ADDRESS_DOMAIN: str`, `source.normalize(scheme: str, value: object) -> str`, `source.normalized_identifiers(identifiers: Mapping[str, object]) -> dict[str, str]`, `source.basis(identifiers: Mapping[str, str]) -> tuple[str, str] | None`, `source.source_address(identifiers: Mapping[str, str]) -> str | None`, `errors.IdentifierMalformed(message, *, scheme, value, reason)` with `REASONS = ("unknown-scheme", "not-a-string", "empty", "malformed", "non-canonical")`.

- [ ] **Step 1: Add the error class**

Append to `python/src/beliefs/errors.py` directly after `CoreferenceEndpointRefused`. The module has no `__all__`; preserve its existing public-class export convention:

```python
class IdentifierMalformed(WriteRefused):
    """A source identifier refused by its scheme's form rule (slice 2b design
    §3.1): one class, a closed reason, the scheme and the offending value.
    `non-canonical` is the boundary's reason — a stored or supplied value the
    rule would have changed."""

    REASONS = ("unknown-scheme", "not-a-string", "empty", "malformed", "non-canonical")

    def __init__(self, message: str, *, scheme: str, value: object, reason: str) -> None:
        if reason not in self.REASONS:
            raise ValueError(f"{reason!r} is not an identifier refusal reason")
        super().__init__(message)
        self.scheme = scheme
        self.value = value
        self.reason = reason
```

- [ ] **Step 2: Write the failing tests**

Create `python/tests/test_source_address.py`:

```python
"""Slice 2b §3: the source basis projection — normalization, precedence, address."""

from __future__ import annotations

import pytest

from beliefs import source, stored
from beliefs.errors import IdentifierMalformed
from beliefs.identity import v1

DOI = "10.1234/abc.DEF"
CANONICAL_DOI = "10.1234/abc.def"


class TestNormalizeDoi:
    @pytest.mark.parametrize(
        "spelling",
        [
            "10.1234/abc.DEF",
            "  10.1234/abc.def  ",
            "doi:10.1234/abc.def",
            "DOI:10.1234/ABC.DEF",
            "https://doi.org/10.1234/abc.def",
            "http://dx.doi.org/10.1234/abc.def",
            "HTTPS://DOI.ORG/10.1234/abc.def",
        ],
    )
    def test_every_spelling_folds_to_one_canonical_form(self, spelling):
        assert source.normalize("doi", spelling) == CANONICAL_DOI

    def test_nfc_is_applied(self):
        assert source.normalize("doi", "10.1234/café") == "10.1234/café"

    @pytest.mark.parametrize("bad", ["10.1/abc", "11.1234/abc", "10.1234/", "10.1234", "10.1234/a b"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("doi", bad)
        assert caught.value.reason == "malformed"


class TestNormalizePmid:
    @pytest.mark.parametrize("spelling", ["12345", " 12345 ", "pmid:12345", "PMID:12345"])
    def test_folds(self, spelling):
        assert source.normalize("pmid", spelling) == "12345"

    @pytest.mark.parametrize("bad", ["0", "012345", "12a45", "-5"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("pmid", bad)
        assert caught.value.reason == "malformed"


class TestNormalizeIsbn:
    def test_isbn13_with_hyphens_and_prefix(self):
        assert source.normalize("isbn", "isbn: 978-0-306-40615-7") == "9780306406157"

    def test_isbn10_is_converted_to_isbn13(self):
        assert source.normalize("isbn", "0-306-40615-2") == "9780306406157"

    def test_isbn10_with_x_check_digit(self):
        assert source.normalize("isbn", "0-8044-2957-X") == "9780804429573"

    @pytest.mark.parametrize(
        "bad",
        [
            "978-0-306-40615-8",  # wrong ISBN-13 check digit
            "0-306-40615-3",  # wrong ISBN-10 check digit
            "0000000000000",  # checksum-valid, wrong prefix (spec §3.1)
            "1234567890123",  # wrong prefix, wrong checksum
            "12345",  # neither length
        ],
    )
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("isbn", bad)
        assert caught.value.reason == "malformed"


class TestNormalizeAccession:
    @pytest.mark.parametrize("spelling", ["gse12345", " GSE12345 ", "nc_000913.3"])
    def test_folds(self, spelling):
        assert source.normalize("accession", spelling) == spelling.strip().upper()

    def test_versioned_and_unversioned_stay_distinct(self):
        assert source.normalize("accession", "NC_000913.3") != source.normalize("accession", "NC_000913")

    @pytest.mark.parametrize("bad", ["12345", "GSE 123", "gse-123", "_GSE"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("accession", bad)
        assert caught.value.reason == "malformed"


class TestRefusalOrder:
    """Spec §3.1: sorted key order, first refusal wins; per entry
    unknown-scheme → not-a-string → empty → malformed."""

    def test_not_a_string_precedes_every_value_rule(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("doi", 5)
        assert caught.value.reason == "not-a-string"

    @pytest.mark.parametrize("scheme,value", [("doi", ""), ("doi", "   "), ("doi", "doi:"), ("pmid", "PMID:"), ("isbn", "isbn:--"), ("accession", " ")])
    def test_empty_after_trim_and_prefix_strip(self, scheme, value):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize(scheme, value)
        assert caught.value.reason == "empty"

    def test_unknown_scheme_wins_over_its_own_value(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"unknown": 1})
        assert (caught.value.reason, caught.value.scheme) == ("unknown-scheme", "unknown")

    def test_sorted_key_order_first_refusal_wins(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"pmid": 5, "doi": ""})
        assert (caught.value.reason, caught.value.scheme) == ("empty", "doi")

    def test_every_entry_is_validated_before_selection(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"doi": CANONICAL_DOI, "pmid": "0"})
        assert (caught.value.reason, caught.value.scheme) == ("malformed", "pmid")

    def test_one_tuple_in_precedence_order(self):
        assert source.SCHEMES == ("doi", "pmid", "isbn", "accession")
        assert stored.ACCEPTED_EXTERNAL_IDENTIFIERS is source.SCHEMES
        assert set(source._RULES) == set(source.SCHEMES)


class TestBasisAndAddress:
    def test_precedence_over_every_non_empty_subset(self):
        from itertools import combinations

        full = {"doi": CANONICAL_DOI, "pmid": "1", "isbn": "9780306406157", "accession": "GSE1"}
        seen = 0
        for size in range(1, 5):
            for schemes in combinations(source.SCHEMES, size):
                subset = {k: full[k] for k in schemes}
                expected = min(schemes, key=source.SCHEMES.index)
                assert source.basis(subset) == (expected, full[expected]), subset
                seen += 1
        assert seen == 15

    def test_no_basis_is_none(self):
        assert source.basis({}) is None
        assert source.source_address({}) is None

    def test_the_address_is_the_domain_digest_over_scheme_and_value(self):
        expected = v1.digest(source.SOURCE_ADDRESS_DOMAIN, {"scheme": "doi", "value": CANONICAL_DOI})
        assert source.source_address({"doi": CANONICAL_DOI, "pmid": "1"}) == f"source:{expected}"

    def test_pinned_digest(self):
        # A stored literal, computed once on 2026-09-10 under science.source-address.v1 over
        # {"scheme": "pmid", "value": "12345"}. Move it only on a ruled domain change.
        assert source.source_address({"pmid": "12345"}) == (
            "source:8e2aa77202899912130944e03f698206f93ec6faaf4d8c1e6847b9eec5e65db9"
        )
        assert source.SOURCE_ADDRESS_DOMAIN == "science.source-address.v1"

    def test_two_records_with_different_selected_bases_are_two_addresses(self):
        assert source.source_address({"pmid": "1"}) != source.source_address({"doi": CANONICAL_DOI, "pmid": "1"})
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py`
Expected: FAIL — `ImportError: cannot import name 'source'`.

- [ ] **Step 4: Write `source.py`**

Create `python/src/beliefs/source.py`:

```python
"""The `source` basis projection (slice 2b design §3).

A source's basis is an identifier issued by the world, normalized. This module
owns the per-scheme form rules, the precedence that selects the basis when a
record carries several, and the address digest. `SCHEMES` is the one accepted
set; `stored.ACCEPTED_EXTERNAL_IDENTIFIERS` re-exports it.

Form only, throughout. No authority is consulted and no identity is inferred.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping

from beliefs.errors import IdentifierMalformed
from beliefs.identity import v1

__all__ = ["SCHEMES", "SOURCE_ADDRESS_DOMAIN", "basis", "normalize", "normalized_identifiers", "source_address"]

SCHEMES = ("doi", "pmid", "isbn", "accession")
"""The accepted schemes in precedence order: the first present selects the basis."""

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
    """Trim, strip one leading scheme prefix, refuse the empty remainder."""
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
    """The canonical form of `value` under `scheme`'s rule, or `IdentifierMalformed`."""
    if scheme not in _RULES:
        raise _refuse(scheme, value, "unknown-scheme", f"accepted schemes are {SCHEMES}")
    return _RULES[scheme](value)


def normalized_identifiers(identifiers: Mapping[str, object]) -> dict[str, str]:
    """Every entry validated in sorted key order, the first refusal winning:
    `unknown-scheme` → `not-a-string` → `empty` → `malformed`. Returns the
    canonical map. Total over the map before any basis is selected."""
    return {scheme: normalize(scheme, identifiers[scheme]) for scheme in sorted(identifiers)}


def basis(identifiers: Mapping[str, str]) -> tuple[str, str] | None:
    """The first scheme present in precedence order, or `None`."""
    for scheme in SCHEMES:
        if scheme in identifiers:
            return scheme, identifiers[scheme]
    return None


def source_address(identifiers: Mapping[str, str]) -> str | None:
    """`source:` + the domain digest over the selected basis; `None` with no basis.
    The projection is never applied to nothing, so no empty-basis address exists."""
    selected = basis(identifiers)
    if selected is None:
        return None
    scheme, value = selected
    return f"source:{v1.digest(SOURCE_ADDRESS_DOMAIN, {'scheme': scheme, 'value': value})}"
```

Note on `_accession`: the `re.compile(r"^$")` prefix matches only the empty string, so `_remainder` strips nothing — accessions have no scheme prefix. Note on `_isbn`: the second `empty` check covers `isbn:--`, whose remainder survives `_remainder` and empties on hyphen removal.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py`
Expected: all pass. Confirm the summary line reads `N passed` with N ≥ 40.

- [ ] **Step 6: Lint and type-check**

Run: `cd python && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: `All checks passed!` and `0 errors`.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/source.py python/src/beliefs/errors.py python/tests/test_source_address.py
git commit -m "feat(source): per-scheme normalization, precedence and the address digest"
```

---

### Task 2: Readers, the history facet and both contract copies

**Files:**
- Modify: `python/src/beliefs/stored.py` (constants near line 152; readers after `external_identifiers`, ~line 349; `__all__`)
- Modify: `contracts/science/CONTRACT.yaml` and `python/src/beliefs/contracts/science/CONTRACT.yaml` (the `source` kind entry ~line 56 and the `facets:` block ~line 96)
- Test: `python/tests/test_source_address.py` (append)

**Interfaces:**
- Consumes: Task 1's `source.*`.
- Produces: `stored.IDENTIFIER_CORRECTION_FACET = "identifier-correction"`, `stored.source_basis(node) -> tuple[str, str] | None`, `stored.source_address_of(node) -> str | None`, `stored.IdentifierCorrection` (frozen dataclass: `from_identifiers: Mapping[str, str]`, `to_identifiers: Mapping[str, str]`, `actor: str`, `grounds: str`, `event_token: str`), `stored.identifier_corrections(node) -> tuple[IdentifierCorrection, ...]` (the history alone; raises `MalformedRecord`), `stored.held_source_addresses(history) -> frozenset[str]`, and **`stored.validate_source_history(node) -> tuple[IdentifierCorrection, ...]`** — the one validator: the history plus redirect agreement (`deprecated_ids == sorted(held − {node.id})`, so duplicates, order, a history-free deprecated id and an underived retired address are one refusal). Every boundary and read path calls `validate_source_history`, never the pieces.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_source_address.py`:

```python
from types import MappingProxyType

from nodes.core.node import Node

from beliefs.errors import MalformedRecord


def raw_source(identifiers, *, history=None, deprecated=(), node_id=None):
    """A hand-built source, stamped, at the derived address unless `node_id` overrides it."""
    facets = {stored.SOURCE_FACET: {"identifiers": dict(identifiers)}}
    if history is not None:
        facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [dict(e) for e in history]}
    node = Node(
        id=node_id or source.source_address(identifiers),
        kind="source",
        title="paper",
        facets=facets,
        deprecated_ids=list(deprecated),
    )
    return stored.stamp_semantic_identity(node)


def entry(frm, to, *, actor="curator", grounds="checked the PDF", token="t1"):
    return {"from": dict(frm), "to": dict(to), "actor": actor, "grounds": grounds, "event_token": token}


A = {"pmid": "1"}
B = {"doi": CANONICAL_DOI, "pmid": "1"}
ADDR_A = source.source_address(A)
ADDR_B = source.source_address(B)


class TestReaders:
    def test_source_basis_and_address_of(self):
        node = raw_source(B)
        assert stored.source_basis(node) == ("doi", CANONICAL_DOI)
        assert stored.source_address_of(node) == node.id == ADDR_B

    def test_no_history_reads_empty(self):
        assert stored.identifier_corrections(raw_source(A)) == ()

    def test_a_well_formed_history_reads_back(self):
        node = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        (correction,) = stored.identifier_corrections(node)
        assert correction.from_identifiers == A and correction.to_identifiers == B
        assert (correction.actor, correction.grounds, correction.event_token) == ("curator", "checked the PDF", "t1")

    def test_held_addresses(self):
        assert stored.held_source_addresses(stored.identifier_corrections(raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A]))) == {ADDR_A, ADDR_B}

    def test_validate_source_history_accepts_the_agreeing_redirect(self):
        node = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        assert len(stored.validate_source_history(node)) == 1
        assert stored.validate_source_history(raw_source(A)) == ()

    @pytest.mark.parametrize(
        "deprecated",
        [
            [],  # the retired address missing
            [ADDR_A, ADDR_A],  # a duplicate
            [ADDR_A, ADDR_B],  # the live address deprecated too
            [ADDR_A, "source:" + "f" * 64],  # a retired address the history does not derive
        ],
        ids=["missing", "duplicate", "live-and-deprecated", "underived"],
    )
    def test_validate_source_history_refuses_a_disagreeing_redirect(self, deprecated):
        node = raw_source(B, history=[entry(A, B)], deprecated=deprecated)
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(node)

    def test_an_unsorted_redirect_refuses(self):
        two = {"pmid": "2"}
        history = [entry(A, B, token="t1"), entry(B, two, token="t2")]
        node = raw_source(two, history=history, deprecated=sorted([ADDR_A, ADDR_B], reverse=True))
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(node)
        assert len(stored.validate_source_history(raw_source(two, history=history, deprecated=sorted([ADDR_A, ADDR_B])))) == 2

    def test_a_history_free_source_with_a_deprecated_id_refuses(self):
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(raw_source(B, deprecated=[ADDR_A]))

    @pytest.mark.parametrize(
        "history",
        [
            [],  # empty entries
            [dict(entry(A, B), extra=1)],  # an extra key
            [{k: v for k, v in entry(A, B).items() if k != "grounds"}],  # a missing key
            [entry({}, B)],  # empty from
            [entry(A, {})],  # empty to
            [entry(A, {"doi": DOI, "pmid": "1"})],  # non-canonical value in a map
            [entry(A, {"url": "x"})],  # unknown scheme in a map
            [entry(A, B, actor="")],
            [entry(A, B, grounds="")],
            [entry(A, B, token="")],
            [entry(A, B, grounds="\udcff")],  # a lone surrogate is not canonically encodable
            [dict(entry(A, B), **{"from": None})],  # a null map: this reader's refusal, never NullRefused
            [entry(A, B, token="t"), entry(B, {"pmid": "2"}, token="t")],  # duplicate token
            [entry(A, B), entry({"pmid": "9"}, {"pmid": "2"}, token="t2")],  # continuity broken
        ],
    )
    def test_malformed_shapes_refuse(self, history):
        node = raw_source(B if history and history[-1]["to"] == B else {"pmid": "2"}, history=history, deprecated=[ADDR_A])
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)

    def test_from_equal_to_refuses_and_nothing_else_does(self):
        # The one fixture that violates only the from != to clause: continuity holds,
        # the entry ends at the current identifiers, and the redirect set is empty.
        node = raw_source(A, history=[entry(A, A)], deprecated=[])
        with pytest.raises(MalformedRecord, match="from and to are equal"):
            stored.identifier_corrections(node)

    def test_the_last_entry_must_end_at_the_current_identifiers(self):
        node = raw_source({"pmid": "7"}, history=[entry(A, B)], deprecated=[ADDR_A])
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)

    def test_the_facet_must_be_a_mapping_with_entries_only(self):
        node = raw_source(B)
        node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [entry(A, B)], "note": 1}
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py -k "Readers"`
Expected: FAIL — `AttributeError: module 'beliefs.stored' has no attribute 'IDENTIFIER_CORRECTION_FACET'`.

- [ ] **Step 3: Add the constants, value and readers to `stored.py`**

Near the other facet constants (after `SOURCE_FACET = "source"`, line 152):

```python
IDENTIFIER_CORRECTION_FACET = "identifier-correction"
```

Add `from beliefs import source as source_basis_projection` to the imports (the alias avoids shadowing the `source` parameter names used elsewhere in the module). Add these entries to `__all__` in alphabetical position: `"IDENTIFIER_CORRECTION_FACET"`, `"IdentifierCorrection"`, `"held_source_addresses"`, `"identifier_corrections"`, `"source_address_of"`, `"source_basis"`, `"validate_source_history"`.

After `external_identifiers` (line 349), add:

```python
def _source_identifiers(node: Node) -> Mapping[str, Any]:
    facet = _facet(node, SOURCE_FACET) or {}
    identifiers = facet.get("identifiers")
    return identifiers if isinstance(identifiers, dict) else {}


def source_basis(node: Node) -> tuple[str, str] | None:
    """The selected `(scheme, value)` of a stored source, or `None`."""
    return source_basis_projection.basis({k: v for k, v in _source_identifiers(node).items() if isinstance(v, str)})


def source_address_of(node: Node) -> str | None:
    """The address the stored identifiers derive — what the boundary compares `node.id` against."""
    return source_basis_projection.source_address({k: v for k, v in _source_identifiers(node).items() if isinstance(v, str)})


@sealed
@final
@dataclass(frozen=True)
class IdentifierCorrection:
    """One attributed entry of a source's identifier-correction history (slice 2b §5.2)."""

    from_identifiers: Mapping[str, str]
    to_identifiers: Mapping[str, str]
    actor: str
    grounds: str
    event_token: str


_CORRECTION_KEYS = frozenset({"from", "to", "actor", "grounds", "event_token"})


def _correction_map(raw: object, where: str) -> Mapping[str, str]:
    if not isinstance(raw, dict) or not raw:
        raise MalformedRecord(f"{where}: is not a non-empty mapping")
    try:
        canonical = source_basis_projection.normalized_identifiers(raw)
    except IdentifierMalformed as caught:
        raise MalformedRecord(f"{where}: {caught}") from caught
    if canonical != raw:
        raise MalformedRecord(f"{where}: holds a non-canonical identifier")
    return MappingProxyType(canonical)


def identifier_corrections(node: Node) -> tuple[IdentifierCorrection, ...]:
    """The history, validated to slice 2b §5.2, or `MalformedRecord`. Absence
    is the no-history state; an empty list is malformed. Continuity ends at
    the current identifiers. Redirect agreement is the boundary's clause, not
    this reader's — it needs `deprecated_ids`, which `held_source_addresses`
    serves."""
    if IDENTIFIER_CORRECTION_FACET not in node.facets:
        return ()
    facet = node.facets[IDENTIFIER_CORRECTION_FACET]
    if not isinstance(facet, dict) or set(facet) != {"entries"} or not isinstance(facet["entries"], list) or not facet["entries"]:
        raise MalformedRecord(f"{node.id}: identifier-correction is a mapping holding a non-empty `entries` list")
    corrections: list[IdentifierCorrection] = []
    tokens: set[str] = set()
    for index, raw in enumerate(facet["entries"]):
        where = f"{node.id}: identifier-correction entry {index}"
        if not isinstance(raw, dict) or set(raw) != _CORRECTION_KEYS:
            raise MalformedRecord(f"{where}: keys are exactly {sorted(_CORRECTION_KEYS)}")
        for key in ("actor", "grounds", "event_token"):
            if not isinstance(raw[key], str) or not raw[key]:
                raise MalformedRecord(f"{where}: {key} is a non-empty string")
        # Maps first, so a null or non-mapping `from`/`to` is this reader's refusal and never an
        # encoding error; then the whole entry under the identity encoding, every refusal of
        # which (NullRefused, LoneSurrogate, ...) is IdentityError and translated here.
        frm = _correction_map(raw["from"], f"{where} from")
        to = _correction_map(raw["to"], f"{where} to")
        try:
            v1.encode(raw)
        except IdentityError as caught:
            raise MalformedRecord(f"{where}: not canonically encodable: {caught}") from caught
        if raw["event_token"] in tokens:
            raise MalformedRecord(f"{where}: event token {raw['event_token']!r} repeats")
        tokens.add(raw["event_token"])
        if frm == to:
            raise MalformedRecord(f"{where}: from and to are equal; a correction changes something")
        if corrections and dict(corrections[-1].to_identifiers) != dict(frm):
            raise MalformedRecord(f"{where}: from does not continue the previous entry's to")
        corrections.append(IdentifierCorrection(frm, to, raw["actor"], raw["grounds"], raw["event_token"]))
    if dict(corrections[-1].to_identifiers) != dict(_source_identifiers(node)):
        raise MalformedRecord(f"{node.id}: the last correction does not end at the current identifiers")
    return tuple(corrections)


def held_source_addresses(history: Sequence[IdentifierCorrection]) -> frozenset[str]:
    """Every address derivable from any map in the history — the set the redirect must agree with."""
    addresses: set[str] = set()
    for correction in history:
        for mapping in (correction.from_identifiers, correction.to_identifiers):
            address = source_basis_projection.source_address(mapping)
            assert address is not None  # a validated map is non-empty
            addresses.add(address)
    return frozenset(addresses)


def validate_source_history(node: Node) -> tuple[IdentifierCorrection, ...]:
    """The one implementation of slice 2b §5.2: the history, then redirect
    agreement — `deprecated_ids` is exactly `sorted(held − {node.id})`. A
    duplicate, an unsorted list, a history-free record carrying any deprecated
    id, and a retired address the history does not derive are one refusal.
    Every write path and both read paths call this and nothing narrower."""
    history = identifier_corrections(node)
    expected = sorted(held_source_addresses(history) - {node.id})
    if list(node.deprecated_ids) != expected:
        raise MalformedRecord(
            f"{node.id}: deprecated_ids {list(node.deprecated_ids)} are not the history's redirect set {expected}"
        )
    return history
```

Add `from beliefs.errors import IdentifierMalformed` to the existing errors import, and `from types import MappingProxyType` if not already imported (it is — check line ~40).

- [ ] **Step 4: Declare the facet in both contract copies**

In both `contracts/science/CONTRACT.yaml` and `python/src/beliefs/contracts/science/CONTRACT.yaml`, replace the `source` kind line:

```yaml
  source:
    domain: science.source.v1
    facets:
      source: { required: true, covered: true }
      identifier-correction: { required: false, covered: false }
```

and in the `facets:` block, after the `source:` reader line add:

```yaml
  identifier-correction: { shape: reader, reader: stored.identifier_corrections }
```

Then verify the copies are identical: `diff contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml` prints nothing.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py tests/test_profile.py tests/test_facet_contracts.py`
Expected: all pass (the contract tests confirm the declaration parses; if a test pins the count of declared facets, update that count in the same commit and say so in the commit body).

- [ ] **Step 6: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/stored.py contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml python/tests/test_source_address.py
git commit -m "feat(stored): source basis readers and the identifier-correction history facet"
```

---

### Task 3: The builder derives the address; migrate every call site

**Files:**
- Modify: `python/src/beliefs/stored.py:251` (`ACCEPTED_EXTERNAL_IDENTIFIERS` becomes the re-export) and `:736-737` (`source_node`)
- Modify: `python/tests/cited_not_run.py` (cut 4's `stale_arms`)
- Modify: the 18 test files calling `source_node` (list them with `grep -rl "source_node(" python/tests`), including the seven frozen-cut phase modules named in spec §10.6
- Test: `python/tests/test_source_address.py` (append), `python/tests/test_corpus_write.py::TestW3TheBasisRefusal`, `python/tests/test_arm_staleness.py`

**Interfaces:**
- Produces: `stored.source_node(*, title: str, identifiers: Mapping[str, object]) -> Node` — no `slug`; refuses `IdentifierMalformed` and `BasisMissing`.

- [ ] **Step 1: Write the failing builder tests**

Append to `python/tests/test_source_address.py`:

```python
from beliefs.errors import BasisMissing


class TestTheBuilder:
    def test_it_stores_the_canonical_form_and_derives_the_id(self):
        node = stored.source_node(title="A paper", identifiers={"doi": "https://doi.org/10.1234/ABC.def", "pmid": "pmid:7"})
        assert node.facets[stored.SOURCE_FACET] == {"identifiers": {"doi": CANONICAL_DOI, "pmid": "7"}}
        assert node.id == source.source_address({"doi": CANONICAL_DOI}) == stored.source_address_of(node)
        assert stored.IDENTIFIER_CORRECTION_FACET not in node.facets

    def test_two_spellings_are_one_facet_one_stamp_one_address(self):
        one = stored.source_node(title="x", identifiers={"doi": "10.1234/ABC"})
        two = stored.source_node(title="y", identifiers={"doi": "doi:10.1234/abc"})
        assert one.id == two.id and one.facets == two.facets

    def test_an_empty_basis_refuses_at_the_builder(self):
        with pytest.raises(BasisMissing):
            stored.source_node(title="A paper", identifiers={})

    def test_an_unaccepted_scheme_refuses_at_the_builder(self):
        with pytest.raises(IdentifierMalformed) as caught:
            stored.source_node(title="A paper", identifiers={"url": "https://example.org"})
        assert caught.value.reason == "unknown-scheme"
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py -k TheBuilder`
Expected: FAIL — `TypeError: source_node() missing 1 required positional argument: 'slug'`.

- [ ] **Step 3: Replace the tuple and the builder**

In `stored.py` replace lines 251–253 with:

```python
ACCEPTED_EXTERNAL_IDENTIFIERS = source_basis_projection.SCHEMES
"""W3's accepted external identifiers for a `source` — one tuple, in precedence
order (slice 2b §3). A closed set: a fallback derived from title and year is
exactly the coercion the row refuses."""
```

Cut 4's frozen arm `W3[8]` sabotages the old literal and cut 4 is cited-not-run, so in `python/tests/cited_not_run.py` add to the `cut=4` entry's `stale_arms` (keep the existing entries; use the sha of this task's commit once made — amend the commit after the first pass to insert it):

```python
            "W3[8]": "moved at <sha>, when slice 2b made source.SCHEMES the one accepted tuple (2026-09-10)",
```

Then replace lines 736–737 with:

```python
def source_node(*, title: str, identifiers: Mapping[str, object]) -> Node:
    """A source at its basis-derived address (slice 2b §4): every identifier
    canonical, the id the digest over the selected basis. No slug — a handle
    never participates in an address. Refuses an empty basis itself, since no
    id exists without one; the boundary refuses it again for hand-built records."""
    canonical = source_basis_projection.normalized_identifiers(identifiers)
    address = source_basis_projection.source_address(canonical)
    if address is None:
        raise BasisMissing(
            "a source carries an accepted external identifier "
            f"({', '.join(ACCEPTED_EXTERNAL_IDENTIFIERS)}); a curation note is its own explicit add, "
            "and no title-and-year fallback exists"
        )
    return _node("source", address.partition(":")[2], title, {SOURCE_FACET: {"identifiers": canonical}}, ())
```

Add `BasisMissing` to the `beliefs.errors` import in `stored.py`.

- [ ] **Step 4: Migrate the call sites**

Mechanical pass, then a manual pass. From `python/`:

```bash
grep -rl "source_node(" tests | xargs sed -i -E 's/source_node\("[^"]*", title=/source_node(title=/g'
grep -rn -E '"10\.[0-9]{1,3}/' tests | cut -d: -f1 | sort -u   # every abbreviated DOI fixture
```

Repair each abbreviated DOI used as an admissible source to a 4-digit registrant, keeping the suffix so intent stays readable: `10.1/abc` → `10.1234/abc`, `10.1/x` → `10.1234/x`, `10.1/s1` → `10.1234/s1`, `10.1/kept` → `10.1234/kept`, and so on. Do this with a second `sed -i -E 's#"10\.1/#"10.1234/#g'` over the same file list, then classify remaining matches: intentionally malformed normalization inputs and frozen evidence stay unchanged; no live positive source fixture may retain an abbreviated DOI.

Then the manual pass, file by file (`grep -rn "source:" tests` lists the 31 literals):

- Every `"source:<slug>"` literal that named a built source becomes the built node's `.id`. Where the test built the node inline and then referred to the literal, bind the node first: `paper = stored.source_node(title="paper", identifiers={"doi": "10.1234/paper"})` and use `paper.id`.
- Literals that name a source that is deliberately *absent* (`source:missing`, `source:elsewhere`, `source:former`) stay as they are — an unresolvable ref is what they assert.
- The seven-module verification also corrects cut 4's stale live assessment-readback expectation to `slug(RUN)`, the bare run identity V2 has returned since 2026-09-06; production semantics and frozen declarations do not move.
- `tests/test_corpus_write.py::TestW3TheBasisRefusal`: the two `identifiers={}` tests now assert `BasisMissing` from the **builder** (drop `writer.add(...)` around the call); add one boundary test that hand-builds a source with `governed_node("source", "handle", "A paper", {stored.SOURCE_FACET: {"identifiers": {}}}, ())` and asserts `writer.add` raises `BasisMissing` — the existing `_refuse_missing_basis` already answers it, so it passes now and keeps passing through Task 4. `test_an_unaccepted_identifier_is_not_a_basis` becomes:

```python
    def test_an_unaccepted_identifier_is_not_a_basis(self, writer):
        # The set is closed: a url or a title-and-year is not an external
        # identifier, and there is no derived-identity escape to reach.
        with pytest.raises(IdentifierMalformed) as caught:
            stored.source_node(title="A paper", identifiers={"url": "https://example.org"})
        assert caught.value.reason == "unknown-scheme"
```

  `test_a_note_is_not_what_a_missing_basis_coerces_to` keeps its `holds` assertion over the address the empty map *would* have had — there is none — so assert `not any(n.kind == "source" for n in writer.read_view.iter_stored())` instead of `holds("source:s1")`.

- [ ] **Step 5: Run the whole suite**

Run: `cd python && uv run --frozen pytest tests --ignore=tests/acceptance`
Expected: every test passes. Then `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py` — passes once `W3[8]` is registered with the right sha. Then run the seven migrated acceptance phase modules directly: `uv run --frozen pytest tests/acceptance/test_permit_acceptance.py tests/acceptance/test_durable_corpus.py tests/acceptance/test_facet_acceptance.py tests/acceptance/test_relocation_acceptance.py tests/acceptance/test_coreference_acceptance.py tests/acceptance/test_session_acceptance.py tests/acceptance/test_deletion_acceptance.py` — all pass. Record the two summary lines in the commit body.

- [ ] **Step 6: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
git add -A python/src/beliefs/stored.py python/tests
git commit -m "feat(stored)!: source_node derives its address from the normalized identifier

Slug removed; 78 call sites and 31 source: literals migrated; abbreviated
DOI fixtures repaired to valid registrants (slice 2b design §10.2)."
```

---

### Task 4: The write boundary — `_refuse_source`, `_refuse_dataset_basis`, the cut 16 adapter

**Files:**
- Modify: `python/src/beliefs/corpus.py` — `_refuse_missing_basis` (~line 2836), `_refuse` (~2716), `_preflight_replace_locked` (~1669)
- Modify: `python/src/beliefs/errors.py` — `SourceAddressDisagreement`
- Modify: `python/tests/acceptance/test_n2_cut16.py::_LIVE_SABOTAGES`, `python/tests/cited_not_run.py` (cut 4's `W3[6]`)
- Test: `python/tests/test_identifier_correction.py` (new), `python/tests/test_arm_staleness.py`

**Interfaces:**
- Produces: `CorpusWriter._refuse_source(node, *, provenance: bool)`, `CorpusWriter._refuse_dataset_basis(node)`, `errors.SourceAddressDisagreement(WriteRefused)`.

- [ ] **Step 1: Add the error**

Append to `errors.py` after `IdentifierMalformed`; preserve the module's existing public-class export convention (it has no `__all__`):

```python
class SourceAddressDisagreement(WriteRefused):
    """A source's stored id is not the address its identifiers derive (slice 2b
    §5.1). The basis is present and canonical; the record simply lives at the
    wrong address, which is what a handle-addressed or hand-edited source is."""
```

- [ ] **Step 2: Write the failing boundary tests**

Create `python/tests/test_identifier_correction.py`:

```python
"""Slice 2b §5–§8: the source write boundary, the correction seam, its layers,
relocation and the read side."""

from __future__ import annotations

import pytest
from authority import ACTOR, FULL
from profiles import BASE
from test_corpus_write import Recorder
from test_source_address import A, ADDR_A, ADDR_B, B, CANONICAL_DOI, entry, raw_source

from beliefs import source, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    BasisMissing,
    IdentifierMalformed,
    SourceAddressDisagreement,
    ValidationRefused,
)
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp


@pytest.fixture()
def writer(request, tmp_path) -> CorpusWriter:
    Recorder.plans.clear()
    callspec = getattr(request.node, "callspec", None)
    root = tmp_path / callspec.id if callspec is not None else tmp_path
    return CorpusWriter(root / "corpus", Recorder, authority=FULL, profile=BASE)


class TestTheBoundary:
    def test_a_builder_source_is_admitted(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        assert writer.read_view.get(minted.id).id == ADDR_B

    def test_an_empty_basis_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(raw_source({}, node_id="source:handle"))

    def test_a_non_canonical_stored_value_refuses(self, writer):
        node = raw_source({"doi": "10.1234/ABC"}, node_id=source.source_address({"doi": "10.1234/ABC"}))
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "non-canonical"

    def test_an_unknown_scheme_beside_a_valid_doi_refuses(self, writer):
        node = raw_source({"doi": CANONICAL_DOI, "url": "x"}, node_id=ADDR_B)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "unknown-scheme"

    def test_a_handle_address_refuses(self, writer):
        with pytest.raises(SourceAddressDisagreement):
            writer.add(raw_source(B, node_id="source:Chen2023"))

    def test_add_refuses_a_history(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A]))

    def test_a_history_free_source_with_a_deprecated_id_refuses(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, deprecated=[ADDR_A]))

    def test_import_admits_a_well_formed_history_and_refuses_a_malformed_one(self, tmp_path):
        # `import_bundle` is a boundary operation: it needs an operation port, which this
        # module's `writer` fixture lacks. test_relocation._writer builds one with a recording port.
        from test_relocation import _writer

        from beliefs.errors import ImportRefused

        importer = _writer(tmp_path / "importer")
        report = {"observer": "o", "instrument": "i", "opened_at": "2026-09-10T00:00:00Z", "closed_at": "2026-09-10T00:00:01Z"}
        good = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        importer.import_bundle([good], **report)
        assert importer.read_view.get(ADDR_B).deprecated_ids == [ADDR_A]
        # The malformed member claims addresses nothing else holds, so the only refusal it can
        # meet is history validation — a BundleMemberHeld on a colliding deprecated id would
        # subclass ImportRefused and satisfy a looser assertion with the validation removed.
        eight, nine = {"pmid": "8"}, {"pmid": "9"}
        bad = raw_source(nine, history=[entry(eight, nine, grounds="")], deprecated=[source.source_address(eight)])
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle([bad], **report)
        assert type(caught.value) is ImportRefused and caught.value.member == bad.id
        assert "grounds" in str(caught.value)

    def test_a_dataset_without_content_identity_still_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(stored.dataset_node("d1", title="d", resources=[]))
```

- [ ] **Step 3: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py`
Expected: `test_a_handle_address_refuses`, `test_add_refuses_a_history`, `test_a_history_free_source_with_a_deprecated_id_refuses`, `test_a_non_canonical_stored_value_refuses` FAIL (no such refusals yet); the rest may already pass.

- [ ] **Step 4: Split the guard**

In `corpus.py` replace `_refuse_missing_basis` with:

```python
    def _refuse_source(self, node: Node, *, provenance: bool = False) -> None:
        """Slice 2b §5.1, in order: canonical identifiers (every entry), a
        basis, the derived address, a well-formed history, redirect agreement.
        `provenance` admits a history (import, relocation, the seam); an
        ordinary add refuses one — history is minted by `correct_identifier`."""
        if node.kind != "source":
            return
        facet = stored._facet(node, stored.SOURCE_FACET) or {}
        identifiers = facet.get("identifiers")
        if not isinstance(identifiers, dict):
            raise ValidationRefused(f"{node.id}: a source facet holds an `identifiers` mapping")
        canonical = source_basis_projection.normalized_identifiers(identifiers)  # IdentifierMalformed propagates
        for scheme, value in identifiers.items():
            if canonical[scheme] != value:
                raise IdentifierMalformed(
                    f"{node.id}: {scheme} identifier {value!r} is stored non-canonically",
                    scheme=scheme, value=value, reason="non-canonical",
                )
        address = stored.source_address_of(node)
        if address is None:
            raise BasisMissing(
                f"{node.id}: a source carries an accepted external identifier "
                f"({', '.join(stored.ACCEPTED_EXTERNAL_IDENTIFIERS)}); a curation note is its own explicit add, "
                "and no title-and-year fallback exists"
            )
        if node.id != address:
            raise SourceAddressDisagreement(f"{node.id}: the identifiers derive {address}")
        if stored.IDENTIFIER_CORRECTION_FACET in node.facets and not provenance:
            raise ValidationRefused(f"{node.id}: a correction history is minted by correct_identifier, never added")
        try:
            stored.validate_source_history(node)  # history and redirect agreement, one validator
        except MalformedRecord as caught:
            raise ValidationRefused(f"{node.id}: refused by document validation: {caught}") from caught

    def _refuse_dataset_basis(self, node: Node) -> None:
        """W3 as narrowed, the dataset half — unchanged in content."""
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:
            raise BasisMissing(
                f"{node.id}: a dataset carries a content identity — every declared resource pinned by an "
                "accepted digest. Supplying it later is a second, separate mint"
            )
```

In `_refuse`, replace `self._refuse_missing_basis(node)` with:

```python
        self._refuse_source(node, provenance=provenance)
        self._refuse_dataset_basis(node)
```

In `_preflight_replace_locked`, replace `self._refuse_missing_basis(node)` with:

```python
        self._refuse_source(node, provenance=True)
        self._refuse_dataset_basis(node)
```

(`_preflight_replace_locked` is reached only by `consolidate` and the seam, both provenance paths.) Add `IdentifierMalformed`, `SourceAddressDisagreement` to the `beliefs.errors` import block and `from beliefs import source as source_basis_projection` to the imports. Keep `_refuse_dataset_basis`'s `if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:` line byte-identical to the old one — cut 4's `W3[7]` matches it and must stay live-matching; the source clause it replaces (`W3[6]`) goes stale and is registered in `cited_not_run.py`'s `cut=4` entry:

```python
            "W3[6]": "moved at <sha>, when slice 2b split the basis guard into _refuse_source and _refuse_dataset_basis (2026-09-10)",
```

- [ ] **Step 5: Add the cut 16 live adapter**

Cut 16's `M3a` arm (`python/tests/n2_arms_cut16.py:197-208`) matches the two lines `self._refuse_family_kinds(node, admitted_kind=node.kind)\n        self._refuse_missing_basis(node)\n` in `_preflight_replace_locked` (confirm with `grep -n "_refuse_family_kinds(node, admitted_kind=node.kind)" python/src/beliefs/corpus.py`; the arm's `before` must occur exactly once). After the split, add to `test_n2_cut16.py::_LIVE_SABOTAGES` (keep the existing entries):

```python
    # Live source-boundary matcher migration, 2026-09-10 (slice 2b): the basis
    # guard split into _refuse_source and _refuse_dataset_basis; the table
    # stays frozen at b0882d3 and the arm asserts the same thing over the split lines.
    "M3a": Sabotage(
        module="corpus.py",
        before=(
            "        self._refuse_family_kinds(node, admitted_kind=node.kind)\n"
            "        self._refuse_source(node, provenance=True)\n"
        ),
        after=(
            "        self._refuse_family_kinds(node)\n"
            "        self._refuse_source(node, provenance=True)\n"
        ),
    ),
```

Verify with `grep -c` that the new `before` occurs exactly once in `corpus.py`.

- [ ] **Step 6: Run**

```
cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_corpus_write.py tests/test_import_bundle.py tests/test_relocation.py
uv run --frozen pytest tests/acceptance/test_n2_cut16.py -k "sabotage_names_one_real_source_site or M3a"
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py
```

Expected: all pass.

Ruled adjacent fixture migrations: the source move and destination-alias fixtures
enter through `import_bundle` with valid correction history, and assert no new
intent after setup. The locked replacement collision uses valid owned-to-target
history. The consolidate replacement-collision fixture uses `discussion`, whose
aliases remain governed by the generic collision boundary; a source cannot validly
claim an address already held in the same keep corpus. The durable W5 move fixture
likewise imports valid correction history.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests/test_identifier_correction.py python/tests/test_corpus_write.py python/tests/acceptance/test_n2_cut16.py python/tests/cited_not_run.py
git commit -m "feat(corpus): source write boundary checks the derived address and the history"
# then insert this commit's sha into cited_not_run.py's W3[6] entry and `git commit --amend --no-edit`
```

---

### Task 5: The read side — `validated_node` and the finding loop

**Files:**
- Modify: `python/src/beliefs/corpus.py:203-216` (`validated_node`), the finding loop (~1258-1263)
- Test: `python/tests/test_identifier_correction.py` (append)

**Interfaces:**
- Consumes: `stored.validate_source_history`, `errors.FacetPayloadRefused` (exists, subclass of `ValidationRefused`).

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_identifier_correction.py`:

```python
from fixtures_cut4 import raw_write
from nodes.core.errors import RefError

from beliefs.errors import FacetPayloadRefused


def raw_edit_history(writer, node_id, mutate):
    """Rewrite one stored source's file outside the boundary, as a forger would."""
    node = writer.read_view.get(node_id).model_copy(deep=True)
    mutate(node)
    raw_write(writer.root, node)
    writer._reconstruct()


class TestTheReadSide:
    def test_a_raw_edited_history_refuses_on_read(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))

        def mutate(node):
            node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": []}

        raw_edit_history(writer, minted.id, mutate)
        with pytest.raises(FacetPayloadRefused):
            writer.read_view.get(minted.id)

    def test_a_duplicated_deprecated_id_refuses_on_read(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=A))
        corrected = writer.correct_identifier(minted.id, B, grounds="g")  # Task 6's seam; run this test after it lands
        raw_edit_history(writer, corrected.id, lambda n: n.deprecated_ids.append(ADDR_A))  # [old] -> [old, old]
        with pytest.raises(FacetPayloadRefused):
            writer.read_view.get(corrected.id)

    def test_the_check_view_reports_facet_payload_malformed(self, writer):
        from beliefs.audit import check_corpus  # the audit entry the finding loop serves

        minted = writer.add(stored.source_node(title="p", identifiers=B))

        def mutate(node):
            node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [entry(A, B, grounds="")]}

        raw_edit_history(writer, minted.id, mutate)
        findings = check_corpus(writer.root, profile=BASE)
        assert any(f.code == "facet-payload-malformed" and f.ref == minted.id and f.detail == stored.IDENTIFIER_CORRECTION_FACET for f in findings)
```

Confirm the audit entry name by `grep -n "^def check" python/src/beliefs/audit.py` and use the function the existing `facet-payload-malformed` tests call (`grep -rn "facet-payload-malformed" python/tests | head`). Adjust the import and call to match.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py -k TheReadSide`
Expected: FAIL — the read returns the node; the finding list lacks the code.

- [ ] **Step 3: Wire the reader into both paths**

In `validated_node`, after the `semantic_hash_disagrees` check:

```python
    if node.kind == "source":
        try:
            stored.validate_source_history(node)
        except MalformedRecord as caught:
            raise FacetPayloadRefused(f"{node.id}: {stored.IDENTIFIER_CORRECTION_FACET}: {caught}") from caught
    return node
```

In the finding loop, immediately after the `for key, payload in node.facets.items(): ... validate_payload ...` block:

```python
        if node.kind == "source":
            try:
                stored.validate_source_history(node)
            except MalformedRecord as refused:
                base_valid = False
                findings.append(
                    Finding("error", "facet-payload-malformed", node.id, stored.IDENTIFIER_CORRECTION_FACET, str(refused))
                )
```

Add `FacetPayloadRefused` to the errors import if absent.

- [ ] **Step 4: Run, lint, commit**

```
cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_audit.py tests/test_world_view.py
uv run --frozen ruff check . && uv run --frozen pyright
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py
git add python/src/beliefs/corpus.py python/tests/test_identifier_correction.py
git commit -m "feat(corpus): read paths validate the identifier-correction history"
```

---

### Task 6: `CorpusWriter.correct_identifier`

**Files:**
- Modify: `python/src/beliefs/corpus.py` — new method after `attest_coreference` (~line 2236)
- Modify: `python/src/beliefs/errors.py` — `CorrectionRefused`
- Test: `python/tests/test_identifier_correction.py` (append)

**Interfaces:**
- Produces: `CorpusWriter.correct_identifier(ref: str, identifiers: Mapping[str, object], *, grounds: str) -> Node`; `errors.CorrectionRefused(message, *, reason)` with `REASONS = ("target-missing", "not-a-source", "grounds-empty", "unchanged")`.

- [ ] **Step 1: Add the error**

Append to `errors.py` after `SourceAddressDisagreement`; preserve the module's existing public-class export convention (it has no `__all__`):

```python
class CorrectionRefused(WriteRefused):
    """`correct_identifier` refused before any effect (slice 2b §6.1): one
    class, a closed reason. Identifier form refusals are `IdentifierMalformed`
    and an empty basis is `BasisMissing`; these are the seam's own."""

    REASONS = ("target-missing", "not-a-source", "grounds-empty", "unchanged")

    def __init__(self, message: str, *, reason: str) -> None:
        if reason not in self.REASONS:
            raise ValueError(f"{reason!r} is not a correction refusal reason")
        super().__init__(message)
        self.reason = reason
```

- [ ] **Step 2: Write the failing tests**

Append to `python/tests/test_identifier_correction.py`:

```python
from nodes.core.relations import Relation

from beliefs.errors import CollisionRefused, CorrectionRefused

C = {"pmid": "2"}
ADDR_C = source.source_address(C)


def minted_a(writer):
    return writer.add(stored.source_node(title="p", identifiers=A))


class TestTheSeamRefusals:
    def test_target_missing(self, writer):
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier("source:nowhere", B, grounds="g")
        assert caught.value.reason == "target-missing"

    def test_not_a_source(self, writer):
        d = writer.add(stored.dataset_node("d", title="d", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]))
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(d.id, B, grounds="g")
        assert caught.value.reason == "not-a-source"

    def test_a_raw_edited_subject_refuses_before_append(self, writer):
        # The one edit only the boundary catches: identifiers moved under the stored id with the
        # stamp recomputed — validated_node's stamp and history checks both pass, and without the
        # pre-append _refuse_source the seam would build a successor whose history never held the
        # stored address, dropping it from the redirect set.
        minted = minted_a(writer)

        def move_identifiers(node):
            node.facets[stored.SOURCE_FACET]["identifiers"] = dict(C)
            stored.stamp_semantic_identity(node)

        raw_edit_history(writer, minted.id, move_identifiers)
        assert writer.read_view.get(minted.id).id == minted.id  # readable: the read path does not catch it
        with pytest.raises(SourceAddressDisagreement):
            writer.correct_identifier(minted.id, B, grounds="g")

    def test_malformed_supplied_identifiers(self, writer):
        minted = minted_a(writer)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.correct_identifier(minted.id, {"doi": "10.1/x"}, grounds="g")
        assert caught.value.reason == "malformed"

    def test_non_canonical_supplied_map_refuses_before_unchanged(self, writer):
        minted = minted_a(writer)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.correct_identifier(minted.id, {"pmid": "PMID:1"}, grounds="g")
        assert caught.value.reason == "non-canonical"

    def test_empty_map(self, writer):
        minted = minted_a(writer)
        with pytest.raises(BasisMissing):
            writer.correct_identifier(minted.id, {}, grounds="g")

    @pytest.mark.parametrize("grounds", ["", "\udcff"])
    def test_grounds_empty_or_unencodable(self, writer, grounds):
        minted = minted_a(writer)
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(minted.id, B, grounds=grounds)
        assert caught.value.reason == "grounds-empty"

    def test_unchanged(self, writer):
        minted = minted_a(writer)
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(minted.id, A, grounds="g")
        assert caught.value.reason == "unchanged"

    def test_collision_with_another_records_address(self, writer):
        minted = minted_a(writer)
        writer.add(stored.source_node(title="other", identifiers=C))
        with pytest.raises(CollisionRefused):
            writer.correct_identifier(minted.id, C, grounds="g")

    def test_collision_with_another_records_retired_address(self, writer):
        minted = minted_a(writer)
        other = writer.add(stored.source_node(title="other", identifiers=C))
        writer.correct_identifier(other.id, {"pmid": "3"}, grounds="g")  # C is now other's retired address
        with pytest.raises(CollisionRefused):
            writer.correct_identifier(minted.id, C, grounds="g")

    def test_every_refusal_has_no_effect(self, writer):
        minted = minted_a(writer)
        before = len(Recorder.plans)
        for call in (
            lambda: writer.correct_identifier("source:nowhere", B, grounds="g"),
            lambda: writer.correct_identifier(minted.id, A, grounds="g"),
            lambda: writer.correct_identifier(minted.id, B, grounds=""),
        ):
            with pytest.raises(Exception):
                call()
        assert len(Recorder.plans) == before
        assert writer.read_view.get(minted.id).model_dump() == minted.model_dump()


class TestTheSeamEffects:
    def test_moved_creates_and_deletes_preserving_uid(self, writer):
        minted = minted_a(writer)
        corrected = writer.correct_identifier(minted.id, B, grounds="checked the PDF")
        plan = Recorder.plans[-1]
        assert [type(op) for op in plan] == [CreateOp, DeleteOp]
        assert corrected.uid == minted.uid and corrected.id == ADDR_B
        assert corrected.deprecated_ids == [ADDR_A]
        (correction,) = stored.identifier_corrections(corrected)
        assert (dict(correction.from_identifiers), dict(correction.to_identifiers), correction.actor, correction.grounds) == (A, B, ACTOR, "checked the PDF")
        assert writer.read_view.resolve(ADDR_A) == ADDR_B
        assert writer.read_view.get(ADDR_B).facets == corrected.facets

    def test_unmoved_replaces_in_place(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        corrected = writer.correct_identifier(minted.id, {**B, "isbn": "9780306406157"}, grounds="g")
        assert [type(op) for op in Recorder.plans[-1]] == [ReplaceOp]
        assert corrected.id == minted.id and corrected.deprecated_ids == []
        assert len(stored.identifier_corrections(corrected)) == 1

    def test_removing_the_selected_identifier_moves_the_address(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        corrected = writer.correct_identifier(minted.id, A, grounds="the DOI was another paper's")
        assert corrected.id == ADDR_A and corrected.deprecated_ids == [ADDR_B]

    def test_a_return_makes_the_old_address_live_again(self, writer):
        minted = minted_a(writer)
        writer.correct_identifier(minted.id, B, grounds="g1")
        back = writer.correct_identifier(ADDR_B, A, grounds="g2")
        assert back.id == ADDR_A and back.uid == minted.uid
        assert back.deprecated_ids == [ADDR_B]
        assert [c.event_token for c in stored.identifier_corrections(back)] and len(stored.identifier_corrections(back)) == 2
        assert writer.read_view.resolve(ADDR_B) == ADDR_A

    def test_a_deprecated_ref_names_the_live_subject(self, writer):
        minted = minted_a(writer)
        writer.correct_identifier(minted.id, B, grounds="g")
        corrected = writer.correct_identifier(ADDR_A, C, grounds="g")
        assert corrected.id == ADDR_C and sorted(corrected.deprecated_ids) == sorted([ADDR_A, ADDR_B])

    def test_referrers_are_byte_unchanged(self, writer):
        # A retraction's `grounded-in` edge is the reference a record may hold to a source
        # (a source is not an eligible retraction NodeTarget). No source-assertion builder exists.
        from test_retract import content_identity, mint_eligible_assessment

        minted = minted_a(writer)
        assessment = mint_eligible_assessment(writer)
        # The id is content-derived over the grounds, so the grounds are supplied at build time;
        # mutating a built retraction leaves its id stale and _validated_retraction refuses it.
        retraction = stored.retraction_node(
            title="retraction",
            target=stored.NodeTarget(assessment.id, assessment.id, content_identity(assessment)),
            reason="defective-code",
            rationale="the recorded result is invalid",
            grounds=(minted.id,),
            actor=ACTOR,
            event_token="event-1",
        )
        writer.retract(retraction)
        files_before = {p: p.read_bytes() for p in (writer.root / "retraction").glob("*.md")}
        writer.correct_identifier(minted.id, B, grounds="g")
        assert {p: p.read_bytes() for p in (writer.root / "retraction").glob("*.md")} == files_before
        assert writer.read_view.resolve(minted.id) == ADDR_B
        assert writer.read_view.inbound(ADDR_B) == writer.read_view.inbound(minted.id)
```

`test_retract.retraction_for` hard-codes `grounds=("verification:v1",)`, so the test builds its own retraction naming the source; `content_identity` is `test_retract`'s helper. The retraction is the referrer; its file bytes must not change, and the old address must still resolve.

- [ ] **Step 3: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py -k "Seam"`
Expected: FAIL — `AttributeError: 'CorpusWriter' object has no attribute 'correct_identifier'`.

- [ ] **Step 4: Implement the seam**

Add to `CorpusWriter` after `attest_coreference`:

```python
    def correct_identifier(self, ref: str, identifiers: Mapping[str, object], *, grounds: str) -> Node:
        """Change a source's identifiers under one attributed assertion — "same
        work; the removed identifiers were erroneous" (slice 2b §6). The
        address moves iff the selected basis changes; the old address is
        retained in `deprecated_ids`; `uid` is preserved; no referrer is read
        or rewritten. One executor submission."""
        self._authority.require("corpus-write", ("source",))
        with self._operation:
            self._require_pins_agree()
            live = self._view.resolve(ref)
            if live is None:
                raise CorrectionRefused(f"{ref!r}: no record resolves in this corpus", reason="target-missing")
            subject = self._view.get(live)
            if subject.kind != "source":
                raise CorrectionRefused(f"{subject.id}: correct_identifier operates on sources only", reason="not-a-source")
            self._refuse_source(subject, provenance=True)
            canonical = source_basis_projection.normalized_identifiers(identifiers)
            for scheme, value in identifiers.items():
                if canonical[scheme] != value:
                    raise IdentifierMalformed(
                        f"{subject.id}: {scheme} identifier {value!r} is not canonical; the seam does not normalize",
                        scheme=scheme, value=value, reason="non-canonical",
                    )
            if not canonical:
                raise BasisMissing(f"{subject.id}: a correction supplies at least one accepted external identifier")
            if type(grounds) is not str or not grounds:
                raise CorrectionRefused(f"{subject.id}: grounds are a non-empty string", reason="grounds-empty")
            try:
                v1.encode(grounds)
            except LoneSurrogate as caught:
                raise CorrectionRefused(f"{subject.id}: grounds are not canonically encodable", reason="grounds-empty") from caught
            current = dict(subject.facets[stored.SOURCE_FACET]["identifiers"])
            if canonical == current:
                raise CorrectionRefused(f"{subject.id}: the supplied identifiers equal the current ones", reason="unchanged")

            successor = subject.model_copy(deep=True)
            successor.facets[stored.SOURCE_FACET]["identifiers"] = canonical
            history = successor.facets.setdefault(stored.IDENTIFIER_CORRECTION_FACET, {"entries": []})
            history["entries"].append(
                {
                    "from": current,
                    "to": dict(canonical),
                    "actor": self._authority.actor,
                    "grounds": grounds,
                    "event_token": secrets.token_hex(16),
                }
            )
            new_address = stored.source_address_of(successor)
            assert new_address is not None
            successor.id = new_address
            # Derive the redirect set first; the completed successor is validated below through the
            # one validator, which requires deprecated_ids to be exactly this.
            held = stored.held_source_addresses(stored.identifier_corrections(successor))
            successor.deprecated_ids = sorted(held - {new_address})
            stored.stamp_semantic_identity(successor)

            self._refuse_invalid(successor)
            self._refuse_facets(successor, provenance=True)
            self._refuse_source(successor, provenance=True)
            self._refuse_governed_stamp(successor)
            content = self._refuse_rendering(successor)
            holder = self._corpus.index.resolve_uid(new_address)
            if holder is not None and holder != subject.uid:
                raise CollisionRefused(f"{new_address} is held by another record ({holder})")

            old_path = self._relative_path(subject)
            new_path = self._relative_path(successor)
            expected = self._corpus.manifest[old_path].sha256
            plan: list[CreateOp | DeleteOp | ReplaceOp]
            if new_path != old_path:
                plan = [CreateOp(path=new_path, content=content), DeleteOp(path=old_path, expected_digest=expected)]
            else:
                plan = [ReplaceOp(path=new_path, content=content, expected_digest=expected)]
            self._corpus.executor.execute(plan)
            self._reconstruct()
            return self._view.get(new_address)
```

Add `ReplaceOp` to the `nodes.core.write_plan` import and `CorrectionRefused`, `LoneSurrogate` to the errors import (check `LoneSurrogate` is imported; `v1` is). Note `_refuse_rendering` returns the rendered bytes — that is the content written, so the file is exactly the losslessly re-parsed form.

- [ ] **Step 5: Run, lint, commit**

```
cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_arm_staleness.py tests/test_frozen_guards.py
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests/test_identifier_correction.py
git commit -m "feat(corpus): correct_identifier renames a source through deprecated_ids with an attributed history"
```

---

### Task 7: The session layers

**Files:**
- Modify: `python/src/beliefs/corpus.py` — `OperationWrites` (~line 2901)
- Modify: `python/src/beliefs/session/writer.py` — `ScopedWriter` (~line 376)
- Modify: `docs/designs/2026-09-05-writer-session-design.md` — dated note: nine session-mediated writes
- Test: `python/tests/test_identifier_correction.py` (append)

- [ ] **Step 1: Write the failing tests**

Append:

```python
from test_session_writer import DIGEST, make_session

from beliefs.permit import RequiredCapabilities
from beliefs.session.writer import ScopedWriter

SOURCES = RequiredCapabilities.for_kinds({"source"}, {})


class TestTheSessionLayers:
    def test_the_scoped_writer_commits_one_corpus_write_and_ledgers_an_act(self, tmp_path):
        session, ports = make_session(tmp_path)
        scoped = session.scoped(SOURCES, "A")
        session.claim_invocation("A", "mint", DIGEST)
        minted = scoped.add(stored.source_node(title="p", identifiers=A))
        corrected = scoped.correct_identifier(minted.id, B, grounds="g")
        assert corrected.id == ADDR_B and corrected.uid == minted.uid
        acts = session.invocation_acts("A")
        assert len(acts) == 2 and acts[-1].record_ids == ((corrected.uid, corrected.id),)
        # One corpus-write intent per act, minting no act-report.
        (port,) = ports
        assert [intent.kind for intent in port.intents][-1] == "corpus-write"
        assert not any(n.kind == "act-report" for n in port.writer.read_view.iter_stored())

    def test_the_facade_exposes_nine_methods(self):
        public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
        assert "correct_identifier" in public
```

`make_session` returns `(session, ports)` where each `RecordingPort` records the intents it appended; read `tests/test_session_writer.py::RecordingPort` for the attribute that holds them (`intents` above) and the writer it was built for, and adjust the two attribute names to match. `tests/test_session_writer.py::test_the_scoped_writer_exposes_the_eight_methods_the_routes_and_its_invocation` pins the public set — add `"correct_identifier"` to that set and rename the test to `..._nine_methods_...` in this task.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py -k SessionLayers`
Expected: FAIL — `AttributeError: ... has no attribute 'correct_identifier'`.

- [ ] **Step 3: Add the two layers**

In `OperationWrites` after `attest_coreference`:

```python
    def correct_identifier(self, ref: str, identifiers: Mapping[str, object], *, grounds: str) -> OperationCommit:
        return self._run(lambda: self._writer.correct_identifier(ref, identifiers, grounds=grounds))
```

In `ScopedWriter` after `attest_coreference`:

```python
    def correct_identifier(self, ref: str, identifiers: Mapping[str, object], *, grounds: str) -> Node:
        minted = self._act(lambda: self._writer.operations.correct_identifier(ref, identifiers, grounds=grounds))
        assert minted is not None
        return minted
```

Update `OperationWrites`'s docstring: "The nine session-mediated writes". In `docs/designs/2026-09-05-writer-session-design.md`, at §4.2's enumeration of the writes, add a dated blockquote:

```markdown
> **Amended 2026-09-10 (slice 2b):** the session-mediated writes number
> **nine** — `correct_identifier` joins them as an ordinary `corpus-write`,
> one intent and one registration, minting no act-report
> (`2026-09-10-world-resolution-slice-2b-design.md` §6).
```

Check for a test pinning "eight" (`grep -rn "eight" python/tests/test_session_writer.py python/tests/acceptance/test_session_acceptance.py`) and update its count.

- [ ] **Step 4: Run, lint, commit**

```
cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_session_writer.py
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/corpus.py python/src/beliefs/session/writer.py docs/designs/2026-09-05-writer-session-design.md python/tests
git commit -m "feat(session): correct_identifier through OperationWrites and ScopedWriter"
```

---

### Task 8: Relocation — `move` carries history, `consolidate` refuses divergence

**Files:**
- Modify: `python/src/beliefs/relocation.py::consolidate` (~line 214, after `AddressDisagreement`)
- Modify: `python/src/beliefs/errors.py` — `HistoryDisagreement`
- Test: `python/tests/test_identifier_correction.py` (append)

- [ ] **Step 1: Add the error**

After `AddressDisagreement` in `errors.py`; preserve the module's existing public-class export convention (it has no `__all__`):

```python
class HistoryDisagreement(RelocationRefused):
    """`consolidate` was given two sources at one address whose identifier maps
    or correction histories differ (slice 2b §7). Reconciling them is a design
    this slice refuses to improvise; the survivor's history must not silently win."""
```

- [ ] **Step 2: Write the failing tests**

Append. `tests/test_relocation.py::_writer` builds a `CorpusWriter` with an `OperationRecorder` port and an adopted manifest; import it and define the pair fixture here:

```python
from test_relocation import _writer


@pytest.fixture()
def two_writers(tmp_path):
    return _writer(tmp_path / "left"), _writer(tmp_path / "right")
```

`_writer` with no `domains` uses the `BASE` profile, which is what every other test in this file uses. Then:

```python
from beliefs.errors import HistoryDisagreement
from beliefs.relocation import consolidate, move

REPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-10T00:00:00Z", "closed_at": "2026-09-10T00:00:01Z"}


class TestRelocation:
    def test_move_carries_history_and_deprecated_ids(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(minted.id, B, grounds="g")
        moved, *_ = move(left, right, corrected.id, **REPORT)
        arrived = right.read_view.get(ADDR_B)
        assert arrived.deprecated_ids == [ADDR_A] and len(stored.identifier_corrections(arrived)) == 1
        assert right.read_view.resolve(ADDR_A) == ADDR_B

    def test_consolidate_identical_histories(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for w in (left, right):
            w.add(node.model_copy(deep=True))
        # Same correction on both replicas: bind both writers to one actor and apply the same call.
        for w in (left, right):
            w.correct_identifier(ADDR_A, B, grounds="g")
        # The two histories differ by event token; consolidate must refuse — see the next test.

    def test_consolidate_refuses_divergent_histories(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for w in (left, right):
            w.add(node.model_copy(deep=True))
            w.correct_identifier(ADDR_A, B, grounds="g")  # two tokens, two histories
        with pytest.raises(HistoryDisagreement):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)

    def test_consolidate_refuses_divergent_maps(self, two_writers):
        left, right = two_writers
        left.add(stored.source_node(title="p", identifiers=B))
        right.add(stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))  # same basis, different map
        with pytest.raises(HistoryDisagreement):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)

    def test_consolidate_refuses_a_handle_addressed_replica_at_replace(self, two_writers):
        # Only _preflight_replace_locked's _refuse_source catches this: both replicas were raw-written
        # at a handle address with a valid stamp and no history, so every read passes and consolidate's
        # own map/history comparison finds them identical.
        left, right = two_writers
        forged = raw_source(B, node_id="source:Chen2023")
        for w in (left, right):
            raw_write(w.root, forged)
            w._reconstruct()
        with pytest.raises(SourceAddressDisagreement):
            consolidate((left, forged.id), (right, forged.id), rationale="r", **REPORT)

    def test_consolidate_accepts_byte_identical_replicas(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(minted.id, B, grounds="g")
        right.import_bundle([corrected], **REPORT)  # a replica with the same history
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert survivor.deprecated_ids == [ADDR_A] and len(stored.identifier_corrections(survivor)) == 1
```

Delete `test_consolidate_identical_histories` (its body is a note, not a test) before running; the byte-identical case is the last test.

- [ ] **Step 3: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py -k Relocation`
Expected: the two `refuses` tests FAIL (consolidate succeeds); the others pass or fail on fixture names to be aligned.

- [ ] **Step 4: Implement the refusal**

In `consolidate`, after the `AddressDisagreement` check:

```python
        if keep_node.kind == "source":
            keep_map = keep_node.facets[stored.SOURCE_FACET]["identifiers"]
            other_map = other_node.facets[stored.SOURCE_FACET]["identifiers"]
            if keep_map != other_map:
                raise HistoryDisagreement(f"{keep_node.id}: the two replicas carry different identifier maps")
            if keep_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET) != other_node.facets.get(
                stored.IDENTIFIER_CORRECTION_FACET
            ):
                raise HistoryDisagreement(f"{keep_node.id}: the two replicas carry different correction histories")
```

Import `HistoryDisagreement`.

- [ ] **Step 5: Run, lint, commit**

```
cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_relocation.py
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/relocation.py python/src/beliefs/errors.py python/tests/test_identifier_correction.py
git commit -m "feat(relocation): consolidate refuses sources with divergent identifier histories"
```

---

### Task 9: Acceptance — W1, W2, W5a, the failure boundary, lifecycle

**Files:**
- Create: `python/tests/acceptance/test_source_address_acceptance.py`

**Interfaces:**
- Consumes: `open_corpus`/`init_corpus_root`/`init_world_root`/`open_world` from `beliefs.root`; `publish`/`hold_shipped` from `tests/test_world_receipts.py`; `open_world_view` from `beliefs.world.view`; `adopted`, `fresh`, `halting_session`, `chain`, `pending_registrations`, `state_of`, `registrations`, `config_for` from `tests/acceptance/test_session_acceptance.py` (read that module first: `fresh(session, invocation, required)` claims the invocation; `adopted` pins `WITH_BIOLOGY`); `PUBLISH_CALLS_BEFORE_RECORD` from `tests/acceptance/session_faults.py`; `mint_eligible_assessment`, `content_identity` from `tests/test_retract.py`.

- [ ] **Step 1: Write the arms**

```python
"""Cut 25 — source addresses derived from the normalized identifier (W1, W2, W5a)."""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import ACTOR, FULL
from nodes.core.errors import ExecutionError
from profiles import BASE, WITH_BIOLOGY, pins_for
from session_faults import PUBLISH_CALLS_BEFORE_RECORD
from test_retract import content_identity, mint_eligible_assessment
from test_session_acceptance import (
    adopted,
    chain,
    config_for,
    fresh,
    halting_session,
    pending_registrations,
    registrations,
    state_of,
)
from test_world_receipts import hold_shipped, publish

from beliefs import source, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    AddressMapConflict,
    CollisionRefused,
    CorrectionRefused,
    HistoryDisagreement,
    RecordAlreadyMinted,
    ReviseOutsideAllowlist,
)
from beliefs.permit import RequiredCapabilities
from beliefs.relocation import consolidate, move
from beliefs.root import init_corpus_root, init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.session.reconcile import reconcile_sessions
from beliefs.world import Fresh, WorldConfig
from beliefs.world.read import Unknown
from beliefs.world.view import open_world_view

REPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-10T00:00:00Z", "closed_at": "2026-09-10T00:00:01Z"}
SOURCES = RequiredCapabilities.for_kinds({"source", "dataset", "run", "proposition", "assessment", "retraction"}, {})
PAIRS = (
    ("Chen2023", "10.1234/chen.a", "10.5678/chen.b"),
    ("Liu2020", "10.1234/liu.a", "10.5678/liu.b"),
    ("Shi2025", "10.1234/shi.a", "10.5678/shi.b"),
)


@pytest.fixture()
def world(work_directory):
    """Two durable corpora and a world root; the caller populates and publishes."""
    roots = []

    def corpus():
        path = Path(mkdtemp(prefix="cut25-corpus-", dir=work_directory))
        roots.append(path)
        init_corpus_root(path, authority=FULL)
        writer = open_corpus(path, authority=FULL, profile=BASE)
        manifest = writer.adopt_manifest(profile=pins_for(BASE))
        return manifest.corpus_id, path, writer

    a, alpha, left = corpus()
    b, beta, right = corpus()
    path = Path(mkdtemp(prefix="cut25-world-", dir=work_directory))
    roots.append(path)
    config = WorldConfig(path, "e" * 32, (alpha, beta))
    init_world_root(config, authority=FULL)
    registry = open_world(config, authority=FULL)
    registry.admit(alpha, provenance=Fresh())
    registry.admit(beta, provenance=Fresh())
    try:
        yield registry, (a, left), (b, right)
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def test_w1_distinct_bases_never_become_one_node(world):
    registry, (a, left), (b, right) = world
    for citekey, first, second in PAIRS:
        left.add(stored.source_node(title=citekey, identifiers={"doi": first}))
        right.add(stored.source_node(title=citekey, identifiers={"doi": second}))
    addresses = {n.id for w in (left, right) for n in w.read_view.iter_stored() if n.kind == "source"}
    assert len(addresses) == 6
    assert left.read_view.resolve("source:Chen2023") is None
    published = publish(registry, (a, b), hold_shipped(registry))
    view = open_world_view(registry, published)
    assert isinstance(view.locate("source:Chen2023"), Unknown) and view.resolve("source:Chen2023") is None
    assert all(view.resolve(address) == address for address in addresses)


def test_w2_a_shared_basis_is_one_address(world):
    registry, (a, left), (b, right) = world
    one = left.add(stored.source_node(title="x", identifiers={"doi": "10.1234/ABC"}))
    two = stored.source_node(title="y", identifiers={"doi": "https://doi.org/10.1234/abc"})
    assert one.id == two.id
    with pytest.raises(CollisionRefused):
        left.add(two)  # fresh uid, held address
    with pytest.raises(RecordAlreadyMinted):
        left.add(one)  # same (uid, id)
    right.add(two)
    with pytest.raises(AddressMapConflict) as caught:
        publish(registry, (a, b), hold_shipped(registry))
    assert caught.value.finding.code == "duplicate-location"
    consolidate((left, one.id), (right, two.id), rationale="one paper", **REPORT)
    published = publish(registry, (a, b), hold_shipped(registry))
    assert open_world_view(registry, published).corpus_of(one.id) == a
    # Negative: a shared secondary identifier infers nothing.
    p = left.add(stored.source_node(title="p", identifiers={"pmid": "77"}))
    dp = right.add(stored.source_node(title="dp", identifiers={"doi": "10.1234/dp", "pmid": "77"}))
    assert p.id != dp.id
    publish(registry, (a, b), hold_shipped(registry))


def test_w5a_dataset_arm_a_rehold_is_a_new_entity(world):
    _, (_, left), _ = world
    assessment = mint_eligible_assessment(left)  # observes dataset:raw through run:r1
    d = left.read_view.get("dataset:raw")
    changed = d.model_copy(deep=True)
    changed.facets[stored.DATASET_FACET]["resources"] = [{"name": "d", "digest": "sha256:" + "9" * 64}]
    stored.stamp_semantic_identity(changed)
    with pytest.raises(ReviseOutsideAllowlist):
        left.revise(changed)
    reheld = left.add(
        stored.dataset_node("raw-reheld", title="raw", resources=[{"name": "d", "digest": "sha256:" + "9" * 64}])
    )
    assert reheld.id != d.id and stored.dataset_declaration(reheld) != stored.dataset_declaration(d)
    run = left.read_view.get("run:r1")  # mint_eligible_assessment's run; AssessmentValue.run is the closure address, not the id
    assert [e.target for e in left.read_view.outbound(assessment.id) if e.predicate == stored.PRODUCED_BY] == [run.id]
    observed = [r.target for r in run.relations if r.predicate == stored.OBSERVES]
    assert observed == [d.id] and reheld.id not in observed
    assert left.read_view.get(d.id).facets[stored.DATASET_FACET] == d.facets[stored.DATASET_FACET]


def test_w5a_source_arm_rename_preserves_uid_and_redirects(world):
    registry, (a, left), (b, right) = world
    paper = left.add(stored.source_node(title="p", identifiers={"doi": "10.1234/wrong"}))
    # The referrer: a retraction grounded in the source (a source is not a retraction NodeTarget).
    assessment = mint_eligible_assessment(left)
    retraction = stored.retraction_node(  # grounds supplied at build: the id is content-derived over them
        title="retraction",
        target=stored.NodeTarget(assessment.id, assessment.id, content_identity(assessment)),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=(paper.id,),
        actor=ACTOR,
        event_token="event-1",
    )
    minted = left.retract(retraction)
    referrer_bytes = (left.root / "retraction" / f"{minted.id.partition(':')[2]}.md").read_bytes()

    corrected = left.correct_identifier(paper.id, {"doi": "10.1234/right"}, grounds="the PDF's DOI")
    assert corrected.uid == paper.uid and corrected.deprecated_ids == [paper.id]
    (correction,) = stored.identifier_corrections(corrected)
    assert correction.actor == ACTOR and correction.grounds == "the PDF's DOI"
    assert left.read_view.resolve(paper.id) == corrected.id
    assert (left.root / "retraction" / f"{minted.id.partition(':')[2]}.md").read_bytes() == referrer_bytes
    assert [e.target for e in left.read_view.outbound(minted.id) if e.predicate == stored.GROUNDED_IN] == [paper.id]
    published = publish(registry, (a, b), hold_shipped(registry))
    view = open_world_view(registry, published)
    assert view.resolve(paper.id) == corrected.id

    # Negative — three arms, three calls, no chooser.
    assert "case" not in inspect.signature(left.correct_identifier).parameters
    other = left.add(stored.source_node(title="p2", identifiers={"doi": "10.1234/another"}))  # arm 2: a new work
    assert other.uid != corrected.uid
    attestation = stored.coreference_attestation_node(  # arm 3: two identifiers legitimately exist
        title="same paper", endpoints=(corrected.id, other.id), stance=1, actor=ACTOR, grounds="the same PDF", event_token="e1"
    )
    left.attest_coreference(attestation)
    assert left.read_view.get(corrected.id).id == corrected.id and left.read_view.get(other.id).id == other.id
    assert left.read_view.get(other.id).deprecated_ids == [] and left.read_view.get(corrected.id).deprecated_ids == [paper.id]


def _halt_at(session, backend, root, skip, subject, target):
    """Arm the halting backend at publish `skip`, run one correction of `subject`
    to `target`, and return the file state observed at the halt as
    `(old_exists, new_exists)`; then disarm and settle through an unrelated add."""
    old_path = root / "source" / f"{subject.id.partition(':')[2]}.md"
    new_path = root / "source" / f"{source.source_address(target).partition(':')[2]}.md"
    backend.skip = skip
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        fresh(session, f"halt-{skip}", SOURCES).correct_identifier(subject.id, target, grounds="g")
    assert backend.halted and state_of(root).unresolved is True
    observed = (old_path.exists(), new_path.exists())
    backend.disarm()
    fresh(session, f"settle-{skip}", SOURCES).add(stored.source_node(title="settle", identifiers={"pmid": str(1000 + skip)}))
    assert state_of(root).unresolved is False
    return observed


@pytest.fixture()
def correction_halt_positions(work_directory) -> tuple[int, int]:
    """Derive the injection positions for the requesting test: sweep
    the halt over the two-op transaction's publish sequence and read the file
    state at each halt. The positions are derived from what was observed, never
    from the single-record count, and the sweep must show the create completing
    before the delete begins."""
    root = adopted(work_directory, "cut25-sweep")
    session, backend, _ops = halting_session(work_directory, root)
    w = fresh(session, "warm", SOURCES)
    w.add(stored.source_node(title="warm", identifiers={"pmid": "99"}))  # the kind directory exists
    observed: list[tuple[int, tuple[bool, bool]]] = []
    for skip in range(PUBLISH_CALLS_BEFORE_RECORD, PUBLISH_CALLS_BEFORE_RECORD + 4):
        subject = w.add(stored.source_node(title="s", identifiers={"pmid": str(10 + skip)}))
        target = {"doi": f"10.1234/s{skip}", "pmid": str(10 + skip)}
        observed.append((skip, _halt_at(session, backend, root, skip, subject, target)))
    states = [state for _, state in observed]
    assert (True, False) in states and (True, True) in states, observed
    assert states.index((True, False)) < states.index((True, True)), observed
    assert (False, False) not in states, observed  # the delete never lands before the create
    halt_before_create = observed[states.index((True, False))][0]
    halt_between = observed[states.index((True, True))][0]
    session.close()
    return halt_before_create, halt_between


def test_failure_boundary_refusals_and_applied_prefixes(work_directory, monkeypatch, correction_halt_positions):
    """Spec §10.3: a refusal has no effect; a halt after submission leaves a stated
    prefix and the root unresolved; a post-commit readback fault leaves the record
    durable; settlement leaves exactly one record with the subject's uid."""
    halt_before_create, halt_between = correction_halt_positions
    root = adopted(work_directory, "cut25-halt")
    session, backend, ops = halting_session(work_directory, root)
    w = fresh(session, "A", SOURCES)
    w.add(stored.source_node(title="warm", identifiers={"pmid": "99"}))  # the kind directory exists
    paper = w.add(stored.source_node(title="p", identifiers={"pmid": "1"}))
    target = {"doi": "10.1234/one", "pmid": "1"}
    old_path = root / "source" / f"{paper.id.partition(':')[2]}.md"
    new_path = root / "source" / f"{source.source_address(target).partition(':')[2]}.md"

    # 1. Refusal: no intent, no effect.
    before = len(chain(root).entries)
    with pytest.raises(CorrectionRefused):
        w.correct_identifier(paper.id, {"pmid": "1"}, grounds="g")
    assert len(chain(root).entries) == before and old_path.exists() and not new_path.exists()

    # 2. Halt before the create's publish (position derived by the requested sweep fixture):
    #    nothing published, the intent stands, reconciliation classifies it.
    backend.skip = halt_before_create
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        w.correct_identifier(paper.id, target, grounds="g")
    assert backend.halted and pending_registrations(root) and state_of(root).unresolved is True
    assert (old_path.exists(), new_path.exists()) == (True, False), "create halted: nothing published"
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert any(f.code in ("session-outcome-unknown", "session-entry-pending") for f in findings)
    backend.disarm()
    fresh(session, "B", SOURCES).add(stored.source_node(title="q", identifiers={"pmid": "2"}))  # settles first
    assert not pending_registrations(root) and state_of(root).unresolved is False
    assert (old_path.exists(), new_path.exists()) == (True, False), "rolled back: the subject stands at its old address"

    # 3. Halt between the create and the delete (the sweep's (True, True) position): the create
    #    completed and the delete did not; settlement resolves the pair to exactly one record.
    backend.skip = halt_between
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        fresh(session, "C", SOURCES).correct_identifier(paper.id, target, grounds="g")
    assert backend.halted and state_of(root).unresolved is True
    assert (old_path.exists(), new_path.exists()) == (True, True), "create completed, delete pending"
    backend.disarm()
    fresh(session, "D", SOURCES).add(stored.source_node(title="r", identifiers={"pmid": "3"}))
    assert state_of(root).unresolved is False
    assert old_path.exists() != new_path.exists(), "settlement leaves one file, never both"
    reader = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    holders = [n for n in reader.read_view.iter_stored() if n.uid == paper.uid]
    assert len(holders) == 1
    stored.validate_source_history(holders[0])

    # 4. Post-commit readback fault: the plan committed, the registration stands, the view is not rebuilt.
    subject = holders[0]
    next_target = {**subject.facets[stored.SOURCE_FACET]["identifiers"], "isbn": "9780306406157"}
    monkeypatch.setattr(
        CorpusWriter, "_reconstruct", lambda self: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None))
    )
    with pytest.raises(ExecutionError):
        fresh(session, "E", SOURCES).correct_identifier(subject.id, next_target, grounds="g")
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    assert any(e.fulfills is not None for e in registrations(root))
    fresh(session, "F", SOURCES).add(stored.source_node(title="s", identifiers={"pmid": "4"}))
    reader = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    holders = [n for n in reader.read_view.iter_stored() if n.uid == paper.uid]
    assert len(holders) == 1 and holders[0].facets[stored.SOURCE_FACET]["identifiers"] == next_target
    stored.validate_source_history(holders[0])
    session.close()


def test_lifecycle_move_consolidate_delete(world):
    registry, (a, left), (b, right) = world
    paper = left.add(stored.source_node(title="p", identifiers={"pmid": "5"}))
    corrected = left.correct_identifier(paper.id, {"doi": "10.1234/five", "pmid": "5"}, grounds="g")
    moved, *_ = move(left, right, corrected.id, **REPORT)
    assert right.read_view.get(moved.id).deprecated_ids == [paper.id]
    assert right.read_view.resolve(paper.id) == moved.id
    left.import_bundle([right.read_view.get(moved.id)], **REPORT)  # a byte-identical replica
    survivor, *_ = consolidate((left, moved.id), (right, moved.id), rationale="r", **REPORT)
    assert survivor.deprecated_ids == [paper.id] and len(stored.identifier_corrections(survivor)) == 1
    other = right.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    right.correct_identifier(other.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g1")
    twin = left.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    left.correct_identifier(twin.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g2")  # another token: divergent
    with pytest.raises(HistoryDisagreement):
        consolidate((left, source.source_address({"doi": "10.1234/six"})), (right, source.source_address({"doi": "10.1234/six"})), rationale="r", **REPORT)
    left.delete(survivor.id)
    assert left.read_view.resolve(paper.id) is None
```

The `correction_halt_positions` fixture derives and returns the two halt positions from observed file states. The halting test requests it explicitly, so direct selection and `--lf` reruns perform the sweep without depending on another test's execution. `(True, False)` before `(True, True)` in the sweep is the proof that the create completes before the delete begins; `(False, False)` anywhere would mean the delete published first and fails the sweep. `SOURCES` grants the kinds `mint_eligible_assessment` and `retract` need through the session's permit.

- [ ] **Step 2: Run on the certified volume**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_source_address_acceptance.py`
Expected: all pass. A `CapabilityUnavailable` failure means the durable tuple is not certified — run the recertification the repo documents, never skip.

- [ ] **Step 3: Commit**

```bash
git add python/tests/acceptance/test_source_address_acceptance.py
git commit -m "test(acceptance): W1, W2 and W5a over derived source addresses"
```

---

### Task 10: N2 arms, the audit, the runner and the cut document

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut25.py`, `python/tests/acceptance/test_n2_cut25.py`, `python/tools/cut25_acceptance.py`, `docs/designs/2026-09-10-conformance-cut-25.md`

- [ ] **Step 1: Declare the arms**

`n2_arms_cut25.py`, on `n2_arms_cut24.py`'s shape with **its own parser** — cut 24's takes a unit plus one bare lowercase letter and cannot name a row under `W5a`:

```python
DECLARATION_UNITS: tuple[str, ...] = ("W1", "W2", "W5a")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`; the hyphen is what lets `W5a` carry rows."""
    unit, _, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (suffix and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-25 row")
    return unit
```

One `Arm` per spec §10.4 mechanism; each `before` is an exact substring occurring once in its module, each `after` the weakening, and each `checks` tuple names tests whose fixture violates **only** the invariant the sabotage removes — an arm whose check survives its sabotage is vacuous and fails the audit. The 24 arms:

| row | module | sabotage (`before` → `after`) | checks (each fails under the sabotage) |
|---|---|---|---|
| W2-a | source.py | `remainder = _remainder("doi", value, _DOI_PREFIX).lower()` → `.lower()` dropped | `test_source_address.py::TestNormalizeDoi::test_every_spelling_folds_to_one_canonical_form` |
| W2-b | source.py | `_DOI_PREFIX = re.compile(r"^(?:doi:\|https?://(?:dx\.)?doi\.org/)", re.IGNORECASE)` → `re.compile(r"^$")` | same |
| W2-c | source.py | `SCHEMES = ("doi", "pmid", "isbn", "accession")` → reversed | `TestBasisAndAddress::test_precedence_over_every_non_empty_subset`, `TestRefusalOrder::test_one_tuple_in_precedence_order` |
| W2-d | source.py | `return {scheme: normalize(scheme, identifiers[scheme]) for scheme in sorted(identifiers)}` → `for scheme in sorted(identifiers)[:1]}` | `TestRefusalOrder::test_every_entry_is_validated_before_selection` |
| W2-e | source.py | `if _isbn13_check(remainder[:12]) != remainder[12]:` → `if False:` | `TestNormalizeIsbn::test_malformed[978-0-306-40615-8]` |
| W2-f | source.py | `if scheme not in _RULES:` → `if False:` (an unknown scheme then hits `_RULES[scheme]` and raises `KeyError`, not `IdentifierMalformed`) | `TestRefusalOrder::test_unknown_scheme_wins_over_its_own_value` |
| W2-g | source.py | `if not remainder:\n        raise _refuse(scheme, value, "empty"` → `if False:` | `TestRefusalOrder::test_empty_after_trim_and_prefix_strip` (the empty DOI then reads `malformed`) |
| W1-a | corpus.py | `if node.id != address:\n            raise SourceAddressDisagreement` → `if False:` | `test_identifier_correction.py::TestTheBoundary::test_a_handle_address_refuses` (builder output is correctly addressed, so no acceptance arm is named) |
| W1-b | corpus.py | `_preflight_replace_locked`'s `self._refuse_source(node, provenance=True)` line → removed | `TestRelocation::test_consolidate_refuses_a_handle_addressed_replica_at_replace` |
| W1-c | corpus.py | `_refuse_source`'s `if canonical[scheme] != value:` → `if False:` | `TestTheBoundary::test_a_non_canonical_stored_value_refuses` |
| W5a-a | corpus.py | `self._refuse_dataset_basis(node)` in `_refuse` → removed | `test_corpus_write.py::TestW3TheBasisRefusal::test_a_dataset_with_no_content_identity_refuses` |
| W5a-b | corpus.py | `successor.deprecated_ids = sorted(held - {new_address})` → `successor.deprecated_ids = []` | `TestTheSeamEffects::test_moved_creates_and_deletes_preserving_uid` (the successor then fails the one validator, so the seam refuses instead of renaming) |
| W5a-c | corpus.py | the two-op plan → `self._corpus.rename(subject.id, new_address)` (rewrites referrers) | `TestTheSeamEffects::test_referrers_are_byte_unchanged` |
| W5a-d | corpus.py | `"actor": self._authority.actor,` → `"actor": "nobody",` | `TestTheSeamEffects::test_moved_creates_and_deletes_preserving_uid` (asserts `correction.actor == ACTOR`) |
| W5a-e | corpus.py | `if canonical == current:\n                raise CorrectionRefused` → `if False:` | `TestTheSeamRefusals::test_unchanged` |
| W5a-f | corpus.py | `self._refuse_source(subject, provenance=True)` (the pre-append validation) → removed | `TestTheSeamRefusals::test_a_raw_edited_subject_refuses_before_append` (identifiers moved under the stored id, stamp recomputed: only the boundary catches it) |
| W5a-g | corpus.py | `if stored.IDENTIFIER_CORRECTION_FACET in node.facets and not provenance:` → `and False:` | `TestTheBoundary::test_add_refuses_a_history` |
| W5a-h | corpus.py | the import loop's `self._refuse(record, document_validated=True, view=union, provenance=True)` → guarded `if record.kind != "source":` | `TestTheBoundary::test_import_admits_a_well_formed_history_and_refuses_a_malformed_one` |
| W5a-i | corpus.py | `validated_node`'s `if node.kind == "source":` → `if False:` | `TestTheReadSide::test_a_raw_edited_history_refuses_on_read`, `TestTheReadSide::test_a_duplicated_deprecated_id_refuses_on_read` |
| W5a-j | corpus.py | the finding loop's `if node.kind == "source":` → `if False:` | `TestTheReadSide::test_the_check_view_reports_facet_payload_malformed` |
| W5a-k | stored.py | `validate_source_history`'s `if list(node.deprecated_ids) != expected:` → `if set(node.deprecated_ids) != set(expected):` | `TestReaders::test_validate_source_history_refuses_a_disagreeing_redirect[duplicate]`, `TestReaders::test_an_unsorted_redirect_refuses` |
| W5a-l | stored.py | `if frm == to:\n            raise MalformedRecord` → `if False:` | `TestReaders::test_from_equal_to_refuses_and_nothing_else_does` |
| W5a-m | relocation.py | the history comparison `if keep_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET) != other_node.facets.get(` → `if False and ...` | `TestRelocation::test_consolidate_refuses_divergent_histories` |
| W5a-n | corpus.py | `_revise_dataset_locked`'s `if candidate_fields != current_fields:` → `if False:` | acceptance `test_w5a_dataset_arm_a_rehold_is_a_new_entity` |

Write each `before` by copying the exact line(s) from the file (`sed -n` them) — never retype. Before declaring the accounting, run the audit and confirm every arm is `sound`: a `vacuous` or `mixed` verdict means the fixture does not isolate the invariant, and the fix is a sharper fixture in the named test, never a looser check.

- [ ] **Step 2: The audit test**

`test_n2_cut25.py`: copy `test_n2_cut24.py` wholesale, then: import `unit_of` from `n2_arms_cut25` (never cut 24's); import `CUT24_ARMS` too and add `n2_arms_cut24.py` to `FROZEN_PRIOR_CUT_FILES` at its freeze commit (`git log -1 --format=%h -- python/tests/acceptance/n2_arms_cut24.py` on `main`); rename every `24` to `25`; set `FROZEN_CUT` to the cut 25 document; leave `CUT25_FREEZE_COMMIT` and `CUT25_FROZEN_SHA256` as `""` with a `pytest.skip("not yet frozen")` guard in the pin test until the freeze commit exists (the freeze task fills them); adjust the three `assert ... in current` strings to cut 25's accounting sentences once the document is written.

- [ ] **Step 3: The runner**

`python/tools/cut25_acceptance.py`: copy `cut24_acceptance.py`, replace `24` with `25`, `PREFIX_RUNNERS = ("cut24_acceptance.py",)`, `PHASE_MODULES = ("test_source_address_acceptance.py", "test_n2_cut25.py")`.

- [ ] **Step 4: The cut document**

`docs/designs/2026-09-10-conformance-cut-25.md`, on cut 24's section shape: §1 what (from spec §1), §2 the boundary (spec §3–§8 condensed to the mechanisms), §3 selection (W1, W2, W5a — each "intended closure; closes when its checks pass"), §4 accounting (`**3 declaration units**`; "Three guarantee rows are read, **0 full/closed** until discharge" — update at freeze), §5 N2 and acceptance obligations (the 24 arms of Step 1, `PREFIX_RUNNERS = ("cut24_acceptance.py",)`), §6 second reader (the four review passes recorded in the spec §14), §7 limitations (spec §13). Do not mark it frozen.

- [ ] **Step 5: Run the audit and the runner**

```
cd python && uv run --frozen pytest tests/acceptance/test_n2_cut25.py
uv run --frozen python tools/cut25_acceptance.py
```

Expected: every arm `sound`; no `stale`, `vacuous`, `mixed` or `uncollected`; the staleness probe over cuts 3–24 identical to the tree baseline (record the baseline from an untouched `main` checkout first: `git stash` is forbidden — use the main worktree at `/mnt/ssd/Dropbox/beliefs`). The runner completes with cut 24's prefix chain green. Fix any arm whose `before` fails to match by re-copying the line; never edit a frozen file.

- [ ] **Step 6: Commit**

```bash
git add python/tests/acceptance/n2_arms_cut25.py python/tests/acceptance/test_n2_cut25.py python/tools/cut25_acceptance.py docs/designs/2026-09-10-conformance-cut-25.md
git commit -m "test(cut25): N2 arms, audit and runner for derived source addresses"
```

---

### Task 11: Documentation, tasks and the freeze

**Files:**
- Modify: `docs/designs/2026-08-02-world-addressing-design.md` (§4.2 `source` row, §4.4 table), `docs/designs/2026-08-08-world-address-ruling.md` (§4.1 row), `docs/designs/2026-09-05-facet-contracts-design.md` (the reader-facet inventory), `docs/guide/identity-world-and-change.md`, `docs/guide/glossary.md`, `docs/guide/open-questions.md`, **`docs/plans/2026-08-29-implementation-roadmap.md`** (the authoritative roadmap's W-row table — not the historical design spec under `docs/superpowers/specs/`), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (current-state summary), the spec's status line, `docs/designs/2026-09-10-conformance-cut-25.md` (freeze), `python/tests/acceptance/test_n2_cut25.py` (pins)
- Tasks: `beliefs-b7994b` and two new siblings under `beliefs-d248ba`

- [ ] **Step 1: Amend the designs by dated note**

World addressing §4.2, `source` row — append to the basis cell: `*— normalized per scheme and selected by fixed precedence doi > pmid > isbn > accession, addressed as the domain digest under `science.source-address.v1` (2026-09-10, slice 2b §3)*`. §4.4's amended table gains a row before "genuinely different version or work":

```markdown
> | **the record gains an identifier that always existed** (enrichment) — one record, one work | a **rename** iff the selected basis changes; old address retained. An attestation needs two records (slice 2b §6.4) |
```

Address ruling §4.1: after the table, `> **Amended 2026-09-10 (slice 2b):** for `source` the renderer reads `stored.source_basis` — the selected `(scheme, value)` — and nothing else.`

Facet-contracts design: add `identifier-correction` to the reader-shaped facet list with a dated note.

- [ ] **Step 2: Guide, roadmap, ledger, open questions**

`identity-world-and-change.md` "Current state": replace "as does source re-addressing in slice 2b" with "Cut 25 derives every source address from its normalized identifier and adds the attributed identifier correction; dataset re-addressing and divergent-history reconciliation are filed." Glossary: entries for *source address*, *identifier correction*. Open questions (identity section): note that accession normalization is form-only and the accepted-authorities question stays open. Roadmap (`docs/plans/2026-08-29-implementation-roadmap.md`) W-row table: move W1, W2, W5a to the closed column at cut 25. Adoption ledger current-state: one sentence on cut 25.

- [ ] **Step 3: Tasks**

```bash
tasks add "Dataset addresses derived from the content identity" --parent beliefs-d248ba -p 2 --size l --tag world-read -b "dataset_node takes an authored slug while dataset_address is computed and never checked against the id; 189 dataset_node sites measured 2026-09-10. The choice between dataset:sha256: as the address and a digest domain is this design's. Filed by slice 2b (docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md section 12)."
tasks add "Reconcile divergent identifier-correction histories at consolidate" --parent beliefs-d248ba -p 3 --size m --tag world-read -b "Slice 2b makes consolidate refuse two source replicas whose identifier maps or correction histories differ (HistoryDisagreement). Reconciling them — which history survives, how tokens merge, whether the union of held addresses is the redirect set — needs its own design (slice 2b section 7)."
tasks add "The contract names stored.source_assertion_value, which does not exist" --status idea --tag contract -b "contracts/science/CONTRACT.yaml declares source-assertion's reader as stored.source_assertion_value; no such function is defined in stored.py and no source-assertion builder exists, so the kind cannot be minted through a builder or read through its declared reader. Found 2026-09-10 while looking for a source referrer in slice 2b."
```

- [ ] **Step 4: Verify, then freeze**

Run the gate from the repository root: `just check && just test` (python, typescript and `tasks check` together), then `cd python && uv run --frozen python tools/cut25_acceptance.py`, then `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py`. With everything green: set the cut document's §4 to the discharged accounting (`**3 declaration units**`, "Three guarantee rows are read, **3 full/closed** (W1, W2, W5a)"), mark W1/W2/W5a closed in the spec's status line and the cut document, commit as `docs(cut25): freeze conformance cut 25`, then fill `CUT25_FREEZE_COMMIT` (full sha) and `CUT25_FROZEN_SHA256` (`sha256sum docs/designs/2026-09-10-conformance-cut-25.md`) in `test_n2_cut25.py`, remove its skip guard, run it, and commit `test(cut25): pin the freeze`.

- [ ] **Step 5: Close the task**

```bash
tasks done beliefs-b7994b "Slice 2b landed: derived source addresses, correct_identifier, cut 25 frozen at <sha>; W1, W2, W5a closed"
git add -A && git commit -m "chore(tasks): close beliefs-b7994b"
```

Then hand the branch to `superpowers:finishing-a-development-branch`.
