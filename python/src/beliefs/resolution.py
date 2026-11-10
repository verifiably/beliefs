"""Referent resolution: the five outcomes, the snapshot, and the receipt.

**Binding a referent is not the same as resolving one**. A claim may
legitimately name an ontology term in a corpus that does not hold that ontology's
bytes, so "is this term in its vocabulary?" has more answers than yes and no.

A single `unknown` could not carry the decision, because it is a **disjunction**:
the term is outside the bound vocabulary, *or* nobody consulted the binding's
namespace. Refusing on it would report *"not in the vocabulary"* on the evidence
that no one looked. The outcome is therefore split, and the resulting five outcomes fall into two
groups that must never be mixed:

    resolved membership results   member        not-member
    check not performed           not-consulted not-present  not-available

`not-member` is a **finding**; `not-consulted` is the absence of one. Only
`not-member` refuses at decode — the other four are well-formed states, and
refusing on them would make typing a claim require holding every ontology it
mentions.

*"A failure to look is not a finding of absence"* — and its **dual** holds here:
a failure to look is not a finding of presence either, which is why an unperformed check is recorded as
unperformed rather than omitted.

`not-present` is produced by `build_snapshot(not_present=...)`: the world read
view's `locate` found the binding's dataset in a covered corpus, and that corpus
is absent from this world. The snapshot records that corpus so this state remains
distinct from both an unheld local dataset and a binding nobody consulted.

**Each of the six binding arms resolves in one way** (`ResolutionSnapshot.resolve`):

    release      the held vocabulary at that release, by the binding itself
    dataset      the members of the held dataset, by the binding itself
    selection    the dataset arm over its `selected` dataset
    run-output   the dataset arm over its produced `dataset`
    scheme       `member` exactly when the term matches the sort's identifier
                 class; always performed, whatever the snapshot holds
    world-kind   the held record ids of that kind, or `not-consulted` when the
                 snapshot carries no inventory of the kind
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, final

from beliefs.contract.domain import (
    DatasetBinding,
    ReleaseBinding,
    RunOutputBinding,
    SchemeBinding,
    SelectionBinding,
    SortBinding,
    WorldKindBinding,
)
from beliefs.errors import ProfileError, ResolutionError
from beliefs.identifiers import canonical, not_a_canonical_identifier
from beliefs.identity import v1
from beliefs.sealed import sealed

if TYPE_CHECKING:
    from beliefs.profile import CompiledSort

__all__ = [
    "BindingCheckReceipt",
    "ReferentPosition",
    "ResolutionSnapshot",
    "TermOutcome",
    "build_snapshot",
]

SNAPSHOT_DOMAIN = "science.snapshot.v2"
"""v2: every binding projects with its arm's `kind` tag, so every non-empty
snapshot's projection changed shape; the empty snapshot moves with the domain."""
RECEIPT_DOMAIN = "science.receipt.v2"
"""v2: the position vocabulary is roles by name (`role:<name>`, `role:<name>[<i>]`),
not argument slots; a receipt's identity is taken over its position labels."""

_MINT = object()
_HEX64 = "[0-9a-f]{64}"
_KIND_NAME = re.compile("[a-z][a-z0-9-]*")


class TermOutcome(Enum):
    """The five outcomes. A closed set, and the tags are the wire spelling."""

    MEMBER = "member"
    NOT_MEMBER = "not-member"
    NOT_CONSULTED = "not-consulted"
    NOT_PRESENT = "not-present"
    NOT_AVAILABLE = "not-available"

    @property
    def refuses(self) -> bool:
        """Whether `decodeClaim` refuses on this outcome.

        Exactly one of the five does. Written as a property of the outcome rather
        than as a condition at the decode site so that the rule has **one**
        statement: a second `if outcome is ...` somewhere else is how the two
        groups get mixed back together.
        """
        return self is TermOutcome.NOT_MEMBER

    @property
    def performed(self) -> bool:
        """Whether the membership check was actually performed.

        The group boundary, and the thing an unchecked binding must never be able
        to impersonate. `member` and `not-member` are findings; the other three
        record that nothing was looked at.
        """
        return self in (TermOutcome.MEMBER, TermOutcome.NOT_MEMBER)


@dataclass(frozen=True)
class ReferentPosition:
    """Where in a claim a referent sits — a role (or one member of a `many`
    role), or a qualifier dimension.

    Both kinds are referent positions and both are resolved (a restriction
    is sorted exactly as a role's referent is), so the receipt has to name them in one
    vocabulary without conflating them.
    """

    kind: str
    """``role``, ``restriction``, ``estimand`` or ``node``."""

    key: str
    """The role name (with ``[<i>]`` for a member), the dimension's term
    identifier, an estimand part, or a node index rendered as text."""

    def label(self) -> str:
        return f"{self.kind}:{self.key}"

    @classmethod
    def role(cls, name: str) -> ReferentPosition:
        """`role:cause` — a `one` role's referent (the reserved `within-model` included)."""
        return cls(kind="role", key=name)

    @classmethod
    def member(cls, name: str, index: int) -> ReferentPosition:
        """`role:parties[0]` — the ``index``-th member, from 0, of a `many` role in
        canonical member-key order: the order the claim holds them in, so the
        label names the same referent wherever the claim was written."""
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ResolutionError(f"a member position is a non-negative integer, found {index!r}")
        return cls(kind="role", key=f"{name}[{index}]")

    @classmethod
    def restriction(cls, dimension: str) -> ReferentPosition:
        return cls(kind="restriction", key=dimension)

    @classmethod
    def estimand(cls, part: str) -> ReferentPosition:
        """`estimand:contrast.baseline`, `estimand:measure.quantity`,
        `estimand:control.conditioning[3]` — the estimand's positions, in the
        receipt's one vocabulary."""
        return cls(kind="estimand", key=part)

    @classmethod
    def node(cls, index: int) -> ReferentPosition:
        """A composite's node, by position in its sorted node set."""
        return cls(kind="node", key=str(index))


@dataclass(frozen=True)
class _BoundVocabulary:
    """One binding's terms, or which of the two ways it could not be read."""

    state: Literal["readable", "not-available", "not-present"]
    terms: frozenset[str]
    absent: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        if self.state == "readable":
            return {"state": "readable", "terms": sorted(self.terms), "absent": []}
        return {"state": self.state, "terms": [], "absent": list(self.absent)}


@sealed
@final
@dataclass(frozen=True, init=False)
class ResolutionSnapshot:
    """The identified, content-derived state of vocabulary availability a decode resolved against.

    **It is a parameter, and that is the whole point.** A decode taking only
    `WireClaim × ProfileSpec → Claim + Refused` is not a
    function: the decision depends on what vocabularies are readable, so two
    holders could decode identical bytes differently through ambient state and
    nothing could say which was right. Making availability an argument is what
    restores well-definedness — same three inputs, same outcome, anywhere.

    So there is deliberately **no default and no ambient fallback**. A decoder
    that could construct its own snapshot from the environment would reintroduce
    exactly the defect the parameter exists to remove, and would do it invisibly.
    """

    bindings: Mapping[SortBinding, _BoundVocabulary]
    """The vocabularies looked at, keyed by a `release` or `dataset` binding: the
    two arms whose membership is a read vocabulary. `selection` and `run-output`
    resolve through the `dataset` key of their dataset."""

    kinds: Mapping[str, frozenset[str]]
    """World kind → the record ids of that kind the corpus holds: the inventory a
    `world-kind` binding resolves against. A kind absent here was not consulted."""

    identity: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionError(
            "ResolutionSnapshot is built, never authored — use build_snapshot(readable=..., unreadable=..., "
            "not_present=..., kinds=...). "
            "Its identity is derived from its contents, and a field-wise constructor would let a snapshot "
            "carry an identity describing a different availability state than its own."
        )

    @classmethod
    def _built(cls, token: object, **fields: object) -> ResolutionSnapshot:
        if token is not _MINT:
            raise ResolutionError("ResolutionSnapshot._built is build_snapshot's own route and takes its mint token")
        snapshot = object.__new__(cls)
        for name, value in fields.items():
            object.__setattr__(snapshot, name, value)
        return snapshot

    def projection(self) -> dict[str, object]:
        """The canonical projection ``identity`` is taken over.

        A **list** of records rather than an object keyed by binding, because a
        binding is a structured value and `science.identity.v1` requires string
        keys. The list is sorted by the binding's own canonical encoding, so the
        order a caller happened to supply cannot reach the identity — and that is
        worth exactly the **injectivity** of the key. `sort` is stable, so two
        distinct bindings encoding alike would be left in insertion order and one
        snapshot would take two identities. That injectivity is
        `SortBinding`'s: a sealed six-arm sum whose projection carries the arm's tag, so no ordinary
        route produces a collision.

        The world-kind inventory is a separate member, ``kinds``, keyed by kind
        name, and present only when the snapshot carries one. A snapshot without
        an inventory therefore projects exactly as it did before inventories
        existed, and one with an inventory — even an empty one for a kind, which
        says the kind was read and holds nothing — never projects like one
        without.
        """
        entries = [{"binding": binding.projection(), **state.projection()} for binding, state in self.bindings.items()]
        entries.sort(key=lambda entry: v1.encode(entry["binding"]))
        projection: dict[str, object] = {"bindings": entries}
        if self.kinds:
            projection["kinds"] = {kind: sorted(ids) for kind, ids in self.kinds.items()}
        return projection

    def resolve(self, sort: CompiledSort, term: str) -> TermOutcome:
        """Resolve one term of one sort, by the arm its binding is.

        The three refusing-to-look outcomes are distinguished **here**, where the
        evidence is, rather than downstream where only their consequences are
        visible. `scheme` never reaches them: its membership is the identifier
        class, a computable predicate, so the check is always performed.
        `selection` and `run-output` are the `dataset` arm plus provenance, so
        they resolve through the dataset arm over the dataset they name, exactly.
        """
        binding = sort.binding
        if isinstance(binding, SchemeBinding):
            if sort.identifier_class is None:
                # Unreachable through compile, which requires a class on every arm
                # but world-kind; a profile defect, not a sixth outcome.
                raise ProfileError(f"sort {sort.term!r} is bound to a scheme and declares no identifier class")
            return TermOutcome.MEMBER if sort.identifier_class.matches(term) else TermOutcome.NOT_MEMBER
        if isinstance(binding, WorldKindBinding):
            held = self.kinds.get(binding.world_kind)
            if held is None:
                return TermOutcome.NOT_CONSULTED
            return TermOutcome.MEMBER if canonical(term) in held else TermOutcome.NOT_MEMBER
        if isinstance(binding, SelectionBinding):
            return self._vocabulary(DatasetBinding(dataset=binding.selected), term)
        if isinstance(binding, RunOutputBinding):
            return self._vocabulary(DatasetBinding(dataset=binding.dataset), term)
        return self._vocabulary(binding, term)

    def _vocabulary(self, binding: SortBinding, term: str) -> TermOutcome:
        state = self.bindings.get(binding)
        if state is None:
            # Nothing was looked at: this binding's namespace was never consulted.
            return TermOutcome.NOT_CONSULTED
        if state.state == "not-present":
            # The world records the binding's dataset in a covered corpus that
            # has no carrier here — the world-level arm.
            return TermOutcome.NOT_PRESENT
        if state.state == "not-available":
            # The dataset is identified and its bytes are not held here. This is
            # the local `not-available`, distinct from an absent world corpus.
            return TermOutcome.NOT_AVAILABLE
        return TermOutcome.MEMBER if canonical(term) in state.terms else TermOutcome.NOT_MEMBER


def _require_binding(binding: object) -> None:
    """A snapshot's keys are `SortBinding`s, and structural is not enough.

    The keys are matched against `profile.sorts[...].binding` by **value**, so
    a lookalike that compares unequal resolves to `not-consulted` — a snapshot
    that was told about a vocabulary reporting that nobody looked at it. The
    binding's own construction is what rules out the ill-formed inhabitants
    (the one-arm sum); this rules out values that never went through it.

    The same defect arrives through a genuine arm that `resolve` never looks up:
    only a `release` or `dataset` binding names a vocabulary that is read. A
    `scheme` is checked by its identifier class, `selection` and `run-output` by
    the `dataset` key of the dataset they name, and `world-kind` by the `kinds`
    inventory, so a vocabulary keyed by any of those would be reported
    `not-consulted` — or never consulted at all — and is refused instead.
    """
    if not isinstance(binding, SortBinding):
        raise ResolutionError(
            f"a snapshot is keyed by SortBinding, found {type(binding).__name__}. Bindings are compared "
            "by value against the sort declarations in force, and a lookalike matches none of them — so the "
            "snapshot would report `not-consulted` for a vocabulary it was handed."
        )
    if not isinstance(binding, ReleaseBinding | DatasetBinding):
        route = _NOT_A_VOCABULARY[binding.kind]
        raise ResolutionError(
            f"a snapshot's vocabularies are keyed by a release or dataset binding; {binding.projection()} "
            f"{route}, so a vocabulary under it would never be read."
        )


_NOT_A_VOCABULARY: Mapping[str, str] = MappingProxyType(
    {
        "scheme": "is resolved by its sort's identifier class",
        "selection": "is resolved through the dataset binding of its `selected` dataset",
        "run-output": "is resolved through the dataset binding of its produced `dataset`",
        "world-kind": "is resolved through the snapshot's `kinds` inventory",
    }
)


def _require_terms(terms: object, where: str) -> Iterable[object]:
    """A vocabulary is a **collection** of terms, and a string is not one of those.

    `str` satisfies `Iterable[str]`, so `{binding: "EX:gene"}` type-checks and
    builds a vocabulary of six characters — none of which is the term the caller
    named, so the term they were declaring present resolves `not-member`. The wire
    decoder already refuses a bare string where it wants a sequence of terms, for
    exactly this reason; a vocabulary needs the same guard, because *iterable of
    strings* is a shape a string wrongly satisfies in this language.
    """
    if isinstance(terms, str | bytes):
        raise ResolutionError(
            f"{where}: a vocabulary is a collection of terms, and {terms!r} is a single string. "
            "Iterating it yields its characters, so the term this was meant to declare present would resolve "
            "`not-member` against a vocabulary that was written to contain it."
        )
    if not isinstance(terms, Iterable):
        raise ResolutionError(f"{where}: expected a collection of terms, found {terms!r}")
    return terms


def _require_term(term: object, where: str) -> str:
    """A vocabulary's members are term identifiers — the same predicate `Referent` applies.

    The two have to agree, and this is the sharper direction: a `Referent` cannot
    carry a non-identifier term, so a snapshot holding one holds a member no claim
    can ever name. `resolve` would answer `not-member` — the single **refusing**
    outcome, positive evidence that a vocabulary was read and lacks the term —
    about a vocabulary that was told it has it. The five outcomes exist to keep an absence of
    evidence from being reported as evidence of absence; this is the same
    confusion arriving from the other side, and it refuses a well-formed claim.

    Canonicity is the same fault with a smaller gap: `resolve` decides membership
    by string equality while every digest here works on the NFC form, so a member
    stored non-canonically is `not-member` for the claim that names its canonical
    spelling — two identifiers to this function and one to `I_claim`.
    """
    problem = not_a_canonical_identifier(term)
    if problem is not None:
        raise ResolutionError(
            f"{where}: {problem}. A `Referent` cannot carry it, so no claim can name this "
            "member, and a claim naming the identifier it was meant to be would be refused as `not-member` "
            "against a vocabulary that was read and was written to contain it."
        )
    return term  # type: ignore[return-value]


def _require_kind(kind: object) -> str:
    if not isinstance(kind, str) or not _KIND_NAME.fullmatch(kind):
        raise ResolutionError(f"kinds is keyed by world kind name, found {kind!r}")
    return kind


def _require_record_id(record: object, kind: str) -> str:
    """A held record id in the kernel's record-id grammar for its kind: the
    identifier class of every sort bound to the kind, so an id outside it is a
    member no claim can name — `_require_term`'s defect, arriving by inventory."""
    _require_term(record, f"kind {kind!r}")
    assert isinstance(record, str)
    if not re.fullmatch(f"{re.escape(kind)}:{_HEX64}", record):
        raise ResolutionError(
            f"kind {kind!r}: {record!r} is not a {kind} record id, `{kind}:` followed by 64 lowercase hex characters"
        )
    return record


def build_snapshot(
    *,
    readable: Mapping[SortBinding, Iterable[str]] | None = None,
    unreadable: Iterable[SortBinding] = (),
    not_present: Mapping[SortBinding, str] | None = None,
    kinds: Mapping[str, Iterable[str]] | None = None,
) -> ResolutionSnapshot:
    """Build a snapshot from what is readable and what is identified but not held.

    A binding absent from all three arguments is `not-consulted`, and that is the
    honest default: a snapshot says what was looked at, and silence about a
    binding is silence, not a claim that its vocabulary is empty. An empty
    `readable` entry is a different fact — the vocabulary was read and contains
    nothing — and the two produce different outcomes.

    ``kinds`` is the world-kind inventory, by the same rule: a kind it names was
    read, and its record ids are the members of every sort bound to that kind (an
    empty entry holds none); a kind it omits is `not-consulted`.
    """
    table: dict[SortBinding, _BoundVocabulary] = {}

    def _place(binding: SortBinding, entry: _BoundVocabulary) -> None:
        _require_binding(binding)
        if binding in table:
            raise ResolutionError(
                f"binding {binding.projection()} is given in more than one availability state "
                f"({table[binding].state} and {entry.state}). One binding has one state; a snapshot that "
                "carried two would let a caller pick."
            )
        table[binding] = entry

    for binding, terms in (readable or {}).items():
        _require_binding(binding)
        _place(
            binding,
            _BoundVocabulary(
                state="readable",
                terms=frozenset(
                    _require_term(term, str(binding.projection()))
                    for term in _require_terms(terms, str(binding.projection()))
                ),
                absent=(),
            ),
        )
    for binding in unreadable:
        _require_binding(binding)
        _place(binding, _BoundVocabulary(state="not-available", terms=frozenset(), absent=()))
    for binding, corpus_id in (not_present or {}).items():
        _require_binding(binding)
        if type(corpus_id) is not str or not corpus_id:
            raise ResolutionError(f"{binding.projection()}: a not-present binding names the absent corpus")
        _place(binding, _BoundVocabulary(state="not-present", terms=frozenset(), absent=(corpus_id,)))

    inventory: dict[str, frozenset[str]] = {}
    if kinds is not None:
        if not isinstance(kinds, Mapping):
            raise ResolutionError(f"kinds is a mapping from world kind to held record ids, found {kinds!r}")
        for kind, ids in kinds.items():
            name = _require_kind(kind)
            inventory[name] = frozenset(
                _require_record_id(record, name) for record in _require_terms(ids, f"kind {name!r}")
            )

    snapshot = ResolutionSnapshot._built(
        _MINT, bindings=MappingProxyType(dict(table)), kinds=MappingProxyType(inventory), identity=""
    )
    object.__setattr__(snapshot, "identity", v1.digest(SNAPSHOT_DOMAIN, snapshot.projection()))
    return snapshot


@sealed
@final
@dataclass(frozen=True, init=False)
class BindingCheckReceipt:
    """Which of the five outcomes each referent position got, and under which snapshot.

    **Not an input to claim identity**. A corpus that happens to hold an
    ontology must not mint different identities from one that does not, or
    `I_claim` would depend on what bytes are lying around — the exact dependency
    the identifier discipline exists to prevent. The arrow runs the other way:
    the receipt names the claim, and the claim knows nothing about the receipt.

    **It is a diagnostic.** It has no independent addressing, no discovery path,
    no succession, and no declared belief consequence. Promoting binding checks
    to addressed records would be a kind with an eligibility analysis, and is
    not done. Nothing here persists.

    ``snapshot_identity`` is what makes the receipt readable apart from the
    snapshot that produced it, and it is required. It is also exactly what
    a scoped dependency asks for: this artifact's validity is
    conditional on one snapshot, and it can travel apart from that snapshot, so
    it records the dependency rather than leaving a later reader to guess.
    """

    claim_identity: str
    """The claim these outcomes were taken for.

    The receipt carries this in addition to the outcomes and the snapshot
    identity. Without it a receipt is a set of position labels with no way to
    tell which claim's roles they were — and a diagnostic that cannot be attached
    to its subject is not much of one. It also pins the sorts: the claim identity
    carries every referent's sort beside its role name, so a position label names
    one referent of one sort and cannot be reinterpreted.
    """

    snapshot_identity: str
    outcomes: Mapping[str, TermOutcome]
    """Position label → outcome. Exactly one per referent position."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionError(
            "BindingCheckReceipt is emitted by decode_claim, never authored. An authored receipt would "
            "report a check that nobody performed, which is the one thing the five outcomes exist to prevent."
        )

    @classmethod
    def _emitted(cls, token: object, **fields: object) -> BindingCheckReceipt:
        if token is not _MINT:
            raise ResolutionError("BindingCheckReceipt._emitted is decode_claim's own route and takes its mint token")
        receipt = object.__new__(cls)
        for name, value in fields.items():
            object.__setattr__(receipt, name, value)
        return receipt

    @property
    def performed(self) -> bool:
        """Whether every position's check was actually performed."""
        return all(outcome.performed for outcome in self.outcomes.values())

    def projection(self) -> dict[str, object]:
        return {
            "claim": self.claim_identity,
            "snapshot": self.snapshot_identity,
            "outcomes": {label: outcome.value for label, outcome in self.outcomes.items()},
        }

    def identity(self) -> str:
        return v1.digest(RECEIPT_DOMAIN, self.projection())


def _emit_receipt(
    claim_identity: str, snapshot: ResolutionSnapshot, outcomes: Mapping[str, TermOutcome]
) -> BindingCheckReceipt:
    return BindingCheckReceipt._emitted(
        _MINT,
        claim_identity=claim_identity,
        snapshot_identity=snapshot.identity,
        outcomes=MappingProxyType(dict(outcomes)),
    )
