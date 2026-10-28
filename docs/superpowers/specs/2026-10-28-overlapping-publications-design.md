# Overlapping publications: one address held in several live corpora

**Status:** draft, revision 3, for the user's review; not accepted. Revision 1 (`e57ab8c`)
had a builder check and a critical review (round 1, verdict revise: 1 Critical, 6
Important, 9 Minor); revision 2 (`fe7539c`) a re-review (round 2, verdict revise: 0
Critical, 5 Important, 5 Minor); both reviewers `claude-code/claude-fable-5-1`. Every
finding is resolved below and §13 lists the dispositions.
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
  `{address, corpus_id, uid}` (`epoch._check_addresses`, run on every open by
  `_locked_open_epoch`), and `world/read.py` `_address_map` reads it back as the same
  singular map.
- `world/view.py` `open_world_view` checks each mapped address against its one carrier, then
  refuses any uid held by two captured corpora ("W8b, the view's half", pinned by cut 23's
  live `W10g` arm). `world/live.py` derives the same map over world kinds and runs a narrower
  check: a uid shared across corpora where some holder is a record outside the map
  (`_require_unmapped_uids_unique`, cut 41's Z5-c).
- `corpus.py` `MountCitations._one` refuses a citation two session corpora hold
  (mount-citations decision 4; cut 44's J17a/J17b arms).
- `publish.py` `publication_preview` renders each selected record canonically
  (`node_to_markdown(read.get(address))`) and `_require_snapshot_records` asserts the text
  re-parses to the captured node; `_population` later compares staged bytes with that frozen
  text. A republished copy therefore carries the same canonical projection as its source.
  `_selected_attributions` groups selected addresses by `read.corpus_of(ref)`, one holder
  each, and a replica holder's claim for an address is the entry its captured marker already
  carries, else `(address, holder, marker uid)`.
- `evaluation.py` `gather` evaluates `counts(corpus_id, address)` once per record against
  the one holder `corpus_of` names, and attributes `node_corpus` to that holder. The belief
  acceptance design §5.1 states that overlap must try the predicate for every holding corpus
  or compute an equivalent union.
- `world/registry.py` `corpus_state_identity` already computes a per-record content digest,
  `v1.digest("science.node-content.v1", <canonical JSON projection>)`, over `nodes`'
  `to_canonical` (id, uid, kind, title, body, metadata with `created`/`updated`/`version`,
  relations, facets, deprecated_ids). It is a private member of the corpus-state identity
  today.
- The four receipt rules (`rules_v1/producer.py`, `retraction.py`, `certification.py`,
  `coreference.py`) fold their inputs into sets, and the coreference unit key excludes the
  corpus, so a record appearing once per holder in `rule_input` adds nothing twice.

Intent provenance: the requirement is the user's reviewed commons design (science
`docs/specs/2026-09-30-science-commons-design.md` §4.7 outcomes 1 to 3, §4.8's first-origin
rule, §9.2's "any holding corpus" rule, §10 and §12 milestone 1b). The brief and the task were
filed by agents from that design; no recorded human turn chooses a mechanism. Every ruling
below is this design author's proposal, grounded in the cited documents and code, for the
user to confirm or correct.

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
   a rule over the holder set and the held supersession chains, and a reordering of the
   holders moves nothing.

Non-goals: a revision carried beside its predecessor under a redirect (§4.1), retirement
policy (commons §10, science's), science's `adopt` conflict rule, its session-holder
resolution and its `Carrier` content check (§8; science's tasks), the TypeScript side (no
epoch reader there, checked at the baseline), a general content-addressed store, and the
W8b text sharing in beliefs-0e1acb (sequenced after this cut, §9).

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
digest covers id, uid, kind, title, body, metadata (`created`, `updated`, `version`),
relations, facets and `deprecated_ids`. Equal content therefore implies an equal uid and
equal deprecated-id lists.

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
- **Revision in place** (same address, same uid, changed content, `metadata.updated`
  included) held beside its unrevised copy is `duplicate-location`: content differs, nothing
  picks. This binds the write root too: once a carrier of *A*'s record r is mounted in *A*'s
  world, `revise` of r in *A*'s write root makes the next epoch, live query, mount citation
  and retained-epoch view refuse until the pair is resolved. A carried record's **content is
  frozen while any carrier of it is mounted**. The kernel offers no exit that keeps both:
  `consolidate` cannot rewrite a chain-verified publication (commons §10.1), the world
  design's §4.4 redirect exists only for a basis change and not for a content revision, and
  republishing the revised r shares its address with the mounted carrier all the same. The
  exits are the carrier's retirement or unmounting (commons §10, science's policy) or a new
  entity. §10 item 1 names this; §8 hands science the surface rule, which is to refuse
  `revise` on an address a mounted carrier holds.
- **Revision under a redirect** (new live address, old address in `deprecated_ids`, same
  uid) held beside its predecessor is `uid-corruption` today and stays so: one uid names two
  canonical addresses. Lifting that is a supersession-aware map, out of scope; §10 item 2
  records it with the follow-up to file.
- **Independent authoring of one source** (equal basis, distinct uids, the "ordinary case"
  of world §4.1). Distinct uids give distinct content, so the pair refuses
  `duplicate-location` exactly as today. No behaviour the existing W8b arms assert changes
  for distinct uids.

### 4.2 Derivation

`derive.CapturedRecord` gains `content: str` (the content identity), supplied by both
captures (`epoch._captured_records`, `live._address_map`). It is **not** added to
`CapturedRecord.projection()`: `rule_input` and the four fixture-bound rules are unchanged,
no receipt subject moves, and the rules already fold a record that appears once per holder
into one producer edge, one `(ref, resolution)` pair, one certification ref and one
coreference unit (§1). W19 carries arms that pin that, so a future rule keyed on `corpus_id`
cannot double-count silently.

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
The legacy shape is a versioned, named input, not a fallback: `_locked_open_epoch` runs the
member checks on every open, so without it no retained epoch could be opened again by
`current_epoch`, `open_epoch`, the epoch audit or the import path. A world rebuilds to get a
multi-holder map. `derive.address_map_projection` writes only the new shape; packaging
identities of existing epochs are untouched.

`content` has exactly one reader in this cut, §5.1's and §5.3's damaged-holder rule: when a
shared address has a holder whose copy cannot be read, the epoch's `content` is what a
readable holder's copy is checked against before it answers alone. A `content: None` entry
cannot be checked that way and keeps the fail-closed rule. The epoch audit
(`world/audit.py`) gains no content check in this cut.

### 4.4 The retraction-discovery map

Target identity to sorted retraction addresses, folded over `located_records`, which yields
one `(corpus_id, record)` per holder. The fold is a set per target, so a retraction held in
two corpora contributes its address once. No change; the arm that proves it is §9's W19-f.

## 5. World reads

### 5.0 Holder states

For a recorded address with holders *H* (the entry's `holders`), the view classifies each
holder as the registry and capture already classify corpora:

- **absent**: not carried in this world (`status.present` false);
- **damaged**: carried, but construction or the base pin failed under its hold
  (`damaged_ids`; only in `on_damage="report"` mode, since `"refuse"` raises at the open);
- **captured** (*P*): carried and captured under its own hold, with the drift check.

A live query has only captured holders. "Present" below means captured.

### 5.1 Opening a view (`open_world_view`)

After capture, for every mapped address and every captured holder in its entry: the carrier
holds the mapped uid under that address (live or deprecated), as today, and the mapped uid's
live address maps back to an entry naming that holder. Then, for every entry with two or
more captured holders: the captured copies have equal content identity. Disagreement refuses
`ResolutionRefused` naming the address and every holder: the holders agreed when the epoch
was built and no longer do, and this world cannot say which copy answers; rebuild to publish
the conflict, or resolve it as §4.1 says. Agreement with each other, not with the epoch's
`content`, is what is required: a single holder whose copy moved since the epoch is drift
today and stays drift, and two holders that moved identically are the same drift.

**A damaged holder.** A shared address with a damaged holder and at least one captured
holder is served from the captured holders iff every captured copy's content identity equals
the entry's `content`; the damage report still names the damaged corpus. If the entry is
legacy (`content: None`), or a captured copy differs from the mapped content, the address
refuses `CorpusDamaged` naming the damaged corpus, as a damaged single holder does today:
the damaged holder is what prevents resolution, since without it the drifted captured copy
would simply be drift. The asymmetry is intended: two identically drifted captured holders
serve (drift is tolerated, as today), and the same pair beside a damaged holder refuses,
because only the published content can vouch for a copy the damaged holder cannot be
compared with. This is what stops a damaged carrier from making the write root's own records
unreadable through every audit, while never serving a copy the publication did not vouch for.
`gather` refuses on the first damaged corpus regardless (`evaluation.py`), so belief is
unaffected; the rule matters to `audit_world` and to resolution (§5.3).

**The owners check, narrowed (W8b, the view's half).** A uid held by two captured corpora is
admitted iff the recorded map names both corpora as holders of that uid's record. Any other
sharing refuses exactly as today, with the existing text. This keeps the check distinct from
`uid-corruption`: corruption is one uid at two addresses, judged by the map before any view
opens; the view's check is one uid at two corpora whose equality the map did not establish.
A record outside the map (a coordination record, an unmapped drift record) shared across
corpora still refuses. `live.py`'s `_require_unmapped_uids_unique` already fires only for a
holder outside the map, so its predicate does not change; its docstring and W8b text are
re-read against this ruling, and beliefs-0e1acb's sharing of the text follows.

`held[corpus]` keeps one entry per captured holder, so drift and `captured_records` are
per corpus as today. `inbound` edges are built from the distinct-record enumeration
(§5.2), one `ResolvedEdge` per relation, never one per holder; an edge's `source_uid` is
present iff any captured holder holds the source.

### 5.2 The served surface (`WorldReadView`, `_LiveCapture`)

- `locate(ref)`: `Unknown` when the map does not record `ref`. Otherwise with holders *H*
  and captured holders *P*: `NotPresent` iff every holder is absent; `CorpusDamaged` iff *P*
  is empty and some holder is damaged, or §5.1's damaged-holder rule refuses; otherwise
  `Resolved(Location(corpus_id=min(P), uid, holders=P), stamp)`. `Location` gains
  `holders: tuple[str, ...]`, required, sorted, non-empty; the two test sites and the cut 7
  live checks that construct `Location` positionally are retargeted.
- `corpus_of(ref)` keeps its signature and returns the **canonical holder**: the least
  captured holder, or for a `NotPresent` address the least recorded holder. This is a
  representative, not a resolution: every captured holder's copy has equal content (§5.1),
  so `get`, `resolve`, `corpus_view` and the facet read through `corpus_view` answer the same
  bytes from any of them, and the choice is a labelling that the holder-agreement check makes
  immaterial. Where a caller's answer does depend on which holder (attribution, acceptance,
  audit filing, not-present naming) the caller reads the holder set instead; §5.4 lists them.
- `holders_of(ref) -> tuple[str, ...]`: the entry's recorded holders, sorted; `()` when
  unmapped. Captured holders are `holders_of(ref)` minus `absent()` minus the damaged ids.
- `_mapped_records()` keeps yielding `(corpus_id, node)` **once per captured holder**, for
  the callers that file something per corpus. `_mapped_holders()` is added, yielding
  `(holders, node)` **once per record** (holders = its captured holders, sorted) for the
  callers that decide something per record over its holders. `iter_stored()` yields each
  record once, ordered by `(canonical holder, uid)`; a record with no captured holder is in
  no `held` map and is yielded by none of the three.
- `_mapped_view(corpus_id)` builds its address table from entries whose `holders` contain
  `corpus_id`.
- `_LiveCapture` carries the same `AddressEntry` map; every holder is captured by
  construction, so the live surface differs only in that `NotPresent` and `CorpusDamaged`
  never occur.

### 5.3 `resolve_address`

For a recorded address: refuse as today on a duplicate carrier or unreadable manifest for
any holder. If every holder is absent, `NotPresent`. Otherwise read each present holder's
carrier: it must produce the mapped uid (today's per-carrier rule, now per holder). A
carrier that cannot be read is treated as §5.1 treats a damaged holder: skipped iff some
other present holder reads and every readable copy's content identity equals the entry's
`content`; otherwise `ResolutionRefused` as today. With two or more readable holders, their
live content identities must agree; disagreement is `ResolutionRefused`, never `NotPresent`.
The answer is `Resolved(Location(min(readable), uid, holders=readable), stamp)`.

### 5.4 Every reader of `corpus_of` and of the per-holder enumeration, ruled

| caller | today | ruling |
|---|---|---|
| `evaluation.py` gather: assessment and verification candidate loops (`candidates = view._mapped_records()`, two sites) | one `(holder, node)` per record | iterate `_mapped_holders()`: each record once, decoded once, traced once; §6 decides acceptance over its holders |
| `evaluation.py` gather: retraction acceptance (`counts`) | one holder | §6: every captured holder |
| `evaluation.py` gather: `node_corpus` attribution (assessments, runs, observed datasets) | one holder | §6: the accepting holders (all captured holders without a policy) |
| `evaluation.py` `_check_filtered_world_standing` | inventory per corpus by `corpus_of` | per captured holder, each corpus's mapped view against that corpus's accepted set |
| `publish.py` `_selected_attributions` | one holder per selected address | §7: the holder set |
| `world/selection.py` `_denoted` (`held` from `_mapped_records`, `contributing`) | the last holder in sort order per record | build `held` from `_mapped_holders()`; `contributing` is the union of every selected record's captured holders; `derive_pins` already refuses disagreeing pins across contributing corpora, so a holder whose manifest disagrees is refused explicitly rather than skipped. Intended ordering: `derive_pins` runs before attribution, so a replica holder of a record an own holder makes own still contributes its pins, and a disagreeing coordination pin refuses `pins-disagree` before §7's v2 narrowing is reached |
| `world/selection.py` `_classify`, `_require_located` | names the absent corpus | not-present only when every holder is absent; the refusal's `corpus_ids` lists every absent holder; `Unresolved.corpus_id` names the least, since mounting any one holder resolves it |
| `audit.py` world loops over `iter_stored` with `corpus_of` (the recomputation loop and the coreference-endpoint loop) | one holder | iterate `_mapped_records`: a finding about a record is filed under every captured holder, the recomputation running once per record. Intended: each corpus's audit is complete for the records that corpus holds, and a consumer summing over `corpora` counts holdings, not records |
| `audit.py` `_CapturedCitations._holder` | the one holder's readable view | the first readable captured holder in sorted order; unreadable only when none is, naming every holder's cause |
| `corpus.py` `_absence_of` | the absent corpus | the canonical holder, which is absent only when every holder is |
| `corpus.py` coreference endpoint refusal | the absent corpus | same |

`corpus_view(ref)` returns the canonical holder's exact `ReadView`;
`_facets_held_to_capture` binds its rows to the captured node, which is holder-independent.
`consulted_contracts` reads a pin for every corpus `node_corpus` names and refuses an
unpinned one, so every holder a world read attributes must be in the caller's `pins`;
science builds its pins and its epochs over the same session mounts, which keeps that true,
and §8 states it as a requirement.

## 6. Belief acceptance over holders

The predicate's signature, `counts(corpus_id, canonical_address) -> bool`, and the
`AcceptancePolicy` and `AcceptanceContext` types are unchanged. What changes is how often it
is asked and what the answer means:

- For every record in the selection domain (assessment, verification, retraction) with
  captured holders *P*, gather asks `counts(h, address)` for **every** `h` in sorted *P*,
  each decision cached per `(h, address)` as today, and the record is **accepted iff any
  holder's decision is true**. This implements commons §9.2 ("the record counts if any
  holding corpus's branch says so") and the acceptance design §5.1's union, and never takes
  the first carrier.
- The record is read once (decoded once, one vertex, one trace entry). `node_corpus`
  attributes its identity to the accepting holders; without a policy, to every captured
  holder. The type already allows a tuple per identity (G10-f's "rejected holder never joins
  identity attribution" still holds per holder).
- `AcceptanceContext.excluded` keeps listing every rejected `(corpus_id, address)` decision,
  including a holder's rejected decision for a record another holder accepted. That is the
  faithful report for 1b's decisive case: under `accept = [B]` *A*'s assessment counts through
  its write-root copy and the copy carried in *B*'s corpus is listed as excluded, so it
  visibly contributes nothing. Completion and digest rules (G13) are unchanged. Science's
  `explain` prints one line per pair; wording that says "copy excluded" rather than "record
  excluded" is science's follow-up (§8).
- Snapshot standing already folds per corpus then unions (`snapshot_standing`), so a
  retraction held twice is decided under each holder and stands if either accepts it; the
  filtered world-standing fidelity check runs each holder's mapped view against that holder's
  accepted set.
- Corpus-local reads are unchanged: one corpus, one holder.

Science's side (sci-4a3543) needs no interface change from this: the predicate is called per
holder with the holder's corpus id, and a `Carrier` content check compares the kernel's
`content_identity` of the carrier's copy with the origin's (§8).

## 7. Publication attribution over holders

`_selected_attributions` groups each selected address by its **captured holder set**
(`holders_of` minus absent; `publication_preview` opens the view in refuse mode, so no
damaged holder reaches it, and a selected record is `Resolved`, so the set is non-empty).

1. **Admission.** Every captured holder of every selected record needs an admission; refuse
   `attribution-holder-unregistered` in sorted holder order, as today.
2. **Declared ownership.** Cut 47's captured-marker guard runs per declared selected holder,
   as today.
3. **Classification per selected address.** Each captured holder yields one claim:
   - an **own** holder (`Fresh`, `ForkOf`, or a declared markerless holder) yields *own*;
   - a **replica** holder (undeclared `ReplicaOf`) yields the origin triple cut 46 derives
     from its captured marker: the entry its marker already carries for that address, copied
     unchanged, else `(address, holder, its marker uid)`.
   The record's attribution is then:
   1. **own, if any holder is own**;
   2. else the one triple every replica holder yields, if the **distinct claims** number
      one;
   3. else, over the distinct claims' origin markers `(origin corpus, marker uid)`, the
      claim whose marker **every other claimed marker supersedes**, when exactly one such
      claim exists. Marker *X* supersedes *Y* when *X* names *Y* in `supersedes_markers`,
      transitively through the markers of every captured holder in the world view (those
      holding no selected record included; a captured marker that fails layout or release
      validation refuses `attribution-source-invalid` naming its holder with empty `refs`).
      The order is a property of the claimed markers, not of which holders carry them, so
      *B*'s re-adopted own publication beside P1 and P3, or a third party holding P2 and P3
      but not P1, both resolve to P1. No live source is reopened: `_selected_attributions`
      already reads captured markers, and attribution design decision 5 already forwards an
      entry whose named origin is not held;
   4. else refuse `PublicationRefused("attribution-ambiguous", refs=(address,),
      corpus_ids=<the holders>, field=<the distinct claims, rendered>)`, with nothing
      written. The claims are carried so that science's `show` can name the marker whose
      adoption would order them (§10 item 3).
4. Under v2, `attribution-contract-unpinned` names the replica holders that hold at least
   one selected record whose attribution is carried (rule 3.2 or 3.3); a record made own by
   an own holder needs no source. This narrows "any remaining replica" in the attribution
   design's decision 6 and the owned-replica design §4 step 4, and is recorded as a dated
   amendment on Y5 and Y17, not only here. Under v3 the frozen tuple carries one entry per
   carried record.

Why own wins: a byte-equal copy in a holder the publisher owns is, under the kernel's
existing authenticity limit (cut 47 §1, publication-attribution decision 8's reasons), the
publisher's own record; commons §4.8 asks for an entry only for records held in an adopted
corpus rather than one the publisher wrote, and the own holder is that corpus.

Why the supersession order: 1b's second half produces disagreeing carriers by construction.
*A* publishes P1 holding r; *B* adopts P1, derives and publishes P2 carrying r attributed to
P1; *A* adopts P2 and publishes the update P3, in which r is own (rule 3.1) and carries no
entry; *B* adopts P3 and keeps P1 mounted because its derivation depends on a record P3
dropped (commons §10.3). *B*'s next publish sees r in P1 (claim P1) and in P3 (claim P3).
Both claims come from one publisher's chain, P3 supersedes P1, and §4.8's first-origin rule
names P1. The order is read from the captured markers, which cut 46 already validates, so no
live source is reopened and the result is frozen with the snapshot like every other entry.
A consequence science's retirement policy must expect: a recipient's own republication then
names P1 in its entries, and commons §10.3 keeps a publication mounted while a held
publication's entries name it, so the recipient's own markers become a retention reason for
the predecessor.

Why rule 3.3 asks for a least element rather than a total order: sibling tips (P3 and P3′
both superseding P1) are not totally ordered, yet P1 is the marker every other claim
supersedes and §4.8's first origin; science will not mount both siblings (§10.2 leaves one
`fetched`), so the case is a kernel-rule question only, and the least-element condition
answers it without picking between the siblings.

Why rule 3.4 refuses rather than picks: two carriers attributing one record to origins with
no common held origin (unrelated publishers, or a chain the recipient holds only the two ends
of, §10 item 3) are two provenance claims, and choosing one by any order would be the thing
commons §4.7 forbids.

Rejected: resolving a carried triple against the writer's own `publication-binding` records
(recognising "attributed to my own earlier publication" as ownership). It is a second
ownership rule inside publish, overlapping cut 47's explicit declaration, and rule 3.1
already covers *A*'s republication because *A*'s write root is captured.

Order independence is by construction: every rule reads the holder set, every quantifier is
over sorted holders, the supersession order is a property of the held markers, and the frozen
snapshot carries the result. The decisive arm is a publish → adopt → republish sequence run
twice with the recipient's roots and admissions in the other order under one intent's
inputs, asserting equal frozen attribution tuples and an equal `published_from.attributions`
marker member (§9, Y19); the whole marker is not compared, since its event token and clock
differ per run.

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
the one equality contract; the per-holder `counts` calls of §6; and the admission checklist
its `adopt` conflict rule must run before admission, since the kernel offers no exit once a
conflicting corpus is admitted and its predecessor is dependency-kept. A candidate is
admissible iff, against every live corpus and every candidate this session already admitted:

1. every shared live address has equal content identity (differing content refuses, commons
   §10.5);
2. no candidate uid is held live under a different canonical address (`uid-corruption`,
   §4.2 rule 1; an ordinary §4.4 identifier correction published as a successor produces
   this against the predecessor, and the candidate's live ids alone do not reveal it);
3. no candidate deprecated id is a live address elsewhere, and no live candidate address is
   a deprecated id of a differing record elsewhere (§4.2 rule 3).

Science must also amend, with the same equality contract: its session-holder resolution
(`science/config.py` `mount_holding` and `cited`, which refuse any address two mounts hold,
content aside, before the kernel is consulted); its `explain` wording for a rejected copy of a
record that counted (§6); its pins, which must cover every mounted holder a world read may
attribute (§5.4); a surface rule refusing `revise` on an address a mounted carrier holds
(§4.1); and `show`'s naming of the marker whose adoption would order an
`attribution-ambiguous` refusal's claims (§7, §10 item 3). Those changes are science's tasks
and are not made here; the completion note on sci-4a3543 names them.

## 9. Guarantee rows, arms and the cut

**Amended by citation**, each with a dated note on its current-facing row and the frozen cut
body untouched:

- **W8b** (world-addressing design): the duplicate-location clause reads "two records of
  differing content at one canonical address in two corpora"; two holders of one record
  (equal content) are the new W19. Cut 28's live arms over `derive.address_map`
  (`W8b-a`..`W8b-d`, `W8`) are textual sabotages of the rewritten function and are retargeted
  in `n2_arms_cut28.py`'s live table; cut 23's `W10g` sabotage of the owners check is
  retargeted to the narrowed predicate; cut 41's Z5-a/Z5-b/Z5-c over `live.py` are re-read
  (Z5-c's predicate is unchanged); cut 7's live checks that construct `Location` are
  retargeted for the new field.
- **J17** (mount citations, cut 44): "differing content"; `J17a`/`J17b` are retargeted so
  their two-mount fixtures differ in content.
- **J20** (cut 44): `node_corpus` attributes to the holder set.
- **G10** (cut 45): the predicate receives every captured holder; `G10-d` and `G10-f` are
  re-read; the union is the new G14.
- **Y5/Y17** (publication design, cuts 46 and 47): the holder-set rule and the v2 narrowing
  of §7; the order rule is the new Y19.

**New rows**, appended at freeze to the tables their subject belongs to. W18, G13 and Y18
are the last used at this baseline, so the ids are W19, W20, G14 and Y19; the plan confirms
them against the tables at freeze.

| Row | Obligation | Decisive checks |
|---|---|---|
| W19 | The address map admits one record held in several corpora and refuses differing content, deprecated keys included | equal content in two or three corpora maps one entry with sorted holders in either capture order; shared uid with differing content, and distinct uids, refuse `duplicate-location` naming every claim; `uid-corruption` still outranks; a deprecated key reached through two holders is one entry; a deprecated key colliding with a live or differing record refuses the typed `ResolutionRefused` in both input orders and both same- and cross-corpus; the projection is the new closed shape; a legacy epoch reads as singleton holders and a mixed document refuses; a retraction held twice is discovered once (W19-f); a record held twice contributes one producer edge, one `(ref, resolution)`, one certification ref and one coreference unit to the receipts |
| W20 | World reads serve a multi-holder record once and refuse holders that disagree | `open_world_view`, `evaluate_live_query` and `resolve_address` serve equal-content holders once with `Location.holders` naming them; captured holders whose copies differ refuse `ResolutionRefused` and never `NotPresent`; `NotPresent` only when every holder is absent and `Resolved` with one present; a shared uid the map did not establish still refuses at open; a damaged holder is skipped when a captured copy equals the mapped content and refuses otherwise, including for a legacy entry; inbound edges are not duplicated and a source held by any holder is present; `contributing` names every captured holder and disagreeing pins refuse; `_mapped_view` sees the record under each holder |
| G14 | Acceptance is a union over holders and reports every holder's decision | a record rejected under one holder and accepted under another is read once, counts, is attributed to the accepting holder, and the rejected pair is in `excluded`; rejected under every holder it is inert; the predicate is asked once per holder; the 1b decisive case under `accept = [B]`; retractions and verifications held twice follow the same rule and are traced once |
| Y19 | A republication's attribution over several holders is a function of the holder set and the held supersession chains | own holder wins over a carried copy with no entry; two carriers agreeing on an origin forward it; claims whose markers have a least element under supersession yield it (the 1b P1/P3 case; the re-adopted own publication beside them; a third party holding P2 and P3 without P1; sibling tips over P1), read through the marker of a captured holder that holds no selected record; claims with no common held origin (unrelated publishers; a chain with its intermediate unheld) refuse `attribution-ambiguous` before intent, carrying the claims; publish → adopt → republish with holders reordered yields equal frozen attribution tuples and marker members; v2 names only the holders of carried records; retries use the frozen tuple |

Ride-along: beliefs-cb2a39's live arm for gather's observes-loop held filter, whose check is
`test_world_view.py::test_an_absent_input_corpus_is_the_banked_reason`, is added to this
cut's live table as the task's shelving note planned.

The plan fixes the exact arm list, declaration units, the sabotage per unit and the
accounting; this section is the obligation set it must cover. The cut is frozen before
product code, names the highest-numbered runner as its prefix, and adds its row to
`test_recent_cut_acceptance.py`.

## 10. Limitations and deferrals

1. **A carried record's content is frozen in the publisher's own world** (§4.1). While a
   carrier of r is mounted, revising r in place in the write root makes every world read
   refuse until the carrier is unmounted or retired or the revision is withdrawn. No redirect
   applies to a content revision and republishing does not help. The kernel refuses
   explicitly and offers no pick; the surface rule, refusing `revise` on a carried address,
   is science's (§8).
2. **A renamed record beside its predecessor is `uid-corruption`** (§4.1). A successor
   publication carrying a record whose address moved under a redirect cannot be mounted
   beside the predecessor that holds the old address. The kernel offers no exit once both
   are admitted and the predecessor is dependency-kept, so science's `adopt` must refuse the
   successor before admission with §8's checklist (its live-address comparison alone would
   admit it). The follow-up is a supersession-aware map that recognises "holder B's
   deprecated id is holder A's live address for the same uid" as a revision rather than
   corruption; filed at this design's completion as a beliefs idea sourced here, not
   promised.
3. **The supersession order is read through held markers only** (§7). A recipient holding
   the two ends of a chain whose intermediate marker it never adopted or has retired (the
   state commons §10.2 keeps as an unresolved link) refuses `attribution-ambiguous` for every
   record the ends attribute differently, until it adopts the intermediate. The refusal
   carries the claims so the surface can name that marker; `publication_tip` has the same
   one-hop blind spot today.
4. **Equality is exact.** Any difference in the canonical projection, metadata timestamps
   included, is a different record. Publish preserves the projection, so this binds only
   copies that were edited, the write root's included (item 1).
5. **A damaged holder is skipped only against a published content identity.** Under a
   legacy entry, or when the captured copy differs from what the epoch mapped, the shared
   address refuses as a single damaged holder does today.
6. **Legacy epochs stay singular** until rebuilt; nothing migrates them.
7. **Authenticity is unchanged.** Own-wins attribution rests on the existing rule that a
   byte-equal copy in an own holder is the publisher's; this design adds no proof of
   authorship. The supersession order is read from markers the recipient holds, which are
   validated for layout but, as today, not authenticated.
8. **No measurement of cost.** Per-holder acceptance calls and per-holder audit filing are
   linear in the number of holders; nothing here caches across calls.

## 11. Verification, surfaces and constraints

Primary code: `world/derive.py`, `world/epoch.py` (`_check_addresses`, capture),
`world/read.py`, `world/view.py`, `world/live.py`, `world/selection.py`, `world/registry.py`
(`content_identity` exposed), `evaluation.py`, `audit.py`, `publish.py`, `corpus.py`
(`MountCitations`, `_absence_of`, the coreference endpoint refusal), `errors.py`
(`attribution-ambiguous` reason text). Tests: `test_world_derive.py`,
`test_world_conflicts.py`, `test_world_read.py` and the cut 7 live checks (positional
`Location`), `test_world_view.py`, `test_world_epoch.py`, `test_live_selection.py`,
`test_mount_citations.py`, `test_publication_attribution.py`,
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
holder-state classification and the damaged-holder rule, the holder-agreement refusals, the
narrowed owners check, the canonical-holder labelling with holder-set readers, the
acceptance union with full reporting, the own-then-agree-then-earliest attribution rule, and
the J17 amendment are decisions to preserve.

On the user's approval: note the ruling on beliefs-81367e; run
`tasks note sci-4a3543 --no-reviewed` with the equality contract (§4.1), the approved
revision and the acceptance interface (§6, §8) and the science-side changes §8 lists; close
beliefs-354eae with this cut; sequence beliefs-0e1acb after it; file the §10 item 2
follow-up.

Also to preserve: the admission checklist handed to science (§8) and the three named
limitations of §10 items 1 to 3.

## 13. Review log

Round 1 (revision `e57ab8c`; builder check and critical review, both
`claude-code/claude-fable-5-1`):

- C1, the own-then-agree rule refuses *B*'s republish after it adopts *A*'s update while
  keeping P1 mounted: **fixed**, §7 rule 3.3 and Y19.
- I1, in-place revision of a carried record locks the write root with no sanctioned exit:
  **named**, §4.1, §10 item 1, science's surface rule in §8.
- I2, a damaged carrier makes the owner's records unreadable, and "present" was undefined:
  **fixed**, §5.0 holder states and §5.1's damaged-holder rule.
- I3, W18 already exists: **fixed**, rows renumbered W19/W20.
- I4 and the builder's first question, `content` published without a reader: **fixed**, its
  one reader is the damaged-holder rule (§4.3, §5.1, §5.3).
- I5, the silent pick in `_denoted` and gather's two candidate loops: **fixed**, named in
  §5.4.
- I6, science's `mount_holding`/`cited` refuse two holders: **added** to §8.
- M1, M9 (misattributed code and reason): **fixed**. M2 (rules fold into sets): **stated**,
  arms in W19. M3 (`_mapped_view`, inbound `source_uid`): **fixed**, §5.1, §5.2. M4
  (consulted-contract pins): **stated**, §5.4, §8. M5 (v2 narrowing is a Y5/Y17 amendment):
  **fixed**, §7 step 4. M6 (audit double filing): **ruled intended**, §5.4. M7
  (`iter_stored` order, audit sites): **fixed**, §5.2, §5.4. M8 (`explain` wording):
  **handed to science**, §6, §8.
- Builder's second question, Y19's "byte-identical markers": **fixed**, §7 compares the
  frozen tuple and the marker member under one intent's inputs.

Round 2 (revision `fe7539c`; re-review, `claude-code/claude-fable-5-1`): I1 to I6 and the
minors judged sound except as below.

- F1 and F5, rule 3.3 ordered the holders' markers under two inconsistent conditions:
  **fixed**, §7 orders the distinct claims' origin markers with a least-element condition;
  the re-adopted-own, third-party and sibling-tip cases are worked and in Y19.
- F2, a chain gap commons §10.2 sanctions refused without naming the gap: **named**, §10
  item 3; the refusal carries the claims and `show`'s naming is handed to science (§8).
- F3, the §4.4 redirect is not an exit for a content revision: **fixed**, §4.1 and §10
  item 1 state the content freeze and its true exits.
- F4, science's `adopt` needed the uid-corruption and deprecated-key checks: **fixed**, §8's
  three-item checklist and §10 item 2.
- F6 (`derive_pins` before the v2 narrowing): **stated intended**, §5.4. F7 (markers of
  holders with no selected record; invalid marker refusal): **fixed**, §7 rule 3.3. F8
  (earliest origin as a retention reason): **stated**, §7. F9 (damaged-refusal naming and
  the intended asymmetry): **fixed**, §5.1. F10 (damaged holders unreachable at publish):
  **fixed**, §7.
