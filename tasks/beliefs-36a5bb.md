---
id: beliefs-36a5bb
title: Refresh cross-repository prerequisite evidence at every roadmap re-rank
status: todo
priority: 2
size: s
complexity: low
process: direct
created: 2026-09-16T10:03:27Z
updated: 2026-10-14T02:14:41Z
depends: []
tags: [docs, roadmap]
agent: claude-code/claude-opus-5
---

Why: The roadmap's existing discharge and method-amendment re-ranks do not explicitly refresh cross-repository prerequisite evidence. The l13-preimage correction at bcb3661 fixed one ranking; cut 37 later closed that boundary (40a390d), but the process gap remains at c1418e7.

Done:
- Add an explicit prerequisite-refresh step to the existing re-ranking procedure in docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md §6 and docs/guide/README.md, and align the roadmap's current-facing method text.
- At each re-rank, read every tier-2 prerequisite's owning task and linked landing/certification evidence. Record what was checked and its revision in the new results record (or method-amendment evidence). A closed task alone does not prove the seam or certification landed. Unavailable evidence is an explicit unknown, never an assumed blocker or completion.
- Recompute tiers from that evidence in the same change. Check the current persistence-cut prerequisite, atoms-f5779f, when executing this task; its current external status was not verified in this local scoping pass.
- Preserve frozen results and historical evidence. Retain the existing two triggers and Ranked at semantics; no watcher, cross-repository automation, third trigger or test that merely asserts tier judgment.

Verification: Run just test-one tests/test_designs_corpus.py tests/test_check_guide.py, then just test-fast before committing and the required documentation checks. Review the procedure against the historical l13-preimage miss and the current persistence-cut row.

Where to look: docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md §§4, 6; docs/plans/2026-08-29-implementation-roadmap.md introduction and Tier 2; docs/guide/README.md, Maintaining the guide; python/tests/test_designs_corpus.py::test_the_roadmap_and_ledger_name_the_same_boundaries; bcb3661 and 40a390d.

## Original capture

Found 2026-09-16: atoms-38887b (the writable-source read_preimage seam) closed 2026-09-11, which by the method's own tier rule moves l13-preimage from tier 2 to tier 1 — yet the re-ranks at cuts 27, 28, 29, 30 and 31 each carried the tier-2 row with 'atoms' deferred-obligation ledger carries no such entry today'. The method's two triggers (a cut's discharge; a method amendment) recompute tier membership only from this repository's cuts, so a cross-repo seam landing is never re-read. Options: make the discharge re-rank read every tier-2 prerequisite's task status (tasks show <cross-repo id>) as a checklist step in the results-record template; or add a third trigger. Corrected by hand in the roadmap on 2026-09-16.

## Notes

- 2026-10-14T02:14:41Z (main): scope: scoped; P2/s/low/direct; refresh tier-2 task and landing evidence within the existing two re-rank triggers, with document and guard checks; bcb3661 corrected l13-preimage and 40a390d discharged it, but method §6 and guide still omit the refresh at c1418e7; original capture preserved
