# `@verifiably/beliefs`

The **shared-encoding path**, and nothing else.

Science is Python-primary — substrate §11 puts the composition root there, and
formal model limitation 9 records **M10** as the only cross-implementation row.
So this package carries exactly two things two implementations must agree on:

- **`science.identity.v1`**, the canonical value contract (computation §4.3);
- **`π_claim`**, the canonical claim projection, and `I_claim` over it (§6.5).

Contract reading, profile resolution and the validated constructor are here
because a projection is of a *typed* claim — the parity fixture's components go
through `buildClaim` before they are projected, or this side would be walking
three stages of a four-stage path while the other walks all four.

## What this side deliberately does not do

It computes **no contract identity and no compiled profile identity**: §8 sites
claim-schema compilation as Python-only, on the ground that compilation is not a
shared encoding and no parity obligation reaches it.

It does not validate **succession** (§8.3) and does not implement **retirement**
(§7.3a) — and it **refuses** contracts that use either, rather than parsing past
them. A reduced parser that quietly accepted what the normative reading refuses
would be a second, weaker reading of the SSOT, and it would look like agreement.

It parses `kinds`, `relations` and `facets` declarations with the same
structural refusals and validates no facet payload; validation is Python-primary,
sited with compilation (facet-contracts §7.2).

## Running it

```sh
npm install
npm test        # vitest
npm run typecheck
npm run check   # biome
```

The parity suite reads `../fixtures/claim-identity-v1.json` and the contracts
under `../contracts/` and `../fixtures/contracts/`. It never writes them.
