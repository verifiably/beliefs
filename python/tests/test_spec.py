"""R20's selected arms, G4's value-state arms, R8's mint half, and R7's no-target refusal. Deferred and deliberately absent: R20 negative (a)'s import half (the import boundary), negative (c) and negative (d)'s two-decomposition comparison (the full workflow surface) — cut 3 §4.2."""

import dataclasses
import inspect
from decimal import Decimal

import pytest
from fixtures_cut3 import seed_plan as plan
from fixtures_cut3 import spec_draft as draft
from fixtures_cut3 import spec_rules as held_rules

from beliefs.errors import MalformedRecord, MalformedSpec, RuleUnbound, UnfreezableSpec
from beliefs.identity import v1
from beliefs.spec import (
    SPEC_DOMAIN,
    Deterministic,
    ExclusionCertification,
    FrozenSpec,
    RealizedSeeds,
    RuleFixture,
    RuleImplementation,
    Seeded,
    SeedPlan,
    SpecDraft,
    SpecInput,
    StochasticUnseeded,
    SuccessorAdmitted,
    SuccessorRefused,
    admit_successor,
    bind_rules,
    derive_seed,
    freeze,
    revise,
)

# --- R20: the union's type refusals -----------------------------------------


def test_r20_deterministic_with_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        Deterministic(plan=plan())  # type: ignore[call-arg]  # the variant carries nothing — refused by the type


def test_r20_stochastic_unseeded_with_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        StochasticUnseeded(rationale="honest", plan=plan())  # type: ignore[call-arg]


def test_r20_seeded_without_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        Seeded()  # type: ignore[call-arg]


def test_r20_multi_root_plan_without_a_total_mapping_is_refused():
    with pytest.raises(MalformedSpec):
        SeedPlan(
            derivation_rule="seed-derivation/v1",
            streams=("model-initialization", "resample-draws"),
            roots={"root-a": 1, "root-b": 2},
            stream_roots={"model-initialization": "root-a"},  # resample-draws has no root
        )


def test_r20_a_mapped_root_must_be_declared():
    with pytest.raises(MalformedSpec):
        plan(stream_roots={"model-initialization": "root-missing"})


def test_r20_stochastic_unseeded_with_a_rationale_is_freezable():
    spec = freeze(
        draft(
            nondeterminism=StochasticUnseeded(rationale="MCMC without a fixed seed"),
            equivalence_rule="tolerance-1e-6/v1",
        ),
        held_rules={**held_rules(), "tolerance-1e-6/v1": held_rules()["content-identity-equality/v1"]},
    )
    assert isinstance(spec, FrozenSpec)


def test_r20_unseeded_beside_a_bitwise_rule_is_caught_at_freeze():
    # Negative (a)'s freeze-time half. The import half is the import boundary's
    # and is deferred (cut 3 §4.2).
    with pytest.raises(UnfreezableSpec):
        freeze(draft(nondeterminism=StochasticUnseeded(rationale="honest")), held_rules=held_rules())


def test_r20_the_spec_names_logical_streams_only_no_family_field_exists():
    # Negative (d)'s spellability half: no workflow rule or process name is
    # spellable in the frozen spec — there is no field to put one in.
    assert "families" not in {f.name for f in dataclasses.fields(SeedPlan)}
    assert "family_streams" not in {f.name for f in dataclasses.fields(SpecDraft)}


def test_r20_two_stream_two_root_seeds_cannot_be_keyed_by_job_alone():
    # Negative (b): the occurrence cannot represent a flat record.
    with pytest.raises(MalformedRecord):
        RealizedSeeds(seeds={"transform": 7})  # type: ignore[dict-item]
    nested = RealizedSeeds(seeds={"transform": {"model-initialization": 7, "resample-draws": 9}})
    assert nested.seeds["transform"]["resample-draws"] == 9


def test_spec_input_roles_are_a_tuple_of_spec_inputs():
    with pytest.raises(MalformedSpec):
        draft(input_roles=[SpecInput(role="observes", dataset="dataset:x")])  # type: ignore[arg-type]


# --- rule binding over supplied implementations ------------------------------


def test_rule_binding_is_the_exact_pair():
    # Plumbing for §4.2's rule_bindings member. R22's unresolvable-rule refusal
    # clause is DEFERRED to the rules store (cut 3 §7 item 4) — this test
    # certifies the mapping shape, not that banked clause.
    bound = bind_rules(("median-difference/v1",), held_rules())
    assert bound == (("median-difference/v1", "impl-interp-1"),)
    with pytest.raises(RuleUnbound):
        bind_rules(("unheld-rule/v1",), held_rules())


def test_r22_a_fixture_failing_implementation_is_not_that_rule():
    broken = RuleImplementation(
        identity="impl-broken",
        evaluate=lambda manifest: {"outcome": "refuted"},
        fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
    )
    with pytest.raises(RuleUnbound):
        bind_rules(("median-difference/v1",), {"median-difference/v1": broken})


# --- R7 (spec half), identity, R8's mint half, G4 ----------------------------


def test_r7_an_assessment_spec_with_no_target_is_refused():
    with pytest.raises(MalformedSpec):
        freeze(draft(target=""), held_rules=held_rules())


def test_the_identity_is_over_the_normative_facet():
    a = freeze(draft(), held_rules=held_rules())
    b = freeze(draft(estimand="a different quantity"), held_rules=held_rules())
    assert a.identity != b.identity
    assert freeze(draft(), held_rules=held_rules()).identity == a.identity  # recomputable


def test_the_identity_matches_the_hand_authored_complete_normative_projection():
    spec = freeze(draft(), held_rules=held_rules())
    assert spec.identity == v1.digest(
        SPEC_DOMAIN,
        {
            "target": "prop-1",
            "estimand": "the effect of x on y",
            "method": "fit the model",
            "assumptions": "iid draws",
            "falsification": "a null effect",
            "input_roles": [{"role": "observes", "dataset": "dataset:sha256:" + "aa" * 32}],
            "applicability": "the sampled population",
            "interpretation_rule": "median-difference/v1",
            "equivalence_rule": "content-identity-equality/v1",
            "parameters": {"alpha": Decimal("0.05")},
            "nondeterminism": {
                "variant": "seeded",
                "plan": {
                    "derivation_rule": "seed-derivation/v1",
                    "streams": ["model-initialization"],
                    "roots": {"root-a": 11},
                    "stream_roots": {"model-initialization": "root-a"},
                },
            },
            "rule_bindings": [
                ["content-identity-equality/v1", "impl-eq-1"],
                ["median-difference/v1", "impl-interp-1"],
            ],
        },
    )


def test_a_frozen_spec_keeps_nested_parameters_immutable_after_freeze():
    parameters = {"nested": {"values": ["before"]}}
    spec = freeze(draft(parameters=parameters), held_rules=held_rules())
    parameters["nested"]["values"].append("after")
    assert spec.parameters == {"nested": {"values": ("before",)}}


def test_frozen_specs_are_minted_only_by_freeze_and_revise():
    original = freeze(draft(), held_rules=held_rules())
    members = {field.name: getattr(original, field.name) for field in dataclasses.fields(FrozenSpec)}

    with pytest.raises(TypeError, match="minted by freeze or revise"):
        FrozenSpec(**members)
    with pytest.raises(TypeError, match="minted by freeze or revise"):
        dataclasses.replace(original, identity="forged-spec-id")

    successor = revise(
        original,
        edits={"estimand": "a revised quantity"},
        held_rules=held_rules(),
        recorded_failures=frozenset(),
    )
    assert type(original) is FrozenSpec and type(successor) is FrozenSpec
    assert successor.supersedes == original.identity


def test_supersedes_is_in_the_hand_authored_normative_projection():
    spec = freeze(draft(), held_rules=held_rules(), supersedes="spec:prior")
    assert spec.identity == v1.digest(
        SPEC_DOMAIN,
        {
            "target": "prop-1",
            "estimand": "the effect of x on y",
            "method": "fit the model",
            "assumptions": "iid draws",
            "falsification": "a null effect",
            "input_roles": [{"role": "observes", "dataset": "dataset:sha256:" + "aa" * 32}],
            "applicability": "the sampled population",
            "interpretation_rule": "median-difference/v1",
            "equivalence_rule": "content-identity-equality/v1",
            "parameters": {"alpha": Decimal("0.05")},
            "nondeterminism": {
                "variant": "seeded",
                "plan": {
                    "derivation_rule": "seed-derivation/v1",
                    "streams": ["model-initialization"],
                    "roots": {"root-a": 11},
                    "stream_roots": {"model-initialization": "root-a"},
                },
            },
            "rule_bindings": [
                ["content-identity-equality/v1", "impl-eq-1"],
                ["median-difference/v1", "impl-interp-1"],
            ],
            "supersedes": "spec:prior",
        },
    )


def test_the_exclusion_certification_is_spellable_only_on_a_reads_declaration():
    # R22's reach arm starts here: the certification's authoring home is the
    # frozen spec's reads declaration, frozen into identity with everything else.
    with pytest.raises(MalformedSpec):
        SpecInput(
            role="observes", dataset="dataset:x", exclusion=ExclusionCertification(rationale="r", attribution="a")
        )
    reads = SpecInput(
        role="reads", dataset="dataset:y", exclusion=ExclusionCertification(rationale="palette", attribution="tester")
    )
    certified = freeze(draft(input_roles=draft().input_roles + (reads,)), held_rules=held_rules())
    plain = freeze(
        draft(input_roles=draft().input_roles + (SpecInput(role="reads", dataset="dataset:y"),)),
        held_rules=held_rules(),
    )
    assert certified.identity != plain.identity


def test_r8_editing_the_equivalence_rule_mints_a_successor_that_references():
    original = freeze(draft(), held_rules=held_rules())
    rules = {**held_rules(), "tolerance-1e-6/v1": held_rules()["content-identity-equality/v1"]}
    successor = revise(
        original,
        edits={"equivalence_rule": "tolerance-1e-6/v1"},
        held_rules=rules,
        recorded_failures=frozenset({original.identity}),
    )
    assert successor.identity != original.identity
    assert successor.supersedes == original.identity


def test_r8_changing_a_root_seed_mints_a_successor_spec():
    # §3.1: the seed is normative spec content; changing a root is a semantic
    # revision, never a runtime choice.
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"nondeterminism": Seeded(plan=plan(roots={"root-a": 12}))},
        held_rules=held_rules(),
        recorded_failures=frozenset(),
    )
    assert successor.identity != original.identity and successor.supersedes == original.identity


def test_g4_an_unreferenced_successor_to_a_recorded_failed_replay_is_refused():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())  # supersedes=None
    verdict = admit_successor(unreferenced, original, frozenset({original.identity}), frozenset())
    assert isinstance(verdict, SuccessorRefused)


def test_g4_a_referencing_successor_is_admitted():
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"estimand": "revised"},
        held_rules=held_rules(),
        recorded_failures=frozenset({original.identity}),
    )
    assert isinstance(admit_successor(successor, original, frozenset({original.identity}), frozenset()), SuccessorAdmitted)


def test_g4_a_discarded_failed_attempt_is_undetectable():
    # The negative: activeness and reference are over the slice's VALUE state —
    # a failure absent from the supplied set never happened, and nothing can
    # tell (kernel G4's bound, pinned rather than papered over).
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())
    assert isinstance(admit_successor(unreferenced, original, frozenset(), frozenset()), SuccessorAdmitted)


def test_g4_an_unreferenced_successor_to_an_unfinished_recorded_attempt_is_refused():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())
    verdict = admit_successor(unreferenced, original, frozenset(), frozenset({original.identity}))
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"


def test_g4_a_spec_in_both_classes_refuses_with_the_recorded_failure_reason():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())
    both = frozenset({original.identity})
    verdict = admit_successor(unreferenced, original, both, both)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_g4_a_referencing_successor_lifts_both_classes():
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original, edits={"estimand": "revised"}, held_rules=held_rules(), recorded_failures=frozenset()
    )
    both = frozenset({original.identity})
    assert isinstance(admit_successor(successor, original, both, both), SuccessorAdmitted)


def test_g4_the_core_keeps_cut_3s_anchor_line():
    # K5: cut 3's three G4 sabotages name this exact line; it must occur once.
    from pathlib import Path

    import beliefs.spec as spec_module

    source = Path(spec_module.__file__).read_text(encoding="utf-8")
    anchor = "    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:"
    assert source.count(anchor) == 1
    assert list(inspect.signature(admit_successor).parameters) == [
        "candidate",
        "superseded",
        "recorded_failures",
        "unfinished_attempts",
    ]


def test_the_derivation_rule_is_a_pure_function_of_its_three_arguments():
    assert derive_seed(11, "transform", "model-initialization") == derive_seed(11, "transform", "model-initialization")
    assert derive_seed(11, "transform", "model-initialization") != derive_seed(11, "transform", "resample-draws")
    assert derive_seed(11, "transform", "model-initialization") != derive_seed(12, "transform", "model-initialization")
    assert derive_seed(11, "transform", "model-initialization") != derive_seed(11, "resample", "model-initialization")


def test_revise_is_the_only_edit_path_and_freeze_takes_drafts_only():
    assert list(inspect.signature(freeze).parameters) == ["draft", "held_rules", "supersedes"]
    assert list(inspect.signature(revise).parameters) == ["original", "edits", "held_rules", "recorded_failures"]
