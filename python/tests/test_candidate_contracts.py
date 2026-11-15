"""Unshipped declarations retain their meanings, coverage and additive history."""

import re
from fractions import Fraction

import pytest
from candidate_contracts import (
    GENERAL_SOURCE_ID,
    STATIC,
    candidate_history,
    candidate_profile,
    fragment,
    general_successor_document,
    general_successor_history,
    oracle,
    time_successor,
    time_successor_document,
    with_rows,
)
from time_roles_fixture import time_contract, time_document

from beliefs import errors
from beliefs.contract.domain import parse_domain_contract
from beliefs.profile import shipped_assumptions_register, shipped_domain_contract
from beliefs.register import RegisterEntry, register_entry_keys
from beliefs.resolution import TermOutcome, build_snapshot

SOURCES = {
    "plasma-populations": "urn:beliefs:definitions:plasma-population-measurement-admissions",
    "catalogue-anchors": "urn:beliefs:definitions:catalogue-anchor-admissions",
}
KEYS = {
    "plasma-populations": {
        "sort:plasma-populations/near-earth-solar-wind",
        "sort:plasma-populations/bulk-flow-speed",
        "measurement:plasma-populations/near-earth-solar-wind",
        "aspect:plasma-populations/bulk-flow-speed",
    },
    "catalogue-anchors": {
        "sort:catalogue-anchors/cdaw-halo-cme",
        "dimension:catalogue-anchors/anchor-epoch",
        "instantiation:catalogue-anchors/halo-anchored-solar-wind-speed",
        "estimand:instantiation:catalogue-anchors/halo-anchored-solar-wind-speed",
    },
}
GENERAL_KEYS = {
    "template:general/event-locked-change",
    "functional:general/mean-within-anchor-window-difference",
    "design:general/within-anchor-windows",
    "selection-mechanism:general/annotation-defined-anchors",
}
SPEED_KEYS = {
    "quantity-kind:si-brochure/speed",
    "unit:si-brochure/metre-per-second",
    "unit:si-brochure/kilometre-per-second",
    "conversion:si-brochure/kilometre-per-second-to-metre-per-second",
}
MOVED = "shipped general changed: recompute general_successor in fixtures/candidate-contracts.json, or retire the fragment if its rows were admitted"


@pytest.mark.parametrize("namespace", STATIC)
def test_static_genesis_matches_its_register_and_oracle(base_contract, namespace):
    revision = candidate_history(namespace, base_contract)
    (row,) = [r for r in oracle()["static"] if r["contract_path"].endswith(f"/{namespace}/DOMAIN.yaml")]
    assert revision.contract.content_identity == row["contract_identity"]
    assert revision.contract.defining_source is not None
    assert revision.contract.defining_source.id == SOURCES[namespace]
    assert set(revision.register.entries) == KEYS[namespace]
    assert revision.register.previous is None
    assert {entry.status for entry in revision.register.entries.values()} == {"provisional"}


def test_general_successor_is_additive_with_exact_register_coverage(base_contract):
    shipped, pinned = shipped_domain_contract("general"), oracle()["general_successor"]
    assert shipped.content_identity == pinned["predecessor_identity"], MOVED
    *_, previous, current = general_successor_history(base_contract)
    assert previous.contract.content_identity == shipped.content_identity
    assert current.contract.content_identity == pinned["contract_identity"]
    assert current.contract.defining_source is not None
    assert current.contract.defining_source.id == GENERAL_SOURCE_ID
    assert register_entry_keys(current.contract) - register_entry_keys(shipped) == GENERAL_KEYS
    assert set(current.register.entries) == set(shipped_assumptions_register("general").entries) | GENERAL_KEYS
    assert all(current.register.entries[key].status == "provisional" for key in GENERAL_KEYS)


def test_time_successor_adds_exactly_the_fragment_keys_and_no_external_code(base_contract):
    genesis, successor = time_successor(base_contract)
    speed = fragment("si-brochure-speed")
    assert register_entry_keys(successor) - register_entry_keys(genesis) == SPEED_KEYS == set(speed["register_entries"])
    for fields in speed["register_entries"].values():
        entry = RegisterEntry(
            fields["collapses"], fields["licenses"], fields["not_established"], status=fields["status"]
        )
        assert entry.status == "provisional"
    assert all("external" not in unit for unit in speed["rows"]["units"].values())
    assert successor.defining_source == genesis.defining_source


def test_time_successor_survives_an_admitted_looking_genesis(base_contract):
    document = time_document()
    for name, code in (("second", "s"), ("hour", "h"), ("hertz", "Hz")):
        document["units"][name].update(external={"ucum": code}, definition="Stand-in for an admitted definition.")
    genesis, successor = time_successor(base_contract, genesis_document=document)
    assert genesis.content_identity != time_contract(base_contract).content_identity
    assert register_entry_keys(successor) - register_entry_keys(genesis) == SPEED_KEYS


@pytest.mark.parametrize(
    "lineage,table,name,change,message",
    [
        ("general", "designs", "independent-groups", None, "drops claim-vocabulary declaration"),
        (
            "general",
            "quantity_kinds",
            "relative-abundance",
            {"dimension": "counted"},
            "different canonical schema projection",
        ),
        ("si-brochure", "conversions", "hour-to-second", None, "drops claim-vocabulary declaration"),
        ("si-brochure", "conversions", "hour-to-second", {"factor": "3601"}, "different canonical schema projection"),
    ],
)
def test_a_changed_or_dropped_existing_row_refuses_succession(base_contract, lineage, table, name, change, message):
    derive = general_successor_document if lineage == "general" else time_successor_document
    document, predecessor = derive(base_contract)
    if change is None:
        del document[table][name]
    else:
        document[table][name].update(change)
    with pytest.raises(errors.SuccessionViolation, match=message):
        parse_domain_contract(
            document, source="<mutated candidate successor>", base=base_contract, predecessor=predecessor
        )


def test_a_fragment_row_that_already_exists_refuses_by_name(base_contract):
    document, shipped = general_successor_document(base_contract)
    with pytest.raises(ValueError, match="general already declares designs.within-anchor-windows"):
        with_rows(document, shipped, {"designs": {"within-anchor-windows": {}}})


def test_halo_class_register_pins_the_documented_criterion(base_contract):
    entry = candidate_history("catalogue-anchors", base_contract).register.entries[
        "sort:catalogue-anchors/cdaw-halo-cme"
    ]
    for pinned in (
        "CMEs an apparent width of 360 deg are marked as Halo in the CPA column.",
        "https://cdaw.gsfc.nasa.gov/CME_list/catalog_description.htm",
        "2026-10-11T18:39:52Z",
        "dc30ab9357df22dc31899ab9650c4502a8297e229d835ce68b65a98dbb46a357",
    ):
        assert pinned in entry.collapses
    assert "revised in place" in entry.not_established


SPEED_MISSING = (
    "plasma-populations: measurements quantity kind names 'si-brochure/speed', which no activated contract declares"
)
OMISSIONS = [
    ("si-brochure", errors.ProfileError, SPEED_MISSING),
    ("speed", errors.ProfileError, SPEED_MISSING),
    (
        "general-successor",
        errors.ProfileError,
        (
            "catalogue-anchors: dimensions.anchor-epoch: applies_to names 'general/event-locked-change', which is no operator "
            "(template or bridge) an activated contract declares"
        ),
    ),
    (
        "plasma-populations",
        errors.MalformedContract,
        (
            "catalogue-anchors: instantiations.halo-anchored-solar-wind-speed: roles.response names sort "
            "'plasma-populations/near-earth-solar-wind', but no compiled contract declares sort"
        ),
    ),
]
TERMS = {
    "plasma-populations/near-earth-solar-wind": "plasma-population:near-earth-solar-wind",
    "plasma-populations/bulk-flow-speed": "plasma-aspect:bulk-flow-speed",
    "catalogue-anchors/cdaw-halo-cme": "catalogue-class:cdaw-halo-cme",
}


def test_candidate_profile_compiles_with_four_explicit_lineages(base_contract):
    profile = candidate_profile(base_contract)
    assert set(profile.activated_contracts) == {"general", "si-brochure", "plasma-populations", "catalogue-anchors"}
    assert dict(profile.defining_sources) == {
        "general": GENERAL_SOURCE_ID,
        "si-brochure": "urn:beliefs:source:bipm-si-brochure",
        **SOURCES,
    }


@pytest.mark.parametrize("omitted,error,message", OMISSIONS)
def test_each_omission_refuses_at_the_first_unresolved_reference(base_contract, omitted, error, message):
    with pytest.raises(error, match=re.escape(message)):
        candidate_profile(base_contract, omit={omitted})


def test_each_sort_admits_its_one_term_and_no_other_token(base_contract):
    profile, snapshot = candidate_profile(base_contract), build_snapshot(readable={})
    for sort, term in TERMS.items():
        assert snapshot.resolve(profile.sorts[sort], term) is TermOutcome.MEMBER
        assert snapshot.resolve(profile.sorts[sort], term + "-other") is TermOutcome.NOT_MEMBER


def test_the_speed_conversion_is_the_exact_factor_1000(base_contract):
    found = candidate_profile(base_contract).conversion_between(
        "si-brochure/metre-per-second", "si-brochure/kilometre-per-second"
    )
    assert found is not None
    assert (found.from_unit, found.to_unit, found.kind, found.factor, found.exact, found.offset, found.error) == (
        "si-brochure/kilometre-per-second",
        "si-brochure/metre-per-second",
        "multiplicative",
        Fraction(1000),
        True,
        None,
        None,
    )
