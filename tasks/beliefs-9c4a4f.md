---
id: beliefs-9c4a4f
title: AcquisitionOutcome cannot tell an already-held dataset from an expectation mismatch
status: shelved
priority: 2
created: 2026-10-09T11:31:49Z
updated: 2026-10-09T11:32:03Z
depends: []
tags: [holdings]
source: beliefs-27d500
---

From beliefs-27d500 item 9 (cut-35 final review, deferred minor). `src/holdings/acquire.py:122-128`: `dataset is None` with `stop is None` covers both the already-held close (:230, the declaration resolves in the read view) and the expectation mismatch (:216, a pinned digest differs). The report entries differ, but the outcome type does not say which. Options: a `held: bool`, a closed outcome vocabulary, or returning the existing dataset node when held. The only caller is `SessionWriter.acquire` (`src/session/writer.py:416`), which passes it through, and science's commons `fetch` deliberately does not use `acquire` (science-commons design §5 step 4). So no consumer yet decides which shape is right.

## Notes

- 2026-10-09T11:32:03Z (main): shelved: Wake when a caller must act differently on an already-held dataset than on a pinned-digest mismatch: a science command that consumes AcquisitionOutcome, or a commons milestone that routes fetch through acquire
