"""B4's absent-dataset arm and B5's read-ledger behavior."""

from __future__ import annotations

from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import pytest
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, profile_with, seed
from domain_facet_fixtures import testing_contract as _testing_contract
from test_evaluation import GENE, OTHER_GENE

from beliefs.belief import Belief, Records, Refused, evaluate
from beliefs.consulted import CorpusPins
from beliefs.contract import domain
from beliefs.errors import MalformedRecord
from beliefs.evaluation import evaluate_over, gather
from beliefs.facet_read import FacetRead
from beliefs.profile import compile_profile, shipped_base_contract


def _gathered(kwargs):
    return {k: v for k, v in kwargs.items() if k != "availability"}


def test_gather_reads_the_declared_facet_off_the_held_observed_dataset(tmp_path):
    profile = profile_with()
    view = seed(tmp_path)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert [row.key for row in inputs.observed_facets] == ["biology/gene-axis"]
    assert ("biology", "biology:" + profile.activated_contracts["biology"]) in inputs.consulted
    assert ("dataset", inputs.observed_facets[0].address) in inputs.read_trace


def test_records_accept_reader_rows_in_order_and_reject_other_carriers(tmp_path):
    profile = profile_with()
    first_view = seed(tmp_path / "a")
    second_view = seed(tmp_path / "b", axis="columns")
    first = gather(first_view, PROPOSITION_REF, **_gathered(kwargs_for(first_view, profile)))
    second = gather(second_view, PROPOSITION_REF, **_gathered(kwargs_for(second_view, profile)))
    rows = tuple(sorted(first.observed_facets + second.observed_facets, key=FacetRead.projection))
    Records(**{**first.records().__dict__, "observed_facets": rows})
    with pytest.raises(MalformedRecord, match="sorted"):
        Records(**{**first.records().__dict__, "observed_facets": tuple(reversed(rows))})
    fake = Mock(spec=FacetRead)
    fake.address, fake.key, fake.payload_digest = rows[0].address, rows[0].key, rows[0].payload_digest
    with pytest.raises(MalformedRecord, match="only the reader mints"):
        Records(**{**first.records().__dict__, "observed_facets": (fake,)})


def test_records_snapshot_the_reader_rows_from_a_caller_list(tmp_path):
    profile = profile_with()
    view = seed(tmp_path)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    supplied = list(inputs.observed_facets)
    records = Records(**{**inputs.records().__dict__, "observed_facets": supplied})  # type: ignore[arg-type]
    supplied.append(Mock(spec=FacetRead))
    assert records.observed_facets == inputs.observed_facets


def test_gather_and_evaluate_agree_on_the_consulted_set(tmp_path):
    profile = profile_with()
    view = seed(tmp_path)
    kwargs = kwargs_for(view, profile)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs))
    belief = evaluate_over(view, PROPOSITION_REF, **kwargs)
    assert isinstance(belief, Belief)
    assert inputs.closure().digest() == belief.belief_input_digest
    assert "biology" in dict(inputs.consulted)


def test_an_absent_observed_dataset_is_absent_from_gather(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, observes_missing=True)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.observed_facets == ()
    assert all(entry.role != "observes" for entry in inputs.runs["run-a"].inputs)
    assert len(cast(list[object], inputs.closure().projection["observes"])) == 1
    assert ("dataset", "dataset:d-missing") not in inputs.read_trace
    assert not isinstance(evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile)), Refused)


def test_the_member_is_present_and_empty_when_nothing_was_read(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, axis=None)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.closure().projection["observed_facets"] == []
    assert "biology" not in dict(inputs.consulted)


def test_a_payload_byte_change_moves_the_digest(tmp_path):
    profile = profile_with()
    rows_view = seed(tmp_path / "rows")
    columns_view = seed(tmp_path / "columns", axis="columns")
    rows = evaluate_over(rows_view, PROPOSITION_REF, **kwargs_for(rows_view, profile))
    columns = evaluate_over(columns_view, PROPOSITION_REF, **kwargs_for(columns_view, profile))
    assert isinstance(rows, Belief) and isinstance(columns, Belief)
    assert rows.value == columns.value
    assert rows.belief_input_digest != columns.belief_input_digest


def test_a_malformed_payload_refuses_the_derivation_through_evaluate_over(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, axis="")
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Refused) and result.reason.startswith("facet-payload-refused:")


def test_evaluate_over_refuses_a_pin_mismatch_before_evaluate_runs(tmp_path):
    profile = profile_with()
    view = seed(tmp_path)
    kwargs = kwargs_for(view, profile)
    pin = kwargs["context"].pins["c1"]
    wrong = CorpusPins(
        science_contract=pin.science_contract,
        domains={**pin.domains, "biology": "biology:" + "9" * 64},
    )
    result = evaluate_over(
        view, PROPOSITION_REF, **{**kwargs, "context": replace(kwargs["context"], pins={"c1": wrong})}
    )
    assert isinstance(result, Refused) and result.reason.startswith("profile-pin-mismatch: biology")


def test_old_facet_receipts_refuse_under_a_new_profile_identity(tmp_path):
    from profiles import FIXTURE, load_document

    loose = profile_with()
    view = seed(tmp_path)
    loose_kwargs = kwargs_for(view, loose)
    inputs = gather(view, PROPOSITION_REF, **_gathered(loose_kwargs))

    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    document["facets"]["gene-axis"]["fields"]["namespace"] = {"type": "string", "required": True}
    strict_contract = domain.parse_domain_contract(
        document, source="<strict>", base=shipped_base_contract(), predecessor=None
    )
    strict = compile_profile(shipped_base_contract(), [_testing_contract(), strict_contract])
    strict_kwargs = kwargs_for(view, strict)
    fresh = evaluate_over(view, PROPOSITION_REF, **strict_kwargs)
    stale = evaluate(
        proposition=PROPOSITION_REF,
        records=inputs.records(),
        availability=loose_kwargs["availability"],
        context=strict_kwargs["context"],
        binding=strict_kwargs["binding"],
        profile=strict,
    )
    assert isinstance(fresh, Refused) and fresh.reason.startswith("facet-payload-refused:")
    assert isinstance(stale, Refused) and stale.reason == "facet-read-profile-mismatch: biology"


# --- D6's facet arm, the isolated case (design §5.6) ------------------------


def _belief(view, profile):
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Belief), result
    return result


def test_isolated_case_biology_enters_through_the_ledger_alone(tmp_path):
    """The claim is at `testing/affects` over `testing` sorts; nothing in its
    schema reaches `biology`. With the facet read, biology is consulted; with
    the facet absent, it is not."""
    profile = profile_with()
    with_view = seed(tmp_path / "with")
    without_view = seed(tmp_path / "without", axis=None)
    with_facet = gather(with_view, PROPOSITION_REF, **_gathered(kwargs_for(with_view, profile)))
    without = gather(without_view, PROPOSITION_REF, **_gathered(kwargs_for(without_view, profile)))
    assert with_facet.claim is not None and with_facet.claim.operator == "testing/affects"
    assert "biology" in dict(with_facet.consulted)
    assert "biology" not in dict(without.consulted)


def test_isolated_case_a_biology_bump_moves_the_digest(tmp_path):
    view = seed(tmp_path)
    before = _belief(view, profile_with("fixture"))
    after = _belief(view, profile_with("fixture, bumped"))
    assert before.value == after.value
    assert before.belief_input_digest != after.belief_input_digest


def test_isolated_case_an_unrelated_bump_leaves_it(tmp_path):
    view = seed(tmp_path)
    before = _belief(view, profile_with("fixture", unrelated="v1"))
    after = _belief(view, profile_with("fixture", unrelated="v2"))
    assert before.belief_input_digest == after.belief_input_digest


def test_isolated_case_holds_with_no_claim_record(tmp_path):
    """A proposition with no claim consults only the base — plus biology
    through the facet. The assessments name a proposition the corpus does not
    hold, as `test_evaluation.claimless_fixture` does."""
    absent = "proposition:never-stored"
    profile = profile_with()
    view = seed(tmp_path, proposition=absent)
    inputs = gather(view, absent, **_gathered(kwargs_for(view, profile)))
    assert inputs.claim is None
    assert set(dict(inputs.consulted)) == {"science", "biology"}


# --- the dogfood shape: biology by both routes (design §5.6) ----------------

BIOLOGY_CLAIM = {
    "operator": "biology/affects",
    "args": [GENE, OTHER_GENE],
    "qualifiers": {},
    "polarity": "positive",
    "layer": "causal",
}


def test_dogfood_shape_reaches_biology_by_both_routes(tmp_path):
    """A claim at `biology/affects` (the fixture's operator) whose sorts are
    biology's, over the same facet-bearing dataset: dropping either route
    leaves biology consulted, which is why this case is the measurement and
    the isolated case is the proof."""
    profile = profile_with()
    view = seed(tmp_path, claim=BIOLOGY_CLAIM)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.claim is not None and inputs.claim.operator == "biology/affects"
    assert "biology" in dict(inputs.consulted)
    assert [row.key for row in inputs.observed_facets] == ["biology/gene-axis"]


def test_dogfood_biology_bump_moves_the_digest(tmp_path):
    view = seed(tmp_path, claim=BIOLOGY_CLAIM)
    before = _belief(view, profile_with("fixture"))
    after = _belief(view, profile_with("editorial"))
    assert before.value == after.value and before.belief_input_digest != after.belief_input_digest


def test_dogfood_unrelated_bump_leaves_the_digest(tmp_path):
    view = seed(tmp_path, claim=BIOLOGY_CLAIM)
    before = _belief(view, profile_with(unrelated="v1"))
    after = _belief(view, profile_with(unrelated="v2"))
    assert before.belief_input_digest == after.belief_input_digest


def test_dogfood_payload_change_moves_the_digest(tmp_path):
    rows = _belief(seed(tmp_path / "rows", claim=BIOLOGY_CLAIM), profile_with())
    columns = _belief(seed(tmp_path / "columns", axis="columns", claim=BIOLOGY_CLAIM), profile_with())
    assert rows.value == columns.value and rows.belief_input_digest != columns.belief_input_digest


# --- M8's added arm (design §7) --------------------------------------------


def test_m8_an_editorial_bump_of_a_foreign_sorts_contract_leaves_claim_identity_and_moves_the_digest(tmp_path):
    """The claim is at `crossing/affects-local-entity`, no domain facet is in
    the closure (`axis=None`), and the bumped contract is `testing`, reached
    through slot 1's sort and nothing else. Dropping the walk's sort-contract
    collection leaves `testing` unconsulted and this test fails (M8a)."""
    from domain_facet_fixtures import CROSSING_CLAIM

    from beliefs.projection import claim_identity

    view = seed(tmp_path, axis=None, claim=CROSSING_CLAIM)
    before = profile_with(crossing=True)
    after = profile_with(crossing=True, testing_description="editorial")
    one = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, before))
    two = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, after))
    assert isinstance(one, Belief) and isinstance(two, Belief)
    inputs_one = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, before)))
    inputs_two = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, after)))
    assert inputs_one.observed_facets == () and inputs_one.claim is not None and inputs_two.claim is not None
    assert claim_identity(inputs_one.claim) == claim_identity(inputs_two.claim)
    assert "testing" in dict(inputs_one.consulted)
    assert one.value == two.value and one.belief_input_digest != two.belief_input_digest
