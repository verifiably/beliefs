"""P1-P9, G1, G8, D7, S6(e): the evaluator end to end.

`scenario(**overrides)` builds one complete, valid `evaluate` kwargs dict —
one claim, two independent supporting assessments, admitting verifications, a
clean two-root snapshot, one corpus, `BELIEF_V1` under its own binding — and
every test below perturbs it. The happy path publishes `Belief(2, ...)`: two
independent supports, no contestation.
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path
from typing import TypedDict, cast

import pytest
import yaml
from profiles import pins_for

from beliefs.belief import (
    NO_BELIEF_REASONS,
    Availability,
    Belief,
    NoBelief,
    Records,
    Refused,
    SuppliedContext,
    evaluate,
)
from beliefs.claim import Referent, build_claim
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.contract import domain, load_base_contract
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import MalformedRecord
from beliefs.lineage import LineageSnapshot
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding, PolicyImplementation
from beliefs.profile import ProfileSpec, compile_profile
from beliefs.projection import claim_identity
from beliefs.record import AssessmentValue, RunInput, RunValue, SourceAssertion
from beliefs.stored import typed_ref
from beliefs.verification import Verification

# --- module-level fixtures: a compiled profile and one claim, loaded once ---

_REPO_ROOT = Path(__file__).resolve().parents[2]
_base = load_base_contract(_REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml")
_testing_document = yaml.safe_load((_REPO_ROOT / "fixtures" / "contracts" / "testing.yaml").read_text(encoding="utf-8"))
_testing = domain.parse_domain_contract(_testing_document, source="<test>", base=_base, predecessor=None)
PROFILE = compile_profile(_base, [_testing])

CLAIM = build_claim(
    profile=PROFILE,
    operator="testing/affects",
    args=(Referent(sort="testing/entity", term="EX:gene-x"), Referent(sort="testing/outcome", term="EX:pheno-y")),
    polarity="positive",
    layer="causal",
)
PROPOSITION = claim_identity(CLAIM)

# A second, unrelated claim — same testing namespace (the fixture set carries
# no second domain contract to reach a genuinely different one), but a
# different operator and different args, and never named by any assessment
# under test. Nothing below evaluates a proposition equal to this claim's
# identity, so it exercises "present in `records.claims`, read by nobody".
OTHER_CLAIM = build_claim(
    profile=PROFILE,
    operator="testing/subtype-of",
    args=(Referent(sort="testing/entity", term="EX:gene-x"), Referent(sort="testing/entity", term="EX:gene-z")),
    layer="structural",
)
OTHER_PROPOSITION = claim_identity(OTHER_CLAIM)


def _dataset(letter: str) -> DatasetDeclaration:
    return DatasetDeclaration(resources=(ResourceDeclaration(name=f"r-{letter}", digest=f"sha256:{letter * 64}"),))


DATASET_A, DATASET_B, DATASET_C = _dataset("a"), _dataset("b"), _dataset("c")


def _address(dataset: DatasetDeclaration) -> str:
    address = dataset_address(dataset)
    assert address is not None
    return address


ADDRESS_A, ADDRESS_B = _address(DATASET_A), _address(DATASET_B)


def _held(*datasets: DatasetDeclaration) -> dict[str, tuple[ByteObservation, ...]]:
    table: dict[str, tuple[ByteObservation, ...]] = {}
    for d in datasets:
        address = dataset_address(d)
        assert address is not None
        observations = []
        for resource in d.resources:
            assert resource.digest is not None
            observations.append(ByteObservation(digest=resource.digest, location="repo://data"))
        table[address] = tuple(observations)
    return table


def _run(ref: str, spec: str, dataset: DatasetDeclaration) -> RunValue:
    return RunValue(ref=typed_ref("run", ref), spec=spec, inputs=(RunInput(role="observes", dataset=dataset),))


def _assessment(spec: str, run: str, outcome: str = "supported") -> AssessmentValue:
    return AssessmentValue(spec=spec, run=run, proposition=PROPOSITION, outcome=outcome, interpretation_rule="rule-1")


def _fifty_inconclusive_records() -> Records:
    """50 eligible, inconclusive assessments — all observing `DATASET_A`,
    which the base scenario already holds."""
    assessments = tuple(_assessment(f"spec-{i}", f"run-{i}", outcome="inconclusive") for i in range(50))
    runs = {a.run: _run(a.run, a.spec, DATASET_A) for a in assessments}
    verifications = tuple(
        Verification(ref=f"v-{i}", assessment=a.identity(), scope="clean-environment", verdict="passed")
        for i, a in enumerate(assessments)
    )
    return Records(
        claims={PROPOSITION: CLAIM},
        assessments=assessments,
        runs=runs,
        source_assertions=(),
        verifications=verifications,
    )


class _Scenario(TypedDict):
    proposition: str
    records: Records
    availability: Availability
    context: SuppliedContext
    binding: PolicyBinding
    profile: ProfileSpec


def scenario(**overrides: object) -> _Scenario:
    a1, a2 = _assessment("spec-a", "run-a"), _assessment("spec-b", "run-b")
    runs = {"run-a": _run("run-a", "spec-a", DATASET_A), "run-b": _run("run-b", "spec-b", DATASET_B)}
    verifications = (
        Verification(ref="v-a", assessment=a1.identity(), scope="clean-environment", verdict="passed"),
        Verification(ref="v-b", assessment=a2.identity(), scope="clean-environment", verdict="passed"),
    )
    records = Records(
        claims={PROPOSITION: CLAIM},
        assessments=(a1, a2),
        runs=runs,
        source_assertions=(),
        verifications=verifications,
    )
    availability = Availability(
        observations=_held(DATASET_A, DATASET_B),
        implementations={BELIEF_V1.identity: BELIEF_V1},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )
    context = SuppliedContext(
        snapshot=LineageSnapshot(roots=(ADDRESS_A, ADDRESS_B), bases={}, producers={}),
        producer_snapshot_identity="producer-snapshot-1",
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        node_corpus={a1.identity(): ("c1",), a2.identity(): ("c1",)},
        pins={"c1": pins_for(PROFILE)},
    )
    kwargs: dict[str, object] = {
        "proposition": PROPOSITION,
        "records": records,
        "availability": availability,
        "context": context,
        "binding": PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        "profile": PROFILE,
    }
    kwargs.update(overrides)
    return cast(_Scenario, kwargs)


@pytest.mark.parametrize("node_corpus", [{"node": "c1"}, {"node": ()}, {"node": ("c1", 1)}, {"node": ("c2", "c1")}])
def test_node_corpus_attributes_nodes_to_sorted_nonempty_string_tuples(node_corpus):
    with pytest.raises(MalformedRecord, match="node_corpus attributes each node to a non-empty tuple of corpus ids"):
        replace(scenario()["context"], node_corpus=node_corpus)


def test_w18j_a_coordination_pin_never_enters_the_belief_input_digest():
    ordinary = scenario()
    first = evaluate(**ordinary)
    pin = ordinary["context"].pins["c1"]
    with_coordination = {
        "c1": CorpusPins(
            science_contract=pin.science_contract,
            domains={**pin.domains, "coordination": "coordination:" + "c" * 64},
        )
    }
    second = evaluate(
        **scenario(context=replace(ordinary["context"], pins=with_coordination))
    )
    assert isinstance(first, Belief) and isinstance(second, Belief)
    assert second.belief_input_digest == first.belief_input_digest


class TestP1TheBindingIsExact:
    def test_nothing_refuses(self):
        result = evaluate(**scenario(binding=None))
        assert isinstance(result, Refused)

    def test_the_rule_identity_alone_refuses(self):
        result = evaluate(**scenario(binding=BELIEF_V1_RULE))
        assert isinstance(result, Refused)

    def test_the_exact_binding_computes(self):
        result = evaluate(**scenario())
        assert isinstance(result, Belief)
        assert result == Belief(2, result.belief_input_digest, scenario()["binding"])


class TestP2FixtureFailureRefuses:
    def test_a_failing_implementation_refuses_not_unavailable(self):
        broken = PolicyImplementation(identity=BELIEF_V1.identity, aggregate=lambda problem: 999)
        kwargs = scenario()
        availability = replace(kwargs["availability"], implementations={BELIEF_V1.identity: broken})
        result = evaluate(**scenario(availability=availability))
        assert isinstance(result, Refused)
        assert result.reason.startswith("implementation-fails-fixtures")

    def test_installing_a_conforming_one_beside_it_still_refuses(self):
        broken = PolicyImplementation(identity=BELIEF_V1.identity, aggregate=lambda problem: 999)
        kwargs = scenario()
        availability = replace(
            kwargs["availability"], implementations={BELIEF_V1.identity: broken, "other-impl": BELIEF_V1}
        )
        result = evaluate(**scenario(availability=availability))
        assert isinstance(result, Refused)
        assert result.reason.startswith("implementation-fails-fixtures")

    def test_a_merely_unheld_implementation_is_unavailable(self):
        binding = PolicyBinding(rule=BELIEF_V1_RULE, implementation="not-held-impl")
        result = evaluate(**scenario(binding=binding))
        assert result == NoBelief("unavailable-policy-unheld")

    def test_holding_it_later_makes_the_same_binding_compute(self):
        binding = PolicyBinding(rule=BELIEF_V1_RULE, implementation="not-held-impl")
        kwargs = scenario()
        implementations = {
            "not-held-impl": PolicyImplementation(identity="not-held-impl", aggregate=BELIEF_V1.aggregate)
        }
        availability = replace(kwargs["availability"], implementations=implementations)
        result = evaluate(**scenario(binding=binding, availability=availability))
        assert isinstance(result, Belief)
        assert result.value == 2

    def test_unheld_fixtures_are_their_own_absence(self):
        kwargs = scenario()
        availability = replace(kwargs["availability"], fixtures={})
        result = evaluate(**scenario(availability=availability))
        assert result == NoBelief("unavailable-fixtures-unheld")


class TestP4TheAbsencesAreDistinguishable:
    def test_a_balanced_directional_set_publishes_belief_zero(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        records = replace(kwargs["records"], assessments=(a1, replace(a2, outcome="refuted")))
        result = evaluate(**scenario(records=records))
        assert isinstance(result, Belief)
        assert result.value == 0

    def test_no_assessments_is_no_eligible_assessment(self):
        kwargs = scenario()
        records = replace(kwargs["records"], assessments=())
        result = evaluate(**scenario(records=records))
        assert result == NoBelief("no-eligible-assessment")

    def test_fifty_inconclusive_are_not_an_absence_of_assessment(self):
        result = evaluate(**scenario(records=_fifty_inconclusive_records()))
        assert result == NoBelief("no-directional-outcome")
        assert result != NoBelief("no-eligible-assessment")

    def test_none_of_the_three_is_unavailable(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        balanced_records = replace(kwargs["records"], assessments=(a1, replace(a2, outcome="refuted")))
        balanced = evaluate(**scenario(records=balanced_records))
        no_eligible = evaluate(**scenario(records=replace(kwargs["records"], assessments=())))
        fifty = evaluate(**scenario(records=_fifty_inconclusive_records()))
        assert isinstance(balanced, Belief)
        for result in (no_eligible, fifty):
            assert isinstance(result, NoBelief)
            assert not result.reason.startswith("unavailable-")

    def test_corpus_absent_is_defined_and_unreached(self):
        NoBelief("unavailable-corpus-absent")  # constructs: it is in the closed set
        assert "unavailable-corpus-absent" in NO_BELIEF_REASONS
        result = evaluate(**scenario())
        assert not (isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent")


class TestP6NoMagnitudeBearingRead:
    @pytest.mark.parametrize("field", ["estimate", "uncertainty", "estimand", "applicability"])
    def test_each_field_moves_the_digest_and_not_the_value(self, field):
        baseline = evaluate(**scenario())
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        records = replace(kwargs["records"], assessments=(replace(a1, **{field: "mutated"}), a2))
        mutated = evaluate(**scenario(records=records))
        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value
        assert mutated.belief_input_digest != baseline.belief_input_digest

    def test_no_mismatch_finding_exists_to_be_emitted(self):
        import beliefs.belief as belief_module

        assert not any("mismatch" in name.lower() for name in vars(belief_module))


class TestP7BeliefIsAComputedView:
    def test_the_evaluator_accepts_no_prior_value_and_no_prior_digest(self):
        parameters = inspect.signature(evaluate).parameters
        assert set(parameters) == {"proposition", "records", "availability", "context", "binding", "profile"}
        assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters.values())
        assert all(p.default is inspect.Parameter.empty for p in parameters.values())

    def test_recomputation_is_byte_identical(self):
        first = evaluate(**scenario())
        second = evaluate(**scenario())
        assert isinstance(first, Belief) and isinstance(second, Belief)
        assert first.value == second.value
        assert first.belief_input_digest == second.belief_input_digest

    def test_no_belief_record_and_no_selector_is_minted(self):
        import beliefs.belief as belief_module

        public = {name: value for name, value in vars(belief_module).items() if not name.startswith("_")}
        assert not any(isinstance(value, dict | list) for value in public.values())

    def test_any_cache_is_observationally_inert(self):
        first = evaluate(**scenario())
        other_binding = PolicyBinding(rule=BELIEF_V1_RULE, implementation="not-held")
        evaluate(**scenario(binding=other_binding))  # an intervening, differently-shaped call
        restored = evaluate(**scenario())
        assert restored == first


class TestP8InconclusiveIsValueInertAndDigestCommitted:
    def test_adding_one_keeps_the_value_and_moves_the_digest(self):
        baseline = evaluate(**scenario())
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        a3 = _assessment("spec-c", "run-c", outcome="inconclusive")
        runs = {**kwargs["records"].runs, "run-c": _run("run-c", "spec-c", DATASET_C)}
        verifications = (
            *kwargs["records"].verifications,
            Verification(ref="v-c", assessment=a3.identity(), scope="clean-environment", verdict="passed"),
        )
        records = replace(kwargs["records"], assessments=(a1, a2, a3), runs=runs, verifications=verifications)
        availability = replace(
            kwargs["availability"], observations={**kwargs["availability"].observations, **_held(DATASET_C)}
        )
        mutated = evaluate(**scenario(records=records, availability=availability))
        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value == 2
        assert mutated.belief_input_digest != baseline.belief_input_digest

    def test_the_exclusion_is_not_a_cardinality_gift(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        i = _assessment("spec-i", "run-i", outcome="inconclusive")
        runs = {**kwargs["records"].runs, "run-i": _run("run-i", "spec-i", DATASET_A)}  # shares x with a1
        verifications = (
            *kwargs["records"].verifications,
            Verification(ref="v-i", assessment=i.identity(), scope="clean-environment", verdict="passed"),
        )
        records = replace(kwargs["records"], assessments=(a1, a2, i), runs=runs, verifications=verifications)
        result = evaluate(**scenario(records=records))
        assert isinstance(result, Belief)
        assert result.value == 2  # not 1: {C, I} never competes — I has no vertex to offer


class TestP9UnholdingPrecedence:
    def test_removing_the_last_eligible_directional_is_input_unheld(self):
        kwargs = scenario()
        a1, _a2 = kwargs["records"].assessments
        records = replace(kwargs["records"], assessments=(a1,))
        availability = replace(kwargs["availability"], observations={})
        result = evaluate(**scenario(records=records, availability=availability))
        assert result == NoBelief("unavailable-input-unheld")

    def test_partial_unholding_recomputes_from_the_survivors(self):
        kwargs = scenario()
        availability = replace(kwargs["availability"], observations=_held(DATASET_A))  # drop DATASET_B
        result = evaluate(**scenario(availability=availability))
        assert isinstance(result, Belief)
        assert result.value == 1

    def test_dropping_a_refuting_assessment_raises_the_value(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        records = replace(kwargs["records"], assessments=(a1, replace(a2, outcome="refuted")))
        balanced = evaluate(**scenario(records=records))
        availability = replace(kwargs["availability"], observations=_held(DATASET_A))  # unhold the refuter's input
        raised = evaluate(**scenario(records=records, availability=availability))
        assert isinstance(balanced, Belief) and balanced.value == 0
        assert isinstance(raised, Belief) and raised.value == 1


class TestG1ASourceAssertionMovesNothing:
    def test_every_field_maximal_moves_no_belief_output_byte(self):
        baseline = evaluate(**scenario())
        sa = SourceAssertion(
            ref="sa-1", relation="asserts", proposition=PROPOSITION, payload={"k1": "v1", "k2": "v2", "k3": "v3"}
        )
        kwargs = scenario()
        records = replace(kwargs["records"], source_assertions=(sa,))
        mutated = evaluate(**scenario(records=records))
        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value
        assert mutated.belief_input_digest == baseline.belief_input_digest


class TestG8AFailingVerificationForcesADifferentAnswer:
    def test_invalidation_flips_the_state_and_the_answer(self):
        baseline = evaluate(**scenario())
        kwargs = scenario()
        _a1, a2 = kwargs["records"].assessments
        failing = Verification(ref="v-fail", assessment=a2.identity(), scope="clean-environment", verdict="failed")
        records = replace(kwargs["records"], verifications=(*kwargs["records"].verifications, failing))
        mutated = evaluate(**scenario(records=records))
        assert isinstance(baseline, Belief) and baseline.value == 2
        assert isinstance(mutated, Belief) and mutated.value == 1
        assert mutated.belief_input_digest != baseline.belief_input_digest

    def test_not_cleared_by_recency_or_sibling(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        failing = Verification(ref="v-fail", assessment=a2.identity(), scope="clean-environment", verdict="failed")
        sibling = Verification(ref="v-sibling", assessment=a1.identity(), scope="clean-environment", verdict="passed")
        records = replace(kwargs["records"], verifications=(*kwargs["records"].verifications, failing, sibling))
        result = evaluate(**scenario(records=records))
        assert isinstance(result, Belief)
        assert result.value == 1  # a2 stays invalidated; a1's unrelated sibling verification changes nothing

    def test_deleting_the_failure_returns_the_assessment(self):
        original = evaluate(**scenario())
        assert isinstance(original, Belief)
        kwargs = scenario()
        _a1, a2 = kwargs["records"].assessments
        failing = Verification(ref="v-fail", assessment=a2.identity(), scope="clean-environment", verdict="failed")
        records = replace(kwargs["records"], verifications=(*kwargs["records"].verifications, failing))
        invalidated = evaluate(**scenario(records=records))
        restored = evaluate(**scenario())  # the failure record simply never supplied again
        assert isinstance(invalidated, Belief) and invalidated.value != original.value
        assert restored == original


class TestD7AtTheEvaluator:
    def test_a_profile_pin_mismatch_refuses_with_its_distinct_prefix(self):
        kwargs = scenario()
        context = replace(
            kwargs["context"],
            pins={"c1": replace(pins_for(PROFILE), science_contract="science:" + "0" * 64)},
        )
        result = evaluate(**scenario(context=context))
        assert isinstance(result, Refused)
        assert result.reason.startswith("profile-pin-mismatch: science")

    def test_disagreeing_corpora_refuse_the_derivation(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        context = replace(
            kwargs["context"],
            node_corpus={a1.identity(): ("c1",), a2.identity(): ("c2",)},
            pins={
                "c1": pins_for(PROFILE),
                "c2": CorpusPins(
                    science_contract=pins_for(PROFILE).science_contract,
                    domains={**pins_for(PROFILE).domains, "testing": "testing:" + "2" * 64},
                ),
            },
        )
        result = evaluate(**scenario(context=context))
        assert isinstance(result, Refused)
        assert result.reason.startswith("consulted-contracts-disagree")

    def test_an_unrelated_claim_moves_neither_value_nor_digest(self):
        baseline = evaluate(**scenario())
        kwargs = scenario()
        claims = {**kwargs["records"].claims, OTHER_PROPOSITION: OTHER_CLAIM}
        records = replace(kwargs["records"], claims=claims)
        mutated = evaluate(**scenario(records=records))
        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value
        assert mutated.belief_input_digest == baseline.belief_input_digest


class TestS6eTheDigestHalf:
    def test_duplicated_contrary_assessments_change_the_digest_not_the_value(self):
        kwargs = scenario()
        a1, a2 = kwargs["records"].assessments
        a2 = replace(a2, outcome="refuted")
        baseline = evaluate(**scenario(records=replace(kwargs["records"], assessments=(a1, a2))))

        dupes = tuple(_assessment(f"spec-d{i}", f"run-d{i}", outcome="refuted") for i in range(2))
        runs = {**kwargs["records"].runs, **{d.run: _run(d.run, d.spec, DATASET_B) for d in dupes}}
        verifications = (
            *kwargs["records"].verifications,
            *(
                Verification(ref=f"v-d{i}", assessment=d.identity(), scope="clean-environment", verdict="passed")
                for i, d in enumerate(dupes)
            ),
        )
        records = replace(kwargs["records"], assessments=(a1, a2, *dupes), runs=runs, verifications=verifications)
        mutated = evaluate(**scenario(records=records))

        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value == 0
        assert mutated.belief_input_digest != baseline.belief_input_digest


class TestPolicyBindingRefuses:
    """Carry-over from task 8's review: `PolicyBinding`'s own `MalformedRecord`
    refusals, untested there."""

    def test_empty_rule_refuses(self):
        with pytest.raises(MalformedRecord):
            PolicyBinding(rule="", implementation="impl-1")

    def test_empty_implementation_refuses(self):
        with pytest.raises(MalformedRecord):
            PolicyBinding(rule=BELIEF_V1_RULE, implementation="")
