# Conformance cut 28 — results

**Cut:** `../designs/2026-09-14-conformance-cut-28.md`, freeze
`dfc8665f414af8ef1a93f81532391e64fb805c18`; freeze document SHA-256
`39e93aa6e5e13e839aad8a675b11e1652fa30fd7e2f05ab62f516ba26480ba62`
**Declaration:** `d11baf9608190735426a7fee1e99cf04c7a6a4c3`; SHA-256
`2d5a4e7496ca59b06c52205152496231eedd13b3749b76cfedd4d97afdb5400d`
**Subject:** view-query evaluation and the W8/W8b conflict discharge
**Discharged:** 2026-09-14, on `design/world-resolution-slice-4`
**Runner:** `python/tools/cut28_acceptance.py`

## 1. What ran

Task 8 ran the complete acceptance chain against the source at `ac94567`:

```sh
cd python
mkdir -p ../.cut28-acceptance
uv run --frozen python tools/cut28_acceptance.py > ../.cut28-acceptance/run.log 2>&1
run_status=$?
printf '%s\n' "$run_status" > ../.cut28-acceptance/exitcode
exit "$run_status"
```

**Exit code 0.** Task 9 copied its transcript byte-for-byte; both copies have
SHA-256 `44c86a368a11ea4945d55341fa2068361cd1404ff901af42a818914d0a47ae36`.
The retained transcript is [`certified.log`](2026-09-14-conformance-cut-28-run/certified.log).
No capability waiver, skip or refusal occurred.
Per the SDD ruling, this successful Task 8 transcript was reused because its
inputs remained unchanged; the runner was not repeated.

The prefix chain was cut 28 → cut 27 → cut 26 → cut 25 → cut 24 → cut 23 →
cut 22 → cut 21 → cut 20 → cut 19 → cut 18 → cut 17. Its **40 module
summaries report 669 passed**. The cut 28 phases reported:

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 24 passed in 14.84s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 42 passed in 50.34s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 19.29s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 6.94s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 33.10s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.15s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 15.97s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 326.09s |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 204.85s |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 16.41s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 15.58s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 86.38s |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 49.04s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 68.57s |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 79.59s |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.42s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.91s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 110 passed in 28.37s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 17.81s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 57.64s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 30.79s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 32.90s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 28.15s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 41.34s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 36.01s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.30s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.91s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.43s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.29s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 131.22s |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 45.16s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 91.71s |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 25.58s |
| cut25 phase 2/3 | `test_source_address_acceptance.py` | 20 passed in 32.84s |
| cut25 phase 3/3 | `test_n2_cut25.py` | 8 passed in 9.38s |
| cut26 phase 2/2 | `test_n2_cut26.py` | 10 passed in 1.57s |
| cut27 phase 2/3 | `test_world_audit_acceptance.py` | 42 passed in 236.45s |
| cut27 phase 3/3 | `test_n2_cut27.py` | 9 passed in 53.53s |
| cut28 phase 2/3 | `test_world_selection_acceptance.py` | 25 passed in 115.87s |
| cut28 phase 3/3 | `test_n2_cut28.py` | 9 passed in 40.48s |

The final inventory is:

```text
declared arms: 23 (= 3 declaration units; 3 guarantee rows)
```

Against the same stable source, from the repository root through the vendored
`tools/tt` recipes:

- `just check` exited **0**: Ruff passed; Pyright reported zero errors,
  warnings and information diagnostics; TypeScript typecheck and Biome passed;
  and `tasks check` reported zero errors and warnings. Transcript:
  [`check.log`](2026-09-14-conformance-cut-28-run/check.log). Pyright also
  printed a benign notice that version 1.1.414 was available; it was a tooling
  update notice, separate from the zero diagnostics, and did not require a
  tooling change or gate rerun.
- `just test` exited **0**: **4,627 Python tests passed in 1,229.35s
  (0:20:29)** and **142 TypeScript tests passed across 7 files**. Transcript:
  [`test.log`](2026-09-14-conformance-cut-28-run/test.log).

The retained `test.log` has one documentation-only redaction: Vitest's printed
machine-specific checkout root was replaced with the main-checkout-relative
`.worktrees/world-resolution-slice-4/ts`. Test output, counts and timings are
otherwise unchanged. The certified acceptance transcript remains byte-exact.

## 2. Accounting and disposition

Cut 28 reads three guarantee rows: **2 full/closed** (W7 and W8b) and
**1 partial** (W8). Three declaration units carry 23 arms. Closing W7 and W8b
moves the closed count from 151 to **153 of 196**, leaving **43 open**. The
generated accounting reports exactly `Closed 153 of 196; open 43.`

- **W7 closes.** View queries evaluate over one explicit world read view,
  including absence, drift, damage, stale records and all four predicates.
- **W8b closes.** Existing code distinguishes UID corruption from duplicate
  location and preserves the documented precedence and refusal behavior.
- **W8 remains partial** only on its ambiguous-search-term conflict, re-homed
  to `authority-labels` with W9 and W14.

## 3. Corrections and deviations from the frozen cut

The frozen cut's §§2–7 and the canonical declaration did not change. The
measured implementation and review corrections were:

- **2026-09-14 — test-first evidence.** Task 3's original RED preceded the
  test file and was invalid evidence. A controlled missing-module regression
  check supplied the missing failing observation before the restored pass.
- **2026-09-14 — conflict guarantees.** Task 6's fixtures were strengthened
  to prove exact claims, rebuild-and-view behavior, both consolidation
  directions and byte-for-byte no-write refusals.
- **2026-09-14 — durable fixtures.** Task 7 replaced raw writes hidden by a
  writer's cached view with writer admission where relocation needed it, and
  isolated UID precedence in a third corpus. Publication-only conflicts remain
  raw staged after admission and are read by a fresh publication boundary.
- **2026-09-14 — sabotage strength.** W7-a gained actual damaged-address
  coverage and W7-p gained a lowercase negative; the rerun proved all 23 of 23
  mutation arms sound.
- **2026-09-14 — independent-world epochs.** Full projections are equal when
  registration order is reversed at one published epoch. Separately created
  worlds compare all non-epoch members and each projection binds its own epoch,
  because the world anchor participates in epoch identity.

The measured declaration count is exactly the frozen count of 23 arms; there
was no arm-count deviation and no staleness re-target was required.

## 4. Reproduction measurement

This cut performs **no new mm30 reproduction run**. The previous single-corpus
measurement remains [cut 22 results §4](2026-09-08-conformance-cut-22-results.md#4-reproduction-measurement)
and the [mm30 record](../designs/2026-09-05-mm30-reproduction.md): 307 of 334
claims typed, 27 `no-claim-recorded`, and equal original/rederived
`NoBelief(no-directional-outcome)` answers. No new mm30 digest comparison or
isolated causal claim is made here.

## 5. Remaining boundary

`world-resolution` retains no guarantee row. Its two filed follow-ups are
dataset addressing (`beliefs-48214e`) and divergent correction-history
reconciliation (`beliefs-24b42b`).

`authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**.
`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm. The ledger's manifest-safety item remains
unowned and unselected.

## 6. Main integration

Merged `design/world-resolution-slice-4` into `main` with `--no-ff` on
2026-09-14 at `fb90cc317836291605f991107d2e987cfa4545e8`, after the final
whole-branch review approved `7f34ead` with no findings. That review independently
verified the frozen cut sections, declaration bytes, pin ancestry, unchanged
source since the branch gates, and the 669 acceptance-test invocations.

`just gate`, begun on that merged revision, exited **0**: Ruff, Pyright, TypeScript
typecheck, Biome and task checks passed; the serial Python suite reported
**4,627 passed in 1,146.99s (0:19:06)**, and TypeScript reported **142 passed**
across seven files. Task validation reported zero errors and warnings.
The output is retained in
[`main-gate.log`](2026-09-14-conformance-cut-28-run/main-gate.log), with only
Vitest's absolute checkout path replaced by `./ts`. Pyright's benign version
notice is retained, as in §1. The earlier transcripts remain unchanged.

While the gate ran, main advanced to `fbdd986` with a `.gitignore`-only change;
the source and tests under validation did not change. The integration-record
commit was rebased onto that main revision to preserve the concurrent change.

The tracked implementation reports are preserved alongside the gate evidence
when clearing the temporary implementation workspace:
[Task 2](2026-09-14-conformance-cut-28-run/task-2-report.md),
[Task 4](2026-09-14-conformance-cut-28-run/task-4-report.md), and
[Task 5](2026-09-14-conformance-cut-28-run/task-5-report.md).
