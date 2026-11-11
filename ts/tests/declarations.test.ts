import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, ProfileError } from "../src/errors.js";
import {
  admitting,
  claimDimensions,
  compileProfile,
  declarationAt,
  estimandDeclarations,
  resolveOperator,
  templateOf,
} from "../src/profile.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const SHIPPED = readFileSync(new URL("contracts/science/CONTRACT.yaml", REPO_ROOT), "utf-8");

describe("document load refuses duplicate keys", () => {
  it("refuses a duplicate top-level key rather than keeping the last", () => {
    const text = "contract: science\ncontract: science\nversion: 1\nclaim_grammar: {}\n";
    expect(() => parseBaseContract(text, "<dup>")).toThrow(/unique/i);
  });
});

describe("the base contract's declarations", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  it("declares twenty-one world kinds and three prose kinds", () => {
    expect(Object.values(base.kinds).filter((kind) => kind.role === "world")).toHaveLength(21);
    expect(Object.values(base.kinds).filter((kind) => kind.role === "prose")).toHaveLength(3);
    expect(base.kinds["instrument-certification"].domain).toBeNull();
    expect(base.kinds["coreference-attestation"].domain).toBe("science.coreference-attestation.v1");
  });
  it("declares the composite grammar and the same-kind rule on supersedes", () => {
    expect(base.compositeGrammar).toEqual({ version: 1, shapes: ["dag"] });
    expect(base.relations.supersedes.sameKind).toBe(true);
    expect(base.relations.composes.sameKind).toBe(false);
    expect(base.relations.composes.targets).toEqual(["proposition"]);
    expect(base.relations.supersedes.sources).toEqual(["proposition", "composite", "reservation-assignment"]);
    expect(base.relations.considers.targets).toEqual(["exposure-event"]);
  });
  it("refuses same_kind where sources and targets differ", () => {
    const line = "composes: { group: world, sources: [composite], targets: [proposition] }";
    expect(SHIPPED).toContain(line); // the mutation must land, or the assertion below asserts nothing
    const bad = SHIPPED.replace(
      line,
      "composes: { group: world, sources: [composite], targets: [proposition], same_kind: true }",
    );
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/same_kind/);
  });
  it("refuses a composes signature outside composite to proposition", () => {
    const line = "composes: { group: world, sources: [composite], targets: [proposition] }";
    expect(SHIPPED).toContain(line); // the mutations must land, or the assertions below assert nothing
    for (const mutated of [
      "composes: { group: world, sources: [composite, proposition], targets: [proposition] }",
      "composes: { group: world, sources: [composite], targets: [proposition, composite] }",
      "composes: { group: world, sources: [proposition], targets: [composite] }",
    ]) {
      expect(() => parseBaseContract(SHIPPED.replace(line, mutated), "<bad>")).toThrow(/one signature and no other/);
    }
  });
  it("refuses an unsupported shape", () => {
    const line = "  shapes: [dag]\n";
    expect(SHIPPED).toContain(line);
    expect(() => parseBaseContract(SHIPPED.replace(line, "  shapes: [dag, pag]\n"), "<bad>")).toThrow(/pag/);
  });
  it("refuses a base contract without the composite grammar", () => {
    const block = "composite_grammar:\n  version: 1\n  shapes: [dag]\n";
    expect(SHIPPED).toContain(block);
    expect(() => parseBaseContract(SHIPPED.replace(block, ""), "<bad>")).toThrow(/composite_grammar/);
  });
  it("declares empirical-observation as the one schema-shaped facet", () => {
    expect(
      Object.values(base.facets)
        .filter((facet) => facet.shape === "schema")
        .map((facet) => facet.key),
    ).toEqual(["empirical-observation"]);
    expect(base.facets["empirical-observation"].fields.locator.schemes).toEqual(["accession", "url", "instrument"]);
  });
  it("refuses kinds on a non-ref field", () => {
    const bad = SHIPPED.replace(
      "attested_by: { type: actor, required: true }",
      "attested_by: { type: actor, required: true, kinds: [x] }",
    );
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/kinds/);
  });
  it("refuses a relation outside the two groups", () => {
    const bad = SHIPPED.replace("observes: { group: world,", "observes: { group: other,");
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/group/);
  });
  it("declares the current retraction endpoint closure", () => {
    expect(base.relations.retracts.sources).toEqual(["retraction"]);
    expect(base.relations.retracts.targets).toEqual([
      "assessment",
      "retraction",
      "verification",
      "procedure",
      "referent-mapping",
      "proxy-model",
      "classification-rule",
      "assumptions-register",
    ]);
  });
  it("matches Python's semantic-domain, description, and null-facet refusals", () => {
    expect(() =>
      parseBaseContract(SHIPPED.replace("domain: science.dataset.v1", "domain: dataset-v1"), "<bad>"),
    ).toThrow(/science\.<kind>\.v<n>/);
    expect(() =>
      parseBaseContract(
        SHIPPED.replace(
          "description: The declared acquisition boundary",
          "description: 7\n    x-ignored: The declared acquisition boundary",
        ),
        "<bad>",
      ),
    ).toThrow(/description|unknown/);
    expect(() => parseBaseContract(`${SHIPPED.split("\nfacets:")[0]}\nfacets: null\n`, "<bad>")).toThrow(/mapping/);
  });
  it.each(["dataset", "discussion"])("refuses explicit null %s.facets", (kind) => {
    const document = parse(SHIPPED);
    document.kinds[kind].facets = null;
    expect(() => parseBaseContract(stringify(document), "<bad>")).toThrow(/facets.*mapping/);
  });
  it("declares the three prose kinds with display only", () => {
    expect(base.kinds.discussion.role).toBe("prose");
    expect(Object.keys(base.kinds.discussion.facets)).toEqual(["display"]);
  });
  it("declares the v2 estimand grammar", () => {
    expect(base.estimandGrammar.version).toBe(2);
    expect(base.estimandGrammar.forms).toEqual([
      "contrast",
      "quantity",
      "law-parameters",
      "event-locked",
      "association",
      "enrichment",
    ]);
    expect(base.estimandGrammar.uncertaintyKinds).toEqual(["interval", "standard-error", "covariance"]);
  });
  it("refuses wider v2 tags and the v1 field set", () => {
    const wide = parse(SHIPPED);
    wide.estimand_grammar.forms.push("rank-contrast");
    expect(() => parseBaseContract(stringify(wide), "<wide>")).toThrow();
    const old = parse(SHIPPED);
    old.estimand_grammar = {
      version: 1,
      tag_encoding: "science.identity.v1",
      contrast_kinds: ["levels", "continuous"],
      scales: ["additive", "multiplicative"],
      uncertainty_kinds: ["interval", "standard-error"],
    };
    expect(() => parseBaseContract(stringify(old), "<old>")).toThrow();
  });
  it("declares the measurement grammar's nine closed sets", () => {
    expect(base.measurementGrammar).toEqual({
      version: 1,
      valueTypes: ["level", "difference", "ratio"],
      levelsOfMeasurement: ["nominal", "ordinal", "interval", "ratio"],
      scaleOrientations: ["higher-is-more", "higher-is-less"],
      transformationKinds: ["identity", "affine", "logarithm", "monotone"],
      monotoneDirections: ["increasing", "decreasing"],
      transformationDomains: ["real", "nonnegative", "positive", "unit-interval"],
      conversionKinds: ["multiplicative", "affine"],
      cardinalities: ["one-to-one", "many-to-one", "one-to-many", "many-to-many"],
      evidenceModes: ["observation", "annotation", "simulation", "derivation", "literature-extraction"],
    });
    expect(Object.isFrozen(base.measurementGrammar)).toBe(true);
    expect(Object.isFrozen(base.measurementGrammar.valueTypes)).toBe(true);
  });
  it("refuses a measurement closed set wider than the kernel's", () => {
    const document = parse(SHIPPED);
    document.measurement_grammar.value_types.push("count");
    expect(() => parseBaseContract(stringify(document), "<bad>")).toThrow(/count/);
  });
  it("refuses a base contract without the measurement grammar", () => {
    const document = parse(SHIPPED);
    document.measurement_grammar = undefined;
    expect(() => parseBaseContract(stringify(document), "<missing>")).toThrow(/measurement_grammar/);
  });
  it.each([0, true, "1", 2])("refuses measurement grammar version %s", (version) => {
    const document = parse(SHIPPED);
    document.measurement_grammar.version = version;
    expect(() => parseBaseContract(stringify(document), "<bad>")).toThrow(/version/);
  });
  it("declares the v2 claim grammar's closed sets", () => {
    const grammar = base.claimGrammar;
    expect(base.version).toBe(2);
    expect(grammar.version).toBe(2);
    expect(grammar.forms).toEqual(["polar", "null"]);
    expect(grammar.roleCategories).toEqual(["set", "temporal", "class", "pattern"]);
    expect(grammar.bindingKinds).toEqual(["release", "dataset", "scheme", "selection", "run-output", "world-kind"]);
    expect(grammar.mappingTypes).toEqual(["exact", "narrower", "broader", "contextual"]);
    expect(grammar.placements).toEqual(["claim", "applicability"]);
    expect(grammar.reservedRoles).toEqual({ "within-model": { worldKind: "procedure" } });
    expect(Object.isFrozen(grammar.reservedRoles)).toBe(true);
    expect(Object.isFrozen(grammar.reservedRoles["within-model"])).toBe(true);
  });
  it("declares the register and four measurement world kinds", () => {
    expect(base.kinds["assumptions-register"].domain).toBe("science.assumptions-register.v1");
    expect(base.kinds["assumptions-register"].facets["assumptions-register"]).toEqual({
      required: true,
      covered: true,
    });
    expect(base.facets["assumptions-register"].shape).toBe("reader");
    for (const name of ["procedure", "referent-mapping", "proxy-model", "classification-rule"]) {
      expect(base.kinds[name].role).toBe("world");
      expect(base.kinds[name].domain).toBe(`science.${name}.v1`);
      expect(base.kinds[name].facets).toEqual({ [name]: { required: true, covered: true } });
      expect(base.facets[name].shape).toBe("reader");
    }
  });
  it("refuses a widened form set", () => {
    const bad = SHIPPED.replace('forms: [polar, "null"]', 'forms: [polar, "null", value]');
    expect(bad).not.toBe(SHIPPED);
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/forms/);
  });
  it("refuses a YAML null inside a closed set", () => {
    const bad = SHIPPED.replace('forms: [polar, "null"]', "forms: [polar, null]");
    expect(bad).not.toBe(SHIPPED);
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/forms/);
  });
  it("refuses a narrowed binding-kind set", () => {
    const bad = SHIPPED.replace(
      "binding_kinds: [release, dataset, scheme, selection, run-output, world-kind]",
      "binding_kinds: [release, dataset, scheme, selection, run-output]",
    );
    expect(bad).not.toBe(SHIPPED);
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/binding_kinds/);
  });
  it.each([
    ["role_categories", "role_categories: [set, temporal, class, pattern]", "role_categories: [set, temporal, class]"],
    [
      "mapping_types",
      "mapping_types: [exact, narrower, broader, contextual]",
      "mapping_types: [exact, narrower, broader, contextual, related]",
    ],
    ["placements", "placements: [claim, applicability]", "placements: [claim]"],
  ])("refuses a %s set other than the operated one", (name, line, mutated) => {
    const bad = SHIPPED.replace(line, mutated);
    expect(bad).not.toBe(SHIPPED);
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(new RegExp(name));
  });
  it("refuses a reserved role naming no declared world kind", () => {
    for (const kind of ["nowhere", "discussion"]) {
      const bad = SHIPPED.replace("within-model: { world_kind: procedure }", `within-model: { world_kind: ${kind} }`);
      expect(bad).not.toBe(SHIPPED);
      expect(() => parseBaseContract(bad, "<bad>")).toThrow(new RegExp(kind));
    }
  });
  it("refuses a malformed reserved role entry", () => {
    for (const entry of ["null", "{}", "{ world_kind: procedure, extra: 1 }", "{ world_kind: null }"]) {
      const bad = SHIPPED.replace("within-model: { world_kind: procedure }", `within-model: ${entry}`);
      expect(() => parseBaseContract(bad, "<bad>")).toThrow(/reserved_roles/);
    }
  });
  it("refuses a claim grammar version other than 2", () => {
    for (const version of ["1", "3"]) {
      const bad = SHIPPED.replace(/claim_grammar:\n {2}version: 2/, `claim_grammar:\n  version: ${version}`);
      expect(bad).not.toBe(SHIPPED);
      expect(() => parseBaseContract(bad, "<bad>")).toThrow(/claim_grammar\.version/);
    }
  });
  it("refuses a base contract without the estimand grammar", () => {
    const document = parse(SHIPPED);
    delete document.estimand_grammar;
    const missing = stringify(document);
    expect(() => parseBaseContract(missing, "<missing>")).toThrow(/estimand_grammar/);
  });
});

describe("a domain contract's facets", () => {
  const TESTING = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  it("namespaces facet keys and carries attaches_to", () => {
    const domain = parseDomainContract(TESTING, "fixtures/contracts/testing.yaml", base);
    expect(Object.keys(domain.facets).sort()).toEqual(["testing/annotation", "testing/axis"]);
    expect(domain.facets["testing/axis"].attachesTo).toEqual(["dataset"]);
  });
  it("refuses kinds and relations in a domain contract", () => {
    expect(() => parseDomainContract(`${TESTING}\nkinds: {}\n`, "<bad>", base)).toThrow(/declares no kinds/);
    expect(() => parseDomainContract(`${TESTING}\nrelations: {}\n`, "<bad>", base)).toThrow(/declares no relations/);
  });
  it("carries an edge on a causal template, by role, and compiles it there", () => {
    const domain = parseDomainContract(TESTING, "fixtures/contracts/testing.yaml", base);
    expect(domain.templates.affects.edge).toEqual({ cause: "cause", effect: "effect" });
    const line = "edge: { cause: cause, effect: effect }";
    expect(TESTING).toContain(line);
    expect(() =>
      parseDomainContract(TESTING.replace(line, "edge: { cause: cause, effect: cause }"), "<bad>", base),
    ).toThrow(/distinct/);
    expect(() =>
      parseDomainContract(TESTING.replace(line, "edge: { cause: agent, effect: effect }"), "<bad>", base),
    ).toThrow(/agent/);
    const profile = compileProfile(base, [domain]);
    expect(profile.templates["testing/affects"].edge).toEqual({ cause: "cause", effect: "effect" });
    expect(profile.templates["testing/correlates-with"].edge).toBeNull();
  });
});

describe("compileProfile resolves the v2 declarations", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  const TESTING = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  const CROSSING = readFileSync(new URL("fixtures/contracts/crossing.yaml", REPO_ROOT), "utf-8");
  const OTHER = TESTING.replace("contract: testing", "contract: elsewhere");
  const testing = parseDomainContract(TESTING, "<testing>", base);
  const crossing = parseDomainContract(CROSSING, "<crossing>", base);
  const other = parseDomainContract(OTHER, "<elsewhere>", base);
  const compiled = compileProfile(base, [testing]);
  const ENTITY = new Set(["testing/entity"]);
  const OUTCOME = new Set(["testing/outcome"]);
  const assign = (roles: Record<string, ReadonlySet<string>>) => new Map(Object.entries(roles));

  // biome-ignore lint/suspicious/noExplicitAny: a YAML document mutated by path, as the Python tests mutate a dict
  const compileMutated = (edit: (document: Record<string, any>) => void) => {
    const document = parse(TESTING);
    edit(document);
    return () => compileProfile(base, [parseDomainContract(stringify(document), "<bad>", base)]);
  };

  it("resolves local names to term identifiers", () => {
    expect(compiled.instantiations["testing/affects-entity-entity"]).toEqual({
      kind: "instantiation",
      term: "testing/affects-entity-entity",
      template: "testing/affects",
      roles: { cause: ["testing/entity"], effect: ["testing/entity", "testing/outcome"] },
    });
    const bridge = compiled.bridges["testing/promotes"];
    expect([bridge.template, bridge.mapping, bridge.layers]).toEqual(["testing/affects", "narrower", ["causal"]]);
    expect(bridge.roles).toEqual({ cause: ["testing/entity"], effect: ["testing/outcome"] });
    expect(compiled.dimensions["testing/population"]).toEqual({
      term: "testing/population",
      restrictionSort: "testing/cohort",
      restriction: null,
      placement: "claim",
      appliesTo: ["testing/affects", "testing/correlates-with", "testing/promotes"],
    });
    const entity = compiled.sorts["testing/entity"];
    expect(entity.binding).toEqual({ kind: "release", namespace: "EX", release: "2026-01-01" });
    expect(entity.identifierClass?.pattern).toBe("EX:[a-z0-9\\-]+");
    expect(entity.categories).toEqual(["set"]);
    expect(compiled.sorts["testing/procedure-spec"].identifierClass).toBeNull();
    expect(compiled.durationConventions["testing/mean-month"]).toEqual({
      term: "testing/mean-month",
      conversion: "testing/mean-month-to-second",
      contract: "testing",
    });
  });

  it("compiles a template with its roles and omits its external reference", () => {
    const transforms = compiled.templates["testing/transforms"];
    expect(transforms.roles.inputs).toEqual({
      name: "inputs",
      arity: "many",
      min: 1,
      max: null,
      coefficients: true,
      constraint: [],
    });
    expect([transforms.signApt, transforms.layers, transforms.forms]).toEqual([
      false,
      ["structural", "causal"],
      ["polar"],
    ]);
    const withExternal = compileMutated((document) => {
      document.templates.affects.external = { reference: "RO:0002410", mapping: "contextual" };
    })();
    expect("external" in withExternal.templates["testing/affects"]).toBe(false);
  });

  it("keys every table by term, and the estimands by compiled typed address", () => {
    expect(Object.keys(compiled.estimands).sort()).toEqual([
      "bridge:testing/promotes",
      "instantiation:testing/affects-entity-entity",
      "instantiation:testing/affects-entity-outcome",
      "instantiation:testing/correlates-event-product",
      "instantiation:testing/promotes",
    ]);
    expect(compiled.estimands["bridge:testing/promotes"].conditioningSorts).toEqual(["testing/entity"]);
    expect(Object.keys(compiled.templates).sort()).toEqual([
      "testing/affects",
      "testing/correlates-with",
      "testing/measured-by",
      "testing/transforms",
    ]);
  });

  it("resolves an operator to a template or a bridge, and a bridge to its template", () => {
    const template = resolveOperator(compiled, "testing/affects");
    const bridge = resolveOperator(compiled, "testing/promotes");
    expect(template.kind).toBe("template");
    expect(bridge.kind).toBe("bridge");
    expect(templateOf(compiled, template)).toBe(template);
    expect(templateOf(compiled, bridge)).toBe(template);
    expect(() => resolveOperator(compiled, "testing/nowhere")).toThrow(ProfileError);
    // An instantiation is not an operator.
    expect(() => resolveOperator(compiled, "testing/affects-entity-outcome")).toThrow(/no operator/);
  });

  it("indexes overlapping instantiations by template", () => {
    expect(compiled.admission["testing/affects"]).toEqual([
      "instantiation:testing/affects-entity-entity",
      "instantiation:testing/affects-entity-outcome",
    ]);
    expect(compiled.admission["testing/measured-by"]).toEqual([
      "instantiation:testing/measured-by-entity-method",
      "instantiation:testing/promotes",
    ]);
    expect(compileProfile(base, [testing, crossing]).admission["testing/affects"]).toEqual([
      "instantiation:crossing/affects-local-entity",
      "instantiation:testing/affects-entity-entity",
      "instantiation:testing/affects-entity-outcome",
    ]);
  });

  it("returns both admitting instantiations over testing/affects, sorted, in either activation order", () => {
    const assignment = assign({ cause: ENTITY, effect: OUTCOME });
    const expected = ["instantiation:testing/affects-entity-entity", "instantiation:testing/affects-entity-outcome"];
    expect(admitting(compiled, "testing/affects", assignment)).toEqual(expected);
    expect(admitting(compileProfile(base, [testing, crossing]), "testing/affects", assignment)).toEqual(expected);
    expect(admitting(compileProfile(base, [crossing, testing]), "testing/affects", assignment)).toEqual(expected);
  });

  it("reads every role, each member sort of a many role, and skips the reserved role", () => {
    const profile = compileProfile(base, [testing, crossing]);
    expect(admitting(profile, "testing/affects", assign({ cause: ENTITY, effect: ENTITY }))).toEqual([
      "instantiation:testing/affects-entity-entity",
    ]);
    expect(
      admitting(profile, "testing/affects", assign({ cause: ENTITY, effect: new Set(["crossing/local-entity"]) })),
    ).toEqual(["instantiation:crossing/affects-local-entity"]);
    expect(admitting(profile, "testing/affects", assign({ cause: OUTCOME, effect: OUTCOME }))).toEqual([]);
    const parties = (...sorts: string[]) => assign({ parties: new Set(sorts) });
    expect(admitting(compiled, "testing/correlates-with", parties("testing/entity", "testing/outcome"))).toEqual([
      "instantiation:testing/correlates-entity-outcome",
    ]);
    expect(admitting(compiled, "testing/correlates-with", parties("testing/event", "testing/product"))).toEqual([
      "instantiation:testing/correlates-event-product",
    ]);
    expect(admitting(compiled, "testing/correlates-with", parties("testing/entity", "testing/product"))).toEqual([]);
    const withinModel = assign({ cause: ENTITY, effect: OUTCOME, "within-model": new Set(["testing/procedure-spec"]) });
    expect(admitting(compiled, "testing/affects", withinModel)).toHaveLength(2);
    expect(() => admitting(compiled, "testing/affects", assign({ cause: ENTITY, agent: ENTITY }))).toThrow(/agent/);
  });

  it("finds the estimand declarations of the admitting set, in the order given", () => {
    const profile = compileProfile(base, [testing, crossing]);
    const admits = admitting(profile, "testing/affects", assign({ cause: ENTITY, effect: OUTCOME }));
    const declarations = estimandDeclarations(profile, "testing/affects", admits);
    expect(declarations.map((decl) => decl.target)).toEqual(admits);
    expect(declarations.map((decl) => decl.conditioningSorts)).toEqual([["testing/outcome"], ["testing/entity"]]);
    const reversed = [...admits].reverse();
    expect(estimandDeclarations(profile, "testing/affects", reversed).map((decl) => decl.target)).toEqual(reversed);
    const correlates = admitting(
      compiled,
      "testing/correlates-with",
      assign({ parties: new Set(["testing/entity", "testing/outcome"]) }),
    );
    expect(estimandDeclarations(compiled, "testing/correlates-with", correlates)).toEqual([]);
    expect(() => estimandDeclarations(compiled, "testing/affects", ["instantiation:testing/promotes"])).toThrow(
      /testing\/measured-by/,
    );
    expect(() => estimandDeclarations(compiled, "testing/affects", ["bridge:testing/promotes"])).toThrow(ProfileError);
  });

  it("distinguishes the same-name instantiation and bridge promotes", () => {
    const bridgeAdmitting = admitting(compiled, "testing/promotes", assign({ cause: ENTITY, effect: OUTCOME }));
    expect(bridgeAdmitting).toEqual(["bridge:testing/promotes"]);
    const [bridgeDecl, ...noBridgeRest] = estimandDeclarations(compiled, "testing/promotes", bridgeAdmitting);
    expect(noBridgeRest).toEqual([]);
    expect(bridgeDecl.target).toBe("bridge:testing/promotes");
    expect(bridgeDecl.conditioningSorts).toEqual(["testing/entity"]);
    expect(bridgeDecl.forms).toContain("contrast");

    const instAdmitting = admitting(
      compiled,
      "testing/measured-by",
      assign({ subject: new Set(["testing/product"]), instrument: new Set(["testing/method"]) }),
    );
    expect(instAdmitting).toEqual(["instantiation:testing/promotes"]);
    const [instDecl, ...noInstRest] = estimandDeclarations(compiled, "testing/measured-by", instAdmitting);
    expect(noInstRest).toEqual([]);
    expect(instDecl.target).toBe("instantiation:testing/promotes");
    expect(instDecl.conditioningSorts).toEqual(["testing/entity"]);
    expect(instDecl.forms).toEqual(["quantity"]);
  });

  it("dereferences typed addresses and refuses every other spelling", () => {
    const instantiation = declarationAt(compiled, "instantiation:testing/promotes");
    const bridge = declarationAt(compiled, "bridge:testing/promotes");
    expect(instantiation.template).toBe("testing/measured-by");
    expect(bridge.template).toBe("testing/affects");
    expect(bridge).toBe(compiled.bridges["testing/promotes"]);
    for (const address of [
      "template:testing/affects",
      "instantiation:testing/nowhere",
      "testing/promotes",
      "bridge:",
    ]) {
      expect(() => declarationAt(compiled, address)).toThrow(ProfileError);
    }
  });

  it("lists a claim's dimensions by applies_to, claim side only", () => {
    expect(claimDimensions(compiled, "testing/affects")).toEqual(["testing/population", "testing/setting"]);
    expect(claimDimensions(compiled, "testing/correlates-with")).toEqual(["testing/population"]);
    expect(claimDimensions(compiled, "testing/promotes")).toEqual(["testing/population"]);
    expect(claimDimensions(compiled, "testing/measured-by")).toEqual([]);
    expect(compiled.dimensions["testing/follow-up"].appliesTo).toEqual(["testing/affects"]);
    expect(() => claimDimensions(compiled, "testing/nowhere")).toThrow(/no operator/);
  });

  it("resolves applies_to locally first, and a qualified name in its own contract", () => {
    const profile = compileProfile(base, [testing, other, crossing]);
    expect(profile.dimensions["testing/population"].appliesTo).toEqual([
      "testing/affects",
      "testing/correlates-with",
      "testing/promotes",
    ]);
    expect(profile.dimensions["elsewhere/population"].appliesTo).toEqual([
      "elsewhere/affects",
      "elsewhere/correlates-with",
      "elsewhere/promotes",
    ]);
    expect(claimDimensions(profile, "testing/affects")).toEqual([
      "crossing/scope",
      "testing/population",
      "testing/setting",
    ]);
    expect(claimDimensions(profile, "elsewhere/affects")).toEqual(["elsewhere/population", "elsewhere/setting"]);
  });

  it.each(["nowhere", "other/affects", "affects-entity-entity", "promotes"])(
    "refuses an instantiation of the undeclared template %s",
    (template) => {
      const run = compileMutated((document) => {
        document.instantiations["affects-entity-outcome"].template = template;
      });
      expect(run).toThrow(ProfileError);
      expect(run).toThrow(/template/);
    },
  );

  it("refuses a bridge of an undeclared template", () => {
    const run = compileMutated((document) => {
      document.bridges.promotes.template = "other/affects";
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/template/);
  });

  it("refuses a listed sort missing a role constraint's category", () => {
    const run = compileMutated((document) => {
      document.templates.affects.roles.effect.constraint = ["set"];
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/testing\/outcome/);
  });

  it("compiles a constraint every listed sort satisfies", () => {
    const profile = compileMutated((document) => {
      document.templates.transforms.roles.inputs.constraint = ["set"];
    })();
    expect(profile.templates["testing/transforms"].roles.inputs.constraint).toEqual(["set"]);
  });

  it.each([
    ["instantiations", "affects-entity-outcome"],
    ["bridges", "promotes"],
  ])("refuses a role the template lacks in %s", (table, name) => {
    const run = compileMutated((document) => {
      document[table][name].roles.agent = ["entity"];
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/agent/);
  });

  it.each([
    ["instantiations", "affects-entity-outcome"],
    ["bridges", "promotes"],
  ])("refuses an omitted role in %s", (table, name) => {
    const run = compileMutated((document) => {
      Reflect.deleteProperty(document[table][name].roles, "effect");
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/effect/);
  });

  it("refuses a within-model role on an instantiation", () => {
    const run = compileMutated((document) => {
      document.instantiations["affects-entity-outcome"].roles["within-model"] = ["procedure-spec"];
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/within-model/);
  });

  it.each(["nowhere", "other/affects", "affects-entity-outcome", "day"])(
    "refuses applies_to naming %s, no active operator",
    (operator) => {
      const run = compileMutated((document) => {
        document.dimensions.setting.applies_to = ["affects", operator];
      });
      expect(run).toThrow(ProfileError);
      expect(run).toThrow(/applies_to/);
    },
  );

  it("refuses a bridge's layers outside its template's, and inherits them when it declares none", () => {
    const run = compileMutated((document) => {
      document.bridges.promotes.layers = ["causal", "methodological"];
    });
    expect(run).toThrow(ProfileError);
    expect(run).toThrow(/methodological/);
    const inherited = compileMutated((document) => {
      Reflect.deleteProperty(document.bridges.promotes, "layers");
    })();
    expect(inherited.bridges["testing/promotes"].layers).toEqual(["causal", "statistical"]);
  });

  it("refuses an estimand level sort naming no role of the template", () => {
    const run = compileMutated((document) => {
      document.estimands["bridge:promotes"].conditioning_sorts = ["unknown-sort"];
    });
    expect(run).toThrow(MalformedContract);
    expect(run).toThrow(/unknown-sort/);
  });

  it("holds the v2 tables frozen, nested arrays included", () => {
    for (const value of [
      compiled.sorts,
      compiled.sorts["testing/entity"],
      compiled.sorts["testing/entity"].categories,
      compiled.dimensions["testing/population"].appliesTo,
      compiled.templates,
      compiled.templates["testing/affects"].roles,
      compiled.templates["testing/affects"].roles.cause.constraint,
      compiled.templates["testing/affects"].layers,
      compiled.instantiations["testing/affects-entity-entity"].roles.effect,
      compiled.bridges["testing/promotes"].layers,
      compiled.estimands["bridge:testing/promotes"].conditioningSorts,
      compiled.durationConventions["testing/mean-month"],
      compiled.admission,
      compiled.admission["testing/affects"],
    ]) {
      expect(Object.isFrozen(value)).toBe(true);
    }
  });
});

describe("compileProfile enforces the declaration constraints", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  const TESTING = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  it("carries kinds, relations and facets", () => {
    const profile = compileProfile(base, [parseDomainContract(TESTING, "<t>", base)]);
    expect(Object.keys(profile.kinds).length).toBeGreaterThanOrEqual(16);
    expect(profile.facets["testing/axis"].attachesTo).toEqual(["dataset"]);
  });
  it("refuses a domain facet attaching to an undeclared or prose kind", () => {
    for (const kind of ["divergence", "discussion"]) {
      const bad = TESTING.replace(
        "attaches_to: [dataset]\n    fields:\n      axis:",
        `attaches_to: [${kind}]\n    fields:\n      axis:`,
      );
      expect(() => compileProfile(base, [parseDomainContract(bad, "<bad>", base)])).toThrow(new RegExp(kind));
    }
  });
});

it("resolves ref kinds from both base and domain facets", () => {
  const baseText = SHIPPED.replace("kinds: [act-report]", "kinds: [missing]");
  expect(() => compileProfile(parseBaseContract(baseText, "<bad>"), [])).toThrow(/missing/);
  const base = parseBaseContract(SHIPPED, "<base>");
  const text = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8").replace(
    "kinds: [dataset]",
    "kinds: [missing]",
  );
  expect(() => compileProfile(base, [parseDomainContract(text, "<bad>", base)])).toThrow(/missing/);
});
it("keeps compiled declaration products immutable", () => {
  const base = parseBaseContract(SHIPPED, "<base>");
  const text = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  const profile = compileProfile(base, [parseDomainContract(text, "<t>", base)]);
  for (const value of [
    profile.kinds,
    profile.kinds.dataset,
    profile.kinds.dataset.facets,
    profile.kinds.dataset.facets.dataset,
    profile.relations,
    profile.relations.retracts,
    profile.relations.retracts.targets,
    profile.facets,
    profile.facets["testing/axis"],
    profile.facets["testing/axis"].attachesTo,
    profile.facets["testing/axis"].fields,
    profile.facets["testing/axis"].fields.vocabulary.kinds,
  ]) {
    expect(Object.isFrozen(value)).toBe(true);
  }
});
