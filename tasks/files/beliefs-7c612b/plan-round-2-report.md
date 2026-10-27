Reviewer: claude-code/claude-opus-5-5. Relayed by user; read-only review.

The plan at `69577b6` (sha256 `9bcec8c8…b61815`, verified) is ready to execute: my verdict is accept. I found nothing Critical or Important, only three minor points that the executor can absorb during Tasks 3 and 4. I also checked the revised spec at `deb8d99`: all six round-2 findings are resolved as the report says. Approving implementation is your call. After that, the design session resumes beliefs-7c612b at execution Setup.

**Verified against the code**
- **Cut 47 is free.** No branch or worktree, including `ce9d05-test-latency`, has a cut-47 document. Cut 46 is still the highest.
- **Accounting.** `roadmap_status.py` reports 226 of 253 closed today, so reopening Y5 and Y17 gives the plan's 224 at freeze and 226 after discharge.
- **Cut-46 row format.** The `REOPENED` type, the `(cut, n, (arms, units, rows))` row shape and the "guarantee rows exercised" output line all match cut 46's form.
- **Runner chain.** `PREFIX_RUNNERS = ("cut46_acceptance.py",)` keeps the chain at constant depth. The `just --set one_cmd … test-one -q` command is the one cut 46 used, and `test-one` already wraps `host-budget run`.
- **Stale anchors.** Y17-a, Y17-g and Y17-i in cut 46 anchor on the `replicas = …` line or the `_selected_attributions(...)` call line, both of which Task 2 must change. The plan names exactly those three for retargeting.
  - Y17-f, h, j and k anchor on code the plan leaves alone.
  - Cut-40's live Y6-a anchors on `)\n    token = …`, not on the preview call, so it still applies unchanged. The plan's "only if needed" is correct.
  - No frozen function pins cover `publish.py`.
- **Named helpers exist.** `capture_fixture`, `wrapper_fixture` (with `.run`), `frozen_attempt`, `pin`, `Prepared`, `world_at`, `build`, `context_at`, `resume`, `unavailable` and `saved_marker` all exist. `source` is a fixture. The `_selected_attributions` spy at `test_publication_attribution.py:572` is positional, and the plan already covers forwarding the new argument through it.
- **Science tasks.** sci-9a7ce2 depends on beliefs-7c612b, and sci-775e90 depends on both, as the report says.

**Minor**
- **P1. Task 3 should reuse the existing durable fixture.** `test_markerless_replica_durably` (`python/tests/acceptance/test_publication_attribution_acceptance.py:289`) already builds the exact scenario: replicate, export the head, `restore_root`, then `admit_arrival(..., ReplicaOf(cid), ...)`. Pull its setup into a shared helper rather than rebuild it from the separate helpers. The plan's extra Fresh-admitted write root in the same world is a stronger, milestone-like case, but it should extend that helper, not fork it.
- **P2. Y17-x can't be killed by the remote mark-only case.** `_expected_marker` is called only from `_populate` (`publish.py:541`), and `_resume_from_mark` never reaches it. A sabotage in `_expected_marker` therefore has to be killed by the local-resume case, or by the remote case that still has its snapshot. Because the ownership declaration isn't stored, the sabotage can only invent an entry from the snapshot, for example `a.snapshot.attributions or (...)`. Task 4 should write that mutation text down and say which case kills it.
- **P3. The marker-present refusal's before-intent ordering has no arm of its own.** `test_ownership_refusals_before_intent` stays uncounted, and Y17-v only covers forwarding the declaration. That is acceptable, because the check sits in preparation and so runs before the intent by construction. The results record should still say so, so that no one reads the extended Y5 coverage as mutation-proved for the new refusal.

**Review notes** (I haven't written them; the task's controller records them):
- `review: spec round 3 — verdict: accept; findings: none; reviewer: claude-code/claude-opus-5-5` (the check of `deb8d99`)
- `review: plan round 2 — verdict: accept; findings: Minor 3; reviewer: claude-code/claude-opus-5-5`

The task's notes already hold plan round 1 (codex/gpt-6-astra, accept).

I changed nothing and ran only read-only commands, plus `roadmap_status.py`, which prints totals. Nothing was pushed and no processes are left running. The worktree `.worktrees/7c612b-replica-publication` and its branch `design/7c612b-replica-publication` are unchanged and unmerged. They get integrated locally after the implementation's final review.
