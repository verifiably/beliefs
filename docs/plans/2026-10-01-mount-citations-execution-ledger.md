---
title: Mount citations execution ledger (cut 44)
---

The subagent-driven execution ledger for `../superpowers/plans/2026-10-01-mount-citations.md`, committed before worktree removal. Agent ids are session-local.

# SDD ledger — plan: docs/superpowers/plans/2026-10-01-mount-citations.md

Spec: docs/superpowers/specs/2026-10-01-mount-citations-design.md (approved after 6 rounds; plan accepted round 3, 2026-10-01).
Execution: sequential subagent-driven, fresh review per task (user's choice).

## Preflight scan

| pair / task | produces → consumes | finding |
|---|---|---|
| T0 ↔ T7 | T0's cut doc §3/§5 reproduces T7 Step 1's arm table; T7 reads CUT44_FREEZE_COMMIT/SHA from T0 | consistent (24 arms, J16-a..m, J17-a/b, J18-a/b, J19-a..e, J20-a, J21-a); T0 implementer must read T7 Step 1 — carried in dispatch |
| T1 ↔ T2 | MountCitations(own, own_profile, read_mounts), holder/overlay/close → writer scope, _refuse_ineligible arms | names agree (holder, overlay); J16-i/j befores spelled after T1 |
| T1 ↔ T7 | J16-f/i/j/J17-a/b befores live in T1 code | T7 spells i/j from tree; others match T1 text |
| T2 ↔ T3 | eligibility_outcome / EligibilityOutcome(reason, unresolved) → _record_findings arm | agree |
| T3 ↔ T4 | _record_findings(..., citations=), ELIGIBILITY_CODES → two-pass audit_world | agree; reader.eligibility(node, profile) contract |
| T2 ↔ T5 | acquisition.validity_refusal reports= (T2) ; evaluation gather (T5) | disjoint files; no interface |
| T5 ↔ T6 | seed_nodes refactor, InputOutsideCorpus → acceptance | agree |
| T2/T5 ↔ arm staleness | F4 re-target (T2), B4b re-target (T5, shares J21-a before) | both foreseen in spec §13; any other stale arm = stop |
| T0 self | cut doc §4 says 10 acceptance cases = T6's count | agree |
| T1..T5 self | each task's tests target the code it specifies; reviewed 3 rounds | no internal contradiction found |
| T6..T10 self | T6 imports library_on/state/fresh from existing acceptance modules | exist on main (cut 43) |

No rulings needed at preflight.

## Progress
Step children: T0 beliefs-dd9cba, T1 beliefs-4d37cf, T2 beliefs-6242bf, T3 beliefs-9097fc, T4 beliefs-807a48, T5 beliefs-72ae3f, T6 beliefs-9482fa, T7 beliefs-a8f943, T8 beliefs-d0ced0, T9 beliefs-a910d3, T10 beliefs-e49d12 (filed by controller = Task 0 Step 4; T0 started).
Task 0: dispatched (BASE b83e621, implementer sonnet, agent a232b4bc2a10a1f57)
Task 0: implementer DONE_WITH_CONCERNS ce4d138 (observations only: ranked-at line stays cut 43; ledger heading renamed w/ anchors; pre-existing dangling anchor left). Review package review-b83e621..ce4d138.diff
Task 0: minor (deferred): ledger's pre-existing dangling #current-state-2026-09-16 link (~line 553), predates lane
Task 0: complete (commits b83e621..ce4d138, review clean). CUT44_FREEZE_COMMIT=ce4d138 CUT44_FROZEN_SHA256=48679ee46e5e2195e1c820a39b9e0e661caa1eee47fdd219029da60ce7f1bb40
Task 1: dispatched (BASE ce4d138, implementer sonnet, agent afd1fc02e3a88e616)
Task 1: implementer DONE cf75aea (test-file deviations: testing_contract alias, ruff SIM117 combined with)
Task 1: Ruling: J16-j's one-line before (`        view = self._citations._one(ref, self._base)\n`) occurs twice in corpus.py (resolve + get) — Task 7 spells J16-j as the two-line resolve body (that line + `        return None if view is None else view.resolve(ref)\n`, unique) with a matching two-line after; no code change in Task 1 — plan already says "spell from the tree where unique"; cost if wrong: J16-j stale/ambiguous, caught by test_arm_staleness at Task 7. Same for J16-i: use the two-line for loop (unique), not its first line.
Task 1: minor (deferred): opened_at raising after capture leaves the hold in the stack without an _opened entry; a caught-and-retried lookup would BuildContended on its own hold (latent; normal use propagates)
Task 1: minor (deferred): _refuse_contract_mismatch reloads the manifest per lookup (spec §3.1 says at open); same behaviour under the hold, extra disk reads (plan text)
Task 1: minor (deferred): no unit test for a second mount contending after the first opened, nor the W+mount duplicate branch (_corpus_id(None)); code correct
Task 1: minor (deferred): MountCitations does not guard repeated roots or the write root in read_mounts; normalization is the session's (Task 2, decision 6)
Task 1: complete (commits ce4d138..cf75aea, review clean; 1 plan-mandated Important ruled → Task 7)
Task 2: dispatched (BASE cf75aea, implementer opus, agent a5d68fe98c5b47a35)
Task 2: implementer DONE ce68292 (deviations: for_kinds run route, reports type widened to ReportView|None, decision-2 check annotations accept MountCitations; concern: boundary.acquisition_guard bearer_refusal write-root only)
Task 2: Ruling: implementer concern "boundary.acquisition_guard judges write root only" — no action; reviewer verified a session's operation_port is a LedgeredPort whose execute_fulfilling_guarded raises SessionProtocolError, and the unattended writer has no read mounts (decision 6) — cost if wrong: an unattended publication with mounts could miss a mount producer; no such path exists today.
Task 2: minor (deferred): reports holder may return None → silent session-wide retrieval fallback (unreachable today; holds and holder share _one); Task 7 could use a raising holder lookup
Task 2: minor (deferred): _refuse_ineligible view=None defaults to self._view (plan-mandated); in-scope guard is an assert (stripped by -O)
Task 2: minor (deferred): F3 (n2_arms_cut20.py:72) before now matches mid-line after _refuse_facets re-indent (12→16 spaces); count 1 and parses, arm live, but match is a substring of a deeper line — final review to judge
Task 2: minor (deferred): J16-i test wraps _refuse_acquired_dataset in an extra w._citing() (plan-mandated), not the real call shape
Task 2: minor (deferred): J16-e/J16-g session tests don't assert where the assessment landed (a vs b)
Task 2: minor (deferred): spec §3.2 drift — says session passes None (code passes ()), names acquisition_view(reading, local=) (built as overlay); old eligibility_refusal docstring rationale on reads dropped — fold into Task 9 amendments
Task 2: complete (commits cf75aea..ce68292, review clean)
Task 3: dispatched (BASE ce68292, implementer sonnet, agent a9a85d0ea487d1b5d)
Task 3: implementer DONE 5c860cc (deviation: 3 tests placed as TestTheCorpusCheck methods)
Task 3: Ruling: tests must be module-level functions — the frozen cut-44 doc (ce4d138) names checks `test_read_side.py::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved` etc. with no class segment, and the brief's code is module-level; "beside the S7 cases" meant placement in the file — cost if wrong: one extra move commit.
Task 3: pre-review fix 0c6dacf (tests at module level)
Task 3: minor (deferred): two blank-line gaps between the new module-level J18 tests in test_read_side.py (ruff passed)
Task 3: minor (deferred): audit_world without citations now reports unheld refs as warning (Task 4's two-pass supplies the reader — verify at Task 4 review)
Task 3: complete (commits ce68292..0c6dacf, review clean)
Task 4: dispatched (BASE 0c6dacf, implementer opus, agent a8e956d4772393df8)
Task 4: implementer DONE_WITH_CONCERNS dfd8cff (narrowed cited test test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues; eligibility_outcome view annotated ProducerView; second pass doubles record-check work)
Task 4: Ruling: the implementer's narrowing of cited test test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues stands — reviewer showed the old last-per-ref dict hid a pre-existing derivation-malformed behind an eligibility-unresolved that this task correctly removes; cut 31 / mm30 §10 cite it for the two pre-grammar codes, still asserted (more strictly) — cost if wrong: a masked defect in derivation on assessment:a-p goes unexamined (logged as minor below).
Task 4: minor (deferred): perf — pass 2 re-runs full record check per corpus (plan-mandated, anchored by J19-a); _CapturedCitations.producers scans every readable corpus per dataset; _incomplete repeats validity_refusal per _holder call — follow-up candidate after a dogfood measures it
Task 4: minor (deferred): test_world_audit.py:376-381 masking explanation is a comment only; assert ("derivation-malformed", assessment id) present
Task 4: minor (deferred): coverage — J19-d unit test doesn't assert W's other records still audited (spec §7 J19 asks); stale-stamp test doesn't assert BETA's own semantic-hash-stale and writes after publish (spec: before the epoch); no test reaches excluded:<scope> — carry the J19-d point into Task 6's durable case
Task 4: minor (deferred): audit.py:617 assert on mutable _profile; pass profile through instead
Task 4: complete (commits 0c6dacf..dfd8cff, review clean)
Task 5: dispatched (BASE dfd8cff, implementer sonnet, agent a03c1793d02e4440c)
Task 5: implementer DONE d45244c (J20 compares value/policy/admission not belief_input_digest — implementer added a spec §13 note; InputOutsideCorpus placed after MalformedRecord)
Task 5: Ruling: the implementer's spec §13 note (J20 compares value/binding/admission, not belief_input_digest, which names epoch/corpus ids by construction) stands — brief Step 2 ordered a §13 record on fallback; spec J20 row never required digest equality — cost if wrong: one note to reword at Task 9.
Task 5: Ruling: Task 6's durable J20 additionally asserts closure projection equality minus producer_snapshot and retraction coverage, plus the full row (assessment+run → W, proposition+d-a+d-b → M, lineage, negative), and durable J21 asserts the assessment — makes §13's "every other closure member is equal" a tested claim; cost if wrong: one extra assertion to drop.
Task 5: minor (deferred): portable J20 (test_world_view.py:560-583) asserts partial attribution only, no lineage/negative (plan-mandated; Task 6 durable covers) — whole-branch review to confirm the row is discharged
Task 5: minor (deferred): `[:2]` no-op slices at test_world_view.py:571,577 (evaluate_over_traced returns a 2-tuple); report deviation 3 wrong
Task 5: minor (deferred): portable J21 test doesn't assert refused.value.assessment
Task 5: minor (deferred): after B4b re-target no live arm guards the observes-loop `if not view.holds(target): continue` (evaluation.py:393-394), still load-bearing on world views with an absent observed dataset — consequence of the approved supersession; final review to judge
Task 5: complete (commits dfd8cff..d45244c, review clean)
Task 6: dispatched (BASE d45244c, implementer opus, agent a6493b464508ef1a9; carries the Task 5 J20/J21 strengthening ruling and the J19 W-still-audited point)
Task 6: implementer DONE 6b90940 (10 passed 36.5s; node_corpus omits proposition → checked via corpus_of; J19 under TYPED asserts W's profile-mismatch; open_corpus roots refuse a second executor factory → use open_world + library writer lock; kwargs_for accepts a world view)
Task 6: Ruling: Important (plan-mandated) "spec §8.2/J16 row describe M pinning a namespace W lacks and M2 on fixture v2, acceptance uses profile_with()/biology('other')" — land a §13 note recording the acceptance fixture choice in Task 9's amendments (same branch, before merge), alongside a note that J20's "the others → M" is checked for the proposition via corpus_of (gather attributes only assessments/runs/datasets, decision 10) — cost if wrong: no durable case covers M-only namespaces; follow-up below.
Task 6: Ruling: file at Task 9 a follow-up beliefs task (idea): consulted_contracts (consulted.py:59) takes corpora only from attributed nodes, so a world read where M holds only the proposition with an M-only namespace would raise ContractDisagreement "pinned by no corpus" — pre-existing latent, outside this lane — cost if wrong: a real mixed-namespace world read refuses.
Task 6: minor (deferred): J16 M3 durable case writes the run inside pytest.raises (:169-170)
Task 6: minor (deferred): durable J18 doesn't assert the warning names the references (spec row)
Task 6: minor (deferred): durable J19 absent arm uses a subset check (:309)
Task 6: complete (commits d45244c..6b90940, review clean; 1 plan-mandated Important ruled → Task 9)
Task 7: dispatched (BASE 6b90940, implementer sonnet, agent a9c9911878f3dd643; Steps 1-4 + guard + standalone N2; controller runs full cut runner harness-tracked and closes beliefs-a8f943)
Task 7: implementer STOPPED (uncommitted): J16-c vacuous — its check writes a report-less verification, decode_verification returns None, _refuse_verification never reads the view. 23 other arms sound; CO_CITED gains J21-a (shared with cut 22's B4b).
Task 7: Ruling: keep J16-c's frozen mutation and check id; reshape the check body (test_mount_citations.py::test_a_verification_of_a_mount_assessment_is_written) to write a published, report-carrying verification over the mount assessment, so the view read decides it; record in spec §13 — the cut doc names the check id, not its body; the plan's "vacuous → reshape, record in §13" — cost if wrong: one more check rewrite.
Task 7: Ruling: J21-a in CO_CITED beside J16-a/b accepted (its check is also B4b's live re-target check) — cost if wrong: guard expects 23 distinct checks instead of 24.
Task 7: implementer DONE cac773c (24 sound; J16-c check reshaped via verification_fixtures.publish_corpus; §13 note). Full cut runner started harness-tracked → .work/acceptance/cut44-runner.log
Task 7: cut runner attempt 1 refused in the prefix chain (cut 6 N2 phase): OPS_WORKERS unset — the plan's runner command omits `host-budget run --`. Ruling: rerun as `host-budget run -- uv run --frozen python tools/cut44_acceptance.py` (same as the justfile's test recipes); fix the command in Task 9's results record — cost if wrong: none, environment only. Attempt 2 started harness-tracked.
Task 7: review Approved (no Critical/Important).
Task 7: Ruling: J21-a duplicates B4b's live re-target in both mutation and check (frozen doc's §5 gives it B4b's check) — the frozen doc's prose "differ in their check" is false; Task 9 corrects the current-facing comment at test_n2_cut22.py:41 and states the overlap in the results record (cut 44's independent evidence is 23 arms + J21 via its own unit/durable tests) — cost if wrong: coverage overstated by one arm.
Task 7: minor (deferred): CO_CITED serves two guard assertions with one set (n2_arms_cut44.py:486)
Task 7: minor (deferred): J16-c check should also assert decode_verification(node).assessment is not None (test_mount_citations.py:743)
Task 7: cut runner attempt 2 (host-budget) FAILED in cut 17's phase test_permit_entry_points (8 needs_volume cases): CapabilityUnavailable SQLite-WAL parent connection "unable to open database file". Root cause (reproduced): acceptance_runner nests each prefix run under the parent's run dir; cut 44's chain is 1 level deeper than cut 43's and the deepest SQLite path exceeds 512 chars (27 levels @ canonical base fails, 20 pass). Not a cut-44 code defect.
Task 7: Ruling: rerun with SCIENCE_CUT44_ROOT=<main>/.work/c44 (13 chars shorter = cut 43's proven depth; .work/ is gitignored, on the certified volume); filed beliefs-fdc40f (P1) for the structural fix; record the invocation in the results record — cost if wrong: cut 45 hits it again unless beliefs-fdc40f lands.
Task 7: cut runner attempt 3 (SCIENCE_CUT44_ROOT=.work/c44): cut 17 now passes (path fix holds); FAILED at cut 23 phase test_world_view_acceptance.py::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably — its tail (lines 376-388) evaluates corpus-locally over A where run-a observes d-a held in B and asserts the old silent drop (absent==(), observed_facets==(), Belief from run-b) → now InputOutsideCorpus. Unforeseen by spec §13 (only F4/B4b foreseen); invisible to the portable suite.
Task 7: Ruling: this tail asserts B4's absent-dataset clause, which the user approved J21 superseding — rewrite only the tail (keep name; R19b/R19c/R19e depend on the earlier part, not the tail) to assert J21's refusal (gather raises InputOutsideCorpus naming run-a and d-a; evaluate_over returns Refused input-outside-corpus); record in spec §13 and the results record; sweep tests/acceptance for other corpus-local reads over unheld inputs before rerunning — cost if wrong: a frozen cut-23 claim is edited where it should have been pinned; the user sees it in the report.
Task 7: fix 912005b (cut-23 tail asserts J21; cut22 comment corrected; §13 note; sweep of 10 acceptance modules found no other silent-drop assertion). Runner attempt 4 started.
Task 7: fix round 1/5 (cut-23 tail; 1 addressed, 0 open; commits cac773c..912005b) — scoped re-review all addressed
Task 7: runner attempt 4 green (exit 0; 24 arms/24 units/6 rows; J16–J21 exercised). Task 7: complete (commits 6b90940..5ac7447, review clean, 1 fix round)
Task 8: dispatched (BASE 5ac7447, implementer sonnet, agent ab14184bc1c0b49ee)
Task 8: implementer DONE 48aaa2f (NoBelief unchanged, state.json byte-identical 1efbd06c; driver opens no session; predecessor canonical path used; verdict step skipped per §25.1). Controller verified biology pin == shipped content identity 24bcec43.
Task 8: review Needs fixes — 4 Important (unsupported recomputed scope/verdict values; predecessor path unexplained; §25.1 verdict claim unattributed; eligibility wording check). Fix round 1 dispatched (resume ab14184bc1c0b49ee).
Task 8: fix round 1/5 (4 addressed, 0 open; commits 48aaa2f..4761862)
Task 8: minor (deferred): §26 writes the predecessor as ~/d/proto/... (home-relative, consistent with §§13–20)
Task 8: complete (commits 5ac7447..4761862, review clean after 1 fix round)
Task 9: dispatched (BASE 4761862, implementer opus, agent a811a86496c3bc2b4; carries rulings.md, runner attempts, §13 amendments, consulted_contracts follow-up filing)
Task 9: implementer DONE_WITH_CONCERNS f6fa3da (220 of 247; filed beliefs-d69102; edited frozen cut-44 doc's **Status:** line only, as cut 43's results commit did, required by test_the_newest_cut_document_says_it_is_discharged; ledger is gitignored → commit at Task 10)
Task 9: Ruling: the cut-44 doc's Status-line edit stands — repo practice (cut 43's results commit) and a test require it; the guard pins §2–7, which stay byte-exact — cost if wrong: a frozen-doc edit the user would rather have avoided.
Task 9: Ruling: Task 10 commits this ledger to docs/plans/2026-10-01-mount-citations-execution-ledger.md before worktree removal (memory: execution ledgers are durable) — cost if wrong: none.
Task 9: review Needs fixes — Important: §7 omits each ruling's cost (incl. the cut-23 R19b/c/e flag); 5 minors folded into the same fix. Fix round 1 dispatched (resume a811a86496c3bc2b4).
Task 9: fix round 1/5 (6 addressed, 0 open; commits f6fa3da..6cf9e8e)
Task 9: minor (deferred): results.md §3 J20 paragraph line 175 re-flowed to 164 chars — re-wrap in the final fix wave
Task 9: complete (commits 4761862..6cf9e8e, 1 fix round)
Task 10: final whole-branch review dispatched (eef8749..6cf9e8e, opus, agent aa42506fd9eb9c4fa; triages 28 deferred minors)
Task 10: final review — With fixes: Important 1 corpus-local read KeyError when an assessment's run is held in a mount (evaluation.py:369-373 skips, belief.py:291 indexes); Important 2 capture hold now also yields BuildHold for in-process writers on a mounted root, undocumented, both messages misname the cause; Important 3 several row sub-cases unexercised while records say "in full" (J17 W+mount duplicate, J19-d W still audited, BETA semantic-hash-stale, J16 split-retrieval raw write, mounts=None negative, "excluded" claimed).
Task 10: Ruling: fix Important 1 in this branch — extend decision 9 to the run itself (corpus-local gather raises InputOutsideCorpus(a, run, (run,)) for an unheld run), unit test + §13 note + results; no new declared arm (cut 44's declaration is frozen at 24) and the results say so — cost if wrong: a discharged cut's behaviour grows by one refusal after its freeze; the alternative ships a KeyError science would hit.
Task 10: Ruling: fix Important 2 — _read_mount re-raises BuildContended naming the read mount and the citing write; spec §13, results §5 and the guide state the converse BuildHold — cost if wrong: message text churn only.
Task 10: Ruling: fix Important 3 by adding the cheap tests; where a case is not cheap (excluded:<scope>), correct the claim and list it unexercised — cost if wrong: none.
Task 10: Ruling: fold in minors: _refuse_ineligible None default → explicit raise, docstring true; corpus.py:1574 message names the session's corpora when mounted; J16-c asserts .assessment; results line 175 wrap. Defer with follow-up tasks: audit/mount-open cost at mm30 scale; live arm for the observes-loop holds filter; one citation scope per import bundle.
Task 10: final fix wave dispatched (FIX_BASE 6cf9e8e, opus, agent af9eba3d6efbd1a3f)
Task 10: final fix wave DONE 3988be8..d5a2715 (5 commits; follow-ups beliefs-e02ef3, beliefs-cb2a39, beliefs-4a2998; excluded:<scope> found unreachable — claim removed, listed unexercised; J19 left closed)
Task 10: Ruling: J19 stays closed with its "excluded" clause recorded as unexercised and unreachable under today's scopes (results §3), not "in full" — all J19 arms ran sound; the clause's antecedent cannot occur — cost if wrong: J19 should read partial; re-review to judge.
Task 10: final fix re-review — Important 1, 2, minors, follow-ups ADDRESSED; Important 3 open: excluded:<scope> IS reachable (construction damage + foreign base pin → excluded:base overwrites damaged:construction; reviewer reproduced), results §3 wrongly says unreachable.
Task 10: Ruling: residual is load-bearing for the record's truth — complete the same fix-wave item (not a new wave): resume the fix implementer to add the reviewer's probe as a unit test, drop the "unexercised/unreachable" clauses (results §2/§3/§5, ledger, roadmap App. A), keep J19 closed; also the InputOutsideCorpus docstring nit and a follow-up idea for the pre-existing "excluded corpus drops its corpus-damaged finding" — controller verifies by running the test and grepping the docs — cost if wrong: J19 overstated if the test is weak; the controller check covers it.
Task 10: residual closed af2dc57 (test_j19_an_excluded_holder_is_unresolved passes; asserts code/ref/excluded:base; record cites it; follow-up beliefs-54e7b8). Controller verified test + docs. Final review: clean (all Important addressed).
Task 10: deferred minors not fixed, per final triage (defer): T0 dangling anchor; T1 opened_at-after-capture, manifest reload, contention test, repeated roots; T2 reports-None, F3 mid-line, J16-i wrapper, J16-e/g landing; T3 blank lines; T4 comment-only, before-epoch timing, _profile assert; T5 [:2] slices, portable J21 assessment; T6 M3 inside raises, J18 refs, J19 subset; T7 CO_CITED; T8 home-relative path. Follow-ups filed: beliefs-fdc40f, beliefs-d69102, beliefs-e02ef3, beliefs-cb2a39, beliefs-4a2998, beliefs-54e7b8.
Task 10: fresh cut runner green at d5a2715 (exit 0, 24/24/6; log .work/acceptance/cut44-runner-final.log). Gate started.
Task 10: gate green (check clean; 5945 passed 1 skipped; N2 46 passed; TS 155 passed; log .work/acceptance/cut44-gate.log). Merge awaits the user.
