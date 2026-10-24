---
id: beliefs-d05bcf
title: "Orient the README lead and the guide's Why-it-matters openings to a newcomer: motivate against ad-hoc analysis practice, not the predecessor"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-24T18:10:13Z
updated: 2026-10-24T18:10:13Z
depends: []
tags: [docs]
source: vdocs-e4318e
agent: claude-code
---

Follow-on to the second guided tour's finding (vdocs-e4318e; atoms-dd5a5e is the atoms piece). A reader new to the project cannot say why beliefs exists from what the guides tell them: the README abstract lists the kernel's parts (typed claims, holdings, runs, verification, belief under a policy, the world index, correction, the mutation log, conformance cuts) without the problem a user would face, and five guide pages open their 'Why it matters' with 'the predecessor' or 'the redesign' (foundations, claims-and-belief, identity-world-and-change, computation-and-reproducibility, contracts-and-adoption), which only a reader who knows proto-science can place. Rewrite the identity.toml abstract and those openings against the status quo of an ad-hoc computational research effort: a folder of scripts and result tables, a conclusion nobody can trace to the exact data and code that produced it, a paper's claim treated as evidence, an analysis counted twice because two scripts read the same data, a result quietly overwritten. Keep the project's history in the designs. Leave README Install to beliefs-98c42d and python/ts READMEs to beliefs-e3ca2a.
