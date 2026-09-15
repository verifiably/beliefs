# Conformance cut 30 — results

**Cut:** `../designs/2026-09-15-conformance-cut-30.md`
**Freeze:** `11d7e1f2048292ee8ebe0def4f43fb98ab0be8eb`; SHA-256 `0aab3895c2532f1a0760dd232c61085db6873ca75d28fcec014ca3a7015b07d7`
**Declaration:** `31b083eaaa9c035cf645146d017ad6760c0cc3c3`; SHA-256 `6c2db675d6793eff3bf3fb65a59438e7ce59064308c061c1e1d18f8cab5a97bd`
**Subject:** divergent correction histories reconciled at `consolidate`
**Discharged:** 2026-09-15, on `design/world-resolution-slice-6`
**Runner:** `python/tools/cut30_acceptance.py`

## 1. What ran

```sh
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
for v in 4 7 10 29 30; do export SCIENCE_CUT${v}_ROOT="$MAIN_CHECKOUT/.cut30-acceptance/world-resolution-slice-6"; done
just check > docs/plans/2026-09-15-conformance-cut-30-run/check.log 2>&1
just test > docs/plans/2026-09-15-conformance-cut-30-run/test.log 2>&1
(cd python && uv run --frozen python tools/cut30_acceptance.py > "$MAIN_CHECKOUT/.cut30-acceptance/run.log" 2>&1)
```

`just check` exited 0 ([`check.log`](2026-09-15-conformance-cut-30-run/check.log), SHA-256 `bedf62488c69a8b34dd258c517ca283a22ecaa018a8d3559887535130dbc5957`). `just test` exited 0: 4,690 Python passed in 1,131.32s and 142 TypeScript tests passed across seven files ([`test.log`](2026-09-15-conformance-cut-30-run/test.log), SHA-256 `442b26ff34bb6c2bfa113cad3de7991322dd43f0ff4d4015f30d2cb046e18b93`). The certified aggregate exited 0: 44 module summaries and 720 tests passed, with no failed, skipped, ERROR, or `CapabilityUnavailable` lines ([`certified.log`](2026-09-15-conformance-cut-30-run/certified.log), SHA-256 `efd8d99c69c3b1aecddc679bf00281e2819f900f5ef6e4c8b2a55a839ae067fd`).

The preliminary full suite is retained at [`test-incomplete-docs.log`](2026-09-15-conformance-cut-30-run/test-incomplete-docs.log), SHA-256 `341232b9803c0597555c14554a6c568d73ad5ce00ce386471fd1f7e9a0119133`: 4,688 passed and two current-state guards failed because the ledger and roadmap named cut 30 before this record existed. It was corrected by creating this record and proven narrowly before the one final full run.

The prefix chain is cut 30 → cut 29 → cut 28 → cut 27 → cut 26 → cut 25 → cut 24 → cut 23 → cut 22 → cut 21 → cut 20 → cut 19 → cut 18 → cut 17. The certified transcript's 44 module summaries report **720 passed**; its final cut-30 phases are `test_source_address_acceptance.py` (21 passed) and `test_n2_cut30.py` (9 passed; ten arms).

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 24 passed in 12.71s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 43 passed in 48.45s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 17.15s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 6.55s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 32.31s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.18s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 15.02s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 316.24s (0:05:16) |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 126.79s (0:02:06) |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 15.32s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 14.23s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 81.11s (0:01:21) |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 45.51s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 68.83s (0:01:08) |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 78.43s (0:01:18) |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.32s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.74s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 110 passed in 28.02s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 16.29s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 55.74s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 28.07s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 32.63s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 30.74s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 40.46s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 36.47s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 9.66s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.69s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.74s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.12s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 123.27s (0:02:03) |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 43.06s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 87.31s (0:01:27) |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 23.43s |
| cut25 phase 2/3 | `test_source_address_acceptance.py` | 21 passed in 37.40s |
| cut25 phase 3/3 | `test_n2_cut25.py` | 8 passed in 8.31s |
| cut26 phase 2/2 | `test_n2_cut26.py` | 10 passed in 1.41s |
| cut27 phase 2/3 | `test_world_audit_acceptance.py` | 42 passed in 237.97s (0:03:57) |
| cut27 phase 3/3 | `test_n2_cut27.py` | 9 passed in 58.54s |
| cut28 phase 2/3 | `test_world_selection_acceptance.py` | 25 passed in 130.52s (0:02:10) |
| cut28 phase 3/3 | `test_n2_cut28.py` | 9 passed in 39.67s |
| cut29 phase 2/3 | `test_dataset_address_acceptance.py` | 10 passed in 7.65s |
| cut29 phase 3/3 | `test_n2_cut29.py` | 9 passed in 5.54s |
| cut30 phase 2/3 | `test_source_address_acceptance.py` | 21 passed in 36.90s |
| cut30 phase 3/3 | `test_n2_cut30.py` | 9 passed in 4.38s |

## 2. Accounting

Zero guarantee rows are read, **0 full/closed** newly; one declaration unit,
W5a, re-read on ten reconciliation arms; W8 unchanged.

## 3. Evidence

No allowlist, frozen declaration, frozen cut body or cited-not-run guard was
changed; cut 25's `W5a-m` is re-targeted live in `test_n2_cut25.py`. Task 4
also moved cut16 W16b/D7b; Task 6 live-retargeted them preserving original
assertions/checks, plus planned cut25 W5a-m. The frozen cut 30 did not include
guard16, so the implementation boundary expanded accordingly.

The read-only [tuple probe](2026-09-15-conformance-cut-30-run/tuple-probe.log) (SHA-256 `bfda336f0a945875b1478a5f60af27ddac71adc500179f67bdb850cd77cdc817`) measured the certified root as `linux/linux-4`, kernel `7.2.2-arch1-1`, ext4 `async,barrier=1,commit=5,data=ordered`, and masks `compat=0x3c,incompat=0x246,ro_compat=0x46b`. The declared storage profile is `flush-honoring-disk.v1`. The worktree measurement has masks `compat=0x103c,incompat=0x22c6,ro_compat=0x1046b`; no allowlist or waiver changed.

The full gate exposed a static audit false positive: `copy.deepcopy` in the new reconciliation function was classified as a filesystem copy. The audit now recognizes the stdlib `copy` module and has a regression proving it still detects `shutil.copy` in the same module.

## 4. Reproduction measurement

None: no source is consolidated in the mm30 corpus.

## 5. Remaining boundary

`world-resolution` retains no filed follow-up and leaves the ledger.
`authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**.
`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm.

## 6. Main integration

Merged `design/world-resolution-slice-6` into `main` with `--no-ff` on
2026-09-15 at `4d785f08630d97975c4fcacf6c5d6f1d8fc000f4`, after the whole-branch
review and scoped review of the final documentation fixes at `7fc856b`.
All review findings were addressed. The merge also retains main's independent
`ops-check` version 4 update from `d537fa7`.

`just gate`, run on that unchanged merged revision with the five certified-root
exports in §1, exited **0**. Ruff, Pyright, TypeScript typecheck and Biome passed;
task validation reported **zero errors and zero warnings**. The serial Python
suite reported **4,690 passed in 1,152.06s (0:19:12)**. TypeScript reported
**142 passed** across seven files. No capability refusal, skip or waiver occurred.

The output is retained in
[`main-gate.log`](2026-09-15-conformance-cut-30-run/main-gate.log), SHA-256
`7f65471fd3e7be795c5aafd123ea722b645453e90525b5b8be175d61162be555`.
Only Vitest's absolute checkout path was replaced by `./ts`; Pyright's
informational version-availability notice is retained. Earlier branch and
certified transcripts are unchanged. This integration record changes only
documentation after the gate.

The rule-6 handoff note for parked task `beliefs-705507` was committed as
`c68c61e` on `design/estimand-typing`; that lane must rebase onto main before opening.
Its stale `process_missing` task warning was resolved by mirroring main's existing
`process: direct` decision for `beliefs-f253a1`. Task validation there now reports
zero errors and zero warnings.
