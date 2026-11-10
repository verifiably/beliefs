"""The assumptions register: a content-addressed world record (design §9.1)."""

from __future__ import annotations

import pytest
from fixtures_cut3 import TESTING_PROFILE
from fixtures_cut4 import reopen
from test_stored import _testing_writer

from beliefs import stored
from beliefs.corpus import corpus_check
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
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
ENTRY = RegisterEntry(
    collapses="every cohort member under one population term",
    licenses="restricting a claim to the cohort",
    not_established="that the cohort represents the population",
)


def register(entries=None, *, describes=TESTING_PIN, previous=None) -> AssumptionsRegister:
    return AssumptionsRegister(
        describes=describes,
        previous=previous,
        entries={"sort:testing/population": ENTRY} if entries is None else entries,
    )


def test_the_exact_values():
    assert REGISTER_DOMAIN == "science.assumptions-register.v1"
    assert ENTRY_KINDS == ("sort", "template", "instantiation", "bridge", "dimension", "measurement", "aspect")


def test_identity_is_content_addressed():
    one, two = register(), register()
    assert register_identity(one) == register_identity(two)
    assert register_identity(one) == "assumptions-register:" + v1.digest(REGISTER_DOMAIN, register_projection(one))
    changed = register({"sort:testing/population": RegisterEntry("other", ENTRY.licenses, ENTRY.not_established)})
    assert register_identity(changed) != register_identity(one)
    renamed = register({"dimension:testing/population": ENTRY})
    assert register_identity(renamed) != register_identity(one)
    successor = register(previous=register_identity(one))
    assert register_identity(successor) != register_identity(one)
    assert "previous" not in register_projection(one)  # absent, never null


def test_typed_keys_do_not_collide(tmp_path):
    """Case 10a: a sort and a dimension sharing the local name `population` are
    two declarations, two entries, and neither is unknown."""
    writer = _testing_writer(tmp_path / "corpus")
    value = register({"sort:testing/population": ENTRY, "dimension:testing/population": ENTRY})
    assert set(value.entries) == {"sort:testing/population", "dimension:testing/population"}
    minted = writer.add(stored.assumptions_register_node(value))
    assert minted.id == register_identity(value)
    findings = corpus_check(reopen(writer.root), TESTING_PROFILE)
    assert not [f for f in findings if f.code.startswith("register-")]


@pytest.mark.parametrize("key", ["testing/gene", "operator:testing/x", "sort:testing", "sort:Testing/gene", "sort:"])
def test_malformed_key_refuses(key):
    with pytest.raises(MalformedRecord, match="typed declaration address"):
        register({key: ENTRY})


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
    with pytest.raises(MalformedRecord, match=field):
        register(**{field: value})


@pytest.mark.parametrize("field", ["collapses", "licenses", "not_established"])
def test_every_entry_field_is_required_prose(field):
    fields = {"collapses": "c", "licenses": "l", "not_established": "n"}
    for bad in ("", None, 1):
        with pytest.raises(MalformedRecord, match=field):
            RegisterEntry(**(fields | {field: bad}))  # type: ignore[arg-type]


def test_round_trip_through_stored_node():
    value = register(
        {"bridge:testing/promotes": ENTRY, "sort:testing/population": ENTRY},
        previous="assumptions-register:" + "ab" * 32,
    )
    node = stored.assumptions_register_node(value, body="free prose, outside identity")
    assert node.id == register_identity(value) and node.kind == "assumptions-register"
    assert node.relations == []
    assert register_from_stored(node) == value
    assert stored.recompute_semantic_hash(node) == stored.stored_semantic_hash(node)
    reworded = stored.assumptions_register_node(value, body="other prose")
    assert reworded.id == node.id


def test_the_reader_refuses_a_facet_that_is_not_the_canonical_projection():
    node = stored.assumptions_register_node(register())
    facet = node.facets["assumptions-register"]
    for bad in (
        facet | {"previous": None},
        facet | {"extra": 1},
        {"describes": facet["describes"]},
        facet | {"entries": {"sort:testing/population": {"collapses": "c", "licenses": "l"}}},
        facet | {"entries": []},
    ):
        node.facets["assumptions-register"] = bad
        with pytest.raises(MalformedRecord, match=node.id):
            register_from_stored(node)
    node.facets["assumptions-register"] = register_projection(register({}))
    with pytest.raises(MalformedRecord, match="does not recompute"):
        register_from_stored(node)


@pytest.mark.parametrize(
    "key", ["measurement:testing/entity", "measurement:testing/cohort", "aspect:testing/energy-aspect"]
)
def test_pack_entries_are_declared(tmp_path, key):
    writer = _testing_writer(tmp_path / "corpus")
    writer.add(stored.assumptions_register_node(register({key: ENTRY})))
    assert not [f for f in corpus_check(reopen(writer.root), TESTING_PROFILE) if f.code == "register-entry-unknown"]


def test_an_aspect_sort_not_declared_in_the_pack_is_unknown(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    writer.add(stored.assumptions_register_node(register({"aspect:testing/level": ENTRY})))
    assert any(f.code == "register-entry-unknown" for f in corpus_check(reopen(writer.root), TESTING_PROFILE))
