"""The assumptions register: a content-addressed world record (design §9.1, register v2)."""

from __future__ import annotations

import pytest
import yaml
from conftest import REPO_ROOT
from fixtures_cut3 import TESTING_PROFILE
from fixtures_cut4 import reopen
from test_stored import _testing_writer

from beliefs import corpus as corpus_mod
from beliefs import register as register_mod
from beliefs import stored
from beliefs.contract import domain as domain_mod
from beliefs.contract import parse_domain_contract
from beliefs.corpus import _registers_report, corpus_check
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.register import (
    ENTRY_KINDS,
    REGISTER_DOMAIN,
    AssumptionsRegister,
    RegisterEntry,
    register_from_stored,
    register_identity,
    register_projection,
)

TESTING_PIN = "testing:" + TESTING_PROFILE.activated_contracts["testing"]
ENTRY_FIELDS = {
    "collapses": "every cohort member under one population term",
    "licenses": "restricting a claim to the cohort",
    "not_established": "that the cohort represents the population",
}

REPRESENTATIVE_TESTING_KEYS: tuple[tuple[str, str], ...] = (
    ("sort", "sort:testing/population"),
    ("dimension", "dimension:testing/population"),
    ("template", "template:testing/affects"),
    ("instantiation", "instantiation:testing/affects-entity-outcome"),
    ("bridge", "bridge:testing/promotes"),
    ("estimand", "estimand:instantiation:testing/affects-entity-outcome"),
    ("duration-convention", "duration-convention:testing/mean-month"),
    ("functional", "functional:testing/probability-of-superiority"),
    ("identification-class", "identification-class:testing/observational"),
    ("design", "design:testing/independent-groups"),
    ("selection-mechanism", "selection-mechanism:testing/cohort-enrolment"),
    ("procedure-kind", "procedure-kind:testing/assay"),
    ("aggregation-rule", "aggregation-rule:testing/sum"),
    ("assumption-kind", "assumption-kind:testing/transport-exchangeability"),
    ("measurement", "measurement:testing/entity"),
    ("aspect", "aspect:testing/energy-aspect"),
    ("quantity-kind", "quantity-kind:testing/duration"),
    ("unit", "unit:testing/second"),
    ("constant", "constant:testing/avogadro"),
    ("conversion", "conversion:testing/hour-to-second"),
    ("transformation", "transformation:testing/identity"),
)


def make_entry(
    collapses: str = ENTRY_FIELDS["collapses"],
    licenses: str = ENTRY_FIELDS["licenses"],
    not_established: str = ENTRY_FIELDS["not_established"],
    *,
    status: str = "provisional",
) -> RegisterEntry:
    return RegisterEntry(collapses, licenses, not_established, status=status)  # type: ignore[arg-type]


def register(entries=None, *, describes=TESTING_PIN, previous=None) -> AssumptionsRegister:
    return AssumptionsRegister(
        describes=describes,
        previous=previous,
        entries={"sort:testing/population": make_entry()} if entries is None else entries,
    )


def test_the_exact_values_and_catalogue_alignment():
    DECLARATION_FAMILIES = domain_mod.DECLARATION_FAMILIES
    _REGISTER_PROFILE_TABLES = corpus_mod._REGISTER_PROFILE_TABLES
    register_from_projection = register_mod.register_from_projection

    provisional = register({"sort:testing/population": make_entry(status="provisional")})
    established = register({"sort:testing/population": make_entry(status="established")})

    assert REGISTER_DOMAIN == "science.assumptions-register.v2"
    assert set(ENTRY_KINDS) == {kind for kind, _ in DECLARATION_FAMILIES}
    assert ENTRY_KINDS == tuple(kind for kind, _ in DECLARATION_FAMILIES)
    assert len(ENTRY_KINDS) == 21
    assert set(_REGISTER_PROFILE_TABLES) == set(ENTRY_KINDS) - {"estimand", "measurement", "aspect"}
    assert [kind for kind, _ in REPRESENTATIVE_TESTING_KEYS] == list(ENTRY_KINDS)
    assert register_identity(provisional) != register_identity(established)
    assert register_from_projection(register_projection(provisional), source="test") == provisional
    assert register_from_projection(register_projection(established), source="test") == established


def test_status_is_required_keyword_only():
    with pytest.raises(TypeError):
        RegisterEntry("c", "l", "n")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        RegisterEntry("c", "l", "n", "provisional")  # type: ignore[misc]


@pytest.mark.parametrize("bad_status", ["", "accepted", "draft", "PROVISIONAL", None, True, 1, ["provisional"]])
def test_invalid_status_refuses(bad_status):
    with pytest.raises(MalformedRecord, match="status"):
        RegisterEntry("c", "l", "n", status=bad_status)  # type: ignore[arg-type]


def test_identity_is_content_addressed():
    entry = make_entry()
    one, two = register(), register()
    assert register_identity(one) == register_identity(two)
    assert register_identity(one) == "assumptions-register:" + v1.digest(REGISTER_DOMAIN, register_projection(one))
    changed = register(
        {"sort:testing/population": RegisterEntry("other", entry.licenses, entry.not_established, status="provisional")}
    )
    assert register_identity(changed) != register_identity(one)
    renamed = register({"dimension:testing/population": entry})
    assert register_identity(renamed) != register_identity(one)
    successor = register(previous=register_identity(one))
    assert register_identity(successor) != register_identity(one)
    assert "previous" not in register_projection(one)  # absent, never null
    projected_entries = register_projection(one)["entries"]
    assert isinstance(projected_entries, dict)
    assert projected_entries["sort:testing/population"]["status"] == "provisional"


def test_typed_keys_do_not_collide(tmp_path):
    """Same local name across tables (`population` sort/dimension and `promotes`
    instantiation/bridge plus both nested estimand targets) stays distinct."""
    entry = make_entry()
    writer = _testing_writer(tmp_path / "corpus")
    keys = {
        "sort:testing/population": entry,
        "dimension:testing/population": entry,
        "instantiation:testing/promotes": entry,
        "bridge:testing/promotes": entry,
        "estimand:instantiation:testing/promotes": entry,
        "estimand:bridge:testing/promotes": entry,
    }
    value = register(keys)
    assert set(value.entries) == set(keys)
    minted = writer.add(stored.assumptions_register_node(value))
    assert minted.id == register_identity(value)
    findings = corpus_check(reopen(writer.root), TESTING_PROFILE)
    assert not [f for f in findings if f.code.startswith("register-")]


@pytest.mark.parametrize(
    ("kind", "key"),
    REPRESENTATIVE_TESTING_KEYS,
    ids=[kind for kind, _ in REPRESENTATIVE_TESTING_KEYS],
)
def test_every_declaration_family_round_trips_and_audits_cleanly(tmp_path, kind, key):
    assert key.startswith(f"{kind}:")
    writer = _testing_writer(tmp_path / f"corpus-{kind}")
    value = register({key: make_entry()})
    projected = register_projection(value)
    assert register_mod.register_from_projection(projected, source="test") == value
    minted = writer.add(stored.assumptions_register_node(value))
    assert register_from_stored(minted) == value
    findings = corpus_check(reopen(writer.root), TESTING_PROFILE)
    assert not [f for f in findings if f.code.startswith("register-")]


@pytest.mark.parametrize(
    "unknown_key",
    [
        *(f"{kind}:testing/missing-target" for kind, _ in REPRESENTATIVE_TESTING_KEYS if kind != "estimand"),
        "estimand:instantiation:testing/missing-target",
        "estimand:bridge:testing/missing-target",
        # `affects-entity-outcome` is an instantiation, not a bridge; target kind must match.
        "estimand:bridge:testing/affects-entity-outcome",
    ],
)
def test_nonexistent_or_wrong_target_reports_register_entry_unknown_never_key_error(tmp_path, unknown_key):
    writer = _testing_writer(tmp_path / "corpus")
    minted = writer.add(stored.assumptions_register_node(register({unknown_key: make_entry()})))
    findings = [f for f in corpus_check(reopen(writer.root), TESTING_PROFILE) if f.code == "register-entry-unknown"]
    assert [(f.ref, f.detail) for f in findings] == [(minted.id, unknown_key)]


@pytest.mark.parametrize(
    "key",
    [
        "testing/gene",
        "operator:testing/x",
        "sort:testing",
        "sort:Testing/gene",
        "sort:",
        "sort:instantiation:testing/entity",
        "estimand:testing/affects-entity-outcome",
        "estimand:template:testing/affects",
        "estimand:instantiation:testing",
        "estimand:instantiation:Testing/affects",
        "estimand:instantiation:testing/a/b",
        "estimand:bridge:",
    ],
)
def test_malformed_key_refuses(key):
    entry = make_entry()
    with pytest.raises(MalformedRecord, match="typed declaration address"):
        register({key: entry})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("describes", "testing"),
        ("describes", "testing:" + "AB" * 32),
        ("describes", "sha256:" + "ab" * 31),
        ("describes", TESTING_PIN + "\n"),
        ("previous", "dataset:" + "ab" * 32),
        ("previous", "assumptions-register:" + "ab" * 31),
    ],
)
def test_malformed_describes_or_previous_refuses(field, value):
    entry = make_entry()
    with pytest.raises(MalformedRecord, match=field):
        register({"sort:testing/population": entry}, **{field: value})


@pytest.mark.parametrize("field", ["collapses", "licenses", "not_established"])
def test_every_entry_field_is_required_prose(field):
    fields = {"collapses": "c", "licenses": "l", "not_established": "n", "status": "provisional"}
    for bad in ("", None, 1):
        with pytest.raises(MalformedRecord, match=field):
            RegisterEntry(**(fields | {field: bad}))  # type: ignore[arg-type]


def test_round_trip_through_stored_node():
    entry = make_entry()
    value = register(
        {
            "bridge:testing/promotes": entry,
            "estimand:bridge:testing/promotes": RegisterEntry("c", "l", "n", status="established"),
            "sort:testing/population": entry,
        },
        previous="assumptions-register:" + "ab" * 32,
    )
    node = stored.assumptions_register_node(value, body="free prose, outside identity")
    assert node.id == register_identity(value) and node.kind == "assumptions-register"
    assert node.relations == []
    assert register_from_stored(node) == value
    assert stored.recompute_semantic_hash(node) == stored.stored_semantic_hash(node)
    reworded = stored.assumptions_register_node(value, body="other prose")
    assert reworded.id == node.id


def test_projection_and_stored_readers_refuse_noncanonical_facets_and_v1_ids():
    register_from_projection = register_mod.register_from_projection
    node = stored.assumptions_register_node(register())
    facet = node.facets["assumptions-register"]
    entry = facet["entries"]["sort:testing/population"]
    bad_projections = (
        None,
        [],
        facet | {"previous": None},
        facet | {"extra": 1},
        {"describes": facet["describes"]},
        facet | {"entries": []},
        facet | {"entries": {"sort:testing/population": {"collapses": "c", "licenses": "l", "not_established": "n"}}},
        facet | {"entries": {"sort:testing/population": entry | {"status": "draft"}}},
        facet | {"entries": {"sort:testing/population": entry | {"status": True}}},
        facet | {"entries": {"sort:testing/population": entry | {"extra": "x"}}},
    )
    for bad in bad_projections:
        with pytest.raises(MalformedRecord, match="source-pin"):
            register_from_projection(bad, source="source-pin")
        if isinstance(bad, dict):
            node.facets["assumptions-register"] = bad
            with pytest.raises(MalformedRecord, match=node.id):
                register_from_stored(node)

    node.facets["assumptions-register"] = register_projection(register({}))
    with pytest.raises(MalformedRecord, match="does not recompute"):
        register_from_stored(node)

    # A stored node carrying a valid v2 projection under an old v1 digest is refused, never migrated.
    v2_projection = register_projection(register())
    v1_id = "assumptions-register:" + v1.digest("science.assumptions-register.v1", v2_projection)
    v1_node = node.model_copy(deep=True, update={"id": v1_id, "facets": {"assumptions-register": v2_projection}})
    with pytest.raises(MalformedRecord, match="does not recompute"):
        register_from_stored(v1_node)


@pytest.mark.parametrize(
    "key", ["measurement:testing/entity", "measurement:testing/cohort", "aspect:testing/energy-aspect"]
)
def test_pack_entries_are_declared(tmp_path, key):
    writer = _testing_writer(tmp_path / "corpus")
    writer.add(stored.assumptions_register_node(register({key: make_entry()})))
    assert not [f for f in corpus_check(reopen(writer.root), TESTING_PROFILE) if f.code == "register-entry-unknown"]


def test_an_aspect_sort_not_declared_in_the_pack_is_unknown(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    writer.add(stored.assumptions_register_node(register({"aspect:testing/level": make_entry()})))
    assert any(f.code == "register-entry-unknown" for f in corpus_check(reopen(writer.root), TESTING_PROFILE))


def test_foreign_ownership_and_register_entry_keys_expansion():
    DECLARATION_FAMILIES = domain_mod.DECLARATION_FAMILIES
    register_entry_keys = register_mod.register_entry_keys
    entry = make_entry()

    base = shipped_base_contract()
    testing_doc = yaml.safe_load((REPO_ROOT / "fixtures" / "contracts" / "testing.yaml").read_text(encoding="utf-8"))
    testing = parse_domain_contract(testing_doc, source="<testing>", base=base, predecessor=None)
    other = parse_domain_contract(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {
                "local-sort": {
                    "binding": {"kind": "release", "namespace": "EX", "release": "2026-01-01"},
                    "identifier_class": {"prefix": "EX", "pattern": "EX:[a-z0-9\\-]+"},
                }
            },
            "dimensions": {},
            "instantiations": {
                "local-affects": {
                    "template": "testing/affects",
                    "roles": {"cause": ["testing/entity"], "effect": ["local-sort"]},
                }
            },
            "bridges": {
                "local-bridge": {
                    "template": "testing/affects",
                    "mapping": "narrower",
                    "roles": {"cause": ["testing/entity"], "effect": ["local-sort"]},
                }
            },
            "estimands": {
                "instantiation:local-affects": {
                    "forms": ["contrast"],
                    "conditioning_sorts": ["testing/entity"],
                },
                "bridge:local-bridge": {
                    "forms": ["contrast"],
                    "conditioning_sorts": ["testing/entity"],
                },
            },
            "measurements": {
                "local-sort": ["testing/count"],
                "testing/method": ["testing/score"],
            },
            "aspects": {
                "testing/energy": ["testing/level", "local-sort"],
                "testing/duration": [],
            },
        },
        source="<other>",
        base=base,
        predecessor=None,
    )
    profile = compile_profile(base, [testing, other])
    pins = {"testing": testing.content_identity, "other": other.content_identity}

    # `register_entry_keys` expands aspect sorts, preserves qualified external sorts without
    # double-prefixing, qualifies nested estimands, and omits empty aspect lists (unlike succession keys).
    other_keys = register_entry_keys(other)
    assert other_keys == frozenset(
        {
            "sort:other/local-sort",
            "instantiation:other/local-affects",
            "bridge:other/local-bridge",
            "estimand:instantiation:other/local-affects",
            "estimand:bridge:other/local-bridge",
            "measurement:other/local-sort",
            "measurement:testing/method",
            "aspect:testing/level",
            "aspect:other/local-sort",
        }
    )
    succession_keys = set(other.claim_vocabulary())
    assert "aspect:testing/duration" in succession_keys
    assert "aspect:testing/energy" in succession_keys
    assert not any(key.startswith("aspect:testing/duration") for key in other_keys)
    assert "estimand:instantiation:local-affects" in succession_keys
    assert "estimand:instantiation:other/local-affects" in other_keys

    # Every key in `register_entry_keys` for both contracts validates cleanly with zero findings.
    testing_keys = register_entry_keys(testing)
    assert {kind for kind, _ in DECLARATION_FAMILIES} == {key.partition(":")[0] for key in testing_keys}
    full_testing = AssumptionsRegister(
        describes=f"testing:{testing.content_identity}",
        previous=None,
        entries={key: entry for key in testing_keys},
    )
    other_reg = AssumptionsRegister(
        describes=f"other:{other.content_identity}",
        previous=None,
        entries={key: entry for key in other_keys},
    )
    assert _registers_report({"r-other": other_reg, "r-testing": full_testing}, pins, profile) == []

    # Conversely, `other` naming `testing`-owned declarations (ordinary, nested estimands, or
    # `testing`'s own measurement/aspect admissions) reports `register-entry-unknown`.
    foreign_on_other = {
        "sort:testing/entity": entry,
        "template:testing/affects": entry,
        "functional:testing/probability-of-superiority": entry,
        "estimand:instantiation:testing/affects-entity-outcome": entry,
        "estimand:bridge:testing/promotes": entry,
        "measurement:testing/entity": entry,
        "aspect:testing/energy-aspect": entry,
    }
    bad_other = AssumptionsRegister(
        describes=f"other:{other.content_identity}",
        previous=None,
        entries=foreign_on_other,
    )
    unknown_on_other = {
        f.detail
        for f in _registers_report({"r-bad-other": bad_other}, pins, profile)
        if f.code == "register-entry-unknown"
    }
    assert unknown_on_other == set(foreign_on_other)

    # And `testing` naming `other`'s declarations (even when the referenced sort in `other`'s
    # measurement/aspect row is in the `testing/` namespace) reports `register-entry-unknown`.
    foreign_on_testing = {
        "sort:other/local-sort": entry,
        "estimand:instantiation:other/local-affects": entry,
        "estimand:bridge:other/local-bridge": entry,
        "measurement:testing/method": entry,
        "aspect:testing/level": entry,
    }
    bad_testing = AssumptionsRegister(
        describes=f"testing:{testing.content_identity}",
        previous=None,
        entries=foreign_on_testing,
    )
    unknown_on_testing = {
        f.detail
        for f in _registers_report({"r-bad-testing": bad_testing}, pins, profile)
        if f.code == "register-entry-unknown"
    }
    assert unknown_on_testing == set(foreign_on_testing)
