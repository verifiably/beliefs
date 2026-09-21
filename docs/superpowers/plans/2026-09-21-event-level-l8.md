# Event-level L8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the event-level cross-chain order relation over captured corpus heads, close L8 in full and L4 and L10 as relabels, re-home L1 to `persistence-cut`, and discharge it as conformance cut 36.

**Architecture:** A new pure module `beliefs.world.events` holds the event domain (an event's *moment* in its chain, a cut's *placement* of a chain). `world/verify.py` gains a pure ordered-cuts helper factored out of `_epochs_ordered`, the witness predicate `_witnessed`, and the relation core `_event_order`, which the composition root wraps as `root.event_order` with the production seam injected. Nothing is written; the relation reads the world chain, the retained epochs' `anchors.yaml`, and the two corpus chains.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, the acceptance harness under `python/tests/acceptance/` and the N2 audit (`n2_arms.py`, `test_n2.py`).

**Spec:** `docs/superpowers/specs/2026-09-21-event-level-l8-design.md` (reviewed 2026-09-21, two rounds; §12 there). Read it first; every task cites its sections.

## Global Constraints

- **Baseline is `main` at `acf4692`.** Work in the worktree `.worktrees/event-level-l8` (branch `event-level-l8`); every path below is relative to the repository root, and paths shown to the user carry the worktree prefix. Exports for a worktree on `WORK_ROOT`: `SCIENCE_MM30_ROOT` and every `SCIENCE_CUT*_ROOT` name the **main checkout's** `.work/…` (memory `worktree-on-work-root-needs-cut-root-exports`; ~190 `CapabilityUnavailable` failures are a missing export, not a regression). The main checkout is `~/d/beliefs`.
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions. — For this lane: `world/events.py` imports only `beliefs.errors` and `beliefs.world.logmodel`; `world/verify.py`'s additions import `epoch` and `registry` lazily inside the function, as its neighbours do; the relation calls no write primitive, so the inventory is unchanged, and Task 3 asserts `test_permit_boundary.py`, `test_permit_entry_points.py` and `test_capability_boundary.py` green.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. — Here that is Task 5, Step 4, with `(cut36, 36, (18, 16, 3))`.
- **The worktree's sibling dependencies resolve through WORK_ROOT links.** `python/pyproject.toml` pins `verifiably-atoms` and `verifiably-nodes` as editable paths `../../atoms/python` and `../../nodes/python`, which from `.worktrees/event-level-l8/python` resolve under `$WORK_ROOT/beliefs/.worktrees/`. The links `.worktrees/atoms → ~/d/atoms` and `.worktrees/nodes → ~/d/nodes` exist (created 2026-09-21); `cd python && uv run --frozen python -c "import atoms, nodes, beliefs"` prints nothing on success. A `Distribution not found at: file://$WORK_ROOT/beliefs/.worktrees/atoms/python` is a missing link, not a dependency change.
- **Frozen declarations and frozen cut bodies stay byte-exact.** Cut 8's guard is cited-not-run (`cited_not_run.py`, R15): cut 36 chains **cut 35's** runner (`PREFIX_RUNNERS = ("cut35_acceptance.py",)`), cites cut 8's two L8 units, and never runs or re-targets `test_n2_cut8.py`. The staleness gate is `tests/test_arm_staleness.py::test_every_arm_a_live_guard_audits_applies_exactly_once` (zero stale live arms) plus `tests/test_frozen_guards.py`; a line the refactor moves in a **live** guard's pin is re-targeted in that guard's `_LIVE_SABOTAGES`; a line it moves in a cited guard's declaration is recorded in `cited_not_run.py`'s `stale_arms` with the commit, never repaired. Task 2 verifies that `_publication_settlement`'s `if type(entry) is SettledEntryView and entry.committed and entry.registration in publications:` line and `_epochs_ordered`'s `first = _packaging_identity(e1)\n    second = _packaging_identity(e2)` lines are untouched — they are cut 8's two L8 pins.
- **Decisions the code must honour verbatim** (spec §2): a registration's moment is its committed settlement, a rolled-back or pending one has none (D2); equal moments are `unordered` (D3); a same-chain question opens no epoch and ignores the world view's classification (D4); `a-precedes-b` iff `W(a,b) and not W(b,a)` (D5); a cut speaks about a chain only with an anchor whose genesis equals the live genesis and whose head places, and both witness cuts cover both corpora (D6); the world chain is inspected **exactly once** per call and every ordered-cuts question is asked of that one view through `_ordered_by_descent` (D7); `EventCorpusUnknown` / `EventCorpusUnresolvable` / `EventUnknown` are the refusals and terminal corpora stay queryable (D8); `EpochMalformed`, `BuildHold`, `LogEvidenceRefused` propagate untranslated (D9); world lock first, `inspect_registered` on the world root **before** the registry scan, released before any corpus lock, corpus locks sorted and never nested (D10).
- **Lock discipline is the audit's**: `seam.world_lock(root)` around the world reads, `with seam.corpus_lock(carrier):` (the writer-style hold) around each corpus inspection. No `World` method under the world lock (R12).
- No `TypeScript` changes; both `CONTRACT.yaml` copies unchanged. `science.belief.v1`'s answers unchanged; P1–P9 green at every commit.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row(s) or invariant(s) it serves. Run every `pytest` from `python/` with `uv run --frozen`.

---

## File map

| File | Responsibility |
| --- | --- |
| `python/src/beliefs/errors.py` | `EventCorpusUnknown`, `EventCorpusUnresolvable`, `EventUnknown` (Task 1) |
| `python/src/beliefs/world/events.py` (new) | `Event`, `Order`, `moment`, `Placement`, `place`, `contains`, `excludes` (Task 1) |
| `python/src/beliefs/world/verify.py` | `_ordered_by_descent` (Task 2); `_placement`, `_witnessed`, `_event_order` (Task 3) |
| `python/src/beliefs/root.py` | `event_order` wrapper; `Event`, `Order` re-exported (Task 3) |
| `python/tests/test_world_events.py` (new) | the domain over fabricated views (Task 1) |
| `python/tests/test_world_log_audit.py` | `_ordered_by_descent` (Task 2); `TestTheEventLevelRelation`, wrapper tests (Task 3) |
| `python/tests/acceptance/test_event_order_acceptance.py` (new) | the sixteen declaration units over real worlds (Task 4) |
| `python/tests/n2_arms_cut36.py` (new), `python/tests/acceptance/n2_arms_cut36.py` (new shim), `python/tests/acceptance/test_n2_cut36.py` (new), `python/tools/cut36_acceptance.py` (new), `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, the recent-cut row (Task 5) |
| `docs/designs/2026-09-21-conformance-cut-36.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py` | the freeze (Task 0) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | §15 (Task 6) |
| `docs/plans/2026-09-21-conformance-cut-36-results.md` (new), the ledger, the roadmap, `python/tools/roadmap_status.py`, the guide, `README.md`, `docs/designs/2026-08-03-tamper-evident-log-design.md`, `docs/designs/2026-08-22-log-verification-design.md`, `docs/guide/open-questions.md`, tasks | discharge and amendments (Task 7) |

---

### Task 0: Freeze cut 36 and file the tasks

**Files:**
- Create: `docs/designs/2026-09-21-conformance-cut-36.md`
- Modify: `README.md` (the designs count and table row), `docs/guide/contracts-and-adoption.md` (the "frozen and not yet discharged" paragraph and the cut list), `python/tests/test_designs_corpus.py` (the number-word table, one entry), `tasks/beliefs-b34652.md` and `tasks/beliefs-3ea822.md` through the CLI

**Interfaces:**
- Produces: the frozen §§2–7 the guard pins (Task 5 reads its freeze commit and body digest); the unit inventory every later task builds against.

- [ ] **Step 1: Confirm cut 36 is unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -q "conformance-cut-3[6-9]" && echo "claimed on $b"; done; echo scan done
git worktree list
```
Expected: `scan done` alone; the only worktrees are `main`, `.worktrees/audio-baseline` and `.worktrees/event-level-l8`.

- [ ] **Step 2: Write the cut document** on cut 35's shape (`docs/designs/2026-09-20-conformance-cut-35.md`; `sed -n 1,215p` it first). Header:

```markdown
# Conformance cut 36 — event-level L8

**Status:** frozen 2026-09-21, before implementation; L8, L4 and L10 are open
**Design:** `../superpowers/specs/2026-09-21-event-level-l8-design.md`, approved for implementation planning 2026-09-21 at `a61c119` after two reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-21-event-level-l8.md`.
**Numbered after** cut 35 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 36–39 at freeze; cut 35 is the highest discharged runner.
```

§1 states what the cut is (spec §1's third and fourth paragraphs, condensed: cut 8 built the ordered-cuts predicate and deferred the event-level relation; this cut builds the event domain, the witness predicate and the witness-asymmetric relation; L8 closes; L4 and L10 close as relabels citing cuts 8–10; L1 is not read and re-homes to `persistence-cut`).

§2 the boundary: `python/src/beliefs/world/events.py`, `world/verify.py`, `root.py`, `errors.py`; `python/tests/test_world_events.py`, `test_world_log_audit.py`; `python/tests/acceptance/test_event_order_acceptance.py`, `python/tests/n2_arms_cut36.py`, `python/tests/acceptance/n2_arms_cut36.py`, `python/tests/acceptance/test_n2_cut36.py`, `python/tools/cut36_acceptance.py`; this cut, the ledger, roadmap, guide, README, the log design's L1/L4/L8/L10 markers and §7 note, the log-verification design's §7 note and §10.7 closure, `open-questions.md`. "Frozen declarations and cut bodies through cut 35 remain byte-exact."

§3 selection: quote the L8, L4 and L10 rows byte-exact from `docs/designs/2026-08-03-tamper-evident-log-design.md` §10 (`grep -n "^| L8 \|^| L4 \|^| L10 " docs/designs/2026-08-03-tamper-evident-log-design.md` and copy the whole lines), then the unit table:

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

§3.2 rows not read: "**L1** is not read. Its remaining arms — kill the executor between entry durability and apply at every stage; crash after entry durability but before the transaction record stores the entry digest; cut persistence at every stage of the settlement sequence for both terminal arms — are the persistence-cut harness's (cut 8 §3.1, `persistence-cut`, `beliefs-3ea822`). This cut's results record re-homes them there; L1 stays partial."

§4 accounting: "**16 declaration units**, thirteen against rows and three boundary invariants; L8, L4 and L10 close; L1 stays partial under `persistence-cut`. 183 of 216 → 186 of 216."

§5 N2 and acceptance obligations, the sabotage table (module, sabotage, check) exactly as Task 5 declares it:

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

That makes **18 arms over 16 units** (L8-a and L8-j home two each; every other unit one). "Both directions are required: the check passes on the real tree and fails under sabotage. The runner uses `PREFIX_RUNNERS = ("cut35_acceptance.py",)` and carries `PHASE_MODULES = ("test_event_order_acceptance.py", "test_n2_cut36.py")`."

§6 second reader: check that the double-witness fixture's builds really overlap (E1 and E3 both record `h0`), that BI-1 observes order through the production seam's functions and not a stub, that L8-g's truncation is a valid prefix (the chain still well-formed), and that L8-i's stand-in views are the only fabricated views in the module.

§7 limitations: the build window (spec §11.1); capture-order sharpening not built (§11.2); no consumer (§11.3); L1 under `persistence-cut` (§11.4).

- [ ] **Step 3: README, guide, the number word**

`README.md`: "Seventy-two documents" → "Seventy-three documents"; "through 2026-09-20" → "through 2026-09-21"; add the table row after the cut-35 row:

```markdown
| `2026-09-21-conformance-cut-36.md` | the frozen event-level-l8 cut: L8 closed, L4 and L10 relabelled, L1 re-homed, 16 declaration units, three boundary invariants, the cut 35 runner as prefix |
```

`docs/guide/contracts-and-adoption.md`: replace the "Cut 35 is frozen and not yet discharged" paragraph (it is discharged; check `git log -1 --format=%h -- docs/plans/2026-09-20-conformance-cut-35-results.md`) with:

```markdown
Cut 36 is frozen and not yet discharged: event-level L8, with L4 and L10 as
relabels and L1 re-homed to `persistence-cut`
(`../designs/2026-09-21-conformance-cut-36.md`).
```
and add `  - ../designs/2026-09-21-conformance-cut-36.md` to the cut list where cut 35's line is.

`python/tests/test_designs_corpus.py`: add `73: "Seventy-three",` to the number-word table beside `72: "Seventy-two",`.

- [ ] **Step 4: Verify**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```
Expected: all pass (the newest results record is still cut 35's, so the "discharged" guards read cut 35).

- [ ] **Step 5: Tasks**

```bash
tasks edit beliefs-b34652 --plan docs/superpowers/plans/2026-09-21-event-level-l8.md
tasks edit beliefs-b34652 --body "Outcome: Beliefs extends the world-read lane with the event-level relation required by L8 and closes the assigned L4 and L10 log remainder as relabels; L1's persistence arms are re-homed to persistence-cut (beliefs-3ea822).

Acceptance evidence: freeze cut 36 (docs/designs/2026-09-21-conformance-cut-36.md); build the event domain, the witness predicate and the witness-asymmetric relation (spec docs/superpowers/specs/2026-09-21-event-level-l8-design.md); discharge L8 in full and L4 and L10 as relabels on the certified volume; update the adoption ledger and roadmap, re-homing L1; pass the complete gates.

Sources: docs/plans/2026-08-29-implementation-roadmap.md event-level-l8 and log-remainder; docs/designs/2026-08-03-tamper-evident-log-design.md §7; docs/designs/2026-08-22-log-verification-design.md §7, §10.7."
tasks note beliefs-3ea822 "Gains L1's remaining arms from log-remainder at cut 36 (spec 2026-09-21-event-level-l8-design §2 decision 12, §10): kill the executor between entry durability and apply at every stage → entry present, pending; recovery settles it and the surface matches; crash after entry durability but before the transaction record stores the entry digest → no second registration; cut persistence at every stage of the settlement sequence for BOTH terminal arms (a committing and a rolling-back transaction) → one registration, one settlement, the binding backfilled, and neither outcome returned nor the lease released before the settlement is durable. L1 stays partial until this task reads them."
```
The plan's step children already exist (filed with the plan: `beliefs-e363db` Task 0, `beliefs-0bf717` Task 1, `beliefs-2411e4` Task 2, `beliefs-5047af` Task 3, `beliefs-645000` Task 4, `beliefs-e7e497` Task 5, `beliefs-867628` Task 6, `beliefs-1d119e` Task 7, `beliefs-77e2fc` Task 8, each depending on its predecessor). `tasks start` each before its task and `tasks done` it in the task's commit. `tasks check` — zero errors.

- [ ] **Step 6: Commit the freeze**

```bash
tasks check && git add docs/designs/2026-09-21-conformance-cut-36.md README.md docs/guide/contracts-and-adoption.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut): freeze conformance cut 36, event-level L8"
git rev-parse HEAD
```
Record the full commit hash: Task 5's guard pins it as `CUT36_FREEZE_COMMIT`, and `sha256sum docs/designs/2026-09-21-conformance-cut-36.md` as `CUT36_FROZEN_SHA256`.

---

### Task 1: The event domain — `world/events.py` and the three errors

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `EpochUnknown`, line 117)
- Create: `python/src/beliefs/world/events.py`
- Test: `python/tests/test_world_events.py`

**Interfaces:**
- Produces: `Event(corpus_id: str, digest: str)` (frozen dataclass); `Order = Literal["a-precedes-b", "b-precedes-a", "unordered"]`; `moment(view: WellFormedView, digest: str) -> int | None` (raises `EventUnknown`); `Placement(head: int)`; `place(view: WellFormedView, *, genesis_digest: str, head_digest: str) -> Placement | None`; `contains(placement: Placement, moment: int) -> bool`; `excludes(placement, moment) -> bool`; errors `EventCorpusUnknown`, `EventCorpusUnresolvable`, `EventUnknown`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_world_events.py`:

```python
"""The event domain of the event-level relation (spec §3): moments and placements
over fabricated well-formed views. Nothing here reads a root."""

from __future__ import annotations

import pytest
from test_world_log_audit import chain, digest, genesis_entry, registration, settlement

from beliefs.errors import EventUnknown
from beliefs.world import events, logmodel


def intent(label: str) -> logmodel.IntentEntryView:
    return logmodel.IntentEntryView(digest=digest(label), payload=b"{}")


GENESIS = genesis_entry(b"g", label="events-genesis")
INTENT = intent("events-intent")
REGISTRATION = registration(digest("events-reg"), "tx-1", (("a.md", None),), (("a.md", "s"),))
COMMITTED = settlement(digest("events-settled"), REGISTRATION.digest, "tx-1", committed=True)
OTHER_REGISTRATION = registration(digest("events-reg-2"), "tx-2", (("b.md", None),), (("b.md", "s"),))
ROLLED_BACK = settlement(digest("events-rolled"), OTHER_REGISTRATION.digest, "tx-2", committed=False)
PENDING = registration(digest("events-reg-3"), "tx-3", (("c.md", None),), (("c.md", "s"),))
VIEW = chain(GENESIS, INTENT, REGISTRATION, COMMITTED, OTHER_REGISTRATION, ROLLED_BACK, PENDING)


class TestMoment:
    def test_genesis_intent_and_committed_settlement_are_their_own_position(self):
        assert events.moment(VIEW, GENESIS.digest) == 0
        assert events.moment(VIEW, INTENT.digest) == 1
        assert events.moment(VIEW, COMMITTED.digest) == 3

    def test_a_registration_normalizes_to_its_committed_settlement(self):
        assert events.moment(VIEW, REGISTRATION.digest) == 3

    def test_a_rolled_back_settlement_and_its_registration_have_no_moment(self):
        assert events.moment(VIEW, ROLLED_BACK.digest) is None
        assert events.moment(VIEW, OTHER_REGISTRATION.digest) is None

    def test_a_pending_registration_has_no_moment(self):
        assert events.moment(VIEW, PENDING.digest) is None

    def test_an_absent_digest_refuses(self):
        with pytest.raises(EventUnknown):
            events.moment(VIEW, digest("not-an-entry"))

    def test_the_settlement_is_found_by_registration_digest_not_by_adjacency(self):
        # The committed settlement sits two entries after its registration here;
        # a lookup by "the next settlement" would find the rolled-back one.
        view = chain(GENESIS, REGISTRATION, OTHER_REGISTRATION, ROLLED_BACK, COMMITTED)
        assert events.moment(view, REGISTRATION.digest) == 4


class TestPlace:
    def test_a_reachable_head_under_the_live_genesis_places(self):
        placement = events.place(VIEW, genesis_digest=GENESIS.digest, head_digest=COMMITTED.digest)
        assert placement == events.Placement(head=3)

    def test_a_genesis_mismatch_places_nothing_even_with_a_reachable_head(self):
        assert events.place(VIEW, genesis_digest=digest("other-genesis"), head_digest=COMMITTED.digest) is None

    def test_an_unplaceable_head_places_nothing(self):
        assert events.place(VIEW, genesis_digest=GENESIS.digest, head_digest=digest("beyond-the-tip")) is None

    def test_contains_is_inclusive_at_the_head_and_excludes_is_its_negation(self):
        placement = events.Placement(head=3)
        assert events.contains(placement, 3) and events.contains(placement, 0)
        assert not events.contains(placement, 4)
        assert events.excludes(placement, 4) and not events.excludes(placement, 3)


def test_the_module_imports_no_engine_and_no_world_sibling():
    import ast
    from pathlib import Path

    source = Path(events.__file__).read_text(encoding="utf-8")
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imported <= {"__future__", "dataclasses", "typing", "beliefs.errors", "beliefs.world.logmodel"}
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd python && uv run --frozen pytest tests/test_world_events.py -q
```
Expected: `ImportError` — `beliefs.world.events` does not exist.

- [ ] **Step 3: The errors** — append after `EpochUnknown` in `python/src/beliefs/errors.py`:

```python
class EventCorpusUnknown(ScienceError):
    """An event names a `corpus_id` this world has never admitted. Presence on a
    configured root is the corpus's own claim, not the world's, and a relation
    that ordered events of an unadmitted corpus would be answering about a
    chain the world never granted membership to."""


class EventCorpusUnresolvable(ScienceError):
    """An event's corpus is admitted but has no presently configured carrier
    root, or more than one. Both are the same failure — the relation cannot say
    which chain it would read — and neither is repairable by choosing. A root
    configured twice is one carrier; two distinct roots claiming one id are
    two. A terminal (retired or departed) corpus is not this refusal: its chain
    still carries its events."""


class EventUnknown(ScienceError):
    """An event's digest names no entry of its corpus's well-formed chain — a
    digest that was never there, or one a valid-prefix truncation removed.
    Raised only over a well-formed view: a malformed chain answers `unordered`
    before any digest is looked up, because it can place nothing."""
```

- [ ] **Step 4: The module** — `python/src/beliefs/world/events.py`:

```python
"""The event domain of the event-level relation.

Spec: `docs/superpowers/specs/2026-09-21-event-level-l8-design.md` §3. An
**event** is one entry of one corpus chain; its **moment** is the position in
that chain at which it happened — an intent, a genesis or a committed
settlement at its own position, a registration at its committed settlement's,
and a pending or rolled-back registration nowhere. A cut's **placement** of a
chain is where its captured head sits in the live chain, and it exists only
when the captured genesis is the live genesis and the head is an entry of it.
The functions here are pure over already-inspected views; locks, seams and
epochs are `world/verify.py`'s.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from beliefs.errors import EventUnknown
from beliefs.world.logmodel import (
    GenesisEntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

__all__ = ["Event", "Order", "Placement", "contains", "excludes", "moment", "place"]


@dataclass(frozen=True)
class Event:
    """One entry of one corpus chain, named by the corpus and the entry digest."""

    corpus_id: str
    digest: str


Order: TypeAlias = Literal["a-precedes-b", "b-precedes-a", "unordered"]


def moment(view: WellFormedView, digest: str) -> int | None:
    """Where the event named by `digest` happened in `view`, or `None` where it
    has not (yet) happened.

    A registration's moment is its **committed** settlement: the transition
    happened when it committed, not when it was declared. A well-formed chain
    settles a registration at most once (the duplicate is L2's malformed arm,
    classified before this is reached), so the settlement is a lookup by
    `registration` digest, never "the next settlement".
    """
    positions = {entry.digest: index for index, entry in enumerate(view.entries)}
    if digest not in positions:
        raise EventUnknown(f"{digest}: no entry of this chain carries that digest")
    entry = view.entries[positions[digest]]
    if type(entry) is GenesisEntryView or type(entry) is IntentEntryView:
        return positions[digest]
    if type(entry) is SettledEntryView:
        return positions[digest] if entry.committed else None
    assert type(entry) is RegisteredEntryView
    for index, candidate in enumerate(view.entries):
        if type(candidate) is SettledEntryView and candidate.registration == digest:
            return index if candidate.committed else None
    return None


@dataclass(frozen=True)
class Placement:
    """One cut's reading of one chain: the captured head's position in the live chain."""

    head: int


def place(view: WellFormedView, *, genesis_digest: str, head_digest: str) -> Placement | None:
    """Where a captured `(genesis_digest, head_digest)` sits in `view`, or
    `None` where the capture speaks about no prefix of this chain: the genesis
    differs (the chain was replaced), or the head is no entry of it (the chain
    was truncated behind the capture, or replaced). A `None` placement
    establishes neither presence nor exclusion (spec decision 6)."""
    if genesis_digest != view.genesis.digest:
        return None
    for index, entry in enumerate(view.entries):
        if entry.digest == head_digest:
            return Placement(head=index)
    return None


def contains(placement: Placement, moment: int) -> bool:
    """The cut's captured head is at or after the moment: the event had happened."""
    return moment <= placement.head


def excludes(placement: Placement, moment: int) -> bool:
    """The cut's captured head is before the moment: the event had not happened."""
    return not contains(placement, moment)
```

- [ ] **Step 5: Run to verify it passes, and the gates**

```bash
cd python && uv run --frozen pytest tests/test_world_events.py -q && uv run --frozen ruff check src/beliefs/world/events.py src/beliefs/errors.py tests/test_world_events.py && uv run --frozen pyright src/beliefs/world/events.py
```
Expected: all pass, no lint or type findings.

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/src/beliefs/errors.py python/src/beliefs/world/events.py python/tests/test_world_events.py
git commit -m "feat(events): the event domain — moments and placements for L8"
```

---

### Task 2: `_ordered_by_descent` — the pure half of `_epochs_ordered`

**Files:**
- Modify: `python/src/beliefs/world/verify.py` (`_epochs_ordered`, lines 1880–1895 at baseline)
- Test: `python/tests/test_world_log_audit.py` (`TestTheOrderedCutsPredicate`)

**Interfaces:**
- Produces: `_ordered_by_descent(view: WellFormedView, e1: str, built_from: str, absent_state: object) -> Ordering` — exactly the tail of today's `_epochs_ordered`; `_epochs_ordered`'s signature, docstring contract and refusals unchanged.

- [ ] **Step 1: Write the failing test** — add to `TestTheOrderedCutsPredicate` in `python/tests/test_world_log_audit.py`:

```python
    def test_ordered_by_descent_is_the_pure_half_and_the_predicate_calls_it(self, tmp_path, monkeypatch):
        """Spec decision 7: the relation asks the pure helper of one captured
        view; `_epochs_ordered` keeps its contract and routes through it."""
        sequence = Sequence(tmp_path)
        view = world_chain(sequence.first)
        assert verify._ordered_by_descent(view, sequence.first, FIRST_SETTLEMENT, ABSENT) == "ordered"
        assert verify._ordered_by_descent(view, sequence.first, WORLD_GENESIS, ABSENT) == "unordered"
        assert verify._ordered_by_descent(world_chain(sequence.first, committed=False), sequence.first, FIRST_SETTLEMENT, ABSENT) == "unordered"
        assert verify._ordered_by_descent(view, sequence.first, digest("not-in-the-chain"), ABSENT) == "unordered"

        seen: list[tuple[str, str]] = []
        original = verify._ordered_by_descent

        def spy(view_, e1, built_from, absent_state):
            seen.append((e1, built_from))
            return original(view_, e1, built_from, absent_state)

        monkeypatch.setattr(verify, "_ordered_by_descent", spy)
        assert ordered(sequence.config, sequence.first, sequence.second, view) == "ordered"
        assert seen == [(sequence.first, FIRST_SETTLEMENT)]
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd python && uv run --frozen pytest tests/test_world_log_audit.py -q -k ordered_by_descent
```
Expected: `AttributeError: module 'beliefs.world.verify' has no attribute '_ordered_by_descent'`.

- [ ] **Step 3: Refactor** — in `python/src/beliefs/world/verify.py`, replace the tail of `_epochs_ordered` (everything after the `with seam.world_lock(...)` block) with:

```python
    if type(view) is not WellFormedView:
        return "unordered"
    return _ordered_by_descent(view, first, built_from, seam.absent_state)


def _ordered_by_descent(view: WellFormedView, e1: str, built_from: str, absent_state: object) -> Ordering:
    """The pure half of `_epochs_ordered`, over one already-inspected world view.

    Ordered **iff** `built_from` — the world head an epoch recorded at
    preflight — is at or after the settlement that committed `e1`'s
    publication. Descent includes the settlement itself (R29). `unordered`
    where `e1` has no committed publication in this view or `built_from` is no
    entry of it. The event-level relation (`_event_order`) asks this of one
    captured view for every candidate pair, so no pair is judged against a
    different observation of the chain (spec decision 7).
    """
    settlement = _publication_settlement(view, e1, absent_state)
    positions = {entry.digest: index for index, entry in enumerate(view.entries)}
    if settlement is None or built_from not in positions:
        return "unordered"
    return "ordered" if positions[built_from] >= positions[settlement] else "unordered"
```
Leave `first = _packaging_identity(e1)` / `second = _packaging_identity(e2)` and the lock block exactly as they are (cut 8's L8u2 pin), and leave `_publication_settlement` untouched (cut 8's L8u1 pin). Amend the last sentence of `_epochs_ordered`'s docstring from "the event-level relation is deferred and L8 is partial (§10.7)" to "the event-level relation is `_event_order` (cut 36)".

- [ ] **Step 4: Run to verify it passes, with the staleness and freeze gates**

```bash
cd python && uv run --frozen pytest tests/test_world_log_audit.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
git -C .. diff --stat
grep -c "if type(entry) is SettledEntryView and entry.committed and entry.registration in publications:" src/beliefs/world/verify.py
grep -c "    first = _packaging_identity(e1)" src/beliefs/world/verify.py
```
Expected: all pass; both `grep -c` print `1` (the cut-8 pins are untouched, so `cited_not_run.py` gains no entry).

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/world/verify.py python/tests/test_world_log_audit.py
git commit -m "refactor(verify): factor the ordered-cuts descent into a pure helper — L8"
```

---

### Task 3: The witness predicate, the relation, and the composition-root wrapper

**Files:**
- Modify: `python/src/beliefs/world/verify.py` (after `_publishes`, end of the ordered-cuts section), `python/src/beliefs/root.py` (the import block at lines 185–195, `__all__` at 218–236, the wrapper after `epochs_ordered` at line 1796)
- Test: `python/tests/test_world_log_audit.py` (new class `TestTheEventLevelRelation`; `TestThePublicWrappers` gains the wrapper)

**Interfaces:**
- Consumes: Task 1's `Event`, `Order`, `moment`, `place`, `contains`, `excludes`; Task 2's `_ordered_by_descent`; `epoch._retained_identities_locked(world_root)`, `epoch._locked_open_epoch(world_root, identity)`, `Epoch.anchors` (`_Anchor.subject/genesis_digest/head_digest`), `Epoch.world_anchor.head_digest`, `Epoch.packaging_identity`; `registry._scan_registry(root)`, `RegistryView.admissions[i].corpus_id`, `registry._carrier_roots(config, corpus_id)`.
- Produces: `_event_order(config: WorldConfig, a: Event, b: Event, *, seam: LogSeam) -> Order`; `_witnessed(...) -> bool`; `_placement(view, epoch_, corpus_id) -> Placement | None`; `_event_carrier(config, registry_view, corpus_id) -> Path`; `root.event_order(config, a, b) -> Order`; `root.Event`, `root.Order`.

- [ ] **Step 1: Write the failing tests** — add to `python/tests/test_world_log_audit.py`, after `TestTheOrderedCutsPredicate`. The world's epochs are **real** (published through `admitted_world`/`publish` with a scripted head callback); the world and corpus chains are fabricated views handed to the `Inspections` double, as `Sequence` does.

```python
# --- the event-level relation (cut 36) -----------------------------------------

from beliefs.errors import (  # noqa: E402  — grouped with the section it serves
    BuildHold,
    EpochMalformed,
    EventCorpusUnknown,
    EventCorpusUnresolvable,
    EventUnknown,
)
from beliefs.world.events import Event  # noqa: E402


class ScriptedHeads(MovingWorldHead):
    """`MovingWorldHead`, plus a scripted `(genesis, tip)` per corpus root, so a
    build's `anchors.yaml` names entries of the corpus views the arm fabricates."""

    def __init__(self, target: Path) -> None:
        super().__init__(target)
        self.corpus: dict[Path, tuple[str, str]] = {}

    def __call__(self, target: Path) -> tuple[str, str]:
        scripted = self.corpus.get(Path(target).resolve())
        if scripted is not None:
            return scripted
        return super().__call__(target)


def intent_entry(label: str) -> logmodel.IntentEntryView:
    return logmodel.IntentEntryView(digest=digest(label), payload=b"{}")


A_GENESIS = genesis_entry(b"a", label="a-genesis")
A_INTENT = intent_entry("a-intent")
A_REG = registration(digest("a-reg"), "a-tx", (("spec.md", ABSENT),), (("spec.md", state("spec.md")),))
A_SETTLED = settlement(digest("a-settled"), A_REG.digest, "a-tx", committed=True)
A_LATER = intent_entry("a-later")
A_VIEW = chain(A_GENESIS, A_INTENT, A_REG, A_SETTLED, A_LATER)
B_GENESIS = genesis_entry(b"b", label="b-genesis")
B_INTENT = intent_entry("b-intent")
B_VIEW = chain(B_GENESIS, B_INTENT)
A = Event  # readability below: A(ALPHA, ...) / B(BETA, ...)
SECOND_REGISTRATION = digest("registration-2")
SECOND_SETTLEMENT = digest("settlement-2")


class Relation:
    """A world with two admitted corpora, real epochs, and stubbed chains.

    `e1` captures A after the spec freeze and B before the intent; `e2` is
    built from `e1`'s settlement and captures B after the intent. The world
    chain published both.
    """

    def __init__(self, tmp_path: Path) -> None:
        self.heads = ScriptedHeads(tmp_path / "world")
        self.world, _recorder, self.bindings, self.roots = admitted_world(
            tmp_path, (ALPHA, BETA), chain_head=self.heads
        )
        self.alpha, self.beta = self.roots[ALPHA].resolve(), self.roots[BETA].resolve()
        self.inspections, self.captures = Inspections(), Captures()
        self.inspections.set(self.alpha, A_VIEW)
        self.inspections.set(self.beta, B_VIEW)

    def build(self, *, world_tip: str, a_head: str, b_head: str, coverage: tuple[str, ...] = (ALPHA, BETA)) -> str:
        self.heads.tip = world_tip
        self.heads.corpus[self.alpha] = (A_GENESIS.digest, a_head)
        self.heads.corpus[self.beta] = (B_GENESIS.digest, b_head)
        return publish(self.world, coverage, self.bindings).packaging_identity

    def world_chain(self, *published: str) -> logmodel.WellFormedView:
        """The world chain that published `published` in order, each settled."""
        genesis = logmodel.GenesisEntryView(
            digest=WORLD_GENESIS, payload=science_root._world_genesis_payload(WORLD_ID), baseline=()
        )
        entries: list[logmodel.EntryView] = []
        for index, identity in enumerate(published, start=1):
            entries.append(publication(digest(f"registration-{index}"), f"tx-{index}", identity))
            entries.append(settlement(digest(f"settlement-{index}"), digest(f"registration-{index}"), f"tx-{index}", committed=True))
        return chain(genesis, *entries)

    def order(self, a: Event, b: Event, *, world_view: logmodel.ChainView | None = None) -> str:
        self.inspections.set(self.world.config.world_root, world_view if world_view is not None else self.world_chain())
        return verify._event_order(self.world.config, a, b, seam=make_seam(self.inspections, self.captures))


def l8_pair(tmp_path: Path) -> tuple[Relation, Event, Event, str, str]:
    """The L8 positive: freeze in A, E1, intent in B, E2 from E1's settlement."""
    relation = Relation(tmp_path)
    e1 = relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_GENESIS.digest)
    e2 = relation.build(world_tip=FIRST_SETTLEMENT, a_head=A_LATER.digest, b_head=B_INTENT.digest)
    return relation, A(ALPHA, A_REG.digest), A(BETA, B_INTENT.digest), e1, e2


class TestTheEventLevelRelation:
    def test_the_l8_positive_orders_and_is_antisymmetric(self, tmp_path):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        view = relation.world_chain(e1, e2)
        assert relation.order(a, b, world_view=view) == "a-precedes-b"
        assert relation.order(b, a, world_view=view) == "b-precedes-a"

    def test_both_first_appearing_in_one_cut_is_unordered(self, tmp_path):
        relation = Relation(tmp_path)
        e1 = relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_INTENT.digest)
        e2 = relation.build(world_tip=FIRST_SETTLEMENT, a_head=A_LATER.digest, b_head=B_INTENT.digest)
        view = relation.world_chain(e1, e2)
        a, b = A(ALPHA, A_REG.digest), A(BETA, B_INTENT.digest)
        assert relation.order(a, b, world_view=view) == "unordered"
        assert relation.order(b, a, world_view=view) == "unordered"

    def test_a_second_cut_not_ordered_after_the_first_witnesses_nothing(self, tmp_path):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        # The chain published e2 first: e1's settlement is after e2's recorded head.
        assert relation.order(a, b, world_view=relation.world_chain(e2, e1)) == "unordered"

    def test_a_cut_missing_one_corpus_establishes_nothing(self, tmp_path):
        relation = Relation(tmp_path)
        e1 = relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_GENESIS.digest, coverage=(ALPHA,))
        e2 = relation.build(world_tip=FIRST_SETTLEMENT, a_head=A_LATER.digest, b_head=B_INTENT.digest)
        a, b = A(ALPHA, A_REG.digest), A(BETA, B_INTENT.digest)
        assert relation.order(a, b, world_view=relation.world_chain(e1, e2)) == "unordered"

    def test_a_genesis_mismatch_and_an_unplaceable_head_establish_nothing(self, tmp_path):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        view = relation.world_chain(e1, e2)
        replaced = chain(genesis_entry(b"a2", label="a-genesis-2"), A_INTENT, A_REG, A_SETTLED, A_LATER)
        relation.inspections.set(relation.alpha, replaced)
        assert relation.order(a, b, world_view=view) == "unordered"
        truncated = chain(A_GENESIS, A_INTENT, A_REG, A_SETTLED)  # e2's A head (A_LATER) is gone
        relation.inspections.set(relation.alpha, truncated)
        assert relation.order(a, b, world_view=view) == "unordered"

    def test_a_malformed_corpus_chain_or_world_chain_is_unordered(self, tmp_path):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        defect = logmodel.DefectView(kind="cycle", subject=None, detail="fabricated")
        relation.inspections.set(relation.alpha, logmodel.MalformedView(defect=defect))
        assert relation.order(a, b, world_view=relation.world_chain(e1, e2)) == "unordered"
        relation.inspections.set(relation.alpha, A_VIEW)
        assert relation.order(a, b, world_view=logmodel.MalformedView(defect=defect)) == "unordered"

    def test_a_malformed_first_chain_answers_before_the_second_lock_is_taken(self, tmp_path):
        """Spec §4.3 step 2 (review round 3, P2 7): with A malformed and B under
        a capture hold, the answer is `unordered`, never `BuildHold`."""
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        defect = logmodel.DefectView(kind="cycle", subject=None, detail="fabricated")
        relation.inspections.set(relation.alpha, logmodel.MalformedView(defect=defect))
        with _operation_lock_for(relation.beta).capture():
            assert relation.order(a, b, world_view=relation.world_chain(e1, e2)) == "unordered"
        assert relation.beta not in relation.inspections.roots

    def test_the_double_witness_is_unordered(self, tmp_path):
        """Spec §4.3: e1 witnesses a before b, e3 (built from the same world
        head) witnesses b before a; e2 and e4 follow each. Neither direction."""
        relation = Relation(tmp_path)
        e3 = relation.build(world_tip=WORLD_GENESIS, a_head=A_INTENT.digest, b_head=B_INTENT.digest)
        e1 = relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_GENESIS.digest)
        e2 = relation.build(world_tip=SECOND_SETTLEMENT, a_head=A_LATER.digest, b_head=B_INTENT.digest)
        e4 = relation.build(world_tip=digest("settlement-3"), a_head=A_LATER.digest, b_head=B_INTENT.digest)
        view = relation.world_chain(e3, e1, e2, e4)
        a, b = A(ALPHA, A_REG.digest), A(BETA, B_INTENT.digest)
        assert relation.order(a, b, world_view=view) == "unordered"
        assert relation.order(b, a, world_view=view) == "unordered"

    def test_same_chain_orders_by_ancestry_and_equal_moments_are_unordered(self, tmp_path):
        relation = Relation(tmp_path)
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest)) == "a-precedes-b"
        assert relation.order(A(ALPHA, A_LATER.digest), A(ALPHA, A_INTENT.digest)) == "b-precedes-a"
        assert relation.order(A(ALPHA, A_REG.digest), A(ALPHA, A_SETTLED.digest)) == "unordered"
        assert relation.order(A(ALPHA, A_REG.digest), A(ALPHA, A_REG.digest)) == "unordered"
        assert relation.order(A(ALPHA, A_GENESIS.digest), A(ALPHA, A_INTENT.digest)) == "a-precedes-b"

    def test_no_moment_is_unordered(self, tmp_path):
        relation = Relation(tmp_path)
        pending = registration(digest("a-pending"), "a-tx-2", (("x.md", ABSENT),), (("x.md", state("x.md")),))
        rolled = registration(digest("a-rolled-reg"), "a-tx-3", (("y.md", ABSENT),), (("y.md", state("y.md")),))
        rolled_back = settlement(digest("a-rolled"), rolled.digest, "a-tx-3", committed=False)
        relation.inspections.set(relation.alpha, chain(A_GENESIS, A_INTENT, pending, rolled, rolled_back))
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, pending.digest)) == "unordered"
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, rolled.digest)) == "unordered"
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, rolled_back.digest)) == "unordered"

    def test_same_chain_opens_no_epoch_and_ignores_the_world_view(self, tmp_path, monkeypatch):
        relation = Relation(tmp_path)
        relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_GENESIS.digest)
        opened: list[str] = []
        original = epoch._locked_open_epoch
        monkeypatch.setattr(epoch, "_locked_open_epoch", lambda root, identity: opened.append(identity) or original(root, identity))
        defect = logmodel.DefectView(kind="cycle", subject=None, detail="fabricated")
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest), world_view=logmodel.MalformedView(defect=defect)) == "a-precedes-b"
        assert opened == []
        assert relation.order(A(ALPHA, A_INTENT.digest), A(BETA, B_INTENT.digest)) == "unordered"
        assert opened  # the cross-chain question opened the retained epoch

    def test_the_world_inspection_precedes_the_registry_scan_on_both_paths(self, tmp_path, monkeypatch):
        relation = Relation(tmp_path)
        relation.build(world_tip=WORLD_GENESIS, a_head=A_SETTLED.digest, b_head=B_GENESIS.digest)
        order: list[str] = []
        relation.inspections.probe = lambda root: order.append(f"inspect:{root.name}")
        original = registry._scan_registry
        monkeypatch.setattr(registry, "_scan_registry", lambda root: order.append("scan") or original(root))
        relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest))
        assert order[:2] == ["inspect:world", "scan"]
        order.clear()
        relation.order(A(ALPHA, A_INTENT.digest), A(BETA, B_INTENT.digest))
        assert order[:2] == ["inspect:world", "scan"]

    def test_the_world_chain_is_inspected_once_and_the_world_lock_is_released_before_corpus_locks(self, tmp_path):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        relation.inspections.roots.clear()
        world_lock = registry._world_lock_for(relation.world.config.world_root)
        held_during_corpus: list[bool] = []
        corpus_roots: list[Path] = []

        def probe(root: Path) -> None:
            if root != relation.world.config.world_root:
                corpus_roots.append(root)
                held_during_corpus.append(world_lock.acquire(blocking=False) is False)
                if not held_during_corpus[-1]:
                    world_lock.release()

        relation.inspections.probe = probe
        assert relation.order(a, b, world_view=relation.world_chain(e1, e2)) == "a-precedes-b"
        assert relation.inspections.roots.count(relation.world.config.world_root) == 1
        assert held_during_corpus == [False, False]  # the world lock was free at each corpus inspection
        assert corpus_roots == sorted((relation.alpha, relation.beta), key=lambda root: {relation.alpha: ALPHA, relation.beta: BETA}[root])

    def test_refusals_are_caller_input_facts(self, tmp_path):
        relation = Relation(tmp_path)
        with pytest.raises(EventCorpusUnknown):
            relation.order(A("0" * 32, A_INTENT.digest), A(ALPHA, A_LATER.digest))
        with pytest.raises(EventUnknown):
            relation.order(A(ALPHA, digest("never")), A(ALPHA, A_LATER.digest))
        twin = corpus_at(tmp_path / "twin", ALPHA)
        two_carriers = registry.WorldConfig(
            relation.world.config.world_root, relation.world.config.world_id, (*relation.world.config.corpus_roots, twin)
        )
        relation.inspections.set(relation.world.config.world_root, relation.world_chain())
        with pytest.raises(EventCorpusUnresolvable):
            verify._event_order(two_carriers, A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest), seam=make_seam(relation.inspections, relation.captures))
        repeated = registry.WorldConfig(
            relation.world.config.world_root, relation.world.config.world_id, (*relation.world.config.corpus_roots, relation.alpha)
        )
        assert verify._event_order(repeated, A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest), seam=make_seam(relation.inspections, relation.captures)) == "a-precedes-b"
        none = registry.WorldConfig(relation.world.config.world_root, relation.world.config.world_id, (relation.beta,))
        with pytest.raises(EventCorpusUnresolvable):
            verify._event_order(none, A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest), seam=make_seam(relation.inspections, relation.captures))

    def test_a_terminal_corpus_still_answers(self, tmp_path):
        relation = Relation(tmp_path)
        relation.world.retire(ALPHA)
        assert relation.order(A(ALPHA, A_INTENT.digest), A(ALPHA, A_LATER.digest)) == "a-precedes-b"

    def test_the_reads_own_refusals_propagate(self, tmp_path, monkeypatch):
        relation, a, b, e1, e2 = l8_pair(tmp_path)
        view = relation.world_chain(e1, e2)
        monkeypatch.setattr(epoch, "_locked_open_epoch", lambda root, identity: (_ for _ in ()).throw(EpochMalformed(identity)))
        with pytest.raises(EpochMalformed):
            relation.order(a, b, world_view=view)
        monkeypatch.undo()
        lock = _operation_lock_for(relation.beta)
        with lock.capture():
            with pytest.raises(BuildHold):
                relation.order(a, b, world_view=view)

    def test_sequence_numbers_are_read_by_nothing(self):
        for core in (verify._ordered_by_descent, verify._witnessed, verify._event_order):
            code, _docstring, rest = inspect.getsource(core).split('"""', 2)
            assert "sequence" not in code + rest, core.__name__
```

Also extend `TestThePublicWrappers`:

```python
    def test_event_order_is_a_wrapper_with_the_seam_injected(self, monkeypatch, tmp_path):
        seen: list[object] = []
        monkeypatch.setattr(
            science_root,
            "_event_order",
            lambda config, a, b, *, seam: seen.append((config, a, b, seam)) or "unordered",
        )
        config = config_for(tmp_path, corpus_root(tmp_path))
        a, b = Event(ALPHA, "1" * 64), Event(ALPHA, "2" * 64)
        assert science_root.event_order(config, a, b) == "unordered"
        assert seen == [(config, a, b, science_root._log_seam())]
        assert list(inspect.signature(science_root.event_order).parameters) == ["config", "a", "b"]
        assert {"event_order", "Event", "Order"} <= set(science_root.__all__)
        assert inspect.signature(verify._event_order).parameters["seam"].kind is inspect.Parameter.KEYWORD_ONLY
```

(`corpus_at`, `epoch`, `registry`, `inspect`, `science_root` and `_operation_lock_for` are already imported at the top of the module. `World.retire(corpus_id) -> StatusRecord` is the retirement act, `registry.py:298`.)

- [ ] **Step 2: Run to verify it fails**

```bash
cd python && uv run --frozen pytest tests/test_world_log_audit.py -q -k "EventLevelRelation or event_order_is_a_wrapper"
```
Expected: `AttributeError: module 'beliefs.world.verify' has no attribute '_event_order'` (and the wrapper test's `AttributeError` on `science_root._event_order`).

- [ ] **Step 3: The relation** — append to `python/src/beliefs/world/verify.py` after `_publishes`:

```python
# --- the event-level relation (cut 36) ---------------------------------------


def _event_order(config: WorldConfig, a: Event, b: Event, *, seam: LogSeam) -> Order:
    """Does `a` precede `b`, `b` precede `a`, or neither — at the granularity
    the log design §7 states.

    Same chain: by ancestry, after both moments resolve. Cross chain: by the
    witness predicate `_witnessed` over the world's retained epochs, and
    **witness-asymmetrically** — `a-precedes-b` exactly when `W(a, b)` holds
    and `W(b, a)` does not. Two overlapping builds can witness both
    directions; that is §7's build-window residual, and the answer is then
    `unordered`, never a positive claim (spec decision 5).

    **Reads, in lock order.** Under the world lock: inspect the world chain
    *first* — the inspection completes recovery, and recovery can rewrite the
    registry files the scan reads next — then scan the registry and resolve
    each corpus's carrier, and, for a cross-chain question only, open every
    retained epoch. A same-chain question opens no epoch and never consults
    the world view's classification, so a malformed world chain or retained
    epoch cannot defeat corpus ancestry (decision 4). Then, with the world lock
    released, each corpus chain is inspected once under its own operation
    lock, in sorted `corpus_id` order and never nested. The world chain is
    inspected exactly once per call, and every ordered-cuts question is asked
    of that one view through `_ordered_by_descent` (decision 7).

    **Refusals are the caller's facts; `unordered` is the evidence's.** An
    unadmitted corpus, an unresolvable carrier and a digest absent from a
    well-formed chain refuse. A malformed chain, an unplaceable or mismatched
    anchor, a pending or rolled-back moment, and the absence of a witness
    answer `unordered`. `EpochMalformed`, `BuildHold` and `LogEvidenceRefused`
    from the reads propagate untranslated: the relation refused to judge.
    """
    from beliefs.world import epoch, registry

    if type(a) is not Event or type(b) is not Event:
        raise TypeError("event_order takes two Event values")
    cross_chain = a.corpus_id != b.corpus_id
    with seam.world_lock(config.world_root):
        world_view = seam.inspect_registered(config.world_root)
        registry_view = registry._scan_registry(config.world_root)
        carriers = {
            corpus_id: _event_carrier(config, registry_view, corpus_id)
            for corpus_id in sorted({a.corpus_id, b.corpus_id})
        }
        epochs: tuple[Epoch, ...] = ()
        if cross_chain:
            epochs = tuple(
                epoch._locked_open_epoch(config.world_root, identity)
                for identity in epoch._retained_identities_locked(config.world_root)
            )
    views: dict[str, WellFormedView] = {}
    for corpus_id in sorted(carriers):
        with seam.corpus_lock(carriers[corpus_id]):
            view = seam.inspect_registered(carriers[corpus_id])
        if type(view) is not WellFormedView:
            # Spec §4.3 step 2: the first chain that can place nothing answers
            # at once — the other corpus's lock is never taken for it.
            return "unordered"
        views[corpus_id] = view
    view_a = views[a.corpus_id]
    view_b = views[b.corpus_id]
    moment_a = moment(view_a, a.digest)
    moment_b = moment(view_b, b.digest)
    if moment_a is None or moment_b is None:
        return "unordered"
    if not cross_chain:
        if moment_a == moment_b:
            return "unordered"
        return "a-precedes-b" if moment_a < moment_b else "b-precedes-a"
    if type(world_view) is not WellFormedView:
        return "unordered"
    first = _Placed(a.corpus_id, view_a, moment_a)
    second = _Placed(b.corpus_id, view_b, moment_b)
    w_ab = _witnessed(world_view, epochs, seam.absent_state, first, second)
    w_ba = _witnessed(world_view, epochs, seam.absent_state, second, first)
    if w_ab and not w_ba:
        return "a-precedes-b"
    if w_ba and not w_ab:
        return "b-precedes-a"
    return "unordered"


@dataclass(frozen=True)
class _Placed:
    """One event, resolved: its corpus, its inspected chain, its moment."""

    corpus_id: str
    view: WellFormedView
    moment: int


def _witnessed(
    world_view: WellFormedView,
    epochs: tuple[Epoch, ...],
    absent_state: object,
    first: _Placed,
    second: _Placed,
) -> bool:
    """`W(first, second)`: some ordered pair of retained epochs E1, E2 has E1
    containing `first` and excluding `second`, E2 containing `second`, and
    both cuts placing both chains (spec §4.2, decision 6). E2 orders after E1
    by `_ordered_by_descent` over the one captured world view."""
    for e1 in epochs:
        on_first = _placement(first.view, e1, first.corpus_id)
        on_second = _placement(second.view, e1, second.corpus_id)
        if on_first is None or on_second is None:
            continue
        if not (contains(on_first, first.moment) and excludes(on_second, second.moment)):
            continue
        for e2 in epochs:
            if e2.packaging_identity == e1.packaging_identity:
                continue
            built_from = e2.world_anchor.head_digest
            if _ordered_by_descent(world_view, e1.packaging_identity, built_from, absent_state) != "ordered":
                continue
            later_first = _placement(first.view, e2, first.corpus_id)
            later_second = _placement(second.view, e2, second.corpus_id)
            if later_first is None or later_second is None:
                continue
            if contains(later_second, second.moment):
                return True
    return False


def _placement(view: WellFormedView, epoch_: Epoch, corpus_id: str) -> Placement | None:
    """The cut's placement of this chain, or `None` where the epoch carries no
    anchor for the corpus — the coverage half of decision 6; `place` decides
    the genesis and head halves."""
    for anchor in epoch_.anchors:
        if anchor.subject == corpus_id:
            return place(view, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest)
    return None


def _event_carrier(config: WorldConfig, registry_view: RegistryView, corpus_id: str) -> Path:
    """The one configured root whose manifest claims `corpus_id`, for an
    admitted corpus — terminal status permitted, since a retired corpus's
    chain still carries its events (decision 8)."""
    from beliefs.world import registry

    if not any(record.corpus_id == corpus_id for record in registry_view.admissions):
        raise EventCorpusUnknown(f"{corpus_id}: this world has not admitted that corpus")
    roots = registry._carrier_roots(config, corpus_id)
    if len(roots) != 1:
        detail = ",".join(sorted(str(root) for root in roots)) or "none"
        raise EventCorpusUnresolvable(
            f"{corpus_id}: exactly one configured carrier root is required; carriers={detail}"
        )
    return roots[0]
```

Imports to add at the top of `verify.py`: `EventCorpusUnknown`, `EventCorpusUnresolvable` in the `beliefs.errors` block; `from beliefs.world.events import Event, Order, Placement, contains, excludes, moment, place`; under `TYPE_CHECKING`, `from beliefs.world.epoch import Epoch` and `from beliefs.world.registry import RegistryView` (beside the existing `AdmissionRecord, ReplicaOf, World, WorldConfig`). Add `"Order"` beside `"Ordering"` in `__all__`.

- [ ] **Step 4: The wrapper** — in `python/src/beliefs/root.py`: add `_event_order` to the `from beliefs.world.verify import (...)` block (alphabetically after `_epochs_ordered`); add `from beliefs.world.events import Event, Order` beside the other `beliefs.world` imports; add `"Event"`, `"Order"` and `"event_order"` to `__all__` (sorted, as the list is); after `epochs_ordered`:

```python
def event_order(config: WorldConfig, a: Event, b: Event) -> Order:
    """Whether `a` precedes `b`, `b` precedes `a`, or neither — the event-level
    relation of the log design §7, over captured corpus heads.

    Same chain by ancestry; across chains only through world-ancestry-ordered
    cuts, witness-asymmetrically (`a-precedes-b` iff `W(a, b)` and not
    `W(b, a)`), `unordered` the default answer. Epoch sequence numbers are read
    by nothing. Cut 36; spec `2026-09-21-event-level-l8-design.md`.
    """
    return _event_order(config, a, b, seam=_log_seam())
```

- [ ] **Step 5: Run to verify it passes, and the boundary gates**

```bash
cd python && uv run --frozen pytest tests/test_world_log_audit.py tests/test_world_events.py tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: all pass; ruff and pyright clean. If `test_capability_boundary.py` flags `world/events.py` or the `verify.py` additions for naming an engine command, the name it flags is one from `ENGINE_COMMANDS` — rename the local; never import.

- [ ] **Step 6: `just test-fast`**

```bash
cd ~/d/beliefs/.worktrees/event-level-l8 && just test-fast 2>&1 | tail -5
```
Expected: green summary line. Record the count.

- [ ] **Step 7: Commit**

```bash
tasks check && git add python/src/beliefs/world/verify.py python/src/beliefs/root.py python/tests/test_world_log_audit.py
git commit -m "feat(verify): the event-level relation over captured corpus heads — L8"
```

---

### Task 4: The acceptance module — real worlds on the certified volume

**Files:**
- Create: `python/tests/acceptance/test_event_order_acceptance.py`

**Interfaces:**
- Consumes: `root.event_order`, `root.Event`, `root.log_seam`, `root.epochs_ordered`, `root.init_corpus_root`, `root.init_world_root`, `root.open_corpus`, `root.open_world`, `root.metadata_root_for`, `root.durable_operation_port`, `root.anchor_heads`, `root.audit_log`, `root.admit_arrival`, `root.replicate_root`, `root._fork_corpus_genesis_payload`; `epoch.build_epoch` through `test_world_receipts.publish` and `hold_shipped`; `epoch._root_state_for` (the gate site for the overlapping schedule); the `work_directory` fixture (`acceptance/conftest.py`); `fixtures_cut3.TESTING_PROFILE`, `TESTING_CLAIM`, `spec_draft`, `spec_rules`, `run_assessment`; `test_world_log_audit`'s `ABSENT`, `chain`, `digest`, `registration`, `settlement`, `state`; `test_world_log_codecs.CHAIN_LEAF` is `atoms.core.scratch.CHAIN_LEAF` (the chain directory leaf, `.#~chain`).
- Produces: exactly sixteen `test_<unit>_…_durably` functions, one per declaration unit, named as Task 5's `UNIT_CHECKS` lists them.

**Mechanics this module relies on, each verified by probe on 2026-09-21 before this plan was written:** `writer.operations.add(node)` appends an operation intent, a registration and a settlement (`OperationCommit.intent_digest`, `.entry_digest`); `adopt_manifest` appends a registration and settlement only; a DOI needs a 4–9 digit prefix (`10.1234/…`); unlinking chain leaves after a settlement leaves a `WellFormedView` in registered mode; replacing a live corpus's `CHAIN_LEAF` directory with one fork-genesis entry and then writing yields a well-formed chain under the new genesis; two builds with no write between are distinct epochs; a carrier missing `anchors.yaml` raises `EpochMalformed` from the retained scan even when renamed inside `epochs/`, and moving it out of `epochs/` clears it; a flipped byte in an interior world-chain leaf reads `MalformedView(name-mismatch)`.

- [ ] **Step 1: The module head and the fixture**

```python
"""Cut 36 acceptance: the event-level relation over real worlds.

Every test names its declaration unit. The worlds are real — `init_world_root`,
admitted corpora, `build_epoch` — and the chains are the engine's, read through
`root.log_seam()`. Two units are stand-ins and say so: L8-i fabricates the one
corpus view it hands the relation (a rollback needs a halted backend; cut 8
fabricated these by entry class too), and BI-3 alters an anchor, never a view.
"""

from __future__ import annotations

import inspect
import shutil
import threading
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp

import pytest
from atoms.chain.model import GenesisEntry, encode_entry, entry_digest
from atoms.core.scratch import CHAIN_LEAF
from authority import FULL
from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, run_assessment, spec_draft, spec_rules
from profiles import pins_for
from test_world_log_audit import ABSENT, chain, digest, registration, settlement, state
from test_world_receipts import hold_shipped, publish

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import _operation_lock_for
from beliefs.errors import (
    BuildHold,
    EpochMalformed,
    EventCorpusUnknown,
    EventCorpusUnresolvable,
    EventUnknown,
    SubjectMismatch,
)
from beliefs.intents.shapes import DecodedIntent, decode_intent
from beliefs.projection import project_claim
from beliefs.report import AssessmentRunIntent
from beliefs.root import (
    Event,
    admit_arrival,
    anchor_heads,
    audit_log,
    durable_operation_port,
    epochs_ordered,
    event_order,
    init_corpus_root,
    init_world_root,
    log_seam,
    metadata_root_for,
    open_corpus,
    open_world,
    replicate_root,
)
from beliefs.spec import freeze
from beliefs.world import Fresh, ReplicaOf, WorldConfig, anchors, epoch, events, registry, verify
from beliefs.world.logmodel import (
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)


def view_of(root: Path) -> WellFormedView:
    view = log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return view


def settlement_of(root: Path, registration_digest: str) -> SettledEntryView:
    (found,) = [
        e for e in view_of(root).entries if type(e) is SettledEntryView and e.registration == registration_digest
    ]
    return found


def chain_dir(root: Path) -> Path:
    return root / CHAIN_LEAF


def truncate_after(root: Path, keep_through: str) -> tuple[str, ...]:
    """Unlink every chain leaf after `keep_through`: a valid prefix (L3's arm)."""
    digests = [e.digest for e in view_of(root).entries]
    removed = tuple(digests[digests.index(keep_through) + 1 :])
    for entry_digest_ in removed:
        (chain_dir(root) / entry_digest_).unlink()
    assert type(log_seam().inspect_registered(root)) is WellFormedView
    return removed


def replace_chain_under_another_fork_genesis(root: Path) -> None:
    """Cut 9's L4u2 construction on a live carrier: the chain directory becomes
    one fork-genesis entry naming another parent, same subject (the manifest
    is untouched). The next write appends under the new genesis."""
    other = encode_entry(None, GenesisEntry(science_root._fork_corpus_genesis_payload(("d" * 64, "c" * 64)), ()))
    shutil.rmtree(chain_dir(root))
    chain_dir(root).mkdir()
    (chain_dir(root) / entry_digest(other)).write_bytes(other)


def rewrite_an_interior_entry(root: Path) -> None:
    """Flip one byte of the first registration's leaf: `MalformedView`."""
    interior = [e for e in view_of(root).entries if type(e) is RegisteredEntryView][0]
    leaf = chain_dir(root) / interior.digest
    data = bytearray(leaf.read_bytes())
    data[len(data) // 2] ^= 0x01
    leaf.write_bytes(bytes(data))
    assert type(log_seam().inspect_registered(root)) is MalformedView


@pytest.fixture()
def world(work_directory):
    """Two corpora A < B (sorted by id) under `TESTING_PROFILE` — the spec
    draft's estimand is typed against `testing/affects` — one world, nothing
    published yet. Each corpus carries a target proposition so a frozen spec
    can be stored in it."""
    roots: list[Path] = []
    scratch = Path(mkdtemp(prefix="cut36-scratch-", dir=work_directory))
    roots.append(scratch)

    def corpus():
        path = Path(mkdtemp(prefix="cut36-corpus-", dir=work_directory))
        roots.append(path)
        init_corpus_root(path, authority=FULL)
        writer = open_corpus(path, authority=FULL, profile=TESTING_PROFILE)
        manifest = writer.adopt_manifest(profile=pins_for(TESTING_PROFILE))
        # Distinct per corpus: two corpora carrying one `proposition:target` address
        # would refuse every build covering both with `AddressMapConflict` (W8b).
        target = writer.add(
            stored.proposition_node(f"target-{manifest.corpus_id}", title="target", claim=project_claim(TESTING_CLAIM))
        )
        return manifest.corpus_id, path, writer, target.id

    class Built:
        def __init__(self):
            first, second = corpus(), corpus()
            (self.a, self.alpha, self.writer_a, self.target_a), (self.b, self.beta, self.writer_b, self.target_b) = sorted(
                (first, second), key=lambda c: c[0]
            )
            path = Path(mkdtemp(prefix="cut36-world-", dir=work_directory))
            roots.append(path)
            self.config = WorldConfig(path, "c" * 32, (self.alpha, self.beta))
            init_world_root(self.config, authority=FULL)
            self.world = open_world(self.config, authority=FULL)
            self.world.admit(self.alpha, provenance=Fresh())
            self.world.admit(self.beta, provenance=Fresh())
            self.bindings = hold_shipped(self.world)
            self.scratch = scratch
            self.freezes = 0

        def build(self, *corpus_ids: str) -> str:
            return publish(self.world, corpus_ids or (self.a, self.b), self.bindings).packaging_identity

        def freeze(self) -> Event:
            """The spec-freeze transition L8 names: a frozen analysis spec stored
            in A through an operation write. The event is the registration; its
            moment is the committed settlement."""
            self.freezes += 1
            spec = freeze(spec_draft(target=self.target_a, method=f"fit the model {self.freezes}"), held_rules=spec_rules())
            commit = self.writer_a.operations.add(stored.analysis_spec_node(spec))
            assert type(view_of(self.alpha).entries[-1]) is SettledEntryView
            assert settlement_of(self.alpha, commit.entry_digest).committed
            return Event(self.a, commit.entry_digest)

        def run_intent(self) -> Event:
            """The run intent L8 names, through the real assessment-run boundary
            over B's durable port. The intent is appended before the run
            executes, so it stands whether the run mints or is refused; the
            event is the intent entry and its payload decodes to an
            `AssessmentRunIntent`."""
            port = durable_operation_port(self.beta, FULL, profile=TESTING_PROFILE)
            work = Path(mkdtemp(prefix="run-", dir=self.scratch))
            run_assessment(work, port=port)
            entry = [e for e in view_of(self.beta).entries if type(e) is IntentEntryView][-1]
            decoded = decode_intent(entry.digest, entry.payload)
            assert type(decoded) is DecodedIntent and type(decoded.value) is AssessmentRunIntent
            return Event(self.b, entry.digest)

        def intent(self) -> Event:
            """An operation intent in B — cheap, real, and the same entry class
            as a run intent. The relation is kind-agnostic (spec decision 1);
            L8-a exercises the row's own pair through `run_intent`."""
            commit = self.writer_b.operations.add(
                stored.source_node(title="b", identifiers={"doi": f"10.1234/b{len(view_of(self.beta).entries)}"})
            )
            assert type(next(e for e in view_of(self.beta).entries if e.digest == commit.intent_digest)) is IntentEntryView
            return Event(self.b, commit.intent_digest)

        def freeze_in_b(self) -> Event:
            spec = freeze(spec_draft(target=self.target_b, method=f"fit the model b{len(view_of(self.beta).entries)}"), held_rules=spec_rules())
            return Event(self.b, self.writer_b.operations.add(stored.analysis_spec_node(spec)).entry_digest)

        def order(self, x: Event, y: Event) -> str:
            return event_order(self.config, x, y)

        def anchor_for(self, identity: str, corpus_id: str):
            with registry._world_lock_for(self.config.world_root):
                opened = epoch._locked_open_epoch(self.config.world_root, identity)
            (anchor,) = [x for x in opened.anchors if x.subject == corpus_id]
            return anchor

        def recorded_world_head(self, identity: str) -> str:
            with registry._world_lock_for(self.config.world_root):
                return epoch._locked_open_epoch(self.config.world_root, identity).world_anchor.head_digest

    built = Built()
    try:
        yield built
    finally:
        for path in roots:
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)


def unordered_both_ways(built, x: Event, y: Event) -> None:
    assert built.order(x, y) == "unordered" and built.order(y, x) == "unordered"


def seam_with_view(root: Path, view) -> verify.LogSeam:
    """The production seam, answering `view` for `root` and the engine's
    inspection for every other root."""
    production = log_seam()
    return replace(
        production,
        inspect_registered=lambda target: view if Path(target).resolve() == root.resolve() else production.inspect_registered(target),
    )
```

`spec_draft(**overrides)` updates a fixed field dict (`fixtures_cut3.py:115`); `title` is not a field, so distinguish freezes by `method=f"fit the model {self.freezes}"` instead of `title=…` in `freeze` and `freeze_in_b` — the stored id is `analysis-spec:<identity>`, and a second identical spec would be a duplicate add. Two distinct freezes in one corpus are required by L8-h, L8-d and L8-g.

- [ ] **Step 2: The overlapping-build schedule** — one helper, spec §4.3's table made executable. The gate is `epoch._root_state_for`, which `_capture` calls **before** taking each corpus's capture hold, so the paused build holds no lock while the main thread writes and builds:

```python
def overlapping_builds(world) -> tuple[Event, Event, str, str, str, str]:
    """Spec §4.3: E3 preflights at h0 and captures A; `a` commits; E1
    preflights at h0, captures A then B, publishes; `b` appends; E3 captures B
    and publishes; E2 and E4 follow. Returns (a, b, e1, e2, e3, e4)."""
    reached_b = threading.Event()
    release_b = threading.Event()
    e3_thread_id: list[int] = []
    original = epoch._root_state_for

    def gated(carrier: Path, factory):
        if threading.get_ident() in e3_thread_id and Path(carrier).resolve() == world.beta.resolve():
            reached_b.set()
            assert release_b.wait(60), "the gated build was never released"
        return original(carrier, factory)

    outcome: dict[str, object] = {}

    def build_e3() -> None:
        e3_thread_id.append(threading.get_ident())
        try:
            outcome["e3"] = world.build()
        except BaseException as caught:  # surfaced by the join below
            outcome["error"] = caught

    epoch._root_state_for = gated  # restored in the finally
    thread = threading.Thread(target=build_e3, name="cut36-e3")
    try:
        thread.start()
        assert reached_b.wait(60), "E3 never reached B's capture"
        a = world.freeze()          # after E3's A capture, before E1's
        e1 = world.build()          # preflight at h0: nothing is published yet
        b = world.intent()          # after E1's B capture, before E3's
    finally:
        # Whatever failed above, the gated thread is released and joined
        # before the fixture tears the roots down under it.
        release_b.set()
        thread.join(120)
        epoch._root_state_for = original
    assert not thread.is_alive() and "error" not in outcome, outcome.get("error")
    e3 = str(outcome["e3"])
    e2 = world.build()
    e4 = world.build()
    # The schedule's own obligations, asserted rather than assumed.
    assert world.recorded_world_head(e1) == world.recorded_world_head(e3)  # both built from h0
    assert epochs_ordered(world.config, e1, e3) == "unordered" and epochs_ordered(world.config, e3, e1) == "unordered"
    assert epochs_ordered(world.config, e1, e2) == "ordered" and epochs_ordered(world.config, e3, e4) == "ordered"
    live_a, live_b = view_of(world.alpha), view_of(world.beta)
    a_moment, b_moment = events.moment(live_a, a.digest), events.moment(live_b, b.digest)
    assert a_moment is not None and b_moment is not None
    for identity, on_a, on_b in ((e1, True, False), (e3, False, True)):
        pa = events.place(live_a, genesis_digest=world.anchor_for(identity, world.a).genesis_digest, head_digest=world.anchor_for(identity, world.a).head_digest)
        pb = events.place(live_b, genesis_digest=world.anchor_for(identity, world.b).genesis_digest, head_digest=world.anchor_for(identity, world.b).head_digest)
        assert pa is not None and pb is not None
        assert events.contains(pa, a_moment) is on_a and events.contains(pb, b_moment) is on_b
    return a, b, e1, e2, e3, e4
```

`_root_state_for(root: Path, executor_factory) -> _RootState` (`corpus.py:767`); `epoch.py` imports it by name (`from beliefs.corpus import … _root_state_for …`), so the gate is installed on `epoch._root_state_for`, the binding `_capture` calls. `monkeypatch` is not used because the gate must be installed and removed around a thread the fixture does not own; the `finally` restores it.

- [ ] **Step 3: The sixteen units**

```python
def test_l8a_a_freeze_before_a_run_intent_across_ordered_cuts_orders_and_is_antisymmetric_durably(world):
    a = world.freeze()
    e1 = world.build()
    b = world.run_intent()
    e2 = world.build()
    assert epochs_ordered(world.config, e1, e2) == "ordered"
    assert world.order(a, b) == "a-precedes-b"
    assert world.order(b, a) == "b-precedes-a"


def test_l8b_co_appearance_is_unordered_and_later_cuts_holding_both_do_not_reverse_a_witness_durably(world):
    """Two claims, and the second is what the exclusion clause defends: with
    exclusion dropped, E2 and E3 (both holding both events) would witness
    `b` before `a` too, and the answer would collapse to `unordered`."""
    a, b = world.freeze(), world.intent()
    world.build()
    world.build()
    unordered_both_ways(world, a, b)
    c = world.freeze()
    world.build()
    d = world.intent()
    world.build()
    world.build()
    assert world.order(c, d) == "a-precedes-b" and world.order(d, c) == "b-precedes-a"


def test_l8c_epoch_sequence_numbers_are_read_by_nothing_durably(world):
    assert [name for name in dir(epoch.Epoch) if "sequence" in name] == []
    for core in (verify._ordered_by_descent, verify._witnessed, verify._event_order):
        code, _docstring, rest = inspect.getsource(core).split('"""', 2)
        assert "sequence" not in code + rest, core.__name__


def test_l8d_a_cut_covering_one_corpus_establishes_nothing_durably(world):
    a = world.freeze()
    world.build(world.a)          # A only: no anchor for B
    b = world.intent()
    world.build(world.a)          # A only again
    unordered_both_ways(world, a, b)
    c = world.freeze()
    world.build()                 # both: the covering pair begins
    d = world.intent()
    world.build()
    assert world.order(c, d) == "a-precedes-b"
    unordered_both_ways(world, a, b)  # b was in every covering cut that holds a: still unwitnessed


def test_l8e_a_chain_replaced_under_another_fork_genesis_establishes_nothing_durably(world):
    a = world.freeze()
    e1 = world.build()
    b = world.intent()
    world.build()
    assert world.order(a, b) == "a-precedes-b"
    replace_chain_under_another_fork_genesis(world.alpha)
    a2 = world.freeze()            # appends under the new genesis
    e3 = world.build()             # E3 places A (new genesis) and B; holds both
    live_genesis = view_of(world.alpha).genesis.digest
    assert world.anchor_for(e3, world.a).genesis_digest == live_genesis
    assert world.anchor_for(e1, world.a).genesis_digest != live_genesis
    unordered_both_ways(world, a2, b)
    with pytest.raises(EventUnknown):
        world.order(a, b)          # the old chain's registration is gone


def test_l8f_the_double_witness_is_unordered_durably(world):
    a, b, _e1, _e2, _e3, _e4 = overlapping_builds(world)
    unordered_both_ways(world, a, b)


def test_l8g_valid_prefix_truncation_invalidates_every_witness_and_unknowns_the_removed_event_durably(world):
    a = world.freeze()
    a_settled = settlement_of(world.alpha, a.digest).digest
    later = world.freeze()         # E1's A head will sit after this
    e1 = world.build()
    b = world.intent()
    e2 = world.build()
    assert world.order(a, b) == "a-precedes-b"
    truncate_after(world.alpha, keep_through=a_settled)   # every cut's A head is now beyond the tip
    for identity in (e1, e2):
        anchor = world.anchor_for(identity, world.a)
        assert events.place(view_of(world.alpha), genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) is None
    unordered_both_ways(world, a, b)
    with pytest.raises(EventUnknown):
        world.order(later, b)


def test_l8h_same_chain_orders_by_ancestry_and_equal_moments_are_unordered_durably(world):
    first = world.freeze()
    second = world.freeze()
    assert world.order(first, second) == "a-precedes-b" and world.order(second, first) == "b-precedes-a"
    settled = Event(world.a, settlement_of(world.alpha, second.digest).digest)
    unordered_both_ways(world, second, settled)
    assert world.order(second, second) == "unordered"
    genesis = Event(world.a, view_of(world.alpha).genesis.digest)
    assert world.order(genesis, first) == "a-precedes-b"


def test_l8i_a_pending_or_rolled_back_registration_has_no_moment_durably(world):
    """Stand-in inspection for A only: the live chain plus a pending and a
    rolled-back registration, by entry class; the world and B are the engine's."""
    first = world.freeze()
    world.build()
    live = view_of(world.alpha)
    pending = registration(digest("cut36-pending"), "tx-p", (("p.md", ABSENT),), (("p.md", state("p.md")),))
    rolled = registration(digest("cut36-rolled"), "tx-r", (("r.md", ABSENT),), (("r.md", state("r.md")),))
    rolled_back = settlement(digest("cut36-rolled-settled"), rolled.digest, "tx-r", committed=False)
    fabricated = chain(live.genesis, *live.entries[1:], pending, rolled, rolled_back)
    seam = seam_with_view(world.alpha, fabricated)
    for digest_ in (pending.digest, rolled.digest, rolled_back.digest):
        assert verify._event_order(world.config, first, Event(world.a, digest_), seam=seam) == "unordered"
        assert verify._event_order(world.config, Event(world.a, digest_), first, seam=seam) == "unordered"


def test_l8j_same_chain_independence_from_a_malformed_carrier_and_world_chain_durably(world, work_directory):
    first = world.freeze()
    second = world.freeze()
    identity = world.build()
    b = world.intent()
    (world.config.world_root / "epochs" / identity / "anchors.yaml").unlink()   # a malformed retained carrier
    assert world.order(first, second) == "a-precedes-b"
    with pytest.raises(EpochMalformed):
        world.order(first, b)
    aside = Path(mkdtemp(prefix="cut36-aside-", dir=work_directory))
    shutil.move(str(world.config.world_root / "epochs" / identity), str(aside / identity))  # out of `epochs/`
    rewrite_an_interior_entry(world.config.world_root)                            # a malformed world chain
    assert world.order(first, second) == "a-precedes-b"
    assert world.order(first, b) == "unordered"
    shutil.rmtree(aside, ignore_errors=True)


def test_l8k_the_refusals_and_a_terminal_corpus_durably(world, work_directory):
    first = world.freeze()
    second = world.freeze()
    with pytest.raises(EventCorpusUnknown):
        world.order(Event("0" * 32, first.digest), second)
    with pytest.raises(EventUnknown):
        world.order(Event(world.a, world.intent().digest), second)      # B's digest asked of A
    twin = Path(mkdtemp(prefix="cut36-twin-", dir=work_directory))
    shutil.copytree(world.alpha, twin, dirs_exist_ok=True, symlinks=True)   # a second root claiming A's id
    try:
        with pytest.raises(EventCorpusUnresolvable):
            event_order(replace(world.config, corpus_roots=(*world.config.corpus_roots, twin)), first, second)
    finally:
        shutil.rmtree(twin, ignore_errors=True)
    assert event_order(replace(world.config, corpus_roots=(*world.config.corpus_roots, world.alpha)), first, second) == "a-precedes-b"
    with pytest.raises(EventCorpusUnresolvable):
        event_order(replace(world.config, corpus_roots=(world.beta,)), first, second)
    with _operation_lock_for(world.alpha).capture():
        with pytest.raises(BuildHold):
            world.order(first, second)
    world.world.retire(world.a)
    assert world.order(first, second) == "a-precedes-b"


def test_l4a_a_deleted_chain_refutes_against_its_registry_anchor_bound_by_corpus_id_durably(world):
    """Relabel unit; the cut document cites every clause of cuts 8 and 9."""
    world.freeze()
    records = anchor_heads(world.world, frozenset({world.a, world.b}))
    assert {record.subject for record in records} == {anchors.CorpusSubject(world.a), anchors.CorpusSubject(world.b)}
    shutil.rmtree(chain_dir(world.alpha))
    observers = verify.ObserverSet(tuple(verify.RegistryCarrier.from_record(record) for record in records))
    report = audit_log(world.config, anchors.CorpusSubject(world.a), world.alpha, observers, actor="alice")
    assert report.outcome == "refuted"
    assert report.observer_bound and all(world.a in label for label in report.observer_bound)  # bound to A's subject, never B's
    sibling = audit_log(world.config, anchors.CorpusSubject(world.b), world.beta, observers, actor="alice")
    assert sibling.outcome == "validated"
```

`RegistryCarrier` is factory-built: construct each with `verify.RegistryCarrier.from_record(record)` (`verify.py:665`), never the dataclass directly. `LogReport.observer_bound: tuple[str, ...]` (`verify.py:889`) is the bound-anchor label tuple; if its labels do not carry the subject id verbatim, assert instead on the refuting finding's `ref`/`detail` naming `world.a` (`grep -n "anchor-unreachable\|_absence_findings" src/beliefs/world/verify.py`).

```python
def test_l10a_a_replica_under_a_fresh_manifest_refuses_subject_mismatch_at_arrival_durably(world, work_directory):
    """Relabel unit; cut 8's L10u1 construction: replicate A, rewrite the copy's
    `corpus.yaml` to a fresh id, arrive as a replica of A."""
    world.freeze()
    copy = Path(mkdtemp(prefix="cut36-replica-", dir=work_directory)) / "copy"
    replicate_root(world.alpha, copy, authority=FULL)
    fresh_id = "f" * 32
    manifest = registry.load_manifest(copy)
    (copy / "corpus.yaml").write_bytes(registry.manifest_bytes(replace(manifest, corpus_id=fresh_id)))
    try:
        with pytest.raises(SubjectMismatch):
            admit_arrival(world.world, copy, ReplicaOf(world.a), verify.ObserverSet(()))
    finally:
        shutil.rmtree(copy.parent, ignore_errors=True)
        shutil.rmtree(metadata_root_for(copy), ignore_errors=True)
```

`registry.manifest_bytes(manifest)` (`registry.py:533`) encodes the manifest; `registry.load_manifest(copy)` reads it, and `CorpusManifest` is a frozen dataclass so `replace(manifest, corpus_id=fresh_id)` is the rewrite. `admit_arrival(world, corpus_root, provenance, observers, *, history=None)` takes no `actor`; the world's authority is the actor.

```python
def test_bi1_recovery_precedes_resolution_on_both_paths_durably(world, monkeypatch):
    first, second = world.freeze(), world.freeze()
    b = world.intent()
    order: list[str] = []
    production = log_seam()
    seam = replace(
        production,
        inspect_registered=lambda root: order.append("inspect-world" if Path(root).resolve() == world.config.world_root else "inspect-corpus") or production.inspect_registered(root),
    )
    original = registry._scan_registry
    monkeypatch.setattr(registry, "_scan_registry", lambda root: order.append("scan") or original(root))
    assert verify._event_order(world.config, first, second, seam=seam) == "a-precedes-b"
    assert order[:2] == ["inspect-world", "scan"]
    order.clear()
    verify._event_order(world.config, first, b, seam=seam)
    assert order[:2] == ["inspect-world", "scan"]


def test_bi2_one_world_inspection_and_the_world_lock_released_before_sorted_unnested_corpus_locks_durably(world):
    a = world.freeze()
    world.build()
    b = world.intent()
    world.build()
    seen: list[Path] = []
    world_free: list[bool] = []
    corpus_free: list[bool] = []
    world_lock = registry._world_lock_for(world.config.world_root)
    production = log_seam()

    def inspect_registered(root: Path):
        seen.append(Path(root).resolve())
        if Path(root).resolve() != world.config.world_root:
            free = world_lock.acquire(blocking=False)
            world_free.append(free)
            if free:
                world_lock.release()
            other = world.beta if Path(root).resolve() == world.alpha.resolve() else world.alpha
            corpus_free.append(_operation_lock_for(other)._holder is None)
        return production.inspect_registered(root)

    assert verify._event_order(world.config, a, b, seam=replace(production, inspect_registered=inspect_registered)) == "a-precedes-b"
    assert seen.count(world.config.world_root) == 1
    assert world_free == [True, True]
    assert corpus_free == [True, True]
    assert seen[1:] == [world.alpha.resolve(), world.beta.resolve()]


def test_bi3_the_genesis_clause_alone_decides_a_placement_durably(world):
    """Spec §8.2 case 4, isolated on the anchor's side: a genuine well-formed
    view, the epoch's own anchor with its reachable head, only the declared
    genesis replaced."""
    world.freeze()
    identity = world.build()
    live = view_of(world.alpha)
    anchor = world.anchor_for(identity, world.a)
    assert events.place(live, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) is not None
    assert events.place(live, genesis_digest=digest("cut36-other-genesis"), head_digest=anchor.head_digest) is None
```

`OperationLock._holder` is the lock's private state (`corpus.py:397`); BI-2 reads it to assert the *other* corpus's lock is unheld while one chain is inspected — no nesting.

- [ ] **Step 4: Run on the certified volume, L8-a first**

```bash
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut36-dev uv run --frozen pytest tests/acceptance/test_event_order_acceptance.py -q -p no:cacheprovider -k l8a
```
L8-a first because `run_intent` is the one construction that crosses the run boundary over the durable port: if `run_assessment` raises from the report publication rather than returning `RunMinted | RunRefused`, record the exception in the results record §3.2 and read the intent as the fixture does (it is appended before the run). Then the whole module:

```bash
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut36-dev uv run --frozen pytest tests/acceptance/test_event_order_acceptance.py -q -p no:cacheprovider
```
Expected: 16 passed. A `CapabilityUnavailable` block is the missing export or an uncertified kernel (memory `run-the-suite-with-the-project-venv`), not a regression.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/tests/acceptance/test_event_order_acceptance.py
git commit -m "test(cut36): the event-level relation's acceptance module — L8, L4, L10"
```

---

### Task 5: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut36.py`, `python/tests/acceptance/n2_arms_cut36.py` (the re-export shim, byte-for-byte cut 35's with `35` → `36`), `python/tests/acceptance/test_n2_cut36.py`, `python/tools/cut36_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit and body digest; Task 4's test names.
- Produces: `CUT36_ARMS` (18), `DECLARATION_UNITS` (16), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS`, `PHASE_MODULES`, `TOOLS`, `ACCEPTANCE`, `PYTHON_ROOT`, `declared_accounting`.

- [ ] **Step 1: The declaration** — `python/tests/n2_arms_cut36.py` on cut 35's shape. `DECLARATION_UNITS = ("L8-a", "L8-b", "L8-c", "L8-d", "L8-e", "L8-f", "L8-g", "L8-h", "L8-i", "L8-j", "L8-k", "L4-a", "L10-a", "BI-1", "BI-2", "BI-3")`; `_MODULE = "acceptance/test_event_order_acceptance.py"`; `UNIT_CHECKS` maps each unit to its Task 4 test node; `unit_of` strips a trailing `1`/`2` from `L8-a1`, `L8-a2`, `L8-j1`, `L8-j2`. Every `before` is copied **from the tree** after Task 3 (`grep -n` the site, copy the exact lines) and checked with `source.count(before) == 1`. The eighteen arms, with the `after` each states:

| arm | module | before (the site) | after |
|---|---|---|---|
| L8-a1 | `world/verify.py` | `            built_from = e2.world_anchor.head_digest` | `            built_from = e1.world_anchor.head_digest` |
| L8-a2 | `world/verify.py` | `    return "ordered" if positions[built_from] >= positions[settlement] else "unordered"` (in `_ordered_by_descent` — after Task 2 this line occurs once) | `>` for `>=` |
| L8-b | `world/verify.py` | `        if not (contains(on_first, first.moment) and excludes(on_second, second.moment)):` | `        if not contains(on_first, first.moment):` — caught by L8-b's second claim, the witnessed pair with two later cuts holding both |
| L8-e | `world/verify.py` | `            return place(view, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest)` (in `_placement`) | `            return place(view, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) or Placement(head=len(view.entries) - 1)` |
| L8-c | `world/verify.py` | `    cross_chain = a.corpus_id != b.corpus_id` | `    sequence = 0  # an epoch sequence number, consulted\n    cross_chain = a.corpus_id != b.corpus_id` |
| L8-d | `world/verify.py` | `        if on_first is None or on_second is None:\n            continue` | `        if on_first is None:\n            continue\n        if on_second is None:\n            on_second = Placement(head=-1)` |
| L8-f | `world/verify.py` | `    if w_ab and not w_ba:` | `    if w_ab:` |
| L8-g | `world/events.py` | `    return None\n\n\ndef contains(` | `    return Placement(head=len(view.entries) - 1)\n\n\ndef contains(` |
| L8-h | `world/events.py` | `    assert type(entry) is RegisteredEntryView\n    for index, candidate` | `    assert type(entry) is RegisteredEntryView\n    return positions[digest]\n    for index, candidate` |
| L8-i | `world/events.py` | `            return index if candidate.committed else None` | `            return index` |
| L8-j1 | `world/verify.py` | `        if cross_chain:\n            epochs = tuple(` | `        if True:\n            epochs = tuple(` |
| L8-j2 | `world/verify.py` | `        epochs: tuple[Epoch, ...] = ()\n        if cross_chain:` | `        epochs: tuple[Epoch, ...] = ()\n        if cross_chain:\n          try:` … (a `try`/`except EpochMalformed: epochs = ()` around the tuple; write the exact indented block and parse it) |
| L8-k | `world/verify.py` | `    if len(roots) != 1:` | `    if len(roots) == 0:` |
| L4-a | `world/verify.py` | `        if bound:\n            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))` | `        if False:\n            return _report(...)` (same second line) |
| L10-a | `world/verify.py` | `        if manifest.corpus_id != provenance.parent_corpus_id:\n            raise SubjectMismatch(` | `        if False:\n            raise SubjectMismatch(` |
| BI-1 | `world/verify.py` | `        world_view = seam.inspect_registered(config.world_root)\n        registry_view = registry._scan_registry(config.world_root)` | the two lines swapped |
| BI-2 | `world/verify.py` | `        world_view = seam.inspect_registered(config.world_root)\n` | the line twice |
| BI-3 | `world/events.py` | `    if genesis_digest != view.genesis.digest:\n        return None` | `    if False:\n        return None` |

Homing: `L8-a1`/`L8-a2` → `L8-a`; `L8-j1`/`L8-j2` → `L8-j`; every other arm → its own unit; the guard's `homed` assertion is `{unit: 2 if unit in ("L8-a", "L8-j") else 1 for unit in DECLARATION_UNITS}`, and `{check for arm in CUT36_ARMS for check in arm.checks} == set(UNIT_CHECKS.values())` holds because every unit has an arm.

- [ ] **Step 2: The guard** — `python/tests/acceptance/test_n2_cut36.py`: copy `test_n2_cut35.py`, then: import `CUT35_ARMS` and add it to `PRIOR_ARMS`; add `"python/tests/n2_arms_cut35.py": "<short sha of the commit that last touched it — git log -1 --format=%h -- python/tests/n2_arms_cut35.py>"` to `FROZEN_PRIOR_CUT_FILES`; `FROZEN_CUT = … "2026-09-21-conformance-cut-36.md"`; `CUT36_FREEZE_COMMIT` and `CUT36_FROZEN_SHA256` from Task 0 Step 6; `FROZEN_DECLARATION = "python/tests/n2_arms_cut36.py"` and `CUT36_DECLARATION_SHA256 = sha256sum` of it once final; the inventory test asserts the sixteen units and `len(CUT36_ARMS) == 18`; `test_every_acceptance_test_the_arms_name_exists` reads `test_event_order_acceptance.py` and asserts `len(names) == len(DECLARATION_UNITS)`; the freeze test asserts `"**16 declaration units**" in current` and `'("cut35_acceptance.py",)' in current`.

- [ ] **Step 3: The runner** — `python/tools/cut36_acceptance.py`: cut 35's with `cut=36`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut36"`, `PREFIX_RUNNERS = ("cut35_acceptance.py",)`, `PHASE_MODULES = ("test_event_order_acceptance.py", "test_n2_cut36.py")`, `declared_accounting` asserting `rows == {"L8", "L4", "L10"}`, and on success:

```python
        print("guarantee rows exercised: 3 (3 newly closed: L8, L4, L10; L1 re-homed to persistence-cut, partial)", flush=True)
```

- [ ] **Step 4: The recent-cut row** — `python/tests/test_recent_cut_acceptance.py`: `import cut36_acceptance as cut36`; add `(cut36, 36, (18, 16, 3))` and id `"cut36"` to the parametrization; add

```python
    if cut == 36:
        assert "guarantee rows exercised: 3 (3 newly closed: L8, L4, L10; L1 re-homed to persistence-cut, partial)" in output
```

- [ ] **Step 5: Guard green, then the cut on the certified volume**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut36-dev uv run --frozen pytest tests/acceptance/test_n2_cut36.py -q -p no:cacheprovider -k "not fails_under_its_own_sabotage"
```
Expected: green. Then the full N2 audit and the chained runner, detached (memory `long-gates-need-setsid-nohup`; the chain cut 35 → 17 is long):

```bash
cd ~/d/beliefs/.worktrees/event-level-l8/python
export SCIENCE_MM30_ROOT=~/d/beliefs/.work/reproduction/mm30
for n in $(seq 4 36); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup uv run --frozen python tools/cut36_acceptance.py > ~/d/beliefs/.work/acceptance/cut36-runner.log 2>&1 &
```
Read the log when it exits; expected tail: three `[cut36 phase n/3]` lines, `declared arms: 18 (= 16 declaration units; 3 guarantee rows)`, the rows-exercised line, exit 0. Every arm `sound`; every check `resolved`. A `stale` verdict means a `before` no longer matches — fix the declaration (Step 1), never the source.

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/tests/n2_arms_cut36.py python/tests/acceptance/n2_arms_cut36.py python/tests/acceptance/test_n2_cut36.py python/tools/cut36_acceptance.py python/tests/test_recent_cut_acceptance.py
git commit -m "test(cut36): N2 declarations, guard, runner and the recent-cut row — L8, L4, L10"
```

---

### Task 6: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §15)

- [ ] **Step 1: Run the driver as cut 35's Task 7 did** — `sed -n '/### Task 7/,/### Task 8/p' docs/superpowers/plans/2026-09-20-url-retrieval.md` for the exact command and the `state.json` fields read. Nothing is recreated or moved aside: no contract succeeded; the relation is read by no driver step.

- [ ] **Step 2: Append §15** — "§15 Cut 36 (2026-09-21): read in place; the same `NoBelief` answer; `state.json` byte-identical; the event-level relation is exercised only by the acceptance module — mm30's world has one corpus chain and its epochs order no cross-chain pair."

- [ ] **Step 3: Commit**

```bash
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md
git commit -m "docs(reproduction): re-run under event-level L8; nothing moves"
```

---

### Task 7: The results record, the re-rank, and the amendments

**Files:**
- Create: `docs/plans/2026-09-21-conformance-cut-36-results.md`
- Modify: `docs/designs/2026-09-21-conformance-cut-36.md` (`**Status:**` only), the spec (`**Status:**`), `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `python/tools/roadmap_status.py`, `docs/guide/contracts-and-adoption.md`, `README.md`, `docs/designs/2026-08-03-tamper-evident-log-design.md`, `docs/designs/2026-08-22-log-verification-design.md`, `docs/guide/open-questions.md`, tasks

- [ ] **Step 1: The results record** on cut 35's shape (`docs/plans/2026-09-20-conformance-cut-35-results.md`): §1 what ran (both summary lines verbatim from the runner log; the per-unit table, 18 arms over 16 units); §2 accounting (L8, L4, L10 closed; L1 re-homed to `persistence-cut`, partial; **186 of 216**); §3 evidence — corrections carried by the cut document; deviations from the plan, every "read at freeze" choice; limitations found at review; §4 the reproduction (§15); §5 `## Remaining boundary` — must name L1 (the ledger guard reads its labels), T2's two kinds, T7's cross-root case, and the open question filed; §6 main integration (filled at merge); §7 execution rulings.

- [ ] **Step 2: `roadmap_status.py`** — add `36: ("conformance-cut-36-results §2", "L8, L4, L10", ""),` after the cut-35 entry (an empty partial list; check how the tool spells "none" by reading the entries for a cut with no partial rows, e.g. `grep -n '"")' tools/roadmap_status.py`, and match). Regenerate Appendix A: `cd python && uv run --frozen python tools/roadmap_status.py`; expected `Closed 186 of 216; open 30.`

- [ ] **Step 3: Ledger and roadmap** — the ledger's `Current state`: a new built bullet for the event-level relation; `event-level-l8` and `log-remainder` leave the table; the `persistence-cut` row becomes "X2's persistence-cut arm; L1's kill-at-stage and settlement-persistence arms (both terminal outcomes)"; the summary names cut 36; 186 of 216. The roadmap, rewritten whole: `**Ranked at:** cut 36, against the ledger's Current state (2026-09-21)`; a `**Cut 36 (2026-09-21) discharges event-level L8 and closes the boundary**` paragraph in the sequence (re-ranks nothing on the path; off-path row 1 discharged, later rows renumber; `act-report-remainder` becomes the `world-read` lane's head; L1 moves from `log-remainder` to `persistence-cut`); the boundary index loses `event-level-l8` and `log-remainder` and `persistence-cut`'s rows gain L1; tier 1 off-path rows renumbered (`l13-preimage` 1, `act-report-remainder` 2, `contract-cut` 3); the ride-along table becomes "none"; the lane table's `world-read` row: "`act-report-remainder` → `publish`", status "off the path at its head; event-level L8 discharged at cut 36"; Appendix A pasted from the tool; Appendix B: the L1 row's classification becomes `persistence-cut` — tier 2, the L4, L8 and L10 rows removed. Then:

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```
Expected: green — `test_the_roadmap_and_ledger_name_the_same_boundaries`, `test_the_ledger_summary_names_the_newest_remaining_boundary` and `test_the_newest_cut_document_says_it_is_discharged` now read cut 36.

- [ ] **Step 4: Guide, README, the design amendments, open questions** — `docs/guide/contracts-and-adoption.md`: the cut-36 line as discharged, "Thirty-two conformance cuts" (count the discharged ones: `ls docs/plans | grep -c "conformance-cut-.*-results"`), the totals; `README.md`: "through **cut 36**", the table row's wording ("the discharged event-level-l8 cut…"), "The latest discharged boundary is cut 36". The log design: L8's row gains `*(amended 2026-09-21, cut 36 — the event-level relation is built: an event is `(corpus_id, entry_digest)`; its moment is its own position for a genesis, an intent or a committed settlement, and its **committed settlement's** position for a registration, a pending or rolled-back registration having none; a cut speaks about a chain only with an anchor whose genesis is the live genesis and whose head places, both cuts covering both corpora; the relation is witness-asymmetric — `a` precedes `b` iff some ordered pair witnesses it and none witnesses the reverse — so two overlapping builds' double witness answers `unordered`, §7's build-window residual made visible; `docs/superpowers/specs/2026-09-21-event-level-l8-design.md`)*`; §7 a dated note of the same substance beneath its text; L4 and L10 gain `*(closed 2026-09-21 at cut 36 as relabels: every clause cut 8, 9 and 10 read is cited; `../plans/2026-09-21-conformance-cut-36-results.md`)*`; L1 gains `*(amended 2026-09-21, cut 36 — the kill-at-stage and settlement-persistence arms are `persistence-cut`'s (`beliefs-3ea822`); the unspellability arm stands certified at cut 8; the row is partial there)*`. The log-verification design: §7 a dated note ("the event-level relation is built at cut 36 as `_event_order`; `_ordered_by_descent` is this predicate's pure half"); §10.7 gains `*(Closed 2026-09-21 — cut 36 …)*` on the pattern of §10.2/§10.3; §10.4's "event-level L8" clause updated. `docs/guide/open-questions.md`: under the log's section, "**Capture-order sharpening of the event-level relation** — the build captures serially in sorted `corpus_id` order, so E1's A-head containing `a` and B-head excluding `b` implies `a` before `b` in real time exactly when `A < B`; using it would order the double witness (spec §11.2). Not built; a design amendment to the log design §7 when a consumer needs it."

- [ ] **Step 5: Status lines and tasks**

The cut document's Status: `discharged 2026-09-21 on the certified volume; results: ../plans/2026-09-21-conformance-cut-36-results.md`. The spec's Status: `discharged at conformance cut 36 on 2026-09-21; results: ../../plans/2026-09-21-conformance-cut-36-results.md`.

```bash
tasks done <Task 7 child> "results record, re-rank, amendments; L1 re-homed"
tasks note beliefs-3ea822 "L1's arms formally re-homed here at cut 36 (results record §2; ledger persistence-cut row; roadmap Appendix B)."
tasks check
```

- [ ] **Step 6: Commit**

```bash
git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut36): results record, re-rank at cut 36, L1 re-homed to persistence-cut"
```

---

### Task 8: Final review, gate, merge

- [ ] **Step 1: Whole-branch review** — `superpowers:requesting-code-review` over `git diff main...HEAD`, against the spec's decisions (Global Constraints, fourth bullet) and the cut document's §5 table. Land fixes as their own commits; record each in the results record §3.2 ("Final review, following cut 35's pattern").

- [ ] **Step 2: The gate**, detached:

```bash
cd ~/d/beliefs/.worktrees/event-level-l8
export SCIENCE_MM30_ROOT=~/d/beliefs/.work/reproduction/mm30
for n in $(seq 4 36); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup just gate > ~/d/beliefs/.work/acceptance/cut36-gate.log 2>&1 &
```
Read the log at exit; expected the pytest summary line with zero failures (memory `pytest-count-claims-need-the-summary-line`) and the TypeScript suite green.

- [ ] **Step 3: Close and merge**

```bash
tasks done beliefs-77e2fc "final review, gate green, merged"
tasks done beliefs-b34652 "cut 36 discharged: event-level L8 in full, L4 and L10 relabelled, L1 re-homed to persistence-cut"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-b34652 — cut 36 discharged"
cd ~/d/beliefs && git merge --no-ff event-level-l8 -m "merge: event-level L8 — conformance cut 36"
```
Then fill the results record's §6 (main integration: the merge commit, `just check` on merged `main`) in a `docs(cut36): record merged-main verification` commit, and remove the worktree (`git worktree unlock` then `git worktree remove .worktrees/event-level-l8`).

---

## Self-review

**Spec coverage.** §3 → Task 1; §4.1 → Task 2; §4.2–4.4 → Task 3; §5 → Task 1; §8.1 → Tasks 1–3; §8.2 → Task 4 (cases 1–10 map to L8-a … BI-3; case 10, `_epochs_ordered` through the root, is `test_world_log_audit.py`'s existing wrapper test plus L8-a's positive); §8.3–8.5 → Task 5; §9 → Task 7; §10 → Tasks 0 and 7; §11 → Task 7 Step 4; AGENTS.md's two cut-plan obligations → Global Constraints and Tasks 3, 5.

**Placeholders.** Task 4 is executable as written: every helper has a body, the overlapping schedule is gated at `epoch._root_state_for` on the E3 thread, and each mechanism it relies on was probed on the certified volume before the plan was written (the note under Task 4's Interfaces). Task 5's `before` strings are the sites Task 3's code defines, copied from the tree at declaration and count-checked.

**Type consistency.** `_event_order(config, a, b, *, seam)`; `_witnessed(world_view, epochs, absent_state, first: _Placed, second: _Placed)`; `_placement(view, epoch_, corpus_id)`; `_event_carrier(config, registry_view, corpus_id)`; `_ordered_by_descent(view, e1, built_from, absent_state)`; `place(view, *, genesis_digest, head_digest)`; `moment(view, digest)`; `Event(corpus_id, digest)`; `Order`; `DefectView(kind, subject, detail)`; `World.retire(corpus_id)`; `admit_arrival(world, corpus_root, provenance: ReplicaOf, observers, *, history=None)`; `replicate_root(source_root, dest_root, *, authority)`.

## Plan review log

- **2026-09-21, round 2 (one P1, two P2; all taken):** the target proposition's id is `target-<corpus_id>`, distinct per corpus, since one `proposition:target` address in two covered corpora refuses every build with `AddressMapConflict`; L4-a constructs carriers through `RegistryCarrier.from_record`; the overlapping schedule releases and joins the E3 thread in its `finally` before the gate is restored, so a failure in E1's build never leaves the thread parked over roots the fixture is about to remove. The reviewer ran all sixteen extracted cases green on the certified volume with the first two substitutions applied in memory, and L8-b and L8-e failed under their intended sabotages.
- **2026-09-21, round 1 (two P1, five P2, three notes; all taken):** the acceptance fixture now stores a real frozen analysis spec through `writer.operations.add` (a registration) and appends a real assessment-run intent through `execute_assessment_run` over B's durable port, operation intents standing in elsewhere; L8-b gained the discriminating claim (a witnessed pair with two later cuts holding both stays ordered); L8-g invalidates every witness by truncating behind every cut's A head while keeping the queried event; L8-j moves the damaged carrier out of `epochs/` before damaging the world chain; the overlapping schedule is written in full, gated at `epoch._root_state_for` on the E3 thread with the recorded heads and placements asserted; L4-a and L10-a have executable bodies (`replicate_root(source, dest, *, authority)`, `admit_arrival` without `actor`); L8-e has its own arm at `_placement`, eighteen arms over sixteen units; the corpus loop answers `unordered` on the first non-well-formed view before the second lock is taken, with the mixed-fault unit case pinned; the two AGENTS.md paragraphs are verbatim; the WORK_ROOT sibling links are recorded; Task 8 closes its own child before the parent; the L8 amendment distinguishes a registration's settlement moment from an intent's or genesis's own position. Mechanics the fixture relies on were probed on the certified volume before the revision (the note under Task 4's Interfaces).
