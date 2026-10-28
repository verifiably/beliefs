# Overlapping publications: one address held in several live corpora

**Status:** draft for the user's review; not accepted.
**Task:** beliefs-918fd2 (child of beliefs-a286e7; beliefs-81367e and sci-4a3543 wait on it).
**Brief:** `../../notes/2026-10-09-overlapping-publications-brief.md`.
**Baseline:** beliefs main `11f6bb2`; science main `7dc27bbeb7711948c4942b3a3cd35fbaf6745514`.
**Workspace:** `.worktrees/918fd2-overlapping-publications`, branch
`design/918fd2-overlapping-publications`.
**Lane:** reopens `world-read`. Shared surfaces named under roadmap concurrency rule 3:
`corpus.py`, `evaluation.py` and `audit.py` (the `write-path` lane's column), `errors.py`,
the ledger, the roadmap and the designs index.
**Cut:** the next unused number at freeze (48 at this baseline; the plan rechecks branches
and worktrees before freezing).

## 1. Intent and evidence

A recipient that holds two publications sharing records cannot read its world. Every
republication of a view keeps its selected records' addresses and uids, and a publication
carrying closure shares content-addressed records with its sources. Once two such corpora
are live, `derive.address_map` refuses the shared address (`duplicate-location`), no epoch
can be captured, and every world read and mount citation fails. Science commons milestone 1b
(`sci-9104fb`) overlaps by construction at its first step: *A* adopts *B*'s derivation, which
carries *A*'s own records. Science's 1a plan refuses any overlapping adoption
(`adopt-conflict`, commons §10 Deviation 3) until this lands.

Read at the baseline, nothing has moved since the brief:

- `python/src/beliefs/world/derive.py` `address_map` refuses `uid-corruption` (one uid, two
  canonical addresses), then `duplicate-location` (one address, several `(corpus_id, uid)`
  claims) whatever the content, then folds deprecated addresses into a singular
  `address -> (corpus_id, uid)` map, raising a bare `ValueError` when a deprecated entry
  collides (beliefs-354eae). Epochs publish the map as `address-map.yaml` with closed entries
  `{address, corpus_id, uid}` (`epoch._check_addresses`), and `world/read.py` `_address_map`
  reads it back as the same singular map.
- `world/view.py` `open_world_view` checks each mapped address against its one carrier, then
  refuses any uid held by two captured corpora ("W8b, the view's half", pinned by cut 23's
  live `W10g` arm). `world/live.py` derives the same map over world kinds and runs a narrower
  check: a uid shared across corpora where some holder is a record outside the map
  (`_require_unmapped_uids_unique`, cut 41's Z5-c).
- `corpus.py` `MountCitations._one` refuses a citation two session corpora hold
  (mount-citations decision 4; cut 44's J17a/J17b arms).
- `publish.py` `_population` stages each selected record's canonical rendering
  (`node_to_markdown(read.get(address))`) and `_require_snapshot_records` asserts it re-parses
  to the captured node, so a republished copy carries the same canonical projection as its
  source. `_selected_attributions` groups selected addresses by `read.corpus_of(ref)`, one
  holder each.
- `evaluation.py` `gather` evaluates `counts(corpus_id, address)` once per record against
  the one holder `corpus_of` names, and attributes `node_corpus` to that holder. The belief
  acceptance design §5.1 states that overlap must try the predicate for every holding corpus
  or compute an equivalent union.
- `world/registry.py` `corpus_state_identity` already computes a per-record content digest,
  `v1.digest("science.node-content.v1", <canonical JSON projection>)`, over `nodes`'
  `to_canonical` (id, uid, kind, title, body, metadata, relations, facets,
  deprecated_ids). It is a private member of the corpus-state identity today.

Intent provenance: the requirement is the user's reviewed commons design (science
`docs/specs/2026-09-30-science-commons-design.md` §4.7 outcomes 1 to 3, §9.2's "any holding
corpus" rule, §10 and §12 milestone 1b). The brief and the task were filed by agents from
that design; no recorded human turn chooses a mechanism. Every ruling below is this design
author's proposal, grounded in the cited documents and code, for the user to confirm or
correct.

## 2. Goals, non-goals and anti-goals

Goals:

1. A world whose live corpora hold one address with identical content captures an epoch,
   serves that record once through every world read (view, live query, resolution, mount
   citation), and contributes it once to belief.
2. One address held with differing content still refuses `duplicate-location`, explicitly,
   never by corpus order, and `consolidate` stays the exit. `uid-corruption` stays
   unconditional and offers no repair.
3. Belief acceptance is tried for every holding corpus; attribution and the acceptance
   report name holders, not a holder picked by order.
4. A republication attributes a record held by several holders to one provenance, chosen by
   a rule over the holder set, and a reordering of the holders moves nothing.

Non-goals: a revision carried beside its predecessor (one uid under two live addresses,
§4.1), retirement policy (commons §10, science's), science's `adopt` conflict rule and
`Carrier` content check (sci-4a3543, science's), the TypeScript side (no epoch reader there,
checked at the baseline), a general content-addressed store, and the W8b text sharing in
beliefs-0e1acb (sequenced after this cut, §9).

Anti-goals: picking a holder by registration or sort order for any answer that depends on
content; reading a holder whose copy was not captured under its own hold; weakening
`uid-corruption`; inventing an origin for a record no holder carries an origin for; a
compatibility shim that reads a legacy epoch as if it were the new shape without saying so.

## 3. Approaches and decision

The brief's three alternatives stand. **Chosen: 1, the multi-holder address map keyed by
content identity.** An address maps to one record (uid, content identity) and the set of
corpora holding it; equal content reads once, unequal content refuses. It is the only option
meeting commons §4.7 for the write-root-plus-carrier case.

Rejected, with the brief: **2, retirement only** (fails §4.7 for 1b's first step and for a
dependency-kept predecessor; commons §10 makes retirement surface policy); **3, recipient
consolidation** (rewrites what was shared; commons §10.1 forbids it; it remains the exit for
real conflicts only).

Within approach 1, three further choices were made. Each has its alternatives in the
section that rules it: what "identical" means (§4.1), which holder a read reports (§5.2),
and which provenance a republication attributes (§7).

## 4. The address map

### 4.1 Content identity

**Ruling.** Two holders of one address hold *the same record* iff their records' content
identities are equal, where a record's content identity is
`v1.digest("science.node-content.v1", <projection>)` over `nodes`' canonical projection of
the parsed node, exactly the member `corpus_state_identity` already computes per node. The
digest covers id, uid, kind, title, body, metadata, relations, facets and `deprecated_ids`.
Equal content therefore implies an equal uid and equal deprecated-id lists.

Expose it as `beliefs.world.registry.content_identity(node: Node) -> str`, called by
`corpus_state_identity`, by the epoch and live captures, by `open_world_view`,
`resolve_address` and `MountCitations`, and available to science (§8). One function, one
domain string; no second digest.

Why this and not the alternatives:

- *Equal uid plus semantic hash* (the brief's other candidate). Semantic identity exists
  only for the kinds that have one (assessment, run, spec, dataset); propositions, sources,
  retractions and coordination records would need a per-kind rule, a second authority on
  what a record is. It would also admit two copies whose `deprecated_ids` or relations
  differ, which the view would then have to choose between.
- *Stored file bytes.* A hand-written source file is not canonical; the republished copy
  is. Byte comparison would refuse a publication against the very corpus it was staged from.

Consequences the brief asked to be ruled:

- **Republication.** Publish stages the canonical rendering of the captured node and
  asserts it re-parses to that node, so a published copy and its source have equal content
  identity by construction. That is the 1b case, and it reads once.
- **Deprecated-id lists.** Part of the content. A copy that gained a deprecated id was
  revised after the publication; it is not the same record and is handled as §4.2's fold
  says.
- **Revision.** A record revised in place (same address, same uid, changed content) held
  beside its unrevised copy is `duplicate-location`: content differs, nothing picks, the
  exits are `consolidate` or, before admission, science's §10.5 refusal. A record renamed
  under a redirect (new live address, old address in `deprecated_ids`, same uid) held beside
  its predecessor is `uid-corruption` today and stays so: one uid names two canonical
  addresses. Lifting that is a supersession-aware map, out of scope; §10 records it as the
  one 1b-adjacent case this design does not admit, with the follow-up to file.
- **Independent authoring of one source** (equal basis, distinct uids, the "ordinary case"
  of world §4.1). Distinct uids give distinct content, so the pair refuses
  `duplicate-location` exactly as today. No behaviour the existing W8b arms assert changes
  for distinct uids.

### 4.2 Derivation

`derive.CapturedRecord` gains `content: str` (the content identity), supplied by both
captures (`epoch._captured_records`, `live._address_map`). It is **not** added to
`CapturedRecord.projection()`: `rule_input` and the four fixture-bound rules are unchanged,
and no receipt subject moves.

`derive.address_map(capture)` returns `Mapping[str, AddressEntry]` with

```python
@dataclass(frozen=True)
class AddressEntry:
    uid: str
    content: str | None        # None only for a legacy epoch entry (§4.3)
    holders: tuple[str, ...]   # sorted corpus ids, at least one
```

in this order:

1. **uid-corruption, unchanged and first.** One uid under two distinct canonical addresses
   anywhere in the capture refuses `AddressMapConflict("uid-corruption")`, naming every
   `(corpus_id, address)` claim, offering no repair. Checked over the complete capture before
   any duplicate is looked at, so a duplicate pair cannot hide a third address.
2. **Canonical claims per address.** Group the canonical claims `(corpus_id, uid, content)`
   by address. If every claim's content identity is equal, the address gets one entry whose
   holders are the sorted claimant corpora. If any two differ, refuse
   `AddressMapConflict("duplicate-location")` with the existing message and a detail naming
   every `(corpus_id, uid)` claim in capture order. A shared uid with differing content is
   still `duplicate-location`; distinct uids always are (§4.1).
3. **Deprecated keys.** Each record's `deprecated_ids` entries become additional keys
   mapping to that record's entry. A deprecated key that is already a live address, or is
   claimed by a record with a different content identity, refuses the existing typed
   `ResolutionRefused` naming the address and both claims, replacing the bare `ValueError`.
   This absorbs beliefs-354eae as that task scoped it: same precedence, same callers
   (`epoch._derived_members`, `live._address_map`), no new error type, both input orders,
   same and cross corpus, nothing published on refusal. The same key reached through two
   holders of one record is one entry, not a collision.

Claims are ordered by the capture, never selected by precedence. Nothing in the derivation
reads a registry, a path or a manifest.

### 4.3 The epoch member `address-map.yaml`

New entries are closed on exactly `{address, content, holders, uid}`, sorted by address,
holders sorted:

```yaml
addresses:
  - address: dataset:one
    content: <64 hex>
    holders: [<corpus a>, <corpus b>]
    uid: <uid>
```

`epoch._check_addresses` admits two closed shapes and no other: the new one, and the legacy
`{address, corpus_id, uid}` that every epoch built before this cut carries. One document
uses one shape; a document mixing them is `EpochMalformed`. `read._address_map` returns
`AddressEntry` for both, a legacy entry reading as `holders=(corpus_id,)`, `content=None`.
The legacy shape is a versioned, named input, not a fallback: a world keeps its retained
epochs readable for `current_epoch`, `open_epoch`, `delete_epoch`'s carried-identity walk,
and the epoch audit, and rebuilds to get a multi-holder map. `derive.address_map_projection`
writes only the new shape; packaging identities of existing epochs are untouched.

Why publish `content` at all: the entry asserts that *n* corpora hold *one* record. Without
the content identity that assertion names nothing a later reader could check; with it,
`resolve_address` (§5.3) and the audit can say whether a carrier still holds what the epoch
mapped. A `content: None` entry makes no such claim and is checked by uid alone, as today.

### 4.4 The retraction-discovery map

Target identity to sorted retraction addresses, folded over `located_records`, which yields
one `(corpus_id, record)` per holder. The fold is a set per target, so a retraction held in
two corpora contributes its address once. No change; the arm that proves it is §9's W18-f.

## 5. World reads

### 5.1 Opening a view (`open_world_view`)

After capture, for every mapped address and every **present** holder in its entry: the
present carrier holds the mapped uid under that address (live or deprecated), as today, and
the mapped uid's live address maps back to an entry naming that holder. Then, for every entry
with two or more present holders: the present holders' captured copies have equal content
identity. Disagreement refuses `ResolutionRefused` naming the address and every holder: the
holders agreed when the epoch was built and no longer do, and this world cannot say which
copy answers; rebuild to publish the conflict, or `consolidate`. Agreement with each other,
not with the epoch's `content`, is what is required: a single holder whose copy moved since
the epoch is drift today and stays drift, and two holders that moved identically are the
same drift.

**The owners check, narrowed (W8b, the view's half).** A uid held by two captured corpora is
admitted iff the recorded map names both corpora as holders of that uid's record. Any other
sharing refuses exactly as today, with the existing text. This keeps the check distinct from
`uid-corruption`: corruption is one uid at two addresses, judged by the map before any view
opens; the view's check is one uid at two corpora whose equality the map did not establish.
A record outside the map (a coordination record, an unmapped drift record) shared across
corpora still refuses. `live.py`'s `_require_unmapped_uids_unique` already fires only for a
holder outside the map, so its predicate does not change; its docstring and W8b text are
re-read against this ruling, and beliefs-0e1acb's sharing of the text follows.

`held[corpus]` keeps one entry per present holder, so drift and `captured_records` are
per corpus as today. `inbound` edges are built from the distinct-record enumeration
(§5.2), one `ResolvedEdge` per relation, never one per holder.

Damage: a damaged holder refuses the shared address (`CorpusDamaged`) whether or not
another holder is readable. The damaged copy cannot be shown to agree, and the fail-closed
answer is the same one a single damaged holder gives today.

### 5.2 The served surface (`WorldReadView`, `_LiveCapture`)

- `locate(ref)`: `Unknown` when the map does not record `ref`. Otherwise let *P* be the
  entry's present holders. `NotPresent` iff *P* is empty: every holder is absent. Otherwise
  `Resolved(Location(corpus_id=min(P), uid, holders=P), stamp)`. `Location` gains
  `holders: tuple[str, ...]`, required, sorted, non-empty.
- `corpus_of(ref)` keeps its signature and returns the **canonical holder**: the least
  present holder, or for a `NotPresent` address the least recorded holder. This is a
  representative, not a resolution: every present holder's copy has equal content (§5.1), so
  `get`, `resolve`, `corpus_view` and the facet read through `corpus_view` answer the same
  bytes from any of them, and the choice is a labelling that the holder-agreement check makes
  immaterial. Where a caller's answer does depend on which holder (attribution, acceptance,
  audit filing, not-present naming) the caller reads the holder set instead; §5.4 lists them.
- `holders_of(ref) -> tuple[str, ...]`: the entry's recorded holders, sorted; `()` when
  unmapped. Present holders are `holders_of(ref)` minus `absent()`.
- `_mapped_records()` keeps yielding `(corpus_id, node)` **once per present holder**, for
  the callers that file something per corpus. `_mapped_holders()` is added, yielding
  `(holders, node)` **once per record** for the callers that decide something per record
  over its holders. `iter_stored()` yields each record once (deduplicated by uid, in sorted
  canonical-holder then uid order).
- `_LiveCapture` carries the same `AddressEntry` map; every holder is present by
  construction, so the live surface differs only in that `NotPresent` never occurs.

### 5.3 `resolve_address`

For a recorded address: refuse as today on a duplicate carrier or unreadable manifest for
any holder. If no holder is present, `NotPresent`. Otherwise every present holder's carrier
must produce the mapped uid (today's per-carrier rule, now per holder), and when two or more
are present their live content identities must agree; disagreement is `ResolutionRefused`,
never `NotPresent`. The answer is `Resolved(Location(min(P), uid, holders=P), stamp)`.

### 5.4 Every reader of `corpus_of`, ruled

| caller | today | ruling |
|---|---|---|
| `evaluation.py` gather: acceptance of assessments, verifications, retractions (`counts`) | one holder | §6: every present holder |
| `evaluation.py` gather: `node_corpus` attribution | one holder | §6: the accepting holders (all present holders without a policy) |
| `evaluation.py` `_check_filtered_world_standing` | inventory per corpus | per present holder, each corpus's mapped view against its own accepted set |
| `publish.py` `_selected_attributions` | one holder per selected address | §7: the holder set |
| `world/selection.py` `_classify`, `_require_located` | names the absent corpus | not-present only when every holder is absent; the refusal's `corpus_ids` lists every absent holder; `Unresolved.corpus_id` names the least, since mounting any one holder resolves it |
| `world/selection.py` `contributing` | the one holder of each selected record | every present holder of every selected record; `derive_pins` already refuses disagreeing pins across contributing corpora, so a holder whose manifest disagrees is refused explicitly rather than skipped |
| `audit.py` world loops (`_recompute`, coreference endpoints) | `iter_stored` then `corpus_of` | iterate `_mapped_records`: a finding about a record is filed under every present holder; the recomputation runs once per record and is attached to each holder |
| `audit.py` `_CapturedCitations._holder` | the one holder's readable view | the first readable present holder in sorted order; unreadable only when none is, naming the causes of all |
| `corpus.py` `_absence_of` | the absent corpus | the canonical holder, which is absent only when every holder is |
| `corpus.py` coreference endpoint refusal | the absent corpus | same |

`corpus_view(ref)` returns the canonical holder's exact `ReadView`;
`_facets_held_to_capture` binds its rows to the captured node, which is holder-independent.

## 6. Belief acceptance over holders

The predicate's signature, `counts(corpus_id, canonical_address) -> bool`, and the
`AcceptancePolicy` and `AcceptanceContext` types are unchanged. What changes is how often it
is asked and what the answer means:

- For every record in the selection domain (assessment, verification, retraction) with
  present holders *P*, gather asks `counts(h, address)` for **every** `h` in sorted *P*, each
  decision cached per `(h, address)` as today, and the record is **accepted iff any holder's
  decision is true**. This implements commons §9.2 ("the record counts if any holding
  corpus's branch says so") and the acceptance design §5.1's union, and never takes the first
  carrier.
- The record is read once (decoded once, one vertex, one trace entry). `node_corpus`
  attributes its identity to the accepting holders; without a policy, to every present
  holder. The type already allows a tuple per identity (G10-f's "rejected holder never joins
  identity attribution" still holds per holder).
- `AcceptanceContext.excluded` keeps listing every rejected `(corpus_id, address)` decision,
  including a holder's rejected decision for a record another holder accepted. That is the
  faithful report for 1b's decisive case: under `accept = [B]` *A*'s assessment counts through
  its write-root copy and the copy carried in *B*'s corpus is listed as excluded, so it
  visibly contributes nothing. Science's `explain` already prints the holder beside each
  pair. Completion and digest rules (G13) are unchanged.
- Snapshot standing already folds per corpus then unions (`snapshot_standing`), so a
  retraction held twice is decided under each holder and stands if either accepts it; the
  filtered world-standing fidelity check runs each holder's mapped view against that holder's
  accepted set.
- Corpus-local reads are unchanged: one corpus, one holder.

Science's side (sci-4a3543) needs no interface change from this: the predicate is called per
holder with the holder's corpus id, and a `Carrier` content check compares the kernel's
`content_identity` of the carrier's copy with the origin's (§8).

## 7. Publication attribution over holders

`_selected_attributions` groups each selected address by its **present holder set**
(`holders_of` minus `absent()`; a selected record is `Resolved`, so the set is non-empty).

1. **Admission.** Every present holder of every selected record needs an admission; refuse
   `attribution-holder-unregistered` in sorted holder order, as today.
2. **Declared ownership.** Cut 47's captured-marker guard runs per declared selected holder,
   as today.
3. **Classification per selected address.** Each present holder yields one claim:
   - an **own** holder (`Fresh`, `ForkOf`, or a declared markerless holder) yields *own*;
   - a **replica** holder (undeclared `ReplicaOf`) yields the origin triple cut 46 derives
     from its captured marker: the holder's own marker, or the earlier origin its marker
     already carries for that address, copied unchanged.
   The record's attribution is then: **own if any holder is own**; otherwise the one triple
   every replica holder yields; otherwise refuse `PublicationRefused("attribution-ambiguous",
   refs=(address,), corpus_ids=<the holders>)`, with nothing written.
4. Under v2, the existing `attribution-contract-unpinned` names the replica holders that
   hold at least one selected record classified as carried; a record made own by an own
   holder needs no source. Under v3 the frozen tuple carries one entry per carried record.

Why own wins: a byte-equal copy in a holder the publisher owns is, under the kernel's
existing authenticity limit (cut 47 §1, publication-attribution decision 8's reasons), the
publisher's own record; the carried copy is the same record travelling back, and §4.8's
first-origin rule says a republication names the first origin, which the own holder is. Why
replica claims must agree rather than pick: two carriers attributing one record to different
origins are two provenance claims, and choosing one by any order would be the thing commons
§4.7 forbids. Why not resolve the carried triple against the writer's own
`publication-binding` records (recognising "attributed to my own earlier publication"): that
is a second ownership rule inside publish, overlapping cut 47's explicit declaration, and the
own-holder rule already covers the 1b case because *A*'s write root is present. It is listed
as a rejected alternative, not a gap.

Order independence is by construction: the rule reads the holder set, every quantifier is
over sorted holders, and the frozen snapshot carries the result. The decisive arm is a publish
→ adopt → republish sequence run twice with the recipient's roots and admissions in the other
order, asserting byte-identical markers (§9, Y17-y).

Preview and publish share this path (`publication_preview` is what `publish` calls), retries
reconstruct from the frozen snapshot (cut 46 §6), and `resume_publish` gains nothing.

## 8. Mount citations (J17) and science's interface

`MountCitations._one`: collect every session holder of the citation. One holder: as today.
Several: compute each holder's record content identity; if all equal, the citation resolves
through the write root's view when it holds the record, else the least corpus id's read-mount
view (a representative; the bytes are equal), and `_refuse_contract_mismatch` runs for
**every** read-mount holder. Unequal: `AddressMapConflict("duplicate-location")` naming every
holder, as today. Decision 4 and J17 are amended by citation to "a citation two session
corpora resolve to differing content refuses"; the mount view still opens every read mount
inside its hold (decision 5) and still never picks by corpus order. `producers` was already a
union and does not change.

Science (sci-4a3543, sci-9104fb) gets, from this cut: `registry.content_identity(node)` as
the one equality contract; the per-holder `counts` calls of §6; and the ruling that its
`adopt` conflict rule may admit a candidate whose shared addresses have equal content
identity with every live holder, refusing differing content before admission (commons
§10.5). Those changes are science's tasks and are not made here.

## 9. Guarantee rows, arms and the cut

**Amended by citation**, each with a dated note on its current-facing row and the frozen cut
body untouched:

- **W8b** (world-addressing design): the duplicate-location clause reads "two records of
  differing content at one canonical address in two corpora"; two holders of one record
  (equal content) are the new W18. Cut 28's live arms over `derive.address_map`
  (`W8b-a`..`W8b-d`, `W8`) are textual sabotages of the rewritten function and are retargeted
  in `n2_arms_cut28.py`'s live table; cut 23's `W10g` sabotage of the owners check is
  retargeted to the narrowed predicate; cut 41's Z5-a/Z5-b/Z5-c over `live.py` are re-read
  (Z5-c's predicate is unchanged).
- **J17** (mount citations, cut 44): "differing content"; `J17a`/`J17b` are retargeted so
  their two-mount fixtures differ in content.
- **J20** (cut 44): `node_corpus` attributes to the holder set.
- **G10** (cut 45): the predicate receives every present holder; `G10-d` and `G10-f` are
  re-read; the union is the new G14.
- **Y5/Y17** (publication design, cuts 46 and 47): the holder-set rule of §7.

**New rows**, appended at freeze to the tables their subject belongs to (ids confirmed by the
plan against the current tables; W17 and G13 are the last used at this baseline):

| Row | Obligation | Decisive checks |
|---|---|---|
| W18 | The address map admits one record held in several corpora and refuses differing content, deprecated keys included | equal content in two or three corpora maps one entry with sorted holders in either capture order; shared uid with differing content, and distinct uids, refuse `duplicate-location` naming every claim; `uid-corruption` still outranks; a deprecated key reached through two holders is one entry; a deprecated key colliding with a live or differing record refuses the typed `ResolutionRefused` in both input orders and both same- and cross-corpus; the projection is the new closed shape; a legacy epoch reads as singleton holders and a mixed document refuses; a retraction held twice is discovered once |
| W19 | World reads serve a multi-holder record once and refuse holders that disagree | `open_world_view`, `evaluate_live_query` and `resolve_address` serve equal-content holders once with `Location.holders` naming them; a holder whose captured copy differs after the epoch refuses `ResolutionRefused` and never `NotPresent`; `NotPresent` only when every holder is absent and `Resolved` with one present; a shared uid the map did not establish still refuses at open; a damaged holder refuses; inbound edges are not duplicated; `contributing` names every present holder and disagreeing pins refuse |
| G14 | Acceptance is a union over holders and reports every holder's decision | a record rejected under one holder and accepted under another is read once, counts, is attributed to the accepting holder, and the rejected pair is in `excluded`; rejected under every holder it is inert; the predicate is asked once per holder; the 1b decisive case under `accept = [B]`; retractions and verifications held twice follow the same rule |
| Y19 | A republication's attribution over several holders is a function of the holder set | own holder wins over a carried copy with no entry; two carriers agreeing on an origin forward it; disagreeing carriers refuse `attribution-ambiguous` before intent; publish → adopt → republish with holders reordered yields byte-identical markers; v2 names only the remaining carried holders; retries use the frozen tuple |

Ride-along: beliefs-cb2a39's live arm for gather's observes-loop held filter, whose check is
`test_world_view.py::test_an_absent_input_corpus_is_the_banked_reason`, is added to this
cut's live table as the task's shelving note planned.

The plan fixes the exact arm list, declaration units, the sabotage per unit and the
accounting; this section is the obligation set it must cover. The cut is frozen before
product code, names the highest-numbered runner as its prefix, and adds its row to
`test_recent_cut_acceptance.py`.

## 10. Limitations and deferrals

1. **A renamed record beside its predecessor is `uid-corruption`** (§4.1). A successor
   publication carrying a record whose address moved under a redirect cannot be mounted
   beside the predecessor that holds the old address. Science's §10.5 exit (refuse the
   successor before admission, keep the predecessor) applies. The follow-up is a
   supersession-aware map that recognises "holder B's deprecated id is holder A's live
   address for the same uid" as a revision rather than corruption; filed at this design's
   completion as a beliefs idea sourced here, not promised.
2. **Equality is exact.** Any difference in the canonical projection, metadata timestamps
   included, is a different record. Publish preserves the projection, so this binds only
   copies that were edited.
3. **A damaged holder refuses the shared address** even when another holder is readable.
4. **Legacy epochs stay singular** until rebuilt; nothing migrates them.
5. **Authenticity is unchanged.** Own-wins attribution rests on the existing rule that a
   byte-equal copy in an own holder is the publisher's; this design adds no proof of
   authorship.
6. **No measurement of cost.** Per-holder acceptance calls and per-holder audit filing are
   linear in the number of holders; nothing here caches across calls.

## 11. Verification, surfaces and constraints

Primary code: `world/derive.py`, `world/epoch.py` (`_check_addresses`, capture),
`world/read.py`, `world/view.py`, `world/live.py`, `world/selection.py`, `world/registry.py`
(`content_identity` exposed), `evaluation.py`, `audit.py`, `publish.py`, `corpus.py`
(`MountCitations`, `_absence_of`, the coreference endpoint refusal), `errors.py`
(`attribution-ambiguous` reason text). Tests: `test_world_derive.py`,
`test_world_conflicts.py`, `test_world_view.py`, `test_world_epoch.py`,
`test_live_selection.py`, `test_mount_citations.py`, `test_publication_attribution.py`,
`test_owned_replica_publication.py`, the acceptance-filter tests, the world and live
acceptance modules and the cut runner; `test_arm_staleness.py` and `test_frozen_guards.py`
discover every live arm the rewrite falsifies beyond those §9 names.

The implementation plan's Global Constraints carry the two obligations below verbatim,
beside this lane's own:

- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine cause types,
  a predicate over engine exceptions, or any other engine-typed behaviour lives in `root.py`
  and reaches its boundary through a seam callable (cut 35's `StoreActSeam.store_refusal`,
  `b065711`), never as an import in the boundary module. Every new caller of a write
  primitive joins `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both directions.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the runner
  import, its `(runner, cut, accounting)` parametrization entry with the declared-arm,
  declaration-unit and guarantee-row counts, and the cut's guarantee-rows-exercised line.
  Cuts 33, 34 and 35 landed theirs at `f4c2cef`, `c77b2aa` and after cut 35's final review;
  the plan's runner task owns the row.

No new write primitive is proposed; the derivation, the readers and the publish preparation
write nothing. No permit, contract release, world-config field or TypeScript change.

Run the hydrated worktree's full `just test` baseline at execution Setup, before code
changes, recording its test count. Develop through `just test-one`, `just test-fast` before
commits, `just check` and the installed hooks. Durable and N2 arms run on the certified
kernel and volume; a capability refusal is a failure, not a skip. This design ran no suite
and no live reproduction; its evidence is the inspected code, tests and documents at the
baseline.

## 12. Builder latitude

The builder chooses `AddressEntry`'s module placement and the private helper names, the
exact sabotage text per arm, the cut number and the fixture reuse, and the order of plan
tasks. The content-identity contract, the derivation order, the two epoch shapes, the
holder-agreement refusals, the narrowed owners check, the canonical-holder labelling with
holder-set readers, the acceptance union with full reporting, the own-wins-then-agree
attribution rule, and the J17 amendment are decisions to preserve.

On the user's approval: note the ruling on beliefs-81367e; run
`tasks note sci-4a3543 --no-reviewed` with the equality contract (§4.1), the approved
revision and the acceptance interface (§6, §8); close beliefs-354eae with this cut; sequence
beliefs-0e1acb after it; file the §10 item 1 follow-up.
