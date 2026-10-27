---
id: beliefs-7c98bc
title: "Store the declared executes, targets and spec-input edges as node relations"
status: shelved
priority: 2
created: 2026-09-23T11:40:35Z
updated: 2026-10-27T13:06:47Z
depends: []
tags: []
agent: claude-code/claude-fable-5-1
---

Kernel §4.1 declares Run --executes--> AnalysisSpec and AnalysisSpec --targets--> Proposition as closed relation signatures, but run_node holds its spec in a facet and analysis_spec_node emits no relations (stored.py), so a view's closure predicate cannot walk either. Storing them as edges would let a findings view be one closure clause per assessment with no enumerated spec. Reaching a proposition from a dataset before any run additionally needs the spec's edge to each declared input dataset; the scope is all three or the pre-run benefit is not claimed. Not a prerequisite of anything; the second-project milestone's count of addresses entries per view (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §6.2, §11) is the measurement that scopes this.

## Notes

- 2026-10-14T02:15:03Z (main): shelved: Revisit when a worked findings view or the second-project measurement records costly explicit address enumeration and demonstrates the missing executes/targets/spec-input traversal it needs. Bring that consumer evidence and the current endpoint-enforcement research (beliefs-9c375c); do not claim pre-run traversal from only two edges.
- 2026-10-14T02:15:05Z (main): scope: shelved; at c1418e7 stored.py run_node and run_publication_node still store spec only in a facet and analysis_spec_node emits no relations; contracts/science/CONTRACT.yaml declares executes/targets but no spec-input signature. Keep the full three-edge proposal until a measured consumer needs it; endpoint-policy research beliefs-9c375c is related, not duplicate implementation work. The external science milestone/spec was not read in this fixed-checkout pass, so its completion and measurements remain unknown.
- 2026-10-27T12:49:57Z (main): measured by science's second-project milestone (sci-0d00d2, record docs/records/2026-10-26-second-project-milestone.md §6 M2): every myeloma view (multiple-myeloma, cancer, health, findings level, evidence-bound question) carries one addresses entry for the mm30 analysis-spec only because a run reaches its spec through a facet and a spec emits no relations; the health view and question carry four more (EZH2 proposition, its spec, cohort, annotation) because nothing links a spec to its target and declared inputs before a run. Stored executes/targets/spec-input edges would retire the spec entry in 5 views and, from an EZH2 anchor, the 3 spec-side health entries; closure anchors are never selected, so anchors still need naming (sci-c5872f).
- 2026-10-27T13:06:47Z (main): correction to the 2026-10-27 note from sci-0d00d2 (record §6 M2, revised): in the health clause, stored edges would retire two entries, not three: the EZH2 spec and the cohort, the spec's one declared input. The annotation is named only in the spec's method text (science sci-06c689: spec declares one input), so it stays an addresses entry unless that lands. The spec entry in the five myeloma views is unchanged.
