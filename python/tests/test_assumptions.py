"""Assumption instances require vocabulary particulars, permitting additional evidence."""

from typing import cast

import pytest

from beliefs.assumptions import AssumptionInstance, check_instance, instance_from_projection, instance_projection
from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedRecord
from beliefs.identity.v1 import encode
from beliefs.profile import compile_profile


def test_required_particulars_are_present_and_extra_keys_are_admitted(base_contract, testing_document):
    profile = compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<assumptions>", base=base_contract, predecessor=None)],
    )
    particulars = {"record": "proxy", "co_scope": "equal", "dimensions": "{}"}
    for extras in ({}, {"error": "1.4"}):
        check_instance(profile, AssumptionInstance("testing/proxy-validity", particulars | extras))
    del particulars["co_scope"]
    with pytest.raises(MalformedRecord):
        check_instance(profile, AssumptionInstance("testing/proxy-validity", particulars))
    with pytest.raises(MalformedRecord):
        check_instance(profile, AssumptionInstance("testing/unknown", {}))


def test_projection_has_no_nulls_and_round_trips():
    raw = {"a": "b"}
    value = AssumptionInstance("testing/proxy-validity", raw)
    raw.clear()
    assert instance_projection(value) == {"kind": "testing/proxy-validity", "particulars": {"a": "b"}}
    assert instance_from_projection(instance_projection(value)) == value
    encode(instance_projection(value))
    with pytest.raises(TypeError):
        cast(dict[str, str], value.particulars)["x"] = "y"


@pytest.mark.parametrize(
    "kind, particulars",
    [
        ("bad", {}),
        ("testing/x", {1: "v"}),
        ("testing/x", {"k": 1}),
        ("testing/x", {"k": "e\u0301"}),
        ("testing/x", {"k": "\ud800"}),
    ],
)
def test_field_grammar(kind, particulars):
    with pytest.raises(MalformedRecord):
        AssumptionInstance(kind, particulars)


@pytest.mark.parametrize(
    "value", [{}, {"kind": "testing/x", "particulars": {}, "extra": 1}, {"kind": "testing/x", "particulars": None}]
)
def test_instance_reader_has_exact_shape(value):
    with pytest.raises(MalformedRecord):
        instance_from_projection(value)
