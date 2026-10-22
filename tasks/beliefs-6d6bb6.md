---
id: beliefs-6d6bb6
title: "Should the publication marker carry a workspace locator (repository, commit, environment bundle)?"
status: idea
priority: 2
created: 2026-10-22T22:44:10Z
updated: 2026-10-22T22:44:10Z
depends: []
tags: [publication]
source: sci-13050a
agent: claude-code/claude-fable-5-1
---

Open question the science commons design (science docs/specs/2026-09-30-science-commons-design.md §5 step 4, §11) asks the kernel at milestone 1a. A marker names no repository or commit; a run's recipe carries the code identity and the environment identity, which is what a reproduction is checked against. In 1a the execution inputs (repository location, commit, environment bundle location) are handed to the reader out of band; from milestone 2 the catalog entry carries them as the cataloguer's claim. Question: should the marker itself carry a workspace locator as publisher-stated content (never identity), or does the catalog's execution claim suffice? Either answer leaves the kernel's recipe validation as the only check.
