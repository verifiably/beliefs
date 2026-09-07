import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { compileProfile } from "../src/profile.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const SHIPPED = readFileSync(new URL("contracts/science/CONTRACT.yaml", REPO_ROOT), "utf-8");

describe("document load refuses duplicate keys (design §3.7)", () => {
  it("refuses a duplicate top-level key rather than keeping the last", () => {
    const text = "contract: science\ncontract: science\nversion: 1\nclaim_grammar: {}\n";
    expect(() => parseBaseContract(text, "<dup>")).toThrow(/unique/i);
  });
});

describe("the base contract's declarations (design §3.1–§3.4)", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  it("declares thirteen world kinds and three prose kinds", () => {
    expect(Object.values(base.kinds).filter((kind) => kind.role === "world")).toHaveLength(13);
    expect(Object.values(base.kinds).filter((kind) => kind.role === "prose")).toHaveLength(3);
    expect(base.kinds["instrument-certification"].domain).toBeNull();
    expect(base.kinds["coreference-attestation"].facets).toEqual({});
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
});

describe("a domain contract's facets (design §3.3)", () => {
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
});

describe("compileProfile enforces the declaration constraints (design §7.2)", () => {
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
