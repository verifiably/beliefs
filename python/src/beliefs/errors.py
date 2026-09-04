"""The error hierarchy.

Every refusal in this package raises one of these. They are deliberately
fine-grained: several banked oracles turn on refusals staying *distinct* rather
than collapsing into one another (D3's five-way non-collapsing test is the
sharpest case), and a test that can only assert "something was raised" cannot
tell a good refusal from a bad one.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:  # pragma: no cover - the report type is the verification module's
    from beliefs.world.verify import LogReport


class ScienceError(Exception):
    """Base for every error this package raises."""


class ManifestMalformed(ScienceError):
    """A corpus manifest is not its exact closed shape."""


class ManifestAlreadyPresent(ScienceError):
    """Fresh manifest adoption found an existing manifest path."""


class ManifestMissing(ScienceError):
    """A corpus has no manifest file."""


class CorpusStateMalformed(ScienceError):
    """A corpus state value is malformed."""


class WorldIdMismatch(ScienceError):
    """A world identifier disagrees with its expected identity."""


class StoreIdMismatch(ScienceError):
    """A store act's supplied root carries a genesis naming another store.

    The store analog of `WorldIdMismatch`, raised by the anchor and export
    acts' subject binding: a store resolves through no registry, so the
    caller-supplied root is bound to the subject by its genesis alone, and a
    genesis naming a different `store_id` — or no store genesis at all — is
    refused before any head is accepted or any registry mutation planned.
    """


class WorldUninitialized(ScienceError):
    """A world operation needs initialization that has not occurred."""


class ProvenanceMismatch(ScienceError):
    """Recorded provenance does not match its expected source."""


class ForkParentUnknown(ScienceError):
    """A fork names no known parent corpus."""


class CorpusIdKnown(ScienceError):
    """A corpus identifier is already known where freshness is required."""


class StatusTargetUnknown(ScienceError):
    """A status operation names no known target."""


class StatusTerminal(ScienceError):
    """A status transition starts from a terminal status."""


class RegistryMalformed(ScienceError):
    """A world registry is malformed."""


class RuleCollision(ScienceError):
    """A content-addressed rule path exists with different bytes."""


class RuleNonconformant(ScienceError):
    """An implementation fails the normative fixtures at install."""


class RuleNotHeld(ScienceError):
    """An exact rule binding is absent at preflight or the pre-publication
    recheck. Every failed identity recomputation, every unreadable stored
    member and every fixture the stored implementation no longer satisfies
    reaches the caller as this one refusal: the pair is not held, and a
    partial hold is not a weaker kind of hold."""


class RuleBindingUnknown(ScienceError):
    """Explicit removal names no held exact pair. Removal is the inverse of the
    install act, not a sweep: it unholds the one
    ``(rule_identity, implementation_identity)`` it was handed, and a pair this
    store does not hold is a refusal rather than a no-op, because a silent
    success would tell its caller that evidence naming that pair had been
    severed here when nothing was."""


class EpochMalformed(ScienceError):
    """An epoch carrier fails its closed layout or packaging identity. It is a
    *carrier* failure: a receipt document that reaches the receipt validator
    and violates the receipt contract is validation outcome ``malformed``, not
    this."""


class EpochUnknown(ScienceError):
    """An explicitly named epoch does not exist. It is the honest answer to a
    name — nothing is retained under this packaging identity, and nothing about
    the bytes of any other epoch is implied. A world whose ``current`` pointer
    has never been written answers the same way: it has published no epoch, and
    inventing one to point at would be worse than saying so."""


class EpochCurrent(ScienceError):
    """Whole-epoch garbage collection named the epoch ``epochs/current`` names.
    Deletion is explicit consumer policy, and the one epoch a world is pointing
    at is not something a consumer may unpublish as a side effect of tidying:
    the pointer would be left naming nothing, and every act that follows it
    would refuse. Moving `current` is publication's business, so the refusal
    names the state rather than offering to repoint it."""


class BuildContended(ScienceError):
    """An epoch build asked for a root's coherent capture and found the
    operation lock already held. The build refuses at once rather than queue:
    waiting behind a corpus operation is what would let a build park the
    writer queue behind itself."""


class BuildHold(ScienceError):
    """A corpus write met an epoch build's coherent capture — present when the
    write arrived, or begun and ended while the write waited in the writer
    queue. The write is refused rather than re-queued, so a capture is never
    something a writer can silently straddle."""


class CoverageUnknown(ScienceError):
    """A build declared a `corpus_id` the world has never admitted. Coverage is
    declared, never inferred: a build that fell back to the registry's live set
    would publish an epoch whose scope nobody chose, and a corpus whose only
    credential is a manifest on a configured root has claimed admission rather
    than been granted it."""


class CoverageNotLive(ScienceError):
    """A build declared an admitted `corpus_id` that has since been retired or
    departed. Coverage is a statement about what the epoch *reports on*, and a
    terminal corpus is one the world has said it no longer reports on."""


class CoverageUnresolvable(ScienceError):
    """A covered `corpus_id` has no presently configured carrier root, or more
    than one. Both are the same failure — the build cannot say which bytes it
    would capture — and neither is repairable by choosing: an epoch built from
    whichever root sorted first would carry a state identity whose provenance
    depended on configuration order."""


class CaptureDrift(ScienceError):
    """A covered corpus's state identity moved between the two computations
    inside one capture hold. The hold excludes every corpus writer, so the
    mover was a raw filesystem edit. The whole capture is discarded and nothing
    is published; the build does not retry, because a silent retry would turn
    an operator editing a corpus under a running build into a build that
    eventually succeeded without saying so."""


class AnchorSubjectUnknown(ScienceError):
    """An anchoring act named a `corpus_id` this world has not admitted.
    Anchoring records what a corpus's chain presently says, and a world that
    anchored an unadmitted id would be recording a claim about a corpus it has
    never granted membership to — presence on a configured root is the
    corpus's own claim, not the world's."""


class AnchorTargetUnresolvable(ScienceError):
    """An admitted `corpus_id` has no presently configured carrier root, or
    more than one. Both are the same failure — the act cannot say whose chain
    it would read — and neither is repairable by choosing: resolution failure
    is never silent narrowing to whichever root sorted first."""


class AuditTargetUnconfigured(ScienceError):
    """An audit named a target root this world is not configured with.

    The audit's target is **explicit and never associated to the subject by
    reading its manifest** (log-verification design §6.1) — a manifest-based
    lookup could not locate the root whose `corpus.yaml` was rewritten to
    another id, which is the exact mismatch the audit exists to report. What
    remains is the configuration: for a corpus subject the root must be one of
    the configured corpus roots, and for a world subject it is the configured
    world root. A root outside both is one this world has made no claim about
    at all, and auditing it would be judging a stranger's bytes under this
    world's subject.

    It is a distinct name rather than `AnchorTargetUnresolvable`: that refusal
    says the act cannot tell *whose* chain it would read, and here the act was
    told exactly which root and that root is not this world's.
    """


class LogHeadCollision(ScienceError):
    """A content-addressed log-head record path exists with different bytes.

    The rules store's discipline, verbatim (log-verification design §3.1): a
    byte-identical record is skipped as success and submits no transaction,
    and a same-name file holding anything else is a collision rather than an
    overwrite — a record is immutable, and one whose name no longer names its
    content would make every later "maximal anchor" a reading of corrupted
    evidence."""


class LogEvidenceRefused(ScienceError):
    """The engine refused to produce the log evidence an act asked for.

    Three engine states escape the inspecting commands' never-raises envelope
    by design (log-verification design §6.4): a chain-vs-record contradiction
    (``ChainStateInvalid``), a halted transaction (``TransactionHalted``), and
    a capture refusal at a modeled path holding an unrepresentable entry
    (``PreconditionRefused``). The composition root's seam adapters translate
    exactly those three — nothing else, and ``ProtocolError`` and setup errors
    keep their own contracts — preserving the engine exception as ``__cause__``.

    **It is a refusal to judge, not a judgment.** It produces no report, it is
    not an arrival refusal, and it sits outside the evaluator's precedence and
    the arrival-cause ranking: the act did not decide that the evidence was
    bad, it never obtained any. Collapsing it into an outcome would let an
    unreadable root and a refuted one read the same downstream.
    """

    def __init__(
        self,
        phase: Literal["inspect", "capture"],
        engine_error: Literal["ChainStateInvalid", "TransactionHalted", "PreconditionRefused"],
        detail: str,
    ) -> None:
        super().__init__(f"{phase}: the engine refused with {engine_error}: {detail}")
        self.phase = phase
        self.engine_error = engine_error
        self.detail = detail


class AdmissionEvidenceRefused(ScienceError):
    """The successor-admission act refused to judge: evidence it must read
    is unreadable, incoherent, or unresolved. Names the offending record
    so the repair is directed; the act is retried after correction, never
    around it (successor-admission design §5)."""

    def __init__(self, reason: str, ref: str) -> None:
        super().__init__(f"{reason}: {ref}")
        self.reason = reason
        self.ref = ref


class ReplicaAdmissionRequiresVerification(ScienceError):
    """A bare `World.admit` was handed `ReplicaOf` provenance.

    A replica arrives carrying a chain that was written somewhere else, and
    admitting it is the one admission that asks a question about evidence:
    whether the traveled chain is the one its anchors describe. `admit` holds no
    verdict to report — it inspects nothing, states no surface and consults no
    observer — so it refuses rather than admitting on trust
    (log-verification design §6.2). The verified route is
    `beliefs.root.admit_arrival`, which returns the admission record and the
    report side by side.

    It is its own name rather than `ProvenanceMismatch`: nothing about the
    caller's composition is wrong here, and the remedy is a different call
    rather than a different argument.
    """


ArrivalCause: TypeAlias = Literal["malformed", "refuted", "pending", "chainless"]
"""§6.2's closed refusal vocabulary for a verified arrival, ranked
`malformed > refuted > pending > chainless`. The cause is derived from the
**report's fields**, never from which precedence step produced the outcome."""

_ARRIVAL_REMEDIES: Mapping[ArrivalCause, str] = MappingProxyType(
    {
        "malformed": "recopy from the origin; a structurally damaged chain is not repairable by evidence "
        "supplied here",
        "refuted": "recopy from the origin, or supply the observers that account for the disagreement",
        "pending": "settlement evidence from the origin, or recopy",
        "chainless": "recopy carrying the chain; a replica that did not carry its chain is not an "
        "unanchored arrival",
    }
)
"""The remedy each cause names, so that "the remedy named" (§6.2) is a property
of the error rather than of whichever call site raised it. The mapping is also
what closes the vocabulary at run time: a fifth cause would have no remedy and
could not be raised."""


class ArrivalRefused(ScienceError):
    """A verified arrival refused on the evidence its own report states.

    Carries the **complete** report — never a summary of it, since the caller's
    next move depends on the findings, the pending set and the observer bound —
    plus one closed cause and the remedy that cause names (log-verification
    design §6.2).

    The cause is read off the report's fields rather than off the precedence
    step that produced the outcome: a pending chain with an empty observer set
    is `unresolvable` at the anchor step and never reaches the pending step, and
    it still refuses arrival with cause `pending`. The four rank
    `malformed > refuted > pending > chainless`, and admissibility requires none
    of them.

    It is not `LogEvidenceRefused` and never overlaps it: this act judged and
    the verdict refused it, where that one never obtained evidence to judge.
    """

    def __init__(self, cause: ArrivalCause, report: "LogReport", detail: str) -> None:
        remedy = _ARRIVAL_REMEDIES[cause]
        super().__init__(f"{detail}: arrival refused on {cause}; remedy: {remedy}")
        self.cause = cause
        self.report = report
        self.remedy = remedy


class SubjectMismatch(ScienceError):
    """A root's manifest claims an identity that is not the selected subject.

    At **arrival** this is a lifecycle-boundary refusal and it fires even on a
    `validated` report (log-verification design §1.2, §6.3): a copied root whose
    manifest was re-minted to a fresh id still carries its parent's chain, and
    that chain judged against the parent validates — a cooperatively logged
    identity rewrite replays consistently. The chain is not what is wrong; the
    lifecycle is, and admitting it would enter one corpus into the registry
    under another's history.

    At **audit** the same disagreement is a finding and never this error: the
    audit reports, and it must stay usable on exactly the roots the operational
    surfaces refuse.

    Its placement is pinned: the report-based causes outrank it — a malformed,
    refuted, pending or chainless chain refuses on that cause first — and it is
    checked **before** the admission transaction, so no mismatched subject is
    ever admitted and then reported.
    """



class ObserverCarrierInvalid(ScienceError):
    """A supplied observer carrier does not validate as what it claims to be.

    Every carrier validates before evaluation (log-verification design §4.1):
    an epoch against its packaging identity, an artifact by its codec, a record
    by its grammar. A carrier that fails refuses the act — **never a silently
    narrowed observer set**, because an anchor dropped for being unreadable and
    an anchor that was never held are the same evidence-free state to a caller
    who is not told, and the second one is admissible.

    It is also the refusal of a carrier constructed past its factory: the
    factories are what retain the validation evidence, and a dataclass built
    directly would carry a provenance discriminator nothing had checked.
    """


class EnumeratedKindUngoverned(ScienceError):
    """A captured record claims a kind that one of the four epoch derivations
    enumerates but that has no governed stored-kind definition (§13). The
    record can be neither derived from — no contract says what its fields mean
    — nor silently omitted, which would publish an enumeration that quietly
    disagreed with the corpus it names. An *absence* of such records is an
    ordinary empty enumeration and is not this."""


class ResolutionRefused(ScienceError):
    """A bound address resolution met ambiguity or corruption (§8.3).

    Two configured roots claiming one `corpus_id`, a present carrier whose
    manifest cannot be read, or a present carrier that does not produce the
    `uid` the epoch mapped the address to. All three are refusals and none of
    them is `NotPresent`: absence is "this corpus is not carried here", and
    letting corruption borrow that answer would tell a caller the record is
    safely elsewhere when what actually happened is that this world cannot say
    what it holds.
    """


class EdgeIndeterminate(ScienceError):
    """A coreference expansion would have traversed an indeterminate edge (§8.4).

    Inspecting an edge state may answer `indeterminate`; *expanding* through
    one may not, because an expansion that skipped the edge would be reporting
    a coreference set as if the edge had been established inactive.

    The refusal names every unestablished input rather than stating that
    something was indeterminate: `missing_coverage` is the sorted live
    `corpus_id` values the epoch's coverage does not contain, and
    `receipt_outcome` is the exact non-``validated`` outcome of the coreference
    receipt, or `None` where the receipt validated and only coverage was
    short. A caller acts on those two differently — one is fixed by building a
    wider epoch, the other by holding a rule or restoring a corpus — so a
    generic message would be a refusal nobody can clear.
    """

    def __init__(
        self,
        message: str,
        *,
        missing_coverage: tuple[str, ...] = (),
        receipt_outcome: str | None = None,
    ) -> None:
        if not missing_coverage and receipt_outcome is None:
            raise ValueError("an indeterminate edge names at least one unestablished input")
        super().__init__(message)
        self.missing_coverage = missing_coverage
        self.receipt_outcome = receipt_outcome


class IdentityError(ScienceError):
    """A value or domain was refused by the identity contract."""


class UnsupportedValueType(IdentityError):
    """A value of a type the contract does not admit."""


class NullRefused(IdentityError):
    """A null. Refused, never pruned: an absent member must differ from a
    present-and-empty one, and pruning is what makes ``{"x": null}`` and ``{}``
    the same bytes."""


class BinaryFloatRefused(IdentityError):
    """A binary float. The caller supplies a decimal and owns the rounding, so a
    scientific value never inherits an accidental IEEE spelling."""


class NonFiniteDecimal(IdentityError):
    """``NaN``, ``Infinity``, ``-Infinity`` or a signalling form. JSON has no
    encoding for these and every substitute collides with something else."""


class NonStringKey(IdentityError):
    """An object key that is not a string."""


class KeyCollision(IdentityError):
    """Two object keys that are distinct before NFC normalization and identical
    after it. Rejected, never silently merged."""


class LoneSurrogate(IdentityError):
    """A string carrying an unpaired UTF-16 surrogate. It has no UTF-8 encoding,
    and the two implementations disagree about what it even is."""


class MalformedDomain(IdentityError):
    """A digest domain that is not a well-formed, versioned domain name."""


class CanonicalTextRefused(IdentityError):
    """Bytes presented as v1-canonical text are not: malformed UTF-8 or
    JSON, a refused constant, a re-encoding refusal (wrapped, cause
    preserved), or re-encoded bytes that differ from the input."""


class ContractError(ScienceError):
    """A contract was refused at load."""


class MalformedContract(ContractError):
    """A contract that is structurally wrong — an unknown field, a missing one, a
    value of the wrong shape. Unknown fields are refused rather than ignored: D5
    is explicit that an unrecognized field is *"refused at load, never ignored and
    never digested"*, and a contract quietly accepting one would make the reader
    and the loader disagree about what the document says."""


class UnparsedContract(ContractError):
    """A contract object that no parser produced.

    The root of the trust chain, and the reason ``ProfileSpec``'s own refusal to
    be authored is not sufficient on its own. That refusal says a profile came
    from ``compile_profile``; this one says what ``compile_profile`` was handed
    came from the authored documents. Without it a claim can be typed against a
    hand-built contract — which is to say typed against nothing, every operator,
    sort, layer and dimension in it invented by whoever built the object, with
    the normative SSOT (D §6) never opened."""


class ContractMismatch(ContractError):
    """Two contracts, each genuine, that were not typed against one another.

    Distinct from ``UnparsedContract`` and worth its own name: nothing here was
    forged, no brand was bypassed, and every parser did its job. A domain
    contract's layer selections are checked **once**, at parse time, against the
    base contract it was handed, and the compiled operator then carries them as
    facts — so compiling it against a *different* base yields a claim standing on
    a layer the compiled base does not declare.

    The general shape, worth remembering because provenance checks do not catch
    it: authenticating each input separately says nothing about whether they
    **belong together**. The rule is narrower than *"every stage records its
    inputs"*, and both halves of it matter. It applies to an artifact whose
    **validity is conditional** on a particular upstream artifact — some check it
    passed was taken against that one and is never retaken — and which **may
    later be recombined independently**, so it can arrive somewhere holding a
    different partner. Such a boundary must **either verify a recorded dependency
    or revalidate the relation**; a stage that rechecks what it depends on, or
    whose output never travels apart from its input, owes neither."""


class ContractDisagreement(ContractError):
    """Two corpora in one closure pinning different identities for one
    consulted namespace — refused, never merged, never preferred by recency
    (D §8.1). The evaluator returns this as `Refused`, D7 unchanged."""


class SuccessionViolation(ContractError):
    """A successor contract that redefines, drops, or misdeclares its lineage.
    Refused at contract **load** — never at claim decode, which sees wire bytes
    and cannot tell a claim being authored now from one being restored from a
    backup (§7.3a)."""


class ProfileError(ScienceError):
    """A profile refused — at compilation, at construction, or at resolution."""


class ResolutionError(ScienceError):
    """A snapshot or receipt refused — at construction, never at resolution itself.

    Resolving a term never raises: every one of §7.2's five outcomes is a
    well-formed answer, including the four that are not `member`. An exception
    here would be a sixth outcome smuggled in through the control flow, and it
    would be the one outcome a caller could not record in a receipt."""


class DecodeError(ScienceError):
    """The refusing arm of ``decodeClaim``'s sum type.

    Every subclass, together with the `ClaimError`s the shared constructor
    raises, is *Refused*: no claim is returned, and no receipt — a receipt
    records checks that were performed on a claim that exists."""


class MalformedWireClaim(DecodeError):
    """A wire value that is not shaped like a claim at all.

    Distinct from the profile-dependent refusals: this is settled before any
    contract is consulted, because the typing below it indexes into the value."""


class UnboundReferent(DecodeError):
    """A term that its sort's bound vocabulary was **read** and found not to contain.

    The one outcome of §7.2's five that refuses. It is positive evidence of a bad
    binding, and admitting it would put an unbindable identifier into an
    immutable claim identity. The three not-performed outcomes accept, and the
    distance between this class and them is the whole subject of §7.2 — refusing
    on `not-consulted` would report *"not in the vocabulary"* on the evidence
    that nobody looked."""


class DuplicateContribution(ProfileError):
    """Two contracts contributing to one namespace. D §8's rule for facets, and
    the same one here: contributions in *different* namespaces compose, and two
    contributions to one namespaced identifier are refused at compile, never
    resolved last-writer-wins."""


class SubclassRefused(ScienceError):
    """A subclass of a type that must stay closed.

    Opacity is worth exactly what `isinstance` is worth. A subclass can expose a
    raw constructor and mint an unchecked object that still satisfies
    `isinstance(x, Claim)` — at which point every downstream reader that trusts a
    `Claim` unconditionally is wrong, and M13's guarantee is gone without a line
    of it having been edited. `ProfileSpec` makes the same claim and needs the
    same seal, and so does every user-defined value type whose invariant a
    `Claim` trusts — `Referent`'s own check is what makes a claim's contents
    identifiers. The scope is that trust relation, not everything a claim holds.

    Not a `ClaimError` or a `ProfileError`: nothing is wrong with any claim or
    any profile. What is wrong is the code that was written."""


class WithdrawnFromAuthoring(ScienceError):
    """A retired identifier reached the **authoring** boundary — an operator, one
    of its argument sorts, a selected dimension, or that dimension's restriction
    sort.

    Deliberately not a `ContractError`: nothing is wrong with the contract, and
    nothing is wrong with the claim as a historical record. §7.3a puts retirement
    in authoring and *only* in authoring, so this refusal must never be reachable
    from decode, import or restore — which is why it is its own class and not a
    member of the family those boundaries raise.
    """


class ClaimError(ScienceError):
    """A claim, or a part of one, that is not admissible.

    Raised by the validated constructor and by the value types it admits. The
    subclasses stay distinct because M11 decodes each ill-formed input *in turn*
    and asserts a refusal each time; a single `ClaimError` would let one check
    silently cover for another's absence.
    """


class UntypedReferent(ClaimError):
    """A bare string, or any untyped value, in an argument slot or a restriction.

    §6.2 types a slot as `Referent(ArgSort(op, i))`, so the sort must travel with
    the value. A string carries no sort, which means nothing about it can be
    checked against the slot it was put in (M4)."""


class MalformedReferent(ClaimError):
    """A `Referent` whose sort or term is not an identifier.

    `term` is the one position in a claim that **nothing downstream checks**:
    the operator, the layer, the dimensions and the sorts are all matched against
    the profile's own tables, so a non-identifier there refuses on its own, but a
    referent's term is only checked for *membership* — and that is deferred to
    decode, against a snapshot. Without this check a `Claim` could be minted
    holding an integer where an identifier belongs."""


class UntypedQualifier(ClaimError):
    """A qualifier entry that is not a `Qualifier`. Structural typing is not
    enough here: an arbitrary object exposing `quantifier` and `restriction`
    would be stored inside a `Claim` and trusted as one."""


class ArityMismatch(ClaimError):
    """More or fewer arguments than the operator declares. Arity is per operator
    because it is not universally 2 (§6.2)."""


class ArgumentSortMismatch(ClaimError):
    """A referent of one sort in a slot declared for another. Inside the model
    these are different types and neither inhabits the other; here the sorts are
    runtime values, so the same fact is a refusal."""


class UndeclaredDimension(ClaimError):
    """A qualifier on a dimension the operator does not permit. `Dims(op)` is
    declared per operator — a population restriction is meaningless for a
    structural operator (§6.2)."""


class RestrictionSortMismatch(ClaimError):
    """A restriction bound to a referent of the wrong sort. A restriction is
    sorted exactly as an argument is (§6.2)."""


class UnknownQuantifier(ClaimError):
    """A quantifier outside the kernel's closed set. §6.4 rules the set
    kernel-owned and closed: `{ generic, universal, existential }`."""


class PolarityRefused(ClaimError):
    """A polarity the operator cannot carry — a sign asserted on a sign-inapt
    operator, no sign supplied for a sign-apt one, or a tag outside the base
    contract's closed set. For a sign-inapt operator `Polarity(op)` is the unit
    type (§6.3), so there is exactly one inhabitant and nothing for an author to
    choose."""


class InadmissibleLayer(ClaimError):
    """A layer outside the operator's declared set. `Layers(op)` is non-empty by
    construction — an operator admitting no layer would make `Claim` uninhabited
    at that operator (§6.2)."""


class TagCollision(ContractError):
    """Two kernel tags that must stay distinct and do not — a duplicate inside a
    closed set, or a ``sign_inapt_tag`` that is also an assertable polarity.
    ``inapt`` and ``unsigned`` are different facts (§7.5), and a projection that
    cannot tell them apart has lost the distinction it exists to carry."""


class RecordError(ScienceError):
    """A kernel record value refused at construction — the belief seam's
    analogue of ``ClaimError``. Subclasses stay distinct for the same reason."""


class MalformedRecord(RecordError):
    """A field that is not what the kernel's tables declare — a digest that is
    not ``<algorithm>:<lowercase hex>``, an outcome or scope outside its closed
    set, a role outside ``observes | reads | transforms``."""


class RecipeVersionUnsupported(RecordError):
    """A v1 recipe lacks the workflow snapshot required by typed decode."""


class DefinitionPlanMismatch(RecordError):
    """A workflow definition's declared streams disagree with its seed plan."""


class SeedClaimMalformed(RecordError):
    """A job cannot write one unambiguous seed claim."""


class PlanUnavailable(RecordError):
    """The planning launch did not yield one complete, consistent job set."""


class CheckpointDeclarationUnmet(RecordError):
    """A checkpoint-expansion declaration disagrees with the definition or plan."""


class TargetUnresolvable(RecordError):
    """A requested target matches no planned job."""


class TargetAmbiguous(RecordError):
    """A requested target matches more than one planned job."""


class RecordUndecodable(RecordError):
    """Captured bytes cannot be read as the named published record."""


class UrlLocatorDeferred(RecordError):
    """A ``url`` locator was constructed before the URL slice exists.

    The holdings design defers the whole URL retrieval boundary (spec §1 item
    1); constructing the locator refuses with this name — a declared behavior
    of conformance cut 10's labeled set, never silence.
    """


class OutcomeRefused(RecordError):
    """An entry outcome outside its act kind's reserved vocabulary — the sharp
    case being `byte-locator-untested` on a non-locator entry. No
    classification is borrowed across kinds (act-report §2.2, T5)."""


class CitationRefused(RecordError):
    """A citation names exactly one entry by zero-based unsigned index into
    the canonical sequence; out-of-range — negative included — is refused at
    the citing site (act-report §2.2, T6)."""


class SignatureRefused(RecordError):
    """An edge outside kernel §4.1's closed relation signatures — the sharp
    case being `assesses` from a source-assertion (G1). Refused in the typed
    constructor: inertness is the default, belief-bearing is the declared
    exception, and the exception is declared exactly once."""


class MalformedSnapshot(RecordError):
    """A lineage snapshot value refused at construction — one representation
    per fact: a `single` basis holds exactly one route, a `conflict` at least
    two distinct, sorted routes, so a conflict that never occurred cannot be
    spelled (substrate §5, sub-problem 4 §5.2)."""


class BasisTagMismatch(RecordError):
    """A basis-scoped query invoked against the wrong tag.

    Not a value refused at construction — every basis here is already
    well-formed (`MalformedSnapshot` is what refuses those). This is a *call*
    outside the domain the query is defined over: `divergence_state` compares
    a dataset's producers against its `single` basis route, and a `conflict`
    has no one route to compare against — the divergence question is decided
    on the tag alone before this is ever reached, and asking it anyway of a
    `conflict` is what this refuses."""


class MalformedSpec(RecordError):
    """A spec facet the freeze cannot accept — an empty ``target``, a seed plan
    whose stream-to-root mapping is not total (a derivation with no determined
    root argument), a mapped root nobody declared (computation §3.1a)."""


class UnfreezableSpec(RecordError):
    """A contradiction across two frozen fields, caught at freeze time — the
    §1.2 case: ``stochastic-unseeded`` beside a bitwise equivalence rule. A
    check, not a type refusal, because it spans fields (computation §3.1a)."""


class RuleUnbound(RecordError):
    """A rule identity with no held conforming implementation. An
    implementation that fails its fixtures is not that rule (computation
    §3.1b). The registry/resolver form of this refusal is the rules store's
    and is deferred (cut 3 §7 item 4)."""


class MixedShapes(RecordError):
    """A verification pair whose run shapes differ.

    One side's equivalence rule is authored and the other's is fixed, so there
    is no honest rule for a mixed pair (§7.3c).
    """


class UnreferencedSuccessor(RecordError):
    """Reserved for the revise path's internal guard; the boundary-facing
    verdict is the ``SuccessorRefused`` value (G4 is an outcome over value
    state, not an exception)."""


class MalformedClosure(RecordError):
    """A closure that cannot be completed — a missing member, an unknown- or
    attested-valued component, a bare lockfile digest as environment identity,
    an input role outside the shape's partition, a manifest disagreeing with
    the declaration. §2: this is not a weaker run; it is not a run."""


class UnsafeInvocation(RecordError):
    """The boundary's own input-safety construction, not confinement (cut 3
    §3): an option-like engine target, an entrypoint that does not resolve to
    a regular file inside the captured bundle, an absolute or root-escaping
    declared output."""


class ConfinementRefusal(ScienceError):
    """Base of the confined boundary's refusals (run-confinement design §8).

    Each subclass carries a stable ``reason`` as a class attribute; the run
    boundary maps it into ``RunRefused.reason`` and keeps the message as the
    in-memory diagnostic. The base carries no reason: a refusal without one is
    not a confinement refusal."""


class ConfinementUnavailable(ConfinementRefusal):
    """Pre-intent: bubblewrap absent or without ``--info-fd``, user namespaces
    disabled, or the loader's ``--list`` not callable on this host."""

    reason = "confinement-unavailable"


class BoundaryPolicyUnsupported(ConfinementRefusal):
    """Pre-intent: the supplied policy matches neither known definition on
    identity, scope rule and unique capability set together — a request
    failure, not an unavailable host."""

    reason = "boundary-policy-unsupported"


class ClosureUnsupported(ConfinementRefusal):
    """Post-intent: the runtime closure cannot be laid out — a SONAME
    collision, a symlink escaping the closure, an unfollowable or mixed
    ``.pth`` line, a non-ELF program interpreter, an unlistable artifact."""

    reason = "closure-unsupported"


class SnapshotMismatch(ConfinementRefusal):
    """Post-intent: an existing, freshly built, or concurrently published
    snapshot disagrees with the manifest. Never rebuilt — a corrupt shared
    snapshot is evidence, not a cache miss."""

    reason = "snapshot-mismatch"


class ClosureMutated(ConfinementRefusal):
    """Post-intent: the bundle, the snapshot or the staged inputs differ
    between the pre-bind and post-exit observations (design §4.4)."""

    reason = "closure-mutated"


class ConfinementNotEstablished(ConfinementRefusal):
    """Post-intent: a namespace equal to the parent's, a canonical mount
    table unequal to the plan, a probe check that failed, or a probe that
    never reported READY. The requested policy cannot be honestly executed."""

    reason = "confinement-not-established"


class NotAnAssessmentVerification(RecordError):
    """``admission_record`` was offered a dataset-production verification,
    which has no assessment to admit (design §7.2)."""


class CorpusRootRefused(ScienceError):
    """A path that cannot be a corpus root — an existing non-directory. The
    composition root creates the directory when it is absent and refuses
    anything else rather than registering a root beside it."""


class SemanticHashStale(ScienceError):
    """A stored node whose recorded semantic hash disagrees with the one its
    stored fields recompute to (`semantic-hash-stale`, substrate §4.3).

    Refused on the read path, never repaired: a disagreement says the fields
    and the hash were not written together, and which of the two is the record
    is exactly what a store with no recorded history cannot say. An edit that
    moves the fields *and* the hash together is undetectable here — the
    recorded-history bound, stated rather than patched.
    """


class SemanticHashMissing(ScienceError):
    """A stored node of a governed kind carrying no semantic-identity stamp at
    all (`semantic-hash-missing`; post-freeze strengthening, adapter design
    review 2026-08-18).

    The recorded-history bound covers fields and stamp moved *together*; a
    forger who simply omits the stamp is statically detectable, and admitting
    the omission would make the cheapest forgery the one the reader waves
    through. Prose kinds carry no semantic domain and no stamp obligation —
    the boundary mints every governed record stamped, so nothing the write
    API produces can raise this.
    """


class RetractionCycleMalformed(ScienceError):
    """A corpus-local retraction graph contains a cycle, so standing is undefined."""


class WriteRefused(ScienceError):
    """The add path's own refusals — what the write API decides, in Science's
    vocabulary. Execution-layer failures are not these: plan validity, engine
    refusal and halt cross the boundary as the seam's `PlanRefusedError` and
    `ExecutionError`, and a third vocabulary wrapping those two would add a
    layer with no added discrimination (adapter design §5)."""


class RecordAlreadyMinted(WriteRefused):
    """The create-path guard: the corpus already holds this `(uid, id)` pair.

    Refused **before plan construction**, so ordinary add and create-shaped
    family members cannot accidentally select `ReplaceOp`. Display-only
    replacement is explicit through `revise`; no public family deletes."""


class SupersedeTargetMissing(WriteRefused):
    """The named predecessor does not resolve in this corpus."""


class SupersedeIdentityUnchanged(WriteRefused):
    """A successor has the predecessor's proposition semantic identity."""


class FamilyKindUnsupported(WriteRefused):
    """A mutation family does not operate on the supplied node kind."""


class CoordinationKindUnsupported(WriteRefused):
    """A record was supplied through the wrong world or coordination family door."""


class CoordinationUnavailable(WriteRefused):
    """The writer's destination is absent from its coordination resolver."""


class PredecessorMismatch(WriteRefused):
    """A predecessor stands but belongs to another kind or coordination address."""


class PredecessorNotStanding(WriteRefused):
    """A supplied predecessor is absent or superseded at the commit check."""


class ProjectNotResolvable(WriteRefused):
    """The project required by a subordinate coordination record does not resolve."""

    def __init__(self, message: str, *, tips: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.tips = tuple(sorted(set(tips)))


class RetractionTargetIneligible(WriteRefused):
    """A retraction target arm or node kind is not eligible."""


class RetractionTargetUnresolvable(WriteRefused):
    """A retraction's local node, dataset, or exact route does not resolve."""


class RetractionGroundsMissing(WriteRefused):
    """A retraction carries no present string grounds reference."""


class RevisionTargetMissing(WriteRefused):
    """The supplied `(uid, id)` pair does not identify a local node."""


class ReviseKindImmutable(WriteRefused):
    """The supplied node kind has no in-place revision path."""


class ReviseOutsideAllowlist(WriteRefused):
    """A revision changes something other than proposition display prose."""


class RelocationRefused(WriteRefused):
    """A two-root world-changing operation refused before any transaction.

    Every relocation refusal is one of these: the operation decides in
    Science's vocabulary under both locks, before an engine lease exists.
    """


class SameRootRefused(RelocationRefused):
    """Both positions resolved to one corpus root.

    `move` has nowhere to move to, and `consolidate`'s scope is two readable
    corpora — a single corpus holding two live records at one canonical address
    needs a recovery scanner this design does not build.
    """


class AddressDisagreement(RelocationRefused):
    """`consolidate` was given two different canonical addresses.

    That is a coreference question and `consolidate` must not answer it. It is
    also why `consolidate` is unavailable for one `uid` under two addresses —
    W8b's corruption case, refused on this precondition rather than by a
    corruption check.
    """


class DuplicateLocation(RelocationRefused):
    """`move`'s destination already holds a record at that canonical address.

    Repairing that is `consolidate`'s job, not `move`'s — and it is also the
    state a `move` interrupted after its destination create leaves behind.
    """


class ContractPinDisagreement(RelocationRefused):
    """The receiving corpus does not pin what the relocated node needs (D7).

    Raised for a differing `science_contract`, a differing identity for a
    namespace the node's facets use, and for a namespace the receiving corpus
    pins nothing for — agreement requires exactly one identity, so a missing pin
    is a disagreement and not a permission.
    """


class RelocationKindExcluded(RelocationRefused):
    """The record's kind is excluded from every world-changing operation.

    Act-reports (T8), coordination records, and holdings observations.
    """


class RelocationTargetMissing(RelocationRefused):
    """A create-only family's target stopped resolving under the lock.

    The replacement for family-adapters §5.3's monotonicity argument: consolidate
    and move can remove a record another operation resolved, so `retract` and
    `supersede` re-read their target and refuse rather than assume.
    """


class BasisMissing(WriteRefused):
    """W3 as narrowed: a `source` with no accepted external identifier, or a
    `dataset` with no content identity. Refused, never coerced to a curation
    `note` — a note is its own explicit add, and supplying the basis later is
    a second, separate mint. No title-and-year fallback exists to reach."""


class EligibilityUnmet(WriteRefused):
    """S7's write boundary: an inadmissible `assesses` edge — one whose run
    has no `observes` input carrying the `empirical-observation` facet. The
    cross-node predicate reads through the same corpus's read view."""


class ValidationRefused(WriteRefused):
    """A `nodes` document (or registry) validation failure, wrapped with the
    `nodes` exception as `__cause__` so no `nodes` error escapes raw."""


class CollisionRefused(WriteRefused):
    """`assert_addable`'s corpus-side refusals — a uid held by another id, or
    an identity claim held by another uid — wrapped for the same reason.
    These never reach an executor."""


class ImportRefused(WriteRefused):
    """A whole import bundle refused before its payload transaction."""

    def __init__(
        self,
        message: str,
        *,
        member: str | None = None,
        cycle_edges: tuple[tuple[str, str], ...] = (),
        report_ref: str | None = None,
    ) -> None:
        super().__init__(message)
        self.member = member
        self.cycle_edges = cycle_edges
        self.report_ref = report_ref


class BundleMemberHeld(ImportRefused):
    """A bundle member is already held or collides with local state."""
