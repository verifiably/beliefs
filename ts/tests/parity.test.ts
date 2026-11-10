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
 * stands in for the fixture's `profile_compiled_identity` pin, since this side
 * computes no compiled identity.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, Member, Qualifier, Referent, type RoleFilling, buildClaim } from "../src/claim.js";
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

interface FixtureMember extends FixtureReferent {
  coefficient: number;
}

type FixtureRole = FixtureReferent | FixtureMember[];

interface FixtureProjection {
  operator: string;
  roles: Record<string, FixtureReferent | FixtureMember[]>;
  qualifiers: Record<string, { quantifier: string; restriction: FixtureReferent }>;
  form: string;
  polarity: string;
  layer: string;
}

interface FixtureRow {
  name: string;
  covers: string;
  claim: {
    operator: string;
    roles: Record<string, FixtureRole>;
    qualifiers: Record<string, { quantifier: string; restriction: FixtureReferent }>;
    form: string;
    polarity: string | null;
    layer: string;
  };
  projection: FixtureProjection;
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

const rawFixture = read("fixtures/claim-identity-v2.json");
const fixture = JSON.parse(rawFixture) as Fixture;

const base = parseBaseContract(read(fixture.base_contract), fixture.base_contract);
const profile = compileProfile(
  base,
  fixture.domain_contracts.map((path) => parseDomainContract(read(path), path, base)),
);

const BETA_TERM = "EX:\u03b2-catenin";
const SAME_CLAIM = ["correlates-with-written-forward", "correlates-with-written-reversed"] as const;

function referent(value: FixtureReferent): Referent {
  return new Referent(value.sort, value.term);
}

function role(value: FixtureRole): RoleFilling {
  if (Array.isArray(value)) {
    return value.map((member) => new Member(referent(member), BigInt(member.coefficient)));
  }
  return referent(value);
}

function build(row: FixtureRow) {
  const qualifiers = new Map<string, Qualifier>();
  for (const [dimension, entry] of Object.entries(row.claim.qualifiers)) {
    qualifiers.set(dimension, new Qualifier(entry.quantifier, referent(entry.restriction)));
  }
  return buildClaim(profile, {
    operator: row.claim.operator,
    roles: new Map(Object.entries(row.claim.roles).map(([name, value]) => [name, role(value)])),
    qualifiers,
    form: row.claim.form,
    polarity: row.claim.polarity,
    layer: row.claim.layer,
  });
}

/** The stored projection with member coefficients as `BigInt`, as `projectClaim` returns them. */
function expectedProjection(row: FixtureRow): unknown {
  const roles: Record<string, unknown> = {};
  for (const [name, value] of Object.entries(row.projection.roles)) {
    roles[name] = Array.isArray(value)
      ? value.map((member) => ({ ...member, coefficient: BigInt(member.coefficient) }))
      : value;
  }
  return { ...row.projection, roles };
}

function referentsOf(projection: FixtureProjection): FixtureReferent[] {
  const found: FixtureReferent[] = [];
  for (const value of Object.values(projection.roles)) {
    if (Array.isArray(value)) found.push(...value);
    else found.push(value);
  }
  for (const entry of Object.values(projection.qualifiers)) found.push(entry.restriction);
  return found;
}

const byName = (name: string): FixtureRow => fixture.vector.find((row) => row.name === name) as FixtureRow;

describe("the fixture is about this profile", () => {
  it("pins the encodings this implementation carries", () => {
    expect(fixture.claim_domain).toBe(CLAIM_DOMAIN);
    expect(fixture.identity_contract).toBe("science.identity.v1");
  });

  it("is a vector, with distinct rows except the one claim written in both member orders", () => {
    expect(fixture.vector.length).toBeGreaterThan(1);
    expect(new Set(fixture.vector.map((row) => row.name)).size).toBe(fixture.vector.length);
    const others = fixture.vector.filter((row) => row.name !== SAME_CLAIM[1]).map((row) => row.digest);
    expect(new Set(others).size).toBe(others.length);
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
      expect(projection).toEqual(expectedProjection(row));
      expect(new TextDecoder().decode(encode(projection))).toBe(row.canonical_bytes);
      expect(claimIdentity(claim)).toBe(row.digest);
    });
  }
});

describe("tag coverage is complete against the base contract", () => {
  const projections = fixture.vector.map((row) => row.projection);

  it("both forms appear", () => {
    const projected = new Set(projections.map((projection) => projection.form));
    for (const form of base.claimGrammar.forms) expect(projected).toContain(form);
  });

  it("every polarity tag appears, including the sign-inapt one", () => {
    const projected = new Set(projections.map((projection) => projection.polarity));
    for (const tag of [...base.claimGrammar.polarities, base.claimGrammar.signInaptTag]) {
      expect(projected).toContain(tag);
    }
    expect(byName("affects-null-statistical").projection.polarity).toBe(base.claimGrammar.signInaptTag);
    expect(byName("transforms-structural").projection.polarity).toBe(base.claimGrammar.signInaptTag);
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

  it("every binding kind binds a referent", () => {
    const reached = new Set(
      projections.flatMap((projection) =>
        referentsOf(projection).map((entry) => profile.sorts[entry.sort].binding.kind),
      ),
    );
    for (const kind of base.claimGrammar.bindingKinds) expect(reached).toContain(kind);
  });
});

describe("the hard cases are present", () => {
  it("a many role with coefficients and one without", () => {
    const inputs = byName("transforms-structural").projection.roles.inputs as FixtureMember[];
    expect(profile.templates["testing/transforms"].roles.inputs.coefficients).toBe(true);
    expect(inputs.some((member) => member.coefficient !== 1)).toBe(true);
    const parties = byName(SAME_CLAIM[0]).projection.roles.parties as FixtureMember[];
    expect(profile.templates["testing/correlates-with"].roles.parties.coefficients).toBe(false);
    expect(parties).toHaveLength(2);
    expect(parties.every((member) => member.coefficient === 1)).toBe(true);
  });

  it("an empty min-0 role projects as an empty list", () => {
    const row = byName("transforms-structural");
    expect(row.claim.roles.facilitators).toEqual([]);
    expect(row.projection.roles.facilitators).toEqual([]);
  });

  it("correlates-with in both member orders has one identity", () => {
    const forward = byName(SAME_CLAIM[0]);
    const reversed = byName(SAME_CLAIM[1]);
    expect(forward.claim.roles.parties).toEqual([...(reversed.claim.roles.parties as FixtureMember[])].reverse());
    expect(forward.claim.roles.parties).not.toEqual(reversed.claim.roles.parties);
    expect(forward.projection).toEqual(reversed.projection);
    expect(forward.canonical_bytes).toBe(reversed.canonical_bytes);
    expect(claimIdentity(build(forward))).toBe(claimIdentity(build(reversed)));
  });

  it("a within-model claim differs from the world claim", () => {
    const model = byName("affects-within-model");
    const referentValue = model.projection.roles["within-model"] as FixtureReferent;
    expect(profile.sorts[referentValue.sort].binding.kind).toBe("world-kind");
    const world = byName("affects-positive-causal");
    const { "within-model": _dropped, ...rest } = model.projection.roles;
    expect(rest).toEqual(world.projection.roles);
    expect(model.digest).not.toBe(world.digest);
  });

  it("the bridge is an operator with its own identity", () => {
    const bridge = byName("promotes-bridge");
    expect(Object.keys(profile.bridges)).toContain(bridge.projection.operator);
    const template = byName("affects-positive-causal");
    expect(template.projection.operator).toBe(profile.bridges[bridge.projection.operator].template);
    expect(bridge.projection.roles).toEqual(template.projection.roles);
    expect(bridge.digest).not.toBe(template.digest);
  });

  it("a claim-side qualifier appears, and a row carries more than one", () => {
    const dimensions = fixture.vector.flatMap((row) => Object.keys(row.projection.qualifiers));
    expect(dimensions.some((dimension) => profile.dimensions[dimension].placement === "claim")).toBe(true);
    expect(Object.keys(byName("affects-existential-two-dimensions").projection.qualifiers).length).toBeGreaterThan(1);
  });

  it("the non-ASCII referent is present", () => {
    const terms = fixture.vector.flatMap((row) => referentsOf(row.projection).map((entry) => entry.term));
    expect(terms).toContain(BETA_TERM);
  });

  it("the astral and BMP pair project in code point order", () => {
    const row = byName("correlates-event-product-astral-bmp");
    const written = (row.claim.roles.parties as FixtureMember[]).map((member) => member.term);
    const projected = (row.projection.roles.parties as FixtureMember[]).map((member) => member.term);
    expect(written).toEqual(["EX:\u{1f600}", "EX:\uff21"]);
    expect(projected).toEqual(["EX:\uff21", "EX:\u{1f600}"]);
  });
});

describe("the components go through the constructor", () => {
  it("a claim cannot be minted without it", () => {
    // The guarantee the parity run rests on: if this threw nothing, the fixture
    // could be satisfied by projecting an object literal, and this side would
    // never exercise the checks the other side does.
    const parts = {
      operator: "testing/affects",
      roles: new Map(),
      qualifiers: new Map(),
      form: "polar",
      polarity: "positive",
      layer: "causal",
    };
    expect(() => new Claim(Symbol("forged"), parts)).toThrow(/use buildClaim/);
  });

  it("a row whose polarity is tampered with is refused, not projected", () => {
    const inapt = byName("transforms-structural");
    expect(inapt.claim.polarity).toBeNull();
    const tampered = { ...inapt, claim: { ...inapt.claim, polarity: "positive" } };
    expect(() => build(tampered)).toThrow(/sign/);
  });
});
