# Current-state evidence — 2026-08-28

**Purpose:** the verification the curation design's §3 rule 1 and §7 step 1
require (`../superpowers/specs/2026-08-28-current-state-documentation-curation-design.md`).
Every current-state claim the curated surfaces make is listed here with the
ancestry, tree surface, or results record that proves it. The pass ran in a
worktree that is removed on merge; this record is what survives. Claims rule 4
left unproved are listed in §6.

Checked at worktree head `4fb5d72` on branch `docs/current-state-curation`,
four commits ahead of `main` at `1f39b0d`.

## 1. Commit claims (ancestry)

Each row was checked with `git merge-base --is-ancestor <commit> HEAD`.

| claim | commit | result |
|---|---|---|
| cut 2 slice merged | `e4d7186` (merge `cut-2-slice`) | ancestor |
| cut 3 slice merged | `4933d92` (merge `run-boundary`) | ancestor |
| composition-root adapter banked | `2140805` | ancestor |
| world-index slice 1 merged | `567ebb4` | ancestor |
| world-index slice 2 (cut 7) merged | `83744e7` | ancestor |
| log verification (cut 8) merged `--no-ff` | `10cc84b` | ancestor |
| root lifecycle (cut 9) merged `--no-ff` | `7a9fec8` | ancestor |
| holdings (cut 10) merged `--no-ff` | `35be6ff` | ancestor |
| intent boundary (cut 11) discharged at | `806444e` | ancestor |
| intent boundary merged `--no-ff` | `1f39b0d` | ancestor |

## 2. Implementation claims (tree surfaces)

Every surface below exists under `python/src/science/`.

| capability | surface |
|---|---|
| typed claim construction, projection, identity, decode | `claim.py`, `projection.py`, `identity/`, `decode.py` |
| admission state, assessment admission gate, belief | `admission.py`, `belief.py`, `policy.py` |
| spec freezing, closure, production, replay, verification, reports | `spec.py`, `closure.py`, `production.py`, `replay.py`, `verification.py`, `verify.py`, `report.py` |
| composition root, durable adapter, write boundary | `adapter.py`, `boundary.py`, `stored.py` |
| world root, registry, lifecycle, epochs | `root.py`, `world/` |
| verified holdings | `holdings/` |
| general intent qualification | `intents/` |

The certified acceptance runners `python/tools/cut4_acceptance.py` through
`cut11_acceptance.py` all exist.

## 3. Discharge claims (results records)

| cut | results record |
|---|---|
| 4 | `2026-08-18-conformance-cut-4-results.md` |
| 5 | `2026-08-19-conformance-cut-5-results.md` |
| 6 | `2026-08-20-conformance-cut-6-results.md` |
| 7 | `2026-08-20-conformance-cut-7-results.md` |
| 8 | `2026-08-22-conformance-cut-8-results.md` |
| 9 | `2026-08-23-conformance-cut-9-results.md` |
| 10 | `2026-08-24-conformance-cut-10-results.md` |
| 11 | `2026-08-27-conformance-cut-11-results.md` |

Cuts 1–3 predate the results-record convention; their landing is proved by
§1's ancestry rows and §2's surfaces, and their selection by the frozen cut
documents under `docs/designs/`.

## 4. Remaining-boundary claims

| boundary | proof it is still open |
|---|---|
| G4 — successor admission | cut 11 results §5; the ledger's dated row-5 correction of 2026-08-28 under §1 |
| event-level L8 | cut 11 results §5; the same ledger note |
| L13 preimage resolver | cut 11 results §5; the same ledger note; tamper-evident-log design §5.3 |
| first full contract cut, executable suite, N1–N10 | ledger §1 row 7, state column: "the first contract cut, the executable suite, and N1–N10 await implementation" |

## 5. Header claims corrected

| header | claim | why false | proof |
|---|---|---|---|
| act-report design | "Nothing here is implemented, and no conformance arm is claimed" | the report layer and completion reading run | `report.py`; cut 3 merge `4933d92`; cut 11 results §1.1 |
| verified-holdings-record design | same wording | verified holdings are a governed stored kind with acts | `holdings/`; cut 10 results |
| contributor-guide design | "Approved for implementation" | the guide exists and is maintained | `docs/guide/` |
| conformance cut 4 | header records the freeze only | the cut was discharged | `2026-08-18-conformance-cut-4-results.md` |

## 6. Unproved (rule 4)

None. Every claim checked above was proved; no surface text was left unchanged
for want of evidence.

## 7. Gates

Run at `90fc4c9`, the last content commit of the pass:

- `python/tools/check_guide.py`: no errors.
- `pytest tests/test_designs_corpus.py tests/test_check_guide.py`:
  `21 passed in 0.74s` — including the new
  `test_the_ledger_summary_names_the_newest_remaining_boundary`, which was
  watched failing (`the ledger has no `Current state` section`) at `a139f82`
  before the summary landed at `5714ebd`.
- `git diff --check main..HEAD`: clean.
- `git diff main..HEAD --name-only -- docs/plans docs/designs`: this record
  (new); the adoption ledger (pure insertion, no removed line); the act-report,
  verified-holdings-record and contributor-guide design headers; and
  `2026-08-17-conformance-cut-4.md`, changed in its status header only — one
  line removed, two added, body byte-identical. No frozen cut body, plan,
  execution ledger or results record changed.
- Superseded-phrase sweep over README, the guide and the corrected headers:
  the only hits are the two original "Nothing here is implemented" sentences,
  which rule 2 keeps and which now each carry a dated superseded line beneath.
- Roadmap-language sweep: no hit in any curated surface; the one pre-existing
  heading `### Measurements constrain the next slice` in
  `docs/guide/contracts-and-adoption.md` is about measurement discipline, not
  an ordering over remaining work, and was left alone.
- Glossary: no definition found stale; untouched, per the design's §4.3.
