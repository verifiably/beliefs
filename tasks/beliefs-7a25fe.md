---
id: beliefs-7a25fe
title: Reject sharing evidence that cannot encode as UTF-8 before either sharing door acts
status: todo
priority: 1
size: xs
complexity: low
process: direct
created: 2026-10-23T14:24:20Z
updated: 2026-10-23T14:24:20Z
depends: []
tags: [publication]
agent: claude-code
---

SharingEvidence accepts source or location holding an isolated surrogate (e.g. "copy-\udcff"); restore_root grants serviceability, or admit_publication commits the admission, and only then encode_line raises UnicodeEncodeError, so the transition happens with no sharing line and the session stays healthy. Validate UTF-8 encodability of source and location in SharingEvidence.__post_init__ (ValueError), and of record_sharing's verdict; tests per field and door proving refusal precedes either act. Found by codex/gpt-6.1-sol review of beliefs-f24fe9 after merge (b923277), reproduced on real roots for all four field x door combinations.
