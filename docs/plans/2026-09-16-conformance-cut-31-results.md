# Conformance cut 31 — results

**Cut:** `../designs/2026-09-15-conformance-cut-31.md`
**Freeze:** `c2a2211c2d9a0889a59e7892dcb71f2008e20e46`; SHA-256 `3cd4409dd08d5b121d3f62bfaaa00e3d553335d6a54e7657471c70677854d93f`
**Declaration:** `python/tests/n2_arms_cut31.py`, committed at `2977a83`; SHA-256 `50a32687a11a3ea3aba01c288c10d1b15ce98010f03cd0c7d7313a67c5c30a3b`
**Subject:** the estimand, its applicability, and the estimate and uncertainty the rule yields, typed
**Design:** `../designs/2026-09-12-estimand-typing-design.md`
**Discharged:** 2026-09-16, on `design/estimand-typing`
**Runner:** `python/tools/cut31_acceptance.py`

## 1. What ran

```sh
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
for v in 4 7 10 29 30 31; do export SCIENCE_CUT${v}_ROOT="$MAIN_CHECKOUT/.cut31-acceptance/estimand-typing"; done
export SCIENCE_MM30_ROOT="$MAIN_CHECKOUT/.work/reproduction/mm30"
export MM30_PREDECESSOR="$MAIN_CHECKOUT/.work/reproduction/mm30.cut22"
just check > docs/plans/2026-09-15-conformance-cut-31-run/check.log 2>&1
just test > docs/plans/2026-09-15-conformance-cut-31-run/test.log 2>&1
(cd python && uv run --frozen python tools/cut31_acceptance.py > "$MAIN_CHECKOUT/.cut31-acceptance/run.log" 2>&1)
just hook-pre-push
```

`just check` exited 0 ([`check.log`](2026-09-15-conformance-cut-31-run/check.log),
SHA-256 `9a8fe9cf6876977bbc9029479648798f5fead7bfc7b4dec382a7e333e52ac602`):
`All checks passed!`, Pyright `0 errors, 0 warnings, 0 informations`, Biome
`Checked 15 files in 26ms. No fixes applied.`, task validation
`{"errors":[],"warnings":[]}`.

`just test` exited 0 ([`test.log`](2026-09-15-conformance-cut-31-run/test.log),
SHA-256 `c9f7a99842612df7866002bdb9c01deef2e78314ec73dd95605405e95509fade`):
**`4817 passed in 1152.58s (0:19:12)`** for the Python half and
**`Test Files  7 passed (7)`** / **`Tests  148 passed (148)`** for TypeScript.

The certified aggregate exited 0
([`certified.log`](2026-09-15-conformance-cut-31-run/certified.log), SHA-256
`c7820f2a12049b5ae57a981cfa2114952c8a2b38ef1b39e47d7ab6d189f03144`): 46 module
summaries and **740 tests passed**, with no failed, skipped, ERROR or
`CapabilityUnavailable` line. Its declaration line reads **`declared arms: 26
(= 10 declaration units; 10 guarantee rows)`**, every arm audits `sound`, and
the baseline resolve — every distinct check run once against the real package —
is `resolved`.

`just hook-pre-push` exited 0 on the final tree: `4817 passed in 1154.30s
(0:19:14)` and `Tests  148 passed (148)`. Its transcript is scratch; the cut
retains the three logs above.

The prefix chain is cut 31 → cut 30 → cut 29 → cut 28 → cut 27 → cut 26 →
cut 25 → cut 24 → cut 23 → cut 22 → cut 21 → cut 20 → cut 19 → cut 18 →
cut 17. Cut 31's own phases are `test_estimand_acceptance.py` (10 passed in
6.12s; one test per table-Q row) and `test_n2_cut31.py` (10 passed in 9.96s;
the twenty-six arms audited both ways).

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 24 passed in 12.64s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 43 passed in 49.90s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 17.35s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 7.21s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 30.88s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.17s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 14.82s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 321.59s (0:05:21) |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 128.56s (0:02:08) |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 16.71s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 14.40s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 79.75s (0:01:19) |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 46.50s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 70.95s (0:01:10) |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 79.97s (0:01:19) |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.60s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.78s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 110 passed in 28.60s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 16.55s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 58.09s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 28.75s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 33.47s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 27.84s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 40.59s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 34.45s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.86s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 35.94s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.52s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.15s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 124.36s (0:02:04) |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 44.21s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 90.40s (0:01:30) |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 23.98s |
| cut25 phase 2/3 | `test_source_address_acceptance.py` | 21 passed in 39.81s |
| cut25 phase 3/3 | `test_n2_cut25.py` | 8 passed in 8.82s |
| cut26 phase 2/2 | `test_n2_cut26.py` | 10 passed in 1.44s |
| cut27 phase 2/3 | `test_world_audit_acceptance.py` | 42 passed in 238.85s (0:03:58) |
| cut27 phase 3/3 | `test_n2_cut27.py` | 9 passed in 53.35s |
| cut28 phase 2/3 | `test_world_selection_acceptance.py` | 25 passed in 118.05s (0:01:58) |
| cut28 phase 3/3 | `test_n2_cut28.py` | 9 passed in 39.22s |
| cut29 phase 2/3 | `test_dataset_address_acceptance.py` | 10 passed in 7.89s |
| cut29 phase 3/3 | `test_n2_cut29.py` | 9 passed in 5.62s |
| cut30 phase 2/3 | `test_source_address_acceptance.py` | 21 passed in 40.58s |
| cut30 phase 3/3 | `test_n2_cut30.py` | 9 passed in 4.44s |
| cut31 phase 2/3 | `test_estimand_acceptance.py` | 10 passed in 6.12s |
| cut31 phase 3/3 | `test_n2_cut31.py` | 10 passed in 9.96s |

## 2. Accounting

Ten guarantee rows are read, **10 full/closed**: Q1–Q10, every clause of every
row including each row's negative and sabotage clauses, with nothing deferred.
The frozen inventory is **10 declaration units** expanding to **26
one-mutation sabotage arms**, homed per unit exactly as the cut's §5 homes them
(Q1 2, Q2 3, Q3 7, Q4 1, Q5 3, Q6 3, Q7 3, Q8 1, Q9 1, Q10 2).

The global corpus is **163 of 206 rows closed, 43 open**, in nineteen tables
(`python/tools/roadmap_status.py`, which gains this cut's entry in this commit).
No P row's verdict changes, M1–M13 are untouched, M6 governs the new
declaration class unamended, claim identities do not move, and
`mm30-reproduction/outcome-file/v1`'s identity is unchanged.

`estimand-typing` enters the ledger's `Current state` and the roadmap's
boundary index at this discharge and closes in this same commit, so neither
table carries an open row for it; the roadmap's lane table carries the closed
`estimand-typing` lane. `weighted-belief`'s *blocked on* becomes the successor
belief-policy design over `commensurable` and `co_scoped` (`beliefs-638318`),
still tier 3 — the key domain it waited for is now supplied and the answer it
waits on is a policy design, not a typing one.

## 3. Evidence

No allowlist, no frozen declaration, no frozen cut body (cut 31 §1–§7
included) and no cited-not-run guard was changed. No `n2_arms_cut*.py` body
through cut 30 was edited.

### 3.1 Corrections carried by the cut document

Three corrections are recorded as dated supplements in
`../designs/2026-09-15-conformance-cut-31.md` §8, outside the frozen body and
outside the guard's `_frozen_body` slice, so the freeze pin is unchanged and is
not re-taken. None adds a declaration unit, a row or an arm.

- **§8.1 — Q10's `UnfreezableSpec("pre-grammar spec")` clause is unreachable
  over the prior corpus.** The 2026-09-05 spec record predates the *projection*
  form: its `analysis-spec` facet carries the frozen members directly and has no
  `projection` key, so `analysis_spec_value` refuses on the facet's shape and
  `restore`'s `estimand_grammar` check — the only site that raises
  `PreGrammarSpec` — is never reached. The assessment half fires exactly as
  written. `prior_pre_grammar` is therefore **defined** by three measurements,
  not asserted: the prior corpus's assessment record raises
  `PreGrammarAssessment`; its analysis-spec record returns no typed value; and
  `audit_corpus` over that state under the successor profile reports exactly
  `profile-mismatch: base`. The requirement the clause exists for — *no reader
  returns a typed value for either* — holds in both halves.
- **§8.2 — the digest movement is measured one level down.** The belief value is
  `NoBelief(no-directional-outcome)`, and a `NoBelief` carries no
  `belief_input_digest`; only a `Belief` does. There is no old/new digest pair
  at the belief and this cut invents none. The movement is quoted at the spec
  identity (`86aaa1a8…` → `10e8bfce…`) and the derived assessment identity
  (`316272987716ac4f…` → `618c6c584da64b62…`), over the same data and the same
  run inputs, with the belief value equal on both the driver's derivation and
  the fresh process's.
- **§8.3 — cut 22's frozen `M8a` arm went vacuous, and its check's premise was
  restored additively.** Q8's estimand walk gave `testing` a second route into
  the consulted set through the fixture's typed estimands, so dropping the claim
  route no longer removed it. The frozen `n2_arms_cut22.py` and `consulted.py`
  are untouched; `python/tests/test_domain_facet_read.py` now measures the
  claim's own route in isolation, every original assertion surviving, and
  `certified.log`'s cut 22 phase shows the arm selecting again (`7 passed`).
  §8.3 also records that Q10-a's after-block widens `restore`'s gate rather than
  coercing, that Q5-a selects on the refusal's name, and that
  `CUT31_DECLARATION_SHA256` is a content pin only.

### 3.2 Deviations from the plan, all reviewed and taken

- **Live re-targets of two earlier cuts' arms.** Cut 20's `D8a`
  (`test_n2_cut20.py`) and cut 21's `V2a`, `V8c`, `V8e` and `V8f`
  (`test_n2_cut21.py`) are re-targeted live as dated `_LIVE_SABOTAGES` entries,
  the mechanism cut 30 used for `W5a-m`. No frozen declaration body is edited.
- **One uncertainty codec, not two.** The plan duplicated the wire↔value
  mapping between `decode.py` and `estimand.py`; the implementation unifies it
  in `estimand.uncertainty_from_mapping` and both readers call it.
- **`audit_world` gained the pre-grammar codes.** The plan named only
  `audit_corpus`; a captured world corpus reports `spec-pre-grammar` and
  `assessment-pre-grammar` under the same rule, and the world-audit test asserts
  the audit continues past them.
- **`python/tools/reproduction/belief.py`'s `pins_negative` passes
  `estimands=`,** so the unpinned-`biology` refusal is measured with the typed
  estimand supplied to the walk as well as the claim.
- **The reproduction's step table gained `preflight` and `analysis_inputs`**,
  and the driver keeps the prior corpus at `.work/reproduction/mm30.cut22`
  rather than deleting it, because the transition measurement reads it.
- **`python/tests/test_n2.py`** forwards `SCIENCE_MM30_ROOT` into an arm's child
  process; without it Q10's check resolves the reproduction work root beside the
  lane's worktree and can neither pass at baseline nor fail meaningfully.

`python/tests/test_domain_facet_read.py` lies outside cut 31 §2's file map; it
was first touched by this lane at `029babe` for the same interaction on a
sibling test, and the §8.3 repair keeps it inside the lane's boundary. The
frozen-guard doctrine is silent on a frozen arm whose *check* goes vacuous under
a later cut — the arm is not stale, its assertion is still true, and its stated
premise has become false — so §8.3 is the precedent: restore the premise
additively in the later cut's own tree, edit neither the frozen declaration nor
the source it sabotages, and show the arm selecting again in the certified
transcript.

## 4. Reproduction measurement

The mm30 reproduction re-ran under the successor contracts, recorded as a dated
addendum at `../designs/2026-09-05-mm30-reproduction.md` §10. It **recreates**
the corpus rather than retyping it (design decision 10), with the prior corpus
state moved aside to `.work/reproduction/mm30.cut22` and never deleted.

- **Three held lists** beside the 285-term concept list: `stage-level` (2 terms,
  `sha256:d77b182f993b076f…`), `measure` (1, `sha256:31993609d906c316…`) and
  `identification` (4, `sha256:559ea6c06d0beba2…`), each bound to a dataset
  address by the successor contract (§10.1).
- **The typed estimand, as spelled** (§10.2): claim `780ace5964c8ab83…` at
  `mm30/affects-concept-molecular-entity`; a `levels` contrast on slot 0 from
  `level:ndmm` to `level:pd`; measure `measure:rna-seq-tpm` on the `additive`
  scale; reference `0`; control `identification:observational` with no
  conditioning; applicability `{}`. Every referent resolved `member` on the
  first call.
- **The refused clause and where it went** (§10.3): the prose applicability's
  *"samples of `dataset:gse179929`"* is dropped under design §4, and *"whose ids
  carry a stage token and whose value is finite"* is **refused** — the operator
  declares no dimension it could be typed along — and was re-authored into
  `method`. That relocation is an **authored judgment**, recorded as one; no row
  certifies scope equality.
- **The prose spec is cited as text and nothing else** (§10.4):
  `86aaa1a8a8edda82…`, not restored, not revised, not superseded; the new spec
  carries `supersedes: None` and no record in the new corpus names it. The
  re-authored spec is `10e8bfce1aaad8a9…`.
- **The identities that moved** (§10.6): spec `86aaa1a8…` → `10e8bfce…`;
  derived assessment `316272987716ac4f…` → `618c6c584da64b62…`. The belief value
  is **equal** on both sides: `NoBelief(no-directional-outcome)`.
- **The consulted set is unchanged**, `{science, mm30, biology}` (§10.5), as
  design §5.4 predicted; with `biology` unpinned the walk still refuses.
- **The fresh process** (§10.7) restored the frozen spec through
  `analysis_spec_value` and the assessment through `assessment_value` from the
  corpus on disk and re-derived both: `rederive`'s four keys — `spec_restored`,
  `assessment_restored`, `belief_equal` and `prior_pre_grammar` — are all
  `True`.
- **The prior corpus state** (§10.8) under the successor profile audits to
  exactly `profile-mismatch: base` and nothing else, its pinned base contract
  predating the grammar.

This cut adds **no new mm30 measurement of the on-path question**: the
reproduction reached the same evaluator answer it reached on 2026-09-08, over
the same data, and nothing here places a boundary on the path. Tier 1's on-path
state is not re-ranked.

## 5. Remaining boundary

`estimand-typing` retains nothing: Q1–Q10 close in full, the design's twelve
limitations are banked as limitations rather than work, and the boundary leaves
the ledger in the commit that entered it.

`weighted-belief` retains **S6 arm (h)** and is re-blocked: its key domain —
`commensurable` and `co_scoped`, both exposed from `beliefs.estimand`, both
total, neither read by `science.belief.v1` — is now supplied, and what it waits
on is the successor belief-policy design over that key (`beliefs-638318`),
which also has to rule on whether its constants are global or domain-scoped.

`authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**.
`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm, and gains this lane as a dependency: the
base contract, the operator declaration class, the assessment facet and the D6
oracle are all amended here, so N1 mints a successor identity for each if the
contract froze first.

## 6. Main integration

To be completed when `design/estimand-typing` merges to `main`: the merge
commit, the whole-branch review disposition, and `just gate` on the unchanged
merged revision with the exports of §1.
