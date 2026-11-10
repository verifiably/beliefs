"""The cross-language claim-identity parity fixture (`science.claim.v2`), Python half.

The fixture is a **frozen oracle**. It is generated once by
`tools/generate_claim_identity_fixture.py`, reviewed, and committed; nothing here
regenerates it, and the generator lives outside the installed package so that
`beliefs` cannot reach it. A fixture recomputed during a test run asserts only
that the implementation agrees with itself, which is the one thing a parity test
must not be satisfied by.

**Every row is built from its components.** The vector carries the claim's parts
as the author wrote them, its expected projection, its expected canonical bytes
and its expected digest, and the test walks all four: components →
`build_claim` → `project_claim` → `encode` → `digest`. Comparing the stored
projection against the stored bytes would test `science.identity.v1` parity
while bypassing `π_claim` — the shared encoding covered, the shared projection
not, which is most of what this fixture is for.

The TypeScript half consumes this same artifact and makes the same four
comparisons. Neither language owns it.

**Declared scope.** The vector cannot exercise `science.identity.v1`'s
code-point-versus-UTF-16 *key* ordering, because π_claim's only non-fixed keys
are dimension and role identifiers and the contract grammar restricts those to
`[a-z][a-z0-9-]*`. That rule is covered by each language's own `identity.v1`
unit tests. The canonical **member** key's code-point order (R10, case 2a) is a
projection rule, not an encoding one, and the astral/BMP row pins it here.
"""

import json
import unicodedata

import pytest
from conftest import REPO_ROOT

from beliefs.claim import Member, Qualifier, Referent, build_claim
from beliefs.contract import load_domain_contract
from beliefs.contract.base import TAG_ENCODING
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

# Loaded at import time so the vector can drive parametrization: a row added to
# the artifact is then tested by construction, rather than by a hand-kept list
# that a later edit could silently fall behind. `conftest` stays the only place a
# repository path is resolved.
FIXTURE_PATH = REPO_ROOT / "fixtures" / "claim-identity-v2.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
VECTOR = FIXTURE["vector"]

BETA_TERM = "EX:\u03b2-catenin"
CAFE_NFD_TERM = "EX:cafe\u0301-cohort"
BMP_TERM = "EX:\uff21"
ASTRAL_TERM = "EX:\U0001f600"


@pytest.fixture(scope="session")
def fixture() -> dict:
    return FIXTURE


@pytest.fixture(scope="session")
def parity_profile(base_contract, testing_contract_path):
    domain = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [domain])


def _referent(value: dict) -> Referent:
    return Referent(sort=value["sort"], term=value["term"])


def _role(value: dict | list) -> Referent | tuple[Member, ...]:
    """A `one` role is a referent object; a `many` role a member list."""
    if isinstance(value, dict):
        return _referent(value)
    return tuple(Member(_referent(member), member["coefficient"]) for member in value)


def _build(profile, claim: dict):
    """Reconstruct a claim from a row's components — the load-bearing step."""
    return build_claim(
        profile,
        operator=claim["operator"],
        roles={name: _role(value) for name, value in claim["roles"].items()},
        qualifiers={
            dimension: Qualifier(entry["quantifier"], _referent(entry["restriction"]))
            for dimension, entry in claim["qualifiers"].items()
        },
        form=claim["form"],
        polarity=claim["polarity"],
        layer=claim["layer"],
    )


def _rows(fixture) -> list[dict]:
    return fixture["vector"]


def _by_name(fixture) -> dict[str, dict]:
    return {row["name"]: row for row in _rows(fixture)}


def _referents(projection: dict) -> list[dict]:
    """Every referent a projection holds: role values, members and restrictions."""
    found: list[dict] = []
    for value in projection["roles"].values():
        found.extend([value] if isinstance(value, dict) else value)
    found.extend(entry["restriction"] for entry in projection["qualifiers"].values())
    return found


# The pair written in both member orders; their digests are asserted equal, and
# every other row's is distinct.
SAME_CLAIM = ("correlates-with-written-forward", "correlates-with-written-reversed")


class TestTheFixtureIsAboutThisProfile:
    """A fixture built against a different contract silently tests nothing."""

    def test_the_header_pins_the_encodings(self, fixture):
        assert fixture["claim_domain"] == CLAIM_DOMAIN == "science.claim.v2"
        assert fixture["identity_contract"] == TAG_ENCODING
        assert fixture["base_contract"] == "contracts/science/CONTRACT.yaml"
        assert fixture["domain_contracts"] == ["fixtures/contracts/testing.yaml"]

    def test_the_header_pins_the_compiled_profile(self, fixture, parity_profile):
        # `compiled_identity` and not a contract identity, deliberately: it moves
        # on a semantic schema edit and stays still on an editorial one. So
        # rewording a description does not demand a regenerated fixture, and
        # changing a role's arity does.
        assert fixture["profile_compiled_identity"] == parity_profile.compiled_identity

    def test_the_vector_is_well_formed(self, fixture):
        rows = _rows(fixture)
        assert rows
        assert len(set(_by_name(fixture))) == len(rows)
        for row in rows:
            assert set(row) == {"name", "covers", "claim", "projection", "canonical_bytes", "digest"}
            assert set(row["claim"]) == {"operator", "roles", "qualifiers", "form", "polarity", "layer"}

    def test_distinct_claims_have_distinct_identities(self, fixture):
        # A collision here would mean the projection lost a distinction it carries.
        others = [row["digest"] for row in _rows(fixture) if row["name"] != SAME_CLAIM[1]]
        assert len(set(others)) == len(others)


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
    """The coverage clause (spec section 11).

    Closed sets are asserted against the **contract**, never against a hand-kept
    list, so adding a tag to the grammar forces a vector entry rather than
    silently going untested.
    """

    def test_both_forms_appear(self, fixture, base_contract):
        projected = {row["projection"]["form"] for row in _rows(fixture)}
        assert set(base_contract.claim_grammar.forms) <= projected

    def test_every_polarity_tag_appears(self, fixture, base_contract):
        projected = {row["projection"]["polarity"] for row in _rows(fixture)}
        assert set(base_contract.claim_grammar.polarity_tags) <= projected
        # `inapt` is reached both ways: a sign-inapt template and a null form.
        rows = _by_name(fixture)
        assert rows["affects-null-statistical"]["projection"]["polarity"] == base_contract.claim_grammar.sign_inapt_tag
        assert rows["transforms-structural"]["projection"]["polarity"] == base_contract.claim_grammar.sign_inapt_tag

    def test_every_quantifier_appears(self, fixture, base_contract):
        projected = {
            entry["quantifier"] for row in _rows(fixture) for entry in row["projection"]["qualifiers"].values()
        }
        assert set(base_contract.claim_grammar.quantifiers) <= projected

    def test_every_layer_appears(self, fixture, base_contract):
        projected = {row["projection"]["layer"] for row in _rows(fixture)}
        assert set(base_contract.claim_grammar.layers) <= projected

    def test_every_binding_kind_binds_a_referent(self, fixture, base_contract, parity_profile):
        reached = {
            parity_profile.sorts[referent["sort"]].binding.kind
            for row in _rows(fixture)
            for referent in _referents(row["projection"])
        }
        assert set(base_contract.claim_grammar.binding_kinds) <= reached


class TestTheHardCasesArePresent:
    """The structural cases the coverage list names, each by its row."""

    def test_a_many_role_with_coefficients_and_one_without(self, fixture, parity_profile):
        rows = _by_name(fixture)
        inputs = rows["transforms-structural"]["projection"]["roles"]["inputs"]
        assert parity_profile.templates["testing/transforms"].roles["inputs"].coefficients
        assert any(member["coefficient"] != 1 for member in inputs)
        parties = rows["correlates-with-written-forward"]["projection"]["roles"]["parties"]
        assert not parity_profile.templates["testing/correlates-with"].roles["parties"].coefficients
        assert len(parties) == 2
        assert all(member["coefficient"] == 1 for member in parties)

    def test_an_empty_min_zero_role_projects_as_an_empty_list(self, fixture):
        row = _by_name(fixture)["transforms-structural"]
        assert row["claim"]["roles"]["facilitators"] == []
        assert row["projection"]["roles"]["facilitators"] == []

    def test_correlates_with_in_both_member_orders_has_one_identity(self, fixture):
        rows = _by_name(fixture)
        forward, reversed_ = (rows[name] for name in SAME_CLAIM)
        assert forward["claim"]["roles"]["parties"] == list(reversed(reversed_["claim"]["roles"]["parties"]))
        assert forward["claim"]["roles"]["parties"] != reversed_["claim"]["roles"]["parties"]
        assert forward["projection"] == reversed_["projection"]
        assert forward["canonical_bytes"] == reversed_["canonical_bytes"]
        assert forward["digest"] == reversed_["digest"]

    def test_a_within_model_claim_differs_from_the_world_claim(self, fixture, parity_profile):
        rows = _by_name(fixture)
        model = rows["affects-within-model"]
        referent = model["projection"]["roles"]["within-model"]
        assert parity_profile.sorts[referent["sort"]].binding.kind == "world-kind"
        world = rows["affects-positive-causal"]
        assert {k: v for k, v in model["projection"]["roles"].items() if k != "within-model"} == world["projection"][
            "roles"
        ]
        assert model["digest"] != world["digest"]

    def test_the_bridge_is_an_operator_with_its_own_identity(self, fixture, parity_profile):
        rows = _by_name(fixture)
        bridge = rows["promotes-bridge"]
        assert bridge["projection"]["operator"] in parity_profile.bridges
        template = parity_profile.bridges[bridge["projection"]["operator"]].template
        template_row = rows["affects-positive-causal"]
        assert template_row["projection"]["operator"] == template
        assert bridge["projection"]["roles"] == template_row["projection"]["roles"]
        assert bridge["digest"] != template_row["digest"]

    def test_a_claim_side_qualifier_appears(self, fixture, parity_profile):
        dimensions = {
            dimension
            for row in _rows(fixture)
            for dimension in row["projection"]["qualifiers"]
            if parity_profile.dimensions[dimension].placement == "claim"
        }
        assert dimensions
        multi = _by_name(fixture)["affects-existential-two-dimensions"]["projection"]
        assert len(multi["qualifiers"]) > 1  # map-key order is observable

    def test_the_non_ascii_referent_is_present(self, fixture):
        terms = {referent["term"] for row in _rows(fixture) for referent in _referents(row["projection"])}
        assert BETA_TERM in terms
        assert not BETA_TERM.isascii()

    def test_the_decomposed_restriction_is_encoded_composed(self, fixture):
        # The projection holds the decomposed form; the canonical bytes hold the
        # composed one. An implementation that normalized at parse time, or not
        # at all, fails exactly one of the two comparisons.
        row = _by_name(fixture)["affects-decomposed-restriction"]
        restriction = row["projection"]["qualifiers"]["testing/population"]["restriction"]["term"]
        assert restriction == CAFE_NFD_TERM
        assert unicodedata.normalize("NFC", restriction) != restriction
        assert restriction not in row["canonical_bytes"]
        assert unicodedata.normalize("NFC", restriction) in row["canonical_bytes"]

    def test_the_astral_and_bmp_pair_project_in_code_point_order(self, fixture):
        row = _by_name(fixture)["correlates-event-product-astral-bmp"]
        written = [member["term"] for member in row["claim"]["roles"]["parties"]]
        projected = [member["term"] for member in row["projection"]["roles"]["parties"]]
        assert written == [ASTRAL_TERM, BMP_TERM]
        assert projected == [BMP_TERM, ASTRAL_TERM]
        # UTF-16 code-unit order is the reverse, so an implementation comparing
        # with `<` on UTF-16 strings projects this row wrongly.
        assert sorted(projected, key=lambda term: term.encode("utf-16-be")) == [ASTRAL_TERM, BMP_TERM]


class TestTheFixtureIsFrozen:
    """The generator lives under `tools/`, outside the installed package.

    That the package cannot *reach* the fixture is a packaging property, and it
    is deliberately not asserted here — a grep over source strings would prove
    neither unreachability nor survive an innocent mention in a docstring. It
    belongs to a packaging test, when that boundary exists to test.
    """

    def test_the_conftest_path_is_this_fixture(self, parity_fixture_path):
        assert parity_fixture_path == FIXTURE_PATH

    def test_the_artifact_is_pure_ascii_on_disk(self, parity_fixture_path):
        # The vector carries non-ASCII and combining characters on purpose. Held
        # as `\\uXXXX` escapes, no editor, merge tool or transfer can normalize
        # them behind the fixture's back — which is the failure it exists to
        # catch, and would otherwise be committed by the file holding it.
        assert parity_fixture_path.read_text(encoding="utf-8").isascii()

    def test_the_v1_fixture_is_retired(self):
        assert not (REPO_ROOT / "fixtures" / "claim-identity-v1.json").exists()
