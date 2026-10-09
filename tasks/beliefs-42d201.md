---
id: beliefs-42d201
title: Should the publication marker carry a workspace locator?
status: shelved
priority: 2
created: 2026-10-01T02:21:10Z
updated: 2026-10-09T10:48:34Z
depends: []
tags: [publication]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
---

Science's commons design §5 step 4: a marker names no repository or commit, so a reproducer obtains the workspace revision and environment bundle out of band in milestone 1 and a catalog carries execution locators as the cataloguer's claim from milestone 2. The kernel's recipe validation on the replay is the check either way. Question: should the marker itself carry locators, and if so are they identity or content?

## Notes

- 2026-10-09T10:48:33Z (main): shelved: The science commons milestone 1a plan (sci-13050a) is written: commons §11 asks this there, after 1a has run with out-of-band execution locators checked by the replay's recipe validation
- 2026-10-09T10:48:33Z (main): scope: shelved; commons §5 step 4 settles 1a (locators out of band, checked by recipe validation) and milestone 2 (catalog execution claim), so the marker question has no evidence until 1a runs; related: beliefs-631101 (replay recipe-identity check before execution)
