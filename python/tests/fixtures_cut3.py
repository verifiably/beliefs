"""Shared fixtures: value builders and held Snakefile definitions."""

import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import cast

from authority import FULL
from dataset_fixtures import dataset_ref
from profiles import BASE

from beliefs.applicability import Applicability, build_applicability
from beliefs.assess import run_record
from beliefs.boundary import HeldTree, execute_assessment_run, execute_production_run
from beliefs.claim import Referent, build_claim
from beliefs.closure import RetractionEnumeration
from beliefs.contract import parse_domain_contract
from beliefs.contract.document import load_document
from beliefs.dependencies import dependency_closure
from beliefs.estimand import Control, MeasuredBinding, OutputSpec, RoleTermLevels, ValueReference, build_estimand
from beliefs.lineage import LineageSnapshot
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Procedure
from beliefs.profile import compile_profile, shipped_base_contract
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
# the public surface must not offer one, and a test pins that.
from beliefs.report import Entry, LocatorEntry, PublishedObservation, RunAttemptEntry, RunRefusal, _mint_report
from beliefs.resolution import build_snapshot
from beliefs.runrecord import GuardedCommit
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
from beliefs.target import AssessedTarget, Standing
from beliefs.tree import TreeMember, make_tree, object_path, tree_digest, tree_file_bytes

D_IN = "sha256:" + "aa" * 32
D_OUT = "sha256:" + "bb" * 32
DATA_ADDRESS = dataset_ref("data")
READS_ADDRESS = dataset_ref("reads")
POLICY = BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")

_TESTING = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "testing.yaml"
TESTING_PROFILE = compile_profile(
    shipped_base_contract(),
    [
        parse_domain_contract(
            load_document(_TESTING, source=str(_TESTING)),
            source=str(_TESTING),
            base=shipped_base_contract(),
            predecessor=None,
        )
    ],
)
TESTING_CLAIM = build_claim(
    TESTING_PROFILE,
    operator="testing/affects",
    roles={"cause": Referent("testing/entity", "EX:gene-x"), "effect": Referent("testing/outcome", "EX:pheno-y")},
    layer="causal",
    form="polar",
    polarity="positive",
)
UNCONSULTED = build_snapshot(readable={})


class FixtureRecords:
    """Explicit held measurement records used by the shared spec fixture."""

    def __init__(self):
        self.nodes = {}

    def put_procedure(self, procedure):
        from beliefs import stored

        node = stored.procedure_node(procedure)
        self.nodes[node.id] = node
        return node.id

    def holds(self, id):
        return id in self.nodes

    def read(self, id):
        return self.nodes[id]

    def retraction_in_force(self, id):
        return False

    def observation_held(self, digest):
        return False

    def crosswalks(self, a, b):
        return ()


MEASUREMENT_RECORDS = FixtureRecords()
OBSERVABLE = Observable("testing/abundance", "testing/entity")
YIELDING_PROCEDURE = MEASUREMENT_RECORDS.put_procedure(
    Procedure(
        kind="testing/assay",
        name="Transcript assay",
        definition="Fixture measurement.",
        yields=(OBSERVABLE,),
        scale=None,
        validated_in={},
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters={},
        external=None,
    )
)
ESTIMATOR_PROCEDURE = MEASUREMENT_RECORDS.put_procedure(
    Procedure(
        kind="testing/estimator",
        name="Difference estimator",
        definition="Fixture analysis.",
        yields=(),
        scale=None,
        validated_in={},
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters={},
        external=None,
    )
)
RESPONSE = MeasuredBinding(
    "cause",
    None,
    Measure(OBSERVABLE, "testing/tpm", None, "ratio", "level", "testing/identity", YIELDING_PROCEDURE),
    None,
    None,
)


def freeze_context(interpretation_rule="median-difference/v1"):
    return {
        "profile": TESTING_PROFILE,
        "claim": TESTING_CLAIM,
        "records": MEASUREMENT_RECORDS,
        "rule_procedures": {interpretation_rule: ESTIMATOR_PROCEDURE},
    }


def typed_estimand(*, profile=TESTING_PROFILE, claim=TESTING_CLAIM, **overrides):
    fields = {
        "form": "contrast",
        "functional": "testing/difference-of-means",
        "bindings": {
            "response": RESPONSE,
            "grouping": RoleTermLevels(
                "cause", None, (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd"))
            ),
        },
        "outputs": {"estimate": OutputSpec("response-difference", "real")},
        "reference": ValueReference(Decimal(0)),
        "control": Control("testing/randomized", (), "testing/independent-groups", "testing/cohort-enrolment"),
        "uncertainty": "interval",
        "assumptions": (),
        "calibration": None,
        "applicability": Applicability({}),
        "records": MEASUREMENT_RECORDS,
    }
    fields.update(overrides)
    estimand, _receipt = build_estimand(profile, claim, snapshot=UNCONSULTED, **fields)
    return estimand


def typed_applicability(values=None):
    applicability, _receipt = build_applicability(
        TESTING_PROFILE, TESTING_CLAIM, {} if values is None else values, snapshot=UNCONSULTED
    )
    return applicability


def typed_target(*, estimand=None, applicability=None, standing: Standing = "empirical", model=None, dependencies=None):
    estimand = typed_estimand() if estimand is None else estimand
    applicability = typed_applicability() if applicability is None else applicability
    if dependencies is None:
        roots = [e.id for e in estimand.dependencies] + list(applicability.rule_ids())
        if model is not None:
            roots.append(model)
        dependencies = dependency_closure(roots, MEASUREMENT_RECORDS, TESTING_PROFILE)
    return AssessedTarget(estimand, applicability, dependencies, model, standing)


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
        "estimand": typed_estimand(),
        "method": "fit the model",
        "assumptions": "iid draws",
        "falsification": "a null effect",
        "input_roles": (SpecInput(role="observes", dataset=DATA_ADDRESS, mode="observation"),),
        "applicability": typed_applicability(),
        "interpretation_rule": "median-difference/v1",
        "equivalence_rule": "content-identity-equality/v1",
        "parameters": {"alpha": Decimal("0.05")},
        "nondeterminism": Seeded(plan=seed_plan()),
        "registers": (),
        "standing": "empirical",
        "model": None,
    }
    fields.update(overrides)
    return SpecDraft(**fields)


def carry_registers(writer):
    """A fixture corpus carries a one-entry assumptions register for each
    activated domain contract (design section 9.2, R9), so `register-missing` is
    not every audit's finding. A test whose subject is the register hygiene report
    itself uses a corpus without one."""
    from beliefs import stored
    from beliefs.register import AssumptionsRegister, RegisterEntry

    for id in (YIELDING_PROCEDURE, ESTIMATOR_PROCEDURE):
        node = MEASUREMENT_RECORDS.read(id)
        if node.facets["procedure"]["kind"] in writer.profile.procedure_kinds and not writer.read_view.holds(id):
            writer.add(node)
    for namespace, identity in writer.profile.activated_contracts.items():
        if namespace == "coordination":
            continue
        sort = min(term for term, declared in writer.profile.sorts.items() if declared.contract == namespace)
        entry = RegisterEntry("fixture collapses", "fixture licenses", "fixture leaves unestablished")
        register = AssumptionsRegister(f"{namespace}:{identity}", None, {f"sort:{sort}": entry})
        writer.add(stored.assumptions_register_node(register))
    return writer


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
        "environment": EnvironmentManifest(
            artifacts=(("/science/env/python/bin/python3", "file", "sha256:" + "dd" * 32),)
        ),
        "workflow_definition": definition().snapshot(),
        "invocation": invocation(),
        "inputs": (RecipeInput(role="observes", dataset=dataset_ref("closure-input"), content=D_IN),),
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
            target_keys=(target_keys if target_keys is not None else ()),
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
        "observed_facets": (),
    }


def runs_for(closures):
    return {run.address(): run_record(run) for run in closures}


def interp(outcome="supported", fail=False):
    def evaluate(manifest):
        if fail:
            raise ValueError("unparseable payload")
        return {
            "outcome": outcome,
            "estimates": {"estimate": Decimal("0.4")},
            "uncertainty": {
                "estimate": {
                    "kind": "interval",
                    "low": Decimal("0.1"),
                    "high": Decimal("0.7"),
                    "level": Decimal("0.95"),
                }
            },
        }

    return {"impl-interp-1": RuleImplementation(identity="impl-interp-1", evaluate=evaluate, fixtures=())}


def result_sensitive():
    # Outcome keyed to the RESULT's bytes: the output digest's low bit
    # decides. Deterministic, and a test can compute its expectation from the
    # manifest it holds — which is what makes the outcome's derivation, not
    # merely the identity, checkable.
    def evaluate(manifest):
        parity = int(manifest.outputs[0][1].split(":", 1)[1], 16) % 2
        return {
            "outcome": "supported" if parity == 0 else "refuted",
            "estimates": {"estimate": Decimal("0.4")},
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
# not fixture post-processing — the mint and scratch-intermediate cases.
SNAKEFILE_SEED_VIOLATING = SNAKEFILE_DETERMINISTIC.replace(
    "from beliefs.seeds import bind",
    "import json\nfrom beliefs.seeds import bind, record_digest_of",
).replace(
    '        value = seed(rule, wildcards, "model-initialization")',
    """        value = seed(rule, wildcards, "model-initialization")
        claim = next(pathlib.Path(".seeds").glob("*.json"))
        record = json.loads(claim.read_text())
        claim.unlink()
        value += 1
        record["seed"] = value
        (claim.parent / f"{record_digest_of(record)}.json").write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")))""",
)

# Byte-nondeterministic output, urandom staying inside the scratch root. Used
# with a stochastic-unseeded production recipe and, declared
# deterministic, as the honest way to obtain a failing assessment replay.
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

# A tree resource named `data` with these members, read from its staged
# directory; the job checks that the directory holds exactly the members, as
# regular files.
TREE_MEMBERS = {"a.txt": b"alpha\n", "sub/b.txt": b"beta\n"}
SNAKEFILE_TREE = """\
import pathlib

rule transform:
    input: "inputs/data/a.txt", "inputs/data/sub/b.txt"
    output: "outputs/result.txt"
    run:
        staged = pathlib.Path("inputs/data")
        assert not any(path.is_symlink() for path in staged.rglob("*"))
        members = sorted(path.relative_to(staged).as_posix() for path in staged.rglob("*") if path.is_file())
        assert members == ["a.txt", "sub/b.txt"], members
        text = "|".join(pathlib.Path(name).read_text() for name in input)
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
# The intermediates-excluded case.
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
    profile = BASE
    """The shared no-I/O port for value-width unit tests."""

    authority = FULL
    root = Path("memory-port")

    def append_intent(self, payload: bytes) -> str:
        return sha256(payload).hexdigest()

    def preflight(self, plan) -> None:
        pass

    def execute(self, plan) -> None:
        pass

    def execute_fulfilling(self, plan, fulfills: str) -> str:
        return "r" * 64

    def execute_fulfilling_guarded(self, plan, fulfills: str, *, guard, fallback):
        return GuardedCommit(self.execute_fulfilling(plan, fulfills), None)


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


def lay_tree(store: Path, members: dict[str, bytes]):
    """A held tree laid out by hand in a store directory: one object per member
    at `objects/sha256/<hh>/<hex>`, and the tree file at its own digest's path."""
    tree = make_tree(
        TreeMember(path=path, digest="sha256:" + sha256(data).hexdigest(), size=len(data))
        for path, data in members.items()
    )
    objects = {member.digest: members[member.path] for member in tree.members}
    objects[tree_digest(tree)] = tree_file_bytes(tree)
    for digest, data in objects.items():
        target = store / object_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return HeldTree(store_root=store, digest=tree_digest(tree))


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
    kernel_scratch=False,
):
    """`kernel_scratch` passes no scratch base, for a run session's port."""
    code, held = stage(tmp_path, snakefile=snakefile, data=data)
    spec = spec if spec is not None else freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())
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
        scratch_base=None if kernel_scratch else scratch_base if scratch_base is not None else tmp_path / "scratch",
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
    scratch_base=None,
    output_dir=None,
    kernel_scratch=False,
):
    """`kernel_scratch` passes no scratch base, for a run session's port."""
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
        scratch_base=None if kernel_scratch else scratch_base if scratch_base is not None else tmp_path / "scratch",
        cores=cores,
        output_dir=output_dir,
    )


def replay_of(
    original,
    tmp_path,
    *,
    port,
    snakefile=SNAKEFILE_DETERMINISTIC,
    host_realization="host-a",
    held_inputs=None,
    expected_inputs=None,
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
            **freeze_context(),
        )
    family_streams = (
        {"transform": original.run.recipe.nondeterminism.plan.streams}
        if isinstance(original.run.recipe.nondeterminism, Seeded)
        else {}
    )
    extra = {"expected_inputs": expected_inputs} if expected_inputs is not None else {}
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
        **extra,
    )


def event_estimand(claim, *, profile=TESTING_PROFILE):
    """A measured per-increment contrast for the event member of parties."""
    from beliefs.estimand import IncrementBinding

    event = next(m.referent for m in claim.roles["parties"] if m.referent.sort == "testing/event")
    observable = Observable("testing/energy", event.sort)
    pid = MEASUREMENT_RECORDS.put_procedure(
        Procedure(
            "testing/assay",
            "Event energy assay",
            "Measure event energy.",
            (observable,),
            None,
            {},
            (),
            (),
            None,
            None,
            {},
            None,
        )
    )
    measure = Measure(observable, "testing/electronvolt", None, "ratio", "level", "testing/identity", pid)
    return typed_estimand(
        profile=profile,
        claim=claim,
        bindings={
            "response": MeasuredBinding("parties", event, measure, None, None),
            "grouping": IncrementBinding("parties", event, measure, Decimal(1), "testing/electronvolt"),
        },
        control=Control("testing/observational", (), "testing/independent-groups", "testing/cohort-enrolment"),
    )
