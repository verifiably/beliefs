"""The read surface over a published epoch: opening one, and answering from it.

Specification §8.1 gives a world two ways to name a publication and only two.
`open_epoch` names one **explicitly**, by the packaging identity of the bytes
it means. `current_epoch` follows the operational pointer and then performs the
same open — no weaker validation, no different result type, no separate path
into the carrier.

**`current` is operational convenience and nothing else.** It exists so a human
or a script can say "the one this world last published" without carrying a
digest around. It is not a belief input and it is not an identity: an API that
accepts belief inputs accepts an explicit producer-snapshot identity, never the
word or the function `current` (§8.1). Nothing in this module is reachable from
belief, and the reason is structural rather than a convention — a snapshot is
retrieved by its own identity from whichever retained epoch carries it.

**One lock, taken before the recovery barrier.** Every act here acquires
`_WorldState.lock` first and crosses the recovery barrier second, and it does
so through the one `registry._locked_barrier` that fixes that order for
publication and deletion too. Opening an epoch holds it through the whole
carrier read, because publication holds the same lock across its whole
transaction and a reader arriving mid-publication must wait and then see the
finished epoch rather than mistake an applied prefix for a malformed carrier.
The lock is not reentrant, which is why `current_epoch` reaches
`epoch._locked_open_epoch` directly rather than calling `open_epoch` — re-entry
would not be a style question here, it would deadlock. No `_locked_*` helper is
*defined* in this module: the three it calls — `epoch._locked_open_epoch`,
`epoch._locked_current_identity` and `rules._locked_resolve_rule_binding` —
carry the discipline in their own prefix, and every call to one below sits
inside a `registry._locked_barrier(world)` block. A helper here whose name
gained that prefix would be claiming the caller holds a lock it does not.

**What the lock does not cover is as deliberate.** Receipt validation takes it
for the recovery barrier and the rules-store resolution — a read of the store
that rule removal writes to under the same lock — and releases it before a
single corpus is opened. The corpus reads and the rule run that follow are
exactly the work `build_epoch` keeps outside its own critical section, and the
exclusion they need is per corpus and is taken per corpus. Holding the world
lock across them would put every registry append and every rule install behind
one enumeration of every covered corpus, on every coreference edge query.

**Receipt validation is the upper of §8.2's two layers.** The carrier layer
refuses bytes it cannot read; this layer judges whether a receipt that *did*
read honours §7.5's contract. The two never merge. `validate_receipt` may not
recover a contract fault by catching `EpochMalformed` — the prohibition is
written into `epoch._parse_receipt`'s docstring — and it reads a receipt
through `_ReceiptCarrier.document`, the deep-frozen whole document from the one
parse the open already performed, rather than going back to the bytes.

**The order the four outcomes are decided in is the contract, not an
optimisation.** `malformed` is settled from the document alone, before this
module has consulted a rules store or looked at a corpus, because §7.5 puts an
unsound receipt contract ahead of resolvability: a receipt naming no exact
implementation cannot be made resolvable by installing one, so asking
availability first and overriding the answer later would be reaching the right
verdict by the wrong route — and the wrong route is observable the moment two
faults coexist. Only once the contract holds does availability decide
`unresolvable`; only once availability holds does the rebuild decide between
`validated` and `refuted`.

**Every answer is bound, and the binding is a shape.** §8.3's `BoundStamp`
carries the epoch's packaging identity and its complete coverage declaration,
and every answer type takes one as a required constructor argument, so an
unstamped answer is unconstructible rather than merely unproduced. The stamp
means "from this publication over this declared coverage" and nothing else:
nothing here measures what has changed since capture, and nothing here may
imply that nothing has.

**The result unions are four small frozen dataclasses.** Not a generic result
framework, and not one type with a discriminant field. §8.3 closes the
resolution union at three arms and §8.4 closes the edge state at three values;
a framework would make both open again, and a caller would have to read a
runtime tag where a type match says the same thing statically.

**Why this is a module and not more of `epoch.py`.** Specification §3 pins the
world package's layout, and the two halves it separates are the carrier — what
an epoch *is*, how it is derived and how it is published — and the reads a
world performs *through* one.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from nodes.core.errors import NodesError

from beliefs.corpus import ReadView, _root_state_for
from beliefs.errors import (
    CaptureDrift,
    EdgeIndeterminate,
    EpochUnknown,
    ManifestMalformed,
    ResolutionRefused,
    RuleNonconformant,
    RuleNotHeld,
    SemanticHashMissing,
    SemanticHashStale,
)

# Module form for the same reason `epoch` imports `rules` that way: every use
# below is at call time, so no import order can bind a partially initialised
# name. Nothing here may touch `epoch.<name>` at module level.
from beliefs.world import derive, epoch, registry, rules

__all__ = [
    "EDGE_STATES",
    "BoundStamp",
    "EdgeAnswer",
    "Location",
    "NotPresent",
    "Resolved",
    "Unknown",
    "coreference_edge",
    "current_epoch",
    "expand_coreference",
    "open_epoch",
    "resolve_address",
    "validate_receipt",
]

EDGE_STATES: tuple[str, ...] = ("active", "inactive", "indeterminate")
"""§8.4's closed edge-state set.

`indeterminate` is a third answer rather than an error value: inspecting an
edge is entitled to return it, and only an *expansion* — which has to traverse
the edge to answer at all — refuses instead.
"""

_SUBJECT_MEMBERS: Mapping[str, str] = {
    "producer": "producer-snapshot.yaml",
    "coreference-reduction": "coreference-map.yaml",
}
"""The two subjects an epoch publishes as members of their own (§6.1)."""

_SUBJECT_KEYS: Mapping[str, str] = {
    "retraction-enumeration": "enumeration",
    "certification-enumeration": "inventory",
}
"""The two subjects §7.5 puts *inside* their receipts instead."""

_CARRIER_READ_FAULTS = (
    SemanticHashMissing,
    SemanticHashStale,
    NodesError,
    OSError,
)
"""What reading a present carrier is converted to `ResolutionRefused` for (§8.3).

Named rather than caught as `Exception`, because the refusal this converts to
is a *finding* about the carrier — "this world cannot say what it holds" — and
a bare catch would report a programming error in this module as one instead.
An `AttributeError` out of a wrong call here is a bug, and stays a bug and
escapes; the `nodes` store raising one on a malformed `relations:` entry is an
upstream hardening question and not this module's to paper over.

**Every member is driven through this catch by an arm**
(`test_resolution_refuses_every_present_carrier_read_fault`), which is the only
claim made about the list. It is deliberately not "and nothing else can
happen": `ReadView.opened_at` -> `Corpus.__init__` -> `node_from_markdown`
reaches `yaml.safe_load` and a bare `Node(...)` construction with no wrapper of
its own, so what surfaces here is whatever those raise, and the honest posture
is a list each of whose members has been *seen*, extended when a new shape is
seen. Three members were added exactly that way, after arms found them
escaping raw, and left again when `nodes` 2.0's parse floor closed the escape.

What each covers: a governed record with no semantic-identity stamp
(`SemanticHashMissing`) or a stale one (`SemanticHashStale`) is §8.3's
corruption, decided on the read path. `NodesError` covers everything the
`nodes` parse floor refuses — front matter that is not YAML, front matter
that parses and is not a node, bytes that are not UTF-8 — as well as what the
store refuses about its own layout and identifiers: since `nodes` 2.0 the read
path wraps each of those in its own `ValidationError`, where 1.2 let
`YAMLError`, pydantic's `ValidationError` and `UnicodeError` escape raw.
`OSError` is the filesystem underneath all of it.
"""


# --- opening one epoch (§8.1) -------------------------------------------------


def open_epoch(world: registry.World, packaging_identity: str) -> epoch.Epoch:
    """Open the one epoch these publication bytes name.

    The complete §8.1 check: the exact member set, every closed document, and
    the recomputed packaging identity. `EpochMalformed` for a carrier that
    fails any of it, `EpochUnknown` for a name this world retains nothing
    under. A receipt that parses and then violates §7.5's contract is *not* a
    carrier failure and opens (§8.2).
    """
    with registry._locked_barrier(world) as world_root:
        return epoch._locked_open_epoch(world_root, packaging_identity)


def current_epoch(world: registry.World) -> epoch.Epoch:
    """Open whichever epoch `epochs/current` presently names.

    One acquisition of the world lock covers the barrier, the pointer read and
    the open, so the epoch returned is the one the pointer named at a single
    moment rather than at two. A world that has published nothing has no
    current epoch, and says so: `EpochUnknown`, never an invented answer.
    """
    with registry._locked_barrier(world) as world_root:
        named = epoch._locked_current_identity(world_root)
        if named is None:
            raise EpochUnknown(
                f"{world_root / 'epochs' / epoch.CURRENT_POINTER}: "
                "this world has published no epoch, so it selects none"
            )
        return epoch._locked_open_epoch(world_root, named)


# --- receipt validation (§7.5, §8.2) ------------------------------------------


def validate_receipt(
    world: registry.World, published: epoch.Epoch, kind: derive.ReceiptKind
) -> derive.ReceiptOutcome:
    """§7.5's verdict on one receipt of one opened epoch.

    Three phases, and the order between them is the contract.

    **Well-formedness**, from the document alone. The keys are exactly
    `epoch.RECEIPT_KEYS[member]`, the discriminant is
    `epoch.RECEIPT_KINDS[member]`, every identity member is written and is a
    well-formed identity, the corpus states are sorted and name each corpus
    once, and a receipt carrying its subject's projection carries the
    projection its subject identity digests. Any failure is ``malformed`` and
    the act returns *before* the world lock is taken — an unsound contract is
    not something a store or a corpus can repair.

    **Availability.** The exact `(rule_identity, implementation_identity)` pair
    must be held here, with its fixtures run — that resolution takes the world
    lock, because it is a read of the rules store and rule removal writes to it
    under the same lock. Every named corpus must then presently stand at the
    exact state the receipt named, which is a read of each corpus under each
    corpus's own hold. Either failing is ``unresolvable``: nothing was rebuilt,
    so nothing was contradicted. A configured root claiming a manifest this
    world cannot read is ``unresolvable`` too — the named state cannot be
    reached — rather than an exception, because §8.4 makes an edge whose
    receipt is anything but ``validated`` ``indeterminate``, and a query that
    raised instead would have no answer to give.

    **The rebuild.** The exact held implementation runs over the corpora as
    re-read, and the canonical §7.6 projection it produces is compared byte for
    byte with the one this epoch published — the member for the two subjects
    §6.1 stores as members, the receipt's own carried projection for the two
    §7.5 stores inside receipts — and the subject identity is recomputed over
    it. Agreement is ``validated``; an omission, a wrong reduction, or a
    subject identity naming something else is ``refuted``.

    **The world lock is released before any corpus is opened**, and the rebuild
    runs outside it. `build_epoch` states the principle for the identical work:
    derivation happens before the lock is reacquired, "so nothing that could
    refuse or take time happens inside the critical section". A validation that
    held the world lock across an enumeration of every covered corpus and a run
    of loaded rule code would serialize every registry append and every rule
    install in the world behind one query — and every coreference edge query
    performs exactly that validation. The exclusion validation actually needs
    is per corpus, and `_standing` takes it per corpus.

    A receipt that reached here at all has already passed the carrier layer.
    This never catches `EpochMalformed` to recover a contract fault, and never
    re-reads the member bytes: `_ReceiptCarrier.document` is the one parse.
    """
    member = _member_for(kind)
    receipt = published.receipts[member]
    fault = _contract_fault(kind, member, receipt)
    if fault is not None:
        return derive.ReceiptOutcome(kind, "malformed", fault)
    # Past this point the five identity members are present and well formed,
    # so the reads below can name them without re-checking that they exist.
    named_states = cast(Sequence[tuple[str, str]], receipt.corpus_states)
    binding = rules.RuleBinding(
        cast(str, receipt.rule_identity), cast(str, receipt.implementation_identity)
    )
    with registry._locked_barrier(world) as world_root:
        try:
            held = rules._locked_resolve_rule_binding(world_root, binding)
        except RuleNotHeld as caught:
            return derive.ReceiptOutcome(
                kind,
                "unresolvable",
                f"the exact pair this receipt names is not held here: {caught}",
            )
    # The world lock is released before a single corpus is opened. Everything
    # below is a corpus read and a rule run — exactly the work `build_epoch`
    # keeps outside its own critical section — and holding the world lock
    # across it would serialize every registry append and every rule install
    # in this world behind one enumeration of every covered corpus. The
    # exclusion that matters is per corpus and is taken per corpus, below.
    captured: list[derive.CapturedCorpus] = []
    for corpus_id, corpus_state in named_states:
        try:
            carriers = registry._carrier_roots(world.config, corpus_id)
        except ManifestMalformed as caught:
            return derive.ReceiptOutcome(
                kind,
                "unresolvable",
                f"{corpus_id}: a configured root claims a manifest this world cannot read, so the "
                f"named state cannot be reached: {caught}",
            )
        if len(carriers) != 1:
            detail = ",".join(sorted(str(root) for root in carriers)) or "none"
            return derive.ReceiptOutcome(
                kind,
                "unresolvable",
                f"{corpus_id}: exactly one carrier of a named corpus is required; carriers={detail}",
            )
        standing = _standing(world, corpus_id, corpus_state, carriers[0])
        if standing is None:
            return derive.ReceiptOutcome(
                kind,
                "unresolvable",
                f"{corpus_id}: {carriers[0]}: this corpus no longer stands at the state "
                f"{corpus_state} the receipt named",
            )
        captured.append(standing)
    produced = held.invoke(derive.Capture(tuple(captured)).rule_input())
    try:
        rebuilt = derive.subject_projection(kind, produced)
    except RuleNonconformant as caught:
        return derive.ReceiptOutcome(
            kind, "refuted", f"the named implementation did not return this kind's subject: {caught}"
        )
    if epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):
        return derive.ReceiptOutcome(
            kind,
            "refuted",
            "rebuilding this subject over the named states with the named implementation "
            "produced a different projection from the one this epoch published",
        )
    if derive.subject_identity(kind, rebuilt) != receipt.subject_identity:
        return derive.ReceiptOutcome(
            kind,
            "refuted",
            f"the rebuilt subject has identity {derive.subject_identity(kind, rebuilt)}, "
            f"not the {receipt.subject_identity} this receipt names",
        )
    return derive.ReceiptOutcome(
        kind, "validated", f"the named binding rebuilt this subject over {len(named_states)} named corpus state(s)"
    )


def _member_for(kind: str) -> str:
    """The §6.1 member the named receipt kind is written to.

    A kind outside §7.5's four is a caller error and refuses here: inventing a
    fifth outcome for it would answer a question the specification does not
    ask.
    """
    for member, declared in epoch.RECEIPT_KINDS.items():
        if declared == kind:
            return member
    raise ValueError(f"{kind!r} is not one of the four receipt kinds {sorted(epoch.RECEIPT_KINDS.values())}")


def _contract_fault(kind: str, member: str, receipt: epoch._ReceiptCarrier) -> str | None:
    """§7.5's receipt contract, checked against one document, or `None`.

    This is the sole enforcer of `epoch.RECEIPT_KEYS`. The carrier layer
    *declares* the closed per-kind key set and deliberately does not police it
    (§8.2), because a receipt whose keys are wrong is one a reader can still
    lift a finding out of, and turning it into an unreadable carrier would
    close the path §8.2 exists to keep open.

    Every check here is a statement about the document and about nothing else,
    which is what makes them decidable before availability. They run in the
    order a reader would ask them: is this the declared key set, is every value
    written, is the discriminant the member's, is each identity an identity,
    are the states the sorted distinct sequence §7.5's formula digests, and —
    for the two kinds that carry their subject's projection — does that
    projection digest to the subject the receipt names.
    """
    declared = epoch.RECEIPT_KEYS[member]
    keys = {str(key) for key in receipt.document}
    if keys != set(declared):
        return (
            f"the document carries {sorted(keys)}, not the closed key set {sorted(declared)} "
            f"that {member} declares"
        )
    if receipt.missing:
        return f"the document writes no value for {list(receipt.missing)}"
    if receipt.kind != epoch.RECEIPT_KINDS[member]:
        return (
            f"the kind discriminant is {receipt.kind!r}, but {member} carries the "
            f"{epoch.RECEIPT_KINDS[member]!r} receipt"
        )
    for location, value, length in (
        ("subject", receipt.subject_identity, 64),
        ("rule_identity", receipt.rule_identity, 64),
        ("implementation_identity", receipt.implementation_identity, 64),
    ):
        try:
            registry._require_lower_hex(value, length, location)
        except ValueError as caught:
            return f"{location} is not a well-formed identity: {caught}"
    states = cast(tuple[tuple[str, str], ...], receipt.corpus_states)
    for corpus_id, corpus_state in states:
        for location, value, length in (
            ("corpus_id", corpus_id, 32),
            ("corpus_state", corpus_state, 64),
        ):
            try:
                registry._require_lower_hex(value, length, location)
            except ValueError as caught:
                return f"a corpus state names a {location} that is not a well-formed identity: {caught}"
    covered = [corpus_id for corpus_id, _state in states]
    if covered != sorted(covered):
        return "corpus_states is not sorted by corpus_id; §7.5's identity formula names sorted pairs"
    if len(set(covered)) != len(covered):
        return "corpus_states names one corpus twice"
    key = _SUBJECT_KEYS.get(kind)
    if key is not None:
        carried = receipt.document[key]
        if not isinstance(carried, Mapping):
            return f"{key} is the subject's projection, not {type(carried).__name__}"
        try:
            carried_identity = derive.subject_identity(kind, _thawed(carried))
        except Exception as caught:  # noqa: BLE001 — any refusal here is the same finding
            return f"{key} is not a projection this subject's identity can be taken over: {caught}"
        if carried_identity != receipt.subject_identity:
            return (
                f"the carried {key} has identity {carried_identity}, not the "
                f"{receipt.subject_identity} this receipt names as its subject"
            )
    return None


def _standing(
    world: registry.World, corpus_id: str, corpus_state: str, carrier: Path
) -> derive.CapturedCorpus | None:
    """One named corpus, re-read at the state the receipt named, or `None`.

    The caller does **not** hold the world lock here, and must not: this takes
    the corpus's own operation lock and runs an enumeration under it, which is
    the one thing `build_epoch` keeps out of its critical section.

    The re-read happens inside that corpus's capture hold, exactly as
    `epoch._capture` does it, and for the same reason: a state read outside the
    hold could be overtaken by a writer before the enumeration, and validation
    would then refute a receipt that was right about a corpus nobody had
    finished changing. The state is compared *first* so that a corpus which has
    moved costs one read rather than a whole enumeration, and so that the
    outcome cannot depend on whether an enumeration of an already-irrelevant
    corpus happened to refuse.

    `None` is "this corpus does not stand where the receipt named", which is
    §7.5's `unresolvable`. Drift inside the hold is `CaptureDrift`, not an
    outcome: the mover was a raw filesystem edit and there is no coherent read
    to report on.
    """
    state = _root_state_for(carrier, world._corpus_executor_factory)
    with state.lock.capture():
        before = registry.corpus_state_identity(carrier)
        if before != corpus_state:
            return None
        records = epoch._captured_records(carrier)
        after = registry.corpus_state_identity(carrier)
    if before != after:
        raise CaptureDrift(
            f"{corpus_id}: {carrier}: the corpus state moved inside a validation hold "
            f"({before} -> {after}); no rebuild is reported from a corpus that did not hold still"
        )
    return derive.CapturedCorpus(corpus_id, before, records)


def _claimed_projection(published: epoch.Epoch, kind: str, receipt: epoch._ReceiptCarrier) -> bytes:
    """The canonical bytes of the subject projection this epoch published.

    Two subjects are epoch members of their own and two live inside their
    receipts (§6.1, §7.5), so "what this epoch claims the subject is" has two
    sources — and both are canonical dumps of the same shape, which is what
    makes one byte-for-byte comparison serve all four kinds.
    """
    member = _SUBJECT_MEMBERS.get(kind)
    if member is not None:
        return published.members[member]
    return epoch._document_bytes(_thawed(cast(Mapping[object, object], receipt.document[_SUBJECT_KEYS[kind]])))


def _thawed(value: object) -> dict[str, object]:
    """A deep-frozen document as the plain value the identity encoder takes.

    `epoch._deep_frozen` turns an opened epoch's documents into read-only views
    and tuples so nothing can be written through them; `v1.encode` refuses both
    types by construction. This reverses exactly that transformation and
    nothing else — no key coercion, no defaults — so a projection lifted out of
    a member digests to what the member's own projection digested.
    """
    return cast(dict[str, object], _plain(value))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_plain(member) for member in value]
    return value


# --- bound answers (§8.3) -----------------------------------------------------


@dataclass(frozen=True)
class BoundStamp:
    """What every answer is bound to: one publication, over one coverage.

    Both members, always. The packaging identity alone would name the bytes
    without saying what they observed, and the coverage alone would say what
    was observed without saying by which publication. §8.3 asks for the epoch
    identity *and* the complete coverage declaration, and the pairs are carried
    whole — `(corpus_id, corpus_state)` — because "over this coverage" is a
    claim about the states the epoch captured, and an id without its state is a
    weaker claim wearing the same words.

    There is no third member and there will not be one. A freshness flag, a
    staleness measure or a capture timestamp would each turn the stamp from
    "this is where the answer came from" into a claim about how much the world
    has moved since, which nothing in §8.3 measures and nothing here may imply.
    """

    packaging_identity: str
    coverage: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        registry._require_lower_hex(self.packaging_identity, 64, "packaging_identity")
        if type(self.coverage) is not tuple:
            raise TypeError("coverage must be an exact tuple of (corpus_id, corpus_state) pairs")
        for pair in self.coverage:
            if type(pair) is not tuple or len(pair) != 2:
                raise TypeError("a coverage entry is an exact (corpus_id, corpus_state) pair")


@dataclass(frozen=True)
class Location:
    """Where a recorded address resolves to: a covered corpus and the `uid`
    the epoch mapped the address to.

    Not a path and not a carrier root. §7.2's address map answers with the
    stable `corpus_id` and the `uid`, both of which survive the corpus moving
    on disk; a location naming a directory would be an answer that expired
    without saying so.
    """

    corpus_id: str
    uid: str


@dataclass(frozen=True)
class Resolved:
    """The address is recorded, its corpus is singly carried here, and that
    carrier produces the `uid` the epoch mapped."""

    location: Location
    stamp: BoundStamp


@dataclass(frozen=True)
class NotPresent:
    """The address is recorded and the corpus carrying it is not here.

    A statement about this world's configuration, not about the address. A
    retired address is recorded exactly as a live one is, so this — never
    `Unknown` — is the answer when its corpus is absent (§8.3).
    """

    stamp: BoundStamp


@dataclass(frozen=True)
class Unknown:
    """The epoch's observed coverage does not record this address at all.

    The honest answer to "I never saw it", and distinct from `NotPresent` in
    the only way that matters: nothing about a corpus is being claimed.
    """

    stamp: BoundStamp


def resolve_address(
    world: registry.World, published: epoch.Epoch, address: str
) -> Resolved | NotPresent | Unknown:
    """§8.3: resolve one address through one publication, bound to it.

    The epoch's address map decides the first question and the world decides
    the second. An address the map does not record is `Unknown` — the
    publication never observed it, and no amount of live state changes that.
    An address it does record names a `corpus_id` and a `uid`; the world is
    then asked, through the registry's own presence rule, whether it carries
    that corpus exactly once. No carrier is `NotPresent`.

    **Ambiguity and corruption refuse.** Two configured roots claiming the
    corpus, a present carrier whose manifest cannot be read, and a present
    carrier that does not produce the mapped `uid` all raise
    `ResolutionRefused`. None of them may borrow `NotPresent`: that answer
    tells a caller the record is safely elsewhere, and here what actually
    happened is that this world cannot say what it holds.

    An unreadable manifest is a refusal *here* and outcome ``unresolvable`` in
    `validate_receipt`, and the asymmetry is the two sections talking about two
    different things. §8.3 closes this act's answer set at three arms and names
    the malformed manifest as one of the refusals, so there is no arm for it to
    become. §8.4 says an edge whose receipt is anything but ``validated`` is
    ``indeterminate``, which is an answer rather than a refusal — a query that
    raised instead would leave the caller with nothing where the specification
    promises a state.
    """
    stamp = _stamp(published)
    recorded = _address_map(published)
    if address not in recorded:
        return Unknown(stamp)
    corpus_id, uid = recorded[address]
    with registry._locked_barrier(world) as world_root:
        world._state.registry = registry._scan_registry(world_root)
        try:
            status = registry._reduce_status(world.config, world._state.registry, corpus_id)
        except ManifestMalformed as caught:
            raise ResolutionRefused(
                f"{address}: {corpus_id}: a configured root claims a manifest this world cannot read, "
                f"so it can say neither that the corpus is here nor that it is absent: {caught}"
            ) from caught
        if any(finding.code == "duplicate-carrier" for finding in status.findings):
            raise ResolutionRefused(
                f"{address}: {corpus_id}: more than one configured carrier claims this corpus, so which "
                "bytes answer is a configuration question rather than a resolution"
            )
        if not status.present:
            return NotPresent(stamp)
        carrier = registry._carrier_roots(world.config, corpus_id)[0]
        try:
            view = ReadView.opened_at(carrier)
            live = view.resolve(address)
            produced = None if live is None else view.get(live).uid
        except _CARRIER_READ_FAULTS as caught:
            raise ResolutionRefused(
                f"{address}: {corpus_id}: {carrier}: the present carrier cannot be read: {caught}"
            ) from caught
    if produced != uid:
        raise ResolutionRefused(
            f"{address}: {corpus_id}: {carrier}: the present carrier produces uid {produced!r}, "
            f"not the {uid!r} this epoch mapped; a carrier that disagrees with the publication is "
            "corruption and not an absence"
        )
    return Resolved(Location(corpus_id, uid), stamp)


def _stamp(published: epoch.Epoch) -> BoundStamp:
    """The one place a stamp is built, from the opened epoch and nothing else."""
    return BoundStamp(published.packaging_identity, published.coverage)


def _address_map(published: epoch.Epoch) -> Mapping[str, tuple[str, str]]:
    """§7.2's published map as `address -> (corpus_id, uid)`.

    Every entry, live and retired alike: `derive.address_map` puts each
    `deprecated_ids` member in beside its record's live address, which is what
    makes a retired address a recorded one and therefore `NotPresent` rather
    than `Unknown` when its corpus goes away.
    """
    addresses = cast(tuple[Mapping[str, str], ...], published.documents["address-map.yaml"]["addresses"])
    return {entry["address"]: (entry["corpus_id"], entry["uid"]) for entry in addresses}


# --- coreference edges (§8.4) -------------------------------------------------


@dataclass(frozen=True)
class EdgeAnswer:
    """One endpoint pair's state under one publication, bound to it.

    `missing_coverage` and `receipt_outcome` are the *reasons* an answer is
    `indeterminate`, carried on the answer rather than reconstructed by the
    caller, because they are what an expansion has to name when it refuses and
    what an operator has to act on: uncovered live corpora are fixed by
    building a wider epoch, a non-validated receipt by holding a rule or
    restoring a corpus. Both are empty and `None` on a determinate answer —
    there is nothing unestablished to report.
    """

    state: str
    stamp: BoundStamp
    missing_coverage: tuple[str, ...] = ()
    receipt_outcome: str | None = None

    def __post_init__(self) -> None:
        if self.state not in EDGE_STATES:
            raise ValueError(f"{self.state!r} is not one of {list(EDGE_STATES)}")
        if self.state != "indeterminate" and (self.missing_coverage or self.receipt_outcome is not None):
            raise ValueError("a determinate edge names no unestablished input")


def coreference_edge(world: registry.World, published: epoch.Epoch, left: str, right: str) -> EdgeAnswer:
    """§8.4: one endpoint pair's state, read through one publication.

    Two conditions, both required. The coreference receipt must have
    ``validated`` — the reduction has to be one this world can still stand
    behind — and the epoch's coverage must contain every `corpus_id` in this
    world's live span, because an epoch that did not observe a live corpus
    cannot know what that corpus attests. Wider coverage is fine: an epoch that
    observed more than the span still observed all of it.

    Where both hold, the state comes from the stored reduced balance: a
    positive balance is `active` and anything else — a zero or negative
    balance, or a pair the reduction never recorded — is `inactive`. Where
    either fails, the answer is `indeterminate` and says which input was not
    established.
    """
    endpoints = _endpoint_pair(left, right)
    stamp, missing, outcome = _edge_context(world, published)
    if missing or not outcome.validated:
        return EdgeAnswer(
            "indeterminate", stamp, missing, None if outcome.validated else outcome.outcome
        )
    balance = _reduced_pairs(published).get(endpoints)
    return EdgeAnswer("active" if balance is not None and balance > 0 else "inactive", stamp)


def expand_coreference(world: registry.World, published: epoch.Epoch, endpoint: str) -> tuple[str, ...]:
    """Every endpoint reachable from this one through `active` edges, sorted.

    The transitive closure, excluding the endpoint asked about: "what else is
    this the same thing as, according to this publication".

    **An expansion never traverses an indeterminate edge, and never skips
    one.** Skipping would report a coreference set as though the edge had been
    established `inactive`, which is precisely the claim an indeterminate edge
    withholds. So where the inputs are not established the whole act refuses,
    whether or not this particular endpoint happens to have an incident pair:
    "the set coreferent with X" is itself the thing that is indeterminate.
    `EdgeIndeterminate` names every unestablished input — the sorted live ids
    outside the coverage, the exact non-``validated`` outcome, or both.
    """
    _require_endpoint(endpoint, "endpoint")
    _stamp_unused, missing, outcome = _edge_context(world, published)
    if missing or not outcome.validated:
        raise EdgeIndeterminate(
            _indeterminate_message(published, missing, outcome),
            missing_coverage=missing,
            receipt_outcome=None if outcome.validated else outcome.outcome,
        )
    neighbours: dict[str, set[str]] = {}
    for (left, right), balance in _reduced_pairs(published).items():
        if balance > 0:
            neighbours.setdefault(left, set()).add(right)
            neighbours.setdefault(right, set()).add(left)
    reached = {endpoint}
    frontier = [endpoint]
    while frontier:
        for other in neighbours.get(frontier.pop(), ()):
            if other not in reached:
                reached.add(other)
                frontier.append(other)
    return tuple(sorted(reached - {endpoint}))


def _edge_context(
    world: registry.World, published: epoch.Epoch
) -> tuple[BoundStamp, tuple[str, ...], derive.ReceiptOutcome]:
    """The two questions §8.4 asks of the world, and the stamp both answers
    carry.

    The span is `registry._live_corpus_ids` — the registry's reduction, not the
    configured carrier-root tuple. A world does not widen its own span by being
    pointed at a directory, and a retired corpus leaves it, which is exactly
    what makes an epoch built over a wider coverage keep answering.

    Two acquisitions of the world lock, not one: `validate_receipt` takes it
    and the registry rescan takes it again. The lock is not reentrant, so
    nesting them would deadlock rather than tighten anything — and there is
    nothing to tighten, because a bound read makes no claim about a single
    instant of live state in the first place.
    """
    outcome = validate_receipt(world, published, "coreference-reduction")
    covered = {corpus_id for corpus_id, _state in published.coverage}
    missing = tuple(
        corpus_id for corpus_id in registry._live_corpus_ids(world.registry()) if corpus_id not in covered
    )
    return _stamp(published), missing, outcome


def _indeterminate_message(
    published: epoch.Epoch, missing: tuple[str, ...], outcome: derive.ReceiptOutcome
) -> str:
    """Every unestablished input, named. A generic indeterminacy message would
    be a refusal nobody can clear."""
    unestablished: list[str] = []
    if missing:
        unestablished.append(f"the live corpora {list(missing)} are outside this epoch's coverage")
    if not outcome.validated:
        unestablished.append(f"the coreference receipt is {outcome.outcome} ({outcome.detail})")
    return (
        f"{published.packaging_identity}: a coreference expansion cannot traverse an indeterminate "
        f"edge; {'; and '.join(unestablished)}"
    )


def _reduced_pairs(published: epoch.Epoch) -> Mapping[tuple[str, str], int]:
    """§7.6's published reduction as `(left, right) -> balance`.

    The distinct-key count is deliberately dropped here: §8.4 derives the edge
    state from the balance, and a reader handed both would have to be told
    which of them decides.
    """
    pairs = cast(tuple[Mapping[str, object], ...], published.documents["coreference-map.yaml"]["pairs"])
    reduced: dict[tuple[str, str], int] = {}
    for entry in pairs:
        left, right = cast(tuple[str, str], entry["endpoints"])
        reduced[(left, right)] = cast(int, entry["balance"])
    return reduced


def _endpoint_pair(left: str, right: str) -> tuple[str, str]:
    """The pair as §7.6 stores it: two distinct endpoints, sorted.

    Sorted here so `(a, b)` and `(b, a)` are one question, and refused when
    they are the same endpoint — a self-pair is a claim with no content, and
    the reduction has nowhere to have stored one.
    """
    _require_endpoint(left, "left")
    _require_endpoint(right, "right")
    if left == right:
        raise ValueError(f"{left!r} is named as both endpoints; a self-pair is not a coreference edge")
    return cast(tuple[str, str], tuple(sorted((left, right))))


def _require_endpoint(value: object, location: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{location} is a nonempty endpoint address")
    return value
