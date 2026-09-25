# Session selection in the ledger — design

**Status:** draft for review, 2026-09-24; revised after review the same day (reader
currency, the append-failure tests, and the conditions for no cut). **Task:** `beliefs-1148ad`.
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

7. **The reader holds `select` to the writer's currency rule.** The writer accepts a
   `select` only for the current invocation (§4.2), so the reader accepts only a
   `select` that names the invocation current at that line. Otherwise
   `open A → open B → select A` would parse, because A is abandoned but still open,
   and a line the writer can never write would move every later act's attribution.
   The reader tracks currency exactly as the writer defines it (writer-session §3.3):
   the latest `invocation-open` makes its invocation current, and that invocation's
   `invocation-close` leaves no current invocation.

8. **No conformance cut, on one condition.** This is a small, typed amendment inside
   the session package, and it uses the ledger's existing persistence mechanism.
   Ordinary unit tests hold it, next to the cut-19 ledger tests it extends, provided
   they fault the `select` append itself at the write, the flush and the fsync. Each
   fault must leave the selection index unchanged and make the session terminal (§6).
   *Rejected:* a cut. It would cost a lane, an N2 runner and a results record for a
   line kind that adds no new persistence path.

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

Protocol rules, in `_parse`, next to the existing J7 rules. `_parse` keeps a
`current` invocation beside `opened` and `closed`: an `invocation-open` sets it to
that invocation, and an `invocation-close` naming it clears it (decision 7). A
`select` must:

- name the invocation that is `current` at its line. This excludes invocations that
  were never opened, that are closed, and that were abandoned by a later open, and it
  excludes any `select` made while no invocation is current;
- name an invocation that holds no earlier `select` (decision 5).

No `select` follows `session-close`, which the existing rule already covers.
Violations raise `LedgerMalformed` naming the line. The whole ledger is refused, so
no reader, and no `attributed_acts()` call, is ever built over a line the writer
could not have written. Reconciliation reads the refusal as `LedgerUnreadable`
evidence, as it does today.

Currency is enforced here for `select` only. The reader still accepts an `act` or an
`invocation-close` that names an open invocation that is not current, a leniency the
writer can never exercise. Closing that gap for existing line kinds is follow-up work
(§7), because it tightens what the reader accepts from ledgers already on disk.

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
5. Append the `select` line with the ledger's discipline: write, flush, `os.fsync`.
   Only after the append returns does the index record the selection. The method then
   returns the pinned address, or `None` for a clear.

A refusal at steps 1–4 appends nothing and leaves the invocation current, so science
closes it with a refusal outcome. A failure at step 5 is the ledger's `LedgerFailed`
state (writer-session decision 20). It raises `SessionLedgerFailed`, and the index
never learns the selection, so `invocation_selection` still answers `None`. The
session is terminal: every later method, including another `select_project`, raises
`SessionLedgerFailed`. The session keeps no "current project" of its own:
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
- **Protocol, writer side.** A second `select` in one invocation, and a `select`
  naming a non-current invocation (an abandoned one included), raise
  `SessionProtocolError` and append nothing.
- **Protocol, reader side.** Each of these raw ledgers raises `LedgerMalformed` naming
  the offending line:
  - `open A, open B, select A`: A is abandoned but open;
  - `open A, open B, close B, select A`: no invocation is current;
  - `open A, close A, select A`;
  - a `select` naming an unopened invocation;
  - a second `select` in one invocation;
  - a malformed `project` (unpinned, subordinate, not an address);
  - a `select` with extra or missing keys.

  For the first two, `read_ledger_evidence` returns `LedgerUnreadable`. An
  `open A, act, open B, select A, act` ledger yields no `attributed_acts()`, so the
  invalid line cannot reattribute B's act.
- **Append failure.** The `select` append is faulted at `write` (a short write), at
  `flush` and at `os.fsync`, one case each. Each raises `SessionLedgerFailed`, leaves
  `invocation_selection` at `None`, and makes the session terminal: `select_project`,
  `claim_invocation`, `close_invocation`, `scoped` and `close` all raise
  `SessionLedgerFailed` afterwards. Nothing after the fault reaches the file.
- **History.** A pre-amendment `session-open` line without `project` parses, with
  `initial_project` `None`, and `reconcile_sessions` over a directory holding one
  reports no `session-ledger-malformed`.
- **Arm staleness.** `test_arm_staleness.py` stays green: no live sabotage before-string
  moves.

## 7. What changes elsewhere

- The writer-session design gets a dated amendment section: the two line rows, §4's
  signatures, and decisions 4–6.
- The adoption ledger gets a line under the session work naming this amendment.
- A follow-up task: the reader holds `act` and `invocation-close` to the same
  currency rule (decision 7), after checking that existing ledgers on disk still
  parse.
- Science's plan for coordination part 2 (`sci-f95f8b`) consumes `select_project`,
  `invocation_selection`, `InvocationRecord.selection` and the `project` argument to
  `open_attended_session`.
