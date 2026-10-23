---
id: beliefs-4dfe18
title: "Guide and glossary: 'autonomy layer is not started' is stale, and the canonical value encoding has no glossary entry"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-23T18:52:19Z
updated: 2026-10-23T18:52:19Z
depends: []
tags: [docs]
agent: claude-code/claude-opus-5-5
---

Found 2026-10-23 during a guided tour of beliefs (vdocs-9ca77b). (1) docs/guide/README.md (updated 2026-09-26), Status and authority, says 'The autonomy layer is not started'; autonomy's README now lists tiers, the closing check, the sandbox and autonomy run's launch side as built. Correct the sentence against autonomy's own state authority. (2) ts/README.md and python/README.md name the 'shared encoding' / canonical value contract (science.identity.v1, computation §4.3) without defining it, and the glossary has no entry for it; a newcomer on the tour had to ask what it means. Add a glossary entry (one value, one byte spelling; type survives encoding; per-kind domain-separated digest; the only cross-implementation contract) linking computation §4.3. Leave the subsystem README rewrite to beliefs-e3ca2a / vdocs-946c49.
