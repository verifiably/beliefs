---
id: beliefs-1ad2c9
title: "The reproduction driver's contract documents carry a top-level `also:` key no consumer reads"
status: shelved
priority: 4
created: 2026-10-27T12:47:57Z
updated: 2026-10-29T00:31:53Z
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
