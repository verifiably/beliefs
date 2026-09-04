# System redesign — adoption-order ledger

**Status:** Living record, updated as designs bank and artifacts land.
**Purpose:** The banked designs are each careful about what they do *not* wait on, but no
document names the dependency order between them or the legal partial states in between.
This ledger does, modeled on `atoms`' deferred-obligation ledger: an entry leaves when its
owning design/plan lands *and* its verification covers it. The design commit that names an
entry discharges nothing.

## 0. The clean-start ruling (2026-08-04)

With every design banked, the redesigned system is **built from the ground up on
`nodes` + `atoms` in this repository**, rather than migrated into the existing
codebase. The prior implementation is preserved, public and unchanged, as
**`proto-science`** (`github.com/khughitt/proto-science`); this repository takes
the `science` name and starts its own version line.

Three consequences, recorded so they survive:

- **The git history is deliberately not carried over.** Nine design
  documents seeded the first commit (a tenth, the domain extension boundary,
  banked 2026-08-04; an eleventh, the formal model and claim calculus, banked
  2026-08-05 — §1 and §3 carry the current inventory); the review
  history that produced them —
  including the eleven-round review of the tamper-evident log — stays browsable
  in `proto-science`.
- **Key project elements are *reproduced*, never migrated.** Code may be
  borrowed, but a record only exists here if this system produced it. A migrated
  record would be a provenance-weak assertion — exactly what the kernel's
  guarantees exist to exclude — and nothing in §1's implementation items assumes
  the old codebase.
- **`proto-science` is not a dependency.** No import, no compatibility layer, no
  dual-write. It is heritage and a reference to read, and the two repositories
  share only the design documents' text.

Ownership moves with the restart: the system lives under the **`verifiably`**
organization rather than a personal account, so governance and long-term
stewardship are not tied to one individual. §5 records the namespace and
decomposition rulings that follow from it.

## Current state (2026-09-04)

This section is the one place that states what is built and what remains to
build. Every other live surface — the README and the contributor guide — links
here rather than restating it. It lists no unresolved design question:
`../guide/open-questions.md` owns those. Nothing below orders the remaining
work.

**Implemented through conformance cut 18.** Every cut from 4 onward has a
discharge results record under `../plans/`; cuts 1–3 are proved by their merge
ancestry and the surfaces they built
(`../plans/2026-08-28-current-state-evidence.md`).

- **Typed claims, admission and belief computation** — claim construction,
  canonical projection and identity, cross-language decode parity, the derived
  admission state, the assessment admission gate, the belief-input closure
  digest, and `science.belief.v1` under an exact binding (cuts 1–2).
- **Run closure, execution, replay, reports and qualification** — spec
  freezing and closure construction, the execution boundary through the minimal
  Snakemake adapter, dataset production, replay, verification-as-value, the
  act-report layer's completion reading, and general intent qualification with
  durable run publication (cuts 3 and 11).
- **Successor admission** — G4 closed at persistence width: `admit_spec_successor`
  derives recorded failures and unfinished attempts from the chain and the
  corpus's verification evidence under one hold and refuses an unreferenced
  successor by class (cut 12). The same cut reads R12 in full and leaves L7
  partial only on its banked limitation.
- **Certified persistence and the mutation families** — the composition root
  over the certified `atoms` engine, the add-only write boundary and read
  capability boundary, and supersede, revise, retraction and explicit import
  through it (cuts 4–5).
- **World registry, epochs, anchoring, lifecycle and verified holdings** — the
  authoritative world root, corpus manifests and corpus-state identity, the
  append-only registry with lifecycle status and presence, epoch publication
  with its derived maps and receipts, mutation-log anchor carriage and
  verification, the root lifecycle and store substrate, and store-side verified
  holdings with their intent-bearing acts (cuts 6–10).
- **Run confinement** — the confined boundary policy: a run executes inside
  a fresh namespaced materialization of the digest-verified runtime closure,
  each planning and execution launch attests the observed capabilities and
  fresh instance,
  `derive_scope` reaches `clean-environment`, and a derived verification
  admits to belief through `admission_record` — closing R15, R4, R9 and R13
  in full (cut 13).
- **Full workflow surface** — content-addressed workflow-definition snapshots,
  semantic wildcard job keys, planning-derived job and target sets, per-family
  seed obligations and execution coverage, definition and job-diagnostic
  queries, and the composed planning/execution receipt and run-domain matrix.
  R2, R16, R20, and R21 are closed; R23's local basis/composition disagreement
  from cut 5 §3.2 is read without reopening its cut-3 replay-cardinality arm
  (cut 15).
- **Coordination and view kinds** — the closed `science.view-query.v1`
  grammar, independently versioned coordination contract, opaque project and
  local addressing, dedicated mint/revision family, multi-corpus tip resolver,
  and world-inert packaging behavior. W11, W12, and W18 are closed; W13's
  two-project negative is read; W17 is closed for the ordinary revision family
  and remains partial only on intent-position, owned by `publish` (cut 14).
- **Two-root relocation** — public destination-first `move` and two-record
  `consolidate`, one shared operation token with root-local intents and reports,
  contract agreement, tagged lineage-basis reconciliation, target
  re-resolution, and sorted deduplicated locking. W5 reads in full; G3 and D7
  close; W16, C3, R23, M3, and T2 remain partial exactly as the results record
  states; T8 is a closed-row re-read (cut 16).
- **Write permits** — closed act families and governed-kind routes,
  `Authority(permit, actor)` bound once at every construction seam, checks
  before effects across the closed 37-definition inventory, and no
  caller-supplied actor. E1–E8 close at cut 17; the command framework's
  writer session and dispatcher are unblocked.
- **Managed deletion and the mutation-lane ride-alongs** — `delete` as an
  ordinary write under the root's lock, with no operation intent, no
  act-report, no referential check and no tombstone; the excluded kinds
  common to every world-changing operation; `retract` and `supersede`
  re-resolving under the lock after a real deletion; log verification's
  managed/raw asymmetry; the managed holdings deletion act as the last-held-copy
  transition; the corpus-local semantic audit, malformed classification first;
  explicit-import derivation validation refusing a contradicted verification or
  assessment before any payload write; `decode.claim_from_stored`, the restore
  seam; and the instrumented resolver behind the only corpus-backed evaluation
  path. G2c, G8, C6, R5, W16, M1 and M5 close; C1, T8, M11 and M13 are
  closed-row re-reads; S5, R23, R19, R22 and M3 remain partial exactly as the
  results record states (cut 18).

**Remaining implementation boundaries with named owners.** One row per
boundary: a stable id, what it is, who owns it, and what it blocks. Row order
carries no priority; ordering over these rows lives in
`../plans/2026-08-29-implementation-roadmap.md`. A boundary enters this
table only when a cut's accounting, a results record, or §1's rows prove it
still open; unresolved design areas are not boundaries and are not listed.

| id | boundary | owner | what it blocks |
|---|---|---|---|
| `url-retrieval` | the URL retrieval boundary, acquisition orchestration and typed retrieval grants: H4, G9, R10, T5, T7's same-root case | `2026-08-24-world-index-holdings-design.md` §1–§3 | the first acquisition of a dataset from outside the system |
| `world-resolution` | the read side of the world: W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 less its two-projects negative; W8a's coreference arms; S1, S1a and S5's cross-corpus reach; D3; X12 and M3's coreference arms; R19's cross-corpus recomputation; R23's snapshot, coverage, divergence and explicit-import clauses | `2026-08-02-world-addressing-design.md` and `2026-08-08-world-address-ruling.md` | resolution states, cross-corpus edges, views, the coreference balance |
| `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | `2026-08-04-domain-extension-boundary-design.md` | the first domain pack |
| `event-level-l8` | **Event-level L8** — the presence/exclusion relation across captured corpus heads | the tamper-evident-log design's own successor work (row 5) | row 5 reading L8 in full |
| `contract-cut` | **The first full contract cut, its executable suite, and N1–N10**; N2's closing doctrine; P1's resolver-negative arm; R22's resolver arm; the `instrument-certification` arms of W8a, X12 and C10; R23's rules-store clauses | sub-problem 5b (row 7) | the normative contract's own guarantees; disposition of the legacy check modules; the conformance-package split (§5) |
| `log-remainder` | L1, L4; L10's relabel | `2026-08-22-log-verification-design.md` | row 5's L rows read in full |
| `act-report-remainder` | T1, T2, T4 | `2026-08-11-act-report-design.md` | the T table in full |
| `packaging-remainder` | X5's relabel; W8a's import-boundary and audit arms | `2026-08-03-world-index-packaging-design.md`; `2026-08-20-world-index-slice-2-design.md` | X5 and W8a read in full |
| `parity-fixture-2` | the second `science.identity.v1` parity fixture, numeric and escape arms | `2026-08-04-formal-model-and-claim-calculus-design.md` §8 (§3 item 8) | cross-language parity of the identity arms tested twice and compared never |
| `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm; C7's consolidate prerequisite discharged at cut 16 and the deletion surface it shares at cut 18 | sub-problem 5a, `2026-08-03-correction-lifecycle-design.md` | the correction lifecycle in full; buildable now, and the mutation lane's only open boundary |
| `l13-preimage` | **L13 preimage resolver** — preimage-backed classification of a removed verification | the named `atoms` blob-read seam (`2026-08-03-tamper-evident-log-design.md` §5.3) | row 5 reading L13 in full; until then the held-copy match is a path match |
| `persistence-cut` | X2's persistence-cut arm | the `atoms` A8 certification extended to the publication path, a cross-repo seam `atoms`' own design owns | X2 in full |
| `verification-publication` | durable publication of verification records — a derived verification written into a corpus through the operation port, with admission evaluated over records read back | the persistence seam; no design names it yet (cut 13 §2) | admission over stored verifications rather than in-memory records; scope recomputation for a stored verification (cut 18 §7) |
| `nodes-remainder` | the reserved-path contract, recoverable construction, digest-id hazards | `nodes` `2026-08-03-nodes-under-the-system-redesign-design.md` (row 3) | audits over damaged corpora; manifest safety |
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot — owed, undesigned | every rendered label; the ambiguous-search refusal |
| `weighted-belief` | S6 arm (h) | the first successor belief policy admitting unequal weights, blocked on ρO3 | weighted belief |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 | an untypeable span minting nothing, end to end |
| `cross-root-publication` | T7's cross-root case | the act-report design's cross-root publication residue | cross-root publication of a provenance reference and its report |

Detailed state, with every dated correction, stays in §1's rows and §3's order
of work. The newest results record
(`../plans/2026-09-04-conformance-cut-18-results.md`) closes G2c, G8, C6, R5,
W16, M1 and M5, re-reads C1, T8, M11 and M13, and leaves S5, R23, R19, R22 and
M3 partial on their named remainders. `test_the_ledger_summary_names_the_newest_remaining_boundary` holds
this section to whichever record is newest;
`test_the_roadmap_and_ledger_name_the_same_boundaries` holds this table and
the roadmap to one set of ids.

## 1. Unbuilt artifacts and what waits on them

| # | artifact | owner | waits on it | state |
|---|---|---|---|---|
| 1 | **World index** — address/producers/retraction/**coreference** maps + producer snapshot, publishable and consumable without the corpora it names *(membership changed 2026-08-08, `2026-08-08-world-address-ruling.md` §4.3 and §5.5: the **alias** map retired — labels are rendered on read, so no corpus content derives it — and the **coreference** map arrived, publishing each endpoint pair's **reduced** balance and distinct-key count so a balance is never computed from whatever happens to be checked out — the **edge state is derived per query**, never stored, because an immutable epoch cannot know the world a later query spans or whether the receipt still resolves. Still four maps; the coreference map is **not** a belief input, and its **coreference-reduction receipt** is designed on the retraction-map contract — packaging §7, X9/X10/X12, amended 2026-08-08 — so the map cannot be published without the completeness evidence)* | world §5; packaging; `2026-08-20-world-registry-design.md`; `2026-08-20-world-index-slice-2-design.md` | `not-present` resolution, receipt checkability, ~~merge inbound hygiene~~ *(lapsed 2026-08-08 — merge is retired and `consolidate` rewrites no inbound reference)*, `corpus_id` uniqueness refusal, §9 anchor carriage (repro §9 amendment 2026-08-03), and retraction discovery — the third derived map, target identity → retraction addresses (5a §4) | **The authoritative core landed 2026-08-20** (`2026-08-20-world-registry-design.md`; cut 6 results at `../plans/2026-08-20-conformance-cut-6-results.md`): world root, corpus manifest and fresh adoption, corpus-state identity, registry admission, and lifecycle status are implemented. Final boundary hardening landed at `fdea7a7`; the slice is merged on `science/main` through integration-lock correction `567ebb4`. **The epoch carrier is now implemented and cut 7 is discharged** (`2026-08-20-world-index-slice-2-design.md`; frozen cut 7; results at `../plans/2026-08-20-conformance-cut-7-results.md`): the rules store, coherent capture, the four derived maps and their four fixture-bound receipts, content-addressed epoch publication with `current`, the bound read surface, whole-epoch GC, and anchor carriage all run, with **38 selected + 10 labeled = 48 declarations** across **7 rows in full and 4 in part**, discharged on the certified tuple. **The work merged into `main` on 2026-08-22 with `--no-ff`, preserving history as results record §7 requires (integration commit `83744e7`)**; that constraint outlives the merge and binds every later integration. This row's artifact is complete. |
| 2 | **Corpus manifests / `corpus_id` minting** | world §5 | world index build; exact corpus-state identity | **Partially landed 2026-08-20** (`2026-08-20-world-registry-design.md` §3–§4): fresh adoption and minting, plus corpus-state identity, are complete. **Build-time uniqueness is now implemented and discharged** by world-index slice 2 and cut 7's X5 build arm (`../plans/2026-08-20-conformance-cut-7-results.md`): a coverage naming two carriers with one `corpus_id` refuses `CoverageUnresolvable` at preflight, with the standing `duplicate-carrier` finding still emitted. **Fork construction landed 2026-08-23** (world-index slice 4, `2026-08-23-world-index-root-lifecycle-design.md` §6; results at `../plans/2026-08-23-conformance-cut-9-results.md`): `fork_corpus` mints the fresh opaque child id and act-authors the destination manifest — `forked_from = (parent corpus_id, parent corpus-state identity)` derived at the bound snapshot, installed by the engine's recorded overrides before the writability grant — and `fork-of` admission is proven end-to-end through `World.admit` with no fixture-authored manifest (cut 9 W13 u2). |
| 3 | **`nodes` contract deltas** — shipped, versioned §11.1 projection; reserved-path contract; recoverable construction; digest-id hazards | `nodes` `2026-08-03-nodes-under-the-system-redesign-design.md` | node content identity and corpus-state identity (world §5, amendment 2026-08-03); manifest safety; audits over damaged corpora | Seam frozen 2026-08-17 (`nodes` `2026-08-17-nodes-write-plan-executor-seam-design.md`, pre-normative — binds the future standard amendment); detailed review complete 2026-08-17; the failure-attribution amendment landed as `abbf52b` on 2026-08-18. The composition-root adapter design banked the same day, consumer-exercising the create path and activating Science's sign-off right over it. **The seam implementation has landed in `nodes`** (`WritePlan` ops, the executor protocol, `DefaultExecutor`, `validate_plan`, `Corpus(root, executor_factory=...)` and the two error names, Python and TypeScript, through `e65bc89`), and Science's durable executor consumes it. **The public, versioned §11.1 RFC 8785 canonical-text API landed in `nodes` at `7cd9bd1` on 2026-08-20; strict non-JSON boundary hardening followed at `5a00bba`, now merged on `nodes/main`.** The reserved-path contract, recoverable construction, and digest-id hazards remain outstanding at the states recorded in the owning design. |
| 4 | **`atoms` A8** — persistence-cut exerciser and durability certification | `atoms` authority design §14 | production durable multi-file commit; retirement of the single-writer/no-durability profile claims (substrate §7) | **A7 landed 2026-08-14; A8 landed 2026-08-17.** A8a supplies the synthetic persistence-cut agreement model; A8b's physical certification swept nine scenarios, 916 marks, and 3,247 replay prefixes with zero violations. Production volume binding now admits exactly the certified `linux`/`linux-4`, kernel `7.1.8-arch1-3`, ext4 tuple with `async`, `barrier=1`, `commit=5`, `data=ordered`, feature masks `compat=0x3c`, `incompat=0x246`, `ro_compat=0x46b`, and `flush-honoring-disk.v1` storage; every other tuple fails closed. **Plan B item 1 landed 2026-08-18 on `science`'s `feat/composition-root-adapter`**: generic corpus writes flow through the certified engine, and conformance cut 4's frozen selection is discharged on a certified volume (`docs/plans/2026-08-18-conformance-cut-4-results.md`). The 2026-08-18 review closed both engine-forced deviations as dated design amendments (§3 steps 3 and 6 there — the `consumer_tag` grammar and derived parent-directory effects; cut 4's frozen text ruled unviolated, in its registration reading), recorded the stored-document mapping as normative surface (design §5a), and added the `semantic-hash-missing` strengthening — an unstamped governed kind refused on read — as a labeled post-freeze arm outside the frozen selection. **Plan B item 2 landed 2026-08-19** (`2026-08-19-family-adapters-design.md`): supersede, revise, retraction, and explicit import flow through the certified engine, and conformance cut 5's 28 selected declarations are discharged (`docs/plans/2026-08-19-conformance-cut-5-results.md`). The hard cut's composition-root-adoption half is complete. Science's profile still claims single-writer operation: the single-planner restriction is in-process by an operation lock and cross-process a stated deployment obligation, so substrate §7's claim retirement waits on more than this slice. **This row is the corpus's single authority for `atoms` implementation state. World-index prerequisite (2026-08-20) — landed 2026-08-21:** slice 2 §2 specified the public coordinator command `read_chain`, returning one complete validated `ChainView` under the recovery lease. It is designed, implemented, reviewed, and **merged into the local `atoms` `main` at `2c077ed745f6eabfec6816c16803e78eefaa279c`, and pushed on 2026-08-22** *(corrected 2026-08-23: it was unpushed when cut 7 discharged and its results record §4 says so; the `atoms` remote `main` stood at `7e97e09` then and stands at `2c077ed` now, so cut 7's reproduction prerequisite is satisfied and that one sentence of its §4 is stale)*. Science resolves `atoms-core` as an editable path dependency, so that merge is what makes the slice-2 branch green; reproducing cut 7's discharge requires that commit, and it is now available from the remote. **Log-verification prerequisite (2026-08-22, `2026-08-22-log-verification-design.md` §2 and §8) — landed 2026-08-23:** three more public commands, behind their own design gate in the `atoms` repository — `inspect_chain`/`inspect_chain_detached`, the never-raises structural inspection returning `WellFormedChain`, `MalformedChain` or `AbsentChain` over one typed validation core shared with the raising paths, so the fourteen-entry defect taxonomy cannot fork; the **batch path-state capture** command over `(backend, root, paths)`, which is what makes "no second summary model" a mechanism rather than a promise; and the shared post-recovery **pending gate**, refusing `PendingUnresolved` from `register_root`'s existing-chain arm, `append_intent`, and `run_transaction`. Designed, reviewed, implemented, and **merged into the local `atoms` `main` at `3aa5a766efb5275e444de193407992ce33e8edb7`, and pushed on 2026-08-23** *(corrected 2026-08-23: it was unpushed when cut 8 discharged and its results record §4 says so; the `atoms` remote `main` stood at `2c077ed` then and stands at `3aa5a76` now, so cut 8's reproduction prerequisite is satisfied and that record carries the dated correction)*. Science resolves `atoms-core` as an editable path dependency, so that merge is what makes the slice-3 branch green; reproducing cut 8's discharge requires that commit, and it is now available from the remote. **Root-lifecycle prerequisite (2026-08-23, `2026-08-23-world-index-root-lifecycle-design.md` §2–§4) — landed 2026-08-23:** the fail-closed writer state as schema-v3 host bookkeeping (the singleton lifecycle row binding machine identity and canonical root path, the retained root-creation operation row, the ten reviewed triggers); the closed five-value `read_lifecycle_state`; the shared writability gate in front of `append_intent` and `run_transaction`; `register_root`'s recorded initialization operation and post-genesis grant; `replicate_root` and `fork_root` with the claim-only no-clobber destination, canonical request/snapshot proofs, and the fork retry split at the grant; `read_pending_fork_operation` and `resume_fork_root`, the resume-before-mint seam; the structural, idempotent `grant_read_serviceability` (creating bookkeeping for a validated metadata-less cold root); and the operator-authorized `migrate_root_to_lifecycle_v3`. Designed behind its own gate in the `atoms` repository (`docs/2026-08-23-root-lifecycle-commands-design.md` there, approved at `b1469f4`), implemented, reviewed, **merged into the local `atoms` `main` and pushed on 2026-08-23; the remote `main` stands at `bf559c2`** — so cut 9's reproduction prerequisite is satisfied from the remote at discharge, with no unpushed disclosure to record. This discharged the holdings-prerequisite clause below for the lifecycle commands (replica, restore admission, fork, writer state, store root kind). **Holdings prerequisite (2026-08-10, verified-holdings record design §3, §7 item 7), under authority §12.2's Plan B:** the coordinator read command (dereference-and-hash under the private lease); post-state capture on the mutating commands — the post-write hash, the post-delete absence check, and `MoveNoClobber`'s dual-location result (source absence plus destination hash from the one effect), each returned before the lease releases, the two-intent move orchestration over that result staying the science boundary's; the replica, restore, and fork commands under the fail-closed writer state — writability granted only by initialization and the fork, a metadata-less store root cold-bootstrapping read-only and unresolvable for holdings reads, the restore command admitting a copy to read-only service only on a `validated` verdict from the log's verification act over the store subject and an explicit observer set of eligible store anchors — every other verdict preserved, the root left unserviceable — never granting writability; a claim-only destination directory may be published first as reserved, surface-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp, and the fork's new genesis durable before its writability grant; and the root-model amendment — §12.2 keys Science's engine root on a corpus root, and the managed payload store arrives as a second root kind, an `atoms` project root whose genesis carries the store identity. A5b's boundary is preserved throughout: the coordinator acts on the consumer's behalf, and no consumer ever receives a `Lease`. **Holdings prerequisite closed 2026-08-25:** the atoms-local holdings design was approved at `558817b`; `read_path_state` and `TransactionOutcome.final_states` were implemented, reviewed, merged `--no-ff`, and pushed — atoms remote `main` stands at `038513f`. Science's world-index slice 5 consumes those seams and implements the governed observation kind, intent-bearing store acts, mechanical coverage, holdings reduction and receipt, and dataset adapter; cut 10's 31 declarations discharged on `design/holdings` (`../plans/2026-08-24-conformance-cut-10-results.md`). The Science slice merged into local `main` with `--no-ff` as `35be6ff` on 2026-08-25; not pushed. Row 4's holdings clause is complete. |
| 5 | **Tamper-evident mutation log** (repro §9) | `2026-08-03-tamper-evident-log-design.md` — `atoms` owns registration (the A7 executor path, landed 2026-08-14); Science owns anchor carriage and verification | closing kernel §8.7's four recorded-mutation consequences and strengthening the fifth — chronology — for boundary-mediated executions (G2a/R12's out-of-band negative remains) | **Design banked 2026-08-03** (per-root chains with settlement lifecycle, epoch-cadence anchors + explicit anchor act, surviving-observer bound; kernel §8.7/G2a, comp §3.3/R12/§9, packaging §3/§4/§5/§5.1/§5.2/X9/§12/lim. 1, and `atoms` §15 amended in the banking commit); A7 implements the engine half and Science now registers corpus mutations through it. **World-index slice 2 has now implemented the anchor carrier** (`../plans/2026-08-20-conformance-cut-7-results.md`): each published epoch carries the per-corpus `(genesis_digest, head_digest)` anchors and the build-start world head, captured inside the same hold that captured the corpus state, and a certified cut-7 arm decodes both from the engine's committed entry files and pins the correspondence. **Carriage and verification have now both landed** (2026-08-23, `2026-08-22-log-verification-design.md`; frozen cut 8; results at `../plans/2026-08-22-conformance-cut-8-results.md`; merged into `main` on 2026-08-23 with `--no-ff`, integration commit `10cc84b`): the ruled registry log-head record and the exported head artifact with their codecs, the explicit anchor act with its idempotency and collision rules, the one read-only four-outcome evaluator and its four-step precedence, the registered-surface projection and replay with its removal policy pass, the audit act, the verified `ReplicaOf` arrival act with `World.admit`'s replica refusal, the world genesis↔mirror agreement check (discharging the dated slice-1/2 deferral), and the ordered-cuts predicate — **43 selected + 10 labeled = 53 declarations** across **5 rows in full and 7 in part**, with L6 unread, discharged on the certified tuple. Of the 53 units, 51 are full and 2 partial (L7u1, L2u5). **This row stays partial**, and the remainder is named exactly: **general intent qualification** (the intent-boundary slice's general reduction and run-/operation-shape arms) *(G4 closed at cut 12, 2026-08-29: `2026-08-29-successor-admission-design.md`)*; **the preimage-backed L13 classification**, waiting on the named `atoms` blob-read seam, with the held-copy match meanwhile weakened to a path match (that design's §5.3, amended 2026-08-23); and **event-level L8**, the presence/exclusion relation across captured corpus heads, this design's own successor work. L10's fork, replica-construction, restore and store arms landed 2026-08-23 with world-index slice 4; **its two holdings-read arms and L7's holdings-shaped qualification and append-before-mutation arms landed 2026-08-25** with world-index slice 5 (`2026-08-24-world-index-holdings-design.md`; cut 10's 20 selected + 11 labeled = 31 declarations discharged, `../plans/2026-08-24-conformance-cut-10-results.md`). Three of kernel §8.7's four recorded-mutation consequences close here — G8, semantic identity, and 5a's standing subtraction; G4 does not, and chronology's strengthening stays boundary-mediated as banked. **Log-consumer note (2026-08-11, act-report design §3):** the intent union gains its third consumer, the **operation intent** — Science-side consumer rules amended: the boundary freezes the observer-corpus root, appends the intent before any member act, and constructs its `fulfills` for the closing terminal record; the `atoms` intent API is unchanged. |
| 6 | **Retraction + correction lifecycle** | sub-problem 5a (§2) | four banked limitations that currently say the wrong answer stays computable (comp §5.2/§11.13/§13, world lim. 11) | **Banked 2026-08-03** (`2026-08-03-correction-lifecycle-design.md`; kernel §3.3/G8/§8.7 amended in the banking commit); cut 5 landed its selected C1–C6 and C10 arms on 2026-08-19; C7–C9 and the unselected clauses remain deferred to their named world-index, audit, and registry-compile dependencies. |
| 7 | **Normative contract + conformance oracles + instrument certification** | sub-problem 5b (§2) | disposition of the 63 legacy check modules (principle in 5b §8); homes for G1, G2a–G2c, G3–G9 (**G9 added 2026-08-09**, admission ramp §6.3); S1–S8 (S1a); **W1–W16** (W5a, W8a–b); R1–R23; C1–C10; X1–X12; N1–N10; L1–L13; D1–D10; M1–M13; P1–P9 (N, L and D added 2026-08-04 — L having been omitted at the §9 banking, and N because 5b §5 puts every oracle table in the suite; **M added 2026-08-05**, on the obligation that design recorded in its own header before drafting, so a third table would not arrive late; **P added 2026-08-05** with the belief policy, under `P` because `B` is the formal model's belief reading); **H1–H4** (added 2026-08-10, the verified-holdings record design §6 — the H table joins the suite on the same rule that added N, L and D); **T1–T8** (added 2026-08-11, the act-report design §5 — the T table joins on the same rule) | **Design banked 2026-08-03** (`2026-08-03-normative-contract-design.md`; tenth kind `instrument-certification`, rule-binding recipe member, certification-enumeration receipt — kernel, world §3/§4.2/§5/W8a, comp §4.2/§4.2a/§7.3/§7.3b–c/R18/R19, 5a §3/§4/C10/§9, packaging §5/§5.2/§7/X9/X10/X12 amended in the banking commit); part of R1–R23 with G2a, G4, M2 and T1–T8's first arms landed 2026-08-12, conformance cut 3's slice (`2026-08-11-conformance-cut-3.md` §4.1/§4.2); G4 read in full at persistence width by cut 12 (2026-08-29); the first contract cut, the executable suite, and N1–N10 await implementation |
| 8 | **Domain extension boundary** — where domain-specific material lives across `nodes`, `science`, and downstream domains | `2026-08-04-domain-extension-boundary-design.md` | consistent organization of domain material; the first domain pack; the predicate-vocabulary design | **Design banked 2026-08-04** (interpretation as facet conjunction with an explicit promotion trigger; exact vocabulary bindings; `ProfileSpec` as the sole compiled profile with a zero `nodes` delta; manifest `profile` block inside corpus-state identity; consulted profile contracts in G3 — world §5/W13/lim. 9, packaging §6, kernel §5.1, substrate §6.1/§12, and this ledger amended in the banking commit); D1–D10 await implementation |
| 9 | **Formal model + typed claim calculus** — a formal model of the banked system (M₀), the smallest system satisfying the intended guarantees (M\*), and the refinement map between them | `2026-08-04-formal-model-and-claim-calculus-design.md` | the claim grammar and canonical tag encoding (`science` base contract); `π_claim` + `tag_claim` in `science.identity.v1`; `ProfileSpec` compilation of claim schemas; the Python/TypeScript claim-identity parity fixture | **Design banked 2026-08-05** (a proposition **is** a typed claim, `Claim = Σ(op:Operator). Args × Qualifiers × Polarity × Layer`, with `statement` demoted out of identity; five-way term resolution; contract succession for claim vocabulary — kernel §4.1/§5/§8/§11 with G3, G7 and limitation 4; comp §7.1; world §4.1/§4.3/W4/§10; substrate §4.2; 5a §3/§4/C10; 5b §4; D §5/§6/§8/§12 with D3, D6 and limitation 2; and this ledger and the README amended in the banking commit); cut 1 implements and tests its selected arms of M4–M11 and M13 (§3 item 10, merged 2026-08-07); cut 5 implements and tests four selected M3 arms (local-DAG termination, abstract cycle witness, forced-verdict consumption, and ordinary unresolved-target refusal). M1–M2, M12, and M3's unselected clauses await implementation, and all four **implementation authorities** above are now built or frozen |
| 10 | **Belief policy** — what a belief *value* is, and the identity under which it is pinned | `2026-08-05-belief-policy-design.md` | the four terms kernel §4.2.1 cites as versioned policy members and never defines; `belief policy version` as the last bare rule reference in the G3 digest; the review-disposition record's F3 and its §5.5 stop rule, which place this ahead of the vertical slice | **Design banked 2026-08-05** (exact `PolicyBinding = (rule identity, implementation content identity)` as a required per-computation argument; `science.belief.v1` with `V = ℤ` and unit weight, so a value is a signed evidence balance and never odds; `Belief \| NoBelief(reason) \| Refused(reason)`; `inconclusive` excluded from the graph — kernel §4.2.1/§5/§5.1/lim. 5, formal model §3.3, D §8, substrate S6(h), 5b §4, and this ledger and the README amended in the banking commit); P2–P9 and part of P1 **landed 2026-08-09, conformance cut 2's slice** (`2026-08-09-conformance-cut-2.md` §4.1/§4.2); P1's resolver-negative arm awaits the rules store and 5b §6's deterministic resolution. Weighting by study design or precision is **blocked on ρO3**, not deferred by choice, and conformance cut 1 is **unchanged** — this discharges its prerequisite without widening it |
| 11 | **Pinned authority snapshot** — which external authorities are accepted, and how a snapshot of one is pinned, versioned, distributed and bumped | `2026-08-08-world-address-ruling.md` §4.2, limitation 5; the vocabulary-admission design (2026-08-07) is the nearest precedent and may be the right home rather than a new document | **every rendered label** (§4.1 there), the ambiguous-search-term refusal (W9, restated), and the authority-evidence arm of coreference normalization — CI can decide none of them without a pinned snapshot to decide against | **Owed, undesigned.** The ruling states the discipline — **pinned local snapshot, never a live network lookup**, so builds stay reproducible and an authority update is an explicit amendment — and does **not** design the artifact. Nothing banked waits on it *for identity*, since no basis is authority-label-derived; what waits is the **display and search** surface, which is why this is owed rather than blocking. **W14** asserts the renderer's invariance; nothing yet asserts the snapshot's own lifecycle |

> **Row 5 current-state correction (2026-08-28).** General intent
> qualification is implemented by world-index slice 6 and discharged by cut
> 11. Row 5 remains partial only for event-level L8, the L13 preimage resolver,
> and G4 with the successor-admission slice as its named owner. This dated note
> supersedes row 5's earlier intent-boundary remainder without rewriting its
> historical state.

> **Plan B gate update (2026-08-20).** Row 1's composition-root-adoption gate is
> satisfied and world-index slice 1 is merged on `science/main` through
> `567ebb4`, after its `nodes` prerequisite merged through `5a00bba`. Slice 2's
> epoch carrier is implemented and cut 7 is discharged
> (`../plans/2026-08-20-conformance-cut-7-results.md`), beginning with the
> cross-repository `atoms.read_chain` prerequisite, which is merged on the local
> `atoms` `main` only and has **not** been pushed. Slice 2 itself **merged into
> `science/main` on 2026-08-22 preserving history**.

> **Docket §4.1 ruled 2026-08-08** (`2026-08-08-world-address-ruling.md`).
> Basis-derived world addressing is **upheld** and **F9 closes**. Three
> consequences reach this ledger: the kernel is **eleven kinds**, not ten
> (twelve since 2026-08-10 — `holdings-observation`, the verified-holdings
> record design §2; thirteen since 2026-08-11 — `act-report`, the act-report
> design §2) — `coreference-attestation` joins on the `retraction`
> precedent; **structural
> merge is retired**, so nothing in artifact 1's world-index build performs a
> reference rewrite on coreference grounds; and **F10 is un-coupled from F9** and
> returns to the docket as its own item, since world §5's receipt apparatus turns
> on multi-corpus federation and the producers map being a belief input, neither
> of which any address scheme changes. Artifact 11 is what the ruling newly owes.

## 2. Sub-problem 5 — split and order (ruled 2026-08-03)

Sub-problem 5 is two clusters with a clean seam, taken in the reverse of the charter's
implied order:

- **5a — retraction and the correction lifecycle**, first: retraction (form already fixed:
  additive, attributed, kernel §5.1 digest member, structurally subtractive,
  eligibility-bearing), conflict-route retirement, and coverage-declaration
  accountability — the judgment cluster, all "who may change recorded judgment and how is
  the change visible."
- **5b — the versioned normative contract and its conformance oracles**, second, carrying
  instrument certification with it: equivalence-rule, falsifier, interpretation-rule, and
  scope-derivation-rule certification, plus code-lineage independence.

Rationale, recorded so it survives:

1. The retraction hole is live in banked designs — four separate limitations defer here.
2. Versioning a normative contract before adding a known-pending belief operation
   guarantees a major bump on arrival; the operation set completes before the document
   that describes it freezes.
3. "Prove this can fail" is what an oracle does, so instrument certification travels with
   the oracle work, not the lifecycle work.

Two standing constraints on 5a:

- **5a does not build tamper evidence.** A retraction record is as deletable as the
  record it retracts; the four §8.7 consequences gain a fifth (deleting a correction
  silently restores standing) rather than losing any. 5a's scope section states this
  non-goal explicitly, so the judgment cluster is not read as closing §8.7 by
  adjacency — the same "hygiene, not tamper evidence" line the kernel drew for the
  verification constructor.
- **One form, decided first.** Whether verification retraction, conflict-route
  retirement, and coverage narrowing are one lifecycle form — an authored, attributed
  act that subtracts standing without deleting a record, with an optional
  replacement — is 5a's opening decision. If they share the form, 5a defines it once
  and instantiates it three times, and coverage narrowing's visibility rule falls out
  of the shared form.

Two standing constraints on 5b:

- **The guarantee tables stay frozen under their current ids.** G1, G2a–G2c, G3–G8,
  S1–S8, W1–W13, R1–R23 are conformance oracles in embryo; 5a extends, never renumbers, so 5b inherits
  them unchanged and gives them a version and a conformance meaning.
- **`nodes`' STANDARD transfers as form, not force.** Its three-tier model exists to stop
  two language implementations drifting; science has one implementation. The reusable
  form is the versioned normative doc, frozen oracles, and explicit change policy;
  science's reason for the oracles is its own estimator doctrine — a check must be able
  to fail.

## 3. Order of work

1. **Sub-problem 5a** — retraction + correction lifecycle. **Banked 2026-08-03.**
2. **World-index packaging design** — where it lives, who writes it, staleness and
   consistency semantics, with §9 anchor carriage as a stated consumer (repro §9
   amendment). Everything in artifact 1's "waits on it" column leans here; it should not
   be designed last by default. 5a added two more consumers: the retraction map (its
   fourth derived map) and the temporal half of 5a's limitation 6, which explicitly
   defers a fresh retraction's reach to this design's staleness semantics.
   **Banked 2026-08-03.**
3. **Sub-problem 5b** — normative contract + oracles + instrument certification, after
   5a's operations exist. **Banked 2026-08-03.** Items 4–6 below proceed on
   their own clocks; the design track's next open item is the §9 log design.
4. **`nodes` contract deltas** land on their own clock; required before profile
   implementation, not before design.
5. **`atoms` A8 landed 2026-08-17; Plan B composition-root adoption is
   implemented.** Item 1 landed 2026-08-18
   (`feat/composition-root-adapter`, artifact 4's row for the record): cut 4's
   frozen selection is discharged on a certified volume and the 2026-08-18
   review closed its two engine-forced deviations as design amendments. Item 2
   landed 2026-08-19: cut 5 discharges the supersede, revise, retraction, and
   explicit-import families. The next mutation surface is the separately
   deferred consolidate/move/deletion cut with the world index.
6. **§9 log design** after the world-index packaging design settles the anchor.
   **Banked 2026-08-03** (`2026-08-03-tamper-evident-log-design.md`);
   **Science's half implemented 2026-08-23** as world-index slice 3
   (`2026-08-22-log-verification-design.md`), discharging frozen cut 8 with
   L3, L5, L9, L11 and L12 read in full, L1/L2/L4/L7/L8/L10/L13 in part, and
   L6 unread. The later slices closed L10's fork, replica, restore, store and
   holdings-read arms plus L7's holdings-shaped qualification and boundary
   arms. **General intent qualification closed 2026-08-28** with the
   intent-boundary slice and cut 11. **G4 closed 2026-08-29** with the
   successor-admission slice and conformance cut 12
   (`2026-08-29-successor-admission-design.md`). The preimage resolver behind
   L13's classification and event-level L8 remain, each with a named owner in
   artifact 5's row.
7. **Domain extension boundary** — where domain-specific material lives, and how
   `science` is organized so a later decomposition into packs is a move rather
   than a rewrite. **Banked 2026-08-04**
   (`2026-08-04-domain-extension-boundary-design.md`); D1–D10 await
   implementation. Its §12 named the **predicate vocabulary** as the next
   focused design; that became item 8.
8. **Formal model and typed claim calculus** — taken instead of a
   predicate-vocabulary design on its own, because the vocabulary question could
   not be answered without saying what a proposition *is*. **Banked 2026-08-05**
   (`2026-08-04-formal-model-and-claim-calculus-design.md`); cut 1 landed its
   selected M4–M11 and M13 arms, and cut 5 landed four selected M3 arms. M1–M2,
   M12, and M3's unselected clauses await implementation. Two consequences for
   the order of work: its **ρO** rows open
   three questions that belong to other designs — merge versus a retraction's
   immutable exact target (world §10; **ρO5, closed 2026-08-08** by `2026-08-08-world-address-ruling.md`,
   which retired merge rather than ruling the cascade), binding-check persistence and its
   correction path (kernel limitation 4), and a population vocabulary — and its
   **implementation authorities** (the claim grammar and kernel tag bytes, the
   `π_claim` projection under `science.identity.v1`, claim-schema compilation,
   and a cross-language parity fixture) have no home yet and are prerequisites
   for building M\*, not for banking it. **Sited 2026-08-06** at the start of
   item 10 (formal model §8, home column); *sited* is not *built*. Three of the
   four are now built — the base contract, `π_claim`/`tag_claim` under
   `science.identity.v1`, and claim-schema compilation — and the fourth, the
   parity fixture, is **frozen and consumed by both implementations**. A
   *second* fixture is now owed and is outside cut 1: `science.identity.v1`'s
   numeric and escape arms are tested twice and compared never (formal model §8).
9. **Belief policy** — taken next because the review-disposition record's §5.5
   stop rule puts it ahead of the vertical slice: the slice stops at the last
   fully designed seam, and anything computing belief had no seam to stop at.
   **Banked 2026-08-05** (`2026-08-05-belief-policy-design.md`); **P2–P9** and
   part of **P1** **landed 2026-08-09, conformance cut 2's slice**
   (`2026-08-09-conformance-cut-2.md` §4.1/§4.2), P1's resolver-negative arm
   left awaiting the rules store. The disposition record's F3 called belief aggregation
   undesigned; that was too broad — kernel §4.2.1 designs the aggregation
   *structure* in depth and substrate S6 already tests eight arms of it. What was
   missing was every scalar it is parameterized by, and the identity pinning
   them. Two consequences for the order of work: weighting by study design or
   precision is **blocked on ρO3** rather than deferred, so no weighted successor
   policy can be written until estimand typing has an owner; and non-empirical
   propositions return an absence reason that deliberately collapses *not
   attempted* with *no applicable route*, which is uncollapsed by whichever
   arrives first — kernel §11's second route, or a route-applicability predicate.
10. **The conformance cut 1 vertical slice** — the first code in this
    repository, and the end of the design-only phase. **Built and merged
    2026-08-07** (`f81d3a3`): 391 Python tests and 101 TypeScript, every one of
    the eleven selected rows carrying executable arms, and the §5.5 stop rule
    held — no belief computed, no persistence boundary crossed. Both gates the
    disposition record put in front of it were open when it started: cut 1 froze
    prospectively (§5, 2026-08-05) and the §5.5 stop rule's belief-policy
    prerequisite was discharged (item 9). Its acceptance criteria were **cut 1's
    eleven rows as frozen** — six fully selected, five part-selected — and it
    adds **no** guarantee table of its own; a slice that minted its own oracles
    would be grading its own homework, which is what freezing the cut in advance
    exists to prevent.

    **N2 is what the slice added to the corpus's practice.** Its trigger is the
    first executable suite, so it landed as a harness rather than a habit: 42
    arms declared as data — the row, what it asserts, a source mutation that
    makes it false, and the exact tests that must fail — applied to a copy of
    the package and audited, with `vacuous`, `uncollected` and `stale` reported
    as malformed contract content rather than as failing tests. Ten of the first
    forty arms were defective on the first audit. The disposition record's §5
    carries what that cost and what it found.

    Three things this item is **not**. It is not the world index, a corpus, a
    run, or a belief — §5.1 puts every persistence boundary outside it, so it
    waits on neither Plan B composition-root adoption nor the `nodes` contract deltas (items 4 and
    5), and it can be built and tested standing alone. It is not `KindSpec`
    compilation — **D4 is fully deferred**, and only the claim-schema half of
    `ProfileSpec` is in scope. And it is not a second implementation in
    TypeScript: formal model limitation 9 records **M10 as the only
    cross-implementation row**, so `ts/` carries the shared encoding and stops.

    One consequence for the order of work. Formal model §8 cited D §6's
    namespaced-facet-key parity fixture as the **existing** precedent for the
    claim parity fixture; measured against the trees it is neither existing nor
    namespaced (§8, corrected 2026-08-06). So M10's fixture is the corpus's
    **first** typed parity fixture and defines the shape rather than inheriting
    one — and D §6's own fixture remains outstanding, unblocked by this item and
    not in cut 1.

11. **The multi-corpus typing exercise** — the first consumer of cut 1's slice,
    and the first measurement in this redesign that is not taken over mm30 alone.
    **Designed 2026-08-07**
    (`2026-08-07-corpus-survey-and-vocabulary-admission-design.md`); **run and
    discharged 2026-08-07** (`2026-08-07-multi-corpus-typing-exercise.md`). It
    compiles a claim vocabulary for mm30, natural-systems and
    post-acute-infection, then runs `build_claim` over every proposition in all
    three.

    **Result: 307 of 307 structured mm30 propositions type; 0 of 45 and 0 of 5
    in the other two, because neither records a claim to type.** The two
    unfitted figures are the **25** records (8.1%) that refuse on argument sort
    once each operator is given per-slot sorts, and the **zero** qualifiers
    recorded in any of the eight corpora. Every grammar gap the disposition
    record found lives in records mm30 never structured, so closing all of them
    would type no additional structured record.

    **Why it is not an mm30 exercise.** A survey of **eight** proto-science
    corpora (6,860 records) measured that of 337 structured propositions across
    all of them, **307 are mm30's** — and the only two other corpora carrying
    subject/predicate/object use a single operator, `affects`, between them.
    mm30 is also the corpus every banked design was written while looking at, so
    it can confirm the calculus and cannot test it. The disposition record's
    limitation 3 already bounds its §2.3 figures to *"the mm30 authored set and
    for nothing else"*; what the survey adds is that the bound cannot be lifted
    by finding a second corpus, because no second corpus has a claim vocabulary
    to measure. One has to be authored. This item is that work — and the run
    **confirmed** the bound rather than lifting it: two of the three corpora
    contributed no typed claim, so the calculus is still exercised against mm30
    alone.

    **One claim this entry made is withdrawn** (typing exercise §4). It said the
    item would make *"the 6-of-16 expressiveness figure and the 6-of-27
    reproduction yield measured rather than hand-computed."* **No constructor
    can.** Those 27 records carry no subject, predicate or object — they state
    their claim in a `title` — and `build_claim` reads front matter, so it
    reaches **0 of 27**. The gap between 0 and 6 is the extraction step (kernel
    limitation 3), which is unautomated and untouched here. Both figures stay
    hand-computed and both stay non-quotable, pending the §2.4 re-homing
    adjudication and open question 4. The exercise measured a **different
    population** instead: the 307 structured records the hand-exercise never
    touched.

    Two results were **predicted in writing before the run**, on the same
    discipline that froze cut 1 prospectively. post-acute-infection's evidence is
    100% literature (95 of 95) with no eligibility field at all, so under **G1**
    its belief output is expected to be **empty** — and an empty result there is a
    **pass**, not a broken tool. natural-systems is at most 26% claim-bearing and
    largely process narrative, so the expected finding is a constraint on the base
    profile: it must not *require* a claim calculus.

    **Both held, and the first held for a different reason than predicted.**
    post-acute-infection's output is empty because the corpus records **no
    claims at all** — 0 of 45 propositions carry a subject, predicate or object
    — so the emptiness is upstream of G1 and **G1's eligibility gate was never
    reached**. No belief was computed (the stop rule below), so G1's behaviour on
    that corpus remains untested; the prediction is confirmed in outcome and its
    mechanism unexamined. natural-systems returned 0 of 5, confirming the base-
    profile constraint that §9.2 had already ruled — the run is that ruling's
    instance, not its evidence.

    Every candidate vocabulary field the exercise surfaces is run against
    domain-extension **2.6** — agreement and exercise over all **eight** surveyed
    corpora, not the three being typed, then the **reader** clause, which is what
    actually admits. That widening is not caution: 2.6's own first draft was
    checked against three corpora, passed, and inverted against eight (corpus
    survey §4.1). Satisfying the reader clause means **naming the check** that
    consumes the field and showing a value perturbation that flips its result,
    identity or refusal; that the field's removal breaks a test is not enough,
    since schema completeness, fixture coverage and a pinned contract digest all
    fail on the declaration alone (corpus survey §7). A field that fails agreement
    is out of the **base profile** and nothing more — it does not thereby enter a
    domain pack, since a domain contract costs ownership, succession and a schema,
    and a readerless field is not worth one. The exercise **must not mint relation
    kinds** for what it finds
    — **2.7** rules one navigation-only `see-also` edge, and a typing pass is
    exactly where a plausible relation gets invented for a single record. The
    disposition record's §5.5 stop rule is inherited unchanged: no belief
    computed, no persistence boundary crossed, and a typing that would need either
    is recorded as *blocked on composition-root adoption* rather than
    worked around.

    **The pass ran and admitted nothing** (typing exercise §5). `predicate` is
    not a base-profile question at all — operators are domain-issued without
    exception (§7.1). `proxy_directness` and `supports_scope` pass agreement and
    fail the reader clause, so they **wait**, named, as `strength` does.
    `identification_strength` is divergent and stays out of the base profile.
    The one genuine candidate, `mechanistic_narrative`, is a **value** rather
    than a field, and is **not admitted**: all 13 of its records across two
    corpora are unstructured, so the layer would admit **zero** claims. The 5 in
    mm30 are the disposition record's 0003, 0007, 0011, 0014 and 0015, every one
    already ruled **R**, three for being the wrong epistemic kind; the other 8
    were never adjudicated. Revisit when a corpus records a **structured**
    proposition carrying it. No relation kind was minted.

    The base profile requires claim **capability**, not claim **instances**
    (corpus survey §9.2): zero claims and zero activated operator contracts is
    conforming, with no profile variant and no activation flag. If a claim exists
    it must type; a proposition that will not type is typing work, not a licensed
    exception.

**One prerequisite is recorded here and is deliberately not an item** (typing
exercise §9). A second corpus that exercises the claim calculus **does not exist
and cannot be measured into existence** — the survey established that no other
surveyed corpus has a claim vocabulary to measure, and item 11 confirmed it with
counts. It has to be **authored**, which is corpus work rather than design or
implementation work, and until someone does it the disposition record's
limitation 3 stands: every claim-calculus figure is bound to the mm30 authored
set and to nothing else. Recorded so that the absence is a stated position and
not an oversight.

## 4. Invariants and gates to pin when their layer lands

- ~~**Concurrent-merge interleaving.**~~ **Lapsed 2026-08-08** (`2026-08-08-world-address-ruling.md` §5).
  This gate assumed an operation that rewrote other corpora's referrers. Merge is
  retired; `consolidate` performs no inbound rewrite and coreference closure rewrites
  nothing, so there is no cross-corpus referrer rewrite left to interleave. "One world
  does not add concurrency" (world lim. 5) now carries the claim alone, correctly —
  what it was too weak for no longer exists.
- **Measurement gates.** Exact maximum-independent-set aggregation and belief-digest
  closure recomputation get measured at mm30 scale before any optimization — the same
  rule substrate §8 applies to `nodes` indexes.
- **Cold arrivals.** A corpus arriving by copy/sync without engine metadata is a normal
  cold bootstrap (`atoms` §7); a corpus arriving *with* another host's metadata is a
  restored-backup classification case. Neither is corruption; both should appear in the
  world-index packaging design's staleness story.

## 5. Repository and package decomposition (ruled 2026-08-04)

The system lives under one GitHub organization, **`verifiably`**, alongside its two
substrates. The organization, not the repository name, is what makes short generic
names (`atoms`, `nodes`, `science`) defensible: they are layer names in one stack.

**Distribution namespaces are flat and the organization does not namespace them.**
The rulings, so they are not re-derived: npm uses the scope — `@verifiably/<name>`;
PyPI has no scopes, so the *distribution* name is `verifiably-<name>` while the
*import* name stays bare (`pip install verifiably-science`, `import science`). The
ugly name is confined to the install line.

**Three boundaries, deliberately not conflated:** what is cloned (repository), what
is installed (distribution), and what imports what (module). Module boundaries are
free and are drawn eagerly. Distribution boundaries are expensive and
hard to reverse — version matrices, release choreography, cross-package
migrations — so they are drawn reluctantly, on the `atoms`/`nodes` test: **split on
an observed second consumer or a genuinely different constraint regime, never on a
projected one.** This is the same discipline computation-reproducibility §9 applies
to the content-addressable store, one level up.

Two splits pass that test now:

- **The normative contract and its conformance oracles**, on doctrinal grounds
  rather than taste. 5b requires **code-lineage independence** for instrument
  certification: an oracle sharing code with the implementation it tests cannot
  independently falsify it, so a suite shipped inside the package it verifies makes
  independence an assertion with no mechanism. Separate distribution makes it
  enforceable and lets a third party run the suite against any implementation —
  the reason `nodes` has a STANDARD.
- **The agent surface** (skills, commands, coding-agent plugin manifests). The
  second consumer is already observed, not projected, and the cadence differs in
  kind: the surface churns while the kernel must not, because belief digests
  depend on kernel semantics. Coupling would also force every library consumer to
  carry agent plumbing it never calls.

Everything else stays in one `science` distribution: the epistemic kernel, world
addressing, computation and reproducibility, the correction lifecycle, world-index
packaging, and the mutation log are **one guarantee surface that co-evolves** — the
2026-08-03 banking commit alone amended five documents across four of them, and as
separate packages each such amendment becomes a multi-repo version dance. The
**CLI** is a consumer of the library and splitting it later is nearly free, so it
stays in-repo behind its own entry point.

Three things are **not** packages:

- **The meta-science arm** is research *about* the system. Under §0 it is
  reproduced as a project and corpus **managed by** the system, not code shipped
  beside it — which makes it the first serious dogfooding consumer.
- **The autonomous arm** is policy over the agent surface (what may run
  unattended, envelope and supervision): a consumer, not a peer.
- **`commons`** keeps its existing repository and its own audience (other
  installations); it consumes the world index.

**Record the seam now, materialize it later.** Empty repositories accumulate stale
scaffolding and imply structure nothing has validated, so the split happens when
the code exists to split, not at organization-creation time.

One dependency is open: the conformance package cannot be scoped until the
**first contract cut** (§1, artifact 7) names what the contract is a contract
*for*. The package boundary and the contract's scope are decided together.

> **Layer names ruled 2026-08-30**
> (`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §3).
> The stack is five layers, one repository and one distribution each:
> `atoms`, `nodes`, **`beliefs`** — this repository, renamed from `science`,
> import name `beliefs`, distribution `verifiably-beliefs` /
> `@verifiably/beliefs` — **`science`**, the daily surface (commands, skills,
> generated harness adapters, CLI and MCP, the derived work queue, publish),
> and **`autonomy`**, the envelope and orchestrator, split from `science` on
> the same code-lineage-independence ground that split the conformance
> package above. "Science" in every banked design names the whole stack.
> The contract and rule identities — `contract: science`,
> `science.identity.v1`, `science.belief.v1` and the `science.<kind>.v<n>`
> grammar — are the names of rules, not of a repository, and are unchanged;
> renaming them would be a contract succession under N1. `contracts/science/`
> stays with them. The agent surface named above is now `science`'s and the
> autonomous arm is `autonomy`'s; no ruling above is otherwise altered.
