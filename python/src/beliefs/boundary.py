"""Begin, execute, capture, and mint runs through the minimal adapter.

The scratch root is staging, not confinement. The boundary renders
configuration, environment, and argv, never the workflow definition. The
``.seeds`` channel is cooperative job reporting whose claims conformance
evaluates later. Cut 3 §3's input-safety rules are enforced here: assessment
runs require a frozen spec, URL/accession inputs are acquisition rather than a
run, and every declared input must already be held.
"""

from __future__ import annotations

import os
import secrets
import shutil
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
    WorkflowDefinition,
    build_argv,
    capture_bundle,
    capture_environment,
    create_scratch_root,
    read_realized_seeds,
    read_trace,
    require_executing_environment,
    run_engine,
    validate_entrypoint,
)
from beliefs.errors import MalformedClosure, MalformedRecord, ScienceError
from beliefs.identity import v1
from beliefs.recipe import (
    BoundaryPolicy,
    BoundaryReceipt,
    Invocation,
    Occurrence,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    project_recipe,
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
from beliefs.spec import (
    DATASET_EQUIVALENCE_RULE,
    SEED_DERIVATION_V1,
    FrozenSpec,
    NondeterminismContract,
    Seeded,
    derive_seed,
)

__all__ = [
    "RunMinted",
    "RunRefused",
    "build_manifest",
    "execute_assessment_run",
    "execute_production_run",
    "mint_run",
]

_POLICY = BoundaryPolicy(
    identity="boundary-policy/minimal-v1",
    scope_rule="scope-derivation/v1",
)
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
    return RunRefused(reason, report, intent, registration)


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


def _render_config(recipe: Recipe, definition: WorkflowDefinition) -> dict[str, str]:
    config = {key: str(value) for key, value in recipe.parameters.items()}
    if type(recipe.nondeterminism) is not Seeded:
        return config

    plan = recipe.nondeterminism.plan
    declared_streams = {stream for streams in definition.family_streams.values() for stream in streams}
    if declared_streams != set(plan.streams):
        raise MalformedClosure("workflow family streams do not match the seed plan")
    if plan.derivation_rule != SEED_DERIVATION_V1:
        raise MalformedClosure(f"unsupported seed derivation rule {plan.derivation_rule!r}")
    for family, streams in definition.family_streams.items():
        for stream in streams:
            key = "seed_" + stream.replace("-", "_")
            value = str(
                derive_seed(
                    plan.roots[plan.stream_roots[stream]],
                    family,
                    stream,
                )
            )
            if key in config and config[key] != value:
                raise MalformedClosure(f"rendered config key {key!r} has conflicting values")
            config[key] = value
    return config


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
) -> RunMinted | RunRefused:
    try:
        scratch = create_scratch_root(scratch_base)
        bundle = scratch / "bundle"
        code_identity = capture_bundle(code_roots, bundle)
        environment = capture_environment()
        captured_entrypoint = validate_entrypoint(bundle, entrypoint)
        if captured_entrypoint.read_bytes() != definition.snakefile:
            return _refused("definition-mismatch", subject, actor, observer, started_at, intent)

        addresses = (
            tuple(entry.dataset for entry in spec.input_roles)
            if spec is not None
            else tuple(entry.dataset for entry in inputs)
        )
        held = _stage_inputs(addresses, held_inputs, scratch)
        invocation = Invocation(
            entrypoint=entrypoint,
            targets=targets,
            bindings=("inputs", "parameters", "nondeterminism"),
            declared_outputs=declared_outputs,
        )
        if spec is not None:
            recipe = project_recipe(
                spec,
                held=held,
                code_identity=code_identity,
                environment=environment,
                workflow_definition_identity=definition.identity(),
                invocation=invocation,
                boundary_policy=_POLICY,
            )
        else:
            if nondeterminism is None:
                raise MalformedClosure("a production recipe requires a nondeterminism contract")
            if any(entry.content != held[entry.dataset] for entry in inputs):
                raise MalformedClosure("a production input content identity does not match held bytes")
            recipe = Recipe(
                shape="dataset-production",
                spec_identity=None,
                code_identity=code_identity,
                environment=environment,
                workflow_definition_identity=definition.identity(),
                invocation=invocation,
                inputs=inputs,
                parameters=parameters,
                nondeterminism=nondeterminism,
                boundary_policy=_POLICY,
                rule_bindings=((DATASET_EQUIVALENCE_RULE, "impl-dataset-eq-1"),),
            )

        config = _render_config(recipe, definition)
        trace_dir = Path(tempfile.mkdtemp(prefix="trace-", dir=scratch.parent))
        handler = trace_dir / "handler.py"
        events = trace_dir / "events.jsonl"
        handler.write_text(LOG_HANDLER_SCRIPT)
        argv = build_argv(
            snakefile=captured_entrypoint,
            scratch=scratch,
            targets=targets,
            config=config,
            log_handler=handler,
            cores=cores,
        )
        env = {**os.environ, "SCIENCE_TRACE_FILE": str(events)}
        require_executing_environment(recipe.environment)
        returncode, _ = run_engine(argv, cwd=scratch, env=env)
        if returncode != 0:
            return _refused("execution-failed", subject, actor, observer, started_at, intent)

        trace = read_trace(events)
        realized_seeds = read_realized_seeds(scratch)
        receipt = BoundaryReceipt(
            scratch_mapping=str(scratch),
            argv=argv,
            rendered_config=tuple(sorted(config.items())),
            capabilities=(),
        )
        occurrence = Occurrence(
            event_token=intent.event_token,
            started_at=started_at,
            actor=actor,
            host_realization=host_realization,
            trace=trace,
            realized_seeds=realized_seeds,
            receipt=receipt,
        )
        manifest = build_manifest(declared_outputs, scratch)
        run = mint_run(recipe, manifest, occurrence, scratch)
        return RunMinted(run, intent, Registration(intent.event_token, run.address()))
    except (ScienceError, OSError) as error:
        return _refused(str(error), subject, actor, observer, started_at, intent)


def execute_assessment_run(
    *,
    spec: object,
    port: OperationPort,
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
