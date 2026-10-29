---
id: beliefs-1ad2c9
title: "The reproduction driver's contract documents carry a top-level `also:` key no consumer reads"
status: shelved
priority: 4
created: 2026-10-27T12:47:57Z
updated: 2026-10-29T00:31:56Z
depends: []
tags: [reproduction]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
---

python/tools/reproduction/mm30-cut22.yaml, mm30-cut31.yaml and mm30.yaml carry `also: [biology]`, which science's loader refuses (composed domains come from its config); the milestone's genesis copies drop the line. Informational. Evidence: science docs/records/2026-10-26-second-project-milestone.md §1.1 C3, §5 F14.

## Notes

- 2026-10-27T12:47:57Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:31:53Z (main): shelved: Wake when the mm30 reproduction contract/export path is next revised, or a consumer needs to load the raw driver documents without the existing science genesis normalization. Preserve the cut-22 and cut-31 predecessor bytes; prefer an explicit export boundary over editing historical inputs.
- 2026-10-29T00:31:56Z (main): scope: shelved; verified at 166f2ad: all three reproduction YAML files still carry also, vocabulary.py selects contract/plan and composes biology explicitly, and its predecessor comments require cut-22/cut-31 byte preservation. Science contracts.py rejects top-level keys other than contract/plan; sci-0d00d2 record C3 confirms stripped copies retain the pinned contract identity. Informational cleanup has a working normalization route; wake on reproduction/export work or a raw-document consumer need, not a standalone rewrite of historical inputs. Original body and source preserved; no brief needed. origin: filing inferred in claude-code:8b479072-91d3-4b9c-b77c-d178525b6574: toolu_018ZMvL1jgvaD8YJmuQAy9R9 writes file_findings.py with the F14 tasks-add arguments, toolu_01HEYqVSaqski2EJTyZsTj5R executes it at 2026-10-27T12:46:52Z and returns F14 beliefs-1ad2c9 created (filtered result, no raw per-task at). Human ask was to execute sci-0d00d2 inline; the F14 cleanup observation was agent-added. No origin_session named; origin agent retained.
  provenance: {"harness_session":"codex:01a1850f-b2a6-7e12-b2a1-fa3427fc5442","harness_session_source":"CODEX_THREAD_ID"}
