---
id: beliefs-a02e11
title: "The base contract declares executes (run -> analysis-spec) as a world relation, but run_node and assessment_node emit no relation to the spec"
status: dropped
priority: 2
created: 2026-10-28T21:05:28Z
updated: 2026-10-29T00:44:32Z
closed: 2026-10-29T00:44:32Z
depends: []
tags: [publication]
source: sci-9104fb
agent: claude-code/claude-fable-5-1
origin: agent
---

Found while designing science commons 1b retirement (sci-9104fb): contracts/science/CONTRACT.yaml lists executes in the world group, yet stored.run_node stores the spec only in the run facet and assessment_node names spec, run and proposition in its facet with relations assesses and produced_by only. publish_request.closure_missing walks WORLD_RELATIONS, so a selection keeping an assessment and its run while dropping their spec passes closure-incomplete although verify needs the spec to replay. Question for the kernel: should the records emit executes (and should closure_missing follow the facet references), or is the facet reference the intended carrier and the relation declaration stale? Science's 1b dependency walk follows the facet references meanwhile.

## Notes

- 2026-10-28T21:05:28Z (add): created
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:32:27Z (main): scope: drop; proposed consolidation into existing planned task beliefs-37d7ca, which already owns stored-edge versus projection-derived publication closure. At 166f2ad, stored.run_node and run_publication_node carry spec only in facets; assessment_node emits assesses/produced_by; publish_request.closure_missing walks stored WORLD_RELATIONS. Kernel authority docs/designs/2026-08-02-epistemic-kernel-design.md section 4.1 and both base-contract copies declare run executes analysis-spec, while docs/superpowers/specs/2026-09-23-publish-act-local-design.md section 4.1 item 5 assumes relations are the whole reference set. Preserve this guarantee/implementation mismatch as input to beliefs-37d7ca; do not declare executes stale or choose a new closure rule in this pass. Science milestone M5 measured both closures complete for its actual selection; the dropped-spec case here is static evidence, not a reproduced publication failure. origin: filing matched in claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90, toolu_01Mn8umHg3EUafp5daCCHEb7 returns created beliefs-a02e11 at 2026-10-28T21:05:28Z exactly. Human asked to take sci-9104fb and relayed a Codex design review about retirement; the kernel remediation question was the filing agent follow-up, not a separately stated human ask. No origin_session named; origin agent retained. proposal: drop beliefs-a02e11 as duplicate after carrying its additional executes declaration and dropped-spec case into beliefs-37d7ca; status intentionally remains idea.
  provenance: {"harness_session":"codex:01a1850f-b2a6-7e12-b2a1-fa3427fc5442","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T00:44:32Z (main): dropped
  provenance: {"harness_session":"codex:01a1850f-b2a6-7e12-b2a1-fa3427fc5442","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T00:44:32Z (main): User approved the scope drop proposal: duplicate of beliefs-37d7ca; the executes declaration mismatch and dropped-spec case are preserved in its stamped note.
  provenance: {"harness_session":"codex:01a1850f-b2a6-7e12-b2a1-fa3427fc5442","harness_session_source":"CODEX_THREAD_ID"}
