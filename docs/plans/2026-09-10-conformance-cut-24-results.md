# Conformance cut 24 — results

**Cut:** `../designs/2026-09-10-conformance-cut-24.md`, frozen 2026-09-10 at
`c72219908c405fb8ccd5d7541c2f588407e89314`, whole-file SHA-256 at freeze
`e15ff057eca27c21907d9c7288811b5c50b34c1041dc038f5c03f54c8e8b5798`
**Subject:** the governed coreference attestation and its populated balance
**Discharged:** 2026-09-10, on `world-resolution`
**Runner:** `python/tools/cut24_acceptance.py`

## 1. What ran

The certified run tested clean commit
`c21a622` (tree `39671cddfc31bfec9caeda3ea9dd34dae3bc9319`) from
`python/` on the certified host and volume:

```text
uv run --frozen python tools/cut24_acceptance.py
```

**Exit code 0.** Its 118-line transcript has SHA-256
`41895472c833a44b30012c7de7200462541299d8b235cb69c70e278fee6bb145` and
is retained byte-for-byte as
[`certified.log`](2026-09-10-conformance-cut-24-run/certified.log). No
capability waiver, skip or refusal occurred.

Task 9 reused that accepted Task 8 transcript under the controller's ruling:
`e8c3327`, the Task 9 starting point, differs from `c21a622` only in
`tasks/beliefs-edf1ad.md`. Runtime and tests did not change. Before the final
runner extraction, the same corrections were tested as HEAD `21857a9` plus
`test_facet_acceptance.py`, `test_n2_cut11.py`, `test_n2_cut18.py` and
`cited_not_run.py`; their pre-extraction green transcript is retained as
[`historical-pre-extraction-green.log`](2026-09-10-conformance-cut-24-run/historical-pre-extraction-green.log).
The extraction changed exercised runner code, so the clean `c21a622` run above
supersedes it.

The prefix chain was cut 24 → cut 23 → cut 22 → cut 21 → cut 20 → cut 19 →
cut 18 → cut 17. Its **33 phase summaries report 540 passed**:

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 23 passed in 12.36s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 42 passed in 47.77s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 17.96s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 6.68s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 30.39s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.16s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 14.76s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 317.96s (0:05:17) |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 126.18s (0:02:06) |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 15.78s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 14.51s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 80.35s (0:01:20) |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 46.16s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 67.16s (0:01:07) |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 77.16s (0:01:17) |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.32s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.64s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 105 passed in 27.09s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 16.10s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 55.56s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 27.74s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 31.62s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 27.27s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 40.18s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 34.97s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.43s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.32s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.52s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 3.94s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 120.08s (0:02:00) |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 42.78s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 88.89s (0:01:28) |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 23.47s |

Cut 24's final inventory is:

```text
declared arms: 20 (= 5 declaration units; 5 guarantee rows)
```

From the repository root, through the vendored `tools/tt` recipes:

- `just check` exited **0**: Ruff, Pyright, TypeScript typecheck, Biome and
  `tasks check` passed with zero task errors and warnings. Transcript:
  [`check.log`](2026-09-10-conformance-cut-24-run/check.log); exit record:
  [`check.exit`](2026-09-10-conformance-cut-24-run/check.exit).
- `just test` exited **0**: **4333 Python tests passed in 1060.63s
  (0:17:40)** and **142 TypeScript tests passed across 7 files**. Transcript:
  [`test.log`](2026-09-10-conformance-cut-24-run/test.log); exit record:
  [`test.exit`](2026-09-10-conformance-cut-24-run/test.exit).
- After the final documentation and tracker updates,
  `uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider`
  exited **0** with 14 passing checks
  ([`focused-docs.log`](2026-09-10-conformance-cut-24-run/focused-docs.log)).
  `just check` then exited **0**, including `tasks check` with zero errors and
  warnings ([`final-check.log`](2026-09-10-conformance-cut-24-run/final-check.log)).
  The separate final task validation has the same zero-error, zero-warning
  result ([`tasks.log`](2026-09-10-conformance-cut-24-run/tasks.log)).

## 2. Accounting and disposition

Five guarantee rows are read: **2 full/closed** (W15, W4) and **3 partial**
(X12, W8a, M3). Five declaration units expand to 20 single-mutation arms.
`roadmap_status.py` reports **144 closed of 195 rows across 18 tables; 51
open**. No new guarantee table or row is introduced.

- **W15 closes:** the governed record, endpoint and actor refusals, exact
  duplicate handling, NFC key, capture lift, coverage, populated balance,
  receipt outcomes, closure isolation and lifecycle behavior are all read.
- **W4 closes as rewritten:** coreference mints an attestation and retires no
  address; both endpoints remain byte-unchanged and live, and no operation
  merges them.
- **X12 stays partial:** its coreference membership, omission-refutes,
  populated-rebuild and digest-boundary arms are read. Its
  `instrument-certification` membership and omission-refutes arms remain with
  `contract-cut`.
- **W8a stays partial:** its coreference completeness and coverage arms are
  read. Its `instrument-certification` omission-refutes arm remains with
  `contract-cut`; its import-boundary and audit arms remain with
  `packaging-remainder`.
- **M3 stays partial:** the active coreference edge changes neither concrete
  records nor the existing abstract/forced/raw cycle readings. The concrete
  controlled-cycle construction remains cut 5's banked limitation.
- **W8b was measured and not selected.** `beliefs-fda0e5` repaired the measured
  build defect: address-map derivation now refuses uid corruption and reports
  duplicate locations distinctly. The row still awaits conformance selection.
- **W1, W2 and W5a are re-filed to slice 2b, `beliefs-b7994b`.** They require
  source addresses derived from the normalized identifier and do not belong to
  the coreference-attestation implementation.

## 3. Corrections and deviations from the frozen cut

- **2026-09-10 — live arm accounting.** Frozen §5 says 18 arms while naming
  19 mutations. Post-freeze review retained the original 18 declarations and
  added independent `W15n` for `act-report` endpoint admission and `X12c` for
  membership-only receipt comparison. The live runner therefore audits 20
  arms, five declaration units and five guarantee rows. Frozen §§2–7 remain
  byte-exact from `c722199`.
- **2026-09-10 — the eighth session route.** The writer-session design's
  historical J1 text says seven public routes. `attest_coreference` is the
  eighth ledgered route. The dated amendment follows the complete historical
  route table so it does not split that table.
- **2026-09-10 — receipt mutation precision.** X12a's original
  projection-only sabotage survived its subject-identity comparison. Its one
  contiguous mutation now bypasses both comparisons for
  `coreference-reduction`; X12c independently isolates membership-only
  validation, and other receipt kinds are unchanged.
- **2026-09-10 — consolidation evidence boundary.** A pre-consolidation epoch
  containing duplicate canonical locations correctly refuses publication with
  `AddressMapConflict`. The acceptance arm asserts that refusal, applies the
  shipped reduction to the coherent durable capture before consolidation, and
  compares that result with the published balance after consolidation. It does
  not claim a published-before receipt.
- **2026-09-10 — historical live adapters and exhaustive fixture.** In mutable
  guards, cut 11 J3a's wrong pre-existing override was removed; cut 18 C1 was
  retargeted after `dc28583` inserted `attest_coreference`, and cut 5 C1[17]
  records that same cited-not-run move; cut 20 F8's exhaustive builder fixture
  now includes the new builder. The initial prefix and cut-20 failures are
  retained as
  [`historical-prefix-failure.log`](2026-09-10-conformance-cut-24-run/historical-prefix-failure.log)
  and
  [`historical-cut20-failure.log`](2026-09-10-conformance-cut-24-run/historical-cut20-failure.log).
  The later pre-extraction green run is historical; the interrupted extraction
  run is retained as
  [`historical-interrupted.log`](2026-09-10-conformance-cut-24-run/historical-interrupted.log)
  and is neither failure nor completion evidence.
- **2026-09-10 — mutable cut 7 journey fixture.** The removed synthetic helper
  was replaced by real attestations and the shipped coreference rule while its
  assertions, node ids and frozen declarations stayed unchanged. Cut 7's full
  N2 regression passed 42 tests.
- **2026-09-10 — W15i and cleanup evidence.** The exact W15i token-counting
  mutant is runnable: direct reduction over ten independent event tokens
  yields balance 10/count 10; the shipped basic fixture refuses it before
  publication. The proof is retained in
  [`w15i-token-mutant.log`](2026-09-10-conformance-cut-24-run/w15i-token-mutant.log).
  One separate baseline capture-lift subprocess passed its behavioral
  assertions but emitted pytest's `Directory not empty` temporary-directory
  cleanup warning. Its root cause was not established; the warning-bearing log
  is retained as
  [`capture-lift-cleanup-warning.log`](2026-09-10-conformance-cut-24-run/capture-lift-cleanup-warning.log).
- **2026-09-10 — Pyright version notice.** The Task 8 commit hook reported
  that Pyright `1.1.414` was available while the project remained pinned to
  `1.1.411`. The notice did not affect the gate result; the existing pin was
  deliberately preserved, and the dependency update remains deferred and was
  not implemented in this slice.

## 4. Reproduction measurement

This cut adds certified coreference-attestation and populated-balance fixtures.
It performs **no new mm30 reproduction run**. The previous single-corpus
measurement remains the
[cut 22 results §4](2026-09-08-conformance-cut-22-results.md#4-reproduction-measurement)
and [mm30 record](../designs/2026-09-05-mm30-reproduction.md): 307 of 334
claims typed, 27 `no-claim-recorded`, and equal original/rederived
`NoBelief(no-directional-outcome)` answers. Those answers carry no
`belief_input_digest`; no new mm30 digest comparison or isolated causal claim
is made here.

## 5. Remaining boundary

`world-resolution` retains **W7, W8 and W8b**; **W13**'s
coverage-declaration, digest-invariance, manifest-only re-mint/forgery,
replica-restore declaration and fork-copy clauses; **R23**'s snapshot,
cross-corpus-divergence and explicit-import clauses; and slice 2b's **W1, W2
and W5a**, filed as `beliefs-b7994b`. W8b is measured, repaired by
`beliefs-fda0e5`, and not selected.

Outside `world-resolution`, the three rows left partial by cut 24 retain their
separate dispositions; their coreference arms are read at this cut. **X12**'s
`instrument-certification` arms stay with `contract-cut`. **W8a**'s
`instrument-certification` arm stays with `contract-cut`, while its
import-boundary and audit arms stay with `packaging-remainder`, which rides
with the world lane. **M3** retains only its banked concrete-cycle limitation,
which remains unscheduled and ranked nowhere.

`packaging-remainder` also owns **X5**'s relabel. `contract-cut` also owns
R23's rules-store clauses.
The remaining implementation slices under the still-open `beliefs-d248ba` are
slice 2b (`beliefs-b7994b`), slice 3 (`beliefs-46847c`) and slice 4
(`beliefs-0e523a`).

## 6. Main integration

Merged `world-resolution` into `main` locally on 2026-09-10 with `--no-ff`,
at `7d6934119f5796eec5384516a26346a878388380`. Its parents are the prior
main `42108347a1efee164522b41db46b9bef07e6d226` and reviewed branch head
`b3014ba7aed1df81f7e4c99d6549bb8e87b5797a`; the merged tree equals the
branch tree.

The whole-branch review found no production correctness blocker. Its
delivery-ownership and authored-path findings were corrected at `b3014ba`,
and scoped re-review approved both without new blocking findings. The
nonblocking cleanup warning and Pyright notice remain recorded in §3.

From the repository root on the merge commit:

```text
just gate > docs/plans/2026-09-10-conformance-cut-24-run/main-gate.log 2>&1
exit 0
4333 passed in 1073.94s (0:17:53)
Test Files  7 passed (7); Tests  142 passed (142)
```

Ruff, Pyright, TypeScript typecheck, Biome and task validation also passed;
task validation reported zero errors and warnings. The complete transcript
and exit record are retained as
[`main-gate.log`](2026-09-10-conformance-cut-24-run/main-gate.log) and
[`main-gate.exit`](2026-09-10-conformance-cut-24-run/main-gate.exit).

After the successful gate, the merged worktree and local feature branch were
removed. No push was performed. This subsequent integration record changes
only documentation and task evidence; the tested runtime and tests remain
unchanged.
