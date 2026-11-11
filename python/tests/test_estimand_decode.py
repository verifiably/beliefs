"""Stored v2 codecs validate shape without consulting the world."""

from copy import deepcopy
from decimal import Decimal
from typing import cast

import pytest
from fixtures_cut3 import TESTING_PROFILE, typed_estimand

from beliefs.errors import ScienceError
from beliefs.estimand import ValueReference, estimand_from_stored, estimand_projection
from beliefs.identity import v1


@pytest.mark.parametrize(
    "field",
    [
        "claim",
        "operator",
        "form",
        "functional",
        "bindings",
        "outputs",
        "reference",
        "control",
        "uncertainty",
        "assumptions",
        "dependencies",
    ],
)
def test_every_required_field_is_required(field):
    body = estimand_projection(typed_estimand())
    del body[field]
    with pytest.raises(ScienceError):
        estimand_from_stored(body, profile=TESTING_PROFILE)


@pytest.mark.parametrize(
    "edit",
    [
        lambda b: b.update(extra="ignored?"),
        lambda b: b.update(calibration=None),
        lambda b: b["bindings"].update(extra={}),
        lambda b: b["bindings"]["response"].update(member=None),
        lambda b: b["outputs"]["estimate"].update(unit="testing/tpm"),
        lambda b: b["reference"].update(value=0.5),
        lambda b: b["reference"].update(value=Decimal("NaN")),
        lambda b: b["dependencies"].append(b["dependencies"][0]),
        lambda b: b["dependencies"].clear(),
        lambda b: b.update(reference={"kind": "guess", "value": Decimal(1)}),
        lambda b: b["control"].update(extra="ignored?"),
    ],
)
def test_malformed_or_noncanonical_projection_refuses(edit):
    body = deepcopy(estimand_projection(typed_estimand()))
    edit(body)
    with pytest.raises(ScienceError):
        estimand_from_stored(body, profile=TESTING_PROFILE)


def test_canonical_numeric_text_and_distinct_reference():
    a = estimand_projection(typed_estimand())
    b = estimand_projection(typed_estimand(reference=ValueReference(Decimal("0.500"))))
    assert a != b
    assert b"0.5" in v1.encode(b)
    assert estimand_from_stored(v1.decode(v1.encode(b)), profile=TESTING_PROFILE).reference == ValueReference(
        Decimal(".5")
    )


def test_v1_shape_is_refused():
    with pytest.raises(ScienceError):
        estimand_from_stored(
            {
                "claim": "x",
                "operator": "testing/affects",
                "contrast": {},
                "measure": {},
                "reference": Decimal(0),
                "control": {},
            },
            profile=TESTING_PROFILE,
        )


def test_many_member_spelling_preserves_the_claims_nfc_identity():
    from fixtures_cut3 import event_estimand

    from beliefs.claim import Member, Referent, build_claim

    values = []
    for term in ["EX:e\u0301", "EX:é"]:
        claim = build_claim(
            TESTING_PROFILE,
            operator="testing/correlates-with",
            roles={"parties": (Member(Referent("testing/event", term)), Member(Referent("testing/product", "EX:p")))},
            layer="statistical",
            polarity="positive",
        )
        e = event_estimand(claim)
        body = estimand_projection(e)
        assert estimand_from_stored(body, profile=TESTING_PROFILE) == e
        values.append(v1.encode(body))
    assert values[0] == values[1]


def test_duplicate_assumptions_are_not_a_canonical_stored_set():
    from beliefs.assumptions import AssumptionInstance

    e = typed_estimand(
        assumptions=(AssumptionInstance("testing/transport-exchangeability", {"dimensions": "", "co_scope": "equal"}),)
    )
    body = estimand_projection(e)
    assumptions = cast(list, body["assumptions"])
    assumptions.append(assumptions[0])
    with pytest.raises(ScienceError):
        estimand_from_stored(body, profile=TESTING_PROFILE)
