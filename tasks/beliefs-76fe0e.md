---
id: beliefs-76fe0e
title: Confinement closure refuses a .pth import of a builtin or stdlib module (coverage's a1_coverage.pth)
status: done
priority: 1
size: s
complexity: mid
owner: fix/pth-builtins
created: 2026-09-23T17:13:50Z
updated: 2026-09-23T17:50:04Z
started: 2026-09-23T17:39:21Z
completed: 2026-09-23T17:50:04Z
depends: []
tags: [confinement]
model: "claude-opus-5-5[1m]"
agent: claude-code/claude-opus-5-5
---

ClosureBuilder.add_pth (python/src/beliefs/adapter.py) accepts a .pth import line only when each imported module is a .py file in site-packages; a builtin (sys) or a standard-library module is refused with ClosureUnsupported('<name>.pth imports 'sys', which is not a closure member'). coverage >= 7.10 installs a1_coverage.pth, whose line is 'import sys; exec(...)', and pytest-testmon depends on coverage, so any environment with testmon (science's dev group) cannot run execute_assessment_run under CONFINED_POLICY: the science run command refuses closure-unsupported (found 2026-09-23 implementing science Task 7, sci-fe0065, belief-path plan). Expected: builtins (sys.builtin_module_names) need no closure row, and stdlib imports resolve through the interpreter's own closure. The beliefs venv carries no a1_coverage.pth, which is why the kernel's confinement tests do not see it.

## Notes

- 2026-09-23T17:39:21Z (fix/pth-builtins): started
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T17:39:21Z (fix/pth-builtins): claimed by claude-code (science belief-path session), worktree .worktrees/pth-builtins
- 2026-09-23T17:50:04Z (fix/pth-builtins): done
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T17:50:04Z (fix/pth-builtins): add_pth accepts a .pth import of a module compiled into the interpreter or a stdlib module the closure already carries; coverage's a1_coverage.pth no longer makes an environment unconfinable
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
