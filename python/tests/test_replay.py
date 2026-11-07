"""The full walk, the retained checks, the three inconclusive
checks, the evaluator and scope checks, the replay-eligibility third.
The admission conjunct and the nothing-is-admitted conjunct live in
acceptance/test_confinement_acceptance.py; the persistence-seam negative
is deferred.
The family/job/stream completeness is checked from the workflow snapshot.
"""

import dataclasses
import inspect
from decimal import Decimal
from pathlib import Path

import pytest
from confinement_fixtures import confined_receipt, instance
from fixtures_cut3 import (
    D_IN,
    DATA_ADDRESS,
    READS_ADDRESS,
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_PRODUCTION,
    SNAKEFILE_SEED_VIOLATING,
    closure_kwargs,
    closure_with,
    planned,
    seed_plan,
    spec_draft,
    spec_rules,
    traced,
    traced_from_key,
    typed_applicability,
    typed_estimand,
)
from fixtures_cut3 import (
    memory_assessment as run_assessment,
)
from fixtures_cut3 import (
    memory_production as run_production,
)
from fixtures_cut3 import (
    memory_replay as replay_of,
)

from beliefs.admission import admit
from beliefs.belief import Belief
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run
from beliefs.closure import build_closure
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import MalformedRecord
from beliefs.recipe import CAPABILITIES, BoundaryPolicy, ResultManifest, TraceJob, WorkflowDefinitionSnapshot, job_key
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.replay import (
    AVAILABLE,
    CONFORMING,
    CONTENT_EQUALITY,
    DATASET_CONTENT_EQUALITY,
    NOT_AVAILABLE,
    CodeLineageCertification,
    EquivalenceImplementation,
    byte_tolerance_rule,
    conformance,
    definition_agrees_with_plan,
    derive_scope,
    qualifies,
    replay_eligibility,
)
from beliefs.report import CLOSED, AssessmentRunIntent, Registration, completion
from beliefs.spec import Deterministic, RealizedSeeds, Seeded, SeedPlan, StochasticUnseeded, derive_seed, freeze
from beliefs.verification import Verification, lifecycle_state

DIGEST = "sha256:" + "11" * 32
FIT_A = job_key("fit", (("sample", "a"),))
FIT_B = job_key("fit", (("sample", "b"),))
SPLIT_FIT = job_key("fit", ())
SPLIT_RESAMPLE = job_key("resample", ())
correct_seed = derive_seed


def _snapshot(family_streams):
    return WorkflowDefinitionSnapshot(
        snakefile_digest=DIGEST,
        family_streams=family_streams,
        checkpoint_expanded_families=(),
    )


def test_definition_agreement_is_none(request) -> None:
    assert request.node.get_closest_marker("xdist_group") is None
    assert definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), seed_plan()) is None


def test_a_family_stream_no_logical_stream_matches_disagrees() -> None:
    reason = definition_agrees_with_plan(_snapshot({"fit": ("resample-draws",)}), seed_plan())
    assert reason is not None and "resample-draws" in reason


def test_a_logical_stream_no_family_claims_disagrees() -> None:
    plan = seed_plan(streams=("model-initialization", "resample-draws"))
    reason = definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), plan)
    assert reason is not None and "resample-draws" in reason


def test_a_deterministic_definition_expects_no_streams() -> None:
    assert definition_agrees_with_plan(_snapshot({}), None) is None
    assert definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), None) is not None


def _family_run(*, families, plan, seeds):
    return closure_with(
        nondeterminism=Seeded(plan=plan),
        family_streams=families,
        realized={key: dict(streams) for key, streams in seeds.items()},
        trace=tuple(traced_from_key(key) for key in seeds),
    )


def test_a_job_realizing_a_stream_its_family_does_not_declare_is_non_conforming() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    seeds = {FIT_A: {stream: correct_seed(11, FIT_A, stream) for stream in ("model-initialization", "resample-draws")}}
    run = _family_run(
        families={"fit": ("model-initialization",), "other": ("resample-draws",)},
        plan=plan,
        seeds=seeds,
    )
    assert {stream for claims in seeds.values() for stream in claims} == set(plan.streams)
    assert conformance(run).startswith("non-conforming")


def test_a_job_omitting_a_stream_its_family_declares_is_non_conforming() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    other = job_key("other", ())
    seeds = {
        FIT_A: {"model-initialization": correct_seed(11, FIT_A, "model-initialization")},
        other: {"resample-draws": correct_seed(11, other, "resample-draws")},
    }
    families = {
        "fit": ("model-initialization", "resample-draws"),
        "other": ("resample-draws",),
    }
    run = _family_run(families=families, plan=plan, seeds=seeds)
    assert {stream for claims in seeds.values() for stream in claims} == set(plan.streams)
    assert conformance(run).startswith("non-conforming")


def test_a_wildcard_instance_is_judged_against_its_family() -> None:
    plan = seed_plan(streams=("model-initialization",))
    seeds = {key: {"model-initialization": correct_seed(11, key, "model-initialization")} for key in (FIT_A, FIT_B)}
    assert conformance(_family_run(families={"fit": ("model-initialization",)}, plan=plan, seeds=seeds)) == CONFORMING


def test_different_families_realizing_different_streams_conforms() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    a, b = job_key("a", ()), job_key("b", ())
    seeds = {
        a: {"model-initialization": correct_seed(11, a, "model-initialization")},
        b: {"resample-draws": correct_seed(11, b, "resample-draws")},
    }
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    assert conformance(_family_run(families=families, plan=plan, seeds=seeds)) == CONFORMING


def test_an_over_claiming_record_does_not_conform() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    a, b = job_key("a", ()), job_key("b", ())
    seeds = {
        key: {stream: correct_seed(11, key, stream) for stream in ("model-initialization", "resample-draws")}
        for key in (a, b)
    }
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    assert conformance(_family_run(families=families, plan=plan, seeds=seeds)).startswith("non-conforming")


def test_two_streams_in_one_job_are_both_checked() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    seeds = {FIT_A: {stream: correct_seed(11, FIT_A, stream) for stream in ("model-initialization", "resample-draws")}}
    run = _family_run(
        families={"fit": ("model-initialization", "resample-draws")},
        plan=plan,
        seeds=seeds,
    )
    assert conformance(run) == CONFORMING


def test_a_constructed_closure_whose_definition_disagrees_is_non_conforming() -> None:
    run = closure_with(
        family_streams={"fit": ("model-initialization",)},
        nondeterminism=Deterministic(),
        trace=(),
    )
    assert conformance(run).startswith("non-conforming")


def test_a_declared_stream_no_executed_job_realized_is_non_conforming() -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    a = job_key("a", ())
    seeds = {a: {"model-initialization": correct_seed(11, a, "model-initialization")}}
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    assert conformance(_family_run(families=families, plan=plan, seeds=seeds)).startswith("non-conforming")


def test_a_seed_claim_for_a_job_absent_from_the_trace_is_non_conforming() -> None:
    plan = seed_plan(streams=("model-initialization",))
    orphan = job_key("fit", (("sample", "b"),))
    realized = {
        FIT_A: {"model-initialization": correct_seed(11, FIT_A, "model-initialization")},
        orphan: {"model-initialization": correct_seed(11, orphan, "model-initialization")},
    }
    run = closure_with(
        nondeterminism=Seeded(plan=plan),
        family_streams={"fit": ("model-initialization",)},
        realized=realized,
        trace=(traced_from_key(FIT_A),),
    )
    assert {stream for claims in realized.values() for stream in claims} == set(plan.streams)
    assert conformance(run).startswith("non-conforming: seed claims for jobs absent")


def test_an_executed_job_outside_the_plan_is_non_conforming() -> None:
    run = closure_with(
        planned=(planned("fit", ("outputs/a.done",)),),
        trace=(traced("fit", {"s": "a"}), traced("stowaway", {})),
        target_keys=(job_key("fit", (("s", "a"),)),),
    )
    assert "not in the plan" in conformance(run)


def test_a_checkpoint_expanded_family_is_admitted_though_unplannable() -> None:
    run = closure_with(
        planned=(planned("split", ("splits",), is_checkpoint=True),),
        trace=(traced("split", {}), traced("fit", {"n": "a"})),
        expanded=("fit",),
        target_keys=(job_key("split", ()),),
        targets=("split",),
    )
    assert conformance(run) == CONFORMING


def test_an_unexpanded_family_gets_no_checkpoint_admission() -> None:
    run = closure_with(
        planned=(planned("split", ("splits",), is_checkpoint=True),),
        trace=(traced("split", {}), traced("fit", {"n": "a"})),
        expanded=(),
        target_keys=(job_key("split", ()),),
    )
    assert "not in the plan" in conformance(run)


def test_a_resolved_target_missing_from_the_trace_is_non_conforming() -> None:
    run = closure_with(
        planned=(
            planned("fit", ("outputs/a.done",)),
            planned("report", ("outputs/r.txt",)),
        ),
        trace=(traced("fit", {}),),
        target_keys=(job_key("report", ()),),
        targets=("report",),
    )
    assert "target" in conformance(run)


def test_recorded_target_keys_must_be_the_invocation_targets_resolution() -> None:
    run = closure_with(
        planned=(planned("report", ("outputs/r.txt",)),),
        trace=(),
        target_keys=(),
        targets=("report",),
    )
    assert "recorded target keys" in conformance(run)


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    base = tmp_path_factory.mktemp("replay")
    scratch_base = base / "scratch"
    original = run_assessment(base / "original", scratch_base=scratch_base)
    replayed = replay_of(original, base / "replayed", scratch_base=scratch_base)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    return original, replayed


def test_a_replay_runs_in_a_fresh_scratch_root_with_an_equal_recipe(pair, request):
    mark = request.node.get_closest_marker("xdist_group")
    assert mark is not None and mark.args == ("tests/test_replay.py",)
    original, replayed = pair
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert (
        original.run.occurrence.receipt.execution.scratch_mapping
        != replayed.run.occurrence.receipt.execution.scratch_mapping
    )
    assert (
        Path(original.run.occurrence.receipt.execution.scratch_mapping).parent
        == Path(replayed.run.occurrence.receipt.execution.scratch_mapping).parent
    )


def test_a_production_replay_runs_through_the_boundary_with_an_equal_recipe(tmp_path):
    original = run_production(tmp_path / "original")
    replayed = replay_of(original, tmp_path / "replayed", snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert (
        original.run.occurrence.receipt.execution.scratch_mapping
        != replayed.run.occurrence.receipt.execution.scratch_mapping
    )


def test_replay_over_a_closure_is_replay_over_the_minted_result(monkeypatch, tmp_path):
    from test_audit import assessment_closure

    from beliefs import replay as replay_module

    frozen = freeze(spec_draft(), held_rules=spec_rules())
    closure = assessment_closure(frozen)
    minted = RunMinted(
        run=closure,
        intent=AssessmentRunIntent(frozen.identity, "tok", "test-actor"),
        registration=Registration("tok", "p" * 64),
    )
    seen: list[dict] = []

    def capture(**kwargs):
        seen.append(kwargs)
        return "sentinel"

    monkeypatch.setattr(replay_module, "execute_assessment_run", capture)
    common = {
        "port": object(),
        "spec": frozen,
        "definition": closure.recipe.workflow_definition,
        "code_roots": (),
        "held_inputs": {},
        "entrypoint": "e",
        "targets": ("t",),
        "declared_outputs": tuple(n for n, _ in closure.result.outputs),
        "observer": "o",
        "started_at": "2026-09-09T00:00:00Z",
        "host_realization": "h",
        "scratch_base": tmp_path,
    }
    assert replay_module.replay(minted, **common) == "sentinel"
    assert replay_module.replay(closure, **common) == "sentinel"
    assert seen[0] == seen[1]


def test_a_replay_refuses_a_reconstructed_recipe_mismatch(tmp_path):
    original = run_assessment(tmp_path / "original")
    changed = SNAKEFILE_DETERMINISTIC.replace(
        "import pathlib, random",
        "import pathlib, random  # changed recipe",
    )
    attempt = replay_of(original, tmp_path / "changed", snakefile=changed)
    assert isinstance(attempt, RunRefused)
    assert attempt.reason == "recipe-identity-mismatch"
    assert attempt.report is not None and attempt.intent is not None and attempt.registration is not None
    assert attempt.registration.intent_token == attempt.intent.event_token
    assert attempt.registration.pointer == attempt.report.identity()
    assert (
        completion(
            attempt.intent,
            (attempt.registration,),
            {attempt.report.identity(): attempt.report},
        )
        == CLOSED
    )


def existing_assessment_state(original):
    existing = AssessmentValue(
        spec="s",
        run=original.run.address(),
        proposition="p",
        outcome="supported",
        interpretation_rule="r",
        estimand=typed_estimand(),
        applicability=typed_applicability(),
    )
    admitting = (
        Verification(
            ref="v1",
            assessment=existing.identity(),
            scope="clean-environment",
            verdict="passed",
        ),
    )
    return admitting, lifecycle_state(admitting)


def test_an_unreplayable_run_creates_no_verification_and_changes_no_state(pair, tmp_path):
    original, _ = pair
    admitting, before = existing_assessment_state(original)
    before_records = admitting
    assert replay_eligibility(original.run, resolvable_here=frozenset(), attributions={}) == NOT_AVAILABLE
    attempt = replay_of(
        original,
        tmp_path / "gone",
        held_inputs={
            DATA_ADDRESS: tmp_path / "gone" / "missing" / "data.txt",
            READS_ADDRESS: tmp_path / "gone" / "missing" / "palette.txt",
        },
    )
    assert isinstance(attempt, RunRefused)
    assert admitting == before_records
    assert lifecycle_state(admitting) == before


def test_restoring_availability_changes_nothing_until_a_replay_actually_runs(pair, tmp_path):
    original, _ = pair
    admitting, before = existing_assessment_state(original)
    everything = frozenset(
        {
            original.run.recipe.code_identity,
            original.run.recipe.environment.identity(),
            original.run.recipe.workflow_definition.identity(),
            *(i.content for i in original.run.recipe.inputs),
        }
    )
    assert (
        replay_eligibility(
            original.run,
            resolvable_here=everything,
            attributions={original.run.address(): "corpus-1"},
        )
        == AVAILABLE
    )
    assert lifecycle_state(admitting) == before
    replayed = replay_of(original, tmp_path / "again")
    assert isinstance(replayed, RunMinted)


def test_a_missing_output_yields_inconclusive(pair):
    original, replayed = pair
    rule = byte_tolerance_rule(store={})
    assert rule.evaluate(original.run.result, replayed.run.result) == "inconclusive"


def test_an_unreadable_output_yields_inconclusive(pair):
    original, replayed = pair
    digests = [d for _, d in original.run.result.outputs] + [d for _, d in replayed.run.result.outputs]
    rule = byte_tolerance_rule(store={d: b"HELLO-not-a-number" for d in digests})
    assert rule.evaluate(original.run.result, replayed.run.result) == "inconclusive"


def test_a_reader_error_yields_inconclusive(pair):
    original, replayed = pair

    class Exploding(dict):
        def __getitem__(self, key):
            raise OSError("reader failure")

    assert byte_tolerance_rule(Exploding()).evaluate(original.run.result, replayed.run.result) == "inconclusive"


def test_a_byte_tolerance_rule_compares_numeric_payloads():
    left = ResultManifest(outputs=(("result", "left"),))
    close = ResultManifest(outputs=(("result", "close"),))
    far = ResultManifest(outputs=(("result", "far"),))
    rule = byte_tolerance_rule({"left": b"1", "close": b"1.000001", "far": b"1.000002"})
    assert rule.evaluate(left, close) == "passed"
    assert rule.evaluate(left, far) == "failed"


# --- the evaluator and scope checks -------------------------------------------
def test_no_equivalence_rule_can_read_an_occurrence():
    with pytest.raises(MalformedRecord):
        EquivalenceImplementation(
            identity="impl-bad",
            evaluate=lambda a, b, occurrence: "passed",  # type: ignore[arg-type]
            fixtures=(),
        )
    for held in (CONTENT_EQUALITY, DATASET_CONTENT_EQUALITY):
        assert len(inspect.signature(held.evaluate).parameters) == 2


@pytest.mark.parametrize(
    "identity, fixtures",
    [
        ("", ()),
        (1, ()),
        ("impl", []),
        ("impl", (object(),)),
    ],
)
def test_equivalence_implementations_are_strict_immutable_values(identity, fixtures):
    with pytest.raises(MalformedRecord):
        EquivalenceImplementation(identity=identity, evaluate=lambda a, b: "passed", fixtures=fixtures)

    with pytest.raises(dataclasses.FrozenInstanceError):
        CONTENT_EQUALITY.identity = "changed"  # type: ignore[misc]


def test_a_seed_violating_run_is_non_conforming_and_derives_not_certified(tmp_path):
    violating = run_assessment(tmp_path / "v", snakefile=SNAKEFILE_SEED_VIOLATING)
    clean = replay_of(violating, tmp_path / "r", snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(violating, RunMinted) and isinstance(clean, RunMinted)
    assert conformance(violating.run).startswith("non-conforming")
    assert derive_scope(violating.run, clean.run, certification=None) == "not-certified"


def test_conformance_enforces_each_nondeterminism_contract(pair):
    original, _ = pair
    assert conformance(original.run) == CONFORMING

    deterministic_recipe = dataclasses.replace(
        original.run.recipe,
        nondeterminism=Deterministic(),
        workflow_definition=dataclasses.replace(original.run.recipe.workflow_definition, family_streams={}),
    )
    no_seeds = dataclasses.replace(
        original.run,
        recipe=deterministic_recipe,
        occurrence=dataclasses.replace(
            original.run.occurrence,
            realized_seeds=RealizedSeeds(seeds={}),
        ),
    )
    assert conformance(no_seeds) == CONFORMING
    assert conformance(dataclasses.replace(no_seeds, occurrence=original.run.occurrence)).startswith("non-conforming")

    unconstrained = dataclasses.replace(
        no_seeds,
        recipe=dataclasses.replace(
            deterministic_recipe,
            nondeterminism=StochasticUnseeded(rationale="external entropy"),
        ),
    )
    assert conformance(unconstrained) == CONFORMING


def split_family_run(run):
    plan = SeedPlan(
        derivation_rule="seed-derivation/v1",
        streams=("initialization", "draws"),
        roots={"fit-root": 11, "resample-root": 22},
        stream_roots={"initialization": "fit-root", "draws": "resample-root"},
    )
    trace = (
        TraceJob("0", "fit", (), ("inputs/data.txt",), ("outputs/fit.txt",)),
        TraceJob("1", "resample", (), ("outputs/fit.txt",), ("outputs/result.txt",)),
    )
    realized = RealizedSeeds(
        seeds={
            SPLIT_FIT: {"initialization": derive_seed(11, SPLIT_FIT, "initialization")},
            SPLIT_RESAMPLE: {"draws": derive_seed(22, SPLIT_RESAMPLE, "draws")},
        }
    )
    return dataclasses.replace(
        run,
        recipe=dataclasses.replace(
            run.recipe,
            workflow_definition=WorkflowDefinitionSnapshot(
                snakefile_digest=run.recipe.workflow_definition.snakefile_digest,
                family_streams={"fit": ("initialization",), "resample": ("draws",)},
                checkpoint_expanded_families=(),
            ),
            nondeterminism=Seeded(plan),
        ),
        occurrence=dataclasses.replace(
            run.occurrence,
            trace=trace,
            planned=(
                planned("fit", ("outputs/fit.txt",)),
                planned("resample", ("outputs/result.txt",)),
            ),
            target_keys=(SPLIT_RESAMPLE,),
            realized_seeds=realized,
        ),
    )


def test_seeded_conformance_checks_reported_split_family_claims_without_a_global_cross_product(pair):
    original, _ = pair
    assert conformance(split_family_run(original.run)) == CONFORMING


def test_seeded_conformance_refuses_an_undeclared_reported_stream(pair):
    original, _ = pair
    split = split_family_run(original.run)
    realized = split.occurrence.realized_seeds
    extra = RealizedSeeds(
        seeds={
            **realized.seeds,
            SPLIT_FIT: {**realized.seeds[SPLIT_FIT], "undeclared": 1},
        }
    )
    changed = dataclasses.replace(
        split,
        occurrence=dataclasses.replace(split.occurrence, realized_seeds=extra),
    )
    assert conformance(changed).startswith("non-conforming")


def test_seeded_conformance_refuses_a_wrong_reported_seed(pair):
    original, _ = pair
    split = split_family_run(original.run)
    realized = split.occurrence.realized_seeds
    wrong = RealizedSeeds(
        seeds={
            **realized.seeds,
            SPLIT_RESAMPLE: {"draws": realized.seeds[SPLIT_RESAMPLE]["draws"] + 1},
        }
    )
    changed = dataclasses.replace(
        split,
        occurrence=dataclasses.replace(split.occurrence, realized_seeds=wrong),
    )
    assert conformance(changed).startswith("non-conforming")


def test_no_authored_scope_parameter_exists():
    assert "scope" not in inspect.signature(derive_scope).parameters
    assert "scope" not in inspect.signature(execute_assessment_run).parameters


def test_equal_recipes_without_a_receipt_derive_same_environment(pair):
    original, replayed = pair
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"


def test_a_hostname_change_stays_same_environment(tmp_path):
    a = run_assessment(tmp_path / "a", host_realization="host-x")
    b = replay_of(a, tmp_path / "b", host_realization="host-y")
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    assert derive_scope(a.run, b.run, certification=None) == "same-environment"
    assert a.run.occurrence.receipt.execution.capabilities == ()


def test_a_comment_change_is_not_certified_never_independent(tmp_path):
    a = run_assessment(tmp_path / "a")
    commented = SNAKEFILE_DETERMINISTIC.replace(
        "import pathlib, random",
        "import pathlib, random  # a comment",
    )
    b = run_assessment(tmp_path / "b", snakefile=commented)
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    assert a.run.recipe.code_identity != b.run.recipe.code_identity
    assert derive_scope(a.run, b.run, certification=None) == "not-certified"


def test_independent_implementation_needs_all_four_conditions(tmp_path):
    a = run_assessment(tmp_path / "a")
    reimplemented = SNAKEFILE_DETERMINISTIC.replace("text.upper()", "text.upper() + ''")
    b = run_assessment(tmp_path / "b", snakefile=reimplemented)
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    certified = CodeLineageCertification(rationale="independent rewrite", attribution="tester")
    assert derive_scope(a.run, b.run, certification=certified) == "independent-implementation"
    assert derive_scope(a.run, b.run, certification=None) == "not-certified"


def test_a_different_spec_identity_is_not_certified(tmp_path):
    a = run_assessment(tmp_path / "a")
    other_spec = freeze(spec_draft(estimand=typed_estimand(reference=Decimal(1))), held_rules=spec_rules())
    b = run_assessment(tmp_path / "b", spec=other_spec)
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    certified = CodeLineageCertification(rationale="claim", attribution="tester")
    assert derive_scope(a.run, b.run, certification=certified) == "not-certified"


def test_code_lineage_certification_is_strict_and_immutable():
    certification = CodeLineageCertification(rationale="independent rewrite", attribution="tester")
    with pytest.raises(dataclasses.FrozenInstanceError):
        certification.rationale = "changed"  # type: ignore[misc]
    with pytest.raises(MalformedRecord):
        CodeLineageCertification(rationale="", attribution="tester")


def _confined(minted, *, capabilities=CAPABILITIES, environment_identity=None):
    run = minted.run
    identity = environment_identity if environment_identity is not None else run.recipe.environment.identity()
    receipt = confined_receipt(capabilities=capabilities, instance=instance(environment_identity=identity))
    return dataclasses.replace(run, occurrence=dataclasses.replace(run.occurrence, receipt=receipt))


def test_the_clean_environment_row_is_reached_only_through_a_qualifying_receipt(pair):
    original, replayed = pair
    assert derive_scope(original.run, _confined(replayed), certification=None) == "clean-environment"
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"
    foreign = _confined(replayed, environment_identity="sha256:" + "00" * 32)
    assert derive_scope(original.run, foreign, certification=None) == "same-environment"


def test_a_receipt_missing_a_required_capability_derives_same_environment(pair):
    original, replayed = pair
    for missing in CAPABILITIES:
        fewer = tuple(capability for capability in CAPABILITIES if capability != missing)
        assert (
            derive_scope(original.run, _confined(replayed, capabilities=fewer), certification=None)
            == "same-environment"
        )


def test_a_policy_qualifies_whatever_its_version_string(pair):
    original, replayed = pair
    v99 = BoundaryPolicy(
        identity="boundary-policy/confined-v99", scope_rule="scope-derivation/v1", capabilities=CAPABILITIES
    )
    left = dataclasses.replace(original.run, recipe=dataclasses.replace(original.run.recipe, boundary_policy=v99))
    right = _confined(replayed)
    right = dataclasses.replace(right, recipe=dataclasses.replace(right.recipe, boundary_policy=v99))
    assert left.recipe.identity() == right.recipe.identity()
    assert derive_scope(left, right, certification=None) == "clean-environment"


def test_two_incomparable_policies_are_not_ranked(pair):
    original, replayed = pair
    one = _confined(replayed, capabilities=("from-bundle", "closure-confined-filesystem"))
    other = _confined(replayed, capabilities=("from-bundle", "network-denied"))
    assert derive_scope(original.run, one, certification=None) == "same-environment"
    assert derive_scope(original.run, other, certification=None) == "same-environment"
    identity = replayed.run.recipe.environment.identity()
    assert qualifies(confined_receipt(instance=instance(environment_identity=identity)), identity)
    assert not qualifies(one.occurrence.receipt, identity) and not qualifies(other.occurrence.receipt, identity)


def test_minimal_pair_never_derives_clean_environment(pair):
    original, replayed = pair
    execution = replayed.run.occurrence.receipt.execution
    assert execution.capabilities == () and execution.instance is None
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"
    assert not qualifies(replayed.run.occurrence.receipt, replayed.run.recipe.environment.identity())


def test_unreachable_bytes_with_a_held_copy_move_none_of_the_three(pair):
    original, _ = pair
    d = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D_IN),))
    run = RunValue(ref="run:run-1", spec="spec-1", inputs=(RunInput(role="observes", dataset=d),))
    assessment = AssessmentValue(
        spec="spec-1",
        run="run-1",
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="r",
        estimand=typed_estimand(),
        applicability=typed_applicability(),
    )
    admitting = (
        Verification(
            ref="v1",
            assessment=assessment.identity(),
            scope="clean-environment",
            verdict="passed",
        ),
    )
    address = dataset_address(d)
    assert address is not None
    local = {address: (ByteObservation(digest=D_IN, location="repo://data"),)}
    far = {address: (ByteObservation(digest=D_IN, location="https://mirror.example/data"),)}
    kwargs = closure_kwargs((assessment,), {"run-1": run})
    before_digest = build_closure(**kwargs).digest()
    before_admission = admit(assessment, run, local, admitting)
    after_digest = build_closure(**kwargs).digest()
    after_admission = admit(assessment, run, far, admitting)
    assert after_digest == before_digest
    assert not {"observations", "availability", "resolvable"} & set(inspect.signature(build_closure).parameters)
    assert after_admission == before_admission
    reading = replay_eligibility(
        original.run,
        resolvable_here=frozenset(),
        attributions={original.run.address(): "corpus-1"},
    )
    assert reading == NOT_AVAILABLE
    assert reading not in ("unverified", "failed")


def test_removing_the_corpus_attribution_reads_not_available_never_an_unchanged_belief(pair):
    original, _ = pair
    everything = frozenset(
        {
            original.run.recipe.code_identity,
            original.run.recipe.environment.identity(),
            original.run.recipe.workflow_definition.identity(),
            *(i.content for i in original.run.recipe.inputs),
        }
    )
    reading = replay_eligibility(original.run, resolvable_here=everything, attributions={})
    assert reading == NOT_AVAILABLE
    assert not isinstance(reading, Belief)


def _forbid_replay_engines(monkeypatch):
    from beliefs import boundary as boundary_module

    def _never_engine(*args, **kwargs):
        raise AssertionError("engine must not launch when replay input digest check refuses")

    monkeypatch.setattr(boundary_module, "run_engine", _never_engine)
    monkeypatch.setattr(boundary_module, "launch_confined", _never_engine)


def test_replay_refuses_mutated_held_input_before_any_engine_launch(tmp_path, monkeypatch):
    original = run_assessment(tmp_path / "original")
    assert isinstance(original, RunMinted)

    tampered = tmp_path / "tampered"
    tampered.mkdir()
    bad_data = tampered / "data.txt"
    bad_data.write_bytes(b"mutated-after-run\n")
    palette = tmp_path / "original" / "held" / "palette.txt"

    _forbid_replay_engines(monkeypatch)
    attempt = replay_of(
        original,
        tmp_path / "replay",
        held_inputs={DATA_ADDRESS: bad_data, READS_ADDRESS: palette},
    )
    assert isinstance(attempt, RunRefused)
    assert "does not match expected" in attempt.reason
    assert attempt.intent is not None and attempt.report is not None and attempt.registration is not None
    assert completion(attempt.intent, (attempt.registration,), {attempt.report.identity(): attempt.report}) == CLOSED


def test_assessment_replay_refuses_conflicting_recipe_input_digests_without_launching_engine(tmp_path, monkeypatch):
    from beliefs.recipe import RecipeInput

    original = run_assessment(tmp_path / "original")
    assert isinstance(original, RunMinted)

    conflicting_recipe = dataclasses.replace(
        original.run.recipe,
        inputs=(
            RecipeInput("observes", DATA_ADDRESS, original.run.recipe.inputs[0].content),
            RecipeInput("reads", DATA_ADDRESS, "sha256:" + "f" * 64),
        ),
    )
    conflicting = dataclasses.replace(
        original,
        run=dataclasses.replace(original.run, recipe=conflicting_recipe),
    )

    _forbid_replay_engines(monkeypatch)
    attempt = replay_of(conflicting, tmp_path / "conflicting")
    assert isinstance(attempt, RunRefused)
    assert "recipe inputs disagree on content identity" in attempt.reason
    assert attempt.intent is not None and attempt.report is not None and attempt.registration is not None
    assert completion(attempt.intent, (attempt.registration,), {attempt.report.identity(): attempt.report}) == CLOSED


def test_assessment_replay_refuses_when_supplied_expected_inputs_disagree_with_recipe_inputs_even_if_bytes_match(
    tmp_path, monkeypatch
):
    from beliefs import boundary as boundary_module

    original = run_assessment(tmp_path / "original")
    assert isinstance(original, RunMinted)
    digest_a = original.run.recipe.inputs[0].content

    restored = tmp_path / "restored"
    restored.mkdir()
    restored_data = restored / "data.txt"
    restored_data.write_bytes(b"restored-declared\n")
    digest_b = boundary_module._digest(restored_data)
    assert boundary_module._digest(restored_data) == digest_b
    assert digest_b != digest_a
    palette = tmp_path / "original" / "held" / "palette.txt"

    _forbid_replay_engines(monkeypatch)
    attempt = replay_of(
        original,
        tmp_path / "replay",
        held_inputs={DATA_ADDRESS: restored_data, READS_ADDRESS: palette},
        expected_inputs={DATA_ADDRESS: digest_b},
    )
    assert isinstance(attempt, RunRefused)
    assert "does not match recipe input" in attempt.reason
    assert attempt.intent is not None and attempt.report is not None and attempt.registration is not None
    assert completion(attempt.intent, (attempt.registration,), {attempt.report.identity(): attempt.report}) == CLOSED


# --- multi-resource and 1-resource nested member replay (beliefs-98f1d7) ---

from fixtures_cut3 import MEMORY_PORT, definition, stage

from beliefs.boundary import _digest, execute_production_run
from beliefs.recipe import MINIMAL_POLICY, RecipeInput
from beliefs.replay import replay as _replay_fn
from beliefs.spec import SpecInput

SNAKEFILE_REPLAY_MULTI = """\
import pathlib

rule transform:
    input: "inputs/tables/expression.tsv", "inputs/tables/clinical.tsv"
    output: "outputs/result.txt"
    run:
        expr = pathlib.Path(input[0]).read_text()
        clin = pathlib.Path(input[1]).read_text()
        pathlib.Path(output[0]).write_text((expr + "|" + clin).upper())
"""

SNAKEFILE_REPLAY_NESTED_SINGLE = """\
import pathlib

rule transform:
    input: "inputs/tables/clinical.tsv"
    output: "outputs/result.txt"
    run:
        assert not pathlib.Path("inputs/clinical.tsv").exists()
        clin = pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text(clin.upper())
"""


def test_replay_multi_resource_and_single_resource_nested_member_mappings(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    expr_path = pkg / "expression.tsv"
    clin_path = pkg / "clinical.tsv"
    expr_path.write_text("gene\ttpm\nTP53\t42\n")
    clin_path.write_text("sample\tarm\nS1\tA\n")
    expr_digest = _digest(expr_path)
    clin_digest = _digest(clin_path)

    multi_held = {
        DATA_ADDRESS: {
            "tables/expression.tsv": expr_path,
            "tables/clinical.tsv": clin_path,
        }
    }
    multi_expected = {
        DATA_ADDRESS: {
            "tables/expression.tsv": expr_digest,
            "tables/clinical.tsv": clin_digest,
        }
    }
    folded_addr = dataset_address(
        DatasetDeclaration(
            resources=(
                ResourceDeclaration("tables/clinical.tsv", clin_digest),
                ResourceDeclaration("tables/expression.tsv", expr_digest),
            )
        )
    )
    assert folded_addr is not None
    folded_digest = folded_addr.removeprefix("dataset:")

    # 1. Multi-resource assessment run + replay (with expected_inputs and with expected_inputs=None)
    code_multi, _ = stage(tmp_path / "code-multi", snakefile=SNAKEFILE_REPLAY_MULTI)
    spec_multi = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
        ),
        held_rules=spec_rules(),
    )
    defn_multi = definition(snakefile=SNAKEFILE_REPLAY_MULTI, family_streams={})
    orig_assess = execute_assessment_run(
        spec=spec_multi,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=defn_multi,
        code_roots=(code_multi,),
        held_inputs=multi_held,
        expected_inputs=multi_expected,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch-assess-orig",
        cores=1,
    )
    assert isinstance(orig_assess, RunMinted), orig_assess
    assert orig_assess.run.recipe.inputs[0].content == folded_digest

    for idx, exp in enumerate((multi_expected, None)):
        rep_assess = _replay_fn(
            orig_assess,
            port=MEMORY_PORT,
            spec=spec_multi,
            definition=defn_multi,
            code_roots=(code_multi,),
            held_inputs=multi_held,
            expected_inputs=exp,
            entrypoint="code/workflow/Snakefile",
            targets=("outputs/result.txt",),
            declared_outputs=("outputs/result.txt",),
            observer="observer-1",
            started_at="2026-08-12T00:00:00Z",
            host_realization="host-a",
            scratch_base=tmp_path / f"scratch-assess-rep-{idx}",
            cores=1,
        )
        assert isinstance(rep_assess, RunMinted), rep_assess
        assert rep_assess.run.recipe.identity() == orig_assess.run.recipe.identity()
        assert rep_assess.run.result == orig_assess.run.result

    # 2. Multi-resource production run + replay (with expected_inputs and with expected_inputs=None)
    orig_prod = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=folded_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=defn_multi,
        code_roots=(code_multi,),
        held_inputs=multi_held,
        expected_inputs=multi_expected,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch-prod-orig",
        cores=1,
    )
    assert isinstance(orig_prod, RunMinted), orig_prod

    for idx, exp in enumerate((multi_expected, None)):
        rep_prod = _replay_fn(
            orig_prod,
            port=MEMORY_PORT,
            spec=None,
            definition=defn_multi,
            code_roots=(code_multi,),
            held_inputs=multi_held,
            expected_inputs=exp,
            entrypoint="code/workflow/Snakefile",
            targets=("outputs/result.txt",),
            declared_outputs=("outputs/result.txt",),
            observer="observer-1",
            started_at="2026-08-12T00:00:00Z",
            host_realization="host-a",
            scratch_base=tmp_path / f"scratch-prod-rep-{idx}",
            cores=1,
        )
        assert isinstance(rep_prod, RunMinted), rep_prod
        assert rep_prod.run.recipe.identity() == orig_prod.run.recipe.identity()
        assert rep_prod.run.result == orig_prod.run.result

    # 3. 1-resource nested member mapping replay (assessment & production)
    code_single, _ = stage(tmp_path / "code-single", snakefile=SNAKEFILE_REPLAY_NESTED_SINGLE)
    defn_single = definition(snakefile=SNAKEFILE_REPLAY_NESTED_SINGLE, family_streams={})
    single_held = {DATA_ADDRESS: {"tables/clinical.tsv": clin_path}}
    single_expected = {DATA_ADDRESS: {"tables/clinical.tsv": clin_digest}}

    orig_nested_prod = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=clin_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=defn_single,
        code_roots=(code_single,),
        held_inputs=single_held,
        expected_inputs=single_expected,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch-nested-orig",
        cores=1,
    )
    assert isinstance(orig_nested_prod, RunMinted), orig_nested_prod
    assert orig_nested_prod.run.recipe.inputs[0].content == clin_digest

    for idx, exp in enumerate((single_expected, None)):
        rep_nested = _replay_fn(
            orig_nested_prod,
            port=MEMORY_PORT,
            spec=None,
            definition=defn_single,
            code_roots=(code_single,),
            held_inputs=single_held,
            expected_inputs=exp,
            entrypoint="code/workflow/Snakefile",
            targets=("outputs/result.txt",),
            declared_outputs=("outputs/result.txt",),
            observer="observer-1",
            started_at="2026-08-12T00:00:00Z",
            host_realization="host-a",
            scratch_base=tmp_path / f"scratch-nested-rep-{idx}",
            cores=1,
        )
        assert isinstance(rep_nested, RunMinted), rep_nested
        assert rep_nested.run.recipe.identity() == orig_nested_prod.run.recipe.identity()
        assert rep_nested.run.result == orig_nested_prod.run.result
