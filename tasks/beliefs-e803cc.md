---
id: beliefs-e803cc
title: Decide enforcement of declared relation endpoints
status: idea
priority: 3
size: m
created: 2026-09-07T17:15:37Z
updated: 2026-09-29T22:42:52Z
depends: []
parent: beliefs-d58675
tags: [domain, design]
---

Facet contracts now declare relation endpoints, but runtime endpoint enforcement remains an explicit open question. Decide where write, import and check should enforce them, how unresolved or cross-corpus targets are handled, and the refusal/finding contract before scheduling implementation. See facet-contracts design section 9 item 2 and guide open questions.

Scoping evidence (2026-09-29): corpus.py already checks assesses target kinds, composite members and supersedes same-kind, but no general contract sources/targets validator was found on the shared refusal path. Inventory write/import/relocation/audit behavior before choosing a policy for unresolved and cross-corpus targets. Handoff: docs/notes/2026-09-29-domain-contract-backlog-brief.md.

## Notes

- 2026-09-29T22:42:52Z (main): scope: briefed; general relation endpoint enforcement remains undecided; existing assesses, composes and supersedes checks require a seam inventory before design; brief: docs/notes/2026-09-29-domain-contract-backlog-brief.md
