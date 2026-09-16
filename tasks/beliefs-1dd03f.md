---
id: beliefs-1dd03f
title: Make the estimand grammar's three closed sets total in code
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-16T06:45:37Z
updated: 2026-09-16T06:45:37Z
depends: []
tags: [belief, contract]
agent: claude-code/claude-fable-5-1
---

Final review of cut 31 (2026-09-16): uncertainty_kinds is parsed and projected but read by no code path; contrast_kinds and scales are checked for membership and then dispatched with an implicit else (decode.py's levels/else-continuous; estimand.py's multiplicative/else-additive), so a base contract widening a set is accepted and silently mis-interpreted. Refuse at EstimandGrammar parsing or profile compile any set that is not exactly the tags the kernel implements, naming the unoperable tag; turn the two else branches into elif + raise. Touches src, so it lands with the next cut that re-runs the certified chain; the results record §3 states it as a limitation until then.
