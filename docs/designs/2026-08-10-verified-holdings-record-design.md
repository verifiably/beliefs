# Verified holdings record — design

**Date:** 2026-08-10
**Status:** banked 2026-08-10; §8's amendment set applied in the banking change.
Nothing here is implemented, and no conformance arm is claimed —
the G9 independence arm and the record's code stay owed to the cut that draws
the persistence seam (§7).
**Inherits:** the admission ramp (`2026-08-09-admission-ramp-design.md`) §6.1
(state derived from declaration plus the system's record of verified holdings),
§6.2 (the dataset basis projection), §6.3 (`G9` and its arms), §6.7 and §8
item 2 (the record undesigned: where it lives, how it is re-checked, what makes
an entry stale); kernel §2.2 (held is possession and addressability, location-
and mechanism-independent); computation `R5` (belief does not depend on
availability in this checkout), `R10` (a URL-valued input routes to
acquisition), and the act-bound validation ruling (validation at explicit
import and audit, "mounting a volume is not an epistemic event", admission
changes because a node was recorded); world §5's producer snapshot (enumeration
bounded by a coverage declaration naming corpora by stable identity, because
enumeration against whatever is checked out is the R5 violation); the
correction lifecycle (revision by superseding record, never by edit); the
ramp's §4 retrieval boundary (preflight refusals, retrieval bounds, and the
`byte-locator-untested` / `retrieval-failed` vocabulary, reused as the acts'
dereference contract, §3); the tamper-evident log design (its own table `L`;
its `intent`/`fulfills` discipline, reused by managed mutations, §3;
guarantees stated at the strength they have until the composition root lands;
`atoms` A8 landed 2026-08-17);
conformance cut 2
(`2026-08-09-conformance-cut-2.md`) §2.1 item 1 — the slice consumes byte
observations as supplied arguments and settles nothing about their store, "an
argument's type is not a storage design."
**Constraints:** the frozen tables stay frozen under their identifiers; this
design adds its own table (**H**, §6), taking the corpus from eleven frozen
tables and 139 rows to **twelve and 143**. The cut-2 document is frozen: it is
amended by Status append only. No timestamp enters any derivation **under the
current projection rule** — the one sanctioned successor (§4) would read
`observed_at` and an explicit reference instant only as pinned,
receipt-committed derivation inputs, and lands by amending this constraint,
never by an ambient clock. No new attester class is privileged (`meta/`
measures reliability, nothing assumes it).

## 1. The gap, and the box already drawn around it

The admission ramp closed F2 by deriving a dataset's state — curation note,
`declared`, `held` — from the declaration and *the system's record of verified
holdings*, and then said plainly that no such record exists: where it lives,
how it is re-checked, and what makes an entry stale are undesigned (ramp §6.7,
§8 item 2). The cost is concrete and measured: 24 of the 47 surveyed records —
62 resources, 11.83 GB — are in a state no measurement can currently determine,
because answering for them is a search when it should be a lookup.

The bounds are already frozen, from three sides:

- **`R5`** — belief does not depend on availability in this checkout. The
  record cannot be a property of a checkout, and a derivation over "whatever
  happens to be here" is the violation whatever store it reads.
- **`G9`** — no API accepts an authored `held`. The record cannot be an
  assertion; it can only be the output of an act that hashed bytes.
- **Act-bound validation** — admission may change *only because a record was
  recorded*: at explicit import, or because an audit minted a superseding node.
  A filesystem changing shape is not an epistemic event. Any staleness
  semantics lives inside this ruling or contradicts it.

Cut 2 sharpened the consumer side without designing the supply side: the
evaluator's availability context takes byte observations *as arguments*,
matched by digest, location never read. This design is the supply side — what
produces those observations, where they persist, and how a caller comes to
hold a current set of them.

Two of the ramp's residues are decided here: the record itself (§8 item 2) and
the staleness of its entries, which is §8 item 1 — how long a probe's evidence
lasts — asked about the remote half. The third residue, the partly-pinned
rule's empirical corroboration, is evidence, not design, and stays open.

## 2. The record

A **holdings observation** is a world record: content-addressed, attributable,
append-only, revised only by supersession. One record spans **one location
claim** — what one act found at one locator — and nothing wider.

Canonical facet:

| field | content |
|---|---|
| `kind` | `holdings-observation` |
| `location` | a **typed, canonical** byte locator: `store(store identity, relative path)` for bytes in a managed store, or `url(canonical absolute URL)` for remote bytes. Each type carries its canonicalization rule, applied **at construction**. For `store`, the relative path is validated under the `atoms` coordinator's **project-relative path grammar, reused rather than redefined**: non-empty, UTF-8-encodable, no NUL byte, not absolute, no trailing separator, `/`-separated with no empty, `.`, or `..` component, reserved-sigil aliases refused. That grammar **refuses rather than normalizes** — `a/../b` is refused, never rewritten — so the canonical form is the accepted spelling itself, equality is byte equality, and a locator is well-formed exactly where the store's own mutations would accept the path. For `url`, the **exact profile**: scheme and host lowercased, default port elided, an empty path written as `/` — `https://host` and `https://host/` are one location, not two — dot-segments resolved, percent-encoding normalized **in the path component only** (uppercase hex, unreserved characters decoded), query preserved byte-exact — its percent-encoding untouched, since an origin may distinguish spellings there and normalizing would merge locations it does not — and **no fragment, no userinfo — both refused at construction**. A fragment never participates in an HTTP request, so spellings differing only there would name one retrieval as two locations; userinfo is a credential, and a credential must never enter immutable world content. The exclusion is **structural exactly as far as structure can see, and a stated caller obligation where it cannot**: an act takes a **canonical locator and nothing else** — URL retrieval is **unauthenticated-only today** (§3), so no grant parameter exists to leak, and userinfo is refused at construction. But capability material can ride in **any component structure cannot classify** — a signed query is byte-indistinguishable from an ordinary one, and a capability path segment or token-bearing hostname is equally opaque — so **credential-free authoring of the whole canonical URL is a caller obligation, not a checked invariant**, this record's analogue of the log's cooperative-write assumption, with its failure mode named rather than hidden: a credential authored into host, path, or query bytes enters immutable world content as location bytes, undetectably. A signed URL names an access grant, not a location, and the caller — who minted or received the grant — is the party that knows the credential-free form. Making the exclusion *checkable* is exactly what a typed grant would add, and is deferred with it (§7 item 8). Equality is field equality of the canonical form, and everything keyed "per location" (§4) keys on it. An opaque string cannot do this job: the same path spelling names different bytes in different stores, and one URL has many spellings, which would break dereferencing, the same-location refusal, and `H2` at once. The two types are the two every §3 act already dereferences; adding a locator type is an amendment (§7) |
| `outcome` | `found` with an **algorithm-qualified** digest `<algorithm>:<hex>`, or `absent`. Both are **established findings**: `found` means the act hashed the bytes it dereferenced; `absent` means the dereference completed and answered that the location holds nothing — today establishable **for a `store` locator only**: the identified root enumerated, the path missing. A `url` locator cannot currently mint `absent`: the inherited boundary classifies every transport and status failure — a 404 included — as `retrieval-failed`, and no qualifying authoritative negative is defined; defining one would be a ramp-boundary amendment, not a record change (§3). An attempt that established neither mints no observation (§3). **Qualification is the invariant, not the algorithm — and qualification is canonical**: the ramp's basis projection already normalizes every digest to `<algorithm>:<lowercase hex>`, and the record adopts that form at construction — lowercase canonical algorithm identifier, lowercase hex, the algorithm's exact width (64 for `sha256`) — refusing an unqualified digest (the survey instrument's rule, made a record invariant, because losing the algorithm is what broke the first freeze) and refusing a non-canonical spelling, since `sha256:AB` and `sha256:ab` would otherwise mint two records of one fact and miss every whole-digest join (§5). None of this freezes the accepted set — canonical form is per-algorithm, and the record stays **algorithm-generic**. Which algorithms may pin bytes is the profile's open residue (ramp §6.2), and the ramp is explicit that the instrument's own sha256-only bound "is its own rather than the profile's" — a capability limit of one tool. Freezing that limit here would make a future accepted declaration unobservable by construction: a basis it could carry, an observation it could never have |
| `expected` | optional: the algorithm-qualified digest the act *expected* at this location — an acquisition retrieving against a declaration records what it was retrieving *for*. This is the explicit expectation link that lets a first-contact mismatch surface at derivation (§5): `found(D′)` with `expected = D` joins to every declaration naming `D`. Promotion never reads it — held is decided by `outcome` alone, so the field adds an association, never an assertion. **With a `found` outcome, `expected` must share the found digest's algorithm — refused at construction otherwise**: an act whose instrument cannot hash in its expectation's algorithm established nothing about that expectation, so it omits the field and reports the unchecked expectation through its own channel — the ramp's rule, a refusal names the tool's limit where a `mismatch` would blame the corpus for it. The constraint is what makes every derivation-time mismatch a same-algorithm comparison (§5) |
| `observer` | the attester's identity — human or agent, equally weighted; reliability is `meta/`'s to measure, never this record's to assert |
| `instrument` | the identity of the tool that hashed or dereferenced — the survey instrument's commit-pinning discipline, generalized |
| `event_token` | minted by the act, one per act — the `retraction` / `coreference-attestation` / `run` precedent, whose token is what "keeps two genuinely distinct … events distinct". Without it, two identical findings by one observer at one location in one clock tick collapse into one identity — a piece of corroborating evidence silently lost — and `observed_at` cannot carry the guarantee: a timestamp has resolution, a mint does not. For every intent-bearing act (§3 — every managed mutation, and every store-dereferencing pure look) this token is the **same one its intent carries** — reused, never a second attempt id, the tamper log's own rule — and, together with the boundary-built `fulfills`, it is what qualifies an observation as its intent's fulfillment (§3) |
| `observed_at` | when the act ran, in **one canonical encoding**: exactly `YYYY-MM-DDTHH:MM:SSZ` — RFC 3339 UTC, whole seconds, **no fractional digits, no offset form** — so one instant has one byte form under the facet hash, and two conforming implementations cannot mint different identities for one act. **Recorded as data, never read by a derivation** (§4). It carries no uniqueness: distinctness of acts is `event_token`'s job, never the clock's |
| `supersedes` | zero or more identities of prior holdings observations, **every one for the same canonical location**. Constructing a record naming a predecessor at a different location is refused — the per-location discipline is by construction, not convention. The plural form is what lets a later act resolve a fork: concurrent observers cannot name each other, so one location can grow parallel heads, and the resolving re-check supersedes every head it replaces (§4). **Canonical representation, because `science.identity.v1` refuses sets:** the facet encodes `supersedes` as a **deduplicated sequence sorted by canonical reference bytes** before hashing — one predecessor set, one identity; anything else would mint one fork-resolution under several addresses, or none |

**The `store identity` a `store` locator names is not left undesigned — it
reuses the one lifecycle contract the corpus already has for exactly this.**
The tamper-evident log design gave the world root a `world_id`: minted once
at fresh initialization, preserved verbatim by replica, restore and cold
bootstrap, and a configuration/genesis mismatch **refuses** rather than
silently re-minting. A store's identity is that contract applied to a store:
minted at store initialization, carried in the store's genesis record,
surviving every move and replica *because it is data, not a path*. And replicas
are ruled **single-writer — structurally, not by prose**, because the chain's
one-tip invariant alone cannot enforce it: two disconnected copies each stay
perfectly linear, and become the log's malformed sibling state only if their
branches are ever brought together. So the rule is **fail-closed at the
engine: writability is a granted state, never a default — and exactly two
authorities grant it**: store initialization (the genesis mint) and the
explicit **fork act** (below), each recording the grant durably in the
host's engine bookkeeping. A **restore never does** — a restore that
granted writability would let two operators restore two metadata-less
copies of one `store_id` on two hosts and mint exactly the two cooperative
writers the rule exists to exclude — so a restored copy is a **read-only
replica, permanently under that identity**, and the only path from a copy
to a writable store is the fork, under a new `store_id`. The **replica act
stamps its copy read-only** in the same bookkeeping, outside the chain
(which a replica must carry unchanged) and outside the registered surface,
and the coordinator **refuses every mutation on a root not granted
writability**, except that a recorded root-creation operation may construct
its claimed destination while converging to its lifecycle state. The default,
not the stamp, is what carries the rule across
hosts: `atoms`' transaction metadata is **single-host by construction and
never travels with the tree**, and a tree arriving without it
cold-bootstraps — so a copied replica does not *lose its stamp into
writability*; a **metadata-less store root bootstraps read-only**, whatever
tree it was copied from, original included. And read-only is not yet
readable for holdings, because fail-closed mutation does not establish that
a copy is **complete**: an interrupted copy can carry genesis and chain
with payload files missing, and an audit over it would mint a false
`absent` for every uncopied path. So a metadata-less store root is
**unresolvable for holdings reads until an explicit restore act establishes
completeness** — by running the log's **verification act** as the admission
gate, under the verifier's own discipline rather than a bare replay: the
restore names the **store subject** and an **explicit observer set** of
eligible store anchors (the store-subject registry record or a supplied
exported head, §8), because a replay without an anchor would verify the
copy against itself — a truncated copy carries a chain its own surface can
match. Only a **`validated`** verdict admits the copy to service,
**read-only**; `refuted`, `malformed`, and `unresolvable` each keep their
verdict, the root stays unserviceable, and every dereference of it is an
inconclusive attempt (§3), never an `absent`. An empty observer set is
already ruled, not re-ruled: unresolvable relative to that set, replay
never reached — the verifier's own L9 bound, needing no new row. The cooperative steps still carry a
**durability order**: the stamp is durable **before** the copy is exposable
as a root — and a replica interrupted earlier is metadata-less, hence
read-only and unresolvable for holdings reads until restored, never a
writable twin — and the fork act's writability grant is
durable only **after** its new genesis is, so an interrupted fork is still a
read-only replica. That **fork act** is the one cooperative exit: it mints a
new `store_id` and a new genesis *before any write is spellable* — the log's
corpus-fork precedent applied to stores; parent and fork are separate
chains, never one chain with incomparable heads — and bytes written under
the fork are observations at a **different canonical location**, since the
store identity differs. Raw-granting writability in engine bookkeeping is a
raw mutation, §4's out-of-band bound beside raw `rm`; and detection of raw-written
copies of one `store_id` is **exactly as wide as the log's own rules, no
wider**: branches assembled in one root are sibling-malformed (its L3); two
divergent heads **both supplied as anchors in one observer set** refute (its
L9); but two copies diverging *after* their last common anchored head and
verified **separately** each validate — the differing tails are its L5's
unanchored residue — so detection requires assembly or co-anchoring, and the
never-co-presented pair is the surviving-observer negative, pinned in L10's
store instantiation (§8). What §4's contested machinery owns is concurrent
observers of **one** store: forks of evidence, never forks of the store.

Identity is the content identity of this facet under a new domain,
**`science.holdings-observation.v1`**, through `science.identity.v1`'s
`v1.digest`. Every field participates: two acts that found the same bytes at
the same location are two records **because each bears its own minted
`event_token`** — distinct evidence stays distinct however the clock reads,
including two acts in one clock tick — and §4 says what "current" means.

**Observations are declaration-independent.** A record says *bytes at L hash
to D* (or *L holds nothing*); it names no dataset. The join to datasets
happens at derivation time, by digest — exactly how cut 2's `admission_state`
already matches, location never read. One observation therefore serves every
dataset whose declaration names that digest, and an observation of unclaimed
bytes is recordable but promotes nothing: no declaration names its digest, and
the fabricated-basis rule is untouched — ramp §6.6's line stands, hashing
bytes a record never declared must never seed a declaration.

**A mismatch is not a record kind.** An act that found bytes hashing to `D′`
where it expected `D` records `found(D′)` with `expected = D` — the truth
about the bytes, plus the association that makes the disagreement reportable.
The mismatch itself is *computed* at derivation (§5), against each declaration
naming `D`, and reported as the ramp's `G9` arm requires: not promoted, and
not reported as a failure to retrieve. The record layer never decides which
declarations are affected; the join does.

## 3. Creation acts

Every holdings observation is minted by one of **exactly two act shapes**,
each per canonical location:

1. **A pure dereference.** An act that looks: it dereferences a canonical
   location under §2's contract and the boundary below, and records what the
   look established — `found` by hashing the bytes, `absent` where the
   dereference completed and answered that nothing is there (a `store`
   answer only, below). The audit and the explicit re-check are this shape —
   the admission-ramp survey is the standing example: an instrument
   dereferenced locations, hashed bytes, and reported — and so is the
   source-URL observation an acquisition mints (below). Each observation
   supersedes the prior record for its location, if one exists; a look that
   established neither finding reports and mints nothing (below). A
   store-dereferencing look appends its intent before it reads (below); a
   URL look is intent-free.
2. **A managed mutation.** A boundary-mediated store write, move, or
   deletion, run
   under the intent discipline (below), whose observation records the
   mutation's **post-state, captured before the mutation's lease releases**
   (below). A write reopens and hashes the destination bytes — never the
   source stream's hash, since a truncated or transformed write would
   otherwise attest bytes the store never held, exactly what H1 reserves
   `found` against. A deletion verifies the location holds nothing — the
   symmetric half — minting an `absent` that is **established, never
   inferred from its own return code**; this is `R5`'s negative (a) —
   destroy the last held copy, heldness ends — enacted the only way the
   act-bound ruling permits: because a record was recorded. A **move** —
   `atoms`' `MoveNoClobber`, one engine effect over a source and a
   destination — is one effect carrying **two holdings acts' evidence**,
   because a holdings act is per canonical location and one intent cannot
   name two: the boundary appends **two intents before mutating**, one per
   location, each with its own token; the single post-state capture
   establishes **both** findings before the lease releases — source
   verified absent, destination reopened and hashed; and two observations
   publish, each fulfilling its own intent — **through two registrations,
   so the crash cases split**: a crash before either publication leaves
   both intents unmatched and both locations unsettled (§4); a crash
   **between the publications** leaves one intent fulfilled and the other
   unmatched — one location settled by its observation, the other
   unsettled — and §4's per-location blocking needs nothing new for
   either, since each location blocks or proceeds on its own intent's
   state alone. Each is the honest reading of a move interrupted exactly
   there: before publication, what happened is unestablished; between
   publications, one location's finding is established and the other's is
   still owed.

**An acquisition is orchestration over these shapes, never a third one.**
`R10` routes URL-valued inputs to acquisition and ramp §6.6 rules that an
acquisition *ends by recording the digest of what it retrieved*. That
recording is **two outputs at two layers, never one record doing both
jobs**. *Declaration authoring, where needed:* for a resource declared with
a locator and no digest — the ramp's eleven — the acquirer **pins the
declaration** with the retrieved digest. This is §6.6's authoring act at the
declaration layer, and it is not the fabricated basis §2 refuses: the record
declared the resource, and what was missing was the pin. The authorship
flows from the act — retrieval against a declared locator — never from an
observation record, so §2's line stands whole: no observation seeds a
declaration, and the eleven acquire their basis by an acquirer's authorship,
not a record store's side effect. *The holdings observations:* the
retrieval's dereference of the source is a **pure look** that established
`found` at the source `url` locator, so H4 gives it an audit's duty — its
own minted `event_token`, no intent. **That look alone can already carry
heldness**: kernel §2.2 says content-addressed, retrievable bytes outside
the repository are held, so once the declaration is pinned and the remote
`found` is published, the projection reads `held` (§4) with nothing
materialized locally. **Materialization is therefore optional**, and where
the acquisition does write the bytes into a managed store, that is a
**managed mutation** at the destination store location, under its own
distinct token — never the URL look's. The acts are independent as
evidence: **each observation publishes as its act completes, never waiting
for the acquisition** — an unfulfilled store intent unsettles its
destination location (§4), never the source's. Whether *the acquisition*
has ended is **orchestration state, owed to the run/report design** that
owns act reports: this design binds each act's own terminus — a fulfilled
intent and its observation for a managed mutation; a published observation
or a reported inconclusive attempt (below) for a pure look — and §6.6's
"unfinished acquisition" reads over those termini. The visibility the
record layer can give is exact: a crashed mutation is durably visible as
its unmatched intent (§4); an intent-free URL attempt that never reported
cannot be made durably visible by this design, and that non-report is
precisely what the run/report seam exists to record — no claim otherwise is
made here. *(Designed 2026-08-11: the act-report design — the operation intent,
the three-valued completion reading, and the act-report whose entries record
the look's non-report.)*

Nothing else mints one. Not a declaration, not a directory listing, not an
import of somebody's claim that bytes exist. `G9`'s "no API accepts an
authored `held`" extends naturally: no API accepts an authored *observation* —
construction is reserved to acts that dereferenced and hashed, and **H1** (§6)
is what makes that reservation independently checkable.

**An inconclusive attempt is not a finding.** A retrieval refusal, a timeout,
a transport failure, unreadable bytes — each proves neither `found` nor
`absent`, and computation §7.1's line — *a failure to look is not a finding of
absence* — binds the acts themselves, not just the drafts the ramp held to it.
Such an attempt mints **no observation**. It lands in the act's own report
under the ramp's existing vocabulary, reused rather than reinvented: a locator
refused before any request was made is **`byte-locator-untested`** with the
refusal reason, a request that was made and did not yield the bytes is
**`retrieval-failed`**. The record layer is untouched: the prior observation,
if any, stays active, because no act established otherwise. `absent` is
reserved for a completed dereference that answered — which today only a
`store` dereference can do (§2). Under the inherited boundary a remote look
never answers *nothing is there*, only `retrieval-failed`, so the cost is
stated rather than hidden: remote disappearance is observable today only as
repeated inconclusive attempts, and a stale remote `found` stands until
either a ramp-boundary amendment defines a qualifying negative response or
the recency successor (§4) discounts it. Stating that cost beats laundering a
status code into absence. **H4** (§6) is what makes the reservation
sabotage-able in both directions.

**Dereferencing is the ramp's boundary, reused — not a second one.** Every act
above consumes an untrusted locator, and §2's canonical form is an equality
contract, not a safety contract. A `store` locator dereferences by resolving
its store identity to a supplied root **whose genesis record must carry that
identity** — verified before any read, a mismatch refusing exactly as the
`world_id` contract refuses a re-mint — **and which must be serviceable**:
genesis identity does not establish that a copied root is complete, so a
metadata-less root not yet admitted by §2's restore-act verification is
**unresolvable for holdings reads** — every dereference of it is an
inconclusive attempt, never an `absent` for a path the copy merely failed
to carry — and then resolving the relative path
under the ramp's local preflight: an absolute path, an upward traversal, or a
symlink escape from the root is refused, **resolved and compared against the
root before any read**. Path safety is not read consistency, so the contract
has a second half: a store dereference-and-hash runs under the **store's
consistent-read boundary**, held from dereference start through hash
completion. The boundary is not conjured from an undesigned store: **a
managed store is an `atoms` project root** — the root whose genesis record
carries §2's store identity — and the boundary is the coordinator's project
lease, the one every boundary-mediated mutation of the root already
serializes through. That lease is **package-private today**, entered by the
coordinator only on behalf of an approved project transaction, and `atoms`
ships no consumer-facing command for it — production adoption is authority
§12.2's Plan B, one consumer at a time — so consuming it here is a named
**adoption obligation on `atoms`**, every part preserving A5b's boundary:
the coordinator acts on the consumer's behalf, and no consumer ever
receives a `Lease`. The **lease-consuming command** obligation has two
parts; §2's replica, restore, and fork commands and the root-model
amendment travel beside them on the same bill (§7 item 7).
*The read command:* a coordinator command
performing dereference-and-hash under the private lease — the audits' and
re-checks' path. *Post-state capture on the mutating commands:* a separate
read command cannot prove a mutation's post-state, because it reacquires
the lease after the mutating command returned and another cooperative
mutation may sit between the two — so the mutating command itself captures
the mutation's post-state **before its lease releases**, and returns it:
the post-write hash; for a deletion, the absence check; and for a move,
whose post-state spans both paths, the **dual-location result** — source
absence plus destination hash from the one effect (the move contract
above). The adoption
also touches the root model, not only commands: authority §12.2 keys
science's engine root on a **corpus root**, while a managed store is a
**second root kind** — an `atoms` project root that is no corpus, its
genesis carrying §2's store identity — so that amendment travels with the
commands, tabled with the engine in §7 and recorded against the adoption
ledger's `atoms` authority row (§8), never assumed built. Under the lease an observation is of **a
stable store state as boundary-mediated writers produce it**: never a mixed
stream hashed while a serialized replacement was mid-flight, never a
transient absence caught between a boundary-mediated remove and write. The
guarantee stops where the tamper log's own does — it holds under the
**cooperative-write assumption and no further**: a raw writer holds no
lease, and what one can do to bytes mid-hash is §4's out-of-band bound, not
a claim this boundary makes. A read that cannot obtain the
boundary is an **inconclusive attempt** — reported, minting nothing — not a
torn `found` and not a false `absent`. A `url` locator inherits the ramp's network boundary's
**refusal and classification discipline** whole, not paraphrased: the
`https`-only scheme set, the non-public-address refusal, per-hop redirect
revalidation, a timeout and a streaming byte ceiling, and the
pin-the-validated-resolution rule with hostname and TLS validation
preserved — *"if it cannot do both, it issues no request."* The **numeric
limits are not inherited**: the timeout and the byte ceiling are each
instrument's **explicit inputs, recorded in the attempt report** beside any
`retrieval-failed` they cause — the ramp itself records that its own 512 MB
ceiling is an instrument choice that would misreport its three largest
resources, a bound this design must not promote into the profile. And retrieval is
**unauthenticated-only**: the act interface offers **no channel for grant
material** — no token or header parameter exists, and userinfo is refused
at the locator (§2) — because no boundary can decide whether an opaque
credential merely authorizes access to the location's bytes or selects a
different representation of them, and a wrong guess mints a `found` for
bytes the location does not name. What structure cannot refuse is a
credential authored *into* the URL's own bytes — a signed query, a
capability path segment, a token-bearing hostname, each indistinguishable
from its ordinary counterpart — §2's stated caller obligation over the
whole canonical URL, never claimed as a checked invariant. The absent channel is the whole contract today; what it defers
is **typed, provider-specific grants** (§7 item 8), each defining its
binding to the exact canonical locator and to each exact redirect hop —
never a blanket per-origin scope — with no grant material ever entering a
report, an error, or a record. The
classification above comes with the boundary: every one of these refusals and
failures is an inconclusive attempt, never an `absent`.

**Managed mutations run under the tamper log's intent discipline, because
they span roots.** A store write, a move, and a boundary-mediated deletion
each
mutate a store while their observation lands in the observer's corpus — two
roots — and the inherited log is per-root, its registration never publishing
across roots. Record-first could attest a mutation that never happened;
mutate-first could crash and leave a stale `found` active with nothing marking
it. So the ordering is pinned, and it uses the log's machinery **as built** —
intent, registered transaction, `fulfills`, the §6 qualification reduction —
never a token-matching shortcut beside it. In the log's vocabulary an
observation is not a "settlement" (that word is reserved for a registered
transaction's completion); it is a published record whose publishing
transaction *fulfills* an intent:

- **One act, one location, one token — and one intent where the act
  mutates.** A holdings act is per canonical location. An acquisition
  retrieving several resources runs several holdings acts — §3's up to two
  per resource: the intent-free URL look and, where the resource is
  materialized, the intent-bearing managed
  mutation, each under its own minted `event_token` — because the
  log permits exactly one fulfilling registration per intent, and one intent
  cannot name many locations. Ramp §6.6's "ends by recording the digest" now
  reads at this grain: what this design binds is each act's own §3
  terminus — a mutating act's intent fulfilled, a look recorded or
  reported — and whether *the acquisition* has ended is orchestration
  state, the run/report design's to record (§3); an act short of its
  terminus is what leaves it the unfinished acquisition §6.6 already names.
  *(Designed 2026-08-11, the act-report design §3: whether the acquisition has
  ended is now the operation intent's derived three-valued reading.)*
- **The intent.** Before mutating, the boundary durably appends a **holdings
  intent** in the observer's corpus root — the root the observation will be
  published through, so the log's same-root rule holds — with payload: the
  canonical location, the act kind, the boundary-minted `event_token`, and
  the actor (the assessment-run intent's shape, with the location standing
  where its spec identity stands).
- **The fulfillment.** After the mutation, the observation is published by a
  **registered, committed transaction** in that same root, and the boundary
  constructs `fulfills` **from its own intent** — no caller-selected
  `fulfills` exists, the log's rule restated, not relaxed. A **qualifying
  fulfillment** is a committed registration whose published record is a
  holdings observation for the intent's canonical location carrying the
  intent's `event_token`. Pointer ancestry alone proves nothing — any
  committed transaction could carry `fulfills` — so matching runs only
  through the log §6's reduction: a non-qualifying pointer never matches,
  and an unreadable one leaves qualification **unresolved**, which proves
  nothing and leaves the location unsettled rather than quietly settled.
- **Unmatched or unresolved, and the repair.** An intent is **unmatched**
  exactly as the log defines it — no pointers at all, or every pointer fully
  resolved and non-qualifying — and proves *a boundary-mediated attempt with
  no recorded outcome*, crash and cancellation indistinguishable. An intent
  whose qualification is **unresolved** — an unreadable pointer — proves
  nothing either way, and blocks exactly as an unmatched one does, **as
  itself, never reinterpreted as unmatched**: collapsing unresolved into
  either resolved state would settle a location no evidence settled. A
  **mutating** intent in either condition leaves its location **unsettled**
  (§4). The repair is a later **re-check of that location through the same
  root**, and its ordering covers the *read*, not merely the publication: a
  store-dereferencing re-check appends its **own holdings intent before
  reading** (below), so the chain — never a clock — orders its dereference
  start after the damaged act's intent, and the store's consistent-read
  boundary keeps the read from interleaving with the attempt itself. A
  **fulfilled** re-check intent later in the chain than the damaged intent
  **lifts the unsettled state**. The damaged intent stays unmatched forever,
  which is the truth: that attempt's outcome was never recorded. What the
  repair establishes is the location's current state, which is all the
  projection asked.

A phantom attestation cannot arise (the observation is published only after
the mutation completed), and a stale `found` cannot silently survive a crash
(the unmatched intent marks it until a later fulfilled re-check answers).
**Every store-dereferencing act appends an intent before it reads** — the
mutating acts because they mutate; re-checks because intent-before-read is
what makes chain position mean *looked after*, not merely *published after*.
Without it, a re-check could read a store, a deletion could then announce
itself and mutate, and the stale reading could publish later and lift a
refusal it never re-examined. The intent's **act kind** keeps the failure
modes distinct: an unmatched *mutating* intent is unsettled state; an
unmatched *re-check* intent is a look that never became a finding — no
mutation behind it, nothing unsettled, the act's failure (H4), not the
record's. A `url` re-check needs no intent: no boundary-mediated act mutates
a URL, so no URL location is ever unsettled, and remote evidence is
time-stamped data, not a race. The log amendments this requires — the intent
union, the §6 qualification reduction, `fulfills` construction, `L7`, and the
§9 ownership split — are tabled in §8.

**The forgery bound, stated at the strength it has.** A hand-forged
observation — a record written to look like an act's output — stands until an
audit reaches its location, exactly as a hand-forged verification stands until
audited. This is the act-bound ruling's own bound ("tamper detection at import
and under audit, and nothing in between") and it is inherited here, not
improved. `atoms` A7 landed the engine half of pre-mutation registration on
2026-08-14, and A8 landed durability certification on 2026-08-17. Detectable
removal for Science still requires composition-root adoption and a surviving anchor; only then is a
record with no registered provenance itself detectable. Until then, saying
otherwise would be claiming an end-to-end guarantee the system does not carry.

## 4. Supersession and staleness

**Active** means: not named by any enumerated record's `supersedes`. Ordering
is by explicit reference only — the records for one canonical location form a
DAG walked from its heads, never a list sorted by time. `observed_at` orders
nothing, decides nothing, and expires nothing (**H2**).

The structure is stated, not assumed:

- **Acyclicity is an invariant, checked — never an impossibility, assumed.**
  The tempting argument — a record's identity covers its predecessors', so a
  cycle would need a hash fixpoint — is the exact argument the formal model's
  **ρA9** found invalid for `retraction` and replaced with the retraction
  graph's acyclicity *invariant*, validated where records are admitted. The
  same ruling governs here: each location's `supersedes` graph **must be a
  DAG as a condition of admissibility**, the projection checks it on every
  walk, and a record set presenting a cycle **refuses the projection**.
  Traversal never trusts termination it has not checked.
- **Forks happen and are legal.** Two concurrent audits of one location
  cannot name each other, so both are heads. Heads whose outcomes **agree** —
  the same `found` digest, or both `absent` — coalesce **in conflict
  classification only**: the location is uncontested, two auditors agreeing
  being corroboration, not conflict, and refusing it would make concurrent
  audit an error. **Every agreeing head remains a record in the active
  set** — coalescing selects no winner and discards nothing, because
  agreeing heads are not interchangeable downstream: two `found(D)` heads
  with different `expected` values carry different associations for §5's
  expectation join, and each is a distinct corroborating act. Heads whose
  outcomes **disagree** make the
  location **contested**, and a contested location is **blocked** (below) —
  the existential held-rule must never silently let `found` outvote
  `absent`. And the classification is **not binary**, because the record is
  algorithm-generic (§2): two `found` heads under **different algorithms** —
  `found(sha256:X)` beside `found(sha512:Y)` — neither agree nor disagree,
  since no whole-digest comparison can settle them (§5's commensurability
  rule). Forcing them into either box misstates the evidence, so the
  location is **incommensurable**: a third classification that **blocks**
  exactly as contested does, scoping through the blocked set (below), while
  `found` against `absent` stays contested — that pair is a genuine
  disagreement about whether anything is there, no algorithm involved. The
  repair for all of them is the same act: a re-check that supersedes *every*
  standing head (the set-valued `supersedes` of §2) and records what is
  actually there.
- **A dangling predecessor is not an error.** A head whose `supersedes` names
  a record outside the enumerated coverage is still a head; the unseen tail
  is the §5 coverage bound doing its job.
- **An unsettled location is blocked, like a contested one.** A location is
  **unsettled** when a **mutating** holdings intent naming it is unmatched —
  or its qualification is **unresolved**, blocking as itself (§3) — under the
  log's reduction, and no **fulfilled** re-check intent for that location
  sits later in that root's chain: some boundary-mediated mutation has no
  recorded outcome, and nothing has demonstrably looked since. The intent's
  chain position — never a clock, and never mere publication order — is what
  puts the repair's *look* after the attempt (§3). Unsettled is contested's
  sibling — both name evidence in a state only an act can repair, and both
  make it the caller's problem instead of a silent guess.

**Blocking is scoped to what depends on it; corruption is not.** A
contested, incommensurable, or unsettled location is **blocked**: its
records leave the active set, and
the projection's **blocked set** — an output reported, and receipt-committed
(§5), beside the active set — gains an **entry**: the canonical location;
the **blocking reasons**, a deduplicated sequence sorted canonically —
any subset of `contested`, `incommensurable`, and `unsettled`, since one
location can hold disagreeing heads *and* an unmatched mutating intent at
once and a single status could not say so; and, per blocked head, its **head join
projection** — the one member shape §5 step 2 defines for both reducer
outputs: the head's record reference, its canonical location, its outcome
and `expected`, and every
reached predecessor's reference, outcome, and
`expected`. References alone would not do: an address cannot be joined on
without resolving content, which would smuggle exact-state resolution in as
an unnamed adapter input. The entry carries the projections because the
adapter must join over them (§5 step 3): the reducer's two outputs plus the
declarations are the adapter's whole input, never a re-enumeration beside
the receipt. The encoding is deterministic on §2's own precedent, stated at
every level rather than waved at: the **active set** sorts by head record
reference bytes; **blocked entries** sort by canonical location bytes — an
entry is keyed by its location, not by any one reference; within an entry,
the **reasons** are fixed enum byte forms, deduplicated and sorted; **head
join projections** sort by head reference bytes; and each projection's
reached-history rows are **deduplicated by record reference, then sorted**
by those reference bytes — a diamond in the `supersedes` DAG reaches one
predecessor along several paths, and one record is one row however many
paths reach it. One reducer output,
one byte form under the receipt. An
unsettled entry may carry **no records at all** — the mutation crashed
before any observation ever existed there — and such an entry refuses
nothing: no evidence, no dependent. The **dataset-scoped
adapter** (§5 step 3) then decides dependency: a dataset answer **refuses**
iff any record in a blocked entry would enter its tuple by a §5 join —
the joins run over the entry's records exactly to answer that question —
and every other dataset proceeds. One crashed act at an unclaimed
locator therefore blocks nothing but itself — refusing the whole coverage
for it would hand any single stray conflict a denial of every dataset the
coverage serves. Contested, incommensurable, and unsettled are **honest
operation** — concurrent audits fork, honest audits hash under different
algorithms, processes crash — and honest operation scopes. A
presented **cycle** is not: no act constructs a record naming a successor's
identity, so a cycle is corruption of the record set itself, and it keeps
refusing the **whole projection** (the checked invariant above).

The derived facts, over a set of active observations:

- a digest `D` is **held** iff some active observation attests `found(D)` —
  at any location, inside or outside the repository (kernel §2.2, `G9`'s
  location arm).
- a dataset's state is cut 2's `admission_state` over those observations,
  unchanged: `held` only when **every** declared resource digest has a
  matching active observation; the quantifier is `G9`'s and stays whole.

**Age alone never changes the derived state.** There is no TTL, no validity
window, no clock read anywhere in the derivation — a TTL would make admission
a function of the wall clock, which is ambient invalidation with a timer, the
exact thing the act-bound ruling refused. An observation stands until a later
act supersedes it: a re-check that found matching bytes refreshes the chain, a
re-check that found different bytes or nothing demotes through it, a
boundary-mediated deletion closes it.

**This closes ramp §8 item 1 at the record layer, and names the seam that
owns the remainder — which is not the belief policy.** "What may admission do
with a six-month-old probe" splits: the record layer answers *the observation
stands until superseded* — six months old and active is active. Whether
anything ever discounts old evidence is a question about **heldness**, and
heldness is decided before admission, which is decided before the belief
policy ever runs — `science.belief.v1` aggregates already-admitted
directional inputs and receives neither observations nor `observed_at`, so
recency can never be its parameter without amending the closure itself. The
seam that *can* own it is the **projection rule** (§5): the derivation
receipt pins the rule's exact binding, so a future recency-bearing projection
rule is a successor rule, pinned and visible in every receipt it signs —
never an ambient reinterpretation of the same records. And such a successor
carries one more obligation, stated now so it cannot be forgotten then: a
rule that discounts by age must take its **reference instant as an explicit
derivation input, committed into the receipt** — otherwise the same rule over
the same corpus states validates today and refutes tomorrow, which breaks the
receipt's re-run contract (§5) with an ambient clock, the exact thing this
section refuses. `observed_at` is in the facet so that successor *can* read
it as data. No current rule does, and this design mints none.

**The out-of-band bound, restated rather than hidden.** Bytes destroyed
without the boundary — a raw `rm` in a store — leave a stale `found` active
until an audit observes the absence. Bytes **mutated** without the boundary
carry the second edge: a raw writer holds no lease, so §3's consistent-read
boundary — cooperative-write bound, like the tamper log it inherits the
assumption from — cannot keep a raw write out of a running hash, and a
`found` minted across one may digest a stream no stable state held. Both are
the sentence the act-bound ruling wrote about raw `cp`, with the arrow
reversed, and both have the same repair (a re-check through the boundary
reads a stable state) and the same eventual strengthening (the log's
detectable removal). A reader who needs current heldness *now* runs the
re-check act; the derivation will not pretend to know what no act observed.

## 5. The coverage projection

How a caller comes to hold a current set of observations — the "undesigned
middle" — is a **projection over a declared coverage**:

1. The caller names a **coverage**: the corpora whose observation records the
   derivation may enumerate, each by stable identity. Holdings observations
   live in **the observer's corpus** — whoever performed the act records it in
   their own corpus, like any attestation; observing needs no write access to
   the dataset's home, and the commons store the recreate-not-migrate ruling
   retires is never written to.
2. The projection enumerates every holdings observation across the coverage,
   resolves supersession chains (a chain may span corpora: an audit in corpus
   B may supersede an acquisition record in corpus A — the ref is an identity,
   and identities do not care where they resolve), and yields the **active
   set** beside the **blocked set** (§4). Both outputs share **one member
   shape, the head join projection**: the head's record reference, its
   **canonical location**, its outcome and its `expected`, and — per record
   the head's `supersedes`
   walk reached inside the coverage — that record's reference, outcome, and
   `expected`. The active set is the head join projections of the unblocked
   heads; a blocked entry carries the same shape per blocked head (§4). One
   shape, because step 3's history join needs every reached predecessor's
   outcome and `expected` for **every** head, active or blocked — an active
   set of bare heads would force exactly the ambient exact-state resolution
   the blocked side refuses. The location is in the shape for the same
   reason: cut 2's argument is a `ByteObservation` of **digest and
   location**, so an adapter handed projections without locations could not
   construct one without resolving records ambiently. Two consequences are stated rather
   than discovered: a record
   superseded only in a corpus *outside* the coverage reads active *within*
   it — the coverage declaration is what makes that a bounded, stated claim
   instead of a silent error; and a declared corpus that cannot be enumerated
   **refuses the whole projection** — a partial enumeration reported as a
   result would be the silent shrink the declaration exists to prevent. The
   enumeration also carries each covered corpus's **holdings intents with
   their qualification states** — matched, unmatched, and **unresolved as
   itself, never collapsed** (§3): the blocked set derives from them (§4).
   An intent outside the coverage is invisible exactly as its would-be
   fulfillment is — the same bounded claim, stated once.
3. A **dataset-scoped adapter** turns the active set into cut 2's argument.
   The seam is already dataset-keyed — the evaluator's availability context
   maps each dataset address to its own `ByteObservation` tuple, and
   `admission_state` reports a supplied observation matching no declared
   digest as a `mismatch` — so the adapter's whole job is deciding **which
   heads enter a dataset's tuple**. Three joins, each explicit:
   - **by outcome** — a head whose `found` digest matches a declared resource
     digest enters. This is promotion, and it is the only join `held` reads.
   - **by expectation** — a `found` head whose `expected` digest matches a
     declared resource digest enters, whatever digest it actually found. A
     first-contact acquisition that retrieved wrong bytes surfaces here, and
     the existing seam reports it as the `mismatch` it is. (An `absent` head
     never enters a tuple — it has no digest to enter with; what it
     contributes is the absence of anything, and the resource reads
     `no-matching-observation-in-coverage`.)
   - **by history** — a head enters if any record it transitively supersedes
     would have entered by outcome or expectation, read from the **head join
     projection** the head carries (step 2), never from an ambient
     resolution of record content. Bytes that drifted since a
     matching observation surface here: the head's differing digest arrives
     as a `mismatch`, an `absent` head contributes nothing and the resource
     reads `no-matching-observation-in-coverage` — the ramp's distinction
     between *different bytes* and *no bytes*, preserved by construction.
   A head none of the three joins reaches belongs to no dataset in question
   and enters nothing — declaration-independence at work, not a gap. And
   every join compares **algorithm-qualified digests as wholes** — same
   algorithm, same hex, or no join — with §2's construction constraint
   (`expected` shares its `found`'s algorithm) closing the one route around
   it: a head admitted by expectation carries a found digest commensurable
   with the declaration it joined, so every mismatch the seam reports
   compares digests under **one** algorithm. The false cross-algorithm
   mismatch — the bytes said to contradict a record nothing checked them
   against, the survey's own coverage error — is **unconstructible**, not
   merely avoided. The same commensurability gates the history join: a head
   enters through its superseded past only where its own found digest shares
   the declared digest's algorithm — a re-check under a different algorithm
   than its predecessor's contributes nothing there, and the resource reads
   `no-matching-observation-in-coverage`: true, in the checkable sense — no
   observation exists that can answer for it. The adapter also owns the
   blocked set's reach (§4): before answering a dataset, it runs the same
   three joins over each blocked entry's join projection — outcome,
   `expected`, and reached history, carried in the entry (§4), so the
   adapter's inputs stay exactly the declarations
   plus the reducer's two receipt-committed outputs — and a hit **refuses
   that dataset's answer** — blocked evidence never enters a tuple, and
   never silently vanishes from one either.
4. The projection also yields a **derivation receipt**, on the contract world
   §5 and `W8a` already set for enumerations that feed belief — adopted
   whole, not paraphrased. The receipt names the **exact corpus-state
   identities** enumerated (a receipt naming corpora rather than states is
   **`malformed`**) — and, because the reducer now reads each corpus's log
   for unmatched holdings intents (§4), **the log chain head under which each
   corpus was enumerated, captured coherently with its state**. The state
   identity is over node content, not the log — world addressing's own
   boundary — so two corpora in identical states can carry different chain
   heads and therefore different unsettled sets; a receipt silent on the
   heads names inputs that do not determine its output. It also names the
   **exact rule binding**: the fixture-bound
   identity of the **active-set reducer** — steps 1 and 2 whole: enumeration,
   the supersession walk, coalescing, the contested-, incommensurable-, and
   unsettled-blocking,
   and the cycle-refusal; the rule a recency-bearing successor would replace
   (§4) — *together with* the content identity of the implementation
   that ran, resolved from the held store — a bare identity or version
   string is `malformed`, and an implementation that fails its fixtures **is
   not that rule**. Validating a receipt is re-running: resolve the binding,
   re-reduce the named states under the named heads, and land in the
   vocabulary the corpus already has — **`validated`** (the named active and blocked sets reproduce byte-for-byte under §4's canonical encoding), **`refuted`**
   (it does not), **`unresolvable`** (a named corpus state, a named
   chain head, or the implementation is not resolvable here — a
   computability state, never an epistemic one, and never reported as
   refutation), **`malformed`** (the
   receipt could never be checked by anyone). A receipt naming coverage and
   output alone would validate nothing — a wrong or incomplete reduction
   could sign a perfectly consistent one — which is `H3`'s second arm (§6).

**The receipt's claim ends at the reducer's output — the active set and the
blocked set.** The dataset-scoped adapter
(step 3) is deliberately outside the binding: its other input is the dataset
declarations, and a receipt that claimed the dataset-keyed tuples without
naming those declarations as inputs would let a wrong adapter reproduce the
active set and still validate — a receipt certifying what it never checked.
The adapter answers instead at the seam it feeds: its output *is* cut 2's
argument, and a mis-join is `G9`'s arms' business at the admission seam,
where the declarations are first-class. One receipt, one claim, checkable in
full — widening it to the tuples is a decision for the cut that would also
put declarations into the receipt's input set, not a default.

**A derivation with no declared coverage is refused** (**H3**). This is world
§5's producer-snapshot argument applied to its second population: enumerated
against whatever happened to be checked out, the projection silently shrinks,
a held dataset reads `declared` because its observing corpus was not mounted,
and admission moves with the checkout — `R5`'s exact prohibition. The ramp's
"held **in this coverage**" stops being a caveat on one survey and becomes the
type of every heldness answer.

**The receipt makes the observation set pinnable; it does not pin it.** Whether
the receipt becomes a member of the belief-input closure — alongside the
producer snapshot it is patterned on — is a decision for the conformance cut
that draws the persistence seam, which will hold the closure's frozen
projection in one hand and this receipt in the other. The precedent leans yes
(the producer snapshot was published exactly so kernel §5.1 could digest it),
and this design's obligation is only to make the yes *possible*: the receipt
is a value with a content identity, ready to be a closure member the day a cut
selects it.

## 6. The H table

On the tamper-evident log's precedent, this design adds its own table rather
than appending to `G`. The ramp's pre-commitment governs: a row exists only
for a property that is **independently sabotage-able** — breakable while every
banked row still passes. Four candidates were tested; four survive.

> **H1 — creation is reserved to acts, and to established outcomes.** A
> holdings observation exists only as the recorded outcome of an act that
> dereferenced its location and **established** what it records — `found` by
> hashing the bytes, `absent` by a completed dereference that answered
> nothing is there — by §3's two act shapes, a pure dereference or a managed
> mutation recording its captured post-state. Nothing mints one from a
> declaration, a directory listing, or an attempt that established neither.

*Sabotage, first arm:* back-fill `found` records from a directory listing,
copying each declared digest into a record without hashing anything. Every
banked arm, exercised at the derivation seam, passes — the derivation *does*
read records, so `G9`'s path-exists arm is satisfied — and the
content-addressing guarantee is void one layer up: the path-exists predicate
has been laundered through the record store. Creation is the unowned half of
the record's lifecycle exactly as promotion was the unowned transition before
`G9`, and H1 owns it. The same arm owns the acquisition shortcut: mint the
destination observation from the source stream's digest without reopening
the destination (§3) — a truncated or transformed write now reads as held
bytes no act ever hashed at that location, and every other row passes,
since a real act really dereferenced the source. *Sabotage, second arm:* hash a store path outside the
consistent-read boundary, mid-replacement. The mixed stream mints `found`
with a digest **no stable store state ever held** — or the transient gap
between a remove and a write mints a false `absent` — and every banked row
passes: a real act really dereferenced, and no other row speaks to what a
look must hold still. H1 reaches it because an observation of no stable
state established nothing; the boundary (§3) is what makes "established" a
checkable word. The arm's sabotage is an act **skipping** the boundary — a
raw writer defeating a held lease is no row's claim: the boundary
serializes cooperative writers only, and raw concurrent mutation is §4's
out-of-band bound, beside raw `rm`. *Sabotage, third arm:* mint `absent`
from the deleting command's own success — the command returned, so the
bytes must be gone. A delete that unlinked the wrong path, failed half its
plan, or raced a cooperative writer now demotes heldness on evidence of
nothing, and every listed arm passes: nothing was fabricated from a
listing, and no read happened at all, torn or otherwise. §3's post-delete
absence check, captured before the mutation's lease releases, is what H1
makes checkable here — `absent` is established by a look that answered,
never inferred from a return code.

> **H2 — supersession is by explicit reference, per location, over a checked
> DAG, and a contested, incommensurable, or unsettled location is
> blocked.** Active-ness is
> resolved by walking each canonical location's `supersedes` graph from its
> heads, with acyclicity validated as an **admissibility invariant** on every
> walk (ρA9's discipline). No derivation orders records by `observed_at`; no
> record supersedes across locations; agreeing heads coalesce in conflict
> classification only, every head staying active (§4); **disagreeing
> heads block the location** rather than letting any outcome win; `found`
> heads under different algorithms — comparable by no whole-digest rule —
> block it as **incommensurable** rather than being forced into either box
> (§4); a mutating
> intent left unmatched — or **qualification-unresolved, blocking as
> itself** — leaves its location unsettled and blocked until a later
> fulfilled re-check intent answers (§4); and a blocked location refuses
> exactly the dataset answers that depend on it, never fewer.

*Sabotage, first arm:* resolve "current" by latest timestamp. Every banked
row passes — none speaks to ordering — and active-ness now moves with clock
skew between observers: two records, neither superseding the other, flip
precedence with no node recorded, which is admission changing because of a
clock, the act-bound violation in its subtlest form. *Sabotage, second arm:*
on disagreeing heads — an active `found` beside an active `absent` — let the
existential held-rule quietly count the `found`. Every banked row passes, and
a location whose own evidence is in open conflict promotes a dataset as if it
were not; H2's blocking is what makes the conflict the problem of exactly the
answers that depend on it, instead of a silent vote. *Sabotage, third arm:* skip the acyclicity check on the
strength of the hash-fixpoint argument — the argument ρA9 already found
invalid once. A crafted record set presenting a cycle now hangs the walk or
silently drops the location, whichever the traversal happens to do; every
banked row passes either way, and H2 alone demands the check that refuses it.
*Sabotage, fourth arm:* enumerate the intents faithfully and **ignore them in
the walk**. Every act creates its intent, so H4's third arm passes; the DAG
is clean and no heads disagree, so H2's other arms pass; and H3 cannot see it
either — a receipt faithfully naming a reducer that ignores intents validates
that reducer's every run. The crash window H4 closes from the act's side
reopens from the reducer's: a mutation with no recorded outcome blocks
nothing, and the stale `found` it may have orphaned promotes as if the
attempt never happened. The same arm covers the softer collapse: resolve an
**unreadable** fulfillment pointer to either resolved state — read as
qualifying, it settles a location no evidence settled; read as unmatched, it
misstates what is known — where the log's reduction says unresolved proves
nothing and must block as itself. The blocking is a guarantee only because
this arm owns it. *Sabotage, fifth arm:* coalesce agreeing heads by
selecting a winner: two `found(D′)` heads at one location with different
`expected` values, one record kept. No heads disagree, so the blocking arms
pass; the DAG is clean; every intent is fulfilled; no timestamp ordered
anything — and one mismatch association is gone: the dropped head's
`expected` was the expectation join (§5) that would have surfaced a
first-contact mismatch against the declaration naming it, and a
corroborating act's evidence vanished with it. That every agreeing head
stays active is a guarantee only because this arm owns it. *Sabotage, sixth
arm:* force an algorithm-mixed pair — `found(sha256:X)` beside
`found(sha512:Y)` — through the binary classification. Read as agreement
(both are `found`, after all), the location coalesces and **promotes under
whichever head matches a declaration** — an existential answer built from
two claims that never corroborated each other. Read as disagreement, the
blocked reason asserts a conflict no comparison established, and the
truthful state — nothing here can be compared — is unreportable. Either
way every other arm passes: no timestamps ordered anything, the DAG is
clean, every head is retained, every intent fulfilled. The
`incommensurable` classification is a guarantee only because this arm owns
it.

> **H3 — the derivation refuses an undeclared coverage, and its receipt is
> checkable.** Every heldness answer names the corpus states **and log chain
> heads** it enumerated and the rule that reduced them; "whatever is checked
> out" is not a coverage, and a receipt the named rule over the named inputs
> does not reproduce is a defect, not a disagreement.

*Sabotage, first arm:* default the coverage to the corpora currently present.
`G9` passes (records are consulted), and `R5`'s banked arms pass — they test
copy loss, not enumeration scope — while unmounting an observing corpus
silently demotes every dataset it vouched for: belief depending on the
checkout, the producer-snapshot defect on the holdings side, with no banked
arm positioned to see it. *Sabotage, second arm:* enumerate half the declared
coverage — or reduce with an implementation other than the bound one — and
sign the receipt anyway. The receipt stays internally consistent, every
banked row passes, and the completeness claim is void; H3's second arm is
what makes "resolve the binding, re-reduce the named states" a test instead
of a hope. The arm inherits §5's outcome vocabulary whole: a reproduced set
is `validated`, a wrong reduction is **`refuted`**, an absent corpus state or
unheld implementation is **`unresolvable`** — never reported as refutation —
and a receipt naming corpora-not-states or a bare version string is
**`malformed`**, refused rather than trusted. *Sabotage, third arm:* name the
corpus states exactly and read the log heads **ambiently** — re-reduce under
whatever chains are present at re-run. The state identities match (the state
identity is over node content, not the log), the reduction reproduces on
every day the chains happen to agree, and on the day a chain gained an
unmatched intent the same receipt flips verdict with no named input changed —
a receipt whose named inputs do not determine its output. Committing each
coherently captured head is what makes the unsettled set part of the claim
instead of ambient state.

> **H4 — no silent act, and no laundered non-answer.** An act records every
> outcome it **established** — `found`, `found` with an unexpected digest,
> `absent` — and an act that established an outcome but cannot record it
> **fails**; it does not report transiently and drop the record. An
> inconclusive attempt records **no observation**: it reports through the
> act's own channel (`byte-locator-untested`, `retrieval-failed`) and never
> mints `absent`. A mutating act runs inside its intent–fulfillment ordering
> (§3) or fails; it never mutates outside it.

*Sabotage, first arm:* an audit that finds a mismatch prints it and mints
nothing. The stale `found` stays active, the dataset stays held, and every
banked arm passes — `G9`'s mismatch arm, exercised over *supplied*
observations, never sees an observation that was never recorded. *Sabotage,
second arm:* a timed-out retrieval recorded as `absent` — the non-answer
laundered into established absence. The fresh `absent` supersedes the
standing `found`, a held dataset demotes on evidence of nothing, and every
banked row passes; computation §7.1's *a failure to look is not a finding of
absence* is banked as prose, and H4 is its only enforcement at this seam.
*Sabotage, third arm:* a deletion that mutates first and skips the intent. A
crash before minting leaves the stale `found` active with nothing marking the
location unsettled; the log's banked rows are per-root and never knew a
holdings act existed; every banked row passes, and H4 alone demands the
ordering that makes the window visible. H4 is computation §7.1 — the framing
the ramp holds its own drafts to — made an obligation on the acts themselves:
a look that established something must become a finding, and a look that
established nothing never may.

The table below is this section's index, machine-checked against the corpus's
guarantee-row inventory (`python/tests/test_designs_corpus.py`); each row's
normative statement and sabotage arms are the paragraphs above, not this
compression.

| # | guarantee | sabotage arms |
|---|---|---|
| **H1** | creation is reserved to acts, and to established outcomes | back-filling `found` from a listing or a source digest is unmintable / a hash outside the consistent-read boundary established nothing, and raw concurrent mutation stays out-of-band / `absent` comes only from a post-delete look, never a return code |
| **H2** | supersession is by explicit reference, per location, over a checked DAG, and a contested, incommensurable, or unsettled location is blocked | active-ness is walked per location over a checked DAG, never ordered by `observed_at` / disagreeing heads block the location rather than any outcome winning / acyclicity is validated on every walk / an unmatched or qualification-unresolved mutating intent leaves its location unsettled, blocking as itself / every agreeing head stays active under coalescence / an algorithm-mixed `found` pair blocks as `incommensurable`, forced into neither box |
| **H3** | the derivation refuses an undeclared coverage, and its receipt is checkable | "whatever is checked out" is not a coverage — enumeration is by declared stable identity / a receipt the bound rule over the named inputs does not reproduce is `refuted`, an absent input `unresolvable`, corpora-not-states is `malformed` / log chain heads are coherently captured, committed inputs, never read ambiently |
| **H4** | no silent act, and no laundered non-answer | an act records every outcome it established or fails, never a transient report and a dropped record / an inconclusive attempt reports through its own channel and never mints `absent` / a mutating act runs inside its intent–fulfillment ordering or fails |

`H1`–`H4` take the frozen corpus from **139 rows across eleven tables to 143
across twelve**. Their arms are acceptance criteria for the conformance cut
that builds the persistence seam; none is claimed exercised by this document.

## 7. What this unblocks, and what stays open

**Unblocked:**

- **The run boundary.** Cut 2 §2's stop-rule failure dissolves: acquisition
  now has a designed place to record what it retrieved, so a run-capture
  slice no longer chooses between designing this record implicitly and
  building a boundary that can admit nothing.
- **The `G9` independence arm.** Its sabotage — install the path-exists
  predicate, assert `G9` fails alone — needs a persisted promotion predicate
  to corrupt. The record is that predicate's substrate; the arm stays owed to
  the cut that builds it, and is now buildable.
- **The ramp's 24 undetermined records.** Their determination is now a
  procedure, not a mystery: an observing act over a coverage that can see
  their bytes — where any exist — after which their state is a lookup. The 10
  with no authority fields remain reachable only this way, which the ramp
  already said; the design changes what kind of thing the answer is, not the
  work of looking.

**Open, deliberately:**

1. **Recency as a successor projection rule.** Whether anything ever
   discounts old observations, and by what curve — now a typed question on
   `observed_at`, owned by the projection-rule seam whose exact binding every
   derivation receipt pins (§4, §5), and bound by the stated obligation: the
   reference instant is an explicit derivation input in the receipt, never an
   ambient clock. Explicitly **not** a belief-policy parameter: the belief
   policy runs after admission and never sees an observation.
2. **The partly-pinned rule's empirical corroboration** — ramp §8 item 3,
   evidence not design, untouched here.
3. **Whether the derivation receipt joins the belief-input closure** — owed
   to the persistence cut (§5).
4. **Further locator types.** §2 fixes two — `store(store identity, relative
   path)` and `url(canonical absolute URL)` — because those are the two the
   creation acts dereference today. A third scheme (an object store's native
   addressing, say) arrives by amendment, with its canonicalization rule, or
   not at all.
5. **Observer reliability weighting.** Observations are equally weighted at
   derivation; `meta/` measures reliability, and whether any consumer reads
   that measurement is that consumer's design, not this record's.
6. **Acquisition completion as orchestration state.** §3 binds each act's
   own terminus; whether an acquisition as a whole has ended — and the
   durable home of a look's non-report — belongs to the run/report design,
   alongside the act reports it owns. *Closed 2026-08-11 by the act-report
   design: completion is the operation intent's derived three-valued reading
   (§3 there), and the look's non-report lands in the closing report's entries
   — or, operator-crashed, as the durable unmatched intent.*
7. **The engine.** Persistence, the tamper-evident log's strengthening, and
   every operational duty (who runs audits, on what cadence) wait on the
   composition root; A7's engine half landed 2026-08-14 and A8's certification
   landed 2026-08-17. §3's
   consistent-read boundary adds one **named item** to that bill, under
   authority §12.2's Plan B: the consumer-facing coordinator read command
   (dereference-and-hash under the private lease); post-state capture on
   the mutating commands — the post-write hash, the post-delete absence
   check, and `MoveNoClobber`'s **dual-location result**, source absence
   plus destination hash from the one effect, each returned before the
   lease releases (§3); the move's two-intent orchestration over that
   result stays the science boundary's, but only that result makes it
   publishable; the **replica, restore, and fork commands** under §2's
   fail-closed writer state — writability a granted state recorded in
   engine bookkeeping, never a default, granted only by initialization
   and the fork; a metadata-less store root cold-bootstrapping
   **read-only and unresolvable for holdings reads**; the restore command
   admitting a copy to read-only service only on a **`validated`** verdict
   from the log's verification act — store subject, explicit observer set
   of eligible store anchors — every other verdict preserved and the root
   left unserviceable, never granting
   writability; a claim-only copied-root directory may publish first as
   reserved, surface-excluded no-clobber bookkeeping, with no payload, chain,
   override, lifecycle stamp or grant, or serviceability before the read-only
   stamp; the fork's new genesis durable before its writability
   grant — so no crash window nor tree copy yields an ungoverned
   writable duplicate — and the root-model
   amendment — §12.2 keys science's engine root on a corpus root, and the
   managed payload store arrives as a **second root kind**, an `atoms`
   project root whose genesis carries §2's store identity. A5b's boundary
   holds throughout: the coordinator acts on the consumer's behalf, and no
   consumer ever receives a `Lease`. Today's lease is package-private and
   entered only on behalf of an approved project transaction, so the
   dereference contract is unbuildable until `atoms` ships this; the
   obligation is recorded where `atoms` state is authoritative — the
   adoption ledger's artifact 4 row (§8) — not only here.
8. **Authenticated retrieval.** The URL boundary is unauthenticated-only
   (§2, §3): over an opaque credential, *authorizes access* versus *selects
   different bytes* is undecidable at the boundary, so the act interface
   offers no channel for grant material, and credential-free authoring of
   the whole canonical URL is §2's stated caller obligation. A
   provider-specific **typed grant** arrives by amendment — and it makes
   the exclusion *checkable* only if its constructor **owns the locator
   parsing**: it builds the canonical locator itself from typed parts,
   never accepting an already-authored opaque URL, since an opaque URL
   re-imports exactly the unclassifiable bytes the type exists to separate.
   The amendment owes exactly what the absent channel protects: binding to
   the exact canonical locator and to each exact redirect hop — never a
   blanket per-origin scope — and the guarantee that no grant material
   enters a report, an error, or a record.

## 8. What this changes elsewhere

Applied in the same change as this document, on the world address ruling's
precedent: a ruling that leaves its amendments untabled leaves the corpus
disagreeing with itself.

| site | change |
|---|---|
| admission ramp §8 item 2 | gains the closure annotation: *designed 2026-08-10 (`2026-08-10-verified-holdings-record-design.md`); the record is a world record in the observer's corpus, per-location, act-minted, superseded never expired, projected under a declared coverage* |
| admission ramp §8 item 1 | gains: *closed at the record layer 2026-08-10 — an observation stands until superseded; what remains is a possible recency-bearing **successor projection rule**, pinned in every derivation receipt with an explicit reference instant, and it is **not** a belief-policy parameter (the holdings design §4)* |
| admission ramp §6.7 | gains a one-line pointer to this design |
| conformance cut 2 | **Status append only:** one sentence recording that the design its §10 item 1 named as the most consequential open question landed 2026-08-10 |
| guide `open-questions.md` | the *where verified holdings are recorded* entry is replaced by its residue: recency as a possible successor **projection rule** (never a belief-policy parameter) and the partly-pinned corroboration; the *third conformance cut* entry's run-capture arm gains *unblocked by the holdings design, 2026-08-10* |
| guide `glossary.md` | **Holdings observation** added; **Held** and **Declared** cite it |
| guide `foundations.md` | the `held` section gains the record: heldness is derived from active holdings observations under a declared coverage; the kind inventory gains `holdings-observation`; this design joins `sources` |
| guide `contracts-and-adoption.md` | frozen-row count **139 → 143**, tables **eleven → twelve**; the open-edges pointer moves the holdings question to its residue |
| epistemic kernel, kind inventory | a world record is a kernel kind, and the counts move with it: the kernel is **eleven kinds today** — eight as designed, then `retraction` (correction lifecycle), `instrument-certification` (5b), `coreference-attestation` (world address ruling, 2026-08-08) — and **`holdings-observation` joins as the twelfth**, on the same appending precedent, the sequence preserved; the §4.4 accounting discipline extends to it. The count sites are amended as an **exact inventory, not a sweep**: the domain extension design's two "eleven kernel kinds — ten until 2026-08-08" clauses (its §1 inherits line and its §5 ownership line); the adoption ledger's docket note ("the kernel is **eleven kinds**, not ten"); the admission ramp §2.2's "binds all eleven kinds"; the world address ruling §3's "now bind all eleven kinds"; the formal model §2.1 heading "(the eleven kernel kinds)" with its "All eleven" lead — `foundations.md`'s anchor link to that heading moves with it; and `foundations.md`'s "the formal inventory contains eleven kernel kinds". The world address ruling's *historical* statements — "an eleventh kernel kind", "taking the kernel to eleven kinds" — record what that ruling did, remain true, and are deliberately untouched |
| tamper-evident log design | one amendment, applied across every site it names. **§3's root inventory and genesis union**: "one chain per engine root: every corpus, and the world root itself" gains the managed payload-store root, and genesis gains a third arm — `store(store_id, forked_from?)`, minted at store initialization, preserved verbatim by replica and restore, a configuration/genesis mismatch refusing exactly as `world(world_id)` does, and `forked_from` present iff a writable copy was minted by the fork act (§2 here: replicas are read-only carriers; a writable fork is a new genesis, the corpus-fork precedent). The **registered surface is a stable projection** — the log's one-projection rule applied to a store: every path in the store's payload namespace, excluding engine bookkeeping (the reserved log path and the engine's metadata) — never "the paths acts happen to mutate", which no registration-time baseline could state and which would put a raw-created payload file outside the surface; under the stable projection a raw-created payload file is **inside** it, and replay refutes a disk surface the timeline never produced, exactly as for a raw-created record. **Store chains anchor through the registry log-head records and the explicit anchor act, never through epochs**: the registry record's subject union gains `store(store_id)` beside `corpus(corpus_id)` — no self-anchoring arises, since the registry lives in the world root and a store root is not it, so the L11 concern stays confined to the `world` subject — the explicit anchor act names stores as it names corpora, and §6's sole-anchor-filter rule binds a store anchor by `store_id` unchanged; epoch head members stay `corpus | world`, an epoch being built over corpora, which a store is not. **The verifier's clauses move with the carrier, or the anchor is publishable but never acceptable**: §6 step 2's subject input — "the act names which corpus or world it verifies" — gains the store subject, and its carrier-eligibility clause — a registry log-head record, "corpus subjects only" — becomes corpus-or-store subjects, the `world`-subject refusal standing untouched; **L4 gains a store arm** — delete or replace a store's chain while its store-subject registry record is in the observer set → refuted, the subject binding associating the anchor by `store_id`, never by elimination; and **L10 gains the store instantiation** (§2 here) — replica act → same genesis, chain carried unchanged, a claim-only destination directory published first as reserved, surface-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation of an existing root **not granted writability** → refused, with recorded root creation the sole pre-grant write exception and the fork act the only writable exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative. Without this arm and a carrier that can hold it, §4's "eventual strengthening" (detectable removal in a store) would name a chain the log never defined — or one nothing could anchor. **§3's `intent` union**: "the one consumer named today is the assessment-run intent" gains the **holdings intent**, appended by every store-dereferencing act — mutating or re-check — before it acts (§3 here); payload: canonical location, act kind, boundary-minted `event_token` (reused per the log's not-a-second-attempt-id rule), actor. **§6's qualification reduction**: a qualifying fulfillment of a holdings intent is a committed registration publishing a holdings observation for the intent's location carrying its `event_token`, under the same reduction — a non-qualifying pointer never matches, an unresolved one proves nothing. **`fulfills` construction**: the boundary constructs the link from its own holdings intent; no caller-supplied path — the rule restated, not relaxed. **`L7`**: "intent claims are exactly as wide as stated" now quantifies over both intent kinds, its arms instantiated for the holdings shape — a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between intent append and mutation reads attempt-without-recorded-outcome, exactly as stated. **§9's ownership split**: the science-side obligations gain the boundary writing holdings intents and constructing their `fulfills`, on the `atoms` intent API as built — the **log's** `atoms` machinery changes nothing, though `atoms` is not wholly unchanged: §3's read command, mutating-command post-state capture, §2's replica, restore, and fork commands with the fail-closed writer state, and the payload-store root kind are separate, named adoption obligations, tabled in §7 item 7 and recorded on the ledger's artifact 4 row |
| world addressing §4.2, the identity-basis table | gains the **`holdings-observation`** row: basis is the content identity of the §2 canonical facet under `science.holdings-observation.v1` — every field participating, the minted `event_token` among them on the `retraction` shape's precedent, `supersedes` hashing as its sorted ref sequence — so the kind has a banked address basis rather than an implied one |
| formal model §2.1 | gains the **holdings observation** player row: content identity over the §2 facet under `science.holdings-observation.v1`, event token included; minted by §3's two act shapes — a pure dereference and a managed mutation recording its captured post-state — under whatever orchestration (acquisition, audit, a move, deletion) runs them; revised by supersession only; read by the coverage projection |
| formal model, tables | reproduces the **H** table, as it reproduces every other |
| normative contract §4 | the exact current inventory extends to twelve tables and 143 rows; the count guard moves in the same change |
| adoption ledger, artifact 4 | the `atoms` authority row gains the holdings prerequisite, under authority §12.2's Plan B: the coordinator read command (dereference-and-hash under the private lease); post-state capture on the mutating commands — the post-write hash, the post-delete absence check, and `MoveNoClobber`'s dual-location result (source absence plus destination hash from the one effect), each returned before the lease releases, the two-intent move orchestration over that result staying the science boundary's (§3); the replica, restore, and fork commands under the fail-closed writer state — writability granted only by initialization and the fork, a metadata-less store root cold-bootstrapping read-only and unresolvable for holdings reads, the restore command admitting a copy to read-only service only on a `validated` verdict from the log's verification act over the store subject and an explicit observer set of eligible store anchors — every other verdict preserved, the root left unserviceable — and never granting writability; a claim-only copied-root directory may publish first as reserved, surface-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp; the fork's new genesis is durable before its writability grant (§2); and the root-model amendment — §12.2 currently keys science's engine root on a corpus root, and the managed payload store arrives as a second root kind, an `atoms` project root whose genesis carries the store identity (§2, §3 here). A5b's boundary is preserved throughout: the coordinator acts on the consumer's behalf, and no consumer ever receives a `Lease`. That row declares itself the corpus's single authority for `atoms` implementation state, so the obligation must live there, not only in §7 |
| adoption ledger, artifact 7 | the oracle inventory extends to the **H** table |
| README | row count **→ 143**, tables **→ twelve**; the design table gains this document's row; the spelled-out design count and date range move per the existing corpus guard |
| `python/tests/test_designs_corpus.py` | `TABLE_OWNERS` gains `H → 2026-08-10-verified-holdings-record-design.md`; the "eleven frozen tables" README assertion becomes twelve via the guard's own machinery |

**Not amended, deliberately:** `G9` — every arm stands, and this design is its
instantiation, not its revision; `R5` and `R10`, leaned on and unmoved; cut 2's
selection, frozen and untouched beyond the Status append; the belief policy —
confirmed a **non-owner** of recency (§4), so nothing arrives there, not even a
question; the domain extension boundary design's *governance* — it rules
domain contracts, not core digest namespaces, so no namespace registration is
owed there and `science.holdings-observation.v1` is accounted for where
identity is accounted (world §4.2 and the formal model); its two kind-count
quotes move with every other count site, per the kernel row above.
