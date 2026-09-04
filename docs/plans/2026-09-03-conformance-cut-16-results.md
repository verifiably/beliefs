# Conformance cut 16 — discharge results

**Date:** 2026-09-04
**Subject:** the two-root relocation slice
(`../designs/2026-09-03-world-changing-families-design.md`), measured against
the frozen cut at `ca31a04`.

The frozen §§2–7 remain byte-exact. This discharge changes only the cut's
status line.

## 1. What ran

All Python commands ran from `python/`. The certified runner executed at
`b0882d37afefa3be8f0150c2ce084ddb7e8e28f4` with its default durable work root
beside the checkout. It scoped XDG cache state to that disposable work root,
probed the certified durability tuple, ran cut 15 as its sole prefix, and then
ran the two cut-16 phases.

`uv run --frozen python tools/cut16_acceptance.py`

```text
[cut16 phase 1/3] cut15_acceptance.py
[cut16 phase 2/3] test_relocation_acceptance.py
16 passed in 57.13s
[cut16 phase 3/3] test_n2_cut16.py
7 passed in 67.35s (0:01:07)
declared arms: 27 (= 11 declaration units; 9 guarantee rows + 2 boundary invariants)
row accounting: 3 full/closed + 5 partial + 1 closed-row re-read
```

The inherited cut-15 runner completed its cut-14 prefix and its own three
phases before the cut-16 phases. No capability refusal or tuple mismatch
occurred, and the aggregate runner exited 0.

### 1.1 Certified host facts

- backend `linux`, revision `linux-4`, storage profile
  `flush-honoring-disk.v1`;
- kernel `7.2.2-arch1-1`;
- ext4 normalized options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`,
  `ro_compat=0x46b`; and
- certification record
  `atoms/docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json` at
  Atoms commit `0b382a9`.

### 1.2 Repository evidence at the certified head

- `uv run --frozen pytest` — **3216 passed in 951.44s (0:15:51)**;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**; and
- `tasks check` — zero errors and zero warnings.

The final discharge commit re-ran the repository's Python, TypeScript,
documentation, task, and whitespace gates; that commit does not claim to know
its own id.

## 2. Accounting and disposition

Cut 16 reads nine guarantee rows: **3 full/closed**, **5 partial**, and **1
closed-row re-read**. Two boundary invariants bring the frozen inventory to
**11 declaration units**. The executable declarations expand those units into
**27 unique one-mutation sabotage arms**.

- **W5 — full.** A source move preserves `uid`, canonical address,
  `deprecated_ids`, inbound references, and belief digest. A producer-map
  dataset move also preserves the producer snapshot and belief digest while
  both corpus-state identities and the completeness receipt move.
- **W16 — part.** Two-root consolidation preserves one address, unions
  relations and canonical tagged lineage routes, retains exactly one input
  `uid`, and writes no redirect, inbound rewrite, new deprecated id,
  coreference attestation, or balance. Both different-address cases refuse on
  the one-address precondition. Its deletion remainder did not run.
- **G3 — closes.** Moving an entity changes location but not the complete
  transitive input-closure digest: the producer snapshot, not its carrying
  index, is the closure member.
- **D7 — closes.** The producer-map move preserves W5 under agreeing
  contracts. Public `move` and `consolidate` refuse disagreeing domain or base
  contracts and missing required pins before an intent is written.
- **C3 — part.** Moving an in-coverage corpus leaves the semantic digest
  unchanged while its completeness receipt records the new exact corpus
  states. Coverage and uncovered-corpus clauses remain elsewhere.
- **R23 — part.** Both move clauses establish that location and receipt state
  are not belief inputs. Consolidation is the only ordinary transition from
  boundary-minted `single` lineage to a sorted multi-route `conflict`; route
  unions are canonical, traversal resolves every route, invalid one-route
  conflicts are unconstructible, and no ordinary API resolves the conflict.
- **M3 — part.** Consolidating two equal-basis replicas of one retraction
  succeeds while a counter-retraction targets it; content identity is unchanged
  and the counter-retraction is neither rewritten nor re-minted.
- **T2 — part.** Successful `move` and `consolidate` each carry one shared
  token and timestamps across two root-local intents and two root-local
  terminal reports, with each root's data registration between its own intent
  and report.
- **T8 — closed-row re-read.** Neither relocation API accepts an act-report as
  a subject or consolidation input, and refusal retains both roots' records
  and complete logs.
- **Boundary re-resolution.** After a real move, `retract` and `supersede`
  re-resolve under the lock and refuse the now-locally-absent target.
- **Boundary lock deduplication.** Resolved roots are deduplicated before
  sorting; a same-root request acquires one lock once, then refuses.

## 3. Corrections and deviations

There is no frozen-cut deviation. The cut-16 audit pins the freeze commit, the
frozen whole-file digest, byte-exact §§2–7, and the exact 11-unit accounting.

Second-reader review found six evidence gaps whose original sabotages were
vacuous: W5's producer subject, T2's data/intent ordering, M3's counter record,
T8's refusal retention, W16's coreference balance, and R23's producer stamp.
The durable assertions were strengthened and eight source sabotages were added.
That yields 27 concrete arms without adding or reclaiming a frozen declaration
unit; all baseline checks resolve and pass, and every sabotage fails its own
check.

Two implementation discoveries were recorded before discharge without
changing the frozen selection. Carried retractions pass their already-admitted
kind only through the lock-held relocation seams; coordination,
holdings-observation, and act-report refusals remain absolute. Recovery is
data-only: every retry mints a fresh operation token and cannot close an
interrupted operation's stranded intent.

The first certified runner attempt also found the ambient XDG cache read-only
to the planning subprocess. The runner now places that cache inside its
disposable certified run directory. This changes no selected behavior or
accounting.

## 4. What this run does not claim

- **No deletion arm ran.** W16 remains part on the clause requiring its
  conflict to survive deletion of either producing run.
- T2 remains part on its other operation kinds, root-selection failure,
  second-fulfillment, missing-spec, and non-conforming-execution clauses.
- R23 remains part on deletion, audit, producer-snapshot, coverage,
  cross-corpus-divergence, explicit-import, and rules-store clauses.
- Nothing here closes L13. Removal classification was not exercised.
- The M1 resolver and claim restore seam do not exist, so M11 and M13 are
  untouched.
- Recovery completes data states only. A fresh invocation never resumes or
  closes the interrupted operation's one or two stranded intents.

## 5. Implementation commits

| commit | subject |
|---|---|
| `ca31a04` | docs(mutation): bank the world-changing families and freeze cut 16 |
| `2317b20` | feat(report): add the record-mutation entry, in memory and in storage |
| `cee226d` | feat(errors): add the relocation refusal vocabulary |
| `661e872` | feat(corpus): add lock-held mutation seams |
| `5174cf8` | feat(relocation): add ordered acquisition and predicates |
| `6a4d972` | feat(boundary): mint relocation act-reports from the boundary |
| `c9265ca` | feat(relocation): add the destination-first cross-corpus move |
| `1ab77aa` | fix(corpus): re-resolve create-only targets under the lock |
| `4edc274` | feat(relocation): add consolidate, the duplicate-location exit |
| `74fbeb0` | test(relocation): pin every durable prefix and its recovery |
| `849493a` | test(cut16): add the durable arms, N2 declarations and the acceptance runner |
| `b0882d3` | test(cut16): close durable evidence gaps |

The intervening focused review-fix commits are part of the tested ancestry.
This results record is committed with the discharge change and therefore does
not embed its own commit id.

## 6. Remaining boundary

`consolidate-family` remains live for managed deletion. W16's deletion arm,
R23's deletion and audit residue, and the deletion cut's assigned G2c, G8, C6,
R5, S5, C1, T8, M11, and M13 readings remain there. C3 stays with
`correction-remainder`; M3 stays split across `world-resolution`, the deletion
cut's audit/admission-order ride-along, and its banked limitation; T2's other
operation-family clauses stay with `act-report-remainder`. R19, R22, M1, M3
and M5 remain assigned to the deletion cut as its run-boundary and formal-model
ride-alongs. No new boundary is created by this discharge.
