---
id: beliefs-010c6e
title: evaluation.gather decodes every stored assessment for every proposition
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-16T22:38:37Z
updated: 2026-09-17T01:15:33Z
depends: []
parent: beliefs-dc4e56
tags: [belief, world-read]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
agent: claude-code/claude-fable-5-1
---

gather calls assessment_value on every assessment node in the view and only then filters on the facet's proposition, so one raw-edited or pre-grammar assessment anywhere in a corpus refuses evaluation for every proposition, and cost is O(corpus decodes) per evaluation. Found at cut 32's whole-branch review (results §3.4, Important 3: the reading's column was narrowed to the member's assesses edges; the evaluator's own scan was out of the lane's scope). Filter by the assesses relation target before decoding, as read_composite now does, keeping the facet check as the second guard; a mismatch between the edge and the facet stays a loud refusal. Verify P1–P9 and the composite reading unchanged.
