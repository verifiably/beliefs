---
id: beliefs-72b6f6
title: Enforce 'a fitted model is never an observes input' with an oracle row
status: idea
priority: 2
created: 2026-10-24T01:46:18Z
updated: 2026-10-24T10:17:22Z
depends: []
parent: beliefs-9396cf
tags: []
agent: claude-code/claude-opus-5-5
---

Why: the composite-claims design states that a fitted model is only ever a reads input (docs/designs/2026-09-12-composite-claims-design.md :49-51), the one rule the 2026-09-12 models assessment said was worth writing down for generators. A search found it in prose only: no oracle row, refusal or test. Scope: decide whether the kernel can tell a fitted-model artifact from a dataset at the observes boundary (it is a content-addressed run output), and if so add the refusal and its sabotage arm; otherwise record why not.

Scope context (2026-10-24): [ref:brief] records the existing generic acquisition protections (F2/F4, introduced at 1d9d235), their tests and declared sabotage, and the remaining distinction between denying empirical standing and banning an input role. F4 explicitly admits eligibility when a valid observed dataset is present beside the invalid one. RunInput/DatasetDeclaration do not distinguish model contents, so content addressing alone cannot support a model-specific refusal. Reuse beliefs-1d023a's worked cases to recommend whether current rules plus authoring guidance suffice or a reviewed semantic extension is needed; no new refusal is authorized by this scope pass. The original capture above is preserved as the motivating question, not a claim that generic code or oracle coverage is absent.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md — existing F2/F4 protection and unresolved fitted-model role semantics
