# Conformance cut 10 — discharge results

**Date:** 2026-08-25
**Subject:** verified holdings, store-side, world-index slice 5
(`docs/designs/2026-08-24-world-index-holdings-design.md`, promoted from the
implementation spec in this same change), measured against conformance cut
10's frozen selection (`docs/designs/2026-08-24-conformance-cut-10.md`).

**The frozen cut's rows, selected bullets, labeled declarations, obligations,
and accounting are not edited here.** Cut 10 froze at `5e0266f`, whose status
pins the independently reviewed text at `2186a71`; only the cut's status header
changed at banking, to record the discharge, point here, and name the promoted
spec path. Results are recorded separately.

**Integration state.** Every implementation commit was made on
`design/holdings`, based on `98ce7ed` on `main`. **The branch is not merged or
pushed by this discharge.** The `--no-ff` merge is the human partner's act and
must preserve the inherited reachability constraints (`4a7dc19`, `c8c0b12`,
`117f37e`, `0977bde`) plus cut 10's freeze pin `2186a71`.

**Integration correction, 2026-08-25.** The human-partner merge subsequently
landed on local `main` as `35be6ff` with `--no-ff`, preserving every named
reachability constraint. The merge has not been pushed. The paragraph above
records the discharge-time state; it is no longer the current integration
state.

## 1. Accounting, independently re-derived

Recounted from the frozen cut's §3 selected bullets, not copied from §4:

| state | rows | n |
|---|---|---:|
| full | H1, H2, H3 | 3 |
| partial | H4, G9, L7, L10 | 4 |

**3 full + 4 partial = 7 rows read.** H4 is partial because its URL/remote arm
does not run; G9 because this cut runs only the independence sabotage; L7
because general qualification, G4, and the run/operation shapes do not run;
L10 because this cut runs only the two holdings-read clauses. Under the
any-unrun-arm rule none may be relabeled full. Every other row remains at its
prior cut's certification or named owner.

Declaration units, counting every §3.1 Selected unit and every §3.3 labeled
declaration once at its single home:

| row | H1 | H2 | H3 | H4 | G9 | L7 | L10 | labeled |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| units | 3 | 6 | 3 | 3 | 1 | 2 | 2 | 11 |

The selected rows sum to 20 and labels J1–J11 sum to 11: **20 selected + 11
labeled = 31 declaration units**. The declaration module carries exactly that
partition and the acceptance audit parses the frozen accounting independently.
All 31 declared units run their complete stated checks under one sabotage;
none of the units itself contains an unrun arm. The four partialities above are
source-row partialities, not failed or shortened declared units.

Seven units (`H1u1`, `H1u3`, `H4u2`, `L10u1`, `L10u2`, `J1`, `J2`) cite the
atoms certification for engine-interior facts. Those citations live in
`ATOMS_CITATIONS_BY_UNIT`, outside every Science check tuple, and are never
counted as Science checks.

### 1.1 What the rows establish

- **H1, full:** acts mint only established outcomes; managed mutations use the
  engine's verified final rows, and detached capture cannot mint.
- **H2, full:** explicit per-location supersession over an acyclic walk;
  contested, incommensurable, and unsettled locations block; agreement retains
  every head and expectation; timestamps order nothing.
- **H3, full:** coverage is declared and whole, capture commits coherent chain
  heads, and receipt validation re-runs the exact named prefixes and binding.
- **H4, partial:** the store instantiation publishes or fails, launders no
  inconclusive attempt into absence, and mutates only after its durable intent.
- **G9, partial:** corrupting the adapter's promotion predicate makes G9 fail
  while G2b, R5, and R10 pass through that same sabotaged installation.
- **L7, partial:** holdings-shaped qualification follows the three-step
  precedence and holdings intents append before mutation; broader shapes wait.
- **L10, partial:** metadata-less and failed-restore unserviceable roots report
  inconclusive holdings attempts and never mint absence. These are the exact
  two remainders cut 9 left; L10 has no named cross-cut remainder after cuts
  8–10, though this cut's row label remains partial.

### 1.2 Harness refinements forced during implementation and review

The all-checks-fail audit forced declaration constructions to become less
vacuous, not broader:

- H2's stored fixtures now decode through the production reader; H3u3 has a
  same-output, head-only identity delta; the unresolved L7 construction is a
  canonical chain the production inspector accepts; and every L7
  non-qualifying fulfillment is a genuine committed transaction.
- G9's co-pass reaches `science.admission.admit`, not merely
  `admission_state`; H4u3 uses the frozen skip-intents/mutate/publish sabotage,
  not a mixed-store binding-order surrogate.
- The cut-10 root is forwarded through the nested N2 child boundary and used
  by the shared durable fixture. Empty and unset values select the same exact
  repository-relative fallback. A configured uncertified root produces a real
  engine refusal rather than a checkout-volume false pass.
- The acceptance suite carries two ordinary construction pins added after the
  implementation surface existed: detached capture over an undamaged store
  cannot mint, and an active absent head ends promotion.

## 2. What ran, and where

Science resolves `atoms-core` and `nodes-core` as editable path dependencies.
All commands ran sequentially from this repository's `python/` directory.
Acceptance runners were never concurrent because their environment-selected
work roots are shared state.

Every gate-relevant edit preceded the evidence collection. The exact
transcripts were inserted afterward into this results record, with their
summary recorded in the execution ledger; neither file's content is read by a
gate. `git diff --check` was repeated after that prose-only insertion.

### 2.1 Host and certified tuple

- backend `LinuxBackend`; storage profile
  `StorageProfile(profile_id='flush-honoring-disk.v1')`
- default work directory `.cut10-acceptance` beside the checkout;
  `SCIENCE_CUT10_ROOT` unset, so the runner used the repository volume
- probe: one throwaway world root, corpus root, and store root; refusal is an
  error, never a skip
- volume: ext4 on `/dev/nvme0n1p2`, mounted `rw,noatime,data=ordered`
- kernel `7.1.8-arch1-3`
- measured source: `04748e7`, plus this banking change's documentation and
  count-table edits

### 2.2 Certified cut-10 discharge

```text
$ cd python && set -o pipefail && uv run --frozen python tools/cut10_acceptance.py
[cut10 phase 1/2] cut9_acceptance.py
[cut9 phase 1/2] cut7_acceptance.py
[cut7 phase 1/3] cut5_acceptance.py
.......................................                                  [100%]
39 passed in 22.66s
[cut7 phase 2/3] cut6_acceptance.py
.......................                                                  [100%]
23 passed in 12.03s
[cut7 phase 3/3] test_n2_cut7.py
..........................................                               [100%]
42 passed in 44.28s
[cut9 phase 2/2] test_n2_cut9.py
.......................                                                  [100%]
23 passed in 17.82s
declared units: 30 (pinned by test_the_declared_units_are_unique_and_number_thirty, among the tests above; not itself a pytest total)
[cut10 phase 2/2] test_n2_cut10.py
...................................                                      [100%]
35 passed in 10.74s
declared units: 31 (= len(CUT10_ARMS); pinned by test_the_declared_units_are_unique_and_number_thirty_one, among the tests above; not itself a pytest total)
### exit: 0
```

The five `N passed` lines are pytest totals: cut 5, cut 6, cut 7, cut 9, and
cut 10's phase respectively. The final `31` is `len(CUT10_ARMS)`, a declaration
count pinned among phase 2's tests; it is **not** a pytest total. Cut 9 is the
sole prior-cut current-tree prefix: it chains cut 7, which chains cuts 5 and 6.
Cut 8 remains a byte-identical pin at its banking commit rather than a
current-tree runner because cut 9 deliberately succeeded its retired store
refusal.

### 2.3 Portable and documentation gates

The portable suite excludes `tests/acceptance` by configuration and therefore
makes no durability claim.

```text
$ cd python && set -o pipefail && uv run --frozen pytest 2>&1 | tail -2
.................................................................        [100%]
2513 passed in 398.05s (0:06:38)
### exit: 0
```

```text
$ cd python && uv run --frozen ruff check .
All checks passed!
### exit: 0
```

```text
$ cd python && uv run --frozen pyright
0 errors, 0 warnings, 0 informations
### exit: 0
```

```text
$ cd python && set -o pipefail && uv run --frozen pytest tests/test_designs_corpus.py 2>&1 | tail -3
............                                                             [100%]
12 passed in 0.45s
### exit: 0
```

```text
$ cd python && uv run --frozen python tools/check_guide.py
### exit: 0
```

```text
$ git diff --check
### exit: 0
```

The three documentation tests deliberately red through Tasks 0–10 — README's
design table, README's spelled count/date, and the guide's design citation —
and turn green only in this banking change.

### 2.4 Stale-claim and worktree audit

The prescribed grep returned matches and exit 0. They fall into four explicit
classes: frozen cuts/results and banked authority rows preserving their dated
claims; historical implementation plans/ledgers quoting their then-current
instructions; the promoted holdings spec stating what this slice **closed**;
and live text that now says the holdings slice landed. No live guide match says
the holdings work remains open. The only authoritative implementation-state
row, adoption-ledger row 4, carries the dated closure at atoms `038513f`; row 5
carries the narrowed remainder.

```text
$ grep -rn "holdings slice\|unresolvable for holdings reads\|row 4's\|dereference-minting" docs/ README.md > /tmp/science-cut10-stale-grep.txt
$ wc -l /tmp/science-cut10-stale-grep.txt
52 /tmp/science-cut10-stale-grep.txt
### exit: 0
```

Before staging, the final status listed exactly the banking amendment set: the
README, adoption ledger, cut-10 status, promoted spec, three guide pages,
results and execution ledgers, implementation plan, and count table. No runtime
source or test declaration changed.

```text
$ git status --short
 M README.md
 M docs/designs/2026-08-03-redesign-adoption-ledger.md
 M docs/designs/2026-08-24-conformance-cut-10.md
RM docs/superpowers/specs/2026-08-24-world-index-holdings-design.md -> docs/designs/2026-08-24-world-index-holdings-design.md
 M docs/guide/contracts-and-adoption.md
 M docs/guide/foundations.md
 M docs/guide/open-questions.md
 M docs/plans/2026-08-24-holdings-ledger.md
 M docs/superpowers/plans/2026-08-24-holdings.md
 M python/tests/test_designs_corpus.py
?? docs/plans/2026-08-24-conformance-cut-10-results.md
```

## 3. Commit identities

Base `98ce7ed` on `main`. The commits this discharge measured, in order:

| commit | subject |
|---|---|
| `823e021` | docs(specs): draft the world-index slice-5 holdings spec |
| `1e8fff4` | docs(specs): close the holdings spec review's six findings |
| `08be4f0` | docs(specs): draw the capture/rule line at mechanism vs judgment |
| `b026cb8` | docs(specs): bind capture to canonical projections under the state identity |
| `eb2899a` | docs(specs): pin qualification as a three-step precedence |
| `1f77781` | docs(specs): correct §2.2 to the engine's commit-time evidence |
| `daccc18` | docs(specs): carry the surface/chain-row distinction and registration obligation |
| `a50fdfb` | docs(specs): state the complete-surface/registered-subset split in §2.2 itself |
| `b231e08` | docs(specs): own the engine-raise abort in §4.1 |
| `3c87ccc` | docs(specs): record the atoms gate approval at 558817b |
| `6a1fe11` | docs(specs): record the landed atoms seam at 038513f |
| `10c9b54` | docs(designs): draft conformance cut 10 (verified holdings, store-side) |
| `39b2d73` | docs(designs): close cut 10's first-round reader findings |
| `2186a71` | docs(designs): close cut 10's amendment-round findings |
| `5e0266f` | docs(designs): freeze conformance cut 10 at 2186a71 |
| `3cd6147` | docs(spec): record cut 10's freeze in the holdings spec status |
| `f684942` | docs(plans): holdings slice implementation plan |
| `94a73cf` | docs(plans): close the plan review's eight findings |
| `662a74f` | docs(plans): close the plan review's second round |
| `4a20cf6` | docs(plans): pin the malformed-intent validity contract and parameterize its test |
| `178ff77` | docs(plans): open the holdings execution ledger |
| `f7df31d` | feat(holdings): the holdings-observation record kind and store locator |
| `5e88932` | feat(holdings): join the stored codec surface as a governed kind |
| `8658789` | feat(holdings): the store act seam over read_path_state and final_states |
| `6300a9a` | feat(holdings): the two store act shapes under the intent discipline |
| `eeff742` | test(holdings): close store act review gaps |
| `86cbe29` | test(holdings): complete store act review coverage |
| `ed0e373` | feat(holdings): mechanical coverage capture under the closed schema |
| `a1f6d41` | fix(holdings): close mechanical capture review findings |
| `7003f32` | fix(holdings): translate initial corpus decode failures |
| `16b74b4` | feat(holdings): the fixture-bound active-set reducer |
| `d6615ca` | fix(holdings): close reducer review findings |
| `63029ac` | feat(holdings): the holdings-reduction receipt under its own domain |
| `d7a5852` | fix(holdings): close receipt validation review findings |
| `265c4b5` | feat(holdings): the dataset-scoped adapter into admission_state |
| `8501893` | test(holdings): pin both adapter result seals |
| `c37e9bc` | test(holdings): pin dataset digest overlap semantics |
| `e1b0ce3` | test(holdings): make digest overlap reducer-reachable |
| `4eb7fd9` | test(cut10): declare the 31 frozen arms |
| `22461e9` | test(cut10): close admission and ordering review |
| `6a8055d` | test(cut10): certified acceptance runner |
| `ef749bd` | test(cut10): keep arm checks on certified root |
| `04748e7` | test(cut10): align empty root fallback |

The banking commit that follows carries this record, the promoted spec, the
cut status change, adoption/guide/README amendments, the plan and execution
ledger close-out, and `_COUNT_WORDS` entries 35 and 36. It changes no holdings
runtime behavior.

## 4. Cross-repository prerequisite

The atoms-local holdings seam was designed and approved at `558817b`, then
implemented and reviewed on `design/holdings-commands`. It merged `--no-ff` and
was pushed; local and remote atoms `main` both resolve to `038513f` at this
discharge. That head provides `read_path_state` and the required
`TransactionOutcome.final_states` field. Its own merged verification was
`6234 passed, 7 skipped`, Ruff clean, Pyright 0, and diff-check clean.

This Science cut consumes that certified interface; it does not re-certify the
atoms lease, descriptor walk, errno classification, or commit-time final-state
observation. The seven citation-bearing units state exactly that boundary.

## 5. What the discharge establishes

- `science.holdings-observation.v1` is a governed stored kind with the closed
  store locator, canonical facet and identity, store-only URL deferral, and
  authored-family refusal.
- Recheck, write, delete, and move append their own intents before reading or
  mutating. Findings publish through registered observation paths; moves use
  two intents and the engine's dual-location final evidence.
- Coverage capture carries every canonical record plus the complete validated
  chain under a closed schema. Qualification and the active-set reducer are a
  pure fixture-bound rule with explicit precedence and three blocking classes.
- A closed holdings-reduction receipt commits coverage, rule binding, chain
  heads, and both output digests; validation selects named historical prefixes
  and re-runs rather than trusting the old answer.
- The dataset adapter joins outcomes, expectations, and history after a
  blocked-first pass, then feeds cut 2's unchanged admission state.
- Adoption-ledger row 4's holdings prerequisite is closed at atoms `038513f`.
  Row 5 narrows to general intent qualification with G4, event-level L8, and
  the L13 preimage resolver.

## 6. What this run does not claim

The frozen cut's §8 limits stand:

- no Science persistence-cut harness; engine-interior durability stays the
  atoms certification's claim;
- no URL canonicalization or retrieval, remote H4 instantiation, or acquisition
  orchestration;
- no general L7 reduction, G4 closure, run/operation qualification shapes, or
  remaining intent-boundary arms;
- no recency successor or typed retrieval grants;
- no ruling that the holdings receipt belongs to the belief-input closure.

The acceptance mutation audit proves each declared check fails under its one
source sabotage. It does not prove arbitrary implementations equivalent,
honest observations, or resistance to out-of-band raw writers.

## 7. Known limitations and departures

- **Digest-set admission.** The unchanged cut-2 `ByteObservation` surface has
  no expectation/history association. If a joined found digest is also another
  digest in a multi-resource declaration, admission treats it as an ordinary
  declared match; the overlap is reducer-reachable and pinned. A mismatch is
  visible when the joined digest differs from the declaration's digest set.
  Cut 10's G9 sabotage uses the declared single-resource construction, so its
  selected independence arm is unaffected.
- **Two-source rule bundle.** `qualify.py` is concatenated byte-for-byte before
  `rules_v1/holdings.py`; the ordinary suite pins that the importable helper and
  shipped rule cannot drift. This is deliberate, not a third implementation.
- **Frozen stand-in defaults.** Two registered-entry fields keep `None`
  defaults only because cut 8's declaration file is pinned byte-identical;
  production supplies both and capture refuses either missing value.
- **Test chronology.** Several cohesive implementation batches made later
  contract pins green on first execution. The execution ledger records each;
  no such pin is represented as red-first TDD.
- **Acceptance-run serialization remains procedural.** No lock file prevents
  two acceptance commands running concurrently; operators and agents must run
  them sequentially.

## 8. Banking corrections

1. The implementation spec promoted to
   `docs/designs/2026-08-24-world-index-holdings-design.md` and now records the
   discharge, results, execution ledger, atoms prerequisite, and current local
   integration state.
2. Cut 10's status header alone records discharge and explains its frozen
   pre-banking spec citation; §1–§8 remain frozen.
3. Adoption-ledger row 4 closes the holdings prerequisite at pushed atoms
   `038513f`; row 5 keeps only general intent qualification with G4,
   event-level L8, and the L13 preimage resolver.
4. README gains the promoted spec and cut 10, the count becomes thirty-six,
   and the date range ends 2026-08-24. The corpus spelling table gains only 35
   and 36.
5. The live guide records cut 10's discharge and local merge state, points
   derived heldness at the executable design, and removes the two cut-9
   holdings-read units and row-4 coordinator seam from its open remainder.
   Frozen cut and prior-results records are untouched.

## 9. Execution ledger

Implementation rulings, review amendments, TDD disclosures, task heads, and
the final banking close-out live at
`docs/plans/2026-08-24-holdings-ledger.md`. That ledger records the final
reviewed pre-banking head `04748e7`; this record and the banking amendments are
the conventional commit immediately following it.
