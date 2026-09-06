import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parseBaseContract } from "../src/contract.js";

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
  it("declares the three prose kinds with display only", () => {
    expect(base.kinds.discussion.role).toBe("prose");
    expect(Object.keys(base.kinds.discussion.facets)).toEqual(["display"]);
  });
});
