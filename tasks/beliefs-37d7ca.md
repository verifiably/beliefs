---
id: beliefs-37d7ca
title: Stored-edge publication closure is narrower than the projection-derived closure of a findings view
status: todo
priority: 3
size: s
complexity: high
process: planned
created: 2026-10-27T12:47:50Z
updated: 2026-10-29T00:32:30Z
depends: []
tags: [publication]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
---

publish_request.closure_missing walks stored world relations only. In the milestone's findings selection the run reaches its analysis-spec only through its `run` facet and the spec reaches its target and input only through its projection, so the spec and its target are reached by the projection-derived rule (science projects design §8.1) and by no stored edge; the dry run refused on attribution before closure could report. Related: beliefs-7c98bc. Evidence: science docs/records/2026-10-26-second-project-milestone.md §5 F13, §6 M5.

## Notes

- 2026-10-27T12:47:50Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:32:30Z (main): Related scope evidence from beliefs-a02e11 (proposed duplicate, still idea): at 166f2ad kernel authority section 4.1 and both base-contract copies declare run executes analysis-spec, but stored.run_node and run_publication_node emit no executes edge; assessment_node emits only assesses/produced_by while carrying spec in its facet. The publish-act-local design section 4.1 item 5 assumes stored relations are the whole reference set. Include the selection retaining an assessment/run but omitting their spec in this task design and checks; resolve how existing facet-only records participate, rather than fixing new factories alone. Distinguish the milestone M5 observation (both closures complete for its actual selected set; attribution refused first) from this statically identified dropped-spec hole. The sci-9104fb retirement design follows facet references meanwhile. Existing scope, source, priority and planned process preserved; no implementation or new design decision in this note.
  provenance: {"harness_session":"codex:01a1850f-b2a6-7e12-b2a1-fa3427fc5442","harness_session_source":"CODEX_THREAD_ID"}
