# Conformance cut 12 — discharge results

**Date:** 2026-08-29
**Subject:** successor admission, G4's closure
(`../designs/2026-08-29-successor-admission-design.md`), measured against
conformance cut 12's frozen selection
(`../designs/2026-08-29-conformance-cut-12.md`).

The frozen cut body from `**Sources:**` onward remains byte-exact at `b2f9593`;
only its status header has evolved through banking and discharge correction.

**Integration state.** Every implementation commit was made on
`design/successor-admission`. The reviewed implementation head is `d958c64`.
Banking at `c4efa9b` and its ordering correction at `66717fa` preceded the
final whole-branch review and fix.
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
  the root's operation lock and never from a caller-supplied set; even a writer
  using the exported raw `DurableOperationPort` waits and is not consulted.
- Class 1a reads only active, coherent, failing verifications; an incoherent
  failing verification or an incoherent superseder of one refuses the act
  globally, naming the record.
- Class 2 and class 1b come from cut 11's reducer unchanged; an unresolvable
  intent for the superseded spec refuses; another spec's does not block.
- Oversized records lift only through a coherent superseder; unreadable and
  uninspectable surfaces refuse; nothing durable leaves no trace.
- The real mode-based unreadability arms withdraw mode at the exact file or
  directory open seam and assert both non-root execution and actual mode `000`.
- `capture_records`' certified surface, cut 11's reducer verdicts, and the
  core's cut-3 anchor line are byte-for-byte unchanged.

## 2. What ran

All commands ran sequentially from `python/`. Durable work ran on the
certified volume at `../.cut12-acceptance`, the default beside the checkout;
`SCIENCE_CUT12_ROOT` was unset.

### 2.1 Host and certified tuple

- backend `linux`, revision `linux-4`; storage profile
  `flush-honoring-disk.v1`
- kernel `7.1.10-arch1-1`
- ext4 device `259:2` (`/dev/nvme1n1p2`), mounted at `/mnt/ssd` with mount
  options `rw,noatime` and superblock options `rw,data=ordered`
- normalized barrier options `async`, `barrier=1`, `commit=5`, `data=ordered`
- durability features `compat=0x3c`, `incompat=0x246`, `ro_compat=0x46b`
- certification record
  `docs/certification/2026-08-28-ext4-linux-7.1.10-arch1-1.json`
- execution authority: the editable Atoms dependency loaded local `main` at
  `dd658ac`, a descendant of remote contract head `038513f`; between them the
  only Atoms production diff is the four-line allowlist/certification-reference
  replacement in `atoms/fs/volume.py`
- that local head is cut 11 execution-ledger R3's separate host-recertification
  prerequisite: the Linux 7.1.10 record reports 3,281 crash prefixes with zero
  violations; remote `038513f` remains the binding transaction-engine contract,
  and no Atoms change ships in this Science branch (ledger R6)

### 2.2 Certified cut-12 runner

`uv run python tools/cut12_acceptance.py`

```text
[cut12 phase 1/3] cut11_acceptance.py
[cut11 phase 1/3] cut10_acceptance.py
[cut10 phase 1/2] cut9_acceptance.py
[cut9 phase 1/2] cut7_acceptance.py
[cut7 phase 1/3] cut5_acceptance.py
39 passed in 15.52s
[cut7 phase 2/3] cut6_acceptance.py
23 passed in 11.68s
[cut7 phase 3/3] test_n2_cut7.py
42 passed in 60.15s (0:01:00)
[cut9 phase 2/2] test_n2_cut9.py
23 passed in 18.38s
declared units: 30 (pinned by test_the_declared_units_are_unique_and_number_thirty, among the tests above; not itself a pytest total)
[cut10 phase 2/2] test_n2_cut10.py
36 passed in 10.93s
declared units: 31 (= len(CUT10_ARMS); pinned by test_the_declared_units_are_unique_and_number_thirty_one, among the tests above; not itself a pytest total)
[cut11 phase 2/3] test_intent_boundary_acceptance.py
18 passed in 5.56s
[cut11 phase 3/3] test_n2_cut11.py
17 passed in 22.86s
declared arms: 66 (= len(CUT11_ARMS), normalizing to the 26 frozen units pinned by test_the_partition_accounts_exactly_the_26_frozen_units, among the tests above; not itself a pytest total)
[cut12 phase 2/3] test_successor_admission_acceptance.py
4 passed in 1.97s
[cut12 phase 3/3] test_n2_cut12.py
16 passed in 15.19s
declared arms: 50 (= len(CUT12_ARMS), normalizing to the 24 frozen units pinned by test_the_partition_accounts_exactly_the_24_frozen_units, among the tests above; not itself a pytest total)
```

### exit: 0

### 2.3 Portable and static gates

`uv run pytest` — 2724 passed in 477.42s (0:07:57)

### exit: 0

`uv run ruff check .` — All checks passed!

### exit: 0

`uv run pyright` — 0 errors, 0 warnings, 0 informations

### exit: 0

## 3. Review and implementation rulings

The earlier post-implementation review reported 3 findings (0 Critical,
2 Important, 1 Minor). Commit `2b9245e` closed all three, and its scoped
re-review was clean (ledger R5). The declaration review expanded the 24 frozen
units into 50 lettered arms; the frozen partition never changed. The two
cut-11 anchors that moved with `reduce_registration` moved in whitespace only
(ledger R4); cut 3's three G4 sabotages match the unchanged anchor line
(ledger R2).

The Task 8 discharge-record review separately reported 1 Critical finding: the
record named the certified tuple but did not disclose that the editable Atoms
dependency loaded local `dd658ac`, so the unconditional deviation claim
overstated the literal frozen execution boundary. This correction and ledger
ruling R6 close that one historical-claim defect; it is not part of the 3
post-implementation findings above.

The final whole-branch review at `66717fa` reported **3 (0 Critical,
2 Important, 1 Minor)** findings: the exported durable port bypassed the
admission lock; mode `000` was applied too early for a synchronized
certified-volume test path; and live execution records retained the
specification's pre-promotion path. Commit `d958c64` closes all three: each durable-port
mutation takes the shared per-root lock, whose same-thread writer acquisition
is now owner/depth reentrant for `CorpusWriter`; G4u11 uses the raw port; all
four mode arms drive and assert mode at their exact open seam; and the tracked
and ignored live ledgers name the promoted design. The fresh portable and
certified gates above passed after that commit (ledger R7).

The frozen selection, declaration partition, and cut body did not change.
Science runtime behavior changed only to serialize the three exported
durable-port mutations on the already authoritative operation lock. The
literal execution-boundary engine head still differs exactly by ledger R6's
separate certified-host prerequisite: local Atoms `dd658ac` descends from
remote contract head `038513f` with only the four-line
allowlist/certification-reference production delta. The exact rationale and
definitive runner summaries live in
`2026-08-29-successor-admission-ledger.md`.

## 4. Commit identities

| commit | subject |
|---|---|
| `ca023ee` | docs(specs): design the successor-admission slice and conformance cut 12 |
| `8f1dc03` | docs(specs): close the successor-admission design review's five findings |
| `a3020d6` | docs(specs): name every capture failure, return the whole registration reduction, and give the refusal an initializer |
| `4996fb4` | docs(specs): keep capture_records' RootKind guard beside capture_surface |
| `b270635` | docs(specs): factor the registration reduction around cut 11's frozen anchors |
| `9f4a4ca` | docs(plans): plan the successor-admission slice and conformance cut 12 |
| `757f028` | docs(plans): close the successor-admission plan review's eight findings |
| `057e0f8` | docs(plans): close the successor-admission plan review's eight follow-ups |
| `f419c71` | docs(plans): correct the arm count, freeze K2's two new clauses, and remove the last execution-time branches |
| `f130421` | docs(plans): keep frozen row copies byte-exact |
| `b2f9593` | docs(designs): freeze conformance cut 12, successor admission |
| `eafff95` | docs(plans): record cut 12's freeze hash in the execution ledger |
| `8d92843` | feat(errors): name the successor-admission act's evidence refusal |
| `c112550` | feat(spec): admit a successor over two blocker classes with fixed precedence |
| `83236db` | feat(records): name the descent's failures beside the unchanged record capture |
| `0b420a6` | fix(records): suppress close failures during record capture |
| `f0e65a6` | refactor(intents): factor the record gate and the registration reduction into values |
| `06ea4eb` | docs(plans): record the cut-11 anchor move |
| `1547365` | feat(succession): admit a spec successor over the chain's qualification and the corpus's failing evidence |
| `9f42ce0` | fix(succession): close the root probe exception boundary |
| `5dff360` | test(cut12): declare successor-admission arms, durable checks, and the acceptance runner |
| `2b9245e` | fix(succession): reuse qualified evidence and normalize input failures |
| `94d3c9a` | docs(plans): record conformance cut 12's discharge |
| `e15e51a` | docs(plans): correct cut 12's execution authority |
| `c4efa9b` | docs: bank the successor-admission slice, close G4, and re-rank the roadmap at cut 12 |
| `66717fa` | docs: close G4 in the adoption ledger's order of work |
| `d958c64` | fix(root): serialize durable operation port mutations |

The banking and status-ordering commits preceded the final whole-branch review;
`d958c64` is the final reviewed implementation head measured above.

## 5. Remaining boundary

Cut 12 closes G4 at persistence width and reads R12 in full. L7 stays partial
on exactly its banked limitation, L7u1. Event-level L8 and the L13 preimage
resolver remain with their named owners. `admit_spec_successor` has no
production caller; the run boundary's nomination of a superseded spec is a
later design's.
