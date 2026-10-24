---
id: beliefs-6d6bb6
title: "Should the publication marker carry a workspace locator (repository, commit, environment bundle)?"
status: idea
priority: 2
reviewed: true
reviewed_at: 2026-10-24T09:57:26Z
created: 2026-10-22T22:44:10Z
updated: 2026-10-24T09:57:26Z
depends: []
parent: beliefs-182296
tags: [publication]
source: sci-13050a
agent: claude-code/claude-fable-5-1
---

Open question the science commons design (science docs/specs/2026-09-30-science-commons-design.md §5 step 4, §11) asks the kernel at milestone 1a. A marker names no repository or commit; a run's recipe carries the code identity and the environment identity, which is what a reproduction is checked against. In 1a the execution inputs (repository location, commit, environment bundle location) are handed to the reader out of band; from milestone 2 the catalog entry carries them as the cataloguer's claim. Question: should the marker itself carry a workspace locator as publisher-stated content (never identity), or does the catalog's execution claim suffice? Either answer leaves the kernel's recipe validation as the only check.

## References

- brief (context, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope evidence and disposition

## Notes

- 2026-10-24T09:57:26Z (main): scope: drop; duplicates beliefs-42d201, which already asks the marker-locator question with the same commons sections 5 and 7.2 alternatives; sci-13050a reports 1a merged at c8a2cd7, meeting that older task's wake condition, but the older shelved task is related context and was not changed in this batch; brief: docs/notes/2026-10-24-publication-session-follow-ups-brief.md; proposal: drop this duplicate in favor of beliefs-42d201; reconsider the canonical task in an explicit later pass
