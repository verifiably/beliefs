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

## 2. Accounting

Zero guarantee rows are read, **0 full/closed** newly; one declaration unit,
W5a, re-read on ten reconciliation arms; W8 unchanged.

## 3. Evidence

No allowlist, frozen declaration, frozen cut body or cited-not-run guard was
changed; cut 25's `W5a-m` is re-targeted live in `test_n2_cut25.py`. Task 4
also moved cut16 W16b/D7b; Task 6 live-retargeted them preserving original
assertions/checks, plus planned cut25 W5a-m. The frozen cut 30 did not include
guard16, so the implementation boundary expanded accordingly.

The certified runner used the main checkout's certified volume: backend `linux/linux-4`, kernel `7.2.2-arch1-1`, ext4 `async,barrier=1,commit=5,data=ordered`, storage profile `flush-honoring-disk.v1`, and masks `compat=0x3c,incompat=0x246,ro_compat=0x46b`. The implementation worktree is on the uncertified tuple `compat=0x103c,incompat=0x22c6,ro_compat=0x1046b`; no allowlist or waiver changed.

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
