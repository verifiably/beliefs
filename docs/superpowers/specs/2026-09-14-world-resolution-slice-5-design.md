# World resolution, slice 5 — dataset addresses derived from the content identity

**Date:** 2026-09-14
**Status:** draft, awaiting review
**Boundary:** `world-resolution`, the first of its two filed follow-ups (`beliefs-d248ba`); task `beliefs-48214e`
**Lane:** `world-read`, worktree `.worktrees/world-resolution-slice-5`
**Sources:** `../../designs/2026-08-02-world-addressing-design.md` (§2.1, §4.2, §4.4, §7: W1, W2, W3, W8, W16),
`../../designs/2026-08-09-admission-ramp-design.md` (§6.2, §6.4),
`../../designs/2026-08-08-world-address-ruling.md` (§3, §5.1),
`2026-09-10-world-resolution-slice-2b-design.md` (§2, §4, §5.1, §10.2, §10.6, §12),
`../../plans/2026-08-29-implementation-roadmap.md` (Appendix B, concurrency rules)
**Measured against:** `main` at `fb1dac1`

## 1. What this slice is

The baseline below describes `main` at `fb1dac1` before implementation.

A dataset's address is already ruled and already computed. The admission ramp
§6.2 rules the **dataset basis projection**: every declared resource's digest,
normalized to `<algorithm>:<lowercase hex>`, deduplicated, sorted byte-wise,
newline-joined and terminated, sha256'd, and the address is
`dataset:sha256:<hex>`. `dataset.py` implements it as `dataset_address`, and
seven kernel modules read it from a stored declaration today: `closure.py`
keys the belief-input digest's `observes` list by it; `evaluation.py` and
`facet_read.py` ledger observed-facet rows against it; `production.py` mints a
produced dataset's address from a manifest by it (R23); `admission.py`,
`belief.py` and `corpus.py` read it from run inputs. The world index's
`producers` map is keyed by dataset address (world design §5). The mm30
reproduction minted its held dataset at `dataset:sha256:a6bf229e…` by
computing the address and handing it to the builder as the slug
(`python/tools/reproduction/hold.py`).

What has never existed is the check. `stored.dataset_node(slug, *, title,
resources=(), …)` takes an authored slug and mints `dataset:<slug>`; the write
boundary's `_refuse_dataset_basis` refuses a dataset with **no** content
identity (W3, cut 4) and never compares the id it has with the address its
declaration derives. Every test dataset lives at `dataset:d1`, `dataset:raw`,
`dataset:lineage-left` — an id that is a handle, which world design §2.1
forbids ("the address is what the system stores, the handle is what a human
types"). Slice 2b closed exactly this gap for `source` at cut 25 — the builder
lost its slug, the boundary gained `SourceAddressDisagreement` — and filed the
dataset half as this follow-up (§12 there), leaving one choice open: whether
the address stays `dataset:sha256:<fold>` as ruled or becomes a domain digest
like `source:`.

This slice makes that choice, removes the slug from the dataset builder, and
holds every dataset record the boundary admits to its derived address. It
builds no new address and no new seam: a dataset whose bytes change is a new
entity (world design §4.4, first row), so there is no correction history, no
rename, no redirect set and no reconciliation to design. The measured
migration is the slice's bulk, and it is named in §10.2 rather than left to
the plan.

**Rows it closes or reads.** None closes: the ledger's `world-resolution`
entry carries no guarantee row, and cut 25 closed W1 and W2 on their
source-spelled arms. The cut re-reads three rows on their dataset arms — W2
(a shared basis gives one address mechanically), W3 (the builder itself
refuses a mint without a basis) and W8 (a record whose stored id is not its
derived address is an address conflict the boundary refuses) — and leaves
every status where it stands. W8's remainder is unchanged: the
ambiguous-search-term conflict, `authority-labels`.

## 2. Decisions

1. **The address stays `dataset:sha256:<hex>`, as ruled.** The alternative —
   a `v1.digest` under a `science.dataset-address.v1` domain over the sorted
   digest list, uniform with `source:` — was weighed and rejected. The ramp
   §6.2 ruling was made once, in argument, precisely so that no
   implementation would choose a second fold; the fold is live in seven
   modules and in R23's frozen arms; a reproduction corpus already holds a
   record at the ruled form; and changing it would move every closure
   projection, observed-facet ledger row and producers-map key that names a
   dataset, for uniformity alone. The `sha256` in the address is the
   fold's own algorithm tag, not a resource's: it is what lets the accepted
   set (`ACCEPTED_ALGORITHMS`) be widened later without the address form
   changing. Cross-kind collision is not a concern the domain would have
   addressed: a `v1.digest` preimage begins `<domain>\n`, a fold begins
   `sha256:<hex>\n`, and the first line already separates them.
2. **The builder derives the id; the slug parameter is removed.** Slice 2b
   §2 item 1's reasoning carries over unchanged: the builder is the one place
   that already holds the declaration, and 219 call sites each computing the
   address is 219 places to get it wrong. `resources` becomes required and
   the empty default goes: an empty declaration has no address (§6.2, "the
   empty declaration is unreachable"), and a builder that accepts one can
   only refuse it.
3. **The boundary compares, on every path.** `_refuse_dataset_basis` keeps
   its name and its first clause byte for byte — cut 4's W3 arms and cut 25's
   `before` strings match those lines — and gains a second: the stored id
   equals the address the stored declaration derives, else
   `DatasetAddressDisagreement(WriteRefused)`. It is already called from
   `_refuse` and from `_preflight_replace_locked`, so ordinary add, import,
   relocation and replacement are all covered without a new call site.
4. **No seam, no history, no redirect.** A dataset re-held with a different
   manifest is always a new entity (world §4.4). `revise` already preserves
   the `dataset` facet (facet-contracts §5.3; cut 25's W5a-n arm), so an
   admitted record's address cannot drift under it. `consolidate` needs no
   dataset arm of `_reconcile`: two records at one derived address hold one
   declaration by construction, and the source-only `HistoryDisagreement`
   stays source-only. Slice 2b §7's reconciliation follow-up
   (`beliefs-24b42b`) is untouched.
5. **One record per byte set, stated as a consequence.** Two datasets
   declaring the same digests are one address whatever their titles,
   `empirical-observation` facets, domain facets or lineage bases. A second
   add of the same bytes is refused as it is today for any held id
   (`RecordAlreadyMinted` under the same `uid`, `CollisionRefused` under a
   different one); the repair is `revise` for display prose and the
   observation facet, and the lineage basis already unions across producers
   (production §5.2). This is W2 for datasets and it is the point; the
   consequence that a second attester's observation of the same bytes lands
   on the one record, through `revise`'s attester rule, is recorded in §13.
6. **Boundary, not audit.** Like the source check, the comparison runs
   where records are admitted. `corpus_check` and the world audit gain no
   id/address finding for a corpus written outside the boundary; §13 records
   the limitation and it is not filed as work, on the same grounds cut 25
   gave for sources.

## 3. The address

Unchanged. `dataset.dataset_address(declaration) -> str | None` is the ruled
projection and this slice does not touch `dataset.py`. What the slice adds is
the stored-record reader beside the source one:

- `stored.dataset_address_of(node) -> str | None` — `dataset_address` over
  `dataset_declaration(node)`; what the boundary compares `node.id` against.
  `dataset_declaration` already keeps an unpinned resource rather than
  dropping it, so the reader inherits all-or-nothing.

The address's local part is `sha256:<hex>`, which `nodes`' slug grammar
(`[A-Za-z0-9][A-Za-z0-9:_.-]*`) admits, and which the reproduction corpus
already stores on disk as `dataset/sha256__<hex>`.

## 4. The builder and the readers

`stored.dataset_node(*, title: str, resources: Sequence[Mapping[str, Any]],
empirical_observation=None, basis=None, domain_facets=None) -> Node` — the
`slug` parameter is **removed** and `resources` is required. The builder
projects the declaration exactly as the reader will (`name` as text, `digest`
as text or absent), derives the address, refuses `None` with `BasisMissing`
(it cannot mint an id without a basis, and the boundary refuses it again for
hand-built records), and mints `_node("dataset", address.partition(":")[2],
…)`. Its facet handling — the observation facet, the lineage basis facet,
namespaced domain facets refused without a `/` — is unchanged.

`governed_node("dataset", …)` remains the public way to hand-build a dataset
at an arbitrary id; that is what the negative arms use, and the boundary is
what makes the address a guarantee rather than a builder habit.

Readers already in `stored.py` are unchanged: `dataset_declaration`,
`basis_routes`, `inputs_of`. The seven modules that compute the address from
a declaration today keep doing so; routing them through the new reader is
not this slice's work and they are listed as read, not rewritten (§11).

## 5. The write boundary

`_refuse_dataset_basis(node)`, in order:

1. `node.kind == "dataset"` and `dataset_address(dataset_declaration(node))
   is None` → `BasisMissing` — the existing clause, line-identical.
2. `node.kind == "dataset"` and `node.id != dataset_address_of(node)` →
   `DatasetAddressDisagreement(WriteRefused)`, naming the id and the derived
   address.

Paths that reach it, none new: `add` (through `_refuse`); `import_bundle`
(through `_refuse` with `provenance=True`, so a bundle member at a handle
address refuses `ImportRefused` naming the member); relocation's `move` and
`consolidate` (the destination writer's `_refuse`); `replace`-shaped family
writes (`_preflight_replace_locked`). `revise` reaches neither clause and
needs neither: it requires an exact `(uid, id)` match and preserves the
`dataset` facet.

## 6. What this slice measures rather than builds

- **The reproduction lane's records are already at derived addresses.** The
  2026-09-05 record's step 3 minted `dataset:sha256:a6bf229e…` and step 1 of
  the concept vocabulary likewise; `hold.py` and `concepts.py` compute the
  address and pass it as the slug. They lose the slug argument and nothing
  else, and the record is not re-run: cut 29 adds no mm30 measurement.
- **Two attesters, one byte set.** The corpus holds one record per content
  identity, and `_revise_dataset_locked`'s attester rule already governs who
  may change the observation facet on it. No new rule is needed; §13 states
  what a second observer does.

## 7. Refusals, named

| refusal | where |
|---|---|
| `BasisMissing` | builder; `_refuse_dataset_basis` clause 1 (unchanged) |
| `DatasetAddressDisagreement` | `_refuse_dataset_basis` clause 2, on add, import, relocation and replacement preflight |
| `MalformedRecord` (facet key without `/`) | builder (unchanged) |
| `ImportRefused` naming the member | `import_bundle` over either of the above |
| `RecordAlreadyMinted` / `CollisionRefused` | a second add of one byte set (unchanged mechanism, new reach) |

`DatasetAddressDisagreement` sits beside `SourceAddressDisagreement` in
`errors.py`, a `WriteRefused`, documented as the dataset half of the same
defect: the basis is present and canonical; the record lives at the wrong
address, which is what a handle-addressed or hand-edited dataset is.

## 8. Testing and the cut

### 8.1 Unit

`test_stored.py`: the builder derives `dataset:sha256:<fold>` from a pinned
declaration; two declarations differing only in resource order, repetition or
names give one id; an unpinned or empty declaration refuses `BasisMissing`;
`dataset_address_of` agrees with `dataset_address` over the stored facet and
is `None` for a hand-built unpinned record.

`test_corpus_write.py`: a `governed_node("dataset", "handle", …)` with a
pinned declaration refuses `DatasetAddressDisagreement` on `add`; the same
record refuses at replacement preflight; a bundle carrying it refuses
`ImportRefused` naming the member; the builder's record is admitted; a second
add of the same bytes under a new `uid` refuses `CollisionRefused`; `revise`
of the admitted record's observation facet keeps the id.

`test_relocation.py` / `test_relocation_rows.py`: `move` of a
handle-addressed dataset into a boundary-governed destination refuses;
`consolidate` of two records at one derived address in two corpora succeeds
with one address and no redirect (W16's dataset arm over a real derived
address, which the existing test already exercises by slug).

### 8.2 Migration

Measured 2026-09-14 against `main` at `fb1dac1`:

| what | count |
|---|---|
| `dataset_node(` sites in `python/tests` | 217, in 50 files |
| `dataset_node(` sites in `python/tools/reproduction` | 2 (`hold.py`, `concepts.py`) |
| sites passing `resources=` | 143 |
| sites passing a title only, no declaration | 52 — every one adds through a raw `nodes` `Corpus`, bypassing the boundary, in the world-build, relabel, receipt and read-side tests |
| `"dataset:<handle>"` literals in `python/tests` | 768 |
| digest constants shared across records | `"1" * 64` in 27 places, `"2" * 64` in 16, `"a" * 64` in 15, `"0" * 64` in 13, `"d" * 64` in 12 |

The migration is one pattern, applied everywhere: a record's id is what the
builder returns, and a closure's or relation's dataset reference is that id.
Its instrument is a small shared helper module, `python/tests/dataset_fixtures.py`:
`pinned(seed: str) -> list[dict]` gives a one-resource declaration whose
digest is a deterministic function of the seed, so `pinned("d1")` and
`pinned("d2")` are two byte sets; `dataset_ref(seed) -> str` is the address
that declaration derives, so a fixture can name a dataset before building it
(closure recipes, relation targets, lineage routes). Every `dataset_node(`
site loses its slug and, where it passed no declaration, gains
`resources=pinned(<old slug>)`; every `"dataset:<handle>"` literal becomes
the built node's `id` or `dataset_ref(<handle>)`; every fixture that gave two
records one shared digest constant gives them two seeds unless the test is
about one byte set in two places (W16, R23 negative (a)), where the shared
constant is the point and stays.

Closure fixtures move with their datasets: `durable_fixture.py`'s `RAW`,
`DERIVED` and the eight `LINEAGE_*` constants, `verification_fixtures.py`'s
`PINNED` and `mint_datasets`, `test_audit.py`'s `add_observed_datasets` and
`test_read_side.py`'s `observed_dataset` all define their references through
`dataset_ref`. No test pins a literal derived identity of a run, assessment
or verification (measured: zero), so recomputed closure addresses break no
expectation by value.

The on-disk fixture in `test_domain_boundary.py` (`id: dataset:gene-expression-matrix`)
and its copy in `../plans/2026-09-12-d1-cross-repository-negative.md` are
raw corpus documents; they migrate to the derived id only if they cross the
boundary, which the plan verifies rather than assumes.

The two reproduction tool sites drop `address.removeprefix("dataset:")` and
keep the address they already compute as the value they report.

### 8.3 Acceptance

`python/tests/acceptance/test_dataset_address_acceptance.py`, on the
certified volume, one function per arm:

- **W2, dataset:** two writers in two corpora each build a dataset from the
  same declaration under different titles and observation attesters; assert
  one address; assert order, repetition and name changes give the same
  address; assert a one-digest change gives a different one; publish the
  world and assert the producers map and a run's `observes` closure name the
  derived address. Negative: a declaration under an unaccepted algorithm
  refuses `BasisMissing` at the builder and again at the boundary for a
  hand-built record.
- **W3, builder arm:** `dataset_node` with an empty or unpinned declaration
  refuses before any write; a declared-not-held dataset is minted (the
  narrowed arm, unchanged).
- **W8, address conflict:** a `governed_node` dataset at a handle refuses
  `DatasetAddressDisagreement` on add, at replacement preflight, on import
  naming the member, and on `move` into a governed destination; the same
  bytes at the derived address are admitted; `consolidate` of two records at
  one derived address gives one address and no redirect.

### 8.4 N2 sabotages

`n2_arms_cut29.py`, one exact source site per arm, each named to an
independent function above. Mechanisms, and the module each lives in:

| unit | mechanism removed or weakened | module |
|---|---|---|
| W2 | builder derives the id from the declaration (replaced by the title) | `stored.py` |
| W2 | `dataset_address_of` reads the stored declaration (replaced by `node.id`) | `stored.py` |
| W3 | builder refuses a `None` address before minting | `stored.py` |
| W8 | id/derived-address agreement on `add` | `corpus.py` |
| W8 | agreement at replacement preflight | `corpus.py` |
| W8 | agreement under import provenance | `corpus.py` |

The plan fixes the count; every arm passes without its mutation and fails
with it; stale, vacuous, mixed and uncollected arms refuse.

### 8.5 The cut

Conformance cut 29, numbered after cut 28 (no other worktree claims 29;
`design/composite-claim`, `design/estimand-typing` and the detached
`audio-baseline` checkout were searched), `python/tools/cut29_acceptance.py`
with `PREFIX_RUNNERS = ("cut28_acceptance.py",)` and
`PHASE_MODULES = ("test_dataset_address_acceptance.py", "test_n2_cut29.py")`.
Declaration units `W2`, `W3`, `W8`, single-homed. Accounting: no row closes;
W2 and W3 are re-read on dataset arms with their closed status unchanged; W8
is read on its address-conflict conflict and stays part on its
ambiguous-search-term conflict. `roadmap_status.py` gains
`29: ("conformance-cut-29-results §2", "", "W8")`. Frozen by dated commit
after review.

### 8.6 Frozen evidence and live tests

Cut documents, declaration tables and `n2_arms_cut*.py` bodies of cuts 4–28
are not edited. Three frozen surfaces touch this slice:

- **Cut 4's W3 arms and cut 25's `before` strings** match the first clause of
  `_refuse_dataset_basis` and the two lines that call it. Decision 3 keeps
  those lines byte-identical; the second clause is appended below them. The
  staleness audit compares measured staleness with the registered set, never
  with an empty one; this slice adds nothing to the registry, and the arms
  registered stale on `main` today stay exactly as registered.
- **Cut 7's `INTERPOSED_WRITE`** is a frozen sabotage fragment that calls
  `stored.dataset_node(<uuid hex>, title="interposed")` inside the sabotaged
  `test_world_build.py`. `test_n2_cut7.py` runs it live
  (`test_relocation_alone_passes_the_witness_and_the_interposed_write_fails_it`),
  and under the new signature the fragment would raise `TypeError` — failing
  the witness for the wrong reason and scoring the arm vacuously. The
  declaration `n2_arms_cut7.py` stays frozen; `test_n2_cut7.py` gains a
  **dated live adapter** on cut 16's `_LIVE_SABOTAGES` pattern that
  substitutes an equivalent live interposed write — a dataset built from a
  uuid-seeded pinned declaration — before the arm is applied, and the
  frozen-text assertions over the declaration are untouched. This is the
  M3a precedent of slice 2b §10.6, and it is named here so the plan does
  not discover it.
- **Live phase modules of earlier cuts** that build datasets —
  `test_n2_cut5.py`, `test_n2_cut7.py`, `test_durable_corpus.py`,
  `test_facet_acceptance.py`, `test_relocation_acceptance.py`,
  `test_coreference_acceptance.py`, `test_source_address_acceptance.py`,
  `test_world_view_acceptance.py`, `test_world_audit_acceptance.py`,
  `test_world_selection_acceptance.py`, `test_durable_traversal.py`,
  `test_durable_records.py`, `test_session_acceptance.py`,
  `test_deletion_acceptance.py`, `test_cut15_lineage.py` and
  `durable_fixture.py` — receive the §8.2 fixture migration and nothing
  else.

## 9. Shared files, under roadmap concurrency rule 3

Rewritten by this lane and named here: `errors.py`,
`python/tests/test_designs_corpus.py` (the README's design count and newest
date move with the cut document), the ledger, the roadmap, `README.md`,
`docs/guide/identity-world-and-change.md`, `docs/guide/glossary.md`
(a **Dataset address** entry beside **Source address**),
`docs/guide/contracts-and-adoption.md` and `docs/guide/foundations.md` (the
"through cut 28" sentences), `python/tools/roadmap_status.py`. Of the
`mutation` lane's surface, `corpus.py` is rewritten at one method; no other
lane is open. `stored.py` and the test corpus are this lane's.

Dated notes, not rewrites: world design §4.2's dataset row ("the stored id is
held to the address at the write boundary from cut 29"); slice 2b §12 item 1
(built at cut 29); the admission ramp is not amended — its ruling stands as
made.

## 10. Task linkage

`beliefs-48214e` carries this spec; the implementation plan's tasks become its
children. `beliefs-24b42b` (divergent-history reconciliation) is the lane's
next boundary and is not a prerequisite. `beliefs-d248ba` stays open until
both follow-ups discharge.

## 11. Limitations and open questions

1. **Boundary-only.** A corpus written outside the write boundary — a raw
   `nodes` corpus, or one hand-edited on disk — can hold a dataset at a
   handle address, and neither `corpus_check` nor the world audit reports it.
   The source check has the same bound since cut 25 and it is stated there
   the same way. It becomes work only if a lane needs the audit arm; none
   does today.
2. **A second observer of one byte set edits, not adds.** The record is per
   content identity and the `empirical-observation` facet is per record, so
   an attester who holds the same bytes a first attester declared reaches the
   record through `revise`, under `_revise_dataset_locked`'s attester rule (a
   changed declaration names the current actor). A per-attester observation
   history is not designed; the holdings observation records (cut 10) carry
   the per-observer evidence, and that is where the second observation lives.
3. **The accepted-algorithm set is still `{"sha256"}`.** Widening it is the
   profile's ruling (ramp §6.2) and changes which declarations have an
   address, not the address form.
4. **The fold's own algorithm is fixed.** `dataset:sha256:` names the fold's
   sha256, and a future accepted resource algorithm does not change it; a
   change to the fold algorithm itself would be a new address form and a
   new ruling.

## 12. Review log

None yet.
