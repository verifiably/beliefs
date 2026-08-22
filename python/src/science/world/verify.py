"""The log seam, the registered-surface projection, and replay.

`LogSeam` is the whole of what an act of slice 3 may do with the engine —
inspect a chain in either mode, state a set of paths, read a validated head,
and take the two locks that make those answers true. Every act core takes one
as a parameter, and `science.root` is the only constructor of a production
seam: a test builds a stand-in, an act never reaches for one.

**What crosses and what does not.** Every callable is typed in Science's own
vocabulary (`science.world.logmodel`), so nothing here names an engine class.
The one exception is deliberate and typed as `object`: a path-state
fingerprint is the engine's own value, carried opaquely and compared only by
equality. `absent_state` is the engine's absent singleton, which replay needs
as the default of its union comparison and which Science must not mint for
itself.

**The adapters' one translation.** Three engine states escape the inspecting
commands' never-raises envelope, and the seam's adapters translate exactly
those three into `LogEvidenceRefused` (design §6.4) — a refusal to judge, not
a judgment. Everything else, `ProtocolError` and setup errors included, keeps
its own contract.

**Replay lives here too**, over the one projection (design §5): the surface a
root's declared layout claims, the accumulated timeline compared against it,
and the policy pass that turns a committed removal into a finding. None of it
imports the engine — the states it compares arrive through the seam.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from nodes.core.errors import NodesError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.ids import NodeId
from nodes.core.node import Node
from yaml import YAMLError

from science.corpus import Finding, OperationLock
from science.errors import MalformedRecord
from science.stored import verification_value
from science.world.logmodel import (
    ChainHead,
    ChainView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

__all__ = [
    "LogSeam",
    "PresentedIdentity",
    "PresentedManifest",
    "PresentedWorldIds",
    "ReplayResult",
    "RootKind",
    "registered_surface_paths",
    "replay",
    "validate_history",
]


@dataclass(frozen=True)
class LogSeam:
    """One root's worth of engine capability, as callables over `Path`.

    `inspect_registered` serves a live root: it takes the project lock, runs
    recovery and answers about chain state. `inspect_detached` serves an
    arriving root: a read-only scan, no metadata root, no recovery, pending
    honestly unresolved. `capture` states exactly the named paths, in the
    caller's order, under one coherent observation. `read_head` is the
    validated head read. `world_lock` yields holding a world root's lock —
    resolved through a lock-only lookup, so an audit locks a world it never
    opened and an opened `World` shares the identical lock object — and
    `corpus_lock` returns a corpus root's operation lock, the very one its
    writers take.
    """

    inspect_registered: Callable[[Path], ChainView]
    inspect_detached: Callable[[Path], ChainView]
    capture: Callable[[Path, tuple[str, ...]], tuple[tuple[str, object], ...]]
    read_head: Callable[[Path], ChainHead]
    absent_state: object
    world_lock: Callable[[Path], AbstractContextManager[None]]
    corpus_lock: Callable[[Path], OperationLock]


@dataclass(frozen=True)
class PresentedManifest:
    """What a corpus root's manifest claims its identity is."""

    corpus_id: str


@dataclass(frozen=True)
class PresentedWorldIds:
    """What a world root claims its identity is, from both places it is written.

    `mirrored` is `None` where the root carries no `world.yaml` at all, which
    is a different fact from a mirror that disagrees with the configuration.
    """

    configured: str
    mirrored: str | None


PresentedIdentity: TypeAlias = PresentedManifest | PresentedWorldIds
"""The typed identity input the evaluator's subject-mismatch findings compare
against.

State fingerprints alone cannot say what a root *claims* to be: a chain proves
what happened to a surface, not which corpus or world the operator believes
they are holding. The claim is therefore an explicit input rather than
something the evaluator goes looking for.
"""


# --- the registered-surface projection (design §5.1) ------------------------

RootKind: TypeAlias = Literal["corpus", "world"]

CORPUS_MANIFEST = "corpus.yaml"
WORLD_MANIFEST = "world.yaml"
WORLD_NAMESPACES = ("epochs", "registry", "rules")
"""The world root's three declared grammars: the registry, the epoch store and
the rules store. `epochs/current` is a member of `epochs/` and needs no entry
of its own."""

RECORD_SUFFIX = ".md"


def registered_surface_paths(root: Path, kind: RootKind) -> tuple[str, ...]:
    """The paths `root`'s declared layout claims, sorted, root-relative POSIX.

    One projection, instantiated per root kind (log design §3, spec §5.1): the
    genesis baseline fingerprints it, every transaction states its
    initial/final over it, and replay compares its accumulated state against
    exactly it.

    - **corpus:** every claimed node-layout path — `nodes`' own corpus-file
      claim, a `.md` leaf anywhere beneath the root — plus `corpus.yaml`. An
      undeclared foreign path (`notes.txt`) is outside the surface and outside
      this design (log design limitation 3).
    - **world:** everything beneath the three declared grammars, plus
      `world.yaml`. A namespace is a namespace: a file beneath `registry/` is
      claimed whether or not it parses as a record, which is what makes a
      raw-created record there visible rather than foreign.

    Excluded either way is bookkeeping, which is every dot-prefixed leaf:
    `.nodes-index` (the substrate's index cache, written outside the
    executor), and the engine's own reserved leaves, which carry a
    dot-prefixed sigil and include the reserved log path. No declared layout
    names a dot-prefixed leaf — a node kind and a slug are identifiers, and
    the reserved names above are `corpus.yaml`, `world.yaml` and the three
    grammar roots — so the rule excludes exactly bookkeeping and nothing
    claimed.

    Enumeration **never follows symlinks**: a symlinked directory is a leaf,
    not a way into another tree, while a symlink *at* a claimed path is itself
    a claimed path, because its state is one the surface can disagree about.
    Only paths that presently exist are listed; a path the timeline knows and
    the disk does not is replay's union comparison to make, not this one's.

    A `root` that is not a directory raises `FileNotFoundError`, both kinds
    alike: an audit whose target root is missing must refuse loudly, and a
    projection that answered `()` would hand replay a wholly absent surface as
    if it had scanned one.
    """
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"{root}: a registered surface is projected from a root directory")
    if kind == "corpus":
        # Sorted over whole paths, not per directory: a walk's own order puts
        # `a/b.md` before `a.md`, and the projection's order is its caller's
        # capture order.
        return tuple(sorted(path for path in _files_beneath(root, "") if _claimed_by_the_corpus_layout(path)))
    if kind == "world":
        return _world_surface(root)
    raise ValueError(f"{kind!r} is not a projected root kind: the projection is instantiated for corpus and world")


def _claimed_by_the_corpus_layout(path: str) -> bool:
    return path == CORPUS_MANIFEST or path.endswith(RECORD_SUFFIX)


def _world_surface(root: Path) -> tuple[str, ...]:
    """The three grammars walked by name, so a foreign sibling tree in the
    world root is never walked at all."""
    found: list[str] = []
    if _present(root / WORLD_MANIFEST):
        found.append(WORLD_MANIFEST)
    for namespace in WORLD_NAMESPACES:
        directory = root / namespace
        if not _present(directory):
            continue
        if directory.is_dir() and not directory.is_symlink():
            found.extend(_files_beneath(directory, f"{namespace}/"))
        else:
            # Something that is not a directory occupies a declared grammar's
            # name. It is a claimed path in the state the disk holds it, and
            # replay's business rather than a reason to look away.
            found.append(namespace)
    return tuple(sorted(found))


def _files_beneath(directory: Path, prefix: str) -> tuple[str, ...]:
    """Every non-directory entry beneath `directory`, prefixed, sorted, with
    symlinks treated as leaves and never followed."""
    found: list[str] = []
    with os.scandir(directory) as scan:
        children = sorted(scan, key=lambda child: child.name)
    for child in children:
        if child.name.startswith("."):
            continue
        path = f"{prefix}{child.name}"
        if child.is_dir(follow_symlinks=False):
            found.extend(_files_beneath(Path(child.path), f"{path}/"))
        else:
            found.append(path)
    return tuple(found)


def _present(path: Path) -> bool:
    """Whether anything at all occupies `path` — a broken symlink included,
    since the surface states symlinks by their target."""
    return path.is_symlink() or path.exists()


# --- the supplied historical bytes (design §5.3) ----------------------------

CONTENT_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
"""`atoms`' exact content-hash form. Spelled as a pattern rather than
reconstructed from the engine's constant: this side of the seam holds no
engine capability, and a key whose form Science guessed wrong refuses loudly
under `validate_history` rather than resolving something it should not."""


def validate_history(history: Mapping[str, bytes]) -> None:
    """Refuse a corrupt `history` input; return `None` when every pair holds.

    Three refusals, all `ValueError`: a key outside the content-hash form, a
    value that is not `bytes`, and bytes that do not hash to the key they are
    filed under. Corrupt evidence is never silently ignored, and it is never
    *partially* ignored either — the act refuses rather than classifying from
    the pairs that happened to hold.

    The evaluator calls this at entry (Task 7), before any outcome is
    produced, so a corrupt history refuses even when evaluation would stop
    before replay; `replay` calls it again, so a digest it names is always one
    it checked.
    """
    for key, payload in history.items():
        if not CONTENT_HASH.fullmatch(key):
            raise ValueError(f"{key!r} is not a content hash: the form is 'sha256:<64 lowercase hex>'")
        if type(payload) is not bytes:
            raise ValueError(f"{key}: a held copy is bytes, not {type(payload).__name__}")
        actual = hashlib.sha256(payload).hexdigest()
        if key != f"sha256:{actual}":
            raise ValueError(f"{key}: the held bytes hash to sha256:{actual}")


# --- replay (design §5.2) and the policy pass (design §5.3) -----------------


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """What replaying one chain over one disk surface established.

    `disagreements` names each one in the order replay found it: an
    initial-fingerprint disagreement as `initial:<path>@<txid>`, a head
    disagreement as `head:<path>`. `refuted` is exactly "there is at least
    one" — the evaluator turns that into the outcome, and never the reverse.
    `findings` is the policy pass's, which is a report field in every case:
    occurrence is not authorization, and a removal is neither a disagreement
    nor a refutation.
    """

    refuted: bool
    disagreements: tuple[str, ...]
    findings: tuple[Finding, ...]


def replay(
    view: WellFormedView,
    disk: tuple[tuple[str, object], ...],
    absent_state: object,
    history: Mapping[str, bytes] | None,
) -> ReplayResult:
    """Replay `view` from its genesis baseline and compare the result to `disk`.

    In chain order over **committed** registrations only: each entry's initial
    fingerprints are verified against the accumulated surface and its finals
    applied; a rolled-back registration, and one nothing has settled, is no
    transition at all.

    The comparison at the head runs over the **union** of the paths replay
    knows and the paths the disk projection discovered, an unknown state on
    either side reading as `absent_state` — so a path the timeline never
    produced disagrees, which is how a raw-created record inside the surface
    is caught, and a path the timeline produced that the disk has lost
    disagrees the same way.

    Every state here is the engine's own, carried opaquely: the only operation
    performed on one is `==`. Nothing is interpreted, and nothing is
    re-encoded — that is what keeps one summary model a mechanism.

    An initial-fingerprint disagreement is reported at the entry where the
    timeline stopped agreeing with itself, and it **skips the head
    comparison**: past that point the accumulated surface is no longer what
    the timeline claims, and comparing it against the disk would report
    consequences of the first disagreement as further evidence. The **policy
    pass still runs to the end of the chain**, because a removal is the
    timeline's own claim about its transition and an inventory truncated at
    the first disagreement would be a silently short one.
    """
    if history is not None:
        validate_history(history)
    held = _held_records(history)
    modeled: dict[str, object] = dict(view.genesis.baseline)
    committed = {
        entry.registration for entry in view.entries if type(entry) is SettledEntryView and entry.committed
    }
    findings: list[Finding] = []
    diverged: tuple[str, ...] = ()

    for entry in view.entries:
        if type(entry) is not RegisteredEntryView or entry.digest not in committed:
            continue
        if not diverged:
            diverged = tuple(
                f"initial:{path}@{entry.txid}"
                for path, state in entry.initial
                if modeled.get(path, absent_state) != state
            )
        # The transition's *declared* pre-state, not the accumulated one: what
        # a transition removed is the timeline's claim about itself, and past a
        # divergence the accumulation is no longer evidence of it.
        declared = dict(entry.initial)
        for path, state in entry.final:
            if state == absent_state and declared.get(path, absent_state) != absent_state:
                findings.extend(_removal_findings(path, entry.txid, held))
            modeled[path] = state

    if diverged:
        return ReplayResult(refuted=True, disagreements=diverged, findings=tuple(findings))
    scanned = dict(disk)
    disagreements = tuple(
        f"head:{path}"
        for path in sorted(set(modeled) | set(scanned))
        if modeled.get(path, absent_state) != scanned.get(path, absent_state)
    )
    return ReplayResult(refuted=bool(disagreements), disagreements=disagreements, findings=tuple(findings))


@dataclass(frozen=True, slots=True)
class _HeldRecord:
    """One held copy, as the policy pass reads it.

    `verdict` is a held verification's verdict and `None` for every other
    kind; `verdict_unreadable` is true for exactly one case — a held
    verification whose facet does not validate — which is a different fact
    from "not a verification" and is worded as its own classification.
    """

    digest: str
    kind: str
    verdict: str | None
    verdict_unreadable: bool


def _removal_findings(path: str, txid: str, held: Mapping[str, _HeldRecord]) -> tuple[Finding, ...]:
    """One committed removal's findings: the removal, and its classification
    where the caller's held bytes resolve the removed record.

    Logged is not permitted (log design §8): the removal finding is emitted
    for every committed removal of a claimed path, including one a legitimate
    act made, because the judgment it supports is the consumer contract's and
    not this design's. Classification is the separate claim, and it is made
    only from evidence the caller actually holds.

    **Every classification speaks about the held copy, never about the removed
    bytes.** The match is by claimed path (see `_held_records`), so a copy that
    claims the path may be a different version of the record than the one the
    transition removed; a finding that said "the removed record is not a
    failing verification" would be asserting exactly what the missing digest
    match would have had to establish.
    """
    removal = Finding(
        severity="warning",
        code="record-removed",
        ref=path,
        detail=f"txid={txid}",
        message="a committed transaction removed a registered-surface record",
    )
    resolved = held.get(path)
    if resolved is None:
        return (removal,)
    return (removal, _classification(path, txid, resolved))


def _classification(path: str, txid: str, held: _HeldRecord) -> Finding:
    """What the one held copy claiming `path` says about the removal."""
    detail = f"txid={txid} digest={held.digest} kind={held.kind}"
    if held.kind != "verification":
        return Finding(
            severity="warning",
            code="removal-classified",
            ref=path,
            detail=detail,
            message="a held copy filed under this digest claims the removed path and is not a verification",
        )
    if held.verdict_unreadable:
        return Finding(
            severity="warning",
            code="removal-classified",
            ref=path,
            detail=f"{detail} verdict=unreadable",
            message="a held copy filed under this digest claims the removed path, and its verification facet does "
            "not validate, so no verdict is read from it",
        )
    if held.verdict == "failed":
        return Finding(
            severity="error",
            code="failing-verification-removed",
            ref=path,
            detail=f"txid={txid} digest={held.digest}",
            message="a held copy filed under this digest claims the removed path and carries a failing verdict, "
            "which the kernel's immutability rules keep",
        )
    return Finding(
        severity="warning",
        code="removal-classified",
        ref=path,
        detail=f"{detail} verdict={held.verdict}",
        message="a held copy filed under this digest claims the removed path and carries no failing verdict",
    )


def _held_records(history: Mapping[str, bytes] | None) -> dict[str, _HeldRecord]:
    """The caller's held copies, indexed by the corpus path each one claims.

    **What this resolution is, and is not.** A chain entry retains a path's
    state, and a state is opaque above the composition root, so this slice
    cannot match a held copy to the removed state by digest: the resolver that
    could is the named `atoms` preimage seam (spec §10.4), and until it exists
    the match is by the path the held record's own identity claims. The
    finding names the digest the copy was filed under so a reader can check
    the claim; a possessed copy is caller-attested evidence either way. Two
    copies claiming one path resolve nothing — which of them was removed is
    exactly the question the digest match would have answered.

    Bytes that are not a Science record are not a resolution and not a
    corruption: a history may hold any blob, and `validate_history` has
    already refused the pairs that are actually corrupt.
    """
    if history is None:
        return {}
    claimed: dict[str, list[_HeldRecord]] = {}
    for digest, payload in history.items():
        try:
            node = node_from_markdown(payload.decode("utf-8"))
            path = _record_path(node.id)
        except (NodesError, ValueError, YAMLError):
            continue
        claimed.setdefault(path, []).append(_held_record(digest, node))
    return {path: copies[0] for path, copies in claimed.items() if len(copies) == 1}


def _record_path(node_id: str) -> str:
    """The corpus-relative path a record id claims.

    `nodes`' own layout rule (`nodes.core.store.Store.path_for`), read off the
    id rather than through a `Store`, which is a writable handle a module that
    mints nothing has no business holding.
    """
    parsed = NodeId.parse(node_id)
    return f"{parsed.kind}/{parsed.slug.replace(':', '__')}{RECORD_SUFFIX}"


def _held_record(digest: str, node: Node) -> _HeldRecord:
    """One decoded held copy, with its verdict read where there is one to read."""
    if node.kind != "verification":
        return _HeldRecord(digest=digest, kind=node.kind, verdict=None, verdict_unreadable=False)
    try:
        verdict = verification_value(node).verdict
    except MalformedRecord:
        return _HeldRecord(digest=digest, kind=node.kind, verdict=None, verdict_unreadable=True)
    return _HeldRecord(digest=digest, kind=node.kind, verdict=verdict, verdict_unreadable=False)
