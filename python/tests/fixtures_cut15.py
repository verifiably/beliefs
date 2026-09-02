"""Workflow fixtures for the full cut-15 surface."""

from hashlib import sha256
from pathlib import Path

from config_probe import run_config_probe  # noqa: F401 — Task 9's shared engine probe
from fixtures_cut3 import DATA_ADDRESS, MEMORY_PORT, READS_ADDRESS, stage

from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, execute_production_run
from beliefs.recipe import MINIMAL_POLICY, RecipeInput
from beliefs.runrecord import OperationPort
from beliefs.spec import Deterministic

SNAKEFILE_WILDCARD = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)
SAMPLES = ["a", "b"]

rule all:
    input: expand("outputs/{s}.txt", s=SAMPLES)

rule fit:
    input: "inputs/data.txt"
    output: "outputs/{s}.txt"
    run:
        value = seed(rule, wildcards, "model-initialization")
        pathlib.Path(output[0]).write_text(f"{wildcards.s}:{value}")
"""

SNAKEFILE_TWO_TARGETS = """\
import pathlib

rule analysis:
    input: "inputs/data.txt"
    output: "outputs/analysis.txt"
    run:
        pathlib.Path(output[0]).write_text(pathlib.Path(input[0]).read_text().upper())

rule report:
    input: "outputs/analysis.txt"
    output: "outputs/report.txt"
    run:
        pathlib.Path(output[0]).write_text("report:" + pathlib.Path(input[0]).read_text())
"""

SNAKEFILE_ONE_RULE_PIPELINE = """\
import pathlib

rule report:
    input: "inputs/data.txt"
    output: "outputs/report.txt"
    run:
        pathlib.Path(output[0]).write_text("report:" + pathlib.Path(input[0]).read_text().upper())
"""

SNAKEFILE_TWO_FAMILIES = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)

rule all:
    input: "outputs/a.txt", "outputs/b.txt"

rule a:
    input: "inputs/data.txt"
    output: "outputs/a.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "model-initialization")))

rule b:
    input: "inputs/data.txt"
    output: "outputs/b.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "resample-draws")))
"""

SNAKEFILE_CHECKPOINT = """\
import pathlib

checkpoint split:
    input: "inputs/data.txt"
    output: directory("splits")
    run:
        target = pathlib.Path(output[0])
        target.mkdir(parents=True, exist_ok=True)
        for name in ("a", "b"):
            (target / (name + ".txt")).write_text(name)

def parts(wildcards):
    directory = checkpoints.split.get(**wildcards).output[0]
    names = sorted(path.stem for path in pathlib.Path(directory).glob("*.txt"))
    return expand("outputs/{n}.done", n=names)

rule fit:
    input: "splits/{n}.txt"
    output: "outputs/{n}.done"
    run:
        pathlib.Path(output[0]).write_text(wildcards.n)

rule all:
    input: parts
"""

SNAKEFILE_ZERO_JOB_FAMILY = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)

rule used:
    input: "inputs/data.txt"
    output: "outputs/used.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "model-initialization")))

rule unused:
    input: "inputs/data.txt"
    output: "outputs/unused.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "resample-draws")))
"""

SNAKEFILE_INPUT_DEPENDENT_DAG = """\
import pathlib

SAMPLES = pathlib.Path("inputs/data.txt").read_text().split()

rule all:
    input: expand("outputs/{s}.txt", s=SAMPLES)

rule fit:
    input: "inputs/data.txt"
    output: "outputs/{s}.txt"
    run:
        pathlib.Path(output[0]).write_text(wildcards.s)
"""

SNAKEFILE_CONSTANT_PRODUCTION = """\
import pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        pathlib.Path(output[0]).write_text("constant")
"""


def fanout_width(base_name: str) -> int:
    return 1 + (len(base_name) % 3)


SNAKEFILE_SCRATCH_KEYED_FANOUT = """\
import os, pathlib
from beliefs.seeds import bind

seed = bind(config)

def _width(base_name):
    return 1 + (len(base_name) % 3)

checkpoint split:
    input: "inputs/data.txt"
    output: directory("splits")
    run:
        target = pathlib.Path(output[0]); target.mkdir(parents=True, exist_ok=True)
        base = pathlib.Path(os.getcwd()).parent.name
        for index in range(_width(base)):
            (target / (chr(97 + index) + ".txt")).write_text(str(index))

def parts(wildcards):
    directory = checkpoints.split.get(**wildcards).output[0]
    names = sorted(p.stem for p in pathlib.Path(directory).glob("*.txt"))
    return expand("outputs/{n}.done", n=names)

rule fit:
    input: "splits/{n}.txt"
    output: "outputs/{n}.done"
    run:
        value = seed(rule, wildcards, "model-initialization")
        pathlib.Path(output[0]).write_text(f"{wildcards.n}:{value}")

rule all:
    input: parts
"""


def run_workflow(
    work_dir: Path,
    *,
    snakefile: str,
    targets,
    declared_outputs,
    port: OperationPort = MEMORY_PORT,
    family_streams=None,
    checkpoint_expanded_families=(),
    nondeterminism=None,
    inputs=None,
    held_inputs=None,
    parameters=None,
    data="hello",
    scratch_base=None,
    boundary_policy=MINIMAL_POLICY,
    started_at="2026-09-01T00:00:00Z",
    host_realization="host-a",
    cores=1,
):
    work_dir.mkdir(parents=True, exist_ok=True)
    code, held = stage(work_dir, snakefile=snakefile, data=data)
    contract = nondeterminism if nondeterminism is not None else Deterministic()
    definition = WorkflowDefinition(
        snakefile=snakefile.encode("utf-8"),
        family_streams=family_streams if family_streams is not None else {},
        checkpoint_expanded_families=tuple(checkpoint_expanded_families),
    )
    supplied = held_inputs if held_inputs is not None else {
        DATA_ADDRESS: held / "data.txt",
        READS_ADDRESS: held / "palette.txt",
    }
    authored = inputs if inputs is not None else (
        RecipeInput(
            role="transforms",
            dataset=DATA_ADDRESS,
            content="sha256:" + sha256(supplied[DATA_ADDRESS].read_bytes()).hexdigest(),
        ),
    )
    return execute_production_run(
        inputs=authored,
        parameters=parameters if parameters is not None else {},
        nondeterminism=contract,
        port=port,
        boundary_policy=boundary_policy,
        definition=definition,
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=tuple(targets),
        declared_outputs=tuple(declared_outputs),
        actor="tester",
        observer="observer-1",
        started_at=started_at,
        host_realization=host_realization,
        scratch_base=scratch_base if scratch_base is not None else work_dir / "scratch",
        cores=cores,
    )


def data_dependent_pair(tmp_path):
    narrow = run_workflow(
        tmp_path / "narrow",
        snakefile=SNAKEFILE_INPUT_DEPENDENT_DAG,
        data="a b",
        targets=("all",),
        declared_outputs=("outputs/a.txt", "outputs/b.txt"),
    )
    wide = run_workflow(
        tmp_path / "wide",
        snakefile=SNAKEFILE_INPUT_DEPENDENT_DAG,
        data="a b c",
        targets=("all",),
        declared_outputs=("outputs/a.txt", "outputs/b.txt", "outputs/c.txt"),
    )
    assert isinstance(narrow, RunMinted) and isinstance(wide, RunMinted)
    return narrow.run, wide.run
