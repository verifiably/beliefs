---
id: beliefs-50067c
title: Cut 19's J2i arm went vacuous when port commits began marking the root unresolved (70ff54e)
status: done
priority: 1
owner: design/publish
created: 2026-09-24T14:03:37Z
updated: 2026-09-24T14:06:36Z
started: 2026-09-24T14:03:42Z
completed: 2026-09-24T14:06:36Z
depends: []
tags: [conformance, testing]
---

Main commit 70ff45e's DurableOperationPort now also marks the root unresolved (beliefs-40e593), so cut 19's frozen N2 arm J2i -- which sabotages only corpus.py's seam mark -- became vacuous: its two checks in test_session_acceptance.py still pass under the sabotage. Fix per cut-31 sec8.3 precedent: restore the check's premise in the check's own test.

## Notes

- 2026-09-24T14:03:42Z (design/publish): started
  provenance: {"harness_session":"claude-code:c93cd81e-dbd2-4766-8217-506a58a55a62","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T14:03:42Z (design/publish): Evidence: guard passes 7/7 at 38ae515 (70ff54e^); fails 1/7 (J2i) at 70ff54e, b9cd8b6 (publish baseline), and 0f490bd (publish HEAD) -- bisected in scratch worktrees. See .superpowers/sdd/2026-09-23-publish-act-local/j2i-investigation.md for full mechanism and verified diff.
- 2026-09-24T14:06:36Z (design/publish): done
  provenance: {"harness_session":"claude-code:c93cd81e-dbd2-4766-8217-506a58a55a62","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T14:06:36Z (design/publish): Restored J2i check isolation by patching science_root.mark_root_unresolved off in the two J2i checks; test_n2_cut19.py 7 passed, test_session_acceptance.py + test_operation_port.py 65 passed
  provenance: {"harness_session":"claude-code:c93cd81e-dbd2-4766-8217-506a58a55a62","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
