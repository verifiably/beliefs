# World resolution slice 2 — implementation plan

**Status:** planned 2026-09-10; not yet frozen or implemented.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `coreference-attestation` a governed, mintable kernel kind whose attestations the epoch build reduces into a populated coreference balance, so that W15, the coreference arms of X12, W8a and M3, and W4 as rewritten can be read closed at conformance cut 24.

**Architecture:** The kind is promoted from deferred to governed in the contract; `stored.py` gains its builder, reader and closed endpoint-kind set; `CorpusWriter.attest_coreference` mints it under the four endpoint refusals and the actor bind, with a matching import clause, and the session facade exposes it as an eighth ledgered route; `epoch._captured_records` lifts the validated facet so the shipped reduction reduces real records; the shipped rule normalizes its deduplication key to NFC and the boundary refuses non-NFC text so identity and reduction agree. Nothing on the read side changes. The work freezes as cut 24 before any code lands and discharges through its own runner after cut 23's.

**Tech Stack:** Python 3.11+ (`uv run --frozen`), pytest with `pytest-xdist`, pydantic v2 `Node` models from `nodes`, the `atoms` durable engine for the acceptance arms, PyYAML for fixtures, ruff and pyright as the gate; vitest for the one TypeScript parity line.

**Spec:** `docs/superpowers/specs/2026-09-10-world-resolution-slice-2-design.md` (revised through `30b3dcb`). The plan argues from it; read both.

## Global Constraints

- Work on branch `world-resolution` in `.worktrees/world-resolution`; conventional commits; no AI-attribution trailers; no `/home/<user>` or absolute Dropbox paths in code or docs.
- Run every Python command from `python/` with `uv run --frozen …`. The pre-commit hook runs `just check` (ruff, pyright, biome, tsc, `tasks check`), so `ts/node_modules` must exist (`cd ts && npm ci` once).
- Fast loop: `uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py`. Before each commit: `uv run --frozen ruff check . && uv run --frozen pyright`.
- Tracker: `tasks start <id>` before a task's first step, `tasks note <id> "<what landed>"` and `tasks done <id> "<result>"` at its last, `tasks check` before every commit. Never edit `tasks/*.md` directly. Task ids: Task 1 `beliefs-2fff11`, Task 2 `beliefs-7d6bd2`, Task 3 `beliefs-e88cae`, Task 4 `beliefs-4407ca`, Task 5 `beliefs-0cefae`, Task 6 `beliefs-413c84`, Task 7 `beliefs-ee18db`, Task 8 `beliefs-edf1ad`, Task 9 `beliefs-e963b9`; the parent is `beliefs-113561`.
- `Authority(...)` is constructed in `beliefs/permit.py` and in tests only. Every new entry point calls `self._authority.require(<family>, <kinds>)` before its hold.
- The attestation record carries **no relations** (spec §2 item 1). Every facet string is NFC at every boundary (spec §2 item 2). The controlled-shape rebuild compares `id`, `facets` and `relations` only (spec §4.1 step 5).
- Lock order at the seam: the writer's own `_operation` hold; a supplied `WorldReadView` was opened **before** the call and is never opened inside it (spec §2 item 3).
- `ENUMERATED_SOURCE_KINDS`, `EXCLUDED_MUTATION_KINDS`, `ELIGIBLE_RETRACTION_TARGET_KINDS`, `evaluation.READ_KINDS`, `read.coreference_edge` and `read.expand_coreference` are **not** edited.
- Shared surfaces this lane rewrites, per roadmap concurrency rule 3: `errors.py`, `corpus.py`, `stored.py`, `world/epoch.py`, `world/derive.py`, `world/rules_v1/coreference.py`, `session/writer.py`, both `CONTRACT.yaml` copies, `python/tests/test_designs_corpus.py`, the ledger, the roadmap and the guide at discharge.
- The cut is frozen before implementation (Task 1) and its §§2–7 are byte-exact from the freeze commit onward; §1 stays editable. The cut number is 24 unless a sibling worktree has already claimed it — check every worktree's `docs/designs/` at freeze.

---

## File structure

| path | responsibility |
|---|---|
| `docs/designs/2026-09-10-conformance-cut-24.md` | the frozen cut: boundary, selection, accounting, obligations |
| `contracts/science/CONTRACT.yaml`, `python/src/beliefs/contracts/science/CONTRACT.yaml` | the kind's domain and facet; byte-identical copies |
| `python/src/beliefs/stored.py` | `COREFERENCE_ATTESTATION_FACET`, `COREFERENCE_ATTESTATION_DOMAIN`, `COREFERENCE_ENDPOINT_KINDS`, `CoreferenceAttestation`, `coreference_attestation_value`, `coreference_attestation_node` |
| `python/src/beliefs/world/rules_v1/coreference.py` + `fixtures/coreference.unicode.yaml` | the NFC-normalized deduplication key and its fixture |
| `python/src/beliefs/world/derive.py` | `CapturedCoreference` refuses non-NFC text |
| `python/src/beliefs/world/epoch.py` | `_captured_records` lifts the facet |
| `python/src/beliefs/errors.py` | `CoreferenceEndpointRefused` |
| `python/src/beliefs/corpus.py` | `CorpusWriter.attest_coreference`, `_validated_coreference`, `_resolve_coreference_endpoints`, the family-kind clause, the import clause, `OperationWrites.attest_coreference` |
| `python/src/beliefs/session/writer.py` | `ScopedWriter.attest_coreference` |
| `python/tests/test_coreference_attestation.py` | **new** unit tests: builder, reader, rule, capture, seam, import, session |
| `python/tests/test_facet_declarations.py`, `test_base_contract.py`, `test_world_build.py`, `test_profile.py`, `test_permit_boundary.py`, `test_permit_entry_points.py`, `test_session_writer.py`, `test_world_read.py`, `ts/tests/declarations.test.ts` | pins that move |
| `python/tests/acceptance/test_coreference_acceptance.py` | **new** durable arms on the certified volume |
| `python/tests/acceptance/n2_arms_cut24.py`, `test_n2_cut24.py` | declarations and guard |
| `python/tools/cut24_acceptance.py` | the runner |
| `python/tools/roadmap_status.py` | cut 24's accounting row |
| `docs/designs/2026-08-02-world-addressing-design.md` (W8a), `2026-08-08-world-address-ruling.md` (§5.5), `2026-09-05-writer-session-design.md`, `2026-09-04-write-permits-design.md`, `2026-09-03-world-changing-families-design.md`, `2026-09-05-facet-contracts-design.md`, `2026-08-20-world-index-slice-2-design.md`, `docs/guide/identity-world-and-change.md` | dated notes |
| `docs/plans/2026-09-XX-conformance-cut-24-results.md`, ledger, roadmap, `README.md` | discharge |

---

### Task 1: Freeze conformance cut 24

**Files:**
- Create: `docs/designs/2026-09-10-conformance-cut-24.md`
- Modify: `README.md` (the design list and the stated count of designs), `python/tests/test_designs_corpus.py` only if `_COUNT_WORDS` needs the next number word

**Interfaces:**
- Produces: the five declaration units `W15`, `X12`, `W8a`, `M3`, `W4`, cited verbatim by Task 7's `DECLARATION_UNITS`; the literals `PREFIX_RUNNERS = ("cut23_acceptance.py",)` and `PHASE_MODULES = ("test_coreference_acceptance.py", "test_n2_cut24.py")` cited by Task 8; the freeze sha and sha256 cited by Task 7's guard.

- [ ] **Step 1: `tasks start beliefs-2fff11`, then confirm the number is free**

```bash
git -C /mnt/ssd/Dropbox/beliefs worktree list
for wt in $(git -C /mnt/ssd/Dropbox/beliefs worktree list --porcelain | awk '/^worktree /{print $2}'); do ls "$wt/docs/designs" | grep -c "conformance-cut-24"; done
git -C /mnt/ssd/Dropbox/beliefs branch -a --contains $(git -C /mnt/ssd/Dropbox/beliefs rev-parse main) | head
```
Expected: every count is `0`. If not, the number is taken; use the next free one everywhere below and in every later task.

- [ ] **Step 2: Write the cut document**

Follow `docs/designs/2026-09-09-conformance-cut-23.md` section for section. Header:

```markdown
# Conformance cut 24 — the coreference attestation and its balance

**Status:** frozen 2026-09-10 before implementation.
**Frozen:** 2026-09-10, before implementation, on `world-resolution`
**Design:** `../superpowers/specs/2026-09-10-world-resolution-slice-2-design.md`, reviewed twice 2026-09-10
**Numbered after** cut 23 (roadmap concurrency rule 1) and **serialized after** its discharge, which landed on `main` at `6eb0b93` (rule 5).
```

`## 1. What this cut is` — spec §1's first two paragraphs, then the selection rule sentence cut 23 uses: "The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial."

`## 2. The boundary` — `In scope:` bullets at file-and-symbol granularity from this plan's file-structure table; `Out of scope:` bullets naming slice 2b (`beliefs-b7994b`: W1, W2, W5a — source addresses derived from the normalized identifier), slice 3 (the import, audit and diagnostic callers; R23's snapshot, divergence and explicit-import clauses; X5, W13), slice 4 (W7), W8b (measured, repaired by `beliefs-fda0e5`, not selected), the `instrument-certification` kind and every `instrument-certification` arm (`contract-cut`), W8a's import-boundary and audit arms (`packaging-remainder`), and the read side (`read.coreference_edge`, `read.expand_coreference`, unchanged).

`## 3. Selection` — one subsection per row:

```markdown
### W15 — closes
A coreference balance is derived over typed endpoints and a declared coverage, is unmoved by exact duplicate submissions, privileges no attester class, and its closure rewrites nothing. Every arm of the row is read: the four endpoint refusals; the balance sequence with the actor swap; first-versus-rest duplication under ten tokens and the different-grounds limit; closure rewriting nothing; the coverage and missing-attestation arm with no-epoch unspellable and the three non-validated receipt outcomes; absent-is-not-empty as spec §6 states it; the cycle route with both negatives. Selected: unit `W15`. **Deferred:** nothing.

### X12 — part, coreference arms
An in-coverage attestation is inside the pair's published balance and an out-of-coverage one outside it; omission and a wrong balance refute the receipt; a refuted receipt moves no `belief_input_digest` and reads its edges `indeterminate`; an unmounted or moved named state is `unresolvable`. Selected: unit `X12`. **Deferred:** the `instrument-certification` membership and omission-refutes arms (`contract-cut`).

### W8a — part, coreference arms
The coreference reduction carries its own completeness evidence: omitting an in-coverage attestation refutes the receipt. The coverage arm is read as the digest-boundary claim it can carry (spec §5): over one coverage, differing coreference maps carry one digest; over two coverages the digest moves with the coverage member of the producer snapshot, recorded by dated note on the row. Selected: unit `W8a`. **Deferred:** the `instrument-certification` omission-refutes arm (`contract-cut`); the import-boundary and audit arms (`packaging-remainder`).

### M3 — part, coreference arm
A coreference attestation over two distinct-basis retractions leaves both byte-unchanged and closes no cycle; no operation merges them; the abstract validator, the forced verdict and the raw-audit classification are unchanged by an active edge. Selected: unit `M3`. **Deferred:** the concrete-cycle arms stay cut 5's banked limitation.

### W4 — closes, as rewritten 2026-08-08
No operation retires an address on coreference grounds: after an attestation both endpoints are byte-unchanged and live with no new `deprecated_ids` entry, and the operation inventory has no member that writes one. Selected: unit `W4`. **Deferred:** nothing; the equal-basis, lineage-divergence and distinct-basis arms live in W16 and W15 by the ruling's re-homing.

### Boundary invariants
The record carries no relations; every facet string is NFC at the builder, the reader and the capture; the seam touches no endpoint; the read side is unchanged.
```

`## 4. Accounting` — exactly these two sentences, which the guard greps:

```markdown
Five guarantee rows are read, **2 full/closed** (W15, W4), 3 partial (X12, W8a, M3), and **5 declaration units** carry them: `W15`, `X12`, `W8a`, `M3`, `W4`. W8b stays measured and not selected; W1, W2 and W5a are re-filed to slice 2b (§2).
```

`## 5. N2 and acceptance obligations` — numbered as cut 23's: (1) the inventory is exactly the five units, single-homed; (2) every durable arm runs on the certified volume, refusal is an error and never a skip; (3) the runner, quoting `PREFIX_RUNNERS = ("cut23_acceptance.py",)` and `PHASE_MODULES = ("test_coreference_acceptance.py", "test_n2_cut24.py")`; (4) the 18 declared arms cover every sabotage site: in `corpus.py` (the admissible-kind set widened to prose; the raw self-pair check dropped; exact resolution weakened to presence; the kind comparison dropped; the actor bind dropped; the family-kind clause dropped; the controlled rebuild narrowed to the id; the import clause dropped; attestations admitted into the retraction graph; a `merge` name registered on the operations facade), in `stored.py` (relations attached to each endpoint), in `world/epoch.py` (the capture lift dropped), in `world/rules_v1/coreference.py` (the event token added to the key; the NFC normalization dropped), in `world/read.py` (missing coverage answered empty; the refuted rebuild answered validated; the rebuild comparison narrowed to membership), and in `world/derive.py` (the coreference map added to the belief input); (5) `test_n2_cut24.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree; (6) prior declarations frozen, no check reclaimed; (7) the freeze pin.

`## 6. Second reader` — the spec's two review passes on 2026-09-10 (§14 there): eight findings, then four. `## 7. Limitations` — (1) the deduplication key defeats exact NFC duplicates only; per-attester capping and grounds equivalence are policy, unbuilt; (2) the coverage arm's "digest unchanged" clause is unsatisfiable as the row states it and is read on one coverage; (3) an attestation over a since-deleted endpoint is reduced and never refused (spec §13 item 3).

- [ ] **Step 3: Add the document to the README list and count**

Open `README.md` at the repository root, add the cut in date order in the same format as cut 23's entry, and bump the stated count of designs by one. Run `uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider` to see the exact phrase `test_the_readme_states_how_many_designs_there_are` expects; extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` if the next number word is missing.

- [ ] **Step 4: Run the design-corpus guards**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider`
Expected: PASS.

- [ ] **Step 5: Commit the freeze and pin it**

```bash
git add docs/designs/2026-09-10-conformance-cut-24.md README.md python/tests/test_designs_corpus.py
git commit -m "docs(cut24): freeze conformance cut 24, the coreference attestation"
git rev-parse --short HEAD
sha256sum docs/designs/2026-09-10-conformance-cut-24.md
tasks note beliefs-113561 "cut 24 frozen at <sha>, sha256 <digest>"
tasks done beliefs-2fff11 "cut 24 frozen at <sha>"
```

---

### Task 2: The governed kind — contract, builder, reader, deferral pins

**Files:**
- Modify: `contracts/science/CONTRACT.yaml:60` and `:83-97`; `python/src/beliefs/contracts/science/CONTRACT.yaml` (same bytes)
- Modify: `python/src/beliefs/stored.py` (`__all__` near `:75-131`; constants near `:147`; the builders after `retraction_node` ends at `:950`)
- Modify: `python/tests/test_facet_declarations.py:39-44`, `python/tests/test_base_contract.py:182-186`, `python/tests/test_world_build.py:977-1037`, `python/tests/test_profile.py:46`, `ts/tests/declarations.test.ts:23`
- Create: `python/tests/test_coreference_attestation.py`

**Interfaces:**
- Produces: `stored.COREFERENCE_ATTESTATION_FACET = "coreference-attestation"`, `stored.COREFERENCE_ATTESTATION_DOMAIN = "science.coreference-attestation.v1"`, `stored.COREFERENCE_ENDPOINT_KINDS: tuple[str, ...]`, `stored.CoreferenceAttestation` (frozen dataclass: `endpoints: tuple[str, str]`, `stance: int`, `actor: str`, `grounds: str`, `event_token: str`), `stored.coreference_attestation_value(node: Node) -> CoreferenceAttestation` (raises `MalformedRecord`), `stored.coreference_attestation_node(*, title: str, endpoints: Sequence[str], stance: int, actor: str, grounds: str, event_token: str) -> Node`.

- [ ] **Step 1: `tasks start beliefs-7d6bd2`, then write the failing tests**

Create `python/tests/test_coreference_attestation.py`:

```python
"""World resolution slice 2: the coreference attestation as a stored kind, its
capture, its seam, and its reduction (spec 2026-09-10-world-resolution-slice-2-design.md)."""

from __future__ import annotations

import pytest
from authority import ACTOR
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS
from beliefs.errors import MalformedRecord
from beliefs.identity import v1

LEFT = "dataset:left"
RIGHT = "dataset:right"
NFC = "caf\u00e9"      # precomposed e-acute
NFD = "cafe\u0301"     # e + combining acute: one string to every digest, two to Python


def attestation(*, endpoints=(RIGHT, LEFT), stance=1, actor=ACTOR, grounds="the same bytes", token="event-1"):
    return stored.coreference_attestation_node(
        title="coreference", endpoints=endpoints, stance=stance, actor=actor, grounds=grounds, event_token=token
    )


class TestTheKindIsGoverned:
    def test_the_kind_has_a_domain_and_one_required_covered_facet(self):
        assert stored.SEMANTIC_DOMAINS["coreference-attestation"] == stored.COREFERENCE_ATTESTATION_DOMAIN
        assert stored.COVERED_FACETS["coreference-attestation"] == (stored.COREFERENCE_ATTESTATION_FACET,)
        assert stored.WORLD_KINDS.index("coreference-attestation") == stored.WORLD_KINDS.index("act-report") - 1

    def test_the_endpoint_kinds_are_the_world_kinds_less_the_three_exclusions(self):
        assert set(stored.COREFERENCE_ENDPOINT_KINDS) == (
            set(stored.WORLD_KINDS) - {"coreference-attestation"} - set(EXCLUDED_MUTATION_KINDS)
        )
        assert stored.COREFERENCE_ENDPOINT_KINDS == (
            "proposition", "source-assertion", "assessment", "analysis-spec", "run",
            "verification", "dataset", "source", "retraction", "instrument-certification",
        )


class TestTheBuilder:
    def test_it_sorts_the_pair_digests_the_facet_and_carries_no_relations(self):
        node = attestation()
        assert node.kind == "coreference-attestation"
        assert node.facets[stored.COREFERENCE_ATTESTATION_FACET] == {
            "endpoints": [LEFT, RIGHT], "stance": 1, "actor": ACTOR,
            "grounds": "the same bytes", "event_token": "event-1",
        }
        # `_node` stamps every governed record; the facet set is exactly the two.
        assert set(node.facets) == {stored.COREFERENCE_ATTESTATION_FACET, "semantic-identity"}
        assert len(stored.stored_semantic_hash(node)) == 64  # the stamp is present and well-formed
        assert node.relations == []
        assert node.id == "coreference-attestation:" + v1.digest(
            stored.COREFERENCE_ATTESTATION_DOMAIN, node.facets[stored.COREFERENCE_ATTESTATION_FACET]
        )
        assert node.id == attestation(endpoints=(LEFT, RIGHT)).id

    def test_two_tokens_are_two_records(self):
        assert attestation(token="event-1").id != attestation(token="event-2").id

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"endpoints": (LEFT, LEFT)},
            {"endpoints": (LEFT,)},
            {"endpoints": (LEFT, "")},
            {"stance": 0},
            {"stance": 2},
            {"stance": True},
            {"grounds": ""},
            {"token": ""},
            {"grounds": NFD},
            {"endpoints": (LEFT, "dataset:" + NFD)},
        ],
    )
    def test_every_malformed_field_is_refused(self, kwargs):
        with pytest.raises(MalformedRecord):
            attestation(**kwargs)

    def test_an_empty_actor_is_the_actor_rule_s_own_error(self):
        with pytest.raises(ValueError):
            attestation(actor="")


class TestTheReader:
    def test_it_round_trips_the_builder(self):
        value = stored.coreference_attestation_value(attestation())
        assert value == stored.CoreferenceAttestation((LEFT, RIGHT), 1, ACTOR, "the same bytes", "event-1")

    @pytest.mark.parametrize(
        "edit",
        [
            lambda f: f.pop("event_token"),
            lambda f: f.update(extra=1),
            lambda f: f.update(endpoints=[RIGHT, LEFT]),
            lambda f: f.update(endpoints=[LEFT, LEFT]),
            lambda f: f.update(stance=-2),
            lambda f: f.update(stance=True),
            lambda f: f.update(grounds=NFD),
            lambda f: f.update(actor=""),
        ],
    )
    def test_every_malformed_facet_is_refused_naming_the_record(self, edit):
        node = attestation()
        edit(node.facets[stored.COREFERENCE_ATTESTATION_FACET])
        with pytest.raises(MalformedRecord, match=node.id):
            stored.coreference_attestation_value(node)

    def test_a_record_without_the_facet_is_refused(self):
        node = attestation()
        node.facets.clear()
        with pytest.raises(MalformedRecord):
            stored.coreference_attestation_value(node)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py -q -p no:cacheprovider`
Expected: FAIL — `AttributeError: module 'beliefs.stored' has no attribute 'coreference_attestation_node'` and the governance assertions fail.

- [ ] **Step 3: Promote the kind in both contract copies**

In `contracts/science/CONTRACT.yaml`, replace line 60 `  coreference-attestation: {}` with:

```yaml
  coreference-attestation:
    domain: science.coreference-attestation.v1
    facets: { coreference-attestation: { required: true, covered: true } }
```

and after line 96 (`  retraction: { shape: reader, reader: corpus.CorpusWriter._validated_retraction }`) add:

```yaml
  coreference-attestation: { shape: reader, reader: stored.coreference_attestation_value }
```

Then `cp contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml`. `test_shipped_base.py::test_the_packaged_copy_is_byte_identical_to_the_normative_file` holds the two together.

- [ ] **Step 4: Add the constants, value, reader and builder to `stored.py`**

Add `from beliefs import identifiers` beside the other `beliefs` imports (`identifiers.py` imports only `unicodedata`, so there is no cycle). Add to `__all__`, in alphabetical position: `"COREFERENCE_ATTESTATION_DOMAIN"`, `"COREFERENCE_ATTESTATION_FACET"`, `"COREFERENCE_ENDPOINT_KINDS"`, `"CoreferenceAttestation"`, `"coreference_attestation_node"`, `"coreference_attestation_value"`. Beside `RETRACTION_FACET = "retraction"` add:

```python
COREFERENCE_ATTESTATION_FACET = "coreference-attestation"
COREFERENCE_ATTESTATION_DOMAIN = "science.coreference-attestation.v1"
COREFERENCE_STANCES = (1, -1)
COREFERENCE_ENDPOINT_KINDS: tuple[str, ...] = (
    "proposition",
    "source-assertion",
    "assessment",
    "analysis-spec",
    "run",
    "verification",
    "dataset",
    "source",
    "retraction",
    "instrument-certification",
)
"""The kinds a coreference attestation may name as endpoints (slice 2 design
§2 item 4): the world kinds less the attestation itself and the two
boundary-minted occurrence records. `test_coreference_attestation.py` holds
this equal to `WORLD_KINDS - {coreference-attestation} - EXCLUDED_MUTATION_KINDS`."""
```

After `retraction_node` (its last line is `return _node("retraction", slug, title, {RETRACTION_FACET: facet}, relations)`), add:

```python
@dataclass(frozen=True)
class CoreferenceAttestation:
    """The stored facet as a value (world address ruling §5.1). Endpoints are
    sorted; every text member is NFC."""

    endpoints: tuple[str, str]
    stance: int
    actor: str
    grounds: str
    event_token: str


def _coreference_text(value: object, location: str) -> str:
    if type(value) is not str or not value:
        raise MalformedRecord(f"a coreference attestation {location} is non-empty text")
    problem = identifiers.not_a_canonical_identifier(value)
    if problem is not None:
        raise MalformedRecord(f"a coreference attestation {location} is not in NFC: {problem}")
    return value


def _coreference_fields(facet: Mapping[str, Any]) -> CoreferenceAttestation:
    if set(facet) != {"endpoints", "stance", "actor", "grounds", "event_token"}:
        raise MalformedRecord("a coreference attestation facet carries exactly endpoints, stance, actor, grounds and event_token")
    endpoints = facet["endpoints"]
    if type(endpoints) is not list or len(endpoints) != 2:
        raise MalformedRecord("a coreference attestation names exactly two endpoints")
    left = _coreference_text(endpoints[0], "endpoint")
    right = _coreference_text(endpoints[1], "endpoint")
    if left == right:
        raise MalformedRecord(f"{left!r} is named as both endpoints; a self-pair is a claim with no content")
    if left > right:
        raise MalformedRecord("a coreference attestation stores its endpoints sorted")
    stance = facet["stance"]
    if type(stance) is not int or stance not in COREFERENCE_STANCES:
        raise MalformedRecord("a coreference stance is +1 or -1")
    return CoreferenceAttestation(
        (left, right),
        stance,
        _coreference_text(facet["actor"], "actor"),
        _coreference_text(facet["grounds"], "grounds"),
        _coreference_text(facet["event_token"], "event token"),
    )


def coreference_attestation_value(node: Node) -> CoreferenceAttestation:
    """The facet reader the base contract names for the kind."""
    facet = _facet(node, COREFERENCE_ATTESTATION_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a coreference attestation carries a {COREFERENCE_ATTESTATION_FACET!r} facet")
    try:
        return _coreference_fields(facet)
    except MalformedRecord as caught:
        raise MalformedRecord(f"{node.id}: {caught}") from caught


def coreference_attestation_node(
    *,
    title: str,
    endpoints: Sequence[str],
    stance: int,
    actor: str,
    grounds: str,
    event_token: str,
) -> Node:
    if isinstance(endpoints, (str, bytes)) or not isinstance(endpoints, Sequence) or len(endpoints) != 2:
        raise MalformedRecord("a coreference attestation names exactly two endpoints")
    named = [_coreference_text(endpoint, "endpoint") for endpoint in endpoints]
    facet: dict[str, Any] = {
        "endpoints": sorted(named),
        "stance": stance,
        "actor": require_actor(actor),
        "grounds": grounds,
        "event_token": event_token,
    }
    _coreference_fields(facet)
    try:
        slug = v1.digest(COREFERENCE_ATTESTATION_DOMAIN, facet)
    except LoneSurrogate as exc:
        raise MalformedRecord("a coreference attestation identity field is not canonically encodable") from exc
    return _node("coreference-attestation", slug, title, {COREFERENCE_ATTESTATION_FACET: facet}, ())
```

- [ ] **Step 5: Run the new tests**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py -q -p no:cacheprovider`
Expected: PASS.

- [ ] **Step 6: Move the pins that held the deferral**

`python/tests/test_facet_declarations.py:39-44` — replace the loop with the one remaining deferred kind and a positive arm:

```python
    def test_the_one_deferred_kind_carries_no_domain_and_no_facets(self, base_contract):
        assert base_contract.kinds["instrument-certification"].domain is None
        assert base_contract.kinds["instrument-certification"].facets == {}
        assert base_contract.kinds["instrument-certification"].role == "world"

    def test_the_coreference_attestation_is_governed_since_slice_2(self, base_contract):
        kind = base_contract.kinds["coreference-attestation"]
        assert kind.domain == "science.coreference-attestation.v1"
        assert set(kind.facets) == {"coreference-attestation"}
        assert kind.facets["coreference-attestation"].required and kind.facets["coreference-attestation"].covered
```

`python/tests/test_base_contract.py:182-186` — the loop becomes `for kind in ("instrument-certification",):`.

`python/tests/test_world_build.py:977` — the parametrize becomes `["instrument-certification"]`; at `:1002-1019` replace the claimant's kind with `instrument-certification` (`Node(id="instrument-certification:c", kind="instrument-certification", title="c")`); at `:1036-1037` the expected set becomes `{"retraction", "run", "coreference-attestation"}`. Leave `test_absence_of_either_kind_is_an_ordinary_empty_enumeration` as it is: its corpus carries no attestation.

`python/tests/test_profile.py:46` — run `uv run --frozen python -c "from beliefs.contract.base import load_base_contract; from beliefs.profile import compile_profile; from pathlib import Path; print(compile_profile(load_base_contract(Path('src/beliefs/contracts/science/CONTRACT.yaml')), []).compiled_identity)"` and paste the printed digest over `daebbdee…`; rename the test `test_no_coordination_contract_preserves_the_slice_2_compiled_identity` and note in its docstring that the identity moved at slice 2 when the coreference kind gained its domain.

`ts/tests/declarations.test.ts:23` — replace `expect(base.kinds["coreference-attestation"].facets).toEqual({});` with `expect(base.kinds["coreference-attestation"].domain).toBe("science.coreference-attestation.v1");`.

- [ ] **Step 7: Run the moved pins and the gate**

Run: `uv run --frozen pytest tests/test_facet_declarations.py tests/test_base_contract.py tests/test_world_build.py tests/test_profile.py tests/test_shipped_base.py tests/test_facet_validation.py tests/test_permit.py tests/test_coordination.py tests/test_holdings_stored.py -q -p no:cacheprovider && (cd ../ts && npm test -- --run 2>&1 | tail -3) && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: all PASS, ruff and pyright clean. `test_a_governed_enumerated_kind_is_admitted` proves the capture no longer refuses the kind; the capture lift itself is Task 3.

- [ ] **Step 8: Commit**

```bash
tasks note beliefs-7d6bd2 "kind governed: domain, facet reader, builder, endpoint-kind set; deferral pins moved; compiled identity re-pinned"
tasks done beliefs-7d6bd2 "coreference-attestation is a governed kind with a builder and reader"
git add contracts python/src/beliefs/contracts python/src/beliefs/stored.py python/tests ts/tests tasks
git commit -m "feat(stored): govern the coreference attestation kind"
```

---

### Task 3: NFC agreement — the rule key, the captured value, the Unicode fixture, the capture lift

**Files:**
- Modify: `python/src/beliefs/world/rules_v1/coreference.py`
- Create: `python/src/beliefs/world/rules_v1/fixtures/coreference.unicode.yaml`
- Modify: `python/src/beliefs/world/derive.py:210-238` (`CapturedCoreference.__post_init__`), `python/src/beliefs/world/epoch.py:1180-1226` (`_captured_records`)
- Test: `python/tests/test_coreference_attestation.py`

**Interfaces:**
- Consumes: `stored.coreference_attestation_value`, `stored.coreference_attestation_node` (Task 2).
- Produces: `_captured_records` passing `coreference=derive.CapturedCoreference(...)` for every attestation node; the shipped `reduce_coreference` with an NFC-normalized key; `derive.CapturedCoreference` refusing non-NFC text with `ValueError`.

- [ ] **Step 1: `tasks start beliefs-e88cae`, then write the failing tests**

Append to `python/tests/test_coreference_attestation.py`:

```python
from pathlib import Path

from nodes.core.corpus import Corpus
from test_world_build import ALPHA, admitted_world, build, corpus_at, install_bindings, make_world, sample_nodes
from test_world_derive import reduce_with

from beliefs.world import derive, registry, rules


def endpoints_and(*attestations):
    """Two datasets and the attestations over them, as raw stored nodes."""
    return (
        stored.dataset_node("left", title="left", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]),
        stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]),
        *attestations,
    )


class TestTheRuleNormalizes:
    def test_the_unicode_fixture_ships_and_reduces_to_one_unit(self):
        bundle = next(b for b in rules.shipped_rule_bundles() if b.symbol == "reduce_coreference")
        assert any(name == "coreference.unicode.yaml" for name, _ in bundle.fixtures)

    def test_two_normalization_forms_of_one_grounds_are_one_unit(self):
        capture = {
            "coverage": ["corpus-a"],
            "records": [
                {
                    "corpus_id": "corpus-a", "address": f"coreference:{n}", "uid": f"uid-{n}",
                    "kind": "coreference-attestation", "deprecated_ids": [], "produces": [],
                    "retraction": None, "certification": None,
                    "coreference": {
                        "endpoints": ["address-a", "address-b"], "stance": 1, "actor": "alice",
                        "grounds": grounds, "event_token": f"event-{n}",
                    },
                }
                for n, grounds in ((1, NFC), (2, NFD))
            ],
        }
        produced = reduce_with("reduce_coreference", capture)
        assert produced == {"pairs": [{"endpoints": ["address-a", "address-b"], "balance": 1, "distinct_key_count": 1}]}


class TestTheCapturedValue:
    def test_non_nfc_text_is_refused(self):
        with pytest.raises(ValueError, match="NFC"):
            derive.CapturedCoreference(("a", "b"), 1, "alice", NFD, "event-1")


class TestTheCaptureLift:
    def test_a_stored_attestation_is_captured_and_reduced(self, tmp_path):
        alpha = corpus_at(tmp_path / "alpha", ALPHA, endpoints_and(attestation(), attestation(token="event-2")))
        world = make_world(tmp_path, alpha)
        world.admit(alpha, provenance=registry.Fresh())
        draft = build(world, (ALPHA,), install_bindings(world))
        captured = [r for r in draft.capture.corpora[0].records if r.kind == "coreference-attestation"]
        assert len(captured) == 2
        assert all(r.coreference == derive.CapturedCoreference((LEFT, RIGHT), 1, ACTOR, "the same bytes", t)
                   for r, t in zip(captured, ("event-1", "event-2")))
        assert dict(derive.coreference_map(draft.run("coreference-reduction")).pairs) == {(LEFT, RIGHT): (1, 1)}

    def test_grounds_rewritten_between_normalization_forms_is_refused_at_capture(self, tmp_path):
        from fixtures_cut4 import path_for

        node = attestation(grounds=NFC)
        alpha = corpus_at(tmp_path / "alpha", ALPHA, endpoints_and(node))
        path = path_for(alpha, node.id)
        text = path.read_text(encoding="utf-8")
        assert NFC in text and NFD not in text
        path.write_text(text.replace(NFC, NFD), encoding="utf-8")  # the probe: identity-equal bytes, reduction-distinct
        world = make_world(tmp_path, alpha)
        world.admit(alpha, provenance=registry.Fresh())
        with pytest.raises(MalformedRecord, match="NFC"):
            build(world, (ALPHA,), install_bindings(world))
```

`reduce_with(symbol, value)` is `test_world_derive.py:83`: it runs the shipped implementation through the store's own loader over a plain projection value. `path_for(root, node_id)` is `fixtures_cut4.py`'s, the same helper `raw_write` uses.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py -q -p no:cacheprovider -k "Normalizes or CapturedValue or CaptureLift"`
Expected: FAIL — no unicode fixture, `distinct_key_count` 2, no `ValueError`, `record.coreference is None`.

- [ ] **Step 3: Normalize the rule's key**

Rewrite `python/src/beliefs/world/rules_v1/coreference.py`'s body (keep the docstring; add one paragraph to it):

```python
Every key member is compared in NFC, the form `science.identity.v1` digests
under, so the reduction and every identity here agree about which strings are
one string; the boundary refuses non-NFC text and this is the rule's own half
of the same agreement (slice 2 design §2 item 2).
"""

import unicodedata


def _nfc(value):
    return unicodedata.normalize("NFC", value)


def reduce_coreference(capture):
    units = {}
    for record in capture["records"]:
        attestation = record["coreference"]
        if attestation is None:
            continue
        endpoints = tuple(sorted(_nfc(endpoint) for endpoint in attestation["endpoints"]))
        if len(endpoints) != 2 or endpoints[0] == endpoints[1]:
            raise ValueError("a coreference attestation names two distinct endpoints")
        stance = attestation["stance"]
        if type(stance) is not int or stance not in (1, -1):
            raise ValueError("a coreference stance is +1 or -1")
        units.setdefault(endpoints, set()).add((stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"])))
    return {
        "pairs": [
            {
                "endpoints": [left, right],
                "balance": sum(stance for stance, _actor, _grounds in distinct),
                "distinct_key_count": len(distinct),
            }
            for (left, right), distinct in sorted(units.items())
        ]
    }
```

Create `python/src/beliefs/world/rules_v1/fixtures/coreference.unicode.yaml`:

```yaml
# The NFC arm. Two submissions of one stance by one attester whose grounds
# differ only in Unicode normalization form — a precomposed é and an e with a
# combining acute. `science.identity.v1` digests both as one string, so the
# reduction counts them as one unit; a reduction comparing raw Python strings
# would publish 2 for both members while every identity stayed fixed.
input:
  coverage: ["corpus-a"]
  records:
    - corpus_id: "corpus-a"
      address: "coreference:one"
      uid: "uid-coreference-one"
      kind: "coreference-attestation"
      deprecated_ids: []
      produces: []
      retraction: null
      certification: null
      coreference:
        endpoints: ["address-a", "address-b"]
        stance: 1
        actor: "alice"
        grounds: "caf\u00E9"
        event_token: "event-1"
    - corpus_id: "corpus-a"
      address: "coreference:two"
      uid: "uid-coreference-two"
      kind: "coreference-attestation"
      deprecated_ids: []
      produces: []
      retraction: null
      certification: null
      coreference:
        endpoints: ["address-a", "address-b"]
        stance: 1
        actor: "alice"
        grounds: "cafe\u0301"
        event_token: "event-2"
expected:
  pairs:
    - endpoints: ["address-a", "address-b"]
      balance: 1
      distinct_key_count: 1
```

- [ ] **Step 4: Refuse non-NFC text in the captured value**

In `python/src/beliefs/world/derive.py` add `from beliefs import identifiers` beside the other `beliefs` imports, and in `CapturedCoreference.__post_init__` replace the four `_require_text(...)` calls on `left`, `right`, `self.actor`, `self.grounds`, `self.event_token` with `_require_canonical_text(...)`, defined beside `_require_text` at `:923`:

```python
def _require_canonical_text(value: object, location: str) -> str:
    text = _require_text(value, location)
    problem = identifiers.not_a_canonical_identifier(text)
    if problem is not None:
        raise ValueError(f"{location} is not in NFC: {problem}")
    return text
```

- [ ] **Step 5: Lift the facet at capture**

In `python/src/beliefs/world/epoch.py` `_captured_records`, after `facets = {node.id: _validated_retraction_facet(node) ...}` add:

```python
    attestations = {
        node.id: stored.coreference_attestation_value(node) for node in nodes if node.kind == "coreference-attestation"
    }
```

and in the `derive.CapturedRecord(...)` call, after the `retraction=(...)` argument, add:

```python
            coreference=(
                None
                if node.id not in attestations
                else derive.CapturedCoreference(
                    attestations[node.id].endpoints,
                    attestations[node.id].stance,
                    attestations[node.id].actor,
                    attestations[node.id].grounds,
                    attestations[node.id].event_token,
                )
            ),
```

Extend the docstring's governance paragraph with one sentence: "A `coreference-attestation` node is read through `stored.coreference_attestation_value`, and a malformed facet — non-NFC text included — raises `MalformedRecord` out of the capture, as a malformed retraction facet does."

- [ ] **Step 6: Extend the mutants' expectations**

`test_world_derive.py`'s `MUTATIONS` table pins, per defective reducer, exactly which fixtures refuse it (`test_a_defective_reducer_is_refused_by_exactly_the_named_fixtures`). The new fixture refuses two of them, confirmed by probe: the "duplicate coreference weighting" mutant keeps the event token in its key, so the two normalization-form submissions stay two units; the "wrong sorting" mutant compares raw strings, so they stay two units there too. Add `"coreference.unicode.yaml"` to both `refused_by` sets (`:937` and `:961-963`). No other mutant's set moves: the rest reduce `sample`-shaped inputs where the fixture's two records still fold to one.

- [ ] **Step 7: Run the tests and the rule suites**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py tests/test_world_rules.py tests/test_world_derive.py tests/test_world_build.py tests/test_world_receipts.py -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: PASS. `test_world_rules.py` installs the shipped bundle and runs its fixtures, the new one included.

- [ ] **Step 8: Commit**

```bash
tasks note beliefs-e88cae "rule key NFC-normalized with coreference.unicode.yaml; CapturedCoreference refuses non-NFC; _captured_records lifts the facet; two mutants' refused_by sets extended"
tasks done beliefs-e88cae "the reduction and the identity encoder agree about string equality; real attestations reduce"
git add python/src/beliefs/world python/tests/test_coreference_attestation.py tasks
git commit -m "feat(world): reduce stored coreference attestations under an NFC key"
```

---

### Task 4: The write seam — errors, `attest_coreference`, family and import clauses, permit inventories

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `RetractionGroundsMissing` at `:1008`)
- Modify: `python/src/beliefs/corpus.py` (imports near `:73-104`; `retract` ends at `:2131` — add the seam after it; `_refuse_family_kinds` at `:2590`; `_validate_import_bundle`'s retraction loop at `:2349-2354`; `OperationWrites` at `:2796`)
- Modify: `python/tests/test_permit_boundary.py:62` (`WRITE_ENTRY_POINTS`), `python/tests/test_permit_entry_points.py` (a `Case`)
- Test: `python/tests/test_coreference_attestation.py`

**Interfaces:**
- Consumes: Task 2's builder and reader; Task 3's capture.
- Produces: `errors.CoreferenceEndpointRefused(WriteRefused)` with `endpoint: str`, `reason: str`, `corpus_id: str | None`, class attribute `REASONS = ("self-pair", "kind-mismatch", "unresolved", "inadmissible-kind")`; `CorpusWriter.attest_coreference(record: Node, *, view: ReadView | WorldReadView | None = None) -> Node`; `CorpusWriter._controlled_coreference(record, attestation) -> None` (static, raises `MalformedRecord`); `CorpusWriter._validated_coreference(record) -> stored.CoreferenceAttestation` (static; reader plus rebuild, for import); `CorpusWriter._resolve_coreference_endpoints(record, attestation, view) -> None` (static); `OperationWrites.attest_coreference(record, *, view=None) -> OperationCommit`.

- [ ] **Step 1: `tasks start beliefs-4407ca`, then write the failing tests**

Append to `python/tests/test_coreference_attestation.py`:

```python
from authority import FULL, lacking, narrowed
from profiles import BASE
from test_corpus_write import Recorder
from test_world_receipts import corpora, hold_shipped, publish, world_over

from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    CoreferenceEndpointRefused,
    ImportRefused,
    PermitExceeded,
    ValidationRefused,
    WriteRefused,
)
from beliefs.world.view import open_world_view

PINNED = [{"name": "d", "digest": "sha256:" + "1" * 64}]


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    Recorder.plans.clear()
    w = CorpusWriter(tmp_path / "corpus", Recorder, authority=FULL, profile=BASE)
    w.add(stored.dataset_node("left", title="left", resources=PINNED))
    w.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
    return w


class TestTheSeam:
    def test_it_mints_and_touches_neither_endpoint(self, writer):
        before = {ref: writer.read_view.get(ref).model_dump() for ref in (LEFT, RIGHT)}
        minted = writer.attest_coreference(attestation())
        assert writer.read_view.get(minted.id).facets == minted.facets
        assert {ref: writer.read_view.get(ref).model_dump() for ref in (LEFT, RIGHT)} == before
        assert minted.relations == [] and writer.read_view.inbound(LEFT) == []

    def test_add_supersede_and_revise_refuse_the_kind(self, writer):
        with pytest.raises(WriteRefused, match="attest_coreference"):
            writer.add(attestation())
        with pytest.raises(WriteRefused, match="attest_coreference"):
            writer.revise(attestation())

    def test_the_permit_is_required_before_the_hold(self, tmp_path):
        w = CorpusWriter(tmp_path / "c", Recorder, authority=lacking(kinds=("coreference-attestation",)), profile=BASE)
        with pytest.raises(PermitExceeded):
            w.attest_coreference(attestation())

    def test_the_actor_is_bound(self, writer):
        with pytest.raises(ActorMismatch):
            writer.attest_coreference(attestation(actor="someone-else"))

    def test_a_raw_self_pair_reaches_its_own_refusal(self, writer):
        node = attestation()
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [LEFT, LEFT]
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(node)
        assert refused.value.reason == "self-pair" and refused.value.endpoint == LEFT

    def test_a_malformed_shape_is_a_validation_refusal(self, writer):
        node = attestation()
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["stance"] = 3
        with pytest.raises(ValidationRefused, match="coreference shape validation"):
            writer.attest_coreference(node)

    def test_the_controlled_rebuild_compares_id_facets_and_relations_and_accepts_a_fresh_uid(self, writer):
        node = attestation()
        node.relations.append(Relation(source=node.id, predicate="cites", target=LEFT))
        with pytest.raises(MalformedRecord, match="controlled stored shape"):  # spec §9: the rebuild is MalformedRecord, not a shape wrap
            writer.attest_coreference(node)
        assert writer.attest_coreference(attestation(token="fresh")).uid  # a uid minted by this construction

    @pytest.mark.parametrize(
        ("endpoints", "reason", "endpoint"),
        [
            (("discussion:d", "discussion:e"), "inadmissible-kind", "discussion:d"),
            (("act-report:a", "act-report:b"), "inadmissible-kind", "act-report:a"),
            (("coreference-attestation:a", "coreference-attestation:b"), "inadmissible-kind", "coreference-attestation:a"),
            ((LEFT, "dataset:missing"), "unresolved", "dataset:missing"),
        ],
    )
    def test_the_endpoint_refusals_over_the_corpus_view(self, writer, endpoints, reason, endpoint):
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation(endpoints=endpoints))
        assert (refused.value.reason, refused.value.endpoint) == (reason, endpoint)

    def test_two_kinds_are_a_category_error(self, writer):
        writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation(endpoints=(LEFT, "source:s")))
        assert refused.value.reason == "kind-mismatch"

    def test_a_retired_address_does_not_resolve_exactly(self, writer):
        # A raw rename through the `nodes` handle: the seam under test is the
        # attestation's, and no kernel rename exists yet (slice 2b).
        writer._corpus.rename(LEFT, "dataset:left-2")
        assert writer.read_view.resolve(LEFT) == "dataset:left-2"
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation())
        assert refused.value.reason == "unresolved" and refused.value.endpoint == LEFT

    def test_the_refusal_order_is_actor_then_self_pair_then_shape(self, writer):
        node = attestation(actor="someone-else")
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [LEFT, LEFT]
        with pytest.raises(ActorMismatch):
            writer.attest_coreference(node)


class TestTheSeamOverAWorldView:
    def test_a_pair_split_across_corpora_resolves_and_a_not_present_endpoint_names_its_corpus(self, tmp_path):
        left = stored.dataset_node("left", title="left", resources=PINNED)
        right = stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}])
        roots = corpora(tmp_path, {"a" * 32: (left,), "b" * 32: (right,)})
        world = world_over(tmp_path, roots)
        published = publish(world, ("a" * 32, "b" * 32), hold_shipped(world))
        view = open_world_view(world, published)
        w = CorpusWriter(roots["a" * 32], Recorder, authority=FULL, profile=BASE)
        assert w.attest_coreference(attestation(), view=view).id
        (roots["b" * 32] / "corpus.yaml").unlink()
        absent = open_world_view(world, published)
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            w.attest_coreference(attestation(token="event-2"), view=absent)
        assert (refused.value.reason, refused.value.endpoint, refused.value.corpus_id) == ("unresolved", RIGHT, "b" * 32)


class TestImport:
    def test_a_bundled_attestation_is_validated_and_resolved_over_the_union(self, tmp_path):
        # Import needs an operation port; `test_facet_seams.writer` builds the
        # port-backed writer and adopts a manifest, so use it rather than the
        # in-memory recorder above (which refuses with "no operation port").
        from test_facet_seams import IMPORT, writer as port_writer

        w = port_writer(tmp_path / "ported")
        w.add(stored.dataset_node("left", title="left", resources=PINNED))
        w.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
        good = attestation(actor="importer")
        w.import_bundle([good], **IMPORT)
        assert w.read_view.holds(good.id)
        bad = attestation(actor="importer", endpoints=(LEFT, "dataset:nowhere"), token="event-9")
        with pytest.raises(ImportRefused, match="dataset:nowhere"):
            w.import_bundle([bad], **IMPORT)
        malformed = attestation(actor="importer", token="event-8")
        malformed.facets[stored.COREFERENCE_ATTESTATION_FACET]["stance"] = 5
        with pytest.raises(ImportRefused, match=malformed.id):
            w.import_bundle([malformed], **IMPORT)
```

`Corpus.rename(old_id, new_id)` is the `nodes` handle's own rename (`nodes/core/corpus.py`), reached through the writer's `_corpus`; `IMPORT` is `test_facet_seams.py:19`'s keyword set for `import_bundle`.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py -q -p no:cacheprovider -k "Seam or Import"`
Expected: FAIL — `ImportError: cannot import name 'CoreferenceEndpointRefused'`.

- [ ] **Step 3: The error class**

In `python/src/beliefs/errors.py` after `RetractionGroundsMissing`:

```python
class CoreferenceEndpointRefused(WriteRefused):
    """A coreference attestation names an endpoint the seam refuses (world
    address ruling §5.1): the four typing refusals, one class, a closed reason."""

    REASONS = ("self-pair", "kind-mismatch", "unresolved", "inadmissible-kind")

    def __init__(self, message: str, *, endpoint: str, reason: str, corpus_id: str | None = None) -> None:
        if reason not in self.REASONS:
            raise ValueError(f"{reason!r} is not a coreference endpoint refusal reason")
        super().__init__(message)
        self.endpoint = endpoint
        self.reason = reason
        self.corpus_id = corpus_id
```

Add it to `errors.__all__` if the module keeps one.

- [ ] **Step 4: The seam, the family clause, the import clause**

In `python/src/beliefs/corpus.py` import `CoreferenceEndpointRefused` beside `RetractionGroundsMissing`. After `retract` (ends `return self._corpus.add(record)` at `:2131`) add:

```python
    def attest_coreference(self, record: Node, *, view: ReadView | WorldReadView | None = None) -> Node:
        """Mint one coreference attestation whose endpoints resolve exactly,
        touching neither endpoint (slice 2 design §4.1).

        `view` is where the endpoints resolve: this corpus by default, or a
        `WorldReadView` the caller opened **before** this call for a pair held
        in two corpora. The seam never opens one: opening takes every covered
        corpus's capture hold, and this writer holds its own.
        """
        self._authority.require("corpus-write", ("coreference-attestation",))
        with self._operation:
            self._require_pins_agree()
            self._refuse_family_kinds(record, admitted_kind="coreference-attestation")
            raw = record.facets.get(stored.COREFERENCE_ATTESTATION_FACET)
            if isinstance(raw, dict):
                if raw.get("actor") != self._authority.actor:
                    raise ActorMismatch(
                        f"{record.id}: the attestation names actor {raw.get('actor')!r}, "
                        f"not the bound {self._authority.actor!r}"
                    )
                endpoints = raw.get("endpoints")
                if isinstance(endpoints, list) and len(endpoints) == 2 and endpoints[0] == endpoints[1]:
                    raise CoreferenceEndpointRefused(
                        f"{record.id}: {endpoints[0]!r} is named as both endpoints; a self-pair is a claim with no content",
                        endpoint=str(endpoints[0]),
                        reason="self-pair",
                    )
            if record.kind != "coreference-attestation":
                raise ValidationRefused(f"{record.id}: attest_coreference accepts a stored coreference attestation only")
            try:
                attestation = stored.coreference_attestation_value(record)
            except MalformedRecord as caught:
                raise ValidationRefused(f"{record.id}: refused by coreference shape validation: {caught}") from caught
            self._controlled_coreference(record, attestation)  # MalformedRecord, outside the shape wrap (spec §9)
            self._resolve_coreference_endpoints(record, attestation, self._view if view is None else view)
            self._refuse(record, document_validated=True)
            return self._corpus.add(record)

    @staticmethod
    def _validated_coreference(record: Node) -> stored.CoreferenceAttestation:
        """The reader and the controlled rebuild, for the import door, where
        every failure is one `ImportRefused` anyway."""
        attestation = stored.coreference_attestation_value(record)
        CorpusWriter._controlled_coreference(record, attestation)
        return attestation

    @staticmethod
    def _controlled_coreference(record: Node, attestation: stored.CoreferenceAttestation) -> None:
        expected = stored.coreference_attestation_node(
            title=record.title,
            endpoints=attestation.endpoints,
            stance=attestation.stance,
            actor=attestation.actor,
            grounds=attestation.grounds,
            event_token=attestation.event_token,
        )
        if record.id != expected.id or record.facets != expected.facets or record.relations != expected.relations:
            raise MalformedRecord(f"{record.id}: coreference attestation does not match the controlled stored shape")

    @staticmethod
    def _resolve_coreference_endpoints(
        record: Node,
        attestation: stored.CoreferenceAttestation,
        view: ReadView | _ImportView | WorldReadView,
    ) -> None:
        """The four endpoint refusals, in the order slice 2 design §4.1 step 6
        states them; a record reaching here has two distinct endpoints."""
        from beliefs.world.read import NotPresent, Unknown
        from beliefs.world.view import WorldReadView as _WorldReadView

        kinds: list[str] = []
        for endpoint in attestation.endpoints:
            if endpoint.partition(":")[0] not in stored.COREFERENCE_ENDPOINT_KINDS:
                raise CoreferenceEndpointRefused(
                    f"{record.id}: {endpoint!r} is outside the admissible endpoint kinds {stored.COREFERENCE_ENDPOINT_KINDS}",
                    endpoint=endpoint,
                    reason="inadmissible-kind",
                )
            if view.resolve(endpoint) != endpoint:
                corpus_id: str | None = None
                detail = "does not resolve exactly"
                if isinstance(view, _WorldReadView):
                    located = view.locate(endpoint)
                    if isinstance(located, NotPresent):
                        corpus_id = view.corpus_of(endpoint)
                        detail = f"is recorded in {corpus_id}, a covered corpus with no carrier here"
                    elif isinstance(located, Unknown):
                        detail = "is unknown to this epoch"
                raise CoreferenceEndpointRefused(
                    f"{record.id}: {endpoint!r} {detail}", endpoint=endpoint, reason="unresolved", corpus_id=corpus_id
                )
            kinds.append(view.get(endpoint).kind)
        if kinds[0] != kinds[1]:
            raise CoreferenceEndpointRefused(
                f"{record.id}: endpoints are of two kinds ({kinds[0]!r}, {kinds[1]!r}); a coreference claim names one kind",
                endpoint=attestation.endpoints[1],
                reason="kind-mismatch",
            )
```

The two imports inside `_resolve_coreference_endpoints` are lazy because `world/view.py` imports `corpus.py`; `WorldReadView` is already a `TYPE_CHECKING` name here (`corpus.py:130-132`), which the annotations use.

In `_refuse_family_kinds` (`:2590`), after the retraction clause:

```python
        if node.kind == "coreference-attestation" and admitted_kind != "coreference-attestation":
            raise WriteRefused("a coreference attestation enters through attest_coreference")
```

In `_validate_import_bundle`, extend the loop at `:2349-2354`:

```python
        for record in records:
            if record.kind == "retraction":
                try:
                    self._validated_retraction(record)
                    self._resolve_retraction_target(record, union)
                except ScienceError as caught:
                    raise ImportRefused(str(caught), member=record.id) from caught
            elif record.kind == "coreference-attestation":
                try:
                    attestation = self._validated_coreference(record)
                    self._resolve_coreference_endpoints(record, attestation, union)
                except ScienceError as caught:
                    raise ImportRefused(str(caught), member=record.id) from caught
```

In `OperationWrites`, after `retract`:

```python
    def attest_coreference(self, record: Node, *, view: ReadView | WorldReadView | None = None) -> OperationCommit:
        return self._run(lambda: self._writer.attest_coreference(record, view=view))
```

and change its class docstring's "The seven session-mediated writes" to "The eight session-mediated writes".

- [ ] **Step 5: The permit inventories**

`python/tests/test_permit_boundary.py:62` — add `"corpus.py:CorpusWriter.attest_coreference": "corpus-write",` after the `retract` line.

`python/tests/test_permit_entry_points.py` — beside `_retract` add:

```python
def _mint_pair(writer):
    from beliefs import stored

    left = writer.add(stored.dataset_node("left", title="left", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]))
    right = writer.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
    return (left, right)


def _attest(authority, work):
    from beliefs import stored

    left, right = _STATE[work]["target"]
    return _writer(authority, work).attest_coreference(
        stored.coreference_attestation_node(
            title="coreference", endpoints=(left.id, right.id), stance=1, actor=authority.actor,
            grounds="one work", event_token="event-1",
        )
    )
```

and in the case table beside the `retract` `Case` (`:592`):

```python
    Case("corpus.py:CorpusWriter.attest_coreference", "corpus-write", ("coreference-attestation",), False, _prepare_corpus(_mint_pair), _attest, _corpus_probe),
```

- [ ] **Step 6: Run the tests and the gate**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_retract.py tests/test_import_bundle.py tests/test_corpus_write.py -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks note beliefs-4407ca "attest_coreference with the four endpoint refusals and actor bind; family clause; import clause; OperationWrites route; permit inventories"
tasks done beliefs-4407ca "the attestation mints through one seam and one import door"
git add python/src/beliefs/errors.py python/src/beliefs/corpus.py python/tests tasks
git commit -m "feat(corpus): mint coreference attestations through attest_coreference"
```

---

### Task 5: The session route and the design amendments it forces

**Files:**
- Modify: `python/src/beliefs/session/writer.py:369-372` (after `retract`), docstrings at `:87` and `:290`
- Modify: `python/tests/test_session_writer.py:284-289`
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (§4.2 items 2–3, §4.4), `docs/designs/2026-09-04-write-permits-design.md` (`:131` and the static inventory table `:268-273`), `docs/designs/2026-09-03-world-changing-families-design.md` (the "seven write" sentence)
- Test: `python/tests/test_coreference_attestation.py`

**Interfaces:**
- Consumes: `OperationWrites.attest_coreference` (Task 4).
- Produces: `ScopedWriter.attest_coreference(record: Node, *, view: ReadView | WorldReadView | None = None) -> Node`.

- [ ] **Step 1: `tasks start beliefs-0cefae`, then write the failing tests**

Append to `python/tests/test_coreference_attestation.py`:

```python
from test_session_writer import DIGEST, make_session

from beliefs.permit import RequiredCapabilities
from beliefs.session.writer import ScopedWriter

ATTESTING = RequiredCapabilities.for_kinds({"dataset", "coreference-attestation"}, {})


class TestTheSessionRoute:
    def test_attest_is_the_eighth_ledgered_route(self, tmp_path):
        session, _ = make_session(tmp_path)
        session.claim_invocation("A", "mint", DIGEST)
        writer = session.scoped(ATTESTING, "A")
        writer.add(stored.dataset_node("left", title="left", resources=PINNED))
        writer.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
        minted = writer.attest_coreference(attestation(actor=writer.actor))
        acts = session.invocation_acts("A")
        assert acts[-1].record_ids == ((minted.uid, minted.id),)  # `_record_act` ledgers (uid, id) pairs

    def test_the_facade_surface_is_the_eight_methods(self):
        public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
        assert "attest_coreference" in public
```

`make_session` (`test_session_writer.py:47`) returns the session and its recording ports; `RequiredCapabilities.for_kinds` is the constructor its `PROPOSITIONS` constant uses (`:83`).

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py -q -p no:cacheprovider -k SessionRoute`
Expected: FAIL — `AttributeError: 'ScopedWriter' object has no attribute 'attest_coreference'`.

- [ ] **Step 3: The route**

In `python/src/beliefs/session/writer.py` after `retract`:

```python
    def attest_coreference(self, record: Node, *, view: ReadView | WorldReadView | None = None) -> Node:
        minted = self._act(lambda: self._writer.operations.attest_coreference(record, view=view))
        assert minted is not None
        return minted
```

Import `ReadView` and `WorldReadView` under `TYPE_CHECKING` if the module does not already name them. Change "seven" to "eight" in the docstrings at `:87` and `:290` where they count the scoped methods.

`python/tests/test_session_writer.py:284-289` — rename the test `test_the_scoped_writer_exposes_the_eight_methods_the_routes_and_its_invocation` and add `"attest_coreference"` to the expected set.

- [ ] **Step 4: The design amendments**

Each is a dated blockquote inserted directly under the sentence it amends, never a rewrite of the sentence:

- `docs/designs/2026-09-05-writer-session-design.md` §4.2 item 2 ("The seven operation seams…") and item 3 ("All seven operation methods…"): `> **Amended 2026-09-10** (world resolution slice 2): an eighth seam, `attest_coreference`, joins on the same rule — refusals first, one commit seam, the `act` line after the commit. J1's "seven" is frozen text and stays; cut 24's results record states the eighth is covered there.` Add the same note under §4.4's static-inventory sentence.
- `docs/designs/2026-09-04-write-permits-design.md:131` (the `KIND_ACTS` row saying the kind is "minted only through `CorpusWriter.add`"): `> **Amended 2026-09-10:** `coreference-attestation` is minted only through `CorpusWriter.attest_coreference` (slice 2 design §4.1); `add` refuses it as it refuses a retraction.` In the static inventory table (`:268-273`) add a row after `CorpusWriter.retract`: `| `CorpusWriter.attest_coreference` | `corpus-write` | `coreference-attestation` | authored into the facet → the facet's `actor` must equal the bound actor, else `ActorMismatch` — added 2026-09-10 |`.
- `docs/designs/2026-09-03-world-changing-families-design.md` — under the sentence at `:41` of the writer-session design's citation and the families design's own "seven write" sentence (grep `seven` there), the same dated note naming the eighth.

- [ ] **Step 5: Run the tests, the design-corpus guard and the gate**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py tests/test_session_writer.py tests/test_designs_corpus.py -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
tasks note beliefs-0cefae "ScopedWriter.attest_coreference ledgered through _act; surface test at eight; three designs amended by dated note"
tasks done beliefs-0cefae "the attestation is the eighth scoped route"
git add python/src/beliefs/session python/tests docs/designs tasks
git commit -m "feat(session): route coreference attestations through the scoped writer"
```

---

### Task 6: Read-side tests over real attestations

**Files:**
- Modify: `python/tests/test_world_read.py:469-535` (the `COREFERENCE_ANCHOR` scaffold, `linked_nodes`, `coreference_world`) and the four `TestCoreferenceEdges` tests at `:537-760`
- Modify: `python/tests/test_world_receipts.py:475-483` (the docstring only)

**Interfaces:**
- Consumes: `stored.coreference_attestation_node` (Task 2); the capture lift (Task 3).
- Produces: `coreference_world(tmp_path, placement, coverage, *, also_configured=())` unchanged in signature, now building over the shipped rule; `linked_nodes(slug)` returning three datasets and two attestations.

- [ ] **Step 1: `tasks start beliefs-413c84`, then replace the scaffold**

Delete `COREFERENCE_ANCHOR`, `COREFERENCE_ARM` and `coreference_successor` (`:478-495`) and the comment block above them. Replace `linked_nodes` and `coreference_world`:

```python
def linked_nodes(slug: str) -> tuple[Node, ...]:
    """Three datasets and two attestations, `a ~ b` and `a ~ c`: a
    three-endpoint chain the reduction turns into two pairs."""
    a, b, c = (
        stored.dataset_node(f"{slug}", title=f"dataset {slug}", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]),
        stored.dataset_node(f"{slug}-b", title=f"dataset {slug} b", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]),
        stored.dataset_node(f"{slug}-c", title=f"dataset {slug} c", resources=[{"name": "d", "digest": "sha256:" + "3" * 64}]),
    )
    attest = lambda left, right, token: stored.coreference_attestation_node(  # noqa: E731
        title="coreference", endpoints=(left.id, right.id), stance=1, actor="alice", grounds="one work", event_token=token
    )
    return (a, b, c, attest(a, b, f"{slug}-1"), attest(a, c, f"{slug}-2"))


def coreference_world(
    tmp_path: Path,
    placement: dict[str, tuple[Node, ...]],
    coverage: tuple[str, ...],
    *,
    also_configured: tuple[Path, ...] = (),
):
    """A world publishing a non-empty, validating coreference reduction over
    stored attestations and the shipped rule."""
    roots = corpora(tmp_path, placement)
    world = world_over(tmp_path, roots, also_configured=also_configured)
    bindings = hold_shipped(world)
    return world, bindings, roots, publish(world, coverage, bindings)
```

Then in `TestCoreferenceEdges` replace every `"run:a"` with `"dataset:a"`, every `"dataset:a"` that was the second member of a pair with `"dataset:a-b"`, and every `"run:a-two"` with `"dataset:a-c"`; the expected `pairs_of` becomes `[["dataset:a", "dataset:a-b"], ["dataset:a", "dataset:a-c"]]` and the expected expansion `("dataset:a-b", "dataset:a-c")`. In `test_edge_indeterminate_names_missing_span_and_receipt_outcome` (`:679-747`) the test removes the coreference binding to reach `unresolvable` and then reinstalls one before its wider-coverage publication; the line `rules.install_rule_binding(world, coreference_successor())` becomes a reinstall of the shipped bundle, so that publication does not raise `RuleNotHeld`:

```python
        rules.install_rule_binding(
            world, next(bundle for bundle in rules.shipped_rule_bundles() if bundle.symbol == "reduce_coreference")
        )
```

Keep every assertion otherwise.

- [ ] **Step 2: Run the module**

Run: `uv run --frozen pytest tests/test_world_read.py -q -p no:cacheprovider`
Expected: PASS with the same test count as before.

- [ ] **Step 3: The receipts docstring**

`test_world_receipts.py:475-483` — the docstring's "The sample corpora carry no coreference attestation, so the reduction over this coverage is empty" stays true (the sample corpora are `sample_nodes`, which mint none); append one sentence: "Populated refutations — an omitted attestation, a wrong balance over a real one — are cut 24's arms in `test_coreference_attestation.py` and its acceptance module."

- [ ] **Step 4: Populated refutation, at unit scale**

Append to `python/tests/test_coreference_attestation.py`:

```python
from test_world_receipts import document, outcomes, repackage

from beliefs.world import read


class TestPopulatedReceipts:
    def two_corpus_world(self, tmp_path):
        left = stored.dataset_node("left", title="left", resources=PINNED)
        right = stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}])
        plus = attestation(actor="alice", token="a-1")
        minus = attestation(actor="bob", stance=-1, token="b-1")
        roots = corpora(tmp_path, {"a" * 32: (left, right, plus), "b" * 32: (minus,)})
        world = world_over(tmp_path, roots)
        return world, roots, hold_shipped(world)

    def test_an_omitted_attestation_and_a_wrong_balance_refute_and_move_no_digest(self, tmp_path):
        world, _roots, bindings = self.two_corpus_world(tmp_path)
        published = publish(world, ("a" * 32, "b" * 32), bindings)
        assert document(published, "coreference-map.yaml") == {
            "pairs": [{"endpoints": [LEFT, RIGHT], "balance": 0, "distinct_key_count": 2}]
        }
        assert read.coreference_edge(world, published, LEFT, RIGHT).state == "inactive"
        for wrong in ({"pairs": []}, {"pairs": [{"endpoints": [LEFT, RIGHT], "balance": 1, "distinct_key_count": 1}]}):
            receipt = dict(document(published, "coreference-receipt.yaml"),
                           subject=derive.subject_identity("coreference-reduction", wrong))
            claimed = repackage(world, published, {"coreference-map.yaml": wrong, "coreference-receipt.yaml": receipt})
            assert read.validate_receipt(world, claimed, "coreference-reduction").outcome == "refuted"
            assert read.coreference_edge(world, claimed, LEFT, RIGHT).state == "indeterminate"
            assert (
                claimed.receipts["producer-receipt.yaml"].subject_identity
                == published.receipts["producer-receipt.yaml"].subject_identity
            )  # the belief input (test_world_read.py:448 pins this member as belief_input_identity's answer)
            assert outcomes(world, claimed)["producer"] == "validated"

    def test_coverage_bounds_the_balance_and_the_narrower_epoch_is_indeterminate_over_the_wider_world(self, tmp_path):
        world, _roots, bindings = self.two_corpus_world(tmp_path)
        narrow = publish(world, ("a" * 32,), bindings)
        assert document(narrow, "coreference-map.yaml")["pairs"][0]["balance"] == 1
        answer = read.coreference_edge(world, narrow, LEFT, RIGHT)
        assert (answer.state, answer.missing_coverage) == ("indeterminate", ("b" * 32,))
```

`Epoch.receipts` is the member-name-keyed mapping of receipt carriers (`epoch.py:602`).

- [ ] **Step 5: Run, gate, commit**

Run: `uv run --frozen pytest tests/test_coreference_attestation.py tests/test_world_read.py tests/test_world_receipts.py -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: PASS.

```bash
tasks note beliefs-413c84 "test_world_read binds real attestations under the shipped rule; populated refutation and coverage arms at unit scale"
tasks done beliefs-413c84 "the read side is exercised over a populated reduction"
git add python/tests tasks
git commit -m "test(world): read coreference edges over stored attestations"
```

---

### Task 7: Durable acceptance arms and the cut 24 declarations

**Files:**
- Create: `python/tests/acceptance/test_coreference_acceptance.py`
- Create: `python/tests/acceptance/n2_arms_cut24.py`
- Create: `python/tests/acceptance/test_n2_cut24.py`

**Interfaces:**
- Consumes: Task 1's five units, freeze sha and sha256; every seam, capture and rule change above.
- Produces: `CUT24_ARMS` (18 arms), `DECLARATION_UNITS = ("W15", "X12", "W8a", "M3", "W4")`, `unit_of`, `CO_CITED = ()`.

- [ ] **Step 1: `tasks start beliefs-ee18db`, then write the durable acceptance module**

`test_coreference_acceptance.py` opens with the docstring `"""Cut 24 over registered roots and the composition root's durable executors."""` and reuses `test_world_view_acceptance.py`'s `durable_world` fixture shape (`:46-121` there): copy that fixture, rename the `mkdtemp` prefixes to `cut24-`, and drop the S7 staging branch (no assessments here). Add a `pair` fixture minting two datasets `dataset:left` and `dataset:right` in corpus A through the durable writer, and a helper:

```python
def attest(writer, *, left=LEFT, right=RIGHT, stance=1, grounds="one work", token, view=None):
    return writer.attest_coreference(
        stored.coreference_attestation_node(
            title="coreference", endpoints=(left, right), stance=stance, actor=writer.authority.actor,
            grounds=grounds, event_token=token,
        ),
        view=view,
    )


def republish(world, coverage):
    return publish(world, coverage, hold_shipped(world))


def balance(published, left=LEFT, right=RIGHT):
    pairs = {tuple(p["endpoints"]): (p["balance"], p["distinct_key_count"]) for p in document(published, "coreference-map.yaml")["pairs"]}
    return pairs.get((left, right))
```

One test per arm of spec §10, named and asserting exactly as the spec states:

```
test_the_four_endpoint_refusals_durably                                   (W15 endpoints, plus not-present and retired over a world view)
test_the_balance_sequence_is_attester_symmetric_and_retains_every_record_durably   (W15 balance: +1 human-a, +1 agent-b → 2 active; swap → identical map bytes; -1 → 1 active, 3 records; second -1 → 0 inactive, 4 records)
test_exact_duplicates_add_no_weight_and_different_grounds_do_durably      (W15 duplicates: ten tokens → ten records, balance 1 count 1 after the first and after all; different grounds → 2, 2)
test_closure_rewrites_nothing_durably                                     (W15 closure: retraction target bytes, belief_input_digest over a closure naming LEFT, inbound/closure/producers before == after)
test_coverage_bounds_the_balance_and_no_epoch_is_unspellable_durably      (W15 coverage: {A,B} → 1 active; {A} → 2; wider world naming {A} → indeterminate missing (B,); expansion raises naming B; `inspect.signature(read.coreference_edge).parameters["published"].default is inspect.Parameter.empty` and the same for expand)
test_the_three_non_validated_outcomes_refuse_expansion_durably            (W15 receipts, in the spec's order: refuted, malformed, then un-hold → unresolvable)
test_an_unmounted_covered_corpus_still_contributes_to_the_published_balance_durably   (W15 absent is not empty: map reads 1; edge indeterminate/unresolvable; remount → active)
test_coreference_between_retractions_closes_no_route_durably               (M3 and W15 cycle: both retractions byte-unchanged; standing unchanged; no graph edge; the validator and forced-verdict checks of cut 5 re-run with the edge active; the raw-cycle audit classification of cut 18 re-run)
test_membership_follows_coverage_durably                                   (X12 membership)
test_omission_and_a_wrong_balance_refute_and_move_no_digest_durably        (X12 / W8a omission and wrong balance; producer, retraction and certification receipts stay validated)
test_unresolvable_for_an_unmounted_and_for_a_moved_named_state_durably     (X12 unresolvable, both cases)
test_the_digest_boundary_holds_on_one_coverage_durably                     (W8a coverage as restated: same coverage, two more attestations in B → one producer snapshot identity, one digest, different maps; the two-coverage pair carries two digests)
test_no_operation_retires_an_address_on_coreference_grounds_durably        (W4: endpoints byte-unchanged and live; no deprecated_ids entry; the inventory has no merge member and no member writes one)
test_lifecycle_treats_an_attestation_as_a_retraction_s_peer_durably        (move → balance unchanged; delete → balance moves and root.audit_log records the removal; consolidate two replicas → one address, balance unchanged; add refuses; a malformed bundled attestation refuses naming the member)
```

The inventory assertion for W4 is literal:

```python
from beliefs import relocation
from beliefs.corpus import CorpusWriter, OperationWrites

INVENTORY = ("add", "retract", "attest_coreference", "supersede", "revise", "delete", "mint_coordination", "revise_coordination")
assert not any(name == "merge" for name in dir(OperationWrites))
assert not hasattr(CorpusWriter, "merge") and not hasattr(relocation, "merge")
assert set(INVENTORY) <= {n for n in dir(OperationWrites) if not n.startswith("_")}
```

For the cut 5 and cut 18 re-runs inside the cycle test, call the same helpers those arms use: `acceptance/test_n2_cut5.py::test_import_consumes_a_forced_cycle_verdict`'s body for the forced verdict, and `test_local_standing.py::test_raw_written_cycle_shape_is_malformed_before_evaluation`'s construction for the raw cycle, each after attesting coreference between the two retractions through a world view over both corpora.

- [ ] **Step 2: Run the module on the certified volume**

Run: `uv run --frozen pytest tests/acceptance/test_coreference_acceptance.py -q -p no:cacheprovider`
Expected: PASS, 14 tests, no skip. A `UncertifiedVolume` error means the work directory is not the certified one: set `SCIENCE_CUT4_ROOT` to the certified volume beside the checkout and rerun; never waive.

- [ ] **Step 3: Write the declarations**

`n2_arms_cut24.py`, on `n2_arms_cut23.py`'s shape:

```python
"""Cut 24's five frozen declaration units and their source sabotages — one arm
per sabotage site the cut document §5 item 4 names."""

from n2_arms import Arm, Sabotage

_CORPUS = "corpus.py"
_STORED = "stored.py"
_EPOCH = "world/epoch.py"
_RULE = "world/rules_v1/coreference.py"
_READ = "world/read.py"
_DERIVE = "world/derive.py"
_A = "acceptance/test_coreference_acceptance.py"
_U = "test_coreference_attestation.py"

DECLARATION_UNITS: tuple[str, ...] = ("W15", "X12", "W8a", "M3", "W4")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    matches = [
        unit
        for unit in DECLARATION_UNITS
        if row == unit or (row.startswith(unit) and len(row) == len(unit) + 1 and row[-1].islower())
    ]
    return max(matches, key=len)
```

Then `CUT24_ARMS`, one `Arm` per site; the `before` strings are the exact lines Tasks 2–4 wrote:

| row | sabotage (module: before → after) | checks |
|---|---|---|
| W15a | `_CORPUS`: `            if endpoint.partition(":")[0] not in stored.COREFERENCE_ENDPOINT_KINDS:\n` → `            if endpoint.partition(":")[0] not in (*stored.COREFERENCE_ENDPOINT_KINDS, *stored.PROSE_KINDS):\n` | `_A::test_the_four_endpoint_refusals_durably`, `_U::TestTheSeam::test_the_endpoint_refusals_over_the_corpus_view` |
| W15b | `_CORPUS`: `                endpoints = raw.get("endpoints")\n                if isinstance(endpoints, list) and len(endpoints) == 2 and endpoints[0] == endpoints[1]:\n` → `                endpoints = raw.get("endpoints")\n                if False:\n` | `_U::TestTheSeam::test_a_raw_self_pair_reaches_its_own_refusal` |
| W15c | `_CORPUS`: `            if view.resolve(endpoint) != endpoint:\n` → `            if view.resolve(endpoint) is None:\n` | `_U::TestTheSeam::test_a_retired_address_does_not_resolve_exactly` |
| W15d | `_CORPUS`: `        if kinds[0] != kinds[1]:\n            raise CoreferenceEndpointRefused(\n` → `        if False and kinds[0] != kinds[1]:\n            raise CoreferenceEndpointRefused(\n` | `_U::TestTheSeam::test_two_kinds_are_a_category_error` |
| W15e | `_CORPUS`: `                if raw.get("actor") != self._authority.actor:\n` → `                if False and raw.get("actor") != self._authority.actor:\n` | `_U::TestTheSeam::test_the_actor_is_bound` |
| W15f | `_CORPUS`: `        if node.kind == "coreference-attestation" and admitted_kind != "coreference-attestation":\n            raise WriteRefused("a coreference attestation enters through attest_coreference")\n` → `        pass\n` | `_U::TestTheSeam::test_add_supersede_and_revise_refuse_the_kind` |
| W15g | `_CORPUS`: `        if record.id != expected.id or record.facets != expected.facets or record.relations != expected.relations:\n            raise MalformedRecord(f"{record.id}: coreference attestation does not match` → `        if record.id != expected.id:\n            raise MalformedRecord(f"{record.id}: coreference attestation does not match` | `_U::TestTheSeam::test_the_controlled_rebuild_compares_id_facets_and_relations_and_accepts_a_fresh_uid` |
| W15h | `_EPOCH`: `                if node.id not in attestations\n                else derive.CapturedCoreference(\n` → `                if True\n                else derive.CapturedCoreference(\n` | `_A::test_the_balance_sequence_is_attester_symmetric_and_retains_every_record_durably`, `_U::TestTheCaptureLift::test_a_stored_attestation_is_captured_and_reduced` |
| W15i | `_RULE`: the contiguous block from `        units.setdefault(endpoints, set()).add((stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"])))\n` through `                "balance": sum(stance for stance, _actor, _grounds in distinct),\n` → the same block with the key `(stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"]), attestation["event_token"])` and the sum `sum(stance for stance, _actor, _grounds, _token in distinct)` — a runnable reducer that counts the token, so the duplicates arm reads 10 rather than crashing on unpacking | `_A::test_exact_duplicates_add_no_weight_and_different_grounds_do_durably` |
| W15j | `_RULE`: `def _nfc(value):\n    return unicodedata.normalize("NFC", value)\n` → `def _nfc(value):\n    return value\n` | `_U::TestTheRuleNormalizes::test_two_normalization_forms_of_one_grounds_are_one_unit` |
| W15k | `_READ`: `    missing = tuple(\n        corpus_id for corpus_id in registry._live_corpus_ids(world.registry()) if corpus_id not in covered\n    )\n` → `    missing = ()\n` | `_A::test_coverage_bounds_the_balance_and_no_epoch_is_unspellable_durably` |
| W15l | `_STORED`: `    return _node("coreference-attestation", slug, title, {COREFERENCE_ATTESTATION_FACET: facet}, ())\n` → `    return _node("coreference-attestation", slug, title, {COREFERENCE_ATTESTATION_FACET: facet}, [Relation(source=f"coreference-attestation:{slug}", predicate="cites", target=endpoint) for endpoint in facet["endpoints"]])\n` | `_A::test_closure_rewrites_nothing_durably`, `_U::TestTheBuilder::test_it_sorts_the_pair_digests_the_facet_and_carries_no_relations` |
| W15m | `_CORPUS`: `            elif record.kind == "coreference-attestation":\n                try:\n                    attestation = self._validated_coreference(record)\n` → `            elif False:\n                try:\n                    attestation = self._validated_coreference(record)\n` | `_U::TestImport::test_a_bundled_attestation_is_validated_and_resolved_over_the_union` |
| X12a | `_READ`: `    if epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n` → `    if kind != "coreference-reduction" and epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n` | `_A::test_omission_and_a_wrong_balance_refute_and_move_no_digest_durably`, `_U::TestPopulatedReceipts::test_an_omitted_attestation_and_a_wrong_balance_refute_and_move_no_digest` |
| X12b | `_DERIVE`: `    return producers[0].subject_identity\n` (in `belief_input_identity`) → `    return v1.digest(PRODUCER_SNAPSHOT_DOMAIN, [producers[0].subject_identity, *sorted(r.subject_identity for r in receipts if r.kind == "coreference-reduction")])\n` — a well-formed versioned domain, so the sabotaged digest runs and moves with the coreference map instead of raising `MalformedDomain` | `_A::test_the_digest_boundary_holds_on_one_coverage_durably` |
| W8aa | `_EPOCH`: `    covered = tuple(sorted(coverage))\n    config = world.config\n    world._state.registry = registry._scan_registry(config.world_root)\n` (in `_locked_resolve_coverage`) → `    config = world.config\n    world._state.registry = registry._scan_registry(config.world_root)\n    covered = tuple(sorted(coverage | {record.corpus_id for record in world._state.registry.admissions}))\n` — the coverage bound: every admitted corpus is captured whatever the declaration says | `_A::test_the_digest_boundary_holds_on_one_coverage_durably`, `_U::TestPopulatedReceipts::test_coverage_bounds_the_balance_and_the_narrower_epoch_is_indeterminate_over_the_wider_world` |
| M3a | `_CORPUS`: `        if stored_node.kind != "retraction":\n            continue\n        retraction = view.get(stored_node.id)\n` (in `standing_in_local_view`) → `        if stored_node.kind not in ("retraction", "coreference-attestation"):\n            continue\n        retraction = view.get(stored_node.id)\n` | `_A::test_coreference_between_retractions_closes_no_route_durably` |
| W4a | `_CORPUS`: `    def retract(self, record: Node) -> OperationCommit:\n        return self._run(lambda: self._writer.retract(record))\n` → the same followed by `\n    merge = retract\n` | `_A::test_no_operation_retires_an_address_on_coreference_grounds_durably` |

Every `before` must occur exactly once in its module; `test_each_sabotage_names_one_real_source_site` enforces it. If `belief_input_identity`'s `return` line is shared with another function's, widen X12b's `before` to include its preceding `raise ValueError(...)` line.

- [ ] **Step 4: Write the guard**

Copy `test_n2_cut23.py` to `test_n2_cut24.py` and change: the docstring to cut 24; import `CUT23_ARMS` from `n2_arms_cut23` and add it to `PRIOR_ARMS`; import `CO_CITED, CUT24_ARMS, DECLARATION_UNITS, unit_of` from `n2_arms_cut24`; drop `_LIVE_SABOTAGES` (none are needed at freeze; add one only if a later commit moves a site, dated); `FROZEN_CUT` to `2026-09-10-conformance-cut-24.md`; `CUT24_FREEZE_COMMIT` and `CUT24_FROZEN_SHA256` from Task 1's note; add `"python/tests/acceptance/n2_arms_cut23.py": "<the commit that last touched it on main, git log -1 --format=%h -- python/tests/acceptance/n2_arms_cut23.py>"` to `FROZEN_PRIOR_CUT_FILES`; `mktemp("n2-cut24")`; the inventory test:

```python
def test_the_inventory_is_exactly_the_five_frozen_units() -> None:
    assert DECLARATION_UNITS == ("W15", "X12", "W8a", "M3", "W4")
    assert {unit_of(arm.row) for arm in CUT24_ARMS} == set(DECLARATION_UNITS)
    assert len(CUT24_ARMS) == 18
```

- [ ] **Step 5: Run the guard**

Run: `uv run --frozen pytest tests/acceptance/test_n2_cut24.py -q -p no:cacheprovider`
Expected: PASS — every check resolves and passes clean, every arm fails under its own sabotage, the freeze pin holds, prior declarations are frozen. A sabotage that does not apply (`before` matched 0 or 2 times) is reported by name; fix the string, never the code.

- [ ] **Step 6: Commit**

```bash
tasks note beliefs-ee18db "14 durable arms, 18 declared N2 arms over 5 units; guard green on the certified volume"
tasks done beliefs-ee18db "cut 24's arms and declarations"
git add python/tests/acceptance tasks
git commit -m "test(cut24): durable coreference arms and the N2 declarations"
```

---

### Task 8: The runner, the guard sweeps and the row notes

**Files:**
- Create: `python/tools/cut24_acceptance.py`
- Modify: `python/tools/roadmap_status.py:54` (add cut 24's row)
- Modify: `docs/designs/2026-08-02-world-addressing-design.md:1512` (W8a's cell, appended note), `docs/designs/2026-08-08-world-address-ruling.md:471` (§5.5 sentence, appended note), `docs/designs/2026-09-05-facet-contracts-design.md:211-216`, `docs/designs/2026-08-20-world-index-slice-2-design.md:819-826`, `docs/guide/identity-world-and-change.md:168-176`

- [ ] **Step 1: `tasks start beliefs-edf1ad`, then write the runner**

Copy `python/tools/cut23_acceptance.py` to `cut24_acceptance.py` and change: the docstring to "Run cut 24 after cut 23"; `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut24-acceptance"`; `PREFIX_RUNNERS = ("cut23_acceptance.py",)`; `PHASE_MODULES = ("test_coreference_acceptance.py", "test_n2_cut24.py")`; the env var `SCIENCE_CUT24_ROOT`; the probe's actor `cut24-probe`; `cut_environment`'s range to `range(4, 25)`; `run_prefix`'s env key `SCIENCE_CUT23_ROOT`; every `cut-23`/`cut23` banner string to 24; `declared_accounting` importing from `n2_arms_cut24`.

- [ ] **Step 2: The status tool's row**

In `python/tools/roadmap_status.py` after line 54 add:

```python
    24: ("conformance-cut-24-results §2", "W15, W4", "X12, W8a, M3"),
```

matching the tuple shape of the rows above it (source, closed rows, partial rows).

- [ ] **Step 3: The row notes and the guide**

Each a dated addition; no existing words are removed:

- `2026-08-02-world-addressing-design.md:1512`, at the end of W8a's cell: ` **Read 2026-09-10 (cut 24, slice 2 design §5):** the coreference coverage arm's "`belief_input_digest` is unchanged" clause is unsatisfiable as stated — `coverage` is a member of the producer snapshot's projection (`derive.ProducerSnapshot.projection`), so narrowing the corpus set moves the digest, which is this row's own producers clause (c). The arm is read as the digest-boundary claim it can carry: over one coverage, two epochs whose coreference maps differ carry one digest.`
- `2026-08-08-world-address-ruling.md:471`, after "…the property W8a's coverage arm asserts for the producers map, here with the belief consequence absent.": `*(Read 2026-09-10: the producers-map property is that the digest **moves** with coverage; the coreference map's property is that it contributes nothing to the digest, asserted on one coverage — cut 24.)*`
- `2026-09-05-facet-contracts-design.md:211-216`: under the sentence about the two deferred kinds, `> **2026-09-10:** `coreference-attestation` gained its domain and facet at world resolution slice 2; `instrument-certification` is the one kind still deferred.`
- `2026-08-20-world-index-slice-2-design.md:819-826`: the same note under "Two enumerated kinds remain prose".
- `docs/guide/identity-world-and-change.md:168-176`: after "Cut 23 adds …", add "Cut 24 makes the coreference attestation a governed, mintable kind and reduces stored attestations into the published balance; snapshot/import and audit callers, and view evaluation remain open." and adjust the following sentence so it no longer lists coreference as open.

- [ ] **Step 4: Run the guard sweeps**

Run: `uv run --frozen pytest tests/test_frozen_guards.py tests/test_arm_staleness.py tests/test_designs_corpus.py -q -p no:cacheprovider`
Expected: PASS — `test_n2_cut24.py` is now live through the new runner; every pin holds; every arm applies once; the staleness baseline is the tree's.

- [ ] **Step 5: Run the whole runner**

Run: `uv run --frozen python tools/cut24_acceptance.py 2>&1 | tee ../.cut24-acceptance/run.log | tail -30`
Expected: exit 0; the prefix chain through cut 23 green; both phases green; the final line `declared arms: 18 (= 5 declaration units; 5 guarantee rows)`.

- [ ] **Step 6: Commit**

```bash
tasks note beliefs-edf1ad "runner cut24_acceptance.py green over the cut 23 prefix; roadmap_status row; W8a and ruling notes; guide"
tasks done beliefs-edf1ad "the cut 24 runner and the row notes"
git add python/tools docs tasks
git commit -m "test(cut24): the acceptance runner, and the coverage-arm reading recorded on W8a"
```

---

### Task 9: Discharge

**Files:**
- Create: `docs/plans/<date>-conformance-cut-24-results.md` and `docs/plans/<date>-conformance-cut-24-run/{certified.log,check.log,test.log}` — the date is the day the gate runs; every `2026-09-XX` below is that date
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Updated`, the `Current state` heading date, the `world-resolution` row: W15 and W4 leave it, X12/W8a/M3 keep only their non-coreference arms, and W1, W2, W5a are named to `beliefs-b7994b`), `docs/plans/2026-08-29-implementation-roadmap.md` (whole rewrite per its header rule: `**Ranked at:** cut 24`, Appendix A regenerated by `python/tools/roadmap_status.py`, Appendix B rows narrowed, W1/W2/W5a's row naming slice 2b), `docs/designs/2026-09-10-conformance-cut-24.md` (`Status:` and §1's first sentence only), `docs/superpowers/specs/2026-09-10-world-resolution-slice-2-design.md` (`Status:` → discharged at cut 24, dated), this plan (`Status:`)

- [ ] **Step 1: `tasks start beliefs-e963b9`, then run the repository gates and retain the transcripts**

From the repository root:

```bash
mkdir -p docs/plans/2026-09-XX-conformance-cut-24-run
(cd python && uv run --frozen python tools/cut24_acceptance.py) > docs/plans/2026-09-XX-conformance-cut-24-run/certified.log 2>&1; echo "exit $?"
just check > docs/plans/2026-09-XX-conformance-cut-24-run/check.log 2>&1; echo "exit $?"
just test  > docs/plans/2026-09-XX-conformance-cut-24-run/test.log  2>&1; echo "exit $?"
grep -E "^[0-9]+ passed" docs/plans/2026-09-XX-conformance-cut-24-run/test.log
```
Expected: three `exit 0`; the pytest summary line and the vitest summary line name their counts. Claim the counts only from those lines.

- [ ] **Step 2: Write the results record**

Sections as cut 23's: `## 1. What ran` (the exact commands, exit codes, the prefix chain, per-phase counts, the `declared arms:` line, the transcript links); `## 2. Accounting and disposition` (W15 and W4 close; X12, W8a and M3 part with their exact remainders; W8b measured and not selected; W1, W2, W5a re-filed to `beliefs-b7994b`); `## 3. Corrections and deviations from the frozen cut` (dated bullets, empty if none; the writer-session J1 "seven" statement and the eighth route covered here go in this section); `## 4. Reproduction measurement` (no new mm30 run; cite cut 22's); `## 5. Remaining boundary` (`world-resolution` retains W7, W8, W8b, W13's clauses, X12/W8a/M3's non-coreference arms as owned, R23's snapshot, divergence and explicit-import clauses, and slice 2b's W1, W2, W5a; `packaging-remainder` unchanged); `## 6. Main integration` after the merge.

- [ ] **Step 3: Regenerate the roadmap's Appendix A and rewrite the ledger's Current state**

Run: `uv run --frozen python tools/roadmap_status.py` and paste its table; rewrite the roadmap whole per its header rule; update the ledger's `world-resolution` row and summary; run `uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider` until green — `test_the_roadmap_and_ledger_name_the_same_boundaries` and `test_the_ledger_summary_names_the_newest_remaining_boundary` bind these documents to the record.

- [ ] **Step 4: Close the tasks and commit**

```bash
tasks done beliefs-e963b9 "cut 24 discharged; results record docs/plans/2026-09-XX-conformance-cut-24-results.md"
tasks note beliefs-46847c "from slice 2 (spec §13 item 3): whether the world-scale audit should report an attestation over a deleted endpoint, beside the drift question slice 1 filed"
tasks note beliefs-113561 "slice 2 discharged at cut 24; W1, W2, W5a continue as beliefs-b7994b"
tasks done beliefs-113561 "coreference attestations and balance discharged at cut 24"
tasks check
git add -A docs python/tests tasks
git commit -m "docs(cut24): discharge conformance cut 24 and re-rank the roadmap"
```

Then merge `world-resolution` into `main` with `--no-ff`, run `just gate` on `main`, record §6 of the results record, and remove the worktree per the roadmap's lane rules.

---

## Review log

**2026-09-10, first review on `3e54338`, eight findings, all resolved.** (1) The builder test asserted the facet set without the `semantic-identity` stamp `_node` adds — it now asserts the payload and the stamp separately (Task 2). (2) `PermitRefused` does not exist; the permit's refusal is `PermitExceeded` (Task 4). (3) The Unicode fixture also refuses the "duplicate coreference weighting" and "wrong sorting" mutants, confirmed by probe — both `refused_by` sets gain it (Task 3 step 6). (4) The in-memory `Recorder` writer has no operation port, so import refused before validation — the import test uses `test_facet_seams.writer` (Task 4). (5) One catch wrapped both the reader and the controlled rebuild as `ValidationRefused`, against spec §9 — the rebuild is `_controlled_coreference`, called outside the wrap and raising `MalformedRecord`; `_validated_coreference` composes both for the import door (Task 4). (6) `ActLine.record_ids` holds `(uid, id)` pairs (Task 5). (7) Deleting the reinstall in the indeterminate-span test would leave its wider publication `RuleNotHeld` — the reinstall now installs the shipped bundle (Task 6). (8) W15i's sabotage crashed on three-way unpacking and X12b's used a malformed identity domain — both mutants are now runnable and wrong (Task 7).
