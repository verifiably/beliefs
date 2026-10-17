---
id: beliefs-e803cc
title: Decide enforcement of declared relation endpoints
status: idea
priority: 3
size: m
reviewed: true
reviewed_at: 2026-10-17T20:35:55Z
created: 2026-09-07T17:15:37Z
updated: 2026-10-17T20:35:55Z
depends: [beliefs-9c375c]
parent: beliefs-d58675
tags: [domain, design]
---

Facet contracts now declare relation endpoints, but runtime endpoint enforcement remains an explicit open question. Decide where write, import and check should enforce them, how unresolved or cross-corpus targets are handled, and the refusal/finding contract before scheduling implementation. See facet-contracts design section 9 item 2 and guide open questions.

Scoping evidence (2026-09-29): corpus.py already checks assesses target kinds, composite members and supersedes same-kind, but no general contract sources/targets validator was found on the shared refusal path. Inventory write/import/relocation/audit behavior before choosing a policy for unresolved and cross-corpus targets. Handoff: docs/notes/2026-09-29-domain-contract-backlog-brief.md.

## Notes

- 2026-09-29T22:42:52Z (main): scope: briefed; general relation endpoint enforcement remains undecided; existing assesses, composes and supersedes checks require a seam inventory before design; brief: docs/notes/2026-09-29-domain-contract-backlog-brief.md
- 2026-10-17T20:35:55Z (main): scope: briefed; still waits on endpoint matrix beliefs-9c375c (open, unclaimed; also gates beliefs-595a53); recorded the missing dep edge that left it stranded; brief adds CoreferenceEndpointRefused (dc28583) as an existing typed endpoint-refusal precedent and mount citations (cf75aea, beliefs-9ce6e4) as the cross-corpus target context; checked main b9c52ee; brief: docs/notes/2026-09-29-domain-contract-backlog-brief.md
