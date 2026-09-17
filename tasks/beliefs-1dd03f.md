---
id: beliefs-1dd03f
title: Make the estimand grammar's three closed sets total in code
status: done
priority: 3
size: s
complexity: mid
process: direct
owner: design/correction-remainder
created: 2026-09-16T06:45:37Z
updated: 2026-09-17T08:30:23Z
started: 2026-09-17T08:28:05Z
completed: 2026-09-17T08:30:23Z
depends: []
parent: beliefs-dc4e56
tags: [belief, contract]
agent: claude-code/claude-fable-5-1
---

Final review of cut 31 (2026-09-16): uncertainty_kinds is parsed and projected but read by no code path; contrast_kinds and scales are checked for membership and then dispatched with an implicit else (decode.py's levels/else-continuous; estimand.py's multiplicative/else-additive), so a base contract widening a set is accepted and silently mis-interpreted. Refuse at EstimandGrammar parsing or profile compile any set that is not exactly the tags the kernel implements, naming the unoperable tag; turn the two else branches into elif + raise. Touches src, so it lands with the next cut that re-runs the certified chain; the results record §3 states it as a limitation until then.

## Notes

- 2026-09-17T08:28:05Z (design/correction-remainder): claimed by Codex task5, pid 4187868
- 2026-09-17T08:30:23Z (design/correction-remainder): RED Python focused selection: 6 failed (four exact-set, log scale, decode grammar); RED npm test -- declarations: 1 failed. GREEN Python 185 passed and TS 25 passed on 2026-09-17
- 2026-09-17T08:30:23Z (design/correction-remainder): Python and TypeScript refuse widened or narrowed estimand closed sets; dispatches refuse unoperable kinds and scales
