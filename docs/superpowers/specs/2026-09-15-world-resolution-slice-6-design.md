# World resolution, slice 6 — reconciling divergent correction histories at `consolidate`

**Date:** 2026-09-15
**Status:** draft, under review; not frozen
**Boundary:** `world-resolution`, the last of its filed follow-ups (`beliefs-d248ba`); task `beliefs-24b42b`
**Lane:** `world-read`, worktree `.worktrees/world-resolution-slice-6`
**Sources:** `2026-09-10-world-resolution-slice-2b-design.md` (§5.2, §6, §7, §8, §12, §13),
`../../designs/2026-08-02-world-addressing-design.md` (§4.4, W5a),
`../../designs/2026-08-08-world-address-ruling.md` (§4.2),
`../../designs/2026-09-03-world-changing-families-design.md` (`consolidate`),
`../../plans/2026-08-29-implementation-roadmap.md` (Appendix B, concurrency rules)
**Measured against:** `main` at `6f08418`

## 1. What this slice is

The baseline below describes `main` at `6f08418` before implementation.

Slice 2b gave a `source` record an attributed correction history: a **linear
chain** of `{from, to, actor, grounds, event_token}` entries under
`identifier-correction`, continuous (`entries[i].to == entries[i+1].from`),
ending at the current identifier map, and deriving the record's redirect set
exactly (`deprecated_ids == sorted(held(history) − {id})`, one validator,
`stored.validate_source_history`). Two replicas of one record in two corpora
that were corrected independently are two branches from a common origin, and
a chain cannot hold two branches. So `consolidate` **refuses** them —
`HistoryDisagreement`, slice 2b §7 — rather than keep the survivor's chain
and silently drop the addresses the other replica held. The refusal cannot be
escaped by the operator: any `correct_identifier` on either side widens the
difference.

This slice makes the two branches one record without losing an event or an
address. The survivor's chain is the spine; the other replica's divergent
suffix is **absorbed** into one new entry of the same facet, verbatim, so
every correction keeps its actor, grounds and token, and the redirect set the
validator derives is exactly the union both replicas held. Where one chain is
a prefix of the other nothing was asserted beyond what one side already
records, and the survivor adopts the longer chain outright. Identifier maps
that differ still refuse: an identifier change is a correction's assertion,
attributed under `grounds` by `correct_identifier`, never a side effect of
`consolidate` under `rationale`.

No guarantee row is read. The slice discharges `world-resolution`'s last
filed follow-up and closes the boundary.

## 2. Decisions

1. **Maps must agree; histories reconcile.** `consolidate` keeps refusing two
   replicas whose current identifier maps differ, and the refusal now names
   the schemes that differ. The seam's own precedent (2b §6.1 step 5: it
   does not canonicalize on the caller's behalf) applies: the operator runs
   `correct_identifier` on one side first, so the change is attributed.
2. **The spine is `keep`'s chain.** `consolidate` already asks the caller to
   name the survivor; the survivor's history is the spine and the other
   replica's divergent suffix is what gets absorbed. Swapping `keep` swaps
   the roles and yields a different — equally valid — record.
3. **One facet, one new entry kind.** A *consolidation entry* lives in the
   same `entries` list, with the same five keys plus `absorbed`. The chain
   stays linear; the absorbed suffix is a chain nested in one entry. No DAG,
   no second facet, no change to `correct_identifier`'s append rule.
4. **Prefix is a fast-forward.** When one chain is a prefix of the other
   (entry-for-entry equal), no entry is minted: the merged history is the
   longer chain. Equal chains stay the identity `_reconcile` is today.
5. **One token is one event.** Within one chain — the spine, or one
   `absorbed` list — tokens are distinct, as 2b §5.2 has it. Across chains
   a token may recur only as the *same* event, byte-identical content
   (`absorbed` included): an event that reached the survivor by two paths
   (a third replica absorbed through two intermediaries) is one event twice
   recorded, not a collision. One token under two contents is a conflicting
   reuse and is malformed. The reconciliation function (§4) never absorbs an
   event the survivor already holds, so an interrupted `consolidate` re-run
   over the already-reconciled survivor is the identity — the families
   design's recovery contract (`consolidate` steps 2–4: "re-run
   `consolidate`; the idempotent union is what makes a re-run safe").
6. **The entry carries the operation's token.** A consolidation entry's
   `event_token` is the token of the `consolidate` intent whose data
   transaction wrote it; `actor` is the consolidating actor and `grounds` is
   `rationale`. On an uninterrupted run the entry, both act-reports and both
   intents share the value. After an interruption between steps 4 and 5 the
   re-run mints a fresh token (the families design: a re-run is a new
   operation and closes nothing), absorbs nothing further, and its reports
   carry the new token while the entry keeps the interrupted operation's —
   truthfully: that operation is the one that wrote it.
7. **`Consolidated` is unchanged.** The act-report already names both
   corpora, both ids and the rationale; the record itself shows what was
   absorbed. Nothing is added to `report.py`.
8. **No frozen text moves.** Cut 28's `W8-b` anchor
   (`            if keep_map != other_map:`) and cut 29's dataset arms in
   `relocation.py` stay byte-identical. Cut 25's `W5a-m` asserts the refusal
   this slice retires; its frozen declaration is not edited and the live
   guard re-targets it (§7.5).

## 3. The entry and the validator

### 3.1 Payload

`identifier-correction` stays `{"entries": [entry, ...]}`. Two entry kinds:

| kind | keys, exactly | `from` vs `to` | minted by |
|---|---|---|---|
| correction | `from, to, actor, grounds, event_token` | `from != to` | `correct_identifier` (2b §6) |
| consolidation | `from, to, actor, grounds, event_token, absorbed` | `from == to` | `consolidate` (§5) |

`absorbed` is a non-empty list of entries — either kind, so a record
consolidated twice nests twice — that is itself a well-formed chain whose
last `to` equals the consolidation entry's `from`. Its first `from` is
unconstrained: two independently authored replicas share no origin map, and
a fork from a shared copy is provenance the chain records, not a clause the
validator checks.

### 3.2 Well-formed history, amended

2b §5.2's clauses hold, read over the new shape:

- `entries` non-empty; absence of the facet is the no-history state.
- Each entry's keys are exactly one of the two sets above. `from` and `to`
  are validated through `normalize`, both non-empty; `actor`, `grounds`,
  `event_token` non-empty strings; the whole entry canonically encodable
  under `science.identity.v1` (the `absorbed` list included).
- A correction entry has `from != to`. A consolidation entry has
  `from == to` and a non-empty `absorbed` — the two clauses together are
  "`from == to` iff `absorbed` is present", and a five-key entry with equal
  maps or a six-key entry with unequal maps is malformed.
- **Continuity** on the spine as before; a consolidation entry continues
  trivially. **Absorbed continuity:** each `absorbed` list is continuous and
  its last `to` equals its entry's `from`. Both recursively.
- **Tokens:** distinct within each chain (the spine; each `absorbed` list),
  recursively. Across chains, every occurrence of one token is the same raw
  entry (deep equality, `absorbed` included); one token under two contents
  is malformed ("conflicting token reuse").
- **Redirect agreement:** `held` is the set of `source_address(m)` over every
  `from` and `to` in the spine *and* every absorbed chain, recursively;
  `set(deprecated_ids) == held − {node.id}`, sorted, no duplicates.

**One validator, unchanged in name.** `stored.identifier_corrections` reads
and validates the shape (recursing into `absorbed`);
`stored.validate_source_history` adds redirect agreement;
`stored.held_source_addresses` recurses. Every promised entry point still
invokes the one validator — `_refuse_source` on every write path,
`validated_node`, the check view's finding loop — and none re-derives a
clause. `add` still refuses the facet; `import_bundle` admits a well-formed
history, nested or not, as provenance; `correct_identifier` still requires
the successor's entries to be the current entries plus exactly one
correction entry (a consolidation entry earlier in the spine is ordinary
history to it).

### 3.3 The reader's value

`IdentifierCorrection` gains one field:

```python
@dataclass(frozen=True)
class IdentifierCorrection:
    from_identifiers: Mapping[str, str]
    to_identifiers: Mapping[str, str]
    actor: str
    grounds: str
    event_token: str
    absorbed: tuple[IdentifierCorrection, ...] = ()   # non-empty iff a consolidation entry
```

Existing readers and tests that construct or compare `IdentifierCorrection`
values are unchanged: a correction entry reads with `absorbed == ()`.

## 4. The reconciliation function

`stored.reconcile_correction_histories(keep: Sequence[Mapping], other: Sequence[Mapping], *, actor: str, grounds: str, event_token: str) -> list[dict]`

A pure function over the two replicas' raw `entries` lists (an absent facet
is `[]`), called by `consolidate` after both records have been read through
`validated_node` (so both chains are well-formed) and after the map check
(so both end at one map, `current`). Let `events(chain)` be the map
`token → raw entry` over the chain and, recursively, every `absorbed` list
in it.

1. **Conflict.** For every token in `events(other)` also in `events(keep)`,
   the two raw entries must be deeply equal; otherwise refuse
   `HistoryDisagreement` naming the token ("conflicting token reuse").
2. **Fast-forward.** If `keep`'s spine is a prefix of `other`'s spine
   (entry-for-entry equal; the empty spine included), return `list(other)`.
   Equal spines are the identity.
3. **Remainder.** `remainder = [e for e in other if e["event_token"] not in events(keep)]`
   over `other`'s spine. If it is empty, return `list(keep)`: every event
   `other` records the survivor already holds — `other` is a prefix, or
   `other` is what an interrupted run already absorbed.
4. **Tail.** `remainder` must be a contiguous tail of `other`'s spine
   (`remainder == other[len(other) − len(remainder):]`); otherwise refuse
   `HistoryDisagreement` ("held events interleave unheld ones"). A governed
   chain cannot produce this — an event is minted after, or absorbed with,
   its predecessors — so it reaches only a raw-imported history, and it is
   refused rather than reordered.
5. **Absorb.** Return
   `[*keep, {"from": current, "to": current, "actor": actor, "grounds": grounds, "event_token": event_token, "absorbed": remainder}]`.
   The tail is continuous and ends at `current`, so the entry validates.

**Idempotence.** `reconcile(reconcile(K, O), O)` is `reconcile(K, O)` in
every branch: after a fast-forward the spines are equal (step 2); after an
absorb every event of `O` is in `events(keep)` (step 3). That is the
re-run-after-interruption guarantee §5 relies on.

The result is written as the facet when non-empty and the facet is removed
when empty (step 3 with two history-free replicas). `deprecated_ids` are not
computed here: `_reconcile`'s union of the two replicas' `deprecated_ids`
equals `held(result) − {id}` in every branch — every map of `other` is in
the spine, in `absorbed`, or already held — and `_preflight_replace_locked`
holds the merged record to that through the one validator, as it holds every
replacement. The function neither reads `deprecated_ids` nor mints a token;
the caller passes the intent's.

## 5. `consolidate`

The envelope of 2b §7 and the world-changing-families design is unchanged —
both locks, `_require_pins_agree` on both, same-root, both targets present,
excluded kinds, `AddressDisagreement`, then the kind-specific input checks.
For `source`, in order:

1. `keep_map != other_map` → `HistoryDisagreement`, message naming
   `sorted(set(keep_map.items()) ^ set(other_map.items()))`'s schemes. The
   line is cut 28's `W8-b` anchor and does not move.
2. *(removed)* the history-equality refusal.
3. `intent = OperationIntent("consolidate", secrets.token_hex(16), actor)`
   **and** the `Consolidated` outcome are constructed **here**, before the
   merge — the intent so the entry can carry its token, the outcome so
   `rationale`'s own validation (`_require_str`: non-empty, canonically
   encodable, `MalformedRecord`) still fires before the value reaches the
   facet, and `test_consolidate_validates_both_reports_before_either_intent`
   keeps its refusal class. The intent is still appended to either root only
   after every preflight, as today.
4. `entries = stored.reconcile_correction_histories(keep_entries, other_entries, actor=keep_writer.authority.actor, grounds=rationale, event_token=intent.event_token)`.
5. `_reconcile(keep_node, other_node, correction_entries=entries)` — the
   existing merge (relations, `deprecated_ids` union, lineage bases,
   re-stamp), plus: for `source`, the facet set to `{"entries": entries}` or
   removed when `entries` is empty. `correction_entries` is `None` for every
   other kind and the facet is untouched.

Then the dataset checks, `_refuse_contract_disagreement`,
`_preflight_replace_locked(merged, provenance=True)` — which runs
`_refuse_source` and so the amended validator over the merged record — the
operation-port preflights, permits, reports, intents, the replace/delete
pair, and both publications, exactly as today. §4's refusals (steps 1 and 4) are
`HistoryDisagreement` before any intent; a merged record the validator
nevertheless refuses is `ValidationRefused` from the preflight: before either
intent, no effect in either root, cut 19's J2 as every relocation refusal.

**Interruption.** The families design's table stands: interrupted after its
step 4 (`keep` replaced, `other` not deleted) the world is still a duplicate
location and the recovery is to re-run `consolidate`. The re-run reads the
already-reconciled survivor as `keep`, finds every event of `other` held,
returns the survivor's chain unchanged (§4 step 3), and completes the
deletion and the reports under its own fresh token. Nothing is absorbed
twice.

`rationale` becomes the consolidation entry's `grounds`; step 3 validates
it through `Consolidated` before the merge, so an empty or non-encodable
rationale refuses `MalformedRecord` as today and never reaches the facet.

`move` carries a nested history across roots unchanged; `delete` retires the
record and its redirect set with it; `supersede` and `revise` still do not
reach `source`.

## 6. Refusals, named

| refusal | where | change |
|---|---|---|
| `HistoryDisagreement` | `consolidate`: identifier maps differ; conflicting token reuse; held events interleaving unheld ones (§4 steps 1, 4) | the history-equality case is retired; the three remaining cases each name what differs; class and name unchanged (cut 28 `W8-b` imports it) |
| `MalformedRecord` | `identifier_corrections`, `validate_source_history` | new clauses: key set per kind, `from == to` iff `absorbed`, absorbed continuity and end, token distinctness across chains, held over chains |
| `ValidationRefused` over `MalformedRecord` | `_refuse_source` on every write path, `consolidate`'s preflight included | unchanged mapping |
| `FacetPayloadRefused` / `facet-payload-malformed` | `validated_node`, the check view | unchanged mapping, new clauses reach it |
| `ImportRefused` naming the member | `import_bundle` over any of the above | unchanged |

No new exception class. Two well-formed chains ending at one map reconcile
unless they disagree about what one token names or a raw-imported chain
interleaves held and unheld events.

## 7. Testing and the cut

### 7.1 Unit

`tests/test_source_address.py::TestReaders`, extended — the reader over the
new shape, each a `MalformedRecord`: a six-key entry with `from != to`; a
five-key entry with `from == to` (the existing clause, kept); an empty
`absorbed`; an absorbed chain that is not continuous; an absorbed chain whose
last `to` is not the entry's `from`; a token repeated within the spine; a
token repeated within one absorbed chain; a token shared between the spine
and an absorbed chain under **different** content (conflicting reuse,
malformed) and under **identical** content (one event by two paths: reads);
a non-encodable grounds inside an absorbed entry; a nested consolidation
entry inside `absorbed` (well-formed, reads); `held_source_addresses` over a
nested history returns every address once; `validate_source_history` refuses
a `deprecated_ids` that omits an absorbed address and one that adds an
underived address.

`tests/test_source_address.py::TestReconcile` (new) —
`reconcile_correction_histories` as a table: equal chains → identity (same
list, no entry); `keep` a proper prefix → `other`'s chain; `other` a proper
prefix → `keep`'s chain; both empty → `[]`; one empty, one not → the
non-empty one; divergent after a common prefix of length `k` → spine plus one
consolidation entry absorbing exactly `other[k:]`; divergent with no common
prefix → absorbs all of `other`; **already absorbed** (`keep` =
`[a, m(absorbed=[b])]`, `other` = `[b]`) → `keep` unchanged; **absorbed then
corrected** (`other` = `[b, e]`) → absorbs `[e]` only; **diamond** (`other`
= `[c, m2(absorbed=[b])]`, `keep` holding `b`) → absorbs both, `b` twice
identically; **conflicting reuse** (`other`'s `b'` shares `b`'s token under
other grounds) → `HistoryDisagreement` naming the token; **interleaved**
(`other` = `[x, b, y]`, `keep` holding `b` but not `x`) →
`HistoryDisagreement`; idempotence on every merging row
(`reconcile(reconcile(K, O), O) == reconcile(K, O)`); the entry's `from`,
`to`, `actor`, `grounds`, `event_token` are the arguments' values; the
function does not read or write `deprecated_ids`.

`tests/test_identifier_correction.py::TestRelocation`, amended —
`test_consolidate_refuses_divergent_histories` is **replaced** by
`test_consolidate_absorbs_divergent_histories`: two writers add one source,
each corrects it A→B under its own grounds (two tokens, divergent), and
`consolidate` yields a survivor whose history is `keep`'s entry followed by
one consolidation entry absorbing `other`'s entry with the intent's token as
`event_token`, `rationale` as `grounds` and the actor; `deprecated_ids ==
[ADDR_A]`; `keep`'s corpus resolves `ADDR_A` to the survivor; `other`'s
corpus resolves nothing; the two act-reports carry the same token. The
mirror with `keep` swapped absorbs the other entry. Then:
`test_consolidate_fast_forwards_a_prefix` — a replica imported before a
correction lands has a *different* current map and refuses at the map check,
so the fixture is a **round trip**: both corpora hold the record at `B`,
`other` is corrected `B→C` then `C→B`, both maps are `B` again, `keep`'s
empty spine is a proper prefix, and the survivor adopts `other`'s two-entry
chain with no consolidation entry and `deprecated_ids == [ADDR_C]`, which
`keep`'s corpus then resolves to the survivor;
`test_consolidate_retries_after_an_interrupted_replacement` — `other`'s
`_delete_locked` is monkeypatched to raise once, after `keep`'s replacement
has landed (families design step 4); `keep` then holds `[a, m(absorbed=[b])]`
and `other` still holds `[b]`; the re-run under a fresh rationale completes:
the survivor's `entries` are byte-identical to the first run's, `other` is
deleted, the re-run's two reports carry its own token and the entry keeps
the first run's; `test_consolidate_of_equal_histories_is_the_identity`
(the existing byte-identical-replica case, asserted on the entries list);
`test_consolidate_of_history_free_replicas_carries_no_facet`;
`test_correct_identifier_appends_after_a_consolidation_entry` (the seam's
plus-exactly-one rule over a spine that ends in a consolidation entry);
`test_move_carries_a_nested_history`; `test_consolidate_twice_nests`
(a survivor absorbed once is consolidated against a third replica and the
absorbed chain contains the earlier consolidation entry);
`test_consolidate_refuses_conflicting_token_reuse` (`other` raw-imported with
`keep`'s token under other grounds: `HistoryDisagreement` before either
intent, no file effect in either root).
`test_divergent_identifier_maps_refuse_consolidation` stays and gains an
assertion on the schemes the message names.

`tests/test_identifier_correction.py::TestTheBoundary`, extended —
`import_bundle` admits a nested history as provenance and refuses a malformed
nested one naming the member; `add` still refuses the facet.

`tests/test_relocation.py` — unchanged: the token-reuse refusal is
`consolidate`'s own (§4 step 1) and is tested beside the other
`HistoryDisagreement` cases above.

`tests/test_world_conflicts.py` — unchanged; its `HistoryDisagreement` case
is the map case.

### 7.2 Acceptance

`tests/acceptance/test_source_address_acceptance.py::test_lifecycle_move_consolidate_delete`
— the divergent case at its end is rewritten from a refusal to the absorb
and read back through the check view (`corpus_check` reports nothing on the
survivor) and the world read view at a published epoch (the retired address
resolves to the survivor in `keep`'s corpus; the address map carries it).
`test_failure_boundary_refusals_and_applied_prefixes` gains a `consolidate`
halt after the families design's step 4, positioned as
`correction_halt_positions` derives its positions — from what the halting
backend observes, never from a guessed count — and asserts the duplicate
location, then the re-run's completion with the survivor's entries unchanged.

`tests/acceptance/test_world_selection_acceptance.py` — unchanged; its
`HistoryDisagreement` case is the map case (cut 28 §W8).

### 7.3 N2 sabotages

Declared in `tests/acceptance/n2_arms_cut30.py`, one declaration unit
`W5a` (the row is closed; these are re-reads on the reconciliation arm and
close nothing new):

| arm | asserts | sabotage | check |
|---|---|---|---|
| `W5a-p` | divergent histories are absorbed, not dropped | `reconcile_correction_histories` step 5 returns `list(keep)` | `test_consolidate_absorbs_divergent_histories` |
| `W5a-q` | the absorbed chain is validated | `identifier_corrections` skips recursion into `absorbed` | the absorbed-not-continuous reader test |
| `W5a-r` | held addresses reach into absorbed chains | `held_source_addresses` does not recurse | the omitted-absorbed-address validator test |
| `W5a-s` | one token is one event across chains | the cross-chain content comparison removed | the conflicting-reuse reader test |
| `W5a-x` | an already-held event is not absorbed again | step 3 absorbs `other`'s whole spine | `test_consolidate_retries_after_an_interrupted_replacement` |
| `W5a-y` | reconciliation refuses conflicting reuse before any intent | step 1 removed | `test_consolidate_refuses_conflicting_token_reuse` |
| `W5a-t` | a consolidation entry changes nothing | the `from == to` iff `absorbed` clause removed | the six-key-unequal and five-key-equal reader tests |
| `W5a-u` | the entry carries the operation's token | `consolidate` passes `secrets.token_hex(16)` instead of `intent.event_token` | the absorb test's token assertion |
| `W5a-v` | a prefix fast-forwards without an entry | step 2 falls through to step 5 | `test_consolidate_fast_forwards_a_prefix` |

The map refusal is not re-declared: cut 28's `W8-b` guards it live and its
anchor does not move.

Each sabotage is a byte-exact `before`/`after` on a line this slice writes;
the plan pins the strings once the code exists, and `arm_staleness` audits
them against the tree.

### 7.4 The cut

Cut **30**, subject to concurrency rule 1's scan of every worktree at freeze
(`cut-number-check-scans-every-worktree`): the highest claimed today is 29 on
`main`, and neither design worktree has claimed one. Frozen document
`docs/designs/2026-09-15-conformance-cut-30.md` on this branch before
implementation; guard `tests/acceptance/test_n2_cut30.py` pinning the freeze
commit and the frozen §§2–7 digest; runner `python/tools/cut30_acceptance.py`
on cut 29's shape; results record
`docs/plans/2026-09-15-conformance-cut-30-results.md` at discharge on the
certified volume, merged `--no-ff`. Selection: no guarantee row is read
(`W5a` is closed at cut 25 and stays closed; `W8` stays partial on its
ambiguous-search-term conflict, unchanged); the accounting is 0 newly closed
and the boundary `world-resolution` leaves the ledger table and the roadmap's
boundary index, as `nodes-remainder` did.

### 7.5 Frozen evidence and live tests

Cut documents, declaration tables and `n2_arms_cut*.py` bodies of cuts 4–29
are not edited. Three frozen surfaces touch this slice:

- **Cut 25's `W5a-m`** ("consolidation refuses divergent correction
  histories") is anchored on the history-equality `if` this slice removes,
  and its check `test_consolidate_refuses_divergent_histories` is replaced.
  The frozen tuple in `n2_arms_cut25.py` stays byte-identical;
  `test_n2_cut25.py`'s live table (`_LIVE_SABOTAGES`, cut 16's pattern,
  already used there for `W1-a`) gains a dated `W5a-m` re-target whose
  `asserts`, `sabotage` and `checks` are `W5a-p`'s — the successor
  discharge, cited by this cut's document. `arm_staleness.audited_arms`
  measures the live tuple, so the registry gains nothing.
- **Cut 28's `W8-b`** anchors `            if keep_map != other_map:` and
  imports `HistoryDisagreement`; both are unchanged (decision 8).
- **Cut 29's dataset arms** in `relocation.py` are below the source block
  and are unchanged.

Every other live test that builds a `source` history (`test_source_address.py`,
`test_identifier_correction.py`, the acceptance modules above,
`test_world_audit_acceptance.py`) reads correction entries with
`absorbed == ()` and is unchanged unless §7.1 names it.

## 8. Shared files, under roadmap concurrency rule 3

Rewritten by this lane, from the roadmap's shared-surface columns:
`python/src/beliefs/errors.py` (a docstring only), `python/tests/test_designs_corpus.py`
(the design-count guard), the ledger, the roadmap, `docs/guide/README.md`.
From the `world-read` column: `relocation.py`, `stored.py`, `corpus.py`
(`_refuse_source`'s docstring). No file from `mutation`'s or `acquisition`'s
columns. The two design worktrees (`estimand-typing`, `composite-claim`) are
parked and rewrite none of these today; the later merge resolves toward the
earlier one.

## 9. Task linkage

`beliefs-24b42b` carries this spec; the implementation plan's tasks become
its children. Its parent `beliefs-d248ba` (`world-resolution`) has no other
open child and closes with it at discharge, when the ledger and roadmap drop
the boundary. Dated notes: slice 2b §7 and §12 item 2 (built at cut 30);
world design §4.4's W5a text (consolidation absorbs); the ledger's `Current
state`; the roadmap's re-rank (§Lanes: `world-read` head becomes
`event-level-l8`; tier 1 on-path becomes empty, so rule 6 admits off-path
lanes — the estimand-typing lane's Task 0 re-reads it).

## 10. Limitations and open questions

1. **Reconciliation is by `keep`.** Two orders give two valid records with
   different spines; neither is more true. The act-report records which was
   chosen and why (`rationale`).
2. **Conflicting token reuse refuses, with no seam to repair it.** Two
   independently minted 16-byte tokens colliding under different content is
   not a designed case; it refuses `HistoryDisagreement` before any intent,
   and the operator has no seam to change a token. Accepted.
3. **A blocked address is still not released** (2b §13 item 1); absorption
   only widens the redirect set, never narrows it.
4. **Map merge is not offered** (decision 1). An operator consolidating two
   replicas whose lower-precedence identifiers differ runs one
   `correct_identifier` first; the refusal names the schemes so the call is
   evident.
5. **The absorbed fork point is provenance, not a clause** (§3.1). A chain
   whose absorbed suffix begins at a map no spine entry ever held is
   well-formed; the validator cannot tell an independent origin from a
   corrupted fork, and does not try.

## 11. Review log

- **2026-09-15, first review, two findings taken.** (P1) The prefix-based
  merge re-absorbed `other`'s chain on a re-run after an interruption between
  the families design's steps 4 and 5, and the one-set token rule then
  refused the survivor — breaking that design's recovery contract, and
  likewise for an imported copy of an absorbed chain. Decision 5, §3.2 and
  §4 are rewritten: one token is one event (identical content may recur
  across chains; different content is conflicting reuse), reconciliation
  absorbs only events the survivor does not hold, and idempotence over an
  already-reconciled survivor is stated and tested (unit and acceptance
  retry-after-replacement). (P2) The fast-forward fixture "imported before a
  correction landed" leaves the maps unequal and refuses at the map check;
  it is now a `B→C→B` round trip, which tests adoption of `C`'s redirect.
