/**
 * The validated constructor and the projection, on this side.
 *
 * The parity fixture drives every row through `buildClaim`, but a fixture of
 * well-formed claims can only show that the accepting path agrees. What it
 * cannot show is that the **refusing** path exists at all — a constructor that
 * checked nothing would reproduce every row byte for byte. So the checks are
 * tested directly here, one `it` per check of the typing rule (§5.6) in the
 * order Python's `Claim._checked` runs them, and the pairing is the point: the
 * fixture proves the two implementations agree, and this file proves there is
 * something to agree about.
 *
 * Found by mutation: accepting a hand-supplied `inapt` tag left the whole suite
 * green before this file existed.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, type ClaimParts, Member, Qualifier, Referent, buildClaim } from "../src/claim.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import {
  ClaimError,
  CoefficientRefused,
  DimensionNotClaimSide,
  DuplicateMember,
  FormRefused,
  IdentifierClassMismatch,
  InadmissibleLayer,
  MalformedReferent,
  PolarityRefused,
  ProfileError,
  RestrictionSortMismatch,
  RoleRefused,
  UndeclaredDimension,
  UndeclaredSort,
  UninstantiatedTemplate,
  UnknownQuantifier,
  UntypedQualifier,
  UntypedReferent,
  WithinModelRefused,
} from "../src/errors.js";
import { encode } from "../src/identity/v1.js";
import { admitting, compileProfile } from "../src/profile.js";
import { CLAIM_DOMAIN, claimIdentity, projectClaim } from "../src/projection.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const read = (relative: string) => readFileSync(new URL(relative, REPO_ROOT), "utf-8");

const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
const testing = parseDomainContract(read("fixtures/contracts/testing.yaml"), "testing", base);
const crossing = parseDomainContract(read("fixtures/contracts/crossing.yaml"), "crossing", base);
const profile = compileProfile(base, [testing]);

const AFFECTS = "testing/affects";
const CORRELATES = "testing/correlates-with";
const TRANSFORMS = "testing/transforms";
const MEASURED_BY = "testing/measured-by";
const PROMOTES = "testing/promotes";
const POPULATION = "testing/population";
const SETTING = "testing/setting";
const FOLLOW_UP = "testing/follow-up";
const INAPT = base.claimGrammar.signInaptTag;

const gene = new Referent("testing/entity", "EX:gene-x");
const otherGene = new Referent("testing/entity", "EX:gene-z");
const outcome = new Referent("testing/outcome", "EX:outcome-y");
const method = new Referent("testing/method", "EX:assay-1");
const adults = new Referent("testing/cohort", "EX:adults");
const humans = new Referent("testing/cohort", "EX:humans");
const MODEL = new Referent("testing/procedure-spec", `procedure:${"a".repeat(64)}`);

type Filling = Referent | readonly Member[];

interface Parts {
  operator?: string;
  roles?: Record<string, Filling>;
  qualifiers?: Record<string, Qualifier>;
  form?: string;
  polarity?: string | null;
  layer?: string;
}

/** Python's keyword call, spelled with records; `roles` and `qualifiers` become the Maps `ClaimParts` takes. */
function build(parts: Parts): Claim {
  return buildClaim(profile, toParts(parts));
}

function toParts(parts: Parts): ClaimParts {
  return {
    operator: parts.operator ?? AFFECTS,
    roles: new Map(Object.entries(parts.roles ?? { cause: gene, effect: outcome })),
    qualifiers: new Map(Object.entries(parts.qualifiers ?? {})),
    form: parts.form ?? "polar",
    polarity: parts.polarity === undefined ? "positive" : parts.polarity,
    layer: parts.layer ?? "causal",
  };
}

const parties = (...referents: Referent[]) => ({ parties: referents.map((r) => new Member(r)) });
const correlates = (roles: Record<string, Filling>, extra: Parts = {}) =>
  build({ operator: CORRELATES, roles, layer: "statistical", ...extra });
const transforms = (roles: Record<string, Filling>, layer = "structural") =>
  build({ operator: TRANSFORMS, roles, polarity: null, layer });
const measured = () =>
  build({
    operator: MEASURED_BY,
    roles: { subject: gene, instrument: method },
    polarity: null,
    layer: "methodological",
  });

describe("the checks follow the typing rule, in order", () => {
  it("(1) refuses an unresolvable operator, and not as a ClaimError", () => {
    expect(() => build({ operator: "testing/absent" })).toThrow(ProfileError);
    expect(() => build({ operator: "testing/absent" })).toThrow(/no operator/);
  });

  it("(2) refuses a missing role", () => {
    expect(() => build({ roles: { cause: gene } })).toThrow(RoleRefused);
    expect(() => build({ roles: { cause: gene } })).toThrow(/effect/);
  });

  it("(2) refuses an undeclared role", () => {
    expect(() => build({ roles: { cause: gene, effect: outcome, bystander: gene } })).toThrow(RoleRefused);
    expect(() => build({ roles: { cause: gene, effect: outcome, bystander: gene } })).toThrow(/bystander/);
  });

  it("(2) takes the roles as a mapping, never a sequence", () => {
    for (const roles of [[gene, outcome], { cause: gene, effect: outcome }]) {
      const parts = { ...toParts({}), roles: roles as unknown as ClaimParts["roles"] };
      expect(() => buildClaim(profile, parts)).toThrow(RoleRefused);
      expect(() => buildClaim(profile, parts)).toThrow(/mapping/);
    }
  });

  it("(3) refuses a bare string in a one role", () => {
    expect(() => build({ roles: { cause: "EX:gene-x" as unknown as Referent, effect: outcome } })).toThrow(
      UntypedReferent,
    );
  });

  it("(3) refuses members in a one role", () => {
    expect(() => build({ roles: { cause: [new Member(gene)], effect: outcome } })).toThrow(UntypedReferent);
  });

  it("(3) a many role holds members, never a referent, a string or bare referents", () => {
    for (const value of [gene, "EX:gene-x", [gene, outcome]]) {
      expect(() => correlates({ parties: value as unknown as Filling })).toThrow(UntypedReferent);
    }
  });

  it("(3) refuses a member count outside the role's bounds as RoleRefused", () => {
    for (const count of [1, 3]) {
      const members = Array.from(
        { length: count },
        (_, i) => new Member(new Referent("testing/entity", `EX:gene-${i}`)),
      );
      expect(() => correlates({ parties: members })).toThrow(RoleRefused);
      expect(() => correlates({ parties: members })).toThrow(/\[2, 2\]/);
    }
  });

  it("(3) refuses an empty min-one role", () => {
    expect(() => transforms({ inputs: [], outputs: [new Member(gene)], facilitators: [] })).toThrow(RoleRefused);
    expect(() => transforms({ inputs: [], outputs: [new Member(gene)], facilitators: [] })).toThrow(/inputs/);
  });

  it("(3) refuses a coefficient other than 1 where the role admits none", () => {
    expect(() => correlates({ parties: [new Member(gene, 2n), new Member(outcome)] })).toThrow(CoefficientRefused);
    expect(() =>
      transforms({
        inputs: [new Member(gene)],
        outputs: [new Member(otherGene)],
        facilitators: [new Member(gene, 2n)],
      }),
    ).toThrow(CoefficientRefused);
    const admitted = transforms({
      inputs: [new Member(gene, 2n)],
      outputs: [new Member(otherGene, 3n)],
      facilitators: [],
    });
    expect((admitted.roles.inputs as readonly Member[]).map((m) => [m.referent, m.coefficient])).toEqual([[gene, 2n]]);
  });

  it("(3) refuses a duplicate member by its NFC key (case 2a)", () => {
    const composed = new Referent("testing/event", "EX:café".normalize("NFC"));
    const decomposed = new Referent("testing/event", "EX:café".normalize("NFD"));
    expect(composed.term).not.toBe(decomposed.term);
    expect(() => correlates(parties(composed, decomposed))).toThrow(DuplicateMember);
  });

  it("(4) refuses an undeclared sort", () => {
    expect(() => build({ roles: { cause: new Referent("testing/absent", "EX:gene-x"), effect: outcome } })).toThrow(
      UndeclaredSort,
    );
  });

  it("(4) refuses an undeclared restriction sort too", () => {
    const qualifiers = { [POPULATION]: new Qualifier("generic", new Referent("testing/absent", "EX:adults")) };
    expect(() => build({ qualifiers })).toThrow(UndeclaredSort);
  });

  it("(4) refuses a term outside its sort's identifier class, restrictions included (case 5)", () => {
    // `EX:ABC` is outside entity's narrow class and inside cohort's wide one.
    expect(() => build({ roles: { cause: new Referent("testing/entity", "EX:ABC"), effect: outcome } })).toThrow(
      IdentifierClassMismatch,
    );
    expect(() => build({ roles: { cause: new Referent("testing/entity", "EX:ABC"), effect: outcome } })).toThrow(
      /EX:ABC/,
    );
    const accepted = build({
      qualifiers: { [POPULATION]: new Qualifier("generic", new Referent("testing/cohort", "EX:ABC")) },
    });
    expect(accepted.qualifiers[POPULATION].restriction.term).toBe("EX:ABC");
    expect(() =>
      build({ qualifiers: { [POPULATION]: new Qualifier("generic", new Referent("testing/cohort", "OTHER:ABC")) } }),
    ).toThrow(IdentifierClassMismatch);
  });

  it("(4) checks a world-kind sort's term for record-id syntax only (case 7)", () => {
    for (const term of [`procedure:${"A".repeat(64)}`, `procedure:${"a".repeat(63)}`, `run:${"a".repeat(64)}`]) {
      expect(() =>
        build({
          roles: { cause: gene, effect: outcome, "within-model": new Referent("testing/procedure-spec", term) },
        }),
      ).toThrow(IdentifierClassMismatch);
    }
    // No snapshot is consulted: any well-formed id of the kind is accepted.
    const accepted = build({ roles: { cause: gene, effect: outcome, "within-model": MODEL } });
    expect(accepted.roles["within-model"]).toBe(MODEL);
  });

  it("(4) refuses a within-model referent whose sort does not bind world-kind procedure", () => {
    expect(() =>
      build({ roles: { cause: gene, effect: outcome, "within-model": new Referent("testing/entity", "EX:model-x") } }),
    ).toThrow(WithinModelRefused);
  });

  it("(5) refuses an assignment no instantiation admits (case 4)", () => {
    expect(() => build({ roles: { cause: outcome, effect: outcome } })).toThrow(UninstantiatedTemplate);
  });

  it("(5) admits a bridge by its own role sorts", () => {
    // `affects-entity-entity` admits `effect: entity` on the template; the bridge
    // lists only `outcome`, so the same assignment refuses on it.
    build({ roles: { cause: gene, effect: gene } });
    expect(() => build({ operator: PROMOTES, roles: { cause: gene, effect: gene } })).toThrow(UninstantiatedTemplate);
    expect(() => build({ operator: PROMOTES, roles: { cause: gene, effect: gene } })).toThrow(/^bridge/);
  });

  it("(5) builds a claim two instantiations admit (case 4, R7)", () => {
    build({});
    const assignment = new Map([
      ["cause", new Set(["testing/entity"])],
      ["effect", new Set(["testing/outcome"])],
    ]);
    expect(admitting(profile, AFFECTS, assignment)).toEqual([
      "instantiation:testing/affects-entity-entity",
      "instantiation:testing/affects-entity-outcome",
    ]);
  });

  it("(5) admits a many role by every member's sort", () => {
    correlates(parties(outcome, gene));
    expect(() => correlates(parties(gene, new Referent("testing/event", "EX:event-1")))).toThrow(
      UninstantiatedTemplate,
    );
  });

  it("(6) refuses an applicability-side dimension among the qualifiers (case 8)", () => {
    const qualifiers = { [FOLLOW_UP]: new Qualifier("generic", new Referent("testing/level", "EX:week-12")) };
    expect(() => build({ qualifiers })).toThrow(DimensionNotClaimSide);
  });

  it("(6) refuses a dimension whose applies_to omits the operator (case 8)", () => {
    const qualifiers = { [SETTING]: new Qualifier("generic", gene) };
    expect(() => correlates(parties(gene, outcome), { qualifiers })).toThrow(UndeclaredDimension);
    expect(() => correlates(parties(gene, outcome), { qualifiers })).toThrow(/does not apply/);
  });

  it("(6) refuses an undeclared dimension", () => {
    const qualifiers = { "testing/absent": new Qualifier("generic", adults) };
    expect(() => build({ qualifiers })).toThrow(UndeclaredDimension);
    expect(() => build({ qualifiers })).toThrow(/no dimension/);
  });

  it("(6) admits a foreign dimension whose applies_to names the operator (Review Focus 4)", () => {
    const both = compileProfile(base, [testing, crossing]);
    const local = new Referent("crossing/local-entity", "EX:local-1");
    const claim = buildClaim(both, {
      ...toParts({ roles: { cause: gene, effect: local } }),
      qualifiers: new Map([["crossing/scope", new Qualifier("generic", adults)]]),
    });
    expect(Object.keys(claim.qualifiers)).toEqual(["crossing/scope"]);
  });

  it("(6) refuses a wrongly sorted restriction", () => {
    // population restricts to cohort.
    expect(() => build({ qualifiers: { [POPULATION]: new Qualifier("generic", gene) } })).toThrow(
      RestrictionSortMismatch,
    );
  });

  it("(6) refuses a quantifier outside the closed set", () => {
    expect(() => build({ qualifiers: { [POPULATION]: new Qualifier("mostly", adults) } })).toThrow(UnknownQuantifier);
  });

  it("(6) refuses a qualifier impostor", () => {
    const impostor = { quantifier: "generic", restriction: adults } as unknown as Qualifier;
    expect(() => build({ qualifiers: { [POPULATION]: impostor } })).toThrow(UntypedQualifier);
  });

  it("(7) admits null only where the template declares it, with no polarity (case 6)", () => {
    // `measured-by` is sign-inapt and declares only `polar`.
    expect(() =>
      build({
        operator: MEASURED_BY,
        roles: { subject: gene, instrument: method },
        form: "null",
        polarity: null,
        layer: "methodological",
      }),
    ).toThrow(FormRefused);
    expect(() => build({ form: "absent" })).toThrow(FormRefused);
    const nullForm = build({ form: "null", polarity: null });
    expect(nullForm.form).toBe("null");
    expect(nullForm.polarity).toBe(INAPT);
    for (const supplied of ["positive", "unsigned", INAPT]) {
      expect(() => build({ form: "null", polarity: supplied })).toThrow(PolarityRefused);
    }
  });

  it("(8) refuses an inadmissible layer, a bridge's own narrowing included", () => {
    expect(() => build({ layer: "structural" })).toThrow(InadmissibleLayer);
    expect(() => build({ operator: PROMOTES, layer: "statistical" })).toThrow(InadmissibleLayer);
  });

  it("admits within-model on a template and on a bridge (Review Focus 5)", () => {
    const onTemplate = build({ roles: { cause: gene, effect: outcome, "within-model": MODEL } });
    const onBridge = build({ operator: PROMOTES, roles: { cause: gene, effect: outcome, "within-model": MODEL } });
    expect(onTemplate.roles["within-model"]).toBe(MODEL);
    expect(onBridge.roles["within-model"]).toBe(MODEL);
    expect(() => build({ roles: { cause: gene, effect: outcome, "within-model": [new Member(MODEL)] } })).toThrow(
      UntypedReferent,
    );
  });

  it("builds an empty min-zero role (case 4a)", () => {
    const claim = transforms({ inputs: [new Member(gene)], outputs: [new Member(otherGene)], facilitators: [] });
    expect(claim.roles.facilitators).toEqual([]);
  });

  it("holds a many role in canonical order", () => {
    const forward = correlates(parties(gene, outcome));
    const reverse = correlates(parties(outcome, gene));
    expect(forward.roles.parties).toEqual(reverse.roles.parties);
    expect((forward.roles.parties as readonly Member[]).map((m) => m.referent)).toEqual([gene, outcome]);
  });

  it("accepts a well-formed claim whole", () => {
    const claim = build({ qualifiers: { [POPULATION]: new Qualifier("universal", adults) }, polarity: "negative" });
    expect(claim.operator).toBe(AFFECTS);
    expect({ ...claim.roles }).toEqual({ cause: gene, effect: outcome });
    expect(claim.qualifiers[POPULATION].restriction.term).toBe("EX:adults");
    expect([claim.form, claim.polarity, claim.layer]).toEqual(["polar", "negative", "causal"]);
  });
});

describe("polarity is the unit inhabitant where there is no sign", () => {
  it("fills the sign-inapt tag when nothing is supplied", () => {
    const claim = measured();
    expect(claim.polarity).toBe(INAPT);
    expect(base.claimGrammar.polarities).not.toContain(claim.polarity);
  });

  it("refuses a sign on a sign-inapt operator, `unsigned` and the tag itself included", () => {
    for (const polarity of ["positive", "unsigned", INAPT]) {
      expect(() =>
        build({
          operator: MEASURED_BY,
          roles: { subject: gene, instrument: method },
          polarity,
          layer: "methodological",
        }),
      ).toThrow(/unit type/);
    }
  });

  it("requires one where the operator has a sign", () => {
    expect(() => build({ polarity: null })).toThrow(/sign-apt/);
    expect(() => build({ polarity: INAPT })).toThrow(PolarityRefused);
    expect(build({ polarity: "unsigned" }).polarity).toBe("unsigned");
  });
});

describe("the projection under science.claim.v2", () => {
  it("is in the v2 domain", () => {
    expect(CLAIM_DOMAIN).toBe("science.claim.v2");
  });

  it("has the v2 shape: roles by name, members with coefficients, sorted restrictions", () => {
    const claim = correlates(parties(outcome, gene), {
      qualifiers: { [POPULATION]: new Qualifier("generic", adults) },
    });
    expect(projectClaim(claim)).toEqual({
      operator: CORRELATES,
      roles: {
        parties: [
          { sort: "testing/entity", term: "EX:gene-x", coefficient: 1n },
          { sort: "testing/outcome", term: "EX:outcome-y", coefficient: 1n },
        ],
      },
      qualifiers: {
        [POPULATION]: { quantifier: "generic", restriction: { sort: "testing/cohort", term: "EX:adults" } },
      },
      form: "polar",
      polarity: "positive",
      layer: "statistical",
    });
  });

  it("projects a one role as a referent object", () => {
    expect(projectClaim(build({})).roles).toEqual({
      cause: { sort: "testing/entity", term: "EX:gene-x" },
      effect: { sort: "testing/outcome", term: "EX:outcome-y" },
    });
  });

  it("projects a coefficient as an integer", () => {
    const claim = transforms({ inputs: [new Member(gene, 2n)], outputs: [new Member(otherGene)], facilitators: [] });
    const text = new TextDecoder().decode(encode(projectClaim(claim)));
    expect(text).toContain('"inputs":[{"coefficient":2,');
    expect(text).toContain('"outputs":[{"coefficient":1,');
  });

  it("projects an empty many role as [] (case 4a)", () => {
    const claim = transforms({ inputs: [new Member(gene)], outputs: [new Member(otherGene)], facilitators: [] });
    expect(projectClaim(claim).roles.facilitators).toEqual([]);
    expect(new TextDecoder().decode(encode(projectClaim(claim)))).toContain('"facilitators":[]');
  });

  it("gives a many role written in either order one identity (cases 2, 3)", () => {
    expect(claimIdentity(correlates(parties(gene, outcome)))).toBe(claimIdentity(correlates(parties(outcome, gene))));
  });

  it("cannot hold one referent twice beside its coefficient-2 form (case 2)", () => {
    const co = new Referent("testing/entity", "EX:co");
    transforms({ inputs: [new Member(co, 2n)], outputs: [new Member(gene)], facilitators: [] });
    expect(() =>
      transforms({ inputs: [new Member(co), new Member(co)], outputs: [new Member(gene)], facilitators: [] }),
    ).toThrow(DuplicateMember);
  });

  it("orders members by canonical key, not raw spelling or UTF-16 units (case 2a)", () => {
    // Raw, the decomposed `é` sorts before `f` and the composed one after it.
    const spelt = (form: "NFC" | "NFD") =>
      correlates(parties(new Referent("testing/event", "EX:é".normalize(form)), new Referent("testing/event", "EX:f")));
    expect(claimIdentity(spelt("NFC"))).toBe(claimIdentity(spelt("NFD")));
    const bmp = new Referent("testing/event", "EX:～");
    const astral = new Referent("testing/event", "EX:\u{1f600}");
    expect(astral.term < bmp.term).toBe(true);
    const projected = projectClaim(correlates(parties(astral, bmp))).roles.parties as { term: string }[];
    expect(projected.map((m) => m.term)).toEqual([bmp.term, astral.term]);
  });

  it("changes with the sort identifier alone (case 1)", () => {
    const asOutcome = build({ roles: { cause: gene, effect: new Referent("testing/outcome", "EX:thing") } });
    const asEntity = build({ roles: { cause: gene, effect: new Referent("testing/entity", "EX:thing") } });
    expect(claimIdentity(asOutcome)).not.toBe(claimIdentity(asEntity));
  });

  it("changes with the form (case 6)", () => {
    expect(claimIdentity(build({ form: "null", polarity: null }))).not.toBe(
      claimIdentity(build({ polarity: "unsigned" })),
    );
  });

  it("changes with within-model (case 7)", () => {
    const within = build({ roles: { cause: gene, effect: outcome, "within-model": MODEL } });
    expect(claimIdentity(within)).not.toBe(claimIdentity(build({})));
    expect(projectClaim(within).roles["within-model"]).toEqual({ sort: MODEL.sort, term: MODEL.term });
  });

  it("separates a bridge claim from its template's (case 9)", () => {
    expect(claimIdentity(build({ operator: PROMOTES }))).not.toBe(claimIdentity(build({})));
  });

  it("forks on the restriction and on the quantifier", () => {
    const at = (quantifier: string, restriction: Referent) =>
      claimIdentity(build({ qualifiers: { [POPULATION]: new Qualifier(quantifier, restriction) } }));
    expect(at("generic", adults)).not.toBe(at("generic", humans));
    expect(at("generic", adults)).not.toBe(at("universal", adults));
    expect(at("generic", adults)).not.toBe(claimIdentity(build({})));
  });

  it("keeps form and polarity present at a sign-inapt operator", () => {
    const projected = projectClaim(measured());
    expect(Object.keys(projected).sort()).toEqual(["form", "layer", "operator", "polarity", "qualifiers", "roles"]);
    expect([projected.form, projected.polarity]).toEqual(["polar", INAPT]);
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
    const claim = build({});
    expect(Object.isFrozen(claim)).toBe(true);
    expect(Object.isFrozen(claim.roles)).toBe(true);
    expect(Object.isFrozen(gene)).toBe(true);
  });
});

describe("the constructor is the only route", () => {
  it("refuses a forged mint token", () => {
    const parts = { ...toParts({}), polarity: "positive" };
    expect(() => new Claim(Symbol("forged"), parts)).toThrow(ClaimError);
  });
});
