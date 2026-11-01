---
id: beliefs-067a8d
title: Adopt shared broad-test policy and remote verification
status: doing
priority: 1
size: m
complexity: mid
process: planned
owner: design/067a8d-test-policy
created: 2026-10-29T13:45:23Z
updated: 2026-11-01T02:38:52Z
started: 2026-11-01T01:56:52Z
depends: [ops-68729d]
tags: []
source: "tt-policy:beliefs"
agent: codex
origin: agent
spec: docs/superpowers/specs/2026-10-31-test-execution-policy-design.md
---

Adopt the approved shared test execution policy for this personal project after the ops pilot. Owner: the next beliefs implementer; Keith approves external activation. State: pending preparation, not offloaded. Shared authority: ops-8bfa85 (read its approved spec and plan with tasks doc); pilot prerequisite ops-68729d.

Observed 2026-10-29: code checkout is its own Git top level; records kind in-tree; profile personal. Current policy file: absent (enabled). Wrapper: {"tools/tt": "# tt version 7"}. Commands: test-fast, test-one, test, check, setup, hook-pre-commit, hook-pre-push, ci-python. Read [ref:front-door] for actual commands and setup. Workflows: .github/workflows/ci.yml.

Current command/ref declarations:
```
py_test_cmd := py_fast_cmd + " && (cd python && uv run --frozen pytest tests/test_n2.py)"
ts_test_cmd := "(cd ts && npm test)"
fast_cmd := py_fast_cmd + " && " + ts_fast_cmd
test_cmd := py_test_cmd + " && " + ts_test_cmd
one_cmd := "cd python && uv run --frozen pytest"
ci_suite_refs := "refs/heads/main"
ci_remote := "origin"
```

Prepare a reviewed project-specific design/plan and isolated worktree. Adopt the published wrapper only after ops and obs readers are live. Keep test-one/focused implementation checks and mandatory hygiene on; split broad lint/type/test work into explicit targets. Preserve current selectors and argument forwarding. Add the forced test-full route. Verify branch/ref coverage against workflow triggers and use explicit TT_FORCE=1 for the full remote suite, including nested recipes. One suite per push, latest-ref cancellation, no duplicate internal-PR run. Keep local policy enabled until an approved hosted invocation finishes with a nonzero test count and accepted coverage.

Inventory capability omissions and private sibling checkouts from actual workflow/setup; none are presumed equivalent to local verification. The current workflow sets VERIFIABLY_UNCERTIFIED_HOST=1; explicitly count certified-volume omissions. Preserve existing Python matrix and Python/TypeScript jobs and atoms/nodes sibling checkouts.

Prepare the activation packet with current private-repository allowance and enforced no-paid-overage setting, setup, exact refs, executed tests, excluded modules and skipped-test/module counts. Publishing workflows, live global instruction/hook delivery and account changes require explicit approval. Existing work/external/shared Git roots are not independent opt-ins. Reuse host/profile proof only for identical setup paths. Detached records remain separate from code policy lookup.

After approved activation, commit .tt.toml with real broad target names, verify focused execution/recorded skip/forced failure/covered remote push, and retire each disabled timing obligation explicitly without claiming performance verification. Record the actual activation revision/time here. On hook-split integration and rollback write exactly: policy: enabled at <RFC3339-UTC> revision <full-sha>. This record's source tt-policy:beliefs is the latency floor lookup key. Keep remaining diagnosis and unrelated obligations. Report status to ops-39bff6; never label pending work as offloaded. The first actual activation files the 30-day regret review under ops; no scheduler and no invented date.

## References

- front-door (input, required, kind=configuration): justfile

## Notes

- 2026-10-29T13:45:23Z (add): created
  provenance: {"harness_session":"codex:01a1874f-c2d8-7320-ae81-7114e37e343f","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-11-01T01:56:52Z (main): started
  provenance: {"harness_session":"claude-code:b2bff3ba-0ad3-458f-809d-bb8b1806af58","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:00:44Z (design/067a8d-test-policy): resumed
  provenance: {"harness_session":"claude-code:b2bff3ba-0ad3-458f-809d-bb8b1806af58","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:03:51Z (design/067a8d-test-policy): Planned path in .worktrees/067a8d-test-policy on design/067a8d-test-policy; locked worktree hydrated with just setup (npm ci + Dropbox ignore attr). Full-suite baseline deferred to implementation Setup per planned-work rule. tools/tt already version 9 (body's version 7 stale). No test-latency or halt tasks open. Repo public (gh API, khughitt): hosted standard runners free, no-paid-overage inapplicable while public.
- 2026-11-01T02:04:00Z (design/067a8d-test-policy): Origin: agent-filed adoption child of ops-8bfa85 (source tt-policy:beliefs); originating human ask in codex:01a1874f-c2d8-7320-ae81-7114e37e343f as recovered on nodes-6fde14's origin note. Project-specific calls in the spec are the designer's, marked as such. Spec frozen at 60b6487 docs/superpowers/specs/2026-10-31-test-execution-policy-design.md; fresh reviewer dispatched.
- 2026-11-01T02:11:09Z (design/067a8d-test-policy): review: spec round 1 — verdict: revise; findings: Important 5, Minor 10; reviewer: claude-code/claude-opus-5-5
- 2026-11-01T02:13:51Z (design/067a8d-test-policy): attached: spec-round-1-report.md (9607 bytes): Full spec round 1 review of frozen 60b6487 by claude-code/claude-opus-5-5: revise, Important 5, Minor 10
- 2026-11-01T02:13:54Z (design/067a8d-test-policy): attached: spec-round-1-ledger.md (2931 bytes): Controller rulings for all 15 spec round 1 findings; all accepted, none deferred
- 2026-11-01T02:21:13Z (design/067a8d-test-policy): review: spec round 2 — verdict: revise; findings: Important 3, Minor 7; reviewer: claude-code/claude-opus-5-5
- 2026-11-01T02:23:47Z (design/067a8d-test-policy): attached: spec-round-2-report.md (10824 bytes): Full spec round 2 review of frozen e2927dd by claude-code/claude-opus-5-5: revise, Important 3, Minor 7
- 2026-11-01T02:23:50Z (design/067a8d-test-policy): attached: spec-round-2-ledger.md (1785 bytes): Controller rulings for all 10 spec round 2 findings; all accepted, none deferred
- 2026-11-01T02:30:56Z (design/067a8d-test-policy): review: spec round 3 — verdict: revise; findings: Important 1, Minor 4; reviewer: claude-code/claude-opus-5-5
- 2026-11-01T02:33:02Z (design/067a8d-test-policy): attached: spec-round-3-report.md (9097 bytes): Full spec round 3 scoped re-review of frozen 2cee097 by claude-code/claude-opus-5-5: revise, Important 1, Minor 4
- 2026-11-01T02:33:06Z (design/067a8d-test-policy): attached: spec-round-3-ledger.md (1418 bytes): Controller rulings for all 5 spec round 3 findings; all accepted, none deferred
- 2026-11-01T02:37:28Z (design/067a8d-test-policy): review: spec round 4 — verdict: accept; findings: Minor 3; reviewer: claude-code/claude-opus-5-5
- 2026-11-01T02:37:36Z (design/067a8d-test-policy): attached: spec-round-4-report.md (7820 bytes): Full spec round 4 scoped re-review of frozen 5237cb7 by claude-code/claude-opus-5-5: accept, Minor 3
- 2026-11-01T02:37:44Z (design/067a8d-test-policy): attached: spec-round-4-ledger.md (1327 bytes): Controller rulings: all three round 4 minors assigned to the implementation plan; design stays frozen at 5237cb7
- 2026-11-01T02:38:33Z (design/067a8d-test-policy): retained: {"host":"titan","kind":"worktree","path":".worktrees/067a8d-test-policy","state":"kept","verification":"verified","purpose":"Frozen design 5237cb7 (sha256 561c57b87c5c05cf8f15890646d0d7c3e8a3669078f3b4d828d91a3a4bb1922d) and four attached review rounds await user design review; branch design/067a8d-test-policy unmerged; ignored entries only python/.venv and ts/node_modules (regenerable)","next_owner":"task:beliefs-067a8d","cleanup_trigger":"After user design and plan review, implementation, activation and authorized integration of design/067a8d-test-policy, rerun the ignored-file, host-pointer and tt-report checks before removal"}
- 2026-11-01T02:38:38Z (design/067a8d-test-policy): retention checkpoint: observed 2026-11-01T02:38:38Z on titan; basis beliefs in-tree . 7ed73f40b9c9f20ff7050bf1d3615498a77e7416:tasks/beliefs-067a8d.md; retained by refs/heads/design/067a8d-test-policy; this host: kept verified 1, kept unknown 0, released 0; changed 1. Rechecked all kept/verified items on this host; session scratchpad copies of the eight attached review files were byte-verified against their attachments and are not retained. No host pointer or process points into the worktree. Other hosts hold no items.
  provenance: {"harness_session":"claude-code:b2bff3ba-0ad3-458f-809d-bb8b1806af58","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:38:52Z (design/067a8d-test-policy): parked (waiting on user, review): User reviews frozen 5237cb7:docs/superpowers/specs/2026-10-31-test-execution-policy-design.md (sha256 561c57b87c5c05cf8f15890646d0d7c3e8a3669078f3b4d828d91a3a4bb1922d) in .worktrees/067a8d-test-policy. After approval the agent resumes there and writes the implementation plan, folding in the three round 4 minors per spec-round-4-ledger.md. No implementation, push or activation yet.
  provenance: {"harness_session":"claude-code:b2bff3ba-0ad3-458f-809d-bb8b1806af58","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
