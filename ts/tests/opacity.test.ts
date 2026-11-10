/**
 * Every route past a type check that this implementation has been shown to have,
 * and the brands and freezes that close them.
 *
 * Each test below **was a working exploit** before the fix, and each produced a
 * value that reached `projectClaim` or `claimIdentity` — so each one is the opacity
 * guarantee failing in a language where `instanceof` was never a check and
 * `readonly` was never a restriction.
 *
 * They arrived in two rounds, and the second round is the more instructive. The
 * first closed three forgeries of the *claim*; the second showed that closing
 * them had moved the forgery one link up the chain rather than ending it, since
 * a brand certifies only what its minting function checked. So the tests are
 * organized by link — value, claim, profile, contract — and the last is the
 * root: what a claim is ultimately typed against is an **authored document**,
 * and every link between the document and the claim has to hold or none of them
 * mean anything.
 *
 * The general lesson, recorded because it is not the Python one: there,
 * `isinstance` is forgeable only through `object.__new__`, which is the same act
 * as a raw write to disk — an audit finding rather than a
 * refusal. Here a derived constructor may `return` an object *instead of*
 * calling `super`, so a forgery needs no unusual call at all. The private-field
 * brand is therefore the load-bearing part on this side, and `readonly` is
 * decoration — while `Object.freeze`, which the first round called decoration
 * too, turns out to be load-bearing wherever a collection is held.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, type ClaimParts, Member, Qualifier, Referent, buildClaim } from "../src/claim.js";
import {
  BaseContract,
  type ClaimGrammar,
  type CompositeGrammar,
  DomainContract,
  type EstimandGrammar,
  parseBaseContract,
  parseDomainContract,
} from "../src/contract.js";
import {
  ClaimError,
  ContractMismatch,
  InadmissibleLayer,
  ProfileError,
  SubclassRefused,
  UninstantiatedTemplate,
  UnparsedContract,
  UntypedReferent,
} from "../src/errors.js";
import {
  type CompiledDimension,
  type CompiledEstimandDecl,
  type CompiledInstantiation,
  type CompiledTemplate,
  ProfileSpec,
  compileProfile,
} from "../src/profile.js";
import { claimIdentity, projectClaim } from "../src/projection.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const read = (relative: string) => readFileSync(new URL(relative, REPO_ROOT), "utf-8");

const baseText = read("contracts/science/CONTRACT.yaml");
const testingText = read("fixtures/contracts/testing.yaml");
const base = parseBaseContract(baseText, "base");
const profile = compileProfile(base, [parseDomainContract(testingText, "testing", base)]);

/** A grammar in which nothing a real contract declares is true. */
const FORGED_GRAMMAR: ClaimGrammar = {
  version: 1,
  quantifiers: ["whatever"],
  polarities: ["yes"],
  signInaptTag: "no",
  layers: ["made-up"],
  forms: ["made-up"],
  roleCategories: ["made-up"],
  bindingKinds: ["made-up"],
  mappingTypes: ["made-up"],
  placements: ["made-up"],
  reservedRoles: { "made-up": { worldKind: "nowhere" } },
};

/** Likewise, for the estimand grammar. */
const FORGED_ESTIMAND_GRAMMAR: EstimandGrammar = {
  version: 1,
  contrastKinds: ["whatever"],
  scales: ["made-up"],
  uncertaintyKinds: ["made-up"],
};

/** Likewise, for the composite grammar. */
const FORGED_COMPOSITE_GRAMMAR: CompositeGrammar = {
  version: 1,
  shapes: ["made-up"],
};

const gene = new Referent("testing/entity", "EX:gene-x");
const otherGene = new Referent("testing/entity", "EX:gene-z");
const outcome = new Referent("testing/outcome", "EX:outcome-y");
const adults = new Referent("testing/cohort", "EX:adults");
const method = new Referent("testing/method", "EX:assay-1");

/** An `affects` claim's parts, with `roles` and `qualifiers` given as records. */
function affectsParts(
  roles: Record<string, Referent | readonly Member[]> = { cause: gene, effect: outcome },
  qualifiers: Record<string, Qualifier> = {},
  layer = "causal",
): ClaimParts {
  return {
    operator: "testing/affects",
    roles: new Map(Object.entries(roles)),
    qualifiers: new Map(Object.entries(qualifiers)),
    form: "polar",
    polarity: "positive",
    layer,
  };
}

describe("a constructor that never runs cannot mint a value", () => {
  /** The forge: a derived constructor returning an object instead of calling `super`. */
  function forge<T>(Base: new (...args: never[]) => T, fields: Record<string, unknown>): T {
    class Rogue extends (Base as new (...args: never[]) => object) {
      constructor() {
        super();
        // The rule this suppresses exists because a constructor returning an object bypasses
        // its own initialization — which is exactly the forge the brands have to survive.
        // biome-ignore lint/correctness/noConstructorReturn: the forge under test
        return Object.create(new.target.prototype);
      }
    }
    const forged = Object.create(Rogue.prototype);
    Object.assign(forged, fields);
    return forged as T;
  }

  it("the forged object still satisfies instanceof, which is the point", () => {
    const bad = forge(Referent, { sort: "testing/entity", term: 123 });
    expect(bad instanceof Referent).toBe(true);
    expect(Referent.is(bad)).toBe(false);
  });

  it("a forged referent cannot fill a role", () => {
    // Before the brand this produced a claim whose projection carried `123`
    // — a trusted claim holding integers where identifiers belong.
    const bad = forge(Referent, { sort: "testing/entity", term: 123 });
    expect(() => buildClaim(profile, affectsParts({ cause: bad, effect: outcome }))).toThrow(UntypedReferent);
    expect(() => buildClaim(profile, affectsParts({ cause: gene, effect: outcome, "within-model": bad }))).toThrow(
      UntypedReferent,
    );
  });

  it("a forged member cannot fill a many role", () => {
    // A member owns its coefficient invariant; a forged one would carry `0` or
    // a JavaScript number into the projection, which then refuses or hashes it.
    const bad = forge(Member, { referent: gene, coefficient: 0 });
    expect(bad instanceof Member).toBe(true);
    expect(Member.is(bad)).toBe(false);
    expect(() =>
      buildClaim(profile, {
        operator: "testing/correlates-with",
        roles: new Map([["parties", [bad, new Member(outcome)]]]),
        qualifiers: new Map(),
        form: "polar",
        polarity: "positive",
        layer: "statistical",
      }),
    ).toThrow(UntypedReferent);
  });

  it("a forged qualifier cannot be selected", () => {
    const bad = forge(Qualifier, { quantifier: "generic", restriction: adults });
    expect(bad instanceof Qualifier).toBe(true);
    expect(() => buildClaim(profile, affectsParts(undefined, { "testing/population": bad }))).toThrow(
      /not a Qualifier/,
    );
  });

  it("a forged claim cannot be projected or hashed", () => {
    const bad = forge(Claim, {
      operator: "x",
      roles: {},
      qualifiers: {},
      form: "polar",
      polarity: "positive",
      layer: "causal",
    });
    expect(bad instanceof Claim).toBe(true);
    expect(() => projectClaim(bad)).toThrow(ClaimError);
    expect(() => claimIdentity(bad)).toThrow(ClaimError);
  });

  it("a subclass cannot be constructed through super either", () => {
    // Closes the ordinary route, so the forge above has to be as contorted as it
    // is. It is the Python `sealed` decorator's job, and only half the fix here.
    class Rogue extends Referent {}
    expect(() => new Rogue("testing/entity", "EX:gene-x")).toThrow(SubclassRefused);
  });
});

describe("the roles and qualifiers a claim holds are genuinely immutable", () => {
  const claim = buildClaim(
    profile,
    affectsParts(undefined, { "testing/population": new Qualifier("generic", adults) }),
  );
  const transforms = buildClaim(profile, {
    operator: "testing/transforms",
    roles: new Map<string, readonly Member[]>([
      ["inputs", [new Member(gene, 2n)]],
      ["outputs", [new Member(otherGene)]],
      ["facilitators", []],
    ]),
    qualifiers: new Map(),
    form: "polar",
    polarity: null,
    layer: "structural",
  });

  it("a caller cannot delete a qualifier and move the claim's identity", () => {
    // `ReadonlyMap` is erased at run time and `Object.freeze` does not reach a
    // Map's entries, so this used to change the identity of a claim someone else
    // was holding.
    const before = claimIdentity(claim);
    expect(() => {
      (claim.qualifiers as Record<string, unknown>)["testing/population"] = undefined;
    }).toThrow(TypeError);
    expect(() => {
      // biome-ignore lint/performance/noDelete: deleting is the attack being refused
      delete (claim.qualifiers as Record<string, unknown>)["testing/population"];
    }).toThrow(TypeError);
    expect(claimIdentity(claim)).toBe(before);
  });

  it("holds them in a frozen null-prototype record", () => {
    expect(Object.isFrozen(claim.qualifiers)).toBe(true);
    expect(Object.getPrototypeOf(claim.qualifiers)).toBe(null);
  });

  it("holds the roles in a frozen null-prototype record", () => {
    const before = claimIdentity(claim);
    expect(Object.isFrozen(claim.roles)).toBe(true);
    expect(Object.getPrototypeOf(claim.roles)).toBe(null);
    expect(() => {
      (claim.roles as Record<string, unknown>).effect = gene;
    }).toThrow(TypeError);
    expect(() => {
      // biome-ignore lint/performance/noDelete: deleting is the attack being refused
      delete (claim.roles as Record<string, unknown>).cause;
    }).toThrow(TypeError);
    expect(claimIdentity(claim)).toBe(before);
  });

  it("keeps each many role's members frozen too", () => {
    const before = claimIdentity(transforms);
    for (const name of ["inputs", "outputs", "facilitators"]) {
      const members = transforms.roles[name] as Member[];
      expect(Object.isFrozen(members)).toBe(true);
      expect(() => members.push(new Member(outcome))).toThrow(TypeError);
    }
    expect(claimIdentity(transforms)).toBe(before);
  });

  it("does not keep the caller's maps or member arrays", () => {
    const qualifiers = new Map([["testing/population", new Qualifier("generic", adults)]]);
    const built = buildClaim(profile, { ...affectsParts(), qualifiers });
    const before = claimIdentity(built);
    qualifiers.delete("testing/population");
    expect(claimIdentity(built)).toBe(before);

    const inputs = [new Member(gene)];
    const roles = new Map<string, readonly Member[]>([
      ["inputs", inputs],
      ["outputs", [new Member(otherGene)]],
      ["facilitators", []],
    ]);
    const reaction = buildClaim(profile, {
      ...affectsParts(),
      operator: "testing/transforms",
      roles,
      polarity: null,
      layer: "structural",
    });
    const reactionBefore = claimIdentity(reaction);
    inputs.push(new Member(new Referent("testing/entity", "EX:smuggled")));
    roles.delete("outputs");
    expect(claimIdentity(reaction)).toBe(reactionBefore);
  });
});

describe("a profile that did not come from the contracts is not a profile", () => {
  const forgedProfile = {
    claimGrammar: FORGED_GRAMMAR,
    estimandGrammar: FORGED_ESTIMAND_GRAMMAR,
    compositeGrammar: FORGED_COMPOSITE_GRAMMAR,
    templates: {
      "forged/op": {
        kind: "template",
        term: "forged/op",
        roles: {},
        signApt: true,
        layers: ["made-up"],
        forms: ["polar"],
        edge: null,
      } satisfies CompiledTemplate,
    },
    instantiations: {},
    bridges: {},
    estimands: {} as Record<string, CompiledEstimandDecl>,
    dimensions: {} as Record<string, CompiledDimension>,
    sorts: {},
    durationConventions: {},
    admission: { "forged/op": [] },
  };

  const parts: ClaimParts = {
    operator: "forged/op",
    roles: new Map([["made-up", new Referent("forged/sort", "X:1")]]),
    qualifiers: new Map(),
    form: "polar",
    polarity: "yes",
    layer: "made-up",
  };

  it("is refused, however well it is shaped", () => {
    // Before the brand this built a claim at an operator no contract declares,
    // on a layer the base contract has never heard of — the SSOT bypassed
    // entirely, and the resulting claim indistinguishable from a real one.
    expect(() => buildClaim(forgedProfile as unknown as ProfileSpec, parts)).toThrow(ProfileError);
    expect(() => buildClaim(forgedProfile as unknown as ProfileSpec, parts)).toThrow(/compileProfile/);
  });

  it("is refused even when it is given the prototype, which is all instanceof asks about", () => {
    // The arm that distinguishes the brand from an `instanceof` check: this
    // object passes the latter and never went near `compileProfile`. Found by
    // mutation — with only the plain literal above, swapping the brand for
    // `instanceof` left the suite green.
    const prototyped = Object.assign(Object.create(ProfileSpec.prototype), forgedProfile);
    expect(prototyped instanceof ProfileSpec).toBe(true);
    expect(ProfileSpec.is(prototyped)).toBe(false);
    expect(() => buildClaim(prototyped as ProfileSpec, parts)).toThrow(ProfileError);
  });

  it("cannot be authored through the constructor either", () => {
    expect(
      () =>
        new ProfileSpec(Symbol("forged"), {
          ...forgedProfile,
          kinds: profile.kinds,
          facets: profile.facets,
          relations: profile.relations,
        }),
    ).toThrow(ProfileError);
  });

  it("recognizes the one compileProfile returns", () => {
    expect(ProfileSpec.is(profile)).toBe(true);
    expect(ProfileSpec.is(forgedProfile)).toBe(false);
  });
});

describe("a contract that nobody authored cannot be compiled", () => {
  // The link above the profile's brand, and the reason that brand was once worth
  // nothing. `compileProfile` accepted structurally typed contracts, so a plain
  // literal minted a *genuine* `ProfileSpec` — `ProfileSpec.is` true, every
  // downstream check satisfied — resolving an operator no document declares. The
  // brand said "compileProfile ran", which was true and useless.
  const forgedBase = {
    name: "science",
    version: 1,
    claimGrammar: FORGED_GRAMMAR,
  };
  const forgedDomain = {
    namespace: "forged",
    version: 1,
    sorts: {},
    dimensions: {},
    templates: {
      op: {
        name: "op",
        roles: {},
        signApt: true,
        layers: ["made-up"],
        forms: ["polar"],
        edge: null,
        definition: null,
        external: null,
      },
    },
  };

  it("refuses an authored base contract", () => {
    expect(() => compileProfile(forgedBase as unknown as BaseContract, [])).toThrow(UnparsedContract);
    expect(() => compileProfile(forgedBase as unknown as BaseContract, [])).toThrow(/parseBaseContract/);
  });

  it("refuses an authored domain contract", () => {
    expect(() => compileProfile(base, [forgedDomain as unknown as DomainContract])).toThrow(UnparsedContract);
    expect(() => compileProfile(base, [forgedDomain as unknown as DomainContract])).toThrow(/parseDomainContract/);
  });

  it("refuses either one wearing the prototype, which is all instanceof would ask about", () => {
    // Both arms, and the second only because the first was written alone: with
    // just the plain literals above, swapping either brand for `instanceof` left
    // the suite green — the literal has no prototype and fails that check too.
    // Third time this exact vacuous test has been caught by mutation.
    const prototypedBase = Object.assign(Object.create(BaseContract.prototype), forgedBase);
    expect(prototypedBase instanceof BaseContract).toBe(true);
    expect(BaseContract.is(prototypedBase)).toBe(false);
    expect(() => compileProfile(prototypedBase as BaseContract, [])).toThrow(UnparsedContract);

    const prototypedDomain = Object.assign(Object.create(DomainContract.prototype), forgedDomain);
    expect(prototypedDomain instanceof DomainContract).toBe(true);
    expect(DomainContract.is(prototypedDomain)).toBe(false);
    expect(() => compileProfile(base, [prototypedDomain as DomainContract])).toThrow(UnparsedContract);
  });

  it("cannot be authored through either constructor", () => {
    expect(
      () =>
        new BaseContract(Symbol("forged"), {
          version: 1,
          claimGrammar: FORGED_GRAMMAR,
          estimandGrammar: FORGED_ESTIMAND_GRAMMAR,
          compositeGrammar: FORGED_COMPOSITE_GRAMMAR,
        }),
    ).toThrow(UnparsedContract);
    expect(
      () =>
        new DomainContract(Symbol("forged"), {
          namespace: "forged",
          version: 1,
          sorts: {},
          dimensions: {},
          templates: {},
          instantiations: {},
          bridges: {},
          estimands: {},
          durationConventions: {},
          facets: {},
          base,
        }),
    ).toThrow(UnparsedContract);
  });

  it("cannot be authored through a subclass either", () => {
    class RogueBase extends BaseContract {}
    class RogueDomain extends DomainContract {}
    expect(
      () =>
        new RogueBase(Symbol("forged"), {
          version: 1,
          claimGrammar: FORGED_GRAMMAR,
          estimandGrammar: FORGED_ESTIMAND_GRAMMAR,
          compositeGrammar: FORGED_COMPOSITE_GRAMMAR,
        }),
    ).toThrow(SubclassRefused);
    expect(
      () =>
        new RogueDomain(Symbol("forged"), {
          namespace: "x",
          version: 1,
          sorts: {},
          dimensions: {},
          templates: {},
          instantiations: {},
          bridges: {},
          estimands: {},
          durationConventions: {},
          facets: {},
          base,
        }),
    ).toThrow(SubclassRefused);
  });

  it("recognizes the ones the parsers return", () => {
    expect(BaseContract.is(base)).toBe(true);
    expect(DomainContract.is(parseDomainContract(testingText, "testing", base))).toBe(true);
  });
});

describe("neither a compiled profile nor its source contract can be edited after the fact", () => {
  // `ReadonlyMap`, `ReadonlySet` and `readonly` are all erased at run time, so
  // before the freezes each of these changed what a *later* claim was allowed to
  // say — while the profile went on carrying a brand attesting to a compilation
  // whose result no longer existed.
  it("refuses a new operator injected into the resolution table", () => {
    expect(() => {
      (profile.templates as Record<string, CompiledTemplate>)["injected/op"] = {
        kind: "template",
        term: "injected/op",
        roles: {},
        signApt: true,
        layers: ["causal"],
        forms: ["polar"],
        edge: null,
      };
    }).toThrow(TypeError);
    expect(() => buildClaim(profile, { ...affectsParts({}), operator: "injected/op" })).toThrow(ProfileError);
  });

  it("refuses a rewritten role sort inside a compiled instantiation", () => {
    // The nested arrays are the part a shallow freeze misses, and the one that
    // re-types an instantiation that is otherwise entirely real.
    const instantiation = profile.instantiations["testing/affects-entity-outcome"] as CompiledInstantiation;
    expect(Object.isFrozen(instantiation)).toBe(true);
    expect(() => {
      (instantiation.roles.cause as string[]).push("testing/outcome");
    }).toThrow(TypeError);
    expect(() => buildClaim(profile, affectsParts({ cause: outcome, effect: outcome }))).toThrow(
      UninstantiatedTemplate,
    );
  });

  it("refuses a rewritten restriction sort inside a compiled dimension", () => {
    // Rewriting it re-types every qualifier on that dimension, across every
    // operator it applies to.
    const dimension = profile.dimensions["testing/population"] as CompiledDimension;
    expect(Object.isFrozen(dimension)).toBe(true);
    expect(() => {
      (dimension as { restrictionSort: string }).restrictionSort = "testing/entity";
    }).toThrow(TypeError);
    expect(() =>
      buildClaim(profile, affectsParts(undefined, { "testing/population": new Qualifier("generic", gene) })),
    ).toThrow(/restricts to sort testing\/cohort/);
  });

  it("refuses a layer smuggled into the base contract after compilation", () => {
    // The source contract and the compiled profile are separate objects, so this
    // one needs both freezes: the grammar the profile holds is the base
    // contract's own, and a template's layers are the profile's copy.
    expect(() => {
      (base.claimGrammar.layers as string[]).push("smuggled");
    }).toThrow(TypeError);
    expect(() => {
      ((profile.templates["testing/affects"] as CompiledTemplate).layers as string[]).push("smuggled");
    }).toThrow(TypeError);
    expect(() => buildClaim(profile, affectsParts(undefined, {}, "smuggled"))).toThrow(InadmissibleLayer);
  });

  it("refuses an operator added to the source contract after compilation", () => {
    const contract = parseDomainContract(testingText, "testing", base);
    const compiled = compileProfile(base, [contract]);
    expect(() => {
      (contract.templates as Record<string, unknown>).smuggled = { name: "smuggled" };
    }).toThrow(TypeError);
    expect(Object.keys(compiled.templates)).not.toContain("testing/smuggled");
  });

  it("holds its tables in frozen null-prototype records", () => {
    for (const table of [profile.templates, profile.bridges, profile.dimensions, profile.sorts]) {
      expect(Object.isFrozen(table)).toBe(true);
      expect(Object.getPrototypeOf(table)).toBe(null);
    }
    expect(Object.isFrozen(profile.sorts)).toBe(true);
    expect(Object.isFrozen(base.claimGrammar)).toBe(true);
  });
});

describe("two genuine contracts that were not typed against each other", () => {
  // Nothing here is forged. Every brand is intact, both parsers ran on real
  // documents, and the claim that came out stood on a layer the compiled base
  // does not declare — because a domain's layers are checked **once**, at parse
  // time, against whatever base it was handed, and the compiled operator then
  // carries them as facts. Provenance checks cannot see this: they authenticate
  // each input and say nothing about whether the two belong together.
  //
  // A domain contract is in scope for that rule on both counts — its validity is
  // conditional on one base, and it reaches `compileProfile` separately from any
  // base — so this boundary verifies the dependency it recorded. A stage that
  // revalidates what it depends on would owe nothing here.
  const wideText = baseText.replace(
    "layers: [causal, structural, statistical, methodological]",
    "layers: [causal, structural, statistical, methodological, speculative]",
  );
  const wideBase = parseBaseContract(wideText, "wide");
  const speculativeText = testingText.replace(
    "layers: [causal, statistical]",
    "layers: [causal, statistical, speculative]",
  );

  it("is refused at compilation", () => {
    const underWide = parseDomainContract(speculativeText, "testing", wideBase);
    expect(underWide.templates.affects.layers).toContain("speculative");
    expect(() => compileProfile(base, [underWide])).toThrow(ContractMismatch);
  });

  it("compiles under the base it was actually parsed against", () => {
    const underWide = parseDomainContract(speculativeText, "testing", wideBase);
    const built = buildClaim(compileProfile(wideBase, [underWide]), affectsParts(undefined, {}, "speculative"));
    expect(projectClaim(built).layer).toBe("speculative");
  });

  it("refuses a base contract the parser did not produce", () => {
    // The parser authenticates its own dependency too: the layer check it runs
    // is worth exactly what the base handed to it is worth.
    const forgedBase = { name: "science", version: 1, claimGrammar: FORGED_GRAMMAR };
    expect(() => parseDomainContract(testingText, "testing", forgedBase as unknown as BaseContract)).toThrow(
      UnparsedContract,
    );
    const prototyped = Object.assign(Object.create(BaseContract.prototype), forgedBase);
    expect(() => parseDomainContract(testingText, "testing", prototyped as BaseContract)).toThrow(UnparsedContract);
  });

  it("records the base it was parsed against", () => {
    expect(parseDomainContract(testingText, "testing", base).base).toBe(base);
  });
});

describe("the checked path still works", () => {
  it("builds, projects and hashes a well-formed claim", () => {
    const claim = buildClaim(profile, {
      operator: "testing/measured-by",
      roles: new Map([
        ["subject", gene],
        ["instrument", method],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: null,
      layer: "methodological",
    });
    expect(projectClaim(claim).roles).toEqual({
      subject: { sort: "testing/entity", term: "EX:gene-x" },
      instrument: { sort: "testing/method", term: "EX:assay-1" },
    });
    expect(claimIdentity(claim)).toMatch(/^[0-9a-f]{64}$/);
  });
});
