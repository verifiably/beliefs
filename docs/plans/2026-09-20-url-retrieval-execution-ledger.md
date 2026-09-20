# URL retrieval execution ledger (cut 35, 2026-09-20)

The subagent-driven execution record of `../superpowers/plans/2026-09-20-url-retrieval.md`: pre-flight scan, per-task completions, fix rounds, every ruling the controller made, and the deferred minors the final review triaged. Kept as a durable artifact; the code history is the record of what landed. The results record is `2026-09-20-conformance-cut-35-results.md`.

Spec: docs/superpowers/specs/2026-09-19-url-retrieval-design.md (reachable, approved 395b550)
Worktree: .worktrees/url-retrieval, branch url-retrieval, start HEAD d80f5d9 (main 728a178)
Goal task beliefs-d13fe8 resumed 2026-09-20.

## Pre-flight scan

| pair / task | produces vs consumes | found |
|---|---|---|
| T1→T2,T4,T5 | UrlLocator(url), url_locator, Locator, HoldingsObservation.location | names match at every use |
| T2→T4 | intent_payload hand-built in T2, swapped in T4; kw signature (location, act_kind, event_token, actor) | matches T4's Produces |
| T1→T2 | _LIVE_SABOTAGES maps row→whole Arm in test_n2_cut10.py; T2 re-targets "as Task 1 Step 6 did" | consistent |
| T3→T4,T5,T6,T8 | Approved(host,port,target,authority,address); retrieve→Retrieved/NotAttempted/Failed; scripted_seam/tls_seam | T6 updates survey fakes to target/authority; consistent |
| T4→T5 | look(ctx, location, *, bounds, seam, scratch, expected, standing); store_refusal; StoreWriteRefused | T5's acquire calls match; T8 pins the same call text |
| T5→T6,T8 | acquire(ctx, writer, request, *, seam, scratch, standing, port, hold); _append_operation_intent(port=); _publish_operation_report(operations=, port=) | T6 route and T8 sabotage lines match |
| T0→T8 | CUT35_FREEZE_COMMIT / CUT35_FROZEN_SHA256 | T8 guard pins them |
| T0 vs T9 | cut doc §§2–7 frozen at T0; T9 edits Status only | consistent with global constraint |
| T3 self | ceiling test reads [65,33] vs read(min(CHUNK, remaining+1)) and the fake's chunk boundary | arithmetic checks |
| T3 self | preflight comment "port 0 sent as given" vs construction refusing port 0 | different surfaces (hop vs declared URL); not a conflict |
| T3 self | _transport_category order (TimeoutError, SSLError, OSError, else protocol) vs parametrized cases | each case lands in its category |
| rubric | any test asserting nothing? refuse_scratch_root's positive call — a no-raise assertion | acceptable |
| rubric | verbatim duplication mandated? none found | — |

Scan clean; no rulings needed before Task 0.

## Progress
Task 0: dispatched (BASE d80f5d9, sonnet)
Task 0: implementer done f746cf7 (CUT35_FREEZE_COMMIT f746cf7cf42e4baaf537fd408d86925716ee9c2f, CUT35_FROZEN_SHA256 d669f076f4dab0474888108d230a15e120cc76da4164a44446cf5d62ef91ddb0). Review: 1 Important — spec §17 corrections (a)-(r) not recorded (plan line 2980, outside the task section; brief omission). Minor (deferred): cut doc `Plan:` field cites the implementation plan — accepted as intended.
Task 0: fix round 1 dispatched (resume implementer; FIX_BASE f746cf7)
Task 0: fix round 1/5 (1 addressed, 0 open — spec §17 corrections recorded; commits f746cf7..5417455)
Task 0: complete (commits d80f5d9..5417455, review clean)
Task 1: dispatched (BASE 5417455, sonnet)
Task 1: implementer done b34bcb5, DONE_WITH_CONCERNS. Ruling: the plan's Step 6 (`_LIVE_SABOTAGES` in test_n2_cut10.py) is a plan defect — cut 10's guard is cited-not-run, its bytes pinned by cut 17's content hash; the tree's re-target mechanism is `tests/cited_not_run.py` `stale_arms` (already used for H4u1/J8), and J3 is re-targeted there — because the global constraint's "live guard" premise does not hold for cut 10 — costs if wrong: a J3 pin recorded in the wrong register, caught by the staleness probe (green). Task 2's "as Task 1 Step 6 did" means the same `stale_arms` route. Ruling: `intents/evidence.py` switched to `value.location.canonical()` in Task 1 (pyright on the widened union); this is Task 2 Step 4's exact change, done early — costs nothing; Task 2 dispatch notes it.
Task 1: review clean. minor (deferred): decision 1 silent on empty port `:`, leading-zero port `:0443`, percent-encoded host — spec §13 candidates, not code; minor (deferred): `%2E` decoded before dot-segment removal (RFC order) vs decision 1's listing order — spec clarification; minor (deferred): `_normalized_path` error text carries the path (construction-time, caller's own spelling); minor (deferred): report hygiene (no pytest summary lines; `not sabotage` added to -k without stating why).
Task 1: complete (commits 5417455..b34bcb5, review clean)
Task 2: dispatched (BASE b34bcb5, sonnet)
Task 2: implementer done 3c3094c; review dispatched
Task 2: review clean. minor (deferred, plan-mandated): intents `_url` scheme check is case-sensitive and looser than `_canonical_url` — a non-canonical url key never matches an observation, so the strict gate is the codec; spec-note candidate.
Task 2: complete (commits b34bcb5..3c3094c, review clean)
Task 3: dispatched (BASE 3c3094c, sonnet)
Task 3: implementer done bed11fe (DONE_WITH_CONCERNS: lint/type deviations from brief code, listed in report); review dispatched
Task 3: review clean; ⚠️ (hop-0 ASCII) resolved by controller: `_canonical_url` refuses bytes outside 0x21–0x7E. minor (deferred, plan-mandated): `content-encoding <value> is not identity` echoes a server header value into a reason; minor (deferred): `int(declared_length)` accepts `+4`/`-1`/underscore forms (only the fake reaches it); minor (deferred): `ip_address()` outside the try in preflight; minor (deferred): fixture `handle_error` swallows every handler exception and its comment names the wrong seam; minor (deferred): per-operation timeout, not wall-clock — docstring sentence.
Task 3: complete (commits 3c3094c..bed11fe, review clean)
Task 4: dispatched (BASE bed11fe, sonnet)
Task 4: implementer done bb9a92d (cut17 E6a re-targeted in _LIVE_SABOTAGES; cut10 L7u2[17] stale_arms; TransactionHalted import path + READ_ONLY member fixed per brief fallback); review dispatched
Task 4: review — 1 Important: spec BI-11 row / §5 parenthetical name ProjectApprovalRefused; the replica fixture yields PreconditionRefused. Ruling: correct the live spec with a §17 note; the frozen cut-35 §3/§6 text (which quotes the row and names ProjectApprovalRefused in the second-reader check) is not edited — Task 9's results record §3 records the deviation and Task 8's BI-11 arm asserts a cause in the closed set as produced — because frozen bodies are byte-exact by constraint — costs if wrong: a reader of the frozen cut doc alone sees the stale cause until the results record; minor (deferred): report GREEN blocks lack summary lines (doubled -q); minor (deferred): `look` defined before `ActContext`; minor (deferred): no `look` test with a valid `expected=` digest — Task 5/8 candidate.
Task 4: fix round 1 dispatched (resume implementer; FIX_BASE bb9a92d)
Task 4: fix round 1/5 (1 addressed, 0 open — spec BI-11 row/§5/§17 corrected; commits bb9a92d..696198c)
Task 4: complete (commits bed11fe..696198c, review clean)
Task 5: dispatched (BASE 696198c, opus)
Task 5: implementer done 229d9d6 (DONE; cut16 T2a re-targeted; 10 recorded deviations). Reported a Task-4 regression: test_capability_boundary (holdings/boundary.py imports atoms.*) x2 and test_permit_boundary (look uninventoried) — controller confirmed 3 failed / 404 passed on the two modules.
Task 4: REOPENED. Ruling: the plan's `store_refusal` in holdings/boundary.py with atoms cause types violates the composition-root invariant (root.py is the one atoms importer) — the predicate moves to root.py and rides `StoreActSeam.store_refusal`; `look` joins WRITE_ENTRY_POINTS — because the invariant is a tested boundary the spec did not account for — costs if wrong: a seam-field churn across 4 constructors; classification semantics unchanged.
Task 4: fix round 2 dispatched (resume implementer; FIX_BASE 229d9d6, on top of Task 5). Task 5 review deferred until the tree is green.
Task 4: fix round 2 done b065711 (test-fast 5172 passed/1 skipped); re-review dispatched. Task 5: review dispatched over 696198c..229d9d6 (opus).
Task 4: fix round 2/5 (3 addressed, 0 open — classifier in root.py on the seam; look inventoried; raw-write allowlist entries judged legitimate scratch cleanups; commits 229d9d6..b065711)
Task 4: complete (commits bed11fe..696198c + fix b065711, review clean)
Task 5: review clean; ⚠️ (test-fast failures pre-existing) resolved: they were Task 4's, fixed at b065711. minor (deferred): test_holdings_acquire `..._the_hold_enters_before_the_root_lock` misnamed (no stop) and proves hold-with-root-free only, not root-inside-hold; minor (deferred): `..._reads_unfinished` never asserts UNFINISHED; minor (deferred): `_publish_operation_report` silently ignores `operation=` when `operations=` given and accepts `operations=()`; minor (deferred): `closed_at` stamped before the closing locks; minor (deferred): `Stop.reason` carries `str(refused)` — never to be copied into a record; minor (deferred): `AcquisitionOutcome` cannot distinguish already-held from expectation-mismatch; minor (deferred): `_refuse_acquired_dataset` duplicates the overlay idiom of `_validate_import_bundle`.
Task 5: complete (commits 696198c..229d9d6, review clean)
Task 6: dispatched (BASE b065711, sonnet)
Task 6: implementer done c72b24a (test-fast 5171 passed/1 skipped; cut19 J11b re-targeted; reconcile test assertion deviated from brief; RED not captured); review dispatched
Task 6: review clean. minor (deferred): survey_admission `APPROVED_SCHEMES` dead + stale comment; `resolver=`/`connect=` lost annotations (Resolver/ConnectionFactory importable); test_admission_survey `_SPEC` comment stale, case 6 "no request issued" now proven only in test_holdings_transport; reconcile test could assert the exact finding list; no arm sabotages `_closing_hold`'s currency check (cut-35 row candidate — note for Task 8/9).
Task 6: complete (commits b065711..c72b24a, review clean)
Task 7: dispatched (BASE c72b24a, sonnet)
Task 7: implementer done 7633785 (rederived_equal true, state.json byte-identical, 5/5 store observations); review dispatched
Task 7: review clean. minor (deferred): report's run command carried the session's SCIENCE_CUT*_ROOT exports beyond cut 34's command (inert for the mm30 driver).
Task 7: complete (commits c72b24a..7633785, review clean)
Task 8: Ruling: the plan's BI-11a/BI-11b `before` bytes name `store_refusal(caught)` in holdings/boundary.py and the predicate body there; after fix b065711 the call is `ctx.seam.store_refusal(caught)` and the predicate `_store_refusal` lives in root.py. The arms target the tree as it stands (BI-11a: holdings/boundary.py, the seam call; BI-11b: root.py, the predicate) with the same claims — because the arms pin behaviour, not the plan's draft bytes — costs if wrong: a mis-targeted arm reads `stale` in the runner and is caught there. Recorded for the results record §3.
Task 8: dispatched (BASE 7633785, opus)
Task 8: implementer done d525b7d (acceptance 27 passed; runner 28 arms sound, exit 0, ~58 min; T4-a/T4-b arms re-sited per the tree; BI-11 asserts PreconditionRefused); review dispatched; hook-pre-push started in background
Task 8: review clean on evidence; 1 Important (plan-mandated recording gap): frozen §5 module/sabotage divergences for H4-b, T2-c, T2-d, T4-a, BI-1, BI-11b (and BI-11's cause name) must be tabled in the results record §3. Ruling: this is Task 9's deliverable (the declaration is sha-pinned and sound; no code change) — carried into Task 9's dispatch as a required §3 table. minor (deferred): T2-b's store-less half runs off the certified volume (note in results record); BI-9 shells `git show 3873d16:` (needs history; comment); test_n2_cut35.py:310 trailing "Export the live tuple" comment followed by nothing.
Task 8: complete (commits 7633785..d525b7d, review clean; results-record obligation → Task 9)
Task 9: dispatched (BASE d525b7d, opus) — Steps 1–4 only; Step 5 (merge, gate on merged tree, §6) is the controller's after the final review
Task 9: implementer done c1de7e2 (ids beliefs-86b150/1af7a7/940592; 183/216; gate still running at commit; flags test_recent_cut_acceptance.py lacks a cut-35 row — for the final review); review dispatched
Gate at d525b7d..c1de7e2 (just hook-pre-push, detached): All checks passed; 5212 passed, 1 skipped in 1196.49s; TS 155 passed; exit=0.
Task 9: review — 1 Important (holdings design §3 sentence spliced into the dated note) + minors (blank lines after two list-embedded notes; §3.3 Task 4 omission; lane-row overlap names world/verify.py instead of stored.py; T2 corpus-write history vs cut 19; gate line for §1). Ruling: minors bundled into the fix round (same files, one-line edits) — because a separate deferral would cost a second docs commit for no review benefit — costs if wrong: nothing structural.
Task 9: fix round 1 dispatched (resume implementer; FIX_BASE c1de7e2)
Task 9: fix round 1/5 (6 addressed, 0 open; commits c1de7e2..1318b9f)
Task 9: complete (commits d525b7d..1318b9f, review clean; Step 5 merge pending)
Final review: dispatched (merge-base 728a178..1318b9f, opus)
Final review: With fixes — Important 1: transport echoes the Content-Encoding header value into a durable reason (plan-mandated; spec never asked for it) → `Failed("content-encoding is not identity")`; Important 2: test_recent_cut_acceptance.py needs the cut-35 row `(cut35, 35, (28, 27, 8))` (convention since cut 33; a plan-template defect). Ruling: fix both on the branch before merge — because both are one-line source edits outside any frozen file and the final reviewer verified the row passes — costs if wrong: a re-run of the focused tests. Deferred minors triaged by the final reviewer: 2 fix-before-merge (above), ~14 file-as-one-idea, rest non-issues.
Final fix wave dispatched (FIX_BASE 1318b9f, sonnet)
