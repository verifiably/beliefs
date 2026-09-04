# The act-report — the terminal record of a boundary operation

**Status:** banked 2026-08-11; §7's amendment set applied in the banking change. Nothing here is implemented, and no conformance arm is claimed.

**Superseded 2026-08-28.** The sentence above claiming nothing is implemented
no longer holds. This header records design facts only; what has been built is
stated in the adoption ledger's current-state summary
(`2026-08-03-redesign-adoption-ledger.md`).

## 1. The gap, and the box already drawn around it

The verified-holdings record design closed where verified holdings are
recorded, and in closing it named this seam as its own residue
(`2026-08-10-verified-holdings-record-design.md` §3, §7 item 6): whether an
acquisition as a whole has ended is orchestration state, owed to "the
run/report design that owns act reports"; an inconclusive attempt "lands in
the act's own report", which existed nowhere durable; and an intent-free URL
attempt that never reported could not be made durably visible by the record
layer at all. The same homelessness afflicts more than acquisition. An audit
"emits findings" (`2026-08-02-world-addressing-design.md` §5), an explicit
import "emits an import finding"
(`2026-08-02-computation-reproducibility-design.md` R19), and a run request
the boundary refuses mints no `run` and leaves no record of the refusal —
none of these outcomes has a designed home.

**The scope ruling: one seam, not three.** This design owns the durable home
of every boundary act's report — acquisition acts and their non-reports,
operation completion, audit findings, import findings, and run attempts for
which no `run` was minted. Splitting the seam would re-create the gap at
each boundary it excluded.

**The inertness ruling, which bounds everything below.** The report layer is
epistemically inert **by type**, the `source-assertion` precedent: an
act-report and its entries are ignored by every derivation — eligibility,
admission, belief, and the coverage projection — while the products an entry
references retain their own semantics, unmodified by being referenced. All
blocking stays where the holdings design put it: a location is unsettled by
its record-layer intent and by nothing at this layer. An unfinished
operation, as such, blocks nothing.

Three inherited bounds shape the mechanism:

- **Kernel G4.** What was never durably recorded is undetectable. Visibility
  here is bought by pre-registration, never claimed from history.
- **R5.** Nothing at this layer depends on availability in this checkout.
- **The log is reused, not rebuilt.** Completion rides on the tamper-evident
  log's existing intent/reduction machinery
  (`2026-08-03-tamper-evident-log-design.md` §3, §6); its science-side
  consumer rules are amended (§7), and the `atoms` intent API is unchanged.

One line is inherited whole from computation §2.2: an incomplete *external*
report — a methods section, a collaborator's account — remains a source
assertion or a note. An act-report is the terminal record of **this
boundary's own operation**, never a costume an imported claim can wear.

## 2. The record

**A thirteenth world-record kind, `act-report`, under
`science.act-report.v1`, minted only by the boundary.** No API accepts an
authored one — the reservation `G9` states for `held` and `H1` makes
checkable for observations, extended to reports. Its guarantee table takes
the letter **T** (**A** already denotes the `atoms` adoption arms and is
not reused).

An act-report is the terminal record of one **opened operation**, or the
refusal record of a run request rejected before an operation can open
(§3.2). The operation kinds are a closed enum, extended only by amendment (the locator-type
discipline of the holdings design §7):

> `acquisition` | `audit` | `import` | `re-check` | `run-attempt`

### 2.1 The facet

- **`operation`** — the kind, from the enum above.
- **`event_token`** — the report occurrence's own, minted at open and
  carried in the operation's intent (§3), never any member act's. For a
  pre-intent refusal (§3.2) it is minted at the refusal itself and carried
  in no intent.
- **`actor`**, **`observer`**, **`instrument`** — the holdings observation's
  attribution discipline, reused.
- **`opened_at`**, **`closed_at`** — `observed_at`'s exact timestamp
  encoding, recorded and never read by any derivation.
- **`entries`** — a **canonical sequence**; order is identity-bearing. One
  entry per member act, in act order.

Each entry carries: the **act kind** — `pure-look` | `managed-mutation` |
`declaration-pin` | `subject-evaluation` | `record-import` | `run-attempt` —
the act's own `event_token` where the record layer minted one, the act's
**subject** — a canonical location (a pure look or managed mutation), a
record ref (a declaration pin, subject evaluation, or record import), a
frozen **spec identity** (an assessment run attempt), a dataset-production
**recipe identity** (a dataset-production run attempt), or, for a
missing-spec refusal, the spec ref the request named, **as supplied and
unresolved**, recorded as absent where the request named none — the
**explicit instrument inputs** where the boundary requires them (the timeout
and the streaming byte ceiling the admission ramp refuses to let become
ambient, recorded beside any failure they cause), and the act's
**outcome**.

### 2.2 Outcomes, per act kind, in native vocabularies

Each act kind keeps the vocabulary its own design gave it; no classification
is borrowed across kinds.

- **A locator act** (a pure look over a `store` or `url` locator): the
  reference to the observation it published; or **`byte-locator-untested`**
  with its reason — spellable **only for a locator act for which no request
  or dereference began**, covering both a preflight refusal and a deliberate
  skip after a cooperative stop; or **`retrieval-failed`** with the failing
  bound or transport reason named — reserved for an attempt that began. A
  member look that returned nothing to a surviving operator is recorded as
  the classification the operator can attest, reason named.
- **A managed mutation**: references to the observation(s) it published. A
  mutation that crashed has no outcome to record here — its story is the
  record layer's unmatched holdings intent, and the entry never restates
  what the log already proves.
- **A declaration pin**: the reference to the pinned declaration (the
  acquirer's authoring act of the holdings design §3).
- **A subject evaluation** (an audit's per-subject act): its finding, in the
  finding's native vocabulary — a contradiction finding, a `malformed` pair,
  `unresolvable`, `lineage-incomplete` — exactly as the owning design names
  it.
- **A record import**: the references to what was imported, and any import
  finding, as R19 names them.
- **A run attempt** (§3.2): the refusal, with the missing or malformed
  closure member named.

*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §2.4, five
clauses. **Operation kinds** gain `consolidate` and `move`. **Act kinds** gain
`record-mutation`. **Subject:** a `record-mutation` entry's subject is a record
ref together with the corpus it is read from or written to — a bare ref cannot
name a side of a two-root operation. **Outcomes:** `record-mutation` takes
`moved` or `consolidated`, and nothing is borrowed from another kind;
`consolidated` carries `retired_uids`, a sequence that is **empty** where the
inputs shared a `uid` and nothing retired. **Composite root-local operations:**
an operation may span two corpus roots under one `event_token` and one
`opened_at`/`closed_at`, minting one intent and one terminal report **per
touched root**; T2 is read root-locally over such an operation.)*

**A finding is an entry outcome, not a separate structure.** Its citation is
the pair **(act-report ref, entry index)** into the canonical sequence — the
index **zero-based and unsigned**, index 0 naming the first entry; one entry
per citation, out-of-range refused at the citing site (T6).

### 2.3 Identity, lifecycle, inertness

**Content identity over the whole facet, including the operation's
`event_token`** — two operations with equal actors, timestamps and entries
are two reports (the R3 discipline; T8). Like every world record, it
additionally bears a node-content identity and contributes to its corpus's
corpus-state identity (formal model §2.1).

**Immutable, append-only, retained.** No supersession path exists: a report
is evidence of its operation, and nothing later rewrites evidence — a later
operation publishes its own report. No ordinary API edits, supersedes, or
deletes one (T8). Retention is ruled in §4.

**Inert by type.** The report and its entries enter no eligibility
predicate, no admission derivation, no belief closure member, and no
coverage projection; everything in belief is inert under it. Referenced
products retain their own semantics — the reference conveys neither
protection nor force (T4).

An explicit import may carry another observer's act-reports. They enter
**structurally validated but not operation-authenticated**: kind and facet
are checked as any import checks them, while nothing can establish that a
boundary operation produced the record — a report derives nothing, so there
is nothing to recompute, and no mutable validation state exists to record a
verdict on. Being inert by type, they weigh nothing anywhere. Attribution
is preserved; no attester class is privileged.

## 3. The completion discipline — the operation intent

Completion is bought with the log's existing machinery: intent, registered
transaction, `fulfills` constructed by the boundary from its own intent, and
the §6 qualification reduction. Nothing mutable is introduced; "is this
operation finished?" is a derived reading over immutable entries, never a
stored status (T3).

### 3.1 Non-run operations

Every boundary operation that is not a run — an acquisition, an audit, an
explicit import, a re-check, however small — proceeds:

1. **Freeze the observer-corpus root.** The root the terminal record will
   publish through is selected and fixed first, so the log's same-root rule
   holds for the whole operation.
2. **Append one operation intent, before any act.** Payload: the operation
   kind, the operation's minted `event_token`, and the actor — the
   assessment-run intent's shape, the intent union's third consumer. If root
   selection or the append fails, **no act begins** — no request is issued,
   no lease is taken, nothing is minted.
3. **Acts run; products publish as each act completes** — observations,
   pinned declarations, imported records — exactly as the holdings design
   binds them, never waiting for the operation.
4. **The act-report closes the operation, success included.** The products
   of a non-run operation are per-act, so the report is the only
   operation-grain record there is. Its publishing transaction is
   registered and committed in the frozen root, and the boundary constructs
   `fulfills` from its own intent — no caller-selected `fulfills` exists.

A **qualifying fulfillment** of an operation intent is the log §6 reduction
read at operation grain: a committed registration whose published record is
an act-report carrying the intent's `event_token`. A non-qualifying pointer
never matches; an unreadable pointer leaves qualification unresolved, which
proves nothing.

Intent-before-first-act is what makes chain position mean *the operation
began before its acts* — the same argument holdings §3 makes for
intent-before-read, one grain up.

### 3.2 Run attempts

**An assessment run opens nothing new.** The boundary appends the
assessment-run intent exactly as built. What changes is one amendment to its
**qualification** (§7): a qualifying fulfillment is a committed registration
publishing either the `run` — as built, and a complete non-conforming
execution mints a run — or, for **an attempt for which no `run` was
minted**, an act-report of kind `run-attempt` carrying the intent's
`event_token`. One intent, one qualifying fulfillment; the singular
`fulfills` discipline is untouched.

**A pre-intent refusal is before the discipline, and stays there.** The
assessment-run intent requires an already-frozen `spec_identity`, so a
request refused for lacking one is refused **before any intent can exist**.
A surviving boundary publishes an **unfulfilling** act-report recording the
refusal — it fulfills nothing, because there is nothing to fulfill — and a
crash before that publication leaves no trace. That is kernel G4's bound,
inherited and stated, not fought. The refusal report's `event_token` is
minted **at the refusal itself** and enters no intent, and the refused
request has **no completion reading**: none of §3.3's three states applies,
because no intent exists to reduce over — it is a refused request's record,
not an operation's.

**A dataset-production run has no spec**, and the assessment-run intent
therefore excludes it. It opens the **operation intent** (kind
`run-attempt`) instead; its qualifying terminal is its `run` or, when none
is minted, an act-report carrying the token.

Cooperative refusals thereby stop contributing to unmatched intents. The
formal claim of an unmatched intent is **exactly what it was** — an attempt
with no qualifying recorded outcome — no stronger.

### 3.3 The three-valued completion reading

Derived per root, never stored:

| intent state (log §6 reduction) | reading |
|---|---|
| **unmatched** | **unfinished** — crash and abandonment indistinguishable |
| qualification **unresolved** | **indeterminate** — completion is not established either way; never collapsed into unfinished |
| **fulfilled** | **closed** |

Ramp §6.6's "unfinished acquisition" is this table's first row. The reading
is per-corpus — an intent and its fulfillment live in one root's chain — and
no cross-corpus completion claim is made.

**The look's non-report is visible in both halves.** Operator crashed →
unmatched intent, durable. Operator survived while a member act returned
nothing → the closing report's entry records what the operator can attest.
A look run outside any operation that never reported stays invisible —
G4's limit, restated once and not improved.

### 3.4 Two intent grains, no interference

A **holdings intent** is per canonical location and **blocks** that
location. An **operation intent** is per operation and **blocks nothing** —
completion visibility only. A store-mutating act inside an acquisition
therefore has two intents in flight at different grains, each in a 1:1 pair
with its own fulfillment; the log's one-fulfilling-registration-per-intent
rule is untouched. A URL look remains location-intent-free, and its
operation's intent supplies precisely the visibility holdings §3 proved the
record layer could not.

## 4. Composition, boundaries, retention

**Dataset acquisition provenance (computation §4.7) is referenced, not
restated.** The per-dataset provenance record's existing fields remain
authoritative; it gains one member, a reference to the acquiring operation's
act-report, which adds operational detail and references — never a second
acquisition-provenance object. For a successful acquisition the provenance
reference and the act-report publish **in the same registered transaction,
in the same root**. No identity cycle arises: the dataset's address is the
§6.2 basis projection, which excludes provenance, so the reference moves the
dataset's record bytes — its node-content identity and its corpus's
corpus-state identity — while the **address is unchanged** (T7).
Cross-root publication is **refused today**; supporting it needs its own
ordering design (§6).

**Boundary receipts stay nested in runs.** A receipt is identity-bearing
and epistemically read — scope derivation consumes it. A report is
operation-grain and inert. Different objects, different layers; nothing
migrates.

**Hand-run instruments stay out-of-world.** The survey instruments run by
hand against external roots, minting no world records; their frozen
artifacts remain their record. An act-report is minted only by the
boundary, so an instrument that never passes through the boundary cannot
produce one. A future survey run as a boundary-mediated audit reports as an
act-report because it *is* a boundary operation — a different thing, not a
migration.

**The audit evaluator stays read-only; its wrapper reports.** The formal
contract is untouched: `audit : Ω → Validated + Findings` mints nothing
(formal model §3.2; 5b §7.6) — the evaluator produces no configuration, no
corrective record, and no epistemic record. The act-report of an `audit`
operation is published by the **boundary wrapper** that ran the evaluator,
under the wrapper's own operation intent, and it is inert like every
report. Findings become citable entry outcomes by being **recorded by the
wrapper** — never by the evaluator acquiring a write. Detection stays split
from correction, now with the detection durably reported.

**Sub-problem 6 stays excluded.** This design gives audit outputs a durable
home; it gives audits no scheduler. Liveness, cadence, and who runs what
remain the agentic surface's, and every operational duty still waits on the
engine — the holdings §7 item 7 line, redrawn here.

**Citing a report position follows R18.** The verification constructor
gains the report-position citation as a **new explicit argument** (§7): the
cited finding's resolved content is embedded inline in the comparison
report, with **(act-report ref, entry index)** as provenance, and the
code-lineage certification remains the only authored claim input. Deleting
the report invalidates no verification — the promised dangling edge does
not exist.

**Retention: retain.** Deletion is not benign — deleting a report makes its
intent's qualification **unresolved**, moving the operation's reading from
closed to **indeterminate** (T3), and leaves any dataset provenance
reference dangling. The rule today is therefore *retain*. A future
compaction protocol must preserve both intent-qualification resolvability
and fulfillment evidence, and it composes with the computation design's
artifact-lifetime open question — inherited, not ruled here.

## 5. The T table — guarantees, certified by mutation

Per the kernel's §5 discipline: break what the guard guards and watch it
fail.

| # | Guarantee | Mutation test |
|---|---|---|
| **T1** | Only the boundary mints an act-report | Attempt to author one through every construction path — direct authoring, and any API taking report fields as input; assert no such path exists. Explicitly import another observer's report and assert it enters **structurally validated, not operation-authenticated, attributed, and inert** — nothing derivable exists to recompute, and no validation state is written. **Negative:** raw-write a self-consistent report; assert it is not detected on read, and that an audit detects it **only with the tamper log implemented and a valid anchored observer set** — otherwise the raw write remains undetectable, and the design text claims no more |
| **T2** | One started operation, one intent, one terminal record — and no act precedes the intent | Run each operation kind to success; assert exactly one qualifying fulfillment: the `run` where one is minted, the act-report otherwise. **Positive:** a post-intent attempt that mints no run closes through **exactly one** qualifying act-report. Attempt a second fulfilling registration on one intent → **malformed**, the log's rule as built. Make root selection fail, then the intent append fail; assert in each case **no act began** — no request issued, no lease taken, **no record minted** (an `event_token` generated in memory and carried by no intent and no record is not a mint). **Negative (a):** a missing-spec run request refuses **pre-intent**; assert a surviving boundary publishes an *unfulfilling* act-report, that it fulfills nothing, and that a crash there leaves no trace. **Negative (b):** a complete non-conforming execution mints a **run**, never an act-report. **Negative (c):** a dataset-production attempt opens the **operation intent** — assert the assessment-run intent cannot be spelled without a `spec_identity` |
| **T3** | Completion is three-valued and derived, never stored | Build all three states: an unmatched intent reads **unfinished**; an unreadable fulfillment pointer reads **indeterminate**, never collapsed into unfinished; a fulfilled intent reads **closed**. Assert no status field is spellable on any record — report, intent payload, or run. Assert deleting a published report moves its operation **closed → indeterminate**, not unfinished — the retention cost of §4, made checkable |
| **T4** | The report layer is inert by type | Add and remove reports and entries; assert the belief digest, admission, eligibility, and the coverage projection are byte-unchanged. Assert an **unfinished operation blocks nothing**: a location with no unmatched holdings intent projects normally while its operation's intent stands unmatched. **Negative:** delete an observation a report references; assert exactly the record-layer consequences occur — the active set and projection move as the holdings design says — while the report is unchanged and confers no protection |
| **T5** | Outcome vocabularies are reserved per act kind | Attempt `byte-locator-untested` on a managed-mutation, record-import, and subject-evaluation entry; assert each is unspellable. Attempt it on a locator act whose request **began**; assert refusal — that is `retrieval-failed`'s territory. Assert a preflight refusal and a deliberate post-stop skip both spell `byte-locator-untested` with distinct reasons. Assert no entry outcome constructs an observation — reports reference products and never mint them |
| **T6** | Findings are citable positions in a canonical sequence | Permute two entries; assert the report identity moves — order is identity-bearing. Cite **(act-report ref, entry index)**; assert it resolves to exactly one entry, and an out-of-range index is refused at the citing site. **R18 arm:** delete the cited report; assert the verification is unchanged and still valid, its embedded content intact |
| **T7** | A successful acquisition's provenance reference and report publish together, and no identity cycle exists | Assert no path publishes the dataset's provenance reference and the act-report in separate transactions or separate roots — the attempt is refused, never half-ordered. Mutate the report; assert the dataset **address** is byte-unchanged (the §6.2 basis excludes provenance) while the dataset's record bytes — its node-content identity — and the corpus-state identity **move** with the reference |
| **T8** | Report identity preserves occurrence, and reports are retained evidence | Run two operations with equal actors, timestamps and entries but distinct operation `event_token`s; assert **distinct identities**. Mutate each facet member in turn; assert the identity moves every time. Attempt to edit, supersede, and delete a report through every ordinary API; assert no such path exists |

## 6. What this unblocks, and what stays open

**Unblocked:**

- **The cut-3 run-capture seam is fully designed.** Cut 2's stop rule failed
  run capture at the holdings record; the holdings design closed that and
  named this seam as its residue. With completion, act reports, and the
  non-report designed, the "runs & the execution boundary" group — R1–R23,
  G2a, G4, the largest deferred group at 25 rows — sits behind a fully
  designed seam. Nothing here rules what cut 3 takes: this design makes the
  candidate eligible, not selected.
- **Ramp §6.6's "unfinished acquisition" is derivable** — the three-valued
  reading of §3.3, replacing a phrase that read over act termini with no
  operation-grain substrate.
- **The 24 undetermined records' determination can finish, checkably.** A
  closed report proves the observing operation **ended** and records its
  actual acts. Without a precommitted subject set it does **not** prove the
  sweep exhausted all intended records or locations — the claim is
  completion of the operation, never coverage of an intention.
- **Audit and import findings gain a citable home** — the evidence half the
  R19 flow (audit finds a contradiction → a separate constructor act mints
  the superseding verification) was missing.
- **Cooperative no-run closure exists.** A surviving boundary can close a
  post-intent attempt that minted no run. Unmatched intents accumulate
  fewer honest members; the formal claim of an unmatched intent is
  unchanged — an attempt with no qualifying recorded outcome.

**Open, deliberately:**

1. **Cross-root publication** of a dataset's provenance reference and its
   acquiring report — refused today (T7); supporting it needs its own
   ordering design.
2. **Compaction.** The rule today is retain. Any future protocol must
   preserve intent-qualification resolvability and fulfillment evidence —
   the two costs T3 makes checkable — and composes with the
   artifact-lifetime question, inherited not ruled.
3. **New operation kinds** arrive by amendment; the enum is closed today at
   the five of §2.
4. **The agentic surface** (kernel sub-problem 6): audit scheduling,
   liveness, the divergence table — untouched.
5. **The engine.** The operation intent reuses the log's existing
   intent/reduction machinery; A7's engine half landed 2026-08-14 and A8's
   certification landed 2026-08-17, while everything durable in Science still
   waits on composition-root adoption. Operational duties stay tabled with the engine bill.

## 7. What this changes elsewhere

The amendment set, applied at banking; every edit lands with a dated
citation naming this design and the section that rules it — the form
*(amended 2026-08-11, the act-report design §3)*. Historical
"what this amendment changed" counts in banked docs are preserved untouched.

1. **Kernel** (`2026-08-02-epistemic-kernel-design.md`): §4.4 and §10 —
   twelve kinds → **thirteen**; the later-designs pointer gains the
   act-report design (**T**) with its date; twelve frozen tables →
   **thirteen**.
2. **The exact count inventory**, beyond the kernel: the domain-extension
   boundary's **both** kind-count sites
   (`2026-08-04-domain-extension-boundary-design.md`); the adoption
   ledger's docket note (`2026-08-03-redesign-adoption-ledger.md`); the
   admission ramp §2.2 (`2026-08-09-admission-ramp-design.md`); the
   world-address ruling §3 (`2026-08-08-world-address-ruling.md`); and the
   guide's foundations heading, lead, and formal-model link
   (`docs/guide/foundations.md`).
3. **Formal model** (`2026-08-04-formal-model-and-claim-calculus-design.md`):
   §2.1's heading renamed to *the thirteen kernel kinds*; a thirteenth
   player row for `act-report` per §2 of this design — boundary-minted
   terminal or pre-intent refusal record; content identity over the facet
   including the operation
   `event_token`; immutable, never superseded, retained; affects nothing;
   inert under everything in belief; banked: this design, T1–T8. §3.2's
   `audit` signature gains a dated note — the evaluator's type is unchanged
   and still mints nothing; the `audit` operation's act-report is the
   boundary wrapper's (§4 of this design). §3.2's transition table narrows
   the `begin` (run) row to **assessment runs** and records
   dataset-production's operation-intent route beside it (§3.2 of this
   design). §5.1's extension totals move from 121 rows / ten tables to
   **129 rows / eleven tables**, with the assertion total recomputed from
   the final T arms as banked; §5.2 gains the **T block** with per-row arm
   counts.
4. **Tamper-evident log** (`2026-08-03-tamper-evident-log-design.md`), named
   at every touched site: **§3's intent union** gains its third consumer,
   the **operation intent** — payload (operation kind, minted
   `event_token`, actor), appended after the observer-corpus root freeze
   and before any act; **§6's qualification reduction** gains the
   operation-grain readings — for a non-run operation the act-report
   carrying the token; for a dataset-production operation the minted `run`
   or, when none is minted, that act-report; and the **assessment-run
   intent's qualification widens** — the `run` as built, or an act-report
   for a post-intent attempt that minted no run, a pre-intent refusal
   publishing an unfulfilling report; **boundary-built `fulfills`** is
   restated for the new consumer — no caller-selected `fulfills` exists;
   **L7**'s arm extends to the operation intent's width; **§9's
   science/`atoms` ownership split** records the operation intent on the
   science side, the `atoms` intent API unchanged. An `audit` operation's
   intent is the **boundary wrapper's**, never the evaluator's — the
   read-only evaluator appends nothing (§4).
5. **Computation** (`2026-08-02-computation-reproducibility-design.md`):
   §4.7's acquisition provenance gains the act-report reference member —
   existing fields authoritative; same transaction, same root (§4, T7).
   **§7.3c's closed constructor signature** gains the report-position
   citation as a **new explicit argument** — its resolved content is
   embedded in the comparison report with (act-report ref, entry index) as
   provenance, and the code-lineage certification remains the **only**
   authored claim input; **R18** (§7.3b) records the embedding; **R19**
   asserts the widened-but-still-closed signature — every other extra
   argument still refused, and deleting the cited report invalidating
   nothing. A dated note beside **R12**'s boundary-mediated arm records
   that cooperative no-run closure now exists, the formal claim unchanged.
   **§7.3c/R19's** "the audit … mints nothing" language gains a dated
   note: the audit's finding is recorded as an entry in the boundary
   wrapper's inert act-report, the evaluator still minting nothing
   epistemic (§4).
6. **Verified-holdings record**
   (`2026-08-10-verified-holdings-record-design.md`): §3's two "owed to the
   run/report design" passages and §7 item 6 gain dated closure notes
   naming this design.
7. **Admission ramp** (`2026-08-09-admission-ramp-design.md`): §6.6 gains a
   dated note — "unfinished acquisition" is now the operation intent's
   unmatched state under §3.3's three-valued reading. §8's item statuses
   are untouched.
8. **World addressing** (`2026-08-02-world-addressing-design.md`): §4.2's
   identity-basis table gains the `act-report` row.
9. **Normative contract** (`2026-08-03-normative-contract-design.md`): §4
   and §11 counts — **thirteen tables, 151 rows** (143 + T1–T8). §7.6's
   "audit mints nothing" ruling gains the wrapper distinction as a dated
   note — the evaluator unchanged, the act-report the wrapper's (§4).
10. **Adoption ledger** (`2026-08-03-redesign-adoption-ledger.md`): the
    log-consumer notes gain the operation intent (science-side consumer
    rules amended; the `atoms` intent API unchanged); **artifact 7 extends
    with T1–T8**; the docket note's count site is in item 2's inventory.
11. **Cut 2** (`2026-08-09-conformance-cut-2.md`): **no edit.** Cut 2 named
    the holdings blocker, already recorded as closed; the run/report
    residue was introduced by the holdings design, so nothing in the frozen
    text goes stale.
12. **Guide** (`docs/guide/`): foundations (item 2's heading/lead/link,
    thirteen kinds); open-questions — the third-cut entry updated to "run
    capture's seam fully designed", and a residue entry for §6's five
    opens; glossary — `act-report`, the operation intent, the three
    completion states, and the audit evaluator/wrapper distinction;
    contracts-and-adoption as touched; `updated:` frontmatter and
    `sources:` entries per convention.
13. **README and corpus guards** (`README.md`,
    `python/tests/test_designs_corpus.py`): twenty-one documents through
    2026-08-11; the design-table row; **151 rows across thirteen tables**;
    `GUARANTEE_TABLES` and `TABLE_OWNERS` gain **T**; the `_ROW` and
    `_ROW_RANGE` classes extend to `[GSWRCXNLDMPHT]`;
    `_COUNT_WORDS[21] = "twenty-one"` is added; `table_words[13]` is
    already in place from the holdings banking.
