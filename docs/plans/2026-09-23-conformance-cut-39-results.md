# Conformance cut 39 — results

**Cut:** `../designs/2026-09-23-conformance-cut-39.md`
**Freeze:** `8e81e1ac72ac9838bc863d07b93e2cdbfa31ad8c`; SHA-256 `b92c7a2052e97d2ccc75fbb7fbb07b5d53d90ecc99904be666c61d9dd9dd7a43` (the first freeze, `15fd610`, moved before review cleared — §3.1)
**Declaration:** `python/tests/n2_arms_cut39.py`; SHA-256 `9a0d3036b8c6353772f57c7dcb193b0f4215225cc4bccbe2f3d36b28023854e8`
**Subject:** publication records — the coordination contract's v2 amendment, the `publication` and `publication-binding` kinds and their deterministic records, the `publish` operation kind and act family, the evidence-bearing publish intent, and the intent-position judgment over the chain's inventory
**Design:** `../superpowers/specs/2026-09-22-publication-records-design.md`
**Plan:** `../superpowers/plans/2026-09-22-publication-records.md`
**Discharged:** 2026-09-23 on `design/publish`, through `4cb09d8`; reproduction recorded at `101cdd2`
**Runner:** `python/tools/cut39_acceptance.py`

## 1. What ran

The certified runner ran from the worktree `publish`'s `python/`, reached by
its canonical path rather than through the `.worktrees` symlink, at head
`4cb09d8`, with every `SCIENCE_CUT*_ROOT` and `SCIENCE_MM30_ROOT` export
spelled through the resolved main checkout, so its cut roots sat on the main
checkout's certified volume (§7). Cut 39 chains **cut 38's** runner
(`PREFIX_RUNNERS = ("cut38_acceptance.py",)`), which retains the complete
live prefix back through cut 17's nineteen phases; cut 38's own chained
summary appears in the log ahead of cut 39's, confirming the prefix ran.
Cut 8 remains cited-not-run.

The runner's two final lines, verbatim from the main checkout's
`.work/acceptance/cut39-runner.log`, are:

```text
declared arms: 14 (= 13 declaration units; 5 guarantee rows)
guarantee rows exercised: 5 (5 newly closed: W17, Y1, Y2, Y3, Y4)
```

Its own phases were:

```text
[cut39 phase 2/3] test_publication_records_acceptance.py
16 passed in 39.95s
[cut39 phase 3/3] test_n2_cut39.py
10 passed in 22.06s
```

The runner's exit status was not literally captured — the reaping wrapper
`detached.sh` still does not persist its wrapped command's `$?` (cut 38
results §7). Exit 0 is established from the log instead: the rows-exercised
line above is printed only inside the runner's `if result == 0:` branch, all
three phases completed, and the full log has zero `FAILED`, `ERROR` or
`Traceback` matches across sixty-two clean pytest summaries. The wrapper
exited and its process group is gone.

Every prefix phase passed. Every one of the thirteen live checks resolved
and passed without sabotage; all fourteen mutations scored **sound**. No
unit was stale, vacuous, mixed or uncollected — `test_n2_cut39.py`'s ten
tests are where those verdicts are asserted, and they passed. W17-p-e homes
two arms (W17-p-e and W17-p-e2); every other unit homes one. Each check below
is in `python/tests/acceptance/test_publication_records_acceptance.py`:

| declaration unit | check | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|
| W17-p-a | `test_w17_p_a_a_second_writer_between_tip_read_and_append_is_refused_durably` | resolved | sound | W17 closes |
| W17-p-b | `test_w17_p_b_…_lawful_sibling_durably` | resolved | sound | W17 closes |
| W17-p-c | `test_w17_p_c_…_not_present_durably` | resolved | sound | W17 closes |
| W17-p-d | `test_w17_p_d_…_nor_tips_durably` | resolved | sound | W17 closes |
| W17-p-e (e, e2) | `test_w17_p_e_the_chain_not_the_directory_says_which_revisions_exist_durably` | resolved | sound, sound | W17 closes |
| W17-p-f | `test_w17_p_f_…_present_once_durably` | resolved | sound | W17 closes |
| Y1-a | `test_y1_a_version_and_door_refusals_durably` | resolved | sound | Y1 closes |
| Y1-b | `test_y1_b_…_inert_to_the_world_and_to_belief_durably` | resolved | sound | Y1 closes |
| Y2-a | `test_y2_a_…_decoded_intent_durably` | resolved | sound | Y2 closes |
| Y3-a | `test_y3_a_…_by_their_domain_durably` | resolved | sound | Y3 closes |
| Y4-a | `test_y4_a_…_no_binding_on_refusal_durably` | resolved | sound | Y4 closes |
| Y4-b | `test_y4_b_…_retires_it_durably` | resolved | sound | Y4 closes |
| Y4-c | `test_y4_c_…_dropping_the_orphan_durably` | resolved | sound | Y4 closes |

The check names are abbreviated where they exceed a table cell; the
declaration's `UNIT_CHECKS` cites each in full. W17-p-e is parametrized four
ways (`missing`, `mismatch`, `unregistered`, `rewritten`), so the thirteen
unit functions collect as the phase's **16 tests**. W17-p-e2 fails the
`rewritten` case alone, the one its sabotage is aimed at.

The unit work that preceded the cut run passed on the certified tuple as
each task landed. Task 0's engine probes: **5 passed** in
`test_publication_engine_order.py`. Task 1's shipped contract and family:
**748 passed** over the targeted modules, **8 passed** over cut 17's guard
with E4c re-targeted, **7 passed** over cut 14's. Task 2's act-report
amendment: **105 passed**, and **44 passed** over the cut 11, 19, 35 and 38
guards. Task 3's publish intent: **45 passed** in its module, **59 passed**
over six prior guards. Task 4's records: **122 passed**. Task 5's judgment:
**34 passed** in `test_standing_at.py` after its fix round. Task 6's doors:
**35 passed** in `test_publication_doors.py` after its fix round, **587
passed** with the permit inventories, the capability boundary and the
staleness probe. Task 7's acceptance module: **16 passed**, with each of the
fourteen arms caught by hand. Task 8's guards: **28 passed** over the
recent-cut, staleness and frozen-guard modules, the cut-39 fast loop at
`9 passed, 1 deselected`, and each arm audited sound one at a time. `just
test-fast` rose from **5279 passed, 1 skipped** at Task 0 to **5473** at
Task 8. Pyright reported `0 errors` and Ruff `All checks passed!` at every
code task, and `tasks check` reported zero errors and zero warnings. No
capability waiver or skip was used for the discharge;
`VERIFIABLY_UNCERTIFIED_HOST` was never set. The full repository integration
gate belongs to §6.

The new recent-cut entry is `(cut39, 39, (14, 13, 5))` and asserts the
guarantee-rows-exercised line above. That interface check mocks subprocess
execution; the actual chained run is the discharge evidence.

## 2. Accounting

**The frozen row, both verdicts.** Task 0's probes selected
`REPLACE_UNREGISTERED = accepted` — the engine commits a `ReplaceOp` over a
file its chain never registered, so W17-p-e's `rewritten` case and its second
arm, W17-p-e2, are declared — and `ROLLBACK_MEANS = patched create effect` —
patching the engine's create-file effect to raise after registration leaves
the registration and a `committed=False` settlement and no file, so W17-p-f
is declared and **run**. That is the first row of the plan's accounting
table: **14 arms, 13 declaration units, 5 rows**, recent-cut row
`(14, 13, 5)`, and the phase passes 16. No arm is unrun, so no row is read in
part.

**W17 closes in full**, its intent-position arm judged over the chain's
inventory. Cut 14 closed the ordinary revision family and left this arm with
`publish` (coordination design §11.6), which withdrew the constructed-prefix
arm because an intent carried only its payload. The publish intent now
carries the frozen `binding_tips` and `marker_tips` and one anchor per
mounted root other than the written root, and `standing_at` decides presence
at the intent's position from each root's committed registrations up to its
bound: every inventoried revision read and content-matched, removals and
rewrites `history-violated`, files the chain does not account for classified
by a chain re-read under the engine's write-ahead order. The six W17-p units
read the second writer between tip read and append (refused
`predecessor-not-standing`), the lawful sibling after the intent, the anchor
bound, mount-order independence, the inventory's refusals, and a rolled-back
registration followed by its retry.

**Y1–Y4 open and close at this cut.** Y1: version 2 declares both kinds, a
version-1 pin authorizes neither, every ordinary door refuses both, and
neither enters a world-index map or moves a `belief_input_digest`. Y2: both
records are byte-functions of the intent and the named arguments. Y3: the
publish intent decodes by its domain and qualifies only by a `publish` report
with its token; a malformed domain payload and a bare domainless `publish`
triple are audit findings. Y4: step 8 is all-or-nothing, a refusal writes its
report alone, and a remotely revealed refusal is an orphan in the next
intent's `marker_tips` until a shared publish carrying it closes.

The global corpus is **193 of 220 guarantee rows closed, 27 open**, up five
from cut 38's 188 of 220 (the Y table's four rows were banked at the freeze,
never selected until now). The accounting entry
`39: ("conformance-cut-39-results §2", "W17, Y1, Y2, Y3, Y4", "")` in
`python/tools/roadmap_status.py` produces the roadmap's Appendix A, whose
totals line reads `Closed 193 of 220; open 27.`; no row is reopened. The
eighth off-path lane under roadmap rule 6 re-ranks nothing on the dogfood
path: the first belief publishes nothing.

`root.py` remains the one `atoms` importer: the `FileState` comparison and
the registered and detached inspectors are the moment seam's
(`root.moment_seam()`), reached through seam callables, and
`coordination.py`, `publication.py`, `publication_doors.py` and
`intents/publish.py` import nothing of `atoms`. **The write inventories were
checked in both directions.** `_bind_publication` calls
`execute_fulfilling_guarded`, an inventoried write primitive, so
`"publication_doors.py:_bind_publication": "publish"` joined
`WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gained a `Case` in
`test_permit_entry_points.py`'s `CASES` (with `extra_families`
`corpus-write`, since the door also writes the act-report); the intent door
writes only through `_append_operation_intent`, already inventoried; no other
new caller of a primitive exists, and
`test_the_inventory_is_closed_in_both_directions` and
`test_the_cases_cover_the_inventory_exactly` pass. The coordination contract
ships as `v1` (the former fixture, identity `c440b93f…`) and `v2`; the base
contract, both base `CONTRACT.yaml` copies and the TypeScript tree are
unchanged. The act-report oracle gains the `publish` kind and its one entry;
the coordination contract gains a version — two amended oracles
`contract-cut` freezes after. Version 2's query vocabulary also carries
`composite` and `composes`, so a version-2 pin spells a `kinds: [composite]`
predicate and `closure` over `composes`; `beliefs-c80d8c`, the amendment cut
32 filed, closes with this record (spec §13).

## 3. Evidence

### 3.1 Frozen evidence and corrections

**The freeze moved before review cleared.** Cut 39 first froze at `15fd610`
(body SHA-256 `c032eab7…9755`). Its review found §5's Y1-b module and §2's
boundary naming `permit.py` or `corpus.py`, as the plan's Task 8 table did;
the exclusion actually lives in `world/epoch.py`, whose capture keeps a node
only when `node.kind in stored.WORLD_KINDS`. The fix commit `8e81e1a` froze
Y1-b's module as `world/epoch.py` and added it to §2, and the freeze moved
there (`CUT39_FREEZE_COMMIT = 8e81e1ac72ac…`, `CUT39_FROZEN_SHA256 =
b92c7a20…7a43`); nothing depended on `15fd610`, which stays in history
unrewritten. The frozen row and both verdicts were unchanged by the move.

Cut 39's body remains byte-exact to that freeze: `git diff` over
`docs/designs/2026-09-23-conformance-cut-39.md` between `8e81e1a` and
`4cb09d8`, the head the cut ran at, is empty, and the file's SHA-256 at this
record's parent is `b92c7a20…7a43`; this record's own commit changes the
`**Status:**` line and nothing else. Its declaration remains at the SHA-256
above. No prior frozen declaration or cut body differs from the pre-lane
tree (`2b875a7`): the branch diff over `n2_arms_cut*.py` and the cut
documents names only cut 39's own.

**Cut 17's E4c re-targeted, frozen `after` kept.** Decision 7 made
`publish` an act family and `publishes()` the kernel requirement, which
removed E4c's pinned `before`,
`        raise ValueError("publish is not an act family")`. Cut 17's live guard
re-targets it in `test_n2_cut17.py`'s `_LIVE_SABOTAGES`: `before` is now
`        return cls(_PUBLICATION_PERMIT)`, the frozen `after`
(`        return cls(WritePermit(frozenset(), frozenset()))`) is kept, and the
check body is rewritten under its cited name to assert that `publishes()`
answers the kernel permit. Cut 17's guard passed **8 passed** under the
re-targeted arm. One consequence is stated here because the texts are
frozen: `n2_arms_cut17.py`'s `asserts` string, "publishes() is refused while
publish is not a family", and the kept check name
`test_publishes_is_refused_while_publish_is_not_a_family` now describe the
opposite of what the check asserts. The declaration is frozen and the name is
cited, so both stay; the check's own comment names the re-target.

**Cut 14's W18a checks swapped their made-up kind.** Two checks cut 14's
live W18a cites —
`test_coordination_write.py::test_an_earlier_contract_version_authorizes_nothing_added_later`
and the acceptance `test_w18a_an_undeclared_kind_mints_nothing` — used
`publication` as a kind version 1 does not declare. Once `publication`
became real, the new `KindNotMintedHere` refusal fired before validation and
both failed. Each now uses `milestone`, still undeclared in version 1, with
the test names unchanged and not hash-pinned. The arm is still sound: under
its sabotage both checks fail (`DID NOT RAISE ValidationRefused`), and cut
14's guard passes **7 passed**.

**Cut 19's J1e keeps its pinned literal.** J1e pins the eight-kind
`OPERATION_KINDS` literal in `report.py`. Rather than rewrite it, the
literal stays as `_DOMAINLESS_OPERATION_KINDS`, and `OPERATION_KINDS` is
derived from it plus `publish`; J1e still mutates the enum through the
derivation, and its sabotage still kills
(`test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration`,
1 failed under the arm).

**Cut 35's T2-c keeps its pinned line unique.**
`CorpusWriter._append_operation_intent` gained a `payload=` parameter for the
pre-encoded publish intent. T2-c pins
`        digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))`;
the new path takes its own early-return branch above that line, and the
digest-shape check moved into `_checked_intent_digest`, whose lines no arm
pins. The T2-c `before` still occurs once and its `after` still parses.

**The corrections the cut document carries.** §3's paragraph after the unit
table adds W17-p-e's `rewritten` case, declared because
`REPLACE_UNREGISTERED` is accepted (spec §16, user review of the plan), and
§5 adds W17-p-e2 as a fourteenth arm row, homed to it. §3.2 supersedes by
citation the frozen cut-14 text's "pure function of a constructed chain
prefix", which is not edited. §2 and §5 carry Y1-b's corrected module above.
Spec §11.2's own table was not amended; the cut is where the fourteenth arm
is frozen.

### 3.2 The planning notes, deviations and read-at-freeze choices

**The planning notes the spec carries (§16).** Every one landed as
written: `completion` admits `PublishIntent` (§5's "completion itself is
unchanged" corrected); the Y table's owner is
`../designs/2026-09-22-publication-design.md`; `standing_at(mounts, address,
kind, *, written, position, anchors, seam)` with `MomentSeam`'s five members
and the inventory, byte match and re-read as pure functions in
`coordination.py`; the written root read with the registered inspector and
every other root with the read-only detached one; `Destination` in
`intents/publish.py` and `Anchor` in `coordination.py`;
`publication_content_malformed` applied by the factories, by `standing_at`
and by `corpus_check`; the doors in `publication_doors.py` with
`PUBLISH_INSTRUMENT`; step 0's `PublicationRefused`; a creation defined on
the registration's own `initial`, with W17-p-e's `rewritten` case and
W17-p-e2; the orphan fold qualifying each report through `shapes.mismatch`,
refusing `report-unqualified`; the stored mirror decoding a binding outcome
through `report.binding_outcome_from_facet`; `selection` members as world
record ids; and the view revision carried by the pin on the view (Task 4),
so `marker_record` takes no `view_revision`.

**Every "read at freeze" choice.** The cut froze before its code existed, so
each sabotage `before` was read from the implemented tree and checked for
exactly one occurrence and a parsing `after`: W17-p-a, W17-p-b (`_judge`'s
one-line `standing_at(… position=opened.digest …)` call, unique because
`marker_tips_at`'s `position=` sits on its own line), W17-p-d, Y2-a, Y4-a,
Y4-b and Y4-c (`_reports_at`'s three-line refusal) in `publication_doors.py`;
W17-p-c, W17-p-e, W17-p-e2 and W17-p-f (the full
`if type(entry) is SettledEntryView and entry.committed …:` line) in
`coordination.py`; Y1-a (`revise_coordination`'s seven-line guard block,
`after` its last five lines) in `corpus.py`; Y1-b
(`        if node.kind in stored.WORLD_KINDS` widened to admit
`publication-binding`) in `world/epoch.py`; Y3-a
(`        if sniffed["domain"] == PUBLISH_INTENT_DOMAIN:`) in
`intents/shapes.py`. Task 0's verdicts were read at freeze from the probes,
and the frozen row from them.

**`ROLLBACK_MEANS` and `RETRY_AFTER_ROLLBACK`.** Both are Task 0's probes in
`python/tests/test_publication_engine_order.py`, run on the certified volume.
`ROLLBACK_MEANS = "patched create effect"`: patching
`atoms.coordinator.effects.create_file.apply` to raise after registration
raises `ExecutionError` ("cut after registration") and leaves one
registration, a `committed=False` settlement and no file; the rollback probe
reads the settlement with the detached inspector first, which runs no
recovery, then with the registered one, and both are well-formed with
nothing pending. `RETRY_AFTER_ROLLBACK = "same intent"`: after a rolled-back
`execute_fulfilling_guarded`, a retry under the same intent is admitted and
commits, leaving two fulfilling registrations, the first rolled back and the
second committed — which W17-p-f reads as "present once, not ambiguous".
`REPLACE_UNREGISTERED = "accepted"` is the third probe, and the write-ahead
order (a registration appended before its create effect runs) the fourth.

**Ruling 6: an engine refusal to inspect a log.** A production inspector's
`LogEvidenceRefused` (`ChainStateInvalid`, `TransactionHalted`) propagates
from `standing_at`. Step 0 lets it propagate — nothing is revealed and
nothing written. Step 8's `_judge`, which only the guard calls, catches it
and returns `PositionRefused("chain-malformed")`, so the guard records
`evidence-refused` with reason `chain-malformed`, carrying `corpus_id`,
`marker` and `remotely_revealed`, and a remotely revealed attempt stays an
orphan. `EVIDENCE_REFUSAL_REASONS` is not widened. The catch sits in `_judge`
rather than the guard because W17-p-a's frozen `before` pins the guard's
first line at eight spaces. Tested at both steps and both roots.

**Y1-b reads the act report's own entry.** A publish's act report is a
world record, so the binding door adds exactly one address-map entry — the
report's. Y1-b asserts that entry is the map's only new one, that the map
without it equals the map before, that the other four members are
byte-equal, and that `belief_input_digest` is unchanged. The unit's claim —
a binding and a marker leave the world-index maps unchanged — is what is
asserted; the report's entry is the act's, not a publication record's. The
Y1-b arm, admitting `publication-binding` to the capture, adds a
`publication-binding:` entry and is caught.

**W17-p-d fails at the codec under its arm.** Ordering anchors by mount path
makes `PublishIntent`'s own ascending-anchor check raise inside
`_open_publication` before the test's order assertion is reached; the check
still fails under the arm, at the codec's line. The reversed-mount-order
comparison passes by construction today, because `CoordinationResolver`
sorts its mounts by path; the check's docstring says so.

**Fixes outside the task briefs**, each tested:

- `session/reconcile.py`'s `_session_of` fell through to `value.get("actor")`
  for any non-operation value and would have raised `AttributeError` on a
  `PublishIntent`; it now reads the actor from a `PublishIntent`
  (`test_a_session_actor_on_a_publish_intent_names_its_session`).
- `Destination` refuses a local locator carrying NUL or text that does not
  encode canonically (a lone surrogate), as `MalformedRecord`.
- The orphan fold refuses an intent with more than one committed fulfilment
  within the bound (`revision-malformed`) rather than folding the last.
- `_bind_publication` refuses a `remotely_revealed` that is not a bool, and
  checks the writer's pins, before any effect.

**Task-level deviations**, each gate-forced or fail-early and each reviewed:
the contract fixture is typed by an `isinstance` narrowing, not a cast;
`test_profile.py`'s exported-route list gained `shipped_coordination`;
`_mint_publish_report` refuses anything but a `PublishIntent` by type; both
factories and `marker_record`'s `selection` refuse a wrong type as
`MalformedRecord` rather than `TypeError`; `bounds` also requires one anchor
per non-written mount (duplicate corpus ids fail closed) and raises
`TypeError` on an answer outside the `ChainView` union; the acceptance
module's `_closed_durably` compares the on-disk report by id and facet, since
`act_report_node` mints a fresh uid per call; the cut-39 shim re-exports
`REPLACE_UNREGISTERED` and `ROLLBACK_MEANS`, which the guard's accounting
table keys on.

**Final review.** Recorded at §6 when the whole-branch review and the
repository gate run.

**Post-discharge fixes.** The whole-branch review after discharge at
`4cb09d8` found two Important findings and four minors, fixed in one
dispatch (Ruling 11). None edits the frozen declaration: every cut-39
`before` still occurs exactly once, no `before` pinned in `permit.py`,
`publication_doors.py`, `profile.py` or `corpus.py` by any earlier cut moved,
and `test_n2_cut39.py` passes all ten, sabotage audit included.

- **I-1, `bc6565f`** — decision 7's exception was admitted by permit
  equality, so `RequiredCapabilities.for_kinds(["publication-binding",
  "act-report"], {"act-report": "corpus-write"})`, reachable from science's
  `mints:` write class, built the kernel requirement. `for_kinds` now refuses
  any family outside `COMMAND_REACHABLE_FAMILIES` before constructing, and
  `__post_init__` admits the kernel permit only while `publishes()` runs.
  `test_every_ordinary_route_naming_publish_still_refuses` gains the
  `for_kinds-exact` and `direct-exact` cases.
- **I-2, `e21fb3d`** — nothing checked that the intent entry at
  `opened.digest` decodes to `opened.intent`. The guard now requires the
  written chain's entry there to be an intent whose payload is
  `encode_publish_intent(opened.intent)`, raising `MalformedRecord` before
  registration otherwise, so nothing is written. The two mismatched-pair
  unit tests now tamper with the chain's appended intent.
- **m-4, `e21fb3d`** — step 0 refuses `mounts-changed` up front when the
  written root is not mounted. The check sits at the profile lookup, not
  inside the lock: an unmounted root has no profile, so the lock was never
  reached and the door answered with a contract refusal.
- **m-1, `392373b`** — `shipped_coordination(True)` passed `True in (1, 2)`
  and `@cache` conflated it with `1`; a non-int version is a `ProfileError`.
- **m-3, `1bbb259`** — the ordinary family doors told a publication kind to
  enter through the coordination family door, which refuses it; they now
  name the publish doors. Same exception type; cut 14's pinned branch is
  untouched.
- **m-2, `7692b3a`** — the coordination-and-view-kinds design's cut-14
  sentence leaving "only W17 intent-position" open gains a dated
  parenthetical recording W17's closure at cut 39.

### 3.3 Review findings and limitations

Every task was reviewed against the spec before the next began. Task 0's
review found the Y1-b site (§3.1) and a stale guide total; Task 5's, the
re-read's absent-view branch returning `chain-malformed` and three minors;
Task 6's, the unvalidated `remotely_revealed`, the silent double fulfilment
and the unchecked pins; Task 7's, Y1-a exercising `add` and `import_bundle`
with a binding only — now a marker too. Each was fixed in a round of its own
and re-reviewed clean.

The spec's §14 limitations stand, none reopening a row: neither door has a
public route, so a session cannot publish; no marker is written anywhere;
the moment seam reads whole chains; anchors bind only mounted roots; a root
populated before its genesis refuses `unregistered-revision`; and the
judgment reads every inventoried revision's bytes and is exact, not cheap.
Narrower ones the reviews recorded: a detached read that carries a staged
registration whose digest is not yet in `entries` would read a file it
created as `unregistered-revision` — unreachable under write-ahead and
erring toward refusal; a committed registration whose pre- and post-state
are the same file over an inventoried path reads `history-violated`, which
no door produces; `standing_at` does not apply `coordination_facet_malformed`
to ordinary kinds, since it serves only the publication doors.

Recorded at the final review (Ruling 12): an exception raised before any
effect at step 8 — a non-bool reveal, a pin disagreement, an unbound port,
malformed binding arguments, a mismatched `OpenedPublication`, a guard
exception other than `LogEvidenceRefused`, or a `LogEvidenceRefused` on the
written root whose fallback cannot write — leaves the intent unfinished
rather than orphaned. Recovering a remotely revealed marker from an
unfinished intent belongs to the second slice's recovery table
(`beliefs-328507`).

## 4. Reproduction measurement

The reproduction record's §18
(`../designs/2026-09-05-mm30-reproduction.md`) records the run at
`b036e8e`, committed at `101cdd2`. `reproduction.rederive` read the
established mm30 corpus in place; no contract succeeded, so nothing was
recreated or moved aside. The fresh result was the same `NoBelief` payload,
`{"detail":"","kind":"NoBelief","reason":"no-directional-outcome"}`, with
`rederived_equal: true`. The complete `state.json` diff was empty; before and
after its SHA-256 was
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`, the same
digest §17 recorded. A grep of the driver for this slice's own symbols
(`PublishIntent`, `publication-binding`, `publication_doors`,
`shipped_coordination`, the coordination family doors) is empty, and mm30's
manifest pins no coordination contract, so the v2 amendment reaches nothing
the driver reads.

## 5. Remaining boundary

`publish` stays open, in the ledger's table and the roadmap's boundary
index, tier 1 off the path. **W17** is closed in full and **Y1–Y4** are
closed; what remains is the governed publication act itself, the second
slice (`beliefs-328507`): the request record and its durable create-only
write, the selection snapshot that answers `corpus-drifted`, the step-0
refusals before the intent (`pins-disagree`, `empty-selection`,
`closure-incomplete` with its composite amendment) and the retry's
`request-corrupt`, staging, head export and replication, the reveal, the
recovery table, the transport seam, and marker-required arrival with the
recipient's `divergent-publication`. It appends its own rows to the Y table
and its lifecycle entries to the act-report's `publish` kind.

**L1** remains partial on its persistence arms: kill the executor between
entry durability and apply at every stage; crash after entry durability but
before the transaction record stores the entry digest; cut persistence at
every stage of the settlement sequence for both terminal arms. These belong
to `persistence-cut` (`beliefs-3ea822`, tier 2), behind `atoms-f5779f`, as
cut 36 re-homed them. Cut 39 reads no L1 arm.

**T7** remains partial on its cross-root case, owned by
`cross-root-publication` (`beliefs-256f17`, tier 3); cut 39 reads no T7 arm.

## 6. Main integration

Filled at merge: the whole-branch review, the repository gate on the exact
integrated head, and the `--no-ff` merge.

## 7. Execution rulings

- **Ruling 1 — the frozen row governs every later count.** Task 8's
  interface line spelled `CUT39_ARMS (14)` and `DECLARATION_UNITS (13)` as
  the first row's example; the guard reads the frozen row from the cut, and
  no later mention restates its own count.
- **Ruling 2 — the merge is outward-facing.** Task 11 runs the gate, then
  stops and asks before merging to `main`.
- **Ruling 3 — Y1-b's site is `world/epoch.py`**, the capture's
  `stored.WORLD_KINDS` membership test the world-index derivation reads,
  added to §2's boundary; the spec names only "the site that keeps
  coordination kinds out of the world-index maps".
- **Ruling 4 — the freeze moves to the fix commit**, since it had not
  cleared review; `CUT39_FREEZE_COMMIT` and `CUT39_FROZEN_SHA256` are the
  re-recorded values (§3.1).
- **Ruling 5 — Task 0's five minors folded into its fix round**: the ledger's
  tense, the detached-inspector reading and the `committed is True` assertion
  in the probes, an unused helper, a wrong comment, a roadmap sentence break.
- **Ruling 6 — `LogEvidenceRefused`** propagates at step 0 and is
  `evidence-refused`/`chain-malformed` at step 8 (§3.2).
- **Ruling 7 — Task 5's cheap minors** went to a short resume of its
  implementer: the re-read's three-way view check, `@sealed` on the value
  types, a same-bytes rewrite test, and a real-seam `revision-mismatch`.
- **Ruling 8 — Task 6's fail-early holes** (the non-bool reveal, the double
  fulfilment, the pins) and its step-0 test gap went to a short fix round.
- **Ruling 9 — the chained runner is the controller's.** It outlives a
  subagent's one-turn budget, so Task 8's implementer committed the guard
  and runner, and the controller launched the runner detached through
  `detached.sh`, read the log, and closed the step task.
- **Ruling 10 — every cut-root export is resolved.** The symlinked checkout
  spelling makes `openat2` under `RESOLVE_NO_SYMLINKS` refuse with `ELOOP`;
  every export was spelled through `readlink -f` (Task 0 found about 195
  environmental failures without it). The exports are load-bearing:
  without them the runner would write its roots onto the uncertified work
  volume (`beliefs-51ffdf`).
- **Ruling 11 — one fix dispatch after the final review** for I-1, I-2 and
  the four minors, then `test_n2_cut39.py` and the gate re-run (§3.2).
- **Ruling 12 — an exception before any effect leaves the intent
  unfinished, not an orphan.** Recorded as a limitation (§3.3) and as a note
  on `beliefs-328507`, whose recovery table must cover it.
- **Every implementer ran in the foreground and committed before
  returning.** The one detached run this lane has made — the chained cut
  runner — went through the reaping wrapper; its process group was
  confirmed gone. The repository gate is the lane's other detached run and
  has not run yet; §6 records it.
