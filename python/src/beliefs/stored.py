"""The stored shape of a Science record — facet keys, relation predicates, and
the semantic hash over them.

Cuts 1–3 built the **values**: assessments, runs, datasets, verifications,
declarations. This module is the one place that says how such a value sits in a
`nodes` document, and how it is read back out of one. Two readers of the same
store disagreeing about which facet carries a run's spec is a corpus with two
meanings, so the mapping is code in one module rather than convention repeated
at each call site.

**Facet keys are unnamespaced.** They belong to the `science` base profile, not
to a domain contract (domain-extension boundary §3.4), and `empirical-observation`
is the one the eligibility predicate turns on.

**Relation predicates are kernel §4.1's closed signatures**, and the role-typed
inputs are stored as relations rather than as facet payload: they are edges the
substrate already resolves, and duplicating them inside a facet would create a
second answer to *what did this run observe*.

Two positions genuinely carry the same ref twice, and it is worth saying why
rather than tidying it away. An assessment's `assesses` and `produced_by` edges
are what the substrate resolves and what kernel §4.1 makes the guarantee out of;
its facet's `proposition` and `run` fields are what `(spec, run, proposition)`
digests. The builders below write both from one argument, so nothing this slice
mints can disagree with itself; a raw write that makes them disagree is an
untrusted import, subject to the same stated bound as every other one.

**The semantic hash covers a fixed set of facets per kind, named in code.** A
stored `covers` list would be data an untrusted writer could shorten, which is a
hash that certifies whatever it was pointed at. What is stored is the digest
alone; the coverage is `COVERED_FACETS`, and the projection records which
covered facets are **present**, so adding a governed facet to a stored node
without restamping is a disagreement rather than a silent extension.

**A governed kind must carry a stamp; a prose kind never has to** *(post-freeze
strengthening, adapter design review 2026-08-18)*. `SEMANTIC_DOMAINS` already
partitions the corpus: a kind with a semantic domain is minted stamped by the
boundary without exception, so an unstamped stored record of such a kind is a
raw write that skipped even self-stamping — statically detectable, and refused
(`semantic-hash-missing`) rather than admitted as the cheapest forgery. Kinds
with no semantic domain — every hand-authored prose node — carry no stamp
obligation. The recorded-history bound (substrate §4.2.1) is unchanged and
covers exactly what it says: fields and stamp moved *together* are undetectable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import report as report_values
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
from beliefs.errors import IdentityError, LoneSurrogate, MalformedRecord
from beliefs.holdings.records import (
    HOLDINGS_OBSERVATION_DOMAIN,
    HOLDINGS_OBSERVATION_KIND,
    Absent,
    Found,
    HoldingsObservation,
    StoreLocator,
)
from beliefs.identity import v1
from beliefs.record import AssessmentValue
from beliefs.verification import Verification

__all__ = [
    "ACCEPTED_EXTERNAL_IDENTIFIERS",
    "ASSESSMENT_FACET",
    "COORDINATION_FACET",
    "COVERED_FACETS",
    "DATASET_FACET",
    "DISPLAY_FACET",
    "EMPIRICAL_OBSERVATION_FACET",
    "GROUNDED_IN",
    "HOLDINGS_OBSERVATION_FACET",
    "LINEAGE_BASIS_FACET",
    "PROPOSITION_FACET",
    "RETRACTION_FACET",
    "RETRACTION_REASONS",
    "RETRACTS",
    "RUN_FACET",
    "SEMANTIC_DOMAINS",
    "SEMANTIC_IDENTITY_FACET",
    "SOURCE_FACET",
    "SUCCEEDED_BY",
    "SUPERSEDES",
    "VERIFICATION_FACET",
    "WORLD_KINDS",
    "WORLD_RELATIONS",
    "NodeTarget",
    "RouteTarget",
    "act_report_facet",
    "act_report_node",
    "assessment_value",
    "dataset_declaration",
    "display_facet_malformed",
    "display_statement",
    "external_identifiers",
    "holdings_observation_node",
    "holdings_observation_value",
    "is_empirical_observation",
    "lineage_basis",
    "recompute_semantic_hash",
    "retraction_node",
    "run_spec",
    "semantic_hash_disagrees",
    "semantic_hash_missing",
    "semantic_projection",
    "stamp_semantic_identity",
    "stored_semantic_hash",
    "union_lineage_bases",
    "used_facet_namespaces",
    "verification_derivation",
    "verification_value",
]

# --- the facet vocabulary ----------------------------------------------------

SEMANTIC_IDENTITY_FACET = "semantic-identity"
EMPIRICAL_OBSERVATION_FACET = "empirical-observation"
PROPOSITION_FACET = "proposition"
ASSESSMENT_FACET = "assessment"
RUN_FACET = "run"
RUN_CLOSURE_FACET = "run-closure"
DATASET_FACET = "dataset"
DISPLAY_FACET = "display"
LINEAGE_BASIS_FACET = "lineage-basis"
SOURCE_FACET = "source"
VERIFICATION_FACET = "verification"
RETRACTION_FACET = "retraction"
HOLDINGS_OBSERVATION_FACET = "holdings-observation"
COORDINATION_FACET = "coordination"


def used_facet_namespaces(node: Node) -> frozenset[str]:
    """The domain namespaces named by this node's namespaced facet keys."""
    return frozenset(key.partition("/")[0] for key in node.facets if "/" in key)

# --- kernel §4.1's closed relation signatures --------------------------------

ASSESSES = "assesses"
PRODUCED_BY = "produced_by"
EXECUTES = "executes"
OBSERVES = "observes"
READS = "reads"
TRANSFORMS = "transforms"
PRODUCES = "produces"
TARGETS = "targets"
VERIFIES = "verifies"
ANCHORED_IN = "anchored_in"
MEMBER_OF = "member_of"
SUPERSEDES = "supersedes"
RETRACTS = "retracts"
GROUNDED_IN = "grounded-in"
SUCCEEDED_BY = "succeeded-by"

WORLD_KINDS = (
    "proposition",
    "source-assertion",
    "assessment",
    "analysis-spec",
    "run",
    "verification",
    "dataset",
    "source",
    "holdings-observation",
    "retraction",
    "instrument-certification",
    "coreference-attestation",
    "act-report",
)
WORLD_RELATIONS = (
    ASSESSES,
    OBSERVES,
    READS,
    TRANSFORMS,
    PRODUCES,
    PRODUCED_BY,
    EXECUTES,
    TARGETS,
    VERIFIES,
    MEMBER_OF,
    GROUNDED_IN,
)

RETRACTION_REASONS = (
    "authored-error",
    "corrupt-input",
    "defective-code",
    "environment-miscapture",
    "false-certification",
    "upstream-retraction",
    "wrong-route",
)

INPUT_ROLES = (OBSERVES, READS, TRANSFORMS)
"""The role partition. `observes` confers eligibility; `reads` never does, in
any quantity; `transforms` is dataset-production lineage input."""

ACCEPTED_EXTERNAL_IDENTIFIERS = ("accession", "doi", "isbn", "pmid")
"""W3's accepted external identifiers for a `source`. A closed set: a fallback
derived from title and year is exactly the coercion the row refuses."""

SEMANTIC_DOMAINS: Mapping[str, str] = {
    "act-report": report_values.ACT_REPORT_DOMAIN,
    "analysis-spec": "science.analysis-spec.v1",
    "assessment": "science.assessment.v1",
    "dataset": "science.dataset.v1",
    HOLDINGS_OBSERVATION_KIND: HOLDINGS_OBSERVATION_DOMAIN,
    "proposition": "science.proposition.v1",
    "retraction": "science.retraction.v1",
    "run": "science.run.v1",
    "source": "science.source.v1",
    "source-assertion": "science.source-assertion.v1",
    "verification": "science.verification.v1",
}

COVERED_FACETS: Mapping[str, tuple[str, ...]] = {
    "act-report": ("act-report",),
    "analysis-spec": ("analysis-spec",),
    "assessment": (ASSESSMENT_FACET,),
    "dataset": (DATASET_FACET, EMPIRICAL_OBSERVATION_FACET, LINEAGE_BASIS_FACET),
    HOLDINGS_OBSERVATION_KIND: (HOLDINGS_OBSERVATION_FACET,),
    "proposition": (PROPOSITION_FACET,),
    "retraction": (RETRACTION_FACET,),
    "run": (RUN_FACET, RUN_CLOSURE_FACET),
    "source": (SOURCE_FACET,),
    "source-assertion": ("source-assertion",),
    "verification": (VERIFICATION_FACET,),
}
"""Which facets the semantic hash governs, per kind. Prose — `title`, `body`,
an authored `display_statement` — is deliberately outside every entry: it is
hand-editable by rule, and a hash covering it would refuse an editorial fix."""


# --- the semantic hash -------------------------------------------------------


def semantic_projection(node: Node) -> dict[str, Any]:
    """What the semantic hash is taken over: the kind, which covered facets are
    present, and their payloads. Never the id or the uid — a rename preserves
    semantics by rule, and a hash that moved under one would refuse it."""
    covered = COVERED_FACETS.get(node.kind, ())
    present = [name for name in covered if name in node.facets]
    return {
        "kind": node.kind,
        "present": present,
        "facets": {name: node.facets[name] for name in present},
    }


def recompute_semantic_hash(node: Node) -> str:
    """The hash the node's stored fields say it should carry."""
    domain = SEMANTIC_DOMAINS.get(node.kind)
    if domain is None:
        raise MalformedRecord(f"kind {node.kind!r} has no semantic-identity domain")
    return v1.digest(domain, semantic_projection(node))


def stored_semantic_hash(node: Node) -> str | None:
    """The stamp as stored, or `None` when the node carries none."""
    facet = node.facets.get(SEMANTIC_IDENTITY_FACET)
    if not isinstance(facet, dict):
        return None
    digest = facet.get("digest")
    return digest if isinstance(digest, str) else None


def semantic_hash_disagrees(node: Node) -> bool:
    """`True` when the stamp and the stored fields disagree. An unstamped node
    is not a disagreement — `semantic_hash_missing` is the separate question of
    whether it was allowed to be unstamped."""
    stored = stored_semantic_hash(node)
    return stored is not None and stored != recompute_semantic_hash(node)


def semantic_hash_missing(node: Node) -> bool:
    """`True` when a governed kind carries no stamp at all. Prose kinds have no
    semantic domain and are never reported — see the module docstring."""
    return node.kind in SEMANTIC_DOMAINS and stored_semantic_hash(node) is None


def stamp_semantic_identity(node: Node) -> Node:
    """Stamp `node` in place with the hash its fields recompute to, and return
    it. The one construction authority for the stamp: a caller computing it
    itself is a second implementation of the predicate the read path checks."""
    node.facets[SEMANTIC_IDENTITY_FACET] = {"digest": recompute_semantic_hash(node)}
    return node


# --- reading values back out of stored documents -----------------------------


def _facet(node: Node, key: str) -> Mapping[str, Any] | None:
    payload = node.facets.get(key)
    return payload if isinstance(payload, dict) else None


def is_empirical_observation(node: Node) -> bool:
    """Whether a dataset carries the facet an `observes` input demands. The
    facet's own payload contract is open (kernel §11); its **presence** is what
    the eligibility predicate reads, and that is all this asks."""
    return _facet(node, EMPIRICAL_OBSERVATION_FACET) is not None


def external_identifiers(node: Node) -> tuple[str, ...]:
    """The accepted external identifiers a `source` carries, sorted. Empty is
    W3's refusal case at the write boundary."""
    facet = _facet(node, SOURCE_FACET) or {}
    identifiers = facet.get("identifiers")
    if not isinstance(identifiers, dict):
        return ()
    return tuple(
        sorted(
            name
            for name in ACCEPTED_EXTERNAL_IDENTIFIERS
            if isinstance(identifiers.get(name), str) and identifiers[name]
        )
    )


def dataset_declaration(node: Node) -> DatasetDeclaration:
    """The stored declaration as cut 2's value. A resource with no digest stays
    unpinned rather than being dropped: `dataset_address` is all-or-nothing, and
    silently discarding the unpinned resource would manufacture an address the
    record does not have."""
    facet = _facet(node, DATASET_FACET) or {}
    resources = facet.get("resources")
    if not isinstance(resources, list):
        return DatasetDeclaration(resources=())
    declared: list[ResourceDeclaration] = []
    for entry in resources:
        if not isinstance(entry, dict):
            raise MalformedRecord(f"{node.id}: a declared resource is not an object")
        digest = entry.get("digest")
        declared.append(
            ResourceDeclaration(
                name=str(entry.get("name", "")),
                digest=digest if isinstance(digest, str) else None,
            )
        )
    return DatasetDeclaration(resources=tuple(declared))


def run_spec(node: Node) -> str | None:
    facet = _facet(node, RUN_FACET) or {}
    spec = facet.get("spec")
    return spec if isinstance(spec, str) else None


def display_facet_malformed(node: Node) -> bool:
    """Whether an authored display facet is not its exact one-field shape."""
    if DISPLAY_FACET not in node.facets:
        return False
    facet = node.facets[DISPLAY_FACET]
    return not (
        isinstance(facet, dict)
        and set(facet) == {"display_statement"}
        and isinstance(facet["display_statement"], str)
    )


def display_statement(node: Node) -> str | None:
    """The authored display prose, or `None` when it is absent or malformed."""
    if display_facet_malformed(node):
        return None
    facet = node.facets.get(DISPLAY_FACET)
    return None if facet is None else facet["display_statement"]


def inputs_of(node: Node, role: str) -> tuple[str, ...]:
    """The dataset refs a run names under one input role, in stored order."""
    return tuple(relation.target for relation in node.relations if relation.predicate == role)


def assessment_value(node: Node) -> AssessmentValue:
    """The stored assessment as cut 2's value — `(spec, run, proposition)` and
    the facet kernel §4.2.1 tables. Absent optionals stay absent."""
    facet = _facet(node, ASSESSMENT_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: an assessment carries an {ASSESSMENT_FACET!r} facet")
    optional = {
        name: facet[name]
        for name in ("estimate", "uncertainty", "estimand", "applicability")
        if isinstance(facet.get(name), str)
    }
    return AssessmentValue(
        spec=str(facet.get("spec", "")),
        run=str(facet.get("run", "")),
        proposition=str(facet.get("proposition", "")),
        outcome=str(facet.get("outcome", "")),
        interpretation_rule=str(facet.get("interpretation_rule", "")),
        **optional,
    )


def verification_value(node: Node) -> Verification:
    facet = _facet(node, VERIFICATION_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a verification carries a {VERIFICATION_FACET!r} facet")
    supersedes = facet.get("supersedes")
    return Verification(
        ref=node.id,
        assessment=str(facet.get("assessment", "")),
        scope=str(facet.get("scope", "")),
        verdict=str(facet.get("verdict", "")),
        supersedes=supersedes if isinstance(supersedes, str) else None,
    )


def verification_derivation(node: Node) -> tuple[str, str] | None:
    """The two run refs a stored verification names, or `None` when it names
    none. Refuses a malformed member rather than repairing it (M11): a
    derivation that cannot be read is not a derivation that reads as absent."""
    facet = _facet(node, VERIFICATION_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a verification carries a {VERIFICATION_FACET!r} facet")
    member = facet.get("derivation")
    if member is None:
        return None
    if not isinstance(member, Mapping) or set(member) != {"original", "replayed"}:
        raise MalformedRecord(f"{node.id}: a derivation member names exactly `original` and `replayed`")
    original, replayed = member["original"], member["replayed"]
    if (
        type(original) is not str
        or type(replayed) is not str
        or not original.startswith("run:")
        or not replayed.startswith("run:")
    ):
        raise MalformedRecord(f"{node.id}: derivation runs are `run:` refs")
    return original, replayed


def lineage_basis(node: Node) -> Mapping[str, Any] | None:
    """The stamped descendant-side basis, as stored. `None` when the dataset
    carries none — an authored dataset with no producing run."""
    return _facet(node, LINEAGE_BASIS_FACET)


def _tagged_basis_routes(node: Node) -> list[dict[str, Any]]:
    basis = node.facets.get(LINEAGE_BASIS_FACET)
    if basis is None:
        return []
    if not isinstance(basis, dict) or set(basis) != {"tag", "routes"}:
        raise MalformedRecord(f"{node.id}: malformed tagged lineage basis")
    tag, routes = basis["tag"], basis["routes"]
    if tag not in ("single", "conflict") or not isinstance(routes, list) or not all(
        isinstance(route, dict) for route in routes
    ):
        raise MalformedRecord(f"{node.id}: malformed tagged lineage basis")
    try:
        keys = [v1.encode(route) for route in routes]
    except IdentityError as caught:
        raise MalformedRecord(f"{node.id}: malformed lineage route") from caught
    if tag == "single" and len(routes) != 1:
        raise MalformedRecord(f"{node.id}: a single lineage basis holds exactly one route")
    if tag == "conflict" and (
        len(routes) < 2 or len(set(keys)) != len(keys) or keys != sorted(keys)
    ):
        raise MalformedRecord(
            f"{node.id}: a conflict lineage basis holds at least two distinct sorted routes"
        )
    return routes


def union_lineage_bases(survivor: Node, loser: Node) -> dict[str, dict]:
    """Keep survivor facets and replace only its lineage basis with the union."""
    encoded_routes = {
        v1.encode(route)
        for node in (survivor, loser)
        for route in _tagged_basis_routes(node)
    }
    facets = dict(survivor.facets)
    if encoded_routes:
        ordered = []
        for encoded in sorted(encoded_routes):
            route = v1.decode(encoded)
            if not isinstance(route, dict):
                raise MalformedRecord("a canonical lineage route is not an object")
            ordered.append(route)
        facets[LINEAGE_BASIS_FACET] = {
            "tag": "single" if len(ordered) == 1 else "conflict",
            "routes": ordered,
        }
    return facets


def basis_routes(node: Node) -> tuple[Mapping[str, Any], ...]:
    """The basis's routes in stored order, so a route's **position** is stable
    for the traversal's unresolved entries."""
    facet = lineage_basis(node)
    if facet is None:
        return ()
    routes = facet.get("routes")
    if not isinstance(routes, list):
        return ()
    return tuple(route for route in routes if isinstance(route, dict))


def holdings_observation_value(node: Node) -> HoldingsObservation:
    facet = _facet(node, HOLDINGS_OBSERVATION_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a holdings observation carries a {HOLDINGS_OBSERVATION_FACET!r} facet")
    try:
        location = facet["location"]
        outcome = facet["outcome"]
        if not isinstance(location, dict) or set(location) != {"type", "store_id", "relative_path"}:
            raise MalformedRecord("a holdings observation location is a store locator")
        if location["type"] != "store":
            raise MalformedRecord("a holdings observation location is a store locator")
        if not isinstance(outcome, dict):
            raise MalformedRecord("a holdings observation outcome is a finding")
        if outcome.get("finding") == "found" and set(outcome) == {"finding", "digest"}:
            finding = Found(outcome["digest"])
        elif outcome.get("finding") == "absent" and set(outcome) == {"finding"}:
            finding = Absent()
        else:
            raise MalformedRecord("a holdings observation outcome is a finding")
        value = HoldingsObservation(
            location=StoreLocator(location["store_id"], location["relative_path"]),
            outcome=finding,
            expected=facet.get("expected"),
            observer=facet["observer"],
            instrument=facet["instrument"],
            event_token=facet["event_token"],
            observed_at=facet["observed_at"],
            supersedes=tuple(facet["supersedes"]),
        )
    except (KeyError, TypeError) as exc:
        raise MalformedRecord(f"{node.id}: a holdings observation facet is malformed") from exc
    if value.facet() != facet:
        raise MalformedRecord(f"{node.id}: a holdings observation facet is malformed")
    return value


_REPORT_ENTRY_OUTCOMES: dict[str, dict[str, tuple[str, ...]]] = {
    "pure-look": {
        "published-observation": ("ref",),
        "byte-locator-untested": ("reason",),
        "retrieval-failed": ("reason",),
    },
    "managed-mutation": {"published-observation": ("ref",)},
    "declaration-pin": {"pinned-declaration": ("ref",)},
    "subject-evaluation": {"evaluation-finding": ("payload",)},
    "record-import": {"imported-records": ("refs", "findings")},
    "record-mutation": {
        "moved": ("source_corpus", "destination_corpus", "ref"),
        "consolidated": (
            "kept_corpus",
            "kept_ref",
            "other_corpus",
            "other_ref",
            "retired_uids",
            "rationale",
        ),
    },
    "run-attempt": {"run-refusal": ("missing_member",)},
}


def _valid_report_entry(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    kind = entry.get("kind")
    if type(kind) is not str:
        return False
    expected_entry_fields = {
        "kind",
        "subject",
        "outcome",
        *(("instrument_inputs",) if kind == "pure-look" else ()),
        *(("corpus",) if kind == "record-mutation" else ()),
    }
    if (
        set(entry) != expected_entry_fields
        or type(entry.get("subject")) is not str
        or (kind == "record-mutation" and type(entry.get("corpus")) is not str)
    ):
        return False
    if kind == "pure-look":
        inputs = entry["instrument_inputs"]
        if not isinstance(inputs, list) or any(
            not isinstance(pair, list)
            or len(pair) != 2
            or any(type(member) is not str for member in pair)
            for pair in inputs
        ):
            return False
    outcomes = _REPORT_ENTRY_OUTCOMES.get(kind)
    outcome = entry.get("outcome")
    if outcomes is None or not isinstance(outcome, dict):
        return False
    outcome_type = outcome.get("type")
    if type(outcome_type) is not str:
        return False
    fields = outcomes.get(outcome_type)
    if fields is None or set(outcome) != {"type", *fields}:
        return False
    for field in fields:
        value = outcome[field]
        if outcome_type == "imported-records" or field == "retired_uids":
            if not isinstance(value, list) or any(
                type(member) is not str for member in value
            ):
                return False
        elif type(value) is not str:
            return False
    return True


def act_report_facet(node: Node) -> Mapping[str, Any]:
    """Validate and return the one stored act-report facet."""
    facet = node.facets.get("act-report")
    required = {
        "operation",
        "event_token",
        "actor",
        "observer",
        "instrument",
        "opened_at",
        "closed_at",
        "entries",
    }
    if (
        not isinstance(facet, dict)
        or set(node.facets) != {"act-report", SEMANTIC_IDENTITY_FACET}
        or set(facet) != required
        or facet.get("operation") not in report_values.OPERATION_KINDS
        or any(type(facet.get(name)) is not str for name in required - {"entries"})
        or not isinstance(facet.get("entries"), list)
        or node.relations
    ):
        raise MalformedRecord(f"{node.id}: malformed act-report facet")
    if any(not _valid_report_entry(entry) for entry in facet["entries"]):
        raise MalformedRecord(f"{node.id}: malformed act-report entry")
    try:
        expected = v1.digest(report_values.ACT_REPORT_DOMAIN, facet)
    except IdentityError as caught:
        raise MalformedRecord(f"{node.id}: malformed act-report facet") from caught
    if node.id != f"act-report:{expected}":
        raise MalformedRecord(
            f"{node.id}: act-report address disagrees with its identity"
        )
    return facet


# --- constructing stored documents -------------------------------------------


@dataclass(frozen=True)
class NodeTarget:
    ref: str
    resolved: str
    content_identity: str


@dataclass(frozen=True)
class RouteTarget:
    dataset: str
    resolved: str
    content_identity: str
    route_identity: str


def _node(kind: str, slug: str, title: str, facets: Mapping[str, Any], relations: Sequence[Relation]) -> Node:
    node = Node(id=f"{kind}:{slug}", kind=kind, title=title, facets=dict(facets), relations=list(relations))
    return stamp_semantic_identity(node)


def act_report_node(report: report_values.ActReport) -> Node:
    if type(report) is not report_values.ActReport:
        raise MalformedRecord("act_report_node requires an ActReport")
    facet = dict(vars(report))
    facet["entries"] = [report_values._entry_facet(entry) for entry in report.entries]
    try:
        slug = report.identity()
    except LoneSurrogate as exc:
        raise MalformedRecord("an act report identity field is not canonically encodable") from exc
    return _node("act-report", slug, f"{report.operation} report", {"act-report": facet}, ())


def proposition_node(
    slug: str, *, title: str, claim: Mapping[str, Any], display_statement: str | None = None
) -> Node:
    """A proposition carrying the typed claim projection. Prose is not an
    identity input: `title` and an authored display statement are display only."""
    facets: dict[str, Any] = {PROPOSITION_FACET: dict(claim)}
    if display_statement is not None:
        facets[DISPLAY_FACET] = {"display_statement": display_statement}
    return _node("proposition", slug, title, facets, ())


def source_node(slug: str, *, title: str, identifiers: Mapping[str, str]) -> Node:
    return _node("source", slug, title, {SOURCE_FACET: {"identifiers": dict(identifiers)}}, ())


def dataset_node(
    slug: str,
    *,
    title: str,
    resources: Sequence[Mapping[str, Any]] = (),
    empirical_observation: Mapping[str, Any] | None = None,
    basis: Mapping[str, Any] | None = None,
) -> Node:
    facets: dict[str, Any] = {DATASET_FACET: {"resources": [dict(resource) for resource in resources]}}
    if empirical_observation is not None:
        facets[EMPIRICAL_OBSERVATION_FACET] = dict(empirical_observation)
    if basis is not None:
        facets[LINEAGE_BASIS_FACET] = dict(basis)
    return _node("dataset", slug, title, facets, ())


def run_node(
    slug: str,
    *,
    title: str,
    spec: str,
    observes: Sequence[str] = (),
    reads: Sequence[str] = (),
    transforms: Sequence[str] = (),
    produces: Sequence[str] = (),
) -> Node:
    node_id = f"run:{slug}"
    relations = [
        Relation(source=node_id, predicate=predicate, target=target)
        for predicate, targets in (
            (OBSERVES, observes),
            (READS, reads),
            (TRANSFORMS, transforms),
            (PRODUCES, produces),
        )
        for target in targets
    ]
    return _node("run", slug, title, {RUN_FACET: {"spec": spec}}, relations)


def run_publication_node(
    slug: str,
    *,
    title: str,
    projection: str,
    spec: str | None,
    observes: Sequence[str] = (),
    reads: Sequence[str] = (),
    transforms: Sequence[str] = (),
    produces: Sequence[str] = (),
) -> Node:
    """A boundary-published run with its canonical address preimage."""
    node_id = f"run:{slug}"
    relations = [
        Relation(source=node_id, predicate=predicate, target=target)
        for predicate, targets in (
            (OBSERVES, observes),
            (READS, reads),
            (TRANSFORMS, transforms),
            (PRODUCES, produces),
        )
        for target in targets
    ]
    run_facet: dict[str, Any] = {} if spec is None else {"spec": spec}
    facets = {
        RUN_FACET: run_facet,
        RUN_CLOSURE_FACET: {"projection": projection},
    }
    return _node("run", slug, title, facets, relations)


def assessment_node(
    slug: str,
    *,
    title: str,
    spec: str,
    run: str,
    proposition: str,
    # `proposition` and `run` are corpus refs: the address of the record, which
    # is what a corpus-local reader can resolve. The claim identity itself lives
    # on the proposition node, in its own facet.
    outcome: str,
    interpretation_rule: str,
    **optional: str,
) -> Node:
    node_id = f"assessment:{slug}"
    facet: dict[str, Any] = {
        "spec": spec,
        "run": run,
        "proposition": proposition,
        "outcome": outcome,
        "interpretation_rule": interpretation_rule,
        **optional,
    }
    relations = [
        Relation(source=node_id, predicate=ASSESSES, target=proposition),
        Relation(source=node_id, predicate=PRODUCED_BY, target=run),
    ]
    return _node("assessment", slug, title, {ASSESSMENT_FACET: facet}, relations)


def verification_node(
    slug: str,
    *,
    title: str,
    assessment: str,
    assessment_ref: str,
    scope: str,
    verdict: str,
    supersedes: str | None = None,
    derivation: tuple[str, str] | None = None,
) -> Node:
    """`assessment` is the assessment **identity** the verification is about —
    what cut 2's lifecycle table matches on — and `assessment_ref` is the corpus
    address the `verifies` edge binds. The two are different facts: an identity
    survives a corpus that never held the record, and an address does not.

    `derivation` names the two runs the verdict was derived from, so a later
    audit can recompute it. It is optional because a stored verification that
    names neither is not malformed — it is simply one the audit cannot check."""
    facet: dict[str, Any] = {"assessment": assessment, "scope": scope, "verdict": verdict}
    if supersedes is not None:
        facet["supersedes"] = supersedes
    if derivation is not None:
        facet["derivation"] = {"original": derivation[0], "replayed": derivation[1]}
    return _node(
        "verification",
        slug,
        title,
        {VERIFICATION_FACET: facet},
        [Relation(source=f"verification:{slug}", predicate=VERIFIES, target=assessment_ref)],
    )


def retraction_node(
    *,
    title: str,
    target: NodeTarget | RouteTarget,
    reason: str,
    rationale: str,
    grounds: Sequence[str],
    actor: str,
    event_token: str,
    successor: str | None = None,
) -> Node:
    if isinstance(target, NodeTarget):
        target_mapping = {
            "arm": "node",
            "ref": target.ref,
            "resolved": target.resolved,
            "content_identity": target.content_identity,
        }
        target_ref = target.ref
    elif isinstance(target, RouteTarget):
        target_mapping = {
            "arm": "route",
            "dataset": target.dataset,
            "resolved": target.resolved,
            "content_identity": target.content_identity,
            "route_identity": target.route_identity,
        }
        target_ref = target.dataset
    else:
        raise MalformedRecord("a retraction target arm is NodeTarget or RouteTarget")
    if not all(type(value) is str and value for value in target_mapping.values()):
        raise MalformedRecord("a retraction target carries non-empty string fields")
    if type(reason) is not str:
        raise MalformedRecord("a retraction reason is a string")
    if reason not in RETRACTION_REASONS:
        raise MalformedRecord(f"retraction reason {reason!r} is outside the closed set {RETRACTION_REASONS}")
    if type(rationale) is not str or not rationale:
        raise MalformedRecord("a retraction rationale is a non-empty string")
    if isinstance(grounds, (str, bytes)) or not isinstance(grounds, Sequence):
        raise MalformedRecord("a retraction's grounds are a sequence of references")
    grounds_list = list(grounds)
    if not grounds_list or not all(type(ground) is str and ground for ground in grounds_list):
        raise MalformedRecord("a retraction names at least one string ground reference")
    if type(actor) is not str or not actor or type(event_token) is not str or not event_token:
        raise MalformedRecord("a retraction carries actor and event attribution")
    if successor is not None and (type(successor) is not str or not successor):
        raise MalformedRecord("a retraction successor is a string reference when present")

    facet: dict[str, Any] = {
        "target": target_mapping,
        "reason": reason,
        "rationale": rationale,
        "grounds": grounds_list,
        "actor": actor,
        "event_token": event_token,
    }
    if successor is not None:
        facet["successor"] = successor
    try:
        slug = v1.digest("science.retraction.v1", facet)
    except LoneSurrogate as exc:
        raise MalformedRecord("a retraction identity field is not canonically encodable") from exc
    node_id = f"retraction:{slug}"
    relations = [Relation(source=node_id, predicate=RETRACTS, target=target_ref)]
    relations.extend(Relation(source=node_id, predicate=GROUNDED_IN, target=ground) for ground in grounds_list)
    if successor is not None:
        relations.append(Relation(source=node_id, predicate=SUCCEEDED_BY, target=successor))
    return _node("retraction", slug, title, {RETRACTION_FACET: facet}, relations)


def holdings_observation_node(observation: HoldingsObservation) -> Node:
    if type(observation) is not HoldingsObservation:
        raise MalformedRecord("holdings_observation_node requires a HoldingsObservation")
    slug = observation.identity()
    return _node(
        HOLDINGS_OBSERVATION_KIND,
        slug,
        f"Holdings observation {slug[:12]}",
        {HOLDINGS_OBSERVATION_FACET: observation.facet()},
        (),
    )
