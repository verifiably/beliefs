---
id: beliefs-96a24a
title: Enforce write permits at every Beliefs write entry point
status: doing
priority: 2
size: xl
owner: design/write-permits
created: 2026-08-31T00:38:28Z
updated: 2026-09-04T09:27:12Z
depends: []
tags: [migration, writer, permits]
spec: docs/designs/2026-09-04-write-permits-design.md
---

Outcome: Every Beliefs write entry point enforces a session-bound closed permit against the actual emitted kind or act and fixes actor identity at the trusted writer boundary.

Acceptance evidence: Design the Beliefs half of the command-framework boundary; cover `CorpusWriter.add`, family adapters, run entry points, and the future publish entry point; refuse declaration mismatch and body overreach before effects; prevent requests from carrying permits or actor strings; expose the writer-session contract needed by Science; and pass direct, bypass, and end-to-end negative tests plus the complete gates.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §5.2 and §8 item 2.

Uncertainty: The cross-repository endpoint and launcher live partly in Science, so the Beliefs API boundary needs its own design and coordinated consumer tests; no permit type exists today.

## Notes

- 2026-09-04T02:44:49Z (design/write-permits): Brainstorming on branch design/write-permits; contract source is science's 2026-08-31 command-framework spec §§4-5 and plan Task 12 Consumes
