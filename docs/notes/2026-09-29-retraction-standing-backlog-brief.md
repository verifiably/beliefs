# Retraction-standing backlog brief — 2026-09-29

## Problem

Five correction/world-read ideas ask when standing should change epoch building,
audits, or reads, and whether absence handling can be simplified. Goal:
`beliefs-0c50ed`. Keep current fail-closed guarantees while separating an
answerable rule-input question from extensions without a demonstrated consumer.
This is a scoping handoff, not an approved design or a reopened conformance lane.

## Current behaviour and evidence

Read at main `aa38dd1`. Three existing focused checks passed via `just test-one`:
`test_world_standing.py`'s found-retraction absence, split-counter disagreement,
and rebuild-after-retraction tests (3 passed, 3.62 s).

- `world/epoch.py:_captured_records` calls `_standing_retractions` per corpus.
  `world/derive.py:CapturedRetraction` carries target and resolution;
  `world/rules_v1/retraction.py` enumerates those resolutions without folding
  the world's graph. `evaluation.py:gather` recomputes standing and refuses a
  disagreement. Slice 1 §11.1 and slice 2 §14.2 still apply to `beliefs-c800ef`.
- `corpus.py:lineage_snapshot` supplies no retired routes;
  `audit.py:check_lineage_basis` compares stored routes with producers.
  Retirement is applied by `gather`. `beliefs-2d5ada` asks for a new comparison,
  not a repair of the current audit contract (slice 1 §11.5).
- The rebuild test confirms that a same-coverage rebuild retains a retracted
  producer identity and reads still refuse it (`beliefs-05dd2a`). Slice 2
  §14.7 banks this asymmetry; import refusal landed in `848a24a`.
- Snapshot absence handling landed in `81104e1`, its precedence test in
  `24f901c`. A departed covered corpus yields unavailable reads; the audit's
  receipt availability checks yield unresolvable. A durable departure event
  (`beliefs-7d3463`) needs an additional contract, per slice 2 §14.1.
- `beliefs-179099` overstates dead code. `gather` walks retractions before the
  absence return, retaining per-ref diagnostics asserted by the passing test.
  Later run/input/proposition absence branches appear redundant for world
  reads. `corpus.py:_absence_of` always returns None for local reads, contrary
  to the original task's claim. No blanket deletion is justified.

Code paths above are under `python/src/beliefs/`; tests under `python/tests/`.
The slice designs are the 2026-09-16 and 2026-09-19 correction-remainder designs
in `docs/superpowers/specs/`. Existing briefs, task attachments, and open tasks
were searched; no overlapping open rule-input research was found.
`beliefs-85df0f` was read as related context and left untouched.

## Constraints

The adoption ledger closes correction-remainder at cut 34; roadmap Appendix B
banks its limitations without creating new rows. Preserve frozen cut bodies,
refusal precedence, receipt reproducibility, and local standing.
`beliefs-eacbe2` owns successor-contract design. Old rules and their fixtures
are content-addressed evidence; a changed algorithm needs explicit version and
identity treatment. No priority increase follows merely from an unknown.

## Alternatives

1. **Retain the current fail-closed bounds.** Recommended for audit comparison,
   build refusal, departure events and incidental cleanup until their wake
   conditions are met. No implementation or design tasks for these now.
2. **Derive standing over the complete capture in a successor rule.** Current
   lean for the split-counter limitation, subject to `beliefs-ae33ff` establishing
   the required graph inputs, reference resolution and identity effects.
3. **Make capture consult the whole world.** Rejected as the default: it crosses
   the current per-corpus capture boundary rather than using the existing
   derivation boundary. Any revival needs evidence and reviewed design.

## Unanswered questions

- Does current rule input suffice for all three target arms and deprecated
  references? `beliefs-ae33ff` answers with a bounded trace/probe and recommends
  whether contract-cut should select a successor rule.
- Which consumer needs retirement-adjusted audit certification, a build-time
  refusal, or a recorded departure event? A worked workflow must supply the
  expected observable result before those shelved ideas wake.
- Is removing later absence branches worth touching the shared gather path?
  A concrete refactor or maintenance issue must justify it and retain early
  diagnostics; this review did not measure a benefit.

## Proposed decomposition

- `beliefs-ae33ff` — P3, small, mid complexity, direct: input/identity inventory
  and recommendation; completion adds a finding note to `beliefs-c800ef` in
  the same commit. No successor-rule implementation is authorized by it.
- `beliefs-c800ef` — briefed; remains an idea pending that finding.
- `beliefs-2d5ada` — shelved until a consumer needs an explicit audit comparison
  of stored and retirement-adjusted certification.
- `beliefs-05dd2a` — shelved until a workflow is blocked by rebuilt retracted
  snapshots, or contract-cut explicitly selects build-time enforcement.
- `beliefs-7d3463` — shelved until a consumer requires durable departure
  attribution beyond unavailable/unresolvable.
- `beliefs-179099` — shelved until a concrete gather refactor warrants removing
  proven redundant later branches; its body now corrects the early/local claim.

All five retain their original source material under `beliefs-0c50ed`. No drops,
implementation changes, or new design task were needed in this pass.
