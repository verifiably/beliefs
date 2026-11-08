"""Begin, execute, capture, and mint runs through the minimal adapter, or
through the confined policy's snapshot-and-sandbox path.

The scratch root is staging under the minimal policy and the host side of the
output root under the confined one. The boundary renders configuration,
environment, and argv, never the workflow definition. The ``.seeds`` channel
is cooperative job reporting whose claims conformance evaluates later. The input-safety rules are
enforced here: assessment runs require a frozen spec, URL/accession inputs are acquisition rather
than a run, and every declared input must already be held.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, final

from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs import stored
from beliefs.acquisition import bearer_refusal
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
    Launch,
    MountPlan,
    check_bundle_intact,
    check_closure_intact,
    fingerprint,
    launch_confined,
    materialize_snapshot,
    mount_plan,
    require_host,
    sandbox_environment,
)
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import (
    CheckpointDeclarationUnmet,
    ConfinementRefusal,
    DefinitionPlanMismatch,
    MalformedClosure,
    MalformedRecord,
    PermitExceeded,
    PlanUnavailable,
    ScienceError,
    TargetAmbiguous,
    TargetUnresolvable,
)
from beliefs.identity import v1
from beliefs.intents.publish import PublishIntent
from beliefs.production import mint_dataset
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
    job_key,
    project_recipe,
    supported_policy,
)
from beliefs.report import (
    ActReport,
    AssessmentRunIntent,
    Consolidated,
    Entry,
    ImportedRecords,
    LocatorEntry,
    Moved,
    OperationIntent,
    PublicationBindingEntry,
    RecordImportEntry,
    RecordMutationEntry,
    Registration,
    RunAttemptEntry,
    RunRefusal,
    SubjectEvaluationEntry,
    _mint_report,
    publish_sequence_error,
)
from beliefs.runrecord import OperationPort, publication_plan
from beliefs.sealed import sealed
from beliefs.spec import DATASET_EQUIVALENCE_RULE, SEED_DERIVATION_V1, FrozenSpec, NondeterminismContract, Seeded
from beliefs.tree import TREE_ALGORITHM, object_path, parse_tree_file

if TYPE_CHECKING:
    from beliefs.corpus import ReadView

__all__ = [
    "HeldTree",
    "RunMinted",
    "RunRefused",
    "acquisition_guard",
    "build_manifest",
    "check_checkpoint_declaration",
    "execute_assessment_run",
    "execute_production_run",
    "mint_run",
    "resolve_targets",
]

_INSTRUMENT = "beliefs.boundary/v1"
_DATASET_ALREADY_HELD = "dataset-already-held"


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
    and the act-report carry the stable reason alone."""


_TREE_DIGEST = re.compile(rf"^{TREE_ALGORITHM}:[0-9a-f]{{64}}$")


@sealed
@final
@dataclass(frozen=True)
class HeldTree:
    """A held tree resource: the store directory that holds it and its
    ``sha256-tree:`` digest. A ``held_inputs[address]`` mapping holds one for a
    resource name, and staging copies its members to
    ``inputs/<name>/<member path>``."""

    store_root: Path
    digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.store_root, Path):
            raise MalformedRecord(f"a held tree's store root {self.store_root!r} is not a path")
        if type(self.digest) is not str or _TREE_DIGEST.fullmatch(self.digest) is None:
            raise MalformedRecord(
                f"a held tree's digest {self.digest!r} is not `{TREE_ALGORITHM}:` and 64 lowercase hex digits"
            )


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


def acquisition_guard(run: RunClosure) -> Callable[[ReadView], str | None]:
    """Refuse a run that would produce a facet-bearing dataset."""
    _, _, (operation, *_) = publication_plan(run)
    proposed = node_from_markdown(operation.content.decode("utf-8"))

    def guard(view: ReadView) -> str | None:
        return "acquisition-boundary" if bearer_refusal(view, proposed) is not None else None

    return guard


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


def _mint_relocation_report(
    intent: OperationIntent,
    *,
    subject: str,
    corpus: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    outcome: Moved | Consolidated,
) -> ActReport:
    if type(intent) is not OperationIntent or intent.kind not in ("move", "consolidate"):
        raise MalformedRecord("a relocation report requires a move or consolidate operation intent")
    return _mint_report(
        operation=intent.kind,
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=(RecordMutationEntry(subject=subject, corpus=corpus, outcome=outcome),),
    )


def _mint_acquisition_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The acquisition operation's terminal record:
    per resource a locator entry and, where materialized, a mutation entry, in
    request order; then the declaration pin when a dataset minted."""
    if type(intent) is not OperationIntent or intent.kind != "acquisition":
        raise MalformedRecord("an acquisition report requires an acquisition operation intent")
    return _mint_report(
        operation="acquisition",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )


def _mint_audit_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The audit operation's terminal record:
    one subject-evaluation entry per finding, in the evaluator's order; a
    clean audit's entries are empty."""
    if type(intent) is not OperationIntent or intent.kind != "audit":
        raise MalformedRecord("an audit report requires an audit operation intent")
    if type(entries) is not tuple or any(type(entry) is not SubjectEvaluationEntry for entry in entries):
        raise MalformedRecord("an audit report carries subject-evaluation entries only")
    return _mint_report(
        operation="audit",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )


def _mint_publish_report(
    intent: PublishIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entry: PublicationBindingEntry,
    lifecycle: tuple[Entry, ...] = (),
) -> ActReport:
    """The publish report: the lifecycle entries in step order, then the one
    publication-binding entry, closing the domain-tagged
    publish intent and nothing else."""
    if type(intent) is not PublishIntent:
        raise MalformedRecord("a publish report closes a publish intent")
    if type(entry) is not PublicationBindingEntry:
        raise MalformedRecord("a publish report carries one publication-binding entry")
    if type(lifecycle) is not tuple:
        raise MalformedRecord("a publish report's lifecycle entries are a tuple")
    if (problem := publish_sequence_error((*lifecycle, entry))) is not None:
        raise MalformedRecord(problem)
    return _mint_report(
        operation="publish",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=(*lifecycle, entry),
    )


def _mint_publish_refusal(
    intent: PublishIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """A publish refused before its binding: the lifecycle
    entries reached, the refusing one last, or the request refusal alone."""
    if type(intent) is not PublishIntent:
        raise MalformedRecord("a publish report closes a publish intent")
    if type(entries) is not tuple or not entries or type(entries[-1]) is PublicationBindingEntry:
        raise MalformedRecord("a pre-binding refusal ends before the binding entry")
    if (problem := publish_sequence_error(entries)) is not None:
        raise MalformedRecord(problem)
    return _mint_report(
        operation="publish",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )


def _mint_recheck_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The re-check operation's terminal record: one locator entry per
    requested location, in request order."""
    if type(intent) is not OperationIntent or intent.kind != "re-check":
        raise MalformedRecord("a re-check report requires a re-check operation intent")
    if type(entries) is not tuple or any(type(entry) is not LocatorEntry for entry in entries):
        raise MalformedRecord("a re-check report carries locator entries only")
    return _mint_report(
        operation="re-check",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )


def _is_acquisition(address: str) -> bool:
    return "://" in address or address.startswith("accession:")


def _preflight(
    addresses: tuple[str, ...],
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
) -> str | None:
    if any(_is_acquisition(address) for address in addresses):
        return "acquisition-not-a-run"
    for address in addresses:
        if address not in held_inputs:
            return "input-not-held"
        source = held_inputs[address]
        if isinstance(source, Mapping) and not source:
            return "input-not-held"
    return None


_DIGEST = re.compile(rf"^(?:sha256|{TREE_ALGORITHM}):[0-9a-f]{{64}}$")


@dataclass(frozen=True)
class _InputConflict:
    reason: str


@dataclass(frozen=True)
class _RecipeContent:
    digest: str


def _content_identity(source_or_digests: str | Mapping[str, str]) -> str:
    if isinstance(source_or_digests, str):
        return source_or_digests
    if not isinstance(source_or_digests, Mapping) or not source_or_digests:
        raise MalformedClosure("resource digest mapping must be a non-empty mapping")
    if len(source_or_digests) == 1:
        return next(iter(source_or_digests.values()))
    declaration = DatasetDeclaration(
        resources=tuple(
            ResourceDeclaration(name=name, digest=digest) for name, digest in sorted(source_or_digests.items())
        )
    )
    addr = dataset_address(declaration)
    assert addr is not None
    return addr.removeprefix("dataset:")


def _validate_relative_input_path(name: str, inputs_dir: Path) -> Path:
    if type(name) is not str or not name or "\\" in name or name.startswith("/"):
        raise MalformedClosure(f"invalid relative input path {name!r}")
    parts = name.split("/")
    if any(not part or part in (".", "..") or part.startswith(".#~") for part in parts):
        raise MalformedClosure(f"invalid relative input path {name!r}")
    staged = (inputs_dir / name).resolve()
    if not staged.is_relative_to(inputs_dir.resolve()):
        raise MalformedClosure(f"relative input path {name!r} escapes staging directory")
    return staged


def _bind_recipe_inputs(
    inputs: tuple[RecipeInput, ...],
    expected_inputs: Mapping[str, object] | None,
) -> Mapping[str, object]:
    recipe_content: dict[str, str | _InputConflict] = {}
    for entry in inputs:
        existing = recipe_content.get(entry.dataset)
        if existing is None:
            recipe_content[entry.dataset] = entry.content
        elif type(existing) is not _InputConflict and existing != entry.content:
            recipe_content[entry.dataset] = _InputConflict(
                f"recipe inputs disagree on content identity for {entry.dataset!r}: {existing} vs {entry.content}"
            )
    if expected_inputs is None:
        return {
            address: value if isinstance(value, _InputConflict) else _RecipeContent(value)
            for address, value in recipe_content.items()
        }
    if not isinstance(expected_inputs, Mapping):
        return {address: _InputConflict("expected_inputs must be a mapping") for address in recipe_content}
    bound: dict[str, object] = dict(recipe_content)
    for address in list(recipe_content):
        if address not in expected_inputs:
            bound[address] = _InputConflict(f"expected input {address!r} is missing content identity")
    for address, expected in expected_inputs.items():
        if type(expected) is _InputConflict:
            bound[address] = expected
        elif address not in recipe_content:
            bound[address] = _InputConflict(f"expected input {address!r} is not in recipe inputs")
        elif type(recipe_content[address]) is _InputConflict:
            bound[address] = recipe_content[address]
        elif type(expected) is _RecipeContent:
            if expected.digest != recipe_content[address]:
                bound[address] = _InputConflict(
                    f"expected input {address!r} content identity {expected.digest} does not match recipe input {recipe_content[address]}"
                )
            else:
                bound[address] = expected
        elif type(expected) is str:
            if expected != recipe_content[address]:
                bound[address] = _InputConflict(
                    f"expected input {address!r} content identity {expected} does not match recipe input {recipe_content[address]}"
                )
            else:
                bound[address] = expected
        elif isinstance(expected, Mapping):
            if not expected or any(
                type(k) is not str or type(v) is not str or not _DIGEST.match(v) for k, v in expected.items()
            ):
                bound[address] = _InputConflict(f"expected input {address!r} has malformed resource digests")
            else:
                folded = _content_identity(expected)
                if folded != recipe_content[address]:
                    bound[address] = _InputConflict(
                        f"expected input {address!r} content identity {folded} does not match recipe input {recipe_content[address]}"
                    )
                else:
                    bound[address] = dict(expected)
        else:
            bound[address] = _InputConflict(f"expected input {address!r} is missing content identity")
    return bound


def _check_destinations(
    addresses: tuple[str, ...],
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    inputs_dir: Path,
) -> None:
    """Decide every staging collision before the first copy, so the outcome never
    depends on input order. A destination is a file resource's name or a tree
    resource's root, and it reserves its path and everything beneath it: no other
    destination may equal it or lie under it."""
    destinations: list[str] = []
    for address in dict.fromkeys(addresses):
        source = held_inputs[address]
        if isinstance(source, Path):
            destinations.append(source.name)
        elif isinstance(source, Mapping):
            destinations.extend(source)
    for name in destinations:
        _validate_relative_input_path(name, inputs_dir)
    reserved = frozenset(destinations)
    seen: set[str] = set()
    for name in sorted(destinations):
        parts = name.split("/")
        if name in seen or any("/".join(parts[:i]) in reserved for i in range(1, len(parts))):
            raise MalformedClosure(f"held inputs collide at staging name {name!r}")
        seen.add(name)


def _stage_tree(address: str, name: str, held: HeldTree, staged: Path) -> str:
    """Copy each member of a held tree to ``staged/<member path>``, one member at
    a time, after verifying the tree file against the tree's digest; every copy is
    re-hashed against its member's digest. Returns the tree's digest."""
    label = f"held input {address!r} resource {name!r}"
    tree_file = held.store_root / object_path(held.digest)
    if not tree_file.is_file() or tree_file.is_symlink():
        raise MalformedClosure(f"{label} tree file is not a readable file")
    data = tree_file.read_bytes()
    if f"{TREE_ALGORITHM}:{sha256(data).hexdigest()}" != held.digest:
        raise MalformedClosure(f"{label} tree file does not match its digest {held.digest}")
    try:
        tree = parse_tree_file(data)
    except MalformedRecord as error:
        raise MalformedClosure(f"{label} tree file does not parse: {error}") from error
    staged.mkdir(parents=True)
    for member in tree.members:
        source = held.store_root / object_path(member.digest)
        if not source.is_file() or source.is_symlink():
            raise MalformedClosure(f"{label} member {member.path!r} is not a readable file")
        target = staged / member.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if (copied := _digest(target)) != member.digest:
            raise MalformedClosure(f"{label} member {member.path!r} digest {copied} does not match {member.digest}")
    return held.digest


def _stage_inputs(
    addresses: tuple[str, ...],
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    scratch: Path,
    expected_inputs: Mapping[str, object] | None = None,
    *,
    staged_trees: list[Path],
) -> dict[str, str | dict[str, str]]:
    """Copy every held input into ``scratch/inputs`` and return the staged
    digests. A held tree is staged as the directory ``inputs/<name>``, which is
    appended to ``staged_trees`` before its first copy, so that the caller
    removes it when the run ends."""
    inputs_dir = scratch / "inputs"
    if expected_inputs is not None:
        if not isinstance(expected_inputs, Mapping):
            raise MalformedClosure("expected_inputs must be a mapping")
        for address, value in expected_inputs.items():
            if type(value) is _InputConflict:
                raise MalformedClosure(value.reason)
        for address in addresses:
            expected = expected_inputs.get(address)
            if type(expected) is str:
                if not _DIGEST.match(expected):
                    raise MalformedClosure(f"expected input {address!r} has malformed content identity")
            elif type(expected) is _RecipeContent:
                if type(expected.digest) is not str or not _DIGEST.match(expected.digest):
                    raise MalformedClosure(f"expected input {address!r} has malformed content identity")
            elif isinstance(expected, Mapping):
                if not expected:
                    raise MalformedClosure(f"expected input {address!r} has malformed resource digests")
                for rel_name, member_digest in expected.items():
                    _validate_relative_input_path(rel_name, inputs_dir)
                    if type(member_digest) is not str or not _DIGEST.match(member_digest):
                        raise MalformedClosure(f"expected input {address!r} has malformed resource digests")
            else:
                raise MalformedClosure(f"expected input {address!r} is missing content identity")
    _check_destinations(addresses, held_inputs, inputs_dir)
    inputs_dir.mkdir()
    staged_out: dict[str, str | dict[str, str]] = {}
    for address in addresses:
        if address in staged_out:
            continue
        source = held_inputs[address]
        if isinstance(source, Path):
            if not source.is_file() or source.is_symlink():
                raise MalformedClosure(f"held input {address!r} is not a readable file")
            expected_digest: str | None = None
            if expected_inputs is not None:
                expected_val = expected_inputs[address]
                if isinstance(expected_val, Mapping):
                    raise MalformedClosure(f"expected input {address!r} is a mapping for a single-file input")
                expected_digest = expected_val.digest if type(expected_val) is _RecipeContent else str(expected_val)
            staged = inputs_dir / source.name
            shutil.copy2(source, staged)
            digest = _digest(staged)
            if expected_digest is not None and digest != expected_digest:
                raise MalformedClosure(
                    f"held input {address!r} digest {digest} does not match expected {expected_digest}"
                )
            staged_out[address] = digest
        elif isinstance(source, Mapping):
            if not source:
                raise MalformedClosure(f"held input {address!r} is an empty resource mapping")
            expected_entry = expected_inputs[address] if expected_inputs is not None else None
            if expected_entry is not None:
                if isinstance(expected_entry, Mapping):
                    if set(expected_entry.keys()) != set(source.keys()):
                        raise MalformedClosure(
                            f"held input {address!r} resources {sorted(source.keys())} do not match expected {sorted(expected_entry.keys())}"
                        )
                elif type(expected_entry) is not _RecipeContent:
                    raise MalformedClosure(
                        f"expected input {address!r} must map resource names to digests for a multi-resource input"
                    )
            staged_digests: dict[str, str] = {}
            for rel_name, resource in sorted(source.items()):
                staged = _validate_relative_input_path(rel_name, inputs_dir)
                if type(resource) is HeldTree:
                    staged_trees.append(staged)
                    member_digest = _stage_tree(address, rel_name, resource, staged)
                else:
                    if not isinstance(resource, Path) or not resource.is_file() or resource.is_symlink():
                        raise MalformedClosure(f"held input {address!r} resource {rel_name!r} is not a readable file")
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(resource, staged)
                    member_digest = _digest(staged)
                if isinstance(expected_entry, Mapping) and member_digest != expected_entry[rel_name]:
                    raise MalformedClosure(
                        f"held input {address!r} resource {rel_name!r} digest {member_digest} does not match expected {expected_entry[rel_name]}"
                    )
                staged_digests[rel_name] = member_digest
            composite = _content_identity(staged_digests)
            if type(expected_entry) is _RecipeContent and composite != expected_entry.digest:
                raise MalformedClosure(
                    f"held input {address!r} digest {composite} does not match expected {expected_entry.digest}"
                )
            staged_out[address] = staged_digests
        else:
            raise MalformedClosure(f"held input {address!r} is not a readable file")
    return staged_out


def _render_config(recipe: Recipe, _definition: WorkflowDefinition | WorkflowDefinitionSnapshot) -> dict[str, str]:
    config = {key: str(value) for key, value in recipe.parameters.items()}
    reserved = {"seed_roots", "seed_derivation_rule"}
    if collisions := sorted(reserved & set(config)):
        raise MalformedClosure(f"recipe parameters collide with boundary seed config: {collisions}")
    if type(recipe.nondeterminism) is not Seeded:
        return config

    plan = recipe.nondeterminism.plan
    if plan.derivation_rule != SEED_DERIVATION_V1:
        raise MalformedClosure(f"unsupported seed derivation rule {plan.derivation_rule!r}")
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
        raise CheckpointDeclarationUnmet(f"checkpoint-expanded families the definition does not contain: {unknown}")
    if declared and not any(job.is_checkpoint for job in planned):
        raise CheckpointDeclarationUnmet(
            f"checkpoint-expanded families {sorted(declared)} declared, but the plan contains no checkpoint"
        )


def resolve_targets(
    targets: tuple[str, ...],
    planned: tuple[PlannedJob, ...],
) -> tuple[str, ...]:
    resolved: list[str] = []
    for target in targets:
        matches = [job for job in planned if job.job_key == job_key(target, ()) or target in job.outputs]
        if not matches:
            raise TargetUnresolvable(f"the plan names no job for target {target!r}")
        if len(matches) > 1:
            raise TargetAmbiguous(f"target {target!r} matches {len(matches)} planned jobs")
        resolved.append(matches[0].job_key)
    return tuple(resolved)


def _check_definition_plan(
    definition: WorkflowDefinition,
    nondeterminism: NondeterminismContract,
) -> None:
    from beliefs.replay import definition_agrees_with_plan

    plan = nondeterminism.plan if type(nondeterminism) is Seeded else None
    if reason := definition_agrees_with_plan(definition.snapshot(), plan):
        raise DefinitionPlanMismatch(f"definition/plan mismatch: {reason}")


def _confined_attestation(
    *,
    scratch_mapping: Path,
    argv: tuple[str, ...],
    config: Mapping[str, str],
    launched: Launch,
    plan: MountPlan,
    snapshot: Path,
    captured: CapturedEnvironment,
    environment: tuple[tuple[str, str], ...],
) -> LaunchAttestation:
    return LaunchAttestation(
        scratch_mapping=str(scratch_mapping),
        argv=argv,
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
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    expected_inputs: Mapping[str, object] | None = None,
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
    staged_trees: list[Path],
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
        expected = expected_inputs if spec is not None else _bind_recipe_inputs(inputs, expected_inputs)
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
                expected_inputs=expected,
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
                staged_trees=staged_trees,
            )
        staged = _stage_inputs(addresses, held_inputs, scratch, expected, staged_trees=staged_trees)
        held = {address: _content_identity(entry) for address, entry in staged.items()}
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

        config = _render_config(recipe, definition)
        _check_definition_plan(definition, recipe.nondeterminism)

        planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))
        try:
            planning_handler = planning_dir / "handler.py"
            planning_events = planning_dir / "events.jsonl"
            planning_handler.write_text(LOG_HANDLER_SCRIPT)
            _stage_inputs(addresses, held_inputs, planning_dir, staged, staged_trees=staged_trees)
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
            planning_returncode, _ = run_engine(
                planning_argv,
                cwd=planning_dir,
                env={**os.environ, "SCIENCE_TRACE_FILE": str(planning_events)},
            )
            if planning_returncode != 0:
                raise PlanUnavailable(f"the planning launch exited {planning_returncode}")
            planned_jobs = read_plan(planning_events)
            check_checkpoint_declaration(definition.snapshot(), planned_jobs)
            target_keys = resolve_targets(targets, planned_jobs)
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
            target_keys=target_keys,
            realized_seeds=realized_seeds,
            receipt=receipt,
        )
        manifest = build_manifest(declared_outputs, scratch)
        run = mint_run(recipe, manifest, occurrence, scratch)
        return RunMinted(run, intent, Registration(intent.event_token, run.address()))
    except ConfinementRefusal as error:
        return _refused(getattr(error, "reason"), subject, actor, observer, started_at, intent, detail=str(error))  # noqa: B009 — ConfinementRefusal's base deliberately carries no `reason`; every raised instance is a named subclass that does
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
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    expected_inputs: Mapping[str, object] | None = None,
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
    staged_trees: list[Path],
) -> RunMinted | RunRefused:
    """The scratch root's ``out/`` is the host side of
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
    staged = _stage_inputs(addresses, held_inputs, output_root, expected_inputs, staged_trees=staged_trees)
    held = {address: _content_identity(entry) for address, entry in staged.items()}
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
    _check_definition_plan(definition, recipe.nondeterminism)
    trace_file = f"{OUTPUT_ROOT}/{TRACE_DIR}/events.jsonl"
    relative_entrypoint = captured_entrypoint.relative_to(bundle.resolve()).as_posix()
    environment = sandbox_environment(trace_file)
    snapshot = materialize_snapshot(captured, scratch_base / "environments")
    check_bundle_intact(bundle, code_identity)
    inputs_before = fingerprint(output_root / "inputs")

    planning_root = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))
    try:
        (planning_root / TRACE_DIR).mkdir()
        (planning_root / HOME_DIR).mkdir()
        _stage_inputs(addresses, held_inputs, planning_root, staged, staged_trees=staged_trees)
        (planning_root / TRACE_DIR / "handler.py").write_text(LOG_HANDLER_SCRIPT)
        planning_argv = build_argv(
            interpreter=f"{SANDBOX_VENV}/bin/python",
            snakefile=f"{BUNDLE_ROOT}/{relative_entrypoint}",
            directory=OUTPUT_ROOT,
            targets=targets,
            config=config,
            log_handler=f"{OUTPUT_ROOT}/{TRACE_DIR}/handler.py",
            cores=cores,
            in_process_jobs=True,
            dry_run=True,
        )
        planning_plan = mount_plan(
            snapshot=snapshot,
            loader=captured.loader,
            bundle=bundle,
            output_root=planning_root,
        )
        planning_inputs_before = fingerprint(planning_root / "inputs")
        planning_result = launch_confined(
            plan=planning_plan,
            environment=environment,
            inner_argv=planning_argv,
            captured=captured,
        )
        check_closure_intact(
            bundle=bundle,
            code_identity=code_identity,
            snapshot=snapshot,
            captured=captured,
            inputs=planning_root / "inputs",
            inputs_fingerprint=planning_inputs_before,
        )
        if planning_result.returncode != 0:
            raise PlanUnavailable(f"the confined planning launch exited {planning_result.returncode}")
        planned_jobs = read_plan(planning_root / TRACE_DIR / "events.jsonl")
        check_checkpoint_declaration(definition.snapshot(), planned_jobs)
        target_keys = resolve_targets(targets, planned_jobs)
        planning_launch = _confined_attestation(
            scratch_mapping=planning_root,
            argv=planning_argv,
            config=config,
            launched=planning_result,
            plan=planning_plan,
            snapshot=snapshot,
            captured=captured,
            environment=environment,
        )
    finally:
        shutil.rmtree(planning_root, ignore_errors=True)

    handler = output_root / TRACE_DIR / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    execution_argv = build_argv(
        interpreter=f"{SANDBOX_VENV}/bin/python",
        snakefile=f"{BUNDLE_ROOT}/{relative_entrypoint}",
        directory=OUTPUT_ROOT,
        targets=targets,
        config=config,
        log_handler=f"{OUTPUT_ROOT}/{TRACE_DIR}/handler.py",
        cores=cores,
        in_process_jobs=True,
    )
    execution_plan = mount_plan(
        snapshot=snapshot,
        loader=captured.loader,
        bundle=bundle,
        output_root=output_root,
    )
    launched = launch_confined(
        plan=execution_plan,
        environment=environment,
        inner_argv=execution_argv,
        captured=captured,
    )
    check_closure_intact(
        bundle=bundle,
        code_identity=code_identity,
        snapshot=snapshot,
        captured=captured,
        inputs=output_root / "inputs",
        inputs_fingerprint=inputs_before,
    )
    if launched.returncode != 0:
        return _refused(
            "execution-failed", subject, actor, observer, started_at, intent, detail=launched.output[-2000:]
        )
    trace = read_trace(output_root / TRACE_DIR / "events.jsonl")
    realized_seeds = read_realized_seeds(output_root)
    execution_launch = _confined_attestation(
        scratch_mapping=scratch,
        argv=execution_argv,
        config=config,
        launched=launched,
        plan=execution_plan,
        snapshot=snapshot,
        captured=captured,
        environment=environment,
    )
    receipt = BoundaryReceipt(planning=planning_launch, execution=execution_launch)
    occurrence = Occurrence(
        event_token=intent.event_token,
        started_at=started_at,
        actor=actor,
        host_realization=host_realization,
        trace=trace,
        planned=planned_jobs,
        target_keys=target_keys,
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
    expected_inputs: Mapping[str, str | Mapping[str, str]] | None = None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
) -> RunMinted | RunRefused:
    try:
        port.authority.require("run", ("run", "act-report"))
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    actor = port.authority.actor
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
    staged_trees: list[Path] = []
    try:
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
            expected_inputs=expected_inputs,
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
            staged_trees=staged_trees,
        )
    finally:
        _remove_staged_trees(staged_trees)
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


def _remove_staged_trees(staged_trees: list[Path]) -> None:
    """Remove the run's staged tree directories when it ends: science never
    deletes run scratch, so a staged copy of a tree would otherwise outlive the
    run. A removal that fails is ignored, as the planning directory's is, so it
    never replaces the run's outcome."""
    for staged in staged_trees:
        shutil.rmtree(staged, ignore_errors=True)


def _cleanup_exported(created_files: list[Path], created_dirs: list[Path]) -> None:
    for f in reversed(created_files):
        f.unlink(missing_ok=True)
    for d in reversed(created_dirs):
        try:
            d.rmdir()
        except OSError:
            pass


def execute_production_run(
    *,
    inputs: tuple[RecipeInput, ...],
    port: OperationPort,
    boundary_policy: BoundaryPolicy,
    expected_recipe_identity: str | None = None,
    expected_inputs: Mapping[str, str | Mapping[str, str]] | None = None,
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path | Mapping[str, Path | HeldTree]],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
    dataset_title: str = "produced dataset",
    output_dir: Path | None = None,
) -> RunMinted | RunRefused:
    try:
        port.authority.require("run", ("run", "dataset", "act-report"))
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    actor = port.authority.actor
    transform_datasets = (
        tuple(dict.fromkeys(entry.dataset for entry in inputs if entry.role == "transforms"))
        if type(inputs) is tuple and all(type(entry) is RecipeInput for entry in inputs)
        else ()
    )
    if (
        type(inputs) is not tuple
        or any(type(entry) is not RecipeInput for entry in inputs)
        or len(transform_datasets) != 1
        or type(dataset_title) is not str
        or not dataset_title.strip()
        or (
            output_dir is not None
            and (not isinstance(output_dir, Path) or output_dir.is_symlink() or not output_dir.is_dir())
        )
    ):
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
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    staged_trees: list[Path] = []
    try:
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
            expected_inputs=expected_inputs,
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
            staged_trees=staged_trees,
        )
        if (
            type(result) is RunMinted
            and expected_recipe_identity is not None
            and result.run.recipe.identity() != expected_recipe_identity
        ):
            result = _refused("recipe-identity-mismatch", "absent", actor, observer, started_at, intent)
        if type(result) is RunMinted and output_dir is not None:
            scratch_root = Path(result.run.occurrence.receipt.execution.scratch_mapping)
            run_output_root = scratch_root / "out" if result.run.occurrence.receipt.confined else scratch_root
            resolved_output_dir = output_dir.resolve()
            try:
                for out_name, out_digest in result.run.result.outputs:
                    dest = _validate_relative_input_path(out_name, resolved_output_dir)
                    if dest.exists() or dest.is_symlink():
                        raise OSError(f"export destination {dest} already exists")
                    missing_ancestors: list[Path] = []
                    cur = dest.parent
                    while cur != resolved_output_dir and not cur.exists():
                        missing_ancestors.append(cur)
                        cur = cur.parent
                    for ancestor in reversed(missing_ancestors):
                        ancestor.mkdir()
                        created_dirs.append(ancestor)
                    created_files.append(dest)
                    shutil.copy2(run_output_root / out_name, dest)
                    if _digest(dest) != out_digest:
                        raise ValueError(f"exported output {out_name!r} digest mismatch")
            except (ScienceError, OSError, ValueError):
                _cleanup_exported(created_files, created_dirs)
                result = _refused("manifest-digest-mismatch", "absent", actor, observer, started_at, intent)
    finally:
        _remove_staged_trees(staged_trees)
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run, dataset_title=dataset_title)
        run_op = plan[0]
        produced_address = mint_dataset(result.run, existing_bases={}).address
        ac_guard = acquisition_guard(result.run)

        def _guard(view: ReadView) -> str | None:
            if (reason := ac_guard(view)) is not None:
                return reason
            if view.holds(produced_address):
                return _DATASET_ALREADY_HELD
            return None

        def _fallback(reason: str) -> WritePlan:
            if reason == _DATASET_ALREADY_HELD:
                return (run_op,)
            return _report_plan(_refused(reason, "absent", actor, observer, started_at, intent).report)

        reason = port.execute_fulfilling_guarded(plan, fulfills, guard=_guard, fallback=_fallback).reason
        if reason not in (None, _DATASET_ALREADY_HELD):
            _cleanup_exported(created_files, created_dirs)
            result = _refused(reason, "absent", actor, observer, started_at, intent)
    else:
        port.execute_fulfilling(_report_plan(result.report), fulfills)
    return result
