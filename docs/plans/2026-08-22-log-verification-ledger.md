# Log Verification and Anchoring Execution Ledger

- **Plan:** `docs/superpowers/plans/2026-08-22-log-verification.md`
- **Design:** `docs/designs/2026-08-22-log-verification-design.md` (promoted from `docs/superpowers/specs/` in the banking commit; cited throughout as *the spec*, which is what it was during execution)
- **Cut:** `docs/designs/2026-08-22-conformance-cut-8.md`
- **Results:** `docs/plans/2026-08-22-conformance-cut-8-results.md`

## Rulings

**R1: Spec clarification — merge and push obligation (§8, §11)**

The spec's original wording in §8 ("and the merge-then-push obligation extending row 4's existing unpushed-`atoms` disclosure") and §11 step 4 ("the push obligation extending row 4's disclosure") implied the atoms head is pushed as part of this plan. This is clarified to match row 4's actual practice: the new atoms head joins row 4's recorded **unpushed** disclosure, and pushing remains a prerequisite of any integration expecting a fresh checkout to build (identical to `read_chain`'s `2c077ed` treatment).

Cost if wrong: A reader assumes the atoms head was pushed during this execution, creating ambiguity about which pushed state a fresh checkout integrates against. Follow-up: aligned the same duty terminology in §2's seam introduction ("merge-and-disclosure" duty).

**R2: Staging-leaf carve-out ratified with a tightening (atoms gate, 2026-08-22)**

The atoms design's reading — a `.#~stage` occupied by anything other than a
staging envelope is a foreign leaf — is ratified, tightened to: the
exemption covers **readable, no-follow regular staging files only**. Spec
§2.1's sentence amended accordingly. Cost if wrong: tamper at the reserved
name would be reclassified as bookkeeping, exactly what an arrival verdict
exists to catch.

**R3: Detached `pending` weakening ratified (atoms gate, 2026-08-22)**

Staged registration evidence stays in `pending`; detached pending digests
need not occur in `entries`. Spec §2.1 amended to state the weaker
invariant. Cost if wrong: a consumer resolving pending digests against
`entries` misses the staged pair — the spec now says not to.

**R4: Engine refusals get a boundary contract (atoms gate, 2026-08-22)**

`ChainStateInvalid` (chain-vs-record contradiction), `TransactionHalted`,
and capture's `PreconditionRefused` are translated by the root-owned seam
adapters into `LogEvidenceRefused(phase, engine_error, detail)` with
`__cause__` preserved — no `LogReport`, not `ArrivalRefused`, outside every
precedence. Spec gains §6.4; the plan's Task 4 seam, Task 8 and Task 9
tests amended. Cost if wrong: an audit of a contradicted or halted root
surfaces a bare engine exception instead of a contracted refusal.

**R5: The `fulfills` submission gate approved (atoms gate, 2026-08-22)**

Including the `test_coordinator_run.py:363` edit, with atoms ledger row
27's carriage assertion preserved verbatim — after the shared-helper claim
was corrected to cover only the referent checks, with the duplicate check
split to submission-time and settlement-time (the defect exists only at
the second committed settlement). Cost if wrong: either the engine can
mint chains its own validator condemns, or a discharged atoms ledger row
loses its verification.

**R6: Defect subjects and `AbsentChain` aligned across both documents
(atoms gate, 2026-08-22)**

`ORPHAN_HISTORY`'s subject is the lowest unvisited digest;
`DUPLICATE_FULFILLMENT`'s subject is the second committed settlement
digest; `AbsentChain` means **no durable chain claim** — directory absent,
or empty without contradictory live metadata — and arrival treats either
as chainless. Spec §2.1 and the plan's Task 4 `DefectView` mapping
amended; the atoms design already carried the ratified behavior. Cost if
wrong: the two repositories' inspection contracts drift at exactly the
member the evaluator's findings name.

**R7: Plan defect — no `science/world/errors.py` exists**

Tasks 5, 7, and 9 pointed error definitions at a nonexistent module; the
existing central `python/src/science/errors.py` is the home, including for
`LogEvidenceRefused`. Cost if wrong: an executor mints a parallel errors
module against house convention.

**R8: The `TransactionHalted` adapter arm is tested at Task 4 (gate closure, 2026-08-22)**

Task 4's file list gains `python/src/science/errors.py` (where the seam
defines `LogEvidenceRefused`), and Task 4's tests cover the
`TransactionHalted` arm of the §6.4 translation; Tasks 8 and 9 cover the
`ChainStateInvalid` and `PreconditionRefused` arms in context. Cost if
wrong: one of the three contracted arms ships untested until an audit or
arrival happens to exercise it.

**R9: `PendingUnresolved` lives in `atoms.chain.errors` (Task 3 boundary, 2026-08-22)**

The plan's Task 2 lines pointed it at `atoms.core.errors`; the gate-approved
atoms design and the landed implementation put it in a new
`atoms/chain/errors.py`. The design wins; the plan's two lines are
corrected, and Task 4's seam imports it from `atoms.chain.errors`. Cost if
wrong: Task 4's implementer chases a nonexistent import path.

**R10: The well-formed view's genesis is `entries[0]`, by identity (Task 4
review, 2026-08-22)**

`WellFormedView.entries` includes the genesis at index 0 with
`genesis is entries[0]` — the engine's own linearization sets
`genesis_digest = entries[0][0]`, and the seam re-types rather than
reshapes. Tasks 5–8's replay and evaluator indexing build on this. Cost if
wrong: an off-by-one over the registered surface, caught by cut 8's replay
units.

**R11: Every seam adapter translates, including `read_head` (Task 4 review,
2026-08-22)**

`read_head` translates the inspect-phase escapes exactly as
`inspect_registered` does — §6.4's contract binds the root-owned seam
adapters as a class, and the phase vocabulary has no third member. The
`World`'s injected `_chain_head` reader is not a seam member and does not
translate. Cost if wrong: audit and the anchor/export acts would see two
different error contracts over the same engine state.

**R12: An act holding `world_lock` must not call `World` methods (Task 4
review, 2026-08-22)**

The seam's `world_lock` returns the identical non-reentrant lock an opened
`World` takes in `registry()`/`status()` — that identity is the contract,
and its consequence is that Tasks 5–9's act cores read registry state
through their own parameters, never through a `World` method call made
under the lock. Cost if wrong: a self-deadlock, not an error.

**R13: Cut 7's pinned audit moves under a ruling; its declaration file does
not move at all (Task 5 review, 2026-08-22)**

Spec §3.3 (build-origin records join the epoch publication transaction)
cannot land under any implementation without two edits to cut 7's pinned
audit `python/tests/acceptance/test_n2_cut7.py`: the `ContentHeads` stub's
`genesis:<name>` label cannot survive the record form's 64-hex validation,
and X2's exact set equality cannot survive a record joining the
transaction. Both edits are claim-preserving (the tip stays
`corpus_state_identity`; set equality is retained, extended by an
exactly-one asserted record) and are authorized here, following the cut-6
precedent of editing the analogous audit only under a recorded ruling. The
declaration file `python/tests/n2_arms_cut7.py` is frozen ever — the
Task 5 fix round restores it byte-identical and derives the anchors inside
`_locked_publication_plan` from the `anchors.yaml` member it already
receives. Cost if wrong: either a frozen surface drifts silently, or the
build's record half is derived from a re-parse the ruling did not weigh.

**R14: `LogHeadCollision` is a distinct named error (Task 5 review,
2026-08-22)**

The spec names the collision refusal without a type; the plan's minting
constraint covers domain strings only. `RuleCollision` is documented as
rule-path-specific, so the record path gets its structural twin in the
central errors module. Cost if wrong: one superfluous error name.

**R15: Corpus-subject export can refuse `BuildHold` (Task 5 review,
2026-08-22)**

`export_head_artifact` takes the carrier's operation lock in writer mode,
so an export during a build capture refuses `BuildHold` — a documented
refusal, added to the export core's docstring and armed. No deadlock
arises: builds capture before taking the world lock, so the world→corpus
order is consistent. Cost if wrong: an undocumented refusal surfaces
mid-export and reads as a defect.

**R16: The held-copy match runs on paths, not digests — a second stated
partiality of L13 (Task 6 review, 2026-08-22)**

Spec §5.3's "a held copy resolves iff its digest matches the recorded
state" is not implementable through the frozen Task-4 seam: states are
opaque above the composition root and the seam exposes no state→digest
accessor (verified against `LogSeam`'s surface). The landed policy pass
decodes held bytes, derives the path the copy's identity claims, matches
the removed path, and names the digest the copy was filed under; two
copies claiming one path resolve nothing. This is a second, distinct
departure beyond §10.4's resolver deferral: the match predicate itself is
weakened, and a single held copy of a different version can misclassify a
removal in either direction. Finding messages are scoped to what the
evidence supports (the copy, never the removed record). Obligations: L13
remains partial with this second reason stated wherever the first is; §5.3
gains a dated amendment at banking (Task 12); the results record
discloses it. Cost if wrong: a reader takes `removal-classified` as proof
the removed bytes were not a failing verification — the understated
immutability violation the pass exists to catch.

**R17: Removal findings carry a severity split (Task 6 review, 2026-08-22)**

`record-removed` is a warning (occurrence is not authorization; epoch GC
removes legitimately); `failing-verification-removed` is an error (§8's
immutability violation). `"warning"` is already the second member of the
nodes `Finding` envelope Science reuses; no production code branches on
severity. Cost if wrong: a reportorial distinction hardens into policy
somewhere downstream without a spec sentence.

**R18: Replay's divergence handling — skip the head compare, never the
policy pass (Task 6 review, 2026-08-22)**

After the first initial-fingerprint disagreement the head compare reports
consequences, not evidence, and is skipped; the policy pass still scans
every committed transition, so the removal inventory is always complete.
Cost if wrong: the highest-value finding of the pass (a
failing-verification removal after the divergence point) silently drops.

**R19: The world projection walks the three grammar namespaces, not the
exact grammars (Task 6 review, 2026-08-22)**

§5.1 says "the exact registry, epoch, and rules-store grammars"; the
landed `_world_surface` lists everything beneath `registry/`, `epochs/`,
`rules/` plus `world.yaml`. Strictly broader: a raw-created foreign file
inside a grammar directory becomes a head disagreement instead of
vanishing. The departure is toward more detection and is stated in the
docstring. Cost if wrong: a reader of §5.1 expects grammar-exact
enumeration and misreads a foreign-file disagreement as a false positive.

**R20: The bookkeeping exclusion is a dot-prefix rule, pinned to the
grammars (Task 6 review, 2026-08-22)**

`.nodes-index`, the engine's `.#~` sigil, and every other exclusion share
the dot prefix; every grammar that can name a claimed path (node kinds and
slugs, registry digests, epoch identities and members, rule identities and
member names) provably refuses a leading dot, and a test pins those
grammar anchors so the equivalence is load-bearing. Cost if wrong: a
future dot-prefixed claimable name silently shrinks the audited surface —
the coverage-overstating direction.

**R21: Provenance is a member of all three carrier arms (Task 7 review,
2026-08-22)**

§4.1 attaches the discriminator to epoch members; the evaluator fixes it in
every factory — `named-local` for a registry record and a world-root epoch
directory, `supplied-export` for a supplied member mapping and an
artifact's bytes — so L11's eligibility is one predicate. Behaviorally
identical today: artifacts are unconditionally `supplied-export` and a
world-subject registry record is unconstructible (§3.1). Forward risk
stated in the carrier docstring: a future artifact arm reading a locally
stored artifact would be labeled `named-local` and become ineligible,
diverging from §4.1's unqualified acceptance of artifacts for a world
subject. Cost if wrong: a carrier arm inherits a custody label its factory
could not establish.

**R22: "Mutually incomparable" is the pair statement of unplaceability
(Task 7 review, 2026-08-22)**

`entries` is a linearization (R10) and a sibling branch is a malformed
defect, so two *reachable* heads are always ordered; the incomparable arm
fires exactly when at least one of a differing pair is unplaced. This is
the spec's only reachable meaning. The pairing is restricted to
unplaced×unplaced so the finding is not re-derived against every healthy
anchor. Cost if wrong: a reader expects a state a linearization cannot
present.

**R23: An epoch carrier revalidates the identity over eleven members and
parses only `anchors.yaml` (Task 7 review, 2026-08-22)**

The other ten are covered by the identity digest and belong to the epoch
reader; an observer carrier is not a second `_locked_open_epoch`. The check
is **self-consistency**, not provenance: `from_export` recomputes the
identity from the mapping the caller supplies, so a caller can fabricate
all eleven and pass a matching identity. That is §10.9's model — custody is
caller-attested and reported as such — not a defect. Cost if wrong: a
reader takes a validated epoch carrier for evidence of origin.

**R24: An absent chain is stated as a `chain-absent` finding, under an
exported constant (Task 7 review, 2026-08-22)**

§6.2 ranks arrival's causes from the report's fields, and `chainless`
versus a fresh unanchored chain is otherwise indistinguishable there — the
two are refused and admitted respectively. Task 9 imports the finding-code
constant rather than matching a bare string. Cost if wrong: arrival
consults its own copy of the view, which §6.2 forbids.

**R25: Eligibility exclusions and the observer bound are always reported
(Task 7 review, 2026-08-22)**

An L11 exclusion is an `observer-ineligible` finding, never a silent
narrowing; the bound is reported in every outcome, malformed included, and
each entry states custody (`read-from-root` | `caller-attested`, §10.9's
deferred holder protocol). Cost if wrong: a caller's supplied evidence
vanishes without explanation, or a `supplied-export` label reads as a
custody claim the module cannot make.

**R26: A wrong-kind `presented` identity is a `TypeError` (Task 7 review,
2026-08-22)**

It is a caller-composition error, not a fact about the root, so it refuses
rather than becoming a mismatch finding — raised before step 1's malformed
return, which is the correct precedence for a programming error. Cost if
wrong: a composition bug is laundered into an evidentiary finding.

**R27: `CORPUS_GENESIS_DOMAIN` is restated in `verify.py`, pinned equal
(Task 7 review, 2026-08-22)**

`science.world` may not import `science.root`, so the constant is restated
and a test pins it equal to `root.GENESIS_DOMAIN` — the treatment
`anchors.WORLD_GENESIS_DOMAIN` already has. The genesis-form predicate
itself is single-homed across `verify.py` and `anchors.py` (Task 7 fix
round) so the two cannot drift. Cost if wrong: two spellings of one domain
diverge silently.

**R28: One genesis-form predicate, owned by `anchors.py`, strict grammar
(Task 7 fix round, 2026-08-22)**

`verify.py` and `anchors.py` had each stated the Science genesis form, and
they had already drifted — the evaluator required a 32-lowercase-hex
`world_id`, the export path did not. `anchors.py` now owns
`parse_corpus_genesis`/`parse_world_genesis` and both callers use them; the
strict grammar won because `WorldConfig.__post_init__` and
`registry._load_world_mirror` already enforce it, so the three loaders now
agree. Consequence inside Task 5's reviewed export act: an on-disk genesis
naming an ungrammatical `world_id` now refuses `WorldUninitialized` rather
than `WorldIdMismatch` — a reclassification within §3.2's documented
refusal set, unreachable for any world root Science can mint (the id is
grammar-checked at config construction and the genesis payload is minted
from it), and reachable only for a tampered or foreign-written genesis.
Cost if wrong: a hand-written world root that a reader considered valid
refuses export with a form error instead of a mismatch.

**R29: `epochs_ordered`'s descent includes the settlement entry (Task 8
review, 2026-08-22)**

A publication linearizes as registration → settlement, so the chain tip at
the instant E1's publication commits *is* the settlement entry, and a build
preflighting then records exactly that digest. Strict descent would answer
`unordered` for the archetypal sequential pair. Nothing the spec means to
exclude is admitted: a build that preflighted *inside* the transaction
recorded the registration digest, whose linearization position is strictly
lower, and still answers `unordered`. Cost if wrong: two epochs published
in sequence read as unordered, and L8's evidence inverts.

**R30: The publication moment is the earliest committed settlement of the
registration creating `epochs/<e1>/anchors.yaml` (Task 8 review,
2026-08-22)**

All eleven members land in one transaction, so any witnesses the same
registration; the anchors member is chosen because the predicate's other
half reads it, making a packaging regression fail both halves together. A
rolled-back first settlement is skipped in favour of a later committed one.
Consequence the ruling accepts explicitly: after a §9 deletion and
republication the *earliest* settlement is retained, so a build started
inside the deletion window is answered `ordered` against an epoch whose
members were absent at its preflight — §7 asks whether E1's publication
event precedes E2's build start in the world timeline, not whether the
members were readable then. Cost if wrong: the predicate is more permissive
than L8's reading of world-ancestry order.

**R31: An absent or malformed world chain answers `unordered` (Task 8
review, 2026-08-22)**

§7 scopes the predicate to an already-validated world chain, the return
type has two values, and the rule is stated in the docstring rather than
left as a fallback. Caller-input facts still refuse (`EpochUnknown`); root
facts are answered. A caller cannot distinguish "no order" from "unreadable
chain" — the audit act is the named place a damaged chain gets named. Cost
if wrong: a damaged world reads as merely unordered to a caller who never
audits.

**R32: `AuditTargetUnconfigured`, boundary history validation, and the
single store refusal (Task 8 review, 2026-08-22)**

`AuditTargetUnconfigured` is minted in the central errors module on R7/R14
precedent — `AnchorTargetUnresolvable` means the opposite state (cannot say
whose chain it would read). `history` is validated at the audit boundary
before the hold, because a corrupt key is a fact about the call, not the
root; the evaluator re-validates, as `replay` already does. The store
refusal is one statement with two callers: audit must refuse before
resolving a root, since a store subject has no root rule. An unreadable
manifest or mirror presents `None` — an unreadable claim is not a
disagreeing claim. Cost if wrong: three small vocabulary choices to redo.

**R33: `epochs_ordered` takes `config`, not `world` — spec §7 needs
amending at banking (Task 8 review, 2026-08-22)**

Spec §7 states `epochs_ordered(world, e1, e2)`; the plan, the brief, and
the landed code take `WorldConfig`, which matches the audit act's own
reason for refusing an opened `World` (it must run where `open_world`
refuses). The code is right and the spec sentence is stale. Obligation:
§7's signature is amended at Task 12 before the spec is promoted to
`docs/designs/`, or a design document banks a false claim. Cost if wrong:
the promoted spec describes an API that does not exist.

**R34: Cut 6's X5 replica clause is superseded, not satisfied (Task 9
review, 2026-08-22)**

Cut 6's declared arm X5 asserts that *a known id* refuses both `Fresh` and
`ReplicaOf` admission provenance
(`test_known_id_refuses_fresh_and_replica_provenance`). Slice 3 makes a
bare admit of a replica refuse `ReplicaAdmissionRequiresVerification`
**before the lock and before any known-id consideration**, so the arm's
replica half no longer demonstrates the row's claim, though its name and
both refusals survive and no frozen file was edited (`test_world_registry.py`
is not in `FROZEN_PRIOR_CUT_FILES`, and `n2_arms_cut6.py` is untouched). The
sabotage direction is unaffected — cut 6's harness mutates the tree
materialized at `CUT6_SOURCE_COMMIT`. But cut 6's own module docstring
states that weakening a live check while leaving its name and green result
in place is outside the harness's reach, which is exactly this case, so the
supersession is recorded here rather than left for the harness to miss.
There is no way to preserve the claim: a bare admit can no longer reach the
known-id check for a replica. Obligation: the cut-8 results record names
this supersession (Task 12). Cost if wrong: a frozen cut scores green over
a claim its declaration no longer covers.

**R35: `PendingUnresolved` maps to `ExecutionError(applied=0)` (Task 9
review, 2026-08-22)**

The atoms pending gate runs before `_append_entry`/`_run_under_lease`, so
the submitted plan applied nothing and `applied=0` is the honest value —
the catch-all's unproved `None` was not. It is not a `LogEvidenceRefused`:
§6.4's vocabulary is exactly three literals and the executor is not a seam
adapter. Both executor mappings are kept in step. Cost if wrong: an arrival
or build refusal reports an unknown application state where a proven zero
was available.

**R36: `open_world` reads the chain — spec-mandated, with two disclosed
consequences (Task 9 review, 2026-08-22)**

§6.3 requires it verbatim ("The genesis payload's `world_id` is read
through `read_chain` in both"), and nothing already read at open could
supply the genesis claim. Consequences, both disclosed rather than
discovered later: opening a world now requires the certified volume
(`read_chain` → `_recovery_lease` → `_project_lease`, the one production
call site naming the certified allowlist), and it now takes the atoms
project lock and resolves recovery, so opening can block on a concurrent
build and is no longer a cheap read. Blast radius verified as confined: no
`tools/`, CLI, or `src/` caller opens a world; every suite caller either
stubs the engine or runs on the certified volume, so today's narrowing is
zero. An unregistered-but-mirrored root now refuses at open rather than at
first write, mapped to the existing `WorldUninitialized` **in `open_world`
itself** — not a seam translation, so §6.4's closed three-literal
vocabulary is untouched, and `_log_seam().read_head` still surfaces the raw
engine refusal. That mapping is conditioned on the unregistered-root case
alone, because `read_chain` can also raise `PreconditionRefused` out of
recovery resolution (observation and create-effect sites), and relabelling
one of those as "never initialized as a world" would be a false statement
about a registered root. Cost if wrong: a mid-recovery refusal reads as an
uninitialized world, or a legitimate open refuses on a volume the rules
allow.

The mapping turns on the engine's **exact wording**
(`root.UNREGISTERED_ROOT`), not on the exception class and not on a
chain-leaf probe: `_registered_root` raises the unregistered refusal at two
sites, and only one of them means "chain directory missing" — the other is
"present but holding no entries", which a leaf-existence probe would miss
and which would mean re-deriving the engine's registration predicate after
its lease is released. The string is pinned against the engine's own source
by a test (R27's treatment of `CORPUS_GENESIS_DOMAIN`), and drift fails
safe: the mapping stops firing and the raw engine refusal reaches the
caller, never a false statement.

**R37: Cut 8's accounting is 51 full + 2 partial (Task 10 review,
2026-08-22)**

L7u1 is partial because the non-ancestor `fulfills` spelling is
directory-unconstructible — a linear content-addressed chain cannot present
a non-ancestor referent without a cycle — and is certified only in atoms's
typed core; the missing and non-intent spellings run on disk. **L2u5 is
partial** because cut 8's L2 bullet enumerates the pending gate's refusal
from all three commands and only two run: `run_transaction` and
`append_intent`. `register_root`'s existing-chain arm has no Science
mapping at all (both initializers call it bare, pinned mechanically by a
source assertion), so there is no Science behaviour to exercise. The fix
round also armed the second production mapping in
`DurableOperationPort.append_intent`, whose own comment said the two
mappings must not drift — the arm now asserts they agree on `(applied,
index)`, verified to bite by counterfactual mutation of each site
independently. Cost if wrong: the results record banks a "full" over an
enumerated arm nobody ran — the error §1 exists to forbid.

**R38: Obligation 1 is discharged two ways, and the split is stated (Task
10 review, 2026-08-22)**

Thirty-five units judge real on-disk canonical envelopes read back through
the engine's own `inspect_chain_detached`, catalogued two-way so a builder
cannot hide, with each of the nine deliberate defects asserting exactly one
engine kind. Sixteen units hand a chain *view* to a stubbed seam and cannot
meet the obligation literally; they are admitted on the narrower ground
that **the arm's claim does not turn on the chain** (it turns on lock
order, precedence, refusal placement, admission identity, or the count of
evaluator calls), named per unit, with the obligation's *purpose* run over
each through a per-unit view-factory table and a structural predicate
pinned against the engine on the three classes a linearization can express.
Three of them (L10u1, D3, D4) were convertible and were not converted,
because conversion would rewrite Task 9's reviewed arrival fixtures without
changing what the arms assert; that is recorded as a cost rather than
argued away. The three converted audit arms wire the registered slot to the
production *detached* inspection, so recovery does not run in them. Cost if
wrong: a fabrication smuggles in the malformation it claims not to have —
structurally impossible for the six defect classes a view cannot express,
which is why the substitute is adequate for what it covers.

**R39: The frozen L rows are amended in place; cut 8's quotes are a freeze
snapshot (Task 12 banking, 2026-08-23)**

Spec §1.2/§1.3's banking obligations reach the log design's **L4, L6 and L10
row cells**, which conformance cut 8 quotes byte-exact. The rows are amended in
place with dated markers — the corpus's own convention for a frozen table
(`designs extend and amend in place, never renumber`), already visible in L4,
L7 and L10's 2026-08-10 and 2026-08-11 markers — and the frozen cut is **not**
edited beyond its status header. The consequence, stated rather than left for a
later reader to discover: cut 8 §3.1's quotations are byte-exact as of the
freeze `117f37e` and no longer byte-exact against the live table. Cut 8 §8
limitation 5 anticipated exactly this ("the cut inherits the spec's dated
amendments … a future design lifts either, the affected declarations are
extended by a successor cut, never edited here"). Alternative rejected: keeping
the amendments out of the row cells and in section prose only, which would have
left the guarantee table stating a mechanism the code does not implement — the
failure mode this repository's design-doc rule exists to prevent. Cost if
wrong: a future second reader's byte-exactness check against cut 8 reports a
drift that is intentional and dated, and must read this ruling to see why.

**R40: Three live design documents outside the plan's Modify list are corrected
(Task 12 banking, 2026-08-23)**

The plan's stale-claim sweep covers `README.md`, `docs/guide/` and the adoption
ledger. Three further **live** (non-frozen) design documents carried claims this
landing makes false, and the house rule is that drift propagates outward:
`2026-08-03-world-index-packaging-design.md` limitation 1 ("the registry is
unanchored … deleting an admission record is undetectable today"),
`2026-08-20-world-registry-design.md` §8.1 ("full replay/refutation and
genesis-to-mirror agreement remain the deferred log reader's claim"), and
`2026-08-20-world-index-slice-2-design.md`'s out-of-scope list ("log
verification … genesis-to-mirror verification, pending the configuration-mismatch
audit"). Each gains a dated correction that closes only what actually closed and
names the bounds that survive. **Frozen conformance cuts 2, 3, 4, 6 and 7 and
the disposition record carry the same L-row deferral claims and are left
untouched** — a frozen cut's deferral table states the world at its freeze, and
editing one to track later work is the error the freeze discipline exists to
forbid. Cost if wrong: three extra dated paragraphs in documents that were
already going to need them.

**R41: The corpus guard's count-spelling table is extended (Task 12 banking,
2026-08-23)**

Promoting the specification takes `docs/designs/` from 31 documents to 32, and
`test_the_readme_states_how_many_designs_there_are` refuses a count it has no
spelling for. `python/tests/test_designs_corpus.py` gains one `_COUNT_WORDS`
entry (`32: "Thirty-two"`). This is the only Python edit in the banking change;
the file is in no cut's frozen set and no declared arm names a node in it, so
the cut-8 audit is unaffected. Cost if wrong: the guard would have failed
closed, which is what it is for.

**R42: The banking commit precedes the ledger commit (Task 12 close-out,
2026-08-23)**

The plan's Task 12 step 5 names the ledger commit first. It is made **second**
here, so that the `## Heads` section below can record the banking commit's
actual hash instead of a forward reference to a commit that did not exist yet.
No cleanup happens between the two — the constraint the plan's ordering exists
to enforce (never leave the ledger in a removable worktree) is satisfied either
way, and this order makes the head record exact rather than approximate. Cost
if wrong: none identified; the ledger is committed on the branch before anything
is removed, which is the whole of the requirement.

**R43: The cut-8 runner's deferred import is suppressed for the type checker
(Task 12 close-out, 2026-08-23)**

Running the project-wide `pyright` gate at banking returned **five**
diagnostics, not the four baseline ones: `tools/cut8_acceptance.py`'s
`from n2_arms_cut8 import CUT8_ARMS` is unresolvable to a static checker,
because the `sys.path` entry it resolves against is inserted three lines above
it at call time. Task 11 introduced it and the gate caught it here. The line
gains `# pyright: ignore[reportMissingImports]` with the reason in the
function's docstring; the gate returns to exactly four. Alternatives rejected:
adding `tests/acceptance` to a project-wide `extraPaths`, which would teach the
whole project to resolve a test directory to fix one deferred import, and
hoisting the import to module scope, which would make the standalone script
import the declarations on every run including the ones that never print the
count. **The edit is to cut 8's own runner, which no freeze pins** — cut 8's
`FROZEN_PRIOR_CUT_FILES` covers cuts 5, 6 and 7's runners and declarations, not
its own — and it changes no behaviour, so the acceptance run was re-collected
after it rather than before. Cost if wrong: a genuinely missing module in that
one import would be reported at run time instead of by the checker; the runner
already reports that failure by name without masking the run's own result.

**R44: `read_chain`'s `2c077ed` is no longer unpushed, and both records that
say otherwise are corrected (Task 12 close-out, 2026-08-23)**

R1 rules that the new atoms head joins row 4's **unpushed** disclosure. Checking
that precedent against the sibling repository rather than against the sentence
describing it showed the precedent had moved: `2c077ed` was **pushed on
2026-08-22**, the `atoms` remote `main` stands at it, and the local `main` is
nine commits ahead. Adoption-ledger row 4 and cut 7's results §4 both still said
the remote stood at `7e97e09`. Both are corrected here — row 4 in place, since
it is the corpus's single live authority for `atoms` state, and cut 7's results
by a dated note beneath the original sentence, since a results record is a claim
about its own discharge and rewriting it would erase what was true then. **R1 is
not weakened:** the slice-3 head `3aa5a76` is genuinely unpushed, its disclosure
is the one R1 requires, and the treatment it copies is what `2c077ed` carried
between merge and push. Cost if wrong: the corpus would go on telling a reader
that reproducing cut 7 needs a local clone it no longer needs — the
overstating-the-obstacle direction, but wrong all the same.

## Rulings — completeness

**R1–R44, complete.** R1–R38 were written at their task boundaries and
committed with them, in the commits named beside each task's head below;
R39–R44 are the banking task's own; R39–R43 were committed with the first
finalization and R44 with the correction commit that follows it.
No ruling was withdrawn, superseded, or rewritten after the fact. This ledger is
the whole record of controller decisions that departed from the plan text, and
it lives at a tracked path — the process failure cut 7's results §10 recorded
did not recur.

Rulings carrying obligations discharged in Task 12, and where each landed:

| ruling | obligation | discharged in |
|---|---|---|
| R1 | the new atoms head joins row 4's **unpushed** disclosure | adoption ledger row 4; results §4 |
| R13 | cut 7's pinned audit moved under a ruling; its declaration file did not | results §3 |
| R16 | §5.3 amended; L13's second partiality stated wherever the first is | the promoted design §5.3; results §7.1 |
| R33 | §7's signature amended before promotion | the promoted design §7 |
| R34 | cut 6's X5 replica clause named as superseded | world-registry design §5.2; results §7.2 |
| R37 | 51 full + 2 partial, per unit | results §1.1 |
| R38 | obligation 1's two grounds, and the three unconverted units | results §1.2 |

## Heads

- Atoms commit hash (Task 2): `3aa5a766efb5275e444de193407992ce33e8edb7` (local atoms `main`, merge of `design/chain-inspection`; unpushed, joining row 4's disclosure per R1)
- Science commit hash (Task 9): `6b858ab` (`fix(world): condition open_world's unregistered-root mapping on the engine's own wording`, closing the last implementation task)
- Science commit hash (Task 11): `4389d2a` (`docs(plans): state each acceptance count with what it counts`, the last commit the cut-8 evidence measured)
- Science commit hash (Task 12 banking): `55b6de7` (`docs(log): bank log verification and discharge cut 8` — the results record, the amendment set, and the specification's promotion)

Branch: `design/log-verification`, base `cd549aa` on `main`. **Not merged** — the
`--no-ff` merge is the human partner's act, and it inherits cut 7's reachability
constraint on `4a7dc19` and `c8c0b12` plus cut 8's own freeze pin `117f37e`.
