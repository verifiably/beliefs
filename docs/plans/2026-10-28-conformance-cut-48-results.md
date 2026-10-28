# Conformance cut 48 — results

**Cut:** `../designs/2026-10-28-conformance-cut-48.md`.
**Freeze:** `5895d232ea47584baa91dcf249717d905735e1a6`; SHA-256 `8ab350edad763dc15d4831de74d3cac13053f869c0da209338919fbbab475d4d`.
**Declaration:** `python/tests/n2_arms_cut48.py`, committed at `c7dffd1`; SHA-256 `b16832c572d2be8718c25139e70c9741206a28bf1cb2285fadc84fcbaf2d100b`.
**Design:** `../superpowers/specs/2026-10-28-overlapping-publications-design.md`, accepted at `e14315c`.
**Plan:** `../superpowers/plans/2026-10-28-overlapping-publications.md`, revision 4 at `a125fa6`.
**Implementation and proof:** through `67da5e1`; status/accounting updates follow the successful run below.
**Task:** beliefs-918fd2 (Task 7 is beliefs-821239). The task holds the implementation review and its disposition; this record and all final status edits enter that review together.

## 1. What ran

The execution baseline `just test` (Setup, 2026-10-28, before Task 1) passed 6,278 non-N2 Python tests, 46 standalone N2 tests and 155 TypeScript tests, with one Python skip. Durable tests ran on the certified kernel `7.2.2-arch1-1` and ext4 volumes mounted `rw,noatime,data=ordered` (the main checkout's `.work/acceptance/cut48` for the chain, its `.cut4-acceptance` for the module runs); no capability refusal was waived.

Before the chain, the W20-b pilot (`test_cut48_pilot`) resolved its baseline and killed its mutation, and the 1b fixture passed its eight cases in a module run. The complete new guard then passed nine checks: every named baseline resolved and all 33 declared mutations and the uncounted ride-along were sound. The retargets Tasks 2 to 5 made were proved in their owning guards' baselines and audits (cuts 7, 23, 24, 27, 28, 33, 34, 41, 42, 44, 45, 46 and 47), after the durable twins §3 names were amended. A sweep of every durable acceptance module except the N2 guards then passed. The recent-runner interface check passed one case for cut 48, proving command/environment/cleanup/accounting shape without substituting for the real run.

The first complete successor at `f3c4b40` started at `2026-10-28T17:42:15.138180+00:00`, ran every prefix phase clean (79 summaries, 1,206 passes) and stopped after 2,511.620 seconds with exit 1 at cut 48's own accounting: the new runner's `declared_accounting` imported the prior cut's tuple name, a slip the recent-runner check would have caught had it been run before the launch. One line was fixed (`67da5e1`) and that check run; no assertion, span or pin changed. The failed log is retained beside the task as `cut48-runner-import.log` (SHA-256 `3dfbe4c424ab947cb6650d95564de71f0374daaa8333dca2cb658e92ed9feb55`) and is not discharge evidence.

The successor restarted at `67da5e1`. `TASK_TEST_HOME` names the empty task-owned test home under persistent task storage; uv resolves the installed frozen environment before HOME changes:

```sh
just --set one_cmd 'cd python && uv run --frozen env HOME="$TASK_TEST_HOME" XDG_CONFIG_HOME="$TASK_TEST_HOME/.config" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 python tools/cut48_acceptance.py' test-one -q
```

The recipe supplies `host-budget run`. Cut 48 chains only `cut47_acceptance.py`, preserving constant prefix depth, then runs `test_overlapping_publications_acceptance.py` and `test_n2_cut48.py`. The runner uses main `.work/acceptance/cut48` on the certified volume and removes its per-run roots.

The invocation began at `2026-10-28T18:25:45.396328+00:00`, exited **0** at `2026-10-28T19:13:24.364287+00:00`, and took **2858.968 seconds**. All **111 pytest phases and 1,215 passing invocations** passed with no failure, error, skip or capability refusal. The 79 printed summaries report **2735.72 seconds** of pytest time and 1,206 passes (the 1b fixture's eight among them, in 87.93 seconds); forwarded `-q` suppresses the final guard summary, whose nine passing dots and successful return establish its nine checks, and that phase's time is excluded from the subtotal. The runner's closing lines read `declared arms: 33 (= 33 declaration units; 6 guarantee rows)` and the accounting line §2 quotes.

The exact log SHA-256 is `ac6833994cd0d7b188852db314122fe6a20449db6043fa353dc10b4e197a4f79`. The task retains the log and command/start/end/exit metadata as `cut48-runner.log` and `cut48-runner.json` under `$WORK_ROOT/beliefs/beliefs-918fd2/`, with the first run's pair beside them.

## 2. Accounting

**33 arms, 33 declaration units, six exercised rows.** W19, W20, G14 and Y19 close; J17 and J20 reclose under their cut 48 amendments; W8b, G10, G12, Y5 and Y17, reopened at freeze, reclose by the retargets proved below. `overlapping-publications` is discharged. `ACCOUNTING[48]` names this section and the six rows; the seven freeze-time `REOPENED` entries are removed. The live total moves from 219 at freeze to **230 of 257 rows closed, 27 open**.

The recent-runner inventory carries `(cut48, 48, (33, 33, 6))` and checks the exact output:

```text
guarantee rows exercised: 6 (4 newly closed: W19, W20, G14, Y19; J17 and J20 amendments reclosed)
```

| unit | check suffix | result |
|---|---|---|
| W19-a | equal_content_reads_once | resolved / sound |
| W19-b | differing_content_refuses | resolved / sound |
| W19-c | corruption_outranks | resolved / sound |
| W19-d | deprecated_key_entry | resolved / sound |
| W19-e | epoch_shapes | resolved / sound |
| W19-f | discovery_once | resolved / sound |
| W19-g | live_map_holders | resolved / sound |
| W20-a | view_serves_once | resolved / sound |
| W20-b | holders_disagree_refuses | resolved / sound |
| W20-c | absence_over_holders | resolved / sound |
| W20-d | owners_check_narrowed | resolved / sound |
| W20-e | damaged_holder_rule | resolved / sound |
| W20-f | resolve_address_holders | resolved / sound |
| W20-g | contributing_union | resolved / sound |
| W20-h | mapped_view_and_absence | resolved / sound |
| W20-i | audit_files_per_holder | resolved / sound |
| G14-a | union_over_holders | resolved / sound |
| G14-b | rejected_everywhere_inert | resolved / sound |
| G14-c | predicate_per_holder | resolved / sound |
| G14-d | filtered_graphs | resolved / sound |
| G14-e | snapshot_merged_fold (`TestG14eMergedFold::test_a_counter_accepted_through_one_holder_restores_in_either_order`) | resolved / sound |
| G14-f | merge_self_check | resolved / sound |
| G14-g | filtered_fidelity_one_comparison | resolved / sound |
| G14-h | v2_rule_binding | resolved / sound |
| G14-i | v2_fold_world | resolved / sound |
| Y19-a | own_wins | resolved / sound |
| Y19-b | carriers_agree | resolved / sound |
| Y19-c | earliest_origin | resolved / sound |
| Y19-d | ambiguous_refuses | resolved / sound |
| Y19-e | order_independent | resolved / sound |
| Y19-f | v2_narrowing | resolved / sound |
| J17-c | citation_equal_content (`test_j17_c_a_citation_of_equal_content_resolves_once_with_every_contract_checked`) | resolved / sound |
| J20-b | node_corpus_holder_set | resolved / sound |

The full node ids and exact sabotage text are frozen in the canonical declaration. Each unit has one independently named check; there are no co-citations. The guard also audits one uncounted live-table arm, beliefs-cb2a39's ride-along (below).

## 3. Behavior, review points and evidence limits

Four checks grew after the first guard audit so that their declared mutations are killable, each asserting its row's own behaviour more directly: W19-c's capture carries a duplicate location beside its uid corruption (the precedence is otherwise unobservable); W20-a adds a shared run carrying a relation (the shared dataset carried none, so a per-holder inbound build was unobservable); W20-g evaluates an addresses-only query (the kinds query's other records made the union trivially complete); W20-i asserts a `supersedes-cross-kind` recomputation finding under both holders (the stale-hash finding it already asserted is filed by the structural pass, not the recomputation loop). No arm, span or assertion in the frozen declaration changed for these; the declaration was committed after them.

The ride-along arm (beliefs-cb2a39: dropping the `continue` on an unheld observed target in gather's observes loop) is homed on `test_world_view.py::TestEvaluationOverTheWorld::test_an_unknown_observed_dataset_is_skipped_at_the_facet_read`, a check added for it, not on the banked-reason check §3 names: a covered corpus's absence returns from `gather` before the observes loop (correction-remainder slice 2 decision 7), so that check passes with the `continue` dropped. The arm lives in the guard's `RIDE_ALONG_ARMS` tuple and joins `CUT48_ARMS` after the 33 declared arms, so the staleness audit covers it while the inventory counts exclude it. It is sound.

Three durable twins of units the W8b amendment reaches were amended to differing content, as the unit twins were in Task 2: `test_w8b_duplicate_location_is_the_same_finding_with_shared_or_distinct_uids_durably[True]`, the twin in `test_w8b_corruption_outranks_duplication_and_a_corpus_alone_reports_neither_durably`, and `test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably`. Under §4.2 a shared uid with equal content is one record held twice; the duplicate location those cases pin is the differing claim.

Retargets proved by kill in their owning guards, each keeping its frozen check and moving its mutation to the same decision's new site: cut 7's `Location` checks and two index-addressed arms; cut 23 W6, W6b, W10, W10d, W10e, W10g and R19b; cut 24's M3a check amended; cut 27 S9-c and W8a-a; cut 28 W8-a and W8b-a..d; cut 34 BI-4 and BI-8; cut 41 Z5-a/b/c; cut 44 J16-d, J17-a, J19-c and J19-d; cut 45 G10-c/d/f, G11-a/b/c, G12-a..i, G12-l and G13-b; cut 46 Y17-a..p and Y18-n; cut 47 Y17-q/r/u. G12-h follows cut 22's B4b pattern: its check is rewritten to the v2 obligation and its mutation, the removal of the explicit two-resolutions refusal, is G14-g's. Every prior canonical declaration and frozen body is unchanged.

Obligation changes recorded in the execution ledger: `TestTheSplit` is rewritten to the v2 obligation (the moved counter is overturned and the world reads) with a v1-bound twin asserting the former refusal; `test_g12_h_split_with_exclusion` reads the v2 split through and carries the v1-bound two-resolutions refusal its retargeted mutation removes (cut 22's B4b pattern, sharing G14-g's mutation); `test_g12_l_accept_all_refusal_parity[split]` keeps parity and adds "no refusal" under the shipped binding; J17's second case (`test_a_citation_held_by_the_write_root_and_a_mount_refuses_naming_both`) is amended to differing content, as spec §8 amends decision 4 and J17 by citation.

Pre-passing pins, each still killed by its row's mutation: `test_g14_i_v2_fold_world` and the closure-digest invariance test passed before Task 4's code (their obligations were met by Tasks 2 and 3); G14-b, Y19-a, Y19-b, Y19-e and Y19-f passed before Task 5's code (the verification loop already iterated one copy per holder, and the sorted first holder happened to be the own or least holder). G14-a, J20-b, Y19-c, Y19-d, J17-c and every W19/W20/G14-c..g unit went RED→GREEN.

The 1b fixture (`test_overlapping_publications_acceptance.py`, eight cases) builds world *A* as its own typed corpus (the shared `source` fixture's topic corpora hold no assessment) and stages every publication under the profile the typed records derive; its uid-corruption case moves the carried copy under another address rather than adding a second file, since two records of one uid inside one corpus is that corpus's own malformed state.

Limitations are the cut's §7, unchanged: a carried record's content is frozen while a carrier is mounted; a renamed record beside its predecessor stays `uid-corruption` (beliefs-49afc2); the supersession order is readable only through held markers; equality is exact; a damaged holder is skipped only against a published content identity; legacy epochs stay singular and v1-bound until rebuilt; authenticity is unchanged; no cost measurement.

## 4. Verification and review

Each task's module run went RED at its new assertions and GREEN after its change, and each task's `task-done` run passed (Task 2: 6,297 fast; Task 3: 6,306; Task 4: 137 in the four standing modules and 6,322 fast; Task 5: 176 in its three modules and 6,332 fast; Task 6: the fixture's cases). The staleness and frozen-guard suites were green after each task's retargets. Precommit checks passed with zero pyright errors or warnings throughout.

After discharge edits, the documentation, recent-runner, staleness and frozen-guard checks passed **63 cases**; the required fast check passed **6,334 Python tests, one skip, in 98.12 seconds**, with no affected TypeScript tests selected (the baseline supplied the TypeScript coverage). `just check`, `tasks check` and `git diff --check` passed. The full `just test` suite ran once more over the final tree before the whole-branch review; its result is on the task. Live roadmap output reports **230 of 257 closed, 27 open**. Only the cut document's status line changed after its freeze; §§2–7 and the canonical declaration remain pinned.

Implementation review is recorded on beliefs-918fd2 before findings are acted on. The task's execution ledger retains every ruling: the W8b fixture amendments and their durable twins, the pre-passing pins, the retarget lists, the ride-along's re-homing, the check extensions, the fixture's own typed corpus and staging profile, the two-resolutions refusal's message, the holders asked, and the runner slip. No final evidence/status edit is exempt from the whole-branch review.

## 5. Remaining boundary

None for `overlapping-publications`: W19, W20, G14 and Y19 close and J17, J20, W8b, G10, G12, Y5 and Y17 reclose at this cut. L1 remains partial under `persistence-cut`, and T7 remains partial under `cross-root-publication`; the other ledger boundaries remain open and are not re-ranked here.

Science's side of commons milestone 1b is sci-73c80e (spec §8 verbatim: the `Carrier` content check, the three-item adopt checklist, `mount_holding`/`cited`, `explain` wording, pins, the in-place change refusal, chain retention, `show`'s marker naming, and the `SYMBOL_FIELDS` replacement); sci-4a3543 and sci-9104fb depend on it. This cut changes no live corpus, mount, registry, configuration, contract pin or science code. beliefs-c800ef's rule has landed as the v2 bundle; the record stays for the user's call.
