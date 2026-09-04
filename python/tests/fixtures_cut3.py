"""Shared cut-3 fixtures: value builders and held Snakefile definitions."""

import json
from decimal import Decimal
from hashlib import sha256
from typing import cast

from authority import FULL

from beliefs.assess import run_record
from beliefs.boundary import execute_assessment_run, execute_production_run
from beliefs.closure import RetractionEnumeration
from beliefs.lineage import LineageSnapshot
from beliefs.recipe import (
    MINIMAL_POLICY,
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentManifest,
    Invocation,
    LaunchAttestation,
    Occurrence,
    PlannedJob,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    TraceJob,
    WorkflowDefinitionSnapshot,
    job_key,
)

# Tests build fixture values through the private constructor deliberately —
# the public surface must not offer one, and Task 11 pins that (T1).
from beliefs.report import Entry, LocatorEntry, PublishedObservation, RunAttemptEntry, RunRefusal, _mint_report
from beliefs.spec import (
    Deterministic,
    RealizedSeeds,
    RuleFixture,
    RuleImplementation,
    Seeded,
    SeedPlan,
    SpecDraft,
    SpecInput,
    freeze,
)

D_IN = "sha256:" + "aa" * 32
D_OUT = "sha256:" + "bb" * 32
DATA_ADDRESS = "dataset:sha256:" + "aa" * 32
READS_ADDRESS = "dataset:sha256:" + "ee" * 32
POLICY = BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")


def seed_plan(streams=("model-initialization",), roots=None, stream_roots=None) -> SeedPlan:
    roots = roots if roots is not None else {"root-a": 11}
    stream_roots = stream_roots if stream_roots is not None else {s: "root-a" for s in streams}
    return SeedPlan(derivation_rule="seed-derivation/v1", streams=streams, roots=roots, stream_roots=stream_roots)


def spec_rules() -> dict[str, RuleImplementation]:
    return {
        "median-difference/v1": RuleImplementation(
            identity="impl-interp-1",
            evaluate=lambda manifest: {"outcome": "supported"},
            fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
        ),
        "content-identity-equality/v1": RuleImplementation(
            identity="impl-eq-1",
            evaluate=lambda a, b: "passed" if a == b else "failed",
            fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),),
        ),
    }


def spec_draft(**overrides) -> SpecDraft:
    fields = {
        "target": "prop-1",
        "estimand": "the effect of x on y",
        "method": "fit the model",
        "assumptions": "iid draws",
        "falsification": "a null effect",
        "input_roles": (SpecInput(role="observes", dataset=DATA_ADDRESS),),
        "applicability": "the sampled population",
        "interpretation_rule": "median-difference/v1",
        "equivalence_rule": "content-identity-equality/v1",
        "parameters": {"alpha": Decimal("0.05")},
        "nondeterminism": Seeded(plan=seed_plan()),
    }
    fields.update(overrides)
    return SpecDraft(**fields)


def seeded() -> Seeded:
    return Seeded(
        plan=SeedPlan(
            derivation_rule="seed-derivation/v1",
            streams=("model-initialization",),
            roots={"root-a": 11},
            stream_roots={"model-initialization": "root-a"},
        )
    )


def invocation(**overrides) -> Invocation:
    fields = {
        "entrypoint": "code/workflow/Snakefile",
        "targets": ("outputs/result.txt",),
        "bindings": ("inputs", "parameters", "nondeterminism"),
        "declared_outputs": ("outputs/result.txt",),
    }
    fields.update(overrides)
    return Invocation(**fields)


def recipe(**overrides) -> Recipe:
    fields = {
        "shape": "assessment",
        "spec_identity": "spec-" + "11" * 8,
        "code_identity": "sha256:" + "cc" * 32,
        "environment": EnvironmentManifest(artifacts=(("/science/env/python/bin/python3", "file", "sha256:" + "dd" * 32),)),
        "workflow_definition": definition().snapshot(),
        "invocation": invocation(),
        "inputs": (RecipeInput(role="observes", dataset="dataset:sha256:" + "ff" * 32, content=D_IN),),
        "parameters": {"alpha": Decimal("0.05")},
        "nondeterminism": seeded(),
        "boundary_policy": POLICY,
        "rule_bindings": (
            ("content-identity-equality/v1", "impl-eq-1"),
            ("median-difference/v1", "impl-interp-1"),
        ),
    }
    fields.update(overrides)
    return Recipe(**fields)


def occurrence(**overrides) -> Occurrence:
    transform_key = TraceJob(
        job_id="0",
        rule="transform",
        wildcards=(),
        inputs=("inputs/data.txt",),
        outputs=("outputs/result.txt",),
    ).job_key()
    fields = {
        "event_token": "tok-1",
        "started_at": "2026-08-12T00:00:00Z",
        "actor": "tester",
        "host_realization": "host-a",
        "trace": (
            TraceJob(
                job_id="0",
                rule="transform",
                wildcards=(),
                inputs=("inputs/data.txt",),
                outputs=("outputs/result.txt",),
            ),
        ),
        "planned": (
            PlannedJob(
                job_key=transform_key,
                family="transform",
                outputs=("outputs/result.txt",),
                is_checkpoint=False,
            ),
        ),
        "target_keys": (transform_key,),
        "realized_seeds": RealizedSeeds(seeds={transform_key: {"model-initialization": 7}}),
        "receipt": BoundaryReceipt(
            planning=LaunchAttestation(scratch_mapping="scratch-mount-a", argv=("snakemake",), rendered_config=()),
            execution=LaunchAttestation(scratch_mapping="scratch-mount-a", argv=("snakemake",), rendered_config=()),
        ),
    }
    fields.update(overrides)
    return Occurrence(**fields)


def closure(**overrides) -> RunClosure:
    fields = {
        "recipe": recipe(),
        "result": ResultManifest(outputs=(("outputs/result.txt", D_OUT),)),
        "occurrence": occurrence(),
    }
    fields.update(overrides)
    return RunClosure(**fields)


def traced(family, wildcards, job_id=None):
    pairs = tuple(sorted(wildcards.items()))
    return TraceJob(
        job_id=job_id or f"{family}-{len(pairs)}",
        rule=family,
        wildcards=pairs,
        inputs=(),
        outputs=(),
    )


def traced_from_key(key):
    parsed = json.loads(key)
    return traced(parsed["rule"], parsed["wildcards"])


def closure_with(
    *,
    nondeterminism=None,
    family_streams=None,
    realized=None,
    trace=None,
    planned=None,
    expanded=(),
    target_keys=None,
    targets=None,
    outputs=(("out.txt", D_OUT),),
):
    """Build a closure from record parts for arms that need no engine."""
    families = family_streams if family_streams is not None else {}
    jobs = trace if trace is not None else (traced("transform", {}),)
    snapshot = WorkflowDefinitionSnapshot(
        snakefile_digest=D_IN,
        family_streams=families,
        checkpoint_expanded_families=expanded,
    )
    built = recipe(
        nondeterminism=nondeterminism or Deterministic(),
        workflow_definition=snapshot,
        invocation=invocation(
            targets=targets or (),
            declared_outputs=tuple(name for name, _ in outputs),
        ),
    )
    return RunClosure(
        recipe=built,
        result=ResultManifest(outputs=tuple(outputs)),
        occurrence=occurrence(
            trace=jobs,
            planned=(
                planned
                if planned is not None
                else tuple(
                    PlannedJob(
                        job_key=job.job_key(),
                        family=job.rule,
                        outputs=job.outputs,
                        is_checkpoint=False,
                    )
                    for job in jobs
                )
            ),
            target_keys=(
                target_keys
                if target_keys is not None
                else ()
            ),
            realized_seeds=RealizedSeeds(seeds=realized or {}),
        ),
    )


def planned(family, outputs=(), is_checkpoint=False, wildcards=()):
    return PlannedJob(
        job_key=job_key(family, tuple(wildcards)),
        family=family,
        outputs=tuple(outputs),
        is_checkpoint=is_checkpoint,
    )


def closure_kwargs(assessments, runs):
    return {
        "proposition": "prop-1",
        "assessments": assessments,
        "runs": runs,
        "verifications": (),
        "snapshot": LineageSnapshot(roots=(), bases={}, producers={}),
        "producer_snapshot_identity": "snap-1",
        "retractions": RetractionEnumeration(found=(), coverage=("supplied",)),
        "consulted": (("science", "base-1"),),
        "binding": ("science.belief.v1", "impl-1"),
    }


def runs_for(closures):
    return {run.address(): run_record(run) for run in closures}


def interp(outcome="supported", fail=False):
    def evaluate(manifest):
        if fail:
            raise ValueError("unparseable payload")
        return {"outcome": outcome, "estimate": "0.4", "uncertainty": "0.1"}

    return {"impl-interp-1": RuleImplementation(identity="impl-interp-1", evaluate=evaluate, fixtures=())}


def result_sensitive():
    # Outcome keyed to the RESULT's bytes: the output digest's low bit
    # decides. Deterministic, and a test can compute its expectation from the
    # manifest it holds — which is what makes the outcome's derivation, not
    # merely the identity, checkable (R22).
    def evaluate(manifest):
        parity = int(manifest.outputs[0][1].split(":", 1)[1], 16) % 2
        return {
            "outcome": "supported" if parity == 0 else "refuted",
            "estimate": "0.4",
        }

    return {"impl-interp-1": RuleImplementation(identity="impl-interp-1", evaluate=evaluate, fixtures=())}


def report(**overrides):
    fields: dict[str, object] = {
        "operation": "acquisition",
        "event_token": "tok-1",
        "actor": "tester",
        "observer": "observer-1",
        "instrument": "instrument-1",
        "opened_at": "2026-08-12T00:00:00Z",
        "closed_at": "2026-08-12T00:05:00Z",
        "entries": (
            LocatorEntry(subject="url://example/data", outcome=PublishedObservation(ref="obs-1")),
            RunAttemptEntry(subject="absent", outcome=RunRefusal(missing_member="spec_identity")),
        ),
    }
    fields.update(overrides)
    return _mint_report(
        operation=cast(str, fields["operation"]),
        event_token=cast(str, fields["event_token"]),
        actor=cast(str, fields["actor"]),
        observer=cast(str, fields["observer"]),
        instrument=cast(str, fields["instrument"]),
        opened_at=cast(str, fields["opened_at"]),
        closed_at=cast(str, fields["closed_at"]),
        entries=cast(tuple[Entry, ...], fields["entries"]),
    )


SNAKEFILE_DETERMINISTIC = """\
import pathlib, random
from beliefs.seeds import bind

seed = bind(config)

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        value = seed(rule, wildcards, "model-initialization")
        rng = random.Random(value)  # the computation USES the seed it reports
        salt = "".join(rng.choice("0123456789abcdef") for _ in range(8))
        text = pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text(text.upper() + ":" + salt)
"""

# Disobeys its rendered configuration: the workflow itself uses and rewrites
# its claim to seed+1 during execution. This is a genuinely violating closure,
# not fixture post-processing — R16's mint arm and R21 negative (e).
SNAKEFILE_SEED_VIOLATING = SNAKEFILE_DETERMINISTIC.replace(
    "from beliefs.seeds import bind",
    "import json\nfrom beliefs.seeds import bind, record_digest_of",
).replace(
    '        value = seed(rule, wildcards, "model-initialization")',
    '''        value = seed(rule, wildcards, "model-initialization")
        claim = next(pathlib.Path(".seeds").glob("*.json"))
        record = json.loads(claim.read_text())
        claim.unlink()
        value += 1
        record["seed"] = value
        (claim.parent / f"{record_digest_of(record)}.json").write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")))''',
)

# Byte-nondeterministic output, urandom staying inside the scratch root. Used
# with a stochastic-unseeded production recipe (R11) and, declared
# deterministic, as the honest way to obtain a failing assessment replay (R8).
SNAKEFILE_NONDETERMINISTIC = """\
import os, pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        text = pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text(text.upper() + os.urandom(8).hex())
"""

# A seed-free deterministic production transform: a Deterministic contract
# renders no seed config, so the production default cannot read one.
SNAKEFILE_PRODUCTION = """\
import pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        text = pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text(text.upper())
"""

SNAKEFILE_TWO_NAMES = """\
import pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/a.txt", "outputs/b.txt"
    run:
        text = pathlib.Path(input[0]).read_text().upper()
        pathlib.Path(output[0]).write_text(text)
        pathlib.Path(output[1]).write_text(text)
"""

# Writes a random-content scratch intermediate beside the declared output —
# R21's intermediates-excluded arm.
SNAKEFILE_SCRATCHY = SNAKEFILE_DETERMINISTIC.replace(
    'pathlib.Path(output[0]).write_text(text.upper() + ":" + salt)',
    'pathlib.Path("scratch.tmp").write_text(__import__("os").urandom(8).hex())\n'
    '        pathlib.Path(output[0]).write_text(text.upper() + ":" + salt)',
)


def definition(
    snakefile: str = SNAKEFILE_DETERMINISTIC,
    family_streams=None,
    checkpoint_expanded_families=(),
):
    from beliefs.adapter import WorkflowDefinition

    streams = family_streams if family_streams is not None else {"transform": ("model-initialization",)}
    return WorkflowDefinition(
        snakefile=snakefile.encode("utf-8"),
        family_streams=streams,
        checkpoint_expanded_families=checkpoint_expanded_families,
    )


class MemoryPort:
    """The shared no-I/O port for value-width unit tests."""

    authority = FULL

    def append_intent(self, payload: bytes) -> str:
        return sha256(payload).hexdigest()

    def execute(self, plan) -> None:
        pass

    def execute_fulfilling(self, plan, fulfills: str) -> None:
        pass


MEMORY_PORT = MemoryPort()


def memory_assessment(*args, **kwargs):
    return run_assessment(*args, port=MEMORY_PORT, **kwargs)


def memory_production(*args, **kwargs):
    return run_production(*args, port=MEMORY_PORT, **kwargs)


def memory_replay(*args, **kwargs):
    return replay_of(*args, port=MEMORY_PORT, **kwargs)


def stage(tmp_path, *, snakefile=SNAKEFILE_DETERMINISTIC, data="hello"):
    code = tmp_path / "code"
    (code / "workflow").mkdir(parents=True)
    (code / "workflow" / "Snakefile").write_bytes(snakefile.encode())
    (code / "helper.py").write_text("VALUE = 1\n")
    held = tmp_path / "held"
    held.mkdir()
    (held / "data.txt").write_text(data)
    (held / "palette.txt").write_text("a fixture auxiliary input")
    return code, held


def run_assessment(
    tmp_path,
    *,
    port,
    boundary_policy=MINIMAL_POLICY,
    snakefile=SNAKEFILE_DETERMINISTIC,
    spec=None,
    definition_override=None,
    started_at="2026-08-12T00:00:00Z",
    host_realization="host-a",
    cores=1,
    data="hello",
    held_inputs=None,
    scratch_base=None,
):
    code, held = stage(tmp_path, snakefile=snakefile, data=data)
    spec = spec if spec is not None else freeze(spec_draft(), held_rules=spec_rules())
    if held_inputs is not None:
        observed = spec.input_roles[0].dataset
        (held / "data.txt").write_bytes(held_inputs[observed].read_bytes())
        supplied = {**held_inputs, observed: held / "data.txt"}
    else:
        supplied = {
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        }
    return execute_assessment_run(
        spec=spec,
        port=port,
        boundary_policy=boundary_policy,
        definition=(definition_override if definition_override is not None else definition(snakefile=snakefile)),
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at=started_at,
        host_realization=host_realization,
        scratch_base=scratch_base if scratch_base is not None else tmp_path / "scratch",
        cores=cores,
    )


def run_production(
    tmp_path,
    *,
    port,
    boundary_policy=MINIMAL_POLICY,
    snakefile=SNAKEFILE_PRODUCTION,
    inputs=None,
    parameters=None,
    nondeterminism=None,
    targets=None,
    declared_outputs=None,
    held_inputs=None,
    started_at="2026-08-12T00:00:00Z",
    host_realization="host-a",
    cores=1,
    data="hello",
    definition_override=None,
):
    code, held = stage(tmp_path, snakefile=snakefile, data=data)
    supplied = (
        held_inputs
        if held_inputs is not None
        else {
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        }
    )
    authored = (
        inputs
        if inputs is not None
        else (
            RecipeInput(
                role="transforms",
                dataset=DATA_ADDRESS,
                content="sha256:" + sha256(supplied[DATA_ADDRESS].read_bytes()).hexdigest(),
            ),
        )
    )
    contract = nondeterminism if nondeterminism is not None else Deterministic()
    family_streams = {"transform": contract.plan.streams} if isinstance(contract, Seeded) else {}
    return execute_production_run(
        inputs=authored,
        parameters=parameters if parameters is not None else {},
        nondeterminism=contract,
        port=port,
        boundary_policy=boundary_policy,
        definition=(
            definition_override
            if definition_override is not None
            else definition(snakefile=snakefile, family_streams=family_streams)
        ),
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=targets if targets is not None else ("outputs/result.txt",),
        declared_outputs=(declared_outputs if declared_outputs is not None else ("outputs/result.txt",)),
        observer="observer-1",
        started_at=started_at,
        host_realization=host_realization,
        scratch_base=tmp_path / "scratch",
        cores=cores,
    )


def replay_of(
    original,
    tmp_path,
    *,
    port,
    snakefile=SNAKEFILE_DETERMINISTIC,
    host_realization="host-a",
    held_inputs=None,
    scratch_base=None,
    cores=1,
):
    from beliefs.replay import replay

    code, held = stage(tmp_path, snakefile=snakefile)
    supplied = (
        held_inputs
        if held_inputs is not None
        else {
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        }
    )
    spec = None
    if original.run.recipe.shape == "assessment":
        spec = freeze(
            spec_draft(nondeterminism=original.run.recipe.nondeterminism),
            held_rules=spec_rules(),
        )
    family_streams = (
        {"transform": original.run.recipe.nondeterminism.plan.streams}
        if isinstance(original.run.recipe.nondeterminism, Seeded)
        else {}
    )
    return replay(
        original,
        port=port,
        spec=spec,
        definition=definition(
            snakefile=snakefile,
            family_streams=family_streams,
        ),
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=original.run.recipe.invocation.targets,
        declared_outputs=original.run.recipe.invocation.declared_outputs,
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization=host_realization,
        scratch_base=scratch_base if scratch_base is not None else tmp_path / "scratch",
        cores=cores,
    )
