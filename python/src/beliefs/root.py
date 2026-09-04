"""The composition root — the one module that imports `atoms`.

Science's durable corpus writes flow through the certified `atoms` engine, and
everything the engine needs that is not a plan is decided here: the volume
binding, the explicit root-registration act, the durable executor that compiles
one `nodes` write plan into one `TransactionSpec`, and the root-taking factory
the write API is built with (adapter design §1–§4).

**Why this module and no other.** `atoms` types are engine capability. Confining
their import to the composition root is an architecture rule, checked as one —
distinct from S8's capability boundary, which is about who holds a *mutable
corpus handle* and is checked over `beliefs.corpus`. Two boundaries, two checks,
neither standing in for the other.

**The corpus supplies its own root.** The factory this module hands the write
API is `(root: Path) -> DurableExecutor`, using the module-bound backend and
storage profile and deriving the metadata root by §2's sibling rule. A
pre-bound executor would let the corpus write through a root it never verified.

**The log seam is the same discipline over reads.** Verification needs to
inspect a chain, state a surface, read a head and take two locks; it gets all
five as callables on one `LogSeam`, typed in Science's own vocabulary, built
here and nowhere else (log-verification design §2, §6.4).
"""

from __future__ import annotations

import io
import secrets
import stat as stat_module
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import IO, cast

from atoms.chain.errors import ChainStateInvalid, PendingUnresolved
from atoms.chain.inspect import AbsentChain, ChainInspection, DefectKind, MalformedChain, WellFormedChain
from atoms.chain.model import (
    ChainOutcome,
    Entry,
    GenesisEntry,
    IntentEntry,
    PathStateJSON,
    RegisteredEntry,
    SettledEntry,
    state_from_json,
    state_to_json,
)
from atoms.coordinator.commands import (
    DestinationOverride,
    LifecycleState,
    PathObserved,
    ReadNotAttempted,
    ReadUnestablished,
    RootOperationId,
    RootOperationInvalid,
    RootOperationMismatch,
    SourceSnapshotMoved,
    TransactionOutcome,
    append_intent,
    capture_states,
    inspect_chain,
    inspect_chain_detached,
    read_chain,
    read_path_state,
    register_root,
    run_transaction,
)
from atoms.coordinator.commands import (
    fork_root as _fork_root_callback,
)
from atoms.coordinator.commands import (
    grant_read_serviceability as _grant_read_serviceability_callback,
)

# The seven lifecycle commands, imported as the private callback aliases the
# lifecycle wrappers and the fork/restore acts consume — same seam discipline
# as `chain_head_reader`: root.py names every engine command (the boundary
# roster reads import sources too), and nothing above it does. Three of the
# wrappers deliberately re-bind the engine names with Path-taking signatures,
# which is why the engine's own arrive aliased rather than shadowed.
from atoms.coordinator.commands import (
    migrate_root_to_lifecycle_v3 as _migrate_root_to_lifecycle_v3_callback,
)
from atoms.coordinator.commands import (
    read_lifecycle_state as _read_lifecycle_state_callback,
)
from atoms.coordinator.commands import (
    read_pending_fork_operation as _read_pending_fork_operation_callback,
)
from atoms.coordinator.commands import replicate_root as _replicate_root_callback
from atoms.coordinator.commands import (
    resume_fork_root as _resume_fork_root_callback,
)
from atoms.core.effects import (
    CreateDirectory,
    CreateFileNoClobber,
    DeletePath,
    Effect,
    MoveNoClobber,
    ReplaceFile,
)
from atoms.core.errors import (
    AtomsError,
    CapabilityUnavailable,
    PreconditionRefused,
    ProjectApprovalRefused,
    ProtocolError,
    SpecValidationError,
    TransactionHalted,
)
from atoms.core.fingerprint import (
    ABSENT,
    AbsentState,
    DirectoryState,
    FileState,
    PathState,
    SymlinkState,
)
from atoms.core.paths import require_rel_path
from atoms.core.scratch import SCRATCH_SIGIL
from atoms.core.spec import TransactionSpec, build_spec
from atoms.fs.backend import Backend
from atoms.fs.platform import select_backend
from atoms.fs.volume import StorageProfile
from atoms.store.errors import MetadataStoreInvalid
from nodes.core.errors import ExecutionError, PlanRefusedError
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp, WritePlan, validate_plan

from beliefs.corpus import CoordinationResolver, CorpusWriter, _operation_lock_for
from beliefs.errors import CorpusRootRefused, LogEvidenceRefused, WorldIdMismatch, WorldUninitialized
from beliefs.holdings.seam import (
    AbsentStateView,
    FileStateView,
    NonRegularStateView,
    PathObservedView,
    PathReadView,
    PathStateView,
    ReadNotAttemptedView,
    ReadUnestablishedView,
    StoreActSeam,
    StoreOutcomeView,
)
from beliefs.holdings.seam import WritePlan as SeamWritePlan
from beliefs.identity import v1
from beliefs.permit import Authority
from beliefs.world import (
    AdmissionRecord,
    CorpusSubject,
    LogHeadRecord,
    ReplicaOf,
    StoreSubject,
    Subject,
    World,
    WorldConfig,
    _load_world_mirror,
    _world_lock_for,
    _world_mirror_bytes,
)
from beliefs.world import registry as _registry
from beliefs.world.anchors import (
    _anchor_heads,
    _export_head_artifact,
    _require_world_genesis,
    parse_store_genesis,
)
from beliefs.world.logmodel import (
    AbsentView,
    ChainHead,
    ChainView,
    DefectView,
    EntryView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)
from beliefs.world.logmodel import DefectKind as ViewDefectKind
from beliefs.world.records import RECORD_CEILING
from beliefs.world.rules import RuleBinding, install_rule_binding, shipped_rule_bundles
from beliefs.world.verify import (
    LogReport,
    LogSeam,
    ObserverSet,
    Ordering,
    _admit_arrival,
    _audit_log,
    _epochs_ordered,
    _restore_root,
    registered_surface_paths,
)

__all__ = [
    "CONSUMER_TAG",
    "CREATED_DIRECTORY_MODE",
    "CREATED_FILE_MODE",
    "GENESIS_DOMAIN",
    "GENESIS_PAYLOAD",
    "INTENT_DOMAIN",
    "PRODUCTION_STORAGE",
    "STORE_CONSUMER_TAG",
    "STORE_GENESIS_DOMAIN",
    "STORE_WRITE_INTENT_DOMAIN",
    "WORLD_CONSUMER_TAG",
    "WORLD_GENESIS_DOMAIN",
    "DestinationOverride",
    "DurableExecutor",
    "DurableOperationPort",
    "LifecycleState",
    "RootOperationId",
    "RootOperationInvalid",
    "RootOperationMismatch",
    "SourceSnapshotMoved",
    "admit_arrival",
    "anchor_heads",
    "audit_log",
    "chain_head_reader",
    "durable_executor_factory",
    "epochs_ordered",
    "export_head_artifact",
    "fork_corpus",
    "fork_store",
    "holdings_seam",
    "init_corpus_root",
    "init_store_root",
    "init_world_root",
    "install_shipped_world_rules",
    "metadata_root_for",
    "migrate_root_to_lifecycle_v3",
    "open_corpus",
    "open_world",
    "read_lifecycle_state",
    "replicate_root",
    "restore_root",
    "write_intent_digest",
    "write_intent_projection",
]

GENESIS_DOMAIN = "science.corpus-root.v1"
"""The registration chain's genesis domain.

The payload deliberately carries **no corpus identity**: corpus manifests and
`corpus_id` minting are root-local acts, not genesis members. An adopted
identity binds through a later chain entry, never by rewriting genesis — a
genesis rewrite is not a correction, it is a different chain.
"""

GENESIS_PAYLOAD = v1.encode({"domain": GENESIS_DOMAIN})
"""The canonical bytes of the constant payload, under `science.identity.v1`.

`register_root` is idempotent on a matching payload and surface and refuses a
mismatch, so these bytes are permanent for every root ever registered with
them: changing this constant does not migrate a root, it orphans one.
"""

INTENT_DOMAIN = "science.corpus-write-intent.v1"
WORLD_GENESIS_DOMAIN = "science.world-root.v1"
STORE_GENESIS_DOMAIN = "science.store-root.v1"

PRODUCTION_STORAGE = StorageProfile(profile_id="flush-honoring-disk.v1")
"""The engine's production storage profile, passed through unchanged.

A storage profile is a declaration by the trusted composition root, which is
this module. Science holds no tuple data, no allowlist and no override:
admitting a new volume configuration is an `atoms` certification amendment, and
cut 4's *every other tuple fails closed* obligation is exercised as the
engine's own refusal — relied on, never re-implemented.
"""

_PRODUCTION_BACKEND: Backend = select_backend()

UNREGISTERED_ROOT = "the project root is not registered"
"""The engine's own words for a root that was never registered.

Restated here because `open_world` must tell that state apart from the *other*
things a chain read can refuse with. `PreconditionRefused` is not one fact:
`read_chain` resolves recovery before it reaches the registration check, and
resolution raises the same class for an observation whose namespace moved and
for a create whose target appeared — each with its own message. Only
`_registered_root` produces this one, at both of its sites, and only it is
mapped onto `WorldUninitialized`.

A test pins the string against `atoms`' own source, the treatment R27 gave
`CORPUS_GENESIS_DOMAIN`. If it ever drifts unnoticed the mapping simply stops
firing and the engine's refusal reaches the caller unchanged — a less friendly
error, never a false statement about a registered root.
"""

METADATA_SUFFIX = ".metadata"


def metadata_root_for(corpus_root: Path) -> Path:
    """The engine's caller-supplied metadata root, by one fixed rule: the
    sibling `<corpus-root>.metadata`.

    The rule normally places the store on the corpus's own volume, and the
    engine **proves** same-volume placement and refuses otherwise — the
    guarantee is the engine's probe, not this naming rule. The sibling sits
    outside the corpus root so that the two cold-arrival cases stay legible: a
    corpus copied without its sibling is a normal cold bootstrap, one copied
    with it is the restored-backup classification case.
    """
    root = Path(corpus_root)
    return root.with_name(root.name + METADATA_SUFFIX)


def init_corpus_root(corpus_root: Path) -> None:
    """Make a corpus root durable — the explicit act, never a fallback.

    Every write against an unregistered root refuses (the engine's
    registered-root check, surfaced through the executor's §4 mapping). Lazy
    registration on first write is rejected on purpose: the genesis act is
    attributable and its timing is a recorded decision, not an accident of
    whichever write happened to come first.

    Re-runnable: `register_root` returns the existing genesis digest when the
    payload and surface match, and refuses when they do not.
    """
    root = Path(corpus_root).resolve()
    if root.exists() and not root.is_dir():
        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a corpus root")
    root.mkdir(parents=True, exist_ok=True)
    register_root(
        _PRODUCTION_BACKEND,
        str(root),
        str(metadata_root_for(root)),
        PRODUCTION_STORAGE,
        GENESIS_PAYLOAD,
        # No manifest exists to baseline and the corpus-write adapter reserves
        # nothing, so the registered surface is empty.
        (),
    )


def _world_genesis_payload(world_id: str) -> bytes:
    return v1.encode({"domain": WORLD_GENESIS_DOMAIN, "world_id": world_id})


def init_world_root(config: WorldConfig) -> None:
    root = config.world_root
    if root.exists() and not root.is_dir():
        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a world root")
    root.mkdir(parents=True, exist_ok=True)
    register_root(
        _PRODUCTION_BACKEND,
        str(root),
        str(metadata_root_for(root)),
        PRODUCTION_STORAGE,
        _world_genesis_payload(config.world_id),
        (),
    )
    mirror = root / "world.yaml"
    if not mirror.exists() and not mirror.is_symlink():
        _world_executor_factory()(root).execute([CreateOp("world.yaml", _world_mirror_bytes(config.world_id))])
        return
    if _load_world_mirror(root) != config.world_id:
        raise WorldIdMismatch(f"{mirror}: world_id does not match configuration")


def _store_genesis_payload(store_id: str, forked_from: tuple[str, str] | None) -> bytes:
    doc: dict[str, object] = {"domain": STORE_GENESIS_DOMAIN, "store_id": store_id}
    if forked_from is not None:
        doc["forked_from"] = {"genesis": forked_from[0], "head": forked_from[1]}
    return v1.encode(doc)


def _decode_store_genesis(payload: bytes) -> tuple[str, tuple[str, str] | None]:
    """Decode a store genesis payload, refusing every non-canonical shape.

    The form is `anchors.parse_store_genesis`'s — the same predicate the
    evaluator's genesis-form step and the acts' subject binding read — with
    the refusal restated in the initializer's own vocabulary.
    """
    try:
        return parse_store_genesis(payload)
    except ValueError as caught:
        raise CorpusRootRefused(
            f"store genesis payload is malformed: {caught}"
        ) from caught


def _read_existing_store_genesis(store_root: Path) -> str | None:
    """The durable store genesis's id, or None for a chain-less root.

    Detached inspection, deliberately: an arriving or interrupted store has
    no serviceable carrier to read coherently, and the question here is only
    whether a durable store genesis already claims this tree.
    """
    inspected = inspect_chain_detached(_PRODUCTION_BACKEND, str(store_root))
    if type(inspected) is not WellFormedChain or not inspected.entries:
        return None
    _digest, genesis = inspected.entries[0]
    if type(genesis) is not GenesisEntry:
        return None
    store_id, _forked_from = _decode_store_genesis(genesis.payload)
    return store_id


def init_store_root(store_root: Path) -> str:
    """Make a store root durable and mint its opaque identity.

    The id is minted, not derived: nothing the genesis carries names the
    root's path, so moving the tree moves nothing the genesis states. A
    populated root refuses — a store initializes empty — and an existing
    genesis is honored only through the engine's own recorded initialization
    operation: a copied store is restored or forked, never re-initialized.
    """
    store_root = Path(store_root)
    if store_root.exists() and not store_root.is_dir():
        raise CorpusRootRefused(
            f"{str(store_root)!r} exists and is not a directory, so it cannot "
            "be a store root"
        )
    store_root.mkdir(parents=True, exist_ok=True)
    existing = _read_existing_store_genesis(store_root)
    if existing is not None:
        if (
            _read_lifecycle_state_callback(
                _PRODUCTION_BACKEND,
                str(store_root),
                str(metadata_root_for(store_root)),
                PRODUCTION_STORAGE,
            )
            is LifecycleState.WRITABLE
        ):
            return existing  # completed init (or fork); the postcondition holds
        try:
            # Only register_root can recognize its own recorded initialization
            # operation; Science never reads or interprets that bookkeeping.
            # The matching retry completes the interrupted grant; every other
            # carrier — bare copied genesis, fork/replicate origin, binding
            # mismatch — is the engine's named refusal, mapped below.
            register_root(
                _PRODUCTION_BACKEND,
                str(store_root),
                str(metadata_root_for(store_root)),
                PRODUCTION_STORAGE,
                _store_genesis_payload(existing, None),
                (),
            )
        except PreconditionRefused as refused:
            raise CorpusRootRefused(
                f"{str(store_root)!r} carries a store genesis this host did "
                "not initialize; a copied store is restored or forked, never "
                "re-initialized"
            ) from refused
        return existing
    populated = registered_surface_paths(store_root, "store")
    if populated:
        raise CorpusRootRefused(
            f"{str(store_root)!r} holds payload {populated[0]!r}; a store "
            "initializes empty"
        )
    store_id = secrets.token_hex(16)
    register_root(
        _PRODUCTION_BACKEND,
        str(store_root),
        str(metadata_root_for(store_root)),
        PRODUCTION_STORAGE,
        _store_genesis_payload(store_id, None),
        (),
    )
    return store_id


def replicate_root(source_root: Path, dest_root: Path) -> RootOperationId:
    """Replicate one registered root byte-for-byte, chain included.

    The thin wrapper over the engine's copy command: both metadata roots
    derive by the one sibling rule and the one production storage profile
    travels. It appends nothing — a replica's chain arrives unchanged and
    its lifecycle is read-only unserviceable — and returns the engine's
    retained operation id, which an exact retry returns again.
    """
    source = Path(source_root)
    dest = Path(dest_root)
    return _replicate_root_callback(
        _PRODUCTION_BACKEND,
        str(source),
        str(metadata_root_for(source)),
        str(dest),
        str(metadata_root_for(dest)),
        PRODUCTION_STORAGE,
    )


def read_lifecycle_state(root: Path) -> LifecycleState:
    """The closed five-value lifecycle union, validated while reading."""
    target = Path(root)
    return _read_lifecycle_state_callback(
        _PRODUCTION_BACKEND,
        str(target),
        str(metadata_root_for(target)),
        PRODUCTION_STORAGE,
    )


def migrate_root_to_lifecycle_v3(root: Path) -> None:
    """The operator-authorized pre-lifecycle migration, passed through.

    Invoking it is the attestation that this host is the pre-lifecycle
    minting host; every structural refusal — metadata-less, mismatched
    binding, anything but the exact version-2 store — is the engine's own.
    """
    target = Path(root)
    _migrate_root_to_lifecycle_v3_callback(
        _PRODUCTION_BACKEND,
        str(target),
        str(metadata_root_for(target)),
        PRODUCTION_STORAGE,
    )


def restore_root(
    dest_root: Path,
    subject: CorpusSubject | StoreSubject,
    observers: ObserverSet,
) -> LogReport:
    """Admit a restored copy: verify its chain, then grant read
    serviceability — one held boundary, the existing report, no new type.

    The wrapper is the whole of what this module adds — the production seam
    and the engine's structural grant, which takes no verdict and no
    attestation: what travels from the evaluation to the grant is only the
    decision to invoke it. Admission is observed through
    `read_lifecycle_state(dest_root)`, never through the return value, and
    nothing here ever grants writability.
    """
    if type(subject) not in {CorpusSubject, StoreSubject}:
        raise TypeError("restore admits corpus and store subjects; a world root is reconstructed, not restored")

    def grant(root: Path) -> None:
        _grant_read_serviceability_callback(
            _PRODUCTION_BACKEND,
            str(root),
            str(metadata_root_for(root)),
            PRODUCTION_STORAGE,
        )

    return _restore_root(dest_root, subject, observers, seam=_log_seam(), grant=grant)


def _fork_corpus_genesis_payload(forked_from: tuple[str, str]) -> bytes:
    """The corpus fork genesis: the constant domain, plus exactly where the
    child came from — the parent's genesis digest and the head the fork
    copied. The non-fork corpus genesis stays the identity-free constant."""
    return v1.encode(
        {
            "domain": GENESIS_DOMAIN,
            "forked_from": {"genesis": forked_from[0], "head": forked_from[1]},
        }
    )


def _fork_pending(dest_root: Path) -> RootOperationId | None:
    return _read_pending_fork_operation_callback(
        _PRODUCTION_BACKEND,
        str(dest_root),
        str(metadata_root_for(dest_root)),
        PRODUCTION_STORAGE,
    )


def _fork_resume(dest_root: Path, operation_id: RootOperationId) -> None:
    _resume_fork_root_callback(
        _PRODUCTION_BACKEND,
        str(dest_root),
        str(metadata_root_for(dest_root)),
        PRODUCTION_STORAGE,
        operation_id,
    )


def fork_corpus(source_root: Path, dest_root: Path) -> _registry.CorpusManifest:
    """Fork a corpus: a new chain, a fresh identity, and the two fork facts.

    The retry branch runs **before any mint**: a pending fork at the
    destination — the pre-stamp claim or an incomplete recorded operation —
    resumes by its retained identity, the engine completing from its own
    record, and the child manifest is read back from the destination where
    the recorded overrides installed it. Only an absent destination mints:
    the child `corpus_id` is fresh and opaque, the manifest is act-authored
    with `forked_from = (parent corpus_id, parent corpus-state identity)`,
    and the fork genesis carries `forked_from = (parent genesis digest,
    parent head digest)` at the bound snapshot — `SourceSnapshotMoved`,
    `RootOperationMismatch`, and `RootOperationInvalid` propagate
    untranslated, and this act adds no third disposition.
    """
    source = Path(source_root)
    dest = Path(dest_root)
    pending = _fork_pending(dest)
    if pending is not None:
        _fork_resume(dest, pending)
        return _registry.load_manifest(dest)

    parent_manifest = _registry.load_manifest(source)
    genesis_digest, head = _chain_head(source)
    corpus_state = _registry.corpus_state_identity(source)
    child_id = secrets.token_hex(16)
    child_manifest = _registry.CorpusManifest(
        2,
        child_id,
        parent_manifest.profile,
        _registry.ForkedFrom(parent_manifest.corpus_id, corpus_state),
    )
    surface = tuple(
        sorted(set(registered_surface_paths(source, "corpus")) | {"corpus.yaml"})
    )
    _fork_root_callback(
        _PRODUCTION_BACKEND,
        str(source),
        str(metadata_root_for(source)),
        str(dest),
        str(metadata_root_for(dest)),
        PRODUCTION_STORAGE,
        expected_source_head=head,
        genesis_payload=_fork_corpus_genesis_payload((genesis_digest, head)),
        surface_paths=surface,
        dest_overrides=(
            DestinationOverride(
                "corpus.yaml", _registry.manifest_bytes(child_manifest), 0o644
            ),
        ),
    )
    return child_manifest


def fork_store(source_root: Path, dest_root: Path) -> str:
    """Fork a store: the same act over the opaque namespace.

    No manifest travels — a store's only identity is its genesis — so the
    override tuple is empty and the child's fresh `store_id` rides in the
    fork genesis beside the two parent digests. The retry branch resumes by
    retained identity exactly as `fork_corpus` does, the child id read back
    from the destination genesis.
    """
    source = Path(source_root)
    dest = Path(dest_root)
    pending = _fork_pending(dest)
    if pending is not None:
        _fork_resume(dest, pending)
        resumed = _read_existing_store_genesis(dest)
        if resumed is None:
            raise CorpusRootRefused(
                f"{str(dest)!r} resumed a fork but carries no store genesis"
            )
        return resumed

    genesis_digest, head = _chain_head(source)
    child_id = secrets.token_hex(16)
    _fork_root_callback(
        _PRODUCTION_BACKEND,
        str(source),
        str(metadata_root_for(source)),
        str(dest),
        str(metadata_root_for(dest)),
        PRODUCTION_STORAGE,
        expected_source_head=head,
        genesis_payload=_store_genesis_payload(child_id, (genesis_digest, head)),
        surface_paths=registered_surface_paths(source, "store"),
        dest_overrides=(),
    )
    return child_id


def write_intent_projection(plan: WritePlan) -> list[dict[str, str]]:
    """The plan's intent, derivable from the plan alone.

    One discriminated shape per operation kind, in plan order, **omitting the
    fields that do not apply**: a create has no `expected_digest` and a delete
    no `content_sha256`, and the identity encoding refuses `null`, so an
    absent field is spelled by its absence rather than by a placeholder that
    would collide with a present-and-empty one.
    """
    projection: list[dict[str, str]] = []
    for op in plan:
        if isinstance(op, CreateOp):
            projection.append(
                {"op": "create", "path": op.path, "content_sha256": sha256(op.content).hexdigest()}
            )
        elif isinstance(op, ReplaceOp):
            projection.append(
                {
                    "op": "replace",
                    "path": op.path,
                    "expected_digest": op.expected_digest,
                    "content_sha256": sha256(op.content).hexdigest(),
                }
            )
        elif isinstance(op, DeleteOp):
            projection.append({"op": "delete", "path": op.path, "expected_digest": op.expected_digest})
        else:
            # Unreachable through the executor, which validates the plan first;
            # stated rather than silently skipped, because an operation missing
            # from the intent is a transaction whose declared intent is not what
            # it does.
            raise TypeError(f"unknown operation kind: {op!r}")
    return projection


def write_intent_digest(plan: WritePlan) -> str:
    """`sha256:`-prefixed digest of the intent projection. The prefix is
    mandatory: the engine's spec compilation checks the format."""
    return _write_intent_digest(plan, INTENT_DOMAIN)


def _write_intent_digest(plan: WritePlan, domain: str) -> str:
    return "sha256:" + v1.digest(domain, write_intent_projection(plan))


CONSUMER_TAG = "science-corpus-write-v1"
"""The engine's consumer tag for every transaction this adapter commits.

**Design deviation, pending review.** The design names
`science.corpus-write.v1`, which the engine refuses: `compile_spec` runs
`require_valid_identifier` over `consumer_tag`, whose grammar is
`[A-Za-z0-9_-]{1,64}` — a tag is woven into a scratch-leaf path component, so
the dot-versioned spelling cannot be shipped. The same name in the admitted
grammar is used until the design says otherwise. Science's own identity
domains are unaffected: `INTENT_DOMAIN` above is a `science.identity.v1`
domain and answers to that grammar, not to the engine's.
"""

WORLD_CONSUMER_TAG = "science-world-write-v1"
WORLD_INTENT_DOMAIN = "science.world-write-intent.v1"
STORE_CONSUMER_TAG = "science-store-write-v1"
STORE_WRITE_INTENT_DOMAIN = "science.store-write-intent.v1"

CREATED_FILE_MODE = 0o644
"""The adapter's one constant, carried by every created and replacement
**post**-state. Pre-states carry their observed mode, never this."""

CREATED_DIRECTORY_MODE = 0o755


def _observe_file(root: Path, path: str, index: int | None = None) -> FileState:
    """Read one regular-file pre-state with the executor's error mapping."""
    target = root / path
    try:
        observed = target.stat()
        content = target.read_bytes()
    except OSError as caught:
        raise ExecutionError(
            f"{path!r} could not be read for its pre-state: {caught}",
            index=index,
            applied=0,
        ) from caught
    if not stat_module.S_ISREG(observed.st_mode):
        raise ExecutionError(f"{path!r} is not a regular file", index=index, applied=0)
    return FileState(
        content_hash="sha256:" + sha256(content).hexdigest(),
        mode=stat_module.S_IMODE(observed.st_mode),
        byte_len=observed.st_size,
    )


def _missing_ancestors(
    root: Path,
    path: str,
    index: int,
    initial: dict[str, PathState],
    current: dict[str, PathState],
) -> list[Effect]:
    """Create the absent parents needed by a file create in the same transaction."""
    effects: list[Effect] = []
    components = path.split("/")[:-1]
    for depth in range(len(components)):
        prefix = "/".join(components[: depth + 1])
        if prefix in current or (root / prefix).exists():
            continue
        post = DirectoryState(mode=CREATED_DIRECTORY_MODE)
        initial[prefix] = ABSENT
        current[prefix] = post
        effects.append(CreateDirectory(effect_id=f"dir-{index}-{depth}", path=prefix, post=post))
    return effects


def _mapped_submit(
    *,
    backend: Backend,
    root: Path,
    metadata_root: Path,
    storage: StorageProfile,
    spec: TransactionSpec,
    payloads: _PlanPayloads,
) -> TransactionOutcome:
    """Submit through the executor's one conservative engine-error mapping."""
    def submit() -> TransactionOutcome:
        try:
            return run_transaction(
                backend,
                str(root),
                str(metadata_root),
                storage,
                spec,
                payloads,
            )
        except (ProjectApprovalRefused, SpecValidationError, PreconditionRefused, CapabilityUnavailable) as caught:
            # Rooted proof, adapter-built spec, clean refusal, missing
            # capability: each is raised before any project mutation, or refuses
            # cleanly with restoration proven by the engine's own contract.
            raise ExecutionError(str(caught), index=None, applied=0) from caught
        except PendingUnresolved as caught:
            raise ExecutionError(str(caught), index=None, applied=0) from caught
        except (MetadataStoreInvalid, ChainStateInvalid) as caught:
            raise ExecutionError(str(caught), index=None, applied=None) from caught
        except (TransactionHalted, ProtocolError) as caught:
            raise ExecutionError(str(caught), index=None, applied=None) from caught
        except AtomsError as caught:
            raise ExecutionError(str(caught), index=None, applied=None) from caught
        except Exception as caught:
            raise ExecutionError(str(caught), index=None, applied=None) from caught

    return submit()


class DurableExecutor:
    """The seam's `WritePlanExecutor`, compiling one `WritePlan` into one
    `TransactionSpec` and submitting it through the engine.

    All-or-nothing is the engine's property, relied on and never
    re-implemented. The complete `TransactionOutcome` is **discarded**: nothing
    in this slice consumes it, and anchor carriage reads registration digests
    from the chain itself rather than from executor state.

    **The build follows path timelines, not independent operations.** A path may
    occur more than once in one plan and the engine validates a continuous
    timeline per path, so each occurrence's pre-state is the previous
    occurrence's post-state, and only a **first** occurrence reads disk.
    """

    def __init__(
        self,
        root: Path,
        *,
        backend: Backend,
        storage: StorageProfile,
        metadata_root: Path,
        consumer_tag: str,
        intent_domain: str,
        fulfills: str | None = None,
    ) -> None:
        self.root = Path(root)
        self._backend = backend
        self._storage = storage
        self._metadata_root = Path(metadata_root)
        self._consumer_tag = consumer_tag
        self._intent_domain = intent_domain
        self._fulfills = fulfills

    # --- the seam's one method ----------------------------------------------

    def execute(self, plan: WritePlan) -> None:
        if not plan:
            # Vacuous: no transaction, no chain entry — what `DefaultExecutor`
            # does with nothing to apply.
            return
        _refuse_malformed(plan)
        effects, initial_surface, final_surface, payloads = self._compile(plan)
        spec = build_spec(
            consumer_tag=self._consumer_tag,
            intent_digest=_write_intent_digest(plan, self._intent_domain),
            initial_surface=initial_surface,
            final_surface=final_surface,
            effects=effects,
            # The adapter reserves nothing and declares no ordering of its own.
            # `build_spec` supplies `schema_version` from the engine's own
            # constant, so no stale literal can ship here.
            dependencies=(),
            fulfills=self._fulfills,
            registered_paths=tuple(dict.fromkeys(operation.path for operation in plan)),
        )
        _mapped_submit(
            backend=self._backend,
            root=self.root,
            metadata_root=self._metadata_root,
            storage=self._storage,
            spec=spec,
            payloads=_PlanPayloads(payloads),
        )

    # --- the build ----------------------------------------------------------

    def _compile(
        self, plan: WritePlan
    ) -> tuple[tuple[Effect, ...], dict[str, PathState], dict[str, PathState], dict[str, bytes]]:
        initial: dict[str, PathState] = {}
        current: dict[str, PathState] = {}
        effects: list[Effect] = []
        payloads: dict[str, bytes] = {}

        for index, op in enumerate(plan):
            if op.path in current:
                pre = current[op.path]
            else:
                # A first-occurrence create reads nothing: its pre-state is
                # `ABSENT` by construction and `CreateFileNoClobber` enforces
                # absence engine-side.
                pre = ABSENT if isinstance(op, CreateOp) else _observe_file(self.root, op.path, index)
                initial[op.path] = pre

            if isinstance(op, CreateOp):
                if not isinstance(pre, AbsentState):
                    raise ExecutionError(
                        f"create at {op.path!r} is unsatisfiable: the state it would see is present",
                        index=index,
                        applied=0,
                    )
                post = _file_state(op.content)
                effects.extend(_missing_ancestors(self.root, op.path, index, initial, current))
                effects.append(CreateFileNoClobber(effect_id=f"op-{index}", path=op.path, post=post))
                payloads[post.content_hash] = op.content
                current[op.path] = post
            elif isinstance(op, ReplaceOp):
                observed = _require_file(pre, op, index)
                post = _file_state(op.content)
                effects.append(ReplaceFile(effect_id=f"op-{index}", path=op.path, pre=observed, post=post))
                payloads[post.content_hash] = op.content
                current[op.path] = post
            else:
                observed = _require_file(pre, op, index)
                effects.append(DeletePath(effect_id=f"op-{index}", path=op.path, pre=observed))
                current[op.path] = ABSENT

        return tuple(effects), initial, current, payloads


class DurableOperationPort:
    def __init__(
        self, root: Path, *, backend: Backend, storage: StorageProfile, metadata_root: Path, authority: Authority
    ) -> None:
        if type(authority) is not Authority:
            raise TypeError("a port binds an Authority")
        self.root = Path(root)
        self._backend = backend
        self._storage = storage
        self._metadata_root = Path(metadata_root)
        self._authority = authority

    @property
    def authority(self) -> Authority:
        return self._authority

    def append_intent(self, payload: bytes) -> str:
        with _operation_lock_for(self.root):
            try:
                return append_intent(
                    self._backend,
                    str(self.root),
                    str(self._metadata_root),
                    self._storage,
                    payload,
                )
            except (ProjectApprovalRefused, PreconditionRefused, CapabilityUnavailable) as caught:
                raise ExecutionError(str(caught), index=None, applied=0) from caught
            except PendingUnresolved as caught:
                # The same gate, before the intent entry is appended: the two
                # mappings state one engine contract and must not drift.
                raise ExecutionError(str(caught), index=None, applied=0) from caught
            except (MetadataStoreInvalid, ChainStateInvalid) as caught:
                raise ExecutionError(str(caught), index=None, applied=None) from caught
            except (TransactionHalted, ProtocolError) as caught:
                raise ExecutionError(str(caught), index=None, applied=None) from caught
            except AtomsError as caught:
                raise ExecutionError(str(caught), index=None, applied=None) from caught
            except Exception as caught:
                raise ExecutionError(str(caught), index=None, applied=None) from caught

    def execute(self, plan: WritePlan) -> None:
        """Publish a record that fulfills no intent."""
        with _operation_lock_for(self.root):
            self._execute(plan)

    def _execute(self, plan: WritePlan) -> None:
        _refuse_over_ceiling(plan)
        DurableExecutor(
            self.root,
            backend=self._backend,
            storage=self._storage,
            metadata_root=self._metadata_root,
            consumer_tag=CONSUMER_TAG,
            intent_domain=INTENT_DOMAIN,
            fulfills=None,
        ).execute(plan)

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None:
        with _operation_lock_for(self.root):
            self._execute_fulfilling(plan, fulfills)

    def _execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None:
        _refuse_over_ceiling(plan)
        DurableExecutor(
            self.root,
            backend=self._backend,
            storage=self._storage,
            metadata_root=self._metadata_root,
            consumer_tag=CONSUMER_TAG,
            intent_domain=INTENT_DOMAIN,
            fulfills=fulfills,
        ).execute(plan)


class _PlanPayloads:
    """The planned-postimage bytes, content-addressed.

    Two effects writing identical content are supplied once, and the consumer
    never learns a staging path. `KeyError` — and only `KeyError` — is the
    signal for a digest this source has no binding for.
    """

    def __init__(self, blobs: Mapping[str, bytes]) -> None:
        self._blobs = dict(blobs)

    def open(self, digest: str) -> IO[bytes]:
        return io.BytesIO(self._blobs[digest])


def _file_state(content: bytes) -> FileState:
    return FileState(
        content_hash="sha256:" + sha256(content).hexdigest(),
        mode=CREATED_FILE_MODE,
        byte_len=len(content),
    )


def _path_state_view(state: PathState) -> PathStateView:
    if type(state) is FileState:
        return FileStateView(state.content_hash)
    if type(state) is AbsentState:
        return AbsentStateView()
    if type(state) is DirectoryState:
        return NonRegularStateView("directory")
    if type(state) is SymlinkState:
        return NonRegularStateView("symlink")
    raise TypeError(f"unknown path state: {type(state).__name__}")


def _path_read_view(result: object) -> PathReadView:
    if type(result) is PathObserved:
        return PathObservedView(_path_state_view(result.state))
    if type(result) is ReadNotAttempted:
        return ReadNotAttemptedView(
            str(result.reason),
            result.lifecycle_state.value if result.lifecycle_state else None,
            result.detail,
        )
    if type(result) is ReadUnestablished:
        return ReadUnestablishedView(str(result.reason), result.detail)
    raise TypeError(f"unknown path read result: {type(result).__name__}")


def _store_outcome_view(outcome: TransactionOutcome) -> StoreOutcomeView:
    return StoreOutcomeView(
        outcome.txid,
        tuple((path, _path_state_view(state)) for path, state in outcome.final_states),
    )


def _store_write(root: Path, path: str, content: bytes) -> StoreOutcomeView:
    root = Path(root)
    require_rel_path("path", path)
    initial: dict[str, PathState] = {}
    final: dict[str, PathState] = {}
    effects: list[Effect] = []
    post = _file_state(content)
    target = root / path
    projection: dict[str, str] = {
        "op": "write",
        "path": path,
        "content_sha256": sha256(content).hexdigest(),
    }
    if target.exists() or target.is_symlink():
        pre = _observe_file(root, path)
        initial[path] = pre
        projection["expected_digest"] = pre.content_hash.removeprefix("sha256:")
        effects.append(ReplaceFile("op-0", path, pre, post))
    else:
        initial[path] = ABSENT
        effects.extend(_missing_ancestors(root, path, 0, initial, final))
        effects.append(CreateFileNoClobber("op-0", path, post))
    final[path] = post
    spec = build_spec(
        consumer_tag=STORE_CONSUMER_TAG,
        intent_digest="sha256:" + v1.digest(STORE_WRITE_INTENT_DOMAIN, [projection]),
        initial_surface=initial,
        final_surface=final,
        effects=effects,
        dependencies=(),
        fulfills=None,
        registered_paths=(path,),
    )
    return _store_outcome_view(
        _mapped_submit(
            backend=_PRODUCTION_BACKEND,
            root=root,
            metadata_root=metadata_root_for(root),
            storage=PRODUCTION_STORAGE,
            spec=spec,
            payloads=_PlanPayloads({post.content_hash: content}),
        )
    )


def _store_delete(root: Path, path: str) -> StoreOutcomeView:
    root = Path(root)
    require_rel_path("path", path)
    pre = _observe_file(root, path)
    spec = build_spec(
        consumer_tag=STORE_CONSUMER_TAG,
        intent_digest="sha256:"
        + v1.digest(
            STORE_WRITE_INTENT_DOMAIN,
            [
                {
                    "op": "delete",
                    "path": path,
                    "expected_digest": pre.content_hash.removeprefix("sha256:"),
                }
            ],
        ),
        initial_surface={path: pre},
        final_surface={path: ABSENT},
        effects=(DeletePath("op-0", path, pre),),
        dependencies=(),
        fulfills=None,
        registered_paths=(path,),
    )
    return _store_outcome_view(
        _mapped_submit(
            backend=_PRODUCTION_BACKEND,
            root=root,
            metadata_root=metadata_root_for(root),
            storage=PRODUCTION_STORAGE,
            spec=spec,
            payloads=_PlanPayloads({}),
        )
    )


def _store_move(root: Path, source: str, destination: str) -> StoreOutcomeView:
    root = Path(root)
    require_rel_path("source", source)
    require_rel_path("destination", destination)
    pre = _observe_file(root, source)
    spec = build_spec(
        consumer_tag=STORE_CONSUMER_TAG,
        intent_digest="sha256:"
        + v1.digest(
            STORE_WRITE_INTENT_DOMAIN,
            [
                {
                    "op": "move",
                    "source": source,
                    "destination": destination,
                    "expected_digest": pre.content_hash.removeprefix("sha256:"),
                }
            ],
        ),
        initial_surface={source: pre, destination: ABSENT},
        final_surface={source: ABSENT, destination: pre},
        effects=(MoveNoClobber("op-0", source, destination, pre),),
        dependencies=(),
        fulfills=None,
        registered_paths=(source, destination),
    )
    return _store_outcome_view(
        _mapped_submit(
            backend=_PRODUCTION_BACKEND,
            root=root,
            metadata_root=metadata_root_for(root),
            storage=PRODUCTION_STORAGE,
            spec=spec,
            payloads=_PlanPayloads({}),
        )
    )


def _store_read_path(root: Path, path: str) -> PathReadView:
    return _path_read_view(
        read_path_state(
            _PRODUCTION_BACKEND,
            str(root),
            str(metadata_root_for(root)),
            PRODUCTION_STORAGE,
            path,
        )
    )


def _store_append_intent(root: Path, payload: bytes) -> str:
    try:
        return append_intent(
            _PRODUCTION_BACKEND,
            str(root),
            str(metadata_root_for(root)),
            PRODUCTION_STORAGE,
            payload,
        )
    except (ProjectApprovalRefused, PreconditionRefused, CapabilityUnavailable) as caught:
        raise ExecutionError(str(caught), index=None, applied=0) from caught
    except PendingUnresolved as caught:
        raise ExecutionError(str(caught), index=None, applied=0) from caught
    except (MetadataStoreInvalid, ChainStateInvalid) as caught:
        raise ExecutionError(str(caught), index=None, applied=None) from caught
    except (TransactionHalted, ProtocolError) as caught:
        raise ExecutionError(str(caught), index=None, applied=None) from caught
    except AtomsError as caught:
        raise ExecutionError(str(caught), index=None, applied=None) from caught
    except Exception as caught:
        raise ExecutionError(str(caught), index=None, applied=None) from caught


def _store_publish_fulfilling(root: Path, plan: SeamWritePlan, fulfills: str) -> None:
    _refuse_over_ceiling(cast(WritePlan, plan))
    DurableExecutor(
        root,
        backend=_PRODUCTION_BACKEND,
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(root),
        consumer_tag=CONSUMER_TAG,
        intent_domain=INTENT_DOMAIN,
        fulfills=fulfills,
    ).execute(cast(WritePlan, plan))


def _require_file(pre: PathState, op: ReplaceOp | DeleteOp, index: int) -> FileState:
    """The digest **and** the existence precondition, both against the state the
    operation will actually see.

    Without the existence half, an operation unsatisfiable by construction would
    fall through to the engine's timeline validation and surface mislabelled as
    an adapter bug.
    """
    if not isinstance(pre, FileState):
        raise ExecutionError(
            f"{op.op} at {op.path!r} is unsatisfiable: the state it would see is absent",
            index=index,
            applied=0,
        )
    if pre.content_hash != "sha256:" + op.expected_digest:
        raise ExecutionError(
            f"{op.path!r} does not hold the expected content: {pre.content_hash} != sha256:{op.expected_digest}",
            index=index,
            applied=0,
        )
    return pre


def _refuse_malformed(plan: WritePlan) -> None:
    """The lexically decidable checks, before any read.

    `nodes` owns the predicate for its own namespace and for lexical escape —
    `validate_plan` is exported precisely so a durable executor keeps one
    authority for it. What it cannot know about is the **engine's** own leaves,
    so that residue is checked here, and `atoms` refuses such a path at compile
    time besides.
    """
    validate_plan(plan)
    for op in plan:
        for component in op.path.split("/"):
            if component.startswith(SCRATCH_SIGIL):
                raise PlanRefusedError(f"path names an engine-reserved leaf: {op.path!r}")


def _refuse_over_ceiling(plan: WritePlan) -> None:
    """Refuse oversized qualifying publications before executor construction."""
    for op in plan:
        content = getattr(op, "content", None)
        if isinstance(content, bytes) and len(content) > RECORD_CEILING:
            raise PlanRefusedError(
                f"planned postimage at {op.path!r} is {len(content)} bytes, "
                f"over the {RECORD_CEILING}-byte record ceiling"
            )


def _durable_executor(root: Path) -> DurableExecutor:
    return DurableExecutor(
        root,
        backend=_PRODUCTION_BACKEND,
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(root),
        consumer_tag=CONSUMER_TAG,
        intent_domain=INTENT_DOMAIN,
    )


def durable_executor_factory() -> Callable[[Path], DurableExecutor]:
    """The stable root-taking factory the write API is built with."""
    return _durable_executor


def _world_executor(root: Path) -> DurableExecutor:
    return DurableExecutor(
        root,
        backend=_PRODUCTION_BACKEND,
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(root),
        consumer_tag=WORLD_CONSUMER_TAG,
        intent_domain=WORLD_INTENT_DOMAIN,
    )


def _world_executor_factory() -> Callable[[Path], DurableExecutor]:
    return _world_executor


def _chain_head(root: Path) -> tuple[str, str]:
    """One root's `(genesis_digest, tip)`, with recovery already completed.

    `read_chain` takes the project lock and resolves recovery before it
    projects, so the two digests are chain state rather than whatever a
    survivor left behind. Only the digests are returned: the `ChainView` — its
    entries, its engine types — stops here, which is what lets the world layer
    anchor an epoch to a chain without importing the engine that keeps one.

    **The seam's `_read_head` issues the identical `read_chain` call with a
    deliberately different error contract, and the asymmetry is not drift.**
    That one is a seam adapter, so §6.4 obliges it to translate
    `ChainStateInvalid` and `TransactionHalted` into `LogEvidenceRefused`;
    this one is the build's chain reader, whose callers — preflight,
    publication — already handle the engine's own exceptions and would be
    changed, not helped, by a Science-typed refusal appearing under them.
    Making the two calls agree would break one of the two contracts.
    """
    view = read_chain(
        _PRODUCTION_BACKEND,
        str(root),
        str(metadata_root_for(root)),
        PRODUCTION_STORAGE,
    )
    return (view.genesis_digest, view.tip)


def chain_head_reader() -> Callable[[Path], tuple[str, str]]:
    """The stable root-taking chain reader a `World` is built with.

    Stable in the same sense as `durable_executor_factory`: the same function
    object every call, so a caller can assert that a world holds *this*
    reader rather than one that merely behaves like it.
    """
    return _chain_head


# --- the log seam ------------------------------------------------------------
#
# `atoms` inspection results are engine types, and every act of the log
# verification slice discriminates over one. Rather than let those classes be
# named above this module, the conversion below re-types the *shape* into
# `beliefs.world.logmodel`'s closed unions and carries the *facts* — the path
# state fingerprints — as the engine's own objects, opaque and compared only by
# equality. That is the whole of the seam's cleverness, and it is what makes
# "Science owns no second summary model" a mechanism.


_DEFECT_KINDS: dict[DefectKind, ViewDefectKind] = {
    DefectKind.FOREIGN_LEAF: "foreign-leaf",
    DefectKind.NAME_BYTES_MISMATCH: "name-mismatch",
    DefectKind.UNDECODABLE_ENTRY: "undecodable-entry",
    DefectKind.GENESIS_COUNT: "genesis-count",
    DefectKind.MISSING_PREDECESSOR: "missing-predecessor",
    DefectKind.SIBLING_BRANCH: "sibling-branch",
    DefectKind.CYCLE: "cycle",
    DefectKind.ORPHAN_HISTORY: "orphan-history",
    DefectKind.SETTLEMENT_WITHOUT_REGISTRATION: "settlement-unregistered",
    DefectKind.SETTLEMENT_TXID_MISMATCH: "settlement-txid-mismatch",
    DefectKind.DUPLICATE_SETTLEMENT: "duplicate-settlement",
    DefectKind.DUPLICATE_REGISTRATION: "duplicate-registration",
    DefectKind.FULFILLS_UNRESOLVED: "fulfills-invalid",
    DefectKind.DUPLICATE_FULFILLMENT: "duplicate-fulfillment",
}
"""The taxonomy, member by member, in the engine's own declaration order.

Three names differ between the vocabularies and the difference is deliberate,
not drift: the engine's `NAME_BYTES_MISMATCH`, `SETTLEMENT_WITHOUT_REGISTRATION`
and `FULFILLS_UNRESOLVED` are spelled `name-mismatch`,
`settlement-unregistered` and `fulfills-invalid` in the design's taxonomy. The
mapping is **closed**: an engine member absent from it raises rather than
producing a view, because a fifteenth defect kind Science silently dropped
would be a malformed chain reported as something else.
"""


def _surface_view(surface: tuple[tuple[str, PathStateJSON], ...]) -> tuple[tuple[str, object], ...]:
    """Decode a chain-carried surface into the engine's `PathState` values.

    The two atoms forms meet here: entries carry `PathStateJSON` and capture
    returns `PathState`, so decoding with the engine's own `state_from_json`
    is what lets replay compare a chain fact against a disk fact directly.
    Science does not build or interpret the result: replay receives it
    opaquely, and mechanical projection can return it only to the engine-owned
    encoder.
    """
    return tuple((path, state_from_json(state)) for path, state in surface)


def _state_facts(state: object) -> tuple[tuple[str, str], ...]:
    return state_to_json(cast(PathState, state))


def _entry_view(digest: str, entry: Entry) -> EntryView:
    if type(entry) is GenesisEntry:
        return GenesisEntryView(
            digest=digest, payload=entry.payload, baseline=_surface_view(entry.baseline)
        )
    if type(entry) is RegisteredEntry:
        return RegisteredEntryView(
            digest=digest,
            txid=entry.txid,
            intent_digest=entry.intent_digest,
            consumer_tag=entry.consumer_tag,
            initial=_surface_view(entry.initial),
            final=_surface_view(entry.final),
            fulfills=entry.fulfills,
        )
    if type(entry) is SettledEntry:
        return SettledEntryView(
            digest=digest,
            txid=entry.txid,
            registration=entry.registration,
            committed=entry.outcome is ChainOutcome.COMMITTED,
        )
    if type(entry) is IntentEntry:
        return IntentEntryView(digest=digest, payload=entry.payload)
    raise ProtocolError(f"unknown chain entry class: {type(entry).__name__}")


def _chain_view(inspection: ChainInspection) -> ChainView:
    """One `atoms` inspection result, re-typed into Science's vocabulary."""
    if type(inspection) is AbsentChain:
        return AbsentView()
    if type(inspection) is MalformedChain:
        defect = inspection.defect
        kind = _DEFECT_KINDS.get(defect.kind)
        if kind is None:
            raise ProtocolError(f"unmapped chain defect kind: {defect.kind}")
        return MalformedView(DefectView(kind=kind, subject=defect.subject, detail=defect.detail))
    if type(inspection) is WellFormedChain:
        entries = tuple(_entry_view(digest, entry) for digest, entry in inspection.entries)
        genesis = entries[0] if entries else None
        if type(genesis) is not GenesisEntryView:
            raise ProtocolError("a well-formed chain's first entry is not its genesis")
        return WellFormedView(
            genesis=genesis, entries=entries, tip=inspection.tip, pending=inspection.pending
        )
    raise ProtocolError(f"unknown chain inspection result: {type(inspection).__name__}")


@contextmanager
def _inspect_escapes() -> Iterator[None]:
    """§6.4's two inspect-phase translations, minted in one place.

    Exactly two exceptions are caught: everything else — `ProtocolError`, the
    volume and store setup errors, anything unforeseen — keeps its own
    contract, because a seam that swallowed the unforeseen would report an
    engine bug as evidence that could not be obtained.
    """
    try:
        yield
    except ChainStateInvalid as caught:
        raise LogEvidenceRefused("inspect", "ChainStateInvalid", str(caught)) from caught
    except TransactionHalted as caught:
        raise LogEvidenceRefused("inspect", "TransactionHalted", str(caught)) from caught


def _inspect_registered(root: Path) -> ChainView:
    with _inspect_escapes():
        inspection = inspect_chain(
            _PRODUCTION_BACKEND, str(root), str(metadata_root_for(root)), PRODUCTION_STORAGE
        )
    return _chain_view(inspection)


def _inspect_detached(root: Path) -> ChainView:
    with _inspect_escapes():
        inspection = inspect_chain_detached(_PRODUCTION_BACKEND, str(root))
    return _chain_view(inspection)


def _capture(root: Path, paths: tuple[str, ...]) -> tuple[tuple[str, object], ...]:
    """State exactly the named paths, the engine's values passed through.

    Nothing is decoded, wrapped or copied on the way out: the tuple the engine
    built is the tuple the seam hands on.
    """
    try:
        return capture_states(_PRODUCTION_BACKEND, str(root), paths)
    except PreconditionRefused as caught:
        raise LogEvidenceRefused("capture", "PreconditionRefused", str(caught)) from caught


def _read_head(root: Path) -> ChainHead:
    """The validated head, with the genesis payload it was read alongside.

    The twin of `_chain_head` above — same `read_chain` call, deliberately
    different error contract; see that docstring for why they must not be
    made to agree.
    """
    with _inspect_escapes():
        view = read_chain(
            _PRODUCTION_BACKEND, str(root), str(metadata_root_for(root)), PRODUCTION_STORAGE
        )
    genesis = view.entries[0][1] if view.entries else None
    if type(genesis) is not GenesisEntry:
        raise ProtocolError("a validated chain's first entry is not its genesis")
    return ChainHead(genesis_digest=view.genesis_digest, genesis_payload=genesis.payload, tip=view.tip)


def _store_genesis(root: Path) -> bytes:
    return _read_head(root).genesis_payload


_HOLDINGS_SEAM = StoreActSeam(
    append_intent=_store_append_intent,
    publish_fulfilling=_store_publish_fulfilling,
    read_path=_store_read_path,
    store_write=_store_write,
    store_delete=_store_delete,
    store_move=_store_move,
    store_genesis=_store_genesis,
)


def holdings_seam() -> StoreActSeam:
    return _HOLDINGS_SEAM


@contextmanager
def _world_lock(root: Path) -> Iterator[None]:
    with _world_lock_for(root):
        yield


def _lifecycle_state_value(root: Path) -> str:
    """The seam's lifecycle reading: the closed union's string value, so the
    world layer branches on the fact without holding the engine's type."""
    return read_lifecycle_state(Path(root)).value


_LOG_SEAM = LogSeam(
    inspect_registered=_inspect_registered,
    inspect_detached=_inspect_detached,
    capture=_capture,
    read_head=_read_head,
    # The engine's own absent singleton, never a Science reconstruction: it is
    # the default of replay's union comparison, and a value that merely
    # compared equal would be a second summary model with one member.
    absent_state=ABSENT,
    world_lock=_world_lock,
    # The write API's own lock-only lookup, unwrapped: an audit and a writer
    # contending for one corpus root must contend for one object.
    corpus_lock=_operation_lock_for,
    lifecycle_state=_lifecycle_state_value,
    state_facts=_state_facts,
)


def _log_seam() -> LogSeam:
    """The production seam — one object, stable across calls.

    Stable in the same sense as `durable_executor_factory` and
    `chain_head_reader`: an act may be asserted to hold *this* seam rather
    than one that merely behaves like it.
    """
    return _LOG_SEAM


def anchor_heads(
    world: World,
    corpus_ids: frozenset[str],
    *,
    store_roots: tuple[tuple[str, Path], ...] = (),
) -> tuple[LogHeadRecord, ...]:
    """The explicit anchor act: record each named subject's present chain head.

    The wrapper is the whole of what this module adds — the production seam.
    The act itself is `beliefs.world.anchors._anchor_heads`, which holds no
    engine capability of its own and is testable against a stand-in seam
    (log-verification design §3.3). Each `store_roots` pair is
    `(store_id, root)`: a store resolves through no registry, so the caller
    supplies the carrier, and the genesis is verified to carry that
    `store_id` before head acceptance or registry mutation.
    """
    return _anchor_heads(world, corpus_ids, store_roots=store_roots, seam=_log_seam())


def export_head_artifact(world: World, subject: Subject, *, store_root: Path | None = None) -> bytes:
    """One subject's head, as the canonical bytes of a standalone artifact.

    Writes nothing and mints no record: export *is* the return of the value,
    and storing it with an external holder is the holder's job — which is also
    what makes it the one act that can anchor the world chain (§3.2, L11).
    A store subject supplies its root, under the same binding the anchor act
    holds: the genesis must carry the subject's own `store_id`.
    """
    return _export_head_artifact(world, subject, store_root=store_root, seam=_log_seam())


def audit_log(
    config: WorldConfig,
    subject: Subject,
    target_root: Path,
    observers: ObserverSet,
    *,
    actor: str,
    history: Mapping[str, bytes] | None = None,
) -> LogReport:
    """Judge one root's chain against one observer set, and report. Writes
    nothing and mints nothing.

    The wrapper is the whole of what this module adds — the production seam.
    The act is `beliefs.world.verify._audit_log`, which takes the world
    **configuration** rather than an opened `World` precisely so that it runs
    on the worlds `open_world` refuses (log-verification design §6.1, §6.3),
    and an **explicit** target root, which is never associated to the subject
    by reading its manifest.
    """
    return _audit_log(
        config, subject, target_root, observers, actor=actor, history=history, seam=_log_seam()
    )


def admit_arrival(
    world: World,
    corpus_root: Path,
    provenance: ReplicaOf,
    observers: ObserverSet,
    *,
    history: Mapping[str, bytes] | None = None,
) -> tuple[AdmissionRecord, LogReport]:
    """Admit an arriving replica, its traveled chain verified first.

    The wrapper is the whole of what this module adds — the production seam.
    The act is `beliefs.world.verify._admit_arrival`, which loads the arriving
    root's manifest itself under that root's own lock, verifies against
    `Corpus(provenance.parent_corpus_id)` — the chain a replica carries is its
    parent's — and commits through the one admission core `World.admit` commits
    through (log-verification design §6.2).

    Returns the `AdmissionRecord` and the verification report **side by side**:
    the observer bound is never discarded, and it never enters admission
    identity, which this design does not amend. `World.admit` refuses
    `ReplicaOf` outright, since it holds no verdict to report.
    """
    return _admit_arrival(world, corpus_root, provenance, observers, history=history, seam=_log_seam())


def epochs_ordered(config: WorldConfig, e1: str, e2: str) -> Ordering:
    """Whether `e2` orders after `e1`, by the world chain's own ancestry.

    Log-verification design §7: ordered iff E2's build-start world head
    descends from the settlement that committed E1's publication; a missing or
    rolled-back publication is `unordered`. Epoch sequence numbers are read by
    nothing. This is the log design §7's predicate only — the event-level
    relation is deferred and L8 is partial.
    """
    return _epochs_ordered(config, e1, e2, seam=_log_seam())


def open_corpus(
    corpus_root: Path, *, authority: Authority, coordination_resolver: CoordinationResolver | None = None
) -> CorpusWriter:
    """The composition root's product: a write API bound to one corpus root,
    writing through the certified engine.

    The root is registered by `init_corpus_root`, never by this call. A corpus
    opened against an unregistered root constructs and reads; its first write
    refuses with the engine's registration refusal as cause.
    """
    root = Path(corpus_root).resolve()
    return CorpusWriter(
        root,
        durable_executor_factory(),
        authority=authority,
        operation_port=DurableOperationPort(
            root,
            backend=_PRODUCTION_BACKEND,
            storage=PRODUCTION_STORAGE,
            metadata_root=metadata_root_for(root),
            authority=authority,
        ),
        coordination_resolver=coordination_resolver,
    )


def install_shipped_world_rules(world: World) -> tuple[RuleBinding, ...]:
    """Hold this package's four v1 enumeration rules in one world — the
    explicit act, never a side effect of initialization or opening.

    It mirrors adoption: shipping content and holding it are two decisions, and
    a world that installed whatever its installed package happened to carry
    would be resolving receipts against a store nobody chose. Each bundle is
    one create-only transaction, and re-running the act over unchanged content
    submits none.
    """
    return tuple(install_rule_binding(world, bundle) for bundle in shipped_rule_bundles())


def open_world(config: WorldConfig, *, authority: Authority) -> World:
    """Open one configured world root, its three identity claims agreeing.

    A world says who it is in three places — the configuration the caller holds,
    the `world.yaml` mirror, and the chain genesis the root was minted under —
    and this is the surface every ordinary consumer crosses, so it is where the
    disagreement is **refused** (log-verification design §6.3, discharging the
    slice-1/2 deferral). The genesis payload is read through `read_chain`, and
    the two refusals it can raise are the export act's own, single-homed in
    `anchors._require_world_genesis`: a payload that is not a Science world
    genesis at all says the root was never initialized as one
    (`WorldUninitialized`), and a well-formed genesis naming another world says
    the configuration and the chain disagree (`WorldIdMismatch`).

    A root with **no registered chain at all** joins the first of those two.
    `read_chain` reports it as `PreconditionRefused`, and `WorldUninitialized` is
    already Science's name for the state — the very name the mirror loader raises
    for a root `init_world_root` never made. The mapping is made **here**, at the
    boundary that made the read, and not in the seam: §6.4's translation
    vocabulary is closed at three engine states and this is not one of them.

    **The mapping is conditioned, not by type.** `PreconditionRefused` is not
    that one fact: `read_chain` resolves recovery *before* it reaches the
    registration check, and resolution refuses with the same class for reasons of
    its own — an observation whose namespace moved under it, a create whose
    target appeared while the plan ran. Renaming any of those "never initialized
    as a world" would be a false statement about a registered root that is
    mid-recovery, with the truth visible only on `__cause__`. So only
    `UNREGISTERED_ROOT`'s exact wording is mapped and everything else propagates
    untouched.

    **Opening is no longer a cheap read.** `read_chain` takes the atoms project
    lock and **resolves recovery** before it answers, so this call can now block
    on a concurrent build or writer holding the same root's lease, recovers an
    interrupted transaction as a side effect of opening, and requires the
    certified volume that every other act on an opened `World` already required.

    The detection/refusal split is deliberate: `audit_log` **reports** the same
    fact as a subject-mismatch finding and takes the configuration rather than
    an opened `World` precisely so that auditing the worlds this call refuses
    stays possible (§6.1).
    """
    mirror_id = _load_world_mirror(config.world_root)
    if mirror_id != config.world_id:
        raise WorldIdMismatch(f"{config.world_root / 'world.yaml'}: world_id does not match configuration")
    try:
        head = _log_seam().read_head(config.world_root)
    except PreconditionRefused as caught:
        if str(caught) != UNREGISTERED_ROOT:
            # Recovery resolution ran first and refused for a reason of its own.
            # That is not this refusal and is not renamed into it.
            raise
        raise WorldUninitialized(
            f"{config.world_root}: the world root carries no registered chain, so it was never initialized "
            "as a world; init_world_root is the act that mints one"
        ) from caught
    _require_world_genesis(config.world_root, head.genesis_payload, config.world_id)
    return World(
        config,
        _world_executor_factory(),
        chain_head=chain_head_reader(),
        corpus_executor_factory=durable_executor_factory(),
        authority=authority,
    )
