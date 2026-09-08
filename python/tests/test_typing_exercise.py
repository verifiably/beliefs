"""Regression tests for the typing exercise's classifiers.

The exercise itself is never run by the suite, for the reason the survey's is
not: it reads corpora outside this repository, so a test asserting a *yield*
would assert something CI cannot see. What is testable is the part that decides
an outcome — whether a record is reported as recording no claim, as carrying a
value the plan does not map, or as refused by the calculus.

Those three are the distinction the whole exercise rests on. A tool that
reported *"the vocabulary is incomplete"* as *"the calculus refused"* would
produce a coverage figure indistinguishable from a real one and wrong in the
direction that flatters the design, and the plan files exist to make the
difference visible rather than to be trusted.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).parents[1] / "tools"

# As in `test_survey_instrument.py`: `tools/` is not a package and deliberately
# is not on the import path, so it is loaded by file.
_SPEC = importlib.util.spec_from_file_location("type_corpus_claims", _TOOLS / "type_corpus_claims.py")
assert _SPEC is not None and _SPEC.loader is not None
exercise = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = exercise
_SPEC.loader.exec_module(exercise)


class TestSortOf:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("concept:progression-free-survival", "concept"),
            ("protein:BCL2", "protein"),
            ("dataset:gse4581", "dataset"),
        ],
    )
    def test_a_kind_prefix_names_the_sort(self, value: str, expected: str) -> None:
        assert exercise.sort_of(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "KPZ",  # natural-systems writes bare prose in a subject slot
            "guide morphism vocabulary",
            ":no-head",
            "no-tail:",
        ],
    )
    def test_a_term_without_a_kind_prefix_has_no_sort(self, value: str) -> None:
        # Guessing one would invent the single fact the slot needs. The record is
        # reported as `unsorted-referent` instead, which is a statement about the
        # corpus rather than about the calculus.
        assert exercise.sort_of(value) is None


class TestPlanFiles:
    """The shipped plans must load, compile, and stay honest about defaulting."""

    @pytest.mark.parametrize(
        "name",
        ["mm30-unsorted", "mm30-modal-sorted", "post-acute-infection", "natural-systems"],
    )
    def test_every_plan_parses_and_compiles(self, name: str) -> None:
        import yaml

        from beliefs.contract import load_base_contract
        from beliefs.contract.domain import parse_domain_contract
        from beliefs.profile import compile_profile

        document = yaml.safe_load((_TOOLS / "vocabularies" / f"{name}.yaml").read_text(encoding="utf-8"))
        base = load_base_contract(exercise.BASE_CONTRACT)
        contract = parse_domain_contract(document["contract"], source=name, base=base, predecessor=None)
        compile_profile(base, [contract])

    @pytest.mark.parametrize("name", ["mm30-unsorted", "mm30-modal-sorted"])
    def test_mm30_plans_do_not_map_a_layer_the_base_contract_lacks(self, name: str) -> None:
        # A forward guard, and worth being precise about what it does not do.
        # Mapping `mechanistic_narrative` onto `causal` today changes **no**
        # count: all 13 records carrying it lack a triple, and the triple is
        # checked first, so none reaches the layer lookup. Measured — both
        # corpora run with the mapping added return their unchanged totals.
        #
        # What it guards is the revisit condition. The value is not admitted to
        # the base layer set precisely because no *structured* record carries it;
        # if one ever does, a mapped plan would type it as `causal` and hide the
        # single record that could reopen the ruling.
        import yaml

        document = yaml.safe_load((_TOOLS / "vocabularies" / f"{name}.yaml").read_text(encoding="utf-8"))
        assert "mechanistic_narrative" not in document["plan"]["layers"]

    def test_the_two_mm30_plans_differ_only_in_their_sorts(self) -> None:
        # The gap between the two runs is the measurement. If anything else drifts
        # between the files, the difference stops being attributable to sorting.
        import yaml

        plans = [
            yaml.safe_load((_TOOLS / "vocabularies" / f"mm30-{v}.yaml").read_text(encoding="utf-8"))
            for v in ("unsorted", "modal-sorted")
        ]
        unsorted, modal = (p["contract"]["operators"] for p in plans)
        assert set(unsorted) == set(modal)
        for name, declaration in unsorted.items():
            for held_fixed in ("arity", "sign_apt", "layers", "dimensions"):
                assert declaration[held_fixed] == modal[name][held_fixed], f"{name}.{held_fixed} drifted"
        for plan_a, plan_b in [(plans[0]["plan"], plans[1]["plan"])]:
            for held_fixed in ("operators", "layers", "polarities"):
                assert plan_a[held_fixed] == plan_b[held_fixed], f"plan.{held_fixed} drifted"


class TestTypeRecord:
    """The outcome classifier, against a compiled profile built from a plan."""

    @pytest.fixture(scope="class")
    @classmethod
    def typed(cls):
        import yaml

        from beliefs.contract import load_base_contract
        from beliefs.contract.domain import parse_domain_contract
        from beliefs.profile import compile_profile

        document = yaml.safe_load((_TOOLS / "vocabularies" / "mm30-modal-sorted.yaml").read_text(encoding="utf-8"))
        base = load_base_contract(exercise.BASE_CONTRACT)
        contract = parse_domain_contract(document["contract"], source="mm30", base=base, predecessor=None)
        profile = compile_profile(base, [contract])
        plan = document["plan"]
        resolved = {
            "operators": {(k, None, None): contract.term(v) for k, v in plan["operators"].items()},
            "sorts": {k: contract.term(v) for k, v in plan["sorts"].items()},
            "layers": dict(plan["layers"]),
            "polarities": dict(plan["polarities"]),
        }
        resolved["operators"][("affects", "concept", "concept")] = resolved["operators"].pop(("affects", None, None))
        resolved["operators"][("affects", "concept", "protein")] = contract.term(plan["operators"]["affects"])

        def run(front: dict):
            return exercise.type_record(profile, resolved, front, exercise.Result(corpus="t", plan="t"))

        return run

    def test_a_well_formed_record_types(self, typed) -> None:
        record = typed(
            {
                "subject": "concept:gain-1q",
                "predicate": "affects",
                "object": "concept:progression-free-survival",
                "claim_layer": "causal_effect",
                "polarity": "negative",
            }
        )
        assert record.outcome == "typed"

    def test_a_record_with_no_triple_records_no_claim(self, typed) -> None:
        # mm30's 27 unstructured propositions and all 45 post-acute-infection
        # ones land here. This is the outcome that must never be reported as a
        # refusal: the calculus was not reached.
        record = typed({"claim_layer": "causal_effect", "title": "PHF19 retains prognostic signal"})
        assert record.outcome == "no-claim-recorded"
        assert "subject" in record.detail and "predicate" in record.detail and "object" in record.detail

    def test_an_unmapped_layer_is_vocabulary_work_not_a_refusal(self, typed) -> None:
        record = typed(
            {
                "subject": "concept:a",
                "predicate": "affects",
                "object": "concept:b",
                "claim_layer": "mechanistic_narrative",
                "polarity": "positive",
            }
        )
        assert record.outcome == "unmapped-layer"

    def test_an_unmapped_shape_is_vocabulary_work_not_a_refusal(self, typed) -> None:
        record = typed(
            {
                "subject": "protein:A",
                "predicate": "affects",
                "object": "concept:b",
                "claim_layer": "causal_effect",
                "polarity": "positive",
            }
        )
        assert record.outcome == "unmapped-shape"
        assert record.detail == "affects protein→concept"

    def test_a_sort_mismatch_is_a_refusal_by_the_calculus(self, typed) -> None:
        # The one outcome in the mm30 run that the contract was not fitted to
        # produce: `affects` is declared concept→concept by the modal rule, and
        # 25 records relate a protein.
        record = typed(
            {
                "subject": "concept:t-11-14",
                "predicate": "affects",
                "object": "protein:BCL2",
                "claim_layer": "causal_effect",
                "polarity": "positive",
            }
        )
        assert record.outcome == "refused-ArgumentSortMismatch"

    def test_a_signed_polarity_on_a_sign_inapt_operator_is_refused(self, typed) -> None:
        # §7.5's distinction, exercised: `subtype-of` has no sign to assert, so
        # asserting one is refused rather than ignored. No mm30 record does this,
        # but that is not corroboration — the predecessor system enforces the
        # same predicate/polarity partition on construction, so a violating
        # record could never have reached disk. The case is constructed here for
        # exactly that reason: the corpora cannot supply one.
        record = typed(
            {
                "subject": "concept:a",
                "predicate": "subtype_of",
                "object": "concept:b",
                "claim_layer": "structural_claim",
                "polarity": "positive",
            }
        )
        assert record.outcome == "refused-PolarityRefused"

    def test_a_bare_term_is_reported_against_the_corpus_not_the_calculus(self, typed) -> None:
        record = typed(
            {
                "subject": "KPZ",
                "predicate": "affects",
                "object": "concept:b",
                "claim_layer": "causal_effect",
                "polarity": "positive",
            }
        )
        assert record.outcome == "unsorted-referent"
