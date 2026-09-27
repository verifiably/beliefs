# Conformance cut 42 — the publish act, remote

**Status:** discharged 2026-09-27 on the certified volume; results: `../plans/2026-09-27-conformance-cut-42-results.md`
**Design:** `../superpowers/specs/2026-09-26-publish-act-remote-design.md`, approved 2026-09-27 at `e353c2d` after three user reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-27-publish-act-remote.md`.
**Numbered after** cut 41 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 42 or above at freeze.

## 1. What this cut is

The remote half of the publish act transports an exported corpus and sibling artifact through an injected seam, verifies the remote listing, and resumes from a durable transport mark. It records abandoned or damaged attempts as orphans, refuses a conflicting unfinished attempt, and lets a recipient restore, admit, and read the publication tip. Y11–Y16 are open at freeze and close on discharge.

## 2. The boundary


| File | Responsibility |
| --- | --- |
| `python/src/beliefs/transport.py` (new), `python/tests/transport_fake.py` (new), `python/tests/test_transport.py` (new) | the seam, the naming, the listings, the fake (Task 1) |
| `python/src/beliefs/report.py`, `python/src/beliefs/stored.py`, `python/tests/test_report.py` | the transport entry, its outcomes, the remote lifecycle (Task 2) |
| `python/src/beliefs/publication_doors.py`, `python/src/beliefs/errors.py`, `python/tests/test_publication_doors.py` | `PreBinding.orphan`, the transport rule, the fold, `unfinished_attempts`, `PublicationRefused(tokens=)` (Task 3) |
| `python/src/beliefs/publish_request.py`, `python/src/beliefs/publish.py` (one line), `python/tests/test_publish_request.py` | the mark codec, the remote `require_usable` (Task 4) |
| `python/src/beliefs/publish.py`, `python/src/beliefs/root.py`, `python/tests/test_publish.py` | the remote act and `evaluate_copy` (Task 5) |
| `python/src/beliefs/publication_arrival.py`, `python/src/beliefs/errors.py`, `python/tests/test_publication_arrival.py` | `require_publication_layout`, `publication_tip`, `PublicationReadingRefused` (Task 6) |
| `python/tests/acceptance/test_publish_remote_acceptance.py` (new) | the fourteen units (Task 7) |
| `python/tests/n2_arms_cut42.py`, `python/tests/acceptance/n2_arms_cut42.py`, `python/tests/acceptance/test_n2_cut42.py`, `python/tools/cut42_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, recent-cut row (Task 8) |

Frozen declarations and cut bodies through cut 41 remain byte-exact.

## 3. Selection

The six guarantee rows are quoted byte-exact from the design's §10:

```markdown
| **Y11** | a remote reveal is verified by the act, not the seam: the remote's enumeration of the publication's whole namespace must equal the local listing of every export-root file and the sibling, by name and SHA-256; a missing, extra or altered file is `transport-incomplete` (`listing-mismatch`), reported, terminal; a remote destination without a transport, or a local one with one, refuses before anything is written |
| **Y12** | the transport mark is written create-only after the export root validates and before the first `push`; once it exists a retry resumes at step 7 from the mark and never re-runs steps 1–6; a mark that fails to decode, or disagrees with its intent, the export root's manifest and chain, the sibling's identity or the export's marker, fails closed with nothing written |
| **Y13** | a transport the seam abandons, whose listing disagrees, or whose export root fails its evaluation against its own chain and sibling before `push` (a selected record missing or altered after the mark), closes the attempt with a report carrying `(corpus_id, marker)`; the fold reads it as a standing orphan that retires nothing, so the next publication's marker supersedes it and every orphan its intent named |
| **Y14** | a publish refuses `publish-unfinished` before its intent, writing nothing, while an `unfinished` attempt for the same `(view, destination)` has a transport mark; an unfinished attempt without a mark never blocks; once the blocking attempt is resumed to a close, the publish proceeds and its marker supersedes the resumed one |
| **Y15** | a crash at any remote step resumes to exactly one binding and one report whose entries run staging, export, reveal, transport, binding; a remote step-8 refusal carries `remotely_revealed: true` and is an orphan; step 9 keeps the export root, the mark, the request and the snapshot |
| **Y16** | a recipient admits a remote publication from a raw copy through `restore_root` against the transported artifact and `admit_publication`, and a copy missing any file never validates; `publication_tip` reads each held root alone, so publications sharing selected records are read side by side; it refuses a held root with a record it cannot read or decode (`capture-damaged`) and a corpus whose layout `admit_publication` would refuse, answers the one standing marker, `divergent-publication` for sibling markers, and the one tip again once a marker superseding both arrives |
```

The fourteen units and their assertion text are the design's §11.2:

| unit | row | assertion |
|---|---|---|
| Y11-a | Y11 | two cases, each on a fresh attempt: the fake alters one export-root file's bytes after `push`, and the fake adds an extra file under `<corpus_id>/` after `push`; each → `transport-incomplete` (`listing-mismatch`), closed, no binding, the report's entries staging, export, reveal, transport |
| Y12-a | Y12 | a crash inside `_push` after one file is uploaded leaves `transport.v1` on disk, and a second publish of the view refuses `publish-unfinished` naming the token |
| Y12-b | Y12 | after the mark, an extra record raw-written into staging, then a crash in `_verify`; `resume_publish` answers `Published` with staging untouched by the resume (no `_stage_record` call, no `staging-corrupt`) |
| Y12-c | Y12 | two cases, each on a fresh attempt crashed in `_push`: the mark rewritten with another `corpus_id`, and the mark rewritten with another `artifact`; each resume → `PublishUnresolved("transport-mark-corrupt")`, the chain tip and the operations root byte-unchanged |
| Y13-a | Y13 | the fake abandons → `PublishRefused("transport-incomplete")`; a second publish binds, and its marker's `supersedes_markers` holds the abandoned attempt's pair |
| Y13-b | Y13 | attempt O abandons, which makes O a standing orphan; attempt T, whose intent's `marker_tips` names O, then abandons too; publish N then binds, and N's `supersedes_markers` holds both O and T |
| Y13-c | Y13 | two cases, each on a fresh attempt crashed in `_push`: one selected record deleted from the serviceable export root, and one selected record's bytes altered (the test lifts permissions to do it). Each resume → `PublishRefused("transport-incomplete")` with reason `export-damaged`, the fake's `push` not called by the resume, the report's entries staging, export, reveal, transport; the next publish binds and its `supersedes_markers` holds the damaged attempt's pair |
| Y14-a | Y14 | the Ruling 12 case: `_bind` monkeypatched to raise before any effect after a verified transport → intent `unfinished`; a new publish refuses `publish-unfinished` with nothing written; `resume_publish` → `Published`; the new publish then binds and supersedes it |
| Y14-b | Y14 | an attempt crashed in `_initialize` (a request, no mark) does not block a second publish, which binds |
| Y15-a | Y15 | for each remote boundary — `_mark`, `_push`, `_verify`, `_bind` — crash then resume → `Published`, one binding revision, one report whose entries are staging, export, reveal, transport, binding; step 9 leaves the export root serviceable and the mark in place |
| Y15-b | Y15 | the one reachable `predecessor-not-standing`, cut 39's W17-p-a race driven through the act. First, a remote publish P binds, so A has a predecessor. A's `port` wrapper then runs a whole remote publish B, superseding P, inside `append_intent`, after A's tip read (`binding_tips == (P,)`) and before A's intent. A transports, then its step 8 refuses `predecessor-not-standing` with `tips == (B,)` and `remotely_revealed: true`. The next publish's `marker_tips` names A's pair. Without P, A's empty `binding_tips` is a subset of any standing set, and the guard answers `evidence-refused` (`tips-disagree`) instead |
| Y16-a | Y16 | a recipient materializes the fake remote, restores against the transported artifact, admits through `admit_publication`, and `publication_tip` answers `CurrentPublication`; the same copy missing one file restores to a non-`validated` verdict and `admit_publication` refuses |
| Y16-b | Y16 | sibling bindings: attempt A crashed in `_initialize`, publish B bound, then A resumed and bound at its own intent position. A and B select the same records. A recipient admits both, and an epoch over its world refuses `duplicate-location` (the premise of decision 9); `publication_tip` over both held roots reads `DivergentPublication` naming both; after the next publication C, whose binding tips are both, arrives → `CurrentPublication(C)` |
| Y16-c | Y16 | a held publication root gains an unreadable extra record file after admission (the reviewer's probe): `publication_tip` refuses `capture-damaged` naming its corpus, and `admit_publication` of the same bytes into a fresh world refuses |

## 4. Accounting

The cut is frozen before its code exists; executable arms run at Task 8. Task 7 is planned to collect 31 acceptance cases (24 from the fourteen units plus seven extra cases).

**14 arms, 14 declaration units**, six rows; Y11–Y16 open and close; recent-cut row `(14, 14, 6)`; Task 7 passes 31; 204 of 237 → 210 of 237.

## 5. N2 and acceptance obligations

| unit | sabotage |
|---|---|
| Y11-a | the comparison checks only the names the act uploaded against their digests, so a digest change is caught but the extra file is not (the fake's listing restricted to the uploaded names) |
| Y12-a | the mark is written after `push` returns instead of before it |
| Y12-b | a resume with a mark re-runs the request path instead of starting at step 7 |
| Y12-c | the resume checks the mark against its intent only, not against the export root and the sibling |
| Y13-a | `_reports_at` yields `PreBinding(orphan=None)` for `transport-incomplete` |
| Y13-b | a `PreBinding` orphan also retires its intent's `marker_tips` |
| Y13-c | step 7 skips the export evaluation, so the resume uploads the damaged export and binds |
| Y14-a | the `publish-unfinished` check is skipped |
| Y14-b | the check blocks on any unfinished attempt, marked or not |
| Y15-a | step 8's report omits the transport entry |
| Y15-b | the act passes `remotely_revealed=False` for a remote destination |
| Y16-a | `transport_files` omits the root's chain files, so the transport still verifies against its own listing but the recipient's copy cannot validate |
| Y16-b | `publication_tip` returns the lowest tip instead of `DivergentPublication` |
| Y16-c | the reading reads each root through a report-mode capture, so an unreadable file is dropped and the layout check passes |

Engine facts pinned by `test_publish_remote_engine.py`: EXPORT_LAYOUT, CHAIN_HEAD_SERVICEABLE, EVALUATE_INTACT, EVALUATE_DELETED, EVALUATE_ALTERED, EVALUATE_WRITES_NOTHING, and DAMAGE_WRITABLE all hold. CHAIN_DIR is `.#~chain`. EVALUATE_UNREADABLE raises `beliefs.errors.LogEvidenceRefused`; EVALUATE_UNDECODABLE answers `refuted`; CHAIN_HEAD_DAMAGED raises `atoms.chain.errors.ChainStateInvalid`; CHAIN_HEAD_DELETED and CHAIN_HEAD_UNREADABLE raise `atoms.core.errors.PreconditionRefused`; EVALUATE_CHAIN_DELETED answers `refuted`.

`PREFIX_RUNNERS = ("cut41_acceptance.py",)` and `PHASE_MODULES = ("test_publish_remote_acceptance.py", "test_n2_cut42.py")`.

## 6. Second reader

Check that every arm publishes under exactly `publishes()`; Y12-b counts `_stage_record` calls on resume; Y13-c damages a selected record of the serviceable export and counts `push` calls; Y15-b's P binds before A opens; and Y16-b asserts the epoch refusal before reading the tip.

## 7. Limitations

1. **Crashes are exceptions at step boundaries.** They are not kills inside
   `push`, which are `persistence-cut`'s along with engine-stage kills. Y12-a
   models a partial upload by the fake's own fault, not by a kill.
2. **The operations root is one per written root.** Step 0's
   `publish-unfinished` check and every resume read marks under the
   operations root the caller supplies. An attempt run under another
   operations root is invisible to them. This is the launcher's obligation,
   like the single-writer obligation (roadmap row 4), and the kernel cannot
   check it.
3. **In-process concurrent attempts can race the check** (§4.1). The window
   is repaired by the next publish, never left permanent.
4. **A remote's own retention is not the kernel's.** Verification reads the
   remote once. A remote that later loses or alters the files is caught by
   each recipient's `restore_root`, not by the publisher.
5. **Transport is reinvoked whole.** `push` re-sends every file on a retry.
   Resuming a partial upload is the seam's optimization, not the act's.
