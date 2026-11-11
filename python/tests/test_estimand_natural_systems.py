"""Quantity and named law outputs represent the natural-systems targets."""

from dataclasses import replace
from decimal import Decimal as D
from typing import Any

import pytest
from fixtures_cut3 import MEASUREMENT_RECORDS, RESPONSE
from test_estimand import (
    build,
)
from test_estimand import (
    context as context,  # noqa: PLC0414 — shared pytest fixture
)

from beliefs.claim import Member, Referent, build_claim
from beliefs.errors import EstimandError
from beliefs.estimand import MeasuredBinding, NullReference, OutputSpec, ValueReference, estimand_projection
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Procedure


def test_peak_power_fraction_has_no_contrast_and_cannot_claim_null():
    e = build(
        form="quantity",
        functional="testing/peak-power-fraction",
        bindings={"response": RESPONSE},
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(D(".5")),
    )
    assert e.form == "quantity" and tuple(e.outputs) == ("estimate",)
    with pytest.raises(EstimandError):
        build(
            form="quantity",
            functional="testing/peak-power-fraction",
            bindings={"response": RESPONSE},
            outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
            reference=NullReference(D(0), D(1)),
        )


def test_power_law_has_a_named_nonempty_independent_list(context):
    kwargs: dict[str, Any] = {
        "form": "law-parameters",
        "functional": "testing/power-law-floor",
        "outputs": {"beta": OutputSpec("dimensionless", "real")},
        "reference": {"beta": ValueReference(D(0))},
    }
    e = build(context, bindings={"response": RESPONSE, "independent": (("scale", RESPONSE),)}, **kwargs)
    assert tuple(e.outputs) == ("beta",)
    for independent in [(), (("scale", RESPONSE), ("scale", RESPONSE))]:
        with pytest.raises(EstimandError):
            build(context, bindings={"response": RESPONSE, "independent": independent}, **kwargs)


def test_directed_association_order_and_symmetric_order(context):
    # Two legitimate members of one many role keep bearer terms distinct.
    from fixtures_cut3 import FixtureRecords

    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    a = Referent("testing/event", "EX:a")
    b = Referent("testing/product", "EX:b")
    claim = build_claim(
        context,
        operator="testing/correlates-with",
        roles={"parties": (Member(a), Member(b))},
        layer="statistical",
        polarity="positive",
    )

    def measured(ref, kind, unit):
        observable = Observable(kind, ref.sort)
        id = records.put_procedure(
            Procedure("testing/assay", ref.term, "Measure.", (observable,), None, {}, (), (), None, None, {}, None)
        )
        return MeasuredBinding(
            "parties", ref, Measure(observable, unit, None, "ratio", "level", "testing/identity", id), None, None
        )

    values = (
        ("a", measured(a, "testing/energy", "testing/electronvolt")),
        ("b", measured(b, "testing/abundance", "testing/tpm")),
    )
    for name, domain, equal in [
        ("spearman-correlation", "signed-unit-interval", True),
        ("transfer-entropy", "nonnegative", False),
    ]:
        kwargs: dict[str, Any] = {
            "form": "association",
            "functional": "testing/" + name,
            "outputs": {"estimate": OutputSpec("dimensionless", domain)},
            "reference": ValueReference(D(0)),
            "records": records,
        }
        left = build(context, claim, bindings={"variables": values}, **kwargs)
        right = build(context, claim, bindings={"variables": tuple(reversed(values))}, **kwargs)
        assert (estimand_projection(left) == estimand_projection(right)) == equal
        absent = replace(values[0][1], member=Referent("testing/event", "EX:absent"))
        with pytest.raises(EstimandError):
            build(context, claim, bindings={"variables": (("a", absent), values[1])}, **kwargs)
