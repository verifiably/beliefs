from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path
from typing import Any

import pytest

from science.dataset import (
    ByteObservation,
    DatasetDeclaration,
    Declared,
    Held,
    ResourceDeclaration,
    admission_state,
)
from science.errors import SubclassRefused
from science.holdings.adapter import DatasetAnswer, DatasetBlocked, dataset_observations

D = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
S512 = "sha512:" + "4" * 128
LOCATION = "store:" + "a" * 32 + ":data.bin"
OTHER_LOCATION = "store:" + "b" * 32 + ":data.bin"


def declaration(digest: str = D) -> DatasetDeclaration:
    return DatasetDeclaration((ResourceDeclaration("data", digest),))


def member(
    digest: str | None,
    *,
    location: str = LOCATION,
    expected: str | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    outcome = {"finding": "absent"} if digest is None else {"finding": "found", "digest": digest}
    value: dict[str, Any] = {
        "head": "f" * 64,
        "location": location,
        "outcome": outcome,
        "history": history or [],
    }
    if expected is not None:
        value["expected"] = expected
    return value


def blocked(location: str, reasons: list[str], *heads: dict[str, Any]) -> dict[str, Any]:
    return {"location": location, "reasons": reasons, "heads": list(heads)}


def test_outcome_join_promotes_a_matching_found():
    answer = dataset_observations(declaration(), [member(D)], [])

    assert answer == DatasetAnswer((ByteObservation(D, LOCATION),))
    assert isinstance(answer, DatasetAnswer)
    assert isinstance(admission_state(declaration(), answer.observations), Held)


def test_a_different_digest_never_promotes_on_presence():
    answer = dataset_observations(declaration(), [member(D2, expected=D)], [])

    assert answer == DatasetAnswer((ByteObservation(D2, LOCATION),))
    assert isinstance(answer, DatasetAnswer)
    state = admission_state(declaration(), answer.observations)
    assert isinstance(state, Declared)
    assert any(finding.outcome == "mismatch" and finding.observed == (D2,) for finding in state.findings)


def test_expectation_join_surfaces_a_first_contact_mismatch():
    answer = dataset_observations(declaration(), [member(D2, expected=D)], [])

    assert answer == DatasetAnswer((ByteObservation(D2, LOCATION),))


def test_history_join_reaches_a_superseded_match():
    history = [{"ref": "e" * 64, "outcome": {"finding": "found", "digest": D}}]
    expected_history = [
        {
            "ref": "d" * 64,
            "outcome": {"finding": "found", "digest": D3},
            "expected": D,
        }
    ]

    found = dataset_observations(declaration(), [member(D2, history=history)], [])
    expected = dataset_observations(declaration(), [member(D2, history=expected_history)], [])
    absent = dataset_observations(declaration(), [member(None, history=history)], [])

    assert found == DatasetAnswer((ByteObservation(D2, LOCATION),))
    assert expected == DatasetAnswer((ByteObservation(D2, LOCATION),))
    assert absent == DatasetAnswer(())


def test_history_join_is_commensurability_gated():
    history = [{"ref": "e" * 64, "outcome": {"finding": "found", "digest": D}}]

    answer = dataset_observations(declaration(), [member(S512, history=history)], [])

    assert answer == DatasetAnswer(())
    assert isinstance(answer, DatasetAnswer)
    state = admission_state(declaration(), answer.observations)
    assert isinstance(state, Declared)
    assert [finding.outcome for finding in state.findings] == ["no-matching-observation-in-coverage"]


@pytest.mark.parametrize(
    "head",
    [
        member(D, location=OTHER_LOCATION),
        member(D2, location=OTHER_LOCATION, expected=D),
        member(
            D2,
            location=OTHER_LOCATION,
            history=[{"ref": "e" * 64, "outcome": {"finding": "found", "digest": D}}],
        ),
    ],
)
def test_a_blocked_hit_refuses_that_datasets_answer(head: dict[str, Any]):
    answer = dataset_observations(
        declaration(),
        [{}],  # invalid if touched: the blocked pass must answer first
        [
            blocked(OTHER_LOCATION, ["unsettled", "contested"], head),
            blocked(LOCATION, ["contested"], member(D)),
        ],
    )

    assert answer == DatasetBlocked(
        locations=(LOCATION, OTHER_LOCATION),
        reasons=("contested", "unsettled"),
    )


def test_a_blocked_unclaimed_locator_blocks_nothing_but_itself():
    blocked_members = [
        blocked(OTHER_LOCATION, ["unsettled"], member(D2, location=OTHER_LOCATION)),
        blocked(LOCATION, ["unsettled"]),
    ]

    claimed = dataset_observations(declaration(D2), [], blocked_members)
    other = dataset_observations(declaration(D), [member(D)], blocked_members)

    assert claimed == DatasetBlocked((OTHER_LOCATION,), ("unsettled",))
    assert other == DatasetAnswer((ByteObservation(D, LOCATION),))


def test_an_unjoined_head_enters_nothing():
    answer = dataset_observations(declaration(), [member(D2)], [])

    assert answer == DatasetAnswer(())
    assert isinstance(answer, DatasetAnswer)
    state = admission_state(declaration(), answer.observations)
    assert isinstance(state, Declared)
    assert [finding.outcome for finding in state.findings] == ["no-matching-observation-in-coverage"]


def test_observations_are_deduplicated_and_sorted_by_digest_then_location():
    answer = dataset_observations(
        DatasetDeclaration((ResourceDeclaration("one", D), ResourceDeclaration("two", D2))),
        [
            member(D2),
            member(D, location=OTHER_LOCATION),
            member(D),
            member(D),
        ],
        [],
    )

    assert answer == DatasetAnswer(
        (
            ByteObservation(D, LOCATION),
            ByteObservation(D, OTHER_LOCATION),
            ByteObservation(D2, LOCATION),
        )
    )


def test_the_adapter_reads_only_its_inputs():
    assert tuple(inspect.signature(dataset_observations).parameters) == ("declaration", "active", "blocked")
    source = Path(inspect.getfile(dataset_observations)).read_text(encoding="utf-8")
    assert all(
        forbidden not in source
        for forbidden in ("science.world", "science.root", "science.corpus", "pathlib", "Path(")
    )


def test_the_result_types_have_exact_fields_and_are_final():
    assert [field.name for field in dataclasses.fields(DatasetAnswer)] == ["observations"]
    assert [field.name for field in dataclasses.fields(DatasetBlocked)] == ["locations", "reasons"]
    assert getattr(DatasetAnswer, "__final__", False) and getattr(DatasetBlocked, "__final__", False)


@pytest.mark.parametrize("result_type", [DatasetAnswer, DatasetBlocked])
def test_the_result_types_are_sealed_at_runtime(result_type: type[object]):
    with pytest.raises(SubclassRefused):
        type("InvalidResult", (result_type,), {})
