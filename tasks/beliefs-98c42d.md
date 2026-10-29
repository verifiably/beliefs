---
id: beliefs-98c42d
title: README Install omits the sibling atoms and nodes checkouts; AGENTS.md Gates carries dated status prose and restated global rules
status: done
priority: 1
size: xs
complexity: low
process: direct
owner: docs/readme-install-agents-gates
created: 2026-10-23T19:33:27Z
updated: 2026-10-29T10:49:42Z
started: 2026-10-29T10:40:34Z
completed: 2026-10-29T10:49:42Z
closed: 2026-10-29T10:49:42Z
depends: []
tags: [docs]
source: ops-65a068
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

Found by the ops documentation-review pilot (ops-65a068) at beliefs 6d420d6.

- README.md Install (lines 19-25) says only `cd python && uv sync --frozen`, but python/pyproject.toml's [tool.uv.sources] takes verifiably-atoms and verifiably-nodes from ../../atoms/python and ../../nodes/python (ci.yml checks both out side by side): a lone clone cannot install. State the sibling checkouts until those packages are published.
- AGENTS.md Gates: 'just check has passed on main since 2026-09-07; it was red until beliefs-97eb6d and beliefs-0e0c9c' and the dated 2026-09-26/09-30 timing medians are status prose; keep the 18 min and 2.4x figures that justify the rule.
- AGENTS.md Gates bullet 3 restates the global Tests rule (test-one, test-fast before committing, when to run just test) and bullet 2 the hydration rule; keep only the project's recipes and their specifics.

Done when those three land and `just check` passes.

## Notes

- 2026-10-29T10:40:34Z (main): started
  provenance: {"harness_session":"claude-code:6f16ea82-da31-4ae3-898f-a065fd8ecf3a","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T10:40:57Z (docs/readme-install-agents-gates): resumed
  provenance: {"harness_session":"claude-code:6f16ea82-da31-4ae3-898f-a065fd8ecf3a","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T10:49:42Z (docs/readme-install-agents-gates): done
  provenance: {"harness_session":"claude-code:6f16ea82-da31-4ae3-898f-a065fd8ecf3a","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T10:49:42Z (docs/readme-install-agents-gates): README Install names the atoms/nodes sibling checkouts; AGENTS.md Gates drops the dated check/timing status and the restated global test and hydration rules, keeping the 18 min and 2.4x figures; just check and test-fast pass
  provenance: {"harness_session":"claude-code:6f16ea82-da31-4ae3-898f-a065fd8ecf3a","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
