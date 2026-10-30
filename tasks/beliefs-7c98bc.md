---
id: beliefs-7c98bc
title: "Design stored executes, targets and spec-input relations from the measured views"
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-23T11:40:35Z
updated: 2026-10-30T13:34:33Z
depends: [beliefs-9c375c]
tags: []
agent: claude-code/claude-fable-5-1
---

Why: Science's completed second-project measurement (sci-0d00d2, science docs/records/2026-10-26-second-project-milestone.md section 6 M2, corrected at d7dd978) establishes a concrete traversal consumer. Stored executes/targets/spec-input edges would retire the mm30 spec address in five views and, from an EZH2 anchor, two health-clause entries (the spec and its one declared input cohort). The annotation is only method text and remains explicit unless sci-06c689 lands; closure anchors remain explicit too. This is enough to design the change, not approval to implement it.

Done: Produce a reviewable design for all three edges, then stop at the user's design-review gate. Use beliefs-9c375c's endpoint-enforcement matrix rather than duplicating that research. Decide the spec-input signature and input-role semantics, target resolution across mounts, and how stored edges agree with immutable spec/run projections. State the effect on existing record/content identities, contract succession and frozen conformance evidence; decide how historical records remain readable without silently rewriting them or adding a compatibility layer. Cover both run_node and run_publication_node, including production runs without a spec. Compare keeping explicit addresses with storing the three edges, using the measured savings rather than assuming they are material. A rejected change is a valid design outcome if its reason is recorded for the consumer.

Verification to design: A findings closure reaches its run's spec; a pre-run traversal reaches the target and every declared dataset input; the corrected M2 selections show precisely which explicit entries disappear and which remain. Include wrong-kind, unresolved/cross-corpus targets, projection/edge disagreement, no-spec production runs, and existing-record/identity behavior. Name affected Python/TypeScript contract consumers and acceptance inventories. Preserve both mandatory conformance-cut obligations from AGENTS.md if a cut is required. Implementation and its reviewed plan are later work, not authorized by this scoping verdict.

Where to look: python/src/beliefs/stored.py (run_node, run_publication_node, analysis_spec_node); contracts/science/CONTRACT.yaml; world/live.py and world/view.py traversal; docs/designs/2026-08-02-epistemic-kernel-design.md section 4.1; the adoption ledger and implementation roadmap; beliefs-9c375c and its domain-contract brief. At e7c3464 the two run builders still keep spec in a facet, analysis_spec_node emits no relations, and the contract declares executes/targets but no spec-input signature. Spec and plan use this repository's docs/superpowers conventions and require separate reviews. No delivery-order change is made here.

Original captured proposal (preserved):
Kernel §4.1 declares Run --executes--> AnalysisSpec and AnalysisSpec --targets--> Proposition as closed relation signatures, but run_node holds its spec in a facet and analysis_spec_node emits no relations (stored.py), so a view's closure predicate cannot walk either. Storing them as edges would let a findings view be one closure clause per assessment with no enumerated spec. Reaching a proposition from a dataset before any run additionally needs the spec's edge to each declared input dataset; the scope is all three or the pre-run benefit is not claimed. Not a prerequisite of anything; the second-project milestone's count of addresses entries per view (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §6.2, §11) is the measurement that scopes this.

## Notes

- 2026-10-14T02:15:03Z (main): shelved: Revisit when a worked findings view or the second-project measurement records costly explicit address enumeration and demonstrates the missing executes/targets/spec-input traversal it needs. Bring that consumer evidence and the current endpoint-enforcement research (beliefs-9c375c); do not claim pre-run traversal from only two edges.
- 2026-10-14T02:15:05Z (main): scope: shelved; at c1418e7 stored.py run_node and run_publication_node still store spec only in a facet and analysis_spec_node emits no relations; contracts/science/CONTRACT.yaml declares executes/targets but no spec-input signature. Keep the full three-edge proposal until a measured consumer needs it; endpoint-policy research beliefs-9c375c is related, not duplicate implementation work. The external science milestone/spec was not read in this fixed-checkout pass, so its completion and measurements remain unknown.
- 2026-10-27T12:49:57Z (main): measured by science's second-project milestone (sci-0d00d2, record docs/records/2026-10-26-second-project-milestone.md §6 M2): every myeloma view (multiple-myeloma, cancer, health, findings level, evidence-bound question) carries one addresses entry for the mm30 analysis-spec only because a run reaches its spec through a facet and a spec emits no relations; the health view and question carry four more (EZH2 proposition, its spec, cohort, annotation) because nothing links a spec to its target and declared inputs before a run. Stored executes/targets/spec-input edges would retire the spec entry in 5 views and, from an EZH2 anchor, the 3 spec-side health entries; closure anchors are never selected, so anchors still need naming (sci-c5872f).
- 2026-10-27T13:06:47Z (main): correction to the 2026-10-27 note from sci-0d00d2 (record §6 M2, revised): in the health clause, stored edges would retire two entries, not three: the EZH2 spec and the cohort, the spec's one declared input. The annotation is named only in the spec's method text (science sci-06c689: spec declares one input), so it stays an addresses entry unless that lands. The spec entry in the five myeloma views is unchanged.
- 2026-10-30T12:03:40Z (main): unshelved
- 2026-10-30T12:03:43Z (main): shelf recovery 2026-10-30: October 27 notes already carry the requested worked enumeration/traversal measurement and its correction (five spec entries and two additional health entries, not three). Restore review of whether that evidence justifies the three-edge proposal; materiality and endpoint policy remain unsettled, with no implementation approval. Full audit and recovery record retained on tasks-11f6d3.
  provenance: {"harness_session":"codex:01a18ca3-4bd6-7d61-8fb4-f4ce4eda96e2","harness_session_source":"CODEX_THREAD_ID"}
