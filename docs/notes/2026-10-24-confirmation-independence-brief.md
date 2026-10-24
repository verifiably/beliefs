# Independent confirmation and participant overlap

## Problem

`beliefs-a91959` asks how a belief distinguishes independent confirmation from
secondary analysis after data informed claim selection. `beliefs-6cd85f` asks how
participant overlap between separately held datasets reaches independence
certification. Both came from the same research program on 2026-10-18. Reuse
aggregation goal `beliefs-8060d0` and its research; these are related questions,
not interchangeable meanings of independence or implementation-ready changes.

## Current behaviour and evidence

Static evidence checked at main `18d5a35`, 2026-10-24; no runtime probe:

- `python/src/beliefs/belief.py` admits eligible assessments, derives pairwise
  dependency edges from observed dataset roots, then passes only assessment
  identities, directions and edges to `policy.aggregate_v1`. It has no built-in
  confirmation/secondary classification. Unit weights apply to directional
  eligible assessments, with dependency selection and contestation; the task's
  phrase "counts every admitted assessment alike" does not mean all are summed.
- Acceptance filtering already exists (`e7b1193`, `0cbfa7d`;
  `docs/superpowers/specs/2026-10-02-belief-acceptance-design.md`).
  `evaluation._AcceptanceSelection` calls `AcceptancePolicy.counts` with corpus
  id and canonical stored address. Its statement enters the closure digest;
  answers carry exclusions and completion. A caller could select a pinned
  externally classified set, but the kernel neither interprets that label nor
  proves that data were reserved before selection. Rejecting every assessment
  reaches `NoBelief("no-eligible-assessment")`, not a built-in "secondary only"
  reason. Existing coverage is in `python/tests/acceptance/test_belief_acceptance.py`.
- `python/src/beliefs/lineage.py:certify` returns `not-certified` for incomplete
  or divergent walks, `shared-source` for intersecting complete closures, and
  `independent` for disjoint complete closures. `python/tests/test_lineage.py`
  explicitly covers two distinct roots with no bases or producers as independent.
  Unrecorded participant overlap therefore need not yield `not-certified`.
  The reported GSE24080/GSE2658 outcome has not been reproduced here.
- Typed applicability is an operator-dimension qualifier map, not a free-form
  label slot (`spec.py`, `estimand.py`, adoption ledger cut 31). v1 does not read
  it for value. Existing inventory `beliefs-9bf498` already covers unread
  applicability and binary dependence; synthesis `beliefs-5e66ba` owns direction.

The source protocol section 12 and roster are not present in this fixed checkout.
The member bodies preserve the reported sample counts, 19 overlap records,
reserved-group convention and publication evidence; these remain source reports,
not independently checked facts. There is no attached draft spec or existing
local brief for this pair.

## Constraints

Preserve frozen cuts, exact policy bindings, receipts, acquisition-only empirical
standing and the distinction between `not-certified` and `shared-source`.
Participant disjointness does not establish freedom from selection exposure.
Publication statements about overlap need an explicit evidence/authority policy;
they must not become empirical support for the target claim merely by being stored.
Keep `beliefs-8ecbb5` (inherited standing) and `beliefs-638318` (weighted policy)
under their existing shelf conditions. This cluster does not gate the separately
tracked first science causal workflow. No shared-resource vocabulary is declared
in this checkout; this bounded static research needs no exclusive host resource.

## Alternatives

1. **Reuse current selection and investigate the missing semantics (lean).**
   Evaluate whether a pinned caller-side classification and acceptance statement
   suffice for confirmation-only reads; separately identify the governed evidence
   needed for participant overlap. This avoids assuming a new facet or policy.
2. **Add governed classification and overlap records.** This could make evidence
   discoverable and auditable, but needs rules for authority, conflicts,
   corrections, absent evidence and digest closure before choosing record kinds.
3. **Make a successor aggregation policy consume both.** It could vary eligibility
   or contribution, but currently lacks the evidence semantics and risks conflating
   methodological validity with pairwise dataset dependence. Do not start here.

## Unanswered questions

- Can current acceptance express the required confirmation-only answer, including
  secondary-only inputs, with a durable classification snapshot? Inventory
  `beliefs-9bf498` traces the seam; synthesis `beliefs-5e66ba` recommends ownership.
- Which reported overlap evidence is sufficient for shared, nested, disjoint or
  unknown pairs, and how do conflicts and retractions change certification and
  its digest? The inventory identifies what is missing; the synthesis identifies
  which questions require later reviewed design. The program owner must supply
  the protocol/roster before any recommendation claims to validate those cases.
- Does either case actually require a successor policy or inherited standing?
  The synthesis must answer explicitly rather than treating those shelves as
  automatic prerequisites. This brief approves neither new semantics nor a design.

## Proposed decomposition

- Reuse `beliefs-8060d0`; parent both previously unparented ideas there without
  changing their original bodies, priorities or sources.
- Reuse `beliefs-9bf498` (P2, small, mid, direct). Add the acceptance seam and
  distinct-root overlap counterexample to its existing information-loss inventory;
  name the unavailable source evidence, without an external study or new feature.
- Reuse `beliefs-5e66ba` (P2, small, high, direct). Within its existing synthesis,
  recommend selection versus governed-record versus successor-policy ownership
  for both cases, and separate answerable findings from later design questions.
- Both ideas are **briefed**, remain unclaimed ideas, and depend on both research
  tasks. Each task's completion records a finding with `tasks note <idea>
  --no-reviewed "<finding>"` on each waiting idea before its branch merges.
  Re-scope after those findings; create no duplicate research or design task now.
