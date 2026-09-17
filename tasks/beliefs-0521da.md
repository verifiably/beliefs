---
id: beliefs-0521da
title: audit_world runs check_spec_target so spec-target-contradicted is reachable in the world audit
status: done
priority: 3
size: xs
complexity: low
process: direct
owner: design/correction-remainder
created: 2026-09-16T06:45:37Z
updated: 2026-09-17T08:27:34Z
started: 2026-09-17T08:26:01Z
completed: 2026-09-17T08:27:34Z
depends: []
parent: beliefs-dc4e56
tags: [belief, world-read]
agent: claude-code/claude-fable-5-1
---

Final review of cut 31 (2026-09-16): audit.py's _recompute (audit_world) calls check_analysis_spec only; check_spec_target runs in audit_corpus alone, so a raw-written spec whose estimand names the wrong claim or operator is contradicted only by the corpus audit. Task 8's ruling gave audit_world the pre-grammar codes on the reasoning that it audits the same records in this lane's own file; the same reasoning covers this. One line in _recompute plus a test_world_audit.py arm; touches src, so it lands with the next cut that re-runs the certified chain; the results record §3 and design §13 state it as a limitation until then.

## Notes

- 2026-09-17T08:26:01Z (design/correction-remainder): claimed by Codex task5, pid 4183152
- 2026-09-17T08:27:34Z (design/correction-remainder): RED uv run --frozen pytest tests/test_world_audit.py -q -k spec_target: failed with no finding; GREEN: 1 passed on 2026-09-17
- 2026-09-17T08:27:34Z (design/correction-remainder): audit_world now reports spec-target-contradicted through the shared target check; focused regression passes
