import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { compileProfile } from "../src/profile.js";

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
  it("declares nineteen world kinds and three prose kinds", () => {
    expect(Object.values(base.kinds).filter((kind) => kind.role === "world")).toHaveLength(19);
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
    expect(base.relations.retracts.targets).toEqual(["assessment", "retraction", "verification"]);
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
  it("declares the estimand grammar's three closed sets", () => {
    expect(base.estimandGrammar.contrastKinds).toEqual(["levels", "continuous"]);
    expect(base.estimandGrammar.scales).toEqual(["additive", "multiplicative"]);
    expect(base.estimandGrammar.uncertaintyKinds).toEqual(["interval", "standard-error"]);
  });
  it("refuses an estimand closed set wider than the tags the kernel operates", () => {
    expect(() =>
      parseBaseContract(
        SHIPPED.replace("scales: [additive, multiplicative]", "scales: [additive, multiplicative, log]"),
        "<bad>",
      ),
    ).toThrow(/log/);
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
  it("declares the three base-v2 world kinds", () => {
    expect(base.kinds["assumptions-register"].domain).toBe("science.assumptions-register.v1");
    expect(base.kinds["assumptions-register"].facets["assumptions-register"]).toEqual({
      required: true,
      covered: true,
    });
    expect(base.facets["assumptions-register"].shape).toBe("reader");
    for (const name of ["procedure", "classification-rule"]) {
      expect(base.kinds[name].role).toBe("world");
      expect(base.kinds[name].domain).toBe(`science.${name}.v1`);
      expect(Object.keys(base.kinds[name].facets)).toEqual([]);
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
    const missing = SHIPPED.replace(/estimand_grammar:[\s\S]*?uncertainty_kinds: \[interval, standard-error\]\n/, "");
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
  it("parses the edges table and refuses an undeclared or non-causal operator", () => {
    const domain = parseDomainContract(TESTING, "fixtures/contracts/testing.yaml", base);
    expect(domain.edges.affects).toEqual({ operator: "affects", cause: 0, effect: 1 });
    expect(() =>
      parseDomainContract(TESTING.replace("edges:\n  affects:", "edges:\n  regulates:"), "<bad>", base),
    ).toThrow(/regulates/);
    expect(() =>
      parseDomainContract(TESTING.replace("edges:\n  affects:", "edges:\n  correlates-with:"), "<bad>", base),
    ).toThrow(/causal/);
    expect(() =>
      parseDomainContract(TESTING.replace("{ cause: 0, effect: 1 }", "{ cause: 0, effect: 0 }"), "<bad>", base),
    ).toThrow(/distinct/);
    const profile = compileProfile(base, [domain]);
    expect(profile.edges["testing/affects"]).toEqual({ operator: "testing/affects", cause: 0, effect: 1 });
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
