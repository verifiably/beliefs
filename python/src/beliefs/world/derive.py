"""Pure derivation: one captured view, four subjects, and one receipt contract.

Specification §7.1 splits an epoch build in two. **Capture** enumerates each
covered corpus exactly once, under that corpus's operation lock, and produces
an immutable captured view. **Derivation** — everything in this module — reads
that view and nothing else. It cannot inspect a corpus root, a registry, a
`current` pointer or an installed default, because it is handed none of them
and imports nothing that could find one. That is the property receipts rest on:
a receipt names the exact captured states it ran over, and a derivation that
could quietly consult a live corpus would make the states it names a partial
account of what it read.

**One captured-record model** (`Capture`, `CapturedCorpus`, `CapturedRecord`).
Not four. §7.1 says the pass produces a view *sufficient for all four
derivations*, so the four reducers read one projection of one model rather than
four bespoke pre-flattened inputs. A record carries the members every
derivation shares — its address, its `uid`, its declared kind, its
`deprecated_ids` and its `produces` edges — and composes in the at-most-one
facet value its kind contributes: a captured retraction, a captured
certification, or a captured coreference attestation. A record's facet slots
are `None` where the record has nothing to say, never absent, so a reducer
reads a total shape and no reducer needs a default.

**Where each derivation lives, and why they are not all rules.** §5.2's build
input names one exact `(rule_identity, implementation_identity)` pair for each
of *four* derivations, and §7.5 mints one receipt for each: the producer
snapshot, the retraction enumeration, the certification inventory and the
coreference map. Those four are fixture-bound rules, held in the rules store,
and this module only parses what they return and computes the pinned identity
of it. The address map (§7.2) and the retraction-discovery map (§7.4) are the
epoch's other two derived maps; neither is a receipt subject, so neither is a
rule, and both are plain folds over the same captured view here. Each fold
reads the captured records — never a corpus — so "one enumeration pass" is
preserved: what is not repeated is the *enumeration*, not the arithmetic.

**Parsing a rule's return is not ceremony.** A rule is admitted content, and
`science.identity.v1` would happily digest a return of the wrong shape into a
perfectly stable identity for a projection §7.6 does not describe. So each
subject value parses the return — closed key set, sorted, distinct, typed —
and re-emits §7.6's projection itself. `RuleNonconformant` is the refusal, the
same name the store uses when an implementation fails its fixtures, because it
is the same fault found one moment later.

**Reading these projections beside §7.6.** The specification writes each
projection with an explicit `list(sorted(...))`; `sorted` already returns a
list, so the code below writes `sorted(...)` and the encoded bytes are the
same. Nothing else about the four projections differs from the text.

**Identity domains, pinned here.** `science.producer-snapshot.v1`,
`science.retraction-enumeration.v1`, `science.certification-inventory.v1` and
`science.coreference-map.v1` are §7.6's four, minted by that amendment. The
receipt domain is `epoch.RECEIPT_DOMAIN`, and a receipt digests the *subject
projection identity* — never the subject bytes a second time.

**One belief input.** The producer snapshot identity is the only member of an
epoch that reaches belief (§7.3). The coreference map is outside belief by the
world-address ruling §5.3, so its receipt carries no semantic identity — and
because the four receipts share one contract, the absence has to be a property
of the receipt's field set rather than a rule about one kind. `DerivationReceipt`
therefore has nowhere to put a semantic identity or a belief member at all;
`BELIEF_INPUT_KIND` names the one kind whose *subject* is one.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, cast

from beliefs.closure import RetractionEnumeration
from beliefs.errors import RuleNonconformant
from beliefs.identity import v1
from beliefs.world import epoch

__all__ = [
    "BELIEF_INPUT_KIND",
    "CERTIFICATION_INVENTORY_DOMAIN",
    "COREFERENCE_MAP_DOMAIN",
    "PRODUCER_SNAPSHOT_DOMAIN",
    "RECEIPT_OUTCOMES",
    "RETRACTION_ENUMERATION_DOMAIN",
    "SUBJECT_DOMAINS",
    "Capture",
    "CapturedCertification",
    "CapturedCoreference",
    "CapturedCorpus",
    "CapturedRecord",
    "CapturedRetraction",
    "CertificationInventory",
    "CoreferenceMap",
    "DerivationReceipt",
    "ProducerSnapshot",
    "ReceiptKind",
    "ReceiptOutcome",
    "address_map",
    "address_map_projection",
    "belief_input_identity",
    "certification_inventory",
    "coreference_map",
    "derivation_receipts",
    "producer_snapshot",
    "producers_map_projection",
    "retraction_discovery_map",
    "retraction_discovery_map_projection",
    "retraction_enumeration",
    "retraction_enumeration_identity",
    "retraction_enumeration_projection",
    "subject_identity",
    "subject_projection",
]

PRODUCER_SNAPSHOT_DOMAIN = "science.producer-snapshot.v1"
RETRACTION_ENUMERATION_DOMAIN = "science.retraction-enumeration.v1"
CERTIFICATION_INVENTORY_DOMAIN = "science.certification-inventory.v1"
COREFERENCE_MAP_DOMAIN = "science.coreference-map.v1"

RECEIPT_OUTCOMES: tuple[str, ...] = ("validated", "refuted", "unresolvable", "malformed")
"""§7.5's closed outcome set, in the order the specification writes it.

Declared here because the outcomes are values of this slice's derivation
contract; deciding one is Task 10's receipt validator, which reads this set.
"""

BELIEF_INPUT_KIND = "producer"
"""The one receipt kind whose subject identity is a belief input (§7.3)."""

ReceiptKind = Literal["producer", "retraction-enumeration", "certification-enumeration", "coreference-reduction"]
"""§7.5's four kinds, as a type. The *values* live in `epoch.RECEIPT_KINDS`,
which is where the join to §6.1's member names is; this exists so a signature
naming a kind says which four it means."""


@dataclass(frozen=True)
class ReceiptOutcome:
    """One receipt's validation verdict, and why (§7.5).

    Three members and no more. `outcome` is the whole answer — the closed set
    §7.5 fixes — and `kind` says which receipt it is the answer for, because a
    verdict travelling without its subject is a verdict a caller has to
    remember the provenance of. `detail` is the finding in words: which key was
    outside the closed set, which corpus no longer stands where it stood, which
    pair is not held. It exists because every non-``validated`` outcome names
    something a caller can act on, and an outcome that made the caller re-derive
    that themselves would be a verdict they could only trust or ignore.

    There is no member for the rebuilt subject and none for the epoch. A
    validation result is not a second, weaker way to obtain either.
    """

    kind: ReceiptKind
    outcome: str
    detail: str

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"{self.kind!r} is not one of {sorted(_KINDS)}")
        if self.outcome not in RECEIPT_OUTCOMES:
            raise ValueError(f"{self.outcome!r} is not one of {list(RECEIPT_OUTCOMES)}")
        _require_text(self.detail, "detail")

    @property
    def validated(self) -> bool:
        """Whether this receipt rebuilt to the subject it named. Read by the
        edge query, which admits exactly one of the four outcomes."""
        return self.outcome == "validated"


# --- the captured view -------------------------------------------------------


@dataclass(frozen=True)
class CapturedRetraction:
    """One captured retraction record's derivation-relevant content.

    `target` is the target identity the retraction names — what the
    retraction-discovery map keys on. `resolution` is the resolution the
    capture found for it, and it travels with the ref into the enumeration so
    that no reader has to decide which resolution an enumeration preferred.
    Both are carried as captured text: this layer never re-resolves one.
    """

    target: str
    resolution: str

    def __post_init__(self) -> None:
        _require_text(self.target, "target")
        _require_text(self.resolution, "resolution")


@dataclass(frozen=True)
class CapturedCertification:
    """One captured certification: its kind and its ref, and nothing else.

    Location-free and resolution-free by construction (§7.6). The corpus the
    record was found in lives on `CapturedCorpus`, and whether the ref resolves
    is a property of the world reading the epoch — so neither is here to be
    accidentally carried into the inventory.
    """

    kind: str
    ref: str

    def __post_init__(self) -> None:
        _require_text(self.kind, "kind")
        _require_text(self.ref, "ref")


@dataclass(frozen=True)
class CapturedCoreference:
    """One captured coreference attestation, as the world-address ruling §5.1
    defines it.

    The endpoints are held **as captured**, not canonicalized here: sorting them
    is part of the reduction the coreference rule performs and is checkable in
    its fixtures. What is refused here is a pair that is not two distinct
    endpoints, and a stance outside ±1 — neither is a claim the reduction could
    weigh.
    """

    endpoints: tuple[str, str]
    stance: int
    actor: str
    grounds: str
    event_token: str

    def __post_init__(self) -> None:
        if type(self.endpoints) is not tuple or len(self.endpoints) != 2:
            raise ValueError("a coreference attestation names exactly two endpoints")
        left, right = self.endpoints
        _require_text(left, "endpoint")
        _require_text(right, "endpoint")
        if left == right:
            raise ValueError(f"{left!r} is named as both endpoints; a self-pair is a claim with no content")
        if type(self.stance) is not int or self.stance not in (1, -1):
            raise ValueError("a coreference stance is +1 or -1")
        _require_text(self.actor, "actor")
        _require_text(self.grounds, "grounds")
        _require_text(self.event_token, "event_token")


@dataclass(frozen=True)
class CapturedRecord:
    """One stored node, as the enumeration pass saw it.

    The universal members come first — the live address, the `uid` the address
    map answers with, the declared kind, the retired addresses this record
    still answers to, and the dataset addresses it `produces`. The three facet
    slots compose in whatever the record's kind contributes, and are `None`
    where it contributes nothing.

    A record may hold at most one facet value. A stored node is one kind, and a
    record claiming to be a retraction *and* a certification would make the two
    enumerations disagree about what they counted.
    """

    address: str
    uid: str
    kind: str
    deprecated_ids: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    retraction: CapturedRetraction | None = None
    certification: CapturedCertification | None = None
    coreference: CapturedCoreference | None = None

    def __post_init__(self) -> None:
        _require_text(self.address, "address")
        _require_text(self.uid, "uid")
        _require_text(self.kind, "kind")
        _require_distinct_text(self.deprecated_ids, "deprecated_ids")
        _require_text_members(self.produces, "produces")
        if self.address in self.deprecated_ids:
            raise ValueError(f"{self.address!r} is both live and deprecated in one record")
        facets = [self.retraction, self.certification, self.coreference]
        if len([facet for facet in facets if facet is not None]) > 1:
            raise ValueError(f"{self.address!r} carries more than one captured facet")

    def projection(self) -> dict[str, object]:
        """This record as the value a reducer reads. Total: every key is
        present on every record, so no reducer supplies a default."""
        return {
            "address": self.address,
            "uid": self.uid,
            "kind": self.kind,
            "deprecated_ids": list(self.deprecated_ids),
            "produces": list(self.produces),
            "retraction": (
                None
                if self.retraction is None
                else {"target": self.retraction.target, "resolution": self.retraction.resolution}
            ),
            "certification": (
                None
                if self.certification is None
                else {"kind": self.certification.kind, "ref": self.certification.ref}
            ),
            "coreference": (
                None
                if self.coreference is None
                else {
                    "endpoints": list(self.coreference.endpoints),
                    "stance": self.coreference.stance,
                    "actor": self.coreference.actor,
                    "grounds": self.coreference.grounds,
                    "event_token": self.coreference.event_token,
                }
            ),
        }


@dataclass(frozen=True)
class CapturedCorpus:
    """One covered corpus's whole capture: its stable id, the corpus-state
    identity computed inside its capture hold, and every record enumerated.

    `corpus_id` is carried as opaque text. The registry owns its shape and
    refuses anything else long before a build reaches here; a pure derivation
    that re-litigated it would be a second authority on the same field.
    """

    corpus_id: str
    corpus_state: str
    records: tuple[CapturedRecord, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.corpus_id, "corpus_id")
        _require_lower_hex(self.corpus_state, 64, "corpus_state")
        if type(self.records) is not tuple:
            raise TypeError("records must be an exact tuple")
        addresses = [record.address for record in self.records]
        if len(set(addresses)) != len(addresses):
            raise ValueError(f"{self.corpus_id!r} enumerated one address twice")


@dataclass(frozen=True)
class Capture:
    """Every covered corpus's capture, and nothing else.

    The declared coverage is not a separate field: it is exactly the set of
    `corpus_id` values captured, because §7.1 admits no third state where a
    corpus is covered and not captured or captured and not covered. Coverage
    checking — admitted, live, singly resolvable — happens in preflight, before
    a capture exists.
    """

    corpora: tuple[CapturedCorpus, ...]

    def __post_init__(self) -> None:
        if type(self.corpora) is not tuple:
            raise TypeError("corpora must be an exact tuple")
        seen: set[str] = set()
        for captured in self.corpora:
            if type(captured) is not CapturedCorpus:
                raise TypeError("a capture holds CapturedCorpus values")
            if captured.corpus_id in seen:
                raise ValueError(f"{captured.corpus_id!r} is captured twice; a corpus is covered once")
            seen.add(captured.corpus_id)

    @property
    def coverage(self) -> tuple[str, ...]:
        """The declared coverage, as sorted stable `corpus_id` values."""
        return tuple(sorted(captured.corpus_id for captured in self.corpora))

    @property
    def corpus_states(self) -> tuple[tuple[str, str], ...]:
        """The sorted `(corpus_id, corpus_state_identity)` pairs every receipt
        of this epoch carries — identically, by §7.5."""
        return tuple(sorted((captured.corpus_id, captured.corpus_state) for captured in self.corpora))

    def located_records(self) -> tuple[tuple[str, CapturedRecord], ...]:
        """Every captured record with the corpus it was found in, in one
        deterministic order. The two location-bearing derivations — the address
        map and the retraction-discovery map — read this; the four rules read
        `rule_input`, which carries the same records."""
        return tuple(
            sorted(
                ((captured.corpus_id, record) for captured in self.corpora for record in captured.records),
                key=lambda located: (located[0], located[1].address),
            )
        )

    def rule_input(self) -> dict[str, object]:
        """The one projection value all four reducers receive.

        Records are ordered by `(corpus_id, address)` so that a rule which
        (wrongly) depended on iteration order would at least be deterministic
        about it, and a fixture pinning the order says what the order is.
        """
        return {
            "coverage": list(self.coverage),
            "records": [
                {"corpus_id": corpus_id, **record.projection()} for corpus_id, record in self.located_records()
            ],
        }


# --- the two maps that are not receipt subjects ------------------------------


def address_map(capture: Capture) -> Mapping[str, tuple[str, str]]:
    """§7.2's address map: every live address **and** every `deprecated_ids`
    entry, each mapped to `(corpus_id, uid)`.

    A retired address is a publication member rather than a corpus-local
    redirect, so its answer survives its corpus being absent — that is the
    whole reason the deprecated entries are here and not left in the corpus.

    The mapping is singular under world §4.3's invariant, and singularity is
    enforced rather than assumed: two claims on one address is corruption, and
    resolving it by insertion order would publish an answer whose correctness
    depended on directory listing order. A second claim refuses even when it
    agrees with the first — two records answering to one address at one `uid`
    is a `uid` collision `nodes` already forbids, and "they happen to agree" is
    not a reason to publish an address whose singularity nobody can vouch for.
    """
    mapping: dict[str, tuple[str, str]] = {}
    for corpus_id, record in capture.located_records():
        for address in (record.address, *record.deprecated_ids):
            held = mapping.get(address)
            if held is not None:
                raise ValueError(
                    f"{address!r} is claimed by {held} and by {(corpus_id, record.uid)}; "
                    "the address map is singular (world §4.3)"
                )
            mapping[address] = (corpus_id, record.uid)
    return MappingProxyType(mapping)


def address_map_projection(mapping: Mapping[str, tuple[str, str]]) -> dict[str, object]:
    """The `address-map.yaml` member's projection, sorted by address."""
    return {
        "addresses": [
            {"address": address, "corpus_id": corpus_id, "uid": uid}
            for address, (corpus_id, uid) in sorted(mapping.items())
        ]
    }


def retraction_discovery_map(capture: Capture) -> Mapping[str, tuple[str, ...]]:
    """§7.4's retraction-discovery map: target identity → sorted retraction
    addresses.

    Several retractions may name one target — event tokens keep genuinely
    distinct retraction events distinct — so the value is a list and never a
    single ref. It is bounded by the capture's coverage in the only way a pure
    derivation can be bounded: a corpus that was not captured contributes no
    record, and the enumeration declares the coverage it ran under beside it.
    """
    targets: dict[str, set[str]] = {}
    for _corpus_id, record in capture.located_records():
        if record.retraction is None:
            continue
        targets.setdefault(record.retraction.target, set()).add(record.address)
    return MappingProxyType({target: tuple(sorted(refs)) for target, refs in sorted(targets.items())})


def retraction_discovery_map_projection(mapping: Mapping[str, tuple[str, ...]]) -> dict[str, object]:
    """The `retraction-discovery-map.yaml` member's projection, sorted."""
    return {
        "targets": [
            {"target": target, "retractions": sorted(refs)} for target, refs in sorted(mapping.items())
        ]
    }


# --- the four receipt subjects -----------------------------------------------


@dataclass(frozen=True)
class ProducerSnapshot:
    """§7.3's producer snapshot: the producers map and the declared coverage.

    Coverage is stable `corpus_id` values, **not** captured states. That split
    is what makes this identity semantic: moving an unchanged entity between
    two covered corpora changes every captured state and therefore every
    receipt, and leaves this identity exactly where it was.
    """

    producers: Mapping[str, tuple[str, ...]]
    coverage: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "producers", MappingProxyType(dict(self.producers)))

    def projection(self) -> dict[str, object]:
        return {
            "producers": [
                {"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(self.producers.items())
            ],
            "coverage": sorted(self.coverage),
        }

    def identity(self) -> str:
        return v1.digest(PRODUCER_SNAPSHOT_DOMAIN, self.projection())


def producers_map_projection(producers: Mapping[str, tuple[str, ...]]) -> dict[str, object]:
    """The `producers-map.yaml` member: the map alone.

    §6.1 stores the map and the snapshot as two members, and only the snapshot
    declares what it was built over — a map carrying its own coverage would be
    a second, unreceipted place for the declaration to live.
    """
    return {
        "producers": [{"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(producers.items())]
    }


def producer_snapshot(produced: object) -> ProducerSnapshot:
    """The producer rule's return, parsed as §7.6's producer snapshot."""
    document = _closed(produced, ("coverage", "producers"), "a producer snapshot")
    producers: dict[str, tuple[str, ...]] = {}
    datasets: list[str] = []
    for entry in _members(document["producers"], "producers"):
        member = _closed(entry, ("dataset", "runs"), "a producers entry")
        dataset = _text(member["dataset"], "dataset")
        datasets.append(dataset)
        producers[dataset] = _sorted_distinct(member["runs"], f"the runs of {dataset!r}")
    _require_ordered(datasets, "the datasets of a producer snapshot")
    return ProducerSnapshot(producers=producers, coverage=_sorted_distinct(document["coverage"], "coverage"))


def retraction_enumeration(produced: object) -> RetractionEnumeration:
    """The retraction rule's return, parsed as §7.6's retraction enumeration.

    The value is `beliefs.closure.RetractionEnumeration` — the belief closure's
    own member — rather than a second type of the same shape. Correction
    lifecycle §6 puts *this* enumeration in the closure, so an epoch that
    published one shape while belief digested another would be two readings of
    one contract.
    """
    document = _closed(produced, ("coverage", "found"), "a retraction enumeration")
    found: list[tuple[str, str]] = []
    for entry in _members(document["found"], "found"):
        if type(entry) is not list or len(entry) != 2:
            raise RuleNonconformant("a found retraction is exactly a (ref, resolution) pair")
        found.append((_text(entry[0], "a retraction ref"), _text(entry[1], "a retraction resolution")))
    _require_ordered(found, "the found retractions")
    if len(set(found)) != len(found):
        raise RuleNonconformant("the found retractions repeat a (ref, resolution) pair")
    return RetractionEnumeration(found=tuple(found), coverage=_sorted_distinct(document["coverage"], "coverage"))


def retraction_enumeration_projection(enumeration: RetractionEnumeration) -> dict[str, object]:
    """§7.6's retraction enumeration projection."""
    return {
        "found": [list(pair) for pair in sorted(enumeration.found)],
        "coverage": sorted(enumeration.coverage),
    }


def retraction_enumeration_identity(enumeration: RetractionEnumeration) -> str:
    """The subject identity under `science.retraction-enumeration.v1`."""
    return v1.digest(RETRACTION_ENUMERATION_DOMAIN, retraction_enumeration_projection(enumeration))


@dataclass(frozen=True)
class CertificationInventory:
    """§7.6's certification inventory: sorted refs under each kind, and the
    coverage. Location-free and resolution-free — the projection has nowhere to
    put a corpus or a resolution, which is stronger than declining to fill one
    in."""

    by_kind: Mapping[str, tuple[str, ...]]
    coverage: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "by_kind", MappingProxyType(dict(self.by_kind)))

    def projection(self) -> dict[str, object]:
        return {
            "by_kind": [
                {"kind": kind, "refs": sorted(refs)} for kind, refs in sorted(self.by_kind.items())
            ],
            "coverage": sorted(self.coverage),
        }

    def identity(self) -> str:
        return v1.digest(CERTIFICATION_INVENTORY_DOMAIN, self.projection())


def certification_inventory(produced: object) -> CertificationInventory:
    """The certification rule's return, parsed as §7.6's inventory."""
    document = _closed(produced, ("by_kind", "coverage"), "a certification inventory")
    by_kind: dict[str, tuple[str, ...]] = {}
    kinds: list[str] = []
    for entry in _members(document["by_kind"], "by_kind"):
        member = _closed(entry, ("kind", "refs"), "a certification inventory entry")
        kind = _text(member["kind"], "kind")
        kinds.append(kind)
        by_kind[kind] = _sorted_distinct(member["refs"], f"the refs of {kind!r}")
    _require_ordered(kinds, "the kinds of a certification inventory")
    return CertificationInventory(by_kind=by_kind, coverage=_sorted_distinct(document["coverage"], "coverage"))


@dataclass(frozen=True)
class CoreferenceMap:
    """§7.6's coreference map: sorted endpoint pair → `(balance, distinct-key
    count)`.

    The reduced values only. `active`, `inactive` and `indeterminate` are
    query-time states, and no coverage, edge state or belief member enters this
    subject identity — so two epochs over different coverages that reduced the
    same attestations carry one coreference identity, and each still answers
    its own query differently.
    """

    pairs: Mapping[tuple[str, str], tuple[int, int]]

    def __post_init__(self) -> None:
        """The reduction's invariants belong to the *type*, not only to the
        parser that builds one from a rule's return.

        `coreference_map` refuses the same three faults as `RuleNonconformant`,
        because there they are a statement about what an implementation
        returned. Here they are a statement about what a coreference map *is*:
        §7.6 stores every pair with `left < right`, and the world-address
        ruling §5.2's unit weights make `abs(balance) <= count` arithmetic
        rather than convention. Without this, a value constructed directly with
        `("b", "a")` would project unordered endpoints straight into a digest —
        a second, wrong identity for a reduction the rule got right.
        """
        pairs: dict[tuple[str, str], tuple[int, int]] = {}
        for endpoints, reduced in dict(self.pairs).items():
            if type(endpoints) is not tuple or len(endpoints) != 2:
                raise ValueError("a coreference pair is keyed by exactly two endpoints")
            left, right = endpoints
            _require_text(left, "endpoint")
            _require_text(right, "endpoint")
            if not left < right:
                raise ValueError(f"the endpoints {[left, right]} are not stored with left < right")
            if type(reduced) is not tuple or len(reduced) != 2:
                raise ValueError(f"{endpoints} must reduce to an exact (balance, distinct_key_count) pair")
            balance, count = reduced
            if type(balance) is not int or type(count) is not int:
                raise ValueError(f"{endpoints} reduces to two integers")
            if count < 1:
                raise ValueError(f"{endpoints} is published having reduced no distinct key")
            if abs(balance) > count:
                raise ValueError(f"a balance of {balance} cannot come from {count} unit-weight keys")
            pairs[endpoints] = reduced
        object.__setattr__(self, "pairs", MappingProxyType(pairs))

    def projection(self) -> dict[str, object]:
        return {
            "pairs": [
                {"endpoints": [left, right], "balance": balance, "distinct_key_count": count}
                for (left, right), (balance, count) in sorted(self.pairs.items())
            ]
        }

    def identity(self) -> str:
        return v1.digest(COREFERENCE_MAP_DOMAIN, self.projection())


def coreference_map(produced: object) -> CoreferenceMap:
    """The coreference rule's return, parsed as §7.6's coreference map."""
    document = _closed(produced, ("pairs",), "a coreference map")
    pairs: dict[tuple[str, str], tuple[int, int]] = {}
    endpoints: list[tuple[str, str]] = []
    for entry in _members(document["pairs"], "pairs"):
        member = _closed(entry, ("balance", "distinct_key_count", "endpoints"), "a coreference pair")
        if type(member["endpoints"]) is not list or len(member["endpoints"]) != 2:
            raise RuleNonconformant("a coreference pair names exactly two endpoints")
        left = _text(member["endpoints"][0], "an endpoint")
        right = _text(member["endpoints"][1], "an endpoint")
        if not left < right:
            raise RuleNonconformant(f"the endpoints {[left, right]} are not stored with left < right")
        count = _count(member["distinct_key_count"], "distinct_key_count")
        if count < 1:
            raise RuleNonconformant("a published coreference pair reduced at least one distinct key")
        balance = _count(member["balance"], "balance")
        if abs(balance) > count:
            raise RuleNonconformant(f"a balance of {balance} cannot come from {count} unit-weight keys")
        endpoints.append((left, right))
        pairs[(left, right)] = (balance, count)
    _require_ordered(endpoints, "the pairs of a coreference map")
    return CoreferenceMap(pairs=pairs)


SUBJECT_DOMAINS: Mapping[str, str] = MappingProxyType(
    {
        "producer": PRODUCER_SNAPSHOT_DOMAIN,
        "retraction-enumeration": RETRACTION_ENUMERATION_DOMAIN,
        "certification-enumeration": CERTIFICATION_INVENTORY_DOMAIN,
        "coreference-reduction": COREFERENCE_MAP_DOMAIN,
    }
)
"""Each receipt kind's subject-identity domain (§7.6).

The four domains are declared individually above because each belongs to its
own subject; this is the join to §7.5's kind vocabulary, and it exists so that
a validator rebuilding "the subject this kind names" reads one table instead of
branching four times.
"""

_SUBJECT_PARSERS: Mapping[str, Callable[[object], object]] = MappingProxyType(
    {
        "producer": producer_snapshot,
        "retraction-enumeration": retraction_enumeration,
        "certification-enumeration": certification_inventory,
        "coreference-reduction": coreference_map,
    }
)


def subject_projection(kind: str, produced: object) -> dict[str, object]:
    """One derivation's return, parsed and canonically projected by kind.

    The receipt validator rebuilds a subject by running the exact named
    implementation and comparing what came back with what the epoch published.
    That comparison is over the §7.6 *projection* — the canonical value the
    subject identity digests — so the parse and the projection have to be one
    step, taken the same way here as at build time. `RuleNonconformant` for a
    return that is not this kind's subject at all.
    """
    parsed = _SUBJECT_PARSERS[_require_kind(kind)](produced)
    if kind == "retraction-enumeration":
        return retraction_enumeration_projection(cast(RetractionEnumeration, parsed))
    return cast("ProducerSnapshot | CertificationInventory | CoreferenceMap", parsed).projection()


def subject_identity(kind: str, projection: Mapping[str, object]) -> str:
    """The §7.6 identity of one subject projection, under its kind's domain.

    Taken over the projection rather than over the parsed value, so that a
    projection lifted back out of a published member digests to exactly what
    the member's own subject digested. The kind discriminant selects the
    domain; it never enters the digested value, because the four domains are
    already disjoint.
    """
    return v1.digest(SUBJECT_DOMAINS[_require_kind(kind)], dict(projection))


def _require_kind(kind: str) -> str:
    if kind not in SUBJECT_DOMAINS:
        raise ValueError(f"{kind!r} is not one of the four receipt kinds {sorted(SUBJECT_DOMAINS)}")
    return kind


# --- the one receipt contract ------------------------------------------------


@dataclass(frozen=True)
class DerivationReceipt:
    """§7.5's receipt: one contract, four kinds, one domain.

    The five identity members are what the identity digests. The two
    projection-bearing members are the enumeration the retraction receipt
    carries and the inventory the certification receipt carries — §7.5 puts
    each *inside* its receipt rather than beside it as another epoch member.

    There is no semantic-identity member and no belief member, for any kind.
    The coreference receipt must carry neither (world-address ruling §5.3), and
    one contract across four kinds means the only honest way to guarantee that
    is a shape with nowhere to put one. What a receipt carries is the *subject*
    identity; whether that subject is a belief input is `BELIEF_INPUT_KIND`'s
    answer, read from the kind and never stored.
    """

    kind: str
    subject_identity: str
    corpus_states: tuple[tuple[str, str], ...]
    rule_identity: str
    implementation_identity: str
    enumeration: Mapping[str, object] | None = None
    inventory: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"{self.kind!r} is not one of {sorted(_KINDS)}")
        _require_lower_hex(self.subject_identity, 64, "subject_identity")
        _require_lower_hex(self.rule_identity, 64, "rule_identity")
        _require_lower_hex(self.implementation_identity, 64, "implementation_identity")
        if type(self.corpus_states) is not tuple:
            raise TypeError("corpus_states must be an exact tuple")
        for pair in self.corpus_states:
            if type(pair) is not tuple or len(pair) != 2:
                raise TypeError("a corpus state is an exact (corpus_id, corpus_state) pair")
            _require_text(pair[0], "corpus_id")
            _require_lower_hex(pair[1], 64, "corpus_state")
        if list(self.corpus_states) != sorted(self.corpus_states):
            raise ValueError("corpus_states is sorted; §7.5's identity formula names sorted pairs")
        if len({corpus_id for corpus_id, _state in self.corpus_states}) != len(self.corpus_states):
            raise ValueError("corpus_states names one corpus twice")
        self._require_projection(self.enumeration, "enumeration", "retraction-enumeration")
        self._require_projection(self.inventory, "inventory", "certification-enumeration")

    def _require_projection(self, value: object, member: str, kind: str) -> None:
        """A projection member is carried by exactly the kind whose subject it
        is. A producer receipt holding an enumeration and a retraction receipt
        holding none are the same fault: a document whose keys are not the
        closed set `epoch.RECEIPT_KEYS` declares for its member."""
        if (value is not None) != (self.kind == kind):
            raise ValueError(f"a {self.kind!r} receipt carries {member!r} iff its kind is {kind!r}")

    @property
    def member(self) -> str:
        """The §6.1 epoch member this receipt is written to."""
        return _MEMBERS[self.kind]

    def identity(self) -> str:
        """§7.5's receipt identity, over the five members that fix what ran."""
        return epoch.receipt_identity(
            self.kind,
            self.subject_identity,
            self.corpus_states,
            self.rule_identity,
            self.implementation_identity,
        )


_MEMBERS: Mapping[str, str] = MappingProxyType({kind: member for member, kind in epoch.RECEIPT_KINDS.items()})
_KINDS: frozenset[str] = frozenset(_MEMBERS)


def derivation_receipts(
    *,
    snapshot: ProducerSnapshot,
    enumeration: RetractionEnumeration,
    inventory: CertificationInventory,
    coreference: CoreferenceMap,
    corpus_states: Sequence[tuple[str, str]],
    bindings: Mapping[str, tuple[str, str]],
) -> tuple[DerivationReceipt, ...]:
    """The four receipts of one epoch, in §6.1's member order.

    One `corpus_states` argument for all four, because §7.5 requires that all
    four carry identical per-corpus states within one epoch. Passing it once is
    how that stops being a convention a publisher has to remember.

    `bindings` maps each receipt kind to the exact
    `(rule_identity, implementation_identity)` that ran. Exactly the four kinds
    are required: a build that resolved three bindings has not derived an
    epoch.

    The three subjects that declare a coverage must declare *this* epoch's, and
    the states must name exactly the corpora they cover. §7.5 says a receipt
    carries "the exact captured corpus-state identity for every covered
    corpus", so a snapshot declaring one coverage beside states naming another
    is a receipt whose two halves describe two builds. The check costs nothing
    and Task 9 derives both from one `Capture`; it exists so that the invariant
    is the type's rather than the publisher's to remember.
    """
    if set(bindings) != _KINDS:
        raise ValueError(f"one binding per receipt kind is required; got {sorted(bindings)}")
    states = tuple(sorted((corpus_id, corpus_state) for corpus_id, corpus_state in corpus_states))
    covered = tuple(corpus_id for corpus_id, _state in states)
    for declared, what in (
        (snapshot.coverage, "the producer snapshot"),
        (enumeration.coverage, "the retraction enumeration"),
        (inventory.coverage, "the certification inventory"),
    ):
        if tuple(sorted(declared)) != covered:
            raise ValueError(
                f"{what} declares coverage {sorted(declared)}, but the captured states name {list(covered)}"
            )
    subjects: Mapping[str, tuple[str, Mapping[str, object] | None, Mapping[str, object] | None]] = {
        "producer": (snapshot.identity(), None, None),
        "retraction-enumeration": (
            retraction_enumeration_identity(enumeration),
            MappingProxyType(retraction_enumeration_projection(enumeration)),
            None,
        ),
        "certification-enumeration": (inventory.identity(), None, MappingProxyType(inventory.projection())),
        "coreference-reduction": (coreference.identity(), None, None),
    }
    return tuple(
        DerivationReceipt(
            kind=kind,
            subject_identity=subjects[kind][0],
            corpus_states=states,
            rule_identity=bindings[kind][0],
            implementation_identity=bindings[kind][1],
            enumeration=subjects[kind][1],
            inventory=subjects[kind][2],
        )
        for member in epoch.EPOCH_MEMBERS
        if (kind := epoch.RECEIPT_KINDS.get(member)) is not None
    )


def belief_input_identity(receipts: Sequence[DerivationReceipt]) -> str:
    """The one belief input an epoch contributes: its producer snapshot
    identity (§7.3).

    A receipt set without exactly one producer receipt has no answer, and
    inventing one would be exactly the fold §7.5 forbids — packaging, receipt
    and corpus-state identities are not belief.
    """
    producers = [receipt for receipt in receipts if receipt.kind == BELIEF_INPUT_KIND]
    if len(producers) != 1:
        raise ValueError(f"exactly one {BELIEF_INPUT_KIND!r} receipt carries the belief input; found {len(producers)}")
    return producers[0].subject_identity


# --- shared checks -----------------------------------------------------------


def _require_text(value: object, location: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{location} is nonempty text")
    return value


def _require_lower_hex(value: object, length: int, location: str) -> str:
    if type(value) is not str or len(value) != length or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{location} must be {length} lowercase hexadecimal characters")
    return value


def _require_text_members(values: object, location: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{location} must be an exact tuple")
    members: tuple[object, ...] = values
    return tuple(_require_text(member, f"a member of {location}") for member in members)


def _require_distinct_text(values: object, location: str) -> tuple[str, ...]:
    """Distinctness is refused where the corpus already refuses it. A record
    may hold one `produces` edge twice — two identical stored relations are a
    corpus nobody tidied, not a corrupt one, and the enumeration counts the
    edge once — but a repeated `deprecated_ids` entry is refused at import
    (`corpus._validate_import_bundle`), so a capture holding one is corrupt."""
    members = _require_text_members(values, location)
    if len(set(members)) != len(members):
        raise ValueError(f"{location} repeats a member")
    return members


def _require_ordered(values: Sequence[str] | Sequence[tuple[str, str]], location: str) -> None:
    """§7.6's projections are sorted, so a rule that returned them unsorted
    returned a different projection — and a different identity for the same
    derivation. Sorting the return here instead would hide that."""
    if list(values) != sorted(values):
        raise RuleNonconformant(f"{location} are not sorted")


def _closed(value: object, keys: tuple[str, ...], what: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise RuleNonconformant(f"{what} is a mapping, not {type(value).__name__}")
    document: dict[object, object] = value
    if any(type(key) is not str for key in document):
        raise RuleNonconformant(f"{what} has a key that is not text")
    member = {str(key): held for key, held in document.items()}
    if tuple(sorted(member)) != keys:
        raise RuleNonconformant(f"{what} has exactly {list(keys)}; got {sorted(member)}")
    return member


def _members(value: object, location: str) -> Iterable[object]:
    if type(value) is not list:
        raise RuleNonconformant(f"{location} is a list, not {type(value).__name__}")
    return value


def _text(value: object, location: str) -> str:
    if type(value) is not str or not value:
        raise RuleNonconformant(f"{location} is nonempty text")
    return value


def _count(value: object, location: str) -> int:
    if type(value) is not int:
        raise RuleNonconformant(f"{location} is an integer, not {type(value).__name__}")
    return value


def _sorted_distinct(value: object, location: str) -> tuple[str, ...]:
    members = tuple(_text(member, f"a member of {location}") for member in _members(value, location))
    _require_ordered(list(members), location)
    if len(set(members)) != len(members):
        raise RuleNonconformant(f"{location} repeats a member")
    return members
