---
id: beliefs-918fd2
title: Design overlapping-publication reads from the brief
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: design/918fd2-overlapping-publications
created: 2026-10-09T10:48:20Z
updated: 2026-10-28T12:15:25Z
started: 2026-10-28T10:25:01Z
depends: []
parent: beliefs-a286e7
tags: [publication, design]
source: docs/notes/2026-10-09-overlapping-publications-brief.md
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-10-28-overlapping-publications-design.md
---

Write the conformance-cut spec that lets a world hold one address in several live corpora: identical content reads once, differing content refuses duplicate-location (consolidate stays the exit), uid-corruption unchanged. Settle the brief's unanswered questions: content identity (byte-equal vs uid+semantic hash), node_corpus attribution and NotPresent/Unknown with one holder absent, the retraction-discovery map, the address-map.yaml epoch format change. Supersede by citation the singular-map rule (derive.address_map), mount-citations decision 4 / cut-44 J17, and belief acceptance's singleton holder set (counts tried per holder). Absorb or sequence beliefs-354eae and beliefs-0e1acb. Global Constraints carry AGENTS.md's two cut obligations. Where to look: python/src/beliefs/world/derive.py address_map, corpus.py _one, world/read.py _address_map, world/live.py, docs/superpowers/specs/2026-10-01-mount-citations-design.md, docs/superpowers/specs/2026-10-02-belief-acceptance-design.md, science docs/specs/2026-09-30-science-commons-design.md §4.7 and §10. Also rule on two things (added 2026-10-09 from a review of the brief): (a) the world views owners check (world/view.py:382), which refuses any uid held by two corpora whatever the address map says. That is the overlapping case itself and is separate from derive.address_maps uid-corruption rule, so rule whether equal-content holders are exempt and keep it distinct from real uid corruption; live.pys copy (beliefs-0e1acb) follows. (b) Origin selection for publication attribution: _selected_attributions (publish.py:232) groups by read.corpus_of(ref), one holder, and identical bytes can arrive through carriers with different provenance. Rule which holders provenance a republication attributes, independent of holder order, and include a publish → adopt → republish arm with the holders reordered whose attribution must not move. On completion, note the ruling on beliefs-81367e.

## Notes

- 2026-10-09T11:14:09Z (main): Ride-along candidate from scoping: beliefs-cb2a39 (an N2 arm for gather's observes-loop held filter) wakes when this cut plans its arms.
- 2026-10-09T13:48:14Z (main): Scope widened 2026-10-09 after a review of the brief: the view's owners check (world/view.py:382) and publication attribution's origin selection (publish.py:232), with a reordered-holders publish → adopt → republish arm
- 2026-10-24T10:22:59Z (main): completion handoff: sci-4a3543 now waits directly on this existing design for its content-identity and holder-provenance decisions. In addition to the existing ruling note on beliefs-81367e, run tasks note sci-4a3543 --no-reviewed with the chosen equality contract, exact approved revision and any acceptance interface requirements before this design result merges. This reuses the existing question; no additional research or implementation is requested here.
- 2026-10-28T10:25:01Z (main): started
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T10:25:23Z (design/918fd2-overlapping-publications): resumed
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T10:40:39Z (design/918fd2-overlapping-publications): design: draft spec docs/superpowers/specs/2026-10-28-overlapping-publications-design.md at e57ab8c (worktree .worktrees/918fd2-overlapping-publications). Rulings: content identity = science.node-content.v1 digest of the canonical projection (registry.content_identity exposed); multi-holder AddressEntry(uid, content, holders); new address-map.yaml shape {address, content, holders, uid} with legacy {address, corpus_id, uid} admitted; owners check narrowed to uids the map does not establish; canonical holder = least present holder for labelling, holder-set readers for acceptance/attribution/audit; acceptance = union over present holders with every rejected pair still reported; attribution = own holder wins, else carriers must agree, else attribution-ambiguous; J17 narrowed to differing content; renamed-record-beside-predecessor stays uid-corruption (limitation). Absorbs beliefs-354eae; sequences beliefs-0e1acb. Builder check and a critical review dispatched before user review.
- 2026-10-28T10:55:44Z (design/918fd2-overlapping-publications): review: spec round 1 — verdict: revise; findings: Critical 1, Important 6, Minor 9; reviewer: claude-code/claude-fable-5-1
- 2026-10-28T10:55:46Z (design/918fd2-overlapping-publications): builder check (brainstorming) on spec round 1: 2 plan-changing questions (whether the published content field has a reader; what Y19's byte-identical-marker check compares) and 1 false code attribution (_population vs publication_preview); reviewer: claude-code/claude-fable-5-1
- 2026-10-28T11:14:40Z (design/918fd2-overlapping-publications): review: spec round 2 — verdict: revise; findings: Important 5, Minor 5; reviewer: claude-code/claude-fable-5-1
- 2026-10-28T11:27:42Z (design/918fd2-overlapping-publications): review: spec round 3 — verdict: revise; findings: Important 1, Minor 7; reviewer: claude-code/claude-fable-5-1
- 2026-10-28T11:30:17Z (design/918fd2-overlapping-publications): parked (waiting on user, review): User reviews the design spec docs/superpowers/specs/2026-10-28-overlapping-publications-design.md at revision 4f8413e on branch design/918fd2-overlapping-publications (worktree .worktrees/918fd2-overlapping-publications; read it with git show 4f8413e:docs/superpowers/specs/2026-10-28-overlapping-publications-design.md). On approval the agent resumes here: note the ruling on beliefs-81367e, run tasks note sci-4a3543 --no-reviewed with the equality contract (spec §4.1), the approved revision and the acceptance interface and science-side changes (§6, §8), file the §10 item 2 follow-up idea, then invoke writing-plans for the implementation plan. On corrections, revise the spec as a new revision and re-park for review.
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T11:40:44Z (design/918fd2-overlapping-publications): resumed
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T11:40:46Z (design/918fd2-overlapping-publications): review: spec round 4 — verdict: revise; findings: Important 2; reviewer: codex/gpt-6-astra
- 2026-10-28T11:59:01Z (design/918fd2-overlapping-publications): review: spec round 5 — verdict: revise; findings: Critical 1, Important 3, Minor 6; reviewer: claude-code/claude-fable-5-1
- 2026-10-28T12:15:25Z (design/918fd2-overlapping-publications): review: spec round 6 — verdict: revise; findings: Important 4, Minor 6; reviewer: claude-code/claude-fable-5-1
