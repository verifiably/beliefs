from dataclasses import FrozenInstanceError

import pytest

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused

HEX_A = "a" * 32
HEX_B = "b" * 32
HEX_C = "c" * 32


@pytest.mark.parametrize(
    ("wire", "value"),
    [
        (f"coord:{HEX_A}", CoordinationAddress(HEX_A)),
        (f"coord:{HEX_A}@{HEX_C}", CoordinationAddress(HEX_A, revision=HEX_C)),
        (f"coord:{HEX_A}/{HEX_B}", CoordinationAddress(HEX_A, HEX_B)),
        (f"coord:{HEX_A}/{HEX_B}@{HEX_C}", CoordinationAddress(HEX_A, HEX_B, HEX_C)),
    ],
)
def test_coordination_addresses_round_trip_exactly(wire, value):
    assert CoordinationAddress.parse(wire) == value
    assert str(value) == wire


@pytest.mark.parametrize(
    "wire",
    [
        "coord:a",
        f"coord:{HEX_A.upper()}",
        f"coord:{HEX_A}/",
        f"coord:{HEX_A}//{HEX_B}",
        f"project:{HEX_A}",
    ],
)
def test_coordination_addresses_refuse_noncanonical_text(wire):
    with pytest.raises(ValueError, match="coordination address"):
        CoordinationAddress.parse(wire)


def test_coordination_addresses_are_frozen():
    address = CoordinationAddress(HEX_A)
    with pytest.raises(FrozenInstanceError):
        address.project = HEX_B  # pyright: ignore[reportAttributeAccessIssue]


def test_the_resolver_refusal_vocabulary_is_closed_and_tips_are_canonical():
    assert CoordinationRefused("divergent-view", (HEX_B, HEX_A, HEX_A)).tips == (HEX_A, HEX_B)
    with pytest.raises(ValueError, match="reason"):
        CoordinationRefused("new-reason", ())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="tip"):
        CoordinationRefused("divergent-view", ("bad",))


def test_the_world_inventory_is_exactly_the_thirteen_banked_kinds():
    assert stored.WORLD_KINDS == (
        "proposition",
        "source-assertion",
        "assessment",
        "analysis-spec",
        "run",
        "verification",
        "dataset",
        "source",
        "holdings-observation",
        "retraction",
        "instrument-certification",
        "coreference-attestation",
        "act-report",
    )
    assert not set(stored.WORLD_KINDS) & {
        "project",
        "question",
        "hypothesis",
        "topic",
        "theme",
        "task",
        "decision",
        "note",
    }
