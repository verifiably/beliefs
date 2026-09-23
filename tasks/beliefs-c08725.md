---
id: beliefs-c08725
title: Relocate the reproduced mm30 corpus from the checkout's working tree to the user's world root
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-09-23T11:40:35Z
updated: 2026-09-23T11:40:35Z
depends: []
tags: [reproduction]
agent: claude-code/claude-fable-5-1
---

The reproduced mm30 world and corpus live under .work/reproduction/mm30 in the beliefs checkout (python/tools/reproduction/paths.py). The science projects design (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §3.1) puts a research world outside every code checkout, at the user's data location; the checkout-adjacent world stays a measurement fixture. Operator task: replicate_root + restore_root into the user's world root and admit it there, never a file copy; record the recipe in the reproduction record as an addendum. Prerequisite of the second-project milestone (§9.2).
