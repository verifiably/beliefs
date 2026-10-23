---
id: beliefs-79d2ce
title: Is an admitted corpus absent from a session's mounts meant to be silently uncovered by every epoch?
status: idea
priority: 2
created: 2026-10-23T17:10:08Z
updated: 2026-10-23T17:10:08Z
depends: []
tags: [publication]
source: sci-13050a
agent: claude-code
---

Found in science commons 1a: after adopt admits a publication, a session opened before the next config load does not mount it, and an epoch published from that session covers only the session's mounts. publication_preview and publish then evaluate selection completeness over that epoch, where selection.absent lists only covered corpora without a carrier (publish.py:345-347, world/view.py:341), so the admitted-but-unmounted corpus is neither covered nor absent and publish succeeds. The science commons spec had assumed publish refuses selection-incomplete naming it until reopen. Science accepted the kernel's behaviour (its publish freezes only the session's own view). Question: is a live admitted corpus outside every epoch the intended state, or should epoch capture or selection completeness consider admissions the session does not mount?
