import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import {
  Member,
  Qualifier,
  Referent,
  buildClaim,
  claimIdentity,
  compileProfile,
  encode,
  parseBaseContract,
  parseDomainContract,
  projectClaim,
} from "../src/index.js";

const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), "utf-8");
// biome-ignore lint/suspicious/noExplicitAny: test documents and cross-language fixture components
type Document = Record<string, any>;
const oracle = JSON.parse(read("fixtures/spectral-candidates.json"));
const event = JSON.parse(read("fixtures/candidate-contracts.json"));
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
function general(names: string[]) {
  // Same two-document path as the existing oracle; full-chain TS validation remains beliefs-750766.
  const path = "domains/general/DOMAIN.yaml";
  const ancestor = parseDomainContract(
    read("domains/general/history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f/DOMAIN.yaml"),
    "ancestor",
    base,
  );
  const previous = parseDomainContract(read(path), path, base, ancestor);
  const doc = parse(read(path)) as Document;
  for (const name of names) {
    const rows = parse(read(`fixtures/contracts/candidates/fragments/${name}.yaml`)).rows;
    for (const [table, entries] of Object.entries(rows)) {
      doc[table] ??= {};
      for (const [key, value] of Object.entries(entries as object)) {
        if (key in doc[table]) throw new Error(`collision: ${table}.${key}`);
        doc[table][key] = value;
      }
    }
  }
  doc.version += 1;
  doc.lineage = { successor: previous.contentIdentity };
  doc.defining_source = { id: "urn:beliefs:definitions:shared-scientific-commitments" };
  return parseDomainContract(stringify(doc), "candidate", base, previous);
}
function profile(joint: boolean, omitTime = false) {
  const domains = [general(joint ? ["general-event-locked", "general-spectral"] : ["general-spectral"])];
  if (!omitTime) {
    const doc = parse(read("domains/si-brochure/DOMAIN.yaml")) as Document;
    const time = parseDomainContract(stringify(doc), "SI", base);
    if (joint) {
      const rows = parse(read("fixtures/contracts/candidates/fragments/si-brochure-speed.yaml")).rows;
      for (const [table, entries] of Object.entries(rows)) doc[table] = { ...doc[table], ...(entries as object) };
      doc.version += 1;
      doc.lineage = { successor: time.contentIdentity };
      domains.push(parseDomainContract(stringify(doc), "speed", base, time));
    } else domains.push(time);
  }
  for (const ns of joint ? ["plasma-populations", "catalogue-anchors", "spectral-example"] : ["spectral-example"]) {
    domains.push(parseDomainContract(read(`fixtures/contracts/candidates/${ns}/DOMAIN.yaml`), ns, base));
  }
  return compileProfile(base, domains);
}
function parts(c: Document) {
  const ref = (r: Document) => new Referent(r.sort, r.term);
  return {
    ...c,
    roles: new Map(
      Object.entries(c.roles).map(([k, v]) => [
        k,
        Array.isArray(v) ? v.map((r) => new Member(ref(r), BigInt(r.coefficient))) : ref(v as Document),
      ]),
    ),
    qualifiers: new Map(
      Object.entries(c.qualifiers).map(([k, v]) => [
        k,
        new Qualifier((v as Document).quantifier, ref((v as Document).restriction)),
      ]),
    ),
  };
}
describe("unshipped spectral parity", () => {
  it("pins both general successors and the synthetic contract", () => {
    expect(general(["general-event-locked"]).contentIdentity).toBe(event.general_successor.contract_identity);
    for (const name of ["spectral", "joint"])
      expect(
        general(name === "joint" ? ["general-event-locked", "general-spectral"] : ["general-spectral"]).contentIdentity,
      ).toBe(oracle.profiles[name].general_contract_identity);
    const p = "fixtures/contracts/candidates/spectral-example/DOMAIN.yaml";
    expect(parseDomainContract(read(p), p, base).contentIdentity).toBe(oracle.synthetic_pair.contract_identity);
  });
  it("reconstructs typed claims, projections, canonical bytes and identities", () => {
    for (const row of oracle.claims) {
      const claim = buildClaim(profile(row.profile === "joint"), parts(row.components));
      expect(projectClaim(claim)).toEqual(row.projection);
      expect(new TextDecoder().decode(encode(projectClaim(claim)))).toBe(row.canonical_bytes);
      expect(claimIdentity(claim)).toBe(row.digest);
    }
  });
  it("types a standalone spectral claim without SI activation", () => {
    const row = oracle.claims.find((r: Document) => r.profile === "spectral");
    expect(claimIdentity(buildClaim(profile(false, true), parts(row.components)))).toBe(row.digest);
  });
});
