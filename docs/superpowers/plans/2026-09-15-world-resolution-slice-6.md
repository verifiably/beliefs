# World Resolution Slice 6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `consolidate` reconciles two `source` replicas whose identifier-correction histories diverged, absorbing the other replica's unheld events into one consolidation entry so no event or retired address is lost, idempotently over a re-run after interruption — discharged as conformance cut 30.

**Architecture:** One facet, one new entry kind: a *consolidation entry* (`from == to`, plus `absorbed`, a nested chain) in `identifier-correction`. `stored.py` reads and validates the recursive shape through the one validator; a pure `stored.reconcile_correction_histories` computes the merged chain; `relocation.consolidate` validates the rationale, computes the merge with the intent's token, and hands the entries to `_reconcile`. Cut 25's frozen `W5a-m` arm (the refusal this retires) is re-targeted by the live guard, never edited.

**Tech Stack:** Python 3.11+, `uv run --frozen pytest` from `python/`, ruff, pyright; the repository's N2 arm apparatus (`n2_arms.py`, `arm_staleness.py`, `acceptance_runner.py`).

**Spec:** `docs/superpowers/specs/2026-09-15-world-resolution-slice-6-design.md` (read it first; section numbers below are its).

## Global Constraints

- Run every Python command from `python/` with the project venv: `uv run --frozen pytest …`, `uv run --frozen ruff check .`, `uv run --frozen pyright`. Never the system python.
- Never run the full suite after every edit (about 18 min). `just test-fast` while working; the pre-push hook runs `just gate`.
- **No frozen text moves** (spec decision 8): `            if keep_map != other_map:` in `relocation.py` (cut 28 `W8-b`), `        if frm == to:` and `    if list(node.deprecated_ids) != expected:` in `stored.py` (cut 25 `W5a-l`, `W5a-k`), and every `n2_arms_cut*.py` body stay byte-identical. `tests/acceptance/test_n2_cut25.py` re-targets `W5a-m` in its live table; guards 26–29 learn the second re-targeted row.
- Every write path stays behind the one validator: nothing re-derives a §3.2 clause.
- Commit messages: conventional commits, no attribution trailer.
- Task records: `tasks start <id>` before a task, `tasks done <id> "<what landed>"` in the commit that lands it, `tasks check` before every commit. Never edit `tasks/*.md` by hand.
- Paths in this plan are repository-relative; the worktree is `.worktrees/world-resolution-slice-6` on branch `design/world-resolution-slice-6`.

---

## File structure

| file | responsibility in this slice |
|---|---|
| `docs/designs/2026-09-15-conformance-cut-30.md` | the frozen cut: boundary, selection, accounting, obligations (Task 1) |
| `python/src/beliefs/stored.py` | `IdentifierCorrection.absorbed`; `_read_chain` (the recursive reader); `held_source_addresses` recursion; `reconcile_correction_histories` (Tasks 2–3) |
| `python/src/beliefs/relocation.py` | `consolidate`: rationale validation, early intent, the merge call; `_reconcile(correction_entries=)` (Task 4) |
| `python/src/beliefs/errors.py` | `HistoryDisagreement` docstring (Task 4) |
| `python/src/beliefs/corpus.py` | `_refuse_source` docstring (Task 4) |
| `python/tests/test_source_address.py` | reader/validator tests; `TestReconcile` (Tasks 2–3) |
| `python/tests/test_identifier_correction.py` | `TestRelocation` amended; `TestTheBoundary` import cases (Task 4) |
| `python/tests/acceptance/test_source_address_acceptance.py` | lifecycle absorb + readback; interruption re-run (Task 5) |
| `python/tests/acceptance/test_n2_cut25.py`, `test_n2_cut26.py` … `test_n2_cut29.py` | the `W5a-m` live re-target and the guards' knowledge of it (Task 6) |
| `python/tests/acceptance/n2_arms_cut30.py`, `test_n2_cut30.py`, `python/tools/cut30_acceptance.py` | declaration, guard, runner (Task 7) |
| `python/tools/roadmap_status.py`, `README.md`, ledger, roadmap, guide, results record, dated notes | discharge and navigation (Tasks 1, 8) |

---

### Task 1: Freeze conformance cut 30

**Files:**
- Create: `docs/designs/2026-09-15-conformance-cut-30.md`
- Modify: `README.md:30` (design count sentence), `README.md:99` (design table — add a row after cut 29's), `docs/guide/contracts-and-adoption.md:44` and `docs/guide/identity-world-and-change.md:25` (citation lists — add the cut 30 line after the cut 29 line), `python/tests/test_designs_corpus.py:301` (`_COUNT_WORDS` gains `65`)
- Test: `python/tests/test_designs_corpus.py` (existing guards)

**Interfaces:**
- Produces: the frozen document whose §§2–7 Task 7's guard pins by SHA-256 and freeze commit; the cut number every later task uses (30).

- [ ] **Step 1: Claim the cut number under concurrency rule 1 — scan every worktree**

```bash
cd /mnt/ssd/Dropbox/beliefs
for w in $(git worktree list --porcelain | sed -n 's/^worktree //p'); do
  git -C "$w" ls-files docs/designs | grep -o 'conformance-cut-[0-9]*' ; done | sort -t- -k3 -n | uniq | tail -1
```
Expected: `conformance-cut-29`. If any worktree shows a higher number, this cut takes the next one after it and every `30` below becomes that number (`beliefs-705507` in `.worktrees/estimand-typing` claims its number at its own freeze; it has not frozen). Record the observed answer in the task: `tasks note beliefs-24b42b "cut number scan 2026-09-15: highest claimed across worktrees is <n>; this cut is <n+1>"`.

- [ ] **Step 2: Write the frozen cut document**

Write `docs/designs/2026-09-15-conformance-cut-30.md` exactly as follows (the commit hash in "measured against" is `git -C .worktrees/world-resolution-slice-6 rev-parse --short HEAD` at the time of writing):

````markdown
# Conformance cut 30 — reconciling divergent correction histories at `consolidate`

**Status:** frozen 2026-09-15, before implementation; not yet discharged.
**Frozen:** 2026-09-15, before implementation, on `design/world-resolution-slice-6`
**Design:** `../superpowers/specs/2026-09-15-world-resolution-slice-6-design.md`, approved 2026-09-15 after two reviews (§11 there)
**Numbered after** cut 29 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The baseline below describes `main` at `6f08418` before implementation.

Slice 2b gave a `source` record a linear, attributed correction history and
made `consolidate` refuse two replicas whose histories differ
(`HistoryDisagreement`, 2b §7): a chain cannot hold two branches, and keeping
the survivor's chain would drop the addresses the other replica held. The
refusal has no operator escape — any further correction widens the
difference — and the families design's recovery contract ("re-run
`consolidate`") could not be met for a `source` once histories diverged.

This cut adds one entry kind to the same facet — a *consolidation entry*,
`from == to`, carrying `absorbed`: the other replica's unheld events as a
nested chain — and a pure reconciliation (`stored.reconcile_correction_histories`)
that fast-forwards a prefix, absorbs a divergent tail, and is the identity
over its own result, so an interrupted run re-runs to completion. One token
is one event: it may recur across chains only as the same entry. Identifier
maps that differ still refuse, naming the schemes; the rationale is validated
before reconciliation on every path.

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-15-conformance-cut-30.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/stored.py`: `IdentifierCorrection.absorbed`, the recursive reader, `held_source_addresses` over absorbed chains, `reconcile_correction_histories`;
- `python/src/beliefs/relocation.py`: `consolidate`'s rationale validation, early intent, reconciliation call; `_reconcile`'s `correction_entries`;
- `python/src/beliefs/errors.py` and `corpus.py`: docstrings only;
- `python/tests/test_source_address.py`, `python/tests/test_identifier_correction.py`: the unit obligations of design §7.1;
- `python/tests/acceptance/test_source_address_acceptance.py`: the lifecycle absorb and the interruption re-run (design §7.2);
- `python/tests/acceptance/test_n2_cut25.py`: the dated `W5a-m` live re-target; `test_n2_cut26.py`–`test_n2_cut29.py`: the second re-targeted row in their prior-declaration checks; `python/tests/arm_staleness.py`: `re_targeted_rows` reads a guard's `RETARGETED_ROWS`;
- `python/tests/acceptance/n2_arms_cut30.py`, `python/tests/acceptance/test_n2_cut30.py`, `python/tools/cut30_acceptance.py`: declaration, guard, runner;
- `python/tools/roadmap_status.py`: the cut 30 accounting entry;
- `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` (§7, §12 item 2) and `docs/designs/2026-08-02-world-addressing-design.md` (W5a's consolidation clause): dated notes;
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/glossary.md`, `README.md` and the cut 30 results record: discharge and navigation.

Out of scope:

- identifier-map merging: `consolidate` refuses differing maps (design decision 1);
- releasing a blocked address (2b §13 item 1);
- `report.py`: `Consolidated` is unchanged (design decision 7);
- `correct_identifier`'s append rule and every other mutation family: unchanged;
- the mm30 reproduction record: no source is consolidated there; no new measurement.

## 3. Selection

No guarantee row is read. `W5a` closed at cut 25 and stays closed; its consolidation arm (`W5a-m`, "consolidation refuses divergent correction histories") is retired by design decision 5 and re-targeted live to its successor, `W5a-p` here (design §7.5). `W8` stays partial on its ambiguous-search-term conflict (cut 28, unchanged); its map-conflict arm (`W8-b`) is untouched.

### Boundary invariants
The `W8-b` anchor `            if keep_map != other_map:` and the `W5a-l` / `W5a-k` anchors `        if frm == to:` and `    if list(node.deprecated_ids) != expected:` are byte-unchanged; no `n2_arms_cut*.py` body is edited; no referrer is rewritten; no address is released; `move`, `delete`, `supersede`, `revise` are unchanged for `source`.

## 4. Accounting

Zero guarantee rows are read, **0 full/closed** newly, and **1 declaration unit** carries the arms: `W5a`, re-read on its reconciliation arms. `world-resolution` then retains no filed follow-up and leaves the ledger's `Current state` table and the roadmap's boundary index at discharge.

## 5. N2 and acceptance obligations

Declared in `python/tests/acceptance/n2_arms_cut30.py` (design §7.3): `W5a-p` (divergent histories absorbed, not dropped), `W5a-q` (the absorbed chain is validated), `W5a-r` (held addresses reach into absorbed chains), `W5a-s` (one token is one event across chains), `W5a-t` (a consolidation entry changes nothing), `W5a-u` (the entry carries the operation's token), `W5a-v` (a prefix fast-forwards without an entry), `W5a-x` (an already-held event is not absorbed again), `W5a-y` (conflicting reuse refuses before any intent), `W5a-z` (the rationale is validated before reconciliation on every path). Each is a byte-exact sabotage on a line this cut writes, audited by `arm_staleness` against the tree. Acceptance: design §7.2. Runner: `python/tools/cut30_acceptance.py`, `PREFIX_RUNNERS = ("cut29_acceptance.py",)`, phase modules `test_source_address_acceptance.py` and `test_n2_cut30.py`.

## 6. Discharge

On the certified volume beside the checkout, `just check`, `just test` and the runner all exit 0; the results record `../plans/2026-09-15-conformance-cut-30-results.md` retains the transcripts and digests; the branch merges `--no-ff`.

## 7. Limitations

Design §10: reconciliation is by `keep`; conflicting token reuse refuses with no seam to repair it; a blocked address is still not released; map merge is not offered; the absorbed fork point is provenance, not a clause.
````

- [ ] **Step 3: Update the README count and design table, the two guide citation lists, and the count-words table**

`python/tests/test_designs_corpus.py:301`: after `    64: "Sixty-four",` add `    65: "Sixty-five",`.

`README.md:30`: change `Sixty-four documents` to `Sixty-five documents` and the `through 2026-09-14` date (find it: `grep -n "through 2026-09" README.md`) to `through 2026-09-15`. Add after the cut 29 row of the design table (`README.md:99`):

```markdown
| `2026-09-15-conformance-cut-30.md` | the frozen slice 6 cut: divergent correction histories reconciled at `consolidate` by absorption, idempotent over a re-run; no guarantee row read |
```

`docs/guide/contracts-and-adoption.md:44` and `docs/guide/identity-world-and-change.md:25`: add `  - ../designs/2026-09-15-conformance-cut-30.md` on the line after the cut 29 entry.

- [ ] **Step 4: Run the designs-corpus guard**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -q`
Expected: all pass (the count sentence, the table, and `test_the_guide_cites_every_design` read the new file). `_COUNT_WORDS` ends at `64: "Sixty-four",` (`test_designs_corpus.py:301`): add `    65: "Sixty-five",` after it in Step 3, or `test_the_readme_states_how_many_designs_there_are` fails asking for it.

- [ ] **Step 5: Commit the freeze**

```bash
git -C .worktrees/world-resolution-slice-6 add docs/designs/2026-09-15-conformance-cut-30.md README.md docs/guide/contracts-and-adoption.md docs/guide/identity-world-and-change.md python/tests/test_designs_corpus.py
git -C .worktrees/world-resolution-slice-6 commit -m "docs(cut30): freeze conformance cut 30 — divergent correction-history reconciliation"
git -C .worktrees/world-resolution-slice-6 rev-parse HEAD
```
Record the full hash and the frozen digest for Task 7:
```bash
sha256sum .worktrees/world-resolution-slice-6/docs/designs/2026-09-15-conformance-cut-30.md
tasks note beliefs-24b42b "cut 30 frozen at <hash>, sha256 <digest>"
```

---

### Task 2: The recursive reader and validator

**Files:**
- Modify: `python/src/beliefs/stored.py:391–483` (`IdentifierCorrection`, `_CORRECTION_KEYS`, `identifier_corrections`, `held_source_addresses`)
- Test: `python/tests/test_source_address.py::TestReaders`

**Interfaces:**
- Produces: `IdentifierCorrection.absorbed: tuple[IdentifierCorrection, ...] = ()`; `_CONSOLIDATION_KEYS`; `_read_chain(raw_entries, where, seen)`; `identifier_corrections` and `held_source_addresses` over the nested shape. `validate_source_history` is unchanged in text (its line is cut 25's `W5a-k` anchor) and gains the new clauses through the reader.
- The test helper `consolidation(frm, absorbed, *, actor=, grounds=, token=)` in `test_source_address.py`, consumed by Tasks 3–4.

- [ ] **Step 1: Add the fixture helper and the failing reader tests**

In `python/tests/test_source_address.py`, after `def entry(...)` (line 193), add:

```python
def consolidation(frm, absorbed, *, actor="consolidator", grounds="one paper", token="c1"):
    """A consolidation entry (slice 6 §3.1): `from == to`, plus the absorbed chain."""
    return {
        "from": dict(frm),
        "to": dict(frm),
        "actor": actor,
        "grounds": grounds,
        "event_token": token,
        "absorbed": [dict(e) for e in absorbed],
    }


C = {"doi": "10.1234/xyz", "pmid": "1"}
ADDR_C = cast(str, source.source_address(C))
```

Append to `class TestReaders`:

```python
    # --- slice 6 §3: the consolidation entry and the nested chain ---

    def test_a_consolidation_entry_reads_with_its_absorbed_chain(self):
        # keep: A→B (t1); other: A→C→B (o1, o2), absorbed at B.
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        node = raw_source(B, history=history, deprecated=sorted([ADDR_A, ADDR_C]))
        first, merged = stored.identifier_corrections(node)
        assert first.absorbed == ()
        assert merged.from_identifiers == B and merged.to_identifiers == B
        assert (merged.actor, merged.grounds, merged.event_token) == ("consolidator", "one paper", "c1")
        assert [c.event_token for c in merged.absorbed] == ["o1", "o2"]
        assert merged.absorbed[0].from_identifiers == A and merged.absorbed[1].to_identifiers == B
        assert stored.validate_source_history(node) == (first, merged)

    def test_a_nested_consolidation_entry_reads(self):
        inner = consolidation(B, [entry(A, B, token="o1")], token="c1")
        outer = consolidation(B, [entry(C, B, token="p1"), inner], token="c2")
        node = raw_source(B, history=[entry(A, B, token="t1"), outer], deprecated=sorted([ADDR_A, ADDR_C]))
        _, merged = stored.identifier_corrections(node)
        assert merged.absorbed[1].absorbed[0].event_token == "o1"

    def test_held_addresses_reach_into_absorbed_chains_once(self):
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        node = raw_source(B, history=history, deprecated=sorted([ADDR_A, ADDR_C]))
        assert stored.held_source_addresses(stored.identifier_corrections(node)) == {ADDR_A, ADDR_B, ADDR_C}

    @pytest.mark.parametrize(
        "deprecated",
        [sorted([ADDR_A]), sorted([ADDR_A, ADDR_C, "source:" + "f" * 64])],
        ids=["omits-an-absorbed-address", "adds-an-underived-address"],
    )
    def test_validate_source_history_holds_the_redirect_set_to_the_absorbed_chain(self, deprecated):
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(raw_source(B, history=history, deprecated=deprecated))

    def test_an_identical_event_may_recur_across_chains(self):
        # The diamond: `b` reached the survivor through two intermediaries.
        b = entry(A, B, token="b")
        history = [
            entry(A, B, token="a"),
            consolidation(B, [b], token="m1"),
            consolidation(B, [entry(A, B, token="c"), consolidation(B, [dict(b)], token="m2")], token="m3"),
        ]
        node = raw_source(B, history=history, deprecated=[ADDR_A])
        assert len(stored.identifier_corrections(node)) == 3

    @pytest.mark.parametrize(
        "history, match",
        [
            ([dict(entry(A, B, token="t1"), absorbed=[entry(B, A, token="o1")])], "changes nothing"),  # six keys, from != to; absorbed ends at `from`
            ([entry(A, B, token="t1"), consolidation(B, [])], "non-empty list"),  # empty absorbed
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry({"pmid": "9"}, B, token="o2")])], "continue"),  # absorbed not continuous
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1")])], "does not end at the entry"),  # absorbed ends elsewhere
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="t1", grounds="other")])], "two different events"),  # conflicting reuse, spine vs absorbed
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o1")])], "repeats"),  # repeats within the absorbed chain
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1", grounds="\udcff")])], "encodable"),  # non-encodable inside absorbed
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1")], token="t1")], "repeats"),  # the entry's own token repeats the spine's
        ],
        ids=["six-keys-unequal", "empty-absorbed", "absorbed-discontinuous", "absorbed-ends-elsewhere",
             "conflicting-reuse", "repeat-inside-absorbed", "unencodable-inside-absorbed", "entry-token-repeats-spine"],
    )
    def test_malformed_consolidation_shapes_refuse(self, history, match):
        node = raw_source(B, history=history, deprecated=[ADDR_A])
        with pytest.raises(MalformedRecord, match=match):
            stored.identifier_corrections(node)
```

Also add the `six-keys-unequal` case's mirror in `test_malformed_shapes_refuse`'s list, which already refuses `from == to` on five keys (`test_from_equal_to_refuses_and_nothing_else_does` covers it; nothing to add there).

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py::TestReaders -q -k "consolidation or absorbed or identical_event or holds_the_redirect"`
Expected: FAIL — the reader refuses the six-key shape (`keys are exactly …`) and `IdentifierCorrection` has no `absorbed`.

- [ ] **Step 3: Implement the recursive reader**

In `python/src/beliefs/stored.py`, replace the block from `class IdentifierCorrection:` through the end of `held_source_addresses` (lines 391–472; leave `validate_source_history` exactly as it is) with:

```python
@sealed
@final
@dataclass(frozen=True)
class IdentifierCorrection:
    """One attributed entry of a source's identifier-correction history (slice 2b
    §5.2). A consolidation entry (slice 6 §3.1) has `from == to` and a non-empty
    `absorbed` chain — the other replica's events, verbatim; a correction entry
    has `absorbed == ()`."""

    from_identifiers: Mapping[str, str]
    to_identifiers: Mapping[str, str]
    actor: str
    grounds: str
    event_token: str
    absorbed: tuple[IdentifierCorrection, ...] = ()


_CORRECTION_KEYS = frozenset({"from", "to", "actor", "grounds", "event_token"})
_CONSOLIDATION_KEYS = _CORRECTION_KEYS | {"absorbed"}


def _correction_map(raw: object, where: str) -> Mapping[str, str]:
    if not isinstance(raw, dict) or not raw:
        raise MalformedRecord(f"{where}: is not a non-empty mapping")
    try:
        canonical = source_basis_projection.normalized_identifiers(raw)
    except IdentifierMalformed as caught:
        raise MalformedRecord(f"{where}: {caught}") from caught
    if canonical != raw:
        raise MalformedRecord(f"{where}: holds a non-canonical identifier")
    return MappingProxyType(canonical)


def _read_chain(raw_entries: object, where: str, seen: dict[str, dict]) -> tuple[IdentifierCorrection, ...]:
    """One chain (slice 6 §3.2): the spine, or one `absorbed` list. Tokens are
    distinct within the chain; across chains `seen` (token → raw entry) holds
    every occurrence of a token to one event."""
    if not isinstance(raw_entries, list) or not raw_entries:
        raise MalformedRecord(f"{where}: is a non-empty list of entries")
    corrections: list[IdentifierCorrection] = []
    tokens: set[str] = set()
    for index, raw in enumerate(raw_entries):
        here = f"{where} entry {index}"
        if not isinstance(raw, dict) or set(raw) not in (_CORRECTION_KEYS, _CONSOLIDATION_KEYS):
            raise MalformedRecord(
                f"{here}: keys are exactly {sorted(_CORRECTION_KEYS)}, plus `absorbed` on a consolidation entry"
            )
        for key in ("actor", "grounds", "event_token"):
            if not isinstance(raw[key], str) or not raw[key]:
                raise MalformedRecord(f"{here}: {key} is a non-empty string")
        # Maps first, so a null or non-mapping `from`/`to` is this reader's refusal and never an
        # encoding error; then the whole entry under the identity encoding, every refusal of
        # which (NullRefused, LoneSurrogate, ...) is IdentityError and translated here.
        frm = _correction_map(raw["from"], f"{here} from")
        to = _correction_map(raw["to"], f"{here} to")
        try:
            v1.encode(raw)
        except IdentityError as caught:
            raise MalformedRecord(f"{here}: not canonically encodable: {caught}") from caught
        token = raw["event_token"]
        if token in tokens:
            raise MalformedRecord(f"{here}: event token {token!r} repeats")
        tokens.add(token)
        if token in seen and seen[token] != raw:
            raise MalformedRecord(f"{here}: event token {token!r} names two different events")
        seen[token] = raw
        if frm == to:
            if "absorbed" not in raw:
                raise MalformedRecord(f"{here}: from and to are equal; a correction changes something")
        elif "absorbed" in raw:
            raise MalformedRecord(f"{here}: a consolidation entry changes nothing, so from and to are equal")
        if corrections and dict(corrections[-1].to_identifiers) != dict(frm):
            raise MalformedRecord(f"{here}: from does not continue the previous entry's to")
        absorbed: tuple[IdentifierCorrection, ...] = ()
        if "absorbed" in raw:
            absorbed = _read_chain(raw["absorbed"], f"{here} absorbed", seen)
            if dict(absorbed[-1].to_identifiers) != dict(frm):
                raise MalformedRecord(f"{here}: the absorbed chain does not end at the entry's identifiers")
        corrections.append(IdentifierCorrection(frm, to, raw["actor"], raw["grounds"], token, absorbed))
    return tuple(corrections)


def identifier_corrections(node: Node) -> tuple[IdentifierCorrection, ...]:
    """Read history validated to slice 2b §5.2 and slice 6 §3.2, or raise `MalformedRecord`."""
    if IDENTIFIER_CORRECTION_FACET not in node.facets:
        return ()
    facet = node.facets[IDENTIFIER_CORRECTION_FACET]
    if not isinstance(facet, dict) or set(facet) != {"entries"}:
        raise MalformedRecord(
            f"{node.id}: identifier-correction is a mapping holding a non-empty `entries` list"
        )
    corrections = _read_chain(facet["entries"], f"{node.id}: identifier-correction", {})
    if dict(corrections[-1].to_identifiers) != dict(_source_identifiers(node)):
        raise MalformedRecord(f"{node.id}: the last correction does not end at the current identifiers")
    return corrections


def held_source_addresses(history: Sequence[IdentifierCorrection]) -> frozenset[str]:
    """Every address derivable from any map in the history, absorbed chains included."""
    addresses: set[str] = set()
    for correction in history:
        for mapping in (correction.from_identifiers, correction.to_identifiers):
            address = source_basis_projection.source_address(mapping)
            assert address is not None  # a validated map is non-empty
            addresses.add(address)
        addresses |= held_source_addresses(correction.absorbed)
    return frozenset(addresses)
```

The `        if frm == to:` line (8 spaces, then the keyword) is cut 25's `W5a-l` anchor: it must occur exactly once in `stored.py` as that substring, which it does at its 8-space indentation inside the loop. Verify: `grep -c '^        if frm == to:$' python/src/beliefs/stored.py` prints `1`.

- [ ] **Step 4: Run the reader tests and the cut 25 guard's static checks**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py tests/test_identifier_correction.py::TestTheReadSide -q`
Expected: all pass, including every pre-existing case (`test_malformed_shapes_refuse`, `test_from_equal_to_refuses_and_nothing_else_does`).

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut25.py -q -k "sabotage_names_one_real_source_site or inventory or lettered"`
Expected: pass — every cut 25 anchor in `stored.py` still matches once.

- [ ] **Step 5: Lint and type-check, then commit**

Run: `cd python && uv run --frozen ruff check src/beliefs/stored.py tests/test_source_address.py && uv run --frozen pyright src/beliefs/stored.py`
Expected: clean.

```bash
git -C .worktrees/world-resolution-slice-6 add python/src/beliefs/stored.py python/tests/test_source_address.py
git -C .worktrees/world-resolution-slice-6 commit -m "feat(stored): read and validate consolidation entries with absorbed chains"
```

---

### Task 3: `reconcile_correction_histories`

**Files:**
- Modify: `python/src/beliefs/stored.py` (after `validate_source_history`)
- Test: `python/tests/test_source_address.py::TestReconcile` (new class)

**Interfaces:**
- Consumes: `HistoryDisagreement` from `beliefs.errors` (exists; add to `stored.py`'s errors import).
- Produces: `stored.reconcile_correction_histories(keep: Sequence[dict[str, Any]], other: Sequence[dict[str, Any]], *, actor: str, grounds: str, event_token: str) -> list[dict[str, Any]]` — raw facet entries (the `dict`s the facet holds) in, raw entries out; raises `HistoryDisagreement` on conflicting reuse or interleaving. Pure; deep-copies its inputs into the result. The input type is `dict`, not `Mapping`, so `copy.deepcopy` returns what the annotation promises and pyright is clean.

- [ ] **Step 1: Write the failing table test**

Append to `python/tests/test_source_address.py`:

```python
class TestReconcile:
    """Slice 6 §4: keep's chain is the spine; other's unheld tail is absorbed; idempotent."""

    A_B = entry(A, B, token="a")
    B_ = entry(A, B, token="b")  # other's independent A→B
    E = entry(B, C, token="e1")  # a further correction B→C …
    E_BACK = entry(C, B, token="e2")  # … and back to B

    def merge(self, keep, other, token="op"):
        return stored.reconcile_correction_histories(keep, other, actor="me", grounds="one paper", event_token=token)

    def test_equal_chains_are_the_identity(self):
        assert self.merge([self.A_B], [self.A_B]) == [self.A_B]
        assert self.merge([], []) == []

    def test_a_proper_prefix_fast_forwards_either_way(self):
        longer = [self.A_B, self.E, self.E_BACK]
        assert self.merge([self.A_B], longer) == longer  # keep is the prefix: adopt other
        assert self.merge(longer, [self.A_B]) == longer  # other is the prefix: keep already holds it
        assert self.merge([], longer) == longer
        assert self.merge(longer, []) == longer

    def test_divergent_chains_absorb_the_tail_after_the_common_prefix(self):
        keep = [self.A_B, self.E, self.E_BACK]
        other = [self.A_B, entry(B, C, token="o1"), entry(C, B, token="o2")]
        merged = self.merge(keep, other)
        assert merged[:3] == keep
        assert merged[3] == {
            "from": B, "to": B, "actor": "me", "grounds": "one paper", "event_token": "op",
            "absorbed": other[1:],
        }

    def test_divergent_chains_with_no_common_prefix_absorb_all_of_other(self):
        merged = self.merge([self.A_B], [self.B_])
        assert merged == [self.A_B, {**consolidation(B, [self.B_], actor="me", grounds="one paper", token="op")}]

    def test_an_already_absorbed_chain_is_not_absorbed_again(self):
        once = self.merge([self.A_B], [self.B_])
        assert self.merge(once, [self.B_]) == once  # the interrupted re-run

    def test_a_chain_corrected_after_absorption_absorbs_only_the_new_tail(self):
        once = self.merge([self.A_B], [self.B_])
        other = [self.B_, entry(B, C, token="o1"), entry(C, B, token="o2")]
        merged = self.merge(once, other, token="op2")
        assert merged[:2] == once and merged[2]["absorbed"] == other[1:] and merged[2]["event_token"] == "op2"

    def test_the_diamond_absorbs_an_identical_event_twice(self):
        once = self.merge([self.A_B], [self.B_])  # keep holds b via m
        other = [entry(A, B, token="c"), consolidation(B, [self.B_], token="m2")]  # a third replica also absorbed b
        merged = self.merge(once, other, token="op2")
        assert merged[2]["absorbed"] == other

    def test_conflicting_token_reuse_refuses(self):
        with pytest.raises(HistoryDisagreement, match="two different events"):
            self.merge([self.A_B], [entry(A, B, token="a", grounds="other grounds")])

    def test_held_events_interleaving_unheld_ones_refuse(self):
        once = self.merge([self.A_B], [self.B_])  # keep holds b (A→B, token b)
        # other: x (B→A, unheld), then b (held, verbatim), then y (a consolidation entry at B, unheld)
        other = [entry(B, A, token="x"), self.B_, consolidation(B, [entry(A, B, token="z")], token="y")]
        with pytest.raises(HistoryDisagreement, match="interleave"):
            self.merge(once, other, token="op2")

    @pytest.mark.parametrize(
        "keep, other",
        [
            ([entry(A, B, token="a")], [entry(A, B, token="b")]),
            ([entry(A, B, token="a"), entry(B, C, token="e1"), entry(C, B, token="e2")], [entry(A, B, token="a"), entry(B, C, token="o1"), entry(C, B, token="o2")]),
            ([entry(A, B, token="a")], [entry(A, B, token="a"), entry(B, C, token="e1"), entry(C, B, token="e2")]),
        ],
        ids=["no-prefix", "common-prefix", "fast-forward"],
    )
    def test_reconciliation_is_idempotent(self, keep, other):
        once = self.merge(keep, other)
        assert self.merge(once, other, token="op2") == once

    def test_the_result_aliases_no_input(self):
        keep, other = [entry(A, B, token="a")], [entry(A, B, token="b")]
        merged = self.merge(keep, other)
        merged[1]["absorbed"][0]["grounds"] = "mutated"
        assert other[0]["grounds"] == "checked the PDF"
```

The interleaving fixture is the only shape that puts a held event before an unheld one: `b` (`A→B`) can sit only where the running map is `A`, so `x` must move `B→A` first, and the unheld tail must be a consolidation entry (`B→B` is not a correction).

Add `HistoryDisagreement` to the test module's `beliefs.errors` import.

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py::TestReconcile -q`
Expected: FAIL — `AttributeError: module 'beliefs.stored' has no attribute 'reconcile_correction_histories'`.

- [ ] **Step 3: Implement**

In `python/src/beliefs/stored.py`: add `HistoryDisagreement` to the `from beliefs.errors import …` line (line 62) and `import copy` beside the stdlib imports. After `validate_source_history`, add:

```python
def _events(entries: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """token → raw entry over a chain and, recursively, every absorbed chain (slice 6 §4)."""
    events: dict[str, dict[str, Any]] = {}
    for entry in entries:
        events[entry["event_token"]] = entry
        events.update(_events(entry.get("absorbed", ())))
    return events


def reconcile_correction_histories(
    keep: Sequence[dict[str, Any]],
    other: Sequence[dict[str, Any]],
    *,
    actor: str,
    grounds: str,
    event_token: str,
) -> list[dict[str, Any]]:
    """Slice 6 §4 over two validated chains that end at one map: `keep`'s chain is
    the spine; a prefix fast-forwards; the events of `other` the spine does not
    hold are absorbed, as a tail, into one consolidation entry. Idempotent over
    its own result — the interrupted-run guarantee `consolidate` relies on."""
    held = _events(keep)
    for token, event in _events(other).items():
        if token in held and held[token] != event:
            raise HistoryDisagreement(f"event token {token!r} names two different events")
    if list(keep) == list(other)[: len(keep)]:
        return copy.deepcopy(list(other))
    remainder = [entry for entry in other if entry["event_token"] not in held]
    if not remainder:
        return copy.deepcopy(list(keep))
    if remainder != list(other)[len(other) - len(remainder) :]:
        raise HistoryDisagreement("held events interleave unheld ones; the chain cannot be absorbed")
    current = dict(keep[-1]["to"])
    return [
        *copy.deepcopy(list(keep)),
        {
            "from": current,
            "to": dict(current),
            "actor": actor,
            "grounds": grounds,
            "event_token": event_token,
            "absorbed": copy.deepcopy(remainder),
        },
    ]
```

`keep` is non-empty at the last line: an empty `keep` is a prefix of every `other` and returned earlier.

- [ ] **Step 4: Run, lint, commit**

Run: `cd python && uv run --frozen pytest tests/test_source_address.py -q && uv run --frozen ruff check src/beliefs/stored.py tests/test_source_address.py && uv run --frozen pyright src/beliefs/stored.py`
Expected: all pass, clean.

```bash
git -C .worktrees/world-resolution-slice-6 add python/src/beliefs/stored.py python/tests/test_source_address.py
git -C .worktrees/world-resolution-slice-6 commit -m "feat(stored): reconcile divergent correction histories by absorption"
```

---

### Task 4: `consolidate` reconciles

**Files:**
- Modify: `python/src/beliefs/relocation.py:163–300` (`_reconcile`, `consolidate`), `python/src/beliefs/errors.py:1158–1161`, `python/src/beliefs/corpus.py:3072–3076`
- Test: `python/tests/test_identifier_correction.py::TestRelocation`, `::TestTheBoundary`

**Interfaces:**
- Consumes: `stored.reconcile_correction_histories` (Task 3); `consolidation`, `C`, `ADDR_C` from `test_source_address` (Task 2).
- Produces: `_reconcile(survivor, loser, *, correction_entries: list[dict[str, Any]] | None = None)`; `consolidate` unchanged in signature.

- [ ] **Step 1: Rewrite `test_consolidate_refuses_divergent_histories` and add the relocation tests**

In `python/tests/test_identifier_correction.py`: extend the `test_source_address` import to `from test_source_address import ADDR_A, ADDR_B, ADDR_C, CANONICAL_DOI, A, B, C, consolidation, entry, raw_source`; add `RelocationRefused` to the `beliefs.errors` import; change the module-level `from test_relocation import _writer` to `from test_relocation import _recording_port, _writer`. Replace `test_consolidate_refuses_divergent_histories` (lines 432–440) with:

```python
    def test_consolidate_absorbs_divergent_histories(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer, grounds in ((left, "g-left"), (right, "g-right")):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds=grounds)
        (keep_entry,) = stored.identifier_corrections(left.read_view.get(ADDR_B))
        (other_entry,) = stored.identifier_corrections(right.read_view.get(ADDR_B))
        survivor, keep_report, other_report = consolidate((left, ADDR_B), (right, ADDR_B), rationale="one paper", **REPORT)
        spine, merged = stored.identifier_corrections(survivor)
        assert spine == keep_entry
        assert merged.from_identifiers == B and merged.to_identifiers == B
        assert merged.absorbed == (other_entry,)
        assert (merged.actor, merged.grounds) == (left.authority.actor, "one paper")
        assert merged.event_token == keep_report.event_token == other_report.event_token
        assert survivor.deprecated_ids == [ADDR_A]
        assert left.read_view.resolve(ADDR_A) == ADDR_B
        assert right.read_view.resolve(ADDR_B) is None and right.read_view.resolve(ADDR_A) is None

    def test_swapping_keep_absorbs_the_other_entry(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer, grounds in ((left, "g-left"), (right, "g-right")):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds=grounds)
        (left_entry,) = stored.identifier_corrections(left.read_view.get(ADDR_B))
        survivor, *_ = consolidate((right, ADDR_B), (left, ADDR_B), rationale="one paper", **REPORT)
        spine, merged = stored.identifier_corrections(survivor)
        assert spine.grounds == "g-right" and merged.absorbed == (left_entry,)

    def test_consolidate_fast_forwards_a_prefix(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=B))
        right.import_bundle([minted], **REPORT)  # a copy at B, no history
        right.correct_identifier(ADDR_B, C, grounds="a typo")  # B→C …
        right.correct_identifier(ADDR_C, B, grounds="no, B was right")  # … and back: the round trip
        other = right.read_view.get(ADDR_B)
        assert len(stored.identifier_corrections(other)) == 2
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert stored.identifier_corrections(survivor) == stored.identifier_corrections(other)
        assert all(c.absorbed == () for c in stored.identifier_corrections(survivor))
        assert survivor.deprecated_ids == [ADDR_C]
        assert left.read_view.resolve(ADDR_C) == ADDR_B

    def test_consolidate_of_history_free_replicas_carries_no_facet(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=B))
        right.import_bundle([minted], **REPORT)
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert stored.IDENTIFIER_CORRECTION_FACET not in survivor.facets and survivor.deprecated_ids == []

    def test_correct_identifier_appends_after_a_consolidation_entry(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        further = left.correct_identifier(survivor.id, C, grounds="g2")
        history = stored.identifier_corrections(further)
        assert len(history) == 3 and history[1].absorbed != () and history[2].to_identifiers == C
        assert further.deprecated_ids == sorted([ADDR_A, ADDR_B])

    def test_move_carries_a_nested_history(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        moved, *_ = move(left, right, survivor.id, **REPORT)
        assert stored.identifier_corrections(moved) == stored.identifier_corrections(survivor)
        assert right.read_view.resolve(ADDR_A) == ADDR_B

    def test_consolidate_twice_nests(self, tmp_path):
        left, right, third = (_writer(tmp_path / name) for name in ("left", "right", "third"))
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right, third):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        once, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r1", **REPORT)
        twice, *_ = consolidate((third, ADDR_B), (left, ADDR_B), rationale="r2", **REPORT)
        history = stored.identifier_corrections(twice)
        assert len(history) == 2 and history[1].absorbed == stored.identifier_corrections(once)
        assert history[1].absorbed[1].absorbed != ()
        assert twice.deprecated_ids == [ADDR_A]

    def test_consolidate_retries_after_an_interrupted_replacement(self, two_writers, monkeypatch):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        original = CorpusWriter._delete_locked
        armed = {"once": True}

        def interrupt(self, ref):
            if armed["once"] and self.root == right.root:
                armed["once"] = False
                raise RuntimeError("interrupted after keep's replacement")
            return original(self, ref)

        monkeypatch.setattr(CorpusWriter, "_delete_locked", interrupt)
        with pytest.raises(RuntimeError):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="first", **REPORT)
        first = stored.identifier_corrections(left.read_view.get(ADDR_B))
        assert len(first) == 2 and first[1].grounds == "first"
        assert right.read_view.holds(ADDR_B)  # still a duplicate location
        survivor, keep_report, other_report = consolidate((left, ADDR_B), (right, ADDR_B), rationale="second", **REPORT)
        assert stored.identifier_corrections(survivor) == first  # nothing absorbed twice
        assert first[1].event_token != keep_report.event_token == other_report.event_token
        assert not right.read_view.holds(ADDR_B)

    def test_consolidate_refuses_conflicting_token_reuse(self, two_writers):
        left, right = two_writers
        left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(ADDR_A, B, grounds="g")
        (held,) = stored.identifier_corrections(corrected)
        reused = raw_source(B, history=[entry(A, B, token=held.event_token, grounds="other grounds")], deprecated=[ADDR_A])
        right.import_bundle([reused], **REPORT)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        intents_before = {id(w): list(_recording_port(w).intents) for w in (left, right)}
        with pytest.raises(HistoryDisagreement, match="two different events"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before
        for writer in (left, right):
            assert _recording_port(writer).intents == intents_before[id(writer)]

    @pytest.mark.parametrize("rationale", ["", "\ud800"], ids=["empty", "unencodable"])
    @pytest.mark.parametrize("divergent", [False, True], ids=["identity-path", "absorb-path"])
    def test_consolidate_refuses_a_malformed_rationale_on_both_paths(self, two_writers, rationale, divergent):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        left.add(node.model_copy(deep=True))
        left.correct_identifier(ADDR_A, B, grounds="g")
        if divergent:
            right.add(node.model_copy(deep=True))
            right.correct_identifier(ADDR_A, B, grounds="g2")
        else:
            right.import_bundle([left.read_view.get(ADDR_B)], **REPORT)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        intents_before = {id(w): list(_recording_port(w).intents) for w in (left, right)}
        reports_before = {id(w): sum(n.kind == "act-report" for n in w.read_view.iter_stored()) for w in (left, right)}
        with pytest.raises(RelocationRefused, match="rationale"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale=rationale, **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before
        for writer in (left, right):
            assert _recording_port(writer).intents == intents_before[id(writer)]
            assert sum(n.kind == "act-report" for n in writer.read_view.iter_stored()) == reports_before[id(writer)]
```

Amend `test_divergent_identifier_maps_refuse_consolidation` to assert the message names the scheme:

```python
    def test_divergent_identifier_maps_refuse_consolidation(self, two_writers):
        left, right = two_writers
        left.add(stored.source_node(title="p", identifiers=B))
        right.add(stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        with pytest.raises(HistoryDisagreement, match="isbn"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
```

In `TestTheBoundary`, after `test_import_admits_a_well_formed_history_and_refuses_a_malformed_one`, add:

```python
    def test_import_admits_a_nested_history_and_refuses_a_malformed_nested_one(self, tmp_path):
        from test_relocation import _writer

        from beliefs.errors import ImportRefused

        importer = _writer(tmp_path / "importer")
        good = raw_source(
            B,
            history=[entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])],
            deprecated=sorted([ADDR_A, ADDR_C]),
        )
        importer.import_bundle([good], **REPORT)
        assert importer.read_view.get(ADDR_B).deprecated_ids == sorted([ADDR_A, ADDR_C])
        eight, nine = {"pmid": "8"}, {"pmid": "9"}
        bad = raw_source(
            nine,
            history=[entry(eight, nine, token="t1"), consolidation(nine, [entry(eight, nine, token="o1", grounds="")])],
            deprecated=[source.source_address(eight)],
        )
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle([bad], **REPORT)
        assert caught.value.member == bad.id and "grounds" in str(caught.value)

    def test_add_still_refuses_a_nested_history(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, history=[entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1")])], deprecated=[ADDR_A]))
```

Check `ReadView.holds` and `iter_stored` exist (`grep -n "def holds\|def iter_stored" python/src/beliefs/corpus.py`); both are used by existing tests in this module and `test_relocation.py`.

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py::TestRelocation -q`
Expected: the new tests FAIL with `HistoryDisagreement` from the history-equality refusal; `test_consolidate_refuses_a_malformed_rationale_on_both_paths` fails on the identity path (no refusal today).

- [ ] **Step 3: Implement in `relocation.py`**

Add imports: `from typing import Any`; `from beliefs.errors import IdentityError` (add to the existing `beliefs.errors` import list, alphabetically); `from beliefs.identity import v1`.

Replace `_reconcile` (lines 163–180):

```python
def _reconcile(
    survivor: Node, loser: Node, *, correction_entries: list[dict[str, Any]] | None = None
) -> Node:
    relations: dict[tuple[str, str, str], Relation] = {}
    for relation in (*survivor.relations, *loser.relations):
        relations.setdefault(_relation_key(relation), relation)
    facets = stored.union_lineage_bases(survivor, loser)
    if correction_entries is not None:  # a source: slice 6 §5 step 5
        if correction_entries:
            facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": correction_entries}
        else:
            facets.pop(stored.IDENTIFIER_CORRECTION_FACET, None)
    unstamped = survivor.model_copy(
        update={
            "relations": [relations[key] for key in sorted(relations)],
            "deprecated_ids": sorted(
                {*survivor.deprecated_ids, *loser.deprecated_ids}
            ),
            "facets": facets,
        }
    )
    return (
        stored.stamp_semantic_identity(unstamped)
        if unstamped.kind in stored.SEMANTIC_DOMAINS
        else unstamped
    )
```

In `consolidate`, replace the block from `if keep_node.kind == "source":` through `merged = _reconcile(keep_node, other_node)` (lines 219–244) with — keeping the `            if keep_map != other_map:` line byte-identical:

```python
        if not isinstance(rationale, str) or not rationale:
            raise RelocationRefused("consolidate: rationale is a non-empty, canonically encodable string")
        try:
            v1.encode(rationale)
        except IdentityError as caught:
            raise RelocationRefused(
                "consolidate: rationale is a non-empty, canonically encodable string"
            ) from caught
        # Constructed before the merge so a consolidation entry carries this operation's
        # token; appended to either root only after every preflight below (slice 6 §5).
        intent = OperationIntent("consolidate", secrets.token_hex(16), keep_writer.authority.actor)
        correction_entries: list[dict[str, Any]] | None = None
        if keep_node.kind == "source":
            keep_map = keep_node.facets[stored.SOURCE_FACET]["identifiers"]
            other_map = other_node.facets[stored.SOURCE_FACET]["identifiers"]
            if keep_map != other_map:
                differing = sorted({*keep_map, *other_map} - {s for s in keep_map if other_map.get(s) == keep_map[s]})
                raise HistoryDisagreement(
                    f"{keep_node.id}: the two replicas carry different identifier maps ({', '.join(differing)})"
                )
            correction_entries = stored.reconcile_correction_histories(
                keep_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET, {"entries": []})["entries"],
                other_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET, {"entries": []})["entries"],
                actor=keep_writer.authority.actor,
                grounds=rationale,
                event_token=intent.event_token,
            )
        if keep_node.kind == "dataset":
            for position, node, writer in (
                ("keep", keep_node, keep_writer),
                ("other", other_node, other_writer),
            ):
                address = stored.dataset_address_of(node)
                if node.id != address:
                    raise DatasetAddressDisagreement(
                        f"{node.id}: the {position} replica in {writer.corpus_id} derives {address}; "
                        "consolidate judges both declarations before it discards one"
                    )
        _refuse_contract_disagreement(other_node, other_writer, keep_writer)
        merged = _reconcile(keep_node, other_node, correction_entries=correction_entries)
```

Then delete the later line `intent = OperationIntent("consolidate", secrets.token_hex(16), keep_writer.authority.actor)` (it now sits above). The dataset block's four-line `for position, node, writer in (` text is cut 29's `W8-b` anchor and is copied above unchanged.

`errors.py:1158–1161`, `HistoryDisagreement`'s docstring:

```python
class HistoryDisagreement(RelocationRefused):
    """`consolidate` was given two sources at one address whose identifier maps
    differ (slice 2b §7: an identifier change is a correction's assertion, never
    a side effect of consolidation), or whose correction histories cannot be
    reconciled — one token naming two different events, or a raw-imported chain
    interleaving held and unheld events (slice 6 §4). Divergent histories
    themselves reconcile by absorption since cut 30."""
```

`corpus.py:3072–3076`, `_refuse_source`'s docstring, append one sentence: `A nested (consolidation) history is validated by the same reader (slice 6 §3.2).`

- [ ] **Step 4: Run the module and the neighbours**

Run: `cd python && uv run --frozen pytest tests/test_identifier_correction.py tests/test_relocation.py tests/test_world_conflicts.py tests/test_source_address.py -q`
Expected: all pass. `test_consolidate_validates_both_reports_before_either_intent` still passes: `observer` is validated by `_relocation_report` after the merge, before any intent, as before.

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut28.py tests/acceptance/test_n2_cut29.py -q -k "sabotage_names_one_real_source_site"`
Expected: pass — cut 28's `W8-b` and cut 29's `W8-b` anchors match once.

- [ ] **Step 5: Lint, type-check, commit**

Run: `cd python && uv run --frozen ruff check src tests/test_identifier_correction.py && uv run --frozen pyright src/beliefs/relocation.py src/beliefs/stored.py`

```bash
git -C .worktrees/world-resolution-slice-6 add python/src/beliefs/relocation.py python/src/beliefs/errors.py python/src/beliefs/corpus.py python/tests/test_identifier_correction.py
git -C .worktrees/world-resolution-slice-6 commit -m "feat(relocation): consolidate absorbs divergent correction histories"
```

---

### Task 5: Acceptance — the lifecycle absorb and the interrupted re-run

**Files:**
- Modify: `python/tests/acceptance/test_source_address_acceptance.py:449–481` (`test_lifecycle_move_consolidate_delete`), append one test
- Test: the same module

**Interfaces:**
- Consumes: `world` fixture (two durable `open_corpus` writers and a registry); `publish`, `hold_shipped`, `open_world_view`; `corpus_check` from `beliefs.corpus`; `consolidation` is not needed here.

- [ ] **Step 1: Rewrite the divergent tail of the lifecycle test**

Replace lines 464–478 (from `other = right.add(stored.source_node(title="o", identifiers={"pmid": "6"}))` through the `with pytest.raises(HistoryDisagreement): consolidate(...)` block) with:

```python
    other = right.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    right.correct_identifier(other.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g1")
    twin = left.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    left.correct_identifier(twin.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g2")  # another token: divergent
    divergent = source.source_address({"doi": "10.1234/six"})
    assert divergent is not None
    (left_entry,) = stored.identifier_corrections(left.read_view.get(divergent))
    (right_entry,) = stored.identifier_corrections(right.read_view.get(divergent))
    merged, keep_report, _other_report = consolidate((left, divergent), (right, divergent), rationale="one paper", **REPORT)
    spine, absorbed = stored.identifier_corrections(merged)
    assert spine == left_entry and absorbed.absorbed == (right_entry,) and absorbed.event_token == keep_report.event_token
    assert merged.deprecated_ids == [other.id]
    assert not [finding for finding in corpus_check(left.read_view, BASE) if finding.ref == merged.id]
    assert right.read_view.resolve(divergent) is None
    published = publish(registry, (a, b), hold_shipped(registry))
    view = open_world_view(registry, published)
    assert view.resolve(other.id) == merged.id and view.corpus_of(merged.id) == a
```

Change the test's first line to unpack the registry and ids: `registry, (a, left), (b, right) = world`. Add `from beliefs.corpus import CorpusWriter, corpus_check` (extend the existing import) and `from profiles import BASE` is already imported. Remove `HistoryDisagreement` from this module's `beliefs.errors` import if nothing else in the module uses it (`grep -n HistoryDisagreement`), else leave it.

- [ ] **Step 2: Append the interruption test**

```python
def test_consolidate_interrupted_after_replacement_re_runs_to_completion(world, monkeypatch):
    """Families design, `consolidate` interrupted after step 4: keep holds the reconciled
    survivor, other still holds its replica, and the recovery is to re-run. Slice 6 §5:
    the re-run absorbs nothing twice."""
    registry, (a, left), (b, right) = world
    for writer, grounds in ((left, "g-left"), (right, "g-right")):
        paper = writer.add(stored.source_node(title="p", identifiers={"pmid": "8"}))
        writer.correct_identifier(paper.id, {"doi": "10.1234/eight", "pmid": "8"}, grounds=grounds)
    address = source.source_address({"doi": "10.1234/eight"})
    assert address is not None
    original = CorpusWriter._delete_locked
    armed = {"once": True}

    def interrupt(self, ref):
        if armed["once"] and self.root == right.root:
            armed["once"] = False
            raise RuntimeError("interrupted after keep's replacement")
        return original(self, ref)

    monkeypatch.setattr(CorpusWriter, "_delete_locked", interrupt)
    with pytest.raises(RuntimeError):
        consolidate((left, address), (right, address), rationale="first", **REPORT)
    after_halt = stored.identifier_corrections(left.read_view.get(address))
    assert len(after_halt) == 2 and after_halt[1].absorbed != ()
    assert right.read_view.holds(address)  # the duplicate location the families table names
    for writer in (left, right):
        assert not any(n.kind == "act-report" for n in writer.read_view.iter_stored())  # both intents unfulfilled
    survivor, keep_report, other_report = consolidate((left, address), (right, address), rationale="second", **REPORT)
    assert stored.identifier_corrections(survivor) == after_halt
    assert after_halt[1].event_token != keep_report.event_token == other_report.event_token
    assert not right.read_view.holds(address)
    published = publish(registry, (a, b), hold_shipped(registry))
    assert open_world_view(registry, published).corpus_of(address) == a
```

If the durable writers append the operation intent through a port whose fulfilment can be read more directly (`_recording_port` is the portable recorder, not the durable port), keep the act-report absence assertion as written: an unfulfilled intent has minted no report.

- [ ] **Step 3: Run the module on the certified volume**

The module needs the certified tuple. Run with the roots cut 29's record exports (its §1), substituting `cut30`:

```bash
cd /mnt/ssd/Dropbox/beliefs
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
export SCIENCE_CUT4_ROOT="$MAIN_CHECKOUT/.cut30-acceptance/world-resolution-slice-6"
export SCIENCE_CUT7_ROOT="$SCIENCE_CUT4_ROOT" SCIENCE_CUT10_ROOT="$SCIENCE_CUT4_ROOT" SCIENCE_CUT29_ROOT="$SCIENCE_CUT4_ROOT" SCIENCE_CUT30_ROOT="$SCIENCE_CUT4_ROOT"
mkdir -p .cut30-acceptance
cd .worktrees/world-resolution-slice-6/python && uv run --frozen pytest tests/acceptance/test_source_address_acceptance.py -q
```
Expected: all pass. A `CapabilityUnavailable` failure means the run is not on the certified tuple — fix the environment, never the test (AGENTS.md).

- [ ] **Step 4: Commit**

```bash
git -C .worktrees/world-resolution-slice-6 add python/tests/acceptance/test_source_address_acceptance.py
git -C .worktrees/world-resolution-slice-6 commit -m "test(acceptance): consolidate absorbs divergent histories and re-runs after interruption"
```

---

### Task 6: Frozen evidence — re-target cut 25's `W5a-m` live

**Files:**
- Modify: `python/tests/acceptance/test_n2_cut25.py:40–75`, `test_n2_cut26.py:214`, `test_n2_cut27.py:227`, `test_n2_cut28.py:230`, `test_n2_cut29.py:232`, `python/tests/arm_staleness.py:116–120` (`re_targeted_rows`)
- Test: `python/tests/acceptance/test_n2_cut25.py`, `python/tests/test_arm_staleness.py` (one new test)

**Interfaces:**
- Produces: `test_n2_cut25.RETARGETED_ROWS = frozenset({"W1-a", "W5a-m"})`, imported as `CUT25_RETARGETED_ROWS` by guards 26–30 and read by `arm_staleness.re_targeted_rows` for cut 25.

- [ ] **Step 1: Add the live re-target table to `test_n2_cut25.py`**

After `_LIVE_SABOTAGES` (ends line 54), add:

```python
# Live re-target, 2026-09-15 (slice 6, cut 30): decision 5 there retires the
# history-equality refusal `W5a-m` asserted, so the arm's successor is cut 30's
# `W5a-p` — divergent histories are absorbed, never dropped. The frozen tuple in
# n2_arms_cut25.py is unchanged; this table is what the live guard audits.
_LIVE_ARMS = {
    "W5a-m": Arm(
        row="W5a-m",
        asserts="consolidation absorbs divergent correction histories (re-targeted 2026-09-15; was: refuses)",
        sabotage=Sabotage(
            module="stored.py",
            before="    if not remainder:\n        return copy.deepcopy(list(keep))\n",
            after="    if True:\n        return copy.deepcopy(list(keep))\n",
        ),
        checks=("test_identifier_correction.py::TestRelocation::test_consolidate_absorbs_divergent_histories",),
    )
}
RETARGETED_ROWS = frozenset(_LIVE_SABOTAGES) | frozenset(_LIVE_ARMS)
```

and change the `CUT25_ARMS` comprehension to:

```python
CUT25_ARMS = (
    *(
        _LIVE_ARMS[arm.row]
        if arm.row in _LIVE_ARMS
        else replace(arm, sabotage=_LIVE_SABOTAGES[arm.row])
        if arm.row in _LIVE_SABOTAGES
        else arm
        for arm in FROZEN_CUT25_ARMS
    ),
    Arm(  # the W5a-o supplement, unchanged
```

`Arm` is already imported there (`from n2_arms import Arm, Sabotage`).

- [ ] **Step 2: Teach guards 26–29 the second re-targeted row**

In each of `test_n2_cut26.py:214`, `test_n2_cut27.py:227`, `test_n2_cut28.py:230`, `test_n2_cut29.py:232`, replace

```python
        replace(live, sabotage=frozen.sabotage) if live.row == "W1-a" else live
```
with
```python
        frozen if live.row in CUT25_RETARGETED_ROWS else live  # re-targeted rows: 2026-09-14 W1-a, 2026-09-15 W5a-m
```
and extend each module's `from test_n2_cut25 import CUT25_ARMS` to `from test_n2_cut25 import CUT25_ARMS, RETARGETED_ROWS as CUT25_RETARGETED_ROWS`. Every other row is still held equal to its frozen declaration. Reserve `RETARGETED_ROWS` for a guard's own overrides: importing cut 25's set under that name would make the detector attribute those overrides to the importing guard.

- [ ] **Step 3: Teach the staleness detector the full override set**

`arm_staleness.re_targeted_rows` reads only `_LIVE_SABOTAGES`, so `test_a_live_guard_re_targets_every_declaration_the_tree_has_outgrown` would report `test_n2_cut25.py::W5a-m[…]` as an uncovered stale declaration. Replace `python/tests/arm_staleness.py:116–120` with:

```python
def re_targeted_rows(guard: Path, *, repo_root: Path) -> frozenset[str]:
    """The rows the guard re-targets: `RETARGETED_ROWS` where the guard declares the
    full set (a re-targeted sabotage, or a whole successor arm — cut 25 since 2026-09-15),
    else the keys of its `_LIVE_SABOTAGES` table; empty when it has neither."""
    tests = repo_root / "python" / "tests"
    module = _load(guard, search=(tests, tests / "acceptance"))
    declared = getattr(module, "RETARGETED_ROWS", None)
    if declared is not None:
        return frozenset(declared)
    return frozenset(getattr(module, "_LIVE_SABOTAGES", {}))
```

Append to `python/tests/test_arm_staleness.py`:

```python
def test_re_targeted_rows_reads_a_guards_full_override_set(git_checkout) -> None:
    """A guard that re-targets a whole arm (asserts, sabotage and checks — cut 25's
    `W5a-m` since cut 30) declares `RETARGETED_ROWS`; the detector reads that, not the
    sabotage-only table, so the coverage test above cannot report the row uncovered."""
    assert arm_staleness.re_targeted_rows(ACCEPTANCE / "test_n2_cut25.py", repo_root=REPO_ROOT) == {"W1-a", "W5a-m"}
    assert arm_staleness.re_targeted_rows(ACCEPTANCE / "test_n2_cut29.py", repo_root=REPO_ROOT) == frozenset()
```

(`ACCEPTANCE` and `REPO_ROOT` are the module's existing constants; `git_checkout` its existing fixture.)

- [ ] **Step 4: Run the cut 25 guard's static checks, the four guards' prior-declaration checks, and the staleness audit**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut25.py -q -k "inventory or lettered or sabotage_names or prior_declarations or row_parser"`
Expected: pass (24 frozen, 25 live; `W5a-m`'s new `before` matches `stored.py` exactly once).

Run: `cd python && for n in 26 27 28 29; do uv run --frozen pytest tests/acceptance/test_n2_cut$n.py -q -k prior_declarations; done`
Expected: pass ×4.

Run: `cd python && uv run --frozen pytest tests/test_arm_staleness.py -q`
Expected: pass — the registry (`cited_not_run.py`) gains nothing; `audited_arms` measures the live cut 25 tuple; the coverage test sees `W5a-m` covered through `RETARGETED_ROWS`.

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut25.py -q -k "every_arm_fails_under_its_own_sabotage or every_live_check"`
Expected: pass — `W5a-m` is sound under its new sabotage (the absorb test fails when reconciliation returns `keep`).

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/world-resolution-slice-6 add python/tests/arm_staleness.py python/tests/test_arm_staleness.py python/tests/acceptance/test_n2_cut25.py python/tests/acceptance/test_n2_cut26.py python/tests/acceptance/test_n2_cut27.py python/tests/acceptance/test_n2_cut28.py python/tests/acceptance/test_n2_cut29.py
git -C .worktrees/world-resolution-slice-6 commit -m "test(n2): re-target cut 25's W5a-m to its cut 30 successor"
```

---

### Task 7: Cut 30's declaration, guard and runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut30.py`, `python/tests/acceptance/test_n2_cut30.py`, `python/tools/cut30_acceptance.py`
- Modify: `python/tools/roadmap_status.py:60` (add the cut 30 entry)

**Interfaces:**
- Consumes: the freeze commit and digest from Task 1; the source lines Tasks 2–4 wrote.
- Produces: `CUT30_ARMS`, `DECLARATION_UNITS = ("W5a",)`, `UNIT_CHECKS`, `CO_CITED`, `unit_of`.

- [ ] **Step 1: Write the declaration**

`python/tests/acceptance/n2_arms_cut30.py`:

```python
"""Cut 30 canonical declaration: W5a re-read on the slice 6 reconciliation arms."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W5a",)
_U = "test_identifier_correction.py::TestRelocation"
_R = "test_source_address.py::TestReaders"
UNIT_CHECKS = {"W5a": f"{_U}::test_consolidate_absorbs_divergent_histories"}
# The absorb test is also cut 25's re-targeted W5a-m check (test_n2_cut25._LIVE_ARMS, 2026-09-15):
# the successor discharge is cited by both, on purpose.
CO_CITED = (f"{_U}::test_consolidate_absorbs_divergent_histories",)


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-30 row")
    return unit


def _arm(row, assertion, module, before, after, *checks):
    return Arm(row=row, asserts=assertion, sabotage=Sabotage(module=module, before=before, after=after), checks=tuple(checks))


CUT30_ARMS = (
    _arm("W5a-p", "Divergent histories are absorbed, not dropped.", "stored.py",
         "    if not remainder:\n        return copy.deepcopy(list(keep))\n",
         "    if True:\n        return copy.deepcopy(list(keep))\n",
         f"{_U}::test_consolidate_absorbs_divergent_histories"),
    _arm("W5a-q", "The absorbed chain is validated.", "stored.py",
         '            absorbed = _read_chain(raw["absorbed"], f"{here} absorbed", seen)\n            if dict(absorbed[-1].to_identifiers) != dict(frm):',
         '            absorbed = _read_chain(raw["absorbed"], f"{here} absorbed", seen)\n            if False:',
         f"{_R}::test_malformed_consolidation_shapes_refuse[absorbed-ends-elsewhere]"),
    _arm("W5a-r", "Held addresses reach into absorbed chains.", "stored.py",
         "        addresses |= held_source_addresses(correction.absorbed)\n",
         "        pass\n",
         f"{_R}::test_held_addresses_reach_into_absorbed_chains_once",
         f"{_R}::test_validate_source_history_holds_the_redirect_set_to_the_absorbed_chain[omits-an-absorbed-address]"),
    _arm("W5a-s", "One token is one event across chains.", "stored.py",
         "        if token in seen and seen[token] != raw:\n",
         "        if False:\n",
         f"{_R}::test_malformed_consolidation_shapes_refuse[conflicting-reuse]"),
    _arm("W5a-t", "A consolidation entry changes nothing.", "stored.py",
         '        elif "absorbed" in raw:\n',
         "        elif False:\n",
         f"{_R}::test_malformed_consolidation_shapes_refuse[six-keys-unequal]"),
    _arm("W5a-u", "The entry carries the operation's token.", "relocation.py",
         "                event_token=intent.event_token,\n",
         "                event_token=secrets.token_hex(16),\n",
         f"{_U}::test_consolidate_absorbs_divergent_histories"),
    _arm("W5a-v", "A prefix fast-forwards without an entry.", "stored.py",
         "    if list(keep) == list(other)[: len(keep)]:\n        return copy.deepcopy(list(other))\n",
         "    if False:\n        return copy.deepcopy(list(other))\n",
         f"{_U}::test_consolidate_fast_forwards_a_prefix",
         "test_source_address.py::TestReconcile::test_a_proper_prefix_fast_forwards_either_way"),
    _arm("W5a-x", "An already-held event is not absorbed again.", "stored.py",
         '    remainder = [entry for entry in other if entry["event_token"] not in held]\n',
         "    remainder = list(other)\n",
         f"{_U}::test_consolidate_retries_after_an_interrupted_replacement",
         "test_source_address.py::TestReconcile::test_an_already_absorbed_chain_is_not_absorbed_again"),
    _arm("W5a-y", "Reconciliation refuses conflicting reuse before any intent.", "stored.py",
         "        if token in held and held[token] != event:\n",
         "        if False:\n",
         f"{_U}::test_consolidate_refuses_conflicting_token_reuse"),
    _arm("W5a-z", "The rationale is validated before reconciliation on every path.", "relocation.py",
         "        if not isinstance(rationale, str) or not rationale:\n",
         "        if False:\n",
         f"{_U}::test_consolidate_refuses_a_malformed_rationale_on_both_paths[identity-path-empty]",
         f"{_U}::test_consolidate_refuses_a_malformed_rationale_on_both_paths[absorb-path-empty]"),
)
```

Under `W5a-z`'s sabotage the unencodable rationale still refuses through `v1.encode`; the checks are the two `empty` cases, whose ids come from pytest's stacked-parametrize naming (`divergent` then `rationale`: verify with `uv run --frozen pytest tests/test_identifier_correction.py --collect-only -q | grep malformed_rationale` and copy the ids exactly). `W5a-s`'s sabotage leaves the within-chain `repeats` check intact, so only the cross-chain case is disabled. Every `before` must match its module exactly once: verify each with `grep -c` before committing (`test_each_sabotage_names_one_real_source_site` in the guard enforces it).

- [ ] **Step 2: Write the guard**

Copy `python/tests/acceptance/test_n2_cut29.py` to `test_n2_cut30.py` and edit:

- docstring → `"""Cut 30 declaration accounting, freeze pin, and N2 audit."""`;
- imports: add `from n2_arms_cut29 import CUT29_ARMS`; change `from n2_arms_cut29 import CO_CITED, CUT29_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of` to `from n2_arms_cut30 import CO_CITED, CUT30_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of`; `from test_n2_cut25 import CUT25_ARMS, RETARGETED_ROWS as CUT25_RETARGETED_ROWS`;
- constants: `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-15-conformance-cut-30.md"`; `CUT30_FREEZE_COMMIT = "<Task 1's hash>"`; `CUT30_FROZEN_SHA256 = "<Task 1's digest>"`; `FROZEN_DECLARATION = "python/tests/acceptance/n2_arms_cut30.py"`; `CUT30_DECLARATION_COMMIT` and `CUT30_DECLARATION_SHA256` are filled in Step 4 after the declaration's own commit;
- `FROZEN_PRIOR_CUT_FILES`: add `"python/tests/acceptance/n2_arms_cut29.py": "0e57a52",`;
- `PRIOR_ARMS`: add `*CUT29_ARMS,`;
- every `CUT29_ARMS`/`cut29`/`29` in the test bodies → `CUT30_ARMS`/`cut30`/`30`; the workspace name `"n2-cut30"`;
- `test_the_inventory_is_exactly_the_three_declared_units` → rename `..._the_one_declared_unit`; body: `assert DECLARATION_UNITS == ("W5a",)`, `assert len(CUT30_ARMS) == 10`;
- `test_the_freeze_commit_and_sections_two_through_seven_are_pinned`: the three literal assertions become `assert "**1 declaration unit**" in current`, `assert "Zero guarantee rows are read, **0 full/closed** newly" in current`, `assert '("cut29_acceptance.py",)' in current`;
- `test_prior_declarations_are_frozen_and_no_check_is_reclaimed`: the cut 25 reconstruction becomes `frozen if live.row in CUT25_RETARGETED_ROWS else live` (Task 6's form);
- `test_row_parser…`: the error match `"is not a cut-30 row"` and the sample rows use `W5a` (`"W5a-"`, `"W5aa"`, `"W5a-A"`, `"W5a-1"`, `"W5a-aa"`, `"W5a-a-b"`, `""`, `"D1"`).

- [ ] **Step 3: Write the runner and the accounting entry**

`python/tools/cut30_acceptance.py` — copy `cut29_acceptance.py`, then: docstring `"""Run cut 30 after cut 29 on the certified durable tuple."""`; `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut30-acceptance"`; `PREFIX_RUNNERS = ("cut29_acceptance.py",)`; `PHASE_MODULES = ("test_source_address_acceptance.py", "test_n2_cut30.py")`; the import `from n2_arms_cut30 import CUT30_ARMS, DECLARATION_UNITS, unit_of`; `cut=30`.

`python/tools/roadmap_status.py:60` — add after the `29:` entry:
```python
    30: ("conformance-cut-30-results §2", "", ""),
```
Run `cd python && uv run --frozen python tools/roadmap_status.py | tail -3` and confirm the totals are unchanged (`Closed 153 of 196; open 43`).

- [ ] **Step 4: Commit the declaration, pin it, run the guard**

```bash
W=.worktrees/world-resolution-slice-6
git -C $W add python/tests/acceptance/n2_arms_cut30.py python/tools/cut30_acceptance.py python/tools/roadmap_status.py
git -C $W commit -m "test(cut30): declare the W5a reconciliation arms and the runner"
git -C $W rev-parse HEAD; sha256sum $W/python/tests/acceptance/n2_arms_cut30.py
```
Write both into `test_n2_cut30.py`'s `CUT30_DECLARATION_COMMIT` / `CUT30_DECLARATION_SHA256`, then:

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut30.py -q`
Expected: all pass, including `test_every_arm_fails_under_its_own_sabotage` (ten arms, each sound) and the freeze pin.

```bash
git -C $W add python/tests/acceptance/test_n2_cut30.py
git -C $W commit -m "test(cut30): guard pinning the freeze and the declaration"
```

---

### Task 8: Discharge — certified run, results record, ledger, roadmap, notes, merge

**Files:**
- Create: `docs/plans/2026-09-15-conformance-cut-30-results.md`, `docs/plans/2026-09-15-conformance-cut-30-run/` (transcripts)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (Current state), `docs/plans/2026-08-29-implementation-roadmap.md` (whole re-rank), `docs/designs/2026-09-15-conformance-cut-30.md` (Status line only — outside §§2–7), `docs/superpowers/specs/2026-09-15-world-resolution-slice-6-design.md` (Status), `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` (§7, §12 item 2 dated notes), `docs/designs/2026-08-02-world-addressing-design.md:258` (W5a/consolidate row, dated note), `docs/guide/identity-world-and-change.md:183`, `docs/guide/contracts-and-adoption.md:196,235`, `docs/guide/glossary.md` (the correction-history entry), `README.md:107,148–150`, `tasks/` via the CLI

- [ ] **Step 1: Gates on the branch**

Run from the worktree root: `just check` then `just test-fast`. Expected: clean. Then the certified run, exactly as cut 29's record §1 with `29 → 30` and `world-resolution-slice-5 → world-resolution-slice-6`, keeping every transcript:

```bash
cd /mnt/ssd/Dropbox/beliefs/.worktrees/world-resolution-slice-6
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
for v in 4 7 10 29 30; do export SCIENCE_CUT${v}_ROOT="$MAIN_CHECKOUT/.cut30-acceptance/world-resolution-slice-6"; done
mkdir -p "$MAIN_CHECKOUT/.cut30-acceptance" docs/plans/2026-09-15-conformance-cut-30-run
just check > docs/plans/2026-09-15-conformance-cut-30-run/check.log 2>&1
just test > docs/plans/2026-09-15-conformance-cut-30-run/test.log 2>&1
(cd python && uv run --frozen python tools/cut30_acceptance.py > "$MAIN_CHECKOUT/.cut30-acceptance/run.log" 2>&1)
cp "$MAIN_CHECKOUT/.cut30-acceptance/run.log" docs/plans/2026-09-15-conformance-cut-30-run/certified.log
```
All three exit 0 (`echo $?` after each). Redact machine paths in the logs as cut 29 did (`<pytest-temp>/`, `.cut30-acceptance/`), then `sha256sum` each. A failure is reported with its output, not worked around; the certified volume is the repository's own (`certified-volume-is-the-repo-volume`).

- [ ] **Step 2: Write the results record**

`docs/plans/2026-09-15-conformance-cut-30-results.md`, on cut 29's shape (`2026-09-14-conformance-cut-29-results.md`): header (cut, freeze hash/digest, declaration hash/digest, subject `divergent correction histories reconciled at consolidate`, discharged date/branch, runner); §1 What ran (the commands, exit codes, transcript links and digests, the prefix chain cut 30 → cut 29 → … → cut 17 and the module summary table copied from `certified.log`); §2 Accounting — `Zero guarantee rows are read, **0 full/closed** newly; one declaration unit, W5a, re-read on ten reconciliation arms; W8 unchanged`; §3 Evidence (the certified tuple paragraph as measured in `certified.log`; "No allowlist, frozen declaration, frozen cut body or cited-not-run guard was changed; cut 25's `W5a-m` is re-targeted live in `test_n2_cut25.py`"); §4 Reproduction measurement (none: no source is consolidated in the mm30 corpus); §5 **Remaining boundary** — must name guarantee rows: `` `world-resolution` retains no filed follow-up and leaves the ledger. `authority-labels` retains **W8's ambiguous-search-term conflict, W9 and W14**. `contract-cut` retains **R23** only on its rules-store clauses and **W8a** only on its `instrument-certification` arm. ``; §6 Main integration (filled after the merge, Step 6).

- [ ] **Step 3: Ledger, roadmap, guide, README, dated notes, statuses**

Ledger `Current state`: heading `## Current state (2026-09-15)` stays (the anchor `#current-state-2026-09-15` is linked from the roadmap and §1); `**Updated 2026-09-15** for cut 30's world-resolution slice 6 discharge.`; `Implemented through conformance cut 30.` … `cuts 26–30 record discharge … most recently ../plans/2026-09-15-conformance-cut-30-results.md`; add a bullet after the existing world-registry bullet: `- **Source identity, correction and reconciliation** — normalized identifier bases, the attributed correction seam and redirect set (cut 25), and divergent correction histories reconciled at `consolidate` by absorption, idempotent over a re-run (cut 30).`; **delete** the `world-resolution` row from the table; rewrite the paragraph after the table: `The newest results record (../plans/2026-09-15-conformance-cut-30-results.md) discharges world-resolution slice 6, reconciling divergent correction histories at consolidate; the world-resolution boundary is closed and beliefs-d248ba with it. W8 remains unchanged. nodes-remainder closed 2026-09-12: …` (keep the rest).

Roadmap (rewritten whole, per its header): `**Ranked at:** cut 30, against the ledger's Current state (2026-09-15)`; replace the "Cut 29 …" paragraphs with `**Cut 30 (2026-09-15) discharges world-resolution slice 6 and closes the boundary** — divergent correction histories reconcile at consolidate by absorption; no guarantee row moves. Tier 1 now has no on-path boundary: the reproduction lane's measurement ranked world-resolution on the path, and its last follow-up is discharged, so rule 6 admits off-path lanes, in breadth order, beside the parked estimand-typing lane (beliefs-705507 re-reads rule 6).` Keep `153 of 196 rows closed, with 43 open`. Boundary index: remove the `world-resolution` row. Tier 1 "On the path": replace the table with one sentence, `No boundary: the reproduction record's on-path measurement is discharged at cut 30; the next measurement (a second corpus) may place one here.` Off-path table unchanged (rows 2–5 renumbered 1–4). Lanes table: `world-read` becomes `` `event-level-l8` (+ `log-remainder`) → `publish` `` with status `off the path at its head; world-resolution discharged at cuts 23–25 and 27–30`. Appendix A: header `at cut 30`, sentence `Cut 30 closes nothing and re-reads W5a on its reconciliation arms.`; the W row's part list unchanged (W5a is closed). Appendix B: unchanged. Run `cd python && uv run --frozen pytest tests/test_designs_corpus.py -q` after every edit round.

Guide: `identity-world-and-change.md:183` add `Cut 30 reconciles divergent correction histories at consolidate — keep's chain is the spine, the other replica's unheld events are absorbed into one consolidation entry, a prefix fast-forwards, and a re-run after interruption absorbs nothing twice; world-resolution is closed.`; `contracts-and-adoption.md:196` `Twenty-three` → `Twenty-four` (count the discharged cuts the sentence means: it read twenty-three at cut 29's discharge, so one more); `:235` add the cut 30 sentence on cut 29's pattern; `glossary.md`'s identifier-correction entry gains `; a consolidation entry (from == to, plus absorbed) records the other replica's history when duplicates consolidate (cut 30)`. `README.md:107` `through **cut 30**`; `:148–150` the latest discharged boundary is cut 30 with both links.

Dated notes: slice 2b spec §7's `consolidate` bullet gains `*Built at cut 30 (2026-09-15): divergent histories reconcile by absorption; see 2026-09-15-world-resolution-slice-6-design.md.*` and §12 item 2 the same; world design line 258 (entity continuity row) gains `*— and from 2026-09-15 (cut 30) consolidate of two source replicas absorbs the non-surviving replica's correction history into the survivor's, so every retired address both held stays derivable*`. Statuses: the cut 30 document's `**Status:**` line → `discharged 2026-09-15; results: ../plans/2026-09-15-conformance-cut-30-results.md` (this line is above §2 and outside the pinned body); the slice 6 spec's `**Status:**` → `discharged at conformance cut 30 on 2026-09-15; results: ../../plans/2026-09-15-conformance-cut-30-results.md`.

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/acceptance/test_n2_cut30.py -q -k "not sabotage"` — Expected: pass (ledger names cut 30 and the remaining rows; roadmap and ledger share one id set; `Ranked at` is cut 30).

- [ ] **Step 4: Close the tasks in the discharge commit**

```bash
W=.worktrees/world-resolution-slice-6
tasks done <this step's child id, from `tasks tree beliefs-24b42b`> "cut 30 discharged: results record, ledger, roadmap, guide, README, dated notes"
tasks done beliefs-24b42b "Divergent correction histories reconcile at consolidate by absorption (cut 30, discharged 2026-09-15)"
tasks done beliefs-d248ba "world-resolution closed: slices 1–6 discharged at cuts 23–25, 27–30; both filed follow-ups landed"
tasks check
git -C $W add -A docs README.md tasks python/tools/roadmap_status.py
git -C $W commit -m "docs(cut30): discharge conformance cut 30 and close world-resolution"
```
`tasks done beliefs-d248ba` is offered by `tasks prime`'s closeout once its last child closes; if it refuses on an open descendant, list them (`tasks tree beliefs-d248ba`) and close or reparent before forcing nothing.

- [ ] **Step 5: Review and merge**

Request review with `superpowers:requesting-code-review` over the whole branch; take every finding as its own commit. Then:

```bash
cd /mnt/ssd/Dropbox/beliefs && git merge --no-ff design/world-resolution-slice-6 -m "merge: world resolution slice 6 — conformance cut 30"
```
Run `just gate` on merged `main` with the five `SCIENCE_CUT*_ROOT` exports of Step 1; record the pass counts, transcript (`main-gate.log`, redacted, digested) and merge hash in the results record's §6; commit that as `docs(cut30): record merged-main verification` on `main`.

- [ ] **Step 6: Worktree cleanup**

The spec and plan are tracked (AGENTS.md names their directories), so nothing needs copying. `git worktree unlock .worktrees/world-resolution-slice-6 && git worktree remove .worktrees/world-resolution-slice-6`; delete the branch only after the merge commit is on `main` (`git branch -d design/world-resolution-slice-6`). Note on `beliefs-705507` (the parked estimand-typing Task 0, from `.worktrees/estimand-typing`): `tasks note beliefs-705507 "Rule 6 re-read 2026-09-15 after cut 30: tier 1 has no on-path boundary; the off-path lane may open — rebase onto main first."`

---

## Self-review

**Spec coverage.** §3.1–3.3 → Task 2; §4 → Task 3; §5 (rationale, early intent, merge, `_reconcile`) → Task 4; §6 refusals → Tasks 3–4 (`HistoryDisagreement` cases) and the docstring; §7.1 unit → Tasks 2–4 (every named test appears by name); §7.2 acceptance → Task 5, as amended; §7.3 ten arms → Task 7 (`W5a-p…z`, `W5a-w` withdrawn per the spec); §7.4 the cut → Tasks 1, 7, 8; §7.5 frozen evidence → Task 6 (and Task 2's anchor check); §8 shared files → Tasks 4, 8; §9 task linkage → Task 8 step 4 and step 6; §10 limitations → the cut document §7 (Task 1).

**Type consistency.** `reconcile_correction_histories(keep, other, *, actor, grounds, event_token) -> list[dict[str, Any]]` is defined in Task 3 and called with the same keywords in Task 4 and sabotaged by name in Tasks 6–7; `_reconcile(survivor, loser, *, correction_entries=None)` defined and called in Task 4; `IdentifierCorrection.absorbed` (Task 2) read as `.absorbed` in Tasks 4–5; `consolidation(frm, absorbed, *, actor, grounds, token)` and `C`/`ADDR_C` (Task 2) imported in Task 4; `RETARGETED_ROWS` (Task 6) imported as `CUT25_RETARGETED_ROWS` in guards 26–30. Sabotage `before` strings in Tasks 6–7 are the exact lines Tasks 3–4 write; Task 7 step 1 requires a `grep -c` of each before committing.
