# Conformance cut 37 — results

**Cut:** `../designs/2026-09-21-conformance-cut-37.md`
**Freeze:** `b4f27a26c552a03bbe2371175cacf739385e905e`; SHA-256 `9d43fa5c1a559d064b8116cf6c0d1395343e6f4bb110603a64b4704b5abe8292`
**Declaration:** `python/tests/n2_arms_cut37.py`; SHA-256 `2af3031429451082791ea905083de858971862b29257b0c97838a946cf5b9cfa`
**Subject:** L13 — digest-matched classification over held copies and surviving preimages, stated absence and corruption refusal
**Design:** `../superpowers/specs/2026-09-21-l13-preimage-design.md`
**Plan:** `../superpowers/plans/2026-09-21-l13-preimage.md`
**Discharged:** 2026-09-21 on `design/l13-preimage`, through `2223f95`; reproduction recorded at `c2ad3ae`
**Runner:** `python/tools/cut37_acceptance.py`

## 1. What ran

The certified runner ran from `.worktrees/l13-preimage/python/`, with cut
roots on the main checkout's certified volume and mm30's retained corpus
as the reproduction root. The worktree's own volume is uncertified. Cut 37
chains **cut 36's** runner (`PREFIX_RUNNERS = ("cut36_acceptance.py",)`),
which retains the complete live prefix back through cut 17's nineteen
phases. Cut 8 remains cited-not-run under R15; its L13u4 and L13u5 are
cited to `2026-08-22-conformance-cut-8-results.md` and read by cut 37's own
durable checks and guard, never by re-running or repairing cut 8's guard.

The runner exited **0**. Its two final lines, verbatim from the main
checkout's `.work/acceptance/cut37-runner.log`, are:

```text
declared arms: 15 (= 11 declaration units; 1 guarantee rows)
guarantee rows exercised: 1 (1 newly closed: L13; row 5 partial for L1 under persistence-cut)
```

Its own phases were:

```text
[cut37 phase 2/3] test_l13_preimage_acceptance.py
11 passed in 10.06s
[cut37 phase 3/3] test_n2_cut37.py
10 passed in 6.82s
```

Every prefix phase passed. Every one of the eleven live checks resolved
and passed without sabotage; all fifteen mutations scored **sound**. No
unit was stale, vacuous, mixed or uncollected. L13-b homes two arms and
L13-d homes four; every other unit homes one. Each check below is in
`python/tests/acceptance/test_l13_preimage_acceptance.py`:

| declaration unit | check | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|
| L13-a | `test_l13a_a_logged_removal_is_in_the_timeline_and_draws_record_removed_durably` | resolved | sound | L13 closes |
| L13-b (b1, b2) | `test_l13b_the_surviving_preimage_classifies_the_removal_on_the_writable_root_durably` | resolved | sound, sound | L13 closes |
| L13-c | `test_l13c_a_held_copy_of_another_version_of_the_record_resolves_nothing_durably` | resolved | sound | L13 closes |
| L13-d (d1–d4) | `test_l13d_no_local_history_is_stated_and_a_held_copy_of_the_removed_bytes_resolves_durably` | resolved | sound, sound, sound, sound | L13 closes |
| L13-e | `test_l13e_corrupt_local_history_refuses_the_act_and_touches_no_project_file_durably` | resolved | sound | L13 closes |
| L13-f | `test_l13f_a_removed_record_of_another_kind_classifies_as_not_a_verification_durably` | resolved | sound | L13 closes |
| L13-g | `test_l13g_retirement_appends_a_status_event_and_deletes_nothing_durably` | resolved | sound | L13 relabel |
| L13-h | `test_l13h_preimage_gc_appears_in_no_chain_and_a_read_appends_nothing_durably` | resolved | sound | L13 relabel |
| BI-1 | `test_bi1_the_reads_are_inside_the_hold_after_the_captures_with_the_chains_arguments_durably` | resolved | sound | boundary invariant |
| BI-2 | `test_bi2_a_read_mutates_nothing_and_joins_no_write_inventory_durably` | resolved | sound | boundary invariant |
| BI-3 | `test_bi3_a_preimage_that_hashes_elsewhere_refuses_before_any_finding_durably` | resolved | sound | boundary invariant |

Task 3's isolated mutation probes also observed the intended failures:
skipping the re-hash failed BI-3 with `DID NOT RAISE PreimageMismatch`;
downgrading `MetadataStoreInvalid` to absence failed L13-e with
`DID NOT RAISE LogEvidenceRefused`. After restoring production, all eleven
durable checks passed in 9.34s. Its focused capability, permit inventories,
replay, audit and arrival regression set passed **658 tests** on the
certified volume. Task 4's recent-cut, staleness and frozen-guard checks
passed **26 tests**. The new recent-cut entry is `(cut37, 37, (15, 11, 1))`
and asserts the guarantee-row line above. These runner-interface checks
mock subprocess execution; the actual chained run is the discharge
evidence. `just check` and `tasks check` passed at Tasks 3 and 4. No
capability waiver or skip was used for the discharge. The full repository
integration gate belongs to §6.

Task 6's documentation guards passed **23 tests**; `just check` passed
(Ruff, Pyright with zero errors or warnings, TypeScript typecheck, Biome,
and task checks), and `tasks check` reported zero errors and warnings.
Appendix A matches the generator output exactly, the results-record count
is 33, and the frozen bodies and declaration hashes were verified again.

## 2. Accounting

**L13 closes in full.** Eleven declaration units comprise eight against
L13 and three boundary invariants. The removed state's digest is rendered
through `LogSeam.state_facts`; both channels resolve that digest, reversing
R16's path match. The audit reads surviving preimages through
`LogSeam.read_preimage` after inspection and both captures, under its hold.
Verified preimage bytes take precedence over a held copy, and bytes that
contradict the declared digest refuse `PreimageMismatch`. Unresolved
removals draw `removal-unclassified`; corrupt local history refuses the
act. The retirement and GC taxonomy clauses retain their cut-8 evidence
and gain the two durable relabel checks.

**Row 5 stays partial for L1's persistence arms alone**, owned by
`persistence-cut` (`beliefs-3ea822`), behind `atoms-f5779f`. Cut 37 reads no
L1 arm. The resolver's absence arm is read on non-writable roots: no
collector exists and no engine-produced writable root lacks its retained
history. This is the spec's declared width, not an unrun writable GC arm.

`l13-preimage` leaves the ledger's table and the roadmap's boundary index
in this record's commit. The global corpus is **187 of 216 guarantee rows
closed, 29 open**, up one from cut 36's 186. The accounting entry
`37: ("conformance-cut-37-results §2", "L13", "")` in
`python/tools/roadmap_status.py` produces Appendix A; no row is reopened
or read in part at cut 37. The sixth off-path lane under roadmap rule 6
re-ranks nothing on the dogfood path: mm30 removes nothing.

Both `CONTRACT.yaml` copies and the TypeScript tree are unchanged.
`root.py` remains the one `atoms` importer. Reading preimages adds no
write primitive, so `WRITE_ENTRY_POINTS` and the permit-entry `CASES`
inventory are unchanged. Arrival and restore do not consult preimages.
The history input's validation, evaluator precedence and four outcomes,
and the `record-removed` finding's code, severity, ref, detail and message
retain their contracts.

## 3. Evidence

### 3.1 Frozen evidence and corrections

Cut 37's body remains byte-exact to its freeze; only `**Status:**` changes
at discharge. Its declaration remains at the SHA-256 above. No prior
frozen declaration or cut body differs from the pre-lane tree. The frozen
cut carries the missing-leaf correction already reviewed before freeze:
L13-e unlinks the indexed blob, because a truncated blob is rejected by
registered inspection before the reader's exception translation runs.
No post-freeze cut-body correction was needed.

The digest refactor made cut 8's `L13u1[38]`, `L13u2[39]` and
`L13u3[40]` stale at `ef07763`. It also made `L2u1[1]` stale: splitting
the committed-removal inventory from replay made its committed-set anchor
occur twice. All four are recorded in `cited_not_run.py`; no historical
arm is repaired. An initial Task 1 change retargeted cut 18's frozen G8
declaration. The review fix at `8055e4b` restored that file byte-for-byte
and kept the production local named `held`, preserving the unique
`if held.verdict == "failed":` sabotage anchor. The final declaration
diff is empty, and replay, staleness and frozen guards passed **74 tests**
after the restoration committed.

### 3.2 Deviations and read-at-freeze choices

**Dated correction to spec §9.2 (2026-09-21).** The acceptance fixtures
author removals through `root.durable_executor_factory()` with real
`CreateOp` and `DeleteOp` transactions, rather than `CorpusWriter.delete`.
The real committed chain and retained preimage are the subject; cut 18's
durable managed-delete check covers `delete`'s chain shape, and the
executor is the path it runs on. The spec's review log records the same
correction. No acceptance unit or declared width changes.

The cut froze before its new source sites existed. Task 4 therefore read
the exact implemented source for all fifteen `before` blocks after Tasks
1–3, rather than treating the planning examples as literal tree bytes.
Two layout choices differed from those examples: L13-b2 copied the
three-line `seam.read_preimage` assignment, changing only `byte_len` to
`0`; BI-1 copied the multiline hold-local preimage assignment through
`return evaluate_log`, then dedented the read outside the hold. The guard
checks every site occurs exactly once and every mutated module parses.
L13-g and L13-h copy cut 8's retirement and taxonomy sabotage bodies
verbatim under cut 37's own guard. The other eleven blocks implement the
frozen table directly; none widens or changes its mutation claim.

Task 1 updated the evaluator test that expected only `record-removed` to
expect its newly required absence companion. Task 2 wired the previously
unwired state codec in the audit test seam. Task 3 resolved the fixture
root before engine calls, used stdlib `dataclasses.replace` for seam
overrides, removed an unused import, and formatted imports for Ruff. An
initial regression command named nonexistent `test_log_seam.py`; the
corrected command ran the audit module and passed. Task 4 canonicalized
the certified roots after two preliminary launch refusals (§7). Task 5
corrected the proposed empty broad grep to the actual driver evidence
(§4 and §7).

**Final review.** Two Minor documentation findings were corrected: §16 of
the reproduction record now distinguishes corrupt-history
`LogEvidenceRefused("preimage", "MetadataStoreInvalid", ...)` from
`PreimageMismatch` for returned bytes that fail the declared-digest re-hash;
the `state_facts` seam docstring now names removal resolution through
`_file_facts` alongside mechanical projection. The review is clean, with no
outstanding findings.

### 3.3 Review findings and limitations

Task 3's initial BI-1 recorded only the surface capture and first/last
events, leaving a read before `capture_records` undetected. The review
fix at `72bbbd0` records completion of both real captures and asserts
their order before every read. The final check still probes the real
operation lock with `BuildContended`, and validates the chain's exact
transaction, path and byte length.

Task 2's unit-level arrival/restore no-read assertions use a creations-only
chain, so they alone cannot expose collection conditional on a removal.
The durable L13-d and BI-1 checks subsequently exercise actual removals
through arrival and restore; the unit fixture limitation remains stated.

The three banked scope limits remain: there is no read-only historical
store API (held copies serve these roots), no collector and hence no
writable-root GC production, and no belief/computation consumer of
`failing-verification-removed`. The finding remains a log-audit result.
A future collector must read the writable absence arm in its own cut.
None of these limits reopens L13.

## 4. Reproduction measurement

The reproduction record's §16
(`../designs/2026-09-05-mm30-reproduction.md`) records the run at
`2223f95`, committed at `c2ad3ae`. `reproduction.rederive` read the
established mm30 corpus in place; no contract succeeded, no corpus was
recreated and nothing moved aside. The fresh result was
`NoBelief(reason="no-directional-outcome")`, with `rederived_equal: true`.
The complete `state.json` diff was empty; before and after its SHA-256 was
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`.

The broad driver grep is **not empty**: `reproduction/close.py:57` has
called `audit_log` since `8125e86`. The narrower `rederive.py` scan finds
no `audit_log`, `log_audits`, `committed_removals` or `read_preimage`
reference; that step imports only `close.evidence_for`. Inspection of
the retained corpus found **`committed_removals: 0`**, so even the
historical step-9 audit has no removal to classify or preimage to read.
The acceptance module supplies this cut's preimage exercise. The
reproduction and design guards passed **50 tests** after §16 was added.

## 5. Remaining boundary

`l13-preimage` closes in full at cut 37. **L1** remains partial on its
persistence arms: kill the executor between entry durability and apply at
every stage; crash after entry durability but before the transaction
record stores the entry digest; cut persistence at every stage of the
settlement sequence for both terminal arms. These belong to
`persistence-cut` (`beliefs-3ea822`, tier 2), behind `atoms-f5779f`, as
cut 36 re-homed them. The unspellability arm stands certified at cut 8.
Row 5 remains partial for these arms alone.

**T2** remains partial on the `audit` and `re-check` operation kinds,
owned by `act-report-remainder` (`beliefs-86b150`), now off-path row 1
and still the `world-read` lane's head.

**T7** remains partial on its cross-root case, owned by
`cross-root-publication` (`beliefs-256f17`, tier 3). This cut changes
neither T2 nor T7. The `cross-repo` lane retains `persistence-cut`;
`contract-cut` is the off-path join at row 2.

## 6. Main integration

The final whole-branch review found no Critical or Important issue. Its two
Minor documentation findings were corrected at `99c7dcd`: mm30 §16 now
distinguishes corrupt-history `LogEvidenceRefused` from returned-byte
`PreimageMismatch`, and `LogSeam.state_facts` names removal resolution as a
consumer. The scoped re-review found no breakage.

The detached repository gate then exited 0: Python reported **5,266 passed,
1 skipped** in 1,213.78 seconds, and TypeScript reported **155 passed** in
seven files. The wrapper removed its pid file, process group `2531288` was
gone, and `host-load --section session` reported nothing left running.

Local `main` was current with its upstream and merged
`design/l13-preimage` with merge commit `b8d864e`. `just check` on the merged
tree exited 0: Ruff, Pyright, TypeScript typecheck, Biome and `tasks check`
were green. No push was made.

## 7. Execution rulings

- **Lifecycle wording.** L13-d asserts the engine's
  `PreconditionRefused` wording `read-only-serviceable does not grant
  writability` in the unclassified finding's message; the detail ends
  `preimage=refused`. Detached arrival makes no read and instead asserts
  `preimage=not-consulted`; it asserts no engine refusal wording. A held
  copy under the exact removed digest resolves both paths. Other-version
  copies do not resolve them. The exception adapter catches exactly
  `PreconditionRefused`, `MetadataStoreInvalid`, `ChainStateInvalid` and
  `TransactionHalted`; only the first becomes unavailable evidence.
- **Leaf layout.** The indexed leaf is
  `metadata_root_for(source)/blobs/sha256/<64 lowercase hex>`, with no
  `sha256:` prefix in the filename. L13-e confirms that exact leaf exists
  before unlinking it. A truncated leaf would test the earlier raw
  inspection refusal instead, so it is deliberately not substituted.
- **Physical certified-root spelling.** A zsh export first preserved
  `~` literally, selecting a path on the uncertified worktree volume;
  expanding the home path then reached a symlink rejected by the older
  confinement probe with `ELOOP`. The successful runner and reproduction
  used canonical paths to the main checkout's certified volume. The
  uncertified tuple refused with ext4 options `async`, `barrier=1`,
  `commit=5`, `data=ordered`, profile `flush-honoring-disk.v1`; no waiver
  converted that refusal into certified evidence. Each detached wrapper
  reaped its process group, removed its PID file, and left no process.
- **Preserve the frozen G8 site.** The Task 1 fix retained the production
  `held.verdict` local rather than changing the cut-18 declaration.
  Historical pins remain intact (§3.1).
- **Record the real mm30 coupling.** The plan's broad-grep empty claim
  was rejected after observing the historical `close.py` call. §16 and
  §4 record that call, the empty narrower scan and zero removals instead.
  Claiming the broad grep was empty would misstate the driver even though
  the reproduction answer is unchanged.
