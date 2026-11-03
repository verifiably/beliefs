/**
 * The validated constructor, on this side.
 *
 * The parity fixture drives every row through `buildClaim`, but a fixture of
 * well-formed claims can only show that the accepting path agrees. What it
 * cannot show is that the **refusing** path exists at all — a constructor that
 * checked nothing would reproduce all eleven rows byte for byte. So the checks
 * are tested directly here, and the pairing is the point: the fixture proves the
 * two implementations agree, and this file proves there is something to agree
 * about.
 *
 * Found by mutation: accepting a hand-supplied `inapt` tag left the whole suite
 * green before this file existed.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, Qualifier, Referent, buildClaim } from "../src/claim.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import {
  ArgumentSortMismatch,
  ArityMismatch,
  ClaimError,
  InadmissibleLayer,
  MalformedReferent,
  PolarityRefused,
  ProfileError,
  RestrictionSortMismatch,
  UndeclaredDimension,
  UnknownQuantifier,
  UntypedQualifier,
  UntypedReferent,
} from "../src/errors.js";
import { compileProfile } from "../src/profile.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const read = (relative: string) => readFileSync(new URL(relative, REPO_ROOT), "utf-8");

const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
const profile = compileProfile(base, [parseDomainContract(read("fixtures/contracts/testing.yaml"), "testing", base)]);

const AFFECTS = "testing/affects";
const SUBTYPE_OF = "testing/subtype-of";
const POPULATION = "testing/population";

const gene = new Referent("testing/entity", "EX:gene-x");
const otherGene = new Referent("testing/entity", "EX:gene-z");
const outcome = new Referent("testing/outcome", "EX:outcome-y");
const adults = new Referent("testing/cohort", "EX:adults");

const noQualifiers = new Map<string, Qualifier>();

function affects(overrides: Partial<Parameters<typeof buildClaim>[1]> = {}) {
  return buildClaim(profile, {
    operator: AFFECTS,
    args: [gene, outcome],
    qualifiers: noQualifiers,
    polarity: "positive",
    layer: "causal",
    ...overrides,
  });
}

describe("polarity is the unit inhabitant where the operator has no sign", () => {
  it("fills the sign-inapt tag when nothing is supplied", () => {
    const claim = buildClaim(profile, {
      operator: SUBTYPE_OF,
      args: [gene, otherGene],
      qualifiers: noQualifiers,
      polarity: null,
      layer: "structural",
    });
    expect(claim.polarity).toBe(base.claimGrammar.signInaptTag);
    expect(base.claimGrammar.polarities).not.toContain(claim.polarity);
  });

  it("refuses the sign-inapt tag supplied by hand", () => {
    // There is exactly one inhabitant, so it is not a choice — accepting it
    // would make the author an authority on a contract-derived fact.
    expect(() =>
      buildClaim(profile, {
        operator: SUBTYPE_OF,
        args: [gene, otherGene],
        qualifiers: noQualifiers,
        polarity: base.claimGrammar.signInaptTag,
        layer: "structural",
      }),
    ).toThrow(PolarityRefused);
  });

  it("refuses a sign on a sign-inapt operator, `unsigned` included", () => {
    // The collapse: `unsigned` says the operator has a sign and this claim
    // asserts none, which is a different fact from having no sign to assert.
    for (const polarity of ["positive", "unsigned"]) {
      expect(() =>
        buildClaim(profile, {
          operator: SUBTYPE_OF,
          args: [gene, otherGene],
          qualifiers: noQualifiers,
          polarity,
          layer: "structural",
        }),
      ).toThrow(/unit type/);
    }
  });

  it("requires one where the operator has a sign", () => {
    expect(() => affects({ polarity: null })).toThrow(/sign-apt/);
    expect(() => affects({ polarity: "inapt" })).toThrow(PolarityRefused);
  });
});

describe("the profile-dependent checks refuse distinctly", () => {
  it("refuses an unresolvable operator", () => {
    expect(() => affects({ operator: "testing/absent" })).toThrow(ProfileError);
  });

  it("refuses the wrong arity", () => {
    expect(() => affects({ args: [gene] })).toThrow(ArityMismatch);
  });

  it("refuses a wrongly sorted argument", () => {
    expect(() => affects({ args: [outcome, gene] })).toThrow(ArgumentSortMismatch);
  });

  it("refuses a bare term in a slot", () => {
    expect(() => affects({ args: ["EX:gene-x" as unknown as Referent, outcome] })).toThrow(UntypedReferent);
  });

  it("refuses an undeclared dimension", () => {
    const qualifiers = new Map([[POPULATION, new Qualifier("generic", adults)]]);
    expect(() =>
      buildClaim(profile, {
        operator: SUBTYPE_OF,
        args: [gene, otherGene],
        qualifiers,
        polarity: null,
        layer: "structural",
      }),
    ).toThrow(UndeclaredDimension);
  });

  it("refuses a wrongly sorted restriction", () => {
    const qualifiers = new Map([[POPULATION, new Qualifier("generic", gene)]]);
    expect(() => affects({ qualifiers })).toThrow(RestrictionSortMismatch);
  });

  it("refuses a quantifier outside the closed set", () => {
    const qualifiers = new Map([[POPULATION, new Qualifier("mostly", adults)]]);
    expect(() => affects({ qualifiers })).toThrow(UnknownQuantifier);
  });

  it("refuses a qualifier impostor", () => {
    const impostor = { quantifier: "generic", restriction: adults } as unknown as Qualifier;
    expect(() => affects({ qualifiers: new Map([[POPULATION, impostor]]) })).toThrow(UntypedQualifier);
  });

  it("refuses an inadmissible layer", () => {
    expect(() => affects({ layer: "structural" })).toThrow(InadmissibleLayer);
  });

  it("accepts a well-formed claim whole", () => {
    const qualifiers = new Map([[POPULATION, new Qualifier("universal", adults)]]);
    const claim = affects({ qualifiers, polarity: "negative" });
    expect(claim.operator).toBe(AFFECTS);
    expect(claim.polarity).toBe("negative");
    expect(claim.qualifiers[POPULATION].restriction.term).toBe("EX:adults");
  });
});

describe("the value types own their invariants", () => {
  it("refuses a referent whose term is not an identifier", () => {
    expect(() => new Referent("testing/entity", 123 as unknown as string)).toThrow(MalformedReferent);
    expect(() => new Referent("testing/entity", "")).toThrow(MalformedReferent);
    expect(() => new Referent("", "EX:gene-x")).toThrow(MalformedReferent);
  });

  it("refuses a qualifier whose restriction is not a Referent", () => {
    expect(() => new Qualifier("generic", "EX:adults" as unknown as Referent)).toThrow(UntypedReferent);
  });

  it("freezes what it mints", () => {
    const claim = affects();
    expect(Object.isFrozen(claim)).toBe(true);
    expect(Object.isFrozen(gene)).toBe(true);
  });
});

describe("the constructor is the only route", () => {
  it("refuses a forged mint token", () => {
    const parts = { operator: AFFECTS, args: [], qualifiers: noQualifiers, polarity: "positive", layer: "causal" };
    expect(() => new Claim(Symbol("forged"), parts)).toThrow(ClaimError);
  });
});
