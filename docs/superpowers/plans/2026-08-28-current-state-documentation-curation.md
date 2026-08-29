# Current-state documentation curation — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each kind of current-state fact one owner — the adoption ledger's new `Current state` summary for what is built and what remains, `open-questions.md` for what is undecided — and turn every other live surface into a link to it, with one guard that keeps the summary honest.

**Architecture:** Documentation-only. One new test in `python/tests/test_designs_corpus.py` binds the ledger summary to the newest results record's `Remaining boundary` section. One new section in the ledger. README, the six guide pages, and four design headers are edited to project or link rather than restate. Frozen cut bodies, plans, execution ledgers and results records are never touched. An evidence record under `docs/plans/` proves every claim the summary makes.

**Tech Stack:** Markdown; Python 3 + pytest (run via `uv run` from `python/`); `python/tools/check_guide.py`.

**Spec:** `docs/superpowers/specs/2026-08-28-current-state-documentation-curation-design.md` — read it first. The plan argues from it; §3's five rules govern every edit.

## Global Constraints

- Work in this worktree, on branch `docs/current-state-curation`. Every path below is relative to the worktree root.
- Rule 1: a commit claim requires ancestry (`git merge-base --is-ancestor <sha> HEAD`); an implementation claim requires a named tree surface; a discharge claim requires its results record.
- Rule 2: never edit a frozen cut body, a plan, an execution ledger, or a results record. Cut 4's *status header* is the sole permitted cut edit.
- Rule 3: no design header gains an enumeration of what landed. Only the four corrections in Task 8 are allowed.
- Rule 4: a claim you cannot prove stays unchanged and is recorded as unproved in the evidence record.
- Rule 5: no "next", "priority", "first", "should" over remaining work anywhere in a live surface.
- The ledger summary heading must begin with the exact words `Current state`, followed by the refresh date in parentheses — the guard finds it by prefix. Its GitHub anchor is `#current-state-2026-08-28`; every link to it uses that slug.
- Every changed guide page gets `updated: 2026-08-28` and a `sources:` list containing only files the page body or its References still name.
- Commits use conventional-commit style with **no** AI-attribution trailer or footer.
- Pytest: `addopts` already sets `-q`. Run tests as `cd python && set -o pipefail && uv run pytest tests/<file> | tail -3` so the summary line and the real exit code both survive.

---

### Task 1: The evidence record

**Files:**
- Create: `docs/plans/2026-08-28-current-state-evidence.md`

**Interfaces:**
- Produces: the evidence rows every later task's claims cite. Task 9 appends the final gate results to this file.

- [ ] **Step 1: Run the ancestry and surface checks**

```bash
cd /mnt/ssd/Dropbox/science/.worktrees/current-state-curation
for c in e4d7186 4933d92 2140805 567ebb4 83744e7 10cc84b 7a9fec8 35be6ff 806444e 1f39b0d; do
  printf "%s " $c; git merge-base --is-ancestor $c HEAD && echo ancestor || echo NOT-ANCESTOR
done
ls docs/plans/*-conformance-cut-*-results.md
ls python/src/science/{claim,projection,identity,decode,admission,belief,policy,spec,closure,production,replay,verification,report,adapter,boundary,root,stored,intents,world,holdings}* 2>&1
ls python/tools/cut*_acceptance.py
grep -n 'the first contract cut, the executable suite, and N1–N10 await implementation' docs/designs/2026-08-03-redesign-adoption-ledger.md | cut -c1-60
sed -n 176,182p docs/plans/2026-08-27-conformance-cut-11-results.md
```

Expected: every listed commit prints `ancestor` (all ten were checked while writing this plan); results records for cuts 4–11 exist; every source module and `cut4`–`cut11` acceptance runner exists; the ledger row-7 phrase is found; cut 11 §5 names G4, event-level L8 and the L13 preimage resolver. If any check differs, that claim is *unproved* — record it as such in step 2 and do not assert it in later tasks.

- [ ] **Step 2: Write the evidence record**

```markdown
# Current-state evidence — 2026-08-28

**Purpose:** the verification the curation design's §3 rule 1 and §7 step 1
require. Every current-state claim the curated surfaces make is listed here
with the ancestry, tree surface, or results record that proves it. The pass
ran in a worktree that is removed on merge; this record is what survives.
Claims rule 4 left unproved are listed last.

Checked at worktree head `<sha of HEAD at the time>` on branch
`docs/current-state-curation`, three commits ahead of `main` at `5699c62`.

## 1. Commit claims (ancestry)

| claim | commit | `git merge-base --is-ancestor` |
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

| capability | surface |
|---|---|
| typed claim construction, projection, identity, decode | `python/src/science/claim.py`, `projection.py`, `identity/`, `decode.py` |
| admission state, assessment admission gate, belief | `python/src/science/admission.py`, `belief.py`, `policy.py` |
| spec freezing, closure, production, replay, verification, reports | `python/src/science/spec.py`, `closure.py`, `production.py`, `replay.py`, `verification.py`, `verify.py`, `report.py` |
| composition root, durable adapter, write boundary | `python/src/science/adapter.py`, `boundary.py`, `stored.py` |
| world root, registry, lifecycle, epochs | `python/src/science/root.py`, `world/` |
| verified holdings | `python/src/science/holdings/` |
| general intent qualification | `python/src/science/intents/` |

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
| G4 — successor admission | cut 11 results §5; ledger §1 dated note of 2026-08-28 under row 5 |
| event-level L8 | cut 11 results §5; same ledger note |
| L13 preimage resolver | cut 11 results §5; same ledger note; tamper-evident-log design §5.3 |
| first full contract cut, executable suite, N1–N10 | ledger §1 row 7, state column: "the first contract cut, the executable suite, and N1–N10 await implementation" |

## 5. Header claims corrected

| header | claim | why false | proof |
|---|---|---|---|
| act-report design | "Nothing here is implemented, and no conformance arm is claimed" | the report layer and completion reading run | `python/src/science/report.py`; cut 3 merge `4933d92`; cut 11 results §1.1 |
| verified-holdings-record design | same wording | verified holdings are a governed stored kind with acts | `python/src/science/holdings/`; cut 10 results |
| contributor-guide design | "Approved for implementation" | the guide exists and is maintained | `docs/guide/` |
| conformance cut 4 | header records freeze only | the cut was discharged | `docs/plans/2026-08-18-conformance-cut-4-results.md` |

## 6. Unproved (rule 4)

_None at the time of writing. Add a row here for any claim a later task could
not prove, and leave that claim's surface text unchanged._

## 7. Gates

_Filled in by the final task._
```

Replace `<sha of HEAD at the time>` with `git rev-parse --short HEAD`. If step 1 failed any check, move that row to §6 with the failing output.

- [ ] **Step 3: Commit**

```bash
git add docs/plans/2026-08-28-current-state-evidence.md
git commit -m "docs(plans): record the current-state evidence for the curation pass"
```

---

### Task 2: The agreement guard, failing

**Files:**
- Modify: `python/tests/test_designs_corpus.py` (constants after `_ROW_RANGE` at line 105; new test after `test_every_cross_reference_resolves`)

**Interfaces:**
- Produces: `PLANS`, `_RESULTS_RECORD`, `_PROSE_LABEL`, `_H2`, `_h2_section(text, prefix) -> str | None`, and `test_the_ledger_summary_names_the_newest_remaining_boundary`. Task 3 makes it pass.

- [ ] **Step 1: Add the constants and section helper**

Insert after the `_ROW_RANGE` definition:

```python
PLANS = ROOT / "docs" / "plans"

#: A discharge results record, keyed by the cut number in its name.
_RESULTS_RECORD = re.compile(r"\A\d{4}-\d\d-\d\d-conformance-cut-(\d+)-results\.md\Z")

#: A guarantee-row label as prose names it — `G4`, `L13`, `S1a` — with no table
#: cell around it. `_ROW` anchors on `| **G4** |` and finds nothing in a prose
#: paragraph, which is why this exists separately.
_PROSE_LABEL = re.compile(r"\b([GSWRCXNLDMPHT][0-9]+[a-z]?)\b")

#: A level-two heading with its optional `N.` numbering stripped.
_H2 = re.compile(r"^## (?:\d+\.\s+)?(.*)$")


def _h2_section(text: str, prefix: str) -> str | None:
    """The body under the first `##` heading whose title starts with `prefix`.

    Runs to the next `##` heading. None when no heading matches, so a caller
    can fail on the heading's absence rather than on an empty body.
    """
    body: list[str] | None = None
    for line in text.splitlines():
        heading = _H2.match(line)
        if heading:
            if body is not None:
                break
            if heading.group(1).startswith(prefix):
                body = []
            continue
        if body is not None:
            body.append(line)
    return None if body is None else "\n".join(body)
```

- [ ] **Step 2: Add the failing test**

Append after `test_every_cross_reference_resolves`:

```python
def test_the_ledger_summary_names_the_newest_remaining_boundary() -> None:
    """A cut lands, names its remainder, and the summary is never updated.

    That is the one disagreement that actually happened, and the only one this
    guard reads for: the newest results record's `Remaining boundary` section
    constrains what the ledger's `Current state` section must name, never what
    else it may say.

    Both reads fail closed. The heading is a convention this guard establishes
    (cut 11 is the first record to carry it), so its absence is a failure, and
    an empty label collection is a failure — a guard asserting over the empty
    set would pass on exactly the drift it exists to catch.
    """
    records = {
        int(m.group(1)): path
        for path in PLANS.glob("*.md")
        if (m := _RESULTS_RECORD.match(path.name))
    }
    assert records, f"no conformance-cut results record under {PLANS}"
    cut, newest = max(records.items())

    remaining = _h2_section(_text(newest), "Remaining boundary")
    assert remaining is not None, f"{newest.name} has no `Remaining boundary` section"
    labels = set(_PROSE_LABEL.findall(remaining))
    assert labels, f"{newest.name}'s Remaining boundary names no guarantee row"

    ledger = _text(DESIGNS / "2026-08-03-redesign-adoption-ledger.md")
    summary = _h2_section(ledger, "Current state")
    assert summary is not None, "the ledger has no `Current state` section"
    assert f"cut {cut}" in summary, f"the ledger's Current state does not name cut {cut}"
    missing = sorted(labels - set(_PROSE_LABEL.findall(summary)))
    assert not missing, (
        f"the ledger's Current state does not name {', '.join(missing)}, "
        f"which {newest.name} leaves open"
    )
```

- [ ] **Step 3: Run it and watch it fail on the missing section**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py -k newest_remaining_boundary | tail -5
```

Expected: `1 failed` with `AssertionError: the ledger has no `Current state` section`. Any other failure means the helper or constants are wrong — fix before continuing.

- [ ] **Step 4: Commit the failing guard**

```bash
git add python/tests/test_designs_corpus.py
git commit -m "test(docs): bind the ledger summary to the newest cut's remaining boundary"
```

---

### Task 3: The ledger's `Current state` summary

**Files:**
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` — insert a new `##` section between the end of §0 (the paragraph ending "…decomposition rulings that follow from it.", currently line 39) and `## 1. Unbuilt artifacts and what waits on them` (line 41)

**Interfaces:**
- Produces: the anchor `#current-state-2026-08-28` that Tasks 4–7 link to.

- [ ] **Step 1: Insert the section**

Between §0's last paragraph and the `## 1.` heading, insert exactly:

```markdown
## Current state (2026-08-28)

This section is the one place that states what is built and what remains to
build. Every other live surface — the README and the contributor guide — links
here rather than restating it. It lists no unresolved design question:
`../guide/open-questions.md` owns those. Nothing below orders the remaining
work.

**Implemented through conformance cut 11.** Every cut from 4 onward has a
discharge results record under `../plans/`; cuts 1–3 are proved by their merge
ancestry and the surfaces they built
(`../plans/2026-08-28-current-state-evidence.md`).

- **Typed claims, admission and belief computation** — claim construction,
  canonical projection and identity, cross-language decode parity, the derived
  admission state, the assessment admission gate, the belief-input closure
  digest, and `science.belief.v1` under an exact binding (cuts 1–2).
- **Run closure, execution, replay, reports and qualification** — spec
  freezing and closure construction, the execution boundary through the minimal
  Snakemake adapter, dataset production, replay, verification-as-value, the
  act-report layer's completion reading, and general intent qualification with
  durable run publication (cuts 3 and 11).
- **Certified persistence and the mutation families** — the composition root
  over the certified `atoms` engine, the add-only write boundary and read
  capability boundary, and supersede, revise, retraction and explicit import
  through it (cuts 4–5).
- **World registry, epochs, anchoring, lifecycle and verified holdings** — the
  authoritative world root, corpus manifests and corpus-state identity, the
  append-only registry with lifecycle status and presence, epoch publication
  with its derived maps and receipts, mutation-log anchor carriage and
  verification, the root lifecycle and store substrate, and store-side verified
  holdings with their intent-bearing acts (cuts 6–10).

**Remaining implementation boundaries with named owners.** One row per
boundary: what it is, who owns it, and what it blocks. Row order carries no
priority. A boundary enters this table only when §1's rows prove it still open;
unresolved design areas are not boundaries and are not listed.

| boundary | owner | what it blocks |
|---|---|---|
| **G4** — successor admission | the successor-admission slice; `2026-08-26-world-index-intent-boundary-design.md` §5 carries the transferred design and its opening obligations | the fourth of kernel §8.7's recorded-mutation consequences; rows 5 and 7 reading G4 in full |
| **Event-level L8** — the presence/exclusion relation across captured corpus heads | the tamper-evident-log design's own successor work (row 5) | row 5 reading L8 in full |
| **L13 preimage resolver** — preimage-backed classification of a removed verification | the named `atoms` blob-read seam (`2026-08-03-tamper-evident-log-design.md` §5.3) | row 5 reading L13 in full; until then the held-copy match is a path match |
| **The first full contract cut, its executable suite, and N1–N10** | sub-problem 5b (row 7) | the normative contract's own guarantees; disposition of the legacy check modules |

Detailed state, with every dated correction, stays in §1's rows and §3's order
of work. The newest results record
(`../plans/2026-08-27-conformance-cut-11-results.md` §5) names this table's
first three rows, and `test_the_ledger_summary_names_the_newest_remaining_boundary`
holds this section to whichever record is newest.
```

- [ ] **Step 2: Run the guard and the corpus tests**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -3
```

Expected: all pass, including the new guard. If `test_every_cross_reference_resolves` complains about `../plans/2026-08-28-current-state-evidence.md`, Task 1 was not committed — it must exist.

- [ ] **Step 3: Confirm nothing else in the ledger moved**

```bash
git diff --stat docs/designs/2026-08-03-redesign-adoption-ledger.md
git diff docs/designs/2026-08-03-redesign-adoption-ledger.md | grep -E '^[-+]' | grep -v '^+++\|^---' | grep '^-'
```

Expected: the second command prints nothing — the change is pure insertion.

- [ ] **Step 4: Commit**

```bash
git add docs/designs/2026-08-03-redesign-adoption-ledger.md
git commit -m "docs(ledger): add the current-state summary the guard reads"
```

---

### Task 4: README `Status` becomes a projection

**Files:**
- Modify: `README.md` lines 69–182 (from `## Status` through the cut 11 paragraph ending "…it has not been pushed."). The fenced directory block that follows stays.

- [ ] **Step 1: Replace the Status section body**

Replace everything from the line after `## Status` up to (not including) the blank line before the ```` ``` ```` directory block with:

```markdown
Every conformance cut through **cut 11** is implemented and discharged. What
runs today: typed claims, admission and belief computation; run closure,
execution, replay, act reports and general intent qualification; certified
persistence through the composition root, with the supersede, revise,
retraction and import families; and the world registry with epochs,
mutation-log anchoring and verification, root lifecycle, and verified
store-side holdings. The latest discharged boundary is cut 11, general intent
qualification ([results](docs/plans/2026-08-27-conformance-cut-11-results.md)).

The guarantee tables are the acceptance criteria — each row must be a failing
test before it is a passing one. There are **151 rows** across **thirteen frozen
tables** (G, S, W, R, C, X, N, L, D, M, P, H, T), and every cut is frozen
*before* its code exists so that a row which fails is a failure rather than a
redefinition.

What is built and what remains to build, each remainder with its named owner,
is stated once, in the
[adoption ledger's current-state summary](docs/designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28).
The per-cut results records under [`docs/plans/`](docs/plans/) are the
evidence trail, and unresolved design questions live in the guide's
[open questions](docs/guide/open-questions.md).
```

- [ ] **Step 2: Check the pinned phrases and the tests**

```bash
grep -c '151 rows' README.md; grep -c 'thirteen frozen' README.md
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -3
```

Expected: both counts `1`; all tests pass.

- [ ] **Step 3: Confirm no chronology survives outside the design catalog**

```bash
sed -n '/^## Status/,$p' README.md | grep -n -i -E 'cut [0-9]+|landed|froze|merged|Design complete'
```

Expected: only the two `cut 11` mentions in the first paragraph.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(readme): project the status section onto the ledger summary"
```

---

### Task 5: Guide index, foundations, identity, contracts

**Files:**
- Modify: `docs/guide/README.md` (front matter `updated`; `## Status and authority` first paragraph)
- Modify: `docs/guide/foundations.md` (front matter; `## Current state`)
- Modify: `docs/guide/identity-world-and-change.md` (front matter; `## Current state`)
- Modify: `docs/guide/contracts-and-adoption.md` (front matter; `## Current state`; `## Open edges`; `## References`)

**Interfaces:**
- Consumes: the ledger anchor `#current-state-2026-08-28`.
- Produces: `contracts-and-adoption.md` now cites the four designs Task 7 removes from `open-questions.md`.

- [ ] **Step 1: `docs/guide/README.md`**

Set `updated: 2026-08-28`. Replace the first paragraph under `## Status and authority` (from "The guide deliberately does not copy…" through "…the source wins.") with:

```markdown
The guide deliberately does not copy a changing implementation tally. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28)
is the sole authority for what is built and what remains to build, each
remainder with its named owner; the consolidated
[open questions](open-questions.md) page is the sole authority for what is
undecided. Each topic page below states only the facts specific to its topic
and links to those two for the rest. If this guide disagrees with a source
design, the source wins.
```

Leave the second paragraph (the two undesigned sub-problems) and `## Maintaining the guide` unchanged.

- [ ] **Step 2: `docs/guide/foundations.md`**

Set `updated: 2026-08-28`. Replace the whole `## Current state` body (from "The adoption ledger records eleven implemented slices." through "…closed with cut 10.") with:

```markdown
The kernel's typed records, admission and belief computation run: claim
construction and identity, the derived admission state, the assessment
admission gate, and `science.belief.v1` under an exact binding. Kernel §8.7's
recorded-mutation consequences close through the mutation log's anchor carriage
and verification, except G4, whose successor admission remains open under a
named owner. The agentic surface and salvage — the two sub-problems with no
design — remain that way. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28)
is the complete statement of what is built and what remains.
```

Reduce `sources:` to the files the body and References still draw on:

```yaml
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-11-act-report-design.md
```

(The dropped cut-6/10/11 designs, the three world-index designs and the three results records were cited only by the removed chronology; `identity-world-and-change.md` and `contracts-and-adoption.md` still cite every one of those designs, so `test_the_guide_cites_every_design` holds.)

- [ ] **Step 3: `docs/guide/identity-world-and-change.md`**

Set `updated: 2026-08-28`. Replace the whole `## Current state` body (from "The authoritative world root, manifest…" through "…storage duplication changes no address.") with:

```markdown
The world side runs end to end at the registry level: the authoritative world
root, corpus manifests and corpus-state identity, and the append-only registry
with lifecycle status and configured presence; epoch publication with its four
derived maps, fixture-bound receipts, bounded reads and whole-epoch GC; the
mutation log's anchor carriage and its verification — the log-head record and
head artifact, the explicit anchor act, the four-outcome evaluator, replay with
its removal policy pass, the audit and replica-arrival boundaries, the
genesis↔mirror agreement check, and the ordered-cuts predicate; the root
lifecycle and store substrate — the fail-closed writer state, the lifecycle
commands, `restore_root`, the fork acts with act-derived `forked_from`, and
genesis-bound store subjects; and verified store-side holdings with their
intent-bearing acts. Global resolution remains designed, and the address ruling
still governs the eventual derived views: labels are computed on read,
coreference is graded rather than merged, and storage duplication changes no
address. What the log still owes — G4's successor admission, event-level L8,
and the L13 preimage resolver — is listed with its owners in the
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28).
```

In `sources:`, remove the five `../plans/*-results.md` entries (the body no longer links them) and keep every design entry — the cut documents froze the guarantees this paragraph says are implemented.

- [ ] **Step 4: `docs/guide/contracts-and-adoption.md`**

Set `updated: 2026-08-28`. Replace the `## Current state` body from "Cuts 1–11 have implemented…" through "…into a status report." (keep the "The contributor guide has no ledger artifact…" paragraph) with:

```markdown
Eleven conformance cuts have been frozen and discharged, each frozen before its
code existed and each from cut 4 onward discharged on the certified tuple with
a results record under `../plans/`. The cut discipline is what this page owns:
a cut selects rows, the acceptance runner arms each selected unit with an exact
sabotage mutation, and a discharge is a results record, never a re-reading of
the frozen text. The complete normative contract cut, its executable suite and
N1–N10 are not yet implemented. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28)
states what is built and which remaining boundaries have named owners; the cut
documents and results records in the references below are the evidence.
```

Replace the `## Open edges` body with:

```markdown
See [Contracts and adoption](open-questions.md#contracts-and-adoption) for
contract governance, the normative artifact's shape, certifying instruments that
already exist, and the residues the verified-holdings record and the act-report
design deliberately left open. The writer model sits with the other authority
questions under
[Identity, world, and change](open-questions.md#identity-world-and-change).
```

Append to `## References`, after the existing seven items:

```markdown
- [Conformance cut 4 — the first persistence slice](../designs/2026-08-17-conformance-cut-4.md)
- [Composition-root adapter design](../designs/2026-08-18-composition-root-adapter-design.md)
- [Conformance cut 5 — the family adapters](../designs/2026-08-19-conformance-cut-5.md)
- [Family adapters design](../designs/2026-08-19-family-adapters-design.md)
- [Cut 11 discharge results, the newest results record](../plans/2026-08-27-conformance-cut-11-results.md)
```

Add to `sources:` (keep the existing entries; remove `../plans/2026-08-24-conformance-cut-10-results.md`, which nothing on the page links any more):

```yaml
  - ../designs/2026-08-17-conformance-cut-4.md
  - ../designs/2026-08-18-composition-root-adapter-design.md
  - ../designs/2026-08-19-conformance-cut-5.md
  - ../designs/2026-08-19-family-adapters-design.md
```

- [ ] **Step 5: Run the guide gates**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -3
```

Expected: `check_guide.py` prints no errors; all tests pass. `test_the_guide_cites_every_design` will still pass at this point because `open-questions.md` has not yet been pruned; Task 7 is where the carried citations matter.

- [ ] **Step 6: Commit**

```bash
git add docs/guide/README.md docs/guide/foundations.md docs/guide/identity-world-and-change.md docs/guide/contracts-and-adoption.md
git commit -m "docs(guide): project the foundations, identity and contracts state onto the ledger summary"
```

---

### Task 6: The two cut-1-frozen pages

**Files:**
- Modify: `docs/guide/claims-and-belief.md` (front matter; `## Current state`)
- Modify: `docs/guide/computation-and-reproducibility.md` (front matter; `## Current state`)

- [ ] **Step 1: `docs/guide/claims-and-belief.md`**

Set `updated: 2026-08-28`. Replace the `## Current state` body (from "Typed claim construction, profile compilation…" through "…not conformance oracles.") with:

```markdown
Typed claim construction, profile compilation, canonical projection, identity,
decode, and Python/TypeScript parity are implemented. So is the belief seam:
the derived admission state, the assessment admission gate, the belief-input
closure digest, and `science.belief.v1` computed under an exact binding, with
the belief policy's P1–P9 and the admission ramp's G9 in cut 2's selection.
Verified holdings are a governed stored kind — recorded per location by
intent-bearing acts and projected under a declared coverage — so an
observation's admission input is a system record rather than a supplied
argument. The survey and typing exercise remain hand-run measurements, not
conformance oracles. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28)
states what remains.
```

Add to `sources:`:

```yaml
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-09-conformance-cut-2.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-24-world-index-holdings-design.md
```

- [ ] **Step 2: `docs/guide/computation-and-reproducibility.md`**

Set `updated: 2026-08-28`. Replace the `## Current state` body (from "The run model, verification scopes…" through "…or assessment admission.") with:

```markdown
The run boundary is implemented: analysis-spec freezing and closure
construction, the execution boundary through the minimal Snakemake adapter,
dataset production, replay, verification-as-value, and the act-report layer's
completion reading, running as real subprocess executions over held fixtures.
Runs publish durably with their closure preimage and typed identity bridge, and
general intent qualification reads every boundary operation through one
three-shape reducer. Assessment admission is gated on the verification reading
rather than on a claim that code ran. What is not built here is owned
elsewhere — the mutation log's event-level order (L8) and the preimage-backed
classification of a removed verification (L13) — and listed with those owners
in the
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28).
```

Add to `sources:`:

```yaml
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-11-conformance-cut-3.md
  - ../designs/2026-08-26-world-index-intent-boundary-design.md
  - ../designs/2026-08-27-conformance-cut-11.md
```

- [ ] **Step 3: Confirm the cut-1-scoped phrases are gone and the gates pass**

```bash
grep -rn -E 'outside that cut|current conformance cut' docs/guide README.md
cd python && set -o pipefail && uv run python tools/check_guide.py && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -3
```

Expected: the grep prints nothing; gates pass.

- [ ] **Step 4: Commit**

```bash
git add docs/guide/claims-and-belief.md docs/guide/computation-and-reproducibility.md
git commit -m "docs(guide): refresh the two current-state sections frozen at cut 1"
```

---

### Task 7: Prune `open-questions.md` to design questions

**Files:**
- Modify: `docs/guide/open-questions.md` (front matter `sources`; the `## Contracts and adoption` section)

**Interfaces:**
- Consumes: Task 5 carried the four displaced citations into `contracts-and-adoption.md`; this task may now remove them here.

- [ ] **Step 1: Remove the implementation-inventory bullet**

Delete the entire bullet beginning `- **Cut 10 is discharged; part of cut 3's deferred boundary stays open.**` through its closing citation list ending `[conformance cut 11](../designs/2026-08-27-conformance-cut-11.md))`. Nothing in it is an undecided design question: "whether as one cut or two" was settled by cuts 4 and 5 having been drawn, and every other sentence is cut history or implementation remainder the ledger summary now owns.

- [ ] **Step 2: Trim the implementation note from the act-report bullet**

In `- **The act-report's residue.**`, delete the sentence beginning "Science-side anchor carriage and a durable-log consumer are **no longer among them**" through "…with cut 8 on 2026-08-23." The four open things stay; where carriage and the consumer landed is ledger material.

- [ ] **Step 3: Rebuild `sources:` from what the body links**

```bash
grep -o '](\.\./[a-z]*/[^)#]*' docs/guide/open-questions.md | sed 's/](//' | sort -u
```

Set `sources:` to exactly that list (it will include `../designs/2026-08-08-world-address-ruling.md`, which the current front matter omits although the body links it four times, and will no longer include the four displaced designs, the cut 2/3/6/7/8/9/10/11 documents, or any results record). Set `updated: 2026-08-28`.

- [ ] **Step 4: Confirm every anchor and every design citation survives**

```bash
grep -n '^## ' docs/guide/open-questions.md
cd python && set -o pipefail && uv run python tools/check_guide.py && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -3
```

Expected: the five section headings (`Foundations`, `Claims and belief`, `Identity, world, and change`, `Computation and reproducibility`, `Contracts and adoption`) are unchanged; `check_guide.py` is silent; `test_the_guide_cites_every_design` passes — if it names any of the four displaced designs, Task 5 step 4 was not applied.

- [ ] **Step 5: Commit**

```bash
git add docs/guide/open-questions.md
git commit -m "docs(guide): keep open-questions to design questions"
```

---

### Task 8: The four header corrections

**Files:**
- Modify: `docs/designs/2026-08-11-act-report-design.md:3`
- Modify: `docs/designs/2026-08-10-verified-holdings-record-design.md:4-7`
- Modify: `docs/designs/2026-08-08-contributor-guide-design.md:4`
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md:3-4`

Rule 3 governs: append, never rewrite, and never enumerate what landed. The contributor-guide and cut 4 headers are the two in-place lifecycle corrections §4.4 allows.

- [ ] **Step 1: act-report design**

After line 3 (the `**Status:**` line), insert a blank line and then:

```markdown
**Superseded 2026-08-28.** The sentence above claiming nothing is implemented
no longer holds. This header records design facts only; what has been built is
stated in the adoption ledger's current-state summary
(`2026-08-03-redesign-adoption-ledger.md`).
```

- [ ] **Step 2: verified-holdings-record design**

After the `**Status:**` paragraph (it ends at the line "the persistence seam (§7)." — line 7), before `**Inherits:**`, insert:

```markdown
**Superseded 2026-08-28.** The claim above that nothing here is implemented no
longer holds. This header records design facts only; what has been built is
stated in the adoption ledger's current-state summary
(`2026-08-03-redesign-adoption-ledger.md`).
```

- [ ] **Step 3: contributor-guide design**

Replace line 4 `**Status:** Approved for implementation` with:

```markdown
**Status:** Approved 2026-08-08; implemented as `docs/guide/` and maintained
under §6's rule.
```

- [ ] **Step 4: conformance cut 4**

Replace lines 3–4:

```markdown
**Status:** Frozen 2026-08-18 — the composition-root adapter design banked
after §7's independent second reading.
```

with:

```markdown
**Status:** Frozen 2026-08-18 — the composition-root adapter design banked
after §7's independent second reading. Discharged 2026-08-18 on the certified
volume (`../plans/2026-08-18-conformance-cut-4-results.md`).
```

- [ ] **Step 5: Confirm the cut-4 body is byte-identical below the header**

```bash
git diff docs/designs/2026-08-17-conformance-cut-4.md | grep -E '^[-+]' | grep -v -E '^(\+\+\+|---)'
```

Expected: exactly the two removed and three added header lines; nothing else.

- [ ] **Step 6: Run the corpus tests and commit**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -3
cd .. && git add docs/designs/2026-08-11-act-report-design.md docs/designs/2026-08-10-verified-holdings-record-design.md docs/designs/2026-08-08-contributor-guide-design.md docs/designs/2026-08-17-conformance-cut-4.md
git commit -m "docs(designs): correct the four stale headers rule 3 allows"
```

---

### Task 9: Final gates and frozen-history review

**Files:**
- Modify: `docs/plans/2026-08-28-current-state-evidence.md` (§7)

- [ ] **Step 1: Superseded-phrase sweep**

```bash
grep -rn -E 'outside that cut|current conformance cut|Nothing here is implemented|Design complete|Approved for implementation' README.md docs/guide docs/designs/2026-08-11-act-report-design.md docs/designs/2026-08-10-verified-holdings-record-design.md docs/designs/2026-08-08-contributor-guide-design.md
grep -n -i -E '\bcut [0-9]+\b' docs/guide/*.md | grep -v -E 'open-questions.md|/References|\]\(\.\./'
```

Expected: the first grep hits only the two original `Nothing here is implemented` sentences (rule 2 keeps them; each now has its superseded line beneath). The second prints only the topic pages' own `cut 2`/`cut 11` mentions inside their current-state paragraphs and nothing in a chronology form ("froze", "landed", "merged", "discharged … on"). Fix any stray chronology sentence and re-run.

- [ ] **Step 2: No roadmap language**

```bash
grep -n -i -E '\b(next slice|next cut|priority|should be (built|done) (first|next)|first (build|implement))\b' README.md docs/guide/*.md docs/designs/2026-08-03-redesign-adoption-ledger.md | grep -v 'open-questions.md'
```

Expected: nothing from the new summary or the projections. (Pre-existing ledger prose elsewhere is out of scope; note any hit in the evidence record rather than editing it.)

- [ ] **Step 3: Full gates**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -3
cd .. && git diff --check main..HEAD
```

Expected: `check_guide.py` silent; the pytest summary line shows every test passed and `0 failed`; `git diff --check` prints nothing.

- [ ] **Step 4: Frozen-history diff review**

```bash
git diff --stat main..HEAD
git diff main..HEAD --name-only -- docs/plans docs/designs
```

Expected `docs/plans`: only `2026-08-28-current-state-evidence.md` (new). Expected `docs/designs`: only the ledger, the act-report, verified-holdings-record and contributor-guide designs, and `2026-08-17-conformance-cut-4.md` — and for cut 4 only its status header (Task 8 step 5). Anything else under those two directories is a rule 2 violation: revert it.

- [ ] **Step 5: Record the gate results and commit**

Replace §7 of `docs/plans/2026-08-28-current-state-evidence.md` with the real output:

```markdown
## 7. Gates

Run at `<git rev-parse --short HEAD>`:

- `python/tools/check_guide.py`: no errors.
- `pytest tests/test_designs_corpus.py tests/test_check_guide.py`: `<the summary line verbatim>`.
- `git diff --check main..HEAD`: clean.
- `git diff main..HEAD --name-only -- docs/plans docs/designs`: `<the list verbatim>`; cut 4 changed in its status header only.
- Superseded-phrase sweep: `<hits, or "no live hits">`.
```

```bash
git add docs/plans/2026-08-28-current-state-evidence.md
git commit -m "docs(plans): record the curation pass's gate results"
```

- [ ] **Step 6: Correct the spec's status in the same delivery**

Per the design-doc rule, the spec's `**Status:**` line goes stale the moment this lands. Edit `docs/superpowers/specs/2026-08-28-current-state-documentation-curation-design.md` line 4 to:

```markdown
**Status:** approved in session; revised 2026-08-28 after written-spec review;
delivered 2026-08-28 on `docs/current-state-curation` (evidence at
`docs/plans/2026-08-28-current-state-evidence.md`)
```

```bash
git add docs/superpowers/specs/2026-08-28-current-state-documentation-curation-design.md
git commit -m "docs(specs): mark the curation design delivered"
```

The branch is then ready for the human-owned `--no-ff` merge into `main`. The roadmap session starts from the merged ledger summary's table and is not part of this plan.
