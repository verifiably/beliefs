"""D3's remaining arm: all five outcomes and three availability states."""

from typing import cast

import pytest
from test_evaluation import EX, GENE

from beliefs.errors import ResolutionError
from beliefs.resolution import TermOutcome, build_snapshot


def test_not_present_is_produced_and_carries_its_corpus():
    snapshot = build_snapshot(not_present={EX: "beta"})
    binding = cast(list[dict[str, object]], snapshot.projection()["bindings"])[0]
    assert snapshot.resolve(EX, GENE) is TermOutcome.NOT_PRESENT
    assert binding["state"] == "not-present"
    assert binding["absent"] == ["beta"]


def test_the_five_outcomes_are_pairwise_distinct():
    readable = build_snapshot(readable={EX: [GENE]})
    outcomes = {
        readable.resolve(EX, GENE),
        readable.resolve(EX, "EX:other"),
        build_snapshot().resolve(EX, GENE),
        build_snapshot(unreadable=[EX]).resolve(EX, GENE),
        build_snapshot(not_present={EX: "beta"}).resolve(EX, GENE),
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
    with pytest.raises(ResolutionError, match="keyed by VocabularyBinding"):
        build_snapshot(**kwargs)
