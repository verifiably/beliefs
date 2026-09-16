---
id: beliefs-dc42bf
title: A succession route for shipped domain packs
status: idea
priority: 2
created: 2026-09-16T22:38:37Z
updated: 2026-09-16T22:38:37Z
depends: []
tags: [domain, design]
source: docs/designs/2026-09-12-composite-claims-design.md
agent: claude-code/claude-fable-5-1
---

shipped_domain_contract parses domains/biology/DOMAIN.yaml with no predecessor and check_succession refuses a document declaring a successor lineage without one, so a shipped pack cannot gain a declaration by succession (composite-claims limitation 18: the biology pack has no edges: row). The mm30 reproduction succeeds its corpus-local contract by a frozen predecessor chain (mm30-cut22.yaml, mm30-cut31.yaml in vocabulary.py); a shipped pack needs an equivalent — a shipped predecessor file per version, or a pack manifest naming the chain — decided in a design before any pack succeeds.
