---
id: beliefs-631101
title: Refuse a replay's recipe-identity mismatch before executing the workflow
status: todo
priority: 3
size: s
complexity: mid
process: planned
created: 2026-10-02T20:34:41Z
updated: 2026-10-09T14:04:04Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
---

Why: execute_assessment_run and execute_production_run (python/src/beliefs/boundary.py ~L1043, ~L1117) compare result.run.recipe.identity() with expected_recipe_identity only after _execute_run returns. A replay of a tampered bundle is therefore refused only after a full planning and execution launch: ~12.6 s confined on titan, measured from science's transports test (sci-97727a). Scoping on 2026-10-09 found that every recipe field is fixed before any engine launch. Both paths build the recipe with _project from the captured bundle identity, the captured environment manifest, the definition, the invocation, inputs/parameters/nondeterminism and the policy. That happens in _execute_run just before the planning dir, and in _execute_confined just before sandbox_environment and materialize_snapshot. mint_run then stores the same Recipe object in RunClosure. No recipe field is known only after the run.

Done:
- Pass expected_recipe_identity into _execute_run and _execute_confined. Compare it right after _project and return _refused("recipe-identity-mismatch", ..., intent) before any planning or execution launch. This is still the post-intent refusal: the caller publishes the report fulfilling the intent, and the mismatched run is never minted or published.
- Remove the post-mint comparison so the check runs exactly once.
- Amend the intent-boundary design, whose text says the check runs "exactly once — after the mint, before the terminal publication" (docs/designs/2026-08-26-world-index-intent-boundary-design.md ~L500). This is a guarantee change: it needs a reviewed amendment, not just a code edit.
- Re-target the N2 arms whose before-text pins the moved block, following the frozen guard doctrine: the cut-3 portable T2 arm "a reconstructed-recipe mismatch closes its intent through a report registration" (tests/n2_arms_cut3.py ~L1663), through a portable override in tests/test_n2.py; and cut 11's J7a/J7b (tests/acceptance/n2_arms_cut11.py ~L722–760), through test_n2_cut11.py's _LIVE_SABOTAGES. The declaration files stay byte-exact.

Verification:
- A focused test in test_replay.py shows that a mismatched replay, assessment and production shape both, refuses with no engine launch. Check that no planning dir and no trace are created, or spy on run_engine/launch_confined.
- The existing mismatch tests (test_replay.py ~L389, test_run_persistence.py ~L198/225) still pass.
- test_arm_staleness reports zero stale arms, and the re-targeted arms' audits score sound.

## Notes

- 2026-10-09T14:04:03Z (main): scope: scoped; confirmed the recipe is fully projected before any launch in both the unconfined and confined paths; rewrote body; todo P3/s/mid/planned (banked design amendment plus N2 re-targets of cut-3 T2 and cut-11 J7a/J7b)
