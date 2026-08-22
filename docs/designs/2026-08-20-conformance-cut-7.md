# Conformance cut 7 — the epoch carrier

**Status:** Frozen 2026-08-20; second reader discharged 2026-08-20 (§6.1),
its seven findings and the carrier-authority prerequisite closed before
freeze. Discharged 2026-08-21;
[results](../plans/2026-08-20-conformance-cut-7-results.md). The implementation
was merged into `main` on 2026-08-22 preserving history, as the results
record's §7 constraint requires.

**Sources:** `2026-08-20-conformance-cut-6.md`; the epoch-carrier
specification `2026-08-20-world-index-slice-2-design.md` §11; and the frozen
X and W rows quoted below.

## 1. What this cut is

Cut 7 is the frozen acceptance boundary for world-index slice 2: the
`OperationLock`, the rules store, coherent capture, the build, epoch
publication and `current`, the four map derivations and their four receipts,
the read surface with its bound stamps and edge query, and the whole-epoch GC
act.

The selection rule is cut 5's rule, unchanged: a clause is selected only when
its source mutation and every named check run entirely inside §2. A row is
**full** only when cut 7 runs every arm in its frozen cell; one unrun arm
makes it **part**, even when a prior cut exercised that arm or an argument
says it should not count. A row with no cut-7 arm is **deferred**. Prior-cut
evidence remains evidence, but it is not silently relabelled as cut-7
selection.

Two structural inheritances:

- a behavior this slice adds that no frozen cell names is carried as a
  **labeled declaration outside the frozen selection** (§3.3), on the
  `semantic-hash-missing` precedent; and
- a behavior that two frozen rows both carry is **selected in exactly one row
  and cross-referenced from the other**, on cut 6's single-homing correction —
  a declaration unit has one home and is counted once.

## 2. The boundary

In scope:

- the `OperationLock` on `_RootState`, with its writer/capture holder kinds
  and capture generation;
- the rules store: identity recomputation, `install_rule_binding`,
  `remove_rule_binding`, and held-binding resolution;
- the build: declared coverage, preflight under the world lock, serial
  coherent capture under per-corpus capture holds, `read_chain` head capture,
  pure derivation, the pre-publication binding recheck, and one-transaction
  publication with the `current` pointer;
- the four map derivations over the ten governed stored kinds — with
  `retraction` the only one of the three receipt-specific enumerated record
  kinds that exists today — the producer snapshot and its existing semantic
  identity, and the four receipts on the one receipt contract;
- receipt validation — the rebuild evaluator and its
  `validated | refuted | unresolvable | malformed` outcomes — exercised
  directly and against fixture-authored receipt documents;
- the read surface: `open_epoch`, `current_epoch`, the closed
  `Resolved | NotPresent | Unknown` union, bound stamps, and the coreference
  edge query;
- the whole-epoch GC act and its sever report;
- the belief closure's existing supplied-snapshot-identity argument, only as
  far as the arms selected in §3 reach it — W8a's belief-invariance unit,
  X3's input-shape unit, and X12's belief-boundary unit;
- committed registration-entry evidence and the published epoch bytes on the
  certified tuple, decoded from the engine-owned chain as acceptance
  evidence; and
- a cut-7 acceptance runner over the certified engine tuple. Portable tests
  remain portable; a selected durable arm errors rather than skips when that
  tuple is unavailable or fails.

Out of scope:

- the governed stored kinds **`coreference-attestation`** and
  **`instrument-certification`** — both are prose kinds today; every arm
  requiring a real in-coverage record of either kind is deferred on the
  kind's own charter (normative-contract §7.6; world address ruling §5.2),
  and the build refuses an ungoverned record of an enumerated kind rather
  than deriving from it (`EnumeratedKindUngoverned`, specification §5.3,
  §10, §13; §3.3 here);
- **W15** — its row is not read; attestation write semantics arrive with the
  kind;
- **log verification**, L1–L13, the explicit anchor act, replay, and
  genesis-to-mirror agreement;
- the **snapshot/receipt import boundary**, the world-scale **audit**, the
  **diagnostic query**, and the snapshot reduction states
  (`checked`/`contradicted`/`unchecked`) — W8a's arms through those surfaces
  defer on them;
- **persistence-cut simulation** — no Science-side power-fail harness exists;
  X2's cut-at-every-stage arm defers on one (§7 limitation 2);
- the **fork constructor**, cross-process locking, the epoch-enumeration
  sweep, and artifact 11's authority snapshot; and
- `atoms.read_chain`'s own behavior — its tests live in that repository; the
  cut consumes the specification §2 contract and gates on the landed command.

Raw filesystem writes may construct negative fixtures — including
fixture-authored receipt documents and sabotaged epoch members; they are not
build or registry operations.

## 3. The selection, against the frozen rows

The code blocks preserve each source row verbatim. **Selected** bullets are
the complete arm inventory that the N2 declarations must enumerate; every
**deferred** bullet names its unblocker.

### 3.1 The epoch rows

#### X1 — full

```markdown
| X1 | A published epoch is immutable, and members are never deleted individually | no API edits or deletes an **individual** epoch member — whole-epoch GC (§9, X11) is the sole deletion operation; raw-edit a member → the epoch's packaging identity no longer matches at audit, reported |
```

- **Selected:** assert no public API edits or deletes an individual epoch
  member — whole-epoch GC is the sole deletion operation, and a
  member-targeted mutation is unspellable through the surface.
- **Selected:** raw-edit a published epoch member and assert `open_epoch`'s
  packaging-identity recomputation detects it and refuses `EpochMalformed`.
  **Reading recorded:** the frozen cell's "at audit, reported" is read as
  the open-time recomputation — the specification's only audit surface for a
  publication (§8.1); the report is the refusal. No findings sweep exists
  (specification §10), and this cut claims none.

#### X2 — part

```markdown
| X2 | **[Plan B]** Publication is crash-atomic and `current` is durable: it never selects a partial epoch and survives a persistence cut | kill the writer at every stage of publication **and** cut persistence (power-fail simulation) at every stage; assert `current` resolves the **prior epoch when the cut precedes the commit decision's durability, and the new, complete epoch after it** — `atoms` recovery rolls a committed transaction forward, never back — and is never missing and never names incomplete content; pre-commit residue is detected and reported. **Interim negative:** the best-effort writer can leave a partial epoch, a missing `current`, or a `current` naming incomplete content after a persistence cut — asserted and reported, per limitation 2 |
```

- **Selected:** interrupt publication by killing the writer at every
  observable stage boundary of the one-transaction write — stated narrowing:
  intra-transaction stages belong to the engine's certified recovery and are
  not Science-observable, so the frozen "every stage" resolves to the
  Science-visible boundaries and is not silently read down later; on the
  next entry
  through the recovery barrier, assert `current` names either the prior
  epoch or the new, complete epoch — never nothing, never incomplete
  content — and that a rolled-forward committed transaction yields the
  complete new epoch.
- **Selected:** on the certified tuple, assert the publication transaction
  commits a registration entry naming every epoch member and `current`
  (create or replace), decoded from the engine-owned chain.
- **Deferred:** the persistence-cut ("power-fail simulation") arm at every
  stage waits on a Science-side persistence-cut harness or an extension of
  the `atoms` A8 certification to this consumer path; committed
  registration-entry evidence plus the engine's own certified crash-atomicity
  is what is claimed here, and no argument substitutes for the unrun arm.
- **Lapsed:** the frozen interim negative describes the best-effort writer,
  which was never built (specification §6.3; slice-1 ruling §1.1). Recorded
  as lapsed, not run.

#### X3 — full

```markdown
| X3 | Belief never reads `current` | attempt a belief computation selecting "current" rather than an explicit snapshot identity → refused; assert every epoch remains readable by packaging identity while it exists |
```

- **Selected:** assert a belief computation selecting "current" is
  unspellable — the closure's producer-snapshot input is a required explicit
  identity argument with no default and no current-accepting parameter, and
  no API composes `current_epoch` into a belief input.
- **Selected:** assert every retained epoch — current and non-current —
  remains readable by its packaging identity while it exists.

#### X5 — part

```markdown
| X5 | Duplicate `corpus_id` is refused at admission and detected at build | admit a known id → refused (replica declaration excepted, minting no admission); raw-place two corpora with one id, build → refused, reported |
```

- **Selected:** raw-place two configured corpora carrying one `corpus_id` and
  run a build whose coverage names it; assert `CoverageUnresolvable` refusal
  at preflight, with the standing `duplicate-carrier` finding still emitted
  by presence reduction — the refusal is the frozen cell's "reported", and
  cut 6's labeled `duplicate-carrier` precursor is now a build refusal as
  that cut recorded prospectively.
- **Prior-cut evidence:** the admission arm was discharged by cut 6's X5
  selection and is not re-selected; this cut runs only the build arm, so the
  row stays **part** here while the two cuts jointly cover both arms.

#### X7 — full

```markdown
| X7 | Admission is the cross-root commit point | build a coverage naming a manifest-bearing but unadmitted corpus → refused; admit it → same build proceeds |
```

- **Selected:** run a build whose coverage names a manifest-bearing but
  unadmitted corpus; assert `CoverageUnknown` refusal.
- **Selected:** admit that corpus and assert the same build input proceeds
  through preflight.

#### X8 — full

```markdown
| X8 | Every epoch answer is bound-stamped | assert answers carry packaging identity + coverage declaration through every read API; an answer without them is unconstructible |
```

- **Selected:** assert every answer from every read API — address
  resolution in all three result states, the edge query, and epoch opening —
  carries the epoch packaging identity and complete coverage declaration.
- **Selected:** assert a stampless answer is unconstructible — the closed
  result types have no stampless constructor and no read path returns a bare
  value.

#### X9 — full

```markdown
| X9 | An epoch's maps **and its anchored head members** share one coherent state view per corpus, held by the corpus write lock (head/state coherence added 2026-08-03, tamper-evident log design §5) | attempt an API write to a covered corpus while the build holds its lock → **refused**, never queued, never interleaved; start a capture on a corpus whose lock an active writer holds → build **refuses**, never waits; raw-mutate a covered corpus during capture → post-check discards, build retries/refuses; assert no published epoch's receipts name two states of one corpus, and that the producer, retraction, certification-enumeration, and coreference-reduction receipts (the third added at 5b's banking, the fourth 2026-08-08 with the coreference map — `2026-08-08-world-address-ruling.md` §5.5) name **identical** states per corpus; capture a corpus's chain head outside the lock hold that captured its state → **unconstructible** through the build, and assert each epoch head member and the receipts' corpus-state identity describe **one** view. **Negative (ABA, limitation 7):** raw-move a corpus `A → B → A` within one capture → pre/post identities match and nothing detects the mixed scan — the raw-write bound, which is why the lock, not the check, carries the guarantee |
```

- **Selected:** attempt an API write to a covered corpus while the build
  holds its capture; assert `BuildHold` refusal — never queued, never
  interleaved.
- **Selected:** start a capture on a corpus whose lock an active writer
  holds; assert `BuildContended` refusal — the build never waits.
- **Selected:** raw-mutate a covered corpus during its capture; assert the
  post-enumeration recompute discards the capture with `CaptureDrift` and
  nothing publishes.
- **Selected:** assert no published epoch's receipts name two states of one
  corpus, and that the producer, retraction, certification-enumeration, and
  coreference-reduction receipts name identical per-corpus states within one
  epoch.
- **Selected:** assert head/state coherence — each epoch head member and the
  receipts' corpus-state identity describe one view, and a chain head
  captured outside the lock hold that captured its state is unconstructible
  through the build: the only head-capture site is inside the hold, and the
  sabotage relocating it outside the hold must fail the declared checks —
  which must interpose a corpus write between the state capture and the
  relocated head capture, since without an interleaved write the sabotage
  passes vacuously; N2's declaration is checked against that vacuousness at
  declaration time.
- **Selected:** the ABA negative as an undetectability assertion, on cut 5's
  S3 and cut 6's X4 precedent: raw-move a covered corpus `A → B → A` within
  one capture; assert the pre/post identities match, the build publishes,
  and nothing detects the mixed scan — packaging limitation 7 pinned as
  built. It claims no detection.

#### X10 — full

```markdown
| X10 | Receipts — producer, retraction-map, certification-enumeration (amended 2026-08-03 at 5b's banking) **and coreference-reduction** (amended 2026-08-08, `2026-08-08-world-address-ruling.md` §5.5) — resolve rule bindings against the held store only | for each receipt kind: un-hold its rule implementation → `unresolvable`, not `refuted`; install a newer rule beside it → still validates against the implementation it names, never revalidates against the newcomer (normative-contract §6); bare version string → `malformed` (world §5's contract, packaged). **For the coreference receipt, assert the extra consequence on the two outcomes this row owns — `unresolvable` and `malformed`:** un-hold its rule → `unresolvable`; raw-write a receipt naming a **bare version string** or a corpus rather than a corpus-state identity → `malformed`, decided with no corpus present and no rule held; and in **each** case assert the covered edges read **`indeterminate`** and a query expanding over one **refuses**. The third outcome, **`refuted`**, is reached only by rebuilding the reduction against the corpora the receipt names, so **X12 owns it** and asserts the same consequence there — this row does not restate that arm. The malformed arm is the one that would otherwise have no consequence anywhere — a permanently uncheckable receipt is the strongest reason to refuse, and reading it as `inactive` would let a forged record silently suppress an edge (that ruling's §5.5) |
```

- **Selected (parameterized over all four receipt kinds):** remove the
  binding a validated receipt names; assert validation now returns
  `unresolvable`, never `refuted` — nothing in any corpus changed.
- **Selected:** install a second conforming implementation beside the named
  one; assert the receipt still validates against the exact pair it names
  and is never revalidated against the newcomer.
- **Selected:** raw-write a receipt naming a bare version string; assert
  validation returns `malformed`, decided with no corpus present and no rule
  held.
- **Selected (the coreference consequence, on this row's two outcomes):**
  for the `unresolvable` case (binding removed) and the `malformed` case
  (bare version string, or a state member naming a corpus rather than a
  corpus-state identity), assert every covered edge reads `indeterminate`
  and a query expansion over one refuses `EdgeIndeterminate` — never
  `inactive`. `refuted` is X12's arm, not restated here.

#### X11 — full

```markdown
| X11 | GC's two hard rules hold | GC act naming `current`'s epoch → refused; delete another epoch → act's report names the snapshots/receipts severed; before deletion the epoch resolves by identity |
```

- **Selected:** run the GC act naming `current`'s epoch; assert
  `EpochCurrent` refusal with nothing deleted.
- **Selected:** delete a non-current epoch; assert the act's report names the
  producer-snapshot identity and four receipt identities the epoch carried
  with their severed flags, and that before deletion the epoch resolved by
  packaging identity.

#### X12 — part

```markdown
| X12 | The retraction map, the certification inventory **and the coreference reduction** are complete over the epoch's coverage at its recorded states, and their receipts can refute an incomplete one (amended 2026-08-03 at 5b's banking; **coreference added 2026-08-08**, `2026-08-08-world-address-ruling.md` §5.5) | standing retraction in-coverage at build → in the map; out-of-coverage → absent, and the coverage declaration states the bound (5a C3's shape, at the artifact layer); an in-coverage `instrument-certification` at build → in the address map and the inventory projection. an in-coverage `coreference-attestation` at build → inside the pair's published balance; out-of-coverage → outside it, with the coverage declaration stating the bound. **The receipt is the completeness check, not the packaging hash:** for each receipted projection — retraction map, certification inventory, coreference reduction — omit an in-coverage entry and repackage into an internally consistent epoch → receipt validation, rebuilding with the named binding against corpora at the named states, **refutes** it; a corpus no longer standing at a named state → `unresolvable`, never a pass. **For coreference, assert the reduction is checked and not merely the membership:** leave every attestation in place and publish a **wrong balance** for a pair → the rebuild **refutes**. Then assert the belief boundary — a **refuted** coreference receipt moves **no** `belief_input_digest`, unlike the producer snapshot, and its consequence is that the covered edges read **`indeterminate`** |
```

- **Selected:** a standing retraction in-coverage at build is in the
  retraction-discovery map; an out-of-coverage retraction is absent, and the
  coverage declaration states the bound.
- **Selected:** omit an in-coverage retraction and repackage into an
  internally consistent epoch; assert receipt validation — rebuilding with
  the named binding against corpora at the named states — refutes it. This
  unit also discharges W8a's identical retraction-omission arm
  (cross-referenced there, counted once).
- **Selected:** move a covered corpus off a named state; assert validation
  returns `unresolvable`, never a pass. This unit also discharges W8a's
  "checkable only against a state that still exists" resolvability clause
  (its snapshot-reduction half stays deferred there).
- **Selected (empty-enumeration instance, recorded as such):** publish a
  nonzero coreference balance for a pair over attestation-free coverage;
  assert the rebuild refutes it — the reduction is checked, not merely the
  membership. The populated instance ("leave every attestation in place")
  defers with the attestation kind.
- **Selected:** assert a refuted coreference receipt moves no
  `belief_input_digest` and that its covered edges read `indeterminate`,
  with expansion refusing.
- **Deferred:** the in-coverage `instrument-certification` membership arm
  (address map and inventory projection) and its omission-refutes arm wait
  on the governed kind (normative-contract §7.6).
- **Deferred:** the in-coverage `coreference-attestation` membership arms
  (inside/outside the published balance), the coreference omission-refutes
  instance of the "each receipted projection" clause, and the populated
  wrong-balance instance wait on the governed kind (world address ruling
  §5.2).

### 3.2 W8a — the derived-maps row

The row is quoted whole; its arms fall to three surfaces — the derivations
and evaluator built here, the snapshot/receipt import-audit apparatus that is
not, and the two absent governed kinds.

```markdown
| **W8a** | All **four** index maps are derived, never authoritative — and the producers map, retraction enumeration, coreference reduction, and certification inventory carry their own scope (amended 2026-08-03, packaging §5 / 5a §4 / 5b §7.6; **amended 2026-08-08**, world address ruling §4.3 and §5.5 — the *membership* changed and the count did not: the alias-map arm is **deleted without replacement**, since a map derived from nothing has nothing to reconstruct, and a **coreference** arm replaces it) | Delete the world index and rebuild it from the corpora alone; assert the **address**, **producers**, **retraction** and **coreference** maps all reconstruct identically. **Added 2026-08-08 — the coreference reduction carries its own completeness evidence, on the retraction map's precedent:** omit an in-coverage `coreference-attestation` and repackage into an internally consistent epoch; assert validation of the **coreference-map derivation receipt** — rebuilding with its fixture-bound rule against corpora at its named states — **refutes** it. **And assert the coverage arm, which is this map's whole hazard:** build over a **narrower** corpus set and assert a pair's published balance may differ, that the **coverage declaration** differs, and — unlike the producers map — that `belief_input_digest` is **unchanged**, since coreference is outside belief (that ruling's §5.3). Then edit each map in the index only; assert the rebuild discards every edit. **Amended 2026-08-03 — the retraction map carries its own completeness evidence:** omit an in-coverage retraction and repackage into an internally consistent epoch; assert validation of the **retraction-map derivation receipt** — rebuilding with its fixture-bound rule against corpora at its named states — **refutes** it (packaging §7, X12). **Amended again at 5b's banking — so does the certification inventory:** omit an in-coverage `instrument-certification` from the address map and repackage; assert validation of the **certification-enumeration receipt** — same contract, same rebuild — **refutes** it (normative-contract §7.6, packaging §7, X12). **Coverage is part of the answer, not of the plumbing:** build the index over a **narrower** corpus set with every included corpus byte-identical, and assert (a) the producers map is smaller, (b) the **coverage declaration** differs, and (c) kernel §5.1's `belief_input_digest` **differs** — pinning that an enumeration is bounded by what it consulted and that two coverages are two belief inputs. **Negative — the receipt is beside the identity, not in it:** move an entity between two covered corpora so **both** corpus-state identities change while the producers map and the covered-corpus set do not; assert the **semantic** snapshot identity and `belief_input_digest` are **unchanged**, and that re-deriving mints a **new receipt** at a different receipt identity while the earlier receipt is left intact — W5 holds through the completeness mechanism as well as through the address map. **And the receipt is still required:** import a snapshot with no receipt and assert it is refused as unrecomputable. **Well-formedness before availability:** for a snapshot declaring coverage `{A, B}`, hand import a receipt naming **only `A`** with `A` present and standing at its recorded state; assert it is **refused as malformed** — and specifically that it is **not** evaluated against availability, **not** `unresolvable`, and above all **not `validated`**, which is what a rebuild from `A` alone would have returned for a map omitting every producer in `B`. Repeat with an **extra** corpus outside coverage, a **duplicate** `corpus_id`, and a receipt whose snapshot identity names a different snapshot; assert each is refused. **The values must be identities, not merely present:** hand import a receipt whose state value names a **corpus** rather than an exact corpus-state identity, and one whose rule reference is a **bare version string** with no fixture binding; assert **`malformed`** for both — specifically **not `unresolvable`**, since no corpus mount and no rule installation could ever make either checkable, and an `unresolvable` verdict would have told their author to go find the missing input. Then assert the contrast that fixes the boundary between the two predicates: a **syntactically valid** state identity and a **syntactically valid** rule identity that are simply **not held here** are `unresolvable`, not malformed — *is it an identity* belongs to `well_formed`, *is it held* belongs to `resolvable`. **Negative:** assert every malformedness above is decided **with no corpus present at all** and with **no rule held**, pinning that malformedness is a property of the record while unresolvability is a property of the checkout. **Malformed is an evaluator outcome, not only an import refusal:** **raw-write** a malformed receipt past the import boundary (§11.11), then run an **audit**; assert the evaluator returns **`malformed`** — not `unresolvable`, not `refuted`, and not `validated` — that the audit emits a **malformed finding naming that pair**, and that the same result comes back from the **diagnostic query**, which writes nothing. Assert the snapshot reduction **excludes** it: with that receipt alone, the snapshot is **`unchecked`** and **not `contradicted`**, so a forged record cannot condemn a snapshot; place a **validating** receipt beside it and assert the snapshot is **`checked`**, with the malformed finding **still emitted**. **Negative — the two roads to `unchecked` are distinguishable:** assert an audit over an all-malformed snapshot and one over a snapshot whose corpora are merely absent both report `unchecked`, but that only the first carries malformed findings — pinning that a permanent record defect is not filed as a transient checkout condition. **The rule identity is in the receipt, and its three transitions are distinct:** validate a receipt under an audit, then **(i) install a newer enumeration rule beside the old one** — assert the old receipt **still validates**, since its named implementation is still held and a content-addressed implementation never changes in place; **(ii) stop holding the old rule** — assert the receipt is now **unresolvable**, and **never refuted**, since nothing in any corpus changed; **(iii) re-derive under the new rule** — assert a **new receipt** at a new receipt identity, the old receipt untouched, and a **new snapshot only if the map or coverage differ**, with the semantic identity and `belief_input_digest` **unchanged** when they do not. Assert a rule identity naming an implementation that **fails its fixtures** is not that rule — a `resolvable` failure, since the reference is well formed and the world simply holds no such rule — while a bare version string is **`malformed`**, per the case above. **Two installations agree, with the precondition stated:** assert two installations in the **same availability context** — both resolving the same rule and the same per-corpus states — reach the **same** outcome for one receipt; assert one lacking the rule returns **`unresolvable`**, which is agreement about what it can establish rather than a contradicting verdict. **Negative — unavailable is not malformed:** import a snapshot whose receipt names exact states whose **corpora are absent from this checkout**; assert the import **proceeds**, that an **import finding** records the unchecked derivation, and that **no validation state is written onto either record**. Assert the malformedness refusals above are still refusals under exactly that condition, pinning that "cannot be checked here" and "cannot be checked" are different findings. **The availability transition, which is what must not move belief:** compute belief **naming that snapshot**, then **mount the corpora** and assert the digest and admission are **unchanged** — mounting is not an argument. Assert a computation naming a **different** snapshot **does** produce a different digest, since the identity is itself a belief input; assert the identity is a **required argument** with no default, so a computation naming none has no digest to produce, and that **no implicit "latest" and no stored selector** exists to be reached. Assert an **audit writes only a new snapshot and a new receipt** and by itself changes **no** belief. **A receipt is checkable only against a state that still exists:** validate a receipt under an **audit**, then change a covered corpus so it stands at a **new** state; audit again and assert the receipt is now **unresolvable** rather than refuted, and the snapshot **`unchecked`**. **The quantifier is per corpus:** build a receipt over **two** corpora, move **one** of them to a new state and leave the other untouched; assert the receipt is **unresolvable**, that the still-standing corpus does **not** satisfy the moved one's entry, and that restoring the moved corpus to its recorded state makes the receipt resolvable again. Assert the same for the rule conjunct, so all three ways of failing `resolvable` are covered — asserting specifically that **no stored validation survives**, since the state is an audit-time diagnostic that is evaluated and never written. Assert that a computation naming that **same snapshot identity** yields the **same digest and admission** across the whole transition, and that re-deriving mints a snapshot and receipt that are checkable again. **The evaluating operation is named:** assert **mounting a corpus performs no validation** — no finding, no record mutated, no validation result written — and that the **audit** is what evaluates. Assert import, audit and the diagnostic query all call **one read-only evaluator**, that only the first two are effectful (refusing a write; publishing a correction), and that the diagnostic query **writes nothing and feeds no belief computation**. **Negative:** assert no fourth path evaluates a receipt, and that the three callers **evaluating in the same availability context** return the same result, since they share the function rather than reimplementing it. **Then assert the limit:** the evaluator is **not pure** — assert the *same* `(snapshot, receipt)` returns `unresolvable` before a needed corpus or rule is available and `validated`/`refuted` after, so agreement is guaranteed **within** an availability context and across nothing else. **Per-pair validation and its quantifiers:** first assert the import boundary — hand it a receipt that is **resolvable and refuted right now** and assert it is **refused before any write**, with no file afterwards. Then build the state a refusal cannot produce, by the route §5 names: import a second receipt **while its corpus is absent**, so it enters unresolvable with a finding, then **mount that corpus and run an audit**, which is what evaluates it to **refuted**. **Then the other half of that route:** import a third receipt whose corpora are all present but whose **named rule is not held here**; assert it enters **unresolvable** with a finding rather than being refused, then **install that rule and audit**, and assert it now evaluates — to **refuted** where the rebuild disagrees, **validated** where it agrees. Assert the rule's arrival — which does of course change what is held, since holding the implementation is the point — **mutates neither the snapshot nor the receipt**, writes **no validation result** anywhere, and changes **no** belief; only the subsequent audit may publish a correction. Exactly as the corpus mount does not. With a validating receipt also present, assert the snapshot is **`checked`** and that the refuted outcome attaches to the **pair**, not to the snapshot. Now make the validating receipt unresolvable while the refuting one still resolves, and assert **`contradicted`**; then make **none** resolve and assert **`unchecked`**, **not** contradicted — the vacuous case, which an "every resolvable receipt is refuted" rule would have gotten backwards. Assert the three states are **total and mutually exclusive over the well-formed receipts**, and that adding a malformed receipt to any of the three leaves the state unchanged while adding one finding. **Negative — the boundary is a moment, not an invariant:** assert no rule requires every stored receipt to be non-refuting, that raw-writing a refuting receipt is likewise not refused, and that both are caught only when something evaluates them — otherwise `contradicted` would be a state with no reachable population. As the limit, assert a contradicted snapshot is **not retired** and can still be named by a computation (limitation 11). **Negative — one snapshot, several receipts:** re-derive after a change that leaves the producers map and coverage untouched; assert a **second receipt** at a **different receipt identity** naming the **same** snapshot identity, that neither receipt is overwritten, and that no belief digest moves — pinning that the receipt is its own record and not a mutable field of the snapshot. **Negative — absent is not empty:** hold out a corpus **inside** coverage that holds a producing run, and assert that producer reports **`not-present`** and the dataset does **not** read as undiverged; contrast with a producer outside coverage, which is unsuspected and is sub-problem 4 §11.15's stated limit rather than a detection |
```

- **Selected (rebuild identity):** delete the world index (the retained
  epochs) and rebuild from the corpora alone; assert the address, producers,
  retraction, and coreference maps all reconstruct identically. The rebuild
  fixture carries populated address, producers, and retraction maps — only
  the coreference map is kind-empty, and it reconstructs identically empty,
  recorded as the empty-enumeration instance.
- **Selected (derived, never authoritative):** edit each map in a published
  epoch only; assert the rebuild discards every edit.
- **Selected (producers coverage arm):** build over a narrower corpus set
  with every included corpus byte-identical; assert the producers map is
  smaller, the coverage declaration differs, and `belief_input_digest`
  differs — an enumeration is bounded by what it consulted.
- **Selected (the receipt is beside the identity):** move an entity between
  two covered corpora by fixture arrangement so both corpus-state identities
  change while the producers map and covered-corpus set do not; assert the
  semantic snapshot identity and `belief_input_digest` are unchanged and
  re-deriving mints a new receipt at a different receipt identity naming the
  same snapshot identity, the earlier receipt intact, no belief digest
  moved. This is the frozen W5 producers-map arm arriving through W8a's
  completeness mechanism; §3.4 records the candidate's disposition.
- **Selected (rule succession):** re-derive under a newly installed rule;
  assert a new receipt at a new receipt identity, the old receipt untouched,
  and a new snapshot only if the map or coverage differ, the semantic
  identity and `belief_input_digest` unchanged when they do not. The (i)
  install-beside and (ii) un-hold transitions are X10's selected units,
  cross-referenced, counted once.
- **Selected (malformed against unresolvable, at the evaluator):**
  fixture-author receipts whose state member names a corpus rather than a
  corpus-state identity, whose coverage omits a declared corpus, carries an
  extra one, duplicates a `corpus_id`, or whose subject names a different
  snapshot; assert each evaluates `malformed`, decided with no corpus
  present and no rule held — and assert the contrast: a syntactically valid
  state identity or rule identity that is simply not held here is
  `unresolvable`, never `malformed`. The bare-version-string instance is
  X10's unit, cross-referenced.
- **Selected (conformance and agreement):** assert a binding whose
  implementation fails its fixtures is not held — validation `unresolvable`,
  a resolvable failure, never `malformed`; assert two installations — two
  world roots over the same corpora, each resolving the binding and the
  states from its own store — in the same availability context return the
  same outcome for one receipt, an installation lacking the rule returns
  `unresolvable`, and the same
  `(snapshot, receipt)` pair moves `unresolvable → validated` when the
  needed corpus state or binding becomes available — agreement within an
  availability context and across nothing else.
- **Selected (the quantifier is per corpus and per conjunct):** build a
  receipt over two corpora; move one off its named state and assert
  `unresolvable`, the still-standing corpus not satisfying the moved one's
  entry; restore it and assert resolvable again; assert the same for the
  rule conjunct; assert no stored validation survives any transition — the
  outcome is evaluated, never written.
- **Selected (belief invariance, narrow):** compute a belief closure naming
  a snapshot identity; change corpus availability and assert the digest and
  admission are unchanged — mounting is not an argument; assert a
  computation naming a different snapshot produces a different digest, and
  that the identity is a required argument with no default. The
  no-implicit-latest half is X3's unit, cross-referenced.
- **Selected (absent is not empty, narrow):** hold out a corpus inside
  coverage that holds a producing run; assert that run's address resolves
  `NotPresent`, never `Unknown` and never `Resolved` — and assert the
  frozen contrast: a producer outside coverage resolves `Unknown`, the
  unsuspected case, which is sub-problem 4 §11.15's stated limit rather
  than a detection. The divergence-reading half ("the dataset does not read
  as undiverged") defers with the epoch-consuming divergence report.
- **Deferred:** the coreference omission-refutes arm and the coreference
  coverage arm (a pair's balance differing under narrower coverage with
  `belief_input_digest` unchanged) wait on the `coreference-attestation`
  kind.
- **Deferred:** the certification omission-refutes arm waits on the
  `instrument-certification` kind.
- **Deferred:** every arm through the snapshot/receipt **import boundary**
  ("import a snapshot with no receipt → refused", the hand-import refusals,
  import-with-absent-corpora proceeding with a finding, the
  resolvable-and-refuted import refusal), the **audit** and **diagnostic
  query** callers, the one-evaluator three-caller architecture, and the
  snapshot reduction states (`checked`/`contradicted`/`unchecked`, their
  totality, and the contradicted-not-retired limit) wait on the import and
  audit surfaces; the evaluator those callers share is what this cut
  exercises directly.

### 3.3 Labeled declarations outside the frozen selection

Ten declarations, on cut 4's `semantic-hash-missing` precedent, each
sabotaged like a selected arm and named by the epoch-carrier specification:

- **Labeled (lock, capture generation):** a writer that entered the wait
  queue and wakes after a capture began and ended must refuse `BuildHold` by
  the capture generation, never proceed as if no capture intervened
  (specification §5.1).
- **Labeled (rules, install):** byte-identical reinstallation of a held
  binding is idempotent success; an existing content-addressed path with
  different bytes refuses `RuleCollision`; an implementation failing the
  normative fixtures refuses `RuleNonconformant` before any transaction
  (specification §4.2).
- **Labeled (rules, removal):** `remove_rule_binding` on an unknown pair
  refuses `RuleBindingUnknown`; a completed removal returns every receipt in
  this world that names the removed pair and loses this store's resolution;
  removing the final implementation also removes `rule.yaml` and the fixture
  members; nothing is removed by installing a successor (specification
  §4.3).
- **Labeled (rules, self-verification):** raw-swap `rule.yaml` or a fixture
  member's bytes; assert the held-check's identity recomputation fails and
  the binding is not held (specification §4.1).
- **Labeled (build, publication recheck):** remove a named binding between
  capture and publication; assert `RuleNotHeld` at the pre-publication
  recheck under the world lock and nothing published (specification §5.4).
- **Labeled (publication, exact rebuild):** rebuild an identical epoch;
  assert only the pointer swaps; with the pointer already naming it, assert
  success; a same-name collision with different or malformed content refuses
  `EpochMalformed`, no member overwritten (specification §6.3).
- **Labeled (read, resolution refusals):** a duplicate carrier, a malformed
  present manifest, and a present carrier that fails to produce the mapped
  `uid` each refuse `ResolutionRefused` — never `NotPresent`, never
  `Unknown` (specification §8.3).
- **Labeled (read, edge-query span):** an epoch whose coverage lacks a live
  `corpus_id` yields `indeterminate` before any balance is considered, and
  `EdgeIndeterminate` names every unestablished input — the sorted missing
  live ids and/or the exact non-`validated` receipt outcome; a generic
  message fails the declared check (specification §8.4).
- **Labeled (capture, ungoverned enumerated kind):** a record whose kind is
  an enumerated map kind but is present only as ungoverned prose refuses the
  build with `EnumeratedKindUngoverned` during capture — nothing derives
  from unvalidated content and nothing is silently dropped (specification
  §5.3, §10, §13).
- **Labeled (durable evidence, world transactions):** on the certified
  tuple, assert the rule-install, rule-removal, and GC-deletion transactions
  each commit a registration entry naming their world-root paths;
  publication's entry is X2's selected unit.

### 3.4 A candidate not separately declared

The specification §11 names W5's producers-map arm as a candidate labeled
declaration. It is not separately declared: §3.2's "receipt is beside the
identity" selection runs that exact behavior inside W8a's own frozen cell,
and a second home would double-count one declaration unit. W5's row is not
read by cut 7 — its move-operation arms have no API to run against — so W5
takes no row state here; the behavior is homed in W8a.

## 4. Accounting

Cut 7 reads 11 frozen rows: **7 full + 4 part + 0 deferred = 11**.

| state | rows | n |
|---|---|---:|
| full | X1, X3, X7, X8, X9, X10, X11 | 7 |
| part | X2, X5, X12, W8a | 4 |
| deferred | — | 0 |

The 10 labeled declarations in §3.3 sit outside this row accounting and
discharge no frozen row.

This is row accounting, not a denominator of prose arms. Each **Selected**
and **Labeled** bullet in §3 is one declaration unit for N2: **38 selected +
10 labeled = 48** declaration units (X rows 2+2+2+1+2+2+6+4+2+5 = 28; W8a
10). Cross-referenced clauses are counted once, at their home. No row
outside these 11 is read by cut 7, and no prior-cut arm is counted as new
selection.

## 5. N2 and acceptance obligations

The implementation plan's N2 task owns cut 7's declarations. It must declare
every §3 **Selected** and **Labeled** bullet, and only those 48 units, as
data with:

- its frozen row id (or `labeled:` name and specification citation) and
  assertion;
- the exact source mutation, against real module text;
- every exact test or acceptance node that must fail under that mutation; and
- a verdict from the standing harness for `vacuous`, `stale`, `mixed`,
  `uncollected`, and class-node collapse.

The unsabotaged baseline must pass. A selected durable arm runs through the
cut-7 acceptance runner on the certified tuple; errors on that tuple are
errors, never skips. Portable arms remain in the portable suite. The cut-7
runner may invoke the cut-5 and cut-6 runners as a prefix, but neither
runner nor either cut's meaning is edited.

N2 gates on the landed `atoms.read_chain` command; the `ChainView`
invariants are that repository's obligation and are consumed here, not
re-certified.

The three surfaces are `python/tests/n2_arms_cut7.py`,
`python/tests/acceptance/test_n2_cut7.py`, and
`python/tools/cut7_acceptance.py`.

N2 is prospective at freeze: the cut fixes the declaration inventory and
claims no declaration, sabotage, or test exists.

## 6. The second reader

The independent reader receives only the frozen rows quoted in §3, the
epoch-carrier specification, and §2's boundary; they are not asked to
preserve this draft's rationale. The review attacks in the historically
common direction, toward overstated coverage.

The reader must:

1. check every selected clause and its exact source mutation against §2;
2. demote any clause that reaches the two absent governed kinds, the
   snapshot/receipt import boundary, the audit, the diagnostic query, the
   reduction states, log verification, persistence-cut simulation, or the
   fork constructor;
3. judge the flagged selections: X1's "reported at audit" read as the
   open-time recomputation refusal; X12's empty-enumeration wrong-balance
   instance and W8a's kind-empty rebuild instance, both recorded as
   degenerate rather than claimed as the populated arms; X9's
   head-outside-hold unconstructibility method; and the then-pending-authority
   labeled declaration (ungoverned enumerated kind), which must not survive
   to freeze unless the specification amendment lands;
4. check every cross-reference for single-homing — the retraction omission
   (X12 ← W8a), the rule transitions (X10 ← W8a), the bare version string
   (X10 ← W8a), no-implicit-latest (X3 ← W8a), and the W5 candidate's
   disposition (§3.4) — and that no unit is counted at two homes; and
5. rederive §4's row accounting and the 48-unit declaration inventory
   independently.

### 6.1 Run and dispositions

The independent reading ran on 2026-08-20 with only §3's quoted frozen rows,
the epoch-carrier specification, and §2's boundary declaration. It
byte-verified all eleven quotations against their sources, found no
demotable selection, judged all four flagged selections sound, confirmed
single-homing in both directions, and rederived the row accounting and the
48-unit inventory exactly. Seven findings, all closed before freeze:

1. **§2's belief-closure clause under-licensed its own selections** — it
   named only §3.2's invariance arms while X3's input-shape unit and X12's
   belief-boundary unit also reach the closure. The clause now names all
   three.
2. **W8a's rebuild-identity bullet miscounted the kind-empty maps** — the
   retraction kind exists, so calling two maps kind-empty would have let the
   rebuild arm run with an unnecessarily degenerate retraction map. The
   bullet now requires populated address, producers, and retraction maps and
   names only the coreference map as kind-empty.
3. **X12's cell silently omitted the coreference omission-refutes
   instance** of its "each receipted projection" clause — neither selected
   nor deferred. It is now in the coreference deferred bullet with the kind
   as unblocker.
4. **W8a's agreement arm was weakened from "two installations" to "two
   evaluations"**, which bare determinism would satisfy vacuously. The
   bullet now requires two world roots over the same corpora, each
   resolving the binding and states from its own store.
5. **W8a's outside-coverage contrast clause was silently dropped** from the
   absent-is-not-empty bullet. The `Unknown` contrast is now selected within
   that unit, with §11.15's stated limit named.
6. **X9's head-relocation sabotage could pass vacuously** without an
   interleaved corpus write between state capture and the relocated head
   capture. The bullet now requires the interposed write and pins the
   vacuousness check to N2 declaration time.
7. **X2's stage narrowing was disclosed but not stated** — the bullet now
   says outright that intra-transaction stages belong to the engine's
   certified recovery and are not Science-observable.

Findings 1–4 were correct-severity; 5–7 record-severity. None changed the
unit count or any row state: the closures reword, extend, or re-home
assertions inside their existing units, and §4's accounting stands.

## 7. Limitations

1. **Two enumerated kinds are prose today.** `coreference-attestation` and
   `instrument-certification` are not governed stored kinds; every membership
   and omission arm over them is deferred on the kinds' own charters, and
   the coreference and certification enumerations legitimately find nothing.
   The empty-enumeration instances selected in §3 are recorded as such and
   claim nothing about populated behavior.
2. **No persistence-cut harness.** X2's power-fail arm is deferred, not
   argued away; committed registration-entry evidence plus the engine's A8
   certification is the whole durable claim.
3. **`atoms.read_chain` is prospective.** The cut consumes the specification
   §2 contract; N2 gates on the landed command and this cut re-certifies
   nothing in that repository.
4. **The evaluator is exercised without its future callers.** Import, audit,
   and the diagnostic query defer with their surfaces; when they land, they
   must call the evaluator this cut certifies, not reimplement it — that
   architecture arm defers with them.
5. **Cut 5 and cut 6 are prefixes, never edits.** Their runners and meaning
   are untouched; cut 6's committed `world.py` sabotage paths remain
   historical evidence across the package promotion.
6. **Cross-process locking is out of scope.** The `OperationLock` arms are
   in-process; single-writer deployment across processes remains the stated
   obligation.
7. **World resolution is not claimed.** The resolution refusals are local
   carrier checks over configured roots; no world-scale resolution or
   federation claim is made.
