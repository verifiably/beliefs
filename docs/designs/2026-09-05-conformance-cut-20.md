# Conformance cut 20 — facet contracts

**Status:** Frozen 2026-09-06. Not yet discharged.

**Sources:** `2026-09-05-facet-contracts-design.md` §§2, 3.1, 7.1, 8–10;
`2026-08-04-domain-extension-boundary-design.md` §10;
`2026-08-02-epistemic-kernel-design.md` §5; and
`2026-08-04-formal-model-and-claim-calculus-design.md` §8.

## 1. What this cut is

Cut 20 is the frozen acceptance boundary for the facet-contracts slice
(facet-contracts design §10), frozen before implementation. It is numbered
after cut 19 under concurrency rule 1, and its discharge is serialized after
cut 19's under rule 5.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. Prior evidence remains evidence but is not selected again.

## 2. The boundary

In scope:

- the bearer invariant over resulting corpus state at every entry of either
  half, including bundles and production publication;
- the closed `empirical-observation` payload schema: required `locator` and
  `attested_by`, optional `retrieval`, and refusal of unknown keys;
- attestation as declaration data, bound at mint and when the declaration
  changes, and preserved by import, relocation and unchanged revision;
- base-contract declarations of kinds, relation signatures and unnamespaced
  facets, and domain-contract declarations of namespaced facets only;
- the closed structural facet grammar: six field types, explicit `required`,
  and the type-specific `kinds` and `schemes` members;
- reader-shaped and schema-shaped facets, with schema validation confined to
  schema-shaped facets and the existing `display` reader retained;
- compilation of kinds, facets, one `nodes` `KindSpec` per kind in a private
  `Registry`, and validators from `ProfileSpec`;
- contract-declared semantic-stamp coverage, kept separate from the consulted
  walk's facets-read input;
- the shipped base profile, compiled once from the packaged byte-identical
  base contract, with the existing inventories exposed as views;
- the writer's required profile and pin-agreement recheck under every
  operation lock;
- `KIND_ACTS` remaining authored write policy in `permit.py`, checked against
  the compiled inventory rather than compiled as kind shape; and
- the minimal `PRACTICE.yaml` loader, whose grammar cannot contribute a
  vocabulary, schema, facet, kind or relation to profile compilation.

Out of scope: the biology pack and every real vocabulary binding (slice
2); URL acquisition itself (`url-retrieval`) — F7's positive arm tests
reference acceptance over an imported report, not acquisition; lineage
inherited observation standing (§14); relation endpoint enforcement at write
(§9); migrating any reader-shaped facet to a schema; contract distribution
(D §12); any `science` code; D6's facet arm and its activated-but-unconsulted
negative; and D1's "add a `nodes` code path" negative.

## 3. Selection

### D1 — part

```markdown
| D1 | `nodes` assigns no domain semantics | assert `nodes` ships **no domain contract, schema, validator, or vocabulary adapter**, and that **no `nodes` API accepts** a domain, contract, or vocabulary argument; assert every domain-flavoured string in the `nodes` tree is **opaque** — its normative fixtures already carry `bio-axes` and `HGNC:7296` (`fixtures/gene_phf19.*`) purely as example payload the kernel never interprets, and that is **conforming, not a violation**; **negative:** add a `nodes` code path that reads a facet key's namespace and behaves differently for `biology/` → refused, since assigning meaning to a namespace is exactly what this row forbids. A grep for domain *names* is **not** the test and would fail against a conforming tree |
```

**Selected:** installed-package signature inspection establishes that no API
takes a domain, contract or vocabulary argument over
`nodes.core.registry.Registry.register`, `KindSpec` and `ShapeSpec`; the
registry receives opaque keys.

**Deferred:** the "add a `nodes` code path" negative.

### D2 — closes

```markdown
| D2 | Interpretation is separable from identity | add a `biology/gene-axis` facet to a dataset node and assert the **dataset address is unchanged** (bytes did not move) while **node content identity and corpus-state identity both move**; correct the facet's payload and assert the same asymmetry again; **negative:** change the bytes and assert a **different dataset** is minted with no facet involvement |
```

**Selected:** every arm, single-homed to
`test_d2_interpretation_is_separable_from_identity_durably`.

**Deferred:** none.

### D4 — closes

```markdown
| D4 | `ProfileSpec` is the only per-kind source; `KindSpec` is compiled | have `science` and a domain both contribute facets to `dataset`; assert exactly **one** `KindSpec` is registered for it carrying the union, that `Registry.register()` is called **once** per kind, and that no duplicate-registration error is reachable; mutate a domain contract and assert the compiled spec changes with **no `nodes` code change**; assert **no second authored per-kind artifact exists** — nothing plays `KIND_DESCRIPTORS`' old role beside `ProfileSpec`, and any further per-kind artifact is compiled from it; assert a namespaced facet key round-trips **identically** through the Python and TypeScript canonical projections (the one shared parity fixture this design adds) |
```

**Selected:** every arm, single-homed to
`test_d4_one_kindspec_per_kind_compiled_from_the_profile`.

**Deferred:** none.

### D5 — closes

```markdown
| D5 | The manifest pin is inside corpus-state identity, over a canonical projection | reformat `corpus.yaml` — whitespace, key order, quoting style — and assert corpus-state identity is **unchanged**; **reorder the `domains` mapping** and assert it is **unchanged** (ordering is inert by construction, since the projection sorts object keys); change a pinned contract identity and assert it **moves**; change any other non-node file and assert it is **unchanged**; assert the digest covers the **complete** canonical projection by adding a new permitted field and confirming it participates without a further amendment; **refusals:** an unknown field, a duplicate `domains` key, and a malformed contract identity are each **refused at load**, never ignored and never digested |
```

**Selected:** every arm, single-homed to
`test_d5_manifest_pin_projection_and_refusals`.

**Deferred:** none.

### D8 — closes

```markdown
| D8 | Domain contributions compose without collision | two domains contributing same-named facets in **different** namespaces → both compose; two contributions to one namespaced facet key → **refused** at compile, never last-writer-wins; a domain attempting to define a **kernel kind** or a relation signature → **refused** |
```

**Selected:** every arm, single-homed to
`test_d8_contributions_compose_without_collision`.

**Deferred:** none.

### D9 — closes

```markdown
| D9 | Practices carry no vocabulary | a `PRACTICE.yaml` declaring a vocabulary binding or a facet schema → **refused**; assert a practice contributes **nothing** to the compiled registry and therefore can never move `belief_input_digest` |
```

**Selected:** every arm, single-homed to
`test_d9_practices_carry_no_vocabulary`.

**Deferred:** none.

### D10 — closes

```markdown
| D10 | Facets stay facets until the promotion trigger | assert no API retracts, supersedes, or attributes an individual facet payload — the three operations that define the trigger are **unspellable** over facets; assert correcting an interpretation is an ordinary node revision leaving no record of the prior claim, and that this is the stated cost (limitation 3) of not yet promoting |
```

**Selected:** every arm, single-homed to `test_d10_facets_stay_facets`.

**Deferred:** none.

### G5 — closes

```markdown
| **G5** | Divergence is computed, never authored | Attempt to author a divergence record; assert no such kind exists |
```

**Selected:** every arm, single-homed to
`test_g5_no_divergence_kind_exists`.

**Deferred:** none.

### F1 — closes

```markdown
| **F1** | The payload contract is enforced at every entry and reported by the check | an unknown key, a missing required field, a wrong type, an unknown scheme, an empty remainder: each refused at `add`, `revise`, relocation with a prefix-stable `FacetPayloadRefused`, and at `import_bundle` as `ImportRefused` naming the member with `FacetPayloadRefused` as its cause; the reproduction's `{boundary, source, asserted_by}` refused at `add`; a raw-written malformation reported `facet-payload-malformed`. **Sabotage:** the validator accepts unknown keys → the reproduction-payload test fails |
```

**Selected:** every arm, single-homed to
`test_f1_payload_contract_enforced_at_every_entry`.

**Deferred:** none.

### F2 — closes

```markdown
| **F2** | The bearer invariant holds over the resulting corpus state, order-independently, for every carrier of a `produces` edge | facet dataset then producing run → run refused; producing run then facet dataset → dataset refused; a non-run record (a `source`, say) carrying `produces` to a facet-bearing dataset → refused on the edge, its kind notwithstanding; a bundle holding both refused in either member order, naming the pair; a production run whose produced address is a facet-bearing dataset → `RunRefused(acquisition-boundary)`, the intent and its refusal report on the chain, no run record, no output publication, store untouched; a raw-written pair reported `facet-bearer-produced`. **Sabotage:** the producer read dropped → the run-then-dataset test fails |
```

**Selected:** every arm, single-homed to
`test_f2_bearer_invariant_over_resulting_state`.

**Deferred:** none.

### F3 — closes

```markdown
| **F3** | Attestation is bound at mint and on a changed declaration, preserved on import, relocation and unchanged revision | Alice mints; Bob revises the locator retaining Alice → `ActorMismatch`; naming Bob → accepted; Alice revising her own with Alice retained → accepted; Bob's revise with unchanged declaration and `attested_by: Bob` → refused; import and move keep a foreign attester byte-identical. **Sabotage:** the comparison skipped → Bob-retaining-Alice passes |
```

**Selected:** every arm, single-homed to
`test_f3_attestation_bound_and_preserved`.

**Deferred:** none.

### F4 — closes

```markdown
| **F4** | Eligibility reads the acquisition-boundary validity predicate under the existential rule | one valid and one invalid observes input → admissible, the invalid one reported `facet-payload-malformed`; only an invalid one → refused with a reason distinct from absence; only an absent one → refused with the absence reason; a raw-written observes dataset carrying a valid facet **and** a lineage basis → refused, reported `facet-bearer-produced`; an observes dataset whose `retrieval` names a deleted report → refused, reported `facet-retrieval-unresolved`. **Sabotage:** validity replaced by presence → the invalid-only test admits |
```

**Selected:** every arm, single-homed to
`test_f4_eligibility_reads_the_validity_predicate`.

**Deferred:** none.

### F5 — closes

```markdown
| **F5** | Profile agreement is rechecked under the lock; the check withholds what it cannot judge | manifest rewritten between construction and `add` → `ContractMismatch`, nothing written; rewritten between a run's intent and its publication → `ContractMismatch`, the intent unfulfilled, no report, no run record; domain-only mismatch → `profile-mismatch` with stamp findings still reported; base mismatch → `profile-mismatch` and no stamp finding. **Sabotage:** the recheck skipped under the lock → the rewritten-manifest test writes |
```

**Selected:** every arm, single-homed to
`test_f5_profile_agreement_rechecked_under_the_lock`.

**Deferred:** none.

### F6 — closes

```markdown
| **F6** | A dataset revision changes interpretation and prose only | each preserved field mutated in turn → `ReviseOutsideAllowlist`; removing `empirical-observation` → refused; removing a domain facet → accepted; adding the facet to an unmarked dataset binds the actor and runs the bearer check; the address is unchanged and node content identity and corpus state move (D2's asymmetry) |
```

**Selected:** every arm, single-homed to
`test_f6_dataset_revision_changes_interpretation_and_prose_only`.

**Deferred:** none.

### F7 — closes

```markdown
| **F7** | `retrieval` resolves or refuses | present and unresolved → refused; resolving to a report whose operation is not `acquisition` → refused; resolving to an **imported, well-formed** `acquisition` report → accepted. The positive arm tests reference acceptance and claims nothing about URL acquisition, which `url-retrieval` owns |
```

**Selected:** every arm, single-homed to
`test_f7_retrieval_resolves_or_refuses`.

**Deferred:** none.

### F8 — closes

```markdown
| **F8** | Every facet a builder writes is declared, and an undeclared key is refused | each `stored.*_node` builder's output, and the writer's coordination node, validated against the compiled registry with no `facet-unexpected` or `facet-missing`; a static inventory of `stored.py`'s facet constants against the shipped base; an undeclared key at `add` → `ValidationRefused(facet-unexpected)`; an unknown kind → refused (G5). **Sabotage:** a builder writes a literal key the contract does not declare → its builder test fails |
```

**Selected:** every arm, single-homed to
`test_f8_every_builder_facet_is_declared`.

**Deferred:** none.

### parity-fixture-2 — closes

```markdown
> **A second obligation this uncovered, and it is owed.** `π_claim` uses strings,
> arrays and string-keyed objects, so the claim fixture pins the value contract
> only over those. `science.identity.v1`'s **numeric arms have no cross-language
> fixture at all** — integers, decimals, the one spelling of zero, the refusal of
> binary floats, the escape table, and the astral key ordering are each tested
> twice and compared never. D §6's precedent is one parity fixture per shared
> *encoding*, and `identity.v1` is a different shared encoding from `π_claim`, so
> a values-level fixture is the second one that precedent asks for. It is **not**
> in cut 1 — §5.1 selects one fixture and the stop rule holds — and it should be
> the first thing added after it. The divergence risk is concrete: the two
> implementations spell the numeric refusal differently, Python refusing `float`
> and TypeScript refusing `number`, and nothing currently compares what they
> accept.
```

**Selected:** the values-level fixture obligation, single-homed to
`test_identity_parity_fixture.py` and `ts/tests/identity-fixture.test.ts`.

**Deferred:** none.

### Boundary invariants

No read entry point gains an argument (facet-contracts design §7.1).
`WORLD_RELATIONS` is unchanged in membership (facet-contracts design §3.1).

## 4. Accounting

Sixteen guarantee rows are read: **15 full/closed** (D2, D4, D5, D8, D9,
D10, G5 and F1–F8) and **1 partial** (D1). The parity-fixture unit and the
boundary-invariant unit bring the N2 inventory to **18 declaration units**.
A grouped unit may expand into sabotage arms, but it is counted once here and
may not be silently split or merged after the freeze.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 18 frozen units in §4, each
   single-homed to the tests named in §3. Lettered sabotage arms normalize
   back to those units.
2. The aggregate runner names `cut19_acceptance.py` as its prefix once main
   carries cut 19, then runs `test_facet_acceptance.py` and the cut-20 N2
   audit.
3. The N2 audit applies the facet-contracts design §10 sabotage list, one arm
   per named check: accept unknown payload keys; drop the producer read; skip
   attestation comparison; skip the pin recheck under lock; replace validity
   with presence; write an undeclared builder facet; compare fixture bytes
   without the digest; accept domain `kinds:`; accept a domain facet attached
   to an undeclared kind; widen `WORLD_RELATIONS` to both relation groups;
   replace the duplicate-key loader with `safe_load`; and take coverage in
   authored order.
4. Capability refusal is an error, never a skip or waiver. Every selected
   behavior runs portably and on the certified kernel and volume tuple.
5. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against its
source table at the freeze commit; audit every selected clause against §2;
and force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- D1 remains partial and the installed-package inspection treats every
  domain-flavoured key as opaque;
- the F2 invariant is checked over resulting state in both bundle orders and
  for every carrier kind;
- F5 rechecks under the operation lock and withholds stamp findings on base
  mismatch;
- the parity fixture compares canonical bytes and digest in both languages;
- the two boundary invariants remain unchanged; and
- every sabotage in §5 fails its named check independently.

## 7. Limitations

1. **Reader-shaped facets are declared, not schema-validated**, and reader
   strictness is uneven, named per reader in §3.2. A payload the named
   reader coerces is a payload this slice accepts.
2. **Relation endpoints are compiled, not enforced at write.** Source and
   target sets enter `compiled_identity`; nothing new refuses an edge whose
   endpoints disagree with them. Validation scope for the contract cut.
3. **`facets_read` is empty**, so D6's facet arm is unproven here.
4. **F7's positive arm is reference acceptance**, not acquisition.
5. **The packaged base contract is a build-time copy**, held byte-identical
   by a test; the normative file stays at `contracts/science/CONTRACT.yaml`.
6. **Domain contract documents are supplied by the caller.** Distribution
   (D §12) stays open; the writer verifies pins, it does not locate
   contracts.
7. **The bearer invariant sees producers in this corpus only.** A producer
   in another corpus is `world-resolution`'s cross-corpus read.
8. **The locator's truth and the observation's nature stay authored** —
   kernel limitation 8, narrowed.
9. **A pin mismatch after a run's intent leaves the intent unfulfilled**
   (§5.4). Stated, not repaired.
10. **TypeScript validates no payload.**
11. **`display` keeps its hand-coded check**, accepting an empty statement.
