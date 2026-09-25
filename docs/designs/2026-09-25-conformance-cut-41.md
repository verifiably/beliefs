# Conformance cut 41 — live view-query evaluation

**Status:** frozen 2026-09-25, before implementation; Z1–Z5 are open
**Design:** `2026-09-24-live-query-evaluation-design.md`, approved 2026-09-24 at `d67359e` after two user reviews, amended 2026-09-25 at the plan review; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-24-live-query-evaluation.md`.
**Numbered** under roadmap concurrency rules 1 and 5: cut 41 by the user's decision of 2026-09-25, prefixing cut 40; the remote publish slice (`beliefs-3ce305`) is relabelled planned cut 42 in this commit. The freeze scan on 2026-09-25 found no cut-41-or-later document, results record or runner on any branch (`main`, `design/live-query`, `design/publish`, `origin/main`).

## 1. What this cut is

`evaluate_query` denotes a `ViewQuery` only over a `WorldReadView` opened at
a published epoch, and refuses `corpus-drifted` once any covered corpus
moves past it. No science command may publish, so a project's `next` would
refuse after the first write of a session and stay refused until an
operator republished. The queue is attention, not belief input: the reason
coordination §6.2 gives for resolving coordination records live, that no
packaging step mediates seeing your own task edit, covers seeing your own
new proposition in your project's queue.

This cut reads the live entry point that answers it:
`evaluate_live_query(world, query) -> LiveSelection` in `world/live.py`. It
covers every corpus the registry admits with no terminal status, lists the
absent ones, captures each present corpus inside its own operation-lock
`capture()` hold, serially and in sorted order, refuses a damaged corpus
`corpus-damaged`, maps addresses with publish's own `derive.address_map`,
runs the denotation `evaluate_query` shares through a private core, and
stamps the result with a `CaptureStamp` naming the per-corpus states read
inside each hold, never an epoch identity. It builds, publishes and writes
nothing. The shared denotation stays cut 28's: no arm here sabotages it.

The cut opens the `live-query` lane, off the dogfood path under roadmap
rule 6, with `world/selection.py` and `world/live.py` as its shared surface.
Under rule 3 it names two files the `world-read` lane (`publish`, planned
cut 42) also lists: `world/view.py`, which gains one private method and one
type alias, and `corpus.py`, which gains one protocol and one annotation;
the later merge resolves toward the earlier one. The lane amends no contract
oracle, so `contract-cut` gains no dependency.

Z1–Z5 open and close. The cut is **off the path**: a live selection is
attention, never belief input, so the first belief reads none.

## 2. The boundary

The files the plan's Tasks 1–5 change or create are:

- `python/src/beliefs/corpus.py`, `python/src/beliefs/world/view.py`,
  `python/src/beliefs/world/selection.py` and
  `python/src/beliefs/world/live.py` (new);
- the test modules `python/tests/test_world_selection.py` and
  `python/tests/test_live_selection.py` (new);
- `python/tests/acceptance/test_live_selection_acceptance.py` (new);
- `python/tests/n2_arms_cut41.py`,
  `python/tests/acceptance/n2_arms_cut41.py`,
  `python/tests/acceptance/test_n2_cut41.py` and
  `python/tools/cut41_acceptance.py` (new), and
  `python/tests/test_recent_cut_acceptance.py`.

Every arm's sabotage lands in `world/live.py` (§5).

Frozen declarations and cut bodies through cut 40 remain byte-exact; cut 28's W7 arms keep applying exactly once.

## 3. Selection

Twelve declaration units are selected and single-homed here, against five
rows. The quoted row text is byte-exact from
`2026-09-24-live-query-evaluation-design.md` (Z1–Z5, §6.3) at freeze.

```markdown
| **Z1** | a live evaluation covers exactly the world's admitted, non-terminal corpora, read from the registry; each present corpus is captured and each absent one is listed |
| **Z2** | each corpus's state reads and enumeration run inside its own capture hold, and a state that moves there discards the evaluation |
| **Z3** | the stamp names exactly the per-corpus states whose records were denoted |
| **Z4** | a damaged present corpus refuses the evaluation and is never omitted from it |
| **Z5** | world-record conflicts refuse with publish's classification and precedence; the scoped check covers only records outside the map |
```

The unit table is the design's §6.2, the assertion column verbatim:

| unit | row | assertion |
|---|---|---|
| Z1-a | Z1 | two present admitted corpora, each holding a record the query matches: both records are selected, `contributing` names both corpora, and the stamp's coverage is exactly those two `(corpus_id, state)` pairs |
| Z1-b | Z1 | a corpus with terminal status whose carrier is still configured and holds a matching record: it is not in the stamp's coverage and its record is never selected |
| Z1-c | Z1 | an admitted corpus whose carrier is missing is listed in `absent` and `complete` is false; an address held only there refuses `address-unknown`, never `address-not-present` |
| Z1-d | Z1 | coverage is the registry's, not an epoch's: in a world that has **never published**, the evaluation succeeds and selects its records; in a world whose current epoch covers only A, a corpus B admitted afterwards with a matching record is covered and its record selected |
| Z2-a | Z2 | a state that moves inside one corpus's capture hold (the `corpus_state_identity` monkeypatch `test_world_view.py` uses) raises `CaptureDrift`, and no selection is returned |
| Z2-b | Z2 | both state reads and the enumeration run inside that corpus's own capture hold. Wrappers around `registry.corpus_state_identity`, `ReadView.opened_at` and `ReadView.iter_stored` record the carrier's operation-lock holder at each call, the last at each record it yields as the evaluation consumes it (enumeration reads the store lazily, so a check at the open alone would miss an enumeration moved outside the hold). Every call and every yield for that carrier must see `"capture"`. A writer holding the corpus's operation lock makes the evaluation refuse `BuildContended`, because a capture never waits |
| Z3-a | Z3 | a record written into corpus A after A's hold releases and before the evaluation returns (injected at the capture of the next corpus): the new record is not selected, and the stamp names A's state from inside the hold, so selection and stamp describe the same bytes |
| Z4-a | Z4 | a present corpus with a malformed stored record refuses `corpus-damaged` naming it; the corpus is never silently left out of a returned selection |
| Z4-b | Z4 | a present corpus whose base pin disagrees refuses `corpus-damaged` naming it |
| Z5-a | Z5 | one canonical address held in two corpora **under the same uid** raises `AddressMapConflict` with code `duplicate-location`. The shared uid is what makes the scoped uniqueness check fire, so its Z5-a sabotage (running that check before `address_map`) turns the refusal into `ResolutionRefused`. A fixture with distinct uids would not see that sabotage |
| Z5-b | Z5 | one uid under two different addresses in two corpora raises `AddressMapConflict` with code `uid-corruption`, taking precedence over any duplicate location in the same capture |
| Z5-c | Z5 | a uid held by a coordination record in A and a world record in B refuses `ResolutionRefused` (W8b), and only after the address map has succeeded |

The module's other tests (the design's §6.2: live after a write, the
qualified agreement with an epoch and its counter-case, damage naming every
offender, coordination records, duplicate carriers, and no writes) live in
the same module and are not declaration units.

## 4. Accounting

The cut is frozen before its code exists, so no arm can run at the freeze.
Each of the twelve was audited on paper against its unit (plan Task 0
Step 2) and each holds; the executable audit is plan Task 5, and an arm
that fails it there is rehomed in a dated §8 supplement, never dropped.

**12 arms, 12 declaration units**, five rows; Z1–Z5 open and close;
recent-cut row `(12, 12, 5)`; 199 of 231 → 204 of 231.

## 5. N2 and acceptance obligations

| arm | module | sabotage | check |
|---|---|---|---|
| Z1-a | `world/live.py` | the capture loop skips the last covered corpus | Z1-a |
| Z1-b | `world/live.py` | the terminal-status filter is dropped from coverage: every admitted corpus id is covered | Z1-b |
| Z1-c | `world/live.py` | absent corpora are dropped from `absent` | Z1-c |
| Z1-d | `world/live.py` | the registry's coverage is filtered by the current epoch's declared coverage | Z1-d |
| Z2-a | `world/live.py` | the before/after state comparison inside the hold is dropped | Z2-a |
| Z2-b | `world/live.py` | the capture hold is bypassed (`nullcontext()` in place of `capture()`), with the before/after comparison kept | Z2-b |
| Z3-a | `world/live.py` | the stamp re-reads `corpus_state_identity` for each covered corpus when it is built, instead of keeping the in-hold state | Z3-a |
| Z4-a | `world/live.py` | a construction failure (`CorpusStateMalformed`) omits the corpus instead of collecting its damage | Z4-a |
| Z4-b | `world/live.py` | the base-pin check is skipped | Z4-b |
| Z5-a | `world/live.py` | a uniqueness check over every record runs before `address_map`, in place of the scoped check after it | Z5-a |
| Z5-b | `world/live.py` | the capture keeps one record per uid before calling `address_map` | Z5-b |
| Z5-c | `world/live.py` | the scoped uniqueness check is dropped | Z5-c |

That makes **12 arms over 12 units**, one each; each check is its unit's
function in `test_live_selection_acceptance.py`, and no check is co-cited.
Both directions are required: the check passes on the real tree and fails
under sabotage.

The runner uses `PREFIX_RUNNERS = ("cut40_acceptance.py",)`, the
highest-numbered acceptance runner at freeze (rule 5); cut 40 is
discharged, so nothing serializes this cut's discharge. It carries
`PHASE_MODULES = ("test_live_selection_acceptance.py", "test_n2_cut41.py")`.

## 6. Second reader

Check that Z2-b observes the holder at every state read, every open, and
every record `iter_stored` yields for the carrier, not just one, and that
the enumeration check reads the holder during consumption, not at generator
creation; that Z3-a's write lands after the first corpus's hold is released
and before the evaluation returns; that Z5-a's duplicate shares its uid; and
that no arm touches `world/selection.py`.

## 7. Limitations

1. **Coherence is per corpus.** Each corpus is captured in its own hold,
   and there is no cross-corpus snapshot, as there is none in a build
   (design decision 5). The stamp's per-corpus states say exactly what was
   read.
2. **An absent corpus's addresses are unknown to a live read.** A capture
   holds only what it read, so a query naming an address held only in an
   absent corpus refuses `address-unknown`, a closure step toward one is
   classified `unknown`, and `address-not-present` is never raised on this
   path (design decision 4).
3. **A live selection is attention, never belief input.** Belief reads and
   publication stay epoch-bound (the design's §5 amendment to coordination
   §6.2).
