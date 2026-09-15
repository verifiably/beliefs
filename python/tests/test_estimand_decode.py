"""Round trips and refusals at the decode boundary (M11's shape, one artifact over)."""

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

import pytest
from test_estimand import E, I, L, M, O, build, parts  # noqa: F401 — fixtures re-exported by name

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.decode import WireEstimand, applicability_from_stored, decode_estimand, estimand_from_stored
from beliefs.errors import ContrastRefused, EstimandSortMismatch, MalformedWireEstimand
from beliefs.estimand import Control, applicability_projection, build_applicability, estimand_projection
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.resolution import build_snapshot


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


def test_a_projection_round_trips_through_canonical_text(profile, claim):
    estimand = build(profile, claim, build_snapshot(readable={}))
    projection = estimand_projection(estimand)
    restored = estimand_from_stored(cast("Mapping[str, object]", v1.decode(v1.encode(projection))), profile=profile)
    assert estimand_projection(restored) == projection
    assert restored.reference == Decimal(0) and type(restored.reference) is Decimal


def test_decode_types_a_wire_value_and_resolves_it(profile, claim):
    from beliefs.projection import claim_identity

    wire = WireEstimand(
        claim=claim_identity(claim), operator="testing/affects",
        contrast={"slot": 0, "kind": "levels", "baseline": "EX:ndmm", "comparison": "EX:pd"},
        measure={"quantity": "EX:tpm", "scale": "additive"}, reference=Decimal(0),
        control={"identification": "EX:observational", "conditioning": []},
    )
    estimand, receipt = decode_estimand(wire, profile=profile, snapshot=build_snapshot(readable={}))
    assert estimand_projection(estimand) == estimand_projection(build(profile, claim, build_snapshot(readable={})))
    assert "estimand:measure.quantity" in receipt.outcomes


@pytest.mark.parametrize("mutate,error", [
    (lambda p: p.pop("reference"), MalformedWireEstimand),
    (lambda p: p.__setitem__("extra", 1), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("kind", "levels-and-continuous"), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("slot", "0"), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("baseline", {"sort": E, "term": "EX:ndmm"}), EstimandSortMismatch),
    (lambda p: p["measure"].__setitem__("quantity", {"sort": 7, "term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["measure"].__setitem__("quantity", {"sort": "", "term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["measure"].__setitem__("quantity", {"term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["measure"].__setitem__("quantity", "EX:tpm"), MalformedWireEstimand),  # the whole wrapper removed: a bare term is the wire form's
    (lambda p: p["control"].__setitem__("conditioning", ["EX:c"]), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("comparison", {"sort": L, "term": "EX:ndmm"}), ContrastRefused),
    (lambda p: p.__setitem__("reference", "zero"), MalformedWireEstimand),
    (lambda p: p["control"].__setitem__("conditioning", "none"), MalformedWireEstimand),
])
def test_ill_formed_stored_projections_refuse_never_repair(profile, claim, mutate, error):
    projection = estimand_projection(build(profile, claim, build_snapshot(readable={})))
    mutate(projection)
    with pytest.raises(error):
        estimand_from_stored(projection, profile=profile)


def test_a_duplicate_conditioning_member_refuses_through_the_sealed_constructor(profile, claim):
    """A stored projection cannot rebuild an estimand `Control.__post_init__`
    would have refused: the decoder must construct every member through the
    sealed types, never hand raw tuples straight to `Estimand._checked`."""
    from beliefs.errors import ControlRefused

    projection = estimand_projection(build(
        profile, claim, build_snapshot(readable={}),
        control=Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),)),
    ))
    cast(dict, projection["control"])["conditioning"] = [{"sort": E, "term": "EX:c"}, {"sort": E, "term": "EX:c"}]
    with pytest.raises(ControlRefused, match="duplicate"):
        estimand_from_stored(projection, profile=profile)


def test_applicability_round_trips_and_refuses_an_undeclared_dimension(profile, claim):
    from beliefs.errors import UndeclaredDimension

    adults, _ = build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))}, snapshot=build_snapshot(readable={}))
    projection = applicability_projection(adults)
    restored = applicability_from_stored(cast("Mapping[str, object]", v1.decode(v1.encode(projection))), profile=profile, operator="testing/affects")
    assert applicability_projection(restored) == projection
    with pytest.raises(UndeclaredDimension):
        applicability_from_stored({"testing/regime": projection["testing/population"]}, profile=profile, operator="testing/affects")
    with pytest.raises(MalformedWireEstimand, match="bare term"):
        applicability_from_stored({"testing/population": {"quantifier": "generic", "restriction": "EX:adults"}}, profile=profile, operator="testing/affects")
