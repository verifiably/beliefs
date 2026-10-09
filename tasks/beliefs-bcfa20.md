---
id: beliefs-bcfa20
title: "Map stack-less hypothesis, evidence and question records onto coordination v3's kinds"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-09T11:37:42Z
updated: 2026-10-09T11:37:42Z
depends: []
parent: beliefs-614364
tags: [coordination]
source: docs/notes/2026-10-09-coordination-outside-the-kernel-brief.md
---

Question: Which fields that stack-less projects require of hypothesis, evidence and question records (a kill condition on each hypothesis, refuted entries kept with the reason, a reproducing command on each evidence entry, an answer link on each question) have no home in coordination contract v3's kinds, and could a nodes profile require them through its check?
Where to start: python/src/beliefs/contracts/coordination/v3/CONTRACT.yaml (the hypothesis, question and note kinds); science docs/specs/2026-09-24-coordination-command-set-design.md §3 (the hypothesis and question commands); the nodes docs/STANDARD.md profile registration and check sections; the structure (not the content) of the hand-kept hypotheses, evidence and open-questions files beliefs-44c0fd names, and their AGENTS.md reading rule.
Bound: A read-only field-by-field mapping. Write no profile, contract amendment or science command. This repository is public, so record field names and required properties only, never entries copied from a work project.
Expected result: A table of field → v3 home (or none) → whether a nodes profile check could require it, plus a one-line recommendation (v3 covers it; v3 needs a named amendment; or only a separate profile fits), recorded on this task and in docs/notes/2026-10-09-coordination-outside-the-kernel-brief.md §5.
Ideas it wakes: On completion, run tasks note on beliefs-44c0fd with the finding, in the same commit as this result.
