# Spec round 1 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 on frozen 60b6487 (spec-round-1-report.md). Controller: claude-code/claude-opus-5-5 (main session).
All 15 findings accepted and corrected in the next frozen revision; none deferred.

- Ruling I1: accept. Routing fixtures declare their own ci_suite_refs; contract test pins live ci_suite_refs globs against ci.yml push.branches; activation commit runs test-one tests/test_front_door.py and the workflow contract test first; warning case uses a backup remote. Why: widening would otherwise redden routing tests unseen until the hosted activation run. Cost (if wrong): one extra test file assertion to maintain.
- Ruling I2: accept. Certified section names test-fast (134), test (18), hook-pre-push-fast (15) as all stopping. Why: the approved gap must be stated at its real size. Cost: none.
- Ruling I3: accept. Hosted JUnit skips with the conftest "certified tuple unavailable on this host:" prefix become the named focused list, recorded in the packet; TT_FORCE=1 just test-fast named as the non-N2 sweep; report-the-exact-mismatch duty kept. Why: no maintained list exists; the probe defines the set at run time. Cost: the hosted list can lag a newly capability-dependent test until the next hosted run.
- Ruling I4: accept. Eligibility defined (pytest default patterns minus tests/acceptance, test_n2.py in pytest-n2.xml; ts/tests/*.test.ts); nonzero executed count per phase per job; every skip reasoned, non-capability skips must match the local baseline by reason. Why: implementer would otherwise guess acceptance. Cost: a legitimately new skip reason blocks until explained.
- Ruling I5: accept. atoms/nodes HEAD revisions in the module inventory and packet; sibling visibility rechecked at activation. Why: attribution of hosted failures and the regret review. Cost: none.
- Ruling M1: accept; state the host-budget change for push-hook check-code (policy-on only).
- Ruling M2: accept; reword ci-* broad rationale.
- Ruling M3: accept; rollback restores refs/heads/main (pre-adoption cadence), workflow trigger may stay. Why: rollback returns to the known baseline. Cost: feature pushes pay full local gate again after a rollback.
- Ruling M4: accept; packet records org Actions spending-limit state if readable read-only, else the explicit deviation.
- Ruling M5: accept; warning fixture copies tools/tt beside its isolated .tt.toml.
- Ruling M6: accept; downloaded artifacts or derived counts attached to beliefs-067a8d.
- Ruling M7: accept; enabled-floor note on beliefs-067a8d at hook-split integration (new step 6, before pushes); ops-39bff6 is done, report is a note on a closed record.
- Ruling M8: accept; mm30-recreate and cut runners described as not tt-wrapped.
- Ruling M9: accept; workflow contract tests handle PyYAML's on: -> True and fail on a missing key.
- Ruling M10: accept; tags worded as observation, pin/cut6-* named.
