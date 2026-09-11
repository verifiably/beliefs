# World resolution, slice 2b — source addresses derived from the normalized identifier

**Status:** designed 2026-09-10; not yet frozen. Task `beliefs-b7994b`, under
`beliefs-d248ba`. Sibling of slice 2
(`2026-09-10-world-resolution-slice-2-design.md`), which re-filed W1, W2 and
W5a here (§1 and §12 there). Freezes as **conformance cut 25** by a dated
commit after review clears; W1, W2 and W5a are **intended closures** until the
selected acceptance and sabotage checks pass.

Amends: world addressing §4.2 (the `source` row) and §4.4 (an enrichment
shape); the address ruling §4.1 (the source renderer reads the basis); the
writer-session design (nine session-mediated writes); the facet-contracts
design (one reader-shaped facet); both copies of `CONTRACT.yaml`; the guide's
identity page and glossary; the roadmap's W-row table; the adoption ledger's
current-state summary; `open-questions.md`.

## 1. What this slice is

The world address ruling upholds basis-derived addressing (§2 there) and
names `source` as the one kind whose basis is an identifier issued by the
world: "external identifier — DOI, PMID, ISBN, accession — normalized" (world
§4.2). The builder does not do it. `stored.source_node(slug, ...)` takes an
authored slug, so two papers sharing a citekey collide at the world layer and
two records of one DOI do not — the two halves of world §1.1, and exactly the
rows W1 and W2 test. W5a's source arm — correct an identifier and assert one
entity, `uid` preserved, address renamed, old address resolving through
`deprecated_ids` — has no seam at all: `revise` refuses `source`, so
identifiers are immutable after mint and the §4.4 mis-transcription rename
cannot be performed.

This slice derives the address from the normalized identifier, builds the one
seam through which a source's identifiers change, and makes the write and read
boundaries check both. Measured 2026-09-10: 78 `source_node` call sites across
18 test files, 31 literal `source:` refs in tests, none in `src`; seven of the
test files are phase modules of frozen cuts (§10.6).

**Rows it intends to close.** W1, W2, W5a (both arms; the dataset arm as the
system stands, §10.3).

**Rows it does not touch.** W14 (the label renderer and lookup-participation
row) stays with slice 4's read side; this slice supplies the basis the
renderer will read and nothing else. W8b stays measured. Dataset
re-addressing — `dataset_node` carries the same authored-slug defect while
`dataset_address` is computed and never checked against the id, 189 sites —
is a sibling task (§12), not this slice.

## 2. Decisions

1. **The address is a digest.** `source:` followed by
   `sha256` under the domain `science.source-address.v1` over
   `{"scheme": s, "value": v}` — the shape every other governed kind already
   has, collision-resistant under domain separation (`encode ∘ π` on the
   basis is injective; the digest is what W1/W2 rest on), and never in conflict with `nodes`' slug grammar
   (`[A-Za-z0-9][A-Za-z0-9:_.-]*`, which no DOI satisfies). A readable
   encoding was rejected: it is a second encoding to specify, and it would
   make `source` the one kind whose address is not a digest.
2. **Fixed precedence chooses the basis.** `doi > pmid > isbn > accession`;
   the highest-precedence scheme present derives the address, the rest ride
   in the facet. Two curators holding the same identifier set mint the same
   address. The consequence is stated and ruled, not hidden: `{pmid: P}` and
   `{doi: D, pmid: P}` are two bases and two addresses, and W2 means *same
   selected basis*, never *any shared identifier* (§6.4). A single declared
   basis was rejected because identical knowledge could mint two addresses;
   refusing more than one identifier was rejected because real records carry
   both a DOI and a PMID.
3. **Canonicalize and refuse malformed.** Builders normalize; write
   boundaries require `normalize(scheme, value) == value` and refuse
   otherwise. Every entry is validated before the basis is selected, so a
   valid DOI cannot hide an unknown scheme or a malformed PMID. A
   syntactically impossible DOI is mis-transcription evidence at the
   cheapest moment.
4. **The stored form is canonical.** Two spellings of one DOI are one facet,
   one stamp, one address. Storing the authored spelling and normalizing only
   for the address would give one address two stamps, which is W2's "one
   identity" failing at the next comparison.
5. **The correction is attributed on the record.** The §4.4 rename must be
   "attributed to an attester and recorded". An act-report was considered
   and rejected: it needs a ninth operation kind, and `report.OPERATION_KINDS`
   is pinned byte-exact by cut 19's frozen arm J1e, which every later cut
   prefixes. The corpus's idiom for an attributed judgement is a record
   carrying `actor`, `grounds` and an event token (retraction, coreference
   attestation), and act-reports report operations; so the assertion lives
   in an identity-inert `identifier-correction` facet on the source, and the
   seam is a session-mediated `corpus-write` like `retract` — no act-report,
   no new operation kind, no frozen literal touched.
6. **No referrer is rewritten.** `nodes`' `Corpus.rename` rewrites
   referrers; this slice does not use it. Content-identity bases,
   `π_claim`, retraction targets and relations read exact addresses (ruling
   §5.3), and the redirect in `deprecated_ids` is what keeps them resolving.
7. **Source only.** Dataset re-addressing is measured and filed, not built
   (§12).

## 3. The address

**New module `python/src/beliefs/source.py`**, on `dataset.py`'s precedent —
one module owning one kind's basis projection.

```python
SCHEMES = ("doi", "pmid", "isbn", "accession")          # closed, in precedence order
SOURCE_ADDRESS_DOMAIN = "science.source-address.v1"

def normalize(scheme: str, value: object) -> str: ...     # raises IdentifierMalformed
def normalized_identifiers(identifiers: Mapping[str, object], *, accepted: Sequence[str]) -> dict[str, str]: ...
def basis(identifiers: Mapping[str, str]) -> tuple[str, str] | None: ...
def source_address(identifiers: Mapping[str, str]) -> str | None: ...
```

`stored.ACCEPTED_EXTERNAL_IDENTIFIERS` **stays as it is**, byte-identical
(*amended 2026-09-10 at planning: an earlier draft re-exported `SCHEMES`
there; cut 4's frozen arm W3 sabotages that exact literal in `stored.py`, and
`test_n2_cut4.py` fails hard on a stale arm*). The accepted set is that
literal; `SCHEMES` is the same set in precedence order, and `source.py` keeps
its own rule table keyed by scheme. The drift hazard of two spellings is
closed two ways: a unit test pins
`set(SCHEMES) == set(stored.ACCEPTED_EXTERNAL_IDENTIFIERS) == set(_RULES)`,
and `normalize` treats a scheme that is accepted but has no rule as an
invariant violation (`LookupError`, never `IdentifierMalformed`) — which is
also what keeps W3's sabotage (`"url"` appended to the accepted literal)
sound: the migrated check expects `unknown-scheme` and gets an error instead.
Acceptance is checked in `stored.py` against its literal before any rule
runs; `source.py` imports nothing from `stored`.

### 3.1 `normalize`

`IdentifierMalformed(WriteRefused)` carries `scheme`, `value` (repr-safe)
and a closed `reason`:
`unknown-scheme | not-a-string | empty | malformed | non-canonical`.
`non-canonical` is the boundary's reason (§5): a stored value the rule would
have changed.

**Refusal order, pinned.** Entries are examined in sorted key order and the
first refusal wins. Per entry: `unknown-scheme` (the key is not in `SCHEMES`)
→ `not-a-string` (the value is not a `str`) → `empty` (after trim and prefix
strip the remainder is empty — so `""`, whitespace-only, and a prefix-only
input such as `doi:` are all `empty`) → `malformed` (the remainder fails its
scheme's shape). `{"unknown": 1}` is therefore `unknown-scheme`, and
`{"doi": "", "pmid": 5}` is `empty` on `doi`.

| scheme | canonical form | `malformed` when |
|---|---|---|
| `doi` | NFC; trim; strip one leading `doi:` or `http://`/`https://` + `doi.org/` or `dx.doi.org/`, case-insensitively; lowercase the remainder | the remainder does not match `10\.[0-9]{4,9}/[^\s]+` |
| `pmid` | trim; strip one leading `pmid:` case-insensitively | the remainder does not match `[1-9][0-9]*` |
| `isbn` | trim; strip one leading `isbn:` case-insensitively; drop hyphens and spaces; uppercase; ISBN-10 (`[0-9]{9}[0-9X]`) has its check digit verified and is converted to ISBN-13 (`978` + nine digits + recomputed check); ISBN-13 (`[0-9]{13}`) must begin `978` or `979` (the International ISBN Agency's two prefixes — a structural check, no authority lookup) and has its check digit verified | neither length, a check digit fails, or a thirteen-digit remainder lacks the `978`/`979` prefix (`0000000000000` is checksum-valid and refused) |
| `accession` | trim; uppercase | the remainder does not match `[A-Z]+[A-Z0-9_.]*` |

Form only, throughout. `NC_000913.3` and `NC_000913` stay two identifiers; the
DOI suffix fold is the DOI handbook's own case-insensitivity; ISBN-10 → 13 is
a deterministic re-encoding of one number. No authority is consulted and no
identity is inferred (ruling §4.2: "authority evidence normalizes form only").

### 3.2 `normalized_identifiers`, `basis`, `source_address`

`normalized_identifiers` validates **every** entry in the order §3.1 pins —
key in `SCHEMES` else `unknown-scheme`; value through `normalize` — and
returns the canonical map.
It is total over the map before any selection happens. Today
`external_identifiers` silently ignores an unknown key and an empty value;
both are the coercion the ruling forbids and both now refuse.

`basis` returns the first `(scheme, value)` present in `SCHEMES` order, or
`None`. `source_address` is `None` when `basis` is, else
`"source:" + v1.digest(SOURCE_ADDRESS_DOMAIN, {"scheme": s, "value": v})`.
`None` is `dataset_address`'s shape: the projection is never applied to
nothing, so no empty-basis address exists.

## 4. The builder and the readers

`stored.source_node(*, title: str, identifiers: Mapping[str, object]) -> Node`
— the `slug` parameter is **removed**. The builder calls
`normalized_identifiers` (its refusals propagate), refuses an empty map with
`BasisMissing` (it cannot mint an id without a basis), stores the canonical
map under `SOURCE_FACET`, and derives the id. It never attaches an
`identifier-correction` facet.

Readers, all in `stored.py`:

- `external_identifiers(node)` — unchanged signature; still the sorted scheme
  names present, still the contract's reader for the `source` facet.
- `source_basis(node) -> tuple[str, str] | None` — `basis` over the stored map.
- `identifier_corrections(node) -> tuple[IdentifierCorrection, ...]` — the
  reader for the new facet, raising `MalformedRecord` on any shape §5.2
  refuses. `IdentifierCorrection` is a frozen value:
  `from_identifiers`, `to_identifiers` (both `Mapping[str, str]`), `actor`,
  `grounds`, `event_token`.

## 5. The write boundary

### 5.1 `_refuse_source`

`_refuse_missing_basis` splits into `_refuse_source(node)` and
`_refuse_dataset_basis(node)`; **both** are called from `_refuse` and from
`_preflight_replace_locked`, which bypasses `_refuse`. The dataset check is
unchanged in content. For a `source`, in order:

1. `SOURCE_FACET` holds a mapping with an `identifiers` mapping, else
   `ValidationRefused`.
2. Every entry through `normalize`; a value the rule would change refuses
   `IdentifierMalformed(reason="non-canonical")`; unknown scheme, non-string,
   empty and malformed refuse with their own reasons. Every entry, before
   any selection.
3. At least one entry, else `BasisMissing` (W3, unchanged in meaning).
4. `node.id == source_address(identifiers)`, else
   `SourceAddressDisagreement(WriteRefused)`.
5. `stored.identifier_corrections(node)` invoked explicitly — reader-shaped
   facets are not validated by `validate_payload`, so the call is the
   validation; `MalformedRecord` becomes `ValidationRefused`.
6. Redirect agreement (§5.2's last clause), over the history the reader
   returned — empty history, empty `deprecated_ids`.

This runs for hand-built and imported records as well as builder output,
which is what makes W1/W2 a boundary guarantee rather than a builder habit.

### 5.2 Well-formed history

`identifier-correction` is declared on `source` in both copies of
`CONTRACT.yaml` as `{ required: false, covered: false }` and in `facets:` as
`{ shape: reader, reader: stored.identifier_corrections }`. Identity-inert
does not mean freely editable: the reader refuses, and every write path and
both read paths (§8) invoke it.

Payload: `{"entries": [entry, ...]}`. Well-formed means all of:

- `entries` is a non-empty list. An empty list is malformed; **absence** of
  the facet is the no-history state.
- Each entry is a mapping with exactly `from`, `to`, `actor`, `grounds`,
  `event_token`. `from` and `to` are mappings over accepted schemes whose
  values are canonical non-empty strings (validated through `normalize`,
  every entry); **both** `from` and `to` are non-empty maps; `from != to`. `actor`, `grounds` and
  `event_token` are non-empty strings; the whole entry is canonically
  encodable under `science.identity.v1` (a lone surrogate is malformed).
- Event tokens are distinct across entries.
- **Continuity:** `entries[i].to == entries[i+1].from` for every `i`, and
  `entries[-1].to ==` the current `SOURCE_FACET` identifiers.
- **Redirect agreement:** let `held` be the set of
  `source_address(m)` over every `from` and `to` map in the history.
  `set(deprecated_ids) == held − {node.id}`, `deprecated_ids` holds no
  duplicate, and is written sorted. With no history, `deprecated_ids` is
  empty — so ordinary `add` cannot manufacture a redirect without carrying
  the facet it is refused for carrying.

Who may write it: `add` refuses a source carrying the facet
(`ValidationRefused`: history is minted by `correct_identifier` only);
`import_bundle` admits a well-formed one as provenance, on the
imported-actor precedent, under the same encodability requirements as
locally minted history; `correct_identifier` requires the successor's
entries to be the current entries plus exactly one; `revise` continues to
refuse `source`.

## 6. The seam — `correct_identifier`

Three layers, the `attest_coreference` shape:

- `CorpusWriter.correct_identifier(ref: str, identifiers: Mapping[str, object], *, grounds: str) -> Node`
- `OperationWrites.correct_identifier(...) -> OperationCommit` — one
  `corpus-write` intent and one registration, no act-report; the
  writer-session design's "eight session-mediated writes" becomes nine,
  amended by dated note.
- `ScopedWriter.correct_identifier(...) -> Node` — the ledger's `act` line.

### 6.1 Envelope

Permit `corpus-write` on `("source",)` first. Then, under `_operation`, in
this order:

1. `_require_pins_agree()`.
2. `ref` resolves in this corpus's view — live or deprecated id — else
   `CorrectionRefused(reason="target-missing")`. The live record is the
   subject.
3. The subject's kind is `source`, else `CorrectionRefused(reason="not-a-source")`.
4. The **current** record passes `_refuse_source` (§5.1) — a raw-edited
   subject is refused before anything is appended.
5. `identifiers` through `normalized_identifiers` (its refusals propagate),
   and the supplied map must **equal** its normalized form — the seam does
   not canonicalize on the caller's behalf; an uppercase or URL-form DOI
   refuses `IdentifierMalformed(reason="non-canonical")` here, before the
   `unchanged` comparison can absorb it. At least one entry, else
   `BasisMissing`.
6. `grounds` is a non-empty, canonically encodable string, else
   `CorrectionRefused(reason="grounds-empty")`.
7. If the new map equals the current map, refuse
   `CorrectionRefused(reason="unchanged")`.
8. Build the successor from a deep copy of the subject: `SOURCE_FACET`
   identifiers replaced by the new map; one history entry appended —
   `{from: current, to: new, actor: authority.actor, grounds, event_token: secrets.token_hex(16)}`;
   if `source_address(current) != source_address(new)`, `id` becomes the
   new address and `deprecated_ids` becomes `sorted(held − {new id})` with
   `held` as §5.2 defines it — so an A→B→A return makes A live again and
   removes it from the deprecated set; `stamp_semantic_identity` recomputed.
9. The successor passes `_refuse_invalid`, `_refuse_facets`,
   `_refuse_source` (every clause of §5.1 and §5.2 including redirect
   agreement), `_refuse_governed_stamp`, `_refuse_rendering`.
10. Collision: `index.resolve_uid(successor.id)` is `None` or
    `subject.uid`; anything else is `CollisionRefused`. A retired address of
    *another* record collides — W14's retired address is a canonical address
    that stopped being live. Checked before submission.

`CorrectionRefused(WriteRefused)` carries a closed `reason`:
`target-missing | not-a-source | grounds-empty | unchanged`.

### 6.2 Effects

One executor submission, then `_reconstruct()`:

- address moved → `[CreateOp(new_path, content), DeleteOp(old_path, expected_digest)]`;
- address unchanged → `[ReplaceOp(path, content, expected_digest)]`.

`expected_digest` is the captured manifest entry's digest for the old path,
as ordinary replacement uses it — the stored bytes, formatting included.
The old path is `_relative_path(subject)`, the new `_relative_path(successor)`.

No referrer is read or rewritten. Failure classes are cut 19's J2: every
refusal above precedes the intent and has no effect; a fault after
submission is `ExecutionError`, the root stays unresolved until settled, and
reconciliation classifies the intent from the chain. The create/delete pair
makes the applied-prefix cases material (§10.3).

### 6.3 What the seam asserts, and what it derives

The maps derive the *change*: `from ⊂ to` is enrichment, a value present in
`from` and absent from `to` is removal or replacement. They cannot establish
that a removed identifier was mis-transcribed rather than legitimately
replaced by an authority. The seam's contract is therefore the actor's
assertion, supported by `grounds`: **"same work; the removed identifiers were
erroneous."** The other §4.4 cases are other calls — "genuinely different
work" is `add`, "two identifiers legitimately exist, as two records" is
`attest_coreference` — and none of the three invokes another. That is W5a's
negative: no case chooser exists. The system records who asserted what, on
what grounds; it cannot prevent a false assertion, only attribute it.

### 6.4 The precedence ruling

One predicate governs whether the address moves, in every shape:
`source_address(from) != source_address(to)`.

| `from` vs `to` | address |
|---|---|
| enrichment adding only lower-precedence identifiers | unchanged; `ReplaceOp` |
| enrichment adding a higher-precedence identifier | moves (the scheme changed); old address retained |
| a value corrected within the selected scheme | moves (the value changed) |
| the selected identifier removed, exposing a lower one | moves (the scheme changed) |
| a non-selected identifier corrected or removed | unchanged |

World §4.4's table gains the enrichment row by dated note: one record and one
work gaining an identifier that always existed is a rename, not an
attestation, because an attestation needs two records.

## 7. Relocation and lifecycle

- `move` admits with provenance and therefore carries the history and
  `deprecated_ids` across roots unchanged; `_refuse_source` runs at the
  destination's preflight.
- `consolidate` **refuses** when the two replicas' `identifiers` maps differ
  or their histories differ (`HistoryDisagreement(RelocationRefused)`,
  `AddressDisagreement`'s sibling). `_reconcile`'s union of `deprecated_ids`
  is unchanged and, over identical histories, is the identity. Reconciling
  divergent histories is filed as its own design (§12); silently keeping the
  survivor's history under a matching address set was the defect this rule
  closes.
- `delete` removes the record; its retired addresses stop resolving with it.
- `supersede` and `revise` do not reach `source`; unchanged.

## 8. The read side

- `validated_node` invokes `stored.identifier_corrections` after the stamp
  checks; a malformed history raises on read as the stamp checks do
  (`FacetPayloadRefused`, the existing exception the finding loop already
  maps to `facet-payload-malformed`).
- The check view's finding loop invokes the reader for every `source` and
  records `facet-payload-malformed` on the facet key, alongside the
  `validate_payload` findings it already records for schema-shaped facets.
- `ReadView.resolve`, `world/view.py`'s locate, and the epoch address map
  already consult `deprecated_ids`; nothing changes there. A published
  epoch's address map carries the retired address beside the live one
  (derive.py `address_map`).
- The label renderer is slice 4's; the ruling §4.1 row for `source` is
  amended to say the renderer reads `source_basis`.

## 9. Refusals, named

| refusal | where |
|---|---|
| `IdentifierMalformed(scheme, value, reason)` | builder, `_refuse_source`, seam step 5, history validation |
| `BasisMissing` | builder, `_refuse_source`, seam step 5 |
| `SourceAddressDisagreement` | `_refuse_source` |
| `ValidationRefused` (history malformed; facet on `add`) | `_refuse_source`, `add` |
| `CorrectionRefused(reason)` | seam steps 2, 3, 6, 7 |
| `CollisionRefused` | seam step 10 |
| `HistoryDisagreement` | `consolidate` |
| `ImportRefused` naming the member | `import_bundle` over any of the above |
| `FacetPayloadRefused` / `facet-payload-malformed` | read (§8) |

## 10. Testing and the cut

### 10.1 Unit

`tests/test_source_address.py` (new): the normalization table per scheme —
accepted spellings folding to one canonical form, each refusal reason
reachable, ISBN-10 → 13 with a wrong check digit refused, a checksum-valid thirteen-digit
number with a wrong prefix refused, the pinned refusal order over `{"unknown": 1}`,
`""`, whitespace and prefix-only input, every entry
validated before basis selection (a valid DOI beside a malformed PMID
refuses); precedence over every subset of the four schemes; a pinned digest
for one `(scheme, value)` so the address domain cannot drift silently; the
builder storing canonical forms and refusing an empty basis; `source_basis`;
`identifier_corrections` over every malformed shape — empty entries,
non-canonical map, unknown scheme in a map, broken continuity, `from == to`,
duplicate token, unencodable grounds, redirect-set disagreement, duplicate
deprecated id, history-free record with a deprecated id.

`tests/test_identifier_correction.py` (new): the refusal order of §6.1 with
each reason reached by the earliest step that can reach it, a non-canonical
supplied map refused before `unchanged`; unmoved
(`ReplaceOp`), moved (`CreateOp` + `DeleteOp`) and A→B→A return with A live
again and absent from `deprecated_ids`; the current record validated before
append (a raw-edited subject refuses); referrers byte-unchanged; `add`
refusing the facet; import admitting provenance and refusing each malformed
shape naming the member; `consolidate` refusing divergent maps and divergent
histories and accepting identical ones; `move` carrying history; the
session and scoped forms with the ledger `act` line and no act-report;
`validated_node` and the finding loop over a raw-edited history.

All DOI fixtures are valid under §3.1 — `10.1234/abc` and its
`https://doi.org/10.1234/ABC` spelling, never `10.1/abc`.

### 10.2 Migration

78 `source_node` sites lose the slug; 31 `source:` literals become the built
node's `id`; tests handing `identifiers={}` to reach `BasisMissing` at the
boundary build the record with `governed_node` instead; every abbreviated DOI
fixture (`10.1/x`, `10.1/abc`, …) is repaired to a valid registrant, not only
de-slugged. Seven of the 18 files are frozen-cut phase modules (§10.6).

### 10.3 Acceptance

`tests/acceptance/test_source_address_acceptance.py` (new), over
`work_directory` with the `durable_world` fixture shape, one durable arm per
row clause:

- **W1:** three pairs sharing a title and a citekey-shaped display, distinct
  DOIs → six records, six addresses; `resolve("source:Chen2023")` is `None`
  in the corpus, and over a published epoch `WorldReadView.locate` answers
  `Unknown` and `resolve` `None` — no handle participates in lookup.
- **W2:** one DOI in two spellings → one address; the second `add` refuses
  (`RecordAlreadyMinted` for the same `(uid, id)`, `CollisionRefused` for a
  fresh `uid`). The same DOI minted in two corpora → epoch publication
  refuses `AddressMapConflict(code="duplicate-location")` and no epoch is
  published; `consolidate` the pair; publish; assert one location.
  **Negative:** `{pmid: P}` and `{doi: D, pmid: P}` are two addresses and
  nothing is inferred from the shared PMID.
- **W5a, dataset arm:** attempt an in-place resource change through
  `revise` → `ReviseOutsideAllowlist`; mint the re-held dataset as a new
  entity; assert the prior assessment still bound to the old one and the two
  content identities distinct. Its protection gets a targeted sabotage
  (§10.5). Dataset address derivation stays the sibling task's.
- **W5a, source arm:** correct a source's DOI → `uid` preserved, id moved,
  the old id resolving through `deprecated_ids` in the corpus and in a
  published epoch's address map; a `source-assertion` anchored in the old
  address and a retraction whose `grounded-in` relation names it (a source
  is not an eligible retraction `NodeTarget`; the grounds reference is the
  edge a retraction may hold to a source) are byte-unchanged and still
  resolve. **Negative:**
  the seam has no case parameter; `add` with the new DOI mints a second
  entity; `attest_coreference` over the pair is the third arm; none of the
  three invokes another.
- **Failure boundary:** a refusal at each §6.1 step → no intent, no effect,
  no file moved; the moved operation faulted after submission with each
  applied prefix (create applied, delete not; both applied, readback
  faulted) → `ExecutionError`, `unresolved` set, reconciliation classifies
  the intent, and after settlement exactly one record stands with the
  subject's `uid`, a consistent history and redirect set.
- **Lifecycle:** `move` a corrected source → history and `deprecated_ids`
  intact at the destination; `consolidate` two replicas → one address,
  history intact; two replicas with divergent histories → refused; `delete`
  → the retired address stops resolving too.

### 10.4 N2 sabotages

`tests/acceptance/n2_arms_cut25.py`, audited by `test_n2_cut25.py` on the cut
12 pattern with the staleness baseline taken from the tree. One per
mechanism: drop the DOI lowercase fold; drop the prefix strip; reverse
precedence; select the basis before validating the map; drop the address
check from `_refuse_source`; drop `_refuse_source` from
`_preflight_replace_locked`; drop `_refuse_dataset_basis` from `_refuse`;
drop the deprecated-set rebuild; rewrite referrers (route through `nodes`'
`Corpus.rename`); drop the actor bind; drop the `unchanged` refusal; drop the
current-record validation before append; let `add` admit the facet; drop the
import validation branch; drop the reader from `validated_node`; drop it from
the finding loop; drop the history-free/empty-`deprecated_ids` clause; drop
the `from != to` clause; drop `consolidate`'s history comparison; skip the
ISBN check digit; admit an unknown scheme; admit an empty value; drop the
dataset revision's resource-preservation comparison in
`_revise_dataset_locked` (the W5a dataset arm's protection, which no earlier
cut sabotages). Each sabotage is validated against its actual site and its
named checks before the accounting freezes.

### 10.5 The cut

Conformance cut 25, numbered after cut 24, `python/tools/cut25_acceptance.py`
with `PREFIX_RUNNERS = ("cut24_acceptance.py",)` and
`PHASE_MODULES = ("test_source_address_acceptance.py", "test_n2_cut25.py")`.
Declaration units `W1`, `W2`, `W5a`, single-homed. All three are intended
closures; each is marked closed only when its selected acceptance and
sabotage checks pass. Frozen by dated commit after review.

### 10.6 Frozen evidence and live tests

Cut documents, declaration tables and `n2_arms_cut*.py` bodies of cuts 19–24
are not edited. Their **live** phase modules —
`test_permit_acceptance.py`, `test_durable_corpus.py`,
`test_facet_acceptance.py`, `test_relocation_acceptance.py`,
`test_coreference_acceptance.py`, `test_session_acceptance.py`,
`test_deletion_acceptance.py` — call the old builder with abbreviated DOI
fixtures and must keep running; they receive the documented fixture migration
(slug removed, DOI repaired, `source:` literal replaced by the built id) and
nothing else. Where a frozen arm's `before` string names a line this slice
must change and the arm is only probed for staleness, it is left as it
stands and its staleness recorded against the tree baseline. One arm is
audited live, not merely probed: cut 16's `M3a` matches
`self._refuse_missing_basis(node)` in `corpus.py`, and `test_n2_cut16.py`
requires that matcher to occur exactly once, which the split into
`_refuse_source` and `_refuse_dataset_basis` breaks; recording the staleness
in cut 25 cannot satisfy cut 16's own audit, and cut 16 sits on every later
prefix chain. The declaration table `n2_arms_cut16.py` stays frozen;
`test_n2_cut16.py` gains a **dated live matcher adapter** for `M3a` in its
existing `_LIVE_SABOTAGES` pattern (the 2026-09-07 facet-contract migration
is the precedent), asserting the same thing over the split lines.

## 11. Shared files, under roadmap concurrency rule 3

`stored.py` (builder, readers, the re-exported tuple), `corpus.py`
(`_refuse_source`, `_refuse_dataset_basis`, `correct_identifier`,
`OperationWrites`, `validated_node`, the finding loop, the import branch),
`session/writer.py`, `relocation.py`, `errors.py`, both `CONTRACT.yaml`
copies, and the 18 test files. Slice 3 (snapshot/import/audit callers) and
slice 4 (view evaluation, W14) touch `world/` and `audit.py`; this slice
touches neither beyond reading them. At most two kernel lanes open.

## 12. Task linkage

`beliefs-b7994b` carries this spec; the implementation plan's tasks become
its children. Two siblings are filed under `beliefs-d248ba`:

1. **Dataset addresses derived from the content identity** — `dataset_node`
   takes an authored slug while `dataset_address` is computed and never
   checked against the id; 189 `dataset_node` sites measured 2026-09-10;
   the choice between `dataset:sha256:` as the address and a digest domain
   is that design's.
2. **Reconciling divergent identifier-correction histories at
   `consolidate`** — this slice refuses them (§7).

## 13. Limitations and open questions

1. **A blocked address is not released.** A mis-transcribed identifier that
   is some *other* work's real identifier leaves that address claimed as a
   retired id of the corrected record for as long as that record exists:
   the history retains every address ever held, and a further correction
   only extends it (an A→B→A return makes A live again, no more). Releasing
   an erroneously claimed address needs an explicit future design.
2. **Accession normalization is form-only.** No namespace authority is
   consulted; `GSE1234` and a hypothetical same-string accession in another
   database are one identifier here. The accepted-authorities question in
   `open-questions.md` stays open with this noted.
3. **A false assertion is attributed, not detected** (§6.3).
4. **Precedence makes some same-work pairs two addresses** (§6.4); the
   shared secondary identifier is a CI-decidable finding for slice 3's audit.
5. **The renderer is not built**; W14 is slice 4's.

## 14. Review log

- 2026-09-10, design review in session, four passes: (1) address form,
  choice rule, strictness, attribution and dataset scope decided; (2) §A
  tightened — dataset admission preserved on both paths, canonicality made
  explicit with every entry validated before selection, the precedence
  consequence stated, well-formed history defined with explicit reader
  invocation; (3) §B corrected — collision admits the subject's own `uid`,
  one address-change predicate, the assertion attributed to the actor
  rather than derived, validation wired into both read paths and before
  and after append, `from != to` per entry, the history-free redirect
  loophole closed, relocation ruled, `expected_digest` from the captured
  manifest, the `unchanged` wording reversed; (4) §C corrected — valid DOI
  fixtures and their migration, W2's epoch expectation as the
  `duplicate-location` refusal, W5a's dataset arm strengthened with its own
  sabotage, failure-boundary coverage added, frozen evidence separated from
  live phase modules, the blocked-address limitation corrected, both
  contract copies named, closures marked intended.
