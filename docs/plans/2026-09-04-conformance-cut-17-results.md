# Conformance cut 17 — discharge results

**Date:** 2026-09-04
**Discharge commit:** `4f59d9c`
**Subject:** write permits
(`../designs/2026-09-04-write-permits-design.md`), measured against frozen
§7/§9 at `c2f87b3`, the implementation amendment at `b25fcc7`, and the
renumbering and relocation amendment at `e6b8c0b`. Section 14.1 assigns this
work cut 17; the frozen text's cut-16 references are cited, not edited.

## 1. Accounting and disposition

Cut 17 selects **8 units**, E1–E8. Label K1 adds **1 labeled unit**, for
**8 selected + 1 labeled = 9 units**. The executable declaration expands them
into **24 unique one-mutation sabotage arms**. Every baseline check resolved
and passed, and every sabotage failed at least one exact cited check.

This discharge closes E1–E8:

- permits hold closed act families, governed kinds, and the explicit
  ungoverned-kind flag;
- one `Authority` binds the permit and actor at each construction seam;
- every inventoried write checks its family and emitted kinds before an
  effect, with no caller-supplied actor;
- requirement construction and permit coverage enforce the declared route;
- the static inventory is closed in both directions over 36 definitions; and
- run, holdings, world, import, and two-root relocation refusals leave their
  durable surfaces unchanged.

Cut 10 is cited rather than run because its H4u1 and J8 whole-body holdings
sabotages are stale by design after the required leading checks. Its five
cited files remain byte-identical at these SHA-256 digests:

| path | SHA-256 |
|---|---|
| `python/tests/acceptance/n2_arms_cut10.py` | `e7e3cf02f8d033a9bf507b6eba0f4968bcf702c901ad3a753013f062c02e5ae8` |
| `python/tests/acceptance/test_n2_cut10.py` | `4058b86679b9a7b17bbfd5115ba3e7c21896e2316c384d700c4af052674dc650` |
| `python/tools/cut10_acceptance.py` | `39a1e333d8b99bacf0bcdc416e86ef6d68e97be797c6acc3c31c922bab838edf` |
| `docs/designs/2026-08-24-conformance-cut-10.md` | `17dcc49b5a7e2207baeae3990d04f5cb35c499156f9c2cbf1c996b6587cefc64` |
| `docs/plans/2026-08-24-conformance-cut-10-results.md` | `83fa5f7cb0ea0abaf82db765162792b2862d6cd9e0feec1eabe2aaaac85d224b` |

K1 succeeds H4u1 with the current `_publish` body and co-cites
`test_publication_failure_after_an_established_outcome_raises`. Cut 16 is run,
not cited: all 27 of its pinned arms remain exact and sound.

## 2. What ran

All commands ran from `python/`. The runner used its default work root
`../.cut17-acceptance`, placed XDG cache state inside the disposable run, set
`SCIENCE_CUT4_ROOT` through `SCIENCE_CUT17_ROOT`, and named no prefix runner.

`uv run --frozen python tools/cut17_acceptance.py`

```text
[cut17 phase 1/19] test_n2_cut6.py — 23 passed
[cut17 phase 2/19] test_n2_cut7.py — 42 passed
[cut17 phase 3/19] test_n2_cut9.py — 23 passed
[cut17 phase 4/19] test_intent_boundary_acceptance.py — 18 passed
[cut17 phase 5/19] test_n2_cut11.py — 17 passed
[cut17 phase 6/19] test_successor_admission_acceptance.py — 4 passed
[cut17 phase 7/19] test_n2_cut12.py — 16 passed
[cut17 phase 8/19] test_confinement_acceptance.py — 15 passed
[cut17 phase 9/19] test_n2_cut13.py — 16 passed
[cut17 phase 10/19] test_coordination_acceptance.py — 22 passed
[cut17 phase 11/19] test_n2_cut14.py — 7 passed
[cut17 phase 12/19] test_cut15_lineage.py — 5 passed
[cut17 phase 13/19] test_n2_cut15.py — 8 passed
[cut17 phase 14/19] test_relocation_acceptance.py — 16 passed
[cut17 phase 15/19] test_n2_cut16.py — 7 passed
[cut17 phase 16/19] test_permit_acceptance.py — 8 passed
[cut17 phase 17/19] test_permit_boundary.py — 18 passed
[cut17 phase 18/19] test_permit_entry_points.py — 93 passed
[cut17 phase 19/19] test_n2_cut17.py — 8 passed
declared arms: 24 (= 8 selected + 1 labeled units)
```

The phase summaries total **366 passed, 0 failed**; the runner exited 0. The
declaration, audit, and runner are committed at `c367070`.

### 2.1 Certified host facts

- backend `linux`, revision `linux-4`; storage profile
  `flush-honoring-disk.v1`;
- kernel `7.2.2-arch1-1`;
- ext4 normalized options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`,
  `ro_compat=0x46b`; and
- certification record
  `atoms/docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json` at
  Atoms commit `0b382a9` (an ancestor of the loaded checkout).

The confinement prerequisite returned no refusal. Any durability or
confinement mismatch would have ended the runner with exit 2, never a skip.

### 2.2 Repository gates

- the complete serial Python suite passed after the implementation tasks;
- `uv run --frozen ruff check --no-cache src tests tools` — all checks passed;
- `uv run --frozen pyright` — 0 errors, 0 warnings, 0 informations;
- the 24-arm cut-17 N2 audit passed; and
- `tasks check` reported zero errors and warnings before this discharge.

## 3. Implementation commits

| commit | subject |
|---|---|
| `cc5cf1b` | feat(permit): closed act families, KIND_ACTS, WritePermit and Authority |
| `6f2ed21` | feat(permit): add required capabilities and coverage |
| `0e4d1a3` | docs(plans): apply the pre-flight rulings to the write-permits plan |
| `b7451c9` | feat(permit): bind Authority at the corpus writer, the port and open_corpus |
| `dfe5677` | feat(permit): require permits on writer families and relocation seams |
| `acf8798` | feat(permit): judge import bundles member by member before the intent |
| `8937b01` | feat(permit): run boundary requires the run permit and refuses without an intent |
| `67750d6` | feat(permit): holdings acts require the holdings permit on the bound context |
| `4626335` | feat(permit): world binds an authority; registry and epoch acts require it |
| `a1f7408` | feat(permit): root lifecycle acts require the lifecycle permit |
| `238695b` | test(permit): hold the write entry points closed statically (E6) |
| `44d3a3d` | test(permit): E1 over every inventoried entry point |
| `4ab62ea` | test(permit): durable acceptance arms for E1, E2, E7 and E8 |
| `c367070` | test(cut17): declare the N2 arms, the audit, and the acceptance runner |

The design and amendment commits precede this range. This results record is
committed with the discharge change and therefore does not yet name that
commit; the follow-up pin does.

## 4. Remaining boundary

No E-table work remains. `write-permits` leaves the live ledger and unblocks
the command framework's writer session and dispatcher. The newest unrelated
open mutation clauses remain W16, C3, R23, M3, and T2 under their existing
owners; this cut neither selects nor changes them. No new boundary is created
by this discharge.
