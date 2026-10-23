---
id: beliefs-f24fe9
title: Session doors and ledger evidence for the publish and sharing acts (science commons 1a)
status: doing
priority: 1
size: m
complexity: high
process: planned
owner: feat/f24fe9-session-doors
created: 2026-10-22T22:44:06Z
updated: 2026-10-23T01:43:29Z
started: 2026-10-23T01:11:23Z
depends: []
tags: [publication]
source: sci-13050a
agent: claude-code/claude-fable-5-1
spec: docs/superpowers/specs/2026-10-22-session-sharing-and-publish-doors-design.md
---

Science commons milestone 1a (science docs/specs/2026-09-30-science-commons-design.md §5, §7.4, §11; command framework §3.3 and §4.4 amendments of 2026-10-01) needs four things the kernel's session surface lacks today. (1) A constructible requirement for the sharing write class: RequiredCapabilities.sharing() whose permit names the families {lifecycle, registry} and no kinds, admitted like publishes() as a kernel requirement; today every permit naming lifecycle or registry outside _PUBLICATION_PERMIT is refused. (2) Doors on ScopedWriter for the sharing acts, under the scoped authority: restore a fetched copy (restore_root) and admit a publication (admit_publication over a World opened under that authority), each ledgered as a new 'sharing' line kind carrying the framework §4.4 amendment's evidence: corpus_id, marker uid, head artifact identity, the marker's world id, pin source, location fetched from, chain verification verdict, and the transition made; LedgerReader exposes the lines per invocation. The §7.1 comparison for this class is ledger-versus-registry. (3) A door for the publish act: ScopedWriter.publish(...) and resume_publish(...) run beliefs.publish with the scoped CorpusWriter, the session's coordination resolver and a World under the scoped authority, so the marker and binding commits reach the ledger as act lines; today publish takes a raw CorpusWriter and writes under writer._operation, which no session door reaches. (4) A public publication preview: the pre-intent computation publish runs (resolved view, selection, closure_missing, derived pins, attribution entries) as one function publish itself calls, so science's publish dry run shows exactly what the act would freeze and cannot disagree with it. Science's milestone plan consumes these four names; its tasks for publish, provider-bind and adopt wait on this.

## Notes

- 2026-10-22T23:10:59Z (main): From science's 1a plan review (2026-10-22): the sharing transitions are {bound, fetched, admitted, mounted, retired} (no 'inspected': inspection uses evaluate_copy and no door); a sharing line carries corpus, marker, artifact, world, view, source, location, verdict, transition, at; the publish door ledgers only the write-root records (binding, act report), since the marker lives in the publication corpus and science's ledger-rebuilt report reads configured roots. Question: resume_publish refuses an actor other than the intent's (session:<id>), so a stranded remote attempt cannot be resumed from a later service session; is a same-world resume across sessions intended, or does the pair stay blocked?
- 2026-10-23T01:08:55Z (main): science side (sci-13050a) landed Tasks 1-3 on branch commons-1a 2026-10-22: science/sharing.py declares a structural SharingLine Protocol with fields invocation, corpus, marker, artifact, world, view, source, location, verdict, transition, at, and replay waits on LedgerReader.invocation(iid).sharing. Science's Task 4 consumes RequiredCapabilities.sharing(), ScopedWriter.record_sharing(SharingEvidence), WriterSession.invocation_sharing(iid); other names are fine, science adapts its Interfaces block.
- 2026-10-23T01:11:23Z (main): started
  provenance: {"harness_session":"claude-code:7cf9b918-1ea1-4dea-9a67-a833c86903e0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-23T01:11:55Z (feat/f24fe9-session-doors): resumed
  provenance: {"harness_session":"claude-code:7cf9b918-1ea1-4dea-9a67-a833c86903e0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-23T01:31:01Z (feat/f24fe9-session-doors): Design draft at docs/superpowers/specs/2026-10-22-session-sharing-and-publish-doors-design.md (worktree .worktrees/f24fe9-session-doors). Rulings: resume keeps the intent's-actor rule (cut 40 decision 9) and a successor-actor resume is follow-up work, so a stranded remote attempt blocks its pair until then; publication_preview raises closure-incomplete like the act rather than returning closure_missing; the sharing act doors are named restore_root and admit_publication, SharingEvidence carries the seven pin facts and the doors determine transition and verdict; the ledgered port learns the guarded commit via a GuardedCommit return; no conformance cut, as the selection amendment.
- 2026-10-23T01:43:29Z (feat/f24fe9-session-doors): Builder check (claude-code/claude-fable-5-1 subagent) on the draft: two false claims fixed (the marker's view may be subordinate, so the sharing line admits any pinned view address; execute_fulfilling_guarded has a second caller, execute_production_run, which becomes ledgered through a session port, now stated and tested); four questions settled in the spec (view form; production-run consequence accepted; profile-disagrees moves behind the attribution refusals, stated; both act doors require their family up front). Spec frozen at 2b7549d on feat/f24fe9-session-doors.
