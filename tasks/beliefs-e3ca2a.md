---
id: beliefs-e3ca2a
title: "python/README.md and ts/README.md: stale project name, one-module layout table and Python-primary claim"
status: doing
priority: 1
size: xs
complexity: low
process: direct
owner: docs/subsystem-readmes-e3ca2a
created: 2026-10-23T18:00:29Z
updated: 2026-10-29T11:20:43Z
started: 2026-10-29T10:54:55Z
depends: []
tags: [docs]
agent: claude-code/claude-fable-5-1
---

Found 2026-10-23 by the vdocs agent working vdocs-946c49, confirmed in the tree: python/README.md is headed "science — Python" (beliefs was extracted from science); its "What is here" table lists one module of about 60; ts/README.md says "Science is Python-primary". Both pass `ops-docs check` and `ops-check` because they are not declared subsystems (`subsystems = []` in identity.toml) and neither tool judges prose.

Do: correct the title and the project name; verify against the code which implementation is primary and what each tree holds before changing the claim, then make the orientation accurate without enumerating every module (name the main areas and where the deeper reference is). vdocs-946c49 declares python/ and ts/ as subsystems with their own identity.toml and AGENTS.md and will rewrite these READMEs into the subsystem shape; make this correction in that pass if it starts first, otherwise before it, and do not restructure beyond what that task specifies. Grep tests for reads of README.md or AGENTS.md before editing (vdocs-0f0163 found one in atoms).

## Notes

- 2026-10-23T19:33:30Z (main): ops-65a068 pilot at beliefs 6d420d6: the rubric found all three parts. Narrowed: ts/README.md's Python-primary claim is accurate (composition root is Python; ts/src holds 6 files of shared encoding), only the word 'Science' is stale. Also in these files: python/README.md:16 and :23-25 omit tools/ops-check, ops-docs check and ruff format --check from just check (AGENTS.md lists them); python/README.md:107-109 'Cuts 1-7 have landed' is stale against the ledger's cut 46; ts/README.md:35 says npm install where setup, CI and the root guides use npm ci; python/pyproject.toml:2-3 still calls science the import name though the wheel builds src/beliefs.
- 2026-10-29T10:54:55Z (main): started
  provenance: {"harness_session":"claude-code:a3f33518-e7bb-47df-bf41-74427ea3f984","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T10:55:16Z (docs/subsystem-readmes-e3ca2a): resumed
  provenance: {"harness_session":"claude-code:a3f33518-e7bb-47df-bf41-74427ea3f984","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T11:00:37Z (docs/subsystem-readmes-e3ca2a): worktree .worktrees/readme-e3ca2a on branch docs/subsystem-readmes-e3ca2a. Scope taken: both READMEs plus the pilot note's extras (check list, cuts line, npm ci, pyproject comment) and the same stale name in pyproject's description and src/beliefs/__init__.py's docstring. science.identity.v1, science.belief.v1 and contract: science stay: rule identities per adoption ledger §5 (2026-08-30). No test reads python/README.md or ts/README.md. Undefined 'shared encoding' left to beliefs-4dfe18.
- 2026-10-29T11:14:22Z (docs/subsystem-readmes-e3ca2a): review: impl round 1 — verdict: revise; findings: Important 1, Minor 5; reviewer: claude-code/claude-opus-5-5
- 2026-10-29T11:20:43Z (docs/subsystem-readmes-e3ca2a): review: impl round 2 — verdict: accept; findings: Minor 2; reviewer: claude-code/claude-opus-5-5
