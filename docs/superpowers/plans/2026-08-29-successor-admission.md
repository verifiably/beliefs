# Successor admission — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close G4 at persistence width — the widened pure core, the deriving boundary `admit_spec_successor`, the one named refusal, the frozen conformance cut 12 with its durable arms and N2 audit, its discharge, and the banking that re-ranks the roadmap.

**Architecture:** Documentation-first (the cut freezes before any implementation commit), then five small production changes — `AdmissionEvidenceRefused` in `science/errors.py`; the two-set `admit_successor` in `science/spec.py` with its first body line byte-identical; `capture_surface` beside `capture_records` in `science/world/records.py`; `decode_node` factored out of `decode_record` and `record_paths_of` + `reduce_registration` factored out of `_qualify_one`; and the new `science/succession.py` that composes them under one hold — then the acceptance layer (`n2_arms_cut12.py`, `test_successor_admission_acceptance.py`, `test_n2_cut12.py`, `tools/cut12_acceptance.py`), the discharge, and banking.

**Tech Stack:** Python 3.13 via `uv run` from `python/`; pytest; ruff; pyright; the `atoms` engine at remote `main` `038513f` as an editable path dependency (no atoms change); `nodes.core` (`Node`, `Index`, `node_from_markdown`); `python/tools/check_guide.py` for the docs gates.

**Spec:** `docs/superpowers/specs/2026-08-29-successor-admission-design.md` — read it first. Inherited authority: `docs/designs/2026-08-26-world-index-intent-boundary-design.md` §5. Cut form: `docs/designs/2026-08-27-conformance-cut-11.md`.

## Global Constraints

- Work in this worktree on branch `design/successor-admission`; paths are relative to the worktree root unless a command says `cd python`.
- **No atoms change.** The engine is consumed at remote `main` `038513f`; nothing under the atoms checkout is edited.
- **The core's first body line stays byte-identical:** `    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:` — cut 3's `n2_arms_cut3.py` sabotages it three times.
- **Cut 11's frozen anchors:** every `Sabotage.before` string in `python/tests/acceptance/n2_arms_cut11.py` must still occur exactly once in its module after every task. The one permitted edit is Task 5's whitespace-only re-indent of the two anchors that move into `reduce_registration`, with the pin advanced in Task 7.
- **`capture_records` is unchanged** in signature, return, and behaviour, including `()` for `kind != "corpus"`.
- **Durable tests** (anything touching the real engine) use the `certified_work` fixture from `python/tests/conftest.py` — never `tmp_path` — and run on the certified volume beside the checkout.
- **Reason strings** of `AdmissionEvidenceRefused` are exactly spec §5's eleven: `root unreadable`, `chain not well-formed`, `namespace uninspectable`, `verification unreadable`, `assessment unreadable`, `verification oversized`, `verification edge cardinality`, `verification target unreadable`, `verification target mismatch`, `record collision`, `qualification unresolved for the superseded spec`.
- Pytest: `addopts` sets `-q`; run `cd python && set -o pipefail && uv run pytest tests/<file> | tail -3`. Lint: `uv run ruff check <paths> && uv run pyright <paths> | tail -1`.
- Conventional commits, no AI-attribution trailer. Every commit leaves the touched test files green.
- Curation rules bind: frozen cut bodies, plans, execution ledgers and results records are never edited after the fact; a design's `**Status:**` is corrected in the same change that lands its work.

---

### Task 1: Freeze conformance cut 12

**Files:**
- Create: `docs/designs/2026-08-29-conformance-cut-12.md`
- Create: `docs/plans/2026-08-29-successor-admission-ledger.md`
- Modify: `README.md` (the design table, its count sentence)
- Modify: `python/tests/test_designs_corpus.py` (`_COUNT_WORDS`)
- Modify: `docs/guide/contracts-and-adoption.md` (front matter `sources:`, `updated`)

**Interfaces:**
- Produces: the frozen unit ids Tasks 6–7 declare arms against (`G4u1`–`G4u14`, `R12u1`–`R12u2`, `L7u14`–`L7u16`, `K1`–`K5`); the freeze commit hash Task 7 pins as `CUT12_FREEZE_COMMIT`.

- [ ] **Step 1: Write the cut document**

Write `docs/designs/2026-08-29-conformance-cut-12.md` with exactly this content. The three quoted rows are byte-exact copies from their source tables at `4110038`: G4 from `2026-08-02-epistemic-kernel-design.md` (the G table), R12 from `2026-08-02-computation-reproducibility-design.md` (the R table), L7 from `2026-08-03-tamper-evident-log-design.md` §10. Before committing, re-copy each row from its source with `grep -E '^\| \*\*G4\*\* \|' docs/designs/2026-08-02-epistemic-kernel-design.md`, `grep -E '^\| \*\*R12\*\* \|' docs/designs/2026-08-02-computation-reproducibility-design.md`, `grep -E '^\| L7 \|' docs/designs/2026-08-03-tamper-evident-log-design.md` and paste the grep output verbatim in place of the three `| … |` lines below — the rows are long and a hand transcription is the drift this step exists to prevent.

````markdown
# Conformance cut 12 — successor admission, G4's closure

**Status:** frozen 2026-08-29, before implementation. Source specification:
`docs/superpowers/specs/2026-08-29-successor-admission-design.md` (cited as
*spec*), promoted to `docs/designs/` at banking.

**Sources:** `2026-08-27-conformance-cut-11.md` (rule and practice
inheritances; the reducer, captured-record evidence input and record
ceiling this cut composes; the L7 units this cut re-reads through a new
consumer); `2026-08-11-conformance-cut-3.md` (the value-width G4
certification whose three `n2_arms_cut3.py` sabotages stay in force);
`2026-08-22-conformance-cut-8.md` (the chain classification the R12
units cite); `2026-08-26-world-index-intent-boundary-design.md` §5 (the
inherited design and its five opening obligations); the live **G4**,
**R12** and **L7** rows quoted verbatim below.

## 1. What this cut is

Cut 12 is the frozen acceptance boundary for the successor-admission
slice: the two-set pure core `admit_successor`; the deriving boundary
`admit_spec_successor` reading, under one hold, the chain's qualification
and the corpus's verification and assessment records; the two blocker
classes with their distinct refusal reasons and fixed precedence; the
evidence, index and coherence gates; the superseder-side rule for
oversized records; the named refusal `AdmissionEvidenceRefused`; and the
capture and reducer factorings that keep cut 11's certified surfaces
byte-for-byte unchanged. **No run-boundary change, no atoms change, no
`revise` change** (spec §2).

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any
unrun arm is **partial**. The three practice inheritances stand: labeled
declarations (§3.3), single-homing, and verbatim row quotation byte-exact
against the source tables at this cut's freeze commit.

Cut 8's engine-interior principle and cut 11's fabrication rule apply:
the atoms append, linearization, settlement and lease discipline are
atoms-certified productions; every fabricated chain passes
`inspect_chain` or presents exactly its one intended defect, and every
fabricated stored record decodes through the stored surface or is
rejected at exactly its intended layer with no earlier defect — asserted
at declaration time.

Single-homing governs three prior certifications this cut touches but
never re-reads: cut 3's value-width G4 disposition (its arms run
unchanged in the prefix and are cited as the certification the G4 units
re-read at persistence width); cut 8's chain classification (malformed
on an interior linkage break, refuted under an anchored observer after
truncation — cited by the R12 units, whose own claim is the admission
act's consequence of the same witness); and cut 11's L7 units (this cut
declares three new L7 units through the successor-admission consumer and
re-declares none of cut 11's).

## 2. The boundary

Cut 11's, unchanged: the certified volume beside the checkout, the
certified `linux` tuple, atoms consumed as an editable path dependency at
remote `main` `038513f` — this slice ships no atoms change. Discharge runs
through `python/tools/cut12_acceptance.py` on cut 11's cadence: the
unedited cut-11 prefix, the durable cut-12 arms, then cut 12's N2 audit;
the pytest summary lines are quoted in the results record; the execution
rulings ledger (`../plans/2026-08-29-successor-admission-ledger.md`) is
committed to its tracked path before any worktree removal.

## 3. The rows

### 3.1 Rows read, quoted verbatim, with dispositions

| **G4** | A **recorded** failed replay cannot be silently orphaned (narrowed — §3.2) | Attempt an unreferenced successor to a recorded failure; assert refusal. **Also assert the negative:** discard the failed attempt entirely and confirm the system *cannot* detect it — the test pins the limit so no reader over-reads G4 |

- **Full.** Selected (14 units), read at persistence width through
  `admit_spec_successor`, acknowledging cut 3's value-width disposition
  as the certification these units re-read. The units:
  - **(u1)** an unreferenced successor to a spec with a live failing
    verification is refused with the recorded-failure reason;
  - **(u2)** an unreferenced successor to a spec whose assessment-run
    intent reads attempt-without-recorded-outcome is refused with the
    unfinished-attempt reason;
  - **(u3)** an unreferenced successor to a spec whose intent was
    fulfilled by a `run-attempt` act-report is refused with the
    recorded-failure reason;
  - **(u4)** a referencing successor lifts each of u1–u3;
  - **(u5)** overlap precedence: a spec in both classes refuses with the
    recorded-failure reason;
  - **(u6)** supersession: a failing verification whose coherent active
    superseder passes contributes no member; superseded by another
    failing one, the block holds through the active member; superseded
    by an incoherent passing one, the act refuses naming the superseder;
  - **(u7)** the evidence gate: a verification with a missing stamp, a
    stale stamp, an id naming another path, or an undecodable body
    refuses naming the path; the same for an assessment, targeted or
    not; a regular file made unreadable refuses naming the path, in
    either namespace;
  - **(u8)** the coherence gate: zero edges, two edges, a target that is
    not an assessment, a deprecated-id target that resolves (admitted),
    a uid collision (refused, naming the colliding id), an identity
    mismatch (refused), and a stored `verifies` relation whose `source`
    names another node — not this record's edge, so its count is zero;
  - **(u9)** oversized: a withheld verification with a decoded, coherent
    superseder is skipped; without one, refused; a withheld assessment
    targeted by a failing verification refuses; untargeted, ignored; a
    decoded node claiming a withheld path's id refuses as a collision;
  - **(u10)** unresolved: a decayed run under the superseded spec
    refuses; a decayed run under another spec does not block;
  - **(u11)** snapshot coherence: a blocker written before the act is
    consulted; one whose writer arrives during the act waits on the
    root's operation lock and is not consulted by that act;
  - **(u12)** the **negative** at persistence width: discard the attempt
    and its intent — nothing durable — and no class holds a trace; the
    successor is admitted;
  - **(u13)** `root unreadable` refuses before any lock is taken; a
    `MalformedView` or `AbsentView` refuses `chain not well-formed`
    under it; a namespace directory made unenumerable refuses
    `namespace uninspectable` — for `verification/` and for `run/`
    alike; an absent `verification/` admits;
  - **(u14)** class 1b selection: a registration carrying an undecodable
    sibling before its qualifying `run-attempt` report still joins the
    spec; one carrying a qualifying run joins nothing.

| **R12** | Spec-predates-run is bounded, and the bound is pinned | Assert the execution boundary refuses a run naming no frozen spec identity. **Then assert the negative:** freeze a spec *after* an out-of-band execution, attach it, and confirm the system **cannot** detect the ordering — pinning §3.3 so no reader takes content addressing for proof of pre-registration. With the §8.7 log implemented (`2026-08-03-tamper-evident-log-design.md`), the **boundary-mediated** arm strengthens — a boundary-started run's intent entry is a removal-detectable witness — while this out-of-band negative stands unchanged (its limitation 5) *(Amended 2026-08-11, the act-report design §3: cooperative no-run closure now exists — a post-intent attempt that minted no run may close through a qualifying act-report — and the formal claim is unchanged: the out-of-band negative stands, and an unmatched intent still proves exactly an attempt with no qualifying recorded outcome.)* |

- **Full.** Selected (2 units), the boundary-mediated strengthening arm;
  every other arm is cut 3's standing certification (the no-spec
  refusal, the out-of-band negative), cited and never re-read. The
  units:
  - **(u1)** excise a boundary-appended intent entry from the interior
    of the chain after a fulfilling registration → `inspect_registered`
    returns a `MalformedView` (cut 8's classification, cited) and the
    admission act refuses `chain not well-formed` rather than deriving
    an empty class 2;
  - **(u2)** truncate the chain to the valid prefix before the intent,
    with an observer anchored at the pre-truncation tip → the evaluator
    reads **refuted** (cut 8's anchor-unreachable step, cited) and the
    admission act — its witness gone — admits the unreferenced
    successor; the pair is the arm: the intent entry is
    removal-detectable because the evaluator reads its removal, and the
    admission act never pretends to.

| L7 | Intent claims are exactly as wide as stated | assessment-run intent with **no pointers at all, or every `fulfills` pointer fully resolved and non-qualifying** — §6's exact reduction, never a collapse of an unresolved candidate → attempt-without-recorded-outcome finding, never a refutation; excise the intent entry after anchoring → **malformed** (interior linkage break) or, via truncation to a valid prefix, **refuted** — never silent; a second committed registration fulfilling the same intent, or a `fulfills` naming a missing or non-ancestor intent → **malformed**; mutate the fulfillment itself — a wrong-purpose committed transaction carrying `fulfills = I`, a run publication under another spec, another `event_token`, or a publication creating no run → each **fails qualification** (§3), the intent stays attempt-without-recorded-outcome, and the non-qualifying `fulfills` is named in a finding; make a **genuine** published run's bytes unresolvable → qualification **unresolvable**, and **no** unmatched finding is emitted (§6's reduction); kill between the intent's durable append and execution start → intent present, no execution — attempt-without-recorded-outcome, exactly as stated; race two cooperative intent appends on one root → serialized by the root lease, one linear chain, never a sibling branch (L3); attempt to publish the run through a root other than the intent's → **refused**, placement froze before execution; assert no caller-supplied `fulfills` path exists at the boundary; **negative:** crash, cancellation, and discarded failure are indistinguishable by construction; the guarantee quantifies over **both** intent kinds — instantiated for the holdings shape, a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between a holdings intent's append and its mutation reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-10, the verified-holdings record design §8)*; the guarantee now quantifies over the **operation intent** too — instantiated for its shape, a report carrying another operation's token, a report of the wrong kind, a run publication for a non-run operation, or a registration publishing no terminal record each **fails qualification** (a second fulfilling registration on one intent stays the chain's **malformed**, classified before qualification — T2's arm), and a kill between the operation intent's append and its first act reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-11, the act-report design §3)* |

- **Partial, limitation-only.** Selected (3 units), the row's arms read
  through the successor-admission consumer; cut 11's thirteen units
  stand and are not re-declared. **L7u1's partial remainder persists**:
  the non-ancestor `fulfills` spelling is directory-unconstructible on a
  linear content-addressed chain (cut 8 results §1.1), banked as a
  limitation, and the any-unrun-arm rule keeps this row `part`. After
  this cut L7's sole unrun arm is that limitation. The units, numbered
  after cut 11's:
  - **(u14)** a kill between the assessment-run intent's durable append
    and execution start → the intent blocks an unreferenced successor
    to its spec, with the unfinished-attempt reason;
  - **(u15)** a run publication under another spec fails qualification
    and the intent still blocks;
  - **(u16)** a qualifying run publication lifts the block — the
    successor is admitted.

### 3.2 Rows not read

**L8** and **L13** — row 5's other named owners, untouched. **G2a's
out-of-band negative stands** (cut 3, computation limitation 5), cited
by R12u2 and never re-read. **G8, S3, R17** — the sibling limit-pinning
negatives, untouched. Every other row carries its standing certification.

### 3.3 Labeled declarations

Five labeled declarations carry the spec's minted obligations outside
the frozen rows, declared as data beside the selected arms:

1. **`capture_surface` shares `capture_records`' descent** — one private
   descent reporting rather than swallowing its failures;
   `capture_records(root, kind)` unchanged in signature, return and
   behaviour, its `RootKind` guard included: **(a)** over a corpus root
   its records equal `capture_surface(root, RECORD_NAMESPACES).records`;
   **(b)** a world or store root containing `run/*.md` still captures
   nothing (spec §4.2).
2. **The descent's named failures** — **(a)** a regular file over the
   ceiling is in `withheld`; **(b)** a regular file whose readable open
   fails is in `unreadable`; **(c)** a namespace directory whose open
   fails with anything other than `ENOENT` is in `uninspectable`;
   **(d)** an absent namespace appears in none of the three; **(e)** a
   `scandir` failure is `uninspectable` unless it is `ENOENT`; **(f)** a
   directory entry whose classification raises is `unreadable`, never a
   leaked exception (spec §4.2).
3. **The registration reduction is factored, not repeated** —
   `record_paths_of` and `reduce_registration` are `_qualify_one`'s
   filter and inner loop as values; `_qualify_one`'s verdicts are
   byte-for-byte cut 11's over cut 11's arms; **(a)** first match in
   `final` order wins; **(b)** an undecodable earlier sibling leaves
   `unresolved` set beside a later match; **(c)** every decoded
   non-qualifying record's reason is returned in order (spec §4.4).
4. **The closed reason set** — `AdmissionEvidenceRefused(reason, ref)`
   carries both as real attributes, assigned by its initializer; `reason`
   is drawn from spec §5's eleven and nothing else; `ref` is a string
   naming the record, directory, root, colliding id or intent digest.
5. **The core's anchor line** — `admit_successor`'s first body line is
   byte-identical to the line cut 3's three G4 sabotages name, so those
   arms keep running against the same source.

## 4. Accounting

Three rows read: **2 full** (G4, R12), **1 partial** (L7, its L7u1
limitation restated). Selected units: G4 14, R12 2, L7 3 — **19 selected
+ 5 labeled = 24 declaration units**.

## 5. N2 obligations

Beyond the standing N2 harness discipline, the declarations carry these
check-time obligations:

1. **Fabrication well-formedness** (§1): every fabricated verification or
   assessment record decodes through `decode_node` and its typed reader,
   or is rejected at exactly its intended layer — the stale stamp fails
   the stamp check with the frontmatter parsing; the id–path mismatch
   fails the layout check with the stamp agreeing; the cardinality and
   identity-mismatch records decode cleanly and fail only the coherence
   gate — asserted at declaration time.
2. **The kill arm** (L7u14) interposes at the port seam between the
   durable append and the first act — deterministic, never a timing
   race — and asserts the intent entry is durably present while no
   member act began.
3. **The snapshot arm** (G4u11) asserts the second writer actually
   waited: it is released only after the act returns, and the blocker it
   writes is consulted by the *next* act.
4. **The oversized arms** (G4u9) sit exactly on the boundary: a record of
   exactly `RECORD_CEILING` bytes is captured; one byte more is withheld.
5. **The R12 arms** assert the chain state before the admission act:
   u1's `inspect_registered` returns a `MalformedView` whose defect names
   the excised digest's successor; u2's returns a `WellFormedView` whose
   tip is the genesis, and the evaluator's report reads `refuted` with
   `anchor-unreachable` as its finding.
6. **The unreadable arms** (G4u7, G4u13) must run as a non-root user;
   the check asserts `os.geteuid() != 0` before changing a mode, so a
   privileged run reports a failing check rather than a vacuous pass.

## 6. Freeze obligations

Four, named before the plan exists: **u1–u3's blockers must be genuine
durable state** — verification and assessment records published through
the port's non-fulfilling `execute`, intents appended through the port,
`run-attempt` reports published through `execute_fulfilling` — never
hand-built sets; **the R12 excision and truncation act on the engine's
own chain leaves** under `root/.#~chain/`, with the resulting view read
through the production seam; **the two cut-11 anchors that move with
`reduce_registration`** change in leading whitespace only, their
replacement text and checks untouched, and cut 12's harness pins
`n2_arms_cut11.py` at the commit that carries the move; **`revise` is
not edited** — its signature check in `test_spec.py` stays as it is.

## 7. Second reader

The charge, unchanged from cut 11 §7: verify every quoted row byte-exact
against its source table as of the freeze commit; audit each selection
against §2's boundary; audit each disposition — full, partial, labeled —
against the selection rule, with any unrun arm forcing partial; and
record findings for amendment before the freeze. The reader's findings
and their closures join this document; the freeze commit is the one that
closes the last of them.

## 8. Limitations

1. **The aggregate read is linear in record count** across the five
   namespaces; per-file I/O and allocation are bounded by
   `RECORD_CEILING + 1`, and no total bound is claimed (spec §4.7).
2. **Detection quantifies over surviving observers** — destruction of a
   root together with every anchor holding it is not detectable from
   nothing; G4u12 is this cut's pin of the same bound.
3. **G2a/R12's out-of-band negative stands**; the boundary-mediated
   strengthening is the whole of what R12u1–u2 read.
4. **L7u1's non-ancestor spelling** stays directory-unconstructible; L7
   stays `part` on that arm alone.
5. **`admit_spec_successor` has no production caller** in this slice
   (spec §2 item 1, §9); the run boundary's nomination of a superseded
   spec is a later design's.
6. **Event-level L8 and the L13 preimage resolver** remain open with
   their named owners.
````

- [ ] **Step 2: Register the document with the corpus guards**

In `README.md`, append after the cut-11 row of the design table:

```markdown
| `2026-08-29-conformance-cut-12.md` | the twelfth frozen conformance cut, selecting successor admission: 2 rows full, 1 part, with 19 selected and 5 labeled declarations; G4 read at persistence width |
```

and change the count sentence `Thirty-eight documents in `docs/designs/`` to `Thirty-nine documents in `docs/designs/``, and its range end `2026-08-02 through 2026-08-27` to `2026-08-02 through 2026-08-29`.

In `python/tests/test_designs_corpus.py`, extend `_COUNT_WORDS` after the `38: "Thirty-eight",` line:

```python
    39: "Thirty-nine",
    40: "Forty",
```

In `docs/guide/contracts-and-adoption.md`, set `updated: 2026-08-29` and add `  - ../designs/2026-08-29-conformance-cut-12.md` to `sources:` immediately after the `../designs/2026-08-27-conformance-cut-11.md` line.

- [ ] **Step 3: Open the execution ledger**

Write `docs/plans/2026-08-29-successor-admission-ledger.md`:

```markdown
# Successor-admission slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-29-successor-admission.md`
Specification: `docs/superpowers/specs/2026-08-29-successor-admission-design.md`
Frozen cut: `docs/designs/2026-08-29-conformance-cut-12.md`
Freeze hash: (recorded in the commit after the freeze)

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the certified engine is standing authority.** Atoms remote
   `main` `038513f` is the binding engine contract (cut 12 §2: no atoms
   change ships with this slice); no task edits atoms.
2. **R2 — the core's anchor line is frozen text.** `admit_successor`'s
   first body line is byte-identical before and after Task 3, so cut 3's
   three G4 sabotages keep matching exactly once.
3. **R3 — two cut-11 anchors move in whitespace only.** Task 5's
   factoring re-indents `if payload is None:` / `pointer_unresolved`
   and `except RecordUndecodable:` / `pointer_unresolved` by the loop's
   new depth; replacement text and checks are untouched; Task 7 pins
   `n2_arms_cut11.py` at that commit.
```

- [ ] **Step 4: Run the documentation gates**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1
```

Expected: `CHECK_GUIDE_OK`; every test passed (the README count, the design listing, the guide citation and the cross-reference guards all read the new file).

- [ ] **Step 5: Commit the freeze, then record its hash**

```bash
git add docs/designs/2026-08-29-conformance-cut-12.md README.md python/tests/test_designs_corpus.py docs/guide/contracts-and-adoption.md docs/plans/2026-08-29-successor-admission-ledger.md
git commit -m "docs(designs): freeze conformance cut 12, successor admission"
git rev-parse --short HEAD
```

Replace `(recorded in the commit after the freeze)` in the ledger with the printed short hash, then:

```bash
git add docs/plans/2026-08-29-successor-admission-ledger.md
git commit -m "docs(plans): record cut 12's freeze hash in the execution ledger"
```

---

### Task 2: `AdmissionEvidenceRefused`

**Files:**
- Modify: `python/src/science/errors.py` (after `class LogEvidenceRefused`'s block; find it with `grep -n 'class LogEvidenceRefused' python/src/science/errors.py`)
- Test: `python/tests/test_succession_errors.py`

**Interfaces:**
- Produces: `science.errors.AdmissionEvidenceRefused(reason: str, ref: str)` with attributes `.reason`, `.ref`, message `f"{reason}: {ref}"`.

- [ ] **Step 1: Write the failing test**

```python
"""The successor-admission act's one named refusal (spec §5)."""

import pytest

from science.errors import AdmissionEvidenceRefused, ScienceError


def test_it_is_a_science_error_carrying_reason_and_ref() -> None:
    refused = AdmissionEvidenceRefused("verification unreadable", "verification/v1.md")
    assert isinstance(refused, ScienceError)
    assert refused.reason == "verification unreadable"
    assert refused.ref == "verification/v1.md"
    assert str(refused) == "verification unreadable: verification/v1.md"


def test_both_arguments_are_required() -> None:
    with pytest.raises(TypeError):
        AdmissionEvidenceRefused("root unreadable")  # type: ignore[call-arg]
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd python && set -o pipefail && uv run pytest tests/test_succession_errors.py | tail -2
```

Expected: `ImportError: cannot import name 'AdmissionEvidenceRefused'`.

- [ ] **Step 3: Add the class**

Insert directly after the `LogEvidenceRefused` class body in `python/src/science/errors.py`:

```python
class AdmissionEvidenceRefused(ScienceError):
    """The successor-admission act refused to judge: evidence it must read
    is unreadable, incoherent, or unresolved. Names the offending record
    so the repair is directed; the act is retried after correction, never
    around it (successor-admission design §5)."""

    def __init__(self, reason: str, ref: str) -> None:
        super().__init__(f"{reason}: {ref}")
        self.reason = reason
        self.ref = ref
```

`errors.py` has no `__all__`; nothing else to register.

- [ ] **Step 4: Run to verify it passes, then lint**

```bash
cd python && set -o pipefail && uv run pytest tests/test_succession_errors.py | tail -1 && uv run ruff check src/science/errors.py tests/test_succession_errors.py && uv run pyright src/science/errors.py | tail -1
```

Expected: `2 passed`; ruff clean; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/errors.py python/tests/test_succession_errors.py
git commit -m "feat(errors): name the successor-admission act's evidence refusal"
```

---

### Task 3: The two-set core

**Files:**
- Modify: `python/src/science/spec.py:335-342` (`admit_successor`)
- Modify: `python/tests/test_spec.py` (the three `test_g4_*` tests and one new test)

**Interfaces:**
- Produces: `science.spec.admit_successor(candidate: FrozenSpec, superseded: FrozenSpec, recorded_failures: frozenset[str], unfinished_attempts: frozenset[str]) -> SuccessorAdmitted | SuccessorRefused`; the two `SuccessorRefused.reason` strings `"an unreferenced successor to a recorded failed replay"` and `"an unreferenced successor to an unfinished recorded attempt"`.

- [ ] **Step 1: Update the three existing G4 tests and add the new ones**

In `python/tests/test_spec.py`, change the three existing calls so each passes both sets positionally — `admit_successor(unreferenced, original, frozenset({original.identity}), frozenset())`, `admit_successor(successor, original, frozenset({original.identity}), frozenset())`, `admit_successor(unreferenced, original, frozenset(), frozenset())` — and add after `test_g4_a_discarded_failed_attempt_is_undetectable`:

```python
def test_g4_an_unreferenced_successor_to_an_unfinished_recorded_attempt_is_refused():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())
    verdict = admit_successor(unreferenced, original, frozenset(), frozenset({original.identity}))
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"


def test_g4_a_spec_in_both_classes_refuses_with_the_recorded_failure_reason():
    original = freeze(draft(), held_rules=held_rules())
    unreferenced = freeze(draft(estimand="revised"), held_rules=held_rules())
    both = frozenset({original.identity})
    verdict = admit_successor(unreferenced, original, both, both)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_g4_a_referencing_successor_lifts_both_classes():
    original = freeze(draft(), held_rules=held_rules())
    successor = revise(
        original, edits={"estimand": "revised"}, held_rules=held_rules(), recorded_failures=frozenset()
    )
    both = frozenset({original.identity})
    assert isinstance(admit_successor(successor, original, both, both), SuccessorAdmitted)


def test_g4_the_core_keeps_cut_3s_anchor_line():
    # K5: cut 3's three G4 sabotages name this exact line; it must occur once.
    from pathlib import Path

    import science.spec as spec_module

    source = Path(spec_module.__file__).read_text(encoding="utf-8")
    anchor = "    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:"
    assert source.count(anchor) == 1
    assert list(inspect.signature(admit_successor).parameters) == [
        "candidate",
        "superseded",
        "recorded_failures",
        "unfinished_attempts",
    ]
```

- [ ] **Step 2: Run to verify the new tests fail**

```bash
cd python && set -o pipefail && uv run pytest tests/test_spec.py -k g4 | tail -2
```

Expected: failures with `TypeError: admit_successor() takes 3 positional arguments but 4 were given`.

- [ ] **Step 3: Widen the core**

Replace `admit_successor` in `python/src/science/spec.py` with:

```python
def admit_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    recorded_failures: frozenset[str],
    unfinished_attempts: frozenset[str],
) -> SuccessorAdmitted | SuccessorRefused:
    """G4 over the slice's value state — the two blocker classes the boundary
    derives (successor-admission design §3). The first check is byte-identical
    to cut 3's line, so a spec in both classes refuses with the recorded-failure
    reason by statement order, never by set iteration. A failure absent from
    both sets never happened: undetectable."""
    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to a recorded failed replay")
    if superseded.identity in unfinished_attempts and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to an unfinished recorded attempt")
    return SuccessorAdmitted(candidate.identity)
```

- [ ] **Step 4: Run test_spec, the cut-3 anchor audit, and lint**

```bash
cd python && set -o pipefail && uv run pytest tests/test_spec.py | tail -1
grep -c 'if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:' src/science/spec.py
uv run ruff check src/science/spec.py tests/test_spec.py && uv run pyright src/science/spec.py | tail -1
```

Expected: all passed; `1`; clean. Then confirm cut 3's arms still fail under their sabotage and pass without it — `test_n2.py` audits every declared arm as one session fixture, so it runs whole (`-k` cannot select a row):

```bash
cd python && set -o pipefail && uv run pytest tests/test_n2.py | tail -1
```

Expected: passed (the audit runs a subprocess pytest per arm; allow several minutes).

- [ ] **Step 5: Commit**

```bash
git add python/src/science/spec.py python/tests/test_spec.py
git commit -m "feat(spec): admit a successor over two blocker classes with fixed precedence"
```

---

### Task 4: `capture_surface`

**Files:**
- Modify: `python/src/science/world/records.py` (whole file rewritten below; `RECORD_CEILING`, `RECORD_NAMESPACES`, `_leaf_seam` and `capture_records`' signature kept)
- Test: `python/tests/test_record_capture.py` (append tests)

**Interfaces:**
- Produces: `science.world.records.CapturedSurface(records, withheld, unreadable, uninspectable)` and `capture_surface(root: Path, namespaces: tuple[str, ...]) -> CapturedSurface`. `capture_records(root, kind)` unchanged.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_record_capture.py`:

```python
def _five(root: Path) -> Path:
    for namespace in (*records.RECORD_NAMESPACES, "verification", "assessment"):
        (root / namespace).mkdir(parents=True, exist_ok=True)
    return root


def test_capture_surface_records_equal_capture_records_over_the_default_namespaces(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    (root / "act-report" / "b.md").write_bytes(b"report-bytes")
    surface = records.capture_surface(root, records.RECORD_NAMESPACES)
    assert surface.records == records.capture_records(root, "corpus")
    assert surface.withheld == surface.unreadable == surface.uninspectable == ()


def test_capture_surface_reads_the_namespaces_it_is_given(certified_work) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    (root / "assessment" / "a.md").write_bytes(b"a")
    (root / "run" / "r.md").write_bytes(b"r")
    surface = records.capture_surface(root, ("verification", "assessment"))
    assert surface.records == (("assessment/a.md", b"a"), ("verification/v.md", b"v"))
    assert records.capture_records(root, "corpus") == (("run/r.md", b"r"),)


def test_a_non_corpus_root_holding_run_records_still_captures_nothing(certified_work) -> None:
    root = _corpus(certified_work / "not-a-corpus")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    assert records.capture_records(root, "world") == ()
    assert records.capture_records(root, "store") == ()


def test_an_oversized_regular_file_is_withheld_and_named(certified_work) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "exact.md").write_bytes(b"x" * records.RECORD_CEILING)
    (root / "verification" / "big.md").write_bytes(b"x" * (records.RECORD_CEILING + 1))
    surface = records.capture_surface(root, ("verification",))
    assert [path for path, _ in surface.records] == ["verification/exact.md"]
    assert surface.withheld == ("verification/big.md",)
    assert surface.unreadable == surface.uninspectable == ()


def test_an_unreadable_regular_file_is_named_not_dropped(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user: root ignores file modes"
    root = _five(certified_work / "root")
    target = root / "verification" / "locked.md"
    target.write_bytes(b"secret")
    target.chmod(0)
    try:
        surface = records.capture_surface(root, ("verification",))
    finally:
        target.chmod(0o644)
    assert surface.records == ()
    assert surface.unreadable == ("verification/locked.md",)
    assert surface.withheld == surface.uninspectable == ()


def test_an_unenumerable_namespace_is_uninspectable_and_an_absent_one_is_silent(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user: root ignores directory modes"
    root = _five(certified_work / "root")
    (root / "assessment").rmdir()
    locked = root / "verification"
    (locked / "v.md").write_bytes(b"v")
    locked.chmod(0)
    try:
        surface = records.capture_surface(root, ("verification", "assessment"))
    finally:
        locked.chmod(0o755)
    assert surface.records == ()
    assert surface.uninspectable == ("verification",)
    assert surface.withheld == surface.unreadable == ()


def test_symlinks_and_fifos_stay_silent_in_capture_surface(certified_work) -> None:
    root = _five(certified_work / "root")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    (root / "verification" / "link.md").symlink_to(outside)
    os.mkfifo(root / "verification" / "pipe.md")
    surface = records.capture_surface(root, ("verification",))
    assert surface == records.CapturedSurface((), (), (), ())


class _FailingEntry:
    """A directory entry whose classification raises — the `DirEntry.is_dir`
    failure the descent must name rather than leak."""

    def __init__(self, name: str, error: OSError) -> None:
        self.name = name
        self._error = error

    def is_dir(self, follow_symlinks: bool = True) -> bool:
        raise self._error


class _Scan:
    def __init__(self, entries) -> None:
        self._entries = entries

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def __iter__(self):
        return iter(self._entries)


def test_a_directory_entry_whose_classification_fails_is_unreadable(certified_work, monkeypatch) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    real_scandir = os.scandir

    def scandir(fd):
        with real_scandir(fd) as scan:
            names = [entry.name for entry in scan]
        return _Scan([_FailingEntry(name, OSError(errno.EIO, "injected")) for name in names])

    monkeypatch.setattr(records.os, "scandir", scandir)
    surface = records.capture_surface(root, ("verification",))
    assert surface.records == ()
    assert surface.unreadable == ("verification/v.md",)
    assert surface.withheld == surface.uninspectable == ()


def test_a_scandir_failure_is_uninspectable_unless_it_is_enoent(certified_work, monkeypatch) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    for code, expected in ((errno.EACCES, ("verification",)), (errno.ENOENT, ())):

        def scandir(fd, code=code):
            raise OSError(code, "injected")

        monkeypatch.setattr(records.os, "scandir", scandir)
        surface = records.capture_surface(root, ("verification",))
        assert surface.records == ()
        assert surface.uninspectable == expected, code


def test_the_log_evaluator_surface_is_pinned(certified_work) -> None:
    # cut 11's captured surface: the three namespaces, silent on every failure.
    root = _five(certified_work / "root")
    (root / "run" / "ok.md").write_bytes(b"ok")
    (root / "run" / "big.md").write_bytes(b"x" * (records.RECORD_CEILING + 1))
    (root / "verification" / "v.md").write_bytes(b"v")
    assert records.capture_records(root, "corpus") == (("run/ok.md", b"ok"),)
```

Ensure `from pathlib import Path` and `import os` are imported at the top of the test file (both already are) and add `import errno`.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && set -o pipefail && uv run pytest tests/test_record_capture.py | tail -2
```

Expected: `AttributeError: module 'science.world.records' has no attribute 'capture_surface'` (and `CapturedSurface`).


- [ ] **Step 3: Rewrite `records.py`**

```python
"""The shared ceiling and fd-anchored, classified, bounded record capture."""

from __future__ import annotations

import errno
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from science.world.verify import RootKind

RECORD_CEILING = 8 * 1024 * 1024
"""Maximum bytes in a qualifying published record (spec §3.1)."""

RECORD_NAMESPACES = ("run", "act-report", "holdings-observation")


def _leaf_seam(path: str) -> None:
    """Interpose after enumeration and before the no-follow leaf open."""


@dataclass(frozen=True)
class CapturedSurface:
    """One descent's records and its three named failures (successor-admission
    design §4.2). `records` is exactly what `capture_records` returns over the
    same namespaces; the path lists are what it used to swallow."""

    records: tuple[tuple[str, bytes], ...]
    withheld: tuple[str, ...]
    """Regular files withheld for size."""
    unreadable: tuple[str, ...]
    """Leaves the descent could not characterise: directory-entry
    classification, `O_PATH` open, readable open, `fstat` re-check or read
    failed."""
    uninspectable: tuple[str, ...]
    """Directories that exist but could not be opened or enumerated — every
    failure but `ENOENT`, which is an absent namespace and is silent."""


@dataclass
class _Descent:
    records: list[tuple[str, bytes]] = field(default_factory=list)
    withheld: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    uninspectable: list[str] = field(default_factory=list)


_LeafFailure = Literal["withheld", "unreadable", "silent"]


def capture_records(
    root: Path,
    kind: RootKind,
) -> tuple[tuple[str, bytes], ...]:
    """Cut 11's captured surface, unchanged: the three record namespaces of a
    corpus root, every failure silent, nothing for any other root kind."""
    if kind != "corpus":
        return ()
    return capture_surface(root, RECORD_NAMESPACES).records


def capture_surface(root: Path, namespaces: tuple[str, ...]) -> CapturedSurface:
    into = _Descent()
    try:
        root_fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        into.uninspectable.append(".")
        return _finish(into)
    try:
        for namespace in namespaces:
            _capture_directory(root_fd, namespace, namespace, into)
    finally:
        os.close(root_fd)
    return _finish(into)


def _finish(into: _Descent) -> CapturedSurface:
    return CapturedSurface(
        tuple(sorted(into.records)),
        tuple(sorted(into.withheld)),
        tuple(sorted(into.unreadable)),
        tuple(sorted(into.uninspectable)),
    )


def _capture_directory(
    parent_fd: int,
    name: str,
    prefix: str,
    into: _Descent,
) -> None:
    try:
        dir_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError as failure:
        if failure.errno != errno.ENOENT:
            into.uninspectable.append(prefix)
        return
    try:
        try:
            with os.scandir(dir_fd) as scan:
                children = sorted(scan, key=lambda child: child.name)
        except OSError as failure:
            if failure.errno != errno.ENOENT:
                into.uninspectable.append(prefix)
            return
        for child in children:
            if child.name.startswith("."):
                continue
            path = f"{prefix}/{child.name}"
            try:
                is_directory = child.is_dir(follow_symlinks=False)
            except OSError:
                into.unreadable.append(path)
                continue
            if is_directory:
                _capture_directory(dir_fd, child.name, path, into)
                continue
            _leaf_seam(path)
            payload = _read_leaf(dir_fd, child.name)
            if isinstance(payload, bytes):
                into.records.append((path, payload))
            elif payload == "withheld":
                into.withheld.append(path)
            elif payload == "unreadable":
                into.unreadable.append(path)
    finally:
        os.close(dir_fd)


def _read_leaf(dir_fd: int, name: str) -> bytes | _LeafFailure:
    """Classify before a readable open; name every failure or oversize.

    A leaf that classifies as something other than a regular file is
    `silent` — not a record, never was. One the descent cannot classify or
    cannot read is `unreadable`; one over the ceiling is `withheld`."""
    try:
        path_fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=dir_fd)
    except OSError:
        return "unreadable"
    try:
        try:
            if not stat.S_ISREG(os.fstat(path_fd).st_mode):
                return "silent"
        except OSError:
            return "unreadable"
        try:
            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)
        except OSError:
            return "unreadable"
        try:
            chunks: list[bytes] = []
            remaining = RECORD_CEILING + 1
            while remaining > 0:
                chunk = os.read(read_fd, min(remaining, 1 << 20))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            return "withheld" if len(data) > RECORD_CEILING else data
        except OSError:
            return "unreadable"
        finally:
            os.close(read_fd)
    finally:
        os.close(path_fd)
```

Every failure the descent can meet is named: a directory open or `scandir` failing with anything but `ENOENT` is `uninspectable`; a directory entry whose classification raises, or a leaf whose `O_PATH` open, `fstat`, readable open or read fails, is `unreadable`; nothing escapes as a raw exception. `capture_records` still returns `()` when the root itself cannot be opened, because `_finish` yields empty records and `capture_records` reads only `.records`.

- [ ] **Step 4: Run the capture tests, the audit and evaluator suites, and lint**

```bash
cd python && set -o pipefail && uv run pytest tests/test_record_capture.py tests/test_world_log_audit.py tests/test_world_log_evaluator.py | tail -1
uv run ruff check src/science/world/records.py tests/test_record_capture.py && uv run pyright src/science/world/records.py | tail -1
```

Expected: all passed; clean. (The swap-race test in `test_record_capture.py` monkeypatches `_leaf_seam`; it must still pass unchanged.)

- [ ] **Step 5: Commit**

```bash
git add python/src/science/world/records.py python/tests/test_record_capture.py
git commit -m "feat(records): name the descent's failures beside the unchanged record capture"
```

---

### Task 5: `decode_node`, `record_paths_of`, `reduce_registration`

**Files:**
- Modify: `python/src/science/intents/evidence.py` (`decode_record` split)
- Modify: `python/src/science/intents/reduce.py` (`_qualify_one` split; `__all__`)
- Modify: `python/tests/acceptance/n2_arms_cut11.py` (two anchors, whitespace only)
- Test: `python/tests/test_intent_evidence.py`, `python/tests/test_intent_reduce.py` (append)

**Interfaces:**
- Produces: `science.intents.evidence.RecordEvidence` (the closed union `RunEvidence | ReportEvidence | ObservationEvidence | InertRecord`); `science.intents.evidence.decode_node(path: str, payload: bytes) -> Node` (raises `RecordUndecodable`); `science.intents.reduce.RegistrationReduction(match: tuple[str, RecordEvidence] | None, unresolved: bool, reasons: tuple[str, ...])`; `record_paths_of(registration: RegisteredEntryView, state_facts: StateFacts) -> list[str]`; `reduce_registration(intent: shapes.DecodedIntent, record_paths: list[str], records: Mapping[str, bytes]) -> RegistrationReduction`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_intent_evidence.py` (add `from science.intents.evidence import decode_node`, `from science.errors import RecordUndecodable`, `from nodes.core.frontmatter import node_to_markdown`, and `from science import stored` where absent):

```python
def _verification_bytes(slug: str = "v1") -> bytes:
    node = stored.verification_node(
        slug,
        title=slug,
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    return node_to_markdown(node).encode("utf-8")


def test_decode_node_returns_the_stamped_node_for_its_own_path() -> None:
    node = decode_node("verification/v1.md", _verification_bytes())
    assert node.id == "verification:v1"
    assert node.kind == "verification"


def test_decode_node_refuses_an_id_that_names_another_path() -> None:
    with pytest.raises(RecordUndecodable, match="does not name this path"):
        decode_node("verification/other.md", _verification_bytes())


def test_decode_node_refuses_a_stale_stamp() -> None:
    node = stored.verification_node(
        "v1",
        title="v1",
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    node.facets["verification"]["verdict"] = "passed"  # after the stamp
    with pytest.raises(RecordUndecodable, match="semantic stamp"):
        decode_node("verification/v1.md", node_to_markdown(node).encode("utf-8"))


def test_decode_node_refuses_a_missing_stamp() -> None:
    node = stored.verification_node(
        "v1",
        title="v1",
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    del node.facets[stored.SEMANTIC_IDENTITY_FACET]
    with pytest.raises(RecordUndecodable, match="semantic stamp"):
        decode_node("verification/v1.md", node_to_markdown(node).encode("utf-8"))


def test_decode_node_refuses_bytes_that_are_not_a_record() -> None:
    with pytest.raises(RecordUndecodable):
        decode_node("verification/v1.md", b"---\nnot: [a record\n---\n")
```

Append to `python/tests/test_intent_reduce.py` (add `from science.intents import shapes` and `from science.intents.reduce import RegistrationReduction, record_paths_of, reduce_registration` to its imports):

```python
def _decoded(payload: bytes = _assessment_payload()) -> shapes.DecodedIntent:
    gate = shapes.decode_intent("i1", payload)
    assert type(gate) is shapes.DecodedIntent
    return gate


def test_record_paths_of_keeps_record_layout_files_in_final_order(run_path) -> None:
    registration = _registration("r1", "i1", "notes/memo.md", run_path, absent=("run/gone.md",))
    assert record_paths_of(registration, _facts) == [run_path]


def test_reduce_registration_first_match_in_order_wins(
    run_path, run_bytes, wrong_spec_run_path, wrong_spec_run_bytes
) -> None:
    records = {run_path: run_bytes, wrong_spec_run_path: wrong_spec_run_bytes}
    reduction = reduce_registration(_decoded(), [wrong_spec_run_path, run_path], records)
    assert reduction.match is not None
    assert reduction.match[0] == run_path
    assert type(reduction.match[1]) is shapes.RunEvidence
    assert reduction.reasons == ("wrong-spec",)
    assert reduction.unresolved is False


def test_reduce_registration_names_an_undecodable_sibling_beside_a_later_match(run_path, run_bytes) -> None:
    records = {"run/bad.md": b"not a record", run_path: run_bytes}
    reduction = reduce_registration(_decoded(), ["run/bad.md", run_path], records)
    assert reduction.match is not None and reduction.match[0] == run_path
    assert reduction.unresolved is True


def test_reduce_registration_with_no_match_returns_every_reason_in_order(
    wrong_spec_run_path, wrong_spec_run_bytes, production_run_path, production_run_bytes
) -> None:
    records = {wrong_spec_run_path: wrong_spec_run_bytes, production_run_path: production_run_bytes}
    reduction = reduce_registration(_decoded(), [production_run_path, wrong_spec_run_path], records)
    assert reduction == RegistrationReduction(None, False, ("wrong-shape", "wrong-spec"))


def test_reduce_registration_marks_a_missing_payload_unresolved() -> None:
    reduction = reduce_registration(_decoded(), ["run/missing.md"], {})
    assert reduction == RegistrationReduction(None, True, ())
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && set -o pipefail && uv run pytest tests/test_intent_evidence.py tests/test_intent_reduce.py | tail -2
```

Expected: `ImportError` for `decode_node` / `reduce_registration`.

- [ ] **Step 3: Factor `decode_node` out of `decode_record`**

In `python/src/science/intents/evidence.py`, set `__all__ = ["RecordEvidence", "decode_node", "decode_record", "record_layout_path"]`, add `from nodes.core.node import Node` and `from typing import TypeAlias` to the imports, define the closed evidence union the design names beneath the imports:

```python
RecordEvidence: TypeAlias = RunEvidence | ReportEvidence | ObservationEvidence | InertRecord
"""What one captured record decodes to — the closed union `reduce_registration`
carries as its match (successor-admission design §4.4)."""
```

and replace `decode_record` in full with these two functions (its return annotation becomes `RecordEvidence`):

```python
def decode_node(path: str, payload: bytes) -> Node:
    """The gate every captured record passes before any typed reader: the
    frontmatter parses, the semantic stamp is present and agrees, the id
    names this path, and the kind agrees with the id (spec §3.1;
    successor-admission design §4.4 step 1)."""
    try:
        node = node_from_markdown(payload.decode("utf-8"))
    except (UnicodeDecodeError, NodesError, YAMLError, ValueError) as caught:
        raise RecordUndecodable(f"{path}: {caught}") from caught
    try:
        if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):
            raise RecordUndecodable(
                f"{path}: the semantic stamp does not agree with the stored fields"
            )
    except (IdentityError, MalformedRecord) as caught:
        raise RecordUndecodable(
            f"{path}: the semantic projection is not encodable: {caught}"
        ) from caught
    kind, _, slug = node.id.partition(":")
    if not slug or path != f"{kind}/{slug}.md":
        raise RecordUndecodable(
            f"{path}: the record id {node.id!r} does not name this path"
        )
    if node.kind != kind:
        raise RecordUndecodable(
            f"{path}: the record kind {node.kind!r} disagrees with its id"
        )
    return node


def decode_record(path: str, payload: bytes) -> RecordEvidence:
    node = decode_node(path, payload)
    if node.kind == "run":
        try:
            publication = runrecord.decode_run_record(node)
        except (MalformedRecord, CanonicalTextRefused) as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if publication is None:
            return InertRecord()
        return RunEvidence(
            publication.shape,
            publication.spec_identity,
            publication.event_token,
        )
    if node.kind == "act-report":
        try:
            facet = stored.act_report_facet(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        return ReportEvidence(str(facet["operation"]), str(facet["event_token"]))
    if node.kind == "holdings-observation":
        try:
            value = stored.holdings_observation_value(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if node.id != f"holdings-observation:{value.identity()}":
            raise RecordUndecodable(
                f"{path}: the observation id disagrees with its identity"
            )
        return ObservationEvidence(
            f"store:{value.location.store_id}:{value.location.relative_path}",
            value.event_token,
        )
    return InertRecord()
```

The three typed branches are today's text verbatim; only the gate moved.

- [ ] **Step 4: Factor the two helpers out of `_qualify_one`**

In `python/src/science/intents/reduce.py`, set `__all__ = ["IntentQualification", "RegistrationReduction", "qualify_chain", "record_paths_of", "reduce_registration"]`, and add after `_is_file`:

```python
@sealed
@final
@dataclass(frozen=True, slots=True)
class RegistrationReduction:
    """One registration's whole reduction (successor-admission design §4.4):
    the first qualifying `(path, evidence)` in `final` order, whether any
    record path had no payload or failed to decode, and every decoded
    non-qualifying record's reason in order."""

    match: tuple[str, evidence_module.RecordEvidence] | None
    unresolved: bool
    reasons: tuple[str, ...]


def record_paths_of(registration: RegisteredEntryView, state_facts: StateFacts) -> list[str]:
    return [
        path
        for path, state in registration.final
        if evidence_module.record_layout_path(path) and _is_file(state_facts(state))
    ]


def reduce_registration(
    intent: shapes.DecodedIntent,
    record_paths: list[str],
    records: Mapping[str, bytes],
) -> RegistrationReduction:
    reasons: list[str] = []
    pointer_unresolved = False
    for path in record_paths:
        payload = records.get(path)
        if payload is None:
            pointer_unresolved = True
            continue
        try:
            record_evidence = evidence_module.decode_record(path, payload)
        except RecordUndecodable:
            pointer_unresolved = True
            continue
        reason = shapes.mismatch(intent, record_evidence)
        if reason is None:
            return RegistrationReduction((path, record_evidence), pointer_unresolved, tuple(reasons))
        reasons.append(reason)
    return RegistrationReduction(None, pointer_unresolved, tuple(reasons))
```

Then rewrite `_qualify_one`'s registration loop so the settlement lookup and both `no-record` blocks are **byte-identical** to today and the inner loop is the call:

```python
    for registration in registrations:
        committed = settlement.get(registration.digest)
        if committed is None:
            unresolved = True
            continue
        if not committed:
            non_qualifying.append((registration.digest, "no-record"))
            continue
        record_paths = record_paths_of(registration, state_facts)
        if not record_paths:
            non_qualifying.append((registration.digest, "no-record"))
            continue
        reduction = reduce_registration(intent, record_paths, records)
        if reduction.match is not None:
            return (
                IntentQualification(
                    intent.digest,
                    intent.shape,
                    "matched",
                    registration.digest,
                ),
                (),
            )
        if reduction.unresolved:
            unresolved = True
            continue
        chosen = (
            min(reduction.reasons, key=shapes.REASON_PRIORITY.index)
            if reduction.reasons
            else "no-record"
        )
        non_qualifying.append((registration.digest, chosen))
```

The tail of `_qualify_one` (from `if unresolved:` down) is unchanged.

- [ ] **Step 5: Re-indent the two cut-11 anchors, whitespace only**

In `python/tests/acceptance/n2_arms_cut11.py`, the two sabotages whose `before` text was inside the moved loop now sit four columns shallower. Change exactly these strings — nothing else in the file:

```python
# was: before="except RecordUndecodable:\n                pointer_unresolved = True",
#      after='except RecordUndecodable:\n                reasons.append("no-record")',
before="except RecordUndecodable:\n            pointer_unresolved = True",
after='except RecordUndecodable:\n            reasons.append("no-record")',

# was: before="if payload is None:\n                pointer_unresolved = True\n                continue",
#      after="if payload is None:\n                continue",
before="if payload is None:\n            pointer_unresolved = True\n            continue",
after="if payload is None:\n            continue",
```

Then verify every cut-11 anchor still matches exactly once:

```bash
cd python && uv run python - <<'EOF'
import sys
sys.path[:0] = ["tests", "tests/acceptance"]
from pathlib import Path
from n2_arms_cut11 import CUT11_ARMS
bad = [a.row for a in CUT11_ARMS if Path("src/science", a.sabotage.module).read_text().count(a.sabotage.before) != 1]
assert not bad, f"stale cut-11 anchors: {bad}"
print("every cut-11 anchor matches once")
EOF
```

Expected: `every cut-11 anchor matches once`.

- [ ] **Step 6: Run the reducer, evidence and consumer suites, then lint**

```bash
cd python && set -o pipefail && uv run pytest tests/test_intent_evidence.py tests/test_intent_reduce.py tests/test_consumer_agreement.py tests/test_world_log_evaluator.py tests/test_world_log_audit.py | tail -1
uv run ruff check src/science/intents tests/test_intent_evidence.py tests/test_intent_reduce.py tests/acceptance/n2_arms_cut11.py && uv run pyright src/science/intents | tail -1
```

Expected: all passed; clean.

- [ ] **Step 7: Commit, and rule it in the ledger**

```bash
git add python/src/science/intents/evidence.py python/src/science/intents/reduce.py python/tests/test_intent_evidence.py python/tests/test_intent_reduce.py python/tests/acceptance/n2_arms_cut11.py
git commit -m "refactor(intents): factor the record gate and the registration reduction into values"
git rev-parse --short HEAD
```

Append to the ledger's rulings: `4. **R4 — cut 11's arm file moved at <hash>.** The two re-indented anchors are the only diff; Task 7 pins this hash.` and commit the ledger: `git commit -am "docs(plans): record the cut-11 anchor move"`.

---

### Task 6: `admit_spec_successor`, complete

The public boundary lands in one commit, every gate present. A committed `admit_spec_successor` that admits over live failing evidence would be exactly the silent fallback this repo forbids, so the class-1a derivation is not split into a later task.

**Files:**
- Create: `python/src/science/succession.py`
- Create: `python/tests/succession_fixtures.py`
- Test: `python/tests/test_succession.py`

**Interfaces:**
- Consumes: Task 2's `AdmissionEvidenceRefused`; Task 3's `admit_successor`; Task 4's `capture_surface`; Task 5's `decode_node`, `record_paths_of`, `reduce_registration`; `nodes.core.structural_index.Index` (`assert_addable`, `upsert`, `resolve_uid`, `outbound_edges(uid) -> list[ResolvedEdge]`, `ResolvedEdge.relation`, `.target_uid`).
- Produces: `science.succession.admit_spec_successor(candidate, superseded, *, seam, root)` — the module's one export; the module-level constants `REASONS` and `EVIDENCE_NAMESPACES` are imported by name in tests and arms but are not in `__all__`.

- [ ] **Step 1: Write the fixture module**

`python/tests/succession_fixtures.py`:

```python
"""Fabricated roots for the successor-admission tests: real engine, real seam.

Every blocker is genuine durable state — records through the port's
non-fulfilling `execute`, intents through `append_intent`, reports through
`execute_fulfilling` (cut 12 §6). Nothing here hands the act a set.
"""

from __future__ import annotations

from pathlib import Path

from fixtures_cut3 import spec_draft, spec_rules
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp
from test_operation_port import durable_port

from science import root as science_root
from science import stored
from science.identity import v1
from science.root import init_corpus_root
from science.spec import FrozenSpec, SuccessorAdmitted, SuccessorRefused, freeze, revise
from science.succession import admit_spec_successor

RUN = "run:r1"
PROPOSITION = "proposition:p1"
RULE = "rule:threshold"


def corpus(work: Path, name: str):
    root = work / name
    init_corpus_root(root)
    return root, durable_port(root)


def specs() -> tuple[FrozenSpec, FrozenSpec, FrozenSpec]:
    """`(original, unreferenced, referencing)` — the second supersedes nothing,
    the third supersedes the first by construction."""
    original = freeze(spec_draft(), held_rules=spec_rules())
    unreferenced = freeze(spec_draft(estimand="revised"), held_rules=spec_rules())
    referencing = revise(
        original, edits={"estimand": "revised"}, held_rules=spec_rules(), recorded_failures=frozenset()
    )
    return original, unreferenced, referencing


def assessment(spec_identity: str, slug: str = "a1") -> Node:
    return stored.assessment_node(
        slug,
        title=slug,
        spec=spec_identity,
        run=RUN,
        proposition=PROPOSITION,
        outcome="refuted",
        interpretation_rule=RULE,
    )


def identity_of(assessment_node: Node) -> str:
    return stored.assessment_value(assessment_node).identity()


def verification(slug: str, target: Node, verdict: str, *, supersedes: str | None = None) -> Node:
    return stored.verification_node(
        slug,
        title=slug,
        assessment=identity_of(target),
        assessment_ref=target.id,
        scope="clean-environment",
        verdict=verdict,
        supersedes=supersedes,
    )


def path_of(node: Node) -> str:
    kind, _, slug = node.id.partition(":")
    return f"{kind}/{slug}.md"


def plan(*nodes: Node) -> tuple[CreateOp, ...]:
    return tuple(CreateOp(path_of(node), node_to_markdown(node).encode("utf-8")) for node in nodes)


def publish(port, *nodes: Node) -> None:
    port.execute(plan(*nodes))


def append_assessment_intent(port, spec_identity: str, token: str = "tok") -> str:
    return port.append_intent(v1.encode({"spec_identity": spec_identity, "event_token": token, "actor": "a"}))


def seam():
    return science_root._log_seam()


def admit(root: Path, candidate: FrozenSpec, superseded: FrozenSpec) -> SuccessorAdmitted | SuccessorRefused:
    return admit_spec_successor(candidate, superseded, seam=seam(), root=root)
```

- [ ] **Step 2: Write the failing tests**

`python/tests/test_succession.py`:

```python
"""`admit_spec_successor` over fabricated roots (successor-admission design §4)."""

from __future__ import annotations

import os

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from nodes.core.write_plan import CreateOp
from succession_fixtures import (
    admit,
    append_assessment_intent,
    assessment,
    corpus,
    publish,
    specs,
    verification,
)

from science import stored
from science.errors import AdmissionEvidenceRefused
from science.runrecord import publication_plan
from science.spec import SuccessorAdmitted, SuccessorRefused
from science.succession import REASONS
from science.world.records import RECORD_CEILING


def _refuses(root, candidate, superseded, reason: str) -> AdmissionEvidenceRefused:
    with pytest.raises(AdmissionEvidenceRefused) as caught:
        admit(root, candidate, superseded)
    assert caught.value.reason == reason
    return caught.value


def _report_plan(report):
    node = stored.act_report_node(report)
    return (CreateOp(f"act-report/{report.identity()}.md", node_to_markdown(node).encode("utf-8")),)


def _raw(port, path: str, payload: bytes) -> None:
    port.execute((CreateOp(path, payload),))


def _oversized(root, path: str) -> None:
    (root / path).parent.mkdir(exist_ok=True)
    (root / path).write_bytes(b"x" * (RECORD_CEILING + 1))


def _failing_pair(port, spec_identity: str, slug: str = "v1"):
    target = assessment(spec_identity)
    failing = verification(slug, target, "failed")
    publish(port, target, failing)
    return target, failing


# --- G4u13, K4: before the derivation ---------------------------------------------


def test_the_reason_set_is_exactly_the_specs_eleven() -> None:
    assert REASONS == (
        "root unreadable",
        "chain not well-formed",
        "namespace uninspectable",
        "verification unreadable",
        "assessment unreadable",
        "verification oversized",
        "verification edge cardinality",
        "verification target unreadable",
        "verification target mismatch",
        "record collision",
        "qualification unresolved for the superseded spec",
    )


def test_an_absent_root_refuses_before_any_lock(certified_work) -> None:
    original, unreferenced, _ = specs()
    refused = _refuses(certified_work / "nowhere", unreferenced, original, "root unreadable")
    assert refused.ref == str((certified_work / "nowhere").resolve())


def test_a_file_where_the_root_should_be_refuses_as_unreadable(certified_work) -> None:
    # `root` is resolved before the `O_DIRECTORY | O_NOFOLLOW` open (design
    # §4.1), so a symlink to a real corpus admits through its target; what
    # the open refuses is a path that is not a directory at all.
    not_a_directory = certified_work / "file"
    not_a_directory.write_bytes(b"")
    original, unreferenced, _ = specs()
    assert _refuses(not_a_directory, unreferenced, original, "root unreadable").ref == str(not_a_directory.resolve())


def test_an_unregistered_directory_is_an_absent_chain_and_refuses(certified_work) -> None:
    root = certified_work / "bare"
    root.mkdir()
    original, unreferenced, _ = specs()
    _refuses(root, unreferenced, original, "chain not well-formed")


def test_an_unenumerable_namespace_refuses_for_verification_and_for_run(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user"
    original, unreferenced, _ = specs()
    for namespace in ("verification", "run"):
        root, _ = corpus(certified_work, f"locked-{namespace}")
        locked = root / namespace
        locked.mkdir()
        locked.chmod(0)
        try:
            refused = _refuses(root, unreferenced, original, "namespace uninspectable")
        finally:
            locked.chmod(0o755)
        assert refused.ref == namespace


def test_an_absent_verification_namespace_admits(certified_work) -> None:
    root, _ = corpus(certified_work, "empty")
    original, unreferenced, _ = specs()
    assert not (root / "verification").exists()
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


# --- G4u2, G4u12, G4u10, L7u15, L7u16: class 2 from the chain -------------------------


def test_an_unfinished_attempt_blocks_an_unreferenced_successor(certified_work) -> None:
    root, port = corpus(certified_work, "unfinished")
    original, unreferenced, referencing = specs()
    append_assessment_intent(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_an_unfinished_attempt_for_another_spec_blocks_nothing(certified_work) -> None:
    root, port = corpus(certified_work, "other-spec")
    original, unreferenced, _ = specs()
    append_assessment_intent(port, "f" * 64)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_the_negative_nothing_durable_admits(certified_work) -> None:
    # G4u12: the attempt and its intent discarded before any append — no class
    # holds a trace, and the successor is admitted. Crash, cancellation and
    # discarded failure are indistinguishable by construction.
    root, _ = corpus(certified_work, "negative")
    original, unreferenced, _ = specs()
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_decayed_run_under_the_superseded_spec_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "decayed")
    original, unreferenced, _ = specs()
    _, path, plan = publication_plan(make_closure(spec=original.identity))
    intent = append_assessment_intent(port, original.identity)
    port.execute_fulfilling(plan, intent)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])
    refused = _refuses(root, unreferenced, original, "qualification unresolved for the superseded spec")
    assert refused.ref == intent


def test_a_decayed_run_under_another_spec_does_not_block(certified_work) -> None:
    root, port = corpus(certified_work, "decayed-other")
    original, unreferenced, _ = specs()
    other = "e" * 64
    _, path, plan = publication_plan(make_closure(spec=other))
    port.execute_fulfilling(plan, append_assessment_intent(port, other))
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_qualifying_run_lifts_the_block(certified_work) -> None:
    # L7u16
    root, port = corpus(certified_work, "qualified")
    original, unreferenced, _ = specs()
    _, _, plan = publication_plan(make_closure(spec=original.identity))
    port.execute_fulfilling(plan, append_assessment_intent(port, original.identity))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_wrong_spec_publication_fails_qualification_and_the_intent_still_blocks(certified_work) -> None:
    # L7u15
    root, port = corpus(certified_work, "wrong-spec")
    original, unreferenced, _ = specs()
    _, _, plan = publication_plan(make_closure(spec="x" * 64))
    port.execute_fulfilling(plan, append_assessment_intent(port, original.identity))
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"


# --- G4u3, G4u14: class 1b from run-attempt reports ------------------------------------


def test_a_run_attempt_report_is_a_recorded_failure(certified_work) -> None:
    root, port = corpus(certified_work, "run-attempt")
    original, unreferenced, referencing = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    port.execute_fulfilling(_report_plan(sample_report(operation="run-attempt", token="tok")), intent)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_an_undecodable_sibling_before_the_qualifying_report_still_joins(certified_work) -> None:
    # G4u14: the registration carries `act-report/aaa.md` (undecodable, sorts
    # first) and the qualifying run-attempt report; `matched` is the reducer's
    # verdict and the report is the match.
    root, port = corpus(certified_work, "sibling")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    report = sample_report(operation="run-attempt", token="tok")
    port.execute_fulfilling(
        (CreateOp("act-report/aaa.md", b"not a record"), *_report_plan(report)),
        intent,
    )
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_a_qualifying_run_beside_a_report_joins_nothing(certified_work) -> None:
    # G4u14, the other half: one registration carries both a qualifying run and
    # a qualifying run-attempt report. `final` is path-ordered and
    # `act-report/` sorts before `run/`, so the report would match first — the
    # arm therefore publishes the report under a token that does not qualify,
    # leaving the run the first (and only) qualifying record, and asserts a
    # `RunEvidence` match is a minted run, not a failure.
    root, port = corpus(certified_work, "run-and-report")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    _, _, run_plan = publication_plan(make_closure(spec=original.identity, token="tok"))
    stray = _report_plan(sample_report(operation="run-attempt", token="other"))
    port.execute_fulfilling((*stray, *run_plan), intent)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_qualifying_report_before_a_qualifying_run_is_the_match(certified_work) -> None:
    # G4u14, the mixed registration proper: both records qualify; the report
    # sorts first in `final`, so the reducer's first match is the report and
    # the spec joins class 1 — the act reads the record that matched, in the
    # reducer's order, never "whichever is a run".
    root, port = corpus(certified_work, "report-then-run")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    _, _, run_plan = publication_plan(make_closure(spec=original.identity, token="tok"))
    report = _report_plan(sample_report(operation="run-attempt", token="tok"))
    port.execute_fulfilling((*report, *run_plan), intent)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


# --- G4u1, G4u4, G4u5, G4u6: class 1a ---------------------------------------------------


def test_a_live_failing_verification_blocks_an_unreferenced_successor(certified_work) -> None:
    root, port = corpus(certified_work, "failing")
    original, unreferenced, referencing = specs()
    _failing_pair(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_a_failing_verification_for_another_spec_blocks_nothing(certified_work) -> None:
    root, port = corpus(certified_work, "failing-other")
    original, unreferenced, _ = specs()
    _failing_pair(port, "d" * 64)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_passing_verification_is_not_blocker_evidence(certified_work) -> None:
    root, port = corpus(certified_work, "passing")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target, verification("v1", target, "passed"))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_overlap_refuses_with_the_recorded_failure_reason(certified_work) -> None:
    # G4u5: the same spec is in both classes.
    root, port = corpus(certified_work, "overlap")
    original, unreferenced, _ = specs()
    _failing_pair(port, original.identity)
    append_assessment_intent(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_a_coherent_passing_superseder_lifts_the_block(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-pass")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    publish(port, verification("v2", target, "passed", supersedes=failing.id))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_failing_superseder_keeps_the_block_through_the_active_member(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-fail")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    publish(port, verification("v2", target, "failed", supersedes=failing.id))
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_an_incoherent_passing_superseder_refuses_naming_itself(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-incoherent")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    superseder = verification("v2", target, "passed", supersedes=failing.id)
    superseder.relations = []  # zero `verifies` edges; the stamp covers the facet, not relations
    publish(port, superseder)
    refused = _refuses(root, unreferenced, original, "verification edge cardinality")
    assert refused.ref == "verification/v2.md"


# --- G4u7: the evidence gate -------------------------------------------------------------


def test_a_stale_stamp_refuses_naming_the_path(certified_work) -> None:
    root, port = corpus(certified_work, "stale")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    stale = verification("v1", target, "failed")
    stale.facets["verification"]["verdict"] = "passed"
    publish(port, target, stale)
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/v1.md"


def test_a_missing_stamp_refuses_naming_the_path(certified_work) -> None:
    root, port = corpus(certified_work, "unstamped")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    bare = verification("v1", target, "failed")
    del bare.facets[stored.SEMANTIC_IDENTITY_FACET]
    publish(port, target, bare)
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/v1.md"


def test_an_id_naming_another_path_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "misnamed")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target)
    _raw(port, "verification/other.md", node_to_markdown(verification("v1", target, "failed")).encode("utf-8"))
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/other.md"


def test_an_undecodable_verification_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "undecodable")
    original, unreferenced, _ = specs()
    _raw(port, "verification/v1.md", b"---\nnot: [a record\n---\n")
    _refuses(root, unreferenced, original, "verification unreadable")


def test_an_undecodable_untargeted_assessment_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "bad-assessment")
    original, unreferenced, _ = specs()
    _raw(port, "assessment/a9.md", b"---\nnot: [a record\n---\n")
    assert _refuses(root, unreferenced, original, "assessment unreadable").ref == "assessment/a9.md"


def test_an_unreadable_regular_file_refuses_in_either_namespace(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user"
    original, unreferenced, _ = specs()
    for namespace, reason in (
        ("verification", "verification unreadable"),
        ("assessment", "assessment unreadable"),
    ):
        root, port = corpus(certified_work, f"locked-file-{namespace}")
        target = assessment(original.identity)
        publish(port, target, verification("v1", target, "failed"))
        locked = root / namespace / ("v1.md" if namespace == "verification" else "a1.md")
        locked.chmod(0)
        try:
            refused = _refuses(root, unreferenced, original, reason)
        finally:
            locked.chmod(0o644)
        assert refused.ref == f"{namespace}/{locked.name}"


# --- G4u8: the coherence gate -------------------------------------------------------------


def test_two_verifies_edges_refuse(certified_work) -> None:
    root, port = corpus(certified_work, "two-edges")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    other = assessment(original.identity, slug="a2")
    doubled = verification("v1", target, "failed")
    doubled.relations.append(Relation(source=doubled.id, predicate=stored.VERIFIES, target=other.id))
    publish(port, target, other, doubled)
    _refuses(root, unreferenced, original, "verification edge cardinality")


def test_a_relation_sourced_elsewhere_is_not_this_verifications_edge(certified_work) -> None:
    # The gate counts outbound edges, not stored relations: the one `verifies`
    # relation this record stores runs from the assessment *to* the
    # verification, so it is an inbound edge of v1 and an outbound edge of a1
    # — and v1 has no outbound edge at all.
    root, port = corpus(certified_work, "foreign-source")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    mislabeled = verification("v1", target, "failed")
    mislabeled.relations = [Relation(source=target.id, predicate=stored.VERIFIES, target=mislabeled.id)]
    publish(port, target, mislabeled)
    assert _refuses(root, unreferenced, original, "verification edge cardinality").ref == "verification/v1.md"


def test_a_target_that_is_not_an_assessment_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "wrong-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    astray = verification("v1", target, "failed")
    astray.relations[0].target = "verification:v1"
    publish(port, target, astray)
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_missing_target_refuses(certified_work) -> None:
    # An unrelated assessment is present so that "some assessment" is never an
    # acceptable stand-in for the one the edge names: the refusal must be the
    # target's absence, not a mismatch against whatever happened to be there.
    root, port = corpus(certified_work, "missing-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    bystander = assessment("b" * 64, slug="a9")
    publish(port, bystander, verification("v1", target, "failed"))  # `target` is never published
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_deprecated_id_target_resolves_and_blocks(certified_work) -> None:
    root, port = corpus(certified_work, "deprecated")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    target.deprecated_ids = ["assessment:old"]
    stored.stamp_semantic_identity(target)
    pointing = verification("v1", target, "failed")
    pointing.relations[0].target = "assessment:old"
    publish(port, target, pointing)
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_a_uid_collision_refuses_naming_the_colliding_id(certified_work) -> None:
    root, port = corpus(certified_work, "collision")
    original, unreferenced, _ = specs()
    first = assessment(original.identity, slug="a1")
    second = assessment(original.identity, slug="a2")
    second.uid = first.uid
    stored.stamp_semantic_identity(second)
    publish(port, first, second)
    # Paths are read in sorted order, so `assessment/a2.md` is the node whose
    # admission to the index collides; its id is the ref.
    assert _refuses(root, unreferenced, original, "record collision").ref == "assessment:a2"


def test_an_identity_mismatch_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "mismatch")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    other = assessment("c" * 64, slug="a2")
    swapped = verification("v1", other, "failed")  # facet identity is `other`'s
    swapped.relations[0].target = target.id  # edge points at `target`
    stored.stamp_semantic_identity(swapped)
    publish(port, target, other, swapped)
    assert _refuses(root, unreferenced, original, "verification target mismatch").ref == "verification/v1.md"


# --- G4u9: oversized records ------------------------------------------------------------------


def test_a_withheld_verification_without_a_superseder_refuses(certified_work) -> None:
    root, _ = corpus(certified_work, "big-alone")
    original, unreferenced, _ = specs()
    _oversized(root, "verification/big.md")
    assert _refuses(root, unreferenced, original, "verification oversized").ref == "verification/big.md"


def test_a_withheld_verification_with_a_coherent_superseder_is_skipped(certified_work) -> None:
    root, port = corpus(certified_work, "big-superseded")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target, verification("v2", target, "passed", supersedes="verification:big"))
    _oversized(root, "verification/big.md")
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_withheld_verification_with_an_incoherent_superseder_refuses_the_superseder(certified_work) -> None:
    root, port = corpus(certified_work, "big-incoherent")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    superseder = verification("v2", target, "passed", supersedes="verification:big")
    superseder.relations = []
    publish(port, target, superseder)
    _oversized(root, "verification/big.md")
    assert _refuses(root, unreferenced, original, "verification edge cardinality").ref == "verification/v2.md"


def test_a_withheld_assessment_targeted_by_a_failing_verification_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "big-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity, slug="big")
    publish(port, verification("v1", target, "failed"))
    _oversized(root, "assessment/big.md")
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_withheld_untargeted_assessment_is_ignored(certified_work) -> None:
    root, _ = corpus(certified_work, "big-untargeted")
    original, unreferenced, _ = specs()
    _oversized(root, "assessment/big.md")
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_decoded_node_claiming_a_withheld_paths_id_is_a_collision(certified_work) -> None:
    root, port = corpus(certified_work, "big-claimed")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    target.deprecated_ids = ["assessment:big"]
    stored.stamp_semantic_identity(target)
    publish(port, target)
    _oversized(root, "assessment/big.md")
    assert _refuses(root, unreferenced, original, "record collision").ref == "assessment:big"
```

- [ ] **Step 3: Run to verify they fail**

```bash
cd python && set -o pipefail && uv run pytest tests/test_succession.py | tail -2
```

Expected: `ModuleNotFoundError: No module named 'science.succession'`.

- [ ] **Step 4: Write the module**

`python/src/science/succession.py`:

```python
"""Successor admission over the durable evidence (successor-admission design §4).

`admit_spec_successor` is the deriving boundary: under the root's own
operation lock it reads the chain's qualification and the corpus's
verification and assessment records, composes G4's two blocker classes,
and calls the pure core with the derived sets — never a caller-invented
one. It lives here and not in `science.spec` because the derivation needs
the log seam, which imports `corpus`, which imports `spec` (design §2).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from nodes.core.errors import CollisionError
from nodes.core.node import Node
from nodes.core.structural_index import Index

from science import stored
from science import verification as verification_module
from science.errors import AdmissionEvidenceRefused, MalformedRecord, RecordUndecodable
from science.intents import shapes
from science.intents.evidence import decode_node
from science.intents.reduce import (
    IntentQualification,
    StateFacts,
    qualify_chain,
    record_paths_of,
    reduce_registration,
)
from science.record import AssessmentValue
from science.report import AssessmentRunIntent
from science.spec import FrozenSpec, SuccessorAdmitted, SuccessorRefused, admit_successor
from science.verification import Verification
from science.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView
from science.world.records import RECORD_NAMESPACES, CapturedSurface, capture_surface
from science.world.verify import LogSeam

__all__ = ["admit_spec_successor"]

EVIDENCE_NAMESPACES = ("verification", "assessment")
"""The two namespaces class 1a reads beside cut 11's three. Module-level, not
exported: the tests import it by name."""

REASONS = (
    "root unreadable",
    "chain not well-formed",
    "namespace uninspectable",
    "verification unreadable",
    "assessment unreadable",
    "verification oversized",
    "verification edge cardinality",
    "verification target unreadable",
    "verification target mismatch",
    "record collision",
    "qualification unresolved for the superseded spec",
)
"""The closed reason set of `AdmissionEvidenceRefused` (design §5). Module-level,
not exported: the design's public surface is the one entrypoint."""


def admit_spec_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    *,
    seam: LogSeam,
    root: Path,
) -> SuccessorAdmitted | SuccessorRefused:
    """Admit or refuse `candidate` as a successor to `superseded`, over the
    evidence beneath `root` — one hold, one pinned order (design §4.2)."""
    root = Path(root).resolve()
    _require_openable_directory(root)
    with seam.corpus_lock(root):
        view = seam.inspect_registered(root)
        if type(view) is not WellFormedView:
            raise AdmissionEvidenceRefused("chain not well-formed", str(root))
        surface = capture_surface(root, RECORD_NAMESPACES + EVIDENCE_NAMESPACES)
        if surface.uninspectable:
            raise AdmissionEvidenceRefused("namespace uninspectable", surface.uninspectable[0])
        records = dict(surface.records)
        unfinished, report_failures = _chain_classes(
            superseded.identity, view, records, seam.state_facts
        )
        recorded_failures = _recorded_failures(surface, records) | report_failures
        return admit_successor(candidate, superseded, recorded_failures, unfinished)


def _require_openable_directory(root: Path) -> None:
    try:
        fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as failure:
        raise AdmissionEvidenceRefused("root unreadable", str(root)) from failure
    os.close(fd)


# --- class 2 and class 1b, from the chain ----------------------------------------


def _chain_classes(
    superseded_identity: str,
    view: WellFormedView,
    records: Mapping[str, bytes],
    state_facts: StateFacts,
) -> tuple[frozenset[str], frozenset[str]]:
    """Unfinished attempts and run-attempt-recorded failures from the chain's
    qualification, with the unresolved gate (design §4.3, §4.4 1b)."""
    rows, _ = qualify_chain(view.entries, records, state_facts=state_facts)
    intents = {entry.digest: entry for entry in view.entries if type(entry) is IntentEntryView}
    registrations = {
        entry.digest: entry for entry in view.entries if type(entry) is RegisteredEntryView
    }
    unfinished: set[str] = set()
    failures: set[str] = set()
    for row in rows:
        if row.shape != "assessment-run":
            continue
        decoded, spec_identity = _decoded_intent(row, intents[row.digest])
        if row.status == "unresolvable":
            if spec_identity == superseded_identity:
                raise AdmissionEvidenceRefused(
                    "qualification unresolved for the superseded spec", row.digest
                )
        elif row.status == "attempt-without-recorded-outcome":
            unfinished.add(spec_identity)
        elif row.status == "matched":
            assert row.fulfilled_by is not None, "a matched row names its registration"
            registration = registrations[row.fulfilled_by]
            reduction = reduce_registration(
                decoded, record_paths_of(registration, state_facts), records
            )
            assert reduction.match is not None, "the reducer called this registration matched"
            _, evidence = reduction.match
            if type(evidence) is shapes.ReportEvidence and evidence.operation == "run-attempt":
                failures.add(spec_identity)
    return frozenset(unfinished), frozenset(failures)


def _decoded_intent(
    row: IntentQualification, entry: IntentEntryView
) -> tuple[shapes.DecodedIntent, str]:
    decoded = shapes.decode_intent(row.digest, entry.payload)
    assert type(decoded) is shapes.DecodedIntent, "an assessment-run row decodes"
    value = decoded.value
    assert isinstance(value, AssessmentRunIntent), "an assessment-run row carries a spec"
    return decoded, value.spec_identity


# --- class 1a, from the verification evidence ---------------------------------------


def _recorded_failures(surface: CapturedSurface, records: Mapping[str, bytes]) -> frozenset[str]:
    """The specs of every active, coherent, failing verification (design
    §4.4 steps 1–5, §4.5)."""
    _refuse_unreadable(surface)
    nodes = _decoded_evidence(records)
    verifications, assessments = _typed(nodes)
    index = _index(nodes)
    withheld = _withheld_ids(surface)
    for ref in withheld:
        if index.resolve_uid(ref) is not None:
            raise AdmissionEvidenceRefused("record collision", ref)

    failing = {path: value for path, value in verifications.items() if value.verdict == "failed"}
    blockers = {value.ref for value in failing.values()} | {
        ref for ref in withheld if ref.startswith("verification:")
    }
    gated = {
        path: value
        for path, value in verifications.items()
        if path in failing or value.supersedes in blockers
    }
    by_uid = {node.uid: path for path, node in nodes.items()}
    targets: dict[str, AssessmentValue] = {}
    for path, value in gated.items():
        edges = [
            edge
            for edge in index.outbound_edges(nodes[path].uid)
            if edge.relation.predicate == stored.VERIFIES
        ]
        if len(edges) != 1:
            raise AdmissionEvidenceRefused("verification edge cardinality", path)
        edge = edges[0]
        if edge.relation.target in withheld:
            raise AdmissionEvidenceRefused("verification target unreadable", path)
        target_path = by_uid.get(edge.target_uid) if edge.target_uid is not None else None
        if target_path is None or target_path not in assessments:
            raise AdmissionEvidenceRefused("verification target unreadable", path)
        target = assessments[target_path]
        if target.identity() != value.assessment:
            raise AdmissionEvidenceRefused("verification target mismatch", path)
        targets[path] = target

    for ref, path in withheld.items():
        if ref.startswith("verification:") and not any(
            value.supersedes == ref for value in gated.values()
        ):
            raise AdmissionEvidenceRefused("verification oversized", path)

    active = {value.ref for value in verification_module.active(tuple(verifications.values()))}
    return frozenset(targets[path].spec for path, value in failing.items() if value.ref in active)


def _refuse_unreadable(surface: CapturedSurface) -> None:
    for path in surface.unreadable:
        kind = path.partition("/")[0]
        if kind in EVIDENCE_NAMESPACES:
            raise AdmissionEvidenceRefused(f"{kind} unreadable", path)


def _decoded_evidence(records: Mapping[str, bytes]) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for path in sorted(records):
        kind = path.partition("/")[0]
        if kind not in EVIDENCE_NAMESPACES:
            continue
        try:
            nodes[path] = decode_node(path, records[path])
        except RecordUndecodable as caught:
            raise AdmissionEvidenceRefused(f"{kind} unreadable", path) from caught
    return nodes


def _typed(nodes: Mapping[str, Node]) -> tuple[dict[str, Verification], dict[str, AssessmentValue]]:
    verifications: dict[str, Verification] = {}
    assessments: dict[str, AssessmentValue] = {}
    for path, node in nodes.items():
        try:
            if node.kind == "verification":
                verifications[path] = stored.verification_value(node)
            else:
                assessments[path] = stored.assessment_value(node)
        except MalformedRecord as caught:
            raise AdmissionEvidenceRefused(f"{node.kind} unreadable", path) from caught
    return verifications, assessments


def _index(nodes: Mapping[str, Node]) -> Index:
    """`Index.build`'s loop, admitting nodes in path order so the colliding
    record is the one named (design §5: the ref is the colliding id)."""
    index = Index()
    for path in sorted(nodes):
        node = nodes[path]
        try:
            index.assert_addable(node)
        except CollisionError as caught:
            raise AdmissionEvidenceRefused("record collision", node.id) from caught
        index.upsert(node)
    return index


def _withheld_ids(surface: CapturedSurface) -> dict[str, str]:
    """`kind:slug` for every withheld evidence path — the id the layout rule
    determines from the path alone (design §4.5)."""
    ids: dict[str, str] = {}
    for path in surface.withheld:
        kind, _, rest = path.partition("/")
        if kind in EVIDENCE_NAMESPACES and rest.endswith(".md"):
            ids[f"{kind}:{rest[:-3]}"] = path
    return ids
```

The coherence gate reads `index.outbound_edges(uid)` — edges whose **source** is this node — and filters by predicate, so a stored `verifies` relation whose `source` names another node is not this verification's edge. `_index` runs `Index.build`'s own `assert_addable`/`upsert` loop in path order so the offending node's id is in hand for the refusal; `Index.build` itself would raise with only the uid in its message. The four `assert`s state invariants of values the reducer just produced; they are not input validation.

- [ ] **Step 5: Run the suite, lint, and the capability-boundary audit**

```bash
cd python && set -o pipefail && uv run pytest tests/test_succession.py | tail -1
uv run ruff check src/science/succession.py tests/test_succession.py tests/succession_fixtures.py && uv run pyright src/science/succession.py | tail -1
uv run pytest tests/test_capability_boundary.py | tail -1
```

Expected: all passed; clean; passed. The capability audit polices three things — naming `Corpus` outside the write API, importing `atoms` outside the composition root, and naming an engine command outside it — and `succession.py` does none: its engine access is the `LogSeam` value it is handed, and its `nodes.core` imports are `Node`, `Index` and `CollisionError`.

- [ ] **Step 6: Commit**

```bash
git add python/src/science/succession.py python/tests/succession_fixtures.py python/tests/test_succession.py
git commit -m "feat(succession): admit a spec successor over the chain's qualification and the corpus's failing evidence"
```

---

### Task 7: The acceptance layer — durable tests, arms, N2 harness, runner

**Files:**
- Create: `python/tests/acceptance/test_successor_admission_acceptance.py`
- Create: `python/tests/acceptance/n2_arms_cut12.py`
- Create: `python/tests/acceptance/test_n2_cut12.py`
- Create: `python/tools/cut12_acceptance.py`
- Modify: `python/tests/conftest.py` (`certified_work` honours `SCIENCE_CUT12_ROOT`)

**Interfaces:**
- Consumes: every unit id from the frozen cut; the freeze hash (ledger, Task 1); the cut-11 anchor-move hash (ledger R4, Task 5).
- Produces: `CUT12_ARMS`, `ROW_UNITS`, `LABELED_UNITS`, `CO_CITED`, `unit_of`; the runner Task 8 executes.

- [ ] **Step 1: Let the durable fixture take cut 12's root**

In `python/tests/conftest.py`, change `configured = os.environ.get("SCIENCE_CUT10_ROOT")` inside `certified_work` to `configured = os.environ.get("SCIENCE_CUT10_ROOT") or os.environ.get("SCIENCE_CUT12_ROOT")`. Cut 10's variable stays first: the cut-11 prefix runner sets `SCIENCE_CUT10_ROOT` for its nested run, and an outer cut-12 root must not override the root that prefix chose. The cut-12 runner sets every variable from cut 4 to cut 12 to one directory, so under it the two agree.

- [ ] **Step 2: Write the durable acceptance tests**

`python/tests/acceptance/test_successor_admission_acceptance.py`:

```python
"""Cut 12's durable arms that need a live boundary, a chain mutation, or a
second writer: G4u11 (snapshot coherence), R12u1–u2, L7u14."""

from __future__ import annotations

import dataclasses
import threading
import time

import pytest
from closure_fixtures import make_closure
from succession_fixtures import (
    admit,
    append_assessment_intent,
    assessment,
    corpus,
    publish,
    seam,
    specs,
    verification,
)
from test_world_log_audit import corpus_anchor, real_audit

from science.errors import AdmissionEvidenceRefused
from science.runrecord import publication_plan
from science.spec import SuccessorAdmitted, SuccessorRefused
from science.succession import admit_spec_successor
from science.world import anchors, registry
from science.world.logmodel import MalformedView, RegisteredEntryView, WellFormedView

CHAIN_LEAF = ".#~chain"
CORPUS_ID = "a" * 32


def test_u11_a_writer_arriving_during_the_act_waits_and_is_not_consulted(certified_work) -> None:
    """The writer starts only once the act holds the root's operation lock —
    the seam's `inspect_registered` runs inside that hold, and the interposed
    seam starts the writer there. The writer queues behind the act (the lock
    admits one holder); the act's derivation never sees the blocker; the
    writer lands after the verdict; the next act consults it."""
    root, port = corpus(certified_work, "snapshot")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    blocker = verification("v1", target, "failed")
    order: list[str] = []

    def write_blocker() -> None:
        # `DurableOperationPort.execute` takes no lock of its own — the
        # production writers (`CorpusWriter`) do, through the very object
        # `corpus_lock` returns — so this writer takes it the way they do.
        order.append("writer-started")
        with production.corpus_lock(root):
            publish(port, target, blocker)
        order.append("writer-done")

    production = seam()
    writer = threading.Thread(target=write_blocker)

    def inspect_then_start_writer(path):
        view = production.inspect_registered(path)  # we are inside the act's hold
        writer.start()
        while "writer-started" not in order:
            time.sleep(0.01)
        time.sleep(0.5)  # the writer has had every chance to publish; the hold denies it
        assert "writer-done" not in order, "the writer published while the act held the lock"
        order.append("act-read")
        return view

    interposed = dataclasses.replace(production, inspect_registered=inspect_then_start_writer)
    verdict = admit_spec_successor(unreferenced, original, seam=interposed, root=root)
    order.append("act-done")
    writer.join(timeout=60)
    assert not writer.is_alive(), "the writer never got the lock after the act released it"
    assert isinstance(verdict, SuccessorAdmitted)
    assert order.index("act-read") < order.index("act-done") < order.index("writer-done")
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_u14_a_kill_between_append_and_execution_blocks_the_successor(certified_work) -> None:
    # The port seam is the kill point: the intent is durable, no member act ran.
    root, port = corpus(certified_work, "kill")
    original, unreferenced, referencing = specs()
    intent = append_assessment_intent(port, original.identity)
    view = seam().inspect_registered(root)
    assert type(view) is WellFormedView
    assert view.tip == intent
    assert not (root / "run").exists()
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def _leaf(root, digest: str):
    return root / CHAIN_LEAF / digest


def test_r12u1_an_excised_intent_entry_reads_malformed_and_the_act_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "excised")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity)
    _, _, plan = publication_plan(make_closure(spec=original.identity))
    port.execute_fulfilling(plan, intent)  # a registration now follows the intent
    intact = seam().inspect_registered(root)
    assert type(intact) is WellFormedView
    successor = next(
        entry.digest
        for entry in intact.entries
        if type(entry) is RegisteredEntryView and entry.fulfills == intent
    )
    _leaf(root, intent).unlink()
    view = seam().inspect_registered(root)
    assert type(view) is MalformedView, view
    # Cut 12 §5 item 5: the defect names the excised entry's successor — the
    # registration whose predecessor is now missing — and its class.
    assert (view.defect.kind, view.defect.subject) == ("missing-predecessor", successor)
    with pytest.raises(AdmissionEvidenceRefused) as refused:
        admit(root, unreferenced, original)
    assert refused.value.reason == "chain not well-formed"


def test_r12u2_a_truncated_chain_reads_refuted_under_an_anchor_and_the_act_admits(certified_work) -> None:
    root, port = corpus(certified_work, "truncated")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity)
    before = seam().inspect_registered(root)
    assert type(before) is WellFormedView and before.tip == intent
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)
    anchor = corpus_anchor(before, CORPUS_ID)
    _leaf(root, intent).unlink()  # the intent was the tip: a valid prefix remains
    after = seam().inspect_registered(root)
    assert type(after) is WellFormedView and after.tip == before.genesis.digest
    config = registry.WorldConfig(certified_work / "world", "0" * 32, (root,))
    report = real_audit(config, anchors.CorpusSubject(CORPUS_ID), root, observers=(anchor,))
    assert report.outcome == "refuted"
    assert "anchor-unreachable" in [finding.code for finding in report.findings]
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)
```

`LogSeam` is a frozen dataclass, so `dataclasses.replace` yields a seam identical in every member but one. `WellFormedView.tip` and `.genesis` are real attributes (`logmodel.py:152-170`). `real_audit(config, subject, root, observers=...)` is `test_world_log_audit.py:1434`; a corpus subject needs only its root in `WorldConfig.corpus_roots` and a `CorpusSubject(corpus_id)` — the manifest may be absent (the audit reads "no claim supplied", never a mismatch), and the anchor-unreachable step precedes the surface replay, so the verdict is `refuted` on the anchor alone.

- [ ] **Step 3: Run the durable tests**

```bash
cd python && set -o pipefail && uv run pytest tests/acceptance/test_successor_admission_acceptance.py | tail -1
```

Expected: `4 passed`.

- [ ] **Step 4: Declare the arms**

`python/tests/acceptance/n2_arms_cut12.py`:

```python
"""Cut 12's declared arms: 19 selected + 5 labeled = 24 units, 50 lettered arms."""

from n2_arms import Arm, Sabotage

_SUCC = "succession.py"
_SPEC = "spec.py"
_RECORDS = "world/records.py"
_REDUCE = "intents/reduce.py"
_EVIDENCE = "intents/evidence.py"
_ERRORS = "errors.py"
_SHAPES = "intents/shapes.py"

_ACCEPT = "acceptance/test_successor_admission_acceptance.py"

CUT12_ARMS = (
    Arm("G4u1", "a live failing verification blocks an unreferenced successor",
        Sabotage(_SUCC,
            before='failing = {path: value for path, value in verifications.items() if value.verdict == "failed"}',
            after='failing = {path: value for path, value in verifications.items() if value.verdict == "never"}'),
        ("test_succession.py::test_a_live_failing_verification_blocks_an_unreferenced_successor",)),
    Arm("G4u2", "an unfinished attempt blocks an unreferenced successor",
        Sabotage(_SUCC,
            before='elif row.status == "attempt-without-recorded-outcome":\n            unfinished.add(spec_identity)',
            after='elif row.status == "attempt-without-recorded-outcome":\n            pass'),
        ("test_succession.py::test_an_unfinished_attempt_blocks_an_unreferenced_successor",
         f"{_ACCEPT}::test_u14_a_kill_between_append_and_execution_blocks_the_successor")),
    Arm("G4u3", "a qualifying run-attempt report is a recorded failure",
        Sabotage(_SUCC,
            before='if type(evidence) is shapes.ReportEvidence and evidence.operation == "run-attempt":',
            after='if False:'),
        ("test_succession.py::test_a_run_attempt_report_is_a_recorded_failure",)),
    Arm("G4u4", "a referencing successor lifts every class",
        Sabotage(_SPEC,
            before='    if superseded.identity in unfinished_attempts and candidate.supersedes != superseded.identity:',
            after='    if superseded.identity in unfinished_attempts:'),
        ("test_spec.py::test_g4_a_referencing_successor_lifts_both_classes",
         "test_succession.py::test_an_unfinished_attempt_blocks_an_unreferenced_successor")),
    Arm("G4u5", "a spec in both classes refuses with the recorded-failure reason",
        Sabotage(_SPEC,
            before='return SuccessorRefused(candidate.identity, "an unreferenced successor to a recorded failed replay")\n    if superseded.identity in unfinished_attempts',
            after='pass\n    if superseded.identity in unfinished_attempts'),
        ("test_spec.py::test_g4_a_spec_in_both_classes_refuses_with_the_recorded_failure_reason",
         "test_succession.py::test_overlap_refuses_with_the_recorded_failure_reason")),
    Arm("G4u6a", "a coherent passing superseder lifts the block",
        Sabotage(_SUCC,
            before='active = {value.ref for value in verification_module.active(tuple(verifications.values()))}',
            after='active = {value.ref for value in verifications.values()}'),
        ("test_succession.py::test_a_coherent_passing_superseder_lifts_the_block",)),
    Arm("G4u6b", "a failing superseder keeps the block through the active member",
        Sabotage(_SUCC,
            before='return frozenset(targets[path].spec for path, value in failing.items() if value.ref in active)',
            after='return frozenset(targets[path].spec for path, value in failing.items() if value.ref in active and value.supersedes is None)'),
        ("test_succession.py::test_a_failing_superseder_keeps_the_block_through_the_active_member",)),
    Arm("G4u6c", "an incoherent passing superseder refuses naming itself",
        Sabotage(_SUCC,
            before='if path in failing or value.supersedes in blockers',
            after='if path in failing'),
        ("test_succession.py::test_an_incoherent_passing_superseder_refuses_naming_itself",
         "test_succession.py::test_a_withheld_verification_with_an_incoherent_superseder_refuses_the_superseder")),
    Arm("G4u7a", "a stale or missing stamp refuses naming the path",
        Sabotage(_EVIDENCE,
            before='if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):',
            after='if False:'),
        ("test_succession.py::test_a_stale_stamp_refuses_naming_the_path",
         "test_succession.py::test_a_missing_stamp_refuses_naming_the_path",
         "test_intent_evidence.py::test_decode_node_refuses_a_stale_stamp",
         "test_intent_evidence.py::test_decode_node_refuses_a_missing_stamp")),
    Arm("G4u7b", "an id naming another path refuses",
        Sabotage(_EVIDENCE,
            before='if not slug or path != f"{kind}/{slug}.md":',
            after='if not slug:'),
        ("test_succession.py::test_an_id_naming_another_path_refuses",
         "test_intent_evidence.py::test_decode_node_refuses_an_id_that_names_another_path")),
    Arm("G4u7c", "an undecodable evidence record refuses, targeted or not",
        Sabotage(_SUCC,
            before='except RecordUndecodable as caught:\n            raise AdmissionEvidenceRefused(f"{kind} unreadable", path) from caught',
            after='except RecordUndecodable:\n            continue'),
        ("test_succession.py::test_an_undecodable_verification_refuses",
         "test_succession.py::test_an_undecodable_untargeted_assessment_refuses")),
    Arm("G4u7d", "an unreadable regular file refuses in either namespace",
        Sabotage(_SUCC,
            before='for path in surface.unreadable:',
            after='for path in ():'),
        ("test_succession.py::test_an_unreadable_regular_file_refuses_in_either_namespace",)),
    Arm("G4u8a", "edge cardinality other than one refuses",
        Sabotage(_SUCC,
            before='if len(edges) != 1:',
            after='if len(edges) == 0:'),
        ("test_succession.py::test_two_verifies_edges_refuse",)),
    Arm("G4u8b", "a target that is not a decoded assessment refuses",
        Sabotage(_SUCC,
            before='if target_path is None or target_path not in assessments:',
            after='if target_path is None:'),
        ("test_succession.py::test_a_target_that_is_not_an_assessment_refuses",)),
    Arm("G4u8c", "a missing target refuses",
        Sabotage(_SUCC,
            before='target_path = by_uid.get(edge.target_uid) if edge.target_uid is not None else None',
            after='target_path = by_uid.get(edge.target_uid) if edge.target_uid is not None else next(iter(assessments), None)'),
        ("test_succession.py::test_a_missing_target_refuses",)),
    Arm("G4u8d", "a deprecated-id target resolves",
        Sabotage(_SUCC,
            before='if edge.relation.target in withheld:',
            after='if edge.relation.target in withheld or edge.relation.target not in index.id_to_uid:'),
        ("test_succession.py::test_a_deprecated_id_target_resolves_and_blocks",)),
    Arm("G4u8e", "a uid collision refuses naming the colliding id",
        Sabotage(_SUCC,
            before='except CollisionError as caught:\n            raise AdmissionEvidenceRefused("record collision", node.id) from caught',
            after='except CollisionError:\n            continue'),
        ("test_succession.py::test_a_uid_collision_refuses_naming_the_colliding_id",)),
    Arm("G4u8f", "an identity mismatch refuses",
        Sabotage(_SUCC,
            before='if target.identity() != value.assessment:',
            after='if False:'),
        ("test_succession.py::test_an_identity_mismatch_refuses",)),
    Arm("G4u8g", "the gate counts outbound edges, not stored relations",
        Sabotage(_SUCC,
            before='for edge in index.outbound_edges(nodes[path].uid)',
            after='for edge in index.outbound_edges(nodes[path].uid) + index.inbound_edges(nodes[path].uid)'),
        ("test_succession.py::test_a_relation_sourced_elsewhere_is_not_this_verifications_edge",)),
    Arm("G4u9a", "a withheld verification without a coherent superseder refuses",
        Sabotage(_SUCC,
            before='raise AdmissionEvidenceRefused("verification oversized", path)',
            after='continue'),
        ("test_succession.py::test_a_withheld_verification_without_a_superseder_refuses",)),
    Arm("G4u9b", "a withheld verification with a coherent superseder is skipped",
        Sabotage(_SUCC,
            before='if ref.startswith("verification:") and not any(',
            after='if ref.startswith("verification:") and any('),
        ("test_succession.py::test_a_withheld_verification_with_a_coherent_superseder_is_skipped",
         "test_succession.py::test_a_withheld_verification_without_a_superseder_refuses")),
    Arm("G4u9c", "a withheld assessment targeted by a failing verification refuses",
        Sabotage(_SUCC,
            before='if edge.relation.target in withheld:\n            raise AdmissionEvidenceRefused("verification target unreadable", path)',
            after='if edge.relation.target in withheld:\n            continue'),
        ("test_succession.py::test_a_withheld_assessment_targeted_by_a_failing_verification_refuses",)),
    Arm("G4u9d", "a decoded node claiming a withheld path's id is a collision",
        Sabotage(_SUCC,
            before='if index.resolve_uid(ref) is not None:\n            raise AdmissionEvidenceRefused("record collision", ref)',
            after='if False:\n            raise AdmissionEvidenceRefused("record collision", ref)'),
        ("test_succession.py::test_a_decoded_node_claiming_a_withheld_paths_id_is_a_collision",)),
    Arm("G4u9e", "the ceiling is exact: RECORD_CEILING bytes capture, one more is withheld",
        Sabotage(_RECORDS,
            before='return "withheld" if len(data) > RECORD_CEILING else data',
            after='return "withheld" if len(data) >= RECORD_CEILING else data'),
        ("test_record_capture.py::test_an_oversized_regular_file_is_withheld_and_named",)),
    Arm("G4u10", "an unresolvable intent for the superseded spec refuses; another spec's does not block",
        Sabotage(_SUCC,
            before='if spec_identity == superseded_identity:\n                raise AdmissionEvidenceRefused(',
            after='if False:\n                raise AdmissionEvidenceRefused('),
        ("test_succession.py::test_a_decayed_run_under_the_superseded_spec_refuses",)),
    Arm("G4u11", "a writer arriving during the act waits and is not consulted",
        Sabotage(_SUCC,
            before='with seam.corpus_lock(root):\n        view = seam.inspect_registered(root)',
            after='if True:\n        view = seam.inspect_registered(root)'),
        (f"{_ACCEPT}::test_u11_a_writer_arriving_during_the_act_waits_and_is_not_consulted",)),
    Arm("G4u12", "nothing durable leaves no trace: the successor is admitted",
        Sabotage(_SPEC,
            before='    return SuccessorAdmitted(candidate.identity)\n\n\ndef _facet_projection',
            after='    return SuccessorRefused(candidate.identity, "phantom")\n\n\ndef _facet_projection'),
        ("test_succession.py::test_the_negative_nothing_durable_admits",
         "test_spec.py::test_g4_a_discarded_failed_attempt_is_undetectable")),
    Arm("G4u13a", "an unopenable root refuses before any lock",
        Sabotage(_SUCC,
            before='raise AdmissionEvidenceRefused("root unreadable", str(root)) from failure',
            after='return'),
        ("test_succession.py::test_an_absent_root_refuses_before_any_lock",
         "test_succession.py::test_a_file_where_the_root_should_be_refuses_as_unreadable")),
    Arm("G4u13b", "a non-well-formed chain refuses",
        Sabotage(_SUCC,
            before='if type(view) is not WellFormedView:',
            after='if False:'),
        ("test_succession.py::test_an_unregistered_directory_is_an_absent_chain_and_refuses",
         f"{_ACCEPT}::test_r12u1_an_excised_intent_entry_reads_malformed_and_the_act_refuses")),
    Arm("G4u13c", "an unenumerable namespace refuses; an absent one admits",
        Sabotage(_SUCC,
            before='if surface.uninspectable:',
            after='if False:'),
        ("test_succession.py::test_an_unenumerable_namespace_refuses_for_verification_and_for_run",)),
    Arm("G4u14a", "class 1b reads the record that matched",
        Sabotage(_REDUCE,
            before='return RegistrationReduction((path, record_evidence), pointer_unresolved, tuple(reasons))',
            after='return RegistrationReduction((path, shapes.InertRecord()), pointer_unresolved, tuple(reasons))'),
        ("test_succession.py::test_an_undecodable_sibling_before_the_qualifying_report_still_joins",
         "test_succession.py::test_a_qualifying_report_before_a_qualifying_run_is_the_match",
         "test_intent_reduce.py::test_reduce_registration_first_match_in_order_wins")),
    Arm("G4u14b", "a matched run is a minted run, never a failure",
        Sabotage(_SUCC,
            before='if type(evidence) is shapes.ReportEvidence and evidence.operation == "run-attempt":\n                failures.add(spec_identity)',
            after='if True:\n                failures.add(spec_identity)'),
        ("test_succession.py::test_a_qualifying_run_beside_a_report_joins_nothing",
         "test_succession.py::test_a_qualifying_run_lifts_the_block")),
    Arm("R12u1", "an excised intent entry reads malformed and the act refuses",
        Sabotage(_SUCC,
            before='raise AdmissionEvidenceRefused("chain not well-formed", str(root))',
            after='raise AdmissionEvidenceRefused("root unreadable", str(root))'),
        (f"{_ACCEPT}::test_r12u1_an_excised_intent_entry_reads_malformed_and_the_act_refuses",)),
    Arm("R12u2", "a truncated chain reads refuted under an anchor and the act admits",
        Sabotage(_SUCC,
            before='return admit_successor(candidate, superseded, recorded_failures, unfinished)',
            after='return admit_successor(candidate, superseded, recorded_failures | {superseded.identity}, unfinished)'),
        (f"{_ACCEPT}::test_r12u2_a_truncated_chain_reads_refuted_under_an_anchor_and_the_act_admits",
         "test_succession.py::test_the_negative_nothing_durable_admits")),
    Arm("L7u14", "a kill between append and execution blocks the successor",
        Sabotage(_SUCC,
            before='if row.shape != "assessment-run":\n            continue',
            after='if row.shape != "assessment-run" or row.status == "attempt-without-recorded-outcome":\n            continue'),
        (f"{_ACCEPT}::test_u14_a_kill_between_append_and_execution_blocks_the_successor",)),
    Arm("L7u15", "a wrong-spec publication fails qualification and the intent still blocks",
        Sabotage(_SHAPES,
            before='if evidence.spec_identity != value.spec_identity:\n                return "wrong-spec"',
            after='if evidence.spec_identity != value.spec_identity:\n                return None'),
        ("test_succession.py::test_a_wrong_spec_publication_fails_qualification_and_the_intent_still_blocks",)),
    Arm("L7u16", "a qualifying publication lifts the block",
        Sabotage(_SUCC,
            before='elif row.status == "matched":',
            after='elif row.status == "matched" and not unfinished.add(spec_identity):'),
        ("test_succession.py::test_a_qualifying_run_lifts_the_block",)),
    Arm("K1a", "capture_surface's records equal capture_records' over the default namespaces",
        Sabotage(_RECORDS,
            before='return capture_surface(root, RECORD_NAMESPACES).records',
            after='return capture_surface(root, RECORD_NAMESPACES[:1]).records'),
        ("test_record_capture.py::test_capture_surface_records_equal_capture_records_over_the_default_namespaces",
         "test_record_capture.py::test_captures_each_record_file_sorted")),
    Arm("K1b", "a non-corpus root holding run records still captures nothing",
        Sabotage(_RECORDS,
            before='if kind != "corpus":\n        return ()',
            after='if kind == "corpus" and False:\n        return ()'),
        ("test_record_capture.py::test_a_non_corpus_root_holding_run_records_still_captures_nothing",)),
    Arm("K2a", "an oversized regular file is withheld and named",
        Sabotage(_RECORDS,
            before='elif payload == "withheld":\n                into.withheld.append(path)',
            after='elif payload == "withheld":\n                pass'),
        ("test_record_capture.py::test_an_oversized_regular_file_is_withheld_and_named",)),
    Arm("K2b", "an unreadable regular file is named, not dropped",
        Sabotage(_RECORDS,
            before='elif payload == "unreadable":\n                into.unreadable.append(path)',
            after='elif payload == "unreadable":\n                pass'),
        ("test_record_capture.py::test_an_unreadable_regular_file_is_named_not_dropped",)),
    Arm("K2c", "an unenumerable namespace is uninspectable; ENOENT is silent",
        Sabotage(_RECORDS,
            before='except OSError as failure:\n        if failure.errno != errno.ENOENT:\n            into.uninspectable.append(prefix)\n        return\n    try:',
            after='except OSError:\n        return\n    try:'),
        ("test_record_capture.py::test_an_unenumerable_namespace_is_uninspectable_and_an_absent_one_is_silent",)),
    Arm("K2d", "a scandir failure is uninspectable unless it is ENOENT",
        Sabotage(_RECORDS,
            before='except OSError as failure:\n            if failure.errno != errno.ENOENT:\n                into.uninspectable.append(prefix)\n            return',
            after='except OSError:\n            return'),
        ("test_record_capture.py::test_a_scandir_failure_is_uninspectable_unless_it_is_enoent",)),
    Arm("K2e", "a directory entry whose classification fails is unreadable, never leaked",
        Sabotage(_RECORDS,
            before='except OSError:\n                into.unreadable.append(path)\n                continue',
            after='except OSError:\n                continue'),
        ("test_record_capture.py::test_a_directory_entry_whose_classification_fails_is_unreadable",)),
    Arm("K3a", "the first match in final order wins",
        Sabotage(_REDUCE,
            before='for path in record_paths:\n        payload = records.get(path)',
            after='for path in reversed(record_paths):\n        payload = records.get(path)'),
        ("test_intent_reduce.py::test_reduce_registration_first_match_in_order_wins",)),
    Arm("K3b", "an undecodable earlier sibling leaves unresolved set beside a later match",
        Sabotage(_REDUCE,
            before='return RegistrationReduction((path, record_evidence), pointer_unresolved, tuple(reasons))',
            after='return RegistrationReduction((path, record_evidence), False, tuple(reasons))'),
        ("test_intent_reduce.py::test_reduce_registration_names_an_undecodable_sibling_beside_a_later_match",)),
    Arm("K3c", "every decoded non-qualifying reason is returned in order",
        Sabotage(_REDUCE,
            before='reasons.append(reason)\n    return RegistrationReduction(None, pointer_unresolved, tuple(reasons))',
            after='reasons.insert(0, reason)\n    return RegistrationReduction(None, pointer_unresolved, tuple(reasons))'),
        ("test_intent_reduce.py::test_reduce_registration_with_no_match_returns_every_reason_in_order",)),
    Arm("K4a", "the refusal carries reason and ref as attributes",
        Sabotage(_ERRORS,
            before='        self.reason = reason\n        self.ref = ref',
            after='        self.reason = ref\n        self.ref = reason'),
        ("test_succession_errors.py::test_it_is_a_science_error_carrying_reason_and_ref",
         "test_succession.py::test_an_absent_root_refuses_before_any_lock")),
    Arm("K4b", "the reason set is closed at the spec's eleven",
        Sabotage(_SUCC,
            before='    "qualification unresolved for the superseded spec",\n)',
            after='    "qualification unresolved for the superseded spec",\n    "phantom",\n)'),
        ("test_succession.py::test_the_reason_set_is_exactly_the_specs_eleven",)),
    Arm("K5", "the core's first body line is cut 3's anchor line",
        Sabotage(_SPEC,
            before='    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:',
            after='    if superseded.identity in recorded_failures and (candidate.supersedes != superseded.identity):'),
        ("test_spec.py::test_g4_the_core_keeps_cut_3s_anchor_line",)),
)

_UNIT_OF_LETTERED = {
    "G4u6a": "G4u6", "G4u6b": "G4u6", "G4u6c": "G4u6",
    "G4u7a": "G4u7", "G4u7b": "G4u7", "G4u7c": "G4u7", "G4u7d": "G4u7",
    "G4u8a": "G4u8", "G4u8b": "G4u8", "G4u8c": "G4u8", "G4u8d": "G4u8",
    "G4u8e": "G4u8", "G4u8f": "G4u8", "G4u8g": "G4u8",
    "G4u9a": "G4u9", "G4u9b": "G4u9", "G4u9c": "G4u9", "G4u9d": "G4u9", "G4u9e": "G4u9",
    "G4u13a": "G4u13", "G4u13b": "G4u13", "G4u13c": "G4u13",
    "G4u14a": "G4u14", "G4u14b": "G4u14",
    "K1a": "K1", "K1b": "K1",
    "K2a": "K2", "K2b": "K2", "K2c": "K2", "K2d": "K2", "K2e": "K2",
    "K3a": "K3", "K3b": "K3", "K3c": "K3",
    "K4a": "K4", "K4b": "K4",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"G4": 14, "R12": 2, "L7": 3}
LABELED_UNITS: tuple[str, ...] = tuple(f"K{number}" for number in range(1, 6))

#: Cut-3 checks a cut-12 arm cites beside its own durable check — the one
#: permitted overlap with a prior cut's declared checks, and exactly which.
CO_CITED: dict[str, tuple[str, ...]] = {
    "G4u12": ("test_spec.py::test_g4_a_discarded_failed_attempt_is_undetectable",),
}
```

Every `before` string must match the implemented source exactly once. Verify:

```bash
cd python && uv run python - <<'EOF'
import sys
sys.path[:0] = ["tests", "tests/acceptance"]
from pathlib import Path
from n2_arms_cut12 import CUT12_ARMS
counts = [(a.row, Path("src/science", a.sabotage.module).read_text().count(a.sabotage.before)) for a in CUT12_ARMS]
bad = [c for c in counts if c[1] != 1]
assert not bad, f"anchors not matching exactly once: {bad}"
print(len(CUT12_ARMS), "arms; every anchor matches once")
EOF
```

Expected: `50 arms; every anchor matches once`. Every `before` string is a verbatim substring of the code Tasks 2–6 give, so any other count is a transcription error in this file; the source is not edited to fit an arm.

- [ ] **Step 5: The N2 harness**

`python/tests/acceptance/test_n2_cut12.py`:

```python
"""Cut 12's declaration accounting, N2 audit, and lettered-arm partition."""

from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from n2_arms import Arm
from n2_arms_cut3 import CUT3_ARMS
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import CUT10_ARMS
from n2_arms_cut11 import CUT11_ARMS
from n2_arms_cut12 import CO_CITED, CUT12_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import MalformedArm, audit, baseline

import science.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-29-conformance-cut-12.md"
CUT12_FREEZE_COMMIT = "<the ledger's freeze hash>"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut6.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut7.py": "117f37e",
    "python/tests/acceptance/n2_arms_cut8.py": "55b6de7",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": "22461e9",
    "python/tests/acceptance/n2_arms_cut11.py": "<ledger R4's anchor-move hash>",
}
# n2_arms_cut3.py stays unpinned, as cut 11 left it: tests/test_n2.py audits
# it live, and cut 12's K5 arm holds its G4 anchor line byte-identical.

PRIOR_ARMS = (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS, *CUT10_ARMS, *CUT11_ARMS)


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    root = tmp_path_factory.mktemp("n2-cut12")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], root / f"arm{pair[0]}"),
                enumerate(CUT12_ARMS),
            )
        )


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason
            + "\n"
            + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut12ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-12 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-12 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-12 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-12 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-12 check passes on the real package",
            sabotage=CUT12_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT12_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


def declared_rows() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT12_ARMS)


class TestTheDeclarationTable:
    def test_the_declared_arms_are_unique_and_number_fifty(self):
        rows = declared_rows()
        assert len(rows) == len(set(rows)) == len(CUT12_ARMS) == 50

    def test_the_labeled_units_appear_in_declaration_order(self):
        labeled = [unit_of(row) for row in declared_rows() if row.startswith("K")]
        assert tuple(dict.fromkeys(labeled)) == LABELED_UNITS

    def test_the_frozen_cut_states_the_same_accounting(self):
        flattened = re.sub(r"\s+", " ", FROZEN_CUT.read_text(encoding="utf-8"))
        total = re.search(
            r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*",
            flattened,
        )
        assert total is not None
        assert tuple(map(int, total.groups())) == (19, 5, 24)
        pairs = re.search(r"Selected units: ((?:[A-Z]+\d+ \d+(?:, )?)+)", flattened)
        assert pairs is not None
        assert {
            row: int(count) for row, count in re.findall(r"([A-Z]+\d+) (\d+)", pairs.group(1))
        } == ROW_UNITS

    def test_the_frozen_cut_names_the_commit_this_audit_reads(self):
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT12_FREEZE_COMMIT, "HEAD"],
            check=False,
        )
        assert completed.returncode == 0

    def test_every_arm_has_one_source_mutation_and_exact_check_nodes(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT12_ARMS:
            assert arm.checks, arm.row
            assert len(arm.checks) == len(set(arm.checks)), arm.row
            assert arm.sabotage.before != arm.sabotage.after, arm.row
            assert arm.asserts.strip(), arm.row
            target = package / arm.sabotage.module
            assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
            assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
            for check in arm.checks:
                parts = check.split("::")
                assert len(parts) >= 2 and parts[-1].startswith("test_"), check

    def test_every_check_lives_in_a_cut12_file(self):
        assert {check.split("::")[0] for arm in CUT12_ARMS for check in arm.checks} == {
            "acceptance/test_successor_admission_acceptance.py",
            "test_intent_evidence.py",
            "test_intent_reduce.py",
            "test_record_capture.py",
            "test_spec.py",
            "test_succession.py",
            "test_succession_errors.py",
        }


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_declaration_files_are_byte_identical(self):
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, f"{path} moved since {pin}"

    def test_no_cut12_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {check for arm in (*PRIOR_ARMS, *CUT3_ARMS) for check in arm.checks}
        for arm in CUT12_ARMS:
            allowed = set(CO_CITED.get(arm.row, ()))
            claimed = set(arm.checks) & prior
            assert claimed <= allowed, f"{arm.row} claims a prior cut's check: {sorted(claimed - allowed)}"

    def test_the_co_cited_checks_are_cut_3s_and_stand_beside_a_cut12_check(self):
        cut3_checks = {check for arm in CUT3_ARMS for check in arm.checks}
        for row, cited in CO_CITED.items():
            arm = next(arm for arm in CUT12_ARMS if arm.row == row)
            assert set(cited) <= cut3_checks
            assert set(arm.checks) - set(cited), f"{row} cites only prior checks"

    def test_the_k_prefix_names_no_frozen_prior_guarantee_unit(self):
        prior = {arm.row for arm in PRIOR_ARMS if not arm.row.startswith(("J", "K"))}
        assert not prior.intersection(LABELED_UNITS)


def test_the_partition_accounts_exactly_the_24_frozen_units() -> None:
    assert ROW_UNITS == {"G4": 14, "R12": 2, "L7": 3}
    assert LABELED_UNITS == tuple(f"K{number}" for number in range(1, 6))
    expected = (
        {f"G4u{number}" for number in range(1, 15)}
        | {"R12u1", "R12u2", "L7u14", "L7u15", "L7u16"}
        | set(LABELED_UNITS)
    )
    assert {unit_of(arm.row) for arm in CUT12_ARMS} == expected
```

`n2_arms_cut3.py` exports `CUT3_ARMS` (`n2_arms_cut3.py:1763`). Replace the two `<…>` hashes with the ledger's values. Run it standalone with **both** root variables set — `test_n2.py`'s `_run_check` forwards `SCIENCE_CUT10_ROOT` (and cuts 4–7) to its subprocess pytests but not `SCIENCE_CUT12_ROOT`, and the durable fixture reads cut 10's first:

```bash
cd python && set -o pipefail && SCIENCE_CUT10_ROOT="$(pwd)/../.cut12-acceptance" SCIENCE_CUT12_ROOT="$(pwd)/../.cut12-acceptance" uv run pytest tests/acceptance/test_n2_cut12.py | tail -1
```

Expected: all passed (the session fixture audits every arm in a subprocess pytest — allow several minutes).

- [ ] **Step 6: The runner**

`python/tools/cut12_acceptance.py`:

```python
"""The cut-12 acceptance command — successor admission, on the certified tuple.

It errors off the certified tuple. It never skips. Three phases run in order:
the unedited cut-11 prefix, durable cut-12 arms, then cut-12's N2 audit.

Never run beside another acceptance command or the ordinary suite. All cut
roots are environment-scoped and concurrent runs would delete shared roots.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut12-acceptance"

PREFIX_RUNNERS = ("cut11_acceptance.py",)
PHASE_MODULES = ("test_successor_admission_acceptance.py", "test_n2_cut12.py")
PROBE_REFUSED = 2


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT12_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    """Register and drop one throwaway world root, corpus root, and store root."""
    from science.root import (
        init_corpus_root,
        init_store_root,
        init_world_root,
        metadata_root_for,
    )
    from science.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        init_store_root(store_root)
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's own refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def declared_arm_count() -> int:
    """Return cut 12's declared arm count, ``len(CUT12_ARMS)``."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut12 import CUT12_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT12_ARMS)


def cut_environment(run: Path) -> dict[str, str]:
    return {
        **os.environ,
        **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 13)},
    }


def run_prefix(runner: str, run: Path) -> int:
    """Run the prior cut's command unchanged beneath ``run``."""
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT11_ROOT": str(run)},
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    phases = len(PREFIX_RUNNERS) + len(PHASE_MODULES)
    for module in PHASE_MODULES:
        path = ACCEPTANCE / module
        if not path.is_file():
            print(f"cut-12 required acceptance module is missing: {path}", file=sys.stderr)
            return 1
    for runner in PREFIX_RUNNERS:
        path = TOOLS / runner
        if not path.is_file():
            print(f"cut-12 required prefix runner is missing: {path}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-12 acceptance cannot run here: the volume beneath "
                f"{work} is not on the engine's certified allowlist.\n"
                f"  the engine refused with {refusal}\n"
                "  set SCIENCE_CUT12_ROOT to a directory on a certified volume, or recertify with\n"
                "  the engine's own tooling. This is an error, not a skip: an environment that\n"
                "  cannot exercise durability must not be able to report cut-12 discharge.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        phase = 0
        for runner in PREFIX_RUNNERS:
            phase += 1
            print(f"[cut12 phase {phase}/{phases}] {runner}", flush=True)
            returncode = run_prefix(runner, run)
            if returncode != 0:
                print(
                    f"cut-12 acceptance stopped: the {runner} prefix exited {returncode}.\n"
                    "  A prior cut's arms are its own claim and cut 12 runs them unchanged, so this\n"
                    "  is that cut's failure and not a cut-12 one. Cut 12's arms did not run and cut\n"
                    "  12 is not discharged.",
                    file=sys.stderr,
                )
                return returncode

        for index, module in enumerate(PHASE_MODULES):
            phase += 1
            last = index == len(PHASE_MODULES) - 1
            print(f"[cut12 phase {phase}/{phases}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ACCEPTANCE / module),
                    *(argv if last else []),
                ],
                cwd=PYTHON_ROOT,
                check=False,
                env=cut_environment(run),
            )
            if completed.returncode != 0:
                return completed.returncode

        try:
            arms = declared_arm_count()
        except Exception as failure:  # noqa: BLE001 - report, do not mask run result
            print(
                f"cut-12 acceptance: could not compute declared-arm count: {failure}",
                file=sys.stderr,
            )
        else:
            print(
                f"declared arms: {arms} (= len(CUT12_ARMS), normalizing to the 24 frozen "
                "units pinned by test_the_partition_accounts_exactly_the_24_frozen_units, "
                "among the tests above; not itself a pytest total)",
                flush=True,
            )
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

```bash
cd python && uv run ruff check tools/cut12_acceptance.py tests/acceptance/n2_arms_cut12.py tests/acceptance/test_n2_cut12.py tests/acceptance/test_successor_admission_acceptance.py tests/conftest.py && uv run pyright tools/cut12_acceptance.py | tail -1
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add python/tests/conftest.py python/tests/acceptance/n2_arms_cut12.py python/tests/acceptance/test_successor_admission_acceptance.py python/tests/acceptance/test_n2_cut12.py python/tools/cut12_acceptance.py
git commit -m "test(cut12): declare successor-admission arms, durable checks, and the acceptance runner"
```

---

### Task 8: Discharge

**Files:**
- Create: `docs/plans/<today>-conformance-cut-12-results.md`
- Modify: `docs/plans/2026-08-29-successor-admission-ledger.md`

- [ ] **Step 1: The portable gates on the whole tree**

```bash
cd python && set -o pipefail && uv run ruff check . && uv run pyright | tail -1 && uv run pytest | tail -1
```

Expected: clean; `0 errors`; every test passed. Record the pytest summary line.

- [ ] **Step 2: The certified run**

```bash
cd python && set -o pipefail && uv run python tools/cut12_acceptance.py 2>&1 | tee ../.cut12-run.log | tail -20
```

Expected: `[cut12 phase 1/3] cut11_acceptance.py` … exit 0; `[cut12 phase 2/3] test_successor_admission_acceptance.py` `4 passed`; `[cut12 phase 3/3] test_n2_cut12.py` all passed; `declared arms: 50 …`; exit 0. A non-zero exit at phase 1 is cut 11's failure, not cut 12's — stop and investigate; the results record cannot be written on a red prefix.

- [ ] **Step 3: Write the results record**

`docs/plans/<today>-conformance-cut-12-results.md`, with every `<…>` filled from the run just made (they are measured values, not decisions):

```markdown
# Conformance cut 12 — discharge results

**Date:** <today>
**Subject:** successor admission, G4's closure
(`../superpowers/specs/2026-08-29-successor-admission-design.md`, promoted to
`../designs/2026-08-29-successor-admission-design.md` at banking), measured
against conformance cut 12's frozen selection
(`../designs/2026-08-29-conformance-cut-12.md`).

The frozen cut remains byte-exact at `<freeze hash>`. Only its status header
changes at banking.

**Integration state.** Every implementation commit was made on
`design/successor-admission`. The reviewed pre-banking head is `<impl head>`.
The branch is not merged or pushed by this discharge; the human partner owns
the history-preserving `--no-ff` merge.

## 1. Accounting

Cut 12 reads three rows: G4 and R12 in full, L7 in part. Its 19 selected units
and labels K1–K5 give **19 selected + 5 labeled = 24 declaration units**. L7
stays partial on exactly its banked limitation, L7u1.

The executable declaration table expands compound requirements into **50
lettered sabotage arms** normalized back to those 24 frozen units. Every armed
claim has one exact once-matching source mutation and at least one check that
fails under it. G4u12 cites cut 3's discarded-attempt check beside its own
durable one (`CO_CITED`); no other prior check is claimed.

### 1.1 What the discharge establishes

- `admit_spec_successor` derives both blocker classes from durable state under
  the root's operation lock and never from a caller-supplied set; a writer
  arriving during the act waits and is not consulted.
- Class 1a reads only active, coherent, failing verifications; an incoherent
  failing verification or an incoherent superseder of one refuses the act
  globally, naming the record.
- Class 2 and class 1b come from cut 11's reducer unchanged; an unresolvable
  intent for the superseded spec refuses; another spec's does not block.
- Oversized records lift only through a coherent superseder; unreadable and
  uninspectable surfaces refuse; nothing durable leaves no trace.
- `capture_records`' certified surface, cut 11's reducer verdicts, and the
  core's cut-3 anchor line are byte-for-byte unchanged.

## 2. What ran

All commands ran sequentially from `python/`. Durable work ran on the
certified volume at `<SCIENCE_CUT12_ROOT or the default beside the checkout>`.

### 2.1 Host and certified tuple

<kernel, filesystem and mount tuple, as `cut11_acceptance.py`'s probe reports it>

### 2.2 Certified cut-12 runner

`uv run python tools/cut12_acceptance.py`

<the three phase lines with their pytest summary lines, verbatim>

### exit: 0

### 2.3 Portable and static gates

`uv run pytest` — <summary line>

### exit: 0

`uv run ruff check .` — All checks passed!

### exit: 0

`uv run pyright` — 0 errors, 0 warnings, 0 informations

### exit: 0

## 3. Review and implementation rulings

The post-implementation review reported <N> findings, each closed before this
record (ledger rulings R<a>–R<b>). The declaration review expanded the 24
frozen units into 50 lettered arms; the frozen partition never changed. The
two cut-11 anchors that moved with `reduce_registration` moved in whitespace
only (ledger R4); cut 3's three G4 sabotages match the unchanged anchor line
(ledger R2). The exact rationale, task heads, and definitive runner summaries
live in `2026-08-29-successor-admission-ledger.md`.

There is no frozen-cut deviation.

## 4. Commit identities

| commit | subject |
|---|---|
<one row per commit from `git log --oneline main..HEAD`, oldest first>

The banking commit following this record changes no runtime behavior.

## 5. Remaining boundary

Cut 12 closes G4 at persistence width and reads R12 in full. L7 stays partial
on exactly its banked limitation, L7u1. Event-level L8 and the L13 preimage
resolver remain with their named owners. `admit_spec_successor` has no
production caller; the run boundary's nomination of a superseded spec is a
later design's.
```

Then delete `.cut12-run.log`.

- [ ] **Step 4: Close the ledger and commit**

Append the discharge ruling to the ledger (`R5 — discharged at <HEAD short hash> on <host tuple>; the three phase summaries are in the results record`), then:

```bash
git add docs/plans/<today>-conformance-cut-12-results.md docs/plans/2026-08-29-successor-admission-ledger.md
git commit -m "docs(plans): record conformance cut 12's discharge"
```

---

### Task 9: Banking

**Files:**
- Move: `docs/superpowers/specs/2026-08-29-successor-admission-design.md` → `docs/designs/2026-08-29-successor-admission-design.md`
- Modify: `docs/designs/2026-08-29-conformance-cut-12.md:3-5` (the `**Status:**` line only)
- Modify: `docs/designs/2026-08-26-world-index-intent-boundary-design.md` (one dated correction at the head of §5)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`; rows 5 and 7)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md`, `python/tools/roadmap_status.py`
- Modify: `README.md`, `docs/guide/README.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/computation-and-reproducibility.md`

- [ ] **Step 1: Promote the spec and close both status lines**

```bash
git mv docs/superpowers/specs/2026-08-29-successor-admission-design.md docs/designs/2026-08-29-successor-admission-design.md
```

Set the promoted design's `**Status:**` to: `implemented and discharged <today> at `<impl head>`; conformance cut 12 froze before implementation at `<freeze hash>` and its 24 units passed through 50 lettered sabotage arms on the certified tuple. Results: `../plans/<today>-conformance-cut-12-results.md`; execution rulings: `../plans/2026-08-29-successor-admission-ledger.md`. Promoted from `docs/superpowers/specs/` in this banking change.` Update its relative links (`../../plans/…` → `../plans/…`).

Set the cut's `**Status:**` to: `**Discharged <today> at `<impl head>`** — all 24 frozen units passed through 50 lettered sabotage arms on the certified tuple; the portable suite reported <N> passing tests, Ruff and Pyright were clean. Results: `../plans/<today>-conformance-cut-12-results.md`. The cut remains frozen byte-exact at `<freeze hash>`; the specification was promoted to `2026-08-29-successor-admission-design.md` at banking.` Nothing below the status line changes.

Add the README design-table row for the promoted design (after the cut-12 row):

```markdown
| `2026-08-29-successor-admission-design.md` | the successor-admission slice: the two-set core, the deriving boundary `admit_spec_successor` over the chain's qualification and the corpus's verification evidence under one hold, the superseder-side oversized rule, and the named evidence refusal |
```

and change `Thirty-nine documents` to `Forty documents`.

- [ ] **Step 2: The dated correction in intent-boundary §5**

Directly under the `## 5. G4's closure — transferred to the successor-admission slice` heading, before the existing blockquote, add:

```markdown
> **Closed <today>, conformance cut 12** (`2026-08-29-successor-admission-design.md`;
> results `../plans/<today>-conformance-cut-12-results.md`). Two corrections to
> the text below, recorded rather than rewritten: the deriving entrypoint lives
> in `science.succession`, not `science.spec` — `corpus` imports `spec` and the
> log seam imports `corpus`, so a top-level definition in `spec.py` is an import
> cycle (design §2 item 4); and the coherence gate also covers a verification
> whose `supersedes` names a failing or withheld one, since an incoherent
> superseder would otherwise lift a block by bare existence (design §4.4 step
> 3). Everything else below was implemented as written.
```

- [ ] **Step 3: The adoption ledger**

Rename `## Current state (2026-08-28)` to `## Current state (<today>)` and update every anchor that names it (`grep -rn 'current-state-2026-08-28' docs README.md`); change `**Implemented through conformance cut 11.**` to `**Implemented through conformance cut 12.**` and add to the bullet list:

```markdown
- **Successor admission** — G4 closed at persistence width: `admit_spec_successor`
  derives recorded failures and unfinished attempts from the chain and the
  corpus's verification evidence under one hold and refuses an unreferenced
  successor by class (cut 12).
```

Remove the `successor-admission` row from the boundaries table. Change the closing paragraph's `names G4, L8 and L13` to `names L8 and L13`. In row 5, replace `**and G4's closure** *(corrected 2026-08-27: …)*` — the whole parenthetical — with `*(G4 closed at cut 12, <today>: `2026-08-29-successor-admission-design.md`)*`. In row 7, after `landed 2026-08-12, conformance cut 3's slice (…)`, add `; G4 read in full at persistence width by cut 12 (<today>)`.

- [ ] **Step 4: Re-rank the roadmap**

In `python/tools/roadmap_status.py`: add `12: ("conformance-cut-12-results §1", "G4, R12", "L7"),` to `ACCOUNTING` and delete the `"G4"` entry from `REOPENED` (leave the dict, now empty, with its comment). Run `cd python && uv run python tools/roadmap_status.py` — expected last line `Closed 64 of 151; open 87.`

Rewrite `docs/plans/2026-08-29-implementation-roadmap.md` whole (it is a current claim): `**Ranked at:** cut 12, against the ledger's Current state (<today>)`; remove `successor-admission` from the Boundary index and from tier 1, renumbering tier 1 so `run-confinement` is row 1 and `contract-cut` row 8; replace Appendix A with the script's new output; in Appendix B drop the G4 and R12 rows and change L7's row to `| L7 | u1's non-ancestor spelling (cut 8 results §1.1) → limitation; every other arm read by cuts 10–12 | limitation only — ranked nowhere |`; Appendix C is unchanged. Then:

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -1
```

Expected: all passed — the join guard now sees 23 ids on both sides.

- [ ] **Step 5: The guide**

Add `../designs/2026-08-29-successor-admission-design.md` to the `sources:` of `docs/guide/contracts-and-adoption.md` and `docs/guide/computation-and-reproducibility.md`; add the new results record beside cut 11's in `contracts-and-adoption.md`'s sources and point its "newest results record" link at it; set both pages' `updated: <today>`; grep `cut 11` across `docs/guide/*.md` and correct every "implemented through cut 11" style claim to cut 12, bumping `updated` on each page touched.

- [ ] **Step 6: Full gates and diff review**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1
cd .. && git diff --check main && echo DIFF_CHECK_CLEAN && git diff main --name-status
```

Expected: `CHECK_GUIDE_OK`; all passed; `DIFF_CHECK_CLEAN`; the file list contains only: the promoted design (R), the cut, the intent-boundary design, the adoption ledger, the roadmap, `roadmap_status.py`, `README.md`, the guide pages touched, the results record and ledger under `docs/plans/`, this plan, and under `python/`: `src/science/{errors,spec,succession}.py`, `src/science/world/records.py`, `src/science/intents/{evidence,reduce}.py`, `tests/{conftest,test_designs_corpus,test_spec,test_record_capture,test_intent_evidence,test_intent_reduce,test_succession,test_succession_errors,succession_fixtures}.py`, `tests/acceptance/{n2_arms_cut11,n2_arms_cut12,test_n2_cut12,test_successor_admission_acceptance}.py`, `tools/cut12_acceptance.py`. Anything else is out of scope — revert it.

- [ ] **Step 7: Commit**

```bash
git add -A docs README.md python/tools/roadmap_status.py
git commit -m "docs: bank the successor-admission slice, close G4, and re-rank the roadmap at cut 12"
git log --oneline main..HEAD
```

The branch is then ready for the human-owned `--no-ff` merge into `main`. The next cut — `run-confinement` — is its own brainstorming session against computation §4.4b.
