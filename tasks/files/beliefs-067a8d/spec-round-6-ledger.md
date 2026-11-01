# Spec round 6 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 on frozen 68fa37f (spec-round-6-report.md). Controller: claude-code/claude-opus-5-5 (main session).
Verdict accept; the spec stays frozen at 68fa37f. The five minors are assigned to the implementation plan, not a spec edit.

- minor (deferred) M1: the plan's forced-gate fixture case asserts check-hygiene, check-code, test rows in order, each ran/forced, no check or gate row, under automatic_broad = false.
- minor (deferred) M2: the plan's AGENTS.md text defines full-gate evidence as the consecutive check-hygiene, check-code and test rows of one invocation (same rev, dirty, content), each ran; under policy-off that needs TT_FORCE=1.
- minor (deferred) M3: the plan validates the evidence path per test runner (pytest, Vitest) through focused local checks before the publication push.
- minor (deferred) M4: the plan's activation-packet task includes wholly skipped modules with the other Durable coverage evidence items.
- minor (deferred) M5: the plan's first commit that touches the spec (its status line on approval) lists round 4 (5237cb7, accept) and records round 5 as codex/gpt-6.1-sol relayed by the user. Why deferred: a status-line wording mismatch changes no requirement. Cost (if wrong): the frozen 68fa37f status line misdescribes review history until that commit.
