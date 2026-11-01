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
updated: 2026-11-01T02:11:09Z
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
