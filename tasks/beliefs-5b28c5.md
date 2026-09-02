---
id: beliefs-5b28c5
title: Speed closure root membership without weakening recapture
status: done
priority: 0
size: s
owner: perf/remove-boundary-recapture
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T12:17:51Z
depends: []
tags: [performance, testing, confinement]
---

Why: minimal-v1 intentionally captures twice: once to mint the recipe and again immediately before launch to refuse an executing environment that drifted. That contract remains. Profiling one 8,367-artifact capture attributed 2.30s of a 5.68s profiled run to the Path.is_relative_to parent-membership scan, while file digest reads totaled about 0.38s.

Change: use os.path.commonpath for boundary-aware closure-root membership and os.path.relpath to spell the sandbox-relative path without rescanning Path.parents. Preserve longest-root precedence, different-drive refusal, returned roots, and every capture and environment check. Do not cache closure evidence or remove boundary.py:459.

Done when: existing closure/root mapping behavior remains green; three capture timings and the six boundary-running modules show a material improvement beyond variance; the full Python repository gates pass.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Rescoped from a test fixture seam to the measured product-level duplicate capture at boundary.py:459.
- 2026-09-02T10:44:46Z (perf/remove-boundary-recapture): Implementation started: encode the one-capture ruling and add a failing minimal-boundary capture-count regression before removing line 459.
- 2026-09-02T11:02:44Z (perf/remove-boundary-recapture): Design review found the banked run-confinement design explicitly requires two captures for minimal-v1; removing line 459 changes its environment-mutation contract rather than deleting a tautology.
- 2026-09-02T11:04:28Z (perf/remove-boundary-recapture): User ruling: retain minimal-v1's two-capture pre-execution environment verification; do not remove boundary.py:459.
- 2026-09-02T11:12:36Z (perf/remove-boundary-recapture): Approved rescope: optimize _Closure.root_of path membership; preserve both minimal-v1 captures. Pure performance refactor uses existing behavior tests plus repeated benchmark.
- 2026-09-02T11:56:03Z (perf/remove-boundary-recapture): Measured: controlled capture median 2.493s -> 2.112s (-15.3%); 118-test six-module baselines 522.09s/547.56s vs candidates 444.31s/446.41s (median -89.47s, -16.7%). Both minimal-v1 captures remain.
- 2026-09-02T12:10:47Z (perf/remove-boundary-recapture): Preserved both minimal-v1 captures and cut closure path-mapping overhead; full suite fell from 915.87s to 825.55s.
- 2026-09-02T12:17:51Z (perf/remove-boundary-recapture): Review fix: order commonpath with the registered root first to preserve Windows same-drive casing semantics; task body now names the implementation that landed.
