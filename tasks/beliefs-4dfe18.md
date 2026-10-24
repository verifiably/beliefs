---
id: beliefs-4dfe18
title: "Guide and glossary: 'autonomy layer is not started' is stale, and the canonical value encoding has no glossary entry"
status: doing
priority: 3
size: xs
complexity: low
process: direct
owner: docs/4dfe18-guide-glossary
created: 2026-10-23T18:52:19Z
updated: 2026-10-24T16:05:41Z
started: 2026-10-24T15:22:16Z
depends: []
tags: [docs]
agent: claude-code/claude-opus-5-5
---

Found 2026-10-23 during a guided tour of beliefs (vdocs-9ca77b). (1) docs/guide/README.md (updated 2026-09-26), Status and authority, says 'The autonomy layer is not started'; autonomy's README now lists tiers, the closing check, the sandbox and autonomy run's launch side as built. Correct the sentence against autonomy's own state authority. (2) ts/README.md and python/README.md name the 'shared encoding' / canonical value contract (science.identity.v1, computation §4.3) without defining it, and the glossary has no entry for it; a newcomer on the tour had to ask what it means. Add a glossary entry (one value, one byte spelling; type survives encoding; per-kind domain-separated digest; the only cross-implementation contract) linking computation §4.3. Leave the subsystem README rewrite to beliefs-e3ca2a / vdocs-946c49.

## Notes

- 2026-10-24T15:22:16Z (main): started
  provenance: {"harness_session":"codex:01a16e80-c499-7db3-aef2-c8e3475cdc37","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-24T15:22:50Z (docs/4dfe18-guide-glossary): resumed
  provenance: {"harness_session":"codex:01a16e80-c499-7db3-aef2-c8e3475cdc37","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-24T15:23:24Z (docs/4dfe18-guide-glossary): Scope confirmed: update docs/guide/README.md against autonomy README (built envelope components; science run endpoint still unwired), add canonical value encoding beside canonical projection in docs/guide/glossary.md, and refresh both updated dates. Keep subsystem README rewrites with their existing task. Workspace: .worktrees/4dfe18-guide-glossary; direct process; just setup completed; full baseline just test running before edits.
- 2026-10-24T15:44:24Z (docs/4dfe18-guide-glossary): Baseline just test: non-N2 phase passed 6230 tests, 1 skipped in 907.59s under a contended host budget; N2 still running. No document edits yet.
- 2026-10-24T16:05:41Z (docs/4dfe18-guide-glossary): Baseline just test passed before edits: 6230 non-N2 Python tests passed, 1 skipped (907.59s); 46 N2 tests passed (1603.68s); 155 TypeScript tests passed. Updated only guide status, canonical value encoding glossary entry and the two updated dates; matched identity semantics to both implementations and computation section 4.3.
