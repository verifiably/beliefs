---
id: beliefs-5e66ba
title: Recommend a long-term evidence-aggregation direction and what it asks of the weighted-belief design
status: todo
priority: 2
size: s
complexity: high
process: direct
created: 2026-10-24T01:04:14Z
updated: 2026-10-24T10:05:40Z
depends: [beliefs-9bf498, beliefs-7edb06, beliefs-d6060a]
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: given the inventory, the prior-art survey and the graphical-model gaps (sibling tasks under this goal), what should belief aggregation become over the long term, and in what order? Candidates to weigh include keeping v1 and adding a weighted successor over commensurable groups; a likelihood- or e-value-based carrier, reported separately from any declared prior so the data stay in front; and policies that read composite structure. For each, name which inventory items it fixes, what it needs the kernel to hold, and its risk to the receipt and independence guarantees. The first science workflow is now sci-35af80; its composite, scope/measurement and causal-tool pieces can proceed under the current belief policy after their own semantic/design prerequisites. Rank later improvements by what they unlock without making this synthesis or a weighted successor a gate for that workflow. Preserve separate presentation of evidence coverage, identification, scope and unresolved assumptions; do not prescribe a graph-confidence scalar or revived ladder without a demonstrated use. Treat scope/commensuration equality as necessary typed information, not sufficient evidence of safe pooling, measurement validity or independence. Include the diagnostic-computation versus belief-admission distinction from beliefs-d6060a and the follow-on roles of structural sensitivity (sci-434b9c), model criticism (sci-37f0c3) and question-directed next (sci-171ad1). End with: a recommended direction, what it would ask of beliefs-638318 (and whether it meets that task's wake condition), and how it relates to beliefs-8b26dc. Output: [ref:direction], for the user to review. No design spec.

Where to start: [ref:brief] frames confirmation versus secondary analysis separately from participant overlap. Use the completed beliefs-9bf498 inventory, sibling survey and graphical-model research, and the existing acceptance contract in docs/superpowers/specs/2026-10-02-belief-acceptance-design.md.

Bound: Preserve the synthesis's existing remit and dependencies; add these two cases to its existing comparison rather than starting a separate review or successor design. Compare caller-side pinned acceptance, governed classification/overlap evidence, and a successor policy. Do not assume applicability is a free-form label slot, dataset disjointness proves no selection exposure, or publication statements automatically certify independence. Keep conclusions conditional on the external protocol/roster evidence not checked in this pass.

Expected result: In [ref:direction] and [ref:brief], recommend the smallest owner and next step for each case: what current acceptance can already do; what evidence representation, conflict/retraction and digest questions need reviewed design; and whether either case actually meets the weighted-policy or inherited-standing shelf conditions. This recommendation must preserve the separately tracked science workflow's independence from aggregation research. No implementation or design spec here.

Ideas it wakes: On completion, run `tasks note beliefs-a91959 --no-reviewed "<finding>"` and `tasks note beliefs-6cd85f --no-reviewed "<finding>"` before this result's branch merges.

## References

- direction (output, kind=brief): docs/notes/evidence-aggregation-direction-brief.md — the recommendation
- brief (input, required, kind=brief): docs/notes/2026-10-24-confirmation-independence-brief.md — confirmation selection and participant-overlap decisions for the synthesis

## Notes

- 2026-10-24T02:19:37Z (main): scope: rescoped; preserved the prior-art/inventory/graphical research dependencies and successor-policy decision; constrained the synthesis so it cannot gate the independently tracked science workflow or imply typed scope equality makes pooling safe. Premises checked against db878fd and the accepted follow-up direction.
