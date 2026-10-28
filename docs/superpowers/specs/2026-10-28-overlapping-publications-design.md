# Overlapping publications: one address held in several live corpora

**Status:** accepted by the user at revision 10, `e14315c` (round 10, 2026-10-28); the
implementation plan follows. Revision 8 (`a451082`) had a scoped re-review of its
additions (round 8, verdict revise: 0 Critical, 4 Important, 6 Minor;
`claude-code/claude-fable-5-1`); revision 9 (`d6a5d47`) the user's third forwarded
review (round 9, verdict revise: 1 Important; reviewer `codex/gpt-6-astra`), which
confirmed the merge checks and the versioned input and moved the fixture-schema check off
the removal path. All resolved in §13. Revision 7 (`77e4a79`)
had the user's second forwarded review (round 7, verdict revise: 2 Important; reviewer
`codex/gpt-6-astra`), which confirmed the successor-rule approach, rejected the
route-namespace assumption, and ruled on beliefs-c800ef and beliefs-ae33ff; §4.5 now
carries a versioned rule input and a self-checking snapshot merge. Revision 5 (`c94a899`)
had a scoped re-review (round 5, verdict revise: 1 Critical, 3 Important, 6 Minor) whose
Critical moved §4.5's fold from the capture into a successor rule version, the direction the
repository had already banked; revision 6 (`d6e2aea`) a scoped re-review of that ruling's
rules-store mechanics (round 6, verdict revise: 0 Critical, 4 Important, 6 Minor); both
`claude-code/claude-fable-5-1`. Revision 1 (`e57ab8c`)
had a builder check and a critical review (round 1, verdict revise: 1 Critical, 6
Important, 9 Minor); revision 2 (`fe7539c`) a re-review (round 2, verdict revise: 0
Critical, 5 Important, 5 Minor); revision 3 (`930de28`) a scoped re-review (round 3,
verdict revise: 0 Critical, 1 Important, 7 Minor), all three `claude-code/claude-fable-5-1`;
revision 4 (`4f8413e`) the user's forwarded review (round 4, verdict revise: 2 Important;
reviewer `codex/gpt-6-astra`), which confirmed the six rulings of §3 to §8 and required
correction-record semantics (§4.5) before planning. Every finding is resolved below and §13
lists the dispositions.
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
  corpus, so a record appearing once per holder in `rule_input` adds nothing twice. The
  retraction rule keys on `(ref, resolution)` and says in its own words that "the same ref
  with two resolutions is two" findings.
- A retraction's captured `resolution` is computed **per corpus**: `epoch._captured_records`
  folds `_standing_retractions` over that corpus's own `ReadView`, so it reflects the
  counters that corpus holds; `read.validate_receipt` re-reads each named corpus under its
  hold through the same `_captured_records` (`read._standing`) and reruns the held rule over
  the rebuilt `rule_input`, refuting a receipt whose projection differs byte for byte.
  `gather` folds standing again over the world view (`retraction_standing(view, facets)`,
  which resolves targets through the world map) and refuses
  `RetractionResolutionDisagreement` when its fold disagrees with a recorded pair; with a
  policy, `_check_filtered_world_standing` repeats the comparison per corpus over
  `_mapped_view(corpus_id)` and that corpus's accepted set. `snapshot_standing` folds per
  corpus over `_captured_views`, applying `counts(corpus_id, address)` inside each corpus's
  fold, unions the `retracted` sets and merges each subject's history chain across corpora
  with the later corpus winning per entry.
- The split this produces is banked. Correction-remainder slice 1 §11.1 names a
  counter-retraction `move`d apart from its target (a sanctioned `move`; the write boundary
  does not *mint* a cross-corpus target, slice 1 §11.3) as the case the evaluator refuses
  rather than misjudges, and names the remedy: "a world-wide fold at **derivation** rather
  than capture — a new version of the `retraction-enumeration` rule, its fixtures and its
  receipt identity". The retraction-standing backlog brief
  (`../../notes/2026-09-29-retraction-standing-backlog-brief.md`) keeps that as alternative
  2, rejects "make capture consult the whole world" as the default (alternative 3, "any
  revival needs evidence and reviewed design"), and files beliefs-c800ef (the successor
  rule) behind beliefs-ae33ff (whether `rule_input` carries enough to fold at derivation).
  `test_world_standing.py::TestTheSplit` pins today's refusal. Rules are world-held,
  content-addressed `(rule_identity, implementation_identity)` pairs with fixtures
  (`world/rules.py`); the four v1 rules are shipped in `rules_v1` and installed explicitly;
  science binds a build to the shipped bundles by symbol (`science/world_belief.py`).

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
  any in-place content change (`revise` is one route; anything that rewrites the canonical
  projection, metadata included, is the same) on an address a mounted carrier holds.
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
`CapturedRecord.projection()`: the v1 rule input (`Capture.rule_input` for
`science.rule-input.v1`, §4.5) and the four v1 fixture-bound rules are byte-identical to
today's, and the three receipt subjects other than the retraction enumeration do not move.
Those
rules fold a record that appears once per holder into one producer edge, one certification
ref and one coreference unit (§1); the retraction enumeration is the one subject whose rule
changes, §4.5. W19 carries arms that pin all four, so a future rule keyed on `corpus_id`
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

### 4.5 Correction standing under overlap

Equal content does not make two copies of a retraction equivalent: a retraction's
*standing* is a property of the correction graph around it, and two holders of one
retraction can hold different graphs without either copy changing. The 1b case produces
this by construction: *A* publishes P carrying retraction R; *A* later writes the
counter-retraction C in its write root; nothing rewrites R, so §4.1's content freeze is
respected, yet *A*'s fold overturns R and P's copy still upholds it. The per-corpus capture
(§1) would record both `(R, upheld)` and `(R, overturned)`, the retraction rule would keep
both pairs by its own stated rule, and `gather`'s world fold would refuse
`RetractionResolutionDisagreement` against whichever pair it did not reproduce.

**Ruling: correction standing is folded once, over the complete capture, after
record-level acceptance, and never per corpus; in the epoch, that fold lives at derivation
in a successor version of the `retraction-enumeration` rule, which is the remedy slice 1
§11.1 and beliefs-c800ef already name.** A retraction's standing in a world is the standing
of one record in one graph, the graph every present holder contributes to; the holders are
where the records were found, not separate worlds. 1b is the evidence the backlog brief
asked for before any revival of its alternative 3, and this design does not revive it: the
capture stays per corpus, and the world-wide reasoning stays at the derivation boundary,
where a held rule and its fixtures reproduce it under receipt validation. In detail:

- **At epoch capture.** The discipline does not change: each corpus is enumerated once
  inside its own hold, and `CapturedRecord.retraction.resolution` stays the per-corpus
  fold, the claim "nothing standing in this corpus retracts this retraction", validating no
  target exactly as `_standing_retractions`' docstring rules; the drifted-target arm it
  names still holds. What `_captured_records` builds gains two fields read by nothing in
  v1's projection: `content` (§4.2) and the retraction's `arm` (next bullets); its
  signature, its enumeration and the lines the live arms over it sabotage are untouched.
  The v1 rule input keeps its shape; the v2 input is a second projection.
- **At derivation: `retraction-enumeration` v2.** A second shipped rule bundle, module
  `rules_v1/retraction_v2.py`, symbol `enumerate_retractions_v2`, fixtures
  `retraction_v2.<case>.yaml` (the fixture discovery is by module prefix, so neither the
  module nor a fixture may be named `retraction.`; the package name `rules_v1` names the
  package generation and the three "four v1 rules" docstrings become "five"), and therefore
  its own `(rule_identity, implementation_identity)` pair. It folds standing over the whole
  of its input (the v2 rule input, next bullet): for every retraction whose `arm` is
  `node`, it resolves the authored target over every record's `address` and
  `deprecated_ids` across all corpora and adds the edge when it resolves, exactly the edge
  rule of `corpus.retraction_standing`; route-arm and snapshot-arm retractions are
  vertices, as in every fold today. It folds the graph in acyclic postorder and emits one
  `(ref, resolution)` per retraction address. No kind test and no namespace assumption
  stands in for the arm: a route identity is an authored string the target validator
  checks only for membership in the dataset's stamped routes, so a route identity equal to
  a retraction's address is admissible today, and a rule that inferred the arm from
  resolution would counter that retraction where the arm-aware fold does not, inside one
  corpus. v2's fixtures carry a node-arm, a route-arm and a snapshot-arm case, and the
  colliding-route case (a route identity equal to a retraction's address, retracted by
  route, with no edge added). The per-corpus `resolution` in its input is read by v1 only;
  v2's fixtures show inputs whose per-corpus resolutions disagree and the one world
  resolution the rule emits, which is what makes the semantic explicit and
  content-addressed.
- **Rule input versions.** The v1 rule input (`Capture.rule_input()` as it is: coverage,
  and per record `corpus_id`, `address`, `uid`, `kind`, `deprecated_ids`, `produces`,
  `retraction: {target, resolution}`, `certification`, `coreference`) is sufficient for the
  node-arm graph and insufficient to tell a node-arm target from a route-arm one; that is
  beliefs-ae33ff's complete answer, and it is an input insufficiency, not a namespace
  invariant. So the input is versioned, and the version is a property of the held rule,
  read from the store at build and at validation alike:
  - `CapturedRetraction` gains `arm: "node" | "route" | "snapshot"`, captured from the
    validated facet beside `target`. `CapturedRecord.projection()` is unchanged, which keeps
    the v1 input, every v1 fixture's key set and v1's identities exactly as they are;
    `Capture.rule_input(version)` emits the v1 projection for `science.rule-input.v1` and,
    for `science.rule-input.v2`, the same projection with `arm` added to each retraction
    member (and nothing else added).
  - `RuleBundle` gains `input_version: str | None`, appended last with default `None` so
    positional constructions keep working. `None` means the stored document `{symbol}`,
    every rule held today: the four shipped v1 world rules, which a world build and
    `validate_receipt` read as `science.rule-input.v1`, and the holdings reduction bundle
    (`holdings/reduce.py`), the rules store's other producer, whose caller supplies its own
    capture (`holdings/receipt.py` resolves the pair through
    `_locked_resolve_rule_binding` and never consults the version); `input_version` is a
    property of world enumeration rules only, and the holdings invocation sites are
    unchanged. `retraction_v2` carries `science.rule-input.v2`, the one value `input`
    admits. The stored rule document admits two closed shapes: `{symbol}` and
    `{symbol, input: science.rule-input.v2}`; `parse_rule_document` returns the symbol
    and the version, reads the first shape as `None`, and refuses any other document, a
    document naming v1 explicitly included, so each rule has one encoding (the §4.3
    pattern). A v2 bundle's rule identity digests `[symbol, fixture-set, input]` under the
    existing `science.enumeration-rule.v1` domain (a three-member list cannot collide with a
    two-member one); v1 identities keep their two-member formula and do not move. This
    amends by citation the pinned definition "a rule identity is `(symbol, fixture-set
    identity)`" in the normative contract design §6 and world-index slice 2 §4.1, the
    `rules.py` module docstring, and
    `test_world_rules.py::test_the_rule_identity_is_the_pinned_domain_over_symbol_and_fixture_set`,
    each with a dated note; `contracts/` carries no rule-identity text, which is what §11's
    "no contract release" means. `_HeldRule` carries the version; `_BuildDraft.run(kind)`
    and `validate_receipt` hand each held rule `rule_input(held.input_version)`. The
    fixture runner hands a rule its fixtures' literal inputs, so the one-ABI-per-version
    property is a conformance check, and it lives with the running half of the held check,
    never the naming half: a fixture-schema check, applied only to a bundle or document
    that declares an input version (unversioned world rules, the holdings bundle and
    generic fixtures are untouched), verifies that every fixture input's record key set is
    the declared version's, and runs in `install_rule_binding` before any identity is
    computed or write plan exists (a v2 bundle with a fixture missing `arm` cannot be
    installed, whatever its implementation returns) and in
    `_locked_resolve_rule_binding` beside `_run_fixtures` (raw-written content that
    violates it is not resolved for a build or a validation). `_locked_stored_rule` stays
    limited to document and identity integrity, so `remove_rule_binding` can still unhold
    an intact, correctly named pair whose fixtures or implementation have stopped
    conforming; the existing removal contract and its tests stand.
    `test_world_derive.py::test_every_shipped_fixture_carries_a_captured_view` pins the key
    set per input version.
  Rule content may import nothing (`TestPurity`) and so can raise only a plain exception, and a
  fixture pins outputs, never refusals; so (a) the kernel wraps a rule raise at
  `_HeldRule.invoke` into `RuleNonconformant` naming the subject kind and the pair, which
  `build_epoch` propagates and `validate_receipt` reports exactly as it reports a
  nonconformant output (`refuted`), and (b) v2's two refusals, a live or deprecated id
  claimed by records of distinct uids and a counter cycle, are pinned by direct tests over
  the shipped bytes, not by fixtures. The collision refusal is defensive: `_derived_members`
  derives the address map **before** running the rules, so `AddressMapConflict` and the
  deprecated-key `ResolutionRefused` keep precedence and a refused build names the real
  fault. The cross-holder cycle is reachable only through raw writes (the write boundary
  mints neither edge) and refuses at derivation, where a one-corpus cycle refuses
  `RetractionCycleMalformed` at capture, before it. The fold is written twice, in the rule
  and in `corpus.retraction_standing`, since the rule may share no code; an equivalence arm
  folds every v2 fixture input (the colliding-route case included) and every W19 world
  fixture through `retraction_standing` over a merged `_CapturedCheckView` and asserts the
  same resolutions.
- **Identities.** The rule identity and the receipt's `rule_identity` move; the subject
  domain `science.retraction-enumeration.v1`, the enumeration member's shape
  (`derive.retraction_enumeration` parses v2's output unchanged) and the belief closure
  digest do not. A v1-bound and a v2-bound epoch over a world with no split therefore
  publish byte-identical enumeration members and closure digests, and that is intended:
  the semantic change travels in the receipt's rule identity alone.
- **Binding and installation.** v1 stays shipped and held; v2 is shipped beside it in the
  same package and installed by the composition root with the others (slice 2 §4.2;
  `install_shipped_world_rules` installs every shipped bundle, which is what keeps legacy
  receipts resolvable; the two "four bundles" count pins become five). Which pair a build
  uses is the caller's binding. Every helper that joins shipped symbols to subject kinds is
  a dict keyed by symbol (science's `SYMBOL_FIELDS`; the test suite's `SYMBOL_KINDS`,
  `install_bindings`, `hold_shipped` and cut 7's `shipped_bindings`), so adding the v2
  symbol beside v1's would silently rebind by the dict's iteration order and omitting it would raise
  `KeyError`: the test helpers take an explicit retraction version so that W19's paired
  arms can express both bindings, and science's `SYMBOL_FIELDS` change **replaces** the v1
  symbol's entry (§8). A v1-bound build over an overlapping world behaves exactly as today
  (two pairs, refused by the reader), so nothing changes for a world that does not rebind.
  R23's retained rules-store clauses (install a newer rule beside the old, the old receipt
  still validates, unhold the old and it is `unresolvable`) describe exactly this state;
  shipping v2 neither discharges nor alters them, and the plan cites them when it checks
  `contract-cut`.
- **Receipt validation.** `validate_receipt` reruns the exact held pair over the
  recaptured corpora, so a v2 receipt reproduces v2's fold from the same per-corpus
  inputs, and a legacy v1 receipt still validates under v1. No epoch is refuted by this
  cut.
- **In `gather` without a policy.** The world fold over the view's held records resolves
  targets through the epoch's address map, which is derived from the same addresses and
  deprecated ids v2 resolved over, so it is the same fold over the same records and
  `RetractionResolutionDisagreement` can arise only from drift, as today for one holder.
  Under a v1 epoch the check keeps refusing the split, as today.
- **In `gather` with a policy.** A retraction is accepted iff any captured holder accepts
  it (§6); the accepted facets are folded once over the merged mapped view; and the
  fidelity check `_check_filtered_world_standing` becomes one comparison rather than one
  per corpus: the "affected" set is every rejected retraction and, transitively through the
  retraction-discovery map, every retraction one of them counters; for every surviving
  retraction outside that set the filtered fold must reproduce the receipt's resolution.
  The per-corpus `_mapped_view` iteration and the second local-versus-world comparison go
  away, since there is one fold, and that fold is `gather`'s own world fold: the view's
  `resolve` already resolves through the epoch map alone (never `_captured_views`), which
  is G12-g's mapped-only obligation, so no separate merged mapped view is needed. The
  receipt lookup refuses explicitly when the enumeration carries two resolutions for one
  ref (a v1 epoch over a split), rather than keeping the pair sort order leaves last, so
  the policy path refuses the split by rule as the no-policy path does.
- **Snapshot standing.** `snapshot_standing` keeps its signature and folds once over a
  merged view of every captured corpus's records, mapped and drift alike (a post-build
  record has no epoch address and still enters the fold, as today). The merge checks its
  own well-definedness and relies on no caller: `read._snapshot_standing` captures the
  receipt's corpora directly, before the availability phase, and never opens a
  `WorldReadView`, so the view's checks at open are not evidence here. Before collapsing
  anything, the merge applies the address map's own classification to the records in hand:
  two records of one uid under different live addresses refuse `AddressMapConflict
  ("uid-corruption")`; two records of one uid whose content identities differ (which
  includes a snapshot-arm retraction naming different subjects) refuse
  `AddressMapConflict("duplicate-location")`, as do records of distinct uids at one live
  address (§4.2 rule 2); a deprecated id that is another record's live address, or that is
  claimed by records of differing content identity, refuses the deprecated-key
  `ResolutionRefused` (§4.2 rule 3); each names the uid or address and every holder, in
  capture order, never a chosen copy. The checks run between records of different holders
  only, since a corpus's own index already enforces id uniqueness, so a one-corpus caller
  is unchanged. Only records of one uid with one address and one content identity collapse
  to one. `_CapturedCheckView` keyed by id would otherwise let insertion order decide which
  copy the fold sees. With a
  policy, a retraction enters the fold iff `counts(h, address)` is true for **some**
  holder `h` of it, each holder's decision recorded as §6 says, so a counter accepted
  through one holder overturns a retraction accepted through another. Target validation
  (`_validated_retraction`, `_resolve_retraction_target`) runs over the merged view, so a
  counter in one holder resolves its target held in another. Each subject has one chain in
  `history`, built from the one fold, and no holder order can overwrite it. Through the
  receipt path: `read._snapshot_standing` catches the merge refusal and returns the
  `unresolvable` outcome together with a `Finding` (the conflict's own for the two
  `AddressMapConflict` cases; `Finding("error", "deprecated-key-collision", <address>,
  <holders>, …)` for the `ResolutionRefused` case); `validate_receipt` returns the outcome
  (this world cannot say what it holds, the `ResolutionRefused` precedent, never `retracted`
  and never an exception) and drops the finding; `reported_receipt` returns both, beside
  the `retraction-unreadable` it already returns for an unreadable chain. Through a
  `WorldReadView` the refusal propagates as an exception from `gather`, as
  `RetractionUnreadable` does. A local `ReadView` caller (one corpus) is unchanged for any
  corpus its own index admits.
- **The local enumeration and corpus-local standing** (`local_retraction_enumeration`,
  `standing_in_local_view`) are one-corpus reads and do not change.

One behaviour change outside overlap, under a v2-bound build: a counter-retraction
`move`d apart from the retraction it counters (slice 1 §11.1's split; a sanctioned `move`,
not a raw write) was `upheld` with its target in the per-corpus enumeration and refused by
`gather`'s world fold; under v2 the enumeration overturns the target and the world reads.
`TestTheSplit`'s obligation flips with it, slice 2 §14.2's retained limit is retired by
citation, and W19 pins the new behaviour on the same fixture.

Rejected: folding at capture after the holds and teaching `validate_receipt` the same fold
(this revision's round-5 draft). It revives the backlog brief's alternative 3: the
reproducibility a receipt vouches for would then rest on unversioned kernel code rather
than a held, fixture-bound rule, validation of every legacy epoch over a split state would
refute until rebuilt, and the per-corpus capture boundary would be crossed for no gain the
derivation boundary does not give. Also rejected: keeping per-holder resolutions and
letting the enumeration carry both pairs (the rule says two pairs are two findings; the
closure digest would move with holder-set membership and `gather` would still refuse);
refusing the build when holders' graphs differ (it refuses the ordinary act of countering
one's own published retraction, which commons §4.4 and §4.8 require to be a new
publication, not a rewrite); and folding per holder with the record counted if any holder's
fold stands (wrong in the plain case: with R and its counter C in *A* and R alone in *B*,
*B*'s fold upholds R while the graph overturns it).

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
- `captured() -> tuple[str, ...]`: the captured corpus ids, sorted (the keys of
  `_captured`). Publish reads non-selected holders' markers through it (§7); it is not
  `registry.admissions`, which also lists corpora admitted after the epoch.
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
| `evaluation.py` `_check_filtered_world_standing` | inventory per corpus by `corpus_of`, one fold per corpus | one comparison against `gather`'s world fold over the view's map-only resolver, with the record-level accepted set (§4.5); no per-corpus iteration |
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
- Correction records follow §4.5: acceptance is decided per record over its holders first,
  and standing is then folded once (the v2 rule in the epoch; `gather`'s world fold at
  read; the merged fold in snapshot standing). The existing per-corpus fold in
  `snapshot_standing` does **not** implement this union (a counter accepted through one
  holder only would be dropped from the other holder's fold, the subject would stay in
  `retracted`, and the history would be merged in holder order), so it is replaced by the
  merged fold, and the filtered fidelity check becomes one comparison.
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
      claim exists (two candidates would need a cycle among held markers, the state
      `publication_tip` refuses as `supersession-cycle`, and the "exactly one" clause
      refuses it here). Marker *X* supersedes *Y* when *X* names *Y* in
      `supersedes_markers`, transitively through the markers of every captured undeclared
      `ReplicaOf` holder in the world view (`captured()`, §5.2), those holding no selected
      record included; `Fresh`, `ForkOf` and declared own holders carry no marker and are
      not read. Those extra markers are read **only when this rule is reached**, so a stale
      marker in an idle replica cannot refuse a publish rules 3.1 and 3.2 settle; one that
      fails layout or release validation then refuses `attribution-source-invalid` naming
      its holder with empty `refs`. The order is a property of the claimed markers, not of
      which holders carry them, so *B*'s re-adopted own publication beside P1 and P3, or a
      third party holding P2 and P3 but not P1, both resolve to P1. No live source is
      reopened: `_selected_attributions` already reads captured markers, and attribution
      design decision 5 already forwards an entry whose named origin is not held;
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
Two consequences science's retirement policy must expect. A recipient's own republication
names P1 in its entries, so any downstream world that adopts it beside P1 keeps P1 mounted
under commons §10.3. And the order is readable only through held markers, while retirement
is irreversible (commons §10's state table): once *B* keeps P1 and *A* publishes P7
superseding P3, retiring P3 would leave P1 and P7 with no held marker connecting them, and
every record they attribute differently would refuse for as long as P1 is kept. So §8 adds
a retention requirement: while a predecessor is dependency-kept, every publication on the
supersession chain from it to the current tip of the same `(view, destination)` stays
mounted, a `keep` the surface sets rather than the user. The alternative, carrying
transitive ancestry in the marker, is a coordination-release change and is named in §10
item 3 as the follow-up if the user prefers it.

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

1. every key, live or deprecated, that the candidate shares with a live record belongs to
   a record of equal content identity (§4.2 rules 2 and 3; content includes the id, so a
   live address meeting another record's deprecated id, or two differing records sharing a
   deprecated id, refuses, and differing content at a shared live address is commons
   §10.5's case);
2. no candidate uid is held live under a different canonical address (`uid-corruption`,
   §4.2 rule 1; an ordinary §4.4 identifier correction published as a successor produces
   this against the predecessor, and the candidate's live ids alone do not reveal it).

Science must also amend, with the same equality contract: its session-holder resolution
(`science/config.py` `mount_holding` and `cited`, which refuse any address two mounts hold,
content aside, before the kernel is consulted); its `explain` wording for a rejected copy of a
record that counted (§6); its pins, which must cover every mounted holder a world read may
attribute (§5.4); a surface rule refusing any in-place content change on an address a
mounted carrier holds (§4.1); the chain-retention rule of §7 (a dependency-kept predecessor
keeps every publication between it and the current tip mounted); `show`'s naming of the
marker whose adoption would order an `attribution-ambiguous` refusal's claims (§7, §10 item
3); and the rebinding of §4.5: `science/world_belief.py` `build_over` installs every
shipped bundle and maps rule symbols to `DerivationBindings` fields through
`SYMBOL_FIELDS`, a dict keyed by symbol, so the change there **replaces** the v1 symbol's
entry with `enumerate_retractions_v2` (adding it beside v1's would rebind silently by the
dict's iteration order), after which every new epoch science builds carries v2's fold and v1 stays
installed for the epochs that name it. Those changes are science's tasks and are not made here; the completion note on
sci-4a3543 names them.

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
- **G12** (cut 45): "mapped-only local oracle" and "split-corpus disagreement" read over
  the one fold of §4.5. Cut 45's live arms whose sabotage text sits inside
  `_check_filtered_world_standing` (G12-d, G12-g, G12-h, G12-i, G12-l) are retargeted;
  G12-g's obligation is re-pinned on the view's map-only resolver; G12-h's
  local-versus-world comparison is retired with the comparison; G12-a/b/c over gather's
  `counts(holder, canonical)` and G12-e over `counts` inside `snapshot_standing` are
  retargeted to the per-holder loops. Cut 34's BI-3 and BI-9 sit outside the rewritten
  functions; BI-4 and BI-8 inside `snapshot_standing` are re-read. The lines cut 7's
  `_RELOCATED_HEAD` (in `_capture`'s hold block), cut 27's W13-b (the `CapturedCorpus`
  append), cut 24's W15h (the coreference branch) and cut 39's Y1-b (the `WORLD_KINDS`
  filter) sabotage are untouched by the two fields `_captured_records` gains, so those
  arms stand. `test_world_standing.py::TestTheSplit`,
  `test_acceptance.py::test_g12_h_split_with_exclusion` and
  `test_g12_l_accept_all_refusal_parity[split]` change obligation under a v2-bound build
  (§4.5) and are rewritten, not retargeted; `test_arm_staleness` discovers the rest.
- **Y5/Y17** (publication design, cuts 46 and 47): the holder-set rule and the v2 narrowing
  of §7; the order rule is the new Y19.

**New rows**, appended at freeze to the tables their subject belongs to. W18, G13 and Y18
are the last used at this baseline, so the ids are W19, W20, G14 and Y19; the plan confirms
them against the tables at freeze.

| Row | Obligation | Decisive checks |
|---|---|---|
| W19 | The address map admits one record held in several corpora and refuses differing content, deprecated keys included; under the v2 rule a retraction's derived resolution is one fold over the whole rule input, the captured per-corpus resolution unchanged | equal content in two or three corpora maps one entry with sorted holders in either capture order; shared uid with differing content, and distinct uids, refuse `duplicate-location` naming every claim; `uid-corruption` still outranks; a deprecated key reached through two holders is one entry; a deprecated key colliding with a live or differing record refuses the typed `ResolutionRefused` in both input orders and both same- and cross-corpus; the projection is the new closed shape; a legacy epoch reads as singleton holders and a mixed document refuses; a retraction held twice is discovered once (W19-f); a record held twice contributes one producer edge, one certification ref and one coreference unit to the receipts; **differing correction graphs under v2:** *A* holds R and its counter C and *B* holds R alone, the v2-bound build publishes one `(R, overturned)` in either capture order, `validate_receipt` validates it and `gather` without a policy agrees, while the same world under v1 publishes both pairs as today; with R, C and D (countering C) in *A* and R and C in *B* the enumeration says `upheld`; a counter-retraction cycle across holders refuses as in one corpus; a counter `move`d apart from its target (`TestTheSplit`'s fixture) is overturned under v2 and the world read agrees; a rule input with one id under two uids refuses `RuleNonconformant` through the kernel wrap, after the address map's refusal, pinned over the shipped bytes; route-arm and snapshot-arm retractions are vertices in v2's fixtures, and a route identity equal to a retraction's address, retracted by route, adds no edge in v2 nor in the world read, inside one corpus; v2's resolutions equal `retraction_standing` over the merged records for every fixture and world fixture; a v1-held rule reads the v1 input and a v2-held rule the v2 input at build, at validation and in the fixture runner, and the v1 fixtures' key sets are unchanged; a v2 bundle with a fixture lacking `arm` refuses at install before any write and, raw-written, refuses at resolution, while an intact, correctly named pair whose fixtures or implementation no longer conform is still removable; the enumeration's receipt identity is the same in both holder orders and the closure digest is unchanged for a world with no split; v2's fixtures hold in both input orders; a v1-bound and a v2-bound build are both expressible by the test helpers |
| W20 | World reads serve a multi-holder record once and refuse holders that disagree | `open_world_view`, `evaluate_live_query` and `resolve_address` serve equal-content holders once with `Location.holders` naming them; captured holders whose copies differ refuse `ResolutionRefused` and never `NotPresent`; `NotPresent` only when every holder is absent and `Resolved` with one present; a shared uid the map did not establish still refuses at open; a damaged holder is skipped when a captured copy equals the mapped content and refuses otherwise, including for a legacy entry; inbound edges are not duplicated and a source held by any holder is present; `contributing` names every captured holder and disagreeing pins refuse; `_mapped_view` sees the record under each holder |
| G14 | Acceptance is a union over holders, reports every holder's decision, and correction standing is folded once over the merged records after it | a record rejected under one holder and accepted under another is read once, counts, is attributed to the accepting holder, and the rejected pair is in `excluded`; rejected under every holder it is inert; the predicate is asked once per holder; the 1b decisive case under `accept = [B]`; retractions and verifications held twice follow the same rule and are traced once; **filtered correction graphs:** with *A* holding R and C and *B* holding R, a policy rejecting C through its only holder leaves R upheld in the filtered fold and the fidelity check passes with C's rejection reported, while a policy accepting C overturns R; with both holders holding R and C and C accepted through *B* only, R is overturned; **snapshot standing:** with both holders holding the snapshot-arm retraction R and its counter C, R accepted through both and C through *B* only, the subject is not retracted and its history lists R `overturned` and C `upheld` as one chain, in both holder orders; a counter accepted through one holder whose target is held in the other resolves and validates; a drift record at a mapped address under another uid refuses the fold naming both holders rather than shadowing either copy; **through the receipt path directly** (`validate_receipt` and `reported_receipt` on the producer receipt, no world view opened), two copies of one uid with differing content, and two with differing canonical addresses, each in both holder orders, yield `unresolvable` with the conflict's finding and never `retracted` |
| Y19 | A republication's attribution over several holders is a function of the holder set and the held supersession chains | own holder wins over a carried copy with no entry; two carriers agreeing on an origin forward it; claims whose markers have a least element under supersession yield it (the 1b P1/P3 case; the re-adopted own publication beside them; a third party holding P2 and P3 without P1; sibling tips over P1); a chain P7 → P3 → P1 with P3 held but holding no selected record is read through P3's marker, and that marker is read only when rule 3.3 is reached; claims with no common held origin (unrelated publishers; a chain with its intermediate unheld) refuse `attribution-ambiguous` before intent, carrying the claims; publish → adopt → republish with holders reordered yields equal frozen attribution tuples and marker members; v2 names only the holders of carried records; retries use the frozen tuple |

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
   explicitly and offers no pick; the surface rule, refusing any in-place content change on
   a carried address, is science's (§8).
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
   the two ends of a chain whose intermediate marker it never adopted (the state commons
   §10.2 keeps as an unresolved link) refuses `attribution-ambiguous` for every record the
   ends attribute differently, until it adopts the intermediate. Retirement is irreversible,
   so an intermediate the recipient retired leaves the refusal standing for as long as the
   predecessor is kept; §8's chain-retention rule is what prevents that state, and the
   refusal carries the claims so the surface can name the marker. `publication_tip` has the
   same one-hop blind spot today. The alternative that removes the limitation, a marker
   carrying its transitive ancestry, is a coordination-release change filed as a follow-up
   only if the user prefers it to the retention rule.
4. **Equality is exact.** Any difference in the canonical projection, metadata timestamps
   included, is a different record. Publish preserves the projection, so this binds only
   copies that were edited, the write root's included (item 1).
5. **A damaged holder is skipped only against a published content identity.** Under a
   legacy entry, or when the captured copy differs from what the epoch mapped, the shared
   address refuses as a single damaged holder does today.
6. **Legacy epochs stay singular** until rebuilt; nothing migrates them. A legacy epoch
   bound to `retraction-enumeration` v1 keeps validating under v1 and keeps v1's split
   refusal at read; a world gets v2's fold only by rebinding and rebuilding (§4.5).
7. **Authenticity is unchanged.** Own-wins attribution rests on the existing rule that a
   byte-equal copy in an own holder is the publisher's; this design adds no proof of
   authorship. The supersession order is read from markers the recipient holds, which are
   validated for layout but, as today, not authenticated.
8. **No measurement of cost.** Per-holder acceptance calls and per-holder audit filing are
   linear in the number of holders; nothing here caches across calls.

## 11. Verification, surfaces and constraints

Primary code: `world/derive.py`, `world/epoch.py` (`_check_addresses`; `_derived_members`
derives the address map before the rules, §4.5; `_capture` and `_captured_records` keep
their signatures and return values, which `test_world_epoch.py` and `test_world_build.py`
monkeypatch; `_captured_records` keeps its signature and returns `CapturedRecord`s with
two more fields), `world/rules_v1/` (`retraction_v2.py` and its `retraction_v2.*.yaml`
fixtures, listed in `rules.py`'s `_SHIPPED`), `world/rules.py` (`RuleBundle.input_version`,
the two closed `rule.yaml` shapes and `parse_rule_document`'s return, the v2 rule-identity
formula with its dated amendment notes on the normative contract design §6 and slice 2
§4.1, `_HeldRule`'s version and its wrap of a rule raise, the versioned fixture-schema
check in `install_rule_binding` and `_locked_resolve_rule_binding` with
`_locked_stored_rule` and `remove_rule_binding` untouched; R23's rules-store clauses are
cited by the plan when it checks
`contract-cut` before freezing), `holdings/reduce.py` and `holdings/receipt.py` only as the
rules store's other producer and consumer, which do not change, `root.py` only as the
installer of every shipped bundle (no new write primitive; `install_shipped_world_rules`
already iterates them; its "four v1" docstring becomes five), `world/read.py`
(`_address_map`; `validate_receipt`'s per-version input and its `unresolvable` outcome for
a merge refusal; `_snapshot_standing`'s outcome-and-finding return; `reported_receipt`'s
finding),
`world/view.py`, `world/live.py`, `world/selection.py`, `world/registry.py`
(`content_identity` exposed), `evaluation.py` (gather's loops and
`_check_filtered_world_standing`), `audit.py`, `publish.py`, `corpus.py`
(`MountCitations`, `_absence_of`, the coreference endpoint refusal, `snapshot_standing`'s
merged fold), `errors.py` (`attribution-ambiguous` reason text). Tests also include
`test_world_build.py`, `test_world_standing.py`, `test_standing_read.py`,
`test_snapshot_retraction.py`, `test_acceptance.py`, `test_correction_acceptance.py`, the
rules-store tests (`test_world_rules.py`'s bundle count and the composition-root install
count become five) and the binding helpers `test_world_build.SYMBOL_KINDS`,
`test_world_receipts.install_bindings`/`hold_shipped` and cut 7's `shipped_bindings`, which
gain an explicit retraction version. Tests: `test_world_derive.py`,
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

Also to preserve: the admission checklist handed to science (§8), the three named
limitations of §10 items 1 to 3, and §4.5's one-fold rule for correction standing (the v2
rule at derivation, the filtered fidelity check as one comparison, and the merged snapshot
fold with its id-collision refusal), with acceptance decided per record over its holders
before the fold and the per-corpus capture untouched. On approval, also: scope
beliefs-c800ef to this cut as its reviewed design, leaving it open until the v2 rule lands
(design approval closes no implementation); close beliefs-ae33ff only with its complete
answer noted on beliefs-c800ef as its body asks: the v1 input carries the node-arm graph
and cannot distinguish node from route targets, so v2 takes the versioned input of §4.5;
and add science's rebinding to the completion note on sci-4a3543.

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

Round 3 (revision `930de28`; scoped re-review, `claude-code/claude-fable-5-1`): F1/F5, F3,
F6, F9, F10 judged sound; the four Y19 cases verified against the code.

- I1, a retired intermediate makes the chain gap permanent and 1b's steady state reaches
  it on *A*'s second update: **fixed** by the chain-retention requirement handed to science
  (§7, §8, §10 item 3), with marker ancestry named as the alternative.
- M1 (only undeclared `ReplicaOf` holders carry markers), M2 (`captured()` accessor), M3
  (extra markers read only when rule 3.3 is reached): **fixed**, §5.2, §7. M4 (checklist
  item 3 missed two differing records sharing a deprecated id): **fixed**, §8 item 1 now
  covers every shared key. M5 (§10.3 misread): **fixed**, §7. M6 (Y19 case for a
  non-selected holder's marker): **fixed**, §9. M7 (any in-place content change, not only
  `revise`): **fixed**, §4.1, §8, §10 item 1.

Round 4 (revision `4f8413e`; the user's forwarded read-only review, `codex/gpt-6-astra`).
Rulings received on the six proposals: content digest, multi-holder map with the explicit
legacy shape, narrowed owners check with representative labels, acceptance union with
rejected-copy reporting (principle confirmed, correction semantics to revise), the
own → agreement → earliest-origin attribution rule within the stated authenticity limit, and
J17 equal-content citations: all **confirmed**. The content freeze and the renamed-record
refusal are accepted as explicit limits provided science enforces §8's preflight checks;
chain retention is preferred over marker ancestry in this cut.

- Finding 1, equal retractions with differing correction graphs produce two receipt
  resolutions and a `gather` refusal: **fixed**, §4.5 folds the resolution once over the
  merged capture; W19 and G14 carry the case with and without a policy.
- Finding 2, the per-corpus snapshot fold does not implement the acceptance union and
  overwrites history in holder order: **fixed**, §4.5 and §6 fold once over the merged
  captured records after record-level acceptance; G14 carries the holder-order case with
  the verdict and the history.

Round 5 (revision `c94a899`; scoped re-review, `claude-code/claude-fable-5-1`): the
one-fold semantic, the filtered-check and snapshot cases, and round 4's two resolutions
judged sound in principle.

- Critical 1, `validate_receipt` recaptures per corpus through `_captured_records` and
  would refute a capture-side fold: **fixed** by moving the fold into a v2
  `retraction-enumeration` rule at derivation (§4.5), the banked remedy; the capture is
  unchanged and validation reproduces the held rule.
- Important 2, the draft silently revived the backlog brief's rejected alternative 3 and
  resolved beliefs-c800ef/ae33ff without citing them, and the split checks flip: **fixed**,
  §1, §4.5, §9 and §12 cite and dispose of them; legacy epochs keep validating under v1
  (§10 item 6).
- Important 3, the merged view is order-dependent for distinct uids sharing an id:
  **fixed**, §4.5's id-collision refusal in the snapshot fold and in v2's input.
- Important 4, the split arises by sanctioned `move`, not raw writes: **fixed**, §1, §4.5,
  W19.
- Minor 5 (derivation refusals precede the fold): **fixed**, §4.5. Minor 6 (arms named):
  **fixed**, §9. Minor 7 (the rejected alternative's counter-example): **fixed**, §4.5.
  Minor 8 (`_merged_mapped_view` duplicates the view's resolver): **fixed**, §4.5. Minor 9
  (`read._snapshot_standing`): **named**, §4.5. Minor 10 (history wording): **fixed**, §1.

Round 6 (revision `d6e2aea`; scoped re-review of the successor-rule ruling,
`claude-code/claude-fable-5-1`): round 5's Critical, Important 2 to 4 and Minors 5, 8 and 9
judged sound; two held pairs per subject kind, the address-map-first order and the
id-collision placement verified against the code.

- Important 1, rule content cannot raise kernel types or pin refusals in fixtures:
  **fixed**, §4.5 adds the kernel wrap at `_HeldRule.invoke`, its `validate_receipt`
  outcome, direct tests over the shipped bytes, and corrects the cycle claim.
- Important 2, `rule_input` lacks the target arm: resolved in revision 7 by a
  resolves-to-a-retraction discriminator under a route-namespace assumption, which round 7
  rejected; **superseded** by revision 8's versioned rule input (round 7, Finding 2).
- Important 3, symbol-keyed binding joins silently rebind or raise: **fixed**, §4.5, §8
  and §11 (explicit-version helpers, replace-not-add, the count pins and docstrings).
- Important 4, W19's "captured resolution": **fixed**, §9.
- Minor 5 (naming): **fixed**, §4.5. Minor 6 (equivalence arm): **fixed**, §4.5, W19.
  Minor 7 (subject domain and closure digest unchanged): **stated**, §4.5. Minor 8 (two
  recorded resolutions for one ref in the filtered lookup): **fixed**, §4.5. Minor 9
  (§5.4/§6 wording): **fixed**. Minor 10 (`read._snapshot_standing`'s outcome): **fixed**,
  §4.5.

Round 7 (revision `77e4a79`; the user's forwarded read-only review, `codex/gpt-6-astra`).
Rulings received: the successor-rule approach in this cut **confirmed**; the
route-namespace assumption **rejected**; beliefs-c800ef is scoped here and stays open until
the fold is implemented; beliefs-ae33ff closes only with its complete answer. The earlier
six rulings stand.

- Finding 1, the snapshot merge relied on checks `read._snapshot_standing` never runs, so
  two copies of one uid with differing content or addresses would collapse by holder
  order: **fixed**, §4.5's merge applies the address map's classification itself and
  refuses before collapsing; `validate_receipt` reports `unresolvable` and
  `reported_receipt` the finding; G14 carries the receipt-path cases in both orders.
- Finding 2, the missing target arm is an input insufficiency, not a namespace invariant:
  **fixed**, §4.5 versions the rule input (`arm` on each retraction member under
  `science.rule-input.v2`, the version held with the rule and read at build, validation
  and fixture run; v1's input, fixtures and identities untouched); the discriminator and
  the assumption are withdrawn; the colliding-route case joins the fixtures and the
  equivalence arm; §12 records ae33ff's complete answer.

Round 8 (revision `a451082`; scoped re-review of revision 8's additions,
`claude-code/claude-fable-5-1`): round 7's two resolutions judged sound; the versioned
input's consistency with storage, resolution and validation, and the merge's
implementability over the receipt path, verified against the code.

- Important 1, the merge's third refusal misclassified distinct uids at a live address:
  **fixed**, §4.5 follows §4.2's rules 2 and 3 exactly.
- Important 2, four sentences still said the capture and `rule_input` do not change:
  **fixed**, §4.2, §4.5, §9, §11.
- Important 3, the v2 identity formula amends a pinned definition uncited: **fixed**, §4.5
  cites the normative contract design §6, slice 2 §4.1, the module docstring and the
  identity test, and clarifies "no contract release".
- Important 4, the holdings bundle is a second producer and consumer: **fixed**, §4.5
  (`input_version` is optional and a property of world enumeration rules only) and §11.
- Minor 5 (the fixture runner cannot build inputs): **fixed**, the key-set check moves to
  resolution. Minor 6 (one encoding per version): **fixed**. Minor 7 (the
  outcome-and-finding seam and the deprecated-key finding code): **fixed**. Minor 8
  (one-corpus callers): **scoped**, cross-holder checks only. Minor 9 (stale round-6 log
  entry): **marked superseded**. Minor 10 (dict iteration order): **fixed**, §4.5, §8.

Round 9 (revision `d6a5d47`; the user's forwarded read-only review, `codex/gpt-6-astra`).
Rulings received: the independent snapshot-merge checks and receipt outcomes
**confirmed**; the versioned input carrying the target arm **confirmed**; the earlier scope
and task-closure rulings stand.

- Finding 1, the fixture-schema check in `_locked_stored_rule` would also gate
  `remove_rule_binding` and trap a correctly named nonconformant pair: **fixed**, §4.5
  places the check in `install_rule_binding` before any write and in
  `_locked_resolve_rule_binding` beside the fixture run, scoped to explicitly versioned
  world inputs; `_locked_stored_rule` and removal are untouched, and W19 pins both the
  install refusal and the removability.
