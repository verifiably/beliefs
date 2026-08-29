# Successor admission — design (the successor-admission slice)

**Date:** 2026-08-29
**Status:** approved in session
**Scope:** G4's closure. The two-class blocker derivation, the deriving
boundary `admit_spec_successor`, the widened pure core, the one named
refusal, and conformance cut 12 — the frozen acceptance boundary that reads
G4 in full, R12's boundary-mediated strengthening arm, and L7's remaining
schedulable arms. No run-boundary change, no `atoms` change, no `revise`
change.

**Inherits:** `2026-08-26-world-index-intent-boundary-design.md` §5 — the
transferred design, read across nine cut readings, whose text is this
slice's authority and whose five **opening obligations** this document
discharges (§4.6). The implementation roadmap
(`../../plans/2026-08-29-implementation-roadmap.md`) ranks this slice first
in tier 1; the adoption ledger's `Current state` table carries it as
`successor-admission`.

**Sources, read at design time:** the kernel's G4 row
(`2026-08-02-epistemic-kernel-design.md` §8 table); computation's R12 row;
the log design's L7 row (`2026-08-03-tamper-evident-log-design.md` §10);
cut 3 (`2026-08-11-conformance-cut-3.md`, the value-width G4 certification
and its three `n2_arms_cut3.py` sabotages over the core); cut 8 (chain
classification of an excised or truncated intent); cut 11
(`2026-08-27-conformance-cut-11.md`, the qualification reducer, the
captured-record evidence input, the record ceiling, the fabrication rule);
and the tree at `4110038`.

## 1. Problem

G4 — *a recorded failed replay cannot be silently orphaned* — was read in
full by cut 3 over the slice's value state: `admit_successor(candidate,
superseded, recorded_failures)` refuses an unreferenced successor when the
caller's set names the superseded spec. The tamper-evident log and the
intent boundary then widened what G4 asserts. A failed attempt is now
durable in two ways cut 3 could not see: as a verification record with a
failing verdict, or as an intent entry whose fulfillment never qualified.
Cut 11 §3.2 and ledger row 5's dated note of 2026-08-28 name G4 open at that
width, and kernel §8.7's fourth recorded-mutation consequence stays open with
it.

The gap is exactly the one intent-boundary §5 states: the core consumes
`recorded_failures` as caller-supplied value state, and the tree has no
production caller of it, so without a frozen derivation "the durable
reduction and the refusal would never compose, and G4's closure could be
claimed over a hand-built set." This slice ships the derivation and the
boundary that owns it.

## 2. Decision

Implement §5 as written, with three rulings §5 left open and one deviation
it could not foresee:

1. **Entrypoint only.** `admit_spec_successor` ships as the named
   boundary; the cut's G4 arms run through it. No production caller is
   added. The run boundary cannot call it without being told *which* spec
   a candidate supersedes — a spec with `supersedes=None` nominates nothing
   — and that nomination is a later boundary's design, not this one's
   (§9).
2. **Oversized records, the superseder-side rule** (opening obligation 5):
   an oversized verification is skipped only when a decoded, coherent
   verification names it in `supersedes`; an oversized assessment refuses
   only when a live failing verification targets it (§4.5).
3. **Cardinality, stated not bounded** (opening obligation 4): per-file
   reads stay ceiling-bounded, the aggregate is linear in record count,
   and no total I/O bound is claimed (§4.7).
4. **Home: `science/succession.py`, not `science.spec`.** §5 says the
   entrypoint is "exported from `science.spec` beside the core". It cannot
   be: `science/corpus.py` imports `science.spec`, and the derivation needs
   `science.world.verify.LogSeam`, which imports `corpus` — a top-level
   definition in `spec.py` is an import cycle. A function-local import
   would dodge the cycle and hide a disk-reading, lock-taking boundary
   inside a pure value module. The derivation therefore has its own
   module, and `science.spec` keeps only the widened pure core (§3). This
   is recorded as a dated correction to §5 at banking (§8).

Everything else — the two classes, their distinct refusal reasons, overlap
precedence, the coherent snapshot under one hold, the `verifies` join and
its cardinality rule, `science.verification.active` as the supersession
selector, the global refusal on incoherent failing evidence, the unresolved
gate, the persistence-width negative — is §5's text and is restated below
only where an implementation choice attaches to it.

## 3. The core (`science/spec.py`)

```python
def admit_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    recorded_failures: frozenset[str],
    unfinished_attempts: frozenset[str],
) -> SuccessorAdmitted | SuccessorRefused:
    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to a recorded failed replay")
    if superseded.identity in unfinished_attempts and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to an unfinished recorded attempt")
    return SuccessorAdmitted(candidate.identity)
```

- **The first body line is byte-identical to today's.** Cut 3's
  `n2_arms_cut3.py` sabotages that exact source line three times (its G4
  arms), and those arms run unchanged under every later cut. The new check
  is a second statement after it. The arms' checks in `test_spec.py` gain
  the new positional argument; that is a test edit, not a frozen-text
  edit, and cut 3's document is untouched.
- **Overlap precedence falls out of statement order.** A spec present in
  both sets refuses with the recorded-failure reason; no set is iterated,
  so the answer cannot depend on iteration order. A referencing successor
  (`candidate.supersedes == superseded.identity`) passes both checks.
- Pure and total over its arguments. It remains "G4 over the slice's value
  state" — the boundary in §4 is what stops the sets being hand-built.
- `revise` is unchanged: it mints `supersedes=original.identity` by
  construction, so a successor it produces is never refused, and its
  `recorded_failures` parameter — unused in its body, its signature pinned
  by a cut-3 check — stays as it is. Widening `revise` is not this slice's
  work.

## 4. The deriving boundary (`science/succession.py`)

```python
def admit_spec_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    *,
    seam: LogSeam,
    root: Path,
) -> SuccessorAdmitted | SuccessorRefused: ...
```

Exported from `science.succession` with `__all__ = ["admit_spec_successor"]`.
The return union is the core's pair, unchanged. The one declared exception
is `AdmissionEvidenceRefused` (§5); `LogEvidenceRefused` from either seam
call propagates untranslated, as it does from the audit — the act refused
to judge, it did not judge. Nothing is written; the act mints no record.

### 4.1 Before the root is touched

`root` is resolved and must be an openable directory. `capture_records`
returns `()` when the root cannot be opened — for the audit that is "no
records"; for admission it would be admitting over an empty surface — so
the boundary refuses `AdmissionEvidenceRefused("root unreadable", root)`
first. Candidate and superseded are values already in hand and need no
check beyond their types.

### 4.2 One hold, one pinned order

Under `seam.corpus_lock(root)` — the root's own operation lock, the very
one its writers take and the one the audit takes for a corpus subject —
**held through the admission decision**, the order is:

1. `view = seam.inspect_registered(root)` — registered mode, so recovery
   runs first and everything after is the post-recovery surface.
   `ChainView` is a union: only a `WellFormedView` has entries to qualify.
   A `MalformedView` or `AbsentView` refuses
   `AdmissionEvidenceRefused("chain not well-formed", root)` — the chain
   is the only source of class 2, and a chain that cannot be read is
   evidence that cannot be read, not evidence of absence;
2. `surface = capture_surface(root, RECORD_NAMESPACES + ("verification", "assessment"))`
   — one capture, fd-anchored, no-follow, `O_PATH`-classified,
   ceiling-plus-one per file, exactly cut 11's mechanics over five
   namespaces instead of three; `surface.uninspectable` non-empty refuses
   here;
3. the derivation (§4.3–§4.5), pure over `view` and `surface`;
4. `admit_successor(candidate, superseded, recorded_failures, unfinished_attempts)`.

Steps 3 and 4 are pure over captured values and could run outside the
hold; they do not, because §5 fixes the hold "through the admission
decision": a blocker appended between the read and the verdict must be
either consulted or sequenced after the verdict, never lost between them.
The snapshot is coherent by construction — both classes come from the one
`view` and the one `records`.

`science.world.records` gains one public function beside `capture_records`:

```python
@dataclass(frozen=True)
class CapturedSurface:
    records: tuple[tuple[str, bytes], ...]
    withheld: tuple[str, ...]      # regular files withheld for size
    unreadable: tuple[str, ...]    # leaves the act could not characterise
    uninspectable: tuple[str, ...] # directories that exist but could not be enumerated

def capture_surface(root: Path, namespaces: tuple[str, ...]) -> CapturedSurface: ...
```

`records` is exactly what `capture_records` would return over the same
namespaces. The three path lists are the descent's failures, named rather
than swallowed:

- **`withheld`** — a leaf classified as a regular file whose bounded read
  exceeded the ceiling;
- **`unreadable`** — a leaf whose `O_PATH | O_NOFOLLOW` open failed
  (classification impossible, so the act cannot even say it is not a
  record), or one classified regular whose readable open, `fstat`
  re-check or read then failed — a permission refusal, a vanished
  descriptor target, an I/O error;
- **`uninspectable`** — a namespace directory, or a subdirectory beneath
  one, whose `O_DIRECTORY | O_NOFOLLOW` open or `scandir` failed with
  anything **other than `ENOENT`**. An absent namespace is a namespace
  with no records and appears nowhere; a namespace that exists and cannot
  be enumerated is a surface the act did not see.

Leaves that classify as something other than a regular file — symlinks,
fifos, sockets — appear in none of the three: they are not records and
never were, and cut 11 certified exactly that silence. The line between
"not a record" and "could not be read" is the `O_PATH` open: a leaf the
act could classify and rejected is the former; one it could not open at
all is the latter.

Both functions share the one private descent, which now reports rather
than returns on failure; `capture_records` keeps its signature and
returns `capture_surface(root, RECORD_NAMESPACES).records`, so the log
evaluator's two callers and its certified captured surface are
byte-for-byte what they were — the evaluator never saw the failures
before and does not see them now. `RECORD_NAMESPACES` is unchanged, so
`record_layout_path` and the reducer's record lookup are unchanged too.

In the admission act, **any `uninspectable` path refuses**
`("namespace uninspectable", path)` **before the derivation** — over all
five namespaces, not two: an unenumerable `run/` hides the fulfillments
class 2 reads and `act-report/` hides class 1b's, and "concerns the
superseded spec" is undecidable over records that were never listed.

### 4.3 Class 2 and the unresolved gate, from the chain

`qualify_chain(view.entries, records, state_facts=seam.state_facts)` — cut
11's reducer, unchanged, over the run/act-report/holdings-observation
paths in `records` (the two new namespaces never match
`record_layout_path`, so their presence in `records` is inert here). For
every row whose shape is `assessment-run`, the intent's `spec_identity`
is read back from its decoded shape:

- `unresolvable` and `spec_identity == superseded.identity` →
  `AdmissionEvidenceRefused("qualification unresolved for the superseded spec", intent digest)`.
  An unresolvable intent carrying another spec blocks nothing. A run or
  act-report file in `unreadable` reaches this gate the same way an
  oversized one does today — no payload in `records`, the pointer
  unresolved — so an unreadable *fulfillment* record already refuses when
  it concerns the superseded spec and is inert otherwise; no separate
  rule is needed for those three namespaces.
- `attempt-without-recorded-outcome` → `spec_identity` joins
  `unfinished_attempts`.
- `matched` → see class 1b.
- `unrecognized`, and every operation or holdings row → nothing.

### 4.4 Class 1, from recorded failure evidence

**1a — failing verifications.** Over the two namespaces this class reads:

1. **Every** captured `verification/*.md` and `assessment/*.md` decodes
   through the **same gate `science.intents.evidence` applies to every
   captured record** — frontmatter parse, semantic stamp present and
   agreeing, id names the path, kind agrees with the id — then through
   its typed reader (`verification_value`, `assessment_value`). Any
   failure refuses `("verification unreadable", path)` or
   `("assessment unreadable", path)`. A path in `unreadable` (§4.2) is
   the same refusal: a regular file the act could not read is evidence it
   could not read. This is opening obligation 1, applied to the whole
   consulted surface rather than to the records some later step happens
   to touch: a tampered or unreadable record in a namespace the act reads
   can neither invent nor erase blocker evidence, and an index built over
   a subset of the namespace (step 3) would otherwise have no honest
   collision semantics.
2. **The index.** `Index.build` over every decoded verification and
   assessment node — live and deprecated ids, the library's collision
   refusal mapped to `("record collision", id)` — opening obligation 2.
   A withheld path's determined id (`verification:<slug>` /
   `assessment:<slug>`, §4.5) is also checked against the index: a decoded
   node claiming that id, live or deprecated, is a collision with a record
   the act cannot see, and refuses the same way.
3. **The coherence gate**, over a verification `v`: exactly one outbound
   `verifies` relation, else `("verification edge cardinality", path)`;
   its target resolves through the index to a decoded assessment, else
   `("verification target unreadable", path)` — a withheld or unreadable
   target included; `assessment_value(target).identity() == v.assessment`,
   else `("verification target mismatch", path)`. The gate runs over
   **every failing verification, and every verification whose
   `supersedes` names a failing or withheld verification**. §5 scoped it
   to failing verdicts alone, on the ground that a passing verification is
   not blocker evidence; a passing verification that *supersedes* blocker
   evidence acts on it, and an incoherent one would lift a valid block by
   its bare existence. That is a widening of §5's gate and is recorded as
   a dated correction at banking (§8). A passing verification that
   supersedes nothing failing stays outside the gate, as §5 says.
4. `science.verification.active` selects the unsuperseded set over all
   decoded verifications (opening obligation 3 — the stored-value helper,
   not the replay-value `active_verifications`). Because step 3 already
   refused every incoherent superseder of a failing record, a failing
   verification is superseded here only by a coherent one. The
   supersession relation itself is the tree's — `active` does not require
   the superseder to verify the same assessment, and `lifecycle_state`
   relies on the same rule; this act inherits it and does not tighten it.
5. Every **active failing** verification, coherent by step 3, contributes
   `assessment_value(target).spec` to `recorded_failures`.

Every refusal here is **global**: incoherent failing evidence cannot be
attributed to a spec, so a relevance scope is undecidable for exactly the
records it would exempt (§5).

**1b — qualifying `run-attempt` act-reports.** A `matched` assessment-run
row names its fulfilling registration in `fulfilled_by`, not the record
that matched — a registration can carry a qualifying run *and* a
`run-attempt` report beside undecodable siblings, and the reducer returns
the first qualifying path in `final` order without reporting which. So
the choice is factored, not repeated. `intents.reduce` gains the
complete per-registration reduction as a value:

```python
@dataclass(frozen=True)
class RegistrationReduction:
    match: tuple[str, RecordEvidence] | None  # first qualifying (path, evidence) in `final` order
    unresolved: bool                           # a record path had no payload or failed to decode
    reasons: tuple[str, ...]                   # every decoded record's mismatch reason, in order

def reduce_registration(intent, registration, settlement, records, state_facts) -> RegistrationReduction: ...
```

It is the exact body of `_qualify_one`'s inner loop over one
registration — settlement lookup, `record_layout_path` filter,
`records.get`, `decode_record`, `shapes.mismatch`, first match wins,
the same path order — returning everything that loop derives, so
`_qualify_one` becomes the outer fold over registrations with **no
second scan and no second decode**: `match` set → `matched`;
otherwise `unresolved` accumulates and `reasons` feeds the same
`REASON_PRIORITY` choice as today. Its verdicts are byte-for-byte cut
11's over cut 11's arms (a labeled declaration, §7.3). The admission act
calls the same function for each matched assessment-run row's
registration and reads `match`: when the evidence is `ReportEvidence`
with `operation == "run-attempt"`, the attempt minted no run — an
execution refusal included — and the intent's `spec_identity` joins
`recorded_failures`; when it is `RunEvidence`, a run was minted and
nothing joins. There is no re-decode and nothing to fail: the value
carries the decoded evidence the reducer's own verdict rested on.

### 4.5 Oversized records, the superseder-side rule

A file withheld by the ceiling has no payload in `records`; its path is in
`withheld` (§4.2), and the path alone decides what follows. (A path in
`unreadable` is different: it refuses outright, §4.4 step 1 — size is the
one withholding the design bounds by construction; a read that fails is
a state the act cannot characterise.)

- `verification/<slug>.md` withheld: skipped iff some decoded verification
  (active or not — the fact needed is that a superseder exists) carries
  `supersedes == "verification:<slug>"` **and passes the coherence gate**
  (§4.4 step 3 — it supersedes something the act cannot read, and the
  ruling in §2 says "decoded, coherent"); otherwise
  `("verification oversized", path)`. The layout rule
  `path == f"{kind}/{slug}.md"` is enforced on every decoded record, so
  the id of the withheld file is determined by its path without reading
  its bytes.
- `assessment/<slug>.md` withheld: refuses `("verification target
  unreadable", verification path)` iff a failing verification's edge
  targets `assessment:<slug>`; untargeted, it is not evidence and is
  ignored, subject only to the collision check of §4.4 step 2.

This is narrower than §5's "until the record is corrected or superseded"
in exactly the way opening obligation 5 asked: supersession is readable
from the superseder's side, so the block lifts without decoding the
record that cannot be decoded.

### 4.6 The five opening obligations, discharged

| # | obligation | where |
|---|---|---|
| 1 | stamp validation precedes the typed readers | §4.4 step 1 — the evidence gate over the whole consulted surface, with stale-verification and stale-assessment arms in the cut |
| 2 | "resolves" has `Index` semantics | §4.4 step 2 — `Index.build` over every decoded node; deprecated-reference and collision arms |
| 3 | the supersession helper is `science.verification.active` | §4.4 step 4 |
| 4 | the ceiling bounds each file, not the namespace | §4.7 — linearity stated; no total bound claimed |
| 5 | an oversized record cannot be recognized as superseded | §4.5 — the superseder-side rule |

### 4.7 Cost, stated

Per-file I/O and allocation are bounded by `RECORD_CEILING + 1`. The
aggregate is linear in the number of files across the five namespaces —
the same shape the audit and the qualification report already accept over
three. No record-count ceiling is introduced: it would be a number with no
design basis, and a busy corpus would become un-admittable until records
were archived. The cut states this as a limitation (§7.6).

## 5. The refusal (`science/errors.py`)

```python
class AdmissionEvidenceRefused(ScienceError):
    """The successor-admission act refused to judge: evidence it must read
    is unreadable, incoherent, or unresolved. Names the offending record."""

    def __init__(self, reason: str, ref: str) -> None:
        super().__init__(f"{reason}: {ref}")
        self.reason = reason
        self.ref = ref
```

Following `ImportRefused`'s form — an explicit initializer that builds the
message and assigns the fields, so `reason` and `ref` are real attributes
and not annotations `Exception` never fills. `ref` is always a `str`: the
boundary passes `str(root)` for the two root-level reasons and the
captured relative path or intent digest otherwise.

Raised, never returned: a refusal of the *act* is a different thing from a
refusal of the *successor*, and the return union stays the core's pair.
`reason` is one of a closed set and `ref` makes the repair directed:

| gate | `reason` | `ref` |
|---|---|---|
| root not an openable directory | `root unreadable` | root path |
| `inspect_registered` returns a `MalformedView` or `AbsentView` | `chain not well-formed` | root path |
| a namespace directory, or one beneath it, exists but could not be enumerated | `namespace uninspectable` | directory path |
| verification undecodable, stamp missing or stale, id–path mismatch, or its classification or read failed | `verification unreadable` | path |
| assessment undecodable, stamp missing or stale, id–path mismatch, or its classification or read failed | `assessment unreadable` | path |
| oversized verification with no decoded, coherent superseder | `verification oversized` | path |
| gated verification with ≠ 1 `verifies` edge | `verification edge cardinality` | path |
| edge target missing, not an assessment, withheld, or unreadable | `verification target unreadable` | verification path |
| resolved target's identity ≠ facet `assessment` | `verification target mismatch` | verification path |
| `Index.build` collision over the decoded nodes, or a decoded node claiming a withheld path's id | `record collision` | colliding id |
| assessment-run intent for the superseded spec reads `unresolvable` | `qualification unresolved for the superseded spec` | intent digest |

The caller corrects the named record and retries the act; nothing routes
around it.

## 6. Accounting

**G4 → full.** The positive arm through `admit_spec_successor` across all
three refusal paths, the lift by a referencing successor, overlap
precedence, the supersession lift and block, every coherence gate, the
oversized rules, snapshot coherence, and the negative re-run at persistence
width: discard the attempt *and* its intent — nothing durable — and no
class holds a trace. Cut 3's value-width disposition stands as the
certification this arm re-reads at persistence width; its arms run
unchanged and are cited, not re-proven.

**R12 → full.** The boundary-mediated strengthening arm: a run started
through the boundary appends its intent before any member act (cut 11);
excise that entry after anchoring and `inspect_registered` returns a
`MalformedView`, which the log evaluator reports as **malformed**;
truncate to a valid prefix and the evaluator — over the anchored observer
set, cut 8's four-outcome precedence — reports **refuted**. Those two
readings are `evaluate_log`'s, certified by cut 8 and cited here, not
re-proven. What this cut adds is the successor-admission consequence of
the same witness: over the excised chain the act refuses
`chain not well-formed` rather than deriving an empty class 2 and
admitting; over the truncated chain the intent is gone from the entries,
the act derives no unfinished attempt, and the successor is admitted —
which is exactly what the evaluator's **refuted** makes detectable
alongside. The intent entry is the removal-detectable witness because its
removal is read by the evaluator; the admission act never pretends to
read it itself. The out-of-band negative stands unchanged (cut 3's arm,
computation limitation 5).

**L7 → part, limitation-only.** The roadmap names "L7's relabel" for this
slice; it cannot happen. Roadmap Appendix C banks L7 u1 — the non-ancestor
`fulfills` spelling, directory-unconstructible on a linear
content-addressed chain — as a limitation (cut 8 results §1.1), and the
any-unrun-arm rule keeps a row with a banked unrun arm `part`. This cut
reads L7's remaining schedulable arms through the new consumer — the kill
between intent append and execution reads attempt-without-recorded-outcome
and *now blocks an unreferenced successor*; a wrong-spec run publication
fails qualification and the intent still blocks — and states L7's
accounting exactly: every schedulable arm read, the sole unrun arm the
banked limitation. The ledger table and the roadmap are corrected at
banking to say "L7 to limitation-only", not "L7's relabel" (§8).

## 7. Conformance cut 12

The cut document (`docs/designs/<freeze date>-conformance-cut-12.md`,
dated the day it freezes) is frozen before implementation and follows cut
11's form: what the cut is,
the boundary, the rows quoted verbatim with dispositions, rows not read,
labeled declarations, accounting, N2 obligations, freeze obligations,
second reader, limitations.

### 7.1 Boundary

Cut 11's, unchanged: the certified volume beside the checkout, the
certified `linux` tuple, `atoms` consumed as an editable path dependency
at remote `main` `038513f` — this slice ships no `atoms` change. Discharge
runs through `python/tools/cut12_acceptance.py` on cut 11's cadence: the
unedited cut-11 prefix, the durable cut-12 arms, then cut 12's N2 audit;
the pytest summary lines quoted in the results record; the execution
rulings ledger committed to a tracked path under `docs/plans/` before any
worktree removal.

### 7.2 Rules inherited

- **Selection** — cut 5's: a clause is selected only when its source
  mutation and every named check run entirely inside §7.1; a row with any
  unrun arm is partial.
- **Verbatim quotation** — G4, R12 and L7 byte-exact against their source
  tables at the freeze commit; single-homing; labeled declarations for the
  obligations §5 minted outside the frozen rows.
- **Fabrication** — cut 8/11's: every fabricated chain passes
  `inspect_chain` or presents exactly its one intended defect; every
  fabricated stored record decodes through the stored surface or is
  rejected at exactly its intended layer with no earlier defect — asserted
  at declaration time, per arm.
- **Engine interior** — the `atoms` append, linearization, settlement and
  lease discipline are `atoms`-certified; this cut certifies Science's
  derivation, gates, capture widening and core over what they return.

### 7.3 Units

Each unit has one exact once-matching source sabotage in
`python/tests/acceptance/n2_arms_cut12.py` and at least one check that
fails under it. The selection, to be fixed exactly in the cut document:

**G4, through `admit_spec_successor`:**
1. an unreferenced successor to a spec with a live failing verification is
   refused with the recorded-failure reason;
2. an unreferenced successor to a spec whose assessment-run intent reads
   attempt-without-recorded-outcome is refused with the unfinished-attempt
   reason;
3. an unreferenced successor to a spec whose intent was fulfilled by a
   `run-attempt` act-report is refused with the recorded-failure reason;
4. a referencing successor lifts each of 1–3;
5. overlap: a spec in both classes refuses with the recorded-failure reason;
6. a failing verification whose coherent active superseder passes
   contributes no member; superseded by another failing one, the block
   holds through the active member; **superseded by an incoherent
   passing one** (zero edges, or a mismatched target), the act refuses
   naming the superseder — the block is never lifted by bare existence;
7. the evidence gate: a verification with a missing stamp, a stale stamp,
   an id naming another path, or an undecodable body refuses naming the
   path; the same for an assessment, **targeted or not**; a regular file
   made unreadable (permission withdrawn after classification) refuses
   naming the path — in either namespace;
8. the coherence gate: zero edges, two edges, a target that is not an
   assessment, a deprecated-id target that resolves (admitted), a
   collision (refused), an identity mismatch (refused);
9. oversized: a withheld verification with a decoded, coherent superseder
   is skipped; without one, refused; a withheld assessment targeted by a
   failing verification refuses; untargeted, ignored; a decoded node
   claiming a withheld path's id refuses as a collision;
10. unresolved: a decayed run under the superseded spec refuses; a decayed
    run under another spec does not block; an unreadable run record is the
    same two ways;
11. snapshot coherence: a blocker written before the act is consulted; one
    written after the act's verdict is not — under the lock, the second
    writer waits;
12. the negative at persistence width: discard the attempt and its intent;
    no class holds a trace; the successor is admitted;
13. `root unreadable` refuses before any lock is taken; a `MalformedView`
    or `AbsentView` refuses `chain not well-formed` under it; a
    `verification/` made unenumerable (mode 000) refuses
    `namespace uninspectable`, and so does an unenumerable `run/`; an
    absent `verification/` is a surface with no failing evidence and
    admits;
14. class 1b selection: a registration carrying an undecodable sibling
    before its qualifying `run-attempt` report still joins the spec; one
    carrying a qualifying run first joins nothing — the helper's order is
    the reducer's.

**R12:** 15. excise a boundary-started run's intent entry after anchoring →
the evaluator reads malformed and the act refuses `chain not well-formed`;
16. truncate to a valid prefix → the evaluator reads refuted over the
anchored observers, and the act — its witness gone — admits; the pair is
the arm.

**L7:** 17. kill between intent append and execution → the intent blocks an
unreferenced successor; 18. a wrong-spec run publication fails
qualification and the intent still blocks; 19. a qualifying publication
lifts the block.

**Labeled declarations** (outside the frozen rows, declared as data):
`capture_surface` sharing `capture_records`' descent with the log
evaluator's surface unchanged; the `withheld`, `unreadable` and
`uninspectable` paths, with `ENOENT` the one silent directory failure;
`reduce_registration` factored from `_qualify_one` with the reducer's
verdicts unchanged over cut 11's arms and no second scan; the closed `reason` set of
`AdmissionEvidenceRefused`; the core's byte-identical first line under
cut 3's arms.

### 7.4 Accounting

G4 full; R12 full; L7 part, remainder exactly u1's banked limitation. No
other row is read.

### 7.5 N2 obligations

Cut 3's G4 arms and cut 11's L7 arms run unchanged in the prefix; the new
arms are cut 12's own. `test_spec.py`'s existing G4 checks gain the new
positional argument and are otherwise untouched.

### 7.6 Limitations

The aggregate read is linear in record count (§4.7). Detection stays
quantified over surviving observers: destruction of a root together with
every anchor holding it is not detectable from nothing. The out-of-band
negative of G2a/R12 stands.

## 8. What changes elsewhere, at banking

- **This spec** is promoted to `docs/designs/2026-08-29-successor-admission-design.md`.
- **Intent-boundary design §5** gains a dated correction: closed at cut 12;
  the entrypoint's home is `science.succession`, not `science.spec` (§2
  item 4); the coherence gate also covers a verification that supersedes
  a failing one (§4.4 step 3). The frozen body is otherwise untouched.
- **Adoption ledger:** row 5's remainder loses G4; row 7's parenthetical
  notes G4 read in full at cut 12; the `Current state` table drops
  `successor-admission`; the "Implemented through" line advances to cut 12.
- **Roadmap:** re-ranked at cut 12 in the same change — `successor-admission`
  leaves the index and tier 1 (`run-confinement` becomes row 1); L7's
  index/ledger phrasing corrected to limitation-only; Appendix A
  regenerated by `python/tools/roadmap_status.py`, whose `ACCOUNTING`
  gains cut 12 (`G4, R12` full; `L7` part) and whose `REOPENED` loses G4;
  Appendix B's G4, R12 and L7 rows updated.
  `test_the_roadmap_and_ledger_name_the_same_boundaries` holds the join.
- **Guide:** `docs/guide/README.md` and any page citing G4 as open, with
  `updated` dates; `check_guide.py` and `test_designs_corpus.py` green.
- **Results record:** `docs/plans/<discharge date>-conformance-cut-12-results.md`
  with a `## Remaining boundary` section naming L8 and L13 (and, under
  `test_the_ledger_summary_names_the_newest_remaining_boundary`, whatever
  the ledger's `Current state` must then name).

## 9. Alternatives rejected

- **Wiring the run boundary.** An optional `supersedes_check` on the
  assessment-run boundary would give the entrypoint a production caller,
  but requires the caller to nominate the superseded spec, changes
  `boundary.py`'s port sequencing, and reads none of G4's rows that the
  entrypoint alone does not. Deriving the nominee from
  `candidate.supersedes` catches only referencing successors — the case G4
  is not about. A later boundary's design.
- **`admit_spec_successor` in `spec.py` with function-local imports.**
  Precedent exists (`world.verify`'s `from science.world import registry`),
  but it hides a boundary inside a value module to satisfy a sentence of
  §5 that predates the import graph it contradicts.
- **Beside the audit in `world/verify.py`.** Reuses
  `_assemble_evaluation_inputs` as-is, at the cost of putting
  spec-succession semantics into the log-verification module.
- **Refusing on any oversized record.** Simplest, but supersession never
  lifts the block — the over-breadth obligation 5 names.
- **A record-count ceiling.** A number with no design basis; fails closed
  on exactly the corpora that have done the most work.
- **Widening `capture_records` itself** with a `namespaces` keyword and a
  second return. The evaluator's two callers would have to change to
  unpack it, and "the certified surface is unchanged" would be a claim
  about a function whose signature had changed. A sibling over the same
  descent keeps that claim trivially true.
- **A second capture pass for the new namespaces.** Two reads under one
  hold are still one snapshot, but one call is one snapshot by
  construction rather than by argument.
- **Deriving class 1b from `IntentQualification` alone.** `matched` names
  the registration, not the record; a registration can hold a run and a
  `run-attempt` report. Adding a `fulfilled_path` member to
  `IntentQualification` would widen cut 11's report contract; repeating
  the reducer's loop in the admission act would be a second copy of one
  selection. Factoring the loop keeps one selection and cut 11's verdicts.
- **Refusing on a non-well-formed chain only when it concerns the
  superseded spec.** A malformed chain has no readable entries, so
  "concerns" is undecidable; the refusal is global.
- **Treating an unreadable regular file like an oversized one.** Size is
  bounded by the design and known from the path; a failed read is a
  state the act cannot characterise, and a failing verification whose
  bytes became unreadable would otherwise leave both derived sets and
  admit the successor.
- **Gating only failing verdicts, as §5 says.** A passing verification
  that supersedes a failing one acts on blocker evidence; an incoherent
  one would lift a valid block by existing. The widening is minimal —
  superseders of failing or withheld records — and recorded as a
  correction.

## 10. Verification

Unit tests, portable: the widened core (signature, both reasons,
precedence, the lift); `capture_surface`'s records, withheld, unreadable
and uninspectable paths — an absent namespace silent, an unenumerable one
named — with `capture_records`' surface unchanged;
`reduce_registration`'s three members against `_qualify_one`'s verdicts; every gate in §5's table over
fabricated roots, positive and negative. The cut's durable arms on the
certified tuple (§7). At banking: `check_guide.py`, `test_designs_corpus.py`,
`test_check_guide.py`, `git diff --check`, and the diff review naming every
file changed.

## 11. Choreography

1. Freeze cut 12 (`docs/designs/…-conformance-cut-12.md`) from §7, before
   any implementation commit; record the freeze commit.
2. Errors: `AdmissionEvidenceRefused`.
3. Core: widen `admit_successor`; update `test_spec.py`'s callers.
4. Capture: `capture_surface` over the shared descent; `capture_records`
   pinned unchanged by test. Reducer: `reduce_registration` factored
   out; `_qualify_one`'s verdicts pinned unchanged over cut 11's arms.
5. `science/succession.py`: the boundary, gate by gate, TDD over
   fabricated roots.
6. `n2_arms_cut12.py`, `test_successor_admission_acceptance.py`,
   `test_n2_cut12.py`, `tools/cut12_acceptance.py`.
7. Discharge on the certified tuple; results record; rulings ledger to a
   tracked path.
8. Banking (§8), including the roadmap re-rank; the `--no-ff` merge is the
   human partner's.
