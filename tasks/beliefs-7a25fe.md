---
id: beliefs-7a25fe
title: Reject sharing evidence that cannot encode as UTF-8 before either sharing door acts
status: doing
priority: 1
size: xs
complexity: low
process: direct
owner: fix/7a25fe-sharing-encoding
created: 2026-10-23T14:24:20Z
updated: 2026-10-23T14:43:55Z
started: 2026-10-23T14:24:42Z
depends: []
tags: [publication]
agent: claude-code
---

SharingEvidence accepts source or location holding an isolated surrogate (e.g. "copy-\udcff"); restore_root grants serviceability, or admit_publication commits the admission, and only then encode_line raises UnicodeEncodeError, so the transition happens with no sharing line and the session stays healthy. Validate UTF-8 encodability of source and location in SharingEvidence.__post_init__ (ValueError), and of record_sharing's verdict; tests per field and door proving refusal precedes either act. Found by codex/gpt-6.1-sol review of beliefs-f24fe9 after merge (b923277), reproduced on real roots for all four field x door combinations.

## Notes

- 2026-10-23T14:24:23Z (main): concerns: beliefs-f24fe9 defect — sharing doors act before discovering that the evidence cannot be encoded into the ledger line
- 2026-10-23T14:24:42Z (fix/7a25fe-sharing-encoding): started
  provenance: {"harness_session":"claude-code:297628b0-d2fd-484c-b8a9-dc5eb3247cd4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-23T14:29:56Z (fix/7a25fe-sharing-encoding): baseline: just test at ff50db0 — non-N2 6222 passed, 1 skipped; N2 46 passed; TypeScript 155 passed
- 2026-10-23T14:43:53Z (fix/7a25fe-sharing-encoding): review: impl round 1 — verdict: accept; findings: minor 3; reviewer: claude-code/claude-sonnet-5-5
- 2026-10-23T14:43:55Z (fix/7a25fe-sharing-encoding): Re-review minors: door test asserted construction behind a dead door branch (restated in 2dcf7ff); doc wording on the verdict check (fixed in 2dcf7ff); require_utf8 exported from ledger.__all__ for writer.py's import (kept).
