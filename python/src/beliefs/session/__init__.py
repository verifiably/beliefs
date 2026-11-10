"""The writer session: the contract's names, and the
two compositions over `beliefs.root`."""

from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from contextlib import ExitStack
from pathlib import Path

from beliefs.coordination import CoordinationAddress
from beliefs.corpus import (
    CoordinationResolver,
    CorpusWriter,
    Finding,
    SnapshotResolver,
    _operation_lock_for,
    _order_by_operation_lock,
    require_pins_agree,
    require_profile_compatible,
)
from beliefs.errors import ChainRole, CorpusRootRefused, ManifestMalformed, ManifestMissing, SessionRefused
from beliefs.permit import Authority, WritePermit
from beliefs.profile import ProfileSpec
from beliefs.root import durable_executor_factory, durable_operation_port, holdings_seam, log_seam, store_identity
from beliefs.session.claim import ChainClaim, claim_chain
from beliefs.session.ledger import (
    TRANSITIONS,
    ActLine,
    InvocationRecord,
    LedgerReader,
    LedgerWriter,
    SelectLine,
    SharingEvidence,
    SharingLine,
    ledger_path,
    open_ledger_reader,
    read_ledger_evidence,
)
from beliefs.session.reconcile import reconcile
from beliefs.session.staging import RunStaging
from beliefs.session.writer import (
    Claim,
    ClaimDone,
    ClaimFresh,
    ClaimMismatch,
    ClaimOpen,
    KernelRefusalValue,
    ScopedWriter,
    WriterSession,
    require_project_address,
    resolve_project,
)
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.logmodel import ChainView, WellFormedView

__all__ = [
    "TRANSITIONS",
    "ActLine",
    "Claim",
    "ClaimDone",
    "ClaimFresh",
    "ClaimMismatch",
    "ClaimOpen",
    "InvocationRecord",
    "KernelRefusalValue",
    "LedgerReader",
    "ScopedWriter",
    "SelectLine",
    "SharingEvidence",
    "SharingLine",
    "WriterSession",
    "open_attended_session",
    "open_ledger_reader",
    "open_run_session",
    "reconcile",
    "reconcile_sessions",
]


_RUN_FAMILIES = frozenset({"corpus-write", "run", "holdings"})


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    write_root: Path,
    profile: ProfileSpec,
    mounts: Mapping[Path, ProfileSpec] | None = None,
    store_root: Path | None = None,
    snapshot_resolver: SnapshotResolver | None = None,
    project: CoordinationAddress | None = None,
) -> WriterSession:
    """The interactive constructor: full permit by construction. It writes `write_root`, one of the
    configured roots, and nothing else. When `mounts` is given, it covers every
    configured root, each under the profile its own manifest pins, and
    coordination resolves over all of them. `None` opens without coordination.

    A world-bound caller passes `RetainedSnapshots(world)`; without it a
    session cannot author a snapshot-arm retraction.

    `project`, an unpinned project address, is the initial selection: it
    resolves through the coordination resolver before the session directory
    exists, and the pinned result is written into `session-open`.
    """
    return _open_session(
        world_config,
        operations_root,
        write_root=write_root,
        profile=profile,
        mounts=mounts,
        store_root=store_root,
        snapshot_resolver=snapshot_resolver,
        project=project,
        ceiling=None,
        run=False,
    )


def open_run_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    write_root: Path,
    profile: ProfileSpec,
    ceiling: WritePermit,
    mounts: Mapping[Path, ProfileSpec] | None = None,
    store_root: Path | None = None,
    snapshot_resolver: SnapshotResolver | None = None,
    project: CoordinationAddress | None = None,
) -> WriterSession:
    """The unattended constructor for a launched run: the same claims, ledger and
    reconciliation as `open_attended_session`, under `ceiling`, the permit the
    launcher's file carried (`WritePermit.from_json`). The ceiling is recorded in
    `session-open`. It must be admissible: never ungoverned, and naming only the
    `corpus-write`, `run` and `holdings` families; anything else refuses with
    `SessionRefused` before any claim or directory. The operations root is pinned
    with `O_NOFOLLOW` before the session directory is created, and an unreadable
    or symbolic-link operations root refuses with `SessionRefused`. A run session
    refuses tree writes (`RunSessionRefused("tree-write")`).
    """
    if type(ceiling) is not WritePermit:
        raise TypeError("ceiling must be a WritePermit")
    return _open_session(
        world_config,
        operations_root,
        write_root=write_root,
        profile=profile,
        mounts=mounts,
        store_root=store_root,
        snapshot_resolver=snapshot_resolver,
        project=project,
        ceiling=ceiling,
        run=True,
    )


def _open_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    write_root: Path,
    profile: ProfileSpec,
    mounts: Mapping[Path, ProfileSpec] | None,
    store_root: Path | None,
    snapshot_resolver: SnapshotResolver | None,
    project: CoordinationAddress | None,
    ceiling: WritePermit | None,
    run: bool,
) -> WriterSession:
    """The shared body: validation, then the claim-to-reconciliation block."""
    if type(world_config) is not WorldConfig:
        raise TypeError("the session constructors take an exact WorldConfig")
    if not isinstance(operations_root, Path):
        raise TypeError("operations_root must be a Path")
    if not isinstance(write_root, Path):
        raise TypeError("write_root must be a Path")
    if not isinstance(profile, ProfileSpec):
        raise TypeError("profile must be a compiled ProfileSpec")
    if mounts is not None and (
        not isinstance(mounts, Mapping)
        or any(not isinstance(key, Path) or not isinstance(value, ProfileSpec) for key, value in mounts.items())
    ):
        raise TypeError("mounts maps each configured root's Path to its compiled ProfileSpec")
    if store_root is not None and not isinstance(store_root, Path):
        raise TypeError("store_root must be a Path")
    if run:
        assert ceiling is not None
        if ceiling.ungoverned:
            raise SessionRefused("a run session's ceiling is never ungoverned")
        inadmissible = sorted(ceiling.act_families - _RUN_FAMILIES)
        if inadmissible:
            raise SessionRefused(
                f"a run session's ceiling names only corpus-write, run and holdings; not {inadmissible}"
            )
    if project is not None:
        require_project_address(project)
        if mounts is None:
            raise SessionRefused(f"{project}: an initial project needs mounted corpora to resolve it")
    write_root = write_root.resolve()
    if write_root not in world_config.corpus_roots:
        raise SessionRefused(f"write root {write_root} is not one of the configured corpus roots")
    root = write_root
    mounted: dict[Path, ProfileSpec] | None = None
    if mounts is not None:
        resolved = [Path(key).resolve() for key in mounts]
        configured = set(world_config.corpus_roots)
        if len(set(resolved)) != len(resolved) or set(resolved) != configured:
            missing = sorted(str(path) for path in configured - set(resolved))
            extra = sorted(str(path) for path in set(resolved) - configured)
            raise SessionRefused(
                f"the mounts are exactly the configured corpus roots, each once; missing {missing}, extra {extra}"
            )
        mounted = {Path(key).resolve(): value for key, value in mounts.items()}
    require_profile_compatible(profile, mounted[root] if mounted is not None else None)
    try:
        corpus_id = load_manifest(root).corpus_id
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"{root}: the corpus is not adopted: {caught}") from caught
    require_pins_agree(root, profile)
    view = log_seam().inspect_detached(root)
    if type(view) is not WellFormedView:
        raise SessionRefused(
            f"{root}: the chain is {type(view).__name__}; a session opens over a registered, well-formed root"
        )
    store_id: str | None = None
    if store_root is not None:
        store_id = store_identity(store_root)
        if store_id is None:
            raise SessionRefused(f"store root {store_root} carries no store genesis")
    resolver = _mount_resolver(mounted)
    read_mounts = tuple(sorted(path for path in mounted if path != root)) if mounted is not None else ()
    pinned = None if project is None else resolve_project(resolver, project)

    session_id = secrets.token_hex(16)
    path = ledger_path(operations_root, session_id)

    def writer_factory(authority: Authority) -> CorpusWriter:
        return CorpusWriter(
            root,
            durable_executor_factory(),
            authority=authority,
            profile=profile,
            operation_port=durable_operation_port(root, authority, profile=profile),
            coordination_resolver=resolver,
            snapshot_resolver=snapshot_resolver,
            read_mounts=read_mounts,
        )

    # The opening path owns what it acquires until it returns: each chain
    # claim, then a run session's operations-root pin, then the ledger. Any
    # exception releases them all and propagates; ledger bytes already written
    # stay (an unclosed ledger reads as an interrupted session) and the session
    # directory is not removed. Only once reconciliation returns does ownership
    # pass to the session.
    with ExitStack() as owned:
        claims = [_claim(owned, root, "write root")]
        if store_root is not None:
            claims.append(_claim(owned, store_root, "store root"))
        # A run session pins its operations root for kernel staging before the
        # session directory or `session-open` is created; the stack closes it
        # on any failure.
        staging = None
        if run:
            try:
                if not operations_root.is_symlink() and not operations_root.exists():
                    operations_root.mkdir(parents=True, exist_ok=True)
                staging = RunStaging(operations_root, session_id)
            except OSError as caught:
                raise SessionRefused(f"operations root {operations_root}: {caught}") from caught
            owned.callback(staging.close)
        path.parent.mkdir(parents=True, exist_ok=False)
        _fsync_directory(path.parent.parent)
        ledger = LedgerWriter(path)
        owned.callback(ledger.close)
        session = WriterSession(
            session_id=session_id,
            world_id=world_config.world_id,
            corpus_root=root,
            corpus_id=corpus_id,
            operations_root=operations_root,
            ledger=ledger,
            writer_factory=writer_factory,
            profile=profile,
            store_root=store_root,
            store_id=store_id,
            holdings_seam=holdings_seam() if store_root is not None else None,
            coordination_resolver=resolver,
            project=pinned,
            world_config=world_config,
            claims=tuple(claims),
            ceiling=ceiling,
            run=run,
            staging=staging,
        )
        # Session-open is written (by the constructor) before reconciliation runs.
        session.findings = reconcile_sessions(
            world_config,
            operations_root,
            exclude=session_id,
            store_roots=() if store_root is None else (store_root,),
        )
        owned.pop_all()
    return session


def _claim(owned: ExitStack, root: Path, role: ChainRole) -> ChainClaim:
    """Claim one chain and push its release onto the opening path's stack."""
    claim = claim_chain(root, role)
    owned.callback(claim.release)
    return claim


def _mount_resolver(mounted: Mapping[Path, ProfileSpec] | None) -> CoordinationResolver | None:
    """Every mount in the resolver. A read mount whose manifest does
    not load refuses as the write root's does; a pin mismatch is the resolver's own."""
    if mounted is None:
        return None
    try:
        return CoordinationResolver(mounted)
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"a mounted corpus is not adopted: {caught}") from caught


def reconcile_sessions(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    exclude: str | None = None,
    store_roots: tuple[Path, ...] = (),
) -> tuple[Finding, ...]:
    """The audit surface: one lock-coherent snapshot per root, read
    through detached inspection; writes nothing and recovers nothing.

    The session directories are listed *inside* the hold with the chains: a
    session that opens between a listing and the chain read would show an intent
    the chain holds under an id the listing never saw, and reconciliation would
    call it `session-unknown`.

    `store_roots` are read too, each keyed by its store id, so a store `act`
    line verifies against its store chain. Their operation locks join the hold
    after the corpus roots'. Every store registration under a session and its
    `act` line are written under that store root's operation lock, so inside the
    hold the store chain and the ledgers agree.
    """
    if type(store_roots) is not tuple or any(not isinstance(root, Path) for root in store_roots):
        raise TypeError("store_roots is a tuple of store root Paths")
    sessions = Path(operations_root) / "sessions"
    chains: dict[str, ChainView] = {}
    extra: list[Finding] = []
    roots = _order_by_operation_lock(world_config.corpus_roots)
    stores = _order_by_operation_lock(store_roots)
    with ExitStack() as stack:
        for root in (*roots, *stores):
            stack.enter_context(_operation_lock_for(root))
        ids = (
            sorted(entry.name for entry in sessions.iterdir() if entry.is_dir() and entry.name != exclude)
            if sessions.is_dir()
            else []
        )
        for root in roots:
            try:
                corpus_id = load_manifest(root).corpus_id
            except (ManifestMissing, ManifestMalformed) as caught:
                extra.append(
                    Finding(
                        severity="error",
                        code="session-corpus-unadopted",
                        ref=str(root),
                        detail=str(caught),
                        message="a configured corpus root with no readable manifest is not reconciled",
                    )
                )
                continue
            chains[corpus_id] = log_seam().inspect_detached(root)
        for root in stores:
            try:
                store_id = store_identity(root)
            except CorpusRootRefused as caught:
                extra.append(_store_unreadable(root, str(caught)))
                continue
            if store_id is None:
                extra.append(_store_unreadable(root, "no chain, no well-formed chain, or no store genesis"))
                continue
            chains[store_id] = log_seam().inspect_detached(root)
        ledgers = tuple(read_ledger_evidence(operations_root, sid) for sid in ids)
    # The order is `reconcile`'s own — chain id, then chain position, then code.
    # The unadopted corpus roots precede it in sorted-root order, then the
    # unreadable store roots in theirs; nothing is re-sorted.
    return (*extra, *reconcile(ledgers, chains))


def _store_unreadable(root: Path, detail: str) -> Finding:
    return Finding(
        severity="error",
        code="session-store-unreadable",
        ref=str(root),
        detail=detail,
        message="a store root whose identity cannot be read is not reconciled",
    )
