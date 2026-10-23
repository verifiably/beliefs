# Session sharing and publish doors execution ledger (beliefs-f24fe9, 2026-10-23)

The subagent-driven execution record of `../superpowers/plans/2026-10-23-session-sharing-and-publish-doors.md`: pre-flight scan, per-task completions, the final review and its fix round, every ruling the controller made, and the deferred minors the final review triaged (it judged none but the one it promoted must be fixed before merge). Kept as a durable artifact; the code history is the record of what landed. No conformance cut (spec decision 13).


Spec: docs/superpowers/specs/2026-10-22-session-sharing-and-publish-doors-design.md (read).
Branch: feat/f24fe9-session-doors; plan approved at cfe3bc2 (plan text says ddcb955); start HEAD 0e9fbfb.

## Pre-flight scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 -> T3, T5 | `RequiredCapabilities.sharing()` -> scoped(SHARING, "A") | consistent |
| T2 -> T3 | SharingEvidence/SharingLine/TRANSITIONS, InvocationRecord.sharing -> _Invocation.sharing, _record_sharing | consistent |
| T3 -> T5, T7 | world_config, _record_sharing, `_require_current` -> doors | consistent |
| T3, T5, T7 share test_session_writer.py method-set test | 17 -> 18 -> 20 -> 22 names | consistent (T7 says 22) |
| T4 -> T7 | LedgeredPort.execute_fulfilling_guarded -> publish's `_bind_publication` via operation_port() | consistent |
| T4 -> T6 | publication_doors `.reason` read; T6 edits publish.py, not publication_doors | no overlap |
| T5 -> T6, T7 | session_doors_fixture.py (published_source, publish_locally) -> preview and door tests | consistent; T6 creates test_session_publish_door.py, T7 extends it |
| T6 -> T7 | require_publishes, hold= -> door | consistent |
| T4, T6 acceptance probes | J7b (cut 11), Y6-a (cut 40) live matchers; declarations frozen | distinct files |
| T8 | docs over all tasks | consistent |
| T1 self | tests vs spec §6 Permit | spec also asks for a for_kinds route compiling to the permit and a ceiling lacking registry refusing at scoped naming it; plan omits -> R1 |
| T2 self | tests vs code | consistent |
| T3 self | tests vs Interfaces | consistent |
| T4 self | tests vs spec §6 guarded | spec asks a non-current invocation refusing before the inner port on the guarded form; plan list omits -> R2 |
| T5 self | "disagreeing copy" test comment is self-contradictory (artifact mismatch would refuse at the binding) | -> R3 |
| T6 self | spec §6 preview asks entries under v3; plan tests v2 only | -> R4 |
| T7 self | tests vs Interfaces | consistent |
| Global: inventory closed both ways | doors call restore_root/admit_publication/publish (not primitive names); ledgered guarded form joins route exemptions (T4) | -> R5 |

- Ruling R1: Task 1 adds the spec's two extra permit cases (a for_kinds route that would compile to the sharing permit refuses; a ceiling without `registry` refuses at `scoped` naming `registry`) — spec §6 binds and the plan is its argument — cost if wrong: two redundant tests.
- Ruling R2: Task 4 adds a guarded-form test that a non-current invocation refuses before the inner port — spec §6 lists it — cost if wrong: one redundant test.
- Ruling R3: Task 5's "disagreeing copy" test builds evidence from the right sibling and corrupts one record's bytes in the copy, expecting a non-validated verdict line and no grant — the artifact-binding check would otherwise refuse first, per decision 4 — cost if wrong: the test exercises a different refusing path than the spec author pictured.
- Ruling R4: Task 6 adds a v3 preview case asserting attribution entries equal what publish freezes, reusing test_publication_attribution.py's v3 fixture pattern; if no v3 world can be built without disproportionate fixture work, the implementer reports it and the v3 claim rests on the existing attribution tests through publish (which now calls the preview) — spec §6 asks for it — cost if wrong: extra fixture work.
- Ruling R5: a door that the inventory tests flag as a new write entry point joins WRITE_ENTRY_POINTS and test_permit_entry_points CASES per the Global Constraint; none is expected beyond T4's route exemption — cost if wrong: an inventory edit the review must check.

## Tasks
Task 1: dispatched (BASE ac5b2cc; implementer sonnet)
Task 1: review round 1 accept (reviewer sonnet); warn items resolved: the exact-permit refusal test passing in GREEN shows the ContextVar gate holds; imports resolve per the 130-passed run.
Task 1: minor (deferred): test_no_for_kinds_route_can_compile_to_the_sharing_permit restates one fact twice and couples to the "does not admit route" wording; could assert no for_kinds result equals the sharing permit.
Task 1: minor (deferred): the lifecycle-alone refusal case guarded nothing new (brief-mandated).
Task 1: complete (commits ac5b2cc..b4b4742, review clean)
Task 2: dispatched (BASE 639d008; implementer sonnet)
Task 2: review round 1 accept (reviewer sonnet); warn items resolved by controller: require_hex enforces exact str + lowercase hex (ledger.py:73-76); InvocationRecord is constructed only in ledger.py (3 sites, all updated).
Task 2: minor (deferred): sharing `at` checked non-empty only, as every line kind is; spec §3 states the UTC form.
Task 2: minor (deferred): SharingEvidence.__post_init__ and the _validated_line sharing branch duplicate the source/location checks.
Task 2: minor (deferred): test_sharing_evidence_validates_each_field matches loosely on the field name.
Task 2: complete (commits 639d008..cd41a54, review clean)
Task 3: dispatched (BASE 8936b9b; implementer sonnet)
Task 3: review round 1 accept (reviewer sonnet); warn items resolved: Task 2's append/parse path is exercised by the round-trip and fault tests; record_sharing calls no write primitive and both closed inventories ran green in test-fast (6167 passed).
Task 3: minor (deferred): _record_sharing's TypeError/ValueError argument checks precede _require_live, so a bad verdict on a closed/failed session raises ValueError, not SessionClosed/SessionLedgerFailed.
Task 3: minor (deferred): currency test lacks the "another's invocation" case (B current, writer scoped to A).
Task 3: minor (deferred): empty-verdict test does not assert invocation_sharing("A") == ().
Task 3: minor (deferred): test_world_config_must_agree_with_world_id builds three sessions in one test via a mkdir loop; parametrize.
Task 3: complete (commits 8936b9b..140b562, review clean)
Task 4: dispatched (BASE b5d864f; implementer opus — multi-file protocol change, durable composition tests, live-probe re-target)
Task 4: implementer NEEDS_CONTEXT — spec §4.6's `_registration_for` readback (exactly one registration per intent) breaks test_publication_engine_order.py::test_a_rolled_back_fulfilment_leaves_the_intent_open_for_a_retry (rollback + same-intent retry leaves two registrations; commit lands, readback raises "found 2", LedgeredPort never ledgers it).
- Ruling R6: the guarded readback (DurableOperationPort.execute_fulfilling_guarded) returns the one registration fulfilling `fulfills` whose SettledEntry is committed, requiring exactly one (ExecutionError otherwise), in a root.py helper beside `_registration_for`; `execute_fulfilling` keeps its exactly-one rule unchanged; Task 8 records the amendment in the session-routes note and the spec gets a dated §4.6 note — why: the engine refuses a second committed fulfilment for one intent, so "the committed one" is exact and keeps a fail-early check, where the implementer's "latest" would silently pick an uncommitted registration if settlement ever lagged; and cut 39's retry path is pinned by an existing test — cost if wrong: one helper to swap for latest=True, and the spec note to revise.
- Ruling R7: "ten port doubles" is twelve in the tree; only the four that return a value change, three forward the inner value, five never return — why: the protocol's return type binds only returning doubles — cost if wrong: a pyright-visible mismatch, which `just check` would catch.
- Ruling R8: the production-run-through-the-session test runs on the durable session (certified_work), not tmp_path — why: "reconcile reports nothing" needs a real chain — cost if wrong: none beyond test runtime.
Task 4: implementer DONE 2fa5ea1 after R6-R8
Task 4: review round 1 accept (reviewer opus); lock order and fallback-before-commit checked clean; warn item (R6's spec §4.6 note and session-routes note) carried into Task 8's dispatch.
Task 4: minor (deferred): J7b live entry keeps the 2026-10-09 "exactly the formatted declared sabotage" comment; add a dated live re-target line (test_n2_cut11.py:355-357).
Task 4: minor (deferred): _committed_registration_for copies _registration_for's read_chain try/except block verbatim (root.py:1114-1118 vs 1151-1155).
Task 4: minor (deferred): GuardedCommit checks types only; empty entry / empty reason accepted.
Task 4: minor (deferred): no TracingLock test that the session lock spans the inner guarded commit.
Task 4: minor (deferred): routes.py:101 chosen[0] picks silently on a double that calls fallback twice, IndexError after commit on one that returns a reason without calling it (doubles only).
Task 4: minor (deferred): the cut-39 retry test passes under committed-match or latest alike; R6's distinction is untested.
Task 4: complete (commits b5d864f..2fa5ea1, review clean)
Task 5: dispatched (BASE 27f2332; implementer opus)
Task 5: implementer DONE_WITH_CONCERNS ab451ac; five deviations ruled:
- Ruling R9: the shared fixture's alpha holds both halves of topic_nodes() and the epoch covers alpha only (the brief's shape refuses closure-incomplete / corpus-drifted); world (alpha, written) and mounts unchanged — why: the brief's fixture cannot publish and the plan says it mirrors cut 40's working source — cost if wrong: Tasks 6-7 test a slightly different world shape than the plan pictured.
- Ruling R10: the restore door's first parameter is `root`, not the spec's `copy`, because the capability-boundary raw-write scan rejects `copy` as a byte-mutation name; Task 8's writer-session amendment records the name and science's Interfaces adapt — why: the boundary scan is a standing invariant and the spec's name is not load-bearing — cost if wrong: science passing `copy=` by keyword breaks until it renames.
- Ruling R11: restore_root's subject TypeError and the argument-type checks run before the lock, per spec §4.4 "before any check"; the brief placed the subject check after the family check — why: the spec binds over the plan — cost if wrong: a wrong-typed call on a stale writer raises TypeError, not SessionProtocolError.
- Ruling R12: admit_publication refuses a None world configuration before the evidence binding — why: both refusals precede any effect, and the brief's own tmp_path test can reach it only there — cost if wrong: a world-less session with disagreeing evidence reports SessionProtocolError rather than SharingEvidenceDisagrees.
- Ruling R13: the refuted-chain admit test restores through the door first and asserts invocation_sharing("A") == (the fetched line,) — why: it still shows the admit appended nothing — cost if wrong: none.
Task 5: review round 1 accept (reviewer opus); binding before act only under the session lock, every carrier searched, no atoms import, no inventory row owed; warn item (science's `copy=` keyword) carried to Task 8 via R10.
Task 5: minor (deferred): restore door raises an untyped NodesValidationError/OSError when the copy's records do not parse (binding reads records before the act); untested and undocumented (writer.py:178).
Task 5: minor (deferred): _require_door_arguments' three TypeError branches untested; isinstance(root, Path) not exact-type (writer.py:481).
Task 5: minor (deferred): decode_head_artifact(carrier.data) re-decodes carrier.artifact (writer.py:174).
Task 5: minor (deferred): every-carrier test varies only the subject; no same-subject wrong-digest-first case or multi-entry `found` join.
Task 5: minor (deferred): the disagreeing-copy test asserts verdict != "validated" without pinning the outcome.
Task 5: minor (deferred): fixture evidence_for reads the marker from s.dest regardless of destination (session_doors_fixture.py:151-153); flagged to Tasks 6-7.
Task 5: complete (commits 27f2332..ab451ac, review clean)
Task 6: dispatched (BASE 323eb85; implementer opus)
Task 6: implementer DONE_WITH_CONCERNS 80230ca (test-fast 6207 passed, 1 skipped, slow under host load ~25; nothing left running).
- Ruling R14: R4's v3 preview case runs on the attribution module's wrapper fixture (intent and _run stood in), not a real v3 world; the real-world v3 claim rests on the attribution acceptance module through publish, which now calls the preview — why: a real v3 world was disproportionate fixture work, the outcome R4 foresaw — cost if wrong: a v3-only divergence between preview and publish on real roots goes unseen until the acceptance module runs.
- Ruling R15: that `_open_publication` runs inside `hold` is proven in Task 7 (the door passes `_closing_hold`); Task 7's dispatch asks for one test that the hold is entered around the intent — why: the hold has no caller until the door — cost if wrong: none if Task 7 delivers it.
- Note: cut 40's frozen declaration lives at python/tests/n2_arms_cut40.py (not tests/acceptance/); untouched.
Task 6: review round 1 accept (reviewer opus); refusal order verified verbatim except the ruled profile-disagrees move (MalformedRecord now also precedes it, within decision 10); Y6-a live after re-runs evaluate_query, sound; warn items carried: R15 to Task 7, R14 rests on the attribution acceptance run (84 passed).
Task 6: minor (deferred): test_n2_cut40.py's trailing "Export the live tuple ..." comment now sits above the new Y6-a test and reads as describing it (:359-362).
Task 6: minor (deferred): no ordering test that pins-disagree / MalformedRecord precede profile-disagrees.
Task 6: minor (deferred): test helper _mint takes a bare dict query.
Task 6: minor (deferred): test_session_publish_door.py imports Clock and PUBLISHES from session_doors_fixture, outside its __all__.
Task 6: minor (deferred): the v3 preview test runs the preview before s.run() on the same wrapper fixture without stating their independence.
Task 6: complete (commits 323eb85..80230ca, review clean)
Task 7: dispatched (BASE 00a192c; implementer opus)
Task 7: implementer DONE_WITH_CONCERNS e480f5b (test-fast 6220 passed, 1 skipped).
- Ruling R16: resume_publish's door opens the session's world under the scoped authority although the act's resume_publish takes no world, as spec §4.4 and decision 7 say ("check liveness, currency and the publication permit under the session lock, open the world, release the lock"); resume therefore needs a world configuration and resolves recovery on the world root — why: the spec binds over the act's signature, the open is the same authority-scoped open publish makes, and a session without a world cannot publish either — cost if wrong: a one-line removal in `_publishing` and a spec note, if a world-less resume is wanted.
- Ruling R17: Task 5's inlined no-world message is now one constant `_NO_WORLD` behind a helper shared with admit_publication, and open_world is a module-level import in writer.py (for the coordination-permit monkeypatch) — why: one message, one source; still imported through beliefs.root — cost if wrong: none.
Task 7: review round 1 accept (reviewer opus); lock order session-then-root on every path incl. the hold re-entry; reconcile closes the ledger-to-chain check. Warn items resolved by controller: the one skip predates the slice (baseline 6123 passed, 1 skipped) and is not CapabilityUnavailable (conftest skips that only under VERIFIABLY_UNCERTIFIED_HOST=1, unset here; the portable suite's structural skips, e.g. test_composite.py:190, account for it); the post-entry close window is decision 7's accepted one, and Task 8's docs claim only the at-entry guarantee.
Task 7: minor (deferred): operation_port() is resolved after the world open, so a portless scoped writer would open the world before refusing (writer.py _publishing).
Task 7: minor (deferred): the Review Focus 4 test does not prove the world was opened before the operations-root refusal (no open_world call-count spy).
Task 7: minor (deferred): crash/Crash helpers copied from tests/acceptance/test_publish_act_acceptance.py into the portable door test.
Task 7: minor (deferred): act_line.record_ids == tuple(set) in the refused-publish test is order-dependent beyond one act-report.
Task 7: complete (commits 00a192c..e480f5b, review clean)
Task 8: dispatched (BASE bafc98d; implementer sonnet; carries R6, R10-R12, R16 and the at-entry guarantee into the docs and a dated spec note)
Task 8: review round 1 accept (reviewer sonnet); append-only (0 deletions), names verified at HEAD; warn items resolved: plan_records validation before commit and `execute` refused were verified in Task 4's review (routes.py:67-68, 89-101).
Task 8: minor (deferred): ragged line wrap in the publish-act-local "Order" bullet.
Task 8: minor (deferred): writer-session text says restore_root's root is "a Path"; the code uses isinstance.
Task 8: complete (commits bafc98d..519418c, review clean)
Final review: dispatched (opus) over cfe3bc2..f187456 with progress.md rulings and deferred minors to triage
Final review round 1 (opus): with fixes — Important 1: the restore door's evidence binding lets a corrupt copy escape as untyped NodesValidationError/PlacementError/CollisionError/OSError (writer.py:183), against restore_root's "malformed outcome, never a pre-evaluation exception"; fix with the _CAPTURE_DAMAGE mapping to a typed refusal (promotes Task 5's deferred minor). All rulings R1-R17 agreed; every other deferred minor may stay deferred.
Final: minor (deferred): record_sharing checks permit/transition/types before liveness/currency, unlike the act doors (writer.py:528-536).
Final: minor (deferred): artifact binding accepts any same-subject carrier, not necessarily the one the act validated against; could refuse >1 same-subject carrier (writer.py:176-181).
Final: minor (deferred): readback failure after a durable guarded commit leaves a committed registration unledgered (pre-existing shape shared with execute_fulfilling); _record_committed's docstring claim "only a crash or ledger I/O failure" is now inaccurate.
Final: minor (deferred): chosen[0] in routes.py:101 relies on the durable port always calling the fallback; an assert would fail early (doubles only).
Final: minor (deferred): misplaced "Export the live tuple" comment in test_n2_cut40.py:359.
Final fix round 1: dispatched to Task 5's implementer (resumed) for Important 1 only.
Final fix round 1/5 (1 addressed, 0 open — corrupt copy refuses capture-damaged at both sharing doors; commits c95329f..fbdfc02); scoped re-review (sonnet, fresh): all findings addressed, no new breakage.
Final: minor (deferred): load_manifest(root) in _bind_sharing_evidence may still raise an untyped error on a corrupt corpus.yaml (out of the finding's scope; unverified).
Final review: clean after round 1.
