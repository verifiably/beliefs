---
id: beliefs-5bda3a
title: Fix the final session-routes plan review findings
status: done
priority: 1
size: xs
owner: kernel-seams
created: 2026-09-09T22:50:30Z
updated: 2026-09-09T22:51:22Z
depends: []
tags: [command-framework]
---

Correct both DeleteOp fixtures to supply expected_digest and defer the ledgered_seam export until Task 5. Verify the snippets and commit the plan correction.

## Notes

- 2026-09-09T22:50:44Z (kernel-seams): Claimed by Codex root for the two authorized plan corrections.
- 2026-09-09T22:51:22Z (kernel-seams): Both DeleteOp refusal snippets pass with explicit digests; Task 4 passes the undefined-export check and Task 5 adds its export with the function.
