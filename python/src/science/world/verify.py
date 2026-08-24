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

**And the evaluator** (design §4): the one read-only function that turns a
chain view, an observer set and a scanned surface into a `LogReport`, in the
four steps §4.2 fixes. It is the entire judgment surface — audit and arrival
both call it, and no third path evaluates.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from nodes.core.errors import NodesError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.ids import NodeId
from nodes.core.node import Node
from yaml import YAMLError

from science.corpus import Finding, OperationLock
from science.errors import (
    ArrivalCause,
    ArrivalRefused,
    AuditTargetUnconfigured,
    EpochMalformed,
    EpochUnknown,
    MalformedRecord,
    ManifestMalformed,
    ManifestMissing,
    ObserverCarrierInvalid,
    SubjectMismatch,
    WorldUninitialized,
)
from science.stored import verification_value
from science.world.logmodel import (
    AbsentView,
    ChainHead,
    ChainView,
    DefectView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

if TYPE_CHECKING:  # pragma: no cover - the cycle below is real at run time
    from science.world.anchors import HeadArtifact, LogHeadRecord, Subject
    from science.world.registry import AdmissionRecord, ReplicaOf, World, WorldConfig

__all__ = [
    "CHAIN_ABSENT",
    "ArtifactCarrier",
    "EpochCarrier",
    "LogReport",
    "LogSeam",
    "ObserverCarrier",
    "ObserverSet",
    "Ordering",
    "PresentedIdentity",
    "PresentedManifest",
    "PresentedWorldIds",
    "Provenance",
    "RegistryCarrier",
    "ReplayResult",
    "RootKind",
    "evaluate_log",
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

RootKind: TypeAlias = Literal["corpus", "world", "store"]

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
    if kind == "store":
        # The whole-namespace projection: a store's payload is opaque, so
        # every non-bookkeeping root-relative entry is claimed. The walker's
        # own dot-prefix rule already excludes exactly bookkeeping — the
        # chain leaf, the root claim, engine metadata — and nothing else,
        # and symlinks stay leaves here as everywhere.
        return tuple(sorted(_files_beneath(root, "")))
    raise ValueError(f"{kind!r} is not a projected root kind: the projection is instantiated per root kind")


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


# --- the observer carriers (design §4.1) ------------------------------------
#
# `science.world.anchors` imports this module for `LogSeam`, so the codecs and
# subjects it owns are reached **at call time, in the module form** — the same
# edge treatment `anchors` itself gives `science.world.registry`. A name-form
# import in either direction would make one import order fail; the annotations
# below are strings (`from __future__ import annotations`) and resolve for a
# type checker through the `TYPE_CHECKING` block alone.

Provenance: TypeAlias = Literal["named-local", "supplied-export"]
"""§4.1's provenance discriminator: read from the world root under
verification, or held by the caller from outside it.

It is a member of every carrier and not only of the epoch arm, because the
eligibility rule the discriminator exists for (`world` accepts supplied-export
only, L11) has to be answerable for whatever a caller supplied. A registry
record is `named-local` by construction — the registry it is read from is the
world root's own — and a head artifact is `supplied-export` by construction:
its bytes reached the caller's hands to be passed in at all.
"""

CHAIN_ABSENT = "chain-absent"
"""The finding code that says the chain view carried no durable claim.

A module-level constant because it is a **contract between two acts**: §6.2's
arrival causes derive from the report's fields, and this code is the whole of
what separates `chainless` (a `ReplicaOf` that did not carry its chain — always
refused) from a fresh chain nobody has anchored yet (admissible). The arrival
boundary imports this name rather than restating the string.
"""

_FACTORY_TOKEN = object()
"""The module-private witness that a carrier came through a factory.

Direct construction is unspellable outside this module: the token is the first
field of every carrier, it is not exported, and a carrier built without it
refuses. That is what makes "the factory fixes the provenance" a mechanism —
there is no parameter to mislabel and no constructor to go around.
"""


def _factory_built(token: object) -> None:
    if token is not _FACTORY_TOKEN:
        raise ObserverCarrierInvalid(
            "an observer carrier is built by its factory, which is what retains the validation evidence"
        )


def _carrier_provenance(observed: tuple[_ObservedAnchor, ...]) -> Provenance:
    """A carrier's provenance, read off the anchors it states.

    Derived rather than stored, because the eligibility rule reads the
    *anchor's* copy: a second field would be a second copy of one fact, and the
    one a reader could inspect would not be the one the verdict turned on. A
    carrier always states at least one anchor — an epoch states its world
    triple even where it covers no corpus — so there is always one to read.
    """
    return observed[0].provenance


@dataclass(frozen=True, slots=True)
class _ObservedAnchor:
    """One `(subject, genesis, head)` triple as some carrier states it.

    `provenance` and `carrier` travel with the triple rather than being looked
    up again: an epoch states many triples and the report's bound names each
    one with the custody it arrived under.
    """

    subject: Subject
    genesis: str
    head: str
    provenance: Provenance
    carrier: str


@dataclass(frozen=True, slots=True)
class RegistryCarrier:
    """A registry log-head record, grammar-checked on entry.

    Provenance is `named-local`: a record is read from the world root's own
    registry. That is never a limitation for the subjects a record can carry —
    a `world` subject is not in the record's union at all (§3.1/L11) — and it
    is exactly right for a corpus subject, whose chain lives in a different
    root from the registry anchoring it.
    """

    _token: object
    record: LogHeadRecord
    observed: tuple[_ObservedAnchor, ...]

    def __post_init__(self) -> None:
        _factory_built(self._token)

    @property
    def provenance(self) -> Provenance:
        return _carrier_provenance(self.observed)

    @staticmethod
    def from_record(record: LogHeadRecord) -> RegistryCarrier:
        """§4.1's record arm: the grammar re-checked, then the anchor lifted.

        The record's own projection is decoded back through the codec rather
        than trusted: a dataclass whose fields were written past `__post_init__`
        (or a record from a decoder that is not this one) is exactly the carrier
        this check exists to refuse, and the round trip is the record's grammar
        by definition rather than a second statement of it.
        """
        from science.world import anchors

        if type(record) is not anchors.LogHeadRecord:
            raise ObserverCarrierInvalid(
                f"a registry carrier holds a LogHeadRecord, not {type(record).__name__}"
            )
        try:
            decoded = anchors.parse_log_head_record(anchors.log_head_projection(record))
        # The codec's own refusals and nothing wider: the projection raises
        # `TypeError` on a subject or origin outside its union and the parser
        # raises `ValueError` on every grammar failure.
        except (TypeError, ValueError) as caught:
            raise ObserverCarrierInvalid(f"the log-head record does not satisfy its grammar: {caught}") from caught
        if decoded != record:
            raise ObserverCarrierInvalid("the log-head record is not what its own projection decodes to")
        observed = (
            _ObservedAnchor(record.subject, record.genesis, record.head, "named-local", "registry-record"),
        )
        return RegistryCarrier(_FACTORY_TOKEN, record, observed)


@dataclass(frozen=True, slots=True)
class ArtifactCarrier:
    """An exported head artifact, codec-validated, its canonical bytes retained.

    Provenance is `supplied-export`: an artifact is a standalone file whose
    whole purpose is to leave the root it describes, and a caller who has its
    bytes to hand in is holding an exported copy. The bytes are kept because
    they, not the decoded value, are what a holder can be asked to show again.
    """

    _token: object
    artifact: HeadArtifact
    data: bytes
    observed: tuple[_ObservedAnchor, ...]

    def __post_init__(self) -> None:
        _factory_built(self._token)

    @property
    def provenance(self) -> Provenance:
        return _carrier_provenance(self.observed)

    @staticmethod
    def from_bytes(data: bytes) -> ArtifactCarrier:
        from science.world import anchors

        try:
            artifact = anchors.decode_head_artifact(data)
        # `TypeError` for bytes that are not bytes, `ValueError` for everything
        # the codec refuses, including non-canonical encodings.
        except (TypeError, ValueError) as caught:
            raise ObserverCarrierInvalid(f"the head artifact does not decode: {caught}") from caught
        observed = (
            _ObservedAnchor(artifact.subject, artifact.genesis, artifact.head, "supplied-export", "head-artifact"),
        )
        return ArtifactCarrier(_FACTORY_TOKEN, artifact, data, observed)


@dataclass(frozen=True, slots=True)
class EpochCarrier:
    """An epoch's eleven members, revalidated against their packaging identity.

    The two factories differ in **which authority they read**, and each fixes
    its own provenance from that: `from_named_local` reads the world root's own
    epoch directory, `from_export` takes a copy the caller holds. Neither takes
    a provenance parameter, so there is nothing to mislabel.

    What a factory name cannot prove is custody. A caller may read the local
    members itself and hand them to `from_export`, so `supplied-export` is
    **caller-attested custody evidence** under the deferred holder protocol
    (§10.9): nothing in this slice learns which exported anchors actually
    survive outside the root they describe.

    **What is revalidated.** The member set is closed and the packaging
    identity is recomputed over every member's bytes — the whole eleven, which
    is why `from_export` takes the complete mapping — and the `anchors.yaml`
    member is parsed as the document §6.1 fixes, because that is the member
    read here. The other ten are covered by the identity and are the epoch
    reader's to interpret; an observer carrier is not a second epoch opener.
    """

    _token: object
    packaging_identity: str
    members: Mapping[str, bytes]
    observed: tuple[_ObservedAnchor, ...]

    def __post_init__(self) -> None:
        _factory_built(self._token)

    @property
    def provenance(self) -> Provenance:
        return _carrier_provenance(self.observed)

    @staticmethod
    def from_named_local(epoch_root: Path) -> EpochCarrier:
        """The world root's own `epochs/<packaging identity>/`, read as a carrier.

        The directory's name is the identity it claims, so recomputing the
        identity over what it holds is a real check rather than a restatement of
        the path — `_locked_open_epoch`'s check, over a carrier the evaluator
        was handed instead of one an act opened.
        """
        from science.world import epoch

        directory = Path(epoch_root)
        try:
            members = dict(epoch._carrier_members(directory))
        # `EpochMalformed` for a member set or member kind the layout refuses,
        # `OSError` for the directory that is missing or unreadable.
        except (EpochMalformed, OSError) as caught:
            raise ObserverCarrierInvalid(f"{directory}: the epoch members do not read: {caught}") from caught
        return _epoch_carrier(members, directory.name, "named-local")

    @staticmethod
    def from_export(members: Mapping[str, bytes], packaging_identity: str) -> EpochCarrier:
        """A supplied epoch copy: the complete member mapping and the identity
        it claims, revalidated against each other."""
        if not isinstance(members, Mapping):
            raise ObserverCarrierInvalid("an exported epoch is supplied as a complete member mapping")
        return _epoch_carrier(dict(members), packaging_identity, "supplied-export")


def _epoch_carrier(members: dict[str, bytes], packaging_identity: str, provenance: Provenance) -> EpochCarrier:
    """The revalidation both epoch factories share, and the anchors it lifts."""
    from science.world import anchors, epoch

    if set(members) != set(epoch.EPOCH_MEMBERS) or any(type(content) is not bytes for content in members.values()):
        raise ObserverCarrierInvalid(
            f"{packaging_identity}: the member set is not the closed epoch layout {sorted(epoch.EPOCH_MEMBERS)}"
        )
    recomputed = epoch.packaging_identity_of(members)
    if recomputed != packaging_identity:
        raise ObserverCarrierInvalid(
            f"{packaging_identity}: the members recompute the packaging identity {recomputed}, "
            "so they are not the epoch this carrier claims"
        )
    try:
        document = epoch._parse_member(packaging_identity, "anchors.yaml", members["anchors.yaml"])
        world = epoch._anchor(cast("Mapping[object, object]", document["world"]))
        observed = tuple(
            _ObservedAnchor(
                anchors.CorpusSubject(triple.subject),
                triple.genesis_digest,
                triple.head_digest,
                provenance,
                f"epoch:{packaging_identity}",
            )
            for triple in epoch._corpus_anchors(document)
        ) + (
            _ObservedAnchor(
                anchors.WorldSubject(world.subject),
                world.genesis_digest,
                world.head_digest,
                provenance,
                f"epoch:{packaging_identity}",
            ),
        )
    # `_parse_member` wraps every shape failure as `EpochMalformed`, and the
    # subject constructors raise `ValueError` on an anchor subject that is not
    # an identity. Nothing between them raises anything else: the member's
    # closed-document check has already run when the triples are lifted.
    except (EpochMalformed, ValueError) as caught:
        raise ObserverCarrierInvalid(
            f"{packaging_identity}: the anchors member is not the triples §6.1 fixes: {caught}"
        ) from caught
    return EpochCarrier(_FACTORY_TOKEN, packaging_identity, MappingProxyType(members), observed)


ObserverCarrier: TypeAlias = RegistryCarrier | EpochCarrier | ArtifactCarrier


@dataclass(frozen=True, slots=True)
class ObserverSet:
    """§4.1's explicit observer set. Nothing is searched for.

    A member that is not a carrier is a `TypeError` and not
    `ObserverCarrierInvalid`: the carriers in a set have already validated (a
    factory is the only way to hold one), so the remaining failure is a caller
    passing something that was never a carrier at all.
    """

    carriers: tuple[ObserverCarrier, ...]

    def __post_init__(self) -> None:
        if type(self.carriers) is not tuple:
            raise TypeError("an observer set holds an exact tuple of carriers")
        for carrier in self.carriers:
            if type(carrier) not in {RegistryCarrier, EpochCarrier, ArtifactCarrier}:
                raise TypeError(f"{type(carrier).__name__} is not an observer carrier")


# --- the report (design §4.1) -----------------------------------------------


@dataclass(frozen=True, slots=True)
class LogReport:
    """One frozen verdict, and everything the verdict was reached over.

    `outcome` is the only judgment: no error doubles as an outcome and no
    outcome doubles as an error. `anchored_through` is the maximal anchored
    head by chain ancestry — never by record order — and `unanchored_tail` is
    L5's residue after it, which is the whole chain where nothing anchors it.
    `intents_unevaluated` states §10.1's deferral in the report itself rather
    than in a document beside it: the inventory is carried, the qualification
    is not made. `observer_bound` names every anchor the subject filter and the
    eligibility rule admitted, with its provenance, and is never discarded.
    """

    outcome: Literal["validated", "refuted", "unresolvable", "malformed"]
    anchored_through: str | None
    unanchored_tail: tuple[str, ...]
    pending: tuple[tuple[str, str], ...]
    intents_unevaluated: tuple[str, ...]
    observer_bound: tuple[str, ...]
    findings: tuple[Finding, ...]


def _report(
    outcome: Literal["validated", "refuted", "unresolvable", "malformed"],
    *,
    anchored_through: str | None = None,
    unanchored_tail: tuple[str, ...] = (),
    pending: tuple[tuple[str, str], ...] = (),
    intents: tuple[str, ...] = (),
    bound: tuple[str, ...] = (),
    findings: tuple[Finding, ...] = (),
) -> LogReport:
    return LogReport(outcome, anchored_through, unanchored_tail, pending, intents, bound, findings)


# --- the evaluator (design §4.2) --------------------------------------------


def evaluate_log(
    subject: Subject,
    view: ChainView,
    observers: ObserverSet,
    disk: tuple[tuple[str, object], ...],
    presented: PresentedIdentity | None,
    absent_state: object,
    history: Mapping[str, bytes] | None = None,
) -> LogReport:
    """§4's one read-only judgment surface: four steps, four outcomes.

    Audit and arrival both call this and no third path evaluates. Nothing is
    searched for: the chain view, the observer set, the scanned surface and the
    presented identity are all supplied, and the act neither opens a root nor
    mints anything.

    **Before the precedence**, one refusal that is not a judgment. A `history`
    that does not validate refuses the act outright (§5.3) — corrupt evidence
    is never silently ignored, and the refusal comes before any outcome is
    produced, so a malformed chain does not get to answer first. Store
    subjects are judged like the other two kinds: the shape-only refusal was
    the log slice's, and the root-lifecycle slice removed it.

    **Then §4.2's four steps, in order, so no state earns two outcomes:**

    1. **Structure.** A malformed chain is `malformed`, stopping with the
       defect named; an absent chain skips to step 2; a present chain's genesis
       form is validated *now* — the Science payload for the subject's kind and
       the empty baseline §1.3 requires. A valid world genesis naming a
       different `world_id` is §6.3's subject mismatch instead, never malformed.
    2. **Anchors.** The subject filter runs first and alone — the presented
       identity never admits or discards an anchor — then the eligibility rule
       (a world subject accepts supplied-export carriers only, L11). Per bound
       anchor: a wholly absent chain refutes (removal); a genesis the chain does
       not share refutes (replacement); a head the chain's ancestry cannot reach
       refutes, and so does a pair the chain cannot order. A reachable old
       anchor never hides a missing newer one, because every bound anchor is
       checked. An empty bound set is `unresolvable`, replay not reached.
    3. **Pending.** Any pending registration is `unresolvable`, replay not
       reached, never inferred from disk.
    4. **Replay.** Any disagreement refutes; otherwise `validated`, with the
       unanchored tail stated.

    **Subject-mismatch findings** (§6.3) compare the presented identity and the
    genesis against the selected subject. They are findings in every outcome —
    including `validated`, since a cooperatively logged identity rewrite
    replays consistently (§1.2) — and they never filter anchors. Turning one
    into a refusal is the arrival boundary's act, not this function's.

    A `LogEvidenceRefused` raised by a seam call the caller made before this
    one is outside every precedence and never reaches here as an outcome.
    """
    if history is not None:
        validate_history(history)
    kind = _subject_kind(subject)
    if type(observers) is not ObserverSet:
        raise TypeError("observers is an ObserverSet, which is the whole of what the evaluator may consult")
    if type(disk) is not tuple:
        raise TypeError("disk is the captured surface as a tuple of (path, state) pairs")

    bound, ineligible = _bound_anchors(subject, observers, kind)
    labels = tuple(_bound_entry(anchor) for anchor in bound)
    findings = list(_presented_findings(subject, kind, presented)) + list(ineligible)

    # Step 1 — structure.
    if type(view) is MalformedView:
        return _report("malformed", bound=labels, findings=tuple(findings) + (_defect_finding(view.defect),))
    if type(view) is AbsentView:
        # No genesis to validate and no entries to reach: an absent chain is
        # decided wholly at step 2, by whether anything anchored it.
        if bound:
            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))
        return _report(
            "unresolvable",
            bound=(),
            findings=tuple(findings) + (_chainless_finding(), _unanchored_finding(subject)),
        )
    if type(view) is not WellFormedView:
        raise TypeError(f"{type(view).__name__} is not a chain view")

    intents = tuple(entry.digest for entry in view.entries if type(entry) is IntentEntryView)
    defect, genesis_identity = _genesis_form(kind, view.genesis)
    if defect is not None:
        # The inventory is carried even here: §10.1 asks that the qualification
        # deferral be stated in *every* report, and a chain the engine
        # linearized has an intent inventory whatever its genesis payload says.
        # The `MalformedView` exit above states none because there are no
        # entries there to inventory, which is a different fact.
        return _report("malformed", intents=intents, bound=labels, findings=tuple(findings) + (defect,))
    findings.extend(_genesis_findings(subject, kind, genesis_identity))

    pending = view.pending
    digests = tuple(entry.digest for entry in view.entries)
    positions = {digest: index for index, digest in enumerate(digests)}

    # Step 2 — anchors.
    if not bound:
        return _report(
            "unresolvable",
            unanchored_tail=digests,
            pending=pending,
            intents=intents,
            findings=tuple(findings) + (_unanchored_finding(subject),),
        )
    anchored_through, tail = _extent(bound, view.genesis.digest, positions, digests)
    refutations = _anchor_refutations(bound, view.genesis.digest, positions)
    if refutations:
        return _report(
            "refuted",
            anchored_through=anchored_through,
            unanchored_tail=tail,
            pending=pending,
            intents=intents,
            bound=labels,
            findings=tuple(findings) + refutations,
        )

    # Step 3 — pending.
    if pending:
        return _report(
            "unresolvable",
            anchored_through=anchored_through,
            unanchored_tail=tail,
            pending=pending,
            intents=intents,
            bound=labels,
            findings=tuple(findings) + tuple(_pending_finding(txid, digest) for txid, digest in pending),
        )

    # Step 4 — replay.
    result = replay(view, disk, absent_state, history)
    findings.extend(result.findings)
    findings.extend(_disagreement_finding(disagreement) for disagreement in result.disagreements)
    return _report(
        "refuted" if result.refuted else "validated",
        anchored_through=anchored_through,
        unanchored_tail=tail,
        pending=pending,
        intents=intents,
        bound=labels,
        findings=tuple(findings),
    )


SubjectKind: TypeAlias = Literal["corpus", "world", "store"]


def _subject_kind(subject: Subject) -> SubjectKind:
    from science.world import anchors

    if type(subject) is anchors.CorpusSubject:
        return "corpus"
    if type(subject) is anchors.WorldSubject:
        return "world"
    if type(subject) is anchors.StoreSubject:
        return "store"
    raise TypeError(f"{type(subject).__name__} is not a verification subject")


def _subject_label(subject: Subject) -> str:
    from science.world import anchors

    if type(subject) is anchors.CorpusSubject:
        return f"corpus:{subject.corpus_id}"
    if type(subject) is anchors.WorldSubject:
        return f"world:{subject.world_id}"
    if type(subject) is anchors.StoreSubject:
        return f"store:{subject.store_id}"
    raise TypeError(f"{type(subject).__name__} is not a verification subject")


def _bound_anchors(
    subject: Subject, observers: ObserverSet, kind: SubjectKind
) -> tuple[tuple[_ObservedAnchor, ...], tuple[Finding, ...]]:
    """§4.2 step 2's two admissions, in their ruled order.

    **The subject filter is first and it is the sole filter**: an anchor for
    another subject is not this subject's evidence, and since every corpus
    chain shares the identical genesis digest (§1.2) a filter that looked at
    genesis would pool two corpora's anchors into one comparison.

    **Then eligibility**, which is about custody rather than about the bytes: a
    world subject accepts `supplied-export` carriers only, because an epoch
    copy or artifact that never left the world root anchors nothing about that
    root (L11). Identical epoch bytes, different eligibility. An excluded
    carrier is reported as a finding rather than dropped in silence — a caller
    who supplied evidence is told why it bound nothing.
    """
    bound: list[_ObservedAnchor] = []
    ineligible: list[Finding] = []
    for carrier in observers.carriers:
        for anchor in carrier.observed:
            if anchor.subject != subject:
                continue
            if kind == "world" and anchor.provenance != "supplied-export":
                ineligible.append(
                    Finding(
                        severity="warning",
                        code="observer-ineligible",
                        ref=anchor.carrier,
                        detail=f"provenance={anchor.provenance} head={anchor.head}",
                        message="a world subject accepts supplied-export carriers only: a copy that never left "
                        "the world root anchors nothing about it",
                    )
                )
                continue
            bound.append(anchor)
    return tuple(bound), tuple(ineligible)


_CUSTODY: Mapping[Provenance, str] = MappingProxyType(
    {"named-local": "read-from-root", "supplied-export": "caller-attested"}
)
"""What each provenance is *evidence of*, stated in the bound itself.

A factory fixes the discriminator from the authority it read, but a factory
name cannot prove custody: a caller may read the local epoch members itself and
hand them to `from_export`. So `supplied-export` is caller-attested evidence
under the deferred holder protocol (§10.9) — nothing in this slice learns which
exported anchors survive outside the root they describe — while `named-local`
is a read this module performed. A reader of the bound is told which of the two
they are holding.
"""


def _bound_entry(anchor: _ObservedAnchor) -> str:
    return (
        f"{anchor.carrier} provenance={anchor.provenance} custody={_CUSTODY[anchor.provenance]} "
        f"subject={_subject_label(anchor.subject)} genesis={anchor.genesis} head={anchor.head}"
    )


def _defect_finding(defect: DefectView) -> Finding:
    """The malformed exit's one finding: the engine's own defect, named.

    `subject` is `None` for exactly one defect kind — a chain with zero or
    several geneses has no single offending entry — and the reference reads
    `chain` there rather than inventing a digest.
    """
    return Finding(
        severity="error",
        code="chain-malformed",
        ref=defect.subject if defect.subject is not None else "chain",
        detail=f"kind={defect.kind}",
        message=defect.detail,
    )


def _genesis_defect(genesis: GenesisEntryView, reason: str) -> Finding:
    return Finding(
        severity="error",
        code="genesis-form-invalid",
        ref="genesis",
        detail=f"digest={genesis.digest}",
        message=reason,
    )


def _genesis_form(kind: SubjectKind, genesis: GenesisEntryView) -> tuple[Finding | None, str | None]:
    """§4.2 step 1's genesis-form validation: the defect, and the named identity.

    Returns `(None, identity)` for a well-formed genesis — the world or store
    id the payload names, which the subject-mismatch check then compares
    against the selected subject, and `None` for a corpus genesis, whose
    payload carries no identity at all (§1.2).

    **The form itself is `anchors`'** (`parse_corpus_genesis`,
    `parse_world_genesis`), which is also what the export act's subject binding
    reads. One predicate, two consequences: a refusal there, a finding here.
    What is this step's own is the *consequence* — a malformed genesis is an
    outcome, never an exception — and the empty-baseline rule, which is a fact
    about the chain's first entry rather than about its payload.

    A world genesis naming *another* well-formed world is not a defect here on
    purpose: it is §6.3's mismatch, and calling it malformed would report a
    lifecycle fact as structural damage — and would make the audit of exactly
    the world `open_world` refuses report the wrong thing (§6.1).
    """
    from science.world import anchors

    identity: str | None = None
    forked = False
    try:
        if kind == "corpus":
            anchors.parse_corpus_genesis(genesis.payload)
        elif kind == "store":
            identity, forked_from = anchors.parse_store_genesis(genesis.payload)
            forked = forked_from is not None
        else:
            identity = anchors.parse_world_genesis(genesis.payload)
    except ValueError as caught:
        return _genesis_defect(genesis, str(caught)), None
    if genesis.baseline != () and not forked:
        return _genesis_defect(
            genesis,
            "a non-fork genesis baseline is empty: the Science initializers register the empty surface, and only "
            "a fork genesis — whose payload states forked_from — registers the destination surface it copied "
            "(§1.3, the fork-baseline lift)",
        ), None
    return None, identity


def _mismatch(source: str, claimed: str, subject: Subject) -> Finding:
    return Finding(
        severity="error",
        code="subject-mismatch",
        ref=source,
        detail=f"claims={claimed} subject={_subject_label(subject)}",
        message="the identity this root presents is not the subject the verification selected",
    )


def _presented_findings(
    subject: Subject, kind: SubjectKind, presented: PresentedIdentity | None
) -> tuple[Finding, ...]:
    """§6.3's mismatch, on the side of it the chain cannot answer.

    A state fingerprint proves what happened to a surface, never which corpus
    or world the operator believes they hold, so the claim is compared as an
    explicit input. `None` is "no claim was supplied", which is not agreement
    and not disagreement: an arrival always supplies one, and an audit over a
    root whose manifest could not be read has nothing to compare.

    A mirror that is absent is left to replay, which sees `world.yaml` missing
    from a claimed surface as a head disagreement — a missing file is not a
    disagreeing claim, and reporting it here as one would say a root claimed
    something it never claimed.
    """
    if presented is None:
        return ()
    if kind == "store":
        raise TypeError("a store subject presents no identity: nothing but its genesis names one")
    if kind == "corpus":
        if type(presented) is not PresentedManifest:
            raise TypeError("a corpus subject's presented identity is a PresentedManifest")
        if presented.corpus_id != subject.corpus_id:  # pyright: ignore[reportAttributeAccessIssue]
            return (_mismatch("manifest", presented.corpus_id, subject),)
        return ()
    if type(presented) is not PresentedWorldIds:
        raise TypeError("a world subject's presented identity is a PresentedWorldIds")
    world_id: str = subject.world_id  # pyright: ignore[reportAttributeAccessIssue]
    findings: list[Finding] = []
    if presented.configured != world_id:
        findings.append(_mismatch("configured", presented.configured, subject))
    if presented.mirrored is not None and presented.mirrored != world_id:
        findings.append(_mismatch("mirror", presented.mirrored, subject))
    return tuple(findings)


def _genesis_findings(subject: Subject, kind: SubjectKind, genesis_identity: str | None) -> tuple[Finding, ...]:
    """The genesis half of §6.3's comparison. The corpus genesis names nobody,
    so there is nothing to compare there (§1.2); world and store geneses each
    name their own id and compare against the selected subject."""
    if genesis_identity is None or kind == "corpus":
        return ()
    selected = (
        subject.store_id if kind == "store" else subject.world_id  # pyright: ignore[reportAttributeAccessIssue]
    )
    if genesis_identity == selected:
        return ()
    return (_mismatch("genesis", genesis_identity, subject),)


def _absence_findings(bound: tuple[_ObservedAnchor, ...]) -> tuple[Finding, ...]:
    return tuple(
        Finding(
            severity="error",
            code="anchor-chain-absent",
            ref=anchor.head,
            detail=f"carrier={anchor.carrier} provenance={anchor.provenance}",
            message="an anchor states a head for a chain that is wholly absent: the removal the anchor makes "
            "evident",
        )
        for anchor in bound
    )


def _unanchored_finding(subject: Subject) -> Finding:
    return Finding(
        severity="warning",
        code="unanchored",
        ref=_subject_label(subject),
        detail="bound=0",
        message="no supplied observer anchors this subject, so nothing binds this chain and replay is not reached",
    )


def _chainless_finding() -> Finding:
    """The absent chain, stated as a fact of the report rather than left to the
    caller's own copy of the view.

    §6.2's arrival causes derive from the report's fields, and `chainless` — a
    `ReplicaOf` that did not carry its chain — is otherwise indistinguishable
    in a report from a fresh chain nobody has anchored yet. Those two are
    admissible and refused respectively, so the difference has to be readable
    here.
    """
    return Finding(
        severity="warning",
        code=CHAIN_ABSENT,
        ref="chain",
        detail="",
        message="no durable chain claim: the chain directory is absent, or present and empty",
    )


def _pending_finding(txid: str, digest: str) -> Finding:
    return Finding(
        severity="warning",
        code="pending-unresolved",
        ref=txid,
        detail=f"entry={digest}",
        message="a registration nothing has settled: registered-mode inspection has already run recovery, so a "
        "surviving pending registration is evidence-starved by construction",
    )


def _disagreement_finding(disagreement: str) -> Finding:
    return Finding(
        severity="error",
        code="replay-disagreement",
        ref=disagreement,
        detail="",
        message="the timeline and the surface disagree",
    )


def _anchor_refutations(
    bound: tuple[_ObservedAnchor, ...], chain_genesis: str, positions: Mapping[str, int]
) -> tuple[Finding, ...]:
    """§4.2 step 2's three refutations over a present, well-formed chain.

    Every bound anchor is checked, never only the maximal one: a reachable old
    anchor never hides a missing newer one.

    **Genesis, then ancestry, scoped by `(subject, genesis_digest)`** (§1.2).
    For a world subject and for a future fork genesis the genesis comparison is
    the replacement arm; for a corpus subject it can never fire, because the
    corpus genesis is a constant — a replaced corpus chain is caught one line
    below, as an anchored head its ancestry cannot reach.

    **Incomparability** is the pair statement of the same fact, and it is
    reported only over pairs where *both* heads are unplaced. The chain's
    entries are a linearization, so any two heads it can place are ordered by
    it, and a placed head against an unplaced one is already said in full by
    the unreachability finding — pairing the two would emit one derived finding
    per surviving anchor and bury the fault that was found. Two unplaced heads
    are the pair that says something more: two claimed heads of one subject
    that no single chain here carries.
    """
    findings: list[Finding] = []
    unplaced: list[_ObservedAnchor] = []
    for anchor in bound:
        if anchor.genesis != chain_genesis:
            unplaced.append(anchor)
            findings.append(
                Finding(
                    severity="error",
                    code="anchor-genesis-mismatch",
                    ref=anchor.head,
                    detail=f"anchor={anchor.genesis} chain={chain_genesis}",
                    message="an anchor states a head under another genesis: the chain here is a replacement, not "
                    "the one that was anchored",
                )
            )
        elif anchor.head not in positions:
            unplaced.append(anchor)
            findings.append(
                Finding(
                    severity="error",
                    code="anchor-unreachable",
                    ref=anchor.head,
                    detail=f"carrier={anchor.carrier} provenance={anchor.provenance}",
                    message="an anchored head is not reachable by this chain's ancestry",
                )
            )
    reported: set[tuple[str, str]] = set()
    for anchor in unplaced:
        for other in unplaced:
            if other.head == anchor.head:
                continue
            pair = (anchor.head, other.head) if anchor.head < other.head else (other.head, anchor.head)
            if pair in reported:
                continue
            reported.add(pair)
            findings.append(
                Finding(
                    severity="error",
                    code="anchors-incomparable",
                    ref=pair[0],
                    detail=f"other={pair[1]}",
                    message="two anchors state heads this chain's ancestry cannot order against each other",
                )
            )
    return tuple(findings)


def _extent(
    bound: tuple[_ObservedAnchor, ...],
    chain_genesis: str,
    positions: Mapping[str, int],
    digests: tuple[str, ...],
) -> tuple[str | None, tuple[str, ...]]:
    """The maximal anchored head by ancestry, and L5's residue after it.

    Maximality is chain position and never record order — records are immutable
    and unordered (§3.1). Where no bound anchor is placed at all the extent is
    the whole chain, which is the same statement `unanchored_tail` makes for a
    chain nothing anchors.
    """
    placed = [positions[anchor.head] for anchor in bound if anchor.genesis == chain_genesis and anchor.head in positions]
    if not placed:
        return None, digests
    top = max(placed)
    return digests[top], digests[top + 1 :]


# --- the audit boundary (design §6.1) ----------------------------------------
#
# Like the two acts in `anchors`, the cores below take the seam as a parameter
# and hold no capability of their own, and they reach `science.world.registry`
# and `science.world.epoch` **at call time, in the module form** — the same
# edge treatment every cycle in this package uses.


def _audit_log(
    config: WorldConfig,
    subject: Subject,
    target_root: Path,
    observers: ObserverSet,
    *,
    actor: str,
    history: Mapping[str, bytes] | None = None,
    seam: LogSeam,
) -> LogReport:
    """§6.1: the evaluator plus a report, and **nothing else**. Writes nothing.

    **The configuration, never an opened `World`.** The act needs the
    configured root set and the world id, and it must stay callable when
    ordinary `open_world` refuses a genesis/configuration/mirror disagreement —
    auditing a broken world is the point (§6.3). So it is built from `config`
    directly, which also settles R12 by construction: there is no `World` here
    to call a method on under the lock.

    **The target root is explicit and never associated by manifest.** The
    configuration holds an unassociated root tuple and ordinary resolution
    associates a root to a subject by reading its `corpus.yaml`, so a
    manifest-based lookup could not locate the root whose manifest was
    rewritten to another id — the exact mismatch this audit exists to report.
    What is checked is only that the root is *configured*: one of the corpus
    roots for a corpus subject, the world root for a world subject. Anything
    else refuses `AuditTargetUnconfigured`.

    **One hold across inspection and capture**, so the verdict and the surface
    it judged are one view: the corpus's own operation lock through the
    lock-only lookup — an audit must remain possible over damaged node bytes,
    which constructing a `Corpus` would refuse before judging — or the world
    root's lock, the identical object an opened `World` takes. Taking a
    corpus's lock in writer mode can refuse `BuildHold` while an epoch build
    holds that root's capture, exactly as the export act can (R15): a surface
    stated from the far side of a capture would not be the surface the chain
    was inspected against.

    **Inside the hold the order is inspection, then the claim, then the
    surface** — the same pinned order `_epochs_ordered` takes below, and for
    the same reason. Registered-mode inspection runs recovery, which applies a
    settled transaction's finals to disk; a manifest or mirror read *before*
    that is a pre-recovery claim standing beside a post-recovery surface, and
    the report would then state a subject mismatch about bytes the act's own
    inspection had already replaced. **Evaluation is outside the hold**: the
    evaluator is pure over values already captured, and the hold exists to make
    those reads one view rather than to serialize the judgment.

    **The caller's own inputs are checked before the root is touched**: an
    unencodable actor, a store subject, a target root outside the
    configuration, and a `history` that does not validate (§5.3) are all facts
    about the call rather than about the root, and refusing them after a lock
    and an inspection would state a surface nobody could be told about. The
    evaluator validates the history again — it is the judgment surface and
    keeps its own guarantee — exactly as `replay` does after it.

    A `LogEvidenceRefused` from either seam call propagates untranslated: the
    act refused to judge, it did not judge (§6.4).
    """
    from science.world import registry

    registry._require_actor(actor)
    if history is not None:
        validate_history(history)
    kind = _subject_kind(subject)
    root = Path(target_root).resolve()
    _configured_target(config, kind, root)
    root_kind: RootKind = kind
    with _subject_hold(seam, root_kind, root):
        view, disk, presented = _assemble_evaluation_inputs(
            seam, root_kind, root, config
        )
    return evaluate_log(subject, view, observers, disk, presented, seam.absent_state, history)


def _assemble_evaluation_inputs(
    seam: LogSeam, kind: RootKind, root: Path, config: WorldConfig | None
) -> tuple[ChainView, tuple[tuple[str, object], ...], PresentedIdentity | None]:
    """The evaluator's inputs, assembled in the one pinned order — inspection,
    then the presented claim, then the capture — under the caller's hold.

    The exact boundary between the two judging acts: `_audit_log` calls it
    with the world configuration (its world arm reads the configured id), and
    the restore core calls it with `None` — a restore's subjects are corpus
    and store, whose claims live in the root itself. No third assembly
    exists.
    """
    view = seam.inspect_registered(root)
    presented = _presented_identity(config, kind, root)
    disk = seam.capture(root, registered_surface_paths(root, kind))
    return view, disk, presented


def _restore_subject_agrees(
    subject: Subject, kind: SubjectKind, view: ChainView, presented: PresentedIdentity | None
) -> bool:
    """Spec §7.2 step 4: the separate lifecycle precondition, never a verdict.

    Store: the validated chain's own genesis names the subject's `store_id`.
    Corpus: the presented manifest names the subject's `corpus_id` — the
    genesis is form-validated only, because a corpus genesis names nobody. A
    `validated` report with a disagreeing identity stays a validated report;
    what it does not do is admit.
    """
    from science.world import anchors

    if kind == "store":
        if type(view) is not WellFormedView:
            return False
        try:
            named, _forked_from = anchors.parse_store_genesis(view.genesis.payload)
        except ValueError:
            return False
        return named == subject.store_id  # pyright: ignore[reportAttributeAccessIssue]
    if type(presented) is not PresentedManifest:
        return False
    return presented.corpus_id == subject.corpus_id  # pyright: ignore[reportAttributeAccessIssue]


def _restore_root(
    dest_root: Path,
    subject: Subject,
    observers: ObserverSet,
    *,
    seam: LogSeam,
    grant: Callable[[Path], None],
) -> LogReport:
    """§7.2: the one held restore boundary — inspect, claim, capture,
    evaluate, gate, grant — and the existing report, unwrapped.

    Admission is observed through the lifecycle state, never the return
    value: the report is the evaluator's judgment of the copy, and the grant
    is a separate structural act taken only on `validated` **and** subject
    agreement. A malformed copy flows into the evaluator and comes back a
    `malformed` outcome, never a pre-evaluation exception. A world subject
    has no restore: a world root is reconstructed, not admitted.
    """
    kind = _subject_kind(subject)
    if kind == "world":
        raise TypeError("a world root is never restored; restore admits corpus and store copies")
    if type(observers) is not ObserverSet:
        raise TypeError("observers is an ObserverSet, which is the whole of what the evaluator may consult")
    root = Path(dest_root).resolve()
    with _subject_hold(seam, kind, root):
        view, disk, presented = _assemble_evaluation_inputs(seam, kind, root, None)
        report = evaluate_log(subject, view, observers, disk, presented, seam.absent_state)
        if report.outcome == "validated" and _restore_subject_agrees(
            subject, kind, view, presented
        ):
            grant(root)
    return report


def _subject_hold(seam: LogSeam, kind: RootKind, root: Path) -> AbstractContextManager[object]:
    """§6.1's one hold, per root kind: the world root's own lock, or — for a
    corpus and a store alike — the root's operation lock through the
    lock-only lookup, which is per-root state and constructs nothing."""
    return seam.world_lock(root) if kind == "world" else seam.corpus_lock(root)


def _configured_target(config: WorldConfig, kind: SubjectKind, root: Path) -> None:
    """The target-root rule, and the whole of it (§6.1).

    Membership of the configured tuple, compared as resolved paths —
    `WorldConfig` resolves both members on construction — and **never** a
    manifest read: associating the root to the subject by what its manifest
    claims is precisely what this act must not do.
    """
    if kind == "store":
        # A store is configured nowhere: the configuration holds corpus and
        # world roots, and a store subject's audit is over exactly the root
        # the caller supplied — which is also why the manifest-lookup trap
        # this rule exists to close cannot arise for one.
        return
    if kind == "world":
        if root != Path(config.world_root):
            raise AuditTargetUnconfigured(
                f"{root}: a world subject's audit targets the configured world root {config.world_root}"
            )
        return
    if root not in config.corpus_roots:
        configured = ",".join(sorted(str(path) for path in config.corpus_roots)) or "none"
        raise AuditTargetUnconfigured(
            f"{root}: a corpus subject's audit targets one of the configured corpus roots; configured={configured}"
        )


def _presented_identity(
    config: WorldConfig | None, kind: RootKind, root: Path
) -> PresentedIdentity | None:
    """What the root under audit *claims* to be, read from where it is written.

    Called after the inspection and before the capture, so the claim is the one
    the recovered root makes — see `_audit_log`.

    A claim that cannot be read is `None` — "no claim was supplied" — rather
    than a mismatch: a missing or malformed `corpus.yaml`, and a world root
    carrying no readable `world.yaml`, say nothing about which subject the
    operator believes they hold, and reporting them as a disagreeing claim
    would put words in a root's mouth. The bytes themselves are still judged:
    an edited manifest or mirror is a path on the registered surface, and
    replay compares it like any other.
    """
    from science.world import registry

    if kind == "store":
        # A store root writes its identity nowhere but its genesis: no
        # manifest, no mirror, so there is no claim to read and nothing to
        # put in a root's mouth.
        return None
    if kind == "corpus":
        try:
            return PresentedManifest(registry.load_manifest(root).corpus_id)
        except (ManifestMissing, ManifestMalformed):
            return None
    if config is None:
        raise TypeError("a world root's presented identity reads the configuration")
    try:
        mirrored: str | None = registry._load_world_mirror(root)
    except WorldUninitialized:
        mirrored = None
    return PresentedWorldIds(config.world_id, mirrored)


# --- the arrival boundary (design §6.2, §6.3) ---------------------------------


def _arrival_cause(report: LogReport) -> ArrivalCause | None:
    """§6.2's four causes, ranked, **derived from the report's fields**.

    Not from which precedence step produced the outcome, and that is the whole
    point of the function: a pending chain with an empty observer set is
    `unresolvable` at step 2 (unanchored) and never reaches step 3, and it still
    refuses arrival with cause `pending`. Reading the step instead of the fields
    would admit it.

    `chainless` is the one cause with no outcome of its own — an `AbsentChain`
    and a fresh chain nobody has anchored are both `unresolvable` — so it is
    read from the evaluator's own `chain-absent` finding, under the constant the
    evaluator exports (R24). Arrival keeps no second copy of the view.

    `None` is the admissible state: none of the four, which for `unresolvable`
    means a well-formed chain with an empty pending set — an arrival at a fresh
    world must be possible, and the unanchored bound is what the report records.
    """
    if report.outcome == "malformed":
        return "malformed"
    if report.outcome == "refuted":
        return "refuted"
    if report.pending:
        return "pending"
    if any(finding.code == CHAIN_ABSENT for finding in report.findings):
        return "chainless"
    return None


def _admit_arrival(
    world: World,
    corpus_root: Path,
    provenance: ReplicaOf,
    observers: ObserverSet,
    *,
    actor: str,
    history: Mapping[str, bytes] | None = None,
    seam: LogSeam,
) -> tuple[AdmissionRecord, LogReport]:
    """§6.2: verify an arriving replica's chain, then admit it. Or refuse.

    **The manifest is loaded here, never supplied.** A caller-supplied manifest
    could disagree with the bytes the lock protects, and the whole act exists to
    make one coherent statement about one root.

    **The subject comes from the provenance**: `S = Corpus(parent_corpus_id)`.
    The chain a replica traveled with is the *parent's* chain and its anchors
    bind by the parent's id, so verifying against the arriving root's own
    manifest would be verifying against a claim the chain never made.

    **Detached inspection**, because an arriving root is not a live one: there
    is no metadata root to recover from, and a pending registration the copy
    carried is honestly unresolved rather than silently settled.

    **One hold, in the existing world→corpus order**, across the manifest read,
    the inspection, the capture and the admission transaction — so the bytes
    admitted cannot change after their verdict. Inside it the order is
    inspection, then the claim, then the capture, which is the audit's pinned
    order kept for one reason rather than two: the claim and the surface must
    stand on the same side of whatever the inspection did to the root. Detached
    inspection does nothing to it today, which is why the order is pinned here
    rather than rediscovered if the mode ever changes.

    **The refusals, in their ruled order.** The report's own causes first,
    ranked `malformed > refuted > pending > chainless`; then §6.3's
    `SubjectMismatch`, which fires even on a `validated` report and fires
    **before** the transaction, so no mismatched subject is ever admitted; then
    the admission core's own refusals, which verification does not weaken.

    **It commits through `registry._locked_admit`** — the same core
    `World.admit` commits through, never a second registration path — so the
    record and its digest are byte-identical to a bare admission of the same
    manifest, provenance and actor. The observer bound is returned beside the
    record and never enters admission identity.

    No `World` method is called under the lock (R12): the world lock the seam
    hands back *is* the one `World.registry()` takes, so the core reads registry
    state through its own scan and this act reaches only for attributes.

    A `LogEvidenceRefused` from either seam call propagates untranslated: the
    act refused to judge, it did not judge, and it is neither an outcome nor an
    arrival cause (§6.4).
    """
    from science.world import anchors, registry

    registry._require_actor(actor)
    if type(provenance) is not registry.ReplicaOf:
        raise TypeError(
            "admit_arrival is the verified route for a replica: fresh and fork provenance are World.admit's"
        )
    if history is not None:
        validate_history(history)
    subject = anchors.CorpusSubject(provenance.parent_corpus_id)
    root = Path(corpus_root).resolve()
    with seam.world_lock(world.config.world_root), seam.corpus_lock(root):
        view = seam.inspect_detached(root)
        manifest = registry.load_manifest(root)
        disk = seam.capture(root, registered_surface_paths(root, "corpus"))
        report = evaluate_log(
            subject,
            view,
            observers,
            disk,
            PresentedManifest(manifest.corpus_id),
            seam.absent_state,
            history,
        )
        cause = _arrival_cause(report)
        if cause is not None:
            raise ArrivalRefused(cause, report, f"{root}: arriving as {_subject_label(subject)}")
        if manifest.corpus_id != provenance.parent_corpus_id:
            raise SubjectMismatch(
                f"{root}: the arriving manifest claims corpus {manifest.corpus_id}, but the chain it traveled "
                f"with is {_subject_label(subject)}'s — a validated chain under another corpus's identity is a "
                "lifecycle refusal, not a finding (§6.3)"
            )
        record = registry._locked_admit(
            world._state,
            world.config.world_root,
            world._executor_factory,
            lambda: manifest,
            provenance,
            actor,
        )
    return record, report


# --- the ordered-cuts predicate (design §7) ----------------------------------

Ordering: TypeAlias = Literal["ordered", "unordered"]

PUBLICATION_WITNESS = "anchors.yaml"
"""The epoch member whose creation the predicate reads as a publication.

Every publication creates all eleven members in one transaction, so any of them
would witness it. This one is chosen because it is the member the predicate
reads on the *other* side — E2's build-start world head — so a packaging change
that stopped publishing it fails both halves of the predicate together rather
than leaving one half quietly answering about nothing.
"""


def _epochs_ordered(config: WorldConfig, e1: str, e2: str, *, seam: LogSeam) -> Ordering:
    """§7: does E2 order after E1, over already validated epochs and chain?

    Ordered **iff** E2's build-start world head descends by ancestry from the
    settlement that committed E1's publication. Both halves are read from
    evidence rather than from any ordering an epoch declares about itself:
    E1's publication is the world-chain transaction that created its members,
    and E2's build-start head is the world head its `anchors.yaml` recorded at
    preflight. **Epoch sequence numbers are read by nothing** — there are none,
    and the predicate would not consult one if there were.

    `unordered` is the answer wherever the descent cannot be established, and
    each way of failing is a fact rather than a fallback: E1's publication
    missing from the chain, or settled as a rollback (no committed publication,
    so nothing to descend from); E2's recorded head absent from the chain (this
    chain does not carry the build's start, so it cannot place it); a chain
    that is absent or malformed (it carries no placeable publication at all).
    Only an established descent answers `ordered`.

    **Descent includes the settlement itself**, because the settlement is the
    tip immediately after E1's publication commits: a build started as soon as
    the publication landed records exactly that entry, and reading descent
    strictly would call the archetypal sequential pair unordered.

    Under the world lock throughout, in the pinned order: inspect first — which
    completes recovery — and then read the epoch, so the members read are the
    members recovery left. `_locked_open_epoch` is the world's own epoch reader
    and assumes the hold; no `World` method is called under the lock (R12).

    This is the log design §7's predicate **only**; the event-level relation is
    deferred and L8 is partial (§10.7).
    """
    from science.world import epoch

    first = _packaging_identity(e1)
    second = _packaging_identity(e2)
    with seam.world_lock(config.world_root):
        view = seam.inspect_registered(config.world_root)
        built_from = epoch._locked_open_epoch(config.world_root, second).world_anchor.head_digest
    if type(view) is not WellFormedView:
        return "unordered"
    settlement = _publication_settlement(view, first, seam.absent_state)
    positions = {entry.digest: index for index, entry in enumerate(view.entries)}
    if settlement is None or built_from not in positions:
        return "unordered"
    return "ordered" if positions[built_from] >= positions[settlement] else "unordered"


def _packaging_identity(value: str) -> str:
    """The identity grammar `_locked_open_epoch` holds its own argument to,
    applied to E1 as well — a value that is not a packaging identity names no
    epoch, so no chain entry can have published one."""
    from science.world import epoch

    if type(value) is not str or not epoch._PACKAGING_IDENTITY.fullmatch(value):
        raise EpochUnknown(f"{value!r} is not a packaging identity, so no epoch is named by it")
    return value


def _publication_settlement(view: WellFormedView, packaging_identity: str, absent_state: object) -> str | None:
    """The digest of the settlement that committed this epoch's publication.

    A publication is the committed transaction that *created* the epoch's
    members: the registration declares the witness path absent and states it
    present. The earliest committed settlement of such a registration is the
    moment the epoch became published, which is what a later build descends
    from; a republication after §9's deletion recreates the same members and
    does not move that moment.

    `None` where no registration published it, and where every one that did
    settled as a rollback — the two ways §7 words a missing publication.
    """
    witness = f"epochs/{packaging_identity}/{PUBLICATION_WITNESS}"
    publications = {
        entry.digest
        for entry in view.entries
        if type(entry) is RegisteredEntryView and _publishes(entry, witness, absent_state)
    }
    if not publications:
        return None
    for entry in view.entries:
        if type(entry) is SettledEntryView and entry.committed and entry.registration in publications:
            return entry.digest
    return None


def _publishes(entry: RegisteredEntryView, witness: str, absent_state: object) -> bool:
    """Whether this registration is the transition that brought `witness` into
    existence — the witness **declared** in its initial surface as absent, and
    stated present in its final.

    The initial declaration is required rather than defaulted. A transaction
    states an initial for every path it registers — the adapter records one at
    each path's first occurrence, and `CreateOp`'s is the engine's own absent
    singleton — so a registration that states a final for the witness and no
    initial for it is not a shape any publication has. Reading the missing
    declaration as absence would let such an entry count as a publication, and
    the error would run toward asserting an order the chain never established.
    """
    initial = dict(entry.initial)
    return (
        dict(entry.final).get(witness, absent_state) != absent_state
        and witness in initial
        and initial[witness] == absent_state
    )
