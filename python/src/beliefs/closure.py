"""The belief input closure and its digest (kernel §5.1, G3, P3).

**"A member is in the closure because something reads it"** (kernel §5.1) —
never because it is the tidiest description of the lineage. The projection
below is exactly `science.belief.v1`'s reads, and nothing else: a candidate
member that no evaluation step consults does not belong here, and a member
the evaluation reads but this projection omits is a digest that cannot move
when that read's answer does (G3).

**Membership is computed from what the caller supplies as records, not
enumerated by the caller** (cut 2 §3): the `assessment_facets`,
`propositions`, `verifications` and `observes` members are built by filtering
`assessments`, `runs` and `verifications` down to `proposition` — never
handed in pre-filtered, so a record that should have entered cannot be
withheld by a caller's omission and still leave a passing digest (the N2
concern this closure exists to close). The remaining members — the lineage
snapshot's projection, the producer-snapshot identity, the retraction
enumeration, the policy binding, the consulted-contract pairs — are supplied
as already-computed values: this module digests them, it does not compute
them (the consulted walk is task 6's, independence certification is task 8's).

Source assertions have no parameter here at all. Nothing filters, projects or
digests a `SourceAssertion` — that absence is G1's digest half, and the N2
sabotage that reintroduces one is what it must be caught by.

Heldness is **not** a member: it selects the shape of the evaluator's answer
(whether a `held`-eligible input is even available to weigh), never the
answer's value, so it has nothing here to be a read of (G3's arm restriction,
ρA8).

`binding` is a plain `(rule identity, implementation identity)` pair, not
`PolicyBinding` — that type arrives in task 8. This module digests the pair;
the evaluator owns the type and passes `(binding.rule, binding.implementation)`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.dataset import dataset_address
from beliefs.identity import v1
from beliefs.lineage import LineageSnapshot, snapshot_projection
from beliefs.record import AssessmentValue, RunValue
from beliefs.sealed import sealed
from beliefs.verification import Verification, active

__all__ = ["BELIEF_INPUT_DOMAIN", "Closure", "RetractionEnumeration", "build_closure"]

BELIEF_INPUT_DOMAIN = "science.belief-input.v1"


@sealed
@final
@dataclass(frozen=True)
class RetractionEnumeration:
    """A supplied closure member: the retraction search's result, as already
    resolved by its caller. `found` is `(ref, resolution)` pairs; `coverage`
    is the searched scope's declaration. Neither is computed here — an
    enumeration is only as good as its stated scope, and both halves travel
    together into the digest."""

    found: tuple[tuple[str, str], ...]
    coverage: tuple[str, ...]


@sealed
@final
@dataclass(frozen=True)
class Closure:
    """The belief input closure: an already encoder-ready projection (lists,
    not tuples; no `None` anywhere) and its digest."""

    projection: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection", MappingProxyType(dict(self.projection)))

    def digest(self) -> str:
        return v1.digest(BELIEF_INPUT_DOMAIN, dict(self.projection))


def build_closure(
    *,
    proposition: str,
    assessments: tuple[AssessmentValue, ...],
    runs: Mapping[str, RunValue],
    verifications: tuple[Verification, ...],
    snapshot: LineageSnapshot,
    producer_snapshot_identity: str,
    retractions: RetractionEnumeration,
    consulted: tuple[tuple[str, str], ...],
    binding: tuple[str, str],
) -> Closure:
    """Build the closure over one proposition's belief inputs (kernel §5.1's
    projection table).

    Computed from the record pool, filtered to `proposition`:

    * `assessment_facets` — `(identity, facet_digest)` pairs, sorted. The
      *pairing* is the member, not the bag of either half on its own (a keyed
      permutation must move the digest even when both bags stay identical).
    * `propositions` — the sorted claim identities of the matched assessments.
    * `verifications` — filtered to verifications naming a matched assessment,
      each row `(ref, scope, verdict, "active" | "superseded")`, sorted;
      "active" uses the same not-superseded rule as `verification.active`.
    * `observes` — the sorted dataset addresses of every `observes` input of
      every matched assessment's run. An address of `None` never enters: a
      curation-note observes input is already refused at the admission gate,
      and here it simply has nothing to digest.

    Supplied, not computed: `snapshot` (projected via `snapshot_projection`),
    `producer_snapshot_identity`, `retractions`, `consulted`, `binding`.
    """
    ours = tuple(a for a in assessments if a.proposition == proposition)
    identities = {a.identity() for a in ours}
    relevant_verifications = tuple(v for v in verifications if v.assessment in identities)
    active_refs = {v.ref for v in active(relevant_verifications)}

    assessment_facets = sorted((a.identity(), a.facet_digest()) for a in ours)
    propositions = sorted({a.proposition for a in ours})
    verification_rows = sorted(
        (v.ref, v.scope, v.verdict, "active" if v.ref in active_refs else "superseded") for v in relevant_verifications
    )
    observes = sorted(
        address
        for a in ours
        for run_input in runs[a.run].inputs
        if run_input.role == "observes"
        if (address := dataset_address(run_input.dataset)) is not None
    )

    projection: dict[str, object] = {
        "assessment_facets": [list(pair) for pair in assessment_facets],
        "propositions": list(propositions),
        "verifications": [list(row) for row in verification_rows],
        "observes": list(observes),
        "lineage": snapshot_projection(snapshot),
        "producer_snapshot": producer_snapshot_identity,
        "retractions": {
            "found": [list(pair) for pair in retractions.found],
            "coverage": list(retractions.coverage),
        },
        "policy_binding": list(binding),
        "consulted": [list(pair) for pair in consulted],
    }
    return Closure(projection=projection)
