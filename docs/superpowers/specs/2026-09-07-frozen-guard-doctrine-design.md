# Frozen guard doctrine — live machinery and cited evidence

**Date:** 2026-09-07
**Subject:** what a conformance guard's `FROZEN_*` pin table claims, and what happens
when the tree falsifies one
**Measured against:** `main` at `9031c9b` — 18 guard modules, 144 pins, 14 live, 4 cited
not run, 3 falsified pins
**Enforced by:** `python/tests/frozen_guards.py`, `python/tests/cited_not_run.py` and
`python/tests/test_frozen_guards.py`, in the portable suite

This is method, not a boundary: it closes no guarantee row, adds no row to the adoption
ledger, and changes no ranking. It rules one question the corpus has answered
inconsistently three times.

## 1. The question, and the three answers already given

Every cut leaves a guard module, `tests/acceptance/test_n2_cutN.py`, carrying `FROZEN_*`
tables that pin prior-cut files — by commit ("this file has not changed since") or by
content ("these exact bytes"). The rule when a cut's source legitimately moves is **fix
the arm, never the source**, so an arm declaration file moves and every table pinning it
is falsified at once. The verification-publication slice moved `n2_arms_cut3.py` and
`n2_arms_cut5.py` at `1e92471` and falsified thirteen tables.

The corpus then answered the same question three different ways within one slice:

- **Task 1** reverted a fix-round edit to `tests/acceptance/test_n2_cut5.py`, ruling that
  "editing frozen evidence to satisfy a run no gate performs is exactly what the freeze
  rule forbids".
- **The fix wave** edited that same module anyway (`205e5f7`, finding C1) and re-minted
  cut 14's content pin over it (`da6bab8`) — leaving the code disagreeing with cut 14's
  own frozen results record, which still published the original hash.
- **Ruling P9** left cuts 7–13 unrepaired and named cut 10 "structurally blocked",
  because repairing its table would break cut 17's content pin over it.

Two readers in a row — the fix wave's I1 triage, and the session that opened this
document — then read a cited-not-run guard's red as a live regression. The rule below is
what makes those the same answer every time.

## 2. Two standings

A guard module is **live** or **cited, not run**. Which one it is decides what its pin
table means.

**Live** — reachable from the newest cut's runner, transitively through `PREFIX_RUNNERS`
and `PHASE_MODULES`. Its pin tables are **machinery**: they exist to track the tree, and
they must hold against it today. When the tree legitimately moves a pinned file, every
live table is re-pinned in the same commit that moves it, and each affected cut record
gains a dated citation amendment. The precedent is `74a5938`.

**Cited, not run** — a later cut has ruled that the module is no longer run, naming why
and what carries its coverage now. Its bytes are **evidence**: the module is what
produced the discharge that later cuts cite in place of running it, which is why the
citing cut usually pins the whole surface by content. Its pin tables are historical
statements about the tree it discharged on. They are **never edited, never re-pinned**,
and a pin inside one that the tree has since falsified is a stated consequence of the
freeze — not a defect, and never a regression.

The newest runner defines *live* whether or not its cut is discharged: a cut being
prepared has already re-rooted or extended the chain, and a guard it drops leaves the
live set when the runner says so. Older runners are not a second opinion. They are the
frozen commands of the trees they discharged on (write-permits design §13.2), so
`cut13_acceptance.py` still naming `cut5_acceptance.py` does not make cut 5 live.

## 3. Why a cited-not-run guard is not re-pinned

Re-pinning it would be the cheap fix, and it is wrong twice over.

It asserts something false about the past. A guard re-pinned to today's commit claims the
cut audited files that did not exist when it ran. The discharge being cited was produced
by the bytes as they stood; a table pointing anywhere else describes a run that never
happened.

And it destroys what the citation rests on. Cut 16 bought byte-identity deliberately —
"the whole cut-10 surface — its design, its declaration file, its acceptance module and
its runner — is left byte-identical and pinned so by cut 16's checks; cut 10 is **cited,
not run**" (write-permits design §13.1) — precisely so a reader can tell that the record
they are citing is the record that was made. Editing the module to repair its table would
break cut 17's `FROZEN_CUT10_SHA256` and, with it, the guarantee the repair was meant to
serve.

`74a5938` is not a precedent against this. The 2026-09-05 history rewrite changed commit
*addresses* while the evidence bytes were identical, so re-citing each orphaned id
restored the pin's truth. Here the pinned file's content genuinely changed. Re-citation
restores a true claim; re-pinning would mint a false one.

## 4. How standing changes, and how the tree is held to it

A module leaves the live set **by ruling** — named in the citing cut's design or results
record, with the reason and the successor certification — never by quietly falling out of
an inventory. Cut 4's guard shows the failure mode: it is in no runner's inventory and no
document names its drop, so nobody can say what its red means.

`python/tests/cited_not_run.py` is the registry: per module, the cut, the ruling, the
discharge that stands, what carries the coverage now, and every pin the tree has since
falsified with the commit that did it. `python/tests/test_frozen_guards.py` holds four
things true, in the portable suite rather than beside the guards — `addopts` ignores
`tests/acceptance`, so a check placed there would run only during a discharge, which is
how five broken live pins survived a whole slice unreported:

1. every guard module is live or declared, never both and never neither;
2. every pin in a live guard holds today;
3. every pin the registry records as falsified really is falsified;
4. every registry entry names documents that exist.

`tests/acceptance/conftest.py` refuses to collect a declared module and writes the ruling
and the standing record to the terminal. It refuses rather than skips: that file's own
rule is that a skip reports green for a guarantee that was not exercised, and it holds
here.

## 5. The 2026-09-07 restoration — dated citation amendment

`205e5f7`'s edit to `python/tests/acceptance/test_n2_cut5.py` is reverted, and cut 14's
`FROZEN_CUT5_SHA256` entry for that module is restored from `f744c34d…` to
`df589285dd377709c322a2a3958196f3e8a8c65032af8d79863b548584e41798`.

Cut 5's guard is cited, not run: "Cut 14 cites cut 5 … it does not invoke cut 5 or an
aggregate runner" (cut 14 results §3), and `pyproject.toml` excludes it from pyright for
the same reason. `df589285…` is the hash cut 14's own results record §3 published and
still publishes; the slice's re-mint had left the code disagreeing with the discharge
record it was pinning. The restoration makes the bytes, the live pin and the frozen
record say the same thing again, and it restores Task 1's ruling, which was right.

No frozen results record is edited by this amendment. The three pins the tree has
falsified — `n2_arms_cut5.py` in cuts 8 and 10, `test_n2_cut6.py` in cut 8 — are recorded
in the registry and left exactly as they are.

## 6. What this does not rule

- **Scalar ancestry pins** (`CUT17_FREEZE_COMMIT` and its siblings) are outside the
  tables this covers; `beliefs-faf658` owns them.
- **Arm staleness** — a sabotage whose `before` block no longer matches — is a different
  failure from a falsified pin, is not detected here, and is `beliefs-ee11e2`'s.
- **Whether a cut should be cited rather than run** stays the citing cut's own ruling.
  This document says only how that ruling is recorded and what follows from it.
