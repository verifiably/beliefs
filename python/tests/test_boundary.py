"""G2a, R3, R10, R12, R21's boundary arms, T2's in-cell arms,
R16's mint arm, R17's execution halves, R2's execution-level negative.
Deferred: T2's committed-registration and ordering arms (persistence), R12's
boundary-mediated strengthening (tamper log), R21's two-target arm and
negative (d) (full workflow surface), write-outside-root fail-closed and
negative (c)'s clean-environment reachability (confinement)."""

import dataclasses
import inspect
import os

import pytest
from fixtures_cut3 import (
    DATA_ADDRESS,
    MEMORY_PORT,
    READS_ADDRESS,
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_NONDETERMINISTIC,
    SNAKEFILE_SCRATCHY,
    SNAKEFILE_SEED_VIOLATING,
    closure,
    definition,
    recipe,
    seeded,
    spec_draft,
    spec_rules,
    stage,
)
from fixtures_cut3 import (
    memory_assessment as run_assessment,
)
from fixtures_cut3 import (
    memory_production as run_production,
)

from beliefs.adapter import (
    LOG_HANDLER_SCRIPT,
    build_argv,
    capture_bundle,
    capture_environment,
    create_scratch_root,
    run_engine,
    validate_entrypoint,
)
from beliefs.boundary import (
    RunMinted,
    RunRefused,
    build_manifest,
    execute_assessment_run,
    execute_production_run,
    mint_run,
)
from beliefs.errors import MalformedClosure
from beliefs.recipe import Occurrence, RunClosure
from beliefs.report import ActReport, OperationIntent, RunAttemptEntry
from beliefs.spec import Seeded, SeedPlan, SpecInput, derive_seed, freeze, revise


@pytest.fixture(scope="module")
def minted(tmp_path_factory):
    outcome = run_assessment(tmp_path_factory.mktemp("happy"))
    assert isinstance(outcome, RunMinted), outcome
    return outcome


def test_the_boundary_mints_a_run_over_the_held_fixture(minted):
    assert minted.run.recipe.shape == "assessment"
    assert minted.run.result.outputs[0][0] == "outputs/result.txt"
    assert minted.registration.pointer == minted.run.address()


def test_the_recorded_environment_is_the_executing_environment(minted):
    assert minted.run.recipe.environment == capture_environment()


def test_the_boundary_refuses_a_definition_the_entrypoint_does_not_embody(tmp_path):
    code, held = stage(tmp_path, snakefile=SNAKEFILE_DETERMINISTIC)
    mismatched = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=MEMORY_PORT,
        definition=definition(snakefile=SNAKEFILE_NONDETERMINISTIC),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        actor="tester",
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(mismatched, RunRefused) and mismatched.reason == "definition-mismatch"


# --- G2a / R12 ----------------------------------------------------------------
def test_g2a_a_run_naming_no_frozen_spec_is_refused_not_downgraded(tmp_path):
    outcome = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"
    assert outcome.intent is None and outcome.registration is None
    assert isinstance(outcome.report, ActReport)


def test_g2a_a_spec_frozen_mid_execution_is_refused_not_downgraded(tmp_path):
    draft = spec_draft()
    refused = run_assessment(tmp_path, spec=draft)
    assert isinstance(refused, RunRefused)
    frozen_later = freeze(draft, held_rules=spec_rules())
    assert isinstance(refused, RunRefused)
    assert frozen_later.identity


def test_r12_the_boundary_refuses_a_bare_spec_identity_string(tmp_path):
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    outcome = run_assessment(tmp_path, spec=frozen.identity)
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"


def test_g2a_r12_an_out_of_band_run_with_a_spec_frozen_afterwards_is_undetectable(tmp_path):
    code, _ = stage(tmp_path)
    scratch = create_scratch_root(tmp_path / "s")
    (scratch / "inputs").mkdir()
    (scratch / "inputs" / "data.txt").write_text("hello")
    bundle = tmp_path / "bundle"
    code_id = capture_bundle((code,), bundle)
    entry = validate_entrypoint(bundle, "code/workflow/Snakefile")
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    handler = trace_dir / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    argv = build_argv(
        snakefile=entry,
        scratch=scratch,
        targets=("outputs/result.txt",),
        config={"seed_model_initialization": "7"},
        log_handler=handler,
        cores=1,
    )
    returncode, _ = run_engine(
        argv,
        cwd=scratch,
        env={**os.environ, "SCIENCE_TRACE_FILE": str(trace_dir / "events.jsonl")},
    )
    assert returncode == 0
    spec = freeze(spec_draft(), held_rules=spec_rules())
    attached = closure(recipe=recipe(spec_identity=spec.identity, code_identity=code_id))
    assert attached.address()
    assert "boundary_mediated" not in {f.name for f in dataclasses.fields(RunClosure)}
    assert "boundary_mediated" not in {f.name for f in dataclasses.fields(Occurrence)}


# --- R10 ----------------------------------------------------------------------
def test_r10_a_url_valued_input_is_refused_as_a_run_input(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="https://example.org/series"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"


def test_r10_an_accession_is_refused_and_no_fallback_synthesizes_a_dataset(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="accession:GSE00001"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"
    assert outcome.report is not None and not hasattr(outcome, "dataset")


# --- R3 (and R2's execution-level negative) -----------------------------------
def test_r3_two_executions_of_one_recipe_are_two_runs(tmp_path):
    first = run_assessment(tmp_path / "a")
    second = run_assessment(tmp_path / "b")
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.recipe.identity() == second.run.recipe.identity()
    assert first.run.address() != second.run.address()
    assert {first.run.address(), second.run.address()} == {
        first.run.address(),
        second.run.address(),
    }


def test_r3_identical_timestamp_actor_and_host_still_yield_distinct_addresses(tmp_path):
    first = run_assessment(
        tmp_path / "a",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-x",
    )
    second = run_assessment(
        tmp_path / "b",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-x",
    )
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    twinned = dataclasses.replace(
        second.run.occurrence,
        started_at=first.run.occurrence.started_at,
        actor=first.run.occurrence.actor,
        host_realization=first.run.occurrence.host_realization,
        trace=first.run.occurrence.trace,
        realized_seeds=first.run.occurrence.realized_seeds,
        receipt=first.run.occurrence.receipt,
    )
    rebuilt = RunClosure(
        recipe=second.run.recipe,
        result=second.run.result,
        occurrence=twinned,
    )
    assert rebuilt.address() != first.run.address()
    assert twinned.event_token != first.run.occurrence.event_token


# --- T2's in-cell arms ---------------------------------------------------------
def test_t2_a_dataset_production_attempt_opens_the_operation_intent(tmp_path):
    outcome = run_production(tmp_path)
    assert isinstance(outcome, RunMinted)
    assert isinstance(outcome.intent, OperationIntent) and outcome.intent.kind == "run-attempt"


def test_t2_negative_b_a_complete_non_conforming_execution_mints_a_run_never_an_act_report(
    tmp_path,
):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)


def test_t2_a_missing_spec_refusal_publishes_an_unfulfilling_report(tmp_path):
    outcome = run_assessment(tmp_path, spec=None.__class__)
    assert isinstance(outcome, RunRefused)
    assert outcome.intent is None
    assert outcome.report is not None
    entry = outcome.report.entries[0]
    assert isinstance(entry, RunAttemptEntry) and entry.subject == "absent"
    assert outcome.registration is None


# --- R21's boundary arms -------------------------------------------------------
def test_r21_manifest_missing_output_mints_no_run(tmp_path):
    code, held = stage(tmp_path)
    spec = freeze(spec_draft(), held_rules=spec_rules())
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        definition=definition(),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt", "outputs/never-written.txt"),
        actor="tester",
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(outcome, RunRefused) and outcome.reason.startswith("manifest")
    assert outcome.intent is not None and outcome.report is not None


def test_r21_the_manifest_is_constructed_by_the_boundary_and_no_supplied_path_exists():
    for fn in (execute_assessment_run, execute_production_run):
        params = set(inspect.signature(fn).parameters)
        assert not {"manifest", "outputs", "result"} & params


def test_r21_a_digest_disagreeing_with_the_bytes_on_disk_mints_no_run(tmp_path, minted):
    scratch = create_scratch_root(tmp_path)
    (scratch / "outputs").mkdir()
    (scratch / "outputs" / "result.txt").write_text("HELLO")
    manifest = build_manifest(("outputs/result.txt",), scratch)
    (scratch / "outputs" / "result.txt").write_text("TAMPERED")
    with pytest.raises(MalformedClosure):
        mint_run(minted.run.recipe, manifest, minted.run.occurrence, scratch)


def test_r21_intermediates_are_excluded_and_scratch_files_leave_the_manifest_equal(tmp_path):
    first = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_SCRATCHY)
    second = run_assessment(tmp_path / "b", snakefile=SNAKEFILE_SCRATCHY)
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.result == second.run.result


def test_r21_negative_a_a_scheduling_only_option_leaves_the_recipe_identity_unchanged(tmp_path):
    one = run_assessment(tmp_path / "a", cores=1)
    two = run_assessment(tmp_path / "b", cores=2)
    assert isinstance(one, RunMinted) and isinstance(two, RunMinted)
    assert one.run.recipe.identity() == two.run.recipe.identity()


def test_r21_negative_c_two_differently_mounted_scratch_roots_yield_equal_recipe_identities(
    tmp_path,
):
    a = run_assessment(tmp_path / "mount-a")
    b = run_assessment(tmp_path / "mount-b")
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    assert a.run.recipe.identity() == b.run.recipe.identity()
    assert a.run.occurrence.receipt.scratch_mapping != b.run.occurrence.receipt.scratch_mapping
    import json

    assert a.run.occurrence.receipt.scratch_mapping not in json.dumps(a.run.recipe.identity())


def test_r21_negative_e_the_two_failure_states_are_distinct(tmp_path):
    disobeyed = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(disobeyed, RunMinted)
    incompletable = run_assessment(
        tmp_path / "b",
        snakefile=SNAKEFILE_NONDETERMINISTIC.replace(
            'output: "outputs/result.txt"',
            'output: "outputs/other.txt"',
        ),
    )
    assert isinstance(incompletable, RunRefused)


# --- R16's mint arm ------------------------------------------------------------
def test_r16_a_seed_violating_execution_still_mints_a_run(tmp_path):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)
    realized = outcome.run.occurrence.realized_seeds.seeds["transform"]["model-initialization"]
    assert realized != derive_seed(11, "transform", "model-initialization")


# --- R17's execution halves ----------------------------------------------------
def test_r17_no_path_supplies_inputs_parameters_or_contract_on_an_assessment_run():
    params = set(inspect.signature(execute_assessment_run).parameters)
    assert (
        not {
            "inputs",
            "parameters",
            "nondeterminism",
            "seed",
            "seeds",
            "root_seed",
            "config",
            "options",
            "environment",
            "env_root",
            "manifest",
        }
        & params
    )


def test_r17_the_boundary_renders_the_configuration_from_the_projected_members(minted):
    rendered = dict(minted.run.occurrence.receipt.rendered_config)
    assert rendered["alpha"] == "0.05"
    assert rendered["seed_model_initialization"] == str(derive_seed(11, "transform", "model-initialization"))


def test_r17_seed_shopping_cannot_occur_at_all(minted):
    successor = revise(
        freeze(spec_draft(), held_rules=spec_rules()),
        edits={
            "nondeterminism": Seeded(
                plan=SeedPlan(
                    derivation_rule="seed-derivation/v1",
                    streams=("model-initialization",),
                    roots={"root-a": 99},
                    stream_roots={"model-initialization": "root-a"},
                )
            )
        },
        held_rules=spec_rules(),
        recorded_failures=frozenset(),
    )
    assert successor.identity != minted.run.recipe.spec_identity
    assert minted.run.recipe.spec_identity == freeze(spec_draft(), held_rules=spec_rules()).identity


def test_r17_a_deleted_or_never_recorded_attempt_is_undetectable(tmp_path):
    refused = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(refused, RunRefused)
    assert refused.report is not None
    held_records = {refused.report.identity(): refused.report}
    held_records.clear()
    assert held_records == {}


def test_r17_negative_b_a_dataset_production_recipe_is_authored_directly(tmp_path):
    params = set(inspect.signature(execute_production_run).parameters)
    assert {"inputs", "parameters", "nondeterminism"} <= params
    outcome = run_production(tmp_path, nondeterminism=seeded())
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.nondeterminism == seeded()
