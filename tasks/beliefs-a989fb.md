---
id: beliefs-a989fb
title: "Sharing door for the retired transition: World.retire under the scoped authority (science commons 1b)"
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-23T01:56:42Z
updated: 2026-10-29T12:16:52Z
depends: [beliefs-c0d952]
parent: beliefs-182296
tags: [publication]
source: beliefs-f24fe9
agent: claude-code
spec: docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md
---

Why: Science commons milestone 1b needs ledgered retirement through the sharing authority; ScopedWriter still has no retire door at main 3328315. The design dependency beliefs-c0d952 is done: revision 3 (578a014), recorded approved after review round 3, merged at 3328315. The linked spec settles the mechanism and verification; [ref:brief] preserves the original questions and approved handoff. Implement directly against that design, with no new plan unless a design gap emerges. Science's retirement/reconcile task sci-9c0bba remains dependent on this implementation.

Done:
- Add ScopedWriter.retire(root, observers, *, evidence) -> SharingLine in python/src/beliefs/session/writer.py. Follow the spec's refusal order: argument types; session lock and current/live invocation; registry authority; world configuration; existing evidence binding; admitted self-replica target; terminal status; act; ledger append. Keep the session lock through the append. Source and location remain attestations.
- For an admitted ReplicaOf itself with no terminal status, call World.retire under scoped authority and ledger transition retired, verdict retired. For an existing retired status by any actor, make no act and ledger already-retired. Re-read after a racing StatusTerminal: ledger already-retired for retired, re-raise for departed. Unknown or non-self-replica admissions refuse StatusTargetUnknown; departed refuses StatusTerminal.
- Preserve World._terminal's actor rule, single-writer deployment across processes, the eleven-field ledger schema and existing append semantics. The line's corpus identifies its unique status record. A failed append leaves the session terminal and the status intact; a successor session recovers with already-retired. Short writes may leave a torn tail; flush/fsync failures leave a complete unacknowledged line readable on disk. Both verdicts may therefore coexist for one status record.
- Keep record_sharing refusing retired and name ScopedWriter.retire in its message; update the ScopedWriter docstring inventory. No depart door, new error, ledger field, conformance cut or science policy implementation. Keep root.py the sole atoms importer; the permit inventories should pass unchanged because World._terminal remains the write-primitive caller, changing them only if their checks establish otherwise.
- Prove the full spec section 5 matrix: truthful fields and actor, no-effect refusals and ordering, same-session repeats, successor-session recovery for ledger-only write/flush/fsync faults (fsync scoped to the ledger descriptor), both race outcomes, direct-record refusal, close waiting until the line, and capability/permit inventories. Assert both in-memory and on-disk evidence per fault, and exactly one status record retaining its original actor.
- Land the section 6 documentation with the code: a dated amendment to the sharing design without rewriting its historical body, a session-work entry in the adoption ledger, and the retirement entry correction in docs/guide/open-questions.md. Science owns dependency/keep/supersession policy and its separate Task 13 interface adoption; do not change that repository here.

Where to look: The linked retirement spec sections 3-7 are the acceptance contract. Reuse _require_door_arguments, _bind_sharing_evidence, admit_publication and _record_sharing in python/src/beliefs/session/writer.py; World.registry, World.retire and World._terminal in python/src/beliefs/world/registry.py; and the unchanged append path in python/src/beliefs/session/ledger.py. Tests belong beside the certified fixtures in python/tests/test_session_sharing_doors.py; fault and lock patterns are in test_session_writer.py and test_session_routes.py. Verify test_session_ledger.py, test_world_registry.py, test_permit_boundary.py, test_permit_entry_points.py and test_capability_boundary.py as affected. Use just test-one through the project front door, then just test-fast and the required checks; create and hydrate the implementation worktree and run the full just test baseline before code changes. No suites were run during scoping.

Rating: P2 retained; medium effort for one door, its failure/concurrency matrix and three documentation updates; high complexity because irreversible registry effects, concurrent sessions and failed ledger acknowledgment interact. Direct process is justified by the approved explicit mechanism and verification, not by low risk. Keep this as one cohesive implementation task.

Original capture (historical; the approved design supersedes the corpus-id-only signature and resolves the design wait):
The session doors design (2026-10-22 §2.4, §8) ledgers bound, fetched, admitted and mounted; retired is backed by World.retire and has no door, so record_sharing refuses it. Milestone 1b's retirement (science commons design §10) needs ScopedWriter.retire(corpus_id, *, evidence) ledgering retired with the status record as evidence.

Handoff: [ref:brief] records why this needs a design first: binding the pin without the existing doors' root/observer arguments, identifying the status record in the sharing evidence, and recovering when retirement commits but the ledger append fails. Wait on beliefs-c0d952; science keeps the dependency/keep/supersession policy.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope evidence and disposition

## Notes

- 2026-10-24T09:57:06Z (main): scope: briefed; verified the missing retire door at 802286e; beliefs-c0d952 must settle evidence binding, status evidence and cross-actor retry after a ledger failure; dependency recorded; brief: docs/notes/2026-10-24-publication-session-follow-ups-brief.md
- 2026-10-29T12:07:58Z (design/publication-retirement): retirement design approved (beliefs-c0d952, docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md at 578a014): the door is ScopedWriter.retire(root, observers, *, evidence) -> SharingLine, binding evidence as admit_publication does; it reads the registry first and ledgers verdict retired (it wrote the status) or already-retired (any actor's retired status found, no second act), so a successor session recovers a retirement whose line failed; non-self-replica admission refuses StatusTargetUnknown, departed refuses StatusTerminal; no schema change, no cut; ready to scope as a direct implementation task against the design, which also lands the sharing-design amendment, the adoption-ledger line and the open-questions correction (design §6)
