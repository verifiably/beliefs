---
id: beliefs-0e1acb
title: "Share live and epoch-view coverage, inbound edges and W8b text"
status: todo
priority: 3
size: m
complexity: mid
process: direct
created: 2026-09-25T11:35:00Z
updated: 2026-10-24T11:15:55Z
depends: []
tags: [world]
agent: claude-code
---

Why: Cut 41 intentionally copied open_world_view's coverage resolution, capture loop, W8b text and inbound-edge construction to preserve single-site sabotage targets. Main 96066b6 still duplicates coverage refusal text and inbound construction; the W8b text is also repeated without the equality pin that exists for manifest and duplicate-carrier messages. This is maintenance work, not a change to live-query or epoch semantics.

Established: The original claim that the capture loops are identical is no longer true. world/view.py loads manifests and supports strict refusal or on_damage="report", including collecting damaged-corpus remainders and producing DamageReport values. world/live.py collects damaged corpus ids into SelectionRefused("corpus-damaged") and uses live-evaluation drift wording. The W8b predicates also differ deliberately: live checks only non-world-kind participation after derive.address_map succeeds; the epoch view checks its captured uid ownership. These policies and their ordering must remain distinct.

Done: Share the common per-corpus carrier/status resolution, inbound-edge assembly and exact W8b refusal text through small private helpers beside the existing view code (live.py already imports world/view.py). Keep registry coverage selection, world-barrier scope, per-corpus holds, damage handling, capture-state checks, drift wording, mapped-record filtering and W8b predicates with their current callers. Do not force the full capture loops or uniqueness algorithms into one configurable abstraction. Preserve no-write live evaluation, stamp identity, inbound source_uid=None behavior for absent/unheld sources, result ordering and defensive copies. This explicitly narrows the original capture-loop de-duplication request to the common behavior that still exists.

Retarget every affected live sabotage through its guard's _LIVE_SABOTAGES and update affected live pin tables together; never rewrite frozen declarations, cited guards or historical result bodies. Start with cuts 23 (W10d/W10e/W10g), 27 (S9-a) and 41, then discover every current affected caller/pin rather than treating that historical list as exhaustive. The authority and original deferral are [ref:live-design] §8 and [ref:cut41-results] §§3.2–3.3; [ref:freeze-doctrine] governs current retargeting.

Verification: Through just test-one, cover test_live_selection.py, test_world_view.py, test_arm_staleness.py and test_frozen_guards.py, plus the affected acceptance checks and live N2 guards. Preserve the existing manifest/duplicate-carrier equality checks; establish W8b text parity and inbound parity while retaining the two capture/damage policies. A moved sabotage must still have a passing baseline and fail its own named checks, not merely match text. Run just test-fast before committing; capability-dependent runtime checks need the certified tuple and must report exact refusals. No runtime check was performed by this scope pass.

Where: python/src/beliefs/world/live.py (_coverage, _capture, _require_unmapped_uids_unique, _inbound); python/src/beliefs/world/view.py::open_world_view; python/tests/test_live_selection.py and test_world_view.py; affected guards under python/tests/acceptance/. Preserve the original review notes below as source material.

## References

- live-design (input, required, kind=spec): docs/designs/2026-09-24-live-query-evaluation-design.md — current live-query guarantees and original duplication ruling
- cut41-results (context, kind=report): docs/plans/2026-09-25-conformance-cut-41-results.md — original deferred review findings
- freeze-doctrine (input, required, kind=spec): docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md — retarget live machinery and preserve historical evidence

## Notes

- 2026-09-25T11:35:08Z (main): From beliefs-cc0aea's Task 3 review (2026-09-25): world/live.py (branch design/live-query, merged with cut 41's discharge) repeats open_world_view's coverage block and refusal messages, capture loop, W8b message and inbound-edge construction word for word. Kept deliberately (live-query design §8): the view.py lines are pinned by live arms of cut 23 (W10d, W10e, W10g) and cut 27 (S9-a), and cut 41's arms need single-site targets in live.py. Sharing them means re-targeting those arms through the guards' _LIVE_SABOTAGES tables, plus cut 41's. A portable test pins live's refusal messages equal to the view's in the meantime.
- 2026-09-25T13:46:35Z (main): Also from cut 41's final review: live.py's W8b refusal text repeats open_world_view's (view.py) and, unlike the manifest and duplicate-carrier messages, has no equality pin (Z5-c matches 'W8b' only). The de-duplication removes the copy; until then, pin it or accept the gap.
