---
id: beliefs-dbb0a4
title: Decide whether the ts parity artifact should be a published package at all
status: idea
priority: 2
created: 2026-09-07T16:01:08Z
updated: 2026-09-07T16:01:08Z
depends: []
tags: [hygiene]
---

ts/package.json is @verifiably/beliefs with private: true. The scope name is already right under the 2026-09-07 scheme, so the only open question is whether it ships.

Worth separating two things that look alike. private: true is a publish guard, not a visibility setting — removing it publishes nothing, it only permits npm publish. So flipping it now buys about one line of work at release time, while removing the guard for the couple of months before release, during which an accidental publish would be real.

The substantive question is what the package is for. The README says ts carries only the one shared encoding — formal model limitation 9, M10 being the only cross-implementation row — which reads as a parity artifact rather than a library anyone should depend on. Publishing it invites use of something that is not meant to be used, and every published package is a support commitment. nodes ships its ts because that ts is a real implementation; beliefs' is not the same kind of thing.

Recommendation on the table: keep private: true until there is a reason to ship, and decide this on what the artifact is for rather than on consistency with its siblings.
