# `@verifiably/beliefs`

The TypeScript mirror of the **shared encoding**, and nothing else.

beliefs is Python-primary: the kernel, its writes and its contract compilation live in
`../python/`. This package carries only what two implementations must agree on, as
[Encoding and parity](../docs/records.md#encoding-and-parity) specifies:

- **`science.identity.v1`**, the canonical value encoding
  ([Identity](../docs/records.md#identity));
- **`π_claim`**, the canonical claim projection, and `I_claim` over it.

Contract reading, profile resolution and the validated claim constructor are here
because a projection is of a *typed* claim: the parity fixture's components go through
`buildClaim` before they are projected, so both sides walk the same path from
components to identity.

## What this side deliberately does not do

It computes **no contract identity and no compiled profile identity**: compilation is
not a shared encoding, and no parity obligation reaches it.

It reads only base contracts and genesis domain contracts, and it **refuses** a
contract that declares a predecessor or a `retired` identifier rather than parsing
past it ([contracts.md](../docs/contracts.md#scope)). A reduced parser that quietly
accepted what the Python reading refuses would be a second, weaker reading of the same
contract, and it would look like agreement.

It parses `kinds`, `relations` and `facets` declarations with the same structural
refusals and validates no facet payload; validation is Python-only, done where
profiles are compiled.

## Running it

```sh
npm ci
npm test        # vitest
npm run typecheck
npm run check   # biome
```

From the repository root, `just setup` runs `npm ci`, and focused runs are described in
[docs/development.md](../docs/development.md#gates-and-focused-runs).

The parity suite reads `../fixtures/claim-identity-v2.json` and the contracts
under `../contracts/` and `../fixtures/contracts/`. The document-reading and
identifier-pattern suites read `../fixtures/document-reading-v1.json` and
`../fixtures/identifier-patterns-v1.json`, the oracles the Python suite reads too. No
test writes them.
