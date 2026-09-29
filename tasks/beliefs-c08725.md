---
id: beliefs-c08725
title: Relocate the reproduced mm30 corpus from the checkout's working tree to the user's world root
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: main
created: 2026-09-23T11:40:35Z
updated: 2026-09-29T08:29:31Z
started: 2026-09-29T08:29:31Z
depends: []
tags: [reproduction]
agent: claude-code/claude-fable-5-1
---

The reproduced mm30 world and corpus live under .work/reproduction/mm30 in the beliefs checkout (python/tools/reproduction/paths.py). The science projects design (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §3.1) puts a research world outside every code checkout, at the user's data location; the checkout-adjacent world stays a measurement fixture. Operator task: replicate_root + restore_root into the user's world root and admit it there, never a file copy; record the recipe in the reproduction record as an addendum. Prerequisite of the second-project milestone (§9.2).

## Notes

- 2026-09-29T08:29:31Z (main): started
  provenance: {"harness_session":"claude-code:eda6e403-572f-4fc2-9be3-c14e9c523159","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-29T08:29:31Z (main): claimed by claude-code (opus-5-5), pid 3905083; target: SCIENCE_CONFIG=/mnt/ssd/science/science.toml (set in dotfiles shell/local/titan.env.zsh, host-local, Dropbox-only), world under /mnt/ssd/science/worlds/<id>/ on the checkout volume
