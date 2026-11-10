"""The remaining checks: all five outcomes, three availability states, and the
six binding arms (§7.4's outcome table)."""

from typing import cast

import pytest
from domain_facet_fixtures import EX, GENE

from beliefs.contract.domain import (
    DatasetBinding,
    RunOutputBinding,
    SchemeBinding,
    SelectionBinding,
    WorldKindBinding,
)
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import ResolutionError
from beliefs.profile import compile_profile
from beliefs.resolution import TermOutcome, build_snapshot

CATALOGUE = DatasetBinding(dataset="dataset:" + "1" * 64)
"""`testing/event`'s selection `dataset`: the catalogue the rule was applied to."""
SELECTED = DatasetBinding(dataset="dataset:" + "3" * 64)
PRODUCED = DatasetBinding(dataset="dataset:" + "5" * 64)
PROCEDURE = "procedure:" + "a" * 64
OTHER_PROCEDURE = "procedure:" + "b" * 64


@pytest.fixture()
def profile(base_contract, testing_contract_path):
    from beliefs.contract import load_domain_contract

    testing = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def entity(profile):
    """`testing/entity`, bound by release to `EX`."""
    return profile.sorts["testing/entity"]


def test_not_present_is_produced_and_carries_its_corpus(entity):
    snapshot = build_snapshot(not_present={EX: "beta"})
    binding = cast(list[dict[str, object]], snapshot.projection()["bindings"])[0]
    assert snapshot.resolve(entity, GENE) is TermOutcome.NOT_PRESENT
    assert binding["state"] == "not-present"
    assert binding["absent"] == ["beta"]


def test_the_five_outcomes_are_pairwise_distinct(entity):
    readable = build_snapshot(readable={EX: [GENE]})
    outcomes = {
        readable.resolve(entity, GENE),
        readable.resolve(entity, "EX:other"),
        build_snapshot().resolve(entity, GENE),
        build_snapshot(unreadable=[EX]).resolve(entity, GENE),
        build_snapshot(not_present={EX: "beta"}).resolve(entity, GENE),
    }
    assert outcomes == set(TermOutcome)


def test_the_identity_moves_across_the_three_availability_states():
    identities = {
        build_snapshot(readable={EX: []}).identity,
        build_snapshot(unreadable=[EX]).identity,
        build_snapshot(not_present={EX: "beta"}).identity,
        build_snapshot(not_present={EX: "gamma"}).identity,
    }
    assert len(identities) == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"readable": {EX: []}, "unreadable": [EX]},
        {"readable": {EX: []}, "not_present": {EX: "beta"}},
        {"unreadable": [EX], "not_present": {EX: "beta"}},
    ],
)
def test_overlapping_inputs_refuse(kwargs):
    with pytest.raises(ResolutionError):
        build_snapshot(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"readable": {"EX": GENE}},
        {"not_present": {"EX": ""}},
    ],
)
def test_an_invalid_binding_is_refused_before_its_value_is_inspected(kwargs):
    with pytest.raises(ResolutionError, match="keyed by SortBinding"):
        build_snapshot(**kwargs)


# --- the six arms -----------------------------------------------------------------


def test_scheme_is_always_performed(profile):
    """Case 13: a `scheme` sort's membership is its identifier class, so the
    check is performed against every snapshot, an empty one included, and the
    receipt records it as performed."""
    method = profile.sorts["testing/method"]
    assert isinstance(method.binding, SchemeBinding)
    for snapshot in (build_snapshot(), build_snapshot(readable={EX: []}), build_snapshot(unreadable=[EX])):
        assert snapshot.resolve(method, "EX:assay") is TermOutcome.MEMBER
        assert snapshot.resolve(method, "EX:Not-In-Class") is TermOutcome.NOT_MEMBER
        assert snapshot.resolve(method, "EX:assay").performed

    wire = WireClaim(
        operator="testing/measured-by",
        roles={
            "subject": {"sort": "testing/entity", "term": GENE},
            "instrument": {"sort": "testing/method", "term": "EX:assay"},
        },
        qualifiers={},
        form="polar",
        polarity="inapt",
        layer="methodological",
    )
    _, receipt = decode_claim(wire, profile=profile, snapshot=build_snapshot())
    assert receipt.outcomes == {"role:instrument": TermOutcome.MEMBER, "role:subject": TermOutcome.NOT_CONSULTED}


def test_a_scheme_binding_is_not_a_vocabulary_key(profile):
    with pytest.raises(ResolutionError, match="identifier class"):
        build_snapshot(readable={profile.sorts["testing/method"].binding: ["EX:assay"]})


@pytest.mark.parametrize(
    ("sort", "dataset"),
    [("testing/event", SELECTED), ("testing/product", PRODUCED)],
)
def test_selection_and_run_output_resolve_through_datasets(profile, sort, dataset):
    """Both are the dataset arm plus provenance, so each resolves exactly as the
    dataset arm over the dataset it names — `selected` for a selection, the
    produced `dataset` for a run output — through every availability state."""
    declared = profile.sorts[sort]
    term = "EX:member-1"
    assert build_snapshot(readable={dataset: [term]}).resolve(declared, term) is TermOutcome.MEMBER
    assert build_snapshot(readable={dataset: []}).resolve(declared, term) is TermOutcome.NOT_MEMBER
    assert build_snapshot(unreadable=[dataset]).resolve(declared, term) is TermOutcome.NOT_AVAILABLE
    assert build_snapshot(not_present={dataset: "beta"}).resolve(declared, term) is TermOutcome.NOT_PRESENT
    assert build_snapshot().resolve(declared, term) is TermOutcome.NOT_CONSULTED


def test_a_selection_reads_its_selected_dataset_never_its_catalogue(profile):
    event = profile.sorts["testing/event"]
    assert isinstance(event.binding, SelectionBinding) and event.binding.dataset == CATALOGUE.dataset
    assert build_snapshot(readable={CATALOGUE: ["EX:member-1"]}).resolve(event, "EX:member-1") is (
        TermOutcome.NOT_CONSULTED
    )


@pytest.mark.parametrize("sort", ["testing/event", "testing/product", "testing/procedure-spec"])
def test_an_arm_resolved_elsewhere_is_not_a_vocabulary_key(profile, sort):
    binding = profile.sorts[sort].binding
    assert isinstance(binding, SelectionBinding | RunOutputBinding | WorldKindBinding)
    with pytest.raises(ResolutionError, match="would never be read"):
        build_snapshot(readable={binding: []})
    with pytest.raises(ResolutionError, match="would never be read"):
        build_snapshot(unreadable=[binding])


def test_world_kind_not_consulted_without_inventory_member_with_one(profile):
    spec = profile.sorts["testing/procedure-spec"]
    assert isinstance(spec.binding, WorldKindBinding)
    assert build_snapshot().resolve(spec, PROCEDURE) is TermOutcome.NOT_CONSULTED
    assert build_snapshot(kinds={"run": ["run:" + "c" * 64]}).resolve(spec, PROCEDURE) is TermOutcome.NOT_CONSULTED
    held = build_snapshot(kinds={"procedure": [PROCEDURE]})
    assert held.resolve(spec, PROCEDURE) is TermOutcome.MEMBER
    assert held.resolve(spec, OTHER_PROCEDURE) is TermOutcome.NOT_MEMBER
    # An inventory of the kind that holds nothing was read: a finding, not silence.
    assert build_snapshot(kinds={"procedure": []}).resolve(spec, PROCEDURE) is TermOutcome.NOT_MEMBER


@pytest.mark.parametrize(
    "kinds",
    [
        {"procedure": PROCEDURE},
        {"procedure": ["run:" + "c" * 64]},
        {"procedure": ["procedure:" + "A" * 64]},
        {"procedure": [7]},
        {"Procedure": [PROCEDURE]},
        {7: [PROCEDURE]},
        [("procedure", [PROCEDURE])],
    ],
)
def test_an_inventory_holds_record_ids_of_its_kind(kinds):
    """A held id outside its kind's record-id grammar is a member no claim can
    name — the identifier class of a world-kind sort is that grammar — so it is
    refused rather than stored."""
    with pytest.raises(ResolutionError):
        build_snapshot(kinds=kinds)  # type: ignore[arg-type]


def test_snapshot_projection_is_injective_across_arms():
    """Every vocabulary entry carries its binding's arm tag, and the world-kind
    inventory is its own member, present only when one is carried: so no two
    distinct availability states share an identity, and a snapshot without an
    inventory projects as it did before inventories existed."""
    snapshots = {
        "nothing": build_snapshot(),
        "release": build_snapshot(readable={EX: []}),
        "dataset": build_snapshot(readable={SELECTED: []}),
        "other-dataset": build_snapshot(readable={PRODUCED: []}),
        "procedure-empty": build_snapshot(kinds={"procedure": []}),
        "procedure-held": build_snapshot(kinds={"procedure": [PROCEDURE]}),
        "run-empty": build_snapshot(kinds={"run": []}),
        "release-and-procedure": build_snapshot(readable={EX: []}, kinds={"procedure": []}),
    }
    assert len({snapshot.identity for snapshot in snapshots.values()}) == len(snapshots)
    assert build_snapshot(kinds={}).identity == snapshots["nothing"].identity
    assert snapshots["release"].projection() == {"bindings": [{"binding": EX.projection(), **_readable([])}]}
    assert snapshots["procedure-held"].projection() == {"bindings": [], "kinds": {"procedure": [PROCEDURE]}}
    for snapshot in snapshots.values():
        for entry in cast(list[dict[str, dict[str, str]]], snapshot.projection()["bindings"]):
            assert entry["binding"]["kind"] in {"release", "dataset"}


def _readable(terms: list[str]) -> dict[str, object]:
    return {"state": "readable", "terms": terms, "absent": []}


def test_the_snapshot_identity_is_taken_under_its_v2_domain():
    """v2: every binding projects with its arm's `kind` tag, so every non-empty
    snapshot changed shape, and a new shape takes a new domain."""
    from beliefs.identity import v1
    from beliefs.resolution import SNAPSHOT_DOMAIN

    assert SNAPSHOT_DOMAIN == "science.snapshot.v2"
    for snapshot in (build_snapshot(), build_snapshot(readable={EX: []}), build_snapshot(kinds={"procedure": []})):
        assert snapshot.identity == v1.digest("science.snapshot.v2", snapshot.projection())
