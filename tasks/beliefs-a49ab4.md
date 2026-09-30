---
id: beliefs-a49ab4
title: Re-run the mm30 recreation on a cadence to catch contract drift
status: idea
priority: 2
created: 2026-09-30T10:37:37Z
updated: 2026-09-30T10:37:37Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
agent: claude-code/claude-opus-5-5
---

Why: just mm30-recreate (beliefs-9e0b42) makes 'reproduces unaided' one 53 s command ending in a verdict, but it has run once (record §25.3: a second fresh run is not shown to agree). Kernel cuts keep changing the contracts the recreation passes through; a periodic run (tasks --every, or after each discharged cut) would catch a cut that breaks the recreation, where today only the frozen fixture is read.

Open before scoping: retention. Each run leaves ~423 MB under .work/reproduction/ and the recipe deletes nothing by design; a cadence needs a rule (keep the last passing directory, remove on pass, or a scratch location on the certified volume). Also whether the trigger is time or a cut discharge.
