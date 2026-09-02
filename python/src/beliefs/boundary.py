"""Begin, execute, capture, and mint runs through the minimal adapter, or
through the confined policy's snapshot-and-sandbox path (run-confinement
design §5).

The scratch root is staging under the minimal policy and the host side of the
output root under the confined one. The boundary renders configuration,
environment, and argv, never the workflow definition. The ``.seeds`` channel
is cooperative job reporting whose claims conformance evaluates later. Cut 3
§3's input-safety rules are enforced here: assessment runs require a frozen
spec, URL/accession inputs are acquisition rather than a run, and every
declared input must already be held.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import final

from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp

from beliefs import stored
from beliefs.adapter import (
    LOG_HANDLER_SCRIPT,
    SANDBOX_VENV,
    CapturedEnvironment,
    WorkflowDefinition,
    build_argv,
    capture_bundle,
    capture_closure,
    create_scratch_root,
    read_plan,
    read_realized_seeds,
    read_trace,
    require_executing_environment,
    run_engine,
    validate_entrypoint,
)
from beliefs.confinement import (
    BUNDLE_ROOT,
    HOME_DIR,
    HOSTNAME,
    OUTPUT_ROOT,
    TRACE_DIR,
    check_bundle_intact,
    check_closure_intact,
    fingerprint,
    launch_confined,
    materialize_snapshot,
    mount_plan,
    require_host,
    sandbox_environment,
)
from beliefs.errors import (
    CheckpointDeclarationUnmet,
    ConfinementRefusal,
    DefinitionPlanMismatch,
    MalformedClosure,
    MalformedRecord,
    PlanUnavailable,
    ScienceError,
)
from beliefs.identity import v1
from beliefs.recipe import (
    CONFINED_POLICY,
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentManifest,
    InstanceAttestation,
    Invocation,
    LaunchAttestation,
    Occurrence,
    PlannedJob,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    WorkflowDefinitionSnapshot,
    project_recipe,
    supported_policy,
)
from beliefs.report import (
    ActReport,
    AssessmentRunIntent,
    ImportedRecords,
    OperationIntent,
    RecordImportEntry,
    Registration,
    RunAttemptEntry,
    RunRefusal,
    _mint_report,
)
from beliefs.runrecord import OperationPort, publication_plan
from beliefs.sealed import sealed
from beliefs.spec import DATASET_EQUIVALENCE_RULE, FrozenSpec, NondeterminismContract, Seeded

__all__ = [
    "RunMinted",
    "RunRefused",
    "build_manifest",
    "check_checkpoint_declaration",
    "execute_assessment_run",
    "execute_production_run",
    "mint_run",
]

_INSTRUMENT = "beliefs.boundary/v1"


@sealed
@final
@dataclass(frozen=True)
class RunMinted:
    run: RunClosure
    intent: AssessmentRunIntent | OperationIntent
    registration: Registration


@sealed
@final
@dataclass(frozen=True)
class RunRefused:
    reason: str
    report: ActReport | None
    intent: AssessmentRunIntent | OperationIntent | None
    registration: Registration | None
    detail: str = ""
    """In-memory only: the refusing error's message. The durable ``RunRefusal``
    and the act-report carry the stable reason alone (design §8)."""


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _output_path(scratch: Path, logical_name: str) -> Path:
    root = scratch.resolve()
    path = (root / logical_name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise MalformedClosure(f"manifest missing output {logical_name!r}")
    return path


def build_manifest(declared_outputs: tuple[str, ...], scratch: Path) -> ResultManifest:
    """Digest exactly the declared output files, never scratch intermediates."""
    if type(declared_outputs) is not tuple or not all(type(name) is str for name in declared_outputs):
        raise MalformedClosure("manifest declarations must be a tuple of strings")
    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) for name in declared_outputs))


def mint_run(
    recipe: Recipe,
    manifest: ResultManifest,
    occurrence: Occurrence,
    scratch: Path,
) -> RunClosure:
    """Recheck manifest bytes at the final mint boundary."""
    if type(manifest) is not ResultManifest:
        raise MalformedClosure("mint_run requires a result manifest")
    for name, expected in manifest.outputs:
        if _digest(_output_path(scratch, name)) != expected:
            raise MalformedClosure(f"manifest digest mismatch for {name!r}")
    return RunClosure(recipe=recipe, result=manifest, occurrence=occurrence)


def _refused(
    reason: str,
    subject: str,
    actor: str,
    observer: str,
    started_at: str,
    intent: AssessmentRunIntent | OperationIntent | None = None,
    *,
    detail: str = "",
) -> RunRefused:
    token = intent.event_token if intent is not None else secrets.token_hex(16)
    report = _mint_report(
        operation="run-attempt",
        event_token=token,
        actor=actor,
        observer=observer,
        instrument=_INSTRUMENT,
        opened_at=started_at,
        closed_at=started_at,
        entries=(RunAttemptEntry(subject, RunRefusal(reason)),),
    )
    registration = Registration(token, report.identity()) if intent is not None else None
    return RunRefused(reason, report, intent, registration, detail)


def _report_plan(report: ActReport | None) -> tuple[CreateOp, ...]:
    if report is None:
        raise MalformedClosure("a refusal reached publication without a report")
    node = stored.act_report_node(report)
    return (
        CreateOp(
            path=f"act-report/{report.identity()}.md",
            content=node_to_markdown(node).encode("utf-8"),
        ),
    )


def _intent_wire(intent: AssessmentRunIntent | OperationIntent) -> bytes:
    if type(intent) is AssessmentRunIntent:
        return v1.encode(
            {
                "spec_identity": intent.spec_identity,
                "event_token": intent.event_token,
                "actor": intent.actor,
            }
        )
    return v1.encode(
        {
            "kind": intent.kind,
            "event_token": intent.event_token,
            "actor": intent.actor,
        }
    )


def _mint_import_report(
    intent: OperationIntent,
    *,
    subject: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    refs: tuple[str, ...],
    findings: tuple[str, ...],
) -> ActReport:
    if type(intent) is not OperationIntent or intent.kind != "import":
        raise MalformedRecord("an import report requires an import operation intent")
    return _mint_report(
        operation="import",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=(RecordImportEntry(subject, ImportedRecords(refs, findings)),),
    )


def _is_acquisition(address: str) -> bool:
    return "://" in address or address.startswith("accession:")


def _preflight(addresses: tuple[str, ...], held_inputs: Mapping[str, Path]) -> str | None:
    if any(_is_acquisition(address) for address in addresses):
        return "acquisition-not-a-run"
    if any(address not in held_inputs for address in addresses):
        return "input-not-held"
    return None


def _stage_inputs(addresses: tuple[str, ...], held_inputs: Mapping[str, Path], scratch: Path) -> Mapping[str, str]:
    inputs_dir = scratch / "inputs"
    inputs_dir.mkdir()
    identities: dict[str, str] = {}
    names: set[str] = set()
    for address in addresses:
        if address in identities:
            continue
        source = held_inputs[address]
        if not isinstance(source, Path) or not source.is_file():
            raise MalformedClosure(f"held input {address!r} is not a readable file")
        if source.name in names:
            raise MalformedClosure(f"held inputs collide at staging name {source.name!r}")
        names.add(source.name)
        staged = inputs_dir / source.name
        shutil.copy2(source, staged)
        identities[address] = _digest(staged)
    return identities


def _render_config(recipe: Recipe, snapshot: WorkflowDefinitionSnapshot) -> dict[str, str]:
    config = {key: str(value) for key, value in recipe.parameters.items()}
    if type(recipe.nondeterminism) is not Seeded:
        return config

    plan = recipe.nondeterminism.plan
    config["seed_roots"] = json.dumps(
        {stream: str(plan.roots[plan.stream_roots[stream]]) for stream in sorted(plan.streams)},
        sort_keys=True,
        separators=(",", ":"),
    )
    config["seed_derivation_rule"] = plan.derivation_rule
    return config


def check_checkpoint_declaration(
    snapshot: WorkflowDefinitionSnapshot,
    planned: tuple[PlannedJob, ...],
) -> None:
    declared = set(snapshot.checkpoint_expanded_families)
    if unknown := sorted(declared - set(snapshot.family_streams)):
        raise CheckpointDeclarationUnmet(
            f"checkpoint-expanded families the definition does not contain: {unknown}"
        )
    if declared and not any(job.is_checkpoint for job in planned):
        raise CheckpointDeclarationUnmet(
            f"checkpoint-expanded families {sorted(declared)} declared, but the plan contains no checkpoint"
        )


def _policy_refusal(policy: BoundaryPolicy) -> ConfinementRefusal | None:
    """Pre-intent: the whole definition must be known, and a confined request
    needs the host's substrate. Never a downgrade."""
    try:
        if supported_policy(policy) == CONFINED_POLICY:
            require_host()
    except ConfinementRefusal as refusal:
        return refusal
    return None


def _project(
    *,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    held: Mapping[str, str],
    code_identity: str,
    environment: EnvironmentManifest,
    definition: WorkflowDefinition,
    invocation: Invocation,
    boundary_policy: BoundaryPolicy,
) -> Recipe:
    if spec is not None:
        return project_recipe(
            spec,
            held=held,
            code_identity=code_identity,
            environment=environment,
            workflow_definition=definition.snapshot(),
            invocation=invocation,
            boundary_policy=boundary_policy,
        )
    if nondeterminism is None:
        raise MalformedClosure("a production recipe requires a nondeterminism contract")
    if any(entry.content != held[entry.dataset] for entry in inputs):
        raise MalformedClosure("a production input content identity does not match held bytes")
    return Recipe(
        shape="dataset-production",
        spec_identity=None,
        code_identity=code_identity,
        environment=environment,
        workflow_definition=definition.snapshot(),
        invocation=invocation,
        inputs=inputs,
        parameters=parameters,
        nondeterminism=nondeterminism,
        boundary_policy=boundary_policy,
        rule_bindings=((DATASET_EQUIVALENCE_RULE, "impl-dataset-eq-1"),),
    )


def _execute_run(
    *,
    intent: AssessmentRunIntent | OperationIntent,
    subject: str,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int,
    boundary_policy: BoundaryPolicy,
) -> RunMinted | RunRefused:
    try:
        scratch = create_scratch_root(scratch_base)
        bundle = scratch / "bundle"
        code_identity = capture_bundle(code_roots, bundle)
        captured = capture_closure()
        environment = captured.manifest
        captured_entrypoint = validate_entrypoint(bundle, entrypoint)
        if captured_entrypoint.read_bytes() != definition.snakefile:
            return _refused("definition-mismatch", subject, actor, observer, started_at, intent)

        addresses = (
            tuple(entry.dataset for entry in spec.input_roles)
            if spec is not None
            else tuple(entry.dataset for entry in inputs)
        )
        if boundary_policy == CONFINED_POLICY:
            return _execute_confined(
                intent=intent,
                subject=subject,
                spec=spec,
                inputs=inputs,
                parameters=parameters,
                nondeterminism=nondeterminism,
                definition=definition,
                addresses=addresses,
                held_inputs=held_inputs,
                captured=captured,
                scratch=scratch,
                bundle=bundle,
                code_identity=code_identity,
                captured_entrypoint=captured_entrypoint,
                entrypoint=entrypoint,
                targets=targets,
                declared_outputs=declared_outputs,
                actor=actor,
                observer=observer,
                started_at=started_at,
                host_realization=host_realization,
                scratch_base=scratch_base,
                cores=cores,
            )
        held = _stage_inputs(addresses, held_inputs, scratch)
        invocation = Invocation(
            entrypoint=entrypoint,
            targets=targets,
            bindings=("inputs", "parameters", "nondeterminism"),
            declared_outputs=declared_outputs,
        )
        recipe = _project(
            spec=spec,
            inputs=inputs,
            parameters=parameters,
            nondeterminism=nondeterminism,
            held=held,
            code_identity=code_identity,
            environment=environment,
            definition=definition,
            invocation=invocation,
            boundary_policy=boundary_policy,
        )

        config = _render_config(recipe, definition.snapshot())
        from beliefs.replay import definition_agrees_with_plan

        plan = recipe.nondeterminism.plan if type(recipe.nondeterminism) is Seeded else None
        if reason := definition_agrees_with_plan(definition.snapshot(), plan):
            raise DefinitionPlanMismatch(f"definition/plan mismatch: {reason}")

        planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))
        planning_handler = planning_dir / "handler.py"
        planning_events = planning_dir / "events.jsonl"
        planning_handler.write_text(LOG_HANDLER_SCRIPT)
        _stage_inputs(addresses, held_inputs, planning_dir)
        planning_argv = build_argv(
            interpreter=sys.executable,
            snakefile=str(captured_entrypoint),
            directory=str(planning_dir),
            targets=targets,
            config=config,
            log_handler=str(planning_handler),
            cores=cores,
            in_process_jobs=False,
            dry_run=True,
        )
        try:
            planning_returncode, _ = run_engine(
                planning_argv,
                cwd=planning_dir,
                env={**os.environ, "SCIENCE_TRACE_FILE": str(planning_events)},
            )
            if planning_returncode != 0:
                raise PlanUnavailable(f"the planning launch exited {planning_returncode}")
            planned_jobs = read_plan(planning_events)
            check_checkpoint_declaration(definition.snapshot(), planned_jobs)
        finally:
            shutil.rmtree(planning_dir, ignore_errors=True)
        planning_launch = LaunchAttestation(
            scratch_mapping=str(planning_dir),
            argv=planning_argv,
            rendered_config=tuple(sorted(config.items())),
            capabilities=(),
        )

        trace_dir = Path(tempfile.mkdtemp(prefix="trace-", dir=scratch.parent))
        handler = trace_dir / "handler.py"
        events = trace_dir / "events.jsonl"
        handler.write_text(LOG_HANDLER_SCRIPT)
        argv = build_argv(
            interpreter=sys.executable,
            snakefile=str(captured_entrypoint),
            directory=str(scratch),
            targets=targets,
            config=config,
            log_handler=str(handler),
            cores=cores,
            in_process_jobs=False,
        )
        env = {**os.environ, "SCIENCE_TRACE_FILE": str(events)}
        require_executing_environment(recipe.environment)
        returncode, _ = run_engine(argv, cwd=scratch, env=env)
        if returncode != 0:
            return _refused("execution-failed", subject, actor, observer, started_at, intent)

        trace = read_trace(events)
        realized_seeds = read_realized_seeds(scratch)
        execution_launch = LaunchAttestation(
            scratch_mapping=str(scratch),
            argv=argv,
            rendered_config=tuple(sorted(config.items())),
            capabilities=(),
        )
        receipt = BoundaryReceipt(planning=planning_launch, execution=execution_launch)
        occurrence = Occurrence(
            event_token=intent.event_token,
            started_at=started_at,
            actor=actor,
            host_realization=host_realization,
            trace=trace,
            planned=planned_jobs,
            realized_seeds=realized_seeds,
            receipt=receipt,
        )
        manifest = build_manifest(declared_outputs, scratch)
        run = mint_run(recipe, manifest, occurrence, scratch)
        return RunMinted(run, intent, Registration(intent.event_token, run.address()))
    except ConfinementRefusal as error:
        return _refused(getattr(error, "reason"), subject, actor, observer, started_at, intent, detail=str(error))  # noqa: B009 — ConfinementRefusal's base deliberately carries no `reason` (design §8); every raised instance is a named subclass that does
    except (ScienceError, OSError) as error:
        return _refused(str(error), subject, actor, observer, started_at, intent)


def _execute_confined(
    *,
    intent: AssessmentRunIntent | OperationIntent,
    subject: str,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    definition: WorkflowDefinition,
    addresses: tuple[str, ...],
    held_inputs: Mapping[str, Path],
    captured: CapturedEnvironment,
    scratch: Path,
    bundle: Path,
    code_identity: str,
    captured_entrypoint: Path,
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int,
) -> RunMinted | RunRefused:
    """Design §5.6 steps 3–5: the scratch root's ``out/`` is the host side of
    the output root; the closure is snapshotted, verified, bound and observed;
    the engine runs only after the gate; the post-exit check precedes every
    read. One capture (the caller's), one pre-bind observation (the bundle's
    fold, the snapshot verification ``materialize_snapshot`` performs, the
    inputs' fingerprint), one post-exit observation — no other pass over the
    closure. Raises ConfinementRefusal for the caller's except clause."""
    output_root = scratch / "out"
    output_root.mkdir()
    (output_root / TRACE_DIR).mkdir()
    (output_root / HOME_DIR).mkdir()
    held = _stage_inputs(addresses, held_inputs, output_root)
    invocation = Invocation(
        entrypoint=entrypoint,
        targets=targets,
        bindings=("inputs", "parameters", "nondeterminism"),
        declared_outputs=declared_outputs,
    )
    recipe = _project(
        spec=spec,
        inputs=inputs,
        parameters=parameters,
        nondeterminism=nondeterminism,
        held=held,
        code_identity=code_identity,
        environment=captured.manifest,
        definition=definition,
        invocation=invocation,
        boundary_policy=CONFINED_POLICY,
    )
    config = _render_config(recipe, definition.snapshot())
    handler = output_root / TRACE_DIR / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    trace_file = f"{OUTPUT_ROOT}/{TRACE_DIR}/events.jsonl"
    relative_entrypoint = captured_entrypoint.relative_to(bundle.resolve()).as_posix()
    inner_argv = build_argv(
        interpreter=f"{SANDBOX_VENV}/bin/python",
        snakefile=f"{BUNDLE_ROOT}/{relative_entrypoint}",
        directory=OUTPUT_ROOT,
        targets=targets,
        config=config,
        log_handler=f"{OUTPUT_ROOT}/{TRACE_DIR}/handler.py",
        cores=cores,
        in_process_jobs=True,
    )
    environment = sandbox_environment(trace_file)
    snapshot = materialize_snapshot(captured, scratch_base / "environments")
    plan = mount_plan(snapshot=snapshot, loader=captured.loader, bundle=bundle, output_root=output_root)
    check_bundle_intact(bundle, code_identity)
    inputs_before = fingerprint(output_root / "inputs")
    launched = launch_confined(plan=plan, environment=environment, inner_argv=inner_argv, captured=captured)
    check_closure_intact(bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=output_root / "inputs", inputs_fingerprint=inputs_before)
    if launched.returncode != 0:
        return _refused("execution-failed", subject, actor, observer, started_at, intent, detail=launched.output[-2000:])
    trace = read_trace(output_root / TRACE_DIR / "events.jsonl")
    realized_seeds = read_realized_seeds(output_root)
    execution_launch = LaunchAttestation(
        scratch_mapping=str(scratch),
        argv=inner_argv,
        rendered_config=tuple(sorted(config.items())),
        capabilities=launched.capabilities,
        instance=InstanceAttestation(
            namespaces=launched.facts.distinct,
            mounts=launched.facts.mounts,
            mount_plan_identity=plan.identity(),
            environment_identity=snapshot.name,
        ),
        rendered_environment=(
            *captured.rendered,
            *((f"env:{name}", "value", value) for name, value in environment),
            ("hostname", "value", HOSTNAME),
        ),
        mounts=plan.host_mapping(),
    )
    receipt = BoundaryReceipt(planning=execution_launch, execution=execution_launch)
    occurrence = Occurrence(
        event_token=intent.event_token,
        started_at=started_at,
        actor=actor,
        host_realization=host_realization,
        trace=trace,
        planned=tuple(
            PlannedJob(job.job_key(), job.rule, job.outputs, False)
            for job in trace
        ),
        realized_seeds=realized_seeds,
        receipt=receipt,
    )
    manifest = build_manifest(declared_outputs, output_root)
    run = mint_run(recipe, manifest, occurrence, output_root)
    return RunMinted(run, intent, Registration(intent.event_token, run.address()))


def execute_assessment_run(
    *,
    spec: object,
    port: OperationPort,
    boundary_policy: BoundaryPolicy,
    expected_recipe_identity: str | None = None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
) -> RunMinted | RunRefused:
    if type(spec) is not FrozenSpec:
        subject = spec if type(spec) is str else "absent"
        refused = _refused("no-frozen-spec", subject, actor, observer, started_at)
        port.execute(_report_plan(refused.report))
        return refused
    if reason := _preflight(tuple(entry.dataset for entry in spec.input_roles), held_inputs):
        refused = _refused(reason, spec.identity, actor, observer, started_at)
        port.execute(_report_plan(refused.report))
        return refused
    if refusal := _policy_refusal(boundary_policy):
        refused = _refused(getattr(refusal, "reason"), spec.identity, actor, observer, started_at, detail=str(refusal))  # noqa: B009
        port.execute(_report_plan(refused.report))
        return refused
    intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)
    fulfills = port.append_intent(_intent_wire(intent))
    result = _execute_run(
        intent=intent,
        subject=spec.identity,
        spec=spec,
        inputs=(),
        parameters={},
        nondeterminism=None,
        definition=definition,
        code_roots=code_roots,
        held_inputs=held_inputs,
        entrypoint=entrypoint,
        targets=targets,
        declared_outputs=declared_outputs,
        actor=actor,
        observer=observer,
        started_at=started_at,
        host_realization=host_realization,
        scratch_base=scratch_base,
        cores=cores,
        boundary_policy=supported_policy(boundary_policy),
    )
    if (
        type(result) is RunMinted
        and expected_recipe_identity is not None
        and result.run.recipe.identity() != expected_recipe_identity
    ):
        result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run)
        port.execute_fulfilling(plan, fulfills)
    else:
        port.execute_fulfilling(_report_plan(result.report), fulfills)
    return result


def execute_production_run(
    *,
    inputs: tuple[RecipeInput, ...],
    port: OperationPort,
    boundary_policy: BoundaryPolicy,
    expected_recipe_identity: str | None = None,
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
) -> RunMinted | RunRefused:
    if type(inputs) is not tuple or any(type(entry) is not RecipeInput for entry in inputs):
        refused = _refused("malformed-inputs", "absent", actor, observer, started_at)
        port.execute(_report_plan(refused.report))
        return refused
    if reason := _preflight(tuple(entry.dataset for entry in inputs), held_inputs):
        refused = _refused(reason, "absent", actor, observer, started_at)
        port.execute(_report_plan(refused.report))
        return refused
    if refusal := _policy_refusal(boundary_policy):
        refused = _refused(getattr(refusal, "reason"), "absent", actor, observer, started_at, detail=str(refusal))  # noqa: B009
        port.execute(_report_plan(refused.report))
        return refused
    intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)
    fulfills = port.append_intent(_intent_wire(intent))
    result = _execute_run(
        intent=intent,
        subject="absent",
        spec=None,
        inputs=inputs,
        parameters=parameters,
        nondeterminism=nondeterminism,
        definition=definition,
        code_roots=code_roots,
        held_inputs=held_inputs,
        entrypoint=entrypoint,
        targets=targets,
        declared_outputs=declared_outputs,
        actor=actor,
        observer=observer,
        started_at=started_at,
        host_realization=host_realization,
        scratch_base=scratch_base,
        cores=cores,
        boundary_policy=supported_policy(boundary_policy),
    )
    if (
        type(result) is RunMinted
        and expected_recipe_identity is not None
        and result.run.recipe.identity() != expected_recipe_identity
    ):
        result = _refused("recipe-identity-mismatch", "absent", actor, observer, started_at, intent)
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run)
        port.execute_fulfilling(plan, fulfills)
    else:
        port.execute_fulfilling(_report_plan(result.report), fulfills)
    return result
