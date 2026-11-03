/**
 * The cross-language parity fixture, TypeScript half.
 *
 * This side reads the **same frozen artifact** the Python side reads, and makes
 * the same four comparisons: components → `buildClaim` → `projectClaim` →
 * `encode` → `digest`. Neither language owns the fixture, and neither
 * regenerates it.
 *
 * **The components go through the checked constructor**, never straight to a
 * projection and never cast to `Claim`. Comparing the stored projection against
 * the stored bytes would exercise `science.identity.v1` and skip `π_claim`, so
 * only one implementation would be walking the whole path and the parity run
 * would be comparing a four-stage path against a three-stage one.
 *
 * The profile is compiled from the **contracts**, not from anything the Python
 * side emitted. If this implementation had read different declarations,
 * `buildClaim` would refuse rather than project something else — which is what
 * stands in for the fixture's `profile_compiled_identity` pin, since compilation is Python-only
 * compilation as Python-only and this side computes no compiled identity.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, Qualifier, Referent, buildClaim } from "../src/claim.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { encode } from "../src/identity/v1.js";
import { compileProfile } from "../src/profile.js";
import { CLAIM_DOMAIN, claimIdentity, projectClaim } from "../src/projection.js";

const REPO_ROOT = new URL("../../", import.meta.url);

function read(relative: string): string {
  return readFileSync(new URL(relative, REPO_ROOT), "utf-8");
}

interface FixtureReferent {
  sort: string;
  term: string;
}

interface FixtureRow {
  name: string;
  covers: string;
  claim: {
    operator: string;
    args: FixtureReferent[];
    qualifiers: Record<string, { quantifier: string; restriction: FixtureReferent }>;
    polarity: string | null;
    layer: string;
  };
  projection: Record<string, unknown>;
  canonical_bytes: string;
  digest: string;
}

interface Fixture {
  claim_domain: string;
  identity_contract: string;
  base_contract: string;
  domain_contracts: string[];
  vector: FixtureRow[];
}

const rawFixture = read("fixtures/claim-identity-v1.json");
const fixture = JSON.parse(rawFixture) as Fixture;

const base = parseBaseContract(read(fixture.base_contract), fixture.base_contract);
const profile = compileProfile(
  base,
  fixture.domain_contracts.map((path) => parseDomainContract(read(path), path, base)),
);

function referent(value: FixtureReferent): Referent {
  return new Referent(value.sort, value.term);
}

function build(row: FixtureRow) {
  const qualifiers = new Map<string, Qualifier>();
  for (const [dimension, entry] of Object.entries(row.claim.qualifiers)) {
    qualifiers.set(dimension, new Qualifier(entry.quantifier, referent(entry.restriction)));
  }
  return buildClaim(profile, {
    operator: row.claim.operator,
    args: row.claim.args.map(referent),
    qualifiers,
    polarity: row.claim.polarity,
    layer: row.claim.layer,
  });
}

describe("the fixture is about this profile", () => {
  it("pins the encodings this implementation carries", () => {
    expect(fixture.claim_domain).toBe(CLAIM_DOMAIN);
    expect(fixture.identity_contract).toBe("science.identity.v1");
  });

  it("is a vector, with distinct rows", () => {
    expect(fixture.vector.length).toBeGreaterThan(1);
    expect(new Set(fixture.vector.map((row) => row.name)).size).toBe(fixture.vector.length);
    expect(new Set(fixture.vector.map((row) => row.digest)).size).toBe(fixture.vector.length);
  });

  it("is stored pure-ASCII, so no tool can normalize it behind the fixture's back", () => {
    // The vector holds a composed non-ASCII referent and a decomposed one on
    // purpose; held as escapes, the assertion cannot be silently deleted.
    // biome-ignore lint/suspicious/noControlCharactersInRegex: the point is the range above 0x7f
    expect(/^[\x00-\x7f]*$/.test(rawFixture)).toBe(true);
  });
});

describe("every row reproduces", () => {
  for (const row of fixture.vector) {
    it(`${row.name} — ${row.covers}`, () => {
      const claim = build(row);
      const projection = projectClaim(claim);
      expect(projection).toEqual(row.projection);
      expect(new TextDecoder().decode(encode(projection))).toBe(row.canonical_bytes);
      expect(claimIdentity(claim)).toBe(row.digest);
    });
  }
});

describe("tag coverage is complete against the base contract", () => {
  const projections = fixture.vector.map((row) => row.projection as unknown as ReturnType<typeof projectClaim>);

  it("every polarity tag appears, including the sign-inapt one", () => {
    const projected = new Set(projections.map((projection) => projection.polarity));
    for (const tag of [...base.claimGrammar.polarities, base.claimGrammar.signInaptTag]) {
      expect(projected).toContain(tag);
    }
  });

  it("every quantifier appears", () => {
    const projected = new Set(
      projections.flatMap((projection) => Object.values(projection.qualifiers).map((entry) => entry.quantifier)),
    );
    for (const quantifier of base.claimGrammar.quantifiers) expect(projected).toContain(quantifier);
  });

  it("every layer appears", () => {
    const projected = new Set(projections.map((projection) => projection.layer));
    for (const layer of base.claimGrammar.layers) expect(projected).toContain(layer);
  });
});

describe("the components go through the constructor", () => {
  it("a claim cannot be minted without it", () => {
    // The guarantee the parity run rests on: if this threw nothing, the fixture
    // could be satisfied by projecting an object literal, and this side would
    // never exercise the checks the other side does.
    const parts = {
      operator: "testing/affects",
      args: [],
      qualifiers: new Map(),
      polarity: "positive",
      layer: "causal",
    };
    expect(() => new Claim(Symbol("forged"), parts)).toThrow(/use buildClaim/);
  });

  it("a row whose polarity is tampered with is refused, not projected", () => {
    const inapt = fixture.vector.find((row) => row.claim.polarity === null) as FixtureRow;
    const tampered = { ...inapt, claim: { ...inapt.claim, polarity: "positive" } };
    expect(() => build(tampered)).toThrow(/unit type/);
  });
});
