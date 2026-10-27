I reviewed the frozen revision, beliefs `338c71f`, `docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md` (sha256 `8a44f249…a25f9`). My verdict is to revise it lightly. The design is sound and its claims about the code hold. One Important gap remains: the spec reverses cut-46 decision 8 without answering the reasons that decision gave. There are also four minor wording or precision points. Task beliefs-7c612b is still parked waiting on your review. Once you rule on these points, the parked design session (or whoever resumes it) records the review note, revises the spec, and starts the plan. I edited nothing and wrote no task note. Reviewers stay read-only.

**Important**

- **I1. §1 overrides decision 8 without answering its reasons.** Cut-46 decision 8 (`2026-10-02-publication-attribution-design.md:109-118`) gives three reasons for its refusal:
  - "Science §4.8 requires every adopted record's marker origin."
  - "The carrier's-own acceptance branch needs a publication's `published_from` claim."
  - "Do not … reclassify registry provenance during publication."

  The spec says it is amending decision 8 but answers none of these. Good rebuttals exist and belong in §1:
  - Science §4.8 limits the entry requirement to records held "in an *adopted* corpus rather than in a corpus it wrote". A hand-listed, markerless, relocated corpus is the installation's own under §9's 2026-10-22 amendment (Deviation 6).
  - A downstream reader of the *new* publication applies carrier's-own to that publication's marker, and that marker does carry `published_from`.
  - The declaration never touches registry provenance.
  - It opens no new laundering route. A `Fresh` holder already contributes records without entries, so copying foreign records into a fresh corpus is already possible. The new marker-present guard also stops the declaration being used on marker-bearing content.

  The successor cut will need this argument anyway, so it should be in the decision record now.

**Minor**

- **M1. §3 overstates the ordering.** It says malformed input raises "before any intent or write". That holds for the plain door, where `require_usable` writes nothing. Through `ScopedWriter.publish`, though, `_publishing()` opens the world first, and its docstring says that open "resolves recovery on the world root". That can write before preparation validates `own_corpora`. Narrow the claim to "before the publication intent or any operations-root write".
- **M2. Corpus-ID validation should reuse an existing pattern.** §3 defines "32 lowercase hexadecimal characters" from scratch. The code already has `_HEX32` (`publication.py:39`, `publish_request.py:46`). Name one to reuse and say it uses `fullmatch`.
- **M3. Y17 appears in three places.** It is at `2026-09-22-publication-design.md:37`, `2026-08-04-formal-model-and-claim-calculus-design.md:1291`, and the frozen `2026-10-02-conformance-cut-46.md:37`. The spec should say the first two are the current-facing copies to amend, so the plan neither misses the formal-model row nor touches the frozen cut.
- **M4. One §7 test case is unclear.** "markers excluded from the selected world records" doesn't say what fixture it means, for example a marker node that is in `captured_records(holder)` but not in the world's recorded index. Define it or drop it.
- **M5. The science previews gain new refusals.** Calling `acceptance_inputs(ctx)` from `publish_preview` adds its duplicate-carrier refusal and its single-write-mount unpack (`(write,) = …`) to previews that succeed today. §6 accepts this implicitly ("reuse … its duplicate-carrier refusals"). It should say outright that this is an intended behaviour change, so the science task's tests cover it.

**Checked against code, no finding**

- `_selected_attributions` (`publish.py:250`) matches §4's description of today's behaviour. That covers the order of the admission check, the v2 path (`attribution-contract-unpinned`), the v3 path (`attribution-source-invalid` / `marker-absent` from `require_publication_layout`), and forwarding of earlier entries.
- `captured_records` returns the whole captured tuple, so the marker scan in §4 step 2 works as written.
- In science, `AcceptanceInputs.own_roots` is a `frozenset[str]` of corpus IDs (`science/acceptance.py:39,95-102`). It already leaves out sharing-registry roots and roots that carry a marker, so the §6 wiring type-checks.
- Markers are staged into the staging corpus, not the write root (`_populate`). Declaring the write root's own corpus, which science always does, therefore won't trip `marker-present`.
- Under v2, a selection that is entirely own returns `None`, so the milestone's v2 writer is unblocked without repinning.
- The resume path stays untouched because the snapshot freezes the attributions.
- No TypeScript code covers publication.
- Outside `publish.py`, the only references to `publication_preview` and `_selected_attributions` are in tests.

For the review note (I haven't written it): `review: spec round 2 — verdict: revise; findings: Important 1, Minor 5; reviewer: claude-code/claude-opus-5-5`. Round 1 was the builder check by codex/gpt-6-astra, already noted on the task.

Nothing was pushed, no processes were left running, and the worktree `.worktrees/7c612b-replica-publication` and its branch `design/7c612b-replica-publication` are unchanged and unmerged. That branch is integrated after the plan and implementation are reviewed.
