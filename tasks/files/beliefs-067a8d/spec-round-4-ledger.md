# Spec round 4 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 scoped re-review of frozen 5237cb7 (spec-round-4-report.md): accept, Minor 3. Controller: claude-code/claude-opus-5-5 (main session).
The design stays frozen at 5237cb7 for user review. All three minors are assigned to the implementation plan, the nodes round-4 precedent; none is deferred past it.

- Ruling M1: assign to plan. The fixture task specifies: host-budget stub checks `run --` and execs the rest; `tasks where` answers fixture project JSON without logging or FAIL_STEP (or the fixture carries tasks/.config.toml); fixture has python/ and ts/, Python-source ops-check/ops-docs stubs, absolute BELIEFS_CI_EVIDENCE_DIR; the fixture policy carries the exact broad_targets list. Why: builder-level fixture detail inside the spec's contract. Cost (if wrong): a RED-phase surprise, caught at RED.
- Ruling M2: assign to plan. The test-one forwarding case moves into the fixture checkout with --set one_cmd; no case runs with cwd=ROOT. Why: resolves the wording conflict in favour of the stricter sentence. Cost: none.
- Ruling M3: assign to plan. The commit that widens ci.yml's trigger also rewrites the justfile ci_suite_refs comment and AGENTS.md's Remote CI line. Why: repo rule on correcting stale claims in the same change. Cost: none.
