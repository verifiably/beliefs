---
id: beliefs-40e593
title: A run committed through the operation port is invisible to the root's shared writer state
status: done
priority: 1
size: s
complexity: mid
owner: fix/port-coherence
created: 2026-09-23T18:01:07Z
updated: 2026-09-23T18:19:54Z
started: 2026-09-23T18:05:54Z
completed: 2026-09-23T18:19:54Z
depends: []
tags: [command-framework]
model: "claude-opus-5-5[1m]"
agent: claude-code/claude-opus-5-5
---

corpus._root_state_for caches one _RootState (Corpus index + ReadView) per resolved root for the process. DurableOperationPort (root.py) executes its plans with its own executor, never the state's _routed_factory, and never marks the state unresolved, so after a run is minted through a port — including ScopedWriter.operation_port()/LedgeredPort, which wraps the writer's own durable_operation_port — every writer on that root keeps a stale index. Observed 2026-09-23 (science belief-path Task 8, sci-881719): in one attended session, the run command mints run:<a>; ReadView.opened_at(root).holds(run:<a>) is True; the next writer.add of the assessment is refused by eligibility_refusal ('the run ... resolves to no node in this corpus'). Every run-then-assess in one science mcp serve process fails; the reproduction driver ran each step in its own process and never saw it. Candidate fix: the port marks the root state unresolved after each commit (and after a failed one), so _SettlingHold's _settle recovers and reconstructs at the next write; or route port plans through the state's executors. A regression test: open_corpus(root) (state cached), commit a run through durable_operation_port(root), then open_corpus(root).read_view.holds(run_ref) is True and adding an assessment that assesses it succeeds.

## Notes

- 2026-09-23T18:05:54Z (fix/port-coherence): started
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T18:05:54Z (fix/port-coherence): claimed by claude-code (science belief-path session), worktree .worktrees/port-coherence
- 2026-09-23T18:19:54Z (fix/port-coherence): done
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T18:19:54Z (fix/port-coherence): the durable operation port marks the root's shared writer state unresolved before its intents and commits, so the next write hold recovers and rebuilds; a run minted through a session's port is visible to the assess that follows it
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
