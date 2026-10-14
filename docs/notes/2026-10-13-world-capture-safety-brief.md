# Remaining world capture safety questions

## Problem

Two world-read ideas concern what a corpus capture can safely establish:
`beliefs-85df0f` asks who owns manifest safety after nodes 2.0;
`beliefs-655c10` asks for evidence that coordination-only drift leaves an epoch's
mapped content unchanged. Establish the first obligation before selecting a cut;
revisit the second when existing measurements establish a need.

## Current behaviour and evidence

Static evidence checked against main `3e6a224` on 2026-10-13:

- **Manifest safety has a narrower historical meaning than the idea suggests.**
  [World resolution slice 3, section 11, limitation 2](../superpowers/specs/2026-09-13-world-resolution-slice-3-design.md)
  identifies the reserved-path guarantee that a root-level non-node file is not
  a walk hazard. It explicitly leaves that guarantee unselected. The
  [adoption ledger, row 3](../designs/2026-08-03-redesign-adoption-ledger.md)
  still calls it unowned; [cut 29 results, section 5](../plans/2026-09-14-conformance-cut-29-results.md)
  preserves the same disposition.
- **Damaged-corpus audit behavior already has an owner.**
  [Substrate S9](../designs/2026-08-02-substrate-consolidation-design.md)
  covers parse-error, path-mismatch, uid-collision and id-collision, auditing
  the remainder without claiming a state identity. `python/src/beliefs/corpus.py`
  `_collecting_view` filters those four codes; `python/tests/test_world_view.py`
  `TestReportMode` tests strict refusal and report-mode exclusion. Whether
  path-collision needs a further beliefs obligation remains to be established.
- **State identity remains strict and comprehensive.**
  `python/src/beliefs/world/registry.py` `corpus_state_identity` reads a strict
  `ReadView` and hashes the complete canonical manifest plus every node's
  canonical content. `world/epoch.py` `_capture` checks states before and
  after enumeration inside each corpus's capture hold. On its way to the
  digest it computes a `science.node-content.v1` identity for every node
  (`registry.py:763-772`), then keeps only the aggregate. An epoch that retained
  that per-uid list would hold the comparison baseline a canonical-equality
  witness needs. Checking against it still reads the whole corpus; what it
  would save is the rebuild, not the read.
- **There is no mapped-content drift witness.** `world/view.py` checks mapped
  addresses and uids, serves the records captured when the view opens rather
  than the epoch's own, and reports whole-corpus state differences. Its
  `DriftReport` has no mapped-content comparison.
  Source task `sci-dc0381` and its spec's decision 7 record why merely classifying
  unmapped records as coordination is unsafe: a simultaneous mapped facet edit
  can pass that classification. The implementation amendment permits unmapped
  coordination records at an unchanged whole-corpus state; subsequent writes
  still make the epoch stale.

## Constraints

Preserve S9 and frozen cut evidence. A missing conformance owner is not itself
evidence of a runtime defect. Distinguish manifest parsing, reserved-path
traversal, and damaged-corpus state refusal.

[World addressing, section 5](../designs/2026-08-02-world-addressing-design.md)
defines canonical content equality and deliberately ignores manifest formatting.
The witness idea's stronger phrase “byte-identical” needs an explicit decision;
the current digest does not prove raw-file equality. Any witness also needs an
epoch-retained comparison baseline and must preserve capture coherence.

Existing measurement owners are `sci-0d00d2` for epoch rebuild frequency and
cost, and `beliefs-e02ef3` for audit and mount-opening costs. The latter belongs
to `beliefs-7e341d` and already names the witness overlap in the
[mount-citations brief](2026-10-09-mount-citations-follow-ups-brief.md).
Reuse those measurements; sharing a possible mechanism does not establish
identical requirements for epoch reuse and mount caching. `sci-0d00d2`'s
commitment comes from the science mount-citations consumer spec, limitation 1
(how often an epoch is built and how long it takes). Its section 7 assigns that
milestone limitations 1 and 3, not limitation 2, which is the coordination-write
staleness the witness addresses. A total rebuild count cannot show
coordination-only cost, so on 2026-10-14 `sci-0d00d2` was asked to record the
class of write (coordination or evidence) behind each forced `science epoch`.

## Alternatives

1. **Establish the remaining obligation, then select its owner (lean).** A
   bounded matrix separates existing guarantees from missing coverage. Keep
   strict epoch currency until measurements justify changing it.
2. **Select a new manifest-safety cut and witness API now.** Premature: the
   exact unowned guarantee, witness equality contract and operational benefit
   are unsettled.
3. **Bank both as limitations.** Reasonable for the witness pending a measured
   need; premature for manifest safety before tracing its reserved-path scope.

## Unanswered questions

- What reserved-path obligation remains after S9, and does path-collision
  reach a beliefs consumer? `beliefs-2a2224` answers with code/test evidence
  and a proposed owner or limitation.
- Do coordination-only rebuilds or repeated mount opens cost enough to justify
  a witness? Existing tasks `sci-0d00d2` and `beliefs-e02ef3` supply the evidence.
- If justified, what equality and epoch baseline can prove the required
  invariance? Resolve during re-scoping before commissioning a design.

## Proposed decomposition

Goal `beliefs-03d483` groups these follow-ups within world-read delivery.

- `beliefs-85df0f`: **briefed**, original source text preserved; depends on
  `beliefs-2a2224`, a P2, small, mid-complexity, direct investigation. Its result
  records the obligation matrix and disposition here and wakes the idea with
  `tasks note beliefs-85df0f --no-reviewed "<finding>"` before merging.
- `beliefs-655c10`: **shelved**. Unshelve and re-scope when `sci-0d00d2` finds
  material coordination-only rebuild cost, or `beliefs-e02ef3` finds material
  mount-opening cost requiring a witness. Both measurements retain their
  existing owners; no duplicate benchmark or design task is filed. The shelf
  with that observable wake counts as banking the witness for goal
  `beliefs-03d483`, which closes once `beliefs-2a2224`'s disposition lands.
