# Session selection in the ledger — design

**Status:** draft for review, 2026-09-24. **Task:** `beliefs-1148ad`.
**Requested by:** science's coordination command set design
(`science docs/specs/2026-09-24-coordination-command-set-design.md`, §8 S2, §4.1,
§5.1) and its projects design's P3 (`science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`).
**Amends:** the writer-session design (`docs/designs/2026-09-05-writer-session-design.md`,
§3.1–§3.3, §3.5).

## 1. Problem

Science's session-bearing endpoints hold a **current project**: a coordination
`project` address, or none. It is set when the launcher opens the session and changed
only by `project-select`. The surface stores it nowhere, because a selection is not a
record and the surface owns no file. Two things need it to be durable:

- **Replay.** A `project-select` invocation's canonical report is one selection block
  (`selected: coord:<p>@<rev>` and that revision's name, or `selected: none`). It is
  rebuilt on the first response, on replay and on continuation, from what the
  invocation recorded, found by invocation id.
- **Attribution (P3).** The current project is on record at open and at every change,
  and every act's ledger entry can be attributed to the selection standing when it ran.

Today the ledger cannot say either. `LINE_KINDS` is closed
(`session/ledger.py`), `session-open` carries exactly six keys, and nothing records a
selection.

## 2. Decisions

1. **The selection is written as one pinned project address.** A selection is `null`
   or the string `coord:<project>@<revision>`: the project address, pinned to the
   revision it resolved to when it was recorded. One value carries both what science's
   report prints and what P3 attributes. The name is not stored: names are content the
   kernel never consults (coordination §3.3), and the pinned revision is immutable, so
   the name read from it is the name at selection time.
   *Rejected:* separate `address` and `revision` fields. That is two keys for one fact,
   plus a rule that both are null or neither is.

2. **The kernel resolves; the caller supplies only the address.** The session resolves
   the address through its own `CoordinationResolver` and records the revision it got.
   A caller never supplies a revision, so a line can never pin a revision that was not
   standing. Science resolves names and addresses first for its own refusals
   (`unknown-project`, `ambiguous-project`). If a revision lands between science's read
   and the kernel's, the ledger line wins, and science's report is rebuilt from it.
   *Rejected:* taking the caller's revision on trust. The ledger would then record a
   claim the kernel never checked.

3. **`session-open` gains `project`, and a new `select` line records each change.** The
   selection at open goes in the `session-open` line. Each change is a
   `{"line": "select", "invocation": <id>, "project": <selection>}` line, appended with
   the ledger's append-then-fsync discipline while the invocation is current, so it
   always comes before that invocation's close.

4. **A selection takes effect at its line.** In ledger order, the selection standing at
   any line is the latest `select` before it, or `session-open`'s value if there is
   none. This holds whether or not the selecting invocation later closes: science's
   session port appends the line and then sets the dispatcher's state, so an abandoned
   invocation's selection is live in the dispatcher and must be live in the trajectory.

5. **At most one `select` per invocation.** Science's audit admits exactly one selection
   block per `session` invocation. The writer refuses a second `select` in the same
   invocation, and the reader refuses a ledger that holds one. The kernel does not know
   science's write classes, so it does not forbid `act` and `select` lines in the same
   invocation. Decision 4 orders them.

6. **Ledgers written before this amendment stay readable.** Real `ledger.v1` files
   exist, for example science's mm30 dogfood operations root, and reconciliation reads
   every ledger in the operations root at each open. The reader accepts a
   `session-open` line without `project` and reads it as `null`: those sessions had no
   selection because the feature did not exist. That is the only historical shape
   accepted. The writer always writes the key, and every other line's key set stays
   exact.
   *Rejected:* a `ledger.v2` file name. Reconciliation would report every existing
   session as having a missing ledger.

7. **No conformance cut.** This is a small, typed amendment inside the session package.
   Ordinary unit tests hold it, next to the cut-19 ledger tests it extends. *Rejected:*
   a cut. It would cost a lane, an N2 runner and a results record for a line kind whose
   failure modes the tests in §6 already name.

## 3. The ledger lines

`session-open` gains one key:

| `line` | fields |
|---|---|
| `session-open` | `session`, `actor`, `world`, `permit`, `at` as before; `project`: `null` or a pinned project address (decision 1) |
| `select` | `invocation`; `project`: `null` or a pinned project address |

Validation, in `_validated_line`. A non-null `project` must parse as a
`CoordinationAddress` with `local` unset and `revision` set, and nothing else is
accepted. `session-open`'s key set is either the old six keys (the historical shape,
decision 6) or the old six plus `project`. `select`'s key set is exactly
`{line, invocation, project}`.

Protocol rules, in `_parse`, next to the existing J7 rules. A `select` names an
invocation that is open and not yet closed, and one that holds no earlier `select`.
No `select` follows `session-close`, which the existing rule already covers.
Violations raise `LedgerMalformed`, which reconciliation reads as `LedgerUnreadable`
evidence, as it does today.

## 4. The API

### 4.1 Opening

```python
def open_attended_session(..., project: CoordinationAddress | None = None) -> WriterSession
```

`project` must be an unpinned project address (`local` and `revision` unset), or the
call raises `ValueError`. When it is given, `coordination` must be too; otherwise the
call refuses `SessionRefused`. The address resolves through the session's resolver
before the session directory is created. No tip, a divergent tip, or a tip that is not
a `project` record refuses `ProjectNotResolvable` (with `tips` set when the address is
divergent), before anything is written. Science's launcher maps that to
`unknown-project` at start (science §5.1). `WriterSession.__init__` takes the resolved
pinned address and the resolver, and writes `project` into `session-open`.

### 4.2 Selecting

```python
def select_project(self, invocation_id: str, address: CoordinationAddress | None) -> CoordinationAddress | None
```

The method runs under the session lock, in this order:

1. Arguments. `invocation_id` must be a valid id, and `address` must be `None` or an
   unpinned project address; otherwise `ValueError`.
2. Liveness. The session must be live, or it raises the existing `SessionClosed` or
   `SessionLedgerFailed`.
3. Protocol. The id must be the current invocation, with no earlier `select` of its
   own; otherwise `SessionProtocolError` (the dispatcher's lock makes both
   unreachable).
4. Resolution. `None` needs no resolver. An address with no resolver refuses
   `CoordinationUnavailable`. An address that fails resolution refuses
   `ProjectNotResolvable`, exactly as at open.
5. Append the `select` line, record it in the index, and return the pinned address, or
   `None` for a clear.

A refusal at steps 1–4 appends nothing and leaves the invocation current, so science
closes it with a refusal outcome. The session keeps no "current project" of its own:
the dispatcher holds the live value (science §5.1), and the kernel holds its record.

```python
def invocation_selection(self, invocation_id: str) -> SelectLine | None
```

This reads the in-memory index, like `invocation_acts`. It returns `None` when the
invocation recorded no selection.

### 4.3 Reading back

- `SelectLine(invocation: str, project: CoordinationAddress | None)` is a new sealed,
  final, frozen dataclass. `project` is pinned when set.
- `InvocationRecord` gains `selection: SelectLine | None`, which is how
  `reader.invocation(id)` answers science's replay across processes.
- `LedgerReader.initial_project: CoordinationAddress | None` is `session-open`'s value.
- `LedgerReader.attributed_acts() -> tuple[tuple[ActLine, CoordinationAddress | None], ...]`
  returns every act in ledger order, each paired with the selection standing at its
  line (decision 4). This is P3's read.

## 5. What does not change

- Reconciliation. `select` lines say nothing about chains or intents, so
  `reconcile.py` ignores them. It still gains the ability to read post-amendment
  ledgers, through `_parse`.
- The `act`, `invocation-open`, `invocation-close` and `session-close` shapes, and the
  frozen cut-19 sabotage strings in `ledger.py`. None of them overlap the edited code.
- The resolver. `select_project` and `open_attended_session` call `resolve`, and
  neither needs S3's `standing`.

## 6. Testing

In `test_session_ledger.py` and the writer-session tests:

- **Round trip.** A session opened with a project records its pinned address in
  `session-open`. `select_project` to a second project, then to `None`, appends two
  `select` lines. `open_ledger_reader` returns them through `initial_project`,
  `invocation(id).selection`, and `invocation_selection` in the live session.
- **P3 trajectory.** Act, select project B, act, clear, act. `attributed_acts()` pairs
  the acts with A@rev, B@rev and `None`, in that order. An abandoned selecting
  invocation still moves the trajectory.
- **Resolution.** An unknown address, a divergent address (with `tips`), a subordinate
  address and a pinned address each refuse as §4 states, and append nothing. A clear
  needs no resolver, and an address without one refuses `CoordinationUnavailable`.
  Revising the project after selection leaves the line pinned to the old revision.
- **Open.** A project without `coordination` refuses `SessionRefused`, and an
  unresolvable one refuses `ProjectNotResolvable`. In both cases no session directory
  is created.
- **Protocol.** A second `select` in one invocation, and a `select` naming a
  non-current invocation, raise `SessionProtocolError`. On the reader side, a `select`
  naming an unopened, closed or already-selected invocation, a malformed `project`
  (unpinned, subordinate, not an address), and a `select` with extra or missing keys
  each raise `LedgerMalformed` with the line number.
- **History.** A pre-amendment `session-open` line without `project` parses, with
  `initial_project` `None`, and `reconcile_sessions` over a directory holding one
  reports no `session-ledger-malformed`.
- **Arm staleness.** `test_arm_staleness.py` stays green: no live sabotage before-string
  moves.

## 7. What changes elsewhere

- The writer-session design gets a dated amendment section: the two line rows, §4's
  signatures, and decisions 4–6.
- The adoption ledger gets a line under the session work naming this amendment.
- Science's plan for coordination part 2 (`sci-f95f8b`) consumes `select_project`,
  `invocation_selection`, `InvocationRecord.selection` and the `project` argument to
  `open_attended_session`.
