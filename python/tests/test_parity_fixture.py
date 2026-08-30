"""M10 — the cross-language parity fixture, Python half.

The fixture is a **frozen conformance oracle**. It is generated once by
`tools/generate_claim_identity_fixture.py`, reviewed, and committed; nothing here
regenerates it, and the generator lives outside the installed package so that
`beliefs` cannot reach it. A fixture recomputed during a test run asserts only
that the implementation agrees with itself, which is the one thing a parity test
must not be satisfied by.

**Every row is built from its components.** The vector carries the claim's parts,
its expected projection, its expected canonical bytes and its expected digest,
and the test walks all four: components → `build_claim` → `project_claim` →
`encode` → `digest`. Comparing the stored projection against the stored bytes
would test `science.identity.v1` parity while bypassing `π_claim` — the shared
encoding covered, the shared projection not, which is most of what M10 is for.

The TypeScript half consumes this same artifact and makes the same four
comparisons. Neither language owns it.

**Declared scope.** The vector cannot exercise `science.identity.v1`'s
code-point-versus-UTF-16 key ordering, because π_claim's only non-fixed keys are
dimension identifiers and the contract grammar restricts those to
`[a-z][a-z0-9-]*` — no contract can issue a key above U+FFFF. That rule is
covered by each language's own `identity.v1` unit tests, and this file does not
claim it.
"""

import json

import pytest
from conftest import REPO_ROOT

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import load_domain_contract
from beliefs.contract.base import TAG_ENCODING
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

# Loaded at import time so the vector can drive parametrization: a row added to
# the artifact is then tested by construction, rather than by a hand-kept list
# that a later edit could silently fall behind. `conftest` stays the only place a
# repository path is resolved.
FIXTURE_PATH = REPO_ROOT / "fixtures" / "claim-identity-v1.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
VECTOR = FIXTURE["vector"]


@pytest.fixture(scope="session")
def fixture() -> dict:
    return FIXTURE


@pytest.fixture(scope="session")
def parity_profile(base_contract, testing_contract_path):
    domain = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [domain])


def _referent(value: dict) -> Referent:
    return Referent(sort=value["sort"], term=value["term"])


def _build(profile, claim: dict):
    """Reconstruct a claim from a row's components — the load-bearing step."""
    return build_claim(
        profile,
        operator=claim["operator"],
        args=tuple(_referent(argument) for argument in claim["args"]),
        qualifiers={
            dimension: Qualifier(entry["quantifier"], _referent(entry["restriction"]))
            for dimension, entry in claim["qualifiers"].items()
        },
        polarity=claim["polarity"],
        layer=claim["layer"],
    )


def _rows(fixture) -> list[dict]:
    return fixture["vector"]


def _names(fixture) -> list[str]:
    return [row["name"] for row in _rows(fixture)]


class TestTheFixtureIsAboutThisProfile:
    """A fixture built against a different contract silently tests nothing."""

    def test_the_header_pins_the_encodings(self, fixture):
        assert fixture["claim_domain"] == CLAIM_DOMAIN
        assert fixture["identity_contract"] == TAG_ENCODING

    def test_the_header_pins_the_compiled_profile(self, fixture, parity_profile):
        # `compiled_identity` and not a contract identity, deliberately: it moves
        # on a semantic schema edit and stays still on an editorial one (M7). So
        # rewording a description does not demand a regenerated fixture, and
        # changing an operator's arity does.
        assert fixture["profile_compiled_identity"] == parity_profile.compiled_identity

    def test_the_vector_is_well_formed(self, fixture):
        rows = _rows(fixture)
        assert rows
        assert len(set(_names(fixture))) == len(rows)
        # Eleven distinct claims, so eleven distinct identities. A collision here
        # would mean the projection lost a distinction it carries.
        assert len({row["digest"] for row in rows}) == len(rows)


class TestEveryRowRoundTrips:
    """Components → build → project → encode → digest, per row."""

    @pytest.mark.parametrize("row", VECTOR, ids=[entry["name"] for entry in VECTOR])
    def test_the_row_reproduces(self, row, parity_profile):
        claim = _build(parity_profile, row["claim"])
        projection = project_claim(claim)
        assert projection == row["projection"]
        assert v1.encode(projection) == row["canonical_bytes"].encode("utf-8")
        assert claim_identity(claim) == row["digest"]


class TestTagCoverageIsCompleteAgainstTheBaseContract:
    """M10's coverage clause.

    Asserted against the **contract**, never against a hand-kept list, so adding
    a tag to the grammar forces a vector entry rather than silently going
    untested. Under a one-claim fixture, changing an unused tag's bytes would
    pass — which is the row's own stated reason for a vector.
    """

    def test_every_polarity_tag_appears(self, fixture, base_contract):
        projected = {row["projection"]["polarity"] for row in _rows(fixture)}
        assert set(base_contract.claim_grammar.polarity_tags) <= projected

    def test_every_quantifier_appears(self, fixture, base_contract):
        projected = {
            entry["quantifier"] for row in _rows(fixture) for entry in row["projection"]["qualifiers"].values()
        }
        assert set(base_contract.claim_grammar.quantifiers) <= projected

    def test_every_layer_appears(self, fixture, base_contract):
        projected = {row["projection"]["layer"] for row in _rows(fixture)}
        assert set(base_contract.claim_grammar.layers) <= projected

    def test_the_hard_cases_are_present(self, fixture):
        rows = {row["name"]: row for row in _rows(fixture)}
        multi = rows["affects-two-dimensions-non-ascii"]["projection"]
        assert len(multi["qualifiers"]) > 1  # map-key order is observable
        assert len(multi["args"]) > 1  # slot order is observable
        assert not multi["args"][0].isascii()

        # The projection holds the decomposed form; the canonical bytes hold the
        # composed one. An implementation that normalized at parse time, or not
        # at all, fails exactly one of the two comparisons.
        decomposed = rows["affects-decomposed-referent"]
        restriction = decomposed["projection"]["qualifiers"]["testing/population"]["restriction"]
        assert not restriction.isascii()
        assert restriction not in decomposed["canonical_bytes"]


class TestTheFixtureIsFrozen:
    """The generator lives under `tools/`, outside the installed package.

    That the package cannot *reach* the fixture is a packaging property, and it
    is deliberately not asserted here — a grep over source strings would prove
    neither unreachability nor survive an innocent mention in a docstring. It
    belongs to a packaging test, when that boundary exists to test.
    """

    def test_the_artifact_is_pure_ascii_on_disk(self, parity_fixture_path):
        # The vector carries non-ASCII and combining characters on purpose. Held
        # as `\\uXXXX` escapes, no editor, merge tool or transfer can normalize
        # them behind the fixture's back — which is the failure it exists to
        # catch, and would otherwise be committed by the file holding it.
        assert parity_fixture_path.read_text(encoding="utf-8").isascii()
