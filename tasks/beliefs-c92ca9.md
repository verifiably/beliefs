---
id: beliefs-c92ca9
title: Add the MIT LICENSE file
status: done
priority: 2
size: xs
complexity: low
process: direct
owner: chore/mit-license
created: 2026-10-09T18:46:54Z
updated: 2026-10-10T11:51:16Z
started: 2026-10-10T11:46:54Z
completed: 2026-10-10T11:51:16Z
depends: []
tags: [docs]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

The repository is public and declares MIT in python/pyproject.toml and ts/package.json but ships no LICENSE file. Add the MIT text at the root as atoms and nodes do (same copyright line), and at python/LICENSE with license-files = ["LICENSE"] in python/pyproject.toml, matching atoms and nodes. Decided by the user 2026-10-09: MIT across the verifiably repositories (verifiably/docs vdocs-910898).

## Notes

- 2026-10-10T11:46:54Z (main): started
  provenance: {"harness_session":"claude-code:a96d74a2-18cd-4799-802a-9bbe4353cae4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:46:57Z (chore/mit-license): resumed
  provenance: {"harness_session":"claude-code:a96d74a2-18cd-4799-802a-9bbe4353cae4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:51:16Z (chore/mit-license): done
  provenance: {"harness_session":"claude-code:a96d74a2-18cd-4799-802a-9bbe4353cae4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:51:16Z (chore/mit-license): MIT LICENSE at the root and python/LICENSE (atoms/nodes text), license-files in python/pyproject.toml; wheel carries License-File: LICENSE
  provenance: {"harness_session":"claude-code:a96d74a2-18cd-4799-802a-9bbe4353cae4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
