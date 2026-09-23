---
id: beliefs-76fe0e
title: Confinement closure refuses a .pth import of a builtin or stdlib module (coverage's a1_coverage.pth)
status: todo
priority: 1
size: s
complexity: mid
created: 2026-09-23T17:13:50Z
updated: 2026-09-23T17:13:50Z
depends: []
tags: [confinement]
agent: claude-code/claude-opus-5-5
---

ClosureBuilder.add_pth (python/src/beliefs/adapter.py) accepts a .pth import line only when each imported module is a .py file in site-packages; a builtin (sys) or a standard-library module is refused with ClosureUnsupported('<name>.pth imports 'sys', which is not a closure member'). coverage >= 7.10 installs a1_coverage.pth, whose line is 'import sys; exec(...)', and pytest-testmon depends on coverage, so any environment with testmon (science's dev group) cannot run execute_assessment_run under CONFINED_POLICY: the science run command refuses closure-unsupported (found 2026-09-23 implementing science Task 7, sci-fe0065, belief-path plan). Expected: builtins (sys.builtin_module_names) need no closure row, and stdlib imports resolve through the interpreter's own closure. The beliefs venv carries no a1_coverage.pth, which is why the kernel's confinement tests do not see it.
