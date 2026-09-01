"""The confined boundary's machinery over synthetic inputs: the snapshot (K2),
the canonical mount comparison and the judgement (K6), fingerprints, the
declared environment, and the bwrap argv shape (design §4.3–§6)."""

import os
from hashlib import sha256
from pathlib import Path

import pytest

import beliefs.confinement as confinement_module
from beliefs.adapter import SANDBOX_ENV, SANDBOX_LIB, SANDBOX_VENV, CapturedEnvironment, capture_bundle
from beliefs.confinement import (
    BUNDLE_ROOT,
    HOSTNAME,
    INPUTS_ROOT,
    OUTPUT_ROOT,
    UNPLANNED,
    InstanceFacts,
    MountPlan,
    bundle_identity,
    bwrap_argv,
    canonical_mounts,
    check_bundle_intact,
    check_closure_intact,
    fingerprint,
    judge_instance,
    judge_report,
    launch_confined,
    materialize_snapshot,
    mount_plan,
    sandbox_environment,
    verify_snapshot,
)
from beliefs.errors import ClosureMutated, ConfinementNotEstablished, SnapshotMismatch
from beliefs.recipe import CAPABILITIES, NAMESPACES, EnvironmentManifest, mount_plan_identity

LOADER = "/lib64/ld-linux-x86-64.so.2"


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def synthetic(tmp_path: Path) -> CapturedEnvironment:
    host = tmp_path / "host"
    host.mkdir()
    (host / "ld.so").write_bytes(b"loader")
    (host / "python3").write_bytes(b"interpreter")
    (host / "liba.so.1").write_bytes(b"liba")
    (host / "libc.so.6").write_bytes(b"libc")
    interpreter = "/science/env/python/bin/python3"
    manifest = EnvironmentManifest(
        artifacts=(
            (LOADER, "file", _digest(b"loader")),
            (interpreter, "file", _digest(b"interpreter")),
            ("/science/env/python/lib/liba.so", "symlink", "liba.so.1"),
            ("/science/env/python/lib/liba.so.1", "file", _digest(b"liba")),
            (f"{SANDBOX_LIB}/libc.so.6", "file", _digest(b"libc")),
        )
    )
    plan = {
        LOADER: host / "ld.so",
        interpreter: host / "python3",
        "/science/env/python/lib/liba.so": host / "liba.so.1",
        "/science/env/python/lib/liba.so.1": host / "liba.so.1",
        f"{SANDBOX_LIB}/libc.so.6": host / "libc.so.6",
    }
    rendered = (
        (f"{SANDBOX_VENV}/bin/python", "symlink", interpreter),
        (f"{SANDBOX_VENV}/pyvenv.cfg", "file", "home = /science/env/python/bin\ninclude-system-site-packages = false\n"),
    )
    loader_map = ((interpreter, "libc.so.6", f"{SANDBOX_LIB}/libc.so.6"),)
    return CapturedEnvironment(manifest=manifest, plan=plan, rendered=rendered, loader=LOADER, interpreter=interpreter, loader_map=loader_map)


# --- K2: the snapshot ---------------------------------------------------------
def test_a_snapshot_is_built_verified_and_published_under_its_environment_identity(tmp_path):
    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    snapshot = materialize_snapshot(captured, environments)
    assert snapshot == environments / captured.manifest.identity()
    assert (snapshot / "science/env/python/bin/python3").read_bytes() == b"interpreter"
    assert os.readlink(snapshot / "science/env/python/lib/liba.so") == "liba.so.1"
    assert (snapshot / "science/env/venv/pyvenv.cfg").read_text().startswith("home = ")
    assert os.readlink(snapshot / "science/env/venv/bin/python") == captured.interpreter
    verify_snapshot(snapshot, captured)
    assert materialize_snapshot(captured, environments) == snapshot
    assert not [entry for entry in environments.iterdir() if ".build-" in entry.name]


def test_k2_an_existing_mismatching_snapshot_refuses_and_is_never_rebuilt(tmp_path):
    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    snapshot = materialize_snapshot(captured, environments)
    corrupt = snapshot / "science/env/lib/libc.so.6"
    corrupt.write_bytes(b"CORRUPT")
    inode = corrupt.stat().st_ino
    with pytest.raises(SnapshotMismatch):
        materialize_snapshot(captured, environments)
    assert corrupt.read_bytes() == b"CORRUPT" and corrupt.stat().st_ino == inode


def test_a_snapshot_with_an_unmanifested_file_or_a_missing_row_refuses(tmp_path):
    captured = synthetic(tmp_path)
    snapshot = materialize_snapshot(captured, tmp_path / "environments")
    (snapshot / "science/env/extra").write_bytes(b"x")
    with pytest.raises(SnapshotMismatch, match="extra"):
        verify_snapshot(snapshot, captured)
    (snapshot / "science/env/extra").unlink()
    (snapshot / "science/env/lib/libc.so.6").unlink()
    with pytest.raises(SnapshotMismatch, match="missing"):
        verify_snapshot(snapshot, captured)


def test_k2_a_concurrent_winner_is_verified_and_reused_or_refused(tmp_path, monkeypatch):
    import shutil

    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    target = environments / captured.manifest.identity()
    original_rename = Path.rename

    def lose_to_a_winner(self: Path, destination):
        if self.parent == environments and self.name.startswith(f"{target.name}.build-"):
            shutil.copytree(self, target, symlinks=True)
            raise OSError("a winner published first")
        return original_rename(self, destination)

    monkeypatch.setattr(Path, "rename", lose_to_a_winner)
    assert materialize_snapshot(captured, environments) == target
    assert not [entry for entry in environments.iterdir() if ".build-" in entry.name]

    shutil.rmtree(target)

    def lose_to_a_corrupt_winner(self: Path, destination):
        if self.parent == environments and self.name.startswith(f"{target.name}.build-"):
            shutil.copytree(self, target, symlinks=True)
            (target / "science/env/lib/libc.so.6").write_bytes(b"CORRUPT")
            raise OSError("a corrupt winner published first")
        return original_rename(self, destination)

    monkeypatch.setattr(Path, "rename", lose_to_a_corrupt_winner)
    with pytest.raises(SnapshotMismatch):
        materialize_snapshot(captured, environments)


# --- integrity ----------------------------------------------------------------
def test_bundle_identity_recomputes_capture_bundles_fold_and_moves_on_an_edit(tmp_path):
    root = tmp_path / "code"
    (root / "workflow").mkdir(parents=True)
    (root / "workflow" / "Snakefile").write_text("rule a: pass\n")
    (root / "helper.py").write_text("VALUE = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    assert bundle_identity(bundle) == code_identity
    (bundle / "code" / "helper.py").write_text("VALUE = 2\n")
    assert bundle_identity(bundle) != code_identity


def test_check_bundle_intact_refuses_an_edited_bundle(tmp_path):
    root = tmp_path / "code"
    root.mkdir()
    (root / "a.py").write_text("A = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    check_bundle_intact(bundle, code_identity)
    (bundle / "code" / "a.py").write_text("A = 2\n")
    with pytest.raises(ClosureMutated, match="bundle"):
        check_bundle_intact(bundle, code_identity)


def test_check_closure_intact_refuses_an_edited_bundle_a_moved_snapshot_and_changed_inputs(tmp_path):
    captured = synthetic(tmp_path)
    snapshot = materialize_snapshot(captured, tmp_path / "environments")
    root = tmp_path / "code"
    root.mkdir()
    (root / "a.py").write_text("A = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "data.txt").write_text("x\n")
    before = fingerprint(inputs)

    def check() -> None:
        check_closure_intact(
            bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=inputs, inputs_fingerprint=before
        )

    check()
    (bundle / "code" / "a.py").write_text("A = 2\n")
    with pytest.raises(ClosureMutated, match="bundle"):
        check()
    (bundle / "code" / "a.py").write_text("A = 1\n")
    (snapshot / "science/env/lib/libc.so.6").write_bytes(b"MOVED")
    with pytest.raises(ClosureMutated, match="snapshot"):
        check()
    (snapshot / "science/env/lib/libc.so.6").write_bytes(b"libc")
    (inputs / "data.txt").write_text("y\n")
    with pytest.raises(ClosureMutated, match="inputs"):
        check()


def test_no_raw_oserror_leaves_the_snapshot_or_integrity_seams(tmp_path, monkeypatch):
    """Design §8: a failed read, copy or invocation is the named refusal of its
    stage, never a raw OSError reaching _execute_run as a string reason."""
    import dataclasses

    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    missing_source = dataclasses.replace(captured, plan={**captured.plan, captured.interpreter: tmp_path / "missing"})
    with pytest.raises(SnapshotMismatch, match="materialized"):
        materialize_snapshot(missing_source, environments)
    assert not [entry for entry in environments.iterdir() if ".build-" in entry.name]
    snapshot = materialize_snapshot(captured, environments)
    unreadable = snapshot / "science/env/lib/libc.so.6"
    unreadable.chmod(0o000)
    try:
        with pytest.raises(SnapshotMismatch, match="unreadable"):
            verify_snapshot(snapshot, captured)
    finally:
        unreadable.chmod(0o644)
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a").write_bytes(b"a")
    (tree / "a").chmod(0o000)
    try:
        with pytest.raises(ClosureMutated, match="could not be read"):
            fingerprint(tree)
        with pytest.raises(ClosureMutated, match="could not be read"):
            bundle_identity(tree)
    finally:
        (tree / "a").chmod(0o644)
    unexecutable = tmp_path / "bwrap"
    unexecutable.write_bytes(b"\x00not an executable image\x00")
    unexecutable.chmod(0o755)  # which() accepts an executable regular file; execve refuses it with ENOEXEC
    monkeypatch.setattr(confinement_module, "_BWRAP", str(unexecutable))
    reason = confinement_module.host_prerequisites()
    assert reason is not None and "could not be invoked" in reason


def test_fingerprints_move_with_content_and_symlink_targets(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a").write_bytes(b"a")
    (tree / "link").symlink_to("a")
    before = fingerprint(tree)
    (tree / "a").write_bytes(b"b")
    assert fingerprint(tree) != before
    (tree / "a").write_bytes(b"a")
    assert fingerprint(tree) == before
    (tree / "link").unlink()
    (tree / "link").symlink_to("b")
    assert fingerprint(tree) != before


# --- the mount plan and the canonical comparison (K6) -------------------------
def _plan(tmp_path: Path) -> MountPlan:
    return mount_plan(snapshot=tmp_path / "snap", loader=LOADER, bundle=tmp_path / "bundle", output_root=tmp_path / "out")


def test_the_mount_plan_rows_are_canonical_and_identity_bearing(tmp_path):
    plan = _plan(tmp_path)
    assert plan.rows == (
        ("/", "root", "ro"),
        (LOADER, "loader", "ro"),
        (SANDBOX_ENV, "env", "ro"),
        (BUNDLE_ROOT, "bundle", "ro"),
        (OUTPUT_ROOT, "output", "rw"),
        (INPUTS_ROOT, "inputs", "ro"),
        ("/dev/null", "device", "rw"),
        ("/dev/urandom", "device", "rw"),
    )
    assert plan.identity() == mount_plan_identity(plan.rows)
    assert plan.expected == tuple(sorted(plan.rows))
    assert plan.role_of(BUNDLE_ROOT) == "bundle" and plan.role_of("/dev/null") == "device" and plan.role_of("/etc") == UNPLANNED
    assert dict(plan.host_mapping())[BUNDLE_ROOT] == str(tmp_path / "bundle")
    assert dict(plan.host_mapping())[SANDBOX_ENV] == str(tmp_path / "snap" / "science" / "env")
    assert dict(plan.host_mapping())[LOADER] == str(tmp_path / "snap" / LOADER.lstrip("/"))


def test_canonical_mounts_keeps_every_row_classifies_by_planned_role_and_unescapes(tmp_path):
    plan = _plan(tmp_path)
    text = (
        "1 0 0:1 / / ro,nosuid - tmpfs tmpfs rw\n"
        "2 1 8:1 /scratch/out /science/out rw,relatime - ext4 /dev/sda1 rw\n"
        "3 2 8:1 /scratch/out/in /science/out/inputs ro,relatime - ext4 /dev/sda1 rw\n"
        "4 2 8:1 /scratch/out/in /science/out/inputs ro,relatime - ext4 /dev/sda1 rw\n"
        "5 1 8:1 /x/with\\040space /science/with\\040space ro - ext4 /dev/sda1 rw\n"
    )
    assert canonical_mounts(text, plan) == (
        ("/", "root", "ro"),
        ("/science/out", "output", "rw"),
        ("/science/out/inputs", "inputs", "ro"),
        ("/science/out/inputs", "inputs", "ro"),
        ("/science/with space", UNPLANNED, "ro"),
    )


def test_k6_a_namespace_equal_to_the_parents_refuses(tmp_path):
    plan = _plan(tmp_path)
    facts = InstanceFacts(distinct=tuple(name for name in NAMESPACES if name != "net"), mounts=plan.expected)
    with pytest.raises(ConfinementNotEstablished, match="net"):
        judge_instance(facts, plan)
    judge_instance(InstanceFacts(distinct=NAMESPACES, mounts=plan.expected), plan)


def test_k6_a_mount_table_unequal_to_the_plan_refuses(tmp_path):
    plan = _plan(tmp_path)
    extra = InstanceFacts(distinct=NAMESPACES, mounts=tuple(sorted((*plan.expected, ("/etc", UNPLANNED, "ro")))))
    with pytest.raises(ConfinementNotEstablished, match="/etc"):
        judge_instance(extra, plan)
    stacked = InstanceFacts(distinct=NAMESPACES, mounts=tuple(sorted((*plan.expected, (INPUTS_ROOT, "inputs", "ro")))))
    with pytest.raises(ConfinementNotEstablished, match="observed rows"):
        judge_instance(stacked, plan)
    missing = InstanceFacts(distinct=NAMESPACES, mounts=tuple(row for row in plan.expected if row[0] != INPUTS_ROOT))
    with pytest.raises(ConfinementNotEstablished, match="inputs"):
        judge_instance(missing, plan)
    writable_root = InstanceFacts(
        distinct=NAMESPACES, mounts=tuple(sorted(("/", "root", "rw") if row[0] == "/" else row for row in plan.expected))
    )
    with pytest.raises(ConfinementNotEstablished):
        judge_instance(writable_root, plan)


def good_report(captured: CapturedEnvironment, environment) -> dict:
    return {
        "environ": dict(environment),
        "hostname": HOSTNAME,
        "cwd": OUTPUT_ROOT,
        "filesystem": {
            "read:/etc/passwd": "ENOENT",
            "read:/tmp": "ENOENT",
            "write:/": "EROFS",
            f"write:{BUNDLE_ROOT}": "EROFS",
            f"write:{SANDBOX_ENV}": "EROFS",
            f"write:{INPUTS_ROOT}": "EROFS",
            f"write:{OUTPUT_ROOT}": "OK",
        },
        "network": {"ipv4": "ENETUNREACH", "ipv6": "EAFNOSUPPORT"},
        "loader": {
            captured.interpreter: {
                "returncode": 0,
                "resolved": {"libc.so.6": [f"{SANDBOX_LIB}/libc.so.6", _digest(b"libc")]},
                "unresolved": [],
            }
        },
    }


def _entry(report: dict) -> dict:
    return report["loader"][next(iter(report["loader"]))]


INNER = ("/science/env/venv/bin/python", "-m", "snakemake", "--snakefile", f"{BUNDLE_ROOT}/code/workflow/Snakefile", "--", "outputs/result.txt")


def test_a_good_report_yields_every_capability(tmp_path):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    assert judge_report(good_report(captured, environment), environment=environment, captured=captured, inner_argv=INNER) == CAPABILITIES


@pytest.mark.parametrize(
    "mutate, match",
    [
        (lambda r: r["environ"].update({"HOSTTYPE": "x86_64"}), "environment"),
        (lambda r: r.update({"hostname": "laptop"}), "hostname"),
        (lambda r: r.update({"cwd": "/"}), "cwd"),
        (lambda r: r["filesystem"].update({"read:/etc/passwd": "READ"}), "filesystem"),
        (lambda r: r["filesystem"].update({f"write:{BUNDLE_ROOT}": "OK"}), "filesystem"),
        (lambda r: r["network"].update({"ipv4": "ECONNREFUSED"}), "network"),
        (lambda r: r["network"].update({"ipv6": "CONNECTED"}), "network"),
        (lambda r: _entry(r)["resolved"].update({"libc.so.6": [f"{SANDBOX_LIB}/libc.so.6", _digest(b"other")]}), "loader"),
        (lambda r: _entry(r)["resolved"].update({"libc.so.6": ["/science/env/python/lib/libc.so.6", _digest(b"libc")]}), "loader"),
        (lambda r: r["loader"].clear(), "loader"),  # an omitted ELF
        (lambda r: _entry(r)["resolved"].clear(), "loader"),  # an omitted SONAME
        (lambda r: _entry(r)["resolved"].update({"libm.so.6": [f"{SANDBOX_LIB}/libm.so.6", _digest(b"m")]}), "loader"),  # an extra SONAME
        (lambda r: _entry(r)["unresolved"].append("libm.so.6 => not found"), "loader"),  # not found
        (lambda r: _entry(r).update({"returncode": 127}), "loader"),  # a nonzero loader exit
        (lambda r: r["loader"].update({"/science/env/site/extra.so": dict(_entry(r))}), "loader"),  # an extra ELF
    ],
)
def test_k6_each_report_deviation_refuses(tmp_path, mutate, match):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    report = good_report(captured, environment)
    mutate(report)
    with pytest.raises(ConfinementNotEstablished, match=match):
        judge_report(report, environment=environment, captured=captured, inner_argv=INNER)


def test_an_engine_argv_whose_snakefile_is_outside_the_bundle_refuses(tmp_path):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    outside = tuple("/science/out/Snakefile" if part.startswith(BUNDLE_ROOT) else part for part in INNER)
    with pytest.raises(ConfinementNotEstablished, match="bundle"):
        judge_report(good_report(captured, environment), environment=environment, captured=captured, inner_argv=outside)


@pytest.mark.parametrize("broken", [lambda r: r.pop("network"), lambda r: r.update({"environ": "not a mapping"}), lambda r: r.update({"loader": None})])
def test_a_malformed_report_shape_is_not_a_traceback_of_its_own(tmp_path, broken):
    """judge_report may raise KeyError or TypeError on a malformed shape; the
    launch wraps those (below). Here: it never returns capabilities for one."""
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    report = good_report(captured, environment)
    broken(report)
    with pytest.raises((ConfinementNotEstablished, KeyError, TypeError, AttributeError)):
        judge_report(report, environment=environment, captured=captured, inner_argv=INNER)


# --- the launch's failure boundary --------------------------------------------
def test_a_launch_protocol_failure_is_confinement_not_established_and_the_child_is_reaped(tmp_path, monkeypatch):
    """A stand-in bubblewrap that writes garbage on the info descriptor and then
    sleeps: the launch refuses with the stable reason, terminates and reaps the
    child, and leaves no descriptor open (design §8)."""
    import sys

    pid_file = tmp_path / "pid"
    fake = tmp_path / "bwrap"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import os, sys, time\n"
        "info = int(sys.argv[sys.argv.index('--info-fd') + 1])\n"
        "os.write(info, b'not json at all')\n"
        "os.close(info)\n"
        f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
        "time.sleep(60)\n"
    )
    fake.chmod(0o755)
    monkeypatch.setattr(confinement_module, "_BWRAP", str(fake))
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    open_before = set(os.listdir("/proc/self/fd"))
    with pytest.raises(ConfinementNotEstablished, match="info descriptor"):
        launch_confined(plan=_plan(tmp_path), environment=environment, inner_argv=INNER, captured=captured)
    assert set(os.listdir("/proc/self/fd")) <= open_before
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def test_bubblewrap_gone_after_intent_is_confinement_not_established_not_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(confinement_module, "_BWRAP", str(tmp_path / "no-such-bwrap"))
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    with pytest.raises(ConfinementNotEstablished, match="PATH"):
        launch_confined(plan=_plan(tmp_path), environment=environment, inner_argv=INNER, captured=captured)


# --- the declared environment and the bwrap argv -----------------------------
def test_the_declared_environment_is_exactly_the_specs_set():
    assert sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl") == (
        ("HOME", "/science/out/.home"),
        ("LC_CTYPE", "C.UTF-8"),
        ("LD_LIBRARY_PATH", "/science/env/lib"),
        ("PATH", "/science/env/venv/bin"),
        ("PWD", "/science/out"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONHASHSEED", "0"),
        ("PYTHONNOUSERSITE", "1"),
        ("PYTHONSAFEPATH", "1"),
        ("SCIENCE_TRACE_FILE", "/science/out/.trace/events.jsonl"),
    )


def test_the_bwrap_argv_binds_then_remounts_the_root_read_only_and_gates_through_the_probe(tmp_path):
    plan = _plan(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    argv = bwrap_argv(plan, environment, INNER, bwrap="/usr/bin/bwrap", info_fd=7, report_fd=8, go_fd=9)
    assert argv[:2] == ("/usr/bin/bwrap", "--unshare-all")
    for flag in ("--die-with-parent", "--new-session", "--clearenv", "--hostname", "--info-fd"):
        assert flag in argv
    assert argv[argv.index("--hostname") + 1] == HOSTNAME
    remount = argv.index("--remount-ro")
    assert argv[remount + 1] == "/"
    assert max(index for index, part in enumerate(argv) if part in ("--ro-bind", "--bind", "--dev-bind")) < remount
    assert argv[argv.index("--chdir") + 1] == OUTPUT_ROOT
    assert ("--setenv", "PYTHONSAFEPATH", "1") == argv[argv.index("PYTHONSAFEPATH") - 1 : argv.index("PYTHONSAFEPATH") + 2]
    separator = argv.index("--")
    assert argv[separator + 1 : separator + 4] == (f"{SANDBOX_VENV}/bin/python", "-m", "beliefs.probe")
    assert argv[-len(INNER):] == INNER
    assert ("--report-fd", "8") == argv[argv.index("--report-fd") : argv.index("--report-fd") + 2]
    assert ("--go-fd", "9") == argv[argv.index("--go-fd") : argv.index("--go-fd") + 2]
    assert "--proc" not in argv and "--dev" not in argv
