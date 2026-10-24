---
id: beliefs-72b6f6
title: Enforce 'a fitted model is never an observes input' with an oracle row
status: idea
priority: 2
created: 2026-10-24T01:46:18Z
updated: 2026-10-24T01:46:18Z
depends: []
tags: []
agent: claude-code/claude-opus-5-5
---

Why: the composite-claims design states that a fitted model is only ever a reads input (docs/designs/2026-09-12-composite-claims-design.md :49-51), the one rule the 2026-09-12 models assessment said was worth writing down for generators. A search found it in prose only: no oracle row, refusal or test. Scope: decide whether the kernel can tell a fitted-model artifact from a dataset at the observes boundary (it is a content-addressed run output), and if so add the refusal and its sabotage arm; otherwise record why not.
