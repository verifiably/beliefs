"""The confined boundary policy's machinery (run-confinement design §4.3–§6).

The snapshot and its verification, the mount plan, the bubblewrap launch gated
by the held probe, the boundary-side observation of the child's namespaces and
mounts from this process's own ``/proc``, and the judgement that turns the
probe's report and that observation into the capabilities the receipt attests.
Nothing here reads the requested policy's capabilities: what the receipt says
is what was observed.
"""

from __future__ import annotations

import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import cast, final

from beliefs.adapter import (
    SANDBOX_ENV,
    SANDBOX_LIB,
    SANDBOX_VENV,
    CapturedEnvironment,
    _fold,
    elf_interpreter,
    loader_listing,
)
from beliefs.errors import (
    ClosureMutated,
    ClosureUnsupported,
    ConfinementNotEstablished,
    ConfinementUnavailable,
    SnapshotMismatch,
)
from beliefs.recipe import CAPABILITIES, NAMESPACES, mount_plan_identity
from beliefs.sealed import sealed

__all__ = [
    "BUNDLE_ROOT",
    "DEVICES",
    "HOME_DIR",
    "HOSTNAME",
    "INPUTS_ROOT",
    "OUTPUT_ROOT",
    "TRACE_DIR",
    "UNPLANNED",
    "InstanceFacts",
    "Launch",
    "MountPlan",
    "bundle_identity",
    "bwrap_argv",
    "canonical_mounts",
    "check_bundle_intact",
    "check_closure_intact",
    "fingerprint",
    "host_prerequisites",
    "judge_instance",
    "judge_report",
    "launch_confined",
    "materialize_snapshot",
    "mount_plan",
    "observe_instance",
    "require_host",
    "sandbox_environment",
    "verify_snapshot",
]

HOSTNAME = "science"
BUNDLE_ROOT = "/science/bundle"
OUTPUT_ROOT = "/science/out"
INPUTS_ROOT = "/science/out/inputs"
TRACE_DIR = ".trace"
HOME_DIR = ".home"
DEVICES = ("/dev/null", "/dev/urandom")
UNPLANNED = "unplanned"
PROBE_MODULE = "beliefs.probe"
_BWRAP = "bwrap"
_NETWORK_UNREACHABLE = ("EAFNOSUPPORT", "ENETUNREACH", "EADDRNOTAVAIL")


def sandbox_environment(trace_file: str) -> tuple[tuple[str, str], ...]:
    """The explicit environment, exactly (design §5.4). Sorted by name."""
    return (
        ("HOME", f"{OUTPUT_ROOT}/{HOME_DIR}"),
        ("LC_CTYPE", "C.UTF-8"),
        ("LD_LIBRARY_PATH", SANDBOX_LIB),
        ("PATH", f"{SANDBOX_VENV}/bin"),
        ("PWD", OUTPUT_ROOT),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONHASHSEED", "0"),
        ("PYTHONNOUSERSITE", "1"),
        ("PYTHONSAFEPATH", "1"),
        ("SCIENCE_TRACE_FILE", trace_file),
    )


# --- host prerequisites (pre-intent) -------------------------------------------
def host_prerequisites() -> str | None:
    """None when the confined policy can be provided here, else why not."""
    bwrap = shutil.which(_BWRAP)
    if bwrap is None:
        return "bubblewrap (bwrap) is not on PATH"
    try:
        usage = subprocess.run([bwrap, "--help"], capture_output=True, text=True, check=False)
        if "--info-fd" not in usage.stdout + usage.stderr:
            return "bubblewrap lacks --info-fd"
        namespaces = subprocess.run(
            [bwrap, "--unshare-all", "--ro-bind", "/", "/", "--", "/bin/true"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return f"bubblewrap could not be invoked: {error}"
    if namespaces.returncode != 0:
        return f"unprivileged user namespaces are unavailable: {namespaces.stderr.strip()}"
    interpreter = Path(os.path.realpath(sys.executable))
    try:
        loader_listing(elf_interpreter(interpreter), interpreter)
    except ClosureUnsupported as error:
        return f"the loader cannot list the interpreter: {error}"
    return None


def require_host() -> None:
    reason = host_prerequisites()
    if reason is not None:
        raise ConfinementUnavailable(reason)


# --- the snapshot -----------------------------------------------------------------
def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _within(root: Path, sandbox: str) -> Path:
    return root / sandbox.lstrip("/")


def verify_snapshot(root: Path, captured: CapturedEnvironment) -> None:
    """Every manifested row by digest, every rendered row by content, and
    nothing else (design §4.3). A read that fails is a mismatch — no raw
    OSError leaves this module (design §8)."""
    try:
        _verify_rows(root, captured)
    except OSError as error:
        raise SnapshotMismatch(f"{root.name}: unreadable while verifying: {error}") from error


def _verify_rows(root: Path, captured: CapturedEnvironment) -> None:
    manifested = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    rendered = {path: (kind, content) for path, kind, content in captured.rendered if kind != "value"}
    seen: set[str] = set()
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        sandbox = "/" + path.relative_to(root).as_posix()
        if sandbox in manifested:
            kind, content = manifested[sandbox]
            actual = os.readlink(path) if path.is_symlink() else (_digest(path) if path.is_file() else "")
        elif sandbox in rendered:
            kind, content = rendered[sandbox]
            actual = os.readlink(path) if path.is_symlink() else (path.read_text(encoding="utf-8") if path.is_file() else "")
        else:
            raise SnapshotMismatch(f"{root.name}: {sandbox} is not a manifested or rendered row (extra)")
        if (kind == "symlink") != path.is_symlink() or actual != content:
            raise SnapshotMismatch(f"{root.name}: {sandbox} disagrees with its {kind} row")
        seen.add(sandbox)
    missing = sorted((set(manifested) | set(rendered)) - seen)
    if missing:
        raise SnapshotMismatch(f"{root.name}: missing rows {missing[:5]}")


def materialize_snapshot(captured: CapturedEnvironment, environments: Path) -> Path:
    """Get-or-build, keyed by environment identity; atomic publication with the
    loser rule; an existing mismatching snapshot refuses and is never rebuilt.
    A copy, link, write or directory operation that fails is SnapshotMismatch
    — no raw OSError leaves this module (design §8)."""
    try:
        return _materialize(captured, environments)
    except OSError as error:
        raise SnapshotMismatch(f"the snapshot under {environments} could not be materialized: {error}") from error


def _materialize(captured: CapturedEnvironment, environments: Path) -> Path:
    environments.mkdir(parents=True, exist_ok=True)
    target = environments / captured.manifest.identity()
    if target.exists():
        verify_snapshot(target, captured)
        return target
    build = Path(tempfile.mkdtemp(prefix=f"{target.name}.build-", dir=environments))
    try:
        for path, kind, content in captured.manifest.artifacts:
            destination = _within(build, path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if kind == "symlink":
                destination.symlink_to(content)
            else:
                shutil.copy2(captured.plan[path], destination)
        for path, kind, content in captured.rendered:
            if kind == "value":
                continue
            destination = _within(build, path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if kind == "symlink":
                destination.symlink_to(content)
            else:
                destination.write_text(content, encoding="utf-8")
        verify_snapshot(build, captured)
    except (OSError, SnapshotMismatch):
        shutil.rmtree(build, ignore_errors=True)
        raise
    try:
        build.rename(target)
    except OSError:
        shutil.rmtree(build, ignore_errors=True)
        verify_snapshot(target, captured)
    return target


# --- integrity: two observations (design §4.4) ---------------------------------
def bundle_identity(bundle: Path) -> str:
    """`capture_bundle`'s fold, recomputed over the copied tree. A read that
    fails is ClosureMutated: the observation could not be made."""
    try:
        return _fold([(path.relative_to(bundle).as_posix(), _digest(path)) for path in sorted(bundle.rglob("*")) if path.is_file()])
    except OSError as error:
        raise ClosureMutated(f"the bundle could not be read: {error}") from error


def fingerprint(root: Path) -> str:
    """Content and link-target fingerprint of a tree. A read that fails is
    ClosureMutated: the observation could not be made."""
    rows = []
    try:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows.append(f"{relative}\nsymlink\n{os.readlink(path)}\n")
            elif path.is_file():
                rows.append(f"{relative}\nfile\n{_digest(path)}\n")
    except OSError as error:
        raise ClosureMutated(f"{root} could not be read: {error}") from error
    return "sha256:" + sha256("".join(rows).encode()).hexdigest()


def check_bundle_intact(bundle: Path, code_identity: str) -> None:
    """The bundle's pre-bind observation: its fold still equals the recorded
    code identity. The snapshot's pre-bind pass is `materialize_snapshot`'s
    verification; the staged inputs' is the fingerprint the caller keeps."""
    if bundle_identity(bundle) != code_identity:
        raise ClosureMutated("the captured bundle no longer folds to its code identity")


def check_closure_intact(
    *,
    bundle: Path,
    code_identity: str,
    snapshot: Path,
    captured: CapturedEnvironment,
    inputs: Path,
    inputs_fingerprint: str,
) -> None:
    """The post-exit observation: one pass each over the bundle, the snapshot
    and the staged inputs, against what was recorded before the bind
    (design §4.4). Runs before the trace, the seeds or any output is read."""
    check_bundle_intact(bundle, code_identity)
    try:
        verify_snapshot(snapshot, captured)
    except SnapshotMismatch as error:
        raise ClosureMutated(f"the snapshot no longer matches its manifest: {error}") from error
    if fingerprint(inputs) != inputs_fingerprint:
        raise ClosureMutated("the staged inputs changed between the bind and exit")


# --- the mount plan -----------------------------------------------------------------
_ROLES = {"ro": "ro", "rw": "rw", "dev": "rw"}


@sealed
@final
@dataclass(frozen=True)
class MountPlan:
    """`binds` are (sandbox path, host source, ro|rw|dev) in bwrap order;
    `rows` is the canonical table the receipt carries, the implicit root first."""

    binds: tuple[tuple[str, str, str], ...]
    roles: tuple[str, ...]
    loader: str

    @property
    def rows(self) -> tuple[tuple[str, str, str], ...]:
        return (("/", "root", "ro"), *((sandbox, role, _ROLES[access]) for (sandbox, _, access), role in zip(self.binds, self.roles)))

    @property
    def expected(self) -> tuple[tuple[str, str, str], ...]:
        """The canonical planned table: the rows, sorted, one per mount."""
        return tuple(sorted(self.rows))

    def role_of(self, mountpoint: str) -> str:
        for point, role, _ in self.rows:
            if point == mountpoint:
                return role
        return UNPLANNED

    def identity(self) -> str:
        return mount_plan_identity(self.rows)

    def host_mapping(self) -> tuple[tuple[str, str], ...]:
        return tuple((sandbox, host) for sandbox, host, _ in self.binds)


def mount_plan(*, snapshot: Path, loader: str, bundle: Path, output_root: Path) -> MountPlan:
    return MountPlan(
        binds=(
            (loader, str(_within(snapshot, loader)), "ro"),
            (SANDBOX_ENV, str(_within(snapshot, SANDBOX_ENV)), "ro"),
            (BUNDLE_ROOT, str(bundle), "ro"),
            (OUTPUT_ROOT, str(output_root), "rw"),
            (INPUTS_ROOT, str(output_root / "inputs"), "ro"),
            (DEVICES[0], DEVICES[0], "dev"),
            (DEVICES[1], DEVICES[1], "dev"),
        ),
        roles=("loader", "env", "bundle", "output", "inputs", "device", "device"),
        loader=loader,
    )


def bwrap_argv(
    plan: MountPlan,
    environment: tuple[tuple[str, str], ...],
    inner_argv: tuple[str, ...],
    *,
    bwrap: str,
    info_fd: int,
    report_fd: int,
    go_fd: int,
) -> tuple[str, ...]:
    argv = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--uid",
        str(os.getuid()),
        "--gid",
        str(os.getgid()),
        "--hostname",
        HOSTNAME,
        "--clearenv",
    ]
    flags = {"ro": "--ro-bind", "rw": "--bind", "dev": "--dev-bind"}
    for sandbox, host, access in plan.binds:
        argv.extend([flags[access], host, sandbox])
    argv.extend(["--remount-ro", "/", "--chdir", OUTPUT_ROOT])
    for name, value in environment:
        argv.extend(["--setenv", name, value])
    argv.extend(["--info-fd", str(info_fd), "--"])
    argv.extend([f"{SANDBOX_VENV}/bin/python", "-m", PROBE_MODULE, "--report-fd", str(report_fd), "--go-fd", str(go_fd), "--loader", plan.loader, "--"])
    argv.extend(inner_argv)
    return tuple(argv)


# --- the observation, from this process's own /proc --------------------------------
def _unescape(field: str) -> str:
    return field.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")


def canonical_mounts(mountinfo: str, plan: MountPlan) -> tuple[tuple[str, str, str], ...]:
    """Every mount, one row each — a stacked or duplicate mount stays a row of
    its own — as (mountpoint, planned role or UNPLANNED, ro|rw), sorted. This
    is what the receipt's instance carries (design §6.1 step 3)."""
    observed: list[tuple[str, str, str]] = []
    for line in mountinfo.splitlines():
        fields = line.split()
        if len(fields) < 6:
            raise ConfinementNotEstablished(f"unparseable mountinfo line {line!r}")
        point = _unescape(fields[4])
        observed.append((point, plan.role_of(point), "ro" if "ro" in fields[5].split(",") else "rw"))
    return tuple(sorted(observed))


@sealed
@final
@dataclass(frozen=True)
class InstanceFacts:
    distinct: tuple[str, ...]
    mounts: tuple[tuple[str, str, str], ...]


def observe_instance(pid: int, plan: MountPlan) -> InstanceFacts:
    distinct = tuple(name for name in NAMESPACES if os.readlink(f"/proc/{pid}/ns/{name}") != os.readlink(f"/proc/self/ns/{name}"))
    return InstanceFacts(distinct, canonical_mounts(Path(f"/proc/{pid}/mountinfo").read_text(encoding="utf-8"), plan))


def judge_instance(facts: InstanceFacts, plan: MountPlan) -> None:
    if missing := [name for name in NAMESPACES if name not in facts.distinct]:
        raise ConfinementNotEstablished(f"namespaces equal to the parent's: {missing}")
    if facts.mounts != plan.expected:
        differences = sorted(set(facts.mounts) ^ set(plan.expected)) or [
            f"{len(facts.mounts)} observed rows against {len(plan.expected)} planned"
        ]
        raise ConfinementNotEstablished(f"observed mounts differ from the plan: {differences}")


def _expected_filesystem() -> dict[str, str]:
    return {
        "read:/etc/passwd": "ENOENT",
        "read:/tmp": "ENOENT",
        "write:/": "EROFS",
        f"write:{BUNDLE_ROOT}": "EROFS",
        f"write:{SANDBOX_ENV}": "EROFS",
        f"write:{INPUTS_ROOT}": "EROFS",
        f"write:{OUTPUT_ROOT}": "OK",
    }


def _terminal_digest(captured: CapturedEnvironment, path: str) -> str | None:
    """The digest of the file row a sandbox path reaches through the manifest's
    own symlink rows; None when it reaches no file row."""
    rows = {row_path: (kind, content) for row_path, kind, content in captured.manifest.artifacts}
    for _ in range(len(rows) + 1):
        row = rows.get(path)
        if row is None:
            return None
        kind, content = row
        if kind == "file":
            return content
        path = content if content.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(path), content))
    return None


def judge_report(
    report: Mapping[str, object],
    *,
    environment: tuple[tuple[str, str], ...],
    captured: CapturedEnvironment,
    inner_argv: tuple[str, ...],
) -> tuple[str, ...]:
    """The probe's report against what was declared. Every failure is a refusal;
    the graded case is reached by selecting the minimal policy, not here. A
    malformed shape raises KeyError or TypeError, which the launch wraps."""
    raw_environ = report["environ"]
    if not isinstance(raw_environ, Mapping):
        raise TypeError(f"malformed report: environ is {type(raw_environ).__name__!r}, not a mapping")
    environ = cast(Mapping[str, str], raw_environ)
    if dict(environ) != dict(environment):
        raise ConfinementNotEstablished(f"environment differs from the declared set: {sorted(set(environ.items()) ^ set(environment))}")
    if report["hostname"] != HOSTNAME:
        raise ConfinementNotEstablished(f"hostname {report['hostname']!r} is not {HOSTNAME!r}")
    if report["cwd"] != OUTPUT_ROOT:
        raise ConfinementNotEstablished(f"cwd {report['cwd']!r} is not {OUTPUT_ROOT!r}")
    filesystem = cast(Mapping[str, str], report["filesystem"])
    if dict(filesystem) != _expected_filesystem():
        raise ConfinementNotEstablished(f"filesystem probes differ: {sorted(set(filesystem.items()) ^ set(_expected_filesystem().items()))}")
    network = cast(Mapping[str, str], report["network"])
    if network["ipv4"] != "ENETUNREACH":
        raise ConfinementNotEstablished(f"network: IPv4 connect reported {network['ipv4']!r}, not ENETUNREACH")
    if network["ipv6"] not in _NETWORK_UNREACHABLE:
        raise ConfinementNotEstablished(f"network: IPv6 reported {network['ipv6']!r}, not one of {_NETWORK_UNREACHABLE}")
    expected: dict[str, dict[str, str]] = {elf: {} for elf in captured.loader_elves}
    for elf, soname, resolved in captured.loader_map:
        expected.setdefault(elf, {})[soname] = resolved
    reported = cast(Mapping[str, Mapping[str, object]], report["loader"])
    if set(reported) != set(expected):
        raise ConfinementNotEstablished(f"loader: the listed ELFs differ from the captured set: {sorted(set(reported) ^ set(expected))}")
    for elf, entry in reported.items():
        if entry["returncode"] != 0 or entry["unresolved"]:
            raise ConfinementNotEstablished(f"loader: {elf} exited {entry['returncode']} with unresolved {entry['unresolved']}")
        resolved_map = cast(Mapping[str, list[str]], entry["resolved"])
        if set(resolved_map) != set(expected[elf]):
            raise ConfinementNotEstablished(f"loader: {elf} lists {sorted(set(resolved_map) ^ set(expected[elf]))} differently from the capture")
        for soname, (path, digest) in resolved_map.items():
            if path != expected[elf][soname] or _terminal_digest(captured, path) != digest:
                raise ConfinementNotEstablished(f"loader: {elf} maps {soname} to {path} ({digest}), not the manifested {expected[elf][soname]}")
    snakefile = inner_argv[inner_argv.index("--snakefile") + 1]
    if not snakefile.startswith(f"{BUNDLE_ROOT}/"):
        raise ConfinementNotEstablished(f"the engine's snakefile {snakefile!r} is not under the bundle")
    return CAPABILITIES


# --- the gated launch ---------------------------------------------------------------
@sealed
@final
@dataclass(frozen=True)
class Launch:
    returncode: int
    output: str
    capabilities: tuple[str, ...]
    facts: InstanceFacts
    report: Mapping[str, object]


def _read_info(fd: int) -> int:
    """bubblewrap's info JSON, read until it parses; the child pid, or a refusal."""
    buffer = b""
    while True:
        chunk = os.read(fd, 4096)
        if not chunk:
            raise ConfinementNotEstablished("bubblewrap closed its info descriptor without reporting the child")
        buffer += chunk
        try:
            info = json.loads(buffer)
        except json.JSONDecodeError:
            continue
        child = info.get("child-pid") if isinstance(info, dict) else None
        if type(child) is not int:
            raise ConfinementNotEstablished("bubblewrap's info report names no integer child-pid")
        return child


def _read_report(fd: int) -> Mapping[str, object]:
    """The probe's JSON report followed by the READY line, read raw so the
    descriptor's ownership stays with the caller."""
    terminator = b"\nREADY\n"
    buffer = b""
    while terminator not in buffer:
        chunk = os.read(fd, 65536)
        if not chunk:
            raise ConfinementNotEstablished("the probe exited before reporting READY")
        buffer += chunk
    body, _, _ = buffer.partition(terminator)
    report = json.loads(body)
    if not isinstance(report, dict):
        raise ConfinementNotEstablished("the probe's report is not a JSON object")
    return cast(Mapping[str, object], report)


def _close(open_fds: set[int], *fds: int) -> None:
    """Close each descriptor exactly once."""
    for fd in fds:
        if fd in open_fds:
            open_fds.discard(fd)
            os.close(fd)


def _reap(process: subprocess.Popen[str]) -> str:
    """Terminate and reap a child whose gate failed; its output, for the detail."""
    process.terminate()
    try:
        output, _ = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    return output or ""


_PROTOCOL_FAILURES = (ConfinementNotEstablished, OSError, ValueError, TypeError, KeyError, AttributeError)


def launch_confined(
    *,
    plan: MountPlan,
    environment: tuple[tuple[str, str], ...],
    inner_argv: tuple[str, ...],
    captured: CapturedEnvironment,
) -> Launch:
    """Start bubblewrap with the held probe as its command; read the child pid;
    wait for the probe's report and READY; inspect that child's namespaces and
    mounts from this process's /proc; judge; then GO or close (design §6.1).

    Every failure between the start and GO — a refusal, a closed pipe,
    malformed info or report, a missing key, an unstartable process — is
    `ConfinementNotEstablished` (design §8: post-intent, never the pre-intent
    `ConfinementUnavailable`); the child is terminated and reaped and every
    descriptor closed on every path."""
    bwrap = shutil.which(_BWRAP)
    if bwrap is None:
        raise ConfinementNotEstablished("bubblewrap (bwrap) left PATH after intent")
    info_r, info_w = os.pipe()
    report_r, report_w = os.pipe()
    go_r, go_w = os.pipe()
    open_fds = {info_r, info_w, report_r, report_w, go_r, go_w}
    argv = bwrap_argv(plan, environment, inner_argv, bwrap=bwrap, info_fd=info_w, report_fd=report_w, go_fd=go_r)
    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            pass_fds=(info_w, report_w, go_r),
            env={},
        )
    except OSError as failure:
        _close(open_fds, *tuple(open_fds))
        raise ConfinementNotEstablished(f"bubblewrap could not be started: {failure}") from failure
    try:
        _close(open_fds, info_w, report_w, go_r)
        child = _read_info(info_r)
        report = _read_report(report_r)
        facts = observe_instance(child, plan)
        judge_instance(facts, plan)
        capabilities = judge_report(report, environment=environment, captured=captured, inner_argv=inner_argv)
        os.write(go_w, b"GO\n")
    except _PROTOCOL_FAILURES as failure:
        _close(open_fds, *tuple(open_fds))  # closing GO tells the probe to exit
        output = _reap(process)
        raise ConfinementNotEstablished(f"{failure}; sandbox output: {output.strip()[-2000:]}") from failure
    finally:
        _close(open_fds, *tuple(open_fds))
    output, _ = process.communicate()
    return Launch(process.returncode, output, capabilities, facts, report)
