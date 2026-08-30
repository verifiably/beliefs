"""The epoch carrier: its frozen member inventory and the receipts inside it.

A world publishes an **epoch** — a content-addressed directory holding four
derived maps, the producer snapshot, four derivation receipts, and the two
declarations that bound them — at ``epochs/<packaging_identity>/``. Slice 2's
specification §6.1 fixes that layout exactly, and `EPOCH_MEMBERS` below is that
inventory. Nothing else writes beneath ``epochs/`` except the one-line
``current`` pointer, which is a member of the *directory* ``epochs/`` and never
of an epoch.

**Two things live here, and they meet only at the draft.** The first is the
part the rules store needs: **which receipts a retained epoch carries, and
which exact rule binding each one names.** A receipt is what makes a derived
map re-checkable, so it records the exact
``(rule_identity, implementation_identity)`` that produced its subject (§7.5).
That makes the epochs directory the place — the only place — where a world can
answer "what evidence would I strand if I stopped holding this pair?", which is
what `beliefs.world.rules.remove_rule_binding` must report.

The second is a build's **coherent preflight and capture** (§5.2, §5.3) and the
**publication** that follows it (§5.4, §6.3), in the bottom half of this
module: the acts that read live state, the frozen `_BuildDraft` that separates
them from everything pure, and the one transaction that turns derived bytes
into a retained epoch. They are here rather than beside the derivations because
an epoch is what they are gathering the inputs for, and because the draft's
shape — anchors, coverage, captured states, the build-start world head — is
§6.1's layout read backwards.

A receipt identity is the digest under `RECEIPT_DOMAIN` of the canonical
projection ``(receipt kind, subject projection identity, sorted corpus-state
pairs, rule identity, implementation identity)``. The kind discriminant is what
keeps the four receipt subjects disjoint under one domain. It is carried
*inside* the document as well as implied by the member name, and the identity
digests the document's own value: a document whose discriminant disagrees with
the member holding it still has one identity, and which of the two readings is
wrong is the validator's finding to make.

**Two layers, and this module is the lower one** (§8.2). Reading a receipt out
of a carrier and judging whether that receipt honours its contract are separate
questions with separate outcomes. What refuses here is *structural
unreadability*: bytes that are not a YAML mapping, a duplicate key, or a value
that is present and is not the text the identity formula digests. Everything a
reader can still lift *something* out of is handed on intact — a discriminant
disagreeing with its member, a value that is not an identity, an unsorted or
repeated corpus state, a key outside the kind's declared set, and an identity
member the document simply omits. Those are receipt-contract violations, and
§8.2's carrier list is closed and names none of them: it is "invalid YAML, a
missing or extra epoch **member**, a bad member content name, or a
packaging-identity mismatch", where a member is one of the eleven files. A
missing receipt *key* is §7.5's own closing sentence instead — "An unsound
receipt contract is ``malformed``" — and turning one into a carrier failure
would close the path §8.2 exists to keep open, where a malformed coreference
receipt opens, evaluates as ``malformed``, and leaves its edges
``indeterminate``.

An omitted identity member is therefore read as *absent*, not as a refusal:
`_ReceiptCarrier` holds each of the five as optional and `missing` names the
ones the document did not carry, which is exactly the finding the validator
has to report. Such a receipt has no identity — there is nothing to digest —
and it names no binding, which is the honest answer rather than a convenient
one: §7.5 puts an unsound contract at ``malformed`` before resolvability is
ever asked, so no act that changes what a store *holds* can move its outcome.

`RECEIPT_KEYS` therefore *declares* the closed per-kind contract without
enforcing it: the receipt validator is what enforces it. The two
projection-bearing kinds carry more than the identity members — §7.5 puts the
retraction enumeration projection inside the retraction receipt and the
certification inventory inside the certification receipt — so one closed set
across all four kinds would be wrong in both directions at once.

**Two readings of a carrier, and the weaker one is deliberate.** The sever scan
answers "which receipts does this world retain", and it stops at the member
set: it recomputes no digest and no packaging identity, because §4.3's removal
report is about the receipts a carrier holds, not about the name the directory
holding them was given, and a stricter scan would make one damaged epoch block
every removal in its world. `_locked_open_epoch` is the strong reading, and it
is what every *read* of an epoch goes through: the exact member set, every
closed document, and the recomputed packaging identity.

**Deliberately not here yet.** Selecting `current` and reading through an epoch
belong to `beliefs.world.read`; deleting one is later still. Nothing beneath
``epochs/`` is written by any act but the one publication transaction below.

**Layering.** The *carrier* half knows nothing of the rules store: a receipt
names a binding as two digests, and reading a receipt does not require holding
what it names. The build half does need the store — preflight resolves four
exact pairs and runs their fixtures — and reaches it through
`beliefs.world.rules` at call time, which is also what keeps the import cycle
between the two modules resolvable in every order.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

import yaml
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp, WritePlan

from beliefs import stored
from beliefs.corpus import ReadView, _acyclic_postorder, _root_state_for, _validated_retraction_facet
from beliefs.errors import (
    CaptureDrift,
    CoverageNotLive,
    CoverageUnknown,
    CoverageUnresolvable,
    EnumeratedKindUngoverned,
    EpochCurrent,
    EpochMalformed,
    EpochUnknown,
)
from beliefs.identity import v1

# Module form, and every use below is at call time. `derive` and `rules` both
# import this module back, and only the module form survives every import
# order: a name-form import of either would bind at *this* module's import
# time, which is exactly the moment the partially-initialised cycle cannot
# satisfy. Nothing here may touch `derive.<name>` or `rules.<name>` at module
# level for the same reason.
from beliefs.world import derive, registry, rules

# Name form, unlike the three above: `beliefs.world.anchors` imports nothing
# from this module, so there is no cycle to survive, and the names below are
# spelled out because `anchors` is also what this module calls an epoch's
# chain-head triples.
from beliefs.world.anchors import BuildOrigin, CorpusSubject, LogHeadRecord, _log_head_member

__all__ = [
    "CURRENT_POINTER",
    "DERIVATION_KINDS",
    "ENUMERATED_SOURCE_KINDS",
    "EPOCH_DOMAIN",
    "EPOCH_MEMBERS",
    "MEMBER_KEYS",
    "RECEIPT_DOMAIN",
    "RECEIPT_IDENTITY_KEYS",
    "RECEIPT_KEYS",
    "RECEIPT_KINDS",
    "RETRACTION_RESOLUTIONS",
    "SNAPSHOT_SUBJECT",
    "DerivationBindings",
    "Epoch",
    "EpochDeletionReport",
    "SeveredIdentity",
    "build_epoch",
    "delete_epoch",
    "packaging_identity_of",
    "receipt_identity",
    "resolve_coverage",
]

EPOCH_MEMBERS: tuple[str, ...] = (
    "address-map.yaml",
    "producers-map.yaml",
    "retraction-discovery-map.yaml",
    "coreference-map.yaml",
    "producer-snapshot.yaml",
    "producer-receipt.yaml",
    "retraction-receipt.yaml",
    "certification-receipt.yaml",
    "coreference-receipt.yaml",
    "anchors.yaml",
    "coverage.yaml",
)
"""Specification §6.1's closed layout, in the order it is written there.

An epoch directory contains exactly these eleven members: a missing one and an
extra one are the same failure, `EpochMalformed`. This is the module's one
declaration of the inventory; every act over epochs reads it from here.
"""

EPOCH_DOMAIN = "science.epoch.v1"
"""§6.2's packaging-identity domain.

It names *publication bytes* and nothing else. No map location, epoch path or
packaging digest enters a semantic identity or a belief input, so this domain
never appears in the producer snapshot's formula and never will.
"""

CURRENT_POINTER = "current"
"""The one-line operational pointer beside the epoch directories.

It is a member of ``epochs/``, not of an epoch, and it is a regular file rather
than a symlink. Named here so every walk of ``epochs/`` agrees about the one
entry that is not a carrier.
"""

MEMBER_KEYS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "address-map.yaml": ("addresses",),
        "producers-map.yaml": ("producers",),
        "retraction-discovery-map.yaml": ("targets",),
        "coreference-map.yaml": ("pairs",),
        "producer-snapshot.yaml": ("coverage", "producers"),
        "anchors.yaml": ("corpora", "world"),
        "coverage.yaml": ("coverage",),
    }
)
"""The closed top-level key set of each epoch member that is not a receipt.

The seven of them, keyed exactly as `EPOCH_MEMBERS` names them, and disjoint
from `RECEIPT_KEYS` by construction: the four receipts are read by the
permissive floor below, because their contract is the receipt validator's to
enforce (§8.2) and a closed reading here would take it away.

Anchors carry the covered corpora's triples under ``corpora`` and the
build-start world-chain head under ``world``, rather than one list with the
world head folded into it. §6.1 asks for both in one member and does not say
how; keeping them apart is what stops a covered corpus from being read as the
world anchor, and the two are genuinely different subjects — a world id is not
a `corpus_id`, and only one of them is what the epoch was anchored *against*.
"""

RECEIPT_KINDS: Mapping[str, str] = MappingProxyType(
    {
        "producer-receipt.yaml": "producer",
        "retraction-receipt.yaml": "retraction-enumeration",
        "certification-receipt.yaml": "certification-enumeration",
        "coreference-receipt.yaml": "coreference-reduction",
    }
)
"""The four receipt members and the kind discriminant each one must carry."""

RECEIPT_DOMAIN = "science.derivation-receipt.v1"
"""One domain for the receipt family; §7.5's kind member keeps them disjoint."""

RECEIPT_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"kind", "subject", "corpus_states", "rule_identity", "implementation_identity"}
)
"""The five members every receipt carries, and the only ones its identity
digests. They are what this layer must be able to lift out of a document; a
document it cannot lift them from is unreadable rather than merely wrong."""

RECEIPT_KEYS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "producer-receipt.yaml": RECEIPT_IDENTITY_KEYS,
        "retraction-receipt.yaml": RECEIPT_IDENTITY_KEYS | {"enumeration"},
        "certification-receipt.yaml": RECEIPT_IDENTITY_KEYS | {"inventory"},
        "coreference-receipt.yaml": RECEIPT_IDENTITY_KEYS,
    }
)
"""The closed key set each receipt kind's document carries — §7.5's contract.

The two projection-bearing kinds carry one member more than the identity
members: the retraction receipt holds its retraction enumeration projection
(``enumeration``) and the certification receipt its location-free,
resolution-free inventory (``inventory``), neither of which is a further epoch
member. Their subject *projections* are read and checked by the receipt
validator, which is also what enforces this closure as outcome ``malformed``
(§8.2). The carrier layer below declares the contract and does not police it.
"""

_STATE_KEYS = ("corpus_id", "corpus_state")
_PACKAGING_IDENTITY = re.compile(r"[0-9a-f]{64}")


def receipt_identity(
    kind: str,
    subject_identity: str,
    corpus_states: tuple[tuple[str, str], ...],
    rule_identity: str,
    implementation_identity: str,
) -> str:
    """§7.5's receipt identity, over the five members that fix what ran.

    Each corpus-state pair encodes as a two-member list, the same shape the
    fixture-set pairs use, so one reading of "a pair" serves the whole slice.
    The formula names *sorted* pairs, so the sort belongs here rather than to
    whoever assembled the sequence — `rules.fixture_set_identity` orders its
    members for the same reason.
    """
    return v1.digest(
        RECEIPT_DOMAIN,
        [
            kind,
            subject_identity,
            [[corpus_id, corpus_state] for corpus_id, corpus_state in sorted(corpus_states)],
            rule_identity,
            implementation_identity,
        ],
    )


@dataclass(frozen=True)
class _ReceiptCarrier:
    """One receipt member of one retained epoch, reduced to what names it.

    The subject itself is not here: the identity digests the subject's
    projection identity, and severing evidence is decided by the binding, so
    the sever report never needs to reconstruct a map.

    Each of the five identity members is optional, because a document may
    simply omit one and that is a receipt-contract fault rather than an
    unreadable carrier (§7.5, §8.2). `missing` names what was omitted; a
    receipt missing anything has no `identity` and names no `binding`.
    """

    packaging_identity: str
    member: str
    kind: str | None
    """The discriminant the *document* carries, which is what the identity
    digests. `RECEIPT_KINDS[member]` is what it should be; whether the two
    agree is the validator's question, not this layer's."""
    subject_identity: str | None
    corpus_states: tuple[tuple[str, str], ...] | None
    """As the document orders them; `receipt_identity` sorts. `None` is the
    member being absent, which an empty coverage is not."""
    rule_identity: str | None
    implementation_identity: str | None
    document: Mapping[object, object]
    """The whole parsed document, deep-frozen, exactly as the member carried it.

    The five members above are what *this* layer lifts; the receipt validator
    (§8.2) has to see everything else too — a key outside
    `RECEIPT_KEYS[member]`, a subject projection that must be re-derived and
    compared — and it may not reach past the carrier to the bytes to find it.
    Carrying the document here is what lets one read of one member serve both
    layers without a second, divergent parse.
    """

    @property
    def missing(self) -> tuple[str, ...]:
        """The identity members this document did not carry, by document key.

        Empty for a receipt whose contract is sound this far. Non-empty is the
        validator's ``malformed`` finding, ready to report.
        """
        return tuple(
            key
            for key, value in (
                ("corpus_states", self.corpus_states),
                ("implementation_identity", self.implementation_identity),
                ("kind", self.kind),
                ("rule_identity", self.rule_identity),
                ("subject", self.subject_identity),
            )
            if value is None
        )

    @property
    def binding(self) -> tuple[str, str] | None:
        """The exact pair this receipt names, as ``(rule, implementation)``,
        or `None` where it named no pair.

        Two digests, compared as two digests: a receipt naming a *sibling*
        implementation of the same rule shares the first member and differs in
        the second, which is exactly the distinction removal turns on.
        """
        if self.rule_identity is None or self.implementation_identity is None:
            return None
        return (self.rule_identity, self.implementation_identity)

    @property
    def identity(self) -> str | None:
        """This receipt's identity, or `None` where the document carried too
        little to have one. An identity over invented members would be an
        identity for a receipt nobody wrote."""
        binding = self.binding
        if self.kind is None or self.subject_identity is None or self.corpus_states is None or binding is None:
            return None
        return receipt_identity(self.kind, self.subject_identity, self.corpus_states, *binding)


def _retained_receipt_bindings_locked(world_root: Path) -> tuple[_ReceiptCarrier, ...]:
    """Every receipt carried by every retained epoch of this world.

    The caller holds the world lock; this must not take it, and the lock is not
    reentrant. Ordering is deterministic — by packaging identity, then by the
    §6.1 member order — so a report derived from this scan does not depend on
    directory iteration order.

    A world that has published nothing, or whose ``epochs/`` directory is
    empty, carries no receipt. Anything else that cannot be read as the closed
    layout is `EpochMalformed`: a caller asking what evidence it is about to
    strand is owed an answer or a refusal, never a short scan.
    """
    base = Path(world_root) / "epochs"
    if base.is_symlink():
        raise EpochMalformed(f"{base}: the epochs directory is a symbolic link")
    if not base.exists():
        return ()
    if not base.is_dir():
        raise EpochMalformed(f"{base}: the epochs directory is not a directory")
    carriers: list[_ReceiptCarrier] = []
    for entry in sorted(base.iterdir()):
        if entry.name == CURRENT_POINTER:
            if entry.is_symlink() or not entry.is_file():
                raise EpochMalformed(f"{entry}: the current pointer is not a regular file")
            continue
        if entry.is_symlink() or not entry.is_dir() or not _PACKAGING_IDENTITY.fullmatch(entry.name):
            raise EpochMalformed(f"{entry}: nothing but epoch carriers and {CURRENT_POINTER!r} lives here")
        if _emptied(entry):
            continue
        carriers.extend(_receipts_of(entry))
    return tuple(carriers)


def _emptied(directory: Path) -> bool:
    """Whether this entry beneath ``epochs/`` holds nothing at all.

    §9 deletes an epoch by deleting each of its eleven members and calls the
    directory left behind nonsemantic. Nonsemantic has to mean *ignored* rather
    than merely unfilled: an empty directory read as a carrier is a carrier
    missing all eleven members, so one deletion would make every later scan of
    ``epochs/`` refuse — the sever report `beliefs.world.rules` computes
    included — and would make §9's own "a repeated deletion raises
    `EpochUnknown`" report `EpochMalformed` instead.

    It is asked *after* the name check, never instead of it: an empty directory
    whose name is not a packaging identity is still something nobody but this
    package may put here, and it still refuses.
    """
    return not any(directory.iterdir())


def _carrier_members(directory: Path) -> Mapping[str, bytes]:
    """One carrier's exact eleven members, read as bytes in §6.1's order.

    The one place a carrier's member set is decided, for the sever scan above
    and for the open act below alike. It stops at the *set*: recomputing the
    packaging identity is the open act's step, and folding it in here would
    make one world's damaged epoch refuse every rule removal in that world —
    §4.3's report is computed over the receipts a carrier holds, not over the
    name the directory holding them was given.
    """
    members: dict[str, bytes] = {}
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            raise EpochMalformed(f"{path}: an epoch member is a regular file")
        members[path.name] = path.read_bytes()
    if set(members) != set(EPOCH_MEMBERS):
        raise EpochMalformed(
            f"{directory}: the member set is not the closed epoch layout; "
            f"missing {sorted(set(EPOCH_MEMBERS) - set(members))}, "
            f"unexpected {sorted(set(members) - set(EPOCH_MEMBERS))}"
        )
    return MappingProxyType({member: members[member] for member in EPOCH_MEMBERS})


def _receipts_of(directory: Path) -> tuple[_ReceiptCarrier, ...]:
    """The four receipts of one closed carrier, in §6.1's member order."""
    members = _carrier_members(directory)
    return tuple(
        _parse_receipt(directory.name, member, members[member])
        for member in EPOCH_MEMBERS
        if member in RECEIPT_KINDS
    )


def _parse_receipt(packaging_identity: str, member: str, content: bytes) -> _ReceiptCarrier:
    """Lift §7.5's five identity-bearing members out of one receipt document.

    This is the structural floor and nothing above it. It refuses only what
    leaves no receipt to hand on: bytes that are not a YAML mapping, a
    duplicate key, or a member that is present and is not the shape the
    identity formula digests. An *absent* identity member is lifted as `None`
    rather than refused — the document still parsed, and §7.5 assigns an
    unsound receipt contract to outcome ``malformed``.

    What this does **not** check is the receipt *contract* — that every
    identity member is there, that the discriminant matches the member, that
    the keys are exactly `RECEIPT_KEYS[member]`, that each digest is an
    identity, that the corpus states are sorted and distinct. Those are §8.2's
    receipt outcome ``malformed``, and the validator that decides them extends
    this extraction without inheriting a refusal policy that would hide them.
    Recovering any of it by catching `EpochMalformed` would put the policy back
    in the layer this split exists to take it out of.
    """
    try:
        document = yaml.load(content.decode("utf-8"), Loader=registry._ManifestLoader)
        if type(document) is not dict:
            raise ValueError("a receipt is a mapping")
        states = document.get("corpus_states")
        return _ReceiptCarrier(
            packaging_identity,
            member,
            _lift_text(document, "kind"),
            _lift_text(document, "subject"),
            None if states is None else _corpus_states(states),
            _lift_text(document, "rule_identity"),
            _lift_text(document, "implementation_identity"),
            cast(Mapping[object, object], _deep_frozen(document)),
        )
    except Exception as caught:
        raise EpochMalformed(f"{packaging_identity}/{member}: {caught}") from caught


def _lift_text(document: dict[object, object], key: str) -> str | None:
    """One identity member as written, or `None` where it was not written.

    A YAML ``null`` and an omitted key are the same absence here: neither is
    the text the identity digests, and neither is a carrier failure.
    """
    value = document.get(key)
    return None if value is None else _require_text(value, key)


def _corpus_states(value: object) -> tuple[tuple[str, str], ...]:
    """The captured corpus-state pair for every covered corpus, as written.

    Sortedness and distinctness are contract, not structure: an unsorted or
    repeated sequence is still a sequence of pairs, and `receipt_identity`
    sorts what it digests. Only a shape with no pair in it refuses.
    """
    if type(value) is not list:
        raise ValueError("corpus_states is a list")
    states: list[tuple[str, str]] = []
    for entry in value:
        if type(entry) is not dict or any(key not in entry for key in _STATE_KEYS):
            raise ValueError(f"a corpus state carries {list(_STATE_KEYS)}")
        states.append(
            (
                _require_text(entry["corpus_id"], "corpus_id"),
                _require_text(entry["corpus_state"], "corpus_state"),
            )
        )
    return tuple(states)


def _require_text(value: object, location: str) -> str:
    """An identity-bearing member is a string. *Which* string — an identity, a
    known discriminant — is the validator's question; that it is text at all is
    this layer's, because the digest is over text."""
    if type(value) is not str:
        raise ValueError(f"{location} is text, not {type(value).__name__}")
    return value


def _deep_frozen(value: object) -> object:
    """A parsed document with nothing a reader can write through.

    An `Epoch` is immutable, and a mapping held behind a frozen field is not:
    without this, a caller could edit the coverage declaration of an opened
    epoch and hand the result to a bound read, which would then answer for a
    coverage no publication ever made. Mappings become read-only views and
    sequences become tuples; scalars are already immutable and pass through.
    """
    if type(value) is dict:
        mapping: dict[object, object] = value
        return MappingProxyType({key: _deep_frozen(member) for key, member in mapping.items()})
    if type(value) is list:
        members: list[object] = value
        return tuple(_deep_frozen(member) for member in members)
    return value


# --- the closed carrier, and opening one (§6.1, §6.2, §8.1) -------------------
#
# The lower of §8.2's two layers, at its full strength. The scan above answers
# "which receipts does this world retain"; what follows answers "are these the
# exact eleven documents this directory's name claims", which is a strictly
# stronger question and the one every read of an epoch must have answered
# first.
#
# The world lock is the caller's throughout: `_locked_open_epoch` never takes
# it and the lock is not reentrant, exactly as `rules._locked_resolve_rule_binding`
# is written. Publication holds it too, which is what makes an in-flight
# transaction invisible rather than briefly indistinguishable from damage.


def packaging_identity_of(members: Mapping[str, bytes]) -> str:
    """§6.2: `science.epoch.v1` over sorted `(member name, member content
    digest)` pairs, where a member content digest is the 64-character lowercase
    SHA-256 hex of that member's exact bytes.

    Taken over the complete member bytes and nothing else. It is computed
    *before* publication and then names the directory the members are created
    in, so the name is a claim about bytes that the bytes themselves settle —
    which is what makes recomputing it on open a real check rather than a
    restatement of the path.
    """
    return v1.digest(
        EPOCH_DOMAIN,
        [[name, rules.member_content_digest(content)] for name, content in sorted(members.items())],
    )


@dataclass(frozen=True)
class Epoch:
    """One opened epoch: its packaging identity and its parsed members.

    Immutable through and through — the mappings are read-only views and the
    parsed documents are deep-frozen — because an epoch is published bytes, and
    a reader holding one must not be able to produce an answer bound to a
    stamp no publication ever made.

    `members` is the exact bytes, kept because they are what the packaging
    identity digests and what a rebuild compares against. `documents` is those
    bytes parsed, keyed the same way. `receipts` is the four receipt carriers,
    handed on to the receipt validator whether or not they honour §7.5's
    contract (§8.2).
    """

    packaging_identity: str
    members: Mapping[str, bytes]
    documents: Mapping[str, Mapping[object, object]]
    receipts: Mapping[str, _ReceiptCarrier]
    coverage: tuple[tuple[str, str], ...]
    """§6.1's `coverage.yaml`, as sorted `(corpus_id, corpus_state)` pairs. The
    source of the bound stamp (§8.3)."""
    anchors: tuple[_Anchor, ...]
    world_anchor: _Anchor

    def __post_init__(self) -> None:
        object.__setattr__(self, "members", MappingProxyType(dict(self.members)))
        object.__setattr__(self, "documents", MappingProxyType(dict(self.documents)))
        object.__setattr__(self, "receipts", MappingProxyType(dict(self.receipts)))


def _locked_open_epoch(world_root: Path, packaging_identity: str) -> Epoch:
    """§8.1's private locked loader: one named epoch, fully validated.

    The caller holds the world lock and has already crossed the recovery
    barrier; this takes neither, because the lock is not reentrant and because
    a loader that completed recovery itself could not be reused by an act that
    had to complete it earlier.

    The order is §8.1's: the exact member set, then every closed document, then
    the recomputed packaging identity. Every failure is `EpochMalformed` with
    the underlying refusal as its cause — except an absence, which is
    `EpochUnknown`, because "there is no such epoch" and "there is one and it
    is broken" are answers a caller acts on differently.
    """
    if not _PACKAGING_IDENTITY.fullmatch(packaging_identity):
        raise EpochUnknown(f"{packaging_identity!r} is not a packaging identity, so no epoch is named by it")
    directory = Path(world_root) / "epochs" / packaging_identity
    if directory.is_symlink():
        raise EpochMalformed(f"{directory}: an epoch carrier is not a symbolic link")
    if not directory.exists():
        raise EpochUnknown(f"{directory}: this world retains no epoch under that packaging identity")
    if not directory.is_dir():
        raise EpochMalformed(f"{directory}: an epoch carrier is a directory")
    if _emptied(directory):
        raise EpochUnknown(f"{directory}: this world retains no epoch under that packaging identity")
    members = _carrier_members(directory)
    documents: dict[str, Mapping[object, object]] = {}
    receipts: dict[str, _ReceiptCarrier] = {}
    for member, content in members.items():
        if member in RECEIPT_KINDS:
            receipts[member] = _parse_receipt(packaging_identity, member, content)
            documents[member] = receipts[member].document
        else:
            documents[member] = _parse_member(packaging_identity, member, content)
    recomputed = packaging_identity_of(members)
    if recomputed != packaging_identity:
        raise EpochMalformed(
            f"{directory}: the members recompute the packaging identity {recomputed}, "
            "so this directory does not hold the epoch its name claims"
        )
    return Epoch(
        packaging_identity,
        members,
        documents,
        receipts,
        _covered_states(documents["coverage.yaml"]),
        _corpus_anchors(documents["anchors.yaml"]),
        _anchor(cast(Mapping[object, object], documents["anchors.yaml"]["world"])),
    )


def _locked_current_identity(world_root: Path) -> str | None:
    """The packaging identity `epochs/current` names, or `None` where this
    world has published nothing.

    The pointer is a regular file holding one line: the packaging identity and
    a newline. Nothing else is a pointer — not a symlink, not a longer
    document, not a bare identity without its terminator — because an
    operational convenience whose spelling was negotiable would be a second,
    weaker way to name an epoch. The caller holds the world lock.
    """
    path = Path(world_root) / "epochs" / CURRENT_POINTER
    if path.is_symlink():
        raise EpochMalformed(f"{path}: the current pointer is not a symbolic link")
    if not path.exists():
        return None
    if not path.is_file():
        raise EpochMalformed(f"{path}: the current pointer is a regular file")
    content = path.read_bytes()
    try:
        named = content.decode("utf-8")
    except UnicodeDecodeError as caught:
        raise EpochMalformed(f"{path}: the current pointer is not UTF-8 text") from caught
    if not named.endswith("\n") or not _PACKAGING_IDENTITY.fullmatch(named[:-1]):
        raise EpochMalformed(f"{path}: the current pointer is one line naming one packaging identity")
    return named[:-1]


def _current_pointer_bytes(packaging_identity: str) -> bytes:
    """The pointer's exact bytes. One line, one identity, one newline."""
    return f"{packaging_identity}\n".encode()


def _parse_member(packaging_identity: str, member: str, content: bytes) -> Mapping[object, object]:
    """One non-receipt member, read as the closed document §6.1 requires.

    The same duplicate-key, unknown-field and malformed-value discipline the
    registry uses, applied to each member's own shape. It stops at *shape*: it
    does not ask whether the address map is singular, whether a producers entry
    names a run the epoch also records, or whether a coreference balance is
    arithmetically reachable. Those are semantic questions, and two of these
    members have no receipt to re-derive them from — §8.1's member-digest and
    packaging-identity recompute is their integrity check, and inventing a
    further outcome for them here would be inventing an authority.
    """
    try:
        document = yaml.load(content.decode("utf-8"), Loader=registry._ManifestLoader)
        if type(document) is not dict:
            raise ValueError("an epoch member is a mapping")
        keys = MEMBER_KEYS[member]
        if tuple(sorted(document)) != keys:
            raise ValueError(f"the document has exactly {list(keys)}; got {sorted(document)}")
        _MEMBER_CHECKS[member](document)
        return cast(Mapping[object, object], _deep_frozen(document))
    except Exception as caught:
        raise EpochMalformed(f"{packaging_identity}/{member}: {caught}") from caught


def _entries(value: object, keys: tuple[str, ...], location: str) -> tuple[Mapping[str, object], ...]:
    """A member's list of closed entries, each with exactly `keys`."""
    if type(value) is not list:
        raise ValueError(f"{location} is a list, not {type(value).__name__}")
    members: list[object] = value
    return tuple(_closed_entry(entry, keys, location) for entry in members)


def _closed_entry(value: object, keys: tuple[str, ...], location: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise ValueError(f"an entry of {location} is a mapping, not {type(value).__name__}")
    entry: dict[object, object] = value
    if tuple(sorted(str(key) for key in entry)) != keys or any(type(key) is not str for key in entry):
        raise ValueError(f"an entry of {location} has exactly {list(keys)}; got {sorted(map(str, entry))}")
    return cast(Mapping[str, object], entry)


def _text_members(value: object, location: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{location} is a list, not {type(value).__name__}")
    members: list[object] = value
    return tuple(_require_text(member, f"a member of {location}") for member in members)


def _check_addresses(document: Mapping[object, object]) -> None:
    for entry in _entries(document["addresses"], ("address", "corpus_id", "uid"), "addresses"):
        for key in ("address", "corpus_id", "uid"):
            _require_text(entry[key], key)


def _check_producers(document: Mapping[object, object]) -> None:
    for entry in _entries(document["producers"], ("dataset", "runs"), "producers"):
        _require_text(entry["dataset"], "dataset")
        _text_members(entry["runs"], "runs")


def _check_targets(document: Mapping[object, object]) -> None:
    for entry in _entries(document["targets"], ("retractions", "target"), "targets"):
        _require_text(entry["target"], "target")
        _text_members(entry["retractions"], "retractions")


def _check_pairs(document: Mapping[object, object]) -> None:
    for entry in _entries(
        document["pairs"], ("balance", "distinct_key_count", "endpoints"), "pairs"
    ):
        endpoints = entry["endpoints"]
        if type(endpoints) is not list or len(endpoints) != 2:
            raise ValueError("a coreference pair names exactly two endpoints")
        _text_members(endpoints, "endpoints")
        for key in ("balance", "distinct_key_count"):
            if type(entry[key]) is not int:
                raise ValueError(f"{key} is an integer, not {type(entry[key]).__name__}")


def _check_snapshot(document: Mapping[object, object]) -> None:
    _text_members(document["coverage"], "coverage")
    _check_producers(document)


_ANCHOR_KEYS = ("genesis_digest", "head_digest", "subject")


def _check_anchors(document: Mapping[object, object]) -> None:
    subjects = [
        _anchor(entry).subject for entry in _entries(document["corpora"], _ANCHOR_KEYS, "corpora")
    ]
    if subjects != sorted(subjects):
        raise ValueError("the corpus anchors are not sorted by subject")
    if len(set(subjects)) != len(subjects):
        raise ValueError("one subject is anchored twice")
    _anchor(_closed_entry(document["world"], _ANCHOR_KEYS, "world"))


def _check_coverage(document: Mapping[object, object]) -> None:
    """§6.1's coverage declaration: sorted, distinct, and both members text.

    Every entry is validated by `_covered_pair` as a *statement* and its
    `corpus_id` is collected unconditionally, exactly as `_check_anchors`
    validates through `_anchor`. Writing the state check as a comprehension
    filter instead would make it validate and select at once: an entry whose
    `corpus_state` was the empty string is text, so it passes, and is falsy, so
    it would drop out of `covered` before the sortedness and distinctness
    checks ever saw its `corpus_id` — and §6.1 makes this member the source of
    the bound stamp, so an unsorted or repeating declaration reaching a
    consumer is not a cosmetic fault.
    """
    covered = [
        _covered_pair(entry)[0]
        for entry in _entries(document["coverage"], ("corpus_id", "corpus_state"), "coverage")
    ]
    if covered != sorted(covered):
        raise ValueError("the coverage declaration is not sorted by corpus_id")
    if len(set(covered)) != len(covered):
        raise ValueError("one corpus is covered twice")


_MEMBER_CHECKS: Mapping[str, Callable[[Mapping[object, object]], None]] = MappingProxyType(
    {
        "address-map.yaml": _check_addresses,
        "producers-map.yaml": _check_producers,
        "retraction-discovery-map.yaml": _check_targets,
        "coreference-map.yaml": _check_pairs,
        "producer-snapshot.yaml": _check_snapshot,
        "anchors.yaml": _check_anchors,
        "coverage.yaml": _check_coverage,
    }
)


def _anchor(entry: Mapping[str, object] | Mapping[object, object]) -> _Anchor:
    return _Anchor(
        _require_text(entry["subject"], "subject"),
        _require_text(entry["genesis_digest"], "genesis_digest"),
        _require_text(entry["head_digest"], "head_digest"),
    )


def _corpus_anchors(document: Mapping[object, object]) -> tuple[_Anchor, ...]:
    corpora: tuple[object, ...] = cast(tuple[object, ...], document["corpora"])
    return tuple(_anchor(cast(Mapping[object, object], entry)) for entry in corpora)


def _covered_pair(entry: Mapping[str, object] | Mapping[object, object]) -> tuple[str, str]:
    """One coverage entry as a `(corpus_id, corpus_state)` pair.

    Both members are validated here, so a caller that needs only one of them
    still gets both checked. That is the whole reason this exists rather than
    two inline lifts: a check written where its value is consumed becomes a
    check that only runs when that value is wanted.
    """
    return (
        _require_text(entry["corpus_id"], "corpus_id"),
        _require_text(entry["corpus_state"], "corpus_state"),
    )


def _covered_states(document: Mapping[object, object]) -> tuple[tuple[str, str], ...]:
    coverage: tuple[object, ...] = cast(tuple[object, ...], document["coverage"])
    return tuple(_covered_pair(cast(Mapping[object, object], entry)) for entry in coverage)


# --- coherent preflight and capture (§5.2, §5.3) ------------------------------
#
# The two halves of an epoch build that touch live state, and the frozen draft
# that separates them from everything pure. Preflight answers "may this build
# run, over exactly these corpora, with exactly these four rules" while holding
# the world lock. Capture then takes each covered corpus's operation lock in
# turn and, under that one exclusion, reads its chain head, its corpus-state
# identity, its stored nodes, and its corpus-state identity again.
#
# Publication is not here. What leaves is `_BuildDraft`, and the discipline it
# encodes is that nothing downstream can re-read a corpus: the draft carries no
# carrier path, no view and no handle, so a derivation that wanted to peek at
# live state would have to be handed one by its caller.

DERIVATION_KINDS: tuple[str, ...] = tuple(
    RECEIPT_KINDS[member] for member in EPOCH_MEMBERS if member in RECEIPT_KINDS
)
"""§5.2's four derivations, keyed as §7.5 keys their receipts, in §6.1's order.

Derived from the member inventory rather than written out again: a build input
that named three kinds, or a fifth, has not described an epoch, and the one
place that says which four there are is `RECEIPT_KINDS`.
"""

ENUMERATED_SOURCE_KINDS: tuple[str, ...] = (
    "coreference-attestation",
    "instrument-certification",
    "retraction",
    "run",
)
"""The stored kinds the four epoch derivations read a record *as*.

A `run` contributes its `produces` edges to the producer snapshot, a
`retraction` its target and resolution to the enumeration and the discovery
map, and the remaining two would contribute a certification and a coreference
attestation. Membership here is what makes a kind's governance a build's
business: every other stored kind contributes only its address and `uid`, which
the address map reads without any contract for the record's fields.

This is deliberately not a blocklist of the two deferred kinds. The refusal is
computed against `stored.SEMANTIC_DOMAINS`, so the day either kind gains its
charter and a governed stored-kind definition, the refusal stops firing without
an edit here — and a *new* enumerated kind that arrives ungoverned starts
refusing without one either.
"""

RETRACTION_OVERTURNED = "overturned"
RETRACTION_UPHELD = "upheld"
RETRACTION_RESOLUTIONS: tuple[str, ...] = (RETRACTION_OVERTURNED, RETRACTION_UPHELD)
"""The closed resolution vocabulary a capture attaches to a found retraction.

`derive.CapturedRetraction` takes the resolution as opaque non-empty text
because a pure derivation has no way to decide one; capture does, and closing
the vocabulary here is what stops two builds of one corpus from spelling the
same corpus-local judgement differently and minting two enumeration identities
for it. A retraction is `upheld` when nothing in its own corpus retracts it and
`overturned` when something standing does — exactly
`corpus.standing_in_local_view`'s judgement, which is corpus-local and
non-authoritative by design.
"""


@dataclass(frozen=True)
class _Anchor:
    """One `(subject, genesis_digest, head_digest)` triple, as §6.1 stores it.

    The subject is a covered `corpus_id` for a corpus anchor and the world id
    for the build-start world anchor. The two digests are exactly what the
    injected callback returned: this layer never learns what an entry is.
    """

    subject: str
    genesis_digest: str
    head_digest: str


@dataclass(frozen=True)
class _Preflight:
    """What §5.2 retains for the rest of one build.

    `carriers` is the pinned `corpus_id -> carrier root` mapping, in sorted id
    order, and it is pinned rather than re-derived: a build that resolved a
    carrier twice could capture one corpus and anchor another.
    """

    coverage: tuple[str, ...]
    carriers: Mapping[str, Path]
    world_anchor: _Anchor
    held: Mapping[str, rules._HeldRule]

    def __post_init__(self) -> None:
        object.__setattr__(self, "carriers", MappingProxyType(dict(self.carriers)))
        object.__setattr__(self, "held", MappingProxyType(dict(self.held)))


@dataclass(frozen=True)
class _BuildDraft:
    """Everything one build carries out of its holds, and nothing else.

    Captured values, the per-corpus anchors, the declared coverage and its
    captured states, the build-start world head, and the four exact rules as
    resolved — their bytes and the entry point loaded from those bytes.

    There is no carrier path here, and that absence is the point. §5.3's "only
    captured values leave the hold" is not a convention a publisher has to
    remember if the draft simply has nowhere to put a root: derivation and
    publication cannot re-read a corpus because they are not told where one is.
    """

    coverage: tuple[str, ...]
    capture: derive.Capture
    anchors: tuple[_Anchor, ...]
    world_anchor: _Anchor
    held: Mapping[str, rules._HeldRule]

    def __post_init__(self) -> None:
        object.__setattr__(self, "held", MappingProxyType(dict(self.held)))

    @property
    def corpus_states(self) -> tuple[tuple[str, str], ...]:
        """The one sorted `(corpus_id, corpus_state)` sequence every receipt of
        this epoch carries. One value, not four: §7.5 requires the four
        receipts to agree, and there is nowhere here for a per-kind state."""
        return self.capture.corpus_states

    @property
    def bindings(self) -> Mapping[str, tuple[str, str]]:
        """Each derivation's exact `(rule_identity, implementation_identity)`,
        ready for `derive.derivation_receipts`."""
        return MappingProxyType(
            {
                kind: (held.binding.rule_identity, held.binding.implementation_identity)
                for kind, held in self.held.items()
            }
        )

    def run(self, kind: str) -> object:
        """Run one resolved derivation over the one captured projection.

        Every kind is handed the same `rule_input()` value, which is what makes
        "enumerated once, fed to all four" a property of the draft rather than
        of whoever remembers to reuse the argument.
        """
        return self.held[kind].invoke(self.capture.rule_input())


def _declared_coverage(coverage: frozenset[str]) -> tuple[str, ...]:
    """The declared covered ids, sorted and non-empty. Never the registry's
    live set.

    §5.2's closing sentence is a rule about what a build may *substitute*, and
    the only way to keep it is to have no path that reads liveness as a
    default. The caller declares; this checks the shape and orders it.

    **An empty coverage is refused, and that is a decision rather than a
    consequence.** Nothing in §5 or §6 makes an empty capture unrepresentable:
    the maps would be empty, the receipts would carry an empty state list, and
    the anchors would still name the world. What such an epoch cannot do is
    answer. §8.3 makes every address outside the observed coverage `Unknown`,
    and §8.4 makes every edge `indeterminate` wherever the epoch's coverage
    does not contain the live-id set — so an epoch declaring nothing answers
    nothing in any world holding a live corpus, and pointing `current` at one
    would disable every read the epoch exists to serve without a single
    refusal being raised. A caller that arrived here with an empty set filtered
    its coverage down to nothing, and is told so at the point the mistake was
    made rather than at the point a reader notices.
    """
    if not isinstance(coverage, (frozenset, set)):
        raise TypeError("a build's coverage is a set of stable corpus ids")
    if not coverage:
        raise ValueError("a build covers at least one corpus; an epoch declaring no coverage answers nothing")
    return tuple(sorted(registry._require_lower_hex(corpus_id, 32, "corpus_id") for corpus_id in coverage))


def _declared_bindings(bindings: Mapping[str, rules.RuleBinding]) -> Mapping[str, rules.RuleBinding]:
    """Exactly one exact pair per receipt kind. Three is not an epoch."""
    if set(bindings) != set(DERIVATION_KINDS):
        raise ValueError(
            f"a build names one exact rule binding per receipt kind {sorted(DERIVATION_KINDS)}; "
            f"got {sorted(bindings)}"
        )
    for kind, binding in bindings.items():
        if type(binding) is not rules.RuleBinding:
            raise TypeError(f"the {kind!r} binding must be an exact RuleBinding")
    return MappingProxyType(dict(bindings))


def _locked_resolve_coverage(
    world: registry.World,
    coverage: frozenset[str],
) -> Mapping[str, Path]:
    """Resolve already-validated corpus ids while the caller holds the world barrier."""
    covered = tuple(sorted(coverage))
    config = world.config
    world._state.registry = registry._scan_registry(config.world_root)
    view = world._state.registry

    def resolve() -> dict[str, Path]:
        carriers: dict[str, Path] = {}
        for corpus_id in covered:
            if not any(record.corpus_id == corpus_id for record in view.admissions):
                raise CoverageUnknown(
                    f"{corpus_id}: declared coverage names a corpus this world has not admitted"
                )
            if any(record.corpus_id == corpus_id for record in view.statuses):
                raise CoverageNotLive(
                    f"{corpus_id}: declared coverage names a corpus with terminal status"
                )
            roots = registry._carrier_roots(config, corpus_id)
            if len(roots) != 1:
                detail = ",".join(sorted(str(root) for root in roots)) or "none"
                raise CoverageUnresolvable(
                    f"{corpus_id}: exactly one configured carrier root is required; carriers={detail}"
                )
            carriers[corpus_id] = roots[0]
        return carriers

    return MappingProxyType(resolve())


def resolve_coverage(
    world: registry.World,
    coverage: frozenset[str],
) -> Mapping[str, Path]:
    """Resolve coverage under the world barrier, releasing it before return."""
    _declared_coverage(coverage)
    with registry._locked_barrier(world):
        return _locked_resolve_coverage(world, coverage)


def _preflight(
    world: registry.World,
    *,
    coverage: frozenset[str],
    bindings: Mapping[str, rules.RuleBinding],
) -> _Preflight:
    """§5.2, in the order §5.2 writes it, under `_WorldState.lock` throughout.

    The chain read comes first and completes recovery, so every world file
    inspected below is inspected after recovery rather than beside it. The
    registry rescan follows; then, for each covered id in sorted order,
    admission, liveness and carrier uniqueness — in that order, so that a
    world with two faults reports the one that is decided first rather than the
    one that happens to be cheapest to find. The four exact bindings resolve
    last, with their fixtures run, because a build whose coverage is
    inadmissible has no business executing rule content at all.

    The world lock is plain and blocking. Holding it across a registry rescan
    and four fixture runs is short and serializes against registry appends and
    rule removal; §5.1's no-queueing rule is about corpus capture and does not
    reach here.
    """
    covered = _declared_coverage(coverage)
    declared = _declared_bindings(bindings)
    config = world.config
    with world._state.lock:
        genesis_digest, head_digest = world._chain_head(config.world_root)
        carriers = _locked_resolve_coverage(world, coverage)
        held = rules._locked_resolve_rule_bindings(config.world_root, declared)
    return _Preflight(covered, carriers, _Anchor(config.world_id, genesis_digest, head_digest), held)


def _capture(world: registry.World, preflight: _Preflight) -> _BuildDraft:
    """§5.3: sorted, serial, and one hold per corpus.

    The whole of a corpus's coherent capture — chain head, state, enumeration,
    state again — happens inside `capture()`, which never waits: a build that
    queued behind a corpus operation could park the writer queue behind itself.
    Serial rather than concurrent, because holding several corpora's operation
    locks at once is a lock order this layer would then have to own, and the
    coherence guarantee is per corpus and gains nothing from overlap.

    The drift comparison is inside the hold so the refusal is attributable to
    it, and it discards by simply not returning: no partial draft exists to be
    salvaged, and there is no retry. Silently trying again would convert an
    operator editing a corpus underneath a running build into a build that
    quietly succeeded on the second look.
    """
    captured: list[derive.CapturedCorpus] = []
    anchors: list[_Anchor] = []
    for corpus_id in preflight.coverage:
        carrier = preflight.carriers[corpus_id]
        state = _root_state_for(carrier, world._corpus_executor_factory)
        with state.lock.capture():
            genesis_digest, head_digest = world._chain_head(carrier)
            before = registry.corpus_state_identity(carrier)
            records = _captured_records(carrier)
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole capture is discarded and nothing is published"
                )
        captured.append(derive.CapturedCorpus(corpus_id, before, records))
        anchors.append(_Anchor(corpus_id, genesis_digest, head_digest))
    return _BuildDraft(
        preflight.coverage,
        derive.Capture(tuple(captured)),
        tuple(anchors),
        preflight.world_anchor,
        preflight.held,
    )


def _capture_build_inputs(
    world: registry.World,
    *,
    coverage: frozenset[str],
    bindings: Mapping[str, rules.RuleBinding],
) -> _BuildDraft:
    """Preflight, then coherent capture: everything a build reads from live
    state, in one act with one frozen result."""
    return _capture(world, _preflight(world, coverage=coverage, bindings=bindings))


def _captured_records(corpus_root: Path) -> tuple[derive.CapturedRecord, ...]:
    """One corpus's stored nodes, enumerated **once**, as captured records.

    The enumeration is `ReadView.iter_stored`, the same unvalidated read
    `registry.corpus_state_identity` takes. That is deliberate: the two state
    computations and this pass have to agree about what the corpus holds, and a
    validating read would refuse records the captured state identity counted,
    leaving the two halves of one coherent capture describing different
    corpora. Record validity is the read side's question (`ReadView.get`), not
    the capture's.

    Governance is this pass's question, and it is asked before any record is
    built. `EnumeratedKindUngoverned` refuses the whole capture: a record whose
    kind one of the four maps enumerates but which has no governed stored-kind
    definition can be neither derived from nor silently omitted.
    """
    view = ReadView.opened_at(corpus_root)
    nodes = tuple(view.iter_stored())
    for node in nodes:
        if node.kind in ENUMERATED_SOURCE_KINDS and node.kind not in stored.SEMANTIC_DOMAINS:
            raise EnumeratedKindUngoverned(
                f"{corpus_root}: {node.id}: kind {node.kind!r} is enumerated by an epoch derivation "
                "but has no governed stored-kind definition; the capture is discarded rather than "
                "derived from or silently narrowed"
            )
    facets = {node.id: _validated_retraction_facet(node) for node in nodes if node.kind == "retraction"}
    standing = _standing_retractions(view, facets)
    return tuple(
        derive.CapturedRecord(
            address=node.id,
            uid=node.uid,
            kind=node.kind,
            deprecated_ids=tuple(node.deprecated_ids),
            produces=tuple(
                relation.target
                for relation in node.relations
                if relation.predicate == stored.PRODUCES and relation.source == node.id
            ),
            retraction=(
                None
                if node.id not in facets
                else derive.CapturedRetraction(
                    _retraction_target(facets[node.id]),
                    RETRACTION_UPHELD if standing.get(node.id, True) else RETRACTION_OVERTURNED,
                )
            ),
        )
        for node in nodes
    )


def _retraction_target(facet: Mapping[str, object]) -> str:
    """The target identity §7.4's discovery map groups on.

    A node-arm retraction names its target by the ref the author wrote, and
    that ref is what travels: turning it into a live address here would make
    the map's keys depend on a resolution the epoch already publishes an
    address map for. A route-arm retraction names an embedded route rather than
    a record, and its route identity keeps it disjoint from a node-arm
    retraction of the same dataset — two genuinely different claims that a
    shared dataset key would silently merge.
    """
    target = cast(Mapping[str, str], facet["target"])
    return target["ref"] if target["arm"] == "node" else target["route_identity"]


def _standing_retractions(view: ReadView, facets: Mapping[str, Mapping[str, object]]) -> Mapping[str, bool]:
    """Which of this corpus's retractions still stand, in one fold.

    `corpus.standing_in_local_view`'s **graph** half, computed for every
    retraction at once instead of one at a time, because the capture pass may
    enumerate the corpus only once. Only node-arm retractions subtract standing
    — a route-arm target names an embedded route, not a record — and the target
    ref is resolved through the corpus index here, exactly as the corpus-local
    judgement resolves it, so a retraction naming another by a deprecated id
    still overturns it. `_acyclic_postorder` is the corpus's own traversal,
    reused rather than reimplemented: a retraction cycle is
    `RetractionCycleMalformed` here for the same reason it is there.

    **What this deliberately does not do, and the divergence it creates.**
    `standing_in_local_view` first puts every retraction through
    `CorpusWriter._resolve_retraction_target`, which enforces target
    eligibility, exact resolution and a matching target content identity, and
    raises `RetractionTargetIneligible` / `RetractionTargetUnresolvable` when
    any of it fails. This does none of that. So on a corpus whose retraction
    target has drifted, the corpus *declines to judge* while capture records
    `upheld` or `overturned` — and that resolution reaches the retraction
    enumeration projection and its published identity.

    That is a choice, not an oversight. Those two refusals are `WriteRefused`
    subclasses: they are the admission gate's verdict on an *act*, not a
    finding about stored content, and re-running them here would make an epoch
    build a second, later admission gate over records the corpus already holds
    — one raw-imported retraction anywhere in any covered corpus would then
    make the whole world unbuildable. §5.3 closes capture's refusal surface at
    `EnumeratedKindUngoverned` and `CaptureDrift` and names no target-validity
    requirement, and the resolution a capture publishes is a claim about the
    retraction graph ("nothing standing in this corpus retracts this
    retraction"), never a claim that the retraction's own target still
    resolves. A reader checks that through the epoch's address map and the
    retraction-discovery map, which is what they are for. Pinned by
    `test_world_build.py::TestSerialCapture`'s drifted-target arm.
    """
    targets: dict[str, list[str]] = {}
    for address, facet in facets.items():
        target = cast(Mapping[str, str], facet["target"])
        if target["arm"] != "node":
            continue
        resolved = view.resolve(target["ref"])
        if resolved is not None:
            targets.setdefault(resolved, []).append(address)
    graph = {target: tuple(sorted(retractions)) for target, retractions in targets.items()}
    standing: dict[str, bool] = {}
    for target in _acyclic_postorder(graph):
        standing[target] = not any(standing[retraction] for retraction in graph.get(target, ()))
    return standing


def _locked_recheck_rule_bindings(world_root: Path, draft: _BuildDraft) -> Mapping[str, rules._HeldRule]:
    """§5.4's pre-publication recheck: the same four exact pairs, still held.

    The world lock — the same lock removal takes — is the caller's, already
    held, and this must not take it: it is a plain `threading.Lock`, so a
    second acquisition inside the same thread is a deadlock rather than a
    style question.

    That the caller holds it *across* the recheck and the transaction is the
    point, not an implementation detail. `rules.remove_rule_binding` computes
    its sever report from the retained epochs **and** submits its delete plan
    under one hold of this lock. A publication that released between the
    recheck and the commit could be straddled entirely by one removal: the
    removal would see no epoch to report, and the epoch would land carrying
    receipts naming a pair this world had already stopped holding. One
    acquisition closes that, and `test_world_epoch.py`'s
    `test_publication_takes_the_world_lock_once_and_rechecks_inside_it` pins
    it — a release and reacquire would reopen the race without deadlocking, so
    only a counted assertion catches it.

    It reads no corpus. Every value publication needs from live corpus state
    was captured under the corpus's own hold, and a second look here would be
    a freshness claim the staleness contract explicitly does not make: covered
    corpora may move between capture and publication, and receipts name the
    exact captured states rather than the present ones.
    """
    declared = {kind: held.binding for kind, held in draft.held.items()}
    return rules._locked_resolve_rule_bindings(world_root, declared)


# --- publication (§5.4, §6.3) -------------------------------------------------
#
# Everything above is either pure or read-only. What follows is the one act
# that writes beneath ``epochs/``, and it writes exactly once: every byte is
# derived before the world lock is reacquired, and what happens inside the lock
# is a recheck, an inspection, and one plan.
#
# There is no staging writer, no sequence file and no second commit protocol.
# Crash atomicity and durability are the engine's properties of that single
# transaction, relied on and never re-implemented.


@dataclass(frozen=True)
class DerivationBindings:
    """The four exact rule bindings one build names (§5.2).

    Named fields rather than a mapping keyed by receipt kind, because a build
    input naming three derivations, or five, is not a build input at all —
    and a shape with exactly four slots says so at construction instead of at
    the first missing lookup. `by_kind` performs the join to §7.5's kind
    vocabulary, which is the rules store's business nowhere else: the store is
    keyed by identity and knows nothing of kinds.
    """

    producer: rules.RuleBinding
    retraction: rules.RuleBinding
    certification: rules.RuleBinding
    coreference: rules.RuleBinding

    def __post_init__(self) -> None:
        for kind, binding in self.by_kind().items():
            if type(binding) is not rules.RuleBinding:
                raise TypeError(f"the {kind!r} binding must be an exact RuleBinding")

    def by_kind(self) -> Mapping[str, rules.RuleBinding]:
        """The same four, keyed as `DERIVATION_KINDS` keys them."""
        return MappingProxyType(
            {
                "producer": self.producer,
                "retraction-enumeration": self.retraction,
                "certification-enumeration": self.certification,
                "coreference-reduction": self.coreference,
            }
        )


def build_epoch(
    world: registry.World,
    *,
    coverage: frozenset[str],
    bindings: DerivationBindings,
) -> Epoch:
    """Build and publish one epoch over exactly this declared coverage.

    Three phases, and the order between them is the whole of §5.4. Capture
    reads live state under each corpus's own hold and produces a frozen draft.
    Derivation is pure and produces the complete member bytes and, from those
    bytes, the packaging identity — **before** any lock is reacquired, so
    nothing that could refuse or take time happens inside the critical section.
    Publication then takes the world lock once and, under it, crosses the
    recovery barrier, rechecks the four bindings, inspects any carrier already
    holding this name, and submits at most one plan.

    The answer is the epoch read back from what was published, not the values
    that were about to be: an `Epoch` a caller holds always means bytes that
    are on disk under the name it carries.
    """
    draft = _capture_build_inputs(world, coverage=coverage, bindings=bindings.by_kind())
    members = _derived_members(draft)
    packaging_identity = packaging_identity_of(members)
    # The barrier first, exactly as preflight takes it first: every world file
    # inspected below — the same-name carrier, the pointer — is then inspected
    # after recovery rather than beside it.
    with registry._locked_barrier(world) as world_root:
        _locked_recheck_rule_bindings(world_root, draft)
        plan = _locked_publication_plan(world_root, packaging_identity, members)
        if plan:
            world._executor_factory(world_root).execute(plan)
        return _locked_open_epoch(world_root, packaging_identity)


def _derived_members(draft: _BuildDraft) -> Mapping[str, bytes]:
    """§6.1's eleven members, as the exact bytes this build would publish.

    Pure: the draft is the only input, and there is no path from here to a
    corpus root, a registry or a pointer. The four rules run once each over
    the one captured projection; the two maps that are not receipt subjects
    fold over the same capture.
    """
    snapshot = derive.producer_snapshot(draft.run("producer"))
    enumeration = derive.retraction_enumeration(draft.run("retraction-enumeration"))
    inventory = derive.certification_inventory(draft.run("certification-enumeration"))
    coreference = derive.coreference_map(draft.run("coreference-reduction"))
    receipts = derive.derivation_receipts(
        snapshot=snapshot,
        enumeration=enumeration,
        inventory=inventory,
        coreference=coreference,
        corpus_states=draft.corpus_states,
        bindings=draft.bindings,
    )
    members: dict[str, bytes] = {
        "address-map.yaml": _document_bytes(
            derive.address_map_projection(derive.address_map(draft.capture))
        ),
        "producers-map.yaml": _document_bytes(derive.producers_map_projection(snapshot.producers)),
        "retraction-discovery-map.yaml": _document_bytes(
            derive.retraction_discovery_map_projection(derive.retraction_discovery_map(draft.capture))
        ),
        "coreference-map.yaml": _document_bytes(coreference.projection()),
        "producer-snapshot.yaml": _document_bytes(snapshot.projection()),
        "anchors.yaml": _document_bytes(_anchors_projection(draft)),
        "coverage.yaml": _document_bytes(_coverage_projection(draft)),
    }
    for receipt in receipts:
        members[receipt.member] = _document_bytes(_receipt_projection(receipt))
    if set(members) != set(EPOCH_MEMBERS):
        raise EpochMalformed(
            f"a build derived {sorted(members)}, which is not the closed epoch layout {sorted(EPOCH_MEMBERS)}"
        )
    return MappingProxyType({member: members[member] for member in EPOCH_MEMBERS})


def _document_bytes(projection: Mapping[str, object]) -> bytes:
    """One member's bytes: the canonical dump of its projection.

    The same deterministic encoding the registry and the rules store use, so
    an epoch member and a registry record are one reading of "a closed YAML
    document" rather than two.
    """
    return yaml.safe_dump(dict(projection), sort_keys=True, allow_unicode=True).encode("utf-8")


def _anchors_projection(draft: _BuildDraft) -> dict[str, object]:
    """§6.1's anchors: one triple per covered corpus, sorted by subject, and
    the build-start world-chain head beside them."""
    return {
        "corpora": [
            {
                "subject": anchor.subject,
                "genesis_digest": anchor.genesis_digest,
                "head_digest": anchor.head_digest,
            }
            for anchor in sorted(draft.anchors, key=lambda anchor: anchor.subject)
        ],
        "world": {
            "subject": draft.world_anchor.subject,
            "genesis_digest": draft.world_anchor.genesis_digest,
            "head_digest": draft.world_anchor.head_digest,
        },
    }


def _coverage_projection(draft: _BuildDraft) -> dict[str, object]:
    """§6.1's coverage: the declared ids and each one's captured state.

    Read from the captured states rather than from the declaration, because
    the two cannot differ — `derive.Capture` derives its coverage from what it
    captured — and taking it from one place means no build can publish a
    declaration its receipts disagree with.
    """
    return {
        "coverage": [
            {"corpus_id": corpus_id, "corpus_state": corpus_state}
            for corpus_id, corpus_state in draft.corpus_states
        ]
    }


def _receipt_projection(receipt: derive.DerivationReceipt) -> dict[str, object]:
    """One receipt member's document: §7.5's five identity members, and the
    subject projection the two projection-bearing kinds carry inside it."""
    projection: dict[str, object] = {
        "kind": receipt.kind,
        "subject": receipt.subject_identity,
        "corpus_states": [
            {"corpus_id": corpus_id, "corpus_state": corpus_state}
            for corpus_id, corpus_state in receipt.corpus_states
        ],
        "rule_identity": receipt.rule_identity,
        "implementation_identity": receipt.implementation_identity,
    }
    if receipt.enumeration is not None:
        projection["enumeration"] = dict(receipt.enumeration)
    if receipt.inventory is not None:
        projection["inventory"] = dict(receipt.inventory)
    if set(projection) != RECEIPT_KEYS[receipt.member]:
        raise EpochMalformed(
            f"{receipt.member}: a receipt document carries exactly {sorted(RECEIPT_KEYS[receipt.member])}"
        )
    return projection


def _locked_log_head_records(
    world_root: Path, packaging_identity: str, members: Mapping[str, bytes]
) -> list[CreateOp]:
    """The build's registry-record half: one log-head record per covered corpus.

    Log-verification design §3.3. The epoch's `anchors.yaml` member and these
    records carry the same triples; the records exist because an anchor a
    consumer can find without opening an epoch is what makes the registry a
    carrier of the observer set. Origin is `build`, naming the packaging
    identity of the epoch this build is publishing — the fact that
    distinguishes them from the anchor act's records, which name an actor.

    **The triples are read back out of the member, not carried in beside it.**
    The member is the bytes the epoch will publish, so deriving the records
    from it is what makes "the same triples" a fact rather than an intention:
    a build cannot record an anchor its own `anchors.yaml` does not state.
    `_corpus_anchors` returns them already sorted by subject, because the
    member is written sorted.

    The world anchor is deliberately absent: a `world` subject is not in the
    record's union at all (§3.1/L11), and only an exported artifact leaving the
    world root can anchor the world chain — the member carries it under a
    separate key, which this reads past.

    §3.1's idempotency rule applies here exactly as it does to the act, so a
    republication of the same epoch over unmoved heads adds nothing to the
    plan.
    """
    document = _parse_member(packaging_identity, "anchors.yaml", members["anchors.yaml"])
    plan: list[CreateOp] = []
    for anchor in _corpus_anchors(document):
        record = LogHeadRecord(
            CorpusSubject(anchor.subject),
            anchor.genesis_digest,
            anchor.head_digest,
            BuildOrigin(packaging_identity),
        )
        member = _log_head_member(world_root, record)
        if member is not None:
            plan.append(member)
    return plan


def _locked_publication_plan(
    world_root: Path, packaging_identity: str, members: Mapping[str, bytes]
) -> WritePlan:
    """The one transaction, or nothing at all. The caller holds the world lock.

    First publication is eleven creates, a create for the pointer, and one
    log-head record per covered corpus. Later publication is the same, with a
    replace for the pointer. An exact rebuild — the content-addressed epoch
    already stands and is byte-identical — creates nothing, because no member
    is ever overwritten, a pointer already naming it leaves nothing to do, and
    the records the first publication wrote are byte-identical too.

    The records join *this* plan rather than a second one because a published
    epoch whose registry half failed separately would be an anchor a consumer
    could find in one carrier and not the other.

    A same-name carrier is validated in full before any of that. It cannot be
    byte-different and still pass: its members would recompute a different
    packaging identity and `_locked_open_epoch` would refuse. The byte
    comparison below is therefore not a second chance to fail but the
    statement of what "already exists" was allowed to mean.

    A directory this name's epoch was *deleted* from is not a same-name
    carrier: §9 leaves it empty and calls it nonsemantic, so republishing the
    same bytes creates the eleven members back into it rather than reading a
    carrier that holds none of them.
    """
    directory = world_root / "epochs" / packaging_identity
    operations: list[CreateOp | ReplaceOp] = []
    if directory.is_symlink() or (directory.exists() and not (directory.is_dir() and _emptied(directory))):
        retained = _locked_open_epoch(world_root, packaging_identity)
        if dict(retained.members) != dict(members):
            raise EpochMalformed(f"{directory}: a retained epoch of this name holds different bytes")
    else:
        operations.extend(
            CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in EPOCH_MEMBERS
        )
    pointer = _locked_current_identity(world_root)
    content = _current_pointer_bytes(packaging_identity)
    if pointer is None:
        operations.append(CreateOp(f"epochs/{CURRENT_POINTER}", content))
    elif pointer != packaging_identity:
        operations.append(
            ReplaceOp(
                f"epochs/{CURRENT_POINTER}",
                content,
                rules.member_content_digest(_current_pointer_bytes(pointer)),
            )
        )
    operations.extend(_locked_log_head_records(world_root, packaging_identity, members))
    return operations


# --- whole-epoch garbage collection (§9) --------------------------------------


SNAPSHOT_SUBJECT = "producer-snapshot"
"""§9's fifth identity, named as a subject beside `DERIVATION_KINDS`' four.

The producer snapshot is the one subject an epoch carries whose identity is not
a receipt's own. It is labelled here rather than by the member holding it,
because the report is about identities and a `.yaml` filename in it would be
the carrier layer leaking into a consumer's vocabulary."""


@dataclass(frozen=True)
class SeveredIdentity:
    """One identity a deleted epoch carried, and whether anything still does.

    `subject` names what the identity is the identity *of* — one of
    `DERIVATION_KINDS`' four receipt kinds, or `SNAPSHOT_SUBJECT` for the
    producer snapshot — so the five entries of a report read in §7.5's own
    vocabulary rather than in a second one invented for reporting. It is the
    kind the *member* declares (`RECEIPT_KINDS`), not the discriminant the
    document happens to carry: where those two disagree the document is a
    contract fault for the receipt validator to find, and the report would be
    filing it under a heading nobody asked about.

    `retained_elsewhere` is the whole point of the report: an identity another
    retained epoch of this world still carries survives the deletion, and one
    no other epoch carries does not. It is a statement about *this* world and
    stops there, exactly as `rules.RuleRemovalReport` does — another consulted
    world may hold the same publication, and this act cannot see it.
    """

    subject: str
    identity: str
    retained_elsewhere: bool


@dataclass(frozen=True)
class EpochDeletionReport:
    """What one `delete_epoch` removed, and what it severed.

    §9 asks for the actor, the producer-snapshot identity and the four receipt
    identities the deleted epoch carried, each flagged with whether any other
    retained epoch still carries it.

    `snapshot` is optional and `receipts` may hold fewer than four, for one
    reason: an identity is read from the receipt document that names it, and a
    receipt that omitted one of §7.5's five identity members has no identity at
    all (`_ReceiptCarrier.identity`). Such a receipt is *not* reported as
    severed, and the reason is `rules._severed_receipts`' reason: §7.5 already
    puts an unsound receipt contract at outcome ``malformed``, decided before
    resolvability is ever asked, so no deletion can move it. Reporting an
    identity for it would mean inventing one nobody published.
    """

    actor: str
    packaging_identity: str
    snapshot: SeveredIdentity | None
    receipts: tuple[SeveredIdentity, ...]

    @property
    def severed(self) -> tuple[str, ...]:
        """The identities this deletion left nothing in this world carrying,
        sorted and distinct."""
        entries = (*(() if self.snapshot is None else (self.snapshot,)), *self.receipts)
        return tuple(sorted({entry.identity for entry in entries if not entry.retained_elsewhere}))


def delete_epoch(world: registry.World, packaging_identity: str, *, actor: str) -> EpochDeletionReport:
    """Delete one whole retained epoch, and report what it severed (§9).

    Explicit consumer policy. Nothing in this package calls it, no schedule
    triggers it, and there is no act that deletes one member of an epoch: an
    epoch is published whole and it is removed whole.

    Under one acquisition of the world lock, and in this order: cross the
    recovery barrier, read and validate `current`, refuse `EpochCurrent` for
    the epoch the pointer names, then open the target. `current` is checked
    before the target is opened because "you may not delete this one" is an
    answer about the world's state rather than about the target's bytes, and a
    consumer who asked to delete the current epoch is owed that answer even if
    the carrier underneath it is also damaged.

    Every *other* retained epoch is then opened with the same private locked
    loader, because the report's question — is this identity still carried
    here? — is a question about what those epochs hold, and §8.1's carrier rule
    is that an epoch this world cannot read refuses the act that reads it. A
    damaged epoch elsewhere therefore refuses the whole deletion with
    `EpochMalformed`, exactly as a damaged carrier refuses a rule removal: a
    sever report computed over a scan that quietly skipped one would be the
    silent unresolvability §4.3 refuses to produce.

    One transaction, holding a `DeleteOp` for each of the eleven members. The
    emptied directory stays where it is; §9 calls it nonsemantic and `_emptied`
    is what makes that true rather than merely stated. There is no tombstone:
    a repeated call raises `EpochUnknown`, and slice 2 claims no exact retry
    after commit.
    """
    actor = registry._require_actor(actor)
    with registry._locked_barrier(world) as world_root:
        current = _locked_current_identity(world_root)
        if current == packaging_identity:
            raise EpochCurrent(
                f"{world_root / 'epochs' / CURRENT_POINTER} names {packaging_identity}, "
                "so deleting it would leave this world pointing at nothing"
            )
        target = _locked_open_epoch(world_root, packaging_identity)
        elsewhere: set[str] = set()
        for retained in _retained_identities_locked(world_root):
            if retained == packaging_identity:
                continue
            elsewhere |= _carried_identities(_locked_open_epoch(world_root, retained))
        report = _deletion_report(actor, target, elsewhere)
        world._executor_factory(world_root).execute(
            [
                DeleteOp(f"epochs/{packaging_identity}/{member}", rules.member_content_digest(content))
                for member, content in target.members.items()
            ]
        )
    return report


def _retained_identities_locked(world_root: Path) -> tuple[str, ...]:
    """Every packaging identity this world retains, sorted and distinct.

    Read off the one epoch scanner rather than by walking ``epochs/`` a second
    time. Every carrier holds four receipts, so a carrier the scan reached is a
    carrier this answers with, and a directory the scan refused refuses here
    too — which is the enumeration's own share of §8.1's carrier rule.
    """
    return tuple(sorted({carrier.packaging_identity for carrier in _retained_receipt_bindings_locked(world_root)}))


def _carried_identities(published: Epoch) -> frozenset[str]:
    """The identities one opened epoch carries: its four receipts and the
    producer snapshot its producer receipt names as its subject.

    The snapshot identity is read from the producer receipt rather than
    recomputed from ``producer-snapshot.yaml``, because §7.5 *defines* that
    receipt's subject to be the published snapshot's identity, and because a
    report has to compare like with like: the four receipt identities have no
    source but the receipt documents, so taking the fifth from anywhere else
    would compare one epoch's claim against another's rederivation and call the
    difference a sever.
    """
    carried = {receipt.identity for receipt in published.receipts.values()}
    carried.add(published.receipts["producer-receipt.yaml"].subject_identity)
    return frozenset(identity for identity in carried if identity is not None)


def _deletion_report(actor: str, target: Epoch, elsewhere: AbstractSet[str]) -> EpochDeletionReport:
    """§9's report over the target's own carried identities, in member order."""
    producer = target.receipts["producer-receipt.yaml"].subject_identity
    snapshot = None if producer is None else SeveredIdentity(SNAPSHOT_SUBJECT, producer, producer in elsewhere)
    receipts: list[SeveredIdentity] = []
    for member in EPOCH_MEMBERS:
        if member not in RECEIPT_KINDS:
            continue
        identity = target.receipts[member].identity
        if identity is not None:
            receipts.append(SeveredIdentity(RECEIPT_KINDS[member], identity, identity in elsewhere))
    return EpochDeletionReport(actor, target.packaging_identity, snapshot, tuple(receipts))
