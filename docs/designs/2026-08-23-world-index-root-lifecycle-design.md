# Root lifecycle and the store substrate — design (world-index slice 4)

**Date:** 2026-08-23
**Status:** banked 2026-08-23 — implemented and discharged; conformance
cut 9 (frozen at `0977bde`) discharged the same day, results at
`../plans/2026-08-23-conformance-cut-9-results.md`, execution rulings at
`../plans/2026-08-23-root-lifecycle-ledger.md`. Review closed at `56db3f3`;
the atoms-local §2–§4 contract was approved at `b1469f4` (findings through
`6555e46`) and its implementation merged and pushed on the atoms remote
(`bf559c2`). Promoted from `docs/superpowers/plans`' spec home at banking
(§8 step 7); the implementation plan is
`../superpowers/plans/2026-08-23-root-lifecycle.md`.
**Inherits:** `2026-08-10-verified-holdings-record-design.md` §2 (the
fail-closed writer state, the durability orders, the restore-as-verification
ruling, and the store amendments its §8 applied to the log design — the
authorities this slice implements); `2026-08-03-tamper-evident-log-design.md`
(the L table, the store genesis arm `store(store_id, forked_from?)`, the
stable-projection registered surface, L4's store arm, L10's store
instantiation); `2026-08-22-log-verification-design.md` (the evaluator, its
four-step precedence and observer-set discipline, §1.2's fork-genesis
exception, §1.3's empty-baseline amendment — lifted here for fork geneses,
§10's deferral ledger items 2 and 3); `2026-08-20-world-registry-design.md`
(W13's declared fork-constructor arm, the manifest grammar, `World.admit`);
packaging §5/X5 and limitation 5; adoption-ledger rows 2, 4, 5.
**Scope rule:** the holdings record itself — the `holdings-observation`
kind, its acts, the coverage projection, H1–H4, and the atoms holdings
dereference-and-hash and mutator post-state capture commands — is the next
slice's, not this one's. This slice builds the substrate those stand on.

## 1. Scope

**Built here (atoms, behind its own design gate — §2–§4, choreography §8
step 5):** the fail-closed
writer state; the root-model amendment admitting a second root kind while
the engine stays root-kind agnostic; `replicate_root`, `fork_root`, and
`grant_read_serviceability` with the read-only `read_lifecycle_state`
query; and the explicit pre-lifecycle migration.

**Built here (Science):** `init_store_root`; the widened `anchor_heads`
and `export_head_artifact`; the evaluator's store-subject path;
`replicate_root`'s thin wrapper; `restore_root`; `fork_corpus` and
`fork_store`; act-minted fork manifests through `World.admit`'s fork-of
path; and the L6 fork-baseline ruling.

**Not here, restated:** holdings reads and H1–H4; intent qualification and
G4; event-level L8; L13's preimage resolver. After this slice the open
remainder is **ledger rows 4–5's implementation remainder**; the
log-verification design's limitations 5, 8, and 9 remain independently.

## 2. The fail-closed writer state (atoms)

Writability is a **granted state recorded durably in the host's engine
bookkeeping** — the metadata root, single-host by construction, never
traveling with the tree. The coordinator refuses every cooperative mutation
of an existing root not granted writability. Recorded root-creation
operations are the sole pre-grant write exception: they may construct their
claimed destination while converging to its recorded lifecycle state. A tree
arriving without metadata cold-bootstraps **read-only and unserviceable**.

**The grant is host-local by a verifiable root/host binding, not by
assumption.** Bookkeeping is a directory, and a directory can be copied;
"never travels" is a construction fact about the engine's own operations,
not a property of `rsync`. So the grant record carries a **binding to the
host's stable machine identity and the root's canonical path**, and the
coordinator validates the binding **before honoring any grant**: a
mismatch reports **`binding-mismatched`** (§4's declared state) and
conveys no grant. This makes post-lifecycle copied bookkeeping fail
closed and supports the two-restored-copies arm. It cannot distinguish
pre-lifecycle origins; the explicit migration exception below addresses
that limit. The binding's
exact carrier is the atoms gate's to design; the requirement — no grant
honored without a matching binding — is frozen here. Forging the binding
in place is a raw bookkeeping edit, already out-of-band. One consequence
stated rather than implied: **moving or renaming a writable root
invalidates its grant, and no writable rebind operation exists** — the
path from a moved root back to writability is the fork, under a new
identity, exactly as for any other copy.

**Two steady-state grantors, plus the explicit pre-lifecycle migration:**

1. **`register_root`, only for its own initialization operation.**
   Registration records a **local initialization operation** in the
   host's bookkeeping **before** the genesis becomes durable; the grant
   completes that operation. A crash between durable genesis and grant is
   therefore finishable: **the retry matching the recorded initialization
   operation — and only that retry — completes the grant.** The bare
   matching-existing-genesis arm, with no recorded local initialization
   operation, **never grants** — otherwise a metadata-less copy could
   promote itself by re-registering the chain it carries.
2. **`fork_root`** (§4), after its new genesis is durable.
3. **The migration** — a version-bound, explicit transition for roots
   registered before the lifecycle state existed. It is honestly a third
   transition, not a case of the two above — and it is honest about what
   it cannot prove: pre-lifecycle bookkeeping carries **no host binding
   and no initialization operation**, so a copied pre-lifecycle
   bookkeeping directory is structurally indistinguishable from the
   original. The migration is therefore an **explicit operator-authorized
   exception**: the operator attests this host is the minting host, and
   the migration records the grant with a fresh §2 binding on that
   attestation — a cooperative obligation stated as one, never laundered
   into a structural claim. Structural refusal applies exactly where
   structure can see: **metadata-less roots and post-lifecycle binding
   mismatches never migrate**. Both the authorized success and the
   structural refusals are cut-9 arms (§7).

**Serviceability.** Writable implies serviceable — a root this host
initialized or forked serves reads by construction (for a fork, only after
its destination overrides, §4, are in place: nothing incomplete becomes
observable). A read-only root is serviceable only through
`grant_read_serviceability` (§4), and a metadata-less root is neither.

## 3. The root model (atoms) and the store root (Science)

Atoms is **root-kind agnostic**: it stores lifecycle state and opaque
genesis bytes; Science owns `corpus`/`world`/`store` payload construction
and validation. The store root is therefore a Science construction over
unchanged engine machinery: `init_store_root` mints a fresh 32-lowercase-hex
`store_id`, constructs the `store(store_id)` genesis payload
(`forked_from` absent), and registers the store's canonical surface.

**The stable projection, defined canonically by Science:** a store's
registered surface is **every non-bookkeeping root-relative entry, symlinks
not followed**. Atoms cannot derive this while remaining root-kind
agnostic, so every registering call — `init_store_root`, and `fork_root`
for both kinds — receives the **explicit canonical registered-surface path
tuple** from Science.

Corpus genesis stays identity-free with an empty baseline; the **fork
genesis** is the ruled exception on both counts (§4, §5).

## 4. The lifecycle commands and the state query (atoms)

> **Amended 2026-09-04 (write permits):** Science's lifecycle wrappers
> (`init_*`, replicate, migrate, restore grant, and fork) take a keyword-only
> `Authority` and require `lifecycle` before any filesystem or engine effect.
> `_fork_resume` remains the named primitive implementation behind checked
> callers.

All three are exact-retry operations; an interrupted invocation is
resumable, and resumption proves before proceeding. The two copy
commands are **no-clobber**: the destination must not exist, and
exclusivity is claimed durably at start by a root-local **operation identity**
claim published atomically with the destination directory — the fact a retry
recognizes across caller-selected metadata roots. The claim is reserved
engine bookkeeping, excluded from consumer surfaces and snapshots.

**`replicate_root(source_root, dest_root, dest_metadata_root)`.** Runs
under the source's held lease, so chain and payload are one coherent view
(a raw writer defeating the lease is the out-of-band bound, unchanged).
A claim-only destination directory may be published first as the
filesystem-level cross-carrier no-clobber point. Before the read-only stamp is
durable it contains only the reserved claim: no payload, chain, destination
override, lifecycle stamp or grant, or serviceability exists. Destination
bookkeeping and its read-only stamp become durable next; only then are chain
and payload exposed and copied unchanged. It grants neither writability nor
serviceability. Interrupted after the stamp: read-only, unserviceable,
restorable. Interrupted before it: metadata-less, cold-bootstrapping
read-only, with only the excluded claim as creation residue.

**`fork_root(source_root, dest_root, dest_metadata_root, genesis_payload,
surface_paths, dest_overrides)`.** Science constructs `genesis_payload`;
atoms never reads it. `dest_overrides` is an opaque set of destination-file
writes — the root-agnostic mechanism for installing the child manifest —
which atoms **applies before baseline capture, genesis, and grant,
interpreting nothing**. Under the source's held lease: materialize the
destination tree, apply the overrides, capture the baseline over
`surface_paths` (the existing internal baseline capture, reused), append
the fresh genesis as a **new chain** — parent and fork never share one —
and record the writability grant only after the genesis is durable. Retry
semantics split at the grant. A kill between genesis and grant leaves a
read-only root with a new genesis; **pre-grant retry resumes the grant
after proving genesis, baseline, and destination tree match** — an
interrupted fork is never stranded unusable. **After the grant, the
operation is complete and legitimate writes may change the tree**, so a
retry recognizes the stored operation identity and returns success
without requiring the original snapshot — it never compares the tree it
has no right to expect.

**`grant_read_serviceability(root, metadata_root)`.** Rechecks structural
facts only — the root is non-writable, and either currently unserviceable
or **already read-only serviceable, which returns success without another
write**: that idempotency is what makes the grant exact-retry like its
two siblings — then durably records read-only serviceability. It accepts **no verdict and no
attestation**; atoms cannot authenticate one, so none is offered a channel.
Calling it outside Science's restore orchestration is explicitly
**out-of-band**, beside raw bookkeeping edits and raw `rm`. Atoms never
exposes a `restore_root`: no atoms name implies verification.

**`read_lifecycle_state(root, metadata_root)`.** The read-only query
beside the three mutating commands: it reports the root's validated
lifecycle state, a closed **five-value union** — **writable**,
**read-only serviceable**, **read-only unserviceable**,
**metadata-less**, or **binding-mismatched** — with the §2 root/host
binding validated as part of the reading. A binding mismatch is its own
declared state, never reported as the state the bookkeeping's bytes
claim, and every consumer treats it as no grant. It is how
Science selects `admit_arrival`'s inspection mode (§7.2) and how any
consumer asks a lifecycle question without interpreting bookkeeping.

## 5. The fork-baseline ruling (lifting §1.3 for fork geneses)

A fork is a populated root with a fresh chain — the shape the
log-verification design's §1.3 declared unconstructible, leaving L6 wholly
unread. This slice is the **registration-surface design act** that
amendment named: a **fork genesis registers the destination surface after
`dest_overrides` as its baseline** — the copied source surface plus the
installed overrides, captured at the destination, which is why §4 orders
override application before baseline capture; non-fork geneses still
require an empty baseline, and **`init_store_root` refuses a populated
payload root** for the same reason. The capture reuses the registration
baseline machinery the fork needs anyway, so the lift costs no new
mechanism.

Both L6 arms become constructible and cut 9 selects both (§7): damage a
baseline-covered pre-log member under a surviving anchor → replay
**refutes**; a consistent anchor-free genesis/baseline rewrite →
**unresolvable**, never validated. **The L6 source row in the log design is
amended before cut 9 freezes**, so the cut's verbatim quotation contains
the lifted ruling rather than the unconstructible original (§8).

## 6. The fork acts, and the two `forked_from` facts (Science)

`fork_corpus(source_root, dest_root)`: mint a fresh `corpus_id`
— W13's fork-constructor arm: a fresh opaque mint, no re-mint path —
author the child manifest **from the act**, and call `fork_root` with the
corpus surface tuple and the manifest as a destination override, so the
manifest is complete before writability (and with it serviceability)
becomes observable. `fork_store` is the same shape minting a fresh
`store_id` into a `store(store_id, forked_from)` genesis.

The two `forked_from` facts are distinct and stay so:

- **fork genesis** `forked_from`: the parent's **genesis digest and head
  digest** at the fork point — chain-level ancestry, what the evaluator's
  genesis and ancestry steps read;
- **child manifest** `forked_from`: the parent's **`corpus_id` and
  corpus-state identity** — world-level provenance, what `World.admit` and
  the registry read.

Consequences: `World.admit`'s fork-of path now takes act-minted manifests,
retiring row 2's fixture authorship; packaging limitation 5 **narrows** —
an act-minted fork's `forked_from` is derived from the parent's manifest
`corpus_id` and corpus-state identity, never caller-supplied, while
declared-only forks stay authored claims; and L4's genesis-mismatch arm becomes readable
for corpora, scoped exactly: **a mismatch is between two fork geneses
selected as the same child corpus subject**. Parent and child anchors are
incomparable by policy and must never trigger it.

## 7. The store-subject surface, `restore_root`, and cut 9

### 7.1 Science's store-subject surface

`anchor_heads` widens to take store subjects beside corpus ids, each store
resolving by a **supplied root**; `export_head_artifact` widens to
`StoreSubject` **under the same resolution contract** — a supplied store
root whose genesis must carry the subject's `store_id`, since with no
store registry there is nothing else to resolve against. The
`HeadArtifact` and `LogHeadRecord` codecs already
carry stores — only the acts, wrappers, and the reachable evaluator path
widen: `_refuse_store_subject` is removed from **both** reachable sites
(`evaluate_log` and `_audit_log`), and `RootKind`,
`registered_surface_paths`, `_subject_hold`, and the audit target rule
widen for stores. A store audit runs under **one hold across inspection,
surface capture, and evaluation**. Genesis agreement is verified **before
head acceptance or registry mutation** — reading the genesis is itself
required, so the check gates what the read is used for, not the read.
No store-admission registry exists: subject-to-root binding is the
supplied root plus its store genesis, nothing more. `admit_arrival` stays
corpus-only.

### 7.2 `restore_root`

> **Amended 2026-09-04 (write permits):** the public wrapper is now
> `restore_root(dest_root, subject, observers, *, authority)`; its nested
> grant callback requires `lifecycle` before invoking the engine grant.

`restore_root(dest_root, subject, observers)`, under **one held
boundary on the destination root** across every step — no cooperative act
can interleave between check and grant:

1. **Inspect.** The evaluator's precedence is preserved: a malformed view
   **reaches `evaluate_log` and returns `malformed`** — never a
   pre-evaluation exception. Nothing binds the subject before inspection;
   binding reads the genesis and manifest, and inspection gets to those
   bytes first.
2. **Capture the presented identity and the surface**: the genesis (and,
   for a corpus, the manifest) as presented, and the registered surface
   under the subject's canonical projection.
3. **Evaluate** with the slice-3 evaluator against the **explicit observer
   set** — store- or corpus-subject registry log-head records, or supplied
   exported head artifacts. An empty observer set is `unresolvable`,
   replay never reached — L9's bound, no new rule.
4. **Subject-agreement gate**, by root kind, over the captured identity:
   for a **store**, the genesis `store_id` must equal the selected
   subject; for a **corpus**, the **manifest `corpus_id`** must equal the
   selected subject, while the genesis passes corpus/fork **form
   validation only** — corpus genesis never carries a `corpus_id` to
   compare.
5. **Grant only on `validated` with subject agreement.** Subject agreement
   is a **separate lifecycle precondition**: a `validated` report carrying
   a subject mismatch does not grant. Every other verdict is preserved and
   returned, the root left unserviceable. Restore never grants
   writability, for either root kind.

**`admit_arrival`'s inspection premise.** A restored corpus root carries
bookkeeping, so the arrival act's detached-mode premise no longer holds
for it. Ruled here: `admit_arrival` selects its inspection mode by
**validated lifecycle state, not by filesystem bookkeeping presence** —
partial or restored bookkeeping may exist while the root is unserviceable,
and a directory's existence is not a state. Science reads that state
through the atoms gate's **`read_lifecycle_state`** query (§4), branching
over the full five-value union: **read-only serviceable** takes
registered inspection (such a root has no possible pending writer state,
so registered inspection is exact); **read-only unserviceable**,
**metadata-less**, and **binding-mismatched** take the detached
inspection the act was built for; and **writable refuses** — a writable
root is this host's own root, not a replica arrival, and a `ReplicaOf`
claim over it is a lifecycle contradiction, never a detached read.
Consequently a **restored corpus arrival must be serviceable before
registered-mode `admit_arrival`**: run `restore_root` first, or arrive
detached. The detached staging-leaf ruling is untouched.

The Science `replicate_root` wrapper is thin: it calls the atoms command
and appends nothing — a replica's chain must arrive unchanged, so there is
no log event to mint; its evidence is the destination's bookkeeping state.

### 7.3 Cut 9 — expected dispositions

Fixed at the cut's own freeze, verbatim L-row splicing and the
any-unrun-arm rule as in cuts 5–8. Expected shape:

- **In:** L6 (both arms, under §5's lifted row); L10's fork,
  replica-construction, restore, and store-instantiation arms (the
  arrival-identity arm stays cut 8's); L4's store arm and the
  distinct-fork-genesis arm (§6's scoping); W13's fork-constructor arm.
- **Labeled:** the fail-closed writer state's negatives — metadata-less
  cold bootstrap read-only and unserviceable; both interrupted-copy and
  interrupted-fork windows; two restored copies of one `store_id` both
  entering service read-only; the out-of-band grant pinned as out-of-band;
  and the **migration's operator-authorized success and structural-refusal
  arms** (§2).

Acceptance runs under the certified-tuple discipline; every count claim
quotes pytest's own summary line under `pipefail`.

## 8. Choreography

1. This spec's review closes.
2. **Pre-freeze amendment:** the log design's L6 row is amended with §5's
   fork-baseline ruling, dated, so cut 9's verbatim quotation carries it.
3. Conformance cut 9: authored, second-read, frozen before implementation.
4. The implementation plan is written against the frozen cut.
5. Atoms design gate (§2–§4): design doc in the atoms repository → review
   → implement → merge on atoms `main` → **push** (cut 8's close-out made
   the push part of the gate, not a trailing disclosure).
6. Science implementation against the merged seam.
7. Certified acceptance, results record, and banking: this document
   promotes to `docs/designs/`; adoption-ledger rows 2, 4, and 5 are
   corrected in the same change (row 4 gains the lifecycle commands and
   the state query as landed atoms state; row 2's fork construction closes; row 5's remainder
   shrinks to intent qualification, event-level L8, and L13's preimage
   resolver); the log-verification design's limitations 2, 3, and 6 close
   or narrow — its limitations 5, 8, and 9 stand; packaging limitation 5
   narrows per §6; and the stale-claim grep runs over the user-facing
   docs.
