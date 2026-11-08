"""The boundary checks and the in-cell checks,
the mint check, the execution halves and the execution-level negative.
Deferred: the committed-registration and ordering checks (persistence), the
boundary-mediated strengthening (tamper log), the two-target check and
negative (d) (full workflow surface), write-outside-root fail-closed and
negative (c)'s clean-environment reachability (confinement)."""

import dataclasses
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from authority import FULL, narrowed
from config_probe import run_config_probe
from fixtures_cut3 import (
    DATA_ADDRESS,
    MEMORY_PORT,
    READS_ADDRESS,
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_NONDETERMINISTIC,
    SNAKEFILE_PRODUCTION,
    SNAKEFILE_SCRATCHY,
    SNAKEFILE_SEED_VIOLATING,
    MemoryPort,
    closure,
    definition,
    recipe,
    seed_plan,
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

from beliefs import boundary
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
    _render_config,
    build_manifest,
    check_checkpoint_declaration,
    execute_assessment_run,
    execute_production_run,
    mint_run,
    resolve_targets,
)
from beliefs.errors import (
    CheckpointDeclarationUnmet,
    MalformedClosure,
    MalformedRecord,
    TargetAmbiguous,
    TargetUnresolvable,
)
from beliefs.identity import v1
from beliefs.recipe import MINIMAL_POLICY, Occurrence, PlannedJob, RunClosure, WorkflowDefinitionSnapshot, job_key
from beliefs.report import (
    ActReport,
    Consolidated,
    Moved,
    OperationIntent,
    RecordMutationEntry,
    RunAttemptEntry,
    RunRefusal,
)
from beliefs.spec import Deterministic, Seeded, SeedPlan, SpecInput, derive_seed, freeze, revise

CHECKPOINT_DIGEST = "sha256:" + "22" * 32
TARGET_ALL = PlannedJob(job_key("all", ()), "all", (), False)
TARGET_FIT_A = PlannedJob(
    job_key("fit", (("s", "a"),)),
    "fit",
    ("outputs/a.done",),
    False,
)
TARGET_FIT_B = PlannedJob(
    job_key("fit", (("s", "b"),)),
    "fit",
    ("outputs/b.done",),
    False,
)


class _NarrowPort(MemoryPort):
    def __init__(self, authority):
        self.authority = authority
        self.appended = []

    def append_intent(self, payload: bytes) -> str:
        self.appended.append(payload)
        return super().append_intent(payload)

    def execute(self, plan) -> None:
        raise AssertionError("a refused run must not write")

    def execute_fulfilling(self, plan, fulfills: str) -> str:
        raise AssertionError("a refused run must not write")


def _assessment(tmp_path, port, **overrides):
    code, held = stage(tmp_path)
    kwargs: dict[str, Any] = {
        "spec": freeze(spec_draft(), held_rules=spec_rules()),
        "port": port,
        "boundary_policy": MINIMAL_POLICY,
        "definition": definition(),
        "code_roots": (code,),
        "held_inputs": {DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        "entrypoint": "code/workflow/Snakefile",
        "targets": ("outputs/result.txt",),
        "declared_outputs": ("outputs/result.txt",),
        "observer": "observer-1",
        "started_at": "2026-08-12T00:00:00Z",
        "host_realization": "host-a",
        "scratch_base": tmp_path / "scratch",
    }
    kwargs.update(overrides)
    return execute_assessment_run(**kwargs)


def test_a_permit_lacking_run_refuses_with_no_intent_and_no_report(tmp_path):
    port = _NarrowPort(narrowed(kinds=("run", "act-report"), families=("corpus-write",)))
    outcome = _assessment(tmp_path, port)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None and outcome.registration is None
    assert "family run" in outcome.detail
    assert port.appended == []


def test_a_permit_lacking_act_report_refuses_before_the_intent(tmp_path):
    port = _NarrowPort(narrowed(kinds=("run",), families=("run",)))
    outcome = _assessment(tmp_path, port)
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert "kind act-report" in outcome.detail
    assert port.appended == []


def test_a_production_run_under_a_permit_lacking_run_refuses_with_no_intent(tmp_path):
    from fixtures_cut3 import run_production as production_run

    port = _NarrowPort(narrowed(kinds=("run", "act-report", "dataset"), families=("corpus-write",)))
    outcome = production_run(tmp_path, port=port)
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None and outcome.registration is None
    assert port.appended == []


def test_a_non_permit_refusal_after_the_check_still_mints_its_report(tmp_path):
    class Port(MemoryPort):
        authority = FULL

        def __init__(self):
            self.executed = []

        def execute(self, plan) -> None:
            self.executed.append(plan)

    port = Port()
    outcome = _assessment(tmp_path, port, spec="not-a-frozen-spec")
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"
    assert outcome.report is not None and len(port.executed) == 1


def test_the_run_intent_carries_the_ports_actor(tmp_path):
    class Port(MemoryPort):
        authority = narrowed(kinds=("run", "act-report"), families=("run",), actor="port-actor")

        def __init__(self):
            self.appended = []

        def append_intent(self, payload: bytes) -> str:
            self.appended.append(payload)
            return super().append_intent(payload)

    port = Port()
    _assessment(tmp_path, port)
    payload = v1.decode(port.appended[0])
    assert isinstance(payload, dict) and payload["actor"] == "port-actor"


def test_the_run_entry_points_take_no_actor(tmp_path):
    with pytest.raises(TypeError):
        _assessment(tmp_path, MemoryPort(), actor="tester")


@pytest.mark.parametrize(
    ("kind", "outcome"),
    [
        ("move", Moved("corpus-a", "corpus-b", "dataset:d1")),
        (
            "consolidate",
            Consolidated("corpus-a", "dataset:d1", "corpus-b", "dataset:d2", ("u2",), "duplicate"),
        ),
    ],
)
def test_the_relocation_mint_authors_one_record_mutation(kind, outcome):
    intent = OperationIntent(kind, "t" * 32, "actor")

    minted = boundary._mint_relocation_report(
        intent,
        subject="dataset:d1",
        corpus="corpus-a",
        observer="o",
        instrument="i",
        opened_at="2026-09-03T10:00:00Z",
        closed_at="2026-09-03T10:00:01Z",
        outcome=outcome,
    )

    assert minted.operation == kind
    assert minted.event_token == intent.event_token
    assert minted.actor == intent.actor
    assert minted.entries == (RecordMutationEntry("dataset:d1", "corpus-a", outcome),)


def test_the_relocation_mint_refuses_a_foreign_intent_kind():
    with pytest.raises(MalformedRecord):
        boundary._mint_relocation_report(
            OperationIntent("import", "t" * 32, "actor"),
            subject="dataset:d1",
            corpus="corpus-a",
            observer="o",
            instrument="i",
            opened_at="2026-09-03T10:00:00Z",
            closed_at="2026-09-03T10:00:01Z",
            outcome=Moved("corpus-a", "corpus-b", "dataset:d1"),
        )


def test_a_rule_target_resolves_to_the_job_with_no_wildcards() -> None:
    assert resolve_targets(("all",), (TARGET_ALL, TARGET_FIT_A)) == (TARGET_ALL.job_key,)


def test_a_file_target_resolves_to_the_job_that_produces_it() -> None:
    assert resolve_targets(
        ("outputs/a.done",),
        (TARGET_ALL, TARGET_FIT_A, TARGET_FIT_B),
    ) == (TARGET_FIT_A.job_key,)


def test_two_targets_resolve_in_request_order() -> None:
    assert resolve_targets(
        ("outputs/b.done", "outputs/a.done"),
        (TARGET_FIT_A, TARGET_FIT_B),
    ) == (TARGET_FIT_B.job_key, TARGET_FIT_A.job_key)


def test_a_target_the_plan_does_not_name_is_unresolvable() -> None:
    with pytest.raises(TargetUnresolvable):
        resolve_targets(("outputs/zzz.done",), (TARGET_ALL, TARGET_FIT_A))


def test_a_target_matching_two_planned_jobs_is_ambiguous() -> None:
    twin = PlannedJob(
        job_key("copy", ()),
        "copy",
        ("outputs/a.done",),
        False,
    )
    with pytest.raises(TargetAmbiguous):
        resolve_targets(("outputs/a.done",), (TARGET_FIT_A, twin))


def _checkpoint_snapshot(families, expanded):
    return WorkflowDefinitionSnapshot(
        snakefile_digest=CHECKPOINT_DIGEST,
        family_streams=families,
        checkpoint_expanded_families=expanded,
    )


def _planned_checkpoint(family, is_checkpoint=False):
    return PlannedJob(
        job_key=job_key(family, ()),
        family=family,
        outputs=(),
        is_checkpoint=is_checkpoint,
    )


def test_a_checkpoint_declaration_with_no_checkpoint_in_the_plan_is_refused() -> None:
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(
            _checkpoint_snapshot({"fit": ()}, ("fit",)),
            (_planned_checkpoint("fit"),),
        )


def test_a_checkpoint_declaration_for_an_absent_family_is_refused() -> None:
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(
            _checkpoint_snapshot({"fit": ()}, ("absent",)),
            (_planned_checkpoint("split", is_checkpoint=True),),
        )


def test_an_empty_checkpoint_declaration_permits_a_planned_checkpoint() -> None:
    check_checkpoint_declaration(
        _checkpoint_snapshot({"split": ()}, ()),
        (_planned_checkpoint("split", is_checkpoint=True),),
    )


@pytest.mark.parametrize("reserved", ("seed_roots", "seed_derivation_rule"))
@pytest.mark.parametrize("contract", (seeded(), Deterministic()))
def test_seed_config_members_cannot_be_shadowed_by_recipe_parameters(reserved, contract) -> None:
    value = recipe(parameters={reserved: "caller supplied"}, nondeterminism=contract)
    with pytest.raises(MalformedClosure):
        _render_config(value, value.workflow_definition)


def test_an_unsupported_seed_derivation_rule_is_refused_before_launch() -> None:
    value = recipe(
        nondeterminism=Seeded(
            plan=SeedPlan(
                derivation_rule="seed-derivation/future",
                streams=("model-initialization",),
                roots={"root-a": 11},
                stream_roots={"model-initialization": "root-a"},
            )
        )
    )
    with pytest.raises(MalformedClosure):
        _render_config(value, value.workflow_definition)


def test_a_checkpoint_declaration_with_a_planned_checkpoint_is_permitted() -> None:
    check_checkpoint_declaration(
        _checkpoint_snapshot({"split": (), "fit": ()}, ("fit",)),
        (
            _planned_checkpoint("split", is_checkpoint=True),
            _planned_checkpoint("fit"),
        ),
    )


def test_the_roots_are_rendered_as_one_mapping_never_per_stream_keys() -> None:
    config = _render_config(recipe(nondeterminism=seeded()), definition().snapshot())
    assert json.loads(config["seed_roots"]) == {"model-initialization": "11"}
    assert config["seed_derivation_rule"] == "seed-derivation/v1"
    assert not any(key.startswith("seed_model") for key in config)


def test_two_streams_differing_only_in_punctuation_do_not_collide() -> None:
    plan = seed_plan(
        streams=("a-b", "a_b"),
        roots={"r": 11},
        stream_roots={"a-b": "r", "a_b": "r"},
    )
    snapshot = definition(family_streams={"transform": ("a-b", "a_b")}).snapshot()
    config = _render_config(recipe(nondeterminism=Seeded(plan=plan)), snapshot)
    assert json.loads(config["seed_roots"]) == {"a-b": "11", "a_b": "11"}


def test_a_deterministic_recipe_renders_no_seed_material() -> None:
    config = _render_config(
        recipe(nondeterminism=Deterministic()),
        definition(family_streams={}).snapshot(),
    )
    assert "seed_roots" not in config and "seed_derivation_rule" not in config


def test_the_engine_coerces_a_structured_config_value_to_strings(tmp_path) -> None:
    observed = run_config_probe(tmp_path, {"seed_roots": '{"a": 11}', "plain": "11"})
    assert observed["seed_roots"] == ["dict", {"a": "11"}]
    assert observed["plain"] == ["int", 11]


def test_the_planning_launch_writes_nothing_into_the_execution_scratch(tmp_path) -> None:
    outcome = run_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(outcome, RunMinted)
    scratch = Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    planning = Path(outcome.run.occurrence.receipt.planning.scratch_mapping)
    assert scratch.exists() and planning != scratch and not planning.exists()


def test_the_plan_is_carried_by_the_occurrence(tmp_path) -> None:
    outcome = run_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(outcome, RunMinted)
    assert {job.family for job in outcome.run.occurrence.planned} == {"transform"}


def test_an_unknown_target_is_a_planning_refusal_not_a_resolution_one(tmp_path) -> None:
    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_PRODUCTION,
        targets=("outputs/zzz.txt",),
    )
    assert isinstance(outcome, RunRefused)
    assert "plan" in outcome.reason and "target" not in outcome.reason


def test_a_definition_disagreement_refuses_before_a_planning_effect(tmp_path) -> None:
    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_PRODUCTION,
        definition_override=definition(
            snakefile=SNAKEFILE_PRODUCTION,
            family_streams={"transform": ("model-initialization",)},
        ),
    )
    assert isinstance(outcome, RunRefused)
    assert "definition" in outcome.reason
    assert not list((tmp_path / "scratch").glob("planning-*"))


@pytest.fixture(scope="module")
def minted(tmp_path_factory):
    outcome = run_assessment(tmp_path_factory.mktemp("happy"))
    assert isinstance(outcome, RunMinted), outcome
    return outcome


def test_the_boundary_mints_a_run_over_the_held_fixture(minted, request):
    mark = request.node.get_closest_marker("xdist_group")
    assert mark is not None and mark.args == ("tests/test_boundary.py",)
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
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_NONDETERMINISTIC),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(mismatched, RunRefused) and mismatched.reason == "definition-mismatch"


def test_a_run_naming_no_frozen_spec_is_refused_not_downgraded(tmp_path):
    outcome = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"
    assert outcome.intent is None and outcome.registration is None
    assert isinstance(outcome.report, ActReport)


def test_a_spec_frozen_mid_execution_is_refused_not_downgraded(tmp_path):
    draft = spec_draft()
    refused = run_assessment(tmp_path, spec=draft)
    assert isinstance(refused, RunRefused)
    frozen_later = freeze(draft, held_rules=spec_rules())
    assert isinstance(refused, RunRefused)
    assert frozen_later.identity


def test_the_boundary_refuses_a_bare_spec_identity_string(tmp_path):
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    outcome = run_assessment(tmp_path, spec=frozen.identity)
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"


def test_an_out_of_band_run_with_a_spec_frozen_afterwards_is_undetectable(tmp_path):
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
        interpreter=sys.executable,
        snakefile=str(entry),
        directory=str(scratch),
        targets=("outputs/result.txt",),
        config={
            "seed_derivation_rule": "seed-derivation/v1",
            "seed_roots": '{"model-initialization":"7"}',
        },
        log_handler=str(handler),
        cores=1,
        in_process_jobs=False,
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


def test_url_valued_input_is_refused_as_a_run_input(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="https://example.org/series"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"


def test_an_accession_is_refused_and_no_fallback_synthesizes_a_dataset(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="accession:GSE00001"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"
    assert outcome.report is not None and not hasattr(outcome, "dataset")


# --- the execution-level negative -----------------------------------
def test_two_executions_of_one_recipe_are_two_runs(tmp_path):
    first = run_assessment(tmp_path / "a")
    second = run_assessment(tmp_path / "b")
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.recipe.identity() == second.run.recipe.identity()
    assert first.run.address() != second.run.address()
    assert {first.run.address(), second.run.address()} == {
        first.run.address(),
        second.run.address(),
    }


def test_identical_timestamp_actor_and_host_still_yield_distinct_addresses(tmp_path):
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


# --- the in-cell checks ---------------------------------------------------------
def test_dataset_production_attempt_opens_the_operation_intent(tmp_path):
    outcome = run_production(tmp_path)
    assert isinstance(outcome, RunMinted)
    assert isinstance(outcome.intent, OperationIntent) and outcome.intent.kind == "run-attempt"


def test_a_complete_non_conforming_execution_mints_a_run_never_an_act_report(
    tmp_path,
):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)


def test_missing_spec_refusal_publishes_an_unfulfilling_report(tmp_path):
    outcome = run_assessment(tmp_path, spec=None.__class__)
    assert isinstance(outcome, RunRefused)
    assert outcome.intent is None
    assert outcome.report is not None
    entry = outcome.report.entries[0]
    assert isinstance(entry, RunAttemptEntry) and entry.subject == "absent"
    assert outcome.registration is None


# --- the boundary checks -------------------------------------------------------
def test_manifest_missing_output_mints_no_run(tmp_path):
    code, held = stage(tmp_path)
    spec = freeze(spec_draft(), held_rules=spec_rules())
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt", "outputs/never-written.txt"),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(outcome, RunRefused) and outcome.reason.startswith("manifest")
    assert outcome.intent is not None and outcome.report is not None


def test_the_manifest_is_constructed_by_the_boundary_and_no_supplied_path_exists():
    for fn in (execute_assessment_run, execute_production_run):
        params = set(inspect.signature(fn).parameters)
        assert not {"manifest", "outputs", "result"} & params


def test_a_digest_disagreeing_with_the_bytes_on_disk_mints_no_run(tmp_path, minted):
    scratch = create_scratch_root(tmp_path)
    (scratch / "outputs").mkdir()
    (scratch / "outputs" / "result.txt").write_text("HELLO")
    manifest = build_manifest(("outputs/result.txt",), scratch)
    (scratch / "outputs" / "result.txt").write_text("TAMPERED")
    with pytest.raises(MalformedClosure):
        mint_run(minted.run.recipe, manifest, minted.run.occurrence, scratch)


def test_intermediates_are_excluded_and_scratch_files_leave_the_manifest_equal(tmp_path):
    first = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_SCRATCHY)
    second = run_assessment(tmp_path / "b", snakefile=SNAKEFILE_SCRATCHY)
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.result == second.run.result


def test_a_scheduling_only_option_leaves_the_recipe_identity_unchanged(tmp_path):
    one = run_assessment(tmp_path / "a", cores=1)
    two = run_assessment(tmp_path / "b", cores=2)
    assert isinstance(one, RunMinted) and isinstance(two, RunMinted)
    assert one.run.recipe.identity() == two.run.recipe.identity()


def test_two_differently_mounted_scratch_roots_yield_equal_recipe_identities(
    tmp_path,
):
    a = run_assessment(tmp_path / "mount-a")
    b = run_assessment(tmp_path / "mount-b")
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    assert a.run.recipe.identity() == b.run.recipe.identity()
    assert a.run.occurrence.receipt.execution.scratch_mapping != b.run.occurrence.receipt.execution.scratch_mapping
    import json

    assert a.run.occurrence.receipt.execution.scratch_mapping not in json.dumps(a.run.recipe.identity())


def test_the_two_failure_states_are_distinct(tmp_path):
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


# --- the mint check ------------------------------------------------------------
def test_a_seed_violating_execution_still_mints_a_run(tmp_path):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)
    key = job_key("transform", ())
    realized = outcome.run.occurrence.realized_seeds.seeds[key]["model-initialization"]
    assert realized != derive_seed(11, key, "model-initialization")


# --- the execution halves ----------------------------------------------------
def test_no_path_supplies_inputs_parameters_or_contract_on_an_assessment_run():
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


def test_the_boundary_renders_the_configuration_from_the_projected_members(minted):
    rendered = dict(minted.run.occurrence.receipt.execution.rendered_config)
    assert rendered["alpha"] == "0.05"
    assert json.loads(rendered["seed_roots"]) == {"model-initialization": "11"}
    assert rendered["seed_derivation_rule"] == "seed-derivation/v1"


def test_seed_shopping_cannot_occur_at_all(minted):
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


def test_a_deleted_or_never_recorded_attempt_is_undetectable(tmp_path):
    refused = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(refused, RunRefused)
    assert refused.report is not None
    held_records = {refused.report.identity(): refused.report}
    held_records.clear()
    assert held_records == {}


def test_a_dataset_production_recipe_is_authored_directly(tmp_path):
    params = set(inspect.signature(execute_production_run).parameters)
    assert {"inputs", "parameters", "nondeterminism"} <= params
    outcome = run_production(tmp_path, nondeterminism=seeded())
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.nondeterminism == seeded()


# --- the policy parameter, pre-intent refusals, stable reasons ---------
import dataclasses as _dc

from fixtures_cut3 import replay_of as _replay_of

import beliefs.boundary as _boundary
from beliefs.errors import ClosureUnsupported
from beliefs.recipe import CONFINED_POLICY, RecipeInput
from beliefs.replay import replay as _replay
from beliefs.report import CLOSED, completion


def test_the_boundary_policy_has_no_default_and_no_ambient_constant():
    for fn in (execute_assessment_run, execute_production_run):
        parameter = inspect.signature(fn).parameters["boundary_policy"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert not hasattr(_boundary, "_POLICY")


def test_an_unsupported_policy_refuses_before_intent(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=_dc.replace(CONFINED_POLICY, scope_rule="scope-derivation/v2"))
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "boundary-policy-unsupported"
    assert outcome.intent is None and outcome.registration is None and outcome.report is not None
    assert "scope-derivation/v2" in outcome.detail


def test_a_minimal_run_carries_a_composed_unconfined_receipt(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=MINIMAL_POLICY)
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    assert not receipt.confined and receipt.execution.capabilities == () and receipt.execution.instance is None
    assert outcome.run.recipe.boundary_policy == MINIMAL_POLICY


def test_replay_carries_the_originals_policy_and_takes_none_of_its_own(tmp_path):
    assert "boundary_policy" not in inspect.signature(_replay).parameters
    original = run_assessment(tmp_path / "a")
    replayed = _replay_of(original, tmp_path / "b", port=MEMORY_PORT)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    assert replayed.run.recipe.boundary_policy == original.run.recipe.boundary_policy == MINIMAL_POLICY


def test_a_confinement_refusal_keeps_its_stable_reason_and_its_detail(tmp_path, monkeypatch):
    def unsupported():
        raise ClosureUnsupported("synthetic: SONAME collision")

    monkeypatch.setattr(_boundary, "capture_closure", unsupported)
    outcome = run_assessment(tmp_path)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "closure-unsupported"
    assert outcome.detail == "synthetic: SONAME collision"
    assert outcome.intent is not None  # post-intent: the intent was fulfilled by a refusal
    assert outcome.report is not None
    report_outcome = outcome.report.entries[0].outcome
    assert isinstance(report_outcome, RunRefusal) and report_outcome.missing_member == "closure-unsupported"


# --- staged input digest enforcement (beliefs-246cde) -------------------


def _forbid_engines(monkeypatch):
    def _never_engine(*args, **kwargs):
        raise AssertionError("engine must not launch when staged input digest check refuses")

    monkeypatch.setattr(_boundary, "run_engine", _never_engine)
    monkeypatch.setattr(_boundary, "launch_confined", _never_engine)


def test_assessment_run_refuses_mismatched_expected_input_before_planning_or_execution(tmp_path, monkeypatch):
    code, held = stage(tmp_path / "mismatched")
    spec = freeze(spec_draft(), held_rules=spec_rules())
    supplied = {DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"}

    _forbid_engines(monkeypatch)
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs=supplied,
        expected_inputs={DATA_ADDRESS: "sha256:" + "0" * 64},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "mismatched" / "scratch",
        cores=1,
    )
    assert isinstance(outcome, RunRefused)
    assert "does not match expected" in outcome.reason
    assert outcome.intent is not None
    assert outcome.report is not None
    assert outcome.registration is not None
    assert completion(outcome.intent, (outcome.registration,), {outcome.report.identity(): outcome.report}) == CLOSED

    monkeypatch.undo()
    code_ok, held_ok = stage(tmp_path / "matching")
    matching = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code_ok,),
        held_inputs={DATA_ADDRESS: held_ok / "data.txt", READS_ADDRESS: held_ok / "palette.txt"},
        expected_inputs={DATA_ADDRESS: _boundary._digest(held_ok / "data.txt")},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "matching" / "scratch",
        cores=1,
    )
    assert isinstance(matching, RunMinted)


def test_stage_inputs_hashes_copied_staged_bytes_not_source_file(tmp_path, monkeypatch):
    import shutil as _shutil

    code, held = stage(tmp_path)
    source_path = held / "data.txt"
    expected_digest = _boundary._digest(source_path)
    real_copy2 = _shutil.copy2

    def tampered_copy2(src, dst, *args, **kwargs):
        result = real_copy2(src, dst, *args, **kwargs)
        if Path(src) == source_path:
            Path(dst).write_bytes(b"tampered-during-copy\n")
        return result

    monkeypatch.setattr(_boundary.shutil, "copy2", tampered_copy2)
    _forbid_engines(monkeypatch)
    outcome = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: source_path, READS_ADDRESS: held / "palette.txt"},
        expected_inputs={DATA_ADDRESS: expected_digest},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
        cores=1,
    )
    assert _boundary._digest(source_path) == expected_digest
    assert isinstance(outcome, RunRefused)
    assert "does not match expected" in outcome.reason


@pytest.mark.parametrize("policy", [MINIMAL_POLICY, CONFINED_POLICY])
def test_planning_restage_refuses_source_mutated_after_initial_staging_and_cleans_planning_dir(
    tmp_path, monkeypatch, policy
):
    code, held = stage(tmp_path)
    source_path = held / "data.txt"
    scratch_base = tmp_path / "scratch"
    real_stage_inputs = _boundary._stage_inputs
    calls = 0

    def mutating_stage_inputs(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = real_stage_inputs(*args, **kwargs)
        if calls == 1:
            source_path.write_bytes(b"mutated-before-planning\n")
        return result

    if policy == CONFINED_POLICY:
        monkeypatch.setattr(_boundary, "materialize_snapshot", lambda captured, root: root)
    monkeypatch.setattr(_boundary, "_stage_inputs", mutating_stage_inputs)
    _forbid_engines(monkeypatch)

    outcome = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=MEMORY_PORT,
        boundary_policy=policy,
        definition=definition(),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: source_path, READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=scratch_base,
        cores=1,
    )
    assert calls == 2
    assert isinstance(outcome, RunRefused)
    assert "does not match expected" in outcome.reason
    assert list(scratch_base.glob("planning-*")) == []


@pytest.mark.parametrize(
    ("bad_expected", "expected_Fragment"),
    [
        (["not-a-mapping"], "expected_inputs must be a mapping"),
        ({}, f"expected input {DATA_ADDRESS!r} is missing content identity"),
        ({DATA_ADDRESS: "not-a-sha256"}, f"expected input {DATA_ADDRESS!r} has malformed content identity"),
    ],
)
def test_stage_inputs_refuses_malformed_or_incomplete_expected_inputs(
    tmp_path, monkeypatch, bad_expected, expected_Fragment
):
    code, held = stage(tmp_path)
    _forbid_engines(monkeypatch)
    outcome = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        expected_inputs=bad_expected,  # type: ignore[arg-type]
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
        cores=1,
    )
    assert isinstance(outcome, RunRefused)
    assert expected_Fragment in outcome.reason


def test_production_run_checks_expected_inputs_and_planning_restage(tmp_path, monkeypatch):
    code, held = stage(tmp_path / "disagree", snakefile=SNAKEFILE_PRODUCTION)
    actual_digest = _boundary._digest(held / "data.txt")
    _forbid_engines(monkeypatch)

    disagree = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=actual_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        expected_inputs={DATA_ADDRESS: "sha256:" + "b" * 64},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "disagree" / "scratch",
        cores=1,
    )
    assert isinstance(disagree, RunRefused)
    assert "does not match recipe input" in disagree.reason

    code_m, held_m = stage(tmp_path / "missing", snakefile=SNAKEFILE_PRODUCTION)
    missing = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=actual_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION),
        code_roots=(code_m,),
        held_inputs={DATA_ADDRESS: held_m / "data.txt", READS_ADDRESS: held_m / "palette.txt"},
        expected_inputs={},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "missing" / "scratch",
        cores=1,
    )
    assert isinstance(missing, RunRefused)
    assert f"expected input {DATA_ADDRESS!r} is missing content identity" in missing.reason

    code_c, held_c = stage(tmp_path / "conflict", snakefile=SNAKEFILE_PRODUCTION)
    conflict = execute_production_run(
        inputs=(
            RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=actual_digest),
            RecipeInput(role="reads", dataset=DATA_ADDRESS, content="sha256:" + "c" * 64),
        ),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION),
        code_roots=(code_c,),
        held_inputs={DATA_ADDRESS: held_c / "data.txt", READS_ADDRESS: held_c / "palette.txt"},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "conflict" / "scratch",
        cores=1,
    )
    assert isinstance(conflict, RunRefused)
    assert "recipe inputs disagree on content identity" in conflict.reason


# --- multi-resource input staging & two-pass member verification (beliefs-98f1d7) ---

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

SNAKEFILE_MULTI_RESOURCE = """\
import pathlib

rule transform:
    input: "inputs/tables/expression.tsv", "inputs/tables/clinical.tsv"
    output: "outputs/result.txt"
    run:
        expr = pathlib.Path(input[0]).read_text()
        clin = pathlib.Path(input[1]).read_text()
        pathlib.Path(output[0]).write_text((expr + "|" + clin).upper())
"""

SNAKEFILE_SINGLE_NESTED_MEMBER = """\
import pathlib

rule transform:
    input: "inputs/tables/clinical.tsv"
    output: "outputs/result.txt"
    run:
        assert not pathlib.Path("inputs/clinical.tsv").exists()
        clin = pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text(clin.upper())
"""


def _stage_package_files(tmp_path: Path) -> tuple[Path, Path]:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    expr_path = pkg_dir / "expression.tsv"
    clin_path = pkg_dir / "clinical.tsv"
    expr_path.write_text("gene\ttpm\nTP53\t42\n")
    clin_path.write_text("sample\tarm\nS1\tA\n")
    return expr_path, clin_path


def test_boundary_stages_multi_resource_dataset_and_folds_content_digest(tmp_path):
    code, _ = stage(tmp_path, snakefile=SNAKEFILE_MULTI_RESOURCE)
    expr_path, clin_path = _stage_package_files(tmp_path)
    expr_digest = _boundary._digest(expr_path)
    clin_digest = _boundary._digest(clin_path)
    expected_folded = dataset_address(
        DatasetDeclaration(
            resources=(
                ResourceDeclaration("tables/clinical.tsv", clin_digest),
                ResourceDeclaration("tables/expression.tsv", expr_digest),
            )
        )
    )
    assert expected_folded is not None
    expected_content = expected_folded.removeprefix("dataset:")

    spec = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
        ),
        held_rules=spec_rules(),
    )
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_MULTI_RESOURCE, family_streams={}),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: {
                "tables/expression.tsv": expr_path,
                "tables/clinical.tsv": clin_path,
            }
        },
        expected_inputs={
            DATA_ADDRESS: {
                "tables/expression.tsv": expr_digest,
                "tables/clinical.tsv": clin_digest,
            }
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
        cores=1,
    )
    assert isinstance(outcome, RunMinted), outcome
    assert outcome.run.recipe.inputs[0].content == expected_content
    scratch = Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    assert (scratch / "inputs" / "tables" / "expression.tsv").read_text() == expr_path.read_text()
    assert (scratch / "inputs" / "tables" / "clinical.tsv").read_text() == clin_path.read_text()
    assert (scratch / "outputs" / "result.txt").read_text() == (
        expr_path.read_text() + "|" + clin_path.read_text()
    ).upper()


def test_boundary_preserves_nested_member_path_for_single_resource_mapping(tmp_path):
    code, _ = stage(tmp_path, snakefile=SNAKEFILE_SINGLE_NESTED_MEMBER)
    _, clin_path = _stage_package_files(tmp_path)
    clin_digest = _boundary._digest(clin_path)

    spec = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
        ),
        held_rules=spec_rules(),
    )
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_SINGLE_NESTED_MEMBER, family_streams={}),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: {"tables/clinical.tsv": clin_path}},
        expected_inputs={DATA_ADDRESS: {"tables/clinical.tsv": clin_digest}},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch-assess",
        cores=1,
    )
    assert isinstance(outcome, RunMinted), outcome
    assert outcome.run.recipe.inputs[0].content == clin_digest
    scratch = Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    assert (scratch / "inputs" / "tables" / "clinical.tsv").is_file()
    assert not (scratch / "inputs" / "clinical.tsv").exists()

    prod_outcome = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=clin_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_SINGLE_NESTED_MEMBER, family_streams={}),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: {"tables/clinical.tsv": clin_path}},
        expected_inputs={DATA_ADDRESS: {"tables/clinical.tsv": clin_digest}},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch-prod",
        cores=1,
    )
    assert isinstance(prod_outcome, RunMinted), prod_outcome
    assert prod_outcome.run.recipe.inputs[0].content == clin_digest


@pytest.mark.parametrize("policy", [MINIMAL_POLICY, CONFINED_POLICY])
def test_boundary_refuses_when_two_members_swap_bytes_between_initial_and_planning_staging(
    tmp_path, monkeypatch, policy
):
    code, _ = stage(tmp_path, snakefile=SNAKEFILE_MULTI_RESOURCE)
    expr_path = tmp_path / "expression.tsv"
    clin_path = tmp_path / "clinical.tsv"
    expr_bytes = b"gene\ttpm\nTP53\t42\n"
    clin_bytes = b"sample\tarm\nS1\tA\n"
    expr_path.write_bytes(expr_bytes)
    clin_path.write_bytes(clin_bytes)
    expr_digest = _boundary._digest(expr_path)
    clin_digest = _boundary._digest(clin_path)

    scratch_base = tmp_path / "scratch"
    real_stage_inputs = _boundary._stage_inputs
    calls = 0

    def swapping_stage_inputs(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = real_stage_inputs(*args, **kwargs)
        if calls == 1:
            expr_path.write_bytes(clin_bytes)
            clin_path.write_bytes(expr_bytes)
        return result

    if policy == CONFINED_POLICY:
        monkeypatch.setattr(_boundary, "materialize_snapshot", lambda captured, root: root)
    monkeypatch.setattr(_boundary, "_stage_inputs", swapping_stage_inputs)
    _forbid_engines(monkeypatch)

    spec = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
        ),
        held_rules=spec_rules(),
    )
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=policy,
        definition=definition(snakefile=SNAKEFILE_MULTI_RESOURCE, family_streams={}),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: {
                "expression.tsv": expr_path,
                "clinical.tsv": clin_path,
            }
        },
        expected_inputs={
            DATA_ADDRESS: {
                "expression.tsv": expr_digest,
                "clinical.tsv": clin_digest,
            }
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=scratch_base,
        cores=1,
    )
    assert calls == 2
    assert isinstance(outcome, RunRefused)
    assert "resource 'clinical.tsv' digest" in outcome.reason or "resource 'expression.tsv' digest" in outcome.reason
    assert outcome.intent is not None
    assert outcome.report is not None
    assert outcome.registration is not None
    assert completion(outcome.intent, (outcome.registration,), {outcome.report.identity(): outcome.report}) == CLOSED
    assert list(scratch_base.glob("planning-*")) == []


def test_multi_resource_validation_refusals_before_and_during_staging(tmp_path, monkeypatch):
    code, _ = stage(tmp_path, snakefile=SNAKEFILE_MULTI_RESOURCE)
    expr_path, clin_path = _stage_package_files(tmp_path)
    expr_digest = _boundary._digest(expr_path)
    spec = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
        ),
        held_rules=spec_rules(),
    )
    _forbid_engines(monkeypatch)

    def _run(held_in, expected_in=None, spec_in=spec, sub="case"):
        return execute_assessment_run(
            spec=spec_in,
            port=MEMORY_PORT,
            boundary_policy=MINIMAL_POLICY,
            definition=definition(snakefile=SNAKEFILE_MULTI_RESOURCE, family_streams={}),
            code_roots=(code,),
            held_inputs=held_in,
            expected_inputs=expected_in,
            entrypoint="code/workflow/Snakefile",
            targets=("outputs/result.txt",),
            declared_outputs=("outputs/result.txt",),
            observer="observer-1",
            started_at="2026-08-12T00:00:00Z",
            host_realization="host-a",
            scratch_base=tmp_path / f"scratch-{sub}",
            cores=1,
        )

    # 1. Empty mapping refuses pre-intent with input-not-held
    empty = _run({DATA_ADDRESS: {}}, sub="empty")
    assert isinstance(empty, RunRefused)
    assert empty.reason == "input-not-held"
    assert empty.intent is None and empty.report is not None

    # 2. Per-resource digest mismatch refuses before engine launch
    bad_member = _run(
        {DATA_ADDRESS: {"tables/expression.tsv": expr_path, "tables/clinical.tsv": clin_path}},
        {DATA_ADDRESS: {"tables/expression.tsv": expr_digest, "tables/clinical.tsv": "sha256:" + "0" * 64}},
        sub="bad-member",
    )
    assert isinstance(bad_member, RunRefused)
    assert "resource 'tables/clinical.tsv' digest" in bad_member.reason

    # 3. Mismatched keys between held_inputs and expected_inputs
    key_mismatch = _run(
        {DATA_ADDRESS: {"a.tsv": expr_path}},
        {DATA_ADDRESS: {"b.tsv": expr_digest}},
        sub="key-mismatch",
    )
    assert isinstance(key_mismatch, RunRefused)
    assert key_mismatch.intent is not None

    # 4. Plain str expected_inputs for a Mapping held_inputs is refused
    plain_str_for_mapping = _run(
        {DATA_ADDRESS: {"a.tsv": expr_path}},
        {DATA_ADDRESS: expr_digest},
        sub="plain-str-for-mapping",
    )
    assert isinstance(plain_str_for_mapping, RunRefused)

    # 5. Mapping expected_inputs for a Path held_inputs is refused
    mapping_for_path = _run(
        {DATA_ADDRESS: expr_path},
        {DATA_ADDRESS: {"a.tsv": expr_digest}},
        sub="mapping-for-path",
    )
    assert isinstance(mapping_for_path, RunRefused)

    # 6. Unsafe relative paths in held_inputs
    for idx, unsafe_rel in enumerate(
        ("../escape.tsv", "/abs.tsv", ".#~scratch.tsv", "a/../b.tsv", "a//b.tsv", "a\\b.tsv")
    ):
        unsafe = _run(
            {DATA_ADDRESS: {unsafe_rel: expr_path}},
            None,
            sub=f"unsafe-{idx}",
        )
        assert isinstance(unsafe, RunRefused), unsafe_rel
        assert "relative input path" in unsafe.reason

    # 7. File-vs-file and file-vs-directory collisions across input datasets
    two_input_spec = freeze(
        spec_draft(
            nondeterminism=Deterministic(),
            input_roles=(
                SpecInput(role="observes", dataset=DATA_ADDRESS),
                SpecInput(role="reads", dataset=READS_ADDRESS),
            ),
        ),
        held_rules=spec_rules(),
    )
    file_collision = _run(
        {
            DATA_ADDRESS: {"tables/clinical.tsv": expr_path},
            READS_ADDRESS: {"tables/clinical.tsv": clin_path},
        },
        spec_in=two_input_spec,
        sub="file-collision",
    )
    assert isinstance(file_collision, RunRefused)
    assert "collide" in file_collision.reason

    dir_collision = _run(
        {
            DATA_ADDRESS: {"tables": expr_path},
            READS_ADDRESS: {"tables/clinical.tsv": clin_path},
        },
        spec_in=two_input_spec,
        sub="dir-collision",
    )
    assert isinstance(dir_collision, RunRefused)
    assert "collide" in dir_collision.reason

    reverse_dir_collision = _run(
        {
            DATA_ADDRESS: {"tables/clinical.tsv": clin_path},
            READS_ADDRESS: {"tables": expr_path},
        },
        spec_in=two_input_spec,
        sub="reverse-dir-collision",
    )
    assert isinstance(reverse_dir_collision, RunRefused)
    assert "collide" in reverse_dir_collision.reason

    # 8. Symlink member in held_inputs is refused
    symlink_path = tmp_path / "symlink_expr.tsv"
    symlink_path.symlink_to(expr_path)
    symlink_refused = _run(
        {DATA_ADDRESS: {"tables/expression.tsv": symlink_path}},
        None,
        sub="symlink",
    )
    assert isinstance(symlink_refused, RunRefused)
    assert "is not a readable file" in symlink_refused.reason


# --- produced dataset minting and pre-intent validation (beliefs-584078) ---


def test_production_run_requires_dataset_in_permit_mints(tmp_path):
    from fixtures_cut3 import run_production as production_run

    port = _NarrowPort(narrowed(kinds=("run", "act-report"), families=("run",)))
    outcome = production_run(tmp_path, port=port)
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None and outcome.registration is None
    assert "kind dataset" in outcome.detail
    assert port.appended == []


def test_production_run_refuses_pre_intent_on_invalid_transforms_or_dataset_title(tmp_path, monkeypatch):
    code, held = stage(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    data_digest = _boundary._digest(held / "data.txt")
    reads_digest = _boundary._digest(held / "palette.txt")
    _forbid_engines(monkeypatch)

    class _RecordingPort(MemoryPort):
        authority = FULL

        def __init__(self):
            self.intents: list[bytes] = []
            self.executed: list[object] = []

        def append_intent(self, payload: bytes) -> str:
            self.intents.append(payload)
            return super().append_intent(payload)

        def execute(self, plan) -> None:
            self.executed.append(plan)

    def _call_prod(inputs, *, dataset_title: object = "produced dataset", sub="case"):
        port = _RecordingPort()
        outcome = execute_production_run(
            inputs=inputs,
            parameters={},
            nondeterminism=Deterministic(),
            port=port,
            boundary_policy=MINIMAL_POLICY,
            definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
            code_roots=(code,),
            held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
            entrypoint="code/workflow/Snakefile",
            targets=("outputs/result.txt",),
            declared_outputs=("outputs/result.txt",),
            observer="observer-1",
            started_at="2026-08-12T00:00:00Z",
            host_realization="host-a",
            scratch_base=tmp_path / f"scratch-{sub}",
            cores=1,
            dataset_title=dataset_title,  # type: ignore[arg-type]
        )
        return outcome, port

    # 1. Zero transforms inputs (only reads)
    reads_only = (RecipeInput(role="reads", dataset=READS_ADDRESS, content=reads_digest),)
    outcome_zero, port_zero = _call_prod(reads_only, sub="zero-transforms")
    assert isinstance(outcome_zero, RunRefused)
    assert outcome_zero.reason == "malformed-inputs"
    assert outcome_zero.intent is None and outcome_zero.registration is None and outcome_zero.report is not None
    assert port_zero.intents == [] and len(port_zero.executed) == 1

    # 2. >1 distinct transforms datasets
    two_transforms = (
        RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=data_digest),
        RecipeInput(role="transforms", dataset=READS_ADDRESS, content=reads_digest),
    )
    outcome_two, port_two = _call_prod(two_transforms, sub="two-transforms")
    assert isinstance(outcome_two, RunRefused)
    assert outcome_two.reason == "malformed-inputs"
    assert outcome_two.intent is None and outcome_two.registration is None and outcome_two.report is not None
    assert port_two.intents == [] and len(port_two.executed) == 1

    # 3. Invalid dataset_title (empty, whitespace, non-str)
    valid_inputs = (
        RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=data_digest),
        RecipeInput(role="reads", dataset=READS_ADDRESS, content=reads_digest),
    )
    for idx, bad_title in enumerate(("", "   ", 123, None)):
        outcome_title, port_title = _call_prod(valid_inputs, dataset_title=bad_title, sub=f"bad-title-{idx}")
        assert isinstance(outcome_title, RunRefused)
        assert outcome_title.reason == "malformed-inputs"
        assert outcome_title.intent is None and outcome_title.registration is None and outcome_title.report is not None
        assert port_title.intents == [] and len(port_title.executed) == 1


def test_production_run_with_one_transforms_and_reads_mints_dataset_with_custom_title(tmp_path):
    from nodes.core.frontmatter import node_from_markdown
    from nodes.core.paths import path_for_node_id

    from beliefs import stored
    from beliefs.production import mint_dataset
    from beliefs.runrecord import GuardedCommit, run_ref

    code, held = stage(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    data_digest = _boundary._digest(held / "data.txt")
    reads_digest = _boundary._digest(held / "palette.txt")

    class _CapturingPort(MemoryPort):
        authority = FULL

        def __init__(self):
            self.plans: list[tuple] = []

        def execute_fulfilling_guarded(self, plan, fulfills: str, *, guard, fallback):
            self.plans.append(plan)
            return GuardedCommit("r" * 64, None)

    port = _CapturingPort()
    outcome = execute_production_run(
        inputs=(
            RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=data_digest),
            RecipeInput(role="reads", dataset=READS_ADDRESS, content=reads_digest),
        ),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
        cores=1,
        dataset_title="curated package",
    )
    assert isinstance(outcome, RunMinted), outcome
    assert len(port.plans) == 1
    run_op, dataset_op = port.plans[0]
    assert run_op.path == f"run/{outcome.run.address()}.md"
    minted = mint_dataset(outcome.run, existing_bases={})
    assert dataset_op.path == path_for_node_id(minted.address)
    dataset_node = node_from_markdown(dataset_op.content.decode("utf-8"))
    assert dataset_node.id == minted.address
    assert dataset_node.title == "curated package"
    assert stored.lineage_basis(dataset_node) == {
        "tag": "single",
        "routes": [
            {
                "run": run_ref(outcome.run.address()),
                "ancestor": DATA_ADDRESS,
                "transforms": [DATA_ADDRESS],
            }
        ],
    }


# --- verified output export from execute_production_run (beliefs-9dfa3f) ---

SNAKEFILE_PRODUCTION_PACKAGE = """\
import pathlib

rule package:
    input: "inputs/data.txt"
    output: "tables/expression.tsv", "datapackage.json"
    run:
        text = pathlib.Path(input[0]).read_text().strip()
        out_table = pathlib.Path(output[0])
        out_table.parent.mkdir(parents=True, exist_ok=True)
        out_table.write_text(f"gene\\tvalue\\n{text.upper()}\\t1\\n")
        pathlib.Path(output[1]).write_text('{"name": "pkg"}\\n')
"""


class _GuardedMemoryPort(MemoryPort):
    authority = FULL

    def __init__(self, initial_nodes: dict[str, Any] | None = None):
        self.nodes: dict[str, Any] = dict(initial_nodes or {})
        self.plans: list[tuple] = []
        self.reasons: list[str | None] = []
        self.fulfilled: list[tuple] = []

    def holds(self, ref: str) -> bool:
        return ref in self.nodes

    def resolve(self, ref: str) -> str | None:
        return ref if ref in self.nodes else None

    def get(self, ref: str):
        return self.nodes[ref]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return ()

    def execute_fulfilling(self, plan, fulfills: str) -> str:
        self.fulfilled.append(plan)
        return super().execute_fulfilling(plan, fulfills)

    def execute_fulfilling_guarded(self, plan, fulfills: str, *, guard, fallback):
        from nodes.core.frontmatter import node_from_markdown

        from beliefs.runrecord import GuardedCommit

        reason = guard(self)
        self.reasons.append(reason)
        chosen = plan if reason is None else fallback(reason)
        self.plans.append(chosen)
        for op in chosen:
            node = node_from_markdown(op.content.decode("utf-8"))
            self.nodes[node.id] = node
        return GuardedCommit("r" * 64, reason)


def _run_package_production(tmp_path: Path, *, port=MEMORY_PORT, output_dir: Any = None, sub: str = "run"):
    code, held = stage(tmp_path / sub, snakefile=SNAKEFILE_PRODUCTION_PACKAGE)
    data_digest = _boundary._digest(held / "data.txt")
    return execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=data_digest),),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION_PACKAGE, family_streams={}),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile",
        targets=("tables/expression.tsv", "datapackage.json"),
        declared_outputs=("tables/expression.tsv", "datapackage.json"),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / sub / "scratch",
        cores=1,
        output_dir=output_dir,
    )


def test_execute_production_run_exports_verified_declared_outputs_to_output_dir(tmp_path):
    output_dir = tmp_path / "exported"
    output_dir.mkdir()
    outcome = _run_package_production(tmp_path, output_dir=output_dir)
    assert isinstance(outcome, RunMinted), outcome
    expected = dict(outcome.run.result.outputs)
    assert set(expected) == {"tables/expression.tsv", "datapackage.json"}
    for rel_name, expected_digest in expected.items():
        exported_file = output_dir / rel_name
        assert exported_file.is_file()
        assert _boundary._digest(exported_file) == expected_digest


def test_execute_production_run_refuses_invalid_output_dir_pre_intent(tmp_path, monkeypatch):
    _forbid_engines(monkeypatch)

    class _RecordingPort(MemoryPort):
        authority = FULL

        def __init__(self):
            self.intents: list[bytes] = []
            self.executed: list[object] = []

        def append_intent(self, payload: bytes) -> str:
            self.intents.append(payload)
            return super().append_intent(payload)

        def execute(self, plan) -> None:
            self.executed.append(plan)

    missing_dir = tmp_path / "does-not-exist"
    regular_file = tmp_path / "regular-file.txt"
    regular_file.write_text("not a dir\n")
    real_dir = tmp_path / "real-dir"
    real_dir.mkdir()
    symlink_dir = tmp_path / "symlink-dir"
    symlink_dir.symlink_to(real_dir)

    for idx, bad_output_dir in enumerate((missing_dir, regular_file, symlink_dir)):
        port = _RecordingPort()
        outcome = _run_package_production(tmp_path, port=port, output_dir=bad_output_dir, sub=f"invalid-{idx}")
        assert isinstance(outcome, RunRefused)
        assert outcome.reason == "malformed-inputs"
        assert outcome.intent is None and outcome.registration is None and outcome.report is not None
        assert port.intents == [] and len(port.executed) == 1


def test_execute_production_run_cleans_partial_file_and_nested_dirs_on_injected_copy_failure(tmp_path, monkeypatch):
    import shutil as _shutil

    output_dir = tmp_path / "exported"
    output_dir.mkdir()
    target_dest = (output_dir / "tables/expression.tsv").resolve()
    real_copy2 = _shutil.copy2

    def failing_copy2(src, dst, *args, **kwargs):
        if Path(dst).resolve() == target_dest:
            Path(dst).write_bytes(b"partial")
            raise OSError("simulated mid-copy failure")
        return real_copy2(src, dst, *args, **kwargs)

    monkeypatch.setattr(_boundary.shutil, "copy2", failing_copy2)
    port = _GuardedMemoryPort()
    outcome = _run_package_production(tmp_path, port=port, output_dir=output_dir)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "manifest-digest-mismatch"
    assert outcome.intent is not None and outcome.report is not None and outcome.registration is not None
    assert len(port.fulfilled) == 1
    assert port.fulfilled[0][0].path == f"act-report/{outcome.report.identity()}.md"
    assert list(output_dir.iterdir()) == []


def test_execute_production_run_cleans_nested_outputs_and_dirs_on_acquisition_guard_refusal(tmp_path):
    from hashlib import sha256 as _sha256

    from nodes.core.node import Node

    from beliefs import stored

    expr_digest = "sha256:" + _sha256(b"gene\tvalue\nHELLO\t1\n").hexdigest()
    pkg_digest = "sha256:" + _sha256(b'{"name": "pkg"}\n').hexdigest()
    produced_address = dataset_address(
        DatasetDeclaration(
            resources=(
                ResourceDeclaration("datapackage.json", pkg_digest),
                ResourceDeclaration("tables/expression.tsv", expr_digest),
            )
        )
    )
    assert produced_address is not None

    empirical_node = Node(
        id=produced_address,
        kind="dataset",
        title="empirical package",
        facets={stored.EMPIRICAL_OBSERVATION_FACET: {"source": "https://example.org/pkg"}},
    )
    port = _GuardedMemoryPort({produced_address: empirical_node})
    output_dir = tmp_path / "exported"
    output_dir.mkdir()

    outcome = _run_package_production(tmp_path, port=port, output_dir=output_dir)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "acquisition-boundary"
    assert outcome.intent is not None and outcome.report is not None and outcome.registration is not None
    assert len(port.plans) == 1
    assert port.plans[0][0].path == f"act-report/{outcome.report.identity()}.md"
    assert list(output_dir.iterdir()) == []


def test_execute_production_run_retains_output_dir_when_dataset_already_held(tmp_path):
    port = _GuardedMemoryPort()
    output_dir_1 = tmp_path / "exported-1"
    output_dir_1.mkdir()
    output_dir_2 = tmp_path / "exported-2"
    output_dir_2.mkdir()

    outcome_1 = _run_package_production(tmp_path, port=port, output_dir=output_dir_1, sub="run-1")
    outcome_2 = _run_package_production(tmp_path, port=port, output_dir=output_dir_2, sub="run-2")

    assert isinstance(outcome_1, RunMinted), outcome_1
    assert isinstance(outcome_2, RunMinted), outcome_2
    assert port.reasons == [None, _boundary._DATASET_ALREADY_HELD]
    assert len(port.plans[0]) == 2
    assert len(port.plans[1]) == 1

    expected = dict(outcome_2.run.result.outputs)
    for rel_name, expected_digest in expected.items():
        exported_file = output_dir_2 / rel_name
        assert exported_file.is_file()
        assert _boundary._digest(exported_file) == expected_digest


# --- tree inputs in run staging (beliefs-2814d7) ---

from hashlib import sha256

from fixtures_cut3 import SNAKEFILE_TREE, TREE_MEMBERS, lay_tree

from beliefs.tree import object_path


def _tree_assessment(tmp_path: Path, held_inputs, *, scratch_base: Path, policy=MINIMAL_POLICY):
    code, _ = stage(tmp_path, snakefile=SNAKEFILE_TREE)
    return execute_assessment_run(
        spec=freeze(
            spec_draft(
                nondeterminism=Deterministic(),
                input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS),),
            ),
            held_rules=spec_rules(),
        ),
        port=MEMORY_PORT,
        boundary_policy=policy,
        definition=definition(snakefile=SNAKEFILE_TREE, family_streams={}),
        code_roots=(code,),
        held_inputs=held_inputs,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=scratch_base,
        cores=1,
    )


def _damage_last_member(store: Path) -> None:
    last = max(TREE_MEMBERS)  # the last member in tree order, staged after the others
    target = store / object_path("sha256:" + sha256(TREE_MEMBERS[last]).hexdigest())
    target.write_bytes(b"damaged after it was observed\n")


def test_stage_inputs_stages_a_held_tree_as_a_directory(tmp_path):
    held = lay_tree(tmp_path / "store", TREE_MEMBERS)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    staged_trees: list[Path] = []

    staged = _boundary._stage_inputs(
        (DATA_ADDRESS,), {DATA_ADDRESS: {"data": held}}, scratch, staged_trees=staged_trees
    )

    assert held.digest.startswith("sha256-tree:")
    assert staged == {DATA_ADDRESS: {"data": held.digest}}
    root = scratch / "inputs" / "data"
    files = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if not path.is_dir()}
    assert {name: path.read_bytes() for name, path in files.items()} == TREE_MEMBERS
    for path in files.values():
        assert not path.is_symlink() and path.stat().st_nlink == 1  # a copy: neither a symbolic nor a hard link
    assert staged_trees == [root.resolve()]


@pytest.mark.parametrize("damaged", ["member", "tree-file"])
def test_a_damaged_tree_object_refuses_staging(tmp_path, monkeypatch, damaged):
    store = tmp_path / "store"
    held = lay_tree(store, TREE_MEMBERS)
    if damaged == "member":
        _damage_last_member(store)
    else:
        tree_file = store / object_path(held.digest)
        tree_file.write_bytes(tree_file.read_bytes() + b"\n")
    held_inputs = {DATA_ADDRESS: {"data": held}}

    scratch = tmp_path / "direct"
    scratch.mkdir()
    with pytest.raises(MalformedClosure, match="does not match"):
        _boundary._stage_inputs((DATA_ADDRESS,), held_inputs, scratch, staged_trees=[])

    _forbid_engines(monkeypatch)
    scratch_base = tmp_path / "scratch"
    outcome = _tree_assessment(tmp_path / "run", held_inputs, scratch_base=scratch_base)
    assert isinstance(outcome, RunRefused), outcome
    assert "does not match" in outcome.reason
    assert outcome.intent is not None and outcome.report is not None
    (run_scratch,) = scratch_base.iterdir()
    assert (run_scratch / "inputs").is_dir() and not (run_scratch / "inputs" / "data").exists()


@pytest.mark.parametrize("linked", ["member", "tree-file"])
def test_a_symlinked_tree_object_refuses_staging_even_with_the_right_bytes(tmp_path, linked):
    store = tmp_path / "store"
    held = lay_tree(store, TREE_MEMBERS)
    digest = held.digest if linked == "tree-file" else "sha256:" + sha256(TREE_MEMBERS["a.txt"]).hexdigest()
    target = store / object_path(digest)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(elsewhere)
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    with pytest.raises(MalformedClosure, match="is not a readable file"):
        _boundary._stage_inputs((DATA_ADDRESS,), {DATA_ADDRESS: {"data": held}}, scratch, staged_trees=[])


def test_a_tree_member_is_verified_by_its_staged_copy(tmp_path, monkeypatch):
    held = lay_tree(tmp_path / "store", TREE_MEMBERS)
    real_copyfile = _boundary.shutil.copyfile

    def tampering_copyfile(src, dst, **kwargs):
        result = real_copyfile(src, dst, **kwargs)
        Path(dst).write_bytes(b"tampered during the copy\n")
        return result

    monkeypatch.setattr(_boundary.shutil, "copyfile", tampering_copyfile)
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    with pytest.raises(MalformedClosure, match="member 'a.txt' digest .* does not match"):
        _boundary._stage_inputs((DATA_ADDRESS,), {DATA_ADDRESS: {"data": held}}, scratch, staged_trees=[])


_FILE = "file"
_TREE = "tree"


@pytest.mark.parametrize("reverse", [False, True], ids=["in-order", "reversed"])
@pytest.mark.parametrize(
    ("first", "second"),
    [
        ((_FILE, "data"), (_TREE, "data")),
        ((_FILE, "data/x"), (_TREE, "data")),
        ((_TREE, "data"), (_TREE, "data/sub")),
        ((_TREE, "data"), (_TREE, "data")),
        ((_TREE, "d"), (_FILE, "d/data/y")),
    ],
    ids=["file-equals-tree", "file-under-tree", "tree-under-tree", "tree-equals-tree", "file-deep-under-tree"],
)
def test_a_tree_root_reserves_its_subtree(tmp_path, monkeypatch, first, second, reverse):
    source = tmp_path / "file.txt"
    source.write_text("a file resource\n")
    tree = lay_tree(tmp_path / "store", {"x": b"a verified member\n", "data/y": b"another member\n"})

    def resource(kind):
        return tree if kind == _TREE else source

    held_inputs = {
        DATA_ADDRESS: {first[1]: resource(first[0])},
        READS_ADDRESS: {second[1]: resource(second[0])},
    }
    addresses = (READS_ADDRESS, DATA_ADDRESS) if reverse else (DATA_ADDRESS, READS_ADDRESS)
    copies: list[object] = []
    monkeypatch.setattr(_boundary.shutil, "copy2", lambda src, dst, **kwargs: copies.append(dst))
    monkeypatch.setattr(_boundary.shutil, "copyfile", lambda src, dst, **kwargs: copies.append(dst))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    staged_trees: list[Path] = []

    with pytest.raises(MalformedClosure, match="collide"):
        _boundary._stage_inputs(addresses, held_inputs, scratch, staged_trees=staged_trees)
    assert copies == []
    assert staged_trees == []


def test_a_confined_tree_refused_mid_staging_leaves_no_staged_tree(tmp_path, monkeypatch):
    store = tmp_path / "store"
    held = lay_tree(store, TREE_MEMBERS)
    _damage_last_member(store)
    real_copyfile = _boundary.shutil.copyfile
    copied: list[str] = []

    def recording_copyfile(src, dst, **kwargs):
        if "inputs" in Path(dst).parts:  # copy2 copies the code bundle through copyfile too
            copied.append(Path(dst).name)
        return real_copyfile(src, dst, **kwargs)

    monkeypatch.setattr(_boundary.shutil, "copyfile", recording_copyfile)
    monkeypatch.setattr(_boundary, "materialize_snapshot", lambda captured, root: root)
    monkeypatch.setattr(_boundary, "require_host", lambda: None)
    _forbid_engines(monkeypatch)
    scratch_base = tmp_path / "scratch"

    outcome = _tree_assessment(
        tmp_path / "run", {DATA_ADDRESS: {"data": held}}, scratch_base=scratch_base, policy=CONFINED_POLICY
    )

    assert isinstance(outcome, RunRefused), outcome
    assert "does not match" in outcome.reason
    assert copied == ["a.txt", "b.txt"]  # the first member was staged before the damaged one refused
    (run_scratch,) = scratch_base.iterdir()
    assert (run_scratch / "out" / "inputs").is_dir()
    assert not (run_scratch / "out" / "inputs" / "data").exists()
    assert list(scratch_base.glob("planning-*")) == []


def test_a_tree_expected_input_must_be_its_tree_digest(tmp_path):
    held = lay_tree(tmp_path / "store", TREE_MEMBERS)
    other = lay_tree(tmp_path / "other", {"a.txt": b"another tree\n"})
    tree_file_digest = "sha256:" + held.digest.removeprefix("sha256-tree:")

    def stage_expecting(expected, sub):
        scratch = tmp_path / sub
        scratch.mkdir()
        return _boundary._stage_inputs(
            (DATA_ADDRESS,), {DATA_ADDRESS: {"data": held}}, scratch, {DATA_ADDRESS: expected}, staged_trees=[]
        )

    staged = {DATA_ADDRESS: {"data": held.digest}}
    assert stage_expecting({"data": held.digest}, "mapping") == staged
    assert stage_expecting(_boundary._RecipeContent(held.digest), "recipe-content") == staged
    for idx, wrong in enumerate(
        ({"data": other.digest}, {"data": tree_file_digest}, _boundary._RecipeContent(other.digest))
    ):
        with pytest.raises(MalformedClosure, match="does not match expected"):
            stage_expecting(wrong, f"wrong-{idx}")


def test_a_staged_tree_is_removed_after_a_production_run(tmp_path):
    held = lay_tree(tmp_path / "store", TREE_MEMBERS)
    reads = tmp_path / "reads.txt"
    reads.write_text("a file resource beside the tree\n")
    output_dir = tmp_path / "exported"
    output_dir.mkdir()

    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_TREE,
        inputs=(
            RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=held.digest),
            RecipeInput(role="reads", dataset=READS_ADDRESS, content=_boundary._digest(reads)),
        ),
        held_inputs={DATA_ADDRESS: {"data": held}, READS_ADDRESS: reads},
        output_dir=output_dir,
    )

    assert isinstance(outcome, RunMinted), outcome
    assert outcome.run.recipe.inputs[0].content == held.digest
    scratch = Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    assert not (scratch / "inputs" / "data").exists()
    assert (scratch / "inputs" / "reads.txt").read_bytes() == reads.read_bytes()  # non-tree staging is kept
    assert outcome.run.result.outputs
    for name, digest in outcome.run.result.outputs:
        assert _boundary._digest(output_dir / name) == digest
    assert (output_dir / "outputs" / "result.txt").read_text() == "ALPHA\n|BETA\n"
