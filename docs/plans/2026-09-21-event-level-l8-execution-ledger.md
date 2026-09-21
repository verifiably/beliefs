# Execution ledger — event-level L8 (cut 36), 2026-09-21

The subagent-driven execution ledger of `../superpowers/plans/2026-09-21-event-level-l8.md`, committed before the worktree's removal (cut 35's precedent, `2026-09-20-url-retrieval-execution-ledger.md`). Paths inside are the worktree's; the run logs live under the main checkout's `.work/acceptance/`.


Spec: docs/superpowers/specs/2026-09-21-event-level-l8-design.md (reachable, a61c119). Worktree .worktrees/event-level-l8, branch event-level-l8, plan at 05f6717. Global constraints copied to global-constraints.md beside this ledger.

## Pre-flight scan (2026-09-21)

| Pair / task | Produces vs consumes | Found |
| --- | --- | --- |
| T0 → T5 | freeze commit hash + cut-36 body sha256 → test_n2_cut36.py's pinned freeze | consistent; T5 reads them from git after T0 lands |
| T0 → T7 | cut doc frozen §§2–7 → T7 edits `**Status:**` only | consistent (frozen body byte-exact) |
| T1 → T3 | `moment(view, digest) -> int|None` (raises EventUnknown), `place(view, *, genesis_digest, head_digest) -> Placement|None`, `contains/excludes(placement, moment)`, `Event`, `Order` → `_placement`, `_witnessed`, `_event_order` | names and signatures match in both task bodies |
| T1 → T3 (root.py) | `Event`, `Order` re-exported from `beliefs.world.events` | consistent; events.py imports only errors + logmodel (composition-root invariant holds) |
| T2 → T3 | `_ordered_by_descent(view, e1, built_from, absent_state) -> Ordering` → `_witnessed` calls it with the one world view | consistent; T2 keeps cut 8's two pinned lines byte-exact |
| T2 ↔ verify.py pins | `first = _packaging_identity(e1)\n    second = _packaging_identity(e2)` and `_publication_settlement`'s `if type(entry) is SettledEntryView …` stay | T2 step verifies via `tests/test_arm_staleness.py tests/test_frozen_guards.py` |
| T3 → T4 | `root.event_order(config, a, b) -> Order`, `root.Event`, errors → acceptance module | consistent |
| T4 → T5 | sixteen `test_<unit>_…_durably` names → `UNIT_CHECKS` | names listed identically in both tasks (checked in plan review 1–2) |
| T5 → T5 | 18 arms over 16 units: L8-a ×2, L8-j ×2, fourteen ×1 = 18; row `(cut36, 36, (18, 16, 3))`; guard `homed` map | arithmetic consistent |
| T5 → T8 | runner `cut36_acceptance.py` chains `cut35_acceptance.py`; recent-cut row → gate | consistent with the cited-not-run rule (cut 8 never chained) |
| T6 → T7 | reproduction §15 → results record cites it | consistent |
| T7 → T8 | close beliefs-77e2fc then beliefs-b34652 (child before parent) | consistent |
| T3 self | mixed-fault test `test_a_malformed_first_chain_answers_before_the_second_lock_is_taken` vs loop code returning `unordered` inside the loop | agree |
| T4 self | fixture `target-{corpus_id}` per corpus; `RegistryCarrier.from_record`; `overlapping_builds` finally releases+joins | agree (plan review 2) |
| Rubric conflicts | none: no assertion-free tests, no verbatim duplicated logic block mandated (the shim is a deliberate byte-for-byte cut-35 pattern the guard depends on) | — |

Scan clean; no rulings needed before Task 0.

## Task log
Task 0: implementer DONE at 6353456 (freeze commit 635345697562f71f23763b72bbd129fc8c19007b; cut doc sha256 c4dea1fc153ecb2a0c5f90fc647ed9f67d3f891498c7e87f1d445366a4f4d6bb); review dispatched
Task 0: minor (deferred): cut doc §5 does not restate that cut 8's guard is cited-not-run (§3's L8-a row carries it; brief's §5 text has no such sentence) — Ruling: leave the frozen body as committed; the results record (Task 7) can restate it — costs nothing if wrong beyond a doc sentence
Task 0: ⚠️ §1/§6/§7 prose not brief-verbatim — controller checked §6/§7 against the brief's sketch: all four §7 limitations and all four §6 checks present; resolved
Task 0: complete (commits 05f6717..6353456, review clean)
Task 1: minor (deferred, plan-mandated): moment's registration branch does a second scan of view.entries after building positions; well-formedness invariants (unique digests, one settlement per registration) relied on, not re-checked — L2 classifies upstream
Task 1: complete (commits 6353456..df4cb0d, review clean)
Task 2: ⚠️ commit body trailer — controller checked `git log -1 --format=%B 2fc2232`: subject only, no trailer; resolved
Task 2: complete (commits df4cb0d..2fc2232, review clean)
Task 3: implementer DONE at c98a3c5 (611 passed on the seven gate modules; just test-fast 5208 passed, 1 pre-existing skip; three lint-only fixture edits to the brief's tests); review dispatched (opus)
Task 3: minor (deferred, fix before merge): root.py epochs_ordered docstring (~1798) still says "the event-level relation is deferred and L8 is partial" — amend to "the event-level relation is `event_order` (cut 36)" (AGENTS.md: stale current-facing claim)
Task 3: minor (deferred): test_world_log_audit.py double-witness docstring says "e2 and e4 follow each"; e4 follows e2's settlement — prose describes §4.3's schedule, not the fixture
Task 3: minor (deferred): test_world_log_audit.py `A = Event` alias comment mentions a `B` alias that does not exist
Task 3: complete (commits 2fc2232..c98a3c5, review clean)
Task 4: implementer DONE at ff6cb0c (16 passed in 77.86s on the certified volume; three lint-only edits); note for Task 7: quote a run without the doubled -q so the count line shows; review dispatched (opus)
Task 4: minor (deferred, brief-verbatim): L8-j's `aside` mkdtemp not removed in a `finally` (leaks cut36-aside-* on the certified volume on assertion failure); fixture `built = Built()` outside the `try` (leaks roots if Built.__init__ fails); BI-2 compares resolved vs unresolved world_root (symlinked SCIENCE_CUT4_ROOT would fail)
Task 4: minor (deferred): L8-j checks the carrier-malformed and world-malformed states separately, not simultaneously as spec §8.2 case 6's "and" reads — results record (Task 7) should say so in a sentence
Task 4: complete (commits c98a3c5..ff6cb0c, review clean)
Task 5: implementer DONE at 5e9a9e4 (gates 25 passed; guard 9 passed/1 deselected; all 18 arms sound via test_n2.audit); task beliefs-e7e497 left doing until the run of record. Controller launched the chained runner detached 12:53 UTC → log <main checkout>/.work/acceptance/cut36-runner.log (main checkout .work/acceptance/cut36-runner.log); review dispatched (opus)
Ruling: Task 6 (reproduction re-run) waits for the chained runner to exit — `state.py` rewrites state.json with a non-atomic write_text and cut 32's guard plus the composite/estimand acceptance modules in the chain read mm30's state.json; a racing read could fail the run of record — costs ~1 h of serial time if wrong, nothing else
Task 5: minor (deferred, inherited from cut 35): test_n2_cut36.py:303 dangling "Export the live tuple" comment with nothing after it
Task 5: minor (deferred): L8-c's after introduces a dead `sequence = 0` binding; its bite rests on L8-c's source inspection (by design of the row)
Task 5: review clean at 5e9a9e4; completion pending the run of record (detached runner launched 12:53 UTC)
Task 5: run of record green (log main .work/acceptance/cut36-runner.log: chain cut 35→17 then [cut36 phase 2/3] 16 passed in 92.79s, [cut36 phase 3/3] 10 passed in 32.85s, declared arms 18 (= 16 units; 3 rows), rows-exercised line); beliefs-e7e497 closed in a chore commit
Task 5: complete (commits ff6cb0c..5e9a9e4 + tasks chore, review clean)
Task 6: implementer DONE at 810ab3d (same NoBelief answer, state.json byte-identical, driver reads no relation; 50 passed); review dispatched
Task 6: ⚠️ "mm30's world has one corpus chain" — controller checked the mm30 root: one corpus.yaml under it, one `corpus` root beside one `world` root, no epochs directory under the world; resolved
Task 6: complete (commits 7cb5151..810ab3d, review clean)
Task 7: implementer DONE at 406d1a6 (13 files; roadmap_status "Closed 186 of 216; open 30."; designs/guide guards 23 passed; ten wording departures listed in its report); review dispatched (opus)
Task 7: review at 406d1a6 — Important: roadmap:329 "Eight others" over a nine-name list (base said "Seven" over eight; carried forward) → fix round 1 dispatched (resume implementer)
Task 7: minor (deferred, fix before merge): cut doc header `**Design:**` line still ends "implementation not yet started." (outside pinned §§2–7; Status-only scope) — Ruling pending at the final review
Task 7: minor (deferred): guide "Thirty-two conformance cuts" counts results files (32) while cuts 4–36 are 33 (cut 25 records discharge in its cut doc) — brief-mandated convention
Task 7: minor (deferred): open-questions.md:200 no blank line before `## Computation and reproducibility` (pre-existing)
Task 7: fix round 1/5 (1 addressed, 0 open — "Eight" → "Nine"; commits 406d1a6..6341910)
Task 7: complete (commits 810ab3d..6341910, review clean after round 1)
Task 8: beliefs-77e2fc started; final whole-branch review dispatched (opus) over acf4692..6341910 with the 12 deferred minors for triage
Final review (opus): ready with fixes. Important: (1) root.py epochs_ordered docstring stale; (2) LogEvidenceRefused propagation untested (spec §8.1) — one fix wave dispatched. Minors: spec §3/§4.2 drift (place/_placement split; continue-for-assert) → dated note in spec §12 (folded into the wave); one-direction `unordered` in L8-j acceptance + unit twin → Ruling: leave (argument-symmetric by construction; fixing the acceptance module post-run-of-record needs a phase re-run) — costs one asymmetric assertion if wrong; _witnessed O(E²) cost → leave (D7 dictates; no consumer); overlapping_builds join-timeout path → leave; literal host paths in plan/§15 → leave (precedent §13/§14, cut 35's plan). Triage of the 12 ledgered minors accepted as the reviewer stated (cut doc Design header line: leave — cuts 34/35 carry the same line; Ruling: keep the "only its status line changes" record claim true).
Final fix wave landed: fff26ec (root.py docstring; LogEvidenceRefused propagation test; two prose nits), 248d6cb (spec §12 note; results §3.2 final-review entry); 470 passed on the four covering modules; scoped re-review dispatched
Final fix wave re-review: all addressed, no new breakage. Gate launched detached (just gate → main .work/acceptance/cut36-gate.log)
Task 8: gate green at 248d6cb (just check: All checks passed, pyright 0 errors; pytest 5251 passed, 1 skipped in 1409.08s; vitest 155 passed; log main .work/acceptance/cut36-gate.log, 16:00–16:24 UTC)
Task 8: complete pending merge (tasks closed; ledger committed as docs/plans/2026-09-21-event-level-l8-execution-ledger.md)
