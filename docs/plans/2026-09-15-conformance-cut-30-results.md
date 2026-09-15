# Conformance cut 30 — results

**Cut:** `../designs/2026-09-15-conformance-cut-30.md`
**Subject:** divergent correction histories reconciled at `consolidate`
**Discharged:** 2026-09-15, on `design/world-resolution-slice-6`
**Runner:** `python/tools/cut30_acceptance.py`

## 1. What ran

`just check` exited 0 ([`check.log`](2026-09-15-conformance-cut-30-run/check.log), SHA-256 `bedf62488c69a8b34dd258c517ca283a22ecaa018a8d3559887535130dbc5957`). `just test` exited 0: 4,690 Python passed in 1,131.32s and 142 TypeScript tests passed across seven files ([`test.log`](2026-09-15-conformance-cut-30-run/test.log), SHA-256 `442b26ff34bb6c2bfa113cad3de7991322dd43f0ff4d4015f30d2cb046e18b93`). The certified aggregate exited 0: 44 module summaries and 720 tests passed, with no failed, skipped, ERROR, or `CapabilityUnavailable` lines ([`certified.log`](2026-09-15-conformance-cut-30-run/certified.log), SHA-256 `efd8d99c69c3b1aecddc679bf00281e2819f900f5ef6e4c8b2a55a839ae067fd`).

The preliminary full suite is retained at [`test-incomplete-docs.log`](2026-09-15-conformance-cut-30-run/test-incomplete-docs.log), SHA-256 `341232b9803c0597555c14554a6c568d73ad5ce00ce386471fd1f7e9a0119133`: 4,688 passed and two current-state guards failed because the ledger and roadmap named cut 30 before this record existed. It was corrected by creating this record and proven narrowly before the one final full run.

## 2. Accounting

Zero guarantee rows are read, **0 full/closed** newly; one declaration unit,
W5a, re-read on ten reconciliation arms; W8 unchanged.

## 3. Evidence

No allowlist, frozen declaration, frozen cut body or cited-not-run guard was
changed; cut 25's `W5a-m` is re-targeted live in `test_n2_cut25.py`. Task 4
also moved cut16 W16b/D7b; Task 6 live-retargeted them preserving original
assertions/checks, plus planned cut25 W5a-m. The frozen cut 30 did not include
guard16, so the implementation boundary expanded accordingly.

The full gate exposed a static audit false positive: `copy.deepcopy` in the new reconciliation function was classified as a filesystem copy. The audit now recognizes the stdlib `copy` module and has a regression proving it still detects `shutil.copy` in the same module.

## 4. Reproduction measurement

None: no source is consolidated in the mm30 corpus.

## 5. Remaining boundary

`world-resolution` retains no filed follow-up and leaves the ledger.
`authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**.
`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm.

## 6. Main integration

Main integration is pending controller merge, merged-main verification, and
worktree cleanup.
