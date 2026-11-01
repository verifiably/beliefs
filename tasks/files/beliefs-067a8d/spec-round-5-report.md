# Spec round 5 review — beliefs-067a8d

Reviewer: codex/gpt-6.1-sol (relayed by the user in session; read-only review, no files changed or tests run).
Revision reviewed: beliefs 5237cb7:docs/superpowers/specs/2026-10-31-test-execution-policy-design.md.
Verdict: revise. Important 2.

Verbatim as relayed:

What this change does: Moves routine broad checks to CI while preserving focused local tests and hygiene. I found two issues in frozen revision 5237cb7.

1. Important: test-full does not run the full gate. Lines 314–319 (.worktrees/067a8d-test-policy/docs/superpowers/specs/2026-10-31-test-execution-policy-design.md#L314) prescribe it when a record must cite a "full local gate," but its contract runs only test. Ruff, Pyright, TypeScript checks and hygiene are omitted. Name TT_FORCE=1 just gate for full-gate evidence, and reserve test-full for suite evidence; otherwise future conformance records could overstate verification.
2. Important: the first approval packet requires evidence generated after approval. Lines 397–417 (.worktrees/067a8d-test-policy/docs/superpowers/specs/2026-10-31-test-execution-policy-design.md#L397) require per-job capability omissions and sibling revisions before approving any push, although the new evidence-producing workflow runs after that push. Separate the initial publication packet from hosted acceptance: disclose pending counts initially, then populate and assess them before policy-off activation. Otherwise the sequence cannot be followed literally.

Verdict: revise these two points before implementation planning. The existing matrix, focused route and explicit certified-host coverage gap otherwise fit the shared design.
Reviewer: codex/gpt-6.1-sol. Read-only review; no files changed or tests run. Hosted results and account settings were not independently revalidated.
