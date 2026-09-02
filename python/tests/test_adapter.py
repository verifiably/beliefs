"""R13's capture arms and the boundary's three input-safety rules.
R13's import-resolution negative and R15's arms live in
acceptance/test_confinement_acceptance.py (cut 13)."""

import importlib.metadata
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fixtures_cut3 import SNAKEFILE_DETERMINISTIC, SNAKEFILE_NONDETERMINISTIC, definition

from beliefs.adapter import (
    LOG_HANDLER_SCRIPT,
    WORKFLOW_DEFINITION_DOMAIN,
    WorkflowDefinition,
    _canonical_distribution_name,
    build_argv,
    capture_bundle,
    create_scratch_root,
    distribution_digest,
    read_realized_seeds,
    read_trace,
    run_engine,
    tree_digest,
    validate_entrypoint,
)
from beliefs.errors import MalformedClosure, UnsafeInvocation


def _definition(**overrides):
    fields = {
        "snakefile": b"rule fit:\n    output: 'out.txt'\n",
        "family_streams": {"fit": ("model-initialization",)},
        "checkpoint_expanded_families": (),
    }
    return WorkflowDefinition(**{**fields, **overrides})


def test_the_domain_is_v2_because_the_projection_gained_a_member():
    assert WORKFLOW_DEFINITION_DOMAIN == "science.workflow-definition.v2"


def test_the_snapshot_carries_the_declaration_not_the_bytes():
    snapshot = _definition().snapshot()
    assert snapshot.family_streams == {"fit": ("model-initialization",)}
    assert snapshot.snakefile_digest.startswith("sha256:")
    assert snapshot.checkpoint_expanded_families == ()


def test_declaring_a_checkpoint_expanded_family_moves_the_identity():
    plain = _definition().snapshot().identity()
    declared = _definition(checkpoint_expanded_families=("fit",)).snapshot().identity()
    assert plain != declared


def test_the_snapshot_identity_is_the_definition_identity():
    definition = _definition()
    assert definition.identity() == definition.snapshot().identity()


def test_a_malformed_checkpoint_declaration_is_refused():
    with pytest.raises(MalformedClosure):
        _definition(checkpoint_expanded_families=("fit", 3))


def make_code_root(tmp_path: Path) -> Path:
    root = tmp_path / "code"
    (root / "workflow").mkdir(parents=True)
    (root / "workflow" / "Snakefile").write_bytes(SNAKEFILE_DETERMINISTIC.encode())
    (root / "helper.py").write_text("VALUE = 1\n")
    return root


def test_r13_modifying_an_untracked_file_changes_code_identity(tmp_path):
    root = make_code_root(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "helper.py"], cwd=root, check=True)
    (root / "untracked.py").write_text("X = 1\n")  # never added
    before = capture_bundle((root,), tmp_path / "b1")
    (root / "untracked.py").write_text("X = 2\n")
    after = capture_bundle((root,), tmp_path / "b2")
    assert before != after  # the capture is real — the bundle covers what ran


def test_r13_modifying_a_tracked_but_uncommitted_file_does_the_same(tmp_path):
    root = make_code_root(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    before = capture_bundle((root,), tmp_path / "b1")
    (root / "helper.py").write_text("VALUE = 2\n")  # the tree changed; no commit moved
    after = capture_bundle((root,), tmp_path / "b2")
    assert before != after


def test_duplicate_bundle_destinations_are_refused_before_overwrite(tmp_path):
    first = tmp_path / "first" / "code"
    second = tmp_path / "second" / "code"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "same.py").write_text("FIRST = 1\n")
    (second / "same.py").write_text("SECOND = 2\n")
    with pytest.raises(MalformedClosure):
        capture_bundle((first, second), tmp_path / "bundle")


def test_an_option_like_target_is_rejected_before_any_argv_is_built(tmp_path):
    with pytest.raises(UnsafeInvocation):
        build_argv(
            interpreter=sys.executable,
            snakefile=str(tmp_path / "Snakefile"),
            directory=str(tmp_path),
            targets=("--unlock",),
            config={},
            log_handler=str(tmp_path / "h.py"),
            cores=1,
            in_process_jobs=False,
        )


def test_a_config_key_cannot_become_an_option_shaped_argument(tmp_path):
    with pytest.raises(UnsafeInvocation):
        build_argv(
            interpreter=sys.executable,
            snakefile=str(tmp_path / "Snakefile"),
            directory=str(tmp_path),
            targets=(),
            config={"--config-injection": "1"},
            log_handler=str(tmp_path / "h.py"),
            cores=1,
            in_process_jobs=False,
        )
    with pytest.raises(UnsafeInvocation):
        build_argv(
            interpreter=sys.executable,
            snakefile=str(tmp_path / "Snakefile"),
            directory=str(tmp_path),
            targets=(),
            config={"seed=extra": "1"},
            log_handler=str(tmp_path / "h.py"),
            cores=1,
            in_process_jobs=False,
        )


def test_the_entrypoint_must_be_a_regular_file_inside_the_bundle(tmp_path):
    root = make_code_root(tmp_path)
    bundle = tmp_path / "bundle"
    capture_bundle((root,), bundle)
    assert validate_entrypoint(bundle, "code/workflow/Snakefile").is_file()
    with pytest.raises(UnsafeInvocation):
        validate_entrypoint(bundle, "../outside/Snakefile")
    with pytest.raises(UnsafeInvocation):
        validate_entrypoint(bundle, "code/workflow")  # a directory is not an entrypoint


def test_execution_is_direct_argv_with_shell_false(tmp_path):
    argv = build_argv(
        interpreter=sys.executable,
        snakefile=str(tmp_path / "Snakefile"),
        directory=str(tmp_path),
        targets=("outputs/result.txt",),
        config={"seed_model_initialization": "7"},
        log_handler=str(tmp_path / "handler.py"),
        cores=1,
        in_process_jobs=False,
    )
    assert argv[0] == sys.executable and argv[1:3] == ("-m", "snakemake")
    assert "--log-handler-script" in argv
    assert argv[argv.index("--") + 1 :] == ("outputs/result.txt",)  # targets after the delimiter, always
    source = inspect.getsource(run_engine)  # the N2 sabotage target
    assert "shell=False" in source and "shell=True" not in source


def engine_run(scratch, entry, trace_dir, *, config):
    # One invocation with the handler channel wired up. The events file lives
    # in a boundary-owned directory outside the scratch root as staging
    # tidiness — the channel is trusted by convention, not enforced: this
    # suite's fixtures never touch it, and tampering defers with confinement.
    trace_dir.mkdir(exist_ok=True)
    handler = trace_dir / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    events = trace_dir / "events.jsonl"
    argv = build_argv(
        interpreter=sys.executable,
        snakefile=str(entry),
        directory=str(scratch),
        targets=("outputs/result.txt",),
        config=config,
        log_handler=str(handler),
        cores=1,
        in_process_jobs=False,
    )
    code, log = run_engine(argv, cwd=scratch, env={**os.environ, "SCIENCE_TRACE_FILE": str(events)})
    return code, log, events


def test_the_adapter_executes_the_held_definition_and_observes_the_trace(tmp_path):
    # The smoke test: one real subprocess through Snakemake 8.11.4.
    root = make_code_root(tmp_path)
    bundle, scratch = tmp_path / "bundle", create_scratch_root(tmp_path / "scratch-base")
    capture_bundle((root,), bundle)
    (scratch / "inputs").mkdir()
    (scratch / "inputs" / "data.txt").write_text("hello")
    entry = validate_entrypoint(bundle, "code/workflow/Snakefile")
    code, log, events = engine_run(scratch, entry, tmp_path / "trace", config={"seed_model_initialization": "7"})
    assert code == 0, log
    assert (scratch / "outputs" / "result.txt").read_text().startswith("HELLO:")
    trace = read_trace(events)
    assert [job.rule for job in trace] == ["transform"]
    assert all(job.job_id for job in trace)  # engine-reported, never an ordinal
    seeds = read_realized_seeds(scratch)
    assert seeds.seeds["transform"]["model-initialization"] == 7


def test_the_computation_derives_from_the_seed_it_reports(tmp_path):
    # The sidecar is not decoration: two rendered seeds, two different output
    # bytes — a fixture reporting one seed while computing from another would
    # break this and the replay-equality arms together.
    outputs = {}
    for seed in ("7", "8"):
        root = make_code_root(tmp_path / f"code-{seed}")
        bundle = tmp_path / f"bundle-{seed}"
        capture_bundle((root,), bundle)
        scratch = create_scratch_root(tmp_path / f"scratch-{seed}")
        (scratch / "inputs").mkdir()
        (scratch / "inputs" / "data.txt").write_text("hello")
        entry = validate_entrypoint(bundle, "code/workflow/Snakefile")
        code, log, _ = engine_run(
            scratch, entry, tmp_path / f"trace-{seed}", config={"seed_model_initialization": seed}
        )
        assert code == 0, log
        outputs[seed] = (scratch / "outputs" / "result.txt").read_text()
    assert outputs["7"] != outputs["8"]


def test_a_malformed_trace_or_seed_report_refuses_capture(tmp_path):
    events = tmp_path / "events.jsonl"
    events.write_text("this is not json\n")
    with pytest.raises(MalformedClosure):
        read_trace(events)
    events.write_text('{"level": "job_info", "name": "transform"}\n')  # no jobid — and no ordinal fallback
    with pytest.raises(MalformedClosure):
        read_trace(events)
    events.write_text('{"level": "job_info", "name": "transform", "jobid": 0}\n')
    with pytest.raises(MalformedClosure):
        read_trace(events)  # input/output/wildcards required too — never silently defaulted
    scratch = create_scratch_root(tmp_path / "s")
    (scratch / ".seeds").mkdir()
    (scratch / ".seeds" / "a.json").write_text('{"transform": {"model-initialization": 7}}')
    (scratch / ".seeds" / "b.json").write_text('{"transform": {"model-initialization": 7}}')
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)  # ANY second claim for one (job, stream) — agreement included
    (scratch / ".seeds" / "b.json").write_text('{"transform": {"model-initialization": 9}}')
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)  # …and disagreeing, likewise
    (scratch / ".seeds" / "b.json").write_text("garbage")
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)


def trace_record(jobid, *, output="outputs/result.txt"):
    return {
        "level": "job_info",
        "jobid": jobid,
        "name": "transform",
        "input": ["inputs/data.txt"],
        "output": [output],
        "wildcards": {},
    }


def test_trace_preserves_equal_required_fields_from_different_engine_job_ids(tmp_path):
    events = tmp_path / "events.jsonl"
    events.write_text("\n".join(json.dumps(trace_record(jobid)) for jobid in (0, 1)))
    assert [job.job_id for job in read_trace(events)] == ["0", "1"]


def test_trace_folds_an_exact_duplicate_from_the_same_engine_job_id(tmp_path):
    events = tmp_path / "events.jsonl"
    record = json.dumps(trace_record(0))
    events.write_text(f"{record}\n{record}\n")
    assert [job.job_id for job in read_trace(events)] == ["0"]


def test_trace_refuses_conflicting_required_fields_for_one_engine_job_id(tmp_path):
    events = tmp_path / "events.jsonl"
    events.write_text(json.dumps(trace_record(0)) + "\n" + json.dumps(trace_record(0, output="outputs/other.txt")))
    with pytest.raises(MalformedClosure):
        read_trace(events)


@pytest.mark.parametrize(
    "report",
    [
        '{"transform": {"model-initialization": 7}, "transform": {"resample-draws": 8}}',
        '{"transform": {"model-initialization": 7, "model-initialization": 8}}',
    ],
)
def test_duplicate_keys_inside_one_seed_report_are_refused(tmp_path, report):
    scratch = create_scratch_root(tmp_path / "scratch")
    (scratch / ".seeds").mkdir()
    (scratch / ".seeds" / "transform.json").write_text(report)
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)


def test_a_seed_report_path_that_is_not_a_directory_is_refused(tmp_path):
    scratch = create_scratch_root(tmp_path / "scratch")
    (scratch / ".seeds").write_text("not a directory")
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)


def test_a_dangling_seed_report_symlink_is_refused(tmp_path):
    scratch = create_scratch_root(tmp_path / "scratch")
    (scratch / ".seeds").symlink_to(tmp_path / "missing", target_is_directory=True)
    with pytest.raises(MalformedClosure):
        read_realized_seeds(scratch)


def make_fixture_distribution(root: Path) -> Path:
    # A minimal purpose-built installed distribution: one module, one
    # dist-info with METADATA and a RECORD listing both files.
    root.mkdir(parents=True)
    (root / "demo_fixture.py").write_text("VALUE = 1\n")
    info = root / "demo_fixture-1.0.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: demo-fixture\nVersion: 1.0\n")
    (info / "RECORD").write_text("demo_fixture.py,,\ndemo_fixture-1.0.dist-info/METADATA,,\n")
    return info


def test_a_byte_mutation_in_a_held_artifact_moves_the_environment_identity(tmp_path):
    info = make_fixture_distribution(tmp_path / "site")
    before = distribution_digest(importlib.metadata.Distribution.at(info))
    (tmp_path / "site" / "demo_fixture.py").write_text("VALUE = 2\n")  # one mutated byte of content
    after = distribution_digest(importlib.metadata.Distribution.at(info))
    assert before != after  # the digest is over the artifact BYTES, not a name==version label


def test_relocated_identical_bytes_yield_the_same_environment_digest(tmp_path):
    info = make_fixture_distribution(tmp_path / "site-a")
    shutil.copytree(tmp_path / "site-a", tmp_path / "elsewhere" / "site-b")
    relocated = tmp_path / "elsewhere" / "site-b" / "demo_fixture-1.0.dist-info"
    assert distribution_digest(importlib.metadata.Distribution.at(info)) == distribution_digest(
        importlib.metadata.Distribution.at(relocated)
    )
    # …the same bytes reached via a different path are the same held content:
    # RECORD-relative names carry no mount point (§4.5)


def test_a_record_listed_site_packages_byte_moves_the_distribution_digest(tmp_path):
    info = make_fixture_distribution(tmp_path / "site")
    nested = tmp_path / "site" / "vendor" / "site-packages"
    nested.mkdir(parents=True)
    artifact = nested / "runtime.py"
    artifact.write_text("VALUE = 1\n")
    with (info / "RECORD").open("a") as record:
        record.write("vendor/site-packages/runtime.py,,\n")
    before = distribution_digest(importlib.metadata.Distribution.at(info))
    artifact.write_text("VALUE = 2\n")
    assert distribution_digest(importlib.metadata.Distribution.at(info)) != before


def test_distribution_names_use_pep_503_canonicalization():
    assert _canonical_distribution_name("Demo__Fixture.Name---Extra") == "demo-fixture-name-extra"


def make_fixture_stdlib(root: Path) -> Path:
    # A small tree standing in for a stdlib root — the real stdlib is never
    # touched; tree_digest is the fold capture_environment applies to it.
    (root / "lib-dynload").mkdir(parents=True)
    (root / "random.py").write_text("def seed(n): ...\n")
    (root / "json").mkdir()
    (root / "json" / "__init__.py").write_text("def loads(s): ...\n")
    (root / "lib-dynload" / "fake_ext.so").write_bytes(b"\x7fELF-fixture-extension")
    return root


def test_a_stdlib_byte_mutation_moves_the_environment_identity(tmp_path):
    original = make_fixture_stdlib(tmp_path / "stdlib-a")
    shutil.copytree(original, tmp_path / "elsewhere" / "stdlib-b")
    relocated = tmp_path / "elsewhere" / "stdlib-b"
    baseline = tree_digest(original, label="stdlib")
    assert baseline == tree_digest(relocated, label="stdlib")  # relocation-invariant
    (relocated / "random.py").write_text("def seed(n): return 0\n")  # one mutated source file
    assert tree_digest(relocated, label="stdlib") != baseline
    (relocated / "random.py").write_text("def seed(n): ...\n")  # restore the source…
    (relocated / "lib-dynload" / "fake_ext.so").write_bytes(b"\x7fELF-mutated")
    assert tree_digest(relocated, label="stdlib") != baseline  # …native extensions move it too
    # __pycache__ is a derived cache and never enters the fold:
    (original / "__pycache__").mkdir()
    (original / "__pycache__" / "random.cpython-311.pyc").write_bytes(b"varying bytes")
    assert tree_digest(original, label="stdlib") == baseline


def test_a_missing_record_listed_artifact_refuses_capture(tmp_path):
    info = make_fixture_distribution(tmp_path / "site")
    (tmp_path / "site" / "demo_fixture.py").unlink()  # RECORD still lists it
    with pytest.raises(MalformedClosure):
        distribution_digest(importlib.metadata.Distribution.at(info))
    bare = tmp_path / "bare" / "demo_fixture-1.0.dist-info"
    bare.mkdir(parents=True)
    (bare / "METADATA").write_text("Metadata-Version: 2.1\nName: demo-fixture\nVersion: 1.0\n")
    with pytest.raises(MalformedClosure):
        distribution_digest(importlib.metadata.Distribution.at(bare))  # no RECORD: unenumerable inventory


def test_the_definition_identity_covers_the_snakefile_and_the_family_streams():
    a = definition()
    assert a.identity() != definition(snakefile=SNAKEFILE_NONDETERMINISTIC).identity()
    assert a.identity() != definition(family_streams={"transform": ("resample-draws",)}).identity()


def test_the_definition_keeps_strict_immutable_members():
    streams = {"transform": ("model-initialization",)}
    value = WorkflowDefinition(snakefile=b"rule all:\n    input: []\n", family_streams=streams)
    streams["transform"] = ("resample-draws",)
    assert value.family_streams == {"transform": ("model-initialization",)}
    with pytest.raises(MalformedClosure):
        WorkflowDefinition(snakefile="not bytes", family_streams={})  # type: ignore[arg-type]
    with pytest.raises(MalformedClosure):
        WorkflowDefinition(snakefile=b"", family_streams={"transform": ["mutable"]})  # type: ignore[dict-item]
