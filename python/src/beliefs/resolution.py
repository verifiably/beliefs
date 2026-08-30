"""Referent resolution: the five outcomes, the snapshot, and the receipt.

**Binding a referent is not the same as resolving one** (§7.2). A claim may
legitimately name an ontology term in a corpus that does not hold that ontology's
bytes, so "is this term in its vocabulary?" has more answers than yes and no.

D §5's `unknown` could not carry the decision, because it is a **disjunction**:
the term is outside the bound vocabulary, *or* nobody consulted the binding's
namespace. Refusing on it would report *"not in the vocabulary"* on the evidence
that no one looked. §7.2 splits it, and the resulting five outcomes fall into two
groups that must never be mixed:

    resolved membership results   member        not-member
    check not performed           not-consulted not-present  not-available

`not-member` is a **finding**; `not-consulted` is the absence of one. Only
`not-member` refuses at decode — the other four are well-formed states, and
refusing on them would make typing a claim require holding every ontology it
mentions.

*"A failure to look is not a finding of absence"* runs through five banked
documents; the accepting rows here are its **dual** — a failure to look is not a
finding of presence either, which is why an unperformed check is recorded as
unperformed rather than omitted.

**`not-present` is unreachable in this cut, and is defined anyway.** It means the
bound dataset has a world address the consulted index records while its corpus is
absent — which needs the world index and holding machinery that cut 1 does not
build (D3's deferred arm). Defining four of five would be implementing a
different closed set than the one §7.2 rules, and the gap would be invisible;
defining all five leaves exactly one outcome that nothing here constructs, which
is a fact a test can state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import final

from beliefs.contract.domain import VocabularyBinding
from beliefs.errors import ResolutionError
from beliefs.identifiers import canonical, not_a_canonical_identifier
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "BindingCheckReceipt",
    "ReferentPosition",
    "ResolutionSnapshot",
    "TermOutcome",
    "build_snapshot",
]

SNAPSHOT_DOMAIN = "science.snapshot.v1"
RECEIPT_DOMAIN = "science.receipt.v1"

_MINT = object()


class TermOutcome(Enum):
    """§7.2's five outcomes. A closed set, and the tags are the wire spelling."""

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
    """Where in a claim a referent sits — a slot index, or a qualifier dimension.

    Both kinds are referent positions and both are resolved (§6.4: a restriction
    is sorted exactly as an argument is), so the receipt has to name them in one
    vocabulary without conflating them.
    """

    kind: str
    """``argument`` or ``restriction``."""

    key: str
    """The slot index rendered as text, or the dimension's term identifier."""

    def label(self) -> str:
        return f"{self.kind}:{self.key}"

    @classmethod
    def argument(cls, slot: int) -> ReferentPosition:
        return cls(kind="argument", key=str(slot))

    @classmethod
    def restriction(cls, dimension: str) -> ReferentPosition:
        return cls(kind="restriction", key=dimension)


@dataclass(frozen=True)
class _BoundVocabulary:
    """What the snapshot holds for one binding: its terms, or the fact that it could not be read."""

    readable: bool
    terms: frozenset[str]

    def projection(self) -> dict[str, object]:
        if not self.readable:
            return {"readable": False}
        return {"readable": True, "terms": sorted(self.terms)}


@sealed
@final
@dataclass(frozen=True, init=False)
class ResolutionSnapshot:
    """The identified, content-derived state of vocabulary availability a decode resolved against.

    **It is a parameter, and that is the whole point.** §6.3 first wrote
    `decodeClaim : WireClaim × ProfileSpec → Claim + Refused`, which is not a
    function: the decision depends on what vocabularies are readable, so two
    holders could decode identical bytes differently through ambient state and
    nothing could say which was right. Making availability an argument is what
    restores §3.4's well-definedness — same three inputs, same outcome, anywhere.

    So there is deliberately **no default and no ambient fallback**. A decoder
    that could construct its own snapshot from the environment would reintroduce
    exactly the defect the parameter exists to remove, and would do it invisibly.
    """

    bindings: Mapping[VocabularyBinding, _BoundVocabulary]
    identity: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionError(
            "ResolutionSnapshot is built, never authored — use build_snapshot(readable=..., unreadable=...). "
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
        `VocabularyBinding`'s: it enforces D §5's sum at construction and is
        sealed, so no ordinary route produces a collision.
        """
        entries = [{"binding": binding.projection(), **state.projection()} for binding, state in self.bindings.items()]
        entries.sort(key=lambda entry: v1.encode(entry["binding"]))
        return {"bindings": entries}

    def resolve(self, binding: VocabularyBinding, term: str) -> TermOutcome:
        """Resolve one term through one binding.

        The three refusing-to-look outcomes are distinguished **here**, where the
        evidence is, rather than downstream where only their consequences are
        visible.
        """
        state = self.bindings.get(binding)
        if state is None:
            # Nothing was looked at: this binding's namespace was never consulted.
            return TermOutcome.NOT_CONSULTED
        if not state.readable:
            # The dataset is identified and its bytes are not held here. This is
            # M4's *local* analogue of `not-available` and is in cut 1; D3's
            # world-level arm — an indexed address whose corpus is absent — is
            # not, and the two are deliberately not allowed to stand in for each
            # other.
            return TermOutcome.NOT_AVAILABLE
        return TermOutcome.MEMBER if canonical(term) in state.terms else TermOutcome.NOT_MEMBER


def _require_binding(binding: object) -> None:
    """A snapshot's keys are `VocabularyBinding`s, and structural is not enough.

    The keys are matched against `profile.sorts[...].vocabulary` by **value**, so
    a lookalike that compares unequal resolves to `not-consulted` — a snapshot
    that was told about a vocabulary reporting that nobody looked at it. The
    binding's own construction is what rules out the ill-formed inhabitants
    (D §5's sum); this rules out values that never went through it.
    """
    if not isinstance(binding, VocabularyBinding):
        raise ResolutionError(
            f"a snapshot is keyed by VocabularyBinding, found {type(binding).__name__}. Bindings are compared "
            "by value against the sort declarations in force, and a lookalike matches none of them — so the "
            "snapshot would report `not-consulted` for a vocabulary it was handed."
        )


def _require_terms(terms: object, binding: VocabularyBinding) -> Iterable[object]:
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
            f"{binding.projection()}: a vocabulary is a collection of terms, and {terms!r} is a single string. "
            "Iterating it yields its characters, so the term this was meant to declare present would resolve "
            "`not-member` against a vocabulary that was written to contain it."
        )
    if not isinstance(terms, Iterable):
        raise ResolutionError(f"{binding.projection()}: expected a collection of terms, found {terms!r}")
    return terms


def _require_term(term: object, binding: VocabularyBinding) -> str:
    """A vocabulary's members are term identifiers — the same predicate `Referent` applies.

    The two have to agree, and this is the sharper direction: a `Referent` cannot
    carry a non-identifier term, so a snapshot holding one holds a member no claim
    can ever name. `resolve` would answer `not-member` — the single **refusing**
    outcome, positive evidence that a vocabulary was read and lacks the term —
    about a vocabulary that was told it has it. §7.2 exists to keep an absence of
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
            f"{binding.projection()}: {problem}. A `Referent` cannot carry it, so no claim can name this "
            "member, and a claim naming the identifier it was meant to be would be refused as `not-member` "
            "against a vocabulary that was read and was written to contain it."
        )
    return term  # type: ignore[return-value]


def build_snapshot(
    *,
    readable: Mapping[VocabularyBinding, Iterable[str]] | None = None,
    unreadable: Iterable[VocabularyBinding] = (),
) -> ResolutionSnapshot:
    """Build a snapshot from what is readable and what is identified but not held.

    A binding absent from **both** arguments is `not-consulted`, and that is the
    honest default: a snapshot says what was looked at, and silence about a
    binding is silence, not a claim that its vocabulary is empty. An empty
    `readable` entry is a different fact — the vocabulary was read and contains
    nothing — and the two produce different outcomes.
    """
    table: dict[VocabularyBinding, _BoundVocabulary] = {}
    for binding, terms in (readable or {}).items():
        _require_binding(binding)
        table[binding] = _BoundVocabulary(
            readable=True,
            terms=frozenset(_require_term(term, binding) for term in _require_terms(terms, binding)),
        )
    for binding in unreadable:
        _require_binding(binding)
        if binding in table:
            raise ResolutionError(
                f"binding {binding.projection()} is given as both readable and unreadable. "
                "One binding has one state; a snapshot that carried both would let a caller pick."
            )
        table[binding] = _BoundVocabulary(readable=False, terms=frozenset())

    snapshot = ResolutionSnapshot._built(_MINT, bindings=MappingProxyType(dict(table)), identity="")
    object.__setattr__(snapshot, "identity", v1.digest(SNAPSHOT_DOMAIN, snapshot.projection()))
    return snapshot


@sealed
@final
@dataclass(frozen=True, init=False)
class BindingCheckReceipt:
    """Which of the five outcomes each referent position got, and under which snapshot.

    **Not an input to claim identity** (§7.2). A corpus that happens to hold an
    ontology must not mint different identities from one that does not, or
    `I_claim` would depend on what bytes are lying around — the exact dependency
    §6.5's identifier discipline exists to prevent. The arrow runs the other way:
    the receipt names the claim, and the claim knows nothing about the receipt.

    **It is a diagnostic.** §7.2 took option 1 explicitly: no independent
    addressing, no discovery path, no succession, and no declared belief
    consequence. Option 2 — promoting binding checks to addressed records — is a
    kind with an eligibility analysis, and is ρO1. Nothing here persists.

    ``snapshot_identity`` is what makes the receipt readable apart from the
    snapshot that produced it, and it is required by M4. It is also exactly what
    §6.3's scoped dependency rule asks for: this artifact's validity is
    conditional on one snapshot, and it can travel apart from that snapshot, so
    it records the dependency rather than leaving a later reader to guess.
    """

    claim_identity: str
    """The claim these outcomes were taken for.

    **Beyond M4's letter**, which asks only for the outcomes and the snapshot
    identity. Without it a receipt is a set of slot labels with no way to tell
    which claim's slots they were — and a diagnostic that cannot be attached to
    its subject is not much of one. It also pins the sorts: the claim identity
    fixes the operator, and §7.3 forbids redefining an operator's `arg_sorts`
    under its own identifier, so the positions cannot be reinterpreted. That
    argument has one hole, and it is already open — a parallel `genesis` in the
    same namespace is compared against nothing (§8.3, ρC1).
    """

    snapshot_identity: str
    outcomes: Mapping[str, TermOutcome]
    """Position label → outcome. Exactly one per referent position (M4)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionError(
            "BindingCheckReceipt is emitted by decode_claim, never authored. An authored receipt would "
            "report a check that nobody performed, which is the one thing §7.2 exists to prevent."
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
