# Conformance cut 23 — results

**Cut:** `../designs/2026-09-09-conformance-cut-23.md`, frozen 2026-09-09 at
`d62c0dc`, whole-file SHA-256 at freeze
`c4873f96fbe6cbbb2925a99a449abe4883e10341592b0c2d363485513bf3eb96`
**Subject:** the world read view, cross-corpus traversal, and named absence
**Discharged:** 2026-09-09, on `design/world-resolution`
**Runner:** `python/tools/cut23_acceptance.py`

## 1. What ran

The refreshed certified run tested commit
`13576c5a7997319abe38f8684747d9cd716e1d2d`, tree
`8c7bf9d6d4baae9efca2909c9669c87527990910`, from `python/` on the certified
host and volume:

```text
uv run --frozen python tools/cut23_acceptance.py > ../docs/plans/2026-09-09-conformance-cut-23-run/certified.log 2>&1
```

**Exit code 0.** The corrected runtime and tests stayed fixed throughout the
run; the subsequent update records only documentation, transcripts and task evidence.
The complete refreshed transcript is
[`certified.log`](2026-09-09-conformance-cut-23-run/certified.log).
No capability waiver, skip or refusal occurred.

The initial Task 13 certified run at
`b5efa6ef9de86f03770a2d0f1e88aea991e9dea1` is retained byte-for-byte as
[`certified-prior-b5efa6e.log`](2026-09-09-conformance-cut-23-run/certified-prior-b5efa6e.log).
It preceded the two final-review behavioral fixes and is historical evidence.
The new run re-executes the whole certified prefix chain after those fixes.

The prefix chain was cut 23 → cut 22 → cut 21 → cut 20 → cut 19 → cut 18 →
cut 17. Its **31 phase summaries report 511 passed**:

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 23 passed in 13.80s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 42 passed in 49.89s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 19.97s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 7.02s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 34.68s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.15s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 17.00s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 327.91s (0:05:27) |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 130.73s (0:02:10) |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 15.71s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 14.05s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 81.11s (0:01:21) |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 54.94s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 64.61s (0:01:04) |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 74.21s (0:01:14) |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.04s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.35s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 102 passed in 26.11s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 15.16s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 59.83s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 26.83s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 27 passed in 29.26s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 26.73s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 40.57s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 34.56s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.18s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.55s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.44s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.07s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 118.15s (0:01:58) |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 45.55s |

Cut 23's final inventory is:

```text
declared arms: 25 (= 8 declaration units; 8 guarantee rows)
```

From the repository root, through the vendored `tools/tt` recipes:

- `just check` exited **0**: Ruff, Pyright, TypeScript typecheck, Biome and
  `tasks check` passed (zero task errors and warnings). Transcript:
  [`check.log`](2026-09-09-conformance-cut-23-run/check.log).
- The first `just test` exited **1**: **3 failed, 4202 passed in 1046.59s**;
  TypeScript did not run because the Python command failed. Its complete
  transcript is [`test-first-failed.log`](2026-09-09-conformance-cut-23-run/test-first-failed.log).
  The three causes and their correction are recorded in §3.
- The pre-final-review `just test` exited **0**: **4205 Python tests passed in 1038.66s**
  and **142 TypeScript tests passed across 7 files**, with no skips or failures.
  Transcript:
  [`test.log`](2026-09-09-conformance-cut-23-run/test.log).

That full repository test run preceded the final-review behavioral fixes;
it is evidence for the preceding tree, not a full-suite result for the fixes.

Final-review covering checks passed **198 tests in 190.16s**, including all
13 new unit regressions, both live cut 22/23 N2 audits and the live/frozen
guard sweep. See [`final-fix-focused.log`](2026-09-09-conformance-cut-23-run/final-fix-focused.log).
The corrected tree's `just check` exited **0**, with zero task errors or
warnings ([`final-fix-check.log`](2026-09-09-conformance-cut-23-run/final-fix-check.log));
document/guide checks passed **22 tests in 3.07s**
([`final-fix-docs.log`](2026-09-09-conformance-cut-23-run/final-fix-docs.log)).
After refreshing the certified results table, document/guide checks passed
**22 tests in 0.81s** and `just check` again exited **0** with zero task errors
or warnings ([`final-fix-refreshed-docs.log`](2026-09-09-conformance-cut-23-run/final-fix-refreshed-docs.log),
[`final-fix-refreshed-check.log`](2026-09-09-conformance-cut-23-run/final-fix-refreshed-check.log)).

During the initial discharge, before its final gate, the focused capability, guide, decode, world-view,
design-corpus, arm-staleness and frozen-guard suite passed **498 tests in
25.16s**. The final gate kept the tree stable until its summary was captured;
afterward the measured counts, task handoff state and implementation plan status
were filled, followed by **22 passing document/guide checks** and `tasks check`
with zero errors and warnings. The final document checks are retained in
[`final-docs.log`](2026-09-09-conformance-cut-23-run/final-docs.log), and task
validation in [`tasks.log`](2026-09-09-conformance-cut-23-run/tasks.log).

The initial-discharge gates started at `b5efa6e`; discharge reporting and documentation
were edited during the first serial run. Final repository and focused checks
run after the corrections, so the transient guide failure is preserved rather
than treated as a passing final state.

## 2. Accounting and disposition

Eight guarantee rows are read: **7 full/closed** (D3, S1, S1a, S5, W6, W10,
R19) and **1 partial** (R23). Eight declaration units expand to 25 single-mutation
arms. `roadmap_status.py` reports **142 closed of 195 rows across 18 tables;
53 open**. No new guarantee table or row is introduced.

- **D3 closes:** all five resolution answers are reachable and distinct; every
  pair of overlapping availability inputs refuses.
- **S1 and S1a close:** relation and lineage closures traverse across corpora;
  the corpus-local negative preserves truncation and dangling distinctions.
- **S5 closes:** absent roots, ancestors and published producing runs carry
  their corpus into lineage incompleteness, certification and projection.
- **W6 closes over the existing epoch reader:** covered absence stays
  `NotPresent`; an unobserved address stays `Unknown`.
- **W10 closes:** ordinary world edges and captured cross-corpus adjacency
  preserve the corpus-local boundary and exclude drift.
- **R19 closes:** world-view recomputation checks a genuine verification,
  reports a well-formed verdict forgery, and refuses a malformed record.
- **R23 stays partial:** its coverage clause is read, with absence inside
  coverage distinct in the lineage projection and digest. Snapshot,
  cross-corpus-divergence and explicit-import clauses stay with slice 3;
  rules-store clauses stay with `contract-cut`.
- **W8b is measured and not selected.** The pre-freeze probe accepted one uid
  at two addresses and raised bare `ValueError` for a duplicate address instead
  of the promised `duplicate-location` finding. `beliefs-fda0e5` remains open.
  The new view's duplicate-uid refusal at open is a boundary invariant and
  does not discharge the build obligation. The status generator correctly
  lists this row as never selected; the frozen prose's “stays part” means open,
  not a selected partial row.

## 3. Corrections and deviations from the frozen cut

- **2026-09-09 — final-review run-only pin agreement.** Both `gather` and pure
  `evaluate` now include matched assessments' typed run addresses in consulted
  closure membership. A second corpus holding only the two selected runs must
  agree on pins and must supply them. Nine regression cases exercise agreement,
  disagreement and missing pins through each of `gather`, `evaluate` and
  `evaluate_over`, with an unrelated disagreeing pin excluded throughout.
- **2026-09-09 — final-review declared inbound sources.** The world index
  resolves stored `Relation.source` through the epoch map. Unknown sources
  contribute no edge; mapped sources absent from held capture retain an edge
  with `source_uid=None`; a different held source supplies its actual uid.
  Four regression cases check these states and world/local closure behavior.
  The index still visits mapped captured containers and resolves targets by map.
- **2026-09-09 — final-review live sabotage adaptations.** Cut 22 D6a's old
  assignment matcher predates run closure membership; its live replacement
  matches the new assignment and removes only observed datasets, retaining
  runs. Cut 23 W10d's old `held.values()` → `captured.values()` loop mutation
  was observed **vacuous** after the declared-source map guard independently
  excluded the unmapped drift run. Its live replacement swaps the complete
  inbound membership block for a captured-record loop with container source
  uids, bypassing both redundant source membership checks in one replacement.
  The same durable assertion must detect `run:late` entering the index. W10e's
  target-map mutation remains unchanged. Both adaptations live in the audit
  guards; all historical declaration bodies, the 25 arms/8 units/8 rows, and
  frozen cut §§2–7 remain unchanged.
- **2026-09-09 — root and refusal reachability.** `closure` fetches its root
  before walking, so lineage handles actual `NotPresent` roots first. Unknown
  roots retain `RefError` in both view types. The absence-helper sabotage is
  checked where it can reach a corrupt fetch; the durable check separately
  requires the fetch and lineage refusal. No failure becomes absence.
- **2026-09-09 — mapped aliases and current addresses.** Published producers
  are unioned by mapped location, so live and retired dataset addresses retain
  all producers even when the producer carrier is absent. A post-publication
  canonical rename that retains the mapped uid and old address still refuses
  at open if its new live address is absent from the publication map.
- **2026-09-09 — complete evaluation absence and attribution.** The read gathers
  missing assessment runs, every run-input role, proposition closure members
  and supplied lineage-snapshot absence. Derived attribution reaches `evaluate`
  through its context; a real duplicated assessment value under two addresses
  proves that both holding corpora's pins are consulted.
- **2026-09-09 — fixture construction and locality.** S7 admission requires a
  local run. Durable split fixtures writer-mint staging prerequisites, admit
  dependents, then writer-delete staging records before publishing the final
  placement. The local evaluation negative proves missing foreign evidence,
  facets and a different digest; it does not require `NoBelief`, since the
  remaining local evidence can legitimately yield a belief.
- **2026-09-09 — narrow implementation adaptations.** Python 3.11 requires
  `default_factory` for the empty absence mapping; the existing `NoBelief.detail`
  is reused. The private resolution state uses the spec's closed `Literal`;
  its unused compatibility property was omitted. `RecordNotPresent` preserves
  the spec's structured ref, corpus id and stamp; foreign-world epochs refuse
  as `EpochUnknown`. Stamp and drift fixtures use the real validation/write
  seams; R19's verdict mutation and W10's mapped-edge mutations target the
  effective code paths. Frozen §§2–7 and historical declarations are unchanged.
- **2026-09-09 — historical guard adaptation.** Factoring validation and
  changing lineage moved old cut-4 arms; the cited-not-run registry records
  the exact moved arms and commits. Cut 15's live R23 and cut 18's live S5/R23b
  mutations follow the new branches. Historical declaration bodies and pins
  remain unchanged, and the frozen-guard discovery/staleness sweep covers the
  resulting inventory.
- **2026-09-09 — repository gate failures.** The first serial gate found a
  static false positive for `copy.deepcopy` against the byte-write name `copy`,
  a decode test matching the old two-state overlap message, and a guide link
  checked between adding the link and writing its results target. The targeted
  reproduction confirmed the two stable failures and the now-valid guide.
  The direct stdlib `deepcopy` import follows existing modules without weakening
  the capability guard; the test now matches the actual generalized refusal.
  The failed transcript is retained; the complete final gate then passed.
- **2026-09-09 — discharge bookkeeping.** The initial discharge reused the certified Task 13 run;
  root `just check` and `just test` remain mandatory. The reporting tool gains
  cut 23's accounting row before Appendix A regeneration. Existing plan children
  supply freeze and discharge tasks, so no duplicate ceremony tasks are filed.
  W15, explicitly deferred by frozen §2, remains open despite its omission from
  the Task 14 brief's remainder list. Two accidentally tracked Task 2 scratch
  files were untracked; their local evidence remained available through the
  completed final review.

## 4. Reproduction measurement

This cut adds certified two-corpus chain, split-producer, evaluation and
verification fixtures. It performs **no new mm30 reproduction run**. The
previous single-corpus measurement remains the
[cut 22 results §4](2026-09-08-conformance-cut-22-results.md#4-reproduction-measurement)
and [mm30 record](../designs/2026-09-05-mm30-reproduction.md): 307 of 334 claims
typed, 27 `no-claim-recorded`, and equal original/rederived
`NoBelief(no-directional-outcome)` answers. Those answers carry no
`belief_input_digest`; no new mm30 digest comparison or isolated causal claim
is made here. The cut's digest assertions concern its new two-corpus fixtures.

## 5. Remaining boundary

`world-resolution` retains **W1, W2, W4, W5a, W7, W8, W8b, W15**; **W13**'s
coverage-declaration, digest-invariance, manifest-only re-mint/forgery,
replica-restore declaration and fork-copy clauses; **W8a**'s coreference arms;
**X12** and **M3**'s coreference arms; and **R23**'s snapshot, cross-corpus
divergence and explicit-import clauses. R23's rules-store clauses remain with
`contract-cut`. W8b's measured build defect stays `beliefs-fda0e5`.

`packaging-remainder` is unchanged: **X5**'s relabel and **W8a**'s import-boundary
and audit arms. Slices 2–4 are filed under the still-open `beliefs-d248ba` as
`beliefs-113561` (coreference, including W15), `beliefs-46847c`
(snapshots/import/audit and packaging), and `beliefs-0e523a` (W7 view evaluation),
with serial dependencies. The parent is `todo` with its claim released;
completion of slice 1 does not claim the remaining boundary is discharged.

## 6. Main integration

The lane merged into `main` on 2026-09-09 at
`6eb0b936ef046a3ae211be00b4f2f0b4bd9b48c8`, after all task reviews and the
final scoped re-review passed. Both final-review findings were addressed.
The merge preserves the independent task-record commits already on `main`.

From the repository root, `just gate` exited **0** on that unchanged merged
tree: **4218 Python tests passed in 1345.43s** and **142 TypeScript tests
passed across 7 files**. Ruff, Pyright, TypeScript typecheck, Biome and
`tasks check` also passed, with zero errors or warnings and no test skips.
This is the full serial gate for the corrected implementation; the earlier
4205-test result in §1 predates the 13 final-review regressions.
The complete [main gate transcript](2026-09-09-conformance-cut-23-run/main-gate.log)
and [exit record](2026-09-09-conformance-cut-23-run/main-gate-exit.log) are retained.
