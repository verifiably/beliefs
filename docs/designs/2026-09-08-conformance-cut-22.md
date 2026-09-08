# Conformance cut 22 — the biology pack, the cross-contract slot, the domain-facet read

**Status:** frozen 2026-09-08 before implementation.
**Frozen:** 2026-09-08, before implementation, on `feat/domain-boundary-slice2`.
**Design:** `2026-09-08-biology-pack-design.md`, reviewed 2026-09-08 (three findings, all in the design's status header).
**Numbered after** cut 21 (concurrency rule 1) and **serialized after** cut 21's discharge, which landed on `main` at `03471da` on 2026-09-08 (rule 5).

## 1. What this cut is

Cut 22 is the frozen acceptance boundary for the `domain` lane's second
slice: a sort reference that crosses contracts, resolved at compile or
refused with the missing namespace named; the consulted walk reaching every
claim's sort and dimension contracts and refusing a consulted namespace
whose pin disagrees with the validating profile; the first derivation-side
domain-facet read, minted by the reader, validated, ledgered and digested,
never weighed; and the first packaged domain contract. The selection was
frozen after the design's written review cleared.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. The `B` table is new, so every B row is selected in full.

## 2. The boundary

In scope:

- `contract/domain.py`: `_sort_reference` and the two parse-time refusals
  (own namespace, base namespace); `OperatorDecl.arg_sorts` and
  `DimensionDecl.restriction_sort` carrying a reference as written;
- `profile.py`: the two-pass compile, `_resolve_sort`, the unresolved-
  reference refusal, `shipped_domain_contract`;
- `consulted.py`: the sort- and dimension-contract collection, the
  `science` and per-namespace pin agreement, `facets_read` derived from
  `FacetRead` rows over closure nodes that include observed addresses;
- `facet_read.py`: `FacetRead`, its minting classmethod, `read_observed_facets`
  over a `ReadView` and a target ref;
- `belief.py`: `Records.observed_facets`, the closure-node widening, the
  `ContractMismatch` → `Refused("profile-pin-mismatch")` mapping;
- `evaluation.py`: `gather`'s observed-dataset read, `EvaluationInputs.observed_facets`,
  `evaluate_over`'s mapping of `ContractMismatch`, `FacetPayloadRefused`
  and `FacetUndeclared` to `Refused`;
- `closure.py`: the `observed_facets` member, always present;
- `stored.dataset_node`'s `domain_facets` parameter;
- `domains/biology/DOMAIN.yaml` and its packaged copy;
- `ts/src/contract.ts` and `ts/src/profile.ts`: the same two forms and three refusals;
- the reproduction driver's steps 1b, 2, 3 and 8 over a fresh work directory.

Out of scope:

- the GO, HP, EFO and MONDO bindings (design §9 item 1);
- a kernel-side vocabulary dataset reader (§12);
- any verdict effect of a domain payload (P §open question 4);
- D1's `nodes` negative (cross-repository; deferred with its reason);
- distribution beyond the package (D §12);
- unresolved `observes` addresses (`world-resolution`; §9 item 10).

## 3. Selection

### B1 — closes

A slot sort resolves or refuses, at the right stage. Selected: a bare name
undeclared → refused at parse; `mm30/concept` inside `mm30` → refused at
parse; `science/x` → refused at parse; `testing/entity` compiled with
`testing` → resolves to that term; compiled without it → refused at compile
naming `testing`; `restriction_sort` takes both forms identically.
**Deferred:** none.

### B2 — closes

The consulted walk reaches every sort's contract, and facet namespaces are
collected on their own. Selected: a claim at `crossing/affects-local-entity`,
whose only route to `testing` is slot 1's argument sort (the operator
declares no dimension), consults `{science, crossing, testing}`; a
same-contract operator's set is unchanged from cut 2; a corpus pinning the
operator's contract only → `ContractDisagreement` naming the sort's
namespace; the isolated case consults `biology` through the ledger alone.
**Deferred:** none.

### B3 — closes

`FacetRead` is minted by the corpus reader only, over a dataset it fetched
through the kernel's view of a `nodes` corpus on disk, with the address
derived from that dataset's own declaration. Selected: no public field-wise
constructor; the reader refuses anything but a `ReadView`; `ReadView` is
sealed and final and its constructor refuses any corpus whose exact type is
not `nodes.core.corpus.Corpus`, so neither an overriding subclass nor a view
over a fabricated corpus object mints a row; there is no route that takes an
in-memory node or a caller-supplied address. **The guarantee's edge, stated:**
a `Corpus` over a directory whose records were written behind the kernel's
boundaries is a corpus, and a row read from it is a real read of forged
bytes — the raw-write class S8 names, which the audit's stamp discipline
addresses and B3 does not. **Deferred:** none.

### B4 — closes

Every read is validated, and only held datasets are read. Selected: a
declared facet failing its schema → `Refused("facet-payload-refused…")`; an
undeclared namespaced key → `Refused("facet-undeclared…")`; through `gather`
with an observed dataset node absent from the view → no run input, no
`FacetRead`, no `observes` entry, nothing refuses. **Deferred:** none.

### B5 — closes

Observed facets enter the digest through the one carrier. Selected: payload
byte change, every other member fixed → digest moves; the member is present
and empty when nothing was read; the rows the closure digests are the rows
the walk consumed. **Deferred:** none.

### B6 — closes

The pack ships byte-identical, and TypeScript refuses what Python refuses.
Selected: packaged copy equals `domains/biology/DOMAIN.yaml`; the pack
compiles with the shipped base and declares the floor; the TypeScript
parser refuses own-namespace and `science` references and an unresolved
reference at compile (vitest, run by the acceptance module).
**Deferred:** none.

### B7 — closes

A consulted namespace's pin agrees with the profile. Selected: pins built
from the profile → the walk proceeds; `science` pinned to another identity →
`Refused("profile-pin-mismatch: science")`; a consulted domain pinned to
another revision → refused naming it; an unconsulted domain pinned to
anything → not compared; `evaluate_over` refuses before `evaluate` runs.
**Deferred:** none.

### D6 — closes

The facet arm and the negative's domain-facet instantiation, on the design's
two cases (§5.6): the isolated case (a claim at `testing/affects` over a run
observing a held dataset carrying `biology/gene-axis`; a biology bump moves
the digest, an unrelated activated domain's bump does not, with payload and
assessment bytes fixed) and the dogfood shape (a claim whose slot sort is
biology's, reaching `biology` by both routes), the latter also durable
through `CorpusWriter.add` on the certified tuple. Cut 2's claim-schema,
base-contract, unconditional and negative arms stand and are cited.
**Deferred:** none.

### M8 — arm added, closes

Over a claim at `crossing/affects-local-entity` with no domain facet in the
closure, an editorial `testing` bump leaves `I_claim` unchanged and moves
`belief_input_digest` — reached through slot 1's foreign sort and nothing
else, so dropping the walk's sort-contract collection fails the check.
**Deferred:** none.

### M6 — re-read, not counted

A successor rewriting a namespaced slot is a changed `arg_sorts` and is
refused; the existing succession tests run unchanged plus one over a
namespaced slot. Cited, not counted.

### D1 — part, unchanged

Cut 20's selection stands; the "add a `nodes` code path" negative is
deferred again: it runs in another repository's suite.

### Boundary invariants

No verdict changes. No claim identity changes for a same-contract claim. No
contract identity changes for a document that names no foreign sort.

## 4. Accounting

Nine guarantee rows are read, **9 full/closed** (B1–B7, D6, M8), 1 partial
(D1, unchanged), 1 re-read not counted (M6). The N2 inventory therefore has
**9 declaration units**, one grouped unit per closed row. A grouped unit may
expand into lettered sabotage arms, but it is counted once here and may not
be silently split or merged after the freeze.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 9 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior marked durable in §3 runs through the certified
   engine on the certified kernel and volume tuple, on the volume beside
   the checkout; its portable arms run beside it. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner `tools/cut22_acceptance.py` names
   `cut21_acceptance.py` as its prefix (`PREFIX_RUNNERS =
   ("cut21_acceptance.py",)`), then runs the biology acceptance module and
   the cut-22 N2 audit.
4. `acceptance/n2_arms_cut22.py` declares the sabotage arms: in
   `contract/domain.py` (the own-namespace refusal dropped), in `profile.py`
   (the resolver namespacing a namespaced name; the unresolved-reference
   refusal dropped; the shipped pack read from the base's path), in
   `consulted.py` (the sort-contract collection dropped — cited once by B2
   over the walk and once by M8 over a belief; the facet-namespace
   collection dropped; the `science` agreement dropped; the domain agreement
   dropped), in `facet_read.py` (a field-wise constructor; the corpus-view
   check dropped; re-validation skipped), in `corpus.py` (`ReadView`'s
   exact-corpus check dropped), in `evaluation.py` (an unheld
   observed dataset fetched), in `belief.py` (the ledger taken from nowhere,
   cited by a check that derives a belief; observed addresses dropped from
   the closure nodes), in `closure.py` (the `observed_facets` member
   emptied). `test_n2_cut22.py` audits them by the cut-12 pattern, with the
   staleness probe's baseline taken from the tree.
5. B5's byte-change test changes one payload byte on the observed dataset
   and nothing else; a test that also re-mints the run or the assessment
   exercises nothing. B5's one-carrier half is proved by a check that
   derives a belief, so the walk inside `evaluate` is what the sabotage
   reaches; and `gather`'s consulted set must equal `evaluate`'s over the
   same corpus, asserted by a check of its own.
6. The isolated case's claim schema must not reach `biology`: its operator
   is `testing/affects` and both slots are `testing` sorts. A case whose
   claim reaches `biology` through a sort is the dogfood shape, not the
   proof.
7. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The written review of 2026-09-08 (three findings) is the second reading of
the design; this freeze carries its consequences: B7 and the isolated case
exist because of it, and B4's absent-dataset arm replaces a claim the tree
falsified.

## 7. Limitations

1. B6's TypeScript half runs as vitest checks in the acceptance module, not
   as sabotage arms: the N2 harness mutates the Python package only.
2. The reproduction re-run is the measurement, not an arm; its findings are
   filed to the reproduction record.
3. M6 is re-read, not re-counted.
4. The durable D6 arm is the dogfood shape only; the isolated case is
   portable.
5. B3 authenticates the view, not the bytes: `nodes.core.corpus.Corpus` is
   another repository's class and reads a directory; a directory of forged
   records is a corpus. The exact-type check closes subclassing and
   fabricated corpus objects; forged bytes are S8's and the audit's.
6. The vocabulary snapshot's address and digest checks are the reproduction
   tool's, not the kernel's (design §9 item 12).
