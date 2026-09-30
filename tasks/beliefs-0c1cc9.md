---
id: beliefs-0c1cc9
title: Make the cut-31 reproduction transition measurement repeatable
status: done
priority: 3
size: s
complexity: mid
process: direct
owner: feat/beliefs-0c1cc9
created: 2026-09-16T20:09:21Z
updated: 2026-09-30T00:00:18Z
started: 2026-09-29T23:51:26Z
completed: 2026-09-30T00:00:18Z
depends: []
parent: beliefs-cde4d9
tags: [conformance, reproduction]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

Why: The cut-32 results and reproduction record §11.5 record a transition measurement that no committed driver step re-runs. Static inspection still finds cut31_corpus_state only in state.py documentation.

Done: Add a small reproduction step that opens the preserved cut-31 corpus read-only under vocabulary.profile(), runs audit_corpus with the held rule implementations, and records the observed findings, corpus id, base pin and record-read count as state.cut31_corpus_state. Measure exactly profile-mismatch: base and zero record reads; return a failing verdict for any other result. Require the archived corpus explicitly (an argument or the existing WORK sibling convention); missing input fails loudly, never substitutes the current corpus or skips. Preserve the archived corpus and its bytes. Keep rederive.prior_state's cut-22 behavior intact.

Verification: Add a focused regression in python/tests/test_reproduction_driver.py covering the transition result, zero reads, missing input and a wrong verdict. Run just test-one tests/test_reproduction_driver.py. When the preserved cut-31 corpus is available, run the new step against it and record its result and read-only check; otherwise state that the historical artifact measurement remains unverified. Append current evidence to the reproduction record without rewriting historical cut bodies.

Where to look: python/tools/reproduction/rederive.py::prior_state, paths.py, state.py; python/src/beliefs/audit.py::audit_corpus; docs/designs/2026-09-05-mm30-reproduction.md §11.5; docs/plans/2026-09-16-conformance-cut-32-results.md §3.3. Handoff: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md

## Original capture

The mm30 reproduction record's §11.5 measurement — the cut-31 corpus state audited read-only under the successor profile, returning exactly 'profile-mismatch: base' and reading no record — was taken by a one-shot script that is not in the tree, and its result is saved as state.cut31_corpus_state in the recreated corpus. Nothing committed reads that key: the driver has no step for it and no acceptance arm asserts it, so decision 11's transition arm is a recorded measurement with no way to re-run it. Give the driver a step (as rederive.prior_state already is for the cut-22 state) or an acceptance arm that reads the key, so the next recreation measures the transition rather than restating it.

## Notes

- 2026-09-29T22:59:41Z (main): scope: scoped; P3/s/mid/direct; committed read-only transition step with an observed mismatch and zero-read check; original capture preserved; brief: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
- 2026-09-29T23:51:26Z (feat/beliefs-0c1cc9): started
  provenance: {"harness_session":"claude-code:d4d2dc53-33e1-4e0d-a9c8-0f172598281e","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-29T23:51:26Z (feat/beliefs-0c1cc9): claimed by claude-code/claude-fable-5-1, harness pid 2351564; process direct in .worktrees/beliefs-0c1cc9
- 2026-09-30T00:00:18Z (feat/beliefs-0c1cc9): done
  provenance: {"harness_session":"claude-code:d4d2dc53-33e1-4e0d-a9c8-0f172598281e","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T00:00:18Z (feat/beliefs-0c1cc9): Step 13 (reproduction.transition) re-runs the cut-31 transition measurement: exit 0 only on profile-mismatch: base with zero records read; run against the preserved archive reproduced the 2026-09-16 value with the archive unchanged (record §24)
  provenance: {"harness_session":"claude-code:d4d2dc53-33e1-4e0d-a9c8-0f172598281e","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
