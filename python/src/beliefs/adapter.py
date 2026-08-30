"""Minimal Snakemake execution adapter and held-content capture."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import cast, final

from beliefs.errors import MalformedClosure, UnsafeInvocation
from beliefs.identity import v1
from beliefs.recipe import EnvironmentManifest, TraceJob
from beliefs.sealed import sealed
from beliefs.spec import RealizedSeeds

WORKFLOW_DEFINITION_DOMAIN = "science.workflow-definition.v1"
_CONFIG_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PEP_503_RUN = re.compile(r"[-_.]+")

LOG_HANDLER_SCRIPT = """\
import json
import os

_EVENTS = os.environ["SCIENCE_TRACE_FILE"]


def log_handler(msg):
    if msg.get("level") == "job_info":
        with open(_EVENTS, "a", encoding="utf-8") as events:
            events.write(json.dumps(msg, default=str) + "\\n")
"""


@sealed
@final
@dataclass(frozen=True)
class WorkflowDefinition:
    snakefile: bytes
    family_streams: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if type(self.snakefile) is not bytes:
            raise MalformedClosure("workflow definition snakefile must be bytes")
        if not isinstance(self.family_streams, Mapping) or not all(
            type(family) is str and type(streams) is tuple and all(type(stream) is str for stream in streams)
            for family, streams in self.family_streams.items()
        ):
            raise MalformedClosure("workflow family streams must map strings to tuples of strings")
        object.__setattr__(self, "family_streams", MappingProxyType(dict(self.family_streams)))

    def identity(self) -> str:
        return v1.digest(
            WORKFLOW_DEFINITION_DOMAIN,
            {
                "snakefile": "sha256:" + sha256(self.snakefile).hexdigest(),
                "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},
            },
        )


def _file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _fold(rows: list[tuple[str, str]]) -> str:
    folded = "".join(f"{name}\n{digest}\n" for name, digest in sorted(rows)).encode()
    return "sha256:" + sha256(folded).hexdigest()


def create_scratch_root(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=base))


def capture_bundle(code_roots: tuple[Path, ...], bundle_dir: Path) -> str:
    rows: list[tuple[str, str]] = []
    names: set[str] = set()
    bundle_dir.mkdir(parents=True)
    for root in code_roots:
        for source in sorted(root.rglob("*")):
            relative = source.relative_to(root)
            if ".git" in relative.parts or not source.is_file():
                continue
            name = (Path(root.name) / relative).as_posix()
            if name in names:
                raise MalformedClosure(f"code roots map more than one file to bundle path {name!r}")
            names.add(name)
            target = bundle_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            rows.append((name, _file_digest(target)))
    return _fold(rows)


def _distribution_cache(parts: tuple[str, ...]) -> bool:
    return "__pycache__" in parts or bool(parts and parts[-1].endswith(".pyc"))


def _stdlib_excluded(parts: tuple[str, ...]) -> bool:
    return "site-packages" in parts or _distribution_cache(parts)


def tree_digest(root: Path, *, label: str) -> str:
    """Fold a file tree under location-independent logical names."""
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if _stdlib_excluded(relative.parts) or not path.is_file():
            continue
        rows.append((f"{label}/{relative.as_posix()}", _file_digest(path)))
    return _fold(rows)


def distribution_digest(dist: importlib.metadata.Distribution) -> str:
    """Fold all non-derived files enumerated by a distribution RECORD."""
    name = dist.metadata["Name"]
    record = dist.read_text("RECORD")
    if not record:
        raise MalformedClosure(f"distribution {name!r} has no readable RECORD — its inventory cannot be enumerated")
    rows = []
    for row in csv.reader(record.splitlines()):
        if not row or not row[0]:
            raise MalformedClosure(f"distribution {name!r} has a malformed RECORD entry")
        entry = importlib.metadata.PackagePath(row[0])
        if _distribution_cache(entry.parts):
            continue
        located = Path(str(dist.locate_file(entry)))
        if not located.is_file():
            raise MalformedClosure(f"distribution {name!r}: RECORD lists {entry} and no such file exists")
        rows.append((entry.as_posix(), _file_digest(located)))
    return _fold(rows)


def _stdlib_digest() -> str:
    labelled = {
        ("stdlib", Path(sysconfig.get_path("stdlib")).resolve()),
        ("platstdlib", Path(sysconfig.get_path("platstdlib")).resolve()),
    }
    return _fold([(label, tree_digest(root, label=label)) for label, root in sorted(labelled)])


def _canonical_distribution_name(name: str) -> str:
    return _PEP_503_RUN.sub("-", name).lower()


def capture_environment() -> EnvironmentManifest:
    rows = {
        ("python", _file_digest(Path(sys.executable).resolve())),
        ("stdlib", _stdlib_digest()),
    }
    for dist in importlib.metadata.distributions():
        name = _canonical_distribution_name(dist.metadata["Name"])
        rows.add((f"dist:{name}", distribution_digest(dist)))
    return EnvironmentManifest(artifacts=tuple(sorted(rows)))


def require_executing_environment(manifest: EnvironmentManifest) -> None:
    if manifest != capture_environment():
        raise MalformedClosure(
            "the recorded environment is not the executing environment — a recipe claiming "
            "environment A cannot run in environment B through this boundary (§4.5)"
        )


def validate_entrypoint(bundle_dir: Path, entrypoint: str) -> Path:
    bundle = bundle_dir.resolve()
    candidate = (bundle / entrypoint).resolve()
    if not candidate.is_relative_to(bundle) or not candidate.is_file():
        raise UnsafeInvocation(f"entrypoint {entrypoint!r} must resolve to a regular file inside the captured bundle")
    return candidate


def build_argv(
    *,
    snakefile: Path,
    scratch: Path,
    targets: tuple[str, ...],
    config: Mapping[str, str],
    log_handler: Path,
    cores: int,
) -> tuple[str, ...]:
    for target in targets:
        if target.startswith("-"):
            raise UnsafeInvocation(
                f"target {target!r} is option-like; shell=False prevents shell injection, "
                "not option injection — targets are separated from options (cut 3 §3)"
            )
    for key in config:
        if not _CONFIG_KEY.fullmatch(key):
            raise UnsafeInvocation(f"config key {key!r} is not an identifier and could parse as an option")
    argv = [
        sys.executable,
        "-m",
        "snakemake",
        "--snakefile",
        str(snakefile),
        "--cores",
        str(cores),
        "--directory",
        str(scratch),
        "--nolock",
        "--log-handler-script",
        str(log_handler),
    ]
    if config:
        argv.append("--config")
        argv.extend(f"{key}={value}" for key, value in sorted(config.items()))
    argv.append("--")
    argv.extend(targets)
    return tuple(argv)


def run_engine(argv: tuple[str, ...], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
    completed = subprocess.run(
        list(argv), shell=False, capture_output=True, text=True, cwd=cwd, env=dict(env), check=False
    )
    return completed.returncode, completed.stdout + completed.stderr


def read_trace(events_file: Path) -> tuple[TraceJob, ...]:
    try:
        lines = events_file.read_text().splitlines()
    except (OSError, UnicodeError) as error:
        raise MalformedClosure("the engine trace is missing or unreadable") from error
    if not lines:
        raise MalformedClosure("the engine trace is empty")

    trace = []
    jobs_by_id: dict[str, TraceJob] = {}
    for line in lines:
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, UnicodeError) as error:
            raise MalformedClosure("the engine trace contains an unparseable record") from error
        if not isinstance(record, dict) or record.get("level") != "job_info":
            raise MalformedClosure("the engine trace contains a non-job_info record")
        required = ("jobid", "name", "input", "output", "wildcards")
        if any(name not in record for name in required):
            raise MalformedClosure("the engine trace record is missing a required member")
        job_id, rule = record["jobid"], record["name"]
        inputs, outputs, wildcards = record["input"], record["output"], record["wildcards"]
        if (
            type(job_id) not in (int, str)
            or str(job_id) == ""
            or type(rule) is not str
            or not rule
            or type(inputs) is not list
            or not all(type(value) is str for value in inputs)
            or type(outputs) is not list
            or not all(type(value) is str for value in outputs)
            or not isinstance(wildcards, dict)
            or not all(type(key) is str and type(value) is str for key, value in wildcards.items())
        ):
            raise MalformedClosure("the engine trace record has a malformed required member")
        job = TraceJob(
            job_id=str(job_id),
            rule=rule,
            wildcards=tuple(sorted(cast(dict[str, str], wildcards).items())),
            inputs=tuple(inputs),
            outputs=tuple(outputs),
        )
        previous = jobs_by_id.get(job.job_id)
        if previous is not None and previous != job:
            raise MalformedClosure(f"engine job ID {job.job_id!r} has conflicting required trace fields")
        if previous is None:
            jobs_by_id[job.job_id] = job
            trace.append(job)
    return tuple(trace)


def read_realized_seeds(scratch: Path) -> RealizedSeeds:
    reports = scratch / ".seeds"
    if reports.is_symlink():
        raise MalformedClosure("the seed-report path is a symlink, not a boundary-owned directory")
    if not reports.exists():
        return RealizedSeeds(seeds={})
    if not reports.is_dir():
        raise MalformedClosure("the seed-report path exists but is not a directory")

    merged: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, str]] = set()
    for report in sorted(reports.glob("*.json")):
        try:
            record = json.loads(report.read_text(), object_pairs_hook=_object_without_duplicate_keys)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise MalformedClosure(f"seed report {report.name!r} is unreadable") from error
        if not isinstance(record, dict):
            raise MalformedClosure(f"seed report {report.name!r} is not nested by job and stream")
        for job, per_stream in record.items():
            if type(job) is not str or not isinstance(per_stream, dict):
                raise MalformedClosure(f"seed report {report.name!r} is not nested by job and stream")
            for stream, seed in per_stream.items():
                if type(stream) is not str or type(seed) is not int:
                    raise MalformedClosure(f"seed report {report.name!r} has a malformed claim")
                key = (job, stream)
                if key in seen:
                    raise MalformedClosure(f"seed report repeats claim {job!r}/{stream!r}")
                seen.add(key)
                merged.setdefault(job, {})[stream] = seed
    return RealizedSeeds(seeds=merged)


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, member in pairs:
        if key in value:
            raise MalformedClosure(f"seed report repeats JSON object key {key!r}")
        value[key] = member
    return value
