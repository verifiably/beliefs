"""The selected checks, the value-state checks, the mint half, and the no-target refusal. Deferred and deliberately absent: the import half of the first negative (the import boundary) and the two-decomposition comparison (the full workflow surface)."""

import dataclasses
import inspect
from decimal import Decimal

import pytest
from fixtures_cut3 import DATA_ADDRESS, typed_applicability, typed_estimand
from fixtures_cut3 import seed_plan as plan
from fixtures_cut3 import spec_draft as draft
from fixtures_cut3 import spec_rules as held_rules

from beliefs.contract.base import ESTIMAND_GRAMMAR
from beliefs.errors import MalformedRecord, MalformedSpec, RuleUnbound, UnfreezableSpec
from beliefs.estimand import applicability_projection, estimand_projection
from beliefs.identity import v1
from beliefs.recipe import job_key
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

# --- the union's type refusals -----------------------------------------


def test_deterministic_with_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        Deterministic(plan=plan())  # type: ignore[call-arg]  # the variant carries nothing — refused by the type


def test_stochastic_unseeded_with_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        StochasticUnseeded(rationale="honest", plan=plan())  # type: ignore[call-arg]


def test_seeded_without_a_plan_is_unspellable():
    with pytest.raises(TypeError):
        Seeded()  # type: ignore[call-arg]


def test_multi_root_plan_without_a_total_mapping_is_refused():
    with pytest.raises(MalformedSpec):
        SeedPlan(
            derivation_rule="seed-derivation/v1",
            streams=("model-initialization", "resample-draws"),
            roots={"root-a": 1, "root-b": 2},
            stream_roots={"model-initialization": "root-a"},  # resample-draws has no root
        )


def test_a_mapped_root_must_be_declared():
    with pytest.raises(MalformedSpec):
        plan(stream_roots={"model-initialization": "root-missing"})


def test_stochastic_unseeded_with_a_rationale_is_freezable():
    spec = freeze(
        draft(
            nondeterminism=StochasticUnseeded(rationale="MCMC without a fixed seed"),
            equivalence_rule="tolerance-1e-6/v1",
        ),
        held_rules={**held_rules(), "tolerance-1e-6/v1": held_rules()["content-identity-equality/v1"]},
    )
    assert isinstance(spec, FrozenSpec)


def test_unseeded_beside_a_bitwise_rule_is_caught_at_freeze():
    # Negative (a)'s freeze-time half. The import half is the import boundary's
    # and is deferred.
    with pytest.raises(UnfreezableSpec):
        freeze(draft(nondeterminism=StochasticUnseeded(rationale="honest")), held_rules=held_rules())


def test_the_spec_names_logical_streams_only_no_family_field_exists():
    # Negative (d)'s spellability half: no workflow rule or process name is
    # spellable in the frozen spec — there is no field to put one in.
    assert "families" not in {f.name for f in dataclasses.fields(SeedPlan)}
    assert "family_streams" not in {f.name for f in dataclasses.fields(SpecDraft)}


def test_two_stream_two_root_seeds_cannot_be_keyed_by_job_alone():
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
    # Plumbing for the rule_bindings member. The unresolvable-rule refusal
    # clause is DEFERRED to the rules store — this test
    # certifies the mapping shape, not that banked clause.
    bound = bind_rules(("median-difference/v1",), held_rules())
    assert bound == (("median-difference/v1", "impl-interp-1"),)
    with pytest.raises(RuleUnbound):
        bind_rules(("unheld-rule/v1",), held_rules())


def test_a_fixture_failing_implementation_is_not_that_rule():
    broken = RuleImplementation(
        identity="impl-broken",
        evaluate=lambda manifest: {"outcome": "refuted"},
        fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
    )
    with pytest.raises(RuleUnbound):
        bind_rules(("median-difference/v1",), {"median-difference/v1": broken})


# --- (spec half), identity, the mint half, value state ----------------------------


def test_an_assessment_spec_with_no_target_is_refused():
    with pytest.raises(MalformedSpec):
        freeze(draft(target=""), held_rules=held_rules())


def test_the_identity_is_over_the_normative_facet():
    a = freeze(draft(), held_rules=held_rules())
    b = freeze(draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=held_rules())
    assert a.identity != b.identity
    assert freeze(draft(), held_rules=held_rules()).identity == a.identity  # recomputable


def test_the_identity_matches_the_hand_authored_complete_normative_projection():
    spec = freeze(draft(), held_rules=held_rules())
    assert spec.identity == v1.digest(
        SPEC_DOMAIN,
        {
            "target": "prop-1",
            "estimand_grammar": ESTIMAND_GRAMMAR,
            "estimand": estimand_projection(typed_estimand()),
            "method": "fit the model",
            "assumptions": "iid draws",
            "falsification": "a null effect",
            "input_roles": [{"role": "observes", "dataset": DATA_ADDRESS}],
            "applicability": applicability_projection(typed_applicability()),
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
            "registers": [],
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

    with pytest.raises(TypeError, match="minted by freeze, revise or restore"):
        FrozenSpec(**members)
    with pytest.raises(TypeError, match="minted by freeze, revise or restore"):
        dataclasses.replace(original, identity="forged-spec-id")

    successor = revise(
        original,
        edits={"estimand": typed_estimand(reference=Decimal(1))},
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
            "estimand_grammar": ESTIMAND_GRAMMAR,
            "estimand": estimand_projection(typed_estimand()),
            "method": "fit the model",
            "assumptions": "iid draws",
            "falsification": "a null effect",
            "input_roles": [{"role": "observes", "dataset": DATA_ADDRESS}],
            "applicability": applicability_projection(typed_applicability()),
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
            "registers": [],
            "rule_bindings": [
                ["content-identity-equality/v1", "impl-eq-1"],
                ["median-difference/v1", "impl-interp-1"],
            ],
            "supersedes": "spec:prior",
        },
    )


def test_the_exclusion_certification_is_spellable_only_on_a_reads_declaration():
    # The reach check starts here: the certification's authoring home is the
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


def test_editing_the_equivalence_rule_mints_a_successor_that_references():
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


def test_changing_a_root_seed_mints_a_successor_spec():
    # The seed is normative spec content; changing a root is a semantic
    # revision, never a runtime choice.
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"nondeterminism": Seeded(plan=plan(roots={"root-a": 12}))},
        held_rules=held_rules(),
        recorded_failures=frozenset(),
    )
    assert successor.identity != original.identity and successor.supersedes == original.identity


def test_an_unreferenced_successor_to_a_recorded_failed_replay_is_refused():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(
        draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=held_rules()
    )  # supersedes=None
    verdict = admit_successor(unreferenced, original, frozenset({original.identity}), frozenset())
    assert isinstance(verdict, SuccessorRefused)


def test_a_referencing_successor_is_admitted():
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"estimand": typed_estimand(reference=Decimal(1))},
        held_rules=held_rules(),
        recorded_failures=frozenset({original.identity}),
    )
    assert isinstance(
        admit_successor(successor, original, frozenset({original.identity}), frozenset()), SuccessorAdmitted
    )


def test_a_discarded_failed_attempt_is_undetectable():
    # The negative: activeness and reference are over the slice's VALUE state —
    # a failure absent from the supplied set never happened, and nothing can
    # tell (the value-state bound, pinned rather than papered over).
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=held_rules())
    assert isinstance(admit_successor(unreferenced, original, frozenset(), frozenset()), SuccessorAdmitted)


def test_an_unreferenced_successor_to_an_unfinished_recorded_attempt_is_refused():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=held_rules())
    verdict = admit_successor(unreferenced, original, frozenset(), frozenset({original.identity}))
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"


def test_a_spec_in_both_classes_refuses_with_the_recorded_failure_reason():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=held_rules())
    both = frozenset({original.identity})
    verdict = admit_successor(unreferenced, original, both, both)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_a_referencing_successor_lifts_both_classes():
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"estimand": typed_estimand(reference=Decimal(1))},
        held_rules=held_rules(),
        recorded_failures=frozenset(),
    )
    both = frozenset({original.identity})
    assert isinstance(admit_successor(successor, original, both, both), SuccessorAdmitted)


def test_the_core_keeps_its_anchor_line():
    # Other tests name this exact line; it must occur once.
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
    transform = job_key("transform", ())
    resample = job_key("resample", ())
    assert derive_seed(11, transform, "model-initialization") == derive_seed(11, transform, "model-initialization")
    assert derive_seed(11, transform, "model-initialization") != derive_seed(11, transform, "resample-draws")
    assert derive_seed(11, transform, "model-initialization") != derive_seed(12, transform, "model-initialization")
    assert derive_seed(11, transform, "model-initialization") != derive_seed(11, resample, "model-initialization")


def test_revise_is_the_only_edit_path_and_freeze_takes_drafts_only():
    assert list(inspect.signature(freeze).parameters) == ["draft", "held_rules", "supersedes"]
    assert list(inspect.signature(revise).parameters) == ["original", "edits", "held_rules", "recorded_failures"]


# --- restore from canonical projection text, no coercion -----
from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules

from beliefs.spec import frozen_projection, restore


def _rich_spec():
    draft = spec_draft(
        input_roles=(
            SpecInput(role="observes", dataset="dataset:" + "1" * 64),
            SpecInput(
                role="reads",
                dataset="dataset:" + "2" * 64,
                exclusion=ExclusionCertification(rationale="r", attribution="a"),
            ),
        ),
        parameters={"alpha": Decimal("0.05"), "iterations": 10, "labels": ["a", "b"], "nested": {"k": Decimal("1.5")}},
    )
    return freeze(draft, held_rules=spec_rules())


def _identified(mapping) -> tuple[str, bytes]:
    return v1.digest(SPEC_DOMAIN, mapping), v1.encode(mapping)


def test_restore_round_trips_every_member_and_the_decimal_by_type():
    spec = _rich_spec()
    text = v1.encode(frozen_projection(spec))
    restored = restore(spec.identity, text, profile=TESTING_PROFILE)
    assert restored == spec and restored.identity == spec.identity
    assert type(restored.parameters["alpha"]) is Decimal and restored.parameters["alpha"] == Decimal("0.05")
    assert type(restored.parameters["iterations"]) is int
    assert isinstance(restored.nondeterminism, Seeded) and restored.input_roles[1].exclusion is not None
    assert v1.encode(frozen_projection(restored)) == text


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda m: m.__setitem__("method", "another method"),
        lambda m: m.__setitem__("extra", 1),
        lambda m: m.pop("estimand"),
        lambda m: m["parameters"].__setitem__("alpha", Decimal("0.5")),
    ],
)
def test_restore_refuses_a_projection_that_does_not_digest_to_the_identity(corrupt):
    spec = _rich_spec()
    mapping = frozen_projection(spec)
    corrupt(mapping)
    with pytest.raises(MalformedRecord):
        restore(spec.identity, v1.encode(mapping), profile=TESTING_PROFILE)


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda m: m.__setitem__("target", 7),
        lambda m: m.__setitem__("target", ""),
        lambda m: m.__setitem__("parameters", ["not", "a", "mapping"]),
        lambda m: m["nondeterminism"]["plan"]["roots"].__setitem__("model-initialization", Decimal("7.5")),
        lambda m: m["nondeterminism"]["plan"]["roots"].__setitem__("model-initialization", True),
        lambda m: m["input_roles"][0].__setitem__("role", 1),
        lambda m: m.__setitem__("rule_bindings", [["only-one"]]),
        lambda m: m.__setitem__("supersedes", 5),
    ],
)
def test_restore_refuses_a_member_of_the_wrong_type_even_under_its_own_identity(corrupt):
    """The digest agrees with the text by construction; the members are
    still typed and never coerced, and `freeze`'s invariants hold."""
    mapping = frozen_projection(_rich_spec())
    corrupt(mapping)
    identity, text = _identified(mapping)
    with pytest.raises(MalformedRecord):
        restore(identity, text, profile=TESTING_PROFILE)


def test_restore_refuses_a_projection_the_restored_spec_would_not_reproduce():
    """`SeedPlan.projection()` sorts its streams; a text
    with them unsorted is canonical, digests to its own identity, and would
    restore to a spec whose projection digests to another."""
    mapping = frozen_projection(_rich_spec())
    nondeterminism = mapping["nondeterminism"]
    assert isinstance(nondeterminism, dict)
    plan = nondeterminism["plan"]
    assert isinstance(plan, dict)
    plan["streams"] = ["b-stream", "a-stream"]
    plan["stream_roots"] = {"a-stream": "r", "b-stream": "r"}
    plan["roots"] = {"r": 7}
    identity, text = _identified(mapping)
    with pytest.raises(MalformedRecord, match="own projection"):
        restore(identity, text, profile=TESTING_PROFILE)


def test_restore_refuses_non_canonical_text_and_the_unfreezable_pair():
    spec = _rich_spec()
    text = v1.encode(frozen_projection(spec))
    with pytest.raises(MalformedRecord):
        restore(spec.identity, text + b"\n", profile=TESTING_PROFILE)
    with pytest.raises(MalformedRecord):
        restore(spec.identity, v1.encode({"estimand_grammar": ESTIMAND_GRAMMAR}), profile=TESTING_PROFILE)
    mapping = {
        **frozen_projection(freeze(spec_draft(), held_rules=spec_rules())),
        "nondeterminism": StochasticUnseeded(rationale="urandom").projection(),
    }
    identity, text = _identified(mapping)
    with pytest.raises(UnfreezableSpec):
        restore(identity, text, profile=TESTING_PROFILE)


# --- estimand typing: the typed members, the grammar member, restoration ---


def test_the_projection_carries_the_grammar_and_typed_members():
    from beliefs.contract.base import ESTIMAND_GRAMMAR
    from beliefs.estimand import applicability_projection, estimand_projection
    from beliefs.spec import frozen_projection

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    assert projection["estimand_grammar"] == ESTIMAND_GRAMMAR
    assert projection["estimand"] == estimand_projection(spec.estimand)
    assert projection["applicability"] == applicability_projection(spec.applicability)


def test_a_string_estimand_is_refused_at_the_draft():
    with pytest.raises(MalformedSpec, match="Estimand"):
        draft(estimand="the effect of x on y")


@pytest.mark.parametrize(
    "override",
    [
        {
            "contrast": __import__("beliefs.estimand", fromlist=["LevelsContrast"]).LevelsContrast(
                role="cause",
                member=None,
                baseline=__import__("beliefs.claim", fromlist=["Referent"]).Referent("testing/level", "EX:pd"),
                comparison=__import__("beliefs.claim", fromlist=["Referent"]).Referent("testing/level", "EX:ndmm"),
            )
        },
        {"reference": Decimal("0.5")},
    ],
)
def test_each_estimand_member_moves_the_spec_identity(override):
    from fixtures_cut3 import typed_estimand

    assert (
        freeze(draft(), held_rules=held_rules()).identity
        != freeze(draft(estimand=typed_estimand(**override)), held_rules=held_rules()).identity
    )


def test_applicability_moves_the_spec_identity():
    from fixtures_cut3 import typed_applicability

    from beliefs.claim import Qualifier, Referent

    six_months = typed_applicability(
        {"testing/follow-up": Qualifier("generic", Referent("testing/level", "EX:six-months"))}
    )
    assert (
        freeze(draft(), held_rules=held_rules()).identity
        != freeze(draft(applicability=six_months), held_rules=held_rules()).identity
    )


def test_restore_round_trips_the_typed_members():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    restored = restore(spec.identity, v1.encode(frozen_projection(spec)), profile=TESTING_PROFILE)
    assert restored.estimand == spec.estimand and dict(restored.applicability) == dict(spec.applicability)
    assert restored.identity == spec.identity


def test_a_pre_grammar_projection_is_refused_by_name():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.errors import PreGrammarSpec, UnfreezableSpec
    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    del projection["estimand_grammar"]
    projection["estimand"] = "the effect of x on y"
    projection["applicability"] = "the sampled population"
    identity = v1.digest(SPEC_DOMAIN, projection)
    with pytest.raises(PreGrammarSpec, match="pre-grammar spec") as caught:
        restore(identity, v1.encode(projection), profile=TESTING_PROFILE)
    assert isinstance(caught.value, UnfreezableSpec)


def test_another_grammar_identity_is_malformed_not_pre_grammar():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    projection["estimand_grammar"] = "science.estimand.v2"
    with pytest.raises(MalformedRecord, match="estimand_grammar"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=TESTING_PROFILE)


def test_a_malformed_typed_member_restores_as_a_record_error():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.errors import RecordError
    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    projection["estimand"]["measure"]["quantity"] = {"sort": "", "term": "EX:tpm"}  # type: ignore[index]
    with pytest.raises(RecordError, match="do not restore"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=TESTING_PROFILE)


def test_revise_copies_the_typed_members():
    from fixtures_cut3 import typed_estimand

    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original,
        edits={"estimand": typed_estimand(reference=Decimal(1))},
        held_rules=held_rules(),
        recorded_failures=frozenset(),
    )
    assert successor.supersedes == original.identity and successor.estimand.reference == Decimal(1)
    assert dict(successor.applicability) == dict(original.applicability)


# --- registers and the v2 identity domain -----------------------------------

REGISTER = "assumptions-register:" + "ab" * 32


def test_spec_domain_v2():
    assert SPEC_DOMAIN == "science.spec.v2"
    spec = freeze(draft(), held_rules=held_rules())
    assert spec.identity == v1.digest("science.spec.v2", frozen_projection(spec))
    assert spec.identity != v1.digest("science.spec.v1", frozen_projection(spec))


def test_registers_required_and_frozen():
    fields = {name: value for name, value in draft().__dict__.items() if name != "registers"}
    with pytest.raises(TypeError, match="registers"):
        SpecDraft(**fields)  # type: ignore[call-arg]  # required, may be empty
    with pytest.raises(MalformedSpec, match="registers"):
        draft(registers=[REGISTER])
    empty = freeze(draft(), held_rules=held_rules())
    cited = freeze(draft(registers=(REGISTER,)), held_rules=held_rules())
    assert empty.registers == () and cited.registers == (REGISTER,)
    assert frozen_projection(cited)["registers"] == [REGISTER]
    assert cited.identity != empty.identity
    successor = revise(cited, edits={}, held_rules=held_rules(), recorded_failures=frozenset())
    assert successor.registers == (REGISTER,)


@pytest.mark.parametrize(
    "entry",
    [
        "assumptions-register:" + "AB" * 32,
        "assumptions-register:" + "ab" * 31,
        "assumptions-register:" + "ab" * 32 + "\n",
        "register:" + "ab" * 32,
        "dataset:" + "ab" * 32,
        "",
    ],
)
def test_malformed_register_id_refuses_at_freeze(entry):
    with pytest.raises(MalformedSpec, match="assumptions-register"):
        freeze(draft(registers=(REGISTER, entry)), held_rules=held_rules())


def test_registers_are_canonical_in_the_projection():
    """T7-m1: the cited registers are a set; two authoring orders are one spec."""
    other = "assumptions-register:" + "cd" * 32
    one = freeze(draft(registers=(other, REGISTER)), held_rules=held_rules())
    two = freeze(draft(registers=(REGISTER, other)), held_rules=held_rules())
    assert one.identity == two.identity and one == two
    assert one.registers == (REGISTER, other)
    assert frozen_projection(one)["registers"] == [REGISTER, other]


def test_a_duplicate_register_refuses():
    with pytest.raises(MalformedSpec, match="more than once"):
        freeze(draft(registers=(REGISTER, REGISTER)), held_rules=held_rules())


def test_restore_refuses_registers_out_of_canonical_form():
    other = "assumptions-register:" + "cd" * 32
    spec = freeze(draft(registers=(REGISTER, other)), held_rules=held_rules())
    for bad, reason in (([other, REGISTER], "own projection"), ([REGISTER, REGISTER], "more than once")):
        mapping = frozen_projection(spec)
        mapping["registers"] = bad
        with pytest.raises(MalformedRecord, match=reason):
            restore(*_identified(mapping), profile=TESTING_PROFILE)


def test_restore_reads_registers():
    spec = freeze(draft(registers=(REGISTER,)), held_rules=held_rules())
    text = v1.encode(frozen_projection(spec))
    restored = restore(spec.identity, text, profile=TESTING_PROFILE)
    assert restored.registers == (REGISTER,) and restored == spec
    missing = frozen_projection(spec)
    del missing["registers"]
    with pytest.raises(MalformedRecord, match="frozen members"):
        restore(*_identified(missing), profile=TESTING_PROFILE)
    for bad in (["assumptions-register:" + "zz" * 32], "not-a-list", [7]):
        mapping = frozen_projection(spec)
        mapping["registers"] = bad
        with pytest.raises(MalformedRecord, match="register"):
            restore(*_identified(mapping), profile=TESTING_PROFILE)
