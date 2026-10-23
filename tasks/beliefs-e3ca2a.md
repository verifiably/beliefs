---
id: beliefs-e3ca2a
title: "python/README.md and ts/README.md: stale project name, one-module layout table and Python-primary claim"
status: todo
priority: 2
size: xs
complexity: low
process: direct
created: 2026-10-23T18:00:29Z
updated: 2026-10-23T18:00:29Z
depends: []
tags: [docs]
agent: claude-code/claude-fable-5-1
---

Found 2026-10-23 by the vdocs agent working vdocs-946c49, confirmed in the tree: python/README.md is headed "science — Python" (beliefs was extracted from science); its "What is here" table lists one module of about 60; ts/README.md says "Science is Python-primary". Both pass `ops-docs check` and `ops-check` because they are not declared subsystems (`subsystems = []` in identity.toml) and neither tool judges prose.

Do: correct the title and the project name; verify against the code which implementation is primary and what each tree holds before changing the claim, then make the orientation accurate without enumerating every module (name the main areas and where the deeper reference is). vdocs-946c49 declares python/ and ts/ as subsystems with their own identity.toml and AGENTS.md and will rewrite these READMEs into the subsystem shape; make this correction in that pass if it starts first, otherwise before it, and do not restructure beyond what that task specifies. Grep tests for reads of README.md or AGENTS.md before editing (vdocs-0f0163 found one in atoms).
