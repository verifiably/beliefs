"""B4's absent-dataset arm and B5's read-ledger behavior."""

from __future__ import annotations

from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import pytest
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, profile_with, seed
from domain_facet_fixtures import testing_contract as _testing_contract

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
