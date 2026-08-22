# Conformance cut 7 — discharge results

**Date:** 2026-08-22
**Subject:** the world-index epoch carrier
(`docs/designs/2026-08-20-world-index-slice-2-design.md`), measured against
conformance cut 7's frozen selection
(`docs/designs/2026-08-20-conformance-cut-7.md`).

**The frozen source rows, selected bullets, and accounting are not edited
here.** Cut 7 froze on 2026-08-20 and results are recorded separately, which is
what this document is.

**Integration state.** Every commit named below was made on the implementation
branch `design/world-index-slice-2`, whose base is `f3a14bf` on `main`. **That
branch was merged into `main` on 2026-08-22 with `--no-ff`, preserving its
history as §7 requires**; the integration commit is `83744e7`, and the branch
and its worktree have since been removed. The merge does *not* discharge §7's
constraint — read it before any later history rewrite.

## 1. The accounting, re-derived

Recounted from the frozen cut's own §3 bullets rather than copied from its §4.

| state | rows | n |
|---|---|---:|
| full | X1, X3, X7, X8, X9, X10, X11 | 7 |
| part | X2, X5, X12, W8a | 4 |
| deferred | — | 0 |

**7 full + 4 part + 0 deferred = 11 frozen rows read.**

Declaration units, counting each **Selected** and **Labeled** bullet once at its
home:

| row | X1 | X2 | X3 | X5 | X7 | X8 | X9 | X10 | X11 | X12 | W8a | labeled |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| units | 2 | 2 | 2 | 1 | 2 | 2 | 6 | 4 | 2 | 5 | 10 | 10 |

X rows sum to 28; W8a contributes 10; the ten §3.3 labeled declarations sit
outside the row accounting. **38 selected + 10 labeled = 48 declaration
units.** The landed declaration module `python/tests/n2_arms_cut7.py` carries
exactly 48 arms with the same per-row distribution, ten of them spelled
`labeled:…`. Cross-referenced clauses (X10's two rule transitions and its
bare-version instance inside W8a, X3's no-implicit-latest half inside W8a's
belief-invariance unit, and §3.4's W5 producers-map candidate homed in W8a) are
counted once, at their home.

## 2. What ran, and where

Science resolves `atoms-core` and `nodes-core` as editable path dependencies
(`python/pyproject.toml` `[tool.uv.sources]`). All Science gates ran from this
repository's `python/` directory, sequentially — never concurrently, because the
cut-5, cut-6, and cut-7 runners share `SCIENCE_CUT*_ROOT` work directories.

### 2.1 Portable gates at `be96250`

| gate | command | result | claim |
|---|---|---|---|
| portable Science tests | `uv run pytest` | 1761 passed | behavior; **no** durability claim |
| lint | `uv run ruff check .` | All checks passed! | code quality |
| typing | `uv run pyright` | 4 errors, 0 warnings, 0 informations | typing; equal to `main`'s pre-existing baseline |
| contributor guide | `uv run python tools/check_guide.py` | passed | documentation consistency |
| cut-7 acceptance module | `uv run pytest tests/acceptance/test_n2_cut7.py` | 42 passed | portable journey + declaration audit; **not** discharge |
| cut-6 runner | `uv run python tools/cut6_acceptance.py` | 23 passed | cut 6 unchanged under this branch |
| cut-5 runner | `uv run python tools/cut5_acceptance.py` | 39 passed | cut 5 unchanged under this branch |
| cut-7 runner | `uv run python tools/cut7_acceptance.py` | exit 0 (39 + 23 + 42) | **cut-7 discharge on the certified tuple** |
| whitespace | `git diff --check` | clean | no whitespace errors |

`pyright` takes no path argument. A narrowed `pyright src` reports 0 and hides
the rest of the project; the whole-project form is the gate, and 4 is `main`'s
baseline, not a regression introduced here.

`uv run pytest` is run bare. `pyproject.toml`'s `addopts` already contains
`-q`, so adding `-q` produces `-qq` and suppresses the pass count.

The portable suite excludes `tests/acceptance` by configuration
(`--ignore=tests/acceptance` in `addopts`). It proves portable behavior only.

### 2.2 The certified run

Reproduced verbatim from the Task 13 execution record. Portable green is not
cut discharge; this run is.

**Host and certified tuple**

- backend `LinuxBackend`; storage profile
  `StorageProfile(profile_id='flush-honoring-disk.v1')`
- work directory: default, `.cut7-acceptance` beside the checkout —
  `SCIENCE_CUT7_ROOT` unset, so the certified volume is the repository's own
- volume: ext4 on `/dev/nvme0n1p2`, mounted `rw,noatime,data=ordered`
- kernel `7.1.8-arch1-3`
- source commit `279391a`

**Command and output, exactly as run**

```text
$ cd python && uv run python tools/cut7_acceptance.py
### command: uv run python tools/cut7_acceptance.py
### SCIENCE_CUT7_ROOT: <unset; default .cut7-acceptance beside the checkout>
[cut7 phase 1/3] cut5_acceptance.py
.......................................                                  [100%]
39 passed in 14.34s
[cut7 phase 2/3] cut6_acceptance.py
.......................                                                  [100%]
23 passed in 10.79s
[cut7 phase 3/3] test_n2_cut7.py
..........................................                               [100%]
42 passed in 37.99s
### exit: 0
```

Phase 1 (cut 5): 39 passed. Phase 2 (cut 6): 23 passed. Phase 3 (cut 7): 42
passed. **Terminal result: exit 0.**

The runner probes the volume before collection. An uncertified tuple is an
error, never a skip:

```text
$ SCIENCE_CUT7_ROOT=/dev/shm/cut7-uncertified uv run python tools/cut7_acceptance.py
cut-7 acceptance cannot run here: the volume beneath /dev/shm/cut7-uncertified is not on the engine's certified allowlist.
  the engine refused with CapabilityUnavailable: filesystem 'tmpfs' has no barrier-option table; the engine cannot decide which of its options bear on durability
  set SCIENCE_CUT7_ROOT to a directory on a certified volume, or recertify with the
  engine's own tooling. This is an error, not a skip: an environment that cannot
  exercise durability must not be able to report cut-7 discharge.
### exit: 2
```

No prefix ran under that refusal. The durability claim is never inferable from
the portable suite.

### 2.3 Declaration audit

The cut-7 acceptance module audits every declared arm against the standing N2
harness for `vacuous`, `stale`, `mixed`, `uncollected`, and class-node collapse.
All 48 arms resolve `sound`; the unsabotaged baseline passes. X9's
relocated-head arm interposes a real corpus write between the state capture and
the relocated head capture, and carries a declaration-time nonvacuousness
witness (`RELOCATED_HEAD_WITNESS`) that passes under relocation alone and fails
once the write is interposed. W8a's agreement arm constructs two distinct world
roots, each resolving the same binding from its own rules store over the same
corpora.

## 3. Commit identities

Base `f3a14bf` on `main`. The commits this discharge measured, in order:

| commit | subject |
|---|---|
| `70c0769` | docs: draft conformance cut 7 for the epoch carrier |
| `c484859` | docs(cut7): close the second reader's findings |
| `b987ebf` | docs(world): bank epoch carrier and cut 7 |
| `4a7dc19` | docs(world): pin subject projections and add the slice 2 plan |
| `f703913` | refactor(world): promote world module to package |
| `c8c0b12` | test(cut6): pair the pinned sabotage direction with a clean run |
| `23e5476` | feat(world): add coherent capture locking |
| `73d2d0d` | fix(world): refuse an unbalanced writer release |
| `7e6e12a` | feat(world): add fixture-bound rule storage |
| `0ef9db1` | feat(world): remove exact rule bindings explicitly |
| `fb5ebd6` | fix(world): separate receipt carrier reading from receipt contract |
| `55853b8` | fix(world): let a receipt missing an identity member reach the validator |
| `8271616` | feat(world): derive epoch projections and receipts |
| `376d649` | test(world): make the normative fixtures prove they discriminate |
| `f44eb3e` | feat(world): capture coherent epoch inputs |
| `91f4e79` | test(world): pin the within-id preflight order and the capture divergence |
| `b4197f0` | feat(world): publish and open immutable epochs |
| `49a8f9f` | fix(world): check every coverage entry, not only the stamped ones |
| `6005a45` | feat(world): expose bound epoch reads |
| `f798a7e` | fix(world): keep the world lock off validation's corpus reads |
| `eb7e683` | fix(world): keep both belief-reach checks and drive the carrier read faults |
| `7f52697` | fix(world): convert non-UTF-8 carrier bytes and drive every read fault |
| `d036610` | feat(world): delete complete epochs explicitly |
| `c79f356` | test(n2): declare conformance cut 7 |
| `8ca085e` | test(n2): close cut-7 declaration review findings |
| `279391a` | test(acceptance): certify world epoch publication |
| `4ed5fd4` | test(world): restore the project-wide pyright gate |
| `be96250` | docs(plan): point the slice-2 gates at the whole project |

`f703913` is the package promotion: `science/world.py` becomes
`science/world/registry.py` with a new `science/world/__init__.py` re-export
surface and no slice-2 semantic change. `python/src/science/world.py` does not
exist in the tree, and no compatibility carrier was left behind. No `atoms`
import escaped `science/root.py`.

Cut 5 and cut 6 are prefixes, never edits. Compared against the branch base
`f3a14bf`, `python/tools/cut5_acceptance.py`, `python/tools/cut6_acceptance.py`,
`python/tests/n2_arms_cut5.py`, `python/tests/n2_arms_cut6.py`, and
`python/tests/acceptance/test_n2_cut5.py` are byte-identical.
`python/tests/acceptance/test_n2_cut6.py` is **not**: see §7.

## 4. The cross-repository prerequisite

This slice required one new public command in the sibling `atoms` repository:
`read_chain`, returning one complete validated `ChainView` under the recovery
lease (slice-2 design §2). It was designed, implemented, reviewed, and **merged
into the local `atoms` `main` only — it has never been pushed to any remote.**
The commits are `29674c2` (`docs(coordinator): design public chain read`) and
`2c077ed745f6eabfec6816c16803e78eefaa279c`
(`feat(coordinator): expose validated chain reads`); the `atoms` remote `main`
still stands at `7e97e09`.

Science resolves `atoms-core` through an editable path dependency, so that local
merge is what makes this branch green. **Anyone reproducing this discharge needs
that `atoms` commit, and it exists only in a local clone.** Pushing it is a
prerequisite of any integration that expects a fresh checkout to build.

`read_chain`'s own behavior is not re-certified here. Its tests live in `atoms`;
this cut consumes the specification §2 contract and gates on the landed command.

## 5. What the discharge establishes

**Artifact 1 — world index: complete.** The rules store, coherent capture, the
build, content-addressed epoch publication with `current`, the four derived maps
(address, producers, retraction, coreference), the producer snapshot, the four
fixture-bound derivation receipts on one contract, the receipt-rebuild evaluator
with its `validated | refuted | unresolvable | malformed` outcomes, the bound
read surface with its closed `Resolved | NotPresent | Unknown` union and
coreference edge query, and the whole-epoch GC act with its sever report are all
implemented and discharged against the frozen cut.

**Artifact 2 — corpus manifests / `corpus_id` minting: the build-time uniqueness
half is closed.** X5's build arm refuses a coverage naming two carriers with one
`corpus_id` (`CoverageUnresolvable` at preflight, with the standing
`duplicate-carrier` finding still emitted by presence reduction). **The fork
constructor remains deferred** on Plan B's root-fork command; `fork-of`
admission still uses fixture-authored manifests.

**Artifact 4 — `atoms` A8: the public chain reader has landed.** The slice-2 §2
prerequisite `read_chain` is implemented in `atoms` (see §4) and Science consumes
it through `science.root`'s injected chain-head callback. The remaining §4-row
holdings prerequisites are untouched.

**Artifact 5 — tamper-evident mutation log: the anchor carrier exists.** Each
published epoch carries the per-corpus `(genesis_digest, head_digest)` anchors
and the build-start world head, captured inside the same hold that captured the
corpus state; a certified arm decodes both from the engine's committed entry
files and pins the correspondence. **Log verification (L1–L13), the explicit
anchor act, replay, and genesis-to-mirror agreement remain deferred.**

## 6. What this run does not claim

The frozen cut's own limitations stand unchanged, and the design's dated
deferrals are preserved:

- **Genesis-to-mirror verification** waits on the configuration-mismatch audit
  and its ownership decision.
- **The fork constructor** waits on Plan B's root-fork command.
- **Cross-process locking** is out of scope: `OperationLock` and its capture
  generation are in-process, and single-writer operation across processes
  remains a stated deployment obligation.
- **GC tombstones and replayable sever reports** are deferred until exact GC
  retry is a real requirement. A post-commit retry raises `EpochUnknown`;
  `atoms` owns transaction recovery.
- **Sequence-number decoration** is omitted by decision — identity plus
  `current` is sufficient.
- **The epoch-enumeration sweep** and world-level epoch findings are an explicit
  dated non-goal until a consumer requires one. No findings sweep exists.
- **The pinned authority snapshot** (artifact 11) is untouched.
- **Two enumerated kinds remain prose.** `coreference-attestation` and
  `instrument-certification` have no governed stored-kind definitions. Their
  empty enumerations are supported and the selected empty-enumeration instances
  are recorded as such; every populated membership, reduction, and
  omission-refutes arm waits on the kinds' own charters. Production capture
  refuses a record claiming either kind with `EnumeratedKindUngoverned` rather
  than deriving from unvalidated content.
- **X2's persistence-cut arm is deferred, not argued away.** No Science-side
  power-fail harness exists. Committed registration-entry evidence plus the
  engine's own A8 certification is the whole durable claim.
- **The evaluator is exercised without its future callers.** The
  snapshot/receipt import boundary, the world-scale audit, the diagnostic query,
  and the snapshot reduction states (`checked`/`contradicted`/`unchecked`) defer
  with their surfaces. When they land they must call the evaluator this cut
  certifies rather than reimplement it.
- **World resolution is not claimed.** The resolution refusals are local carrier
  checks over configured roots; no world-scale resolution or federation claim is
  made.

## 7. Integration constraint — this branch must be merged preserving history

Cut 6's 22 arms all declare `module="world.py"`. `f703913` moved that file to
`world/registry.py`, so `python/tests/acceptance/test_n2_cut6.py` was amended
(`f703913`, then `c8c0b12`) to audit cut 6's source mutations against the
**pre-move tree at commit `4a7dc19`**, and Task 12 added a freeze guard pinning
that amended file to `c8c0b12`. The amendment is the only deviation from "cut 5
and cut 6 are byte-identical"; the runners and both declaration modules are
untouched.

**A squash merge, or a rebase that orphans `4a7dc19`, reds cut 6 permanently.**
The audit resolves `4a7dc19` as a real object; if that commit is not reachable
from the integration commit, the cut-6 acceptance runner cannot check out the
tree its arms name and there is no way to repair it without editing a frozen
cut. Integrate with a merge that preserves this branch's history.

**It reds cut 7 as well, and loudly.** `tests/acceptance/test_n2_cut7.py`'s
`FROZEN_PRIOR_CUT_FILES` pins five prior-cut surfaces — cut 5's and cut 6's
declaration modules, both runners, and cut 6's amended acceptance module —
against `4a7dc19` and `c8c0b12`. The guard shells out to `git diff --quiet
<pin> HEAD`; an unreachable pin makes git exit 128, which is not 0, so the
assertion fires with the path and the pin named. That is the useful asymmetry:
cut 6 degrades into an acceptance run that cannot check out the tree its arms
name, while cut 7 fails in the ordinary test suite with a message that says
which commit went missing.

**Mitigation, applied 2026-08-22: both commits carry a tag.**
`pin/cut6-pre-move-tree` points at `4a7dc19` and `pin/cut6-acceptance-amendment`
at `c8c0b12`; each tag's message names the file it protects and the failure it
prevents. A tag keeps the object from being collected and makes the constraint
discoverable from `git tag --points-at`. The tags were first made annotated —
this checkout had no signing key configured — and re-made **SSH-signed** later
the same day, with a repo-local `gpg.ssh.allowedSignersFile` so `git tag -v`
verifies them here; a clone verifies them only after configuring its own
allowed-signers entry for the key. One limit remains, stated plainly: a tag
does not survive a hash-rewriting migration, so the indefinite lifetime below
stays exactly as true after tagging as before it. The tags are local; nothing
has been pushed.

**The lifetime of this constraint is indefinite.** It is not discharged by
merging: `4a7dc19` and `c8c0b12` must stay reachable from *every future
integration commit*, not merely from the first one. Any later history rewrite —
a repository migration, a `filter-branch`, an archival squash of old branches —
silently inherits it as a blocker, and per the frozen-cut rule the resulting red
cannot be repaired by editing the cut.

## 8. Known limitations of the landed implementation

Recorded honestly and not fixed in this landing. None is load-bearing for the
discharge above; each is a candidate for a follow-up.

**Recommended follow-up, typed.** `python/src/science/world/epoch.py:212`
declares `RECEIPT_KINDS: Mapping[str, str]` where the values are in fact
`ReceiptKind` literals. The clean fix moves the `ReceiptKind` `Literal` into
`epoch` beside `RECEIPT_KINDS` and re-exports it from `derive`, because `derive`
imports `epoch` and the reverse import is unavailable at module scope. Consumers
currently work around the widened type.

**Structure and clarity**

- `read.py` is roughly 743 lines and is the largest module in the package.
- The `SYMBOL_KINDS` table is duplicated between `tests/acceptance/test_n2_cut7.py`
  and `tests/test_world_build.py`, pinned equal by a test, because no public
  shipped-symbol → receipt-kind join exists in `science`. Someone should own
  that join.
- `SeveredIdentity.subject` carries a receipt *kind*, while §7.5 and §7.6 use
  "subject" for what a receipt is *about*. Defensible as the one field that also
  fits `SNAPSHOT_SUBJECT`, but the vocabulary collides.
- `_contract_fault` has a sibling bare `except Exception`.
- `tools/cut7_acceptance.py`'s `PROBE_REFUSED = 2` docstring claims the code is
  distinct from pytest's own; it is not — `pytest.ExitCode.INTERRUPTED` is also
  2. The behavior is correct; the docstring's justification is wrong.
- **`_require_lower_hex` is defined twice**, at `world/registry.py:178` and
  `world/derive.py:906`, with behavior that differs only in whether the hex
  alphabet is a named constant. Neither definition is shared, so `world/read.py`
  (`:403`, `:413`) and `world/epoch.py:1029` reach across a module boundary into
  `registry`'s *private* copy rather than importing one owned helper.
- **`_require_text` is defined three times with divergent contracts**, and the
  divergence is silent because the name is identical: `world/epoch.py:518`
  admits `""` (deliberately — its docstring says which string it is belongs to
  the validator), while `world/derive.py:900` and `decode.py:79` both refuse the
  empty string, and `decode.py`'s raises `MalformedWireClaim` where the other
  two raise `ValueError`. A reader who learns one contract will carry it to the
  wrong call site. **The fix is renames, not deduplication.** All three
  contracts are correct where they stand; collapsing them into one helper with
  a flag would trade a naming collision for a defensive interface, which this
  repository's rules forbid. Distinct names — `_require_text_allow_empty` in
  `epoch`, a `decode`-local `_require_wire_text` — remove the collision without
  touching any contract. Only `_require_lower_hex` above is a genuine dedup:
  one definition, exported properly, so `read.py` and `epoch.py` stop reaching
  into a private.

**Performance and concurrency**

- `_reduced_pairs` assumes published endpoints are already sorted.
- `_edge_context` takes two lock acquisitions.
- Each non-target epoch's eleven members are read twice per deletion — once by
  the sever scan and once by `_locked_open_epoch`.
- `rules.py:349`, `:401`, and `:532` take the world lock without crossing the
  recovery barrier, including `remove_rule_binding`, which reads every retained
  epoch. Pre-existing shape, out of this slice's scope.

**Coverage gaps in the tests themselves**

- `test_the_actor_must_be_encodable_text` drives only `actor=None`; the
  `v1.encode` `ValueError` path its name promises is untested, and nothing pins
  `snapshot is None` or a short `receipts`.
- A symlink at `epochs/<valid-identity>` pointing at an empty directory raises
  `EpochUnknown` out of `build_epoch` — an error §10 does not list for the build
  owner. Adversarial input only.

**Undocumented dependencies**

- The four arms naming acceptance nodes audit `sound` **only** because
  `_run_check`'s explicit node id beats `addopts`' `--ignore=tests/acceptance`.
  A pytest change that made `--ignore` win would turn four declared arms into
  silent `uncollected` findings rather than a loud failure. Nothing states this
  dependency in the harness.
- `.gitignore` lists `.cut4-acceptance/` and nothing for cuts 5, 6, or 7. Each
  runner removes its own `run-` directory in a `finally`, so the gap surfaces
  only when a run is interrupted before that `finally` — at which point the
  residue is untracked and visible in `git status`.
- No lock file enforces the "never run two acceptance runners concurrently"
  rule; the shared `SCIENCE_CUT*_ROOT` work directories make it a convention
  rather than a mechanism.
- Upstream `nodes` `Relation.from_serialized` hardening remains outstanding.

## 9. Corrections this landing made to the frozen and banked text

Three claims were found wrong and corrected, per this repository's rule that a
status header and a design sentence are claims about the past. The first two
were corrected in the landing change itself; the third on 2026-08-22, after the
merge:

1. **The slice-2 design's "empty directories are nonsemantic and may remain"
   was wrong as written** (§9, and the same wording in §4.3). Implemented
   literally it corrupts worlds: the executor deletes files, not directories, so
   a whole-epoch deletion leaves `epochs/<id>/` empty, and an empty directory
   read as a carrier is a carrier missing all eleven members. A reviewer
   reproduced all three consequences — the retained-receipt scanner refusing
   forever, a repeated deletion answering `EpochMalformed` instead of §9's own
   `EpochUnknown`, and republication of the same bytes blocked. Task 11 shipped
   an `_emptied()` guard; §9 now says the emptied directory **remains and every
   scan of `epochs/` ignores it**, and records the consequence: `open_epoch` on
   an externally destroyed carrier (`rm epochs/<id>/*`) answers `EpochUnknown`
   where it once answered `EpochMalformed`. That is forced by §9's own
   no-tombstone decision and is now the documented behavior.
2. **The implementation plan's Task-12 check-node table was unusable as
   written.** It spells all 48 nodes `file.py::function`. Every named function
   exists verbatim, but 31 of them are methods on a class, and
   `pytest file.py::method` exits 4 — which the N2 harness scores `uncollected`,
   not `sound`. Transcribed literally the table would have produced 31 arms that
   look like declarations and assert nothing. Cut 1 already spells node ids with
   the class segment and the landed declarations do too; the table now carries
   that annotation. No unit was renumbered or re-homed, and the reduction of the
   landed declarations back to `file::function` is set-identical to the table.

3. **This record was dated 2026-08-21; the discharge is 2026-08-22.** The
   original date named the evening the certifying acceptance run first went
   green (`279391a`, 22:40 on 2026-08-21). But two later commits changed
   surfaces cut 7's own arms audit — `4ed5fd4` and `be96250` touched six
   `tests/test_world_*.py` modules, and `f3217cc`, at 00:41 on 2026-08-22,
   touched `tests/test_world_rules.py`, which three cut-7 arms name. A
   discharge dates from the run that certifies the tuple actually landed, so it
   cannot predate the last change to an audited surface. The runs that satisfy
   that — after `f3217cc`, after the merge `83744e7`, and after `e7ed517` — all
   ran on 2026-08-22. The date is corrected here, in the frozen cut's status
   header, and in the root `README.md`.

## 10. Execution record — the rulings ledger was destroyed

Recorded 2026-08-22, after the merge.

This slice was executed with a subagent-driven controller: a fresh implementer
per task, an independent review after each, and a bounded fix loop. Every
controller decision that departed from the plan text was written to a rulings
ledger at `.superpowers/sdd/2026-08-20-world-index-slice-2/progress.md` — a
git-ignored file inside the disposable worktree. **The worktree was removed
before the ledger was copied out, so the ledger is gone and nothing in git ever
held it.** Rulings R1–R15 are unreproducible; what follows is the reconstruction
that survives, and it is a reconstruction, not a transcript.

**Reconstructed rulings, with what each costs if wrong**

- **R8** — amend `tests/acceptance/test_n2_cut6.py` to audit the pre-move tree
  at `4a7dc19` rather than declare a cut 6b. Cost: the permanent reachability
  constraint in §7. Judged under-priced rather than wrong at final review, and
  §7 now prices it.
- **R10** — integrate preserving history. Cost if ignored: cuts 6 and 7 red,
  unrepairable. Discharged by the `--no-ff` merge at `83744e7`.
- **R13** — a criterion the controller gave Task 6 about carrier failure was
  withdrawn as wrong: §8.2's list is closed and a missing receipt *key* is not
  on it. Cost if it had stood: a receipt outcome misclassified as carrier
  failure, collapsing the §8.2 layering.
- **R17** — treat project-wide `pyright` as the gate, and insert Task 13.5 to
  restore it. Partly wrong as first framed: `python/README.md` documented the
  gate as `pyright src`, so the implementers who reported it clean reported
  truthfully. The 73 added errors and the remediation were real; the imputation
  of misreporting was not, and is withdrawn here.
- **R19** — the frozen cut's check-node table is spelled `file.py::function`,
  but 31 of its 45 names are methods; declarations carry the class segment
  instead. Recorded in full at §9.2.
- **R18, R20, R22, R23** — process rulings: one skipped fix round on an approved
  task, one skipped re-review of a five-line documentation fix the controller
  verified itself, one extra fix round spent closing a half-unfalsified arm on
  an already-approved Task 12, and the parking of the two helper duplications
  now recorded in §8.
- **R1–R7, R9, R11, R12, R14, R15, R16, R21** — lost. Their effects are in the
  commits and in the reviews those commits passed; their reasoning is not
  recoverable.

**The process failure, named.** The rulings ledger is an execution artifact
whose whole purpose is to outlive the execution, and it was kept in
git-ignored scratch inside a worktree scheduled for deletion. That is the same
durability failure class this repository already names for certified arms: an
artifact that must survive belongs on the durable volume beside the checkout,
not in scratch. Future subagent-driven executions must either keep the rulings
ledger at a tracked path and commit it at close-out, or copy it out of the
worktree before `git worktree remove`.
