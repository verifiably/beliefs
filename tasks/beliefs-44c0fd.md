---
id: beliefs-44c0fd
title: "A lightweight hypothesis and evidence profile for work projects, from radiology's HY/EV pattern"
status: idea
priority: 2
created: 2026-09-16T21:45:25Z
updated: 2026-09-16T21:45:25Z
depends: []
tags: [coordination]
agent: "claude-code/claude-opus-5[1m]"
---

radiology (cainex) built, by hand and in two markdown files, the thing a work project needs from beliefs without the kernel: docs/hypotheses.md — every entry names the observation that would kill it, refuted entries stay permanently with why they died; docs/evidence.md — every entry needs a command that reproduces it; docs/open-questions.md. Its AGENTS.md makes reading them mandatory before any investigation. The next work project will build the same thing again. Proposal: a small nodes profile (kinds hypothesis, evidence, question; relations refutes/supports/answers; the kill-condition and reproducing-command fields required by the profile's check) that a project can adopt with no science stack, and that beliefs can later subsume as a lite tier. Tasks link to it by opaque ref (a task carries HY-03 in its body or source; the profile owns HY-03) — hypotheses do not become a tasks kind, because that is the proto-science path (§1 of the user/autonomy design). Open: whether this lives in beliefs, in nodes as a shipped example profile, or as its own tiny repo (nodes README: profiles live downstream). Where to look: cainex/radiology docs/hypotheses.md, docs/evidence.md, AGENTS.md §'evidence'; nodes docs/STANDARD.md profile registration. From a design conversation in ai on 2026-09-16.
