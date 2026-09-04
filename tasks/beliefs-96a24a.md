---
id: beliefs-96a24a
title: Enforce write permits at every Beliefs write entry point
status: done
priority: 2
size: xl
owner: design/write-permits
created: 2026-08-31T00:38:28Z
updated: 2026-09-04T19:27:09Z
depends: []
tags: [migration, writer, permits]
spec: docs/designs/2026-09-04-write-permits-design.md
plan: docs/plans/2026-09-04-write-permits.md
---

Outcome: Every Beliefs write entry point enforces a session-bound closed permit against the actual emitted kind or act and fixes actor identity at the trusted writer boundary.

Acceptance evidence: Design the Beliefs half of the command-framework boundary; cover `CorpusWriter.add`, family adapters, run entry points, and the future publish entry point; refuse declaration mismatch and body overreach before effects; prevent requests from carrying permits or actor strings; expose the writer-session contract needed by Science; and pass direct, bypass, and end-to-end negative tests plus the complete gates.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §5.2 and §8 item 2.

Uncertainty: The cross-repository endpoint and launcher live partly in Science, so the Beliefs API boundary needs its own design and coordinated consumer tests; no permit type exists today.

## Notes

- 2026-09-04T02:44:49Z (design/write-permits): Brainstorming on branch design/write-permits; contract source is science's 2026-08-31 command-framework spec §§4-5 and plan Task 12 Consumes
- 2026-09-04T09:27:37Z (design/write-permits): Design banked and cut 16 frozen at 895f822 on design/write-permits; awaiting spec review, then writing-plans
- 2026-09-04T09:57:20Z (design/write-permits): Review findings 1-6 closed at e01e43f; cut 16 text amended before any code, freeze commit 895f822 stands
- 2026-09-04T10:09:19Z (design/write-permits): Second review pass closed; cut 16 and the E table frozen at ee6af71 (status line names it); awaiting approval to start writing-plans
- 2026-09-04T10:32:29Z (design/write-permits): Third review pass closed (run-only try shape); cut 16 and the E table frozen at c2f87b3
- 2026-09-04T13:16:18Z (design/write-permits): Implementation amendment §13 ruled: cut 10 cited, runner names an inventory, actor locals keep pinned arms matching, ungoverned dimension, _fork_resume as implementation; commit recoverable by git log --grep 'rule the cut 16 implementation amendment'
- 2026-09-04T13:20:01Z (design/write-permits): Execution found the plan's global staleness probe includes historical cut-6 world.py arms that do not target the current src/beliefs tree; gates allow that exact pre-existing missing set and reject every new stale arm
- 2026-09-04T13:41:50Z (design/write-permits): Renumbered the cut to 17 (§14): relocation claimed 16 at ca31a04 before the c2f87b3 freeze; merged main (cut 16) into the branch; §14 inventories the five relocation seams in corpus.py and removes actor from relocation.move/consolidate; plan renumbered and amended (Tasks 5, 11, 13, 14, 15)
- 2026-09-04T14:16:38Z (design/write-permits): claimed by codex, pid 1
- 2026-09-04T14:17:42Z (design/write-permits): reviewed Task 2 commit 751f56f: no findings; permit tests, lint, typing, actor encoding refusal and tasks check pass
- 2026-09-04T19:27:09Z (design/write-permits): Write permits landed and cut 17 discharged: Authority bound at every seam, E1-E8 closed, cut 10 cited
