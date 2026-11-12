/** Annotation examples test grammar and identity, not release membership. */
import { readFileSync } from "node:fs";
import { expect, it } from "vitest";
import {
  Referent,
  buildClaim,
  claimIdentity,
  compileProfile,
  encode,
  parseBaseContract,
  parseDomainContract,
  projectClaim,
} from "../src/index.js";
const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf8");
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
const previous = parseDomainContract(
  read("domains/general/history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f/DOMAIN.yaml"),
  "old-general",
  base,
);
const general = parseDomainContract(read("domains/general/DOMAIN.yaml"), "general", base, previous);
const biology = parseDomainContract(read("domains/biology/DOMAIN.yaml"), "biology", base);
const profile = compileProfile(base, [general, biology]);
it("requires explicit general activation and agrees on biology content identity", () => {
  expect(() => compileProfile(base, [biology])).toThrow();
  expect(biology.contentIdentity).toBe("05e6f4fd06de8112d8f13d235c0793b6767404208cbf4210b7b9b24fc1840aca");
  expect(read("domains/biology/DOMAIN.yaml")).toBe(read("python/src/beliefs/domains/biology/DOMAIN.yaml"));
});
interface Row {
  claim: {
    operator: string;
    roles: Record<string, { sort: string; term: string }>;
    form: string;
    polarity: string | null;
    layer: string;
  };
  projection: unknown;
  canonical_bytes: string;
  digest: string;
}
const fixture = JSON.parse(read("fixtures/biology-claim-identity-v2.json")) as { vector: Row[] };
it("reproduces Python projections, canonical bytes and identities for every biology vector", () => {
  for (const row of fixture.vector) {
    const claim = buildClaim(profile, {
      ...row.claim,
      qualifiers: new Map(),
      roles: new Map(Object.entries(row.claim.roles).map(([k, v]) => [k, new Referent(v.sort, v.term)])),
    });
    expect(projectClaim(claim)).toEqual(row.projection);
    expect(new TextDecoder().decode(encode(projectClaim(claim)))).toBe(row.canonical_bytes);
    expect(claimIdentity(claim)).toBe(row.digest);
  }
});
it.each([
  "PHF19",
  "ensembl:ENST00000312189",
  "ensembl:ENST00000312189.0",
  "ensembl:ENSG00000119403",
  "ensembl:ENSMUST000001.1",
])("refuses transcript syntax %s", (term) => {
  expect(() =>
    buildClaim(profile, {
      operator: "biology/transcribed-from",
      roles: new Map([
        ["transcript", new Referent("biology/transcript", term)],
        ["gene", new Referent("biology/ensembl-gene", "ensembl:ENSG00000119403")],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: null,
      layer: "structural",
    }),
  ).toThrow();
});
it.each(["PHF19", "ensembl:ENSP00000310372", "ensembl:ENSP00000310372.0", "ensembl:ENSG00000119403", "uniprot:Q5T6S3"])(
  "refuses protein syntax %s",
  (term) => {
    expect(() =>
      buildClaim(profile, {
        operator: "biology/translated-from",
        roles: new Map([
          ["transcript", new Referent("biology/transcript", "ensembl:ENST00000312189.10")],
          ["protein", new Referent("biology/protein", term)],
        ]),
        qualifiers: new Map(),
        form: "polar",
        polarity: null,
        layer: "structural",
      }),
    ).toThrow();
  },
);
