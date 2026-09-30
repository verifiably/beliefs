---
id: beliefs-9ce6e4
title: Assessment eligibility and evidence gathering across mounted corpora
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-30T16:04:32Z
updated: 2026-09-30T16:04:33Z
depends: []
tags: [session]
agent: claude-code/claude-opus-5-5
---

An attended session writes one root and mounts N read corpora (cut 43). A run in the write root may observe a dataset whose record a read mount declares — a dataset's id derives from its content, so it is one world record and cannot be declared again in the write root without a duplicate-location that refuses every live selection. The run boundary accepts it (it needs only the address and a held path), but CorpusWriter._refuse_ineligible reads eligibility_refusal through the writer's own view, so the assessment over that run refuses EligibilityUnmet; gather/admission likewise read the proposition's own corpus. Needed: eligibility at the assess write, and evidence gathering and admission, resolving an observed dataset's declaration over the session's mounts. Science's coordination part 3 (sci-923d3a) keeps write-command dataset inputs in the write root and refuses a read mount's dataset by name until this lands; science's second-project milestone (sci-0d00d2) needs it to assess a working-corpus proposition over mm30 data.

## Notes

- 2026-09-30T16:04:32Z (main): concerns: beliefs-fe7149 extension — cross-corpus dataset inputs at assessment and admission, found in science's part 3 plan review round 2
