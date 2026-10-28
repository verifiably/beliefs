---
id: beliefs-a02e11
title: "The base contract declares executes (run -> analysis-spec) as a world relation, but run_node and assessment_node emit no relation to the spec"
status: idea
priority: 2
created: 2026-10-28T21:05:28Z
updated: 2026-10-28T21:05:28Z
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
