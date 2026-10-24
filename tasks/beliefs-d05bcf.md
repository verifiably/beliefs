---
id: beliefs-d05bcf
title: "Orient the README lead and the guide's Why-it-matters openings to a newcomer: motivate against ad-hoc analysis practice, not the predecessor"
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: docs/d05bcf-newcomer-why
created: 2026-10-24T18:10:13Z
updated: 2026-10-24T18:39:21Z
started: 2026-10-24T18:10:45Z
depends: []
tags: [docs]
source: vdocs-e4318e
agent: claude-code
---

Follow-on to the second guided tour's finding (vdocs-e4318e; atoms-dd5a5e is the atoms piece). A reader new to the project cannot say why beliefs exists from what the guides tell them: the README abstract lists the kernel's parts (typed claims, holdings, runs, verification, belief under a policy, the world index, correction, the mutation log, conformance cuts) without the problem a user would face, and five guide pages open their 'Why it matters' with 'the predecessor' or 'the redesign' (foundations, claims-and-belief, identity-world-and-change, computation-and-reproducibility, contracts-and-adoption), which only a reader who knows proto-science can place. Rewrite the identity.toml abstract and those openings against the status quo of an ad-hoc computational research effort: a folder of scripts and result tables, a conclusion nobody can trace to the exact data and code that produced it, a paper's claim treated as evidence, an analysis counted twice because two scripts read the same data, a result quietly overwritten. Keep the project's history in the designs. Leave README Install to beliefs-98c42d and python/ts READMEs to beliefs-e3ca2a.

## Notes

- 2026-10-24T18:10:45Z (main): started
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-24T18:10:49Z (docs/d05bcf-newcomer-why): resumed
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-24T18:19:58Z (docs/d05bcf-newcomer-why): baseline 2026-10-24 (just test, worktree .worktrees/d05bcf-newcomer-why at 91052fb): python 6230 passed, 1 skipped (87.39 s); N2 46 passed (182.18 s); ts 155 passed
- 2026-10-24T18:34:38Z (docs/d05bcf-newcomer-why): review: impl round 1 — verdict: revise; findings: Important 2, Minor 4; reviewer: claude-code/claude-fable-5-1
- 2026-10-24T18:39:21Z (docs/d05bcf-newcomer-why): minor (deferred): outside the changed hunks the guide still assumes a reader who knows the predecessor at foundations.md (the predecessor's concept/construct/variable/outcome kinds), guide README (Salvage: the predecessor's pipelines) and computation-and-reproducibility.md ('Science imports a minimal normalized DAG'); a later pass over the whole guide owns them
