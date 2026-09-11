# Conformance cut 25 — source addresses derived from normalized identifiers

**Status:** frozen and discharged 2026-09-11. W1, W2 and W5a are closed.
**Design:** `../superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md`, reviewed in four passes 2026-09-10.
**Numbered after and serialized after** cut 24, whose discharge is in the branch ancestry.

## 1. What this cut is

World addressing derives a source's basis from an external identifier, but the
pre-slice builder accepted an authored slug: identical handles could collide for
different works, and different handles could split one DOI. Source identifiers
could not be corrected because `revise` refused the kind.

This cut reads the derived address, strict boundary and attributed correction
seam built by slice 2b. Builders normalize every identifier; fixed precedence
selects one basis. Correction preserves `uid`, records the actor's assertion
that this is the same work, and retains retired addresses without rewriting
referrers. Writes, reads, import and relocation validate history and redirects.

The selection rule is cut 5's: a clause is selected only when its source mutation
and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `python/src/beliefs/source.py`: `doi > pmid > isbn > accession`, per-scheme
  normalization and ordered refusals, validation of every entry before selection,
  and `science.source-address.v1` digest over `{"scheme": s, "value": v}`.
- `python/src/beliefs/stored.py` and both copies of `CONTRACT.yaml`: the
  keyword-only source builder, basis readers, identity-inert correction facet and
  single history/redirect validator. Entries are canonical, attributed, encodable,
  non-empty, changing and continuous, with distinct tokens; `deprecated_ids` is
  exactly the sorted held-address set less the live id.
- `python/src/beliefs/corpus.py`: admission and replacement require canonical
  values and a derived source address; dataset basis admission stays enforced.
  Ordinary add refuses history; import admits valid provenance. Correction checks
  authority and the current subject before append, refuses malformed, empty,
  unchanged or colliding successors before submission, and validates the completed
  successor. Address movement submits one create/delete plan; unchanged addresses
  submit replacement. No referrer is rewritten.
- `python/src/beliefs/corpus.py` and `python/src/beliefs/session/writer.py`: the
  operation and scoped correction forms, one `corpus-write` with no new operation
  kind or act-report. Both read validation and the check finding loop invoke the
  shared history validator.
- `python/src/beliefs/relocation.py`: movement carries history as provenance;
  consolidation refuses differing identifier maps or histories and validates the
  replacement; deletion removes the record and its redirects together.
- The live static and dynamic permit inventories register `correct_identifier`
  as a source `corpus-write`, with family, kind and exact-permit coverage.
- Source/correction unit tests, durable
  `python/tests/acceptance/test_source_address_acceptance.py`, cut 25's N2
  declarations and audit, and `python/tools/cut25_acceptance.py`.
- Dataset revision's resource-preservation comparison and W5a acceptance proving
  a re-hold is a new entity with its prior assessment bound to the old identity.

Out of scope: dataset address derivation; reconciling divergent correction
histories; source-assertion builders/readers; W14's renderer; W8b; slice 3's
snapshot/import/audit/diagnostic remainder and slice 4's world-view evaluation.
Frozen declarations and cut bodies through cut 24 remain byte-exact. Prior live
phase modules receive only the authorized source fixture migration; cut 4's two
displaced W3 arms are registered as cited staleness and cut 16 M3a is retargeted
in its live guard, as design §10.6 requires.

## 3. Selection

### W1 — closed

Three pairs sharing a title and citekey-shaped display but holding distinct DOIs
produce six records and addresses. A handle resolves nowhere in the corpus or
published world. Hand-built and replacement records must agree with their
derived address. Selected unit: `W1`. Deferred: nothing within this source row.

### W2 — closed

Equivalent spellings normalize to one facet, stamp and address. Every identifier
is validated before precedence chooses a basis. Duplicate adds refuse; duplicate
corpus locations refuse publication until consolidation leaves one location.
`{pmid: P}` and `{doi: D, pmid: P}` remain distinct selected bases despite their
shared secondary identifier. Selected unit: `W2`. Deferred: nothing in this row.

### W5a — closed

Both arms run. Dataset resource changes refuse in-place revision; re-holding
mints a new entity and preserves the prior assessment's binding. Source correction
preserves `uid`, moves exactly when the selected basis changes, retains redirects
(including A→B→A), and changes no referrer bytes. Add, correction and coreference
attestation are distinct explicit acts with no case chooser. Refusals have no
intent or effect; submitted create/delete prefixes are classified and settled.
Move, consolidation and delete preserve the lifecycle rules. Selected unit:
`W5a`. Dataset re-addressing stays a separate task.

## 4. Accounting

Three guarantee rows are read, **3 full/closed** (W1, W2, W5a), and
**3 declaration units** carry them. There are **24 declared arms**. The reviewed
acceptance and sabotage checks supply closure evidence.

## 5. N2 and acceptance obligations

1. Units are exactly `W1`, `W2`, `W5a`; rows are `<unit>` or `<unit>-<letter>`.
   A trailing hyphen without a letter is invalid. No earlier check is reclaimed;
   `CO_CITED = ()`.
2. Every durable arm runs on the certified kernel/volume tuple. Capability
   refusal is an error, never a waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut24_acceptance.py",)` and
   `PHASE_MODULES = ("test_source_address_acceptance.py", "test_n2_cut25.py")`.
4. These 24 arms each mutate one exact source site and name independent test
   functions in `n2_arms_cut25.py`. Every check must pass without its mutation and
   fail with it; stale, vacuous, mixed and uncollected arms refuse.

| Row | Module | Removed or weakened mechanism |
|---|---|---|
| W2-a | source.py | DOI lowercase fold |
| W2-b | source.py | DOI prefix stripping |
| W2-c | source.py | Fixed scheme precedence (reversed) |
| W2-d | source.py | Whole-map validation (first entry only) |
| W2-e | source.py | ISBN-13 check-digit validation |
| W2-f | source.py | Named unknown-scheme refusal |
| W2-g | source.py | Named empty-remainder refusal |
| W1-a | corpus.py | Source id/derived-address agreement |
| W1-b | corpus.py | Source validation at replacement preflight |
| W1-c | corpus.py | Canonical stored values |
| W5a-a | corpus.py | Dataset basis admission refusal |
| W5a-b | corpus.py | Deprecated-address rebuild |
| W5a-c | corpus.py | No-referrer-write plan (replaced by `Corpus.rename`) |
| W5a-d | corpus.py | Authority actor binding (replaced by `nobody`) |
| W5a-e | corpus.py | Unchanged-map refusal |
| W5a-f | corpus.py | Current-source validation before append |
| W5a-g | corpus.py | History prohibited on ordinary add |
| W5a-h | corpus.py | Source validation at import |
| W5a-i | corpus.py | History/redirect validation on read |
| W5a-j | corpus.py | History validation in check findings |
| W5a-k | stored.py | Exact redirect list (weakened to set equality) |
| W5a-l | stored.py | Every history entry's `from != to` |
| W5a-m | relocation.py | Consolidation history agreement |
| W5a-n | corpus.py | Dataset revision resource preservation |

5. The audit uses the existing per-function harness unchanged. Staleness is
   measured using actual live adapters and pinned source trees; cited staleness
   must equal the registry. Against untouched main, only the authorized cut 4
   W3[6]/W3[8] additions and cut 16 M3a declaration displacement are permitted;
   every live matcher must still apply exactly once.
6. Prior declarations remain pinned, including cut 24 at `79f118f`. The immediate
   follow-up commit pins cut 25's freeze commit and this document's digest after
   the freeze commit exists.

## 6. Second reader

The design's four review passes on 2026-09-10 (spec §14) resolved: (1) address
form, choice rule, strictness, attribution and dataset scope; (2) both admission
paths, canonicality, total validation, precedence and explicit history reader
invocation; (3) own-uid collision handling, address-change predicate, actor
assertion, read/append validation, history-free redirects, relocation, manifest
digest and unchanged refusal; (4) valid DOI migration, W2 duplicate location,
dataset sabotage, failure prefixes, frozen evidence boundaries, blocked-address
limitation, both contracts and intended closure wording.

Subsequent plan review established the shared history/redirect validator, row
parser, per-mutation fixtures and cited-not-run treatment of cut 4. Task 10's
implementation evidence received controller review before Task 11 froze.

## 7. Limitations

1. A mis-transcribed identifier belonging to another work remains blocked as a
   retired address while the corrected record exists; releasing it needs a design.
2. Accession normalization is form-only, without a namespace authority. Equal
   strings in different databases are one identifier here.
3. False same-work assertions are attributed, not detected.
4. Precedence can give one work two addresses; a shared secondary identifier is
   a future audit finding, never automatic identity inference.
5. The source label renderer is unbuilt; W14 belongs to slice 4.

## 8. Post-freeze coverage correction — 2026-09-11

Final review found a missing design §10.4 mechanism: frozen W5a-k weakens
redirect list equality to set equality, but its fixtures have correction
history. It does not remove only the history-free redirect refusal. The
production guard was correct; the controller authorized this supplemental
live proof while preserving the original discharge evidence.

`python/tests/acceptance/test_n2_cut25.py` retains the frozen declaration under
`FROZEN_CUT25_ARMS` and exports `CUT25_ARMS` with supplemental **W5a-o**. In
`stored.py`, its exact unique source mutation is:

```python
    if list(node.deprecated_ids) != expected:
```

changed to:

```python
    if history and list(node.deprecated_ids) != expected:
```

It selects both existing independent checks:

- `test_source_address.py::TestReaders::test_a_history_free_source_with_a_deprecated_id_refuses`
- `test_identifier_correction.py::TestTheBoundary::test_a_history_free_source_with_a_deprecated_id_refuses`

Both checks pass without sabotage and fail under this mutation. The existing
baseline, exact-site, uniqueness, no-reclaim and soundness loops include the
supplement: **25 live audited arms**, across the same three declaration units.
Portable staleness reads the guard's live `CUT25_ARMS`, so this arm also refuses
a displaced source matcher.

Historical accounting remains **24 frozen declared arms**, three declaration
units and three closed rows. The runner's `declared_accounting` reads the frozen
declaration file and therefore remains `24/3/3`; it executes the live audit as
its existing phase. `n2_arms_cut25.py` and this document's frozen §§2–7 remain
byte-exact. The original freeze commit
`50726094e7109dc9bad2754a85515580c8614127` and frozen-document SHA-256
`05c17b94be314daf1aabf07c0f9750b1a41d8db30ba352fe0aec3977b11038b7`
are unchanged. This dated supplement is outside that frozen body and does not
rewrite the original discharge or create a new declaration unit.
