# Conformance cut 29 — results

**Cut:** `../designs/2026-09-14-conformance-cut-29.md`, freeze
`21d1a11390b91d3104b35aa729ebe148f8fb5fd6`; freeze document SHA-256
`1247569526f49480c59705fd9e3b3960cd4639b1010eb9bbec77870353780208`
**Declaration:** `0e57a524d3b1db07b0682a1570051b1b4d79c574`; SHA-256
`ae9d0f669d9f287e76815d90a787f608a1303ff0da4c32f7c918a30d8515df62`
**Subject:** dataset addresses derived from the content identity
**Discharged:** 2026-09-15, on `design/world-resolution-slice-5`
**Runner:** `python/tools/cut29_acceptance.py`

## 1. What ran

The final root gate and aggregate runner covered the source at `4d69f37` plus
the complete tested delta recorded by `f06834f`: accounting and documentation,
the decoded-lineage projection repair and regression, and the cut 28 raw-fixture
repair:

```sh
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
export SCIENCE_CUT4_ROOT="$MAIN_CHECKOUT/.cut29-acceptance/world-resolution-slice-5"
export SCIENCE_CUT7_ROOT="$MAIN_CHECKOUT/.cut29-acceptance/world-resolution-slice-5"
export SCIENCE_CUT10_ROOT="$MAIN_CHECKOUT/.cut29-acceptance/world-resolution-slice-5"
export SCIENCE_CUT29_ROOT="$MAIN_CHECKOUT/.cut29-acceptance/world-resolution-slice-5"
mkdir -p .cut29-acceptance docs/plans/2026-09-14-conformance-cut-29-run
just check > docs/plans/2026-09-14-conformance-cut-29-run/check.log 2>&1
just test > docs/plans/2026-09-14-conformance-cut-29-run/test.log 2>&1
(cd python && uv run --frozen python tools/cut29_acceptance.py > ../.cut29-acceptance/run.log 2>&1)
cp .cut29-acceptance/run.log docs/plans/2026-09-14-conformance-cut-29-run/certified.log
```

All three commands exited **0**. The retained transcripts are
[`check.log`](2026-09-14-conformance-cut-29-run/check.log),
[`test.log`](2026-09-14-conformance-cut-29-run/test.log), and
[`certified.log`](2026-09-14-conformance-cut-29-run/certified.log). Their
post-redaction SHA-256 digests are, respectively,
`d5424bcee7762cbbe6984a40afde998e2f978aa7266f00b8f276e5fbf23f59c4`,
`bde32a9f9f183dd907606bbbe54a23d81cdc3a4313ac62b1594d9b9d4747cb2a`, and
`47fe6542abbf8afc51be4cd835ae1700eda576cef72033ab2911e4ed8f68a353`.
No capability refusal, skip or waiver occurred.

The freeze and early implementation reports are retained with the run evidence:
[`task-1-report.md`](2026-09-14-conformance-cut-29-run/task-1-report.md),
[`task-2-report.md`](2026-09-14-conformance-cut-29-run/task-2-report.md), and
[`task-3-report.md`](2026-09-14-conformance-cut-29-run/task-3-report.md).

The prefix chain was cut 29 → cut 28 → cut 27 → cut 26 → cut 25 → cut 24 →
cut 23 → cut 22 → cut 21 → cut 20 → cut 19 → cut 18 → cut 17.
Its **42 module summaries report 689 passed**:

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 24 passed in 12.54s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 43 passed in 47.13s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 17.29s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 6.61s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 30.71s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.11s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 14.62s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 313.29s (0:05:13) |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 122.82s (0:02:02) |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 15.28s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 13.96s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 79.36s (0:01:19) |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 45.15s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 67.85s (0:01:07) |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 78.07s (0:01:18) |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.23s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.61s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 110 passed in 26.89s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 15.43s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 54.73s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 26.96s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 31.63s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 27.46s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 39.96s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 33.79s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.27s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.09s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.48s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.12s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 118.63s (0:01:58) |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 43.57s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 88.47s (0:01:28) |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 23.63s |
| cut25 phase 2/3 | `test_source_address_acceptance.py` | 20 passed in 30.72s |
| cut25 phase 3/3 | `test_n2_cut25.py` | 8 passed in 8.51s |
| cut26 phase 2/2 | `test_n2_cut26.py` | 10 passed in 1.40s |
| cut27 phase 2/3 | `test_world_audit_acceptance.py` | 42 passed in 224.33s (0:03:44) |
| cut27 phase 3/3 | `test_n2_cut27.py` | 9 passed in 51.11s |
| cut28 phase 2/3 | `test_world_selection_acceptance.py` | 25 passed in 113.45s (0:01:53) |
| cut28 phase 3/3 | `test_n2_cut28.py` | 9 passed in 39.92s |
| cut29 phase 2/3 | `test_dataset_address_acceptance.py` | 10 passed in 7.57s |
| cut29 phase 3/3 | `test_n2_cut29.py` | 9 passed in 5.44s |

```text
declared arms: 6 (= 3 declaration units; 3 guarantee rows)
```

The root `just check` transcript reports Ruff clean; Pyright zero errors,
warnings and information diagnostics; TypeScript typecheck and Biome clean;
and `tasks check` zero errors and warnings. The root `just test` transcript
reports **4,645 Python tests passed in 1,086.99s (0:18:06)** and **142
TypeScript tests passed across 7 files**.

The retained `test.log` has one documentation-only redaction: Vitest's
machine-specific checkout root was replaced with
`.worktrees/world-resolution-slice-5/ts`. Test output, counts and timings are
otherwise unchanged. The successful certified transcript required no
redaction.

## 2. Accounting and disposition

Cut 29 reads three guarantee rows on their dataset arms and closes none newly:
W2 and W3 keep their closed status; W8 remains partial only on its
ambiguous-search-term conflict. Three declaration units carry 6 arms. The
closed count stays at **153 of 196**, with **43 open**. The generated accounting
reports exactly `Closed 153 of 196; open 43.`

- **W2 stays closed.** Stored dataset ids and every address-bearing reader now
  agree with the ruled content-identity fold.
- **W3 stays closed.** The builder and governed write boundary still refuse a
  dataset without its required content identity.
- **W8 remains partial.** Dataset address disagreement is refused at the write
  boundary and at both inputs of `consolidate`; only the
  ambiguous-search-term conflict remains.

## 3. Corrections and deviations from the frozen cut

The frozen cut's §§2–7 and the canonical declaration did not change. The
measured implementation and review corrections were:

- **Cut 20 F8 live adapter.** The frozen sabotage matched the former dataset
  builder return. A dated adapter retargets the same undeclared-provenance
  mutation at the derived-address return; the canonical cut 20 declaration
  and acceptance re-export remain unchanged.
- **Cut 7 X9 live adapter.** The existing dated adapter follows the migrated
  derived dataset reference while preserving the frozen declaration.
- **Cut 25 W1-a live adapter.** The source-address comparison was narrowed to
  its source clause after the dataset-address clause acquired the same generic
  shape. Guards for cuts 26–29 apply that same W1-a-only normalization when
  comparing their live imported prefix; all canonical declarations and pins
  remain unchanged.
- **Fixture migration and independent oracles.** All live dataset references
  now use their derived addresses. Boundary, snapshot, coreference and
  structural-membership probes retain independent observations instead of
  deriving expected values from the code under test.
- **Raw-write durable fixtures.** Tests that stage intentionally invalid raw
  records clear the selected root through the existing `_forget_roots_under`
  helper and reopen it before the governed move or consolidation boundary, so
  cached writer state cannot mask the staged record.
- **Decoded lineage route order.** The first certified attempt exposed a
  pre-existing mismatch: stored lineage routes use canonical `v1` order while
  `Basis` requires its decoded `Route` values in the lineage value's field
  order. `lineage_snapshot` now sorts only the decoded values with the existing
  `_route_sort_key`; stored route identity, order, traversal positions and
  input-validation semantics remain unchanged. A deterministic opposing-order
  regression failed before and passed after the repair.
- **Cut 28 corruption fixture.** The second certified attempt found a W8b
  world-level corruption fixture admitting a deliberately forged dataset id
  through the newly governed boundary. That one invalid record is now staged
  through the existing raw-write helper; the valid twins still use ordinary
  admission and every precedence and corpus-local assertion remains.

The failed attempts are retained as diagnostics in
[`certified-failed.log`](2026-09-14-conformance-cut-29-run/certified-failed.log)
(SHA-256 `1e23170763a9ce6f9c52ac8770deb689b0e5e12d4f3c064024c9ce1f43c45a16`)
and
[`certified-failed-2.log`](2026-09-14-conformance-cut-29-run/certified-failed-2.log)
(SHA-256 `3dc9998be33a9fe1343f8b7554fd19a2df8ee23864080ff1fd0908d7067d239a`).
Their machine-specific temporary or checkout prefixes were replaced by
`<pytest-temp>/` and the main-checkout-relative `.cut29-acceptance/` path.

The certified runner selected scratch beneath
`.cut29-acceptance/world-resolution-slice-5` in the main checkout because its
measured tuple matches the allowlist: backend `linux/linux-4`, kernel
`7.2.2-arch1-1`, ext4 options `async,barrier=1,commit=5,data=ordered`, storage
profile `flush-honoring-disk.v1`, and feature masks
`compat=0x3c,incompat=0x246,ro_compat=0x46b`. The implementation continued to
execute from this worktree, whose physical volume measured
`compat=0x103c,incompat=0x22c6,ro_compat=0x1046b`; no certification rule or
allowlist was weakened.

No allowlist, frozen declaration, frozen cut body or cited-not-run guard was
changed.

### Post-review focused evidence

The review-only changes after `f06834f` did not alter production code or the
frozen evidence. They added the independent replacement-preflight regression,
strengthened two no-effect snapshots to compare file contents, retained the
first three task reports, and corrected migrated-call formatting and this
accounting. The prior 4,645-Python + 142-TypeScript root run and the exact-chain
42-module/689-pass run above remain the final complete and certified runs; the
following is additional focused evidence, not a relabeling of either run.

With the four `SCIENCE_CUT*_ROOT` variables above exported:

```text
cd python && uv run --frozen pytest \
  tests/test_corpus_write.py::test_replace_preflight_refuses_a_dataset_whose_address_disagrees \
  tests/test_relocation.py::test_move_refuses_a_handle_addressed_dataset_into_a_governed_destination \
  tests/acceptance/test_dataset_address_acceptance.py::test_w8_consolidate_judges_both_declarations_before_it_discards_one_durably \
  tests/acceptance/test_world_audit_acceptance.py::test_the_world_audit_reproduces_every_per_record_finding_durably
5 passed in 6.07s

cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/acceptance/test_n2_cut29.py
23 passed in 6.13s

cd python && uv run --frozen ruff check <seven touched Python files>
All checks passed!

cd python && uv run --frozen pyright
0 errors, 0 warnings, 0 informations

tasks check
zero errors, zero warnings

git diff --check
passed

just hook-pre-commit
Ruff clean; Pyright 0 errors, 0 warnings, 0 informations; TypeScript typecheck
passed; Biome checked 15 files with no fixes; tasks check zero errors and warnings
```

## 4. Reproduction measurement

This cut performs **no new mm30 reproduction run**. The previous single-corpus
measurement remains [cut 22 results §4](2026-09-08-conformance-cut-22-results.md#4-reproduction-measurement)
and the [mm30 record](../designs/2026-09-05-mm30-reproduction.md). The dataset
addresses recorded there are what the builder now derives. No new mm30 digest
comparison or isolated causal claim is made here.

## 5. Remaining boundary

`world-resolution` retains one filed follow-up: divergent correction-history
reconciliation (`beliefs-24b42b`).

`authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**.
`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm. The ledger's manifest-safety item
remains unowned and unselected.

## 6. Main integration

Pending controller merge and the gate on merged `main`.
