# Publication records — execution ledger

The controller's ledger for executing `docs/superpowers/plans/2026-09-22-publication-records.md` by subagent-driven development (cut 39), committed as a durable artifact. Agent ids are the session's subagent handles.


Spec: docs/superpowers/specs/2026-09-22-publication-records-design.md (approved cb19908). Plan approved by user 2026-09-23 after review 3 fix at 192ae53.

## Preflight scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T0 → T7, T8, T10 | T0 freezes ROLLBACK_MEANS, REPLACE_UNREGISTERED, one accounting row; T7 pass count, T8 homed/unit_of/declared_accounting/freeze phrase, T10 results read it | agree (fixed at da5f559, 192ae53) |
| T0 → T8 | freeze commit + body digest → CUT39_FREEZE_COMMIT/CUT39_FROZEN_SHA256 | agree |
| T1 ↔ T3 ↔ T5 (coordination.py) | T1 kind tuples; T3 adds Anchor; T5 MomentSeam/standing_at; all must keep cut 14/19/35/38 pinned befores unique | agree; each ends with test_arm_staleness |
| T1 → T4 | PUBLICATION_KINDS | agree |
| T1 ↔ T6 (corpus.py) | T1 KindNotMintedHere guards; T5 mounted(); T6 payload= kwarg | agree; Y1-a before spells T1's guard text |
| T1 → T8 (permit.py) | T1 re-targets cut17 E4c; T8 Y1-b before chosen from tree | agree |
| T2 → T3 | OPERATION_KINDS with publish | agree |
| T2 ↔ T6 (report/stored) | binding_outcome_from_facet, act_report_facet passthrough → T6 fold | agree |
| T3 → T4, T5, T6 | Destination, PublishIntent, Anchor, codec | agree |
| T4 → T5, T6 | publication_content_malformed, factories, addresses | agree |
| T5 → T6 | MomentSeam, standing_at, bounds, _creates | agree |
| T6 → T7 | doors, fold, PUBLISH_INSTRUMENT | agree |
| T7 → T8 | test names cited by UNIT_CHECKS | agree |
| T8 self | Interfaces line says `CUT39_ARMS (14)`, `DECLARATION_UNITS (13)` while body reads the frozen row | conflict (see Ruling 1) |
| T0 self | probes precede freeze; freeze phrase per row | consistent |
| T1–T7 self | tests specified match code specified (reviewed 3x: agent, user x2, user check 3) | consistent |
| T9–T11 self | docs/results/merge; T11 merge is outward-facing | T11 merge: stop and ask per norms |

Ruling 1: Task 8's Interfaces counts (14/13) are the first row's example; the frozen row from Task 0 governs — the Global Constraints say no later mention restates its own count — costs a wrong inventory assertion if wrong, caught by the guard.
Ruling 2: Task 11's merge to main is a side effect outside the worktree; run through the gate, then stop and ask before merging — costs one round-trip.

## Progress
Task 0: dispatched (BASE cc52474)
Task 0: implementer a3e21a750e17b75b9 (opus) dispatched from BASE cc52474
Task 0: implementer DONE_WITH_CONCERNS at 15fd610 — verdicts ROLLBACK_MEANS=patched create effect, RETRY_AFTER_ROLLBACK=same intent, REPLACE_UNREGISTERED=accepted; frozen row (14, 13, 5), W17 closes, Task 7 passes 16. Freeze commit 15fd610a79d4, body sha256 c032eab7404b…9755; cut doc docs/designs/2026-09-23-conformance-cut-39.md
Task 0: reviewer a8ea04b0849382e1c (opus) dispatched on review-cc52474..15fd610.diff
Note for later dispatches: export cut roots via $(readlink -f …) — ~/d paths cause ELOOP (Task 0 concern 1)
Task 0: review — Needs fixes: (I1) §5/§2 Y1-b site names permit.py/corpus.py but the exclusion lives at world/epoch.py:1251 [plan-mandated in part]; (I2) guide contracts-and-adoption.md:143 still 216/twenty. Minors: ledger :353 tense; probes read via inspect_registered (recovery) — add inspect_detached + committed True in replace; unused _registrations; wrong comment :71; roadmap sentence break.
Ruling 3: Y1-b's site is frozen as `world/epoch.py` (the `stored.WORLD_KINDS` membership test the world-index derivation reads), added to §2's boundary — the plan's Task 8 grep already covered world/*.py and the spec only says "the site that keeps coordination kinds out of the world-index maps" — if wrong, Task 8's arm lands elsewhere and needs a superseding citation.
Ruling 4: the freeze moves to the fix commit (it has not cleared review); CUT39_FREEZE_COMMIT/CUT39_FROZEN_SHA256 are the re-recorded values — nothing yet depends on 15fd610.
Ruling 5: fold the five minors into fix round 1 (all in files this task owns, cheap, and two strengthen probe evidence) rather than deferring.
Task 0: fix round 1 implementer DONE (8e81e1a, ff94cee); new freeze 8e81e1ac72ac, body sha256 b92c7a2052e9…7a43
Task 0: re-reviewer a2d933279087261dd (sonnet) on review-15fd610..ff94cee.diff
Task 0: fix round 1/5 (7 addressed, 0 open; commits 15fd610..ff94cee)
Task 0: complete (commits cc52474..ff94cee, review clean)
Task 1: dispatched (BASE db969d1)
Task 1: implementer a2cc6f320309ad5a8 (opus) dispatched from BASE db969d1
Task 1: implementer DONE at a312745 — deviations: W18a cited tests swapped undeclared kind publication→milestone (arm still sound), test_profile __all__, fixture typing. Carry to Task 10: results record states W18a swap beside E4c re-target.
Task 1: reviewer a6050d9d55d2ac85a (opus) on review-db969d1..a312745.diff
Task 1: review Approved. ⚠️ staleness/boundary resolved by controller run: 540 passed (test_arm_staleness, capability, permit boundary, entry points).
Task 1: minor (deferred): permit.py:44 `_COORDINATION_KINDS` unused (plan said keep) — final review triage
Task 1: minor (deferred): n2_arms_cut17.py:144 text and test_permit.py test name contradict re-targeted E4c check — disclose in Task 10 results record
Task 1: minor (deferred): corpus.py:3229 `_refuse_family_kinds` message points publication kinds at the coordination door — wording
Task 1: complete (commits db969d1..a312745, review clean)
Task 2: dispatched (BASE 328bdce)
Task 2: implementer a38bebe87e3e66654 (opus) dispatched from BASE 328bdce
Task 2: implementer DONE at 5b53299 — kept cut19 J1e literal as _DOMAINLESS_OPERATION_KINDS, OPERATION_KINDS derived; act-report design amendment (spec §7) left for Task 10
Task 2: reviewer a7f8d5183174ceead (opus) on review-328bdce..5b53299.diff
Task 2: review Approved. ⚠️ staleness resolved by controller run: 8 passed.
Task 2: minor → carried into Task 3: boundary.py:78 `_mint_publish_report(intent: Any)` + getattr duck-typing; tighten to PublishIntent / `type(intent) is not PublishIntent` once Task 3 defines it
Task 2: minor → carried into Task 3: report.py:64 comment should name cut 19 J1e's pinned before
Task 2: minor → carried into Task 3: test_report.py lacks constructor case for non-tuple tips
Task 2: complete (commits 328bdce..5b53299, review clean)
Task 3: dispatched (BASE e0866ff)
Task 3: implementer aba3250419e04eedd (opus) dispatched from BASE e0866ff, with Task 2 minors a–c
Task 3: implementer DONE at f132b3c + 75ec40f (minors) — also fixed latent session/reconcile.py _session_of .get on PublishIntent
Task 3: reviewer ad1ba4f5eb0909b2e (opus) on review-e0866ff..75ec40f.diff
Task 3: review Approved. ⚠️ staleness resolved by controller run (see below). ⚠️ "one anchor per mount other than written root" is Task 5/6's caller-side obligation.
Task 3: minor → carried into Task 4: Destination local branch accepts NUL and lone surrogates (encode raises IdentityError, not MalformedRecord); refuse "\x00" and v1.encode-check the locator, re-raising as MalformedRecord, +2 tests
Task 3: minor (deferred): beliefs-3ae33c done note says 44 tests vs report 45 — cosmetic
Task 3: complete (commits e0866ff..75ec40f, review clean)
Task 4: dispatched (BASE 33ecc54)
Task 4: implementer a4fe391a299d196b9 (opus) dispatched from BASE 33ecc54, with Task 3 minor (Destination encodability)
Task 4: implementer DONE at bc29811 (carried minor) + 5d8db9d
Task 4: reviewer af4b898c93092848b (opus) on review-33ecc54..5d8db9d.diff
Task 4: review Approved (staleness verified by reviewer count + implementer run).
Task 4: minor → carried into Task 5: publication.py:316 marker_record(selection=None) raises TypeError; check type(selection) is tuple first
Task 4: minor (deferred): publication.py:274,282 reaches private CorpusWriter._coordination_node with stub nodes (plan-mandated) — final review
Task 4: minor (deferred): marker_consistent repeats rule checks — harmless
Task 4: complete (commits 33ecc54..5d8db9d, review clean)
Task 5: dispatched (BASE 4e74460)
Task 5: implementer a1f72c1f95c44fe6c (opus) dispatched from BASE 4e74460, with Task 4 minor (selection=None)
Task 5: implementer DONE at 04e150f (minor) + 394c173 — concerns: LogEvidenceRefused surfaces as exception; staged registration on detached read → unregistered-revision; same before/after → history-violated
Task 5: reviewer aa94c7f3ca1a429cd (opus) on review-4e74460..394c173.diff
Task 5: review Approved; risk 1 (LogEvidenceRefused escapes standing_at) assigned to Task 6.
Ruling 6: LogEvidenceRefused — standing_at keeps propagating it (no remap inside the judgment); step 0 lets it propagate (nothing revealed, nothing written); step 8's guard catches it around the judgment and records `evidence-refused` with reason `chain-malformed` (the closed EVIDENCE_REFUSAL_REASONS set is not widened), carrying the marker/corpus/remotely_revealed so the orphan invariant holds; pinned by a Task 6 test — why: spec §6 says a remotely revealed attempt refused for any reason is an orphan the next publish supersedes; a label within the closed set avoids amending the frozen act-report entry — costs one reason label if the user prefers a new reason.
Ruling 7: Task 5's cheap minors go to a short resume of the Task 5 implementer (re-read branch mirrors bounds' AbsentView/out-of-union discrimination; @sealed on PositionRefused/MomentSeam/ChainBound; a pre==post history-violated unit test; a real-seam revision-mismatch assertion) — they are in Task 5's files and one is a semantic inconsistency — costs a few minutes.
Task 5: minor (deferred): standing_at skips coordination_facet_malformed for ordinary kinds — note only; standing_at serves the publication doors
Task 5: fix round 1 implementer DONE at 182920e; re-reviewer a27738ee1061a86c0 (sonnet) on review-394c173..182920e.diff
Task 5: fix round 1/5 (4 addressed, 0 open; commits 394c173..182920e)
Task 5: complete (commits 4e74460..182920e, review clean)
Task 6: dispatched (BASE 4396549)
Task 6: implementer a4653d0ac6fa6e919 (opus) dispatched from BASE 4396549, carrying Ruling 6
Task 6: implementer DONE at 9fb9f4e — Ruling 6 catch in _judge (guard-only caller); payload= early-return branch to keep cut 35 T2-c pin
Task 6: reviewer ac67a7fa2026b0c6e (opus) on review-4396549..9fb9f4e.diff
Task 6: review Approved. Minors: (1) remotely_revealed unvalidated before effects — non-bool loses the refusal report/orphan; (2) two committed fulfilments of one intent chosen silently in fold; (3) _bind_publication skips _require_pins_agree; test gap: step 0 chain-absent/chain-malformed.
Ruling 8: fold minors 1–3 and the step-0 test gap into a short Task 6 fix round — (1) and (2) are fail-early holes on the orphan invariant, all in Task 6's file — costs a few minutes.
Task 6: fix round 1 implementer DONE at 9930fd6
Task 6: re-reviewer a456861ac63bf05bf (sonnet) on review-9fb9f4e..9930fd6.diff
Task 6: fix round 1/5 (4 addressed, 0 open; commits 9fb9f4e..9930fd6)
Task 6: complete (commits 4396549..9930fd6, review clean)
Task 7: dispatched (BASE bd7736b)
Task 7: implementer a77ee7668a9fcd379 (opus) dispatched from BASE bd7736b; dev work dir .work/acceptance/cut39-dev
Task 7: implementer DONE at ca87e06 — 16 passed, 14/14 arms caught by hand; Y1-b excludes the publish's own act report from the address map; W17-p-d caught by PublishIntent ascending-anchor check. Carry to Task 10: state Y1-b act-report exclusion.
Task 7: reviewer afe499050b0e0196b (opus) on review-bd7736b..ca87e06.diff
Task 7: review Approved with Important: Y1-a add/import_bundle only exercised with a binding, not a marker. Minors: v1 ValidationRefused lacks match=; W17-p-d "same anchors in both orders" true only because resolver sorts; `bound` shadowed at :670; Y2-a duplicate byte assertion.
Task 7: fix round 1 dispatched (Important + minors) to a77ee7668a9fcd379
Task 7: fix round 1 implementer DONE at 1af4706
Task 7: re-reviewer a6ea8c96b3e794a96 (sonnet) on review-ca87e06..1af4706.diff
Ruling 9: Task 8 splits at Step 5 — the implementer does Steps 1–4, the Step 5 guard-green commands, and commits (Step 6) without closing beliefs-5b44e2; the controller launches the chained runner detached through detached.sh, reads the log, and closes the step task (or routes failures back) — the runner outlives a subagent's one-turn/600 s budget — costs one extra commit for the task close.
Ruling 10: every `~/d/beliefs/...` export in Task 8's commands is resolved with readlink -f (Task 0 found the ~/d spelling causes ELOOP) — costs nothing.
Task 7: fix round 1/5 (5 addressed, 0 open; commits ca87e06..1af4706)
Task 7: complete (commits bd7736b..1af4706, review clean)
Task 8: dispatched (BASE 7fcb112)
Task 8: implementer ac93237848a2d3627 (opus) dispatched from BASE 7fcb112 (Steps 1–4, 5-guard, 6 commit; runner is controller's)
Task 8: implementer DONE at 4cb09d8 (guard green, 14 arms sound individually). Controller launched chained runner pgid 118189, log .work/acceptance/cut39-runner.log
Task 8: reviewer a4efe7f65b8376a95 (opus) on review-7fcb112..4cb09d8.diff
Task 8: review Approved; ⚠️ 14/14 sound inside guard fixture pending chained runner.
Task 8: minor (deferred): ACCOUNTING table written twice (guard and runner), both pinned
Task 8: minor (deferred): runner rows-exercised print not keyed by table (unreachable branch)
Task 8: minor (deferred): RETRY_AFTER_ROLLBACK constant unused (documents probe)
Task 8: chained runner exited clean — 16 passed, guard 10 passed, 14 arms/13 units/5 rows, 5 newly closed; pgroup gone
Task 8: complete (commits 7fcb112..05e48a2, review clean)
Task 9: dispatched (BASE b036e8e)
Task 9: implementer ac2f5dbb0748e244e (sonnet) dispatched from BASE b036e8e
Task 9: implementer DONE at 101cdd2 — same NoBelief payload, rederived_equal true, state.json identical
Task 9: reviewer a5ade6dd76214da07 (sonnet) on review-b036e8e..101cdd2.diff
Task 9: complete (commits b036e8e..101cdd2, review clean)
Task 10: dispatched (BASE aeeacf6)
Task 10: implementer a2455765c8722e424 (opus) dispatched from BASE aeeacf6, with task-10-carry.md
Task 10: implementer DONE at f623e2b — added three stale-claim notes beyond file list; act-report notes dated 09-23
Task 10: reviewer a4c6a1e59b723e420 (opus) on review-aeeacf6..f623e2b.diff
Task 10: minor (deferred): coordination design §7 (:641-644) cut-14 narrative "W17 partial" borderline stale — a dated parenthetical
Task 10: minor (deferred): ledger built bullet "Two internal doors write the source root, …" parses ambiguously
Task 10: complete (commits aeeacf6..f623e2b, review clean)
Task 11: started; merge-base 2b875a7443ff3f71a81940f57423929932ae34ec
Task 11: final reviewer a81526146c43006f1 (opus) on review-2b875a7..15389a7.diff; gate launched at 15389a7 pgid 504104, log .work/acceptance/cut39-gate.log
Task 11: final review — Ready after fixes. I-1 (Important): for_kinds can rebuild the kernel publish permit, so science's `mints:` route reaches publish (decision 7 broken). I-2 (Important): step 8 never checks opened.intent is the intent entry at opened.digest. m-1 shipped_coordination(True); m-2 coordination design §7 stale "W17 partial" (fix before merge); m-3 _refuse_family_kinds wording; m-4 unmounted written root refuses late. All rulings hold (6 questionable only in labelling). Q4: exceptions before effects leave the intent open, not orphaned — cut 40's recovery table must state it.
Ruling 11: one fix dispatch for I-1, I-2, m-1, m-2, m-3, m-4 — I-1 breaks a spec decision; I-2 is the step-0→step-8 seam the second slice will rebuild; the minors are one-liners — then re-run test_n2_cut39 (all 14 arms) and the gate — costs one gate re-run.
Ruling 12: the "exceptions before effects leave the intent open (unfinished), not an orphan" boundary is recorded in the results record §7 limitations and as a note on beliefs-328507 for cut 40's recovery table — costs nothing; it's the second slice's scope.
Task 11: final fix wave afab3510ce4791366 (opus) dispatched from 15389a7
Task 11: gate at 15389a7 (pre-fix) green — 5514 passed, 1 skipped; TS 155 passed; checks passed
Task 11: fix wave DONE 15389a7..7e5f936 (bc6565f e21fb3d 392373b 1bbb259 7692b3a 7e5f936); test_n2_cut39 10 passed; final gate launched pgid 645606 log cut39-gate-final.log
Task 11: fix-wave re-reviewer a872ad2742469b9e1 (opus) on review-15389a7..7e5f936.diff
Task 11: fix-wave re-review — all findings addressed (I-1, I-2, m-1..m-4, Ruling 12). I-2's missing-digest → MalformedRecord judged correct (orphans are derived from chain intents; a report fulfilling an absent digest could never be folded).
Task 11: final gate at 7e5f936 green — 5525 passed, 1 skipped; TS 155; checks passed
