---
id: beliefs-9f83f7
title: "Harden the session sharing doors: deferred minors from the beliefs-f24fe9 review"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-23T13:32:56Z
updated: 2026-10-23T14:24:25Z
depends: []
tags: [publication]
agent: claude-code
---

Deferred at beliefs-f24fe9's final review (docs/plans/2026-10-23-session-doors-execution-ledger.md lists them all). The ones that tighten the contract science codes against: (1) record_sharing checks permit, transition and argument types before liveness and currency, unlike the act doors, so a closed session can raise PermitExceeded or ValueError rather than SessionClosed; (2) the artifact binding accepts any same-subject carrier, so refuse an observer set holding more than one ArtifactCarrier for the evidence's corpus; (3) load_manifest in _bind_sharing_evidence may raise an untyped error on a corrupt corpus.yaml, map it as the record read now maps CAPTURE_DAMAGE; (4) _record_committed's docstring says only a crash or ledger I/O failure leaves a commit unledgered, but a readback failure after a durable commit does too (both execute_fulfilling and the guarded form); (5) routes.py LedgeredPort guarded form picks chosen[0] silently, assert exactly one fallback call. Test-depth items (TracingLock span test, same-subject wrong-digest-first carrier, pinned refusing verdict, Review Focus 4 open_world spy) are in the ledger.

## Notes

- 2026-10-23T14:01:00Z (main): Also from the final review, on ruling R16: the resume_publish door opens the session's world although the act does not use it, so a world root that refuses to open (e.g. mid-recovery) blocks a resume the act could run. Decide whether resume should skip the open (one line in writer.py _publishing plus a spec note) or keep it for symmetry with publish.
- 2026-10-23T14:24:25Z (main): Correction (codex/gpt-6.1-sol review): item (3) is wrong as written. load_manifest already raises typed ManifestMissing / ManifestMalformed (world/registry.py:500-509); mapping it to capture-damaged would only normalize the API, not fix an untyped escape.
