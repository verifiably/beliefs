# Conformance cut 24 — the coreference attestation and its balance

**Status:** discharged 2026-09-10; frozen before implementation. Results: `../plans/2026-09-10-conformance-cut-24-results.md`.
**Frozen:** 2026-09-10, before implementation, on `world-resolution`
**Design:** `../superpowers/specs/2026-09-10-world-resolution-slice-2-design.md`, reviewed twice 2026-09-10
**Numbered after** cut 23 (roadmap concurrency rule 1) and **serialized after** its discharge, which landed on `main` at `6eb0b93` (rule 5).

## 1. What this cut is

The following baseline describes the tree before implementation. Cut 24 is
now discharged: W15 and W4 close, while X12, W8a and M3 gain their
coreference arms and remain partial. The dated results record preserves the
measured outcome; §§2–7 remain frozen.

The world address ruling made different-basis coreference an attributed,
additive attestation with a derived balance and retired structural merge. The
kernel banked the shape and built everything downstream of the record: the
reduction rule and its four fixtures (`world/rules_v1/coreference.py`), the
captured value (`derive.CapturedCoreference`), the epoch member
`coreference-map.yaml` and its receipt, the permit entry, and the read side's
three edge states with the expansion refusal (`world/read.py`). What it never
built is the record. `contracts/science/CONTRACT.yaml` declares
`coreference-attestation: {}` with no domain and no facet; `stored.py` has no
builder and no reader; `CorpusWriter` has no seam; and `epoch._captured_records`
lifts no coreference facet, so every published coreference map is `{"pairs": []}`
and every build refuses a record that claims the kind with
`EnumeratedKindUngoverned`. The cut 7 results record names this: "two
enumerated kinds remain prose … every populated membership, reduction, and
omission-refutes arm waits on the kinds' own charters."

This slice builds the record and connects it. It promotes the kind from
deferred to governed, gives it a stored builder and facet reader, adds the one
write seam that mints it under the four endpoint refusals the ruling names,
lifts the facet at capture so the shipped reduction reduces real attestations,
and reads every populated arm the balance, receipt and edge-state rows carry.
The read side's balance branch does not change: over an established coverage a
pair the reduction never recorded is `inactive`, which is the ruling's "zero or
negative does not" activate, and omission is the receipt's finding, not the
reader's.

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

> **2026-09-10 post-freeze accounting correction:** review found that §5's
> frozen “18 declared arms” count names 19 distinct mutations and that the live
> plan omitted two independent checks: admitting `act-report` as an endpoint
> kind and narrowing exact receipt validation to membership. Sections 2–7 stay
> byte-exact. The live Task 7 inventory adds `W15n` and `X12c` to the original
> 18 arms, for 20; the discharge record will carry this dated deviation.

## 2. The boundary

In scope:

- `docs/designs/2026-09-10-conformance-cut-24.md`: the frozen boundary,
  selection, accounting and obligations;
- `contracts/science/CONTRACT.yaml` and
  `python/src/beliefs/contracts/science/CONTRACT.yaml`: the kind's domain and
  facet;
- `python/src/beliefs/stored.py`: `COREFERENCE_ATTESTATION_FACET`,
  `COREFERENCE_ATTESTATION_DOMAIN`, `COREFERENCE_ENDPOINT_KINDS`,
  `CoreferenceAttestation`, `coreference_attestation_value` and
  `coreference_attestation_node`;
- `python/src/beliefs/world/rules_v1/coreference.py` and
  `fixtures/coreference.unicode.yaml`: the NFC-normalized deduplication key and
  its fixture;
- `python/src/beliefs/world/derive.py`: `CapturedCoreference`'s NFC refusal;
- `python/src/beliefs/world/epoch.py`: `_captured_records`' facet lift;
- `python/src/beliefs/errors.py`: `CoreferenceEndpointRefused`;
- `python/src/beliefs/corpus.py`: `CorpusWriter.attest_coreference`,
  `_validated_coreference`, `_resolve_coreference_endpoints`, the family-kind
  clause, the import clause and `OperationWrites.attest_coreference`;
- `python/src/beliefs/session/writer.py`: `ScopedWriter.attest_coreference`;
- `python/tests/test_coreference_attestation.py`: the builder, reader, rule,
  capture, seam, import and session unit arms;
- `python/tests/test_facet_declarations.py`,
  `python/tests/test_base_contract.py`, `python/tests/test_world_build.py`,
  `python/tests/test_profile.py`, `python/tests/test_permit_boundary.py`,
  `python/tests/test_permit_entry_points.py`,
  `python/tests/test_session_writer.py`, `python/tests/test_world_read.py` and
  `ts/tests/declarations.test.ts`: the pins that move;
- `python/tests/acceptance/test_coreference_acceptance.py`,
  `python/tests/acceptance/n2_arms_cut24.py` and
  `python/tests/acceptance/test_n2_cut24.py`: the durable arms, declarations
  and guard;
- `python/tools/cut24_acceptance.py` and `python/tools/roadmap_status.py`: the
  runner and cut 24 accounting row;
- `docs/designs/2026-08-02-world-addressing-design.md` (W8a),
  `docs/designs/2026-08-08-world-address-ruling.md` (§5.5),
  `docs/designs/2026-09-05-writer-session-design.md`,
  `docs/designs/2026-09-04-write-permits-design.md`,
  `docs/designs/2026-09-03-world-changing-families-design.md`,
  `docs/designs/2026-09-05-facet-contracts-design.md`,
  `docs/designs/2026-08-20-world-index-slice-2-design.md` and
  `docs/guide/identity-world-and-change.md`: the dated notes;
- `docs/plans/2026-09-XX-conformance-cut-24-results.md`, the adoption ledger,
  roadmap and `README.md`: the discharge records.

Out of scope:

- slice 2b (`beliefs-b7994b`): W1, W2 and W5a — source addresses derived from
  the normalized identifier;
- slice 3: the import, audit and diagnostic callers; R23's snapshot, divergence
  and explicit-import clauses; X5 and W13;
- slice 4: W7;
- W8b: measured, repaired by `beliefs-fda0e5`, and not selected;
- the `instrument-certification` kind and every `instrument-certification` arm
  (`contract-cut`);
- W8a's import-boundary and audit arms (`packaging-remainder`);
- the read side: `read.coreference_edge` and `read.expand_coreference` stay
  unchanged.

## 3. Selection

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

## 4. Accounting

Five guarantee rows are read, **2 full/closed** (W15, W4), 3 partial (X12, W8a, M3), and **5 declaration units** carry them: `W15`, `X12`, `W8a`, `M3`, `W4`. W8b stays measured and not selected; W1, W2 and W5a are re-filed to slice 2b (§2).

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the five units `W15`, `X12`, `W8a`,
   `M3` and `W4`, each single-homed to the test that exercises it.
2. Every durable arm runs on the certified volume. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut23_acceptance.py",)` and
   `PHASE_MODULES = ("test_coreference_acceptance.py", "test_n2_cut24.py")`.
4. The 18 declared arms cover every sabotage site: in `corpus.py` (the
   admissible-kind set widened to prose; the raw self-pair check dropped; exact
   resolution weakened to presence; the kind comparison dropped; the actor
   bind dropped; the family-kind clause dropped; the controlled rebuild
   narrowed to the id; the import clause dropped; attestations admitted into
   the retraction graph; a `merge` name registered on the operations facade),
   in `stored.py` (relations attached to each endpoint), in `world/epoch.py`
   (the capture lift dropped; capture iterates every live admitted corpus
   instead of the declared coverage), in `world/rules_v1/coreference.py` (the
   event token added to the key; the NFC normalization dropped), in
   `world/read.py` (missing coverage answered empty; the refuted rebuild
   answered validated; the rebuild comparison narrowed to membership), and in
   `world/derive.py` (the coreference map added to the belief input).
5. `test_n2_cut24.py` audits them by the cut-12 pattern with the staleness
   probe's baseline taken from the tree.
6. Prior declarations remain frozen and no check is reclaimed.
7. This cut document and its declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites §§2–7; any deviation is
   dated in the results record.

## 6. Second reader

The design's two review passes on 2026-09-10 are its second reading: eight
first-review findings and four second-review findings were resolved.

## 7. Limitations

1. The deduplication key defeats exact NFC duplicates only; per-attester
   capping and grounds equivalence are policy, unbuilt.
2. The coverage arm's "digest unchanged" clause is unsatisfiable as the row
   states it and is read on one coverage.
3. An attestation over a since-deleted endpoint is reduced and never refused
   (spec §13 item 3).
