# General intent qualification — design (world-index slice 6, the intent boundary)

**Date:** 2026-08-26
**Status:** draft — spec under review; conformance cut 11 freezes before any
implementation task, per §8 step 3. Promotion from `docs/superpowers/specs/`
to `docs/designs/` happens in the banking change, per the slice-5 precedent.
**Inherits:** `2026-08-03-tamper-evident-log-design.md` §6 as amended — the
qualification reduction this slice implements at its full stated width: the
matched / unresolvable / attempt-without-recorded-outcome precedence, the
assessment-run shape *(amended 2026-08-11, the act-report design §3 — the
widening to a `run-attempt` act-report)*, the holdings shape *(amended
2026-08-10, the verified-holdings record design §8)*, and the operation
shape *(amended 2026-08-11)*; `2026-08-11-act-report-design.md` §3 (the
operation intent, the completion discipline, T2's malformed-before-
qualification rule); `2026-08-24-world-index-holdings-design.md` §4.3 (the
holdings-shaped interior, written so this slice replaces its interior, not
its callers) and its deferral 5 (this slice's named territory);
`2026-08-22-log-verification-design.md` (the evaluator, the report that
states the qualification deferral, §10 item 1 — the owner row this slice
discharges; cut 8's frozen L7 row is this slice's arm inventory);
`2026-08-02-epistemic-kernel-design.md` §3.2 and §8.7 (G4 narrowed, the
recorded-history completeness table, the G-table's G4 row with its negative
half); adoption-ledger row 5 (the intent-boundary remainder named there).
**Constraints:** no `atoms` change — the intent API is unchanged, and
`read_chain`/`inspect_chain` supply everything the reducer reads. Frozen cut
bodies stay frozen under their identifiers. Qualification is report-field
status, never the chain verdict (log §6). No compatibility alias for any
retired field. The rules-store dialect's constraints hold as built: pure
source, no science imports, binding by content digest.

## 1. Scope

**Built here (Science only):**

1. **The general qualification reduction** — one pure reducer implementing
   log §6's precedence, parameterized by a closed union of the three
   intent-union shapes (assessment-run, operation, holdings).
2. **The verifier's lift** — `LogReport.intents_unevaluated` retires;
   evaluated qualification takes its place as report fields and findings.
3. **The holdings interior replacement** — the installed holdings rule's
   qualification source is regenerated from the general reducer's holdings
   shape; new content digest, new pinned receipt, callers untouched.
4. **G4's closure** — both halves of the kernel G-table row, read through
   the reduction.

**Closed here:** L7 from partial to its stated width — the guarantee
quantifies over all three intent kinds, exactly as cut 8's frozen row
states it; kernel §8.7's fourth recorded-mutation consequence (G4); the
"intent qualification is unevaluated" deferral stated in every report
(log-verification design §10 item 1); adoption-ledger row 5's
intent-boundary remainder.

**Not here, each staying with its named owner:**

1. **Event-level L8** — the presence/exclusion relation across captured
   corpus heads; the log-verification design's own successor work.
2. **The L13 preimage resolver** — waits on the named `atoms` blob-read
   seam; row 5's other named remainder.
3. **The URL retrieval boundary, acquisition orchestration, typed
   retrieval grants, recency as a successor projection rule** — the
   holdings design's deferrals 1–4, untouched.
4. **Out-of-band chronology** (G2a's negative) — stays open exactly as
   banked; nothing here strengthens it.
5. **The derived-answer negatives** — a discarded replay stops being
   consulted; neither §8.7 nor this slice claims to change how belief is
   computed from what remains.

## 2. The reduction module (`science/intents/`)

**2.1 One reducer, one precedence.** The module ships a single pure
function implementing log §6's reduction, and the three shapes are data to
it, never forks of it — the same no-second-taxonomy rule that put
`inspect_chain`'s validation core behind one shared implementation. The
precedence, verbatim from §6:

- any qualifying pointer → **matched**;
- no qualifier, but any pointer whose published record cannot be read →
  qualification **unresolvable** — decayed bytes are not evidence of no
  outcome, and **no** unmatched finding is emitted;
- only when every pointer fully resolves and none qualifies → the
  **attempt-without-recorded-outcome** finding, with each non-qualifying
  `fulfills` named in its own finding.

Unresolved never collapses into either resolved state — the holdings
slice's rule, now general.

**2.2 The closed shape union.** Exactly three members, closed by
construction. Each shape contributes two pure functions:

- **decode**: entry payload → a validated intent of this shape, `None` for
  another domain, or a raised malformation for a payload that names this
  shape's domain and fails its schema — the holdings decoder's contract,
  now the union's.
- **qualifies**: a committed registration's published record × a decoded
  intent → qualifying or not, at the shape's stated width:
  - **assessment-run**: the `run` as built, or an act-report of kind
    `run-attempt` carrying the intent's `event_token`, for a post-intent
    attempt that minted no run. A pre-intent refusal publishes an
    *unfulfilling* report and fulfills nothing.
  - **operation**: for a non-run operation, the act-report carrying the
    intent's `event_token`; for a `dataset-production` operation, the
    minted `run` or, when none is minted, that act-report.
  - **holdings**: a holdings observation for the intent's canonical
    location carrying the intent's `event_token` — the interior as written
    today, relocated, not rewritten.

**2.3 Malformation stays the chain's.** A second committed registration
fulfilling one intent, a `fulfills` naming a missing or non-ancestor
intent — structure, classified before qualification ever runs (T2's rule).
The reducer never re-litigates what the chain already ruled malformed.

**2.4 The dialect constraint is a design input.** The shape functions are
pure and single-module so the rules-store concatenation can consume the
holdings shape unchanged (§4). Purity is not an implementation nicety
here; it is what makes one interior servable to two consumers.

## 3. Verifier integration (`science/world/verify.py`)

`LogReport.intents_unevaluated` retires. In its place the report carries
the evaluated form: per-intent qualification status — `matched`,
`unresolvable`, or `attempt-without-recorded-outcome`, the third status
carried exactly when §6's attempt-without-recorded-outcome finding is
emitted for that intent — and the findings §6 names: that finding, and
one finding per non-qualifying `fulfills`. Carriage rules are the
inventory's, unchanged in spirit:

- carried even on a genesis-form `malformed` exit — a chain the engine
  linearized has an intent inventory whatever its genesis payload says;
- absent on the `MalformedView` exit, where there are no entries to
  inventory — a different fact, as the current comment states.

Qualification remains **report-field status, never the chain verdict**:
no qualification state changes `outcome`, and no outcome suppresses
qualification's findings. Callers and tests naming the retired field
update in the same task; no alias, no deprecation shim.

## 4. The holdings interior replacement (`science/holdings/`)

The installed rule's qualification source (`qualify.py`, concatenated into
the `rules_v1` fixture) is regenerated from the general reducer's holdings
shape, so the rule and the verifier share one interior. The rule's
callers — the capture split, the active-set reducer, the three blocking
classes, the coverage projection, the adapter, the receipt *machinery* —
are untouched: holdings §4.3's contract, "replaces its interior, not its
callers," discharged as written. What changes is exactly:

1. the rule source's qualification section, now generated from the shared
   shape rather than hand-maintained beside it;
2. the rule's content digest, and therefore the pinned receipt — a new
   receipt is minted under the existing receipt discipline, and the old
   one remains what it always was, a value with a content identity;
3. nothing else. Blocking semantics, per-location precedence (§5.1's
   pinned capture precedence), and the reducer's fixture binding are
   byte-for-byte concerns of the regeneration, certified by arms that run
   the holdings qualification through both consumers and compare.

## 5. G4's closure

**The positive half.** A **recorded** failed replay attempt cannot be
silently orphaned. Through the reduction: an intent whose fulfillment
never qualifies — a kill between the durable intent append and execution
start, a wrong-purpose committed transaction, a publication creating no
run — reads **attempt-without-recorded-outcome** in every report over the
chain, and discarding the failed *fulfillment* while the intent survives
moves qualification, never erases the attempt. The kernel G-table row's
refusal arm — an unreferenced successor to a recorded failure — is read
where the boundary already refuses it.

**The negative half, pinning the limit.** Discard the failed attempt
*entirely* — no intent appended, nothing durable — and confirm the system
**cannot** detect it: crash, cancellation, and discarded failure are
indistinguishable by construction. The arm asserts the limit so no reader
over-reads G4, exactly as G8's negative pins its own. Detection stays
quantified over surviving observers throughout — destruction of a root
together with every anchor holding it is not detectable from nothing.

G4 closes at this slice's discharge; the G2a-ordering row is untouched.

## 6. Conformance cut 11

The cut document (`conformance-cut-11`, dated at drafting) freezes before
any implementation task. Its selection is drawn from frozen text, not written
fresh:

- **cut 8's L7 row** — the qualification arms at all three widths:
  no-pointers and all-resolved-non-qualifying; the mutated fulfillment
  family per shape (wrong purpose, wrong spec, wrong token, no record
  created; wrong location for holdings; wrong kind and wrong-operation
  token for operation); unresolvable published bytes with no unmatched
  finding; kill-between-append-and-start per shape; the
  root-other-than-the-intent's refusal; no caller-supplied `fulfills`
  path at the boundary; and the row's negative. The two chain-structural
  L7 units stay cut 8's — certified there, not re-read.
- **the kernel G-table G4 row** — both halves (§5).
- **both-consumer agreement** — the regenerated holdings rule and the
  verifier answer holdings qualification identically over the same
  captured evidence (§4 item 3).
- **L7u1's partial remainder** — re-examined at the new width; selected
  if constructible, its partiality re-stated with the same reason if not.

Classification follows the any-unrun-arm rule: any arm not run keeps its
row partial, and no argument for why an arm shouldn't count earns a
"full." Discharge is on the certified volume, through the certified
acceptance-runner cadence, with pytest summary lines quoted in the
results record and the execution rulings ledger committed to a tracked
path before any worktree removal.

## 7. What this changes elsewhere (applied at banking)

- **Kernel §8.7** — the fourth recorded-mutation consequence closes; the
  status paragraph gains G4's dated closure with the negative's pin
  restated.
- **Adoption-ledger row 5** — the intent-boundary remainder discharges;
  the row's remainder text shrinks to event-level L8 and the L13
  preimage resolver.
- **Adoption-ledger design-track item 6** — same shrink.
- **Log-verification design §10 item 1** — closed with a dated note, the
  slice-3 precedent for items 2, 3 and 6.
- **`2026-08-22-log-verification-design.md` deferral texts and the
  holdings design's deferral 5** — dated closure notes; frozen cut bodies
  untouched.
- **README/guide live claims** — the stale-claim grep
  (`intent qualification|intents_unevaluated|G4`) runs at banking; live
  text saying qualification is unevaluated updates, frozen records stay.

## 8. Choreography (order of work)

1. This spec's review closes.
2. The conformance cut 11 document is drafted from the frozen sources §6
   names and reviewed by a second reader.
3. **Cut 11 freezes** — before any implementation task.
4. Implementation on `design/intent-boundary`, TDD throughout, the
   holdings slice's per-task review cadence: the reduction module, the
   verifier lift, the interior replacement, G4's arms — each task
   red-then-green with its review findings closed by amendment.
5. Certified discharge: the acceptance runner on the certified volume;
   results record and rulings ledger committed to tracked paths.
6. Banking: §7's changes, status header here, promotion to
   `docs/designs/`; the `--no-ff` merge is the human partner's act.

Any gap discovered mid-task between a frozen arm and built boundary
behavior (a refusal the boundary does not yet make, a record it does not
yet publish) upgrades scope by a dated amendment here before the task
proceeds — never a silent narrowing of the arm.
