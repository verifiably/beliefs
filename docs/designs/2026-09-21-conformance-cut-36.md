# Conformance cut 36 — event-level L8

**Status:** frozen 2026-09-21, before implementation; L8, L4 and L10 are open
**Design:** `../superpowers/specs/2026-09-21-event-level-l8-design.md`, approved for implementation planning 2026-09-21 at `a61c119` after two reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-21-event-level-l8.md`.
**Numbered after** cut 35 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 36–39 at freeze; cut 35 is the highest discharged runner.

## 1. What this cut is

Cut 8 built half of the log design's cross-chain granularity:
`world/verify.py:_epochs_ordered` answers whether one epoch orders after
another through the world chain, and deferred "the event-level relation —
presence/exclusion reasoning across captured corpus heads" as the design's
own successor work (cut 8 §3.1; log-verification design §10.7). This cut
builds what cut 8 left: the event domain — what an event is and where its
moment lies in its chain; the witness predicate over two cuts and two
chains, with coverage and placeability made explicit; and the
witness-asymmetric relation the caller asks, searched over the world's
retained epochs and answered with a direction or `unordered`. L8 closes in
full. L4 and L10 close as relabels, citing the arms cuts 8 through 10
already read. L1 is not read here; its remaining persistence arms re-home
to `persistence-cut`.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/world/events.py`, `world/verify.py`, `root.py`,
  `errors.py`;
- `python/tests/test_world_events.py`, `test_world_log_audit.py`;
- `python/tests/acceptance/test_event_order_acceptance.py`,
  `python/tests/n2_arms_cut36.py`,
  `python/tests/acceptance/n2_arms_cut36.py`,
  `python/tests/acceptance/test_n2_cut36.py`,
  `python/tools/cut36_acceptance.py`;
- this cut, the ledger, roadmap, guide, README, the log design's
  L1/L4/L8/L10 markers and §7 note, the log-verification design's §7 note
  and §10.7 closure, `open-questions.md`.

Frozen declarations and cut bodies through cut 35 remain byte-exact.

## 3. Selection

Sixteen declaration units are selected and single-homed here. The quoted
row text is byte-exact from the named design at freeze.

```markdown
| L8 | Cross-chain order exists only through world-ancestry-ordered cuts | committed spec-freeze transition in E1's captured head, intent absent from E1, intent in E2, E2's build-start world head descending from E1's publication entry → ordered; both events first appearing in one cut → unordered, and "spec predates run" is not emitted; assert epoch sequence numbers are read by nothing |
```

```markdown
| L4 | Chain removal refutes against any surviving anchor, bound to its subject | delete the chain while a registry log-head record (or supplied exported head) is in the observer set → refuted — the "detectable journal removal" clause of kernel §8.7, discharged; with **two anchored corpora** and one arriving chainless → the subject binding associates the surviving anchor with the arriving corpus's `corpus_id` and refutes exactly it, never the sibling — an anchor is never matched to a root by elimination or by opaque genesis digest alone; raw re-mint an anchored corpus's manifest (`corpus.yaml` A → B) with the chain present → verify selecting **A**; A-bound anchors remain admitted by the selected subject, the manifest mismatch is reported separately, and replay **refutes** the edit — never `unresolvable` by subject disqualification; an edited configuration `world_id` against a present world chain → subject-mismatch finding **and operation refusal** (§3's lifecycle rule) — configuration is not registered surface, so replay cannot refute it, and the chain verdict derives independently of the presented configuration; replace an anchored corpus's chain with a **self-consistent different genesis** under the same `corpus_id`, verify selecting that subject → **refuted**, never empty-set `unresolvable` — a selected-subject anchor naming another genesis is replacement evidence, not a non-match; export a **W1** head, rewrite the local world subject and genesis to **W2**, verify explicitly selecting **W1** → refuted as removal/replacement, while selecting **W2** is a separate-world audit, never a verdict about W1; delete an anchored corpus A's chain **and** re-mint its `corpus.yaml` as B, then verify explicitly selecting **A** with A's anchor supplied → **refuted** as removal — the selected subject associates the anchor, and the presented manifest never discards it into empty-set `unresolvable`; delete or replace a store's chain while its store-subject registry record is in the observer set → **refuted**, the subject binding associating the anchor by `store_id`, never by elimination *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2 — mechanism, not verdict: the corpus genesis is identity-free, so the "self-consistent **different** genesis under the same `corpus_id`" arm is not currently constructible — a fabricated distinct corpus genesis is malformed at genesis-form validation before any anchor judgment. Corpus-chain **replacement** is refuted through anchored-head unreachability under the same constant genesis instead, which is the arm conformance cut 8 reads; the different-genesis refutation is read for **world** subjects and defers, with L10's fork arms, for a future fork genesis)* |
```

```markdown
| L10 | A fork is a new chain; a replica is the same chain | fork act → fresh genesis carrying `(parent genesis, parent head)` and its own baseline; assert parent and fork anchors are never compared; replica/restore → same genesis, chain carried unchanged, comparability intact; a copy presenting the parent genesis under a fresh `corpus_id` manifest without a fork-genesis → its chain refuses to verify under the new identity (genesis names the parent `corpus_id`); the **store instantiation** (the verified-holdings record design §2) — replica act → same genesis, chain carried unchanged, a claim-only destination directory published first as reserved, surface-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation of an existing root **not granted writability** → refused, with recorded root creation the sole pre-grant write exception and the fork act the only writable exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2/§6.2 — mechanism, not verdict: the copy presenting the parent genesis under a fresh `corpus_id` manifest **cannot** be caught by a genesis-payload comparison, since a corpus genesis names no `corpus_id`. The arrival act is the mechanism instead — `admit_arrival` selects `S = Corpus(provenance.parent_corpus_id)`, because the chain a replica carries is its parent's, and the fresh manifest then refuses `SubjectMismatch`: its chain refuses to verify under the new identity, exactly the frozen claim. This is the one arm of this row conformance cut 8 reads; every fork, replica-construction, restore and store arm still waits on ledger row 4)* |
```

| unit | row | what it reads |
|---|---|---|
| L8-a | L8 | a committed spec-freeze transition in A, E1, a run intent in B, E2 built from E1's publication → `a-precedes-b`; the reverse question → `b-precedes-a`; cut 8's two units (the ordered-cuts predicate, the sequence-number negative) cited to `../plans/2026-08-22-conformance-cut-8-results.md`, never re-run |
| L8-b | L8 | both events first appearing in one cut → `unordered` in both argument orders, no positive answer emitted; and a witnessed pair stays ordered when two later cuts hold both events — the exclusion clause's own claim |
| L8-c | L8 | epoch sequence numbers are read by nothing: no `Epoch` attribute names one and no line of `_ordered_by_descent`, `_witnessed` or `_event_order` does |
| L8-d | L8 | E1 covering A only → `unordered`; a later pair of cuts covering both orders the pair |
| L8-e | L8 | A's chain replaced under a different fork genesis presenting the same subject after E1 (cut 9's L4u2 fixture) → `unordered` |
| L8-f | L8 | the double witness by the overlapping-build schedule (spec §4.3) → `unordered` |
| L8-g | L8 | valid-prefix truncation of A behind every cut's captured head, the queried event retained: the pair → `unordered` (no witness places); the removed event → `EventUnknown` |
| L8-h | L8 | same chain: two committed transitions order by ancestry; a registration and its own settlement → `unordered`; the same event twice → `unordered` |
| L8-i | L8 | no moment (stand-in inspection over real published epochs): a pending registration and a rolled-back one each → `unordered` |
| L8-j | L8 | same-chain independence: a malformed retained carrier and a malformed world chain leave a same-chain answer standing; the cross-chain question refuses `EpochMalformed` with the carrier present and answers `unordered` once the carrier is moved out of `epochs/` and only the world chain is damaged |
| L8-k | L8 | the refusals: `EventCorpusUnknown`; `EventCorpusUnresolvable` for no carrier and for two distinct roots claiming one id, one root configured twice staying resolvable; `EventUnknown` for another chain's digest; `BuildHold` under a capture hold; a terminal corpus still answers |
| L4-a | L4 | relabel: every clause read at cuts 8 (seven units) and 9 (two units) cited; one durable check — a corpus chain deleted while its registry log-head record is in the observer set → `refuted`, the anchor bound by `corpus_id` |
| L10-a | L10 | relabel: the arrival-identity arm (cut 8), the fork, replica, restore and store arms (cut 9) and the two holdings-read clauses (cut 10) cited; one durable check — a replica presenting the parent genesis under a fresh `corpus_id` manifest refuses `SubjectMismatch` at `admit_arrival` |
| BI-1 | — | recovery before resolution: the world inspection precedes the registry scan on a same-chain and on a cross-chain question |
| BI-2 | — | one world inspection per call; the world lock is released before the first corpus lock; corpus locks are taken in sorted order and never nested |
| BI-3 | — | the isolated genesis clause: a genuine well-formed view, an anchor with a reachable head, only `genesis_digest` replaced → `place` is `None`, while the unaltered anchor places |

### 3.2 Rows not read

**L1** is not read. Its remaining arms — kill the executor between entry
durability and apply at every stage; crash after entry durability but
before the transaction record stores the entry digest; cut persistence at
every stage of the settlement sequence for both terminal arms — are the
persistence-cut harness's (cut 8 §3.1, `persistence-cut`, `beliefs-3ea822`).
This cut's results record re-homes them there; L1 stays partial.

## 4. Accounting

**16 declaration units**, thirteen against rows and three boundary
invariants; L8, L4 and L10 close; L1 stays partial under `persistence-cut`.
183 of 216 → 186 of 216.

## 5. N2 and acceptance obligations

Acceptance has one arm per declaration unit, with two units (L8-a, L8-j)
each carrying two arms. Each N2 sabotage has a byte-exact `before` block
copied from the tree at freeze and parsed after mutation.

| arm | module | sabotage | check |
|---|---|---|---|
| L8-a1 | `world/verify.py` | `_witnessed` reads E1's own world anchor instead of E2's | L8-a |
| L8-a2 | `world/verify.py` | `_ordered_by_descent` compares strictly (`>` for `>=`; R29 regresses) | L8-a |
| L8-b | `world/verify.py` | `_witnessed` drops the E1-on-B exclusion clause (under it, two later cuts holding both events witness the reverse and the positive collapses to `unordered`) | L8-b |
| L8-c | `world/verify.py` | `_event_order` acquires a sequence number | L8-c |
| L8-d | `world/verify.py` | `_witnessed` treats a missing E1 anchor for B as exclusion | L8-d |
| L8-e | `world/verify.py` | `_placement` turns an unplaceable anchor (mismatched genesis or absent head) into the chain's tip | L8-e |
| L8-f | `world/verify.py` | `_event_order` answers `a-precedes-b` on `W(a,b)` alone | L8-f |
| L8-g | `world/events.py` | `place` accepts a head absent from the chain as the chain's tip | L8-g |
| L8-h | `world/events.py` | `moment` returns a registration's own position | L8-h |
| L8-i | `world/events.py` | `moment` returns a rolled-back settlement's position | L8-i |
| L8-j1 | `world/verify.py` | `_event_order` opens the retained epochs for a same-chain question | L8-j |
| L8-j2 | `world/verify.py` | `_event_order` maps `EpochMalformed` to `unordered` | L8-j |
| L8-k | `world/verify.py` | `_event_carrier` resolves two distinct carriers to the first | L8-k |
| L4-a | `world/verify.py` | an absent chain under a bound anchor reads `unresolvable` | L4-a |
| L10-a | `world/verify.py` | `admit_arrival` no longer refuses a manifest naming another corpus | L10-a |
| BI-1 | `world/verify.py` | the registry scan precedes the world inspection | BI-1 |
| BI-2 | `world/verify.py` | the world chain is inspected twice per call | BI-2 |
| BI-3 | `world/events.py` | `place` ignores the genesis digest | BI-3 |

That makes **18 arms over 16 units** (L8-a and L8-j home two each; every
other unit one). Both directions are required: the check passes on the
real tree and fails under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut35_acceptance.py",)` and carries
`PHASE_MODULES = ("test_event_order_acceptance.py", "test_n2_cut36.py")`.

## 6. Second reader

Check that the double-witness fixture's builds really overlap (E1 and E3
both record `h0`), that BI-1 observes order through the production seam's
functions and not a stub, that L8-g's truncation is a valid prefix (the
chain still well-formed), and that L8-i's stand-in views are the only
fabricated views in the module.

## 7. Limitations

1. **The build window remains the residual uncertainty** (log design
   limitation 4), now visible as the double witness answering `unordered`.
2. **Capture-order sharpening** — the build captures serially in sorted
   `corpus_id` order, so "E1's A-head contains `a` and its B-head excludes
   `b`" implies `a` before `b` in real time exactly when `A < B`; using it
   would order the double witness. Filed in `open-questions.md`, not
   built.
3. **No consumer.** Comp §3.3's chronology claim has no finding that
   consults the relation; one is the owning lane's, when a boundary needs
   it.
4. **L1's persistence arms** are `persistence-cut`'s, behind
   `atoms-f5779f`.
