---
id: beliefs-7c98bc
title: "Store the declared executes, targets and spec-input edges as node relations"
status: shelved
priority: 2
created: 2026-09-23T11:40:35Z
updated: 2026-10-14T02:15:03Z
depends: []
tags: []
agent: claude-code/claude-fable-5-1
---

Kernel §4.1 declares Run --executes--> AnalysisSpec and AnalysisSpec --targets--> Proposition as closed relation signatures, but run_node holds its spec in a facet and analysis_spec_node emits no relations (stored.py), so a view's closure predicate cannot walk either. Storing them as edges would let a findings view be one closure clause per assessment with no enumerated spec. Reaching a proposition from a dataset before any run additionally needs the spec's edge to each declared input dataset; the scope is all three or the pre-run benefit is not claimed. Not a prerequisite of anything; the second-project milestone's count of addresses entries per view (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §6.2, §11) is the measurement that scopes this.

## Notes

- 2026-10-14T02:15:03Z (main): shelved: Revisit when a worked findings view or the second-project measurement records costly explicit address enumeration and demonstrates the missing executes/targets/spec-input traversal it needs. Bring that consumer evidence and the current endpoint-enforcement research (beliefs-9c375c); do not claim pre-run traversal from only two edges.
