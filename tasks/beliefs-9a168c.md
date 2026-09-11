---
id: beliefs-9a168c
title: Fix CI history checkout and orphaned conformance citations
status: done
priority: 1
size: s
owner: fix/ci-history
created: 2026-09-11T15:38:09Z
updated: 2026-09-11T20:17:46Z
started: 2026-09-11T15:38:24Z
completed: 2026-09-11T20:17:46Z
depends: []
tags: [testing]
source: "https://github.com/verifiably/beliefs/actions/runs/34612482806"
---

Reproduce the five Python CI failures in a shallow clone, fetch complete Beliefs history, and replace the seven orphaned cut-17 citations with their byte-identical landed commit. Validate the affected guards in a fresh clone and run the repository gates.

## Notes

- 2026-09-11T15:38:24Z (fix/ci-history): Claimed by Codex, process recorded by task session; shallow clone reproduces all five failures, full history leaves seven references to orphan 1d8f293, and c367070 has identical cut-17 declaration bytes.
- 2026-09-11T15:40:51Z (fix/ci-history): Independent review found no issues: all edited guards are live, no pins target the edited surfaces, all live commit pins are reachable from origin/main, and frozen evidence is preserved. just check passes with zero task errors or warnings.
- 2026-09-11T15:42:30Z (fix/ci-history): Targeted regression and cut-25 freeze checks: 16 passed on Python 3.13; 16 passed on Python 3.11 in a fresh clone without the orphaned commit. Full just gate remains running.
- 2026-09-11T15:46:40Z (fix/ci-history): Claimed by Codex, pid 4140815, in .worktrees/fix-ci-history.
- 2026-09-11T20:17:46Z (fix/ci-history): Full just gate passed: 4476 Python tests in 1023.59s and 142 TypeScript tests; ruff, pyright, tsc, biome and tasks check clean with zero warnings. Log: /tmp/beliefs-ci-history-gate.log.
- 2026-09-11T20:17:46Z (fix/ci-history): Enabled complete CI history and corrected seven orphaned live citations to byte-identical reachable commits; full gate and Python 3.11/3.13 targeted checks pass.
