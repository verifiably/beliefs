import { readFileSync } from "node:fs";
import { expect, it } from "vitest";
import { stringify } from "yaml";
import { claimVocabulary } from "../src/contract-succession.js";
import * as errors from "../src/errors.js";
import { compileProfile, parseBaseContract, parseDomainContract } from "../src/index.js";
const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf8");
interface Case {
  name: string;
  document: Record<string, unknown>;
  previous: string | null;
  outcome: string;
  content_identity: string | null;
  error?: string;
  diagnostic?: string;
}
const vector = JSON.parse(read("fixtures/defining-source.json")) as {
  cases: Case[];
  production: { namespace: string; contract_path: string; contract_identity: string }[];
  profiles: Record<string, string>;
};
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
function parse(row: Case): ReturnType<typeof parseDomainContract> {
  const prior = row.previous ? parse(vector.cases.find((c) => c.name === row.previous) as Case) : undefined;
  return parseDomainContract(stringify(row.document), row.name, base, prior);
}
it("adopted production contracts parse and their profiles compile", () => {
  const inventory = JSON.parse(read("contracts/source-ownership/INVENTORY.json")) as {
    lineages: Record<string, { revisions: { contract_path: string; contract_identity: string }[] }>;
  };
  const parsed = new Map<string, ReturnType<typeof parseDomainContract>>();
  const rows = [...vector.production].sort((a) => (a.contract_path.includes("history/") ? -1 : 1));
  for (const row of rows) {
    const path = inventory.lineages[row.namespace]?.revisions.find(
      (revision) => revision.contract_identity === row.contract_identity,
    )?.contract_path;
    if (!path) throw new Error(`Missing inventory path for ${row.namespace}/${row.contract_identity}`);
    const c = parseDomainContract(read(path), path, base, parsed.get(row.namespace));
    expect(c.contentIdentity).toBe(row.contract_identity);
    parsed.set(row.namespace, c);
  }
  for (const names of Object.keys(vector.profiles))
    compileProfile(
      base,
      names.split("+").map((n) => parsed.get(n) as ReturnType<typeof parseDomainContract>),
    );
});
it.each(vector.cases)("$name", (row) => {
  if (row.outcome === "accept") {
    const c = parse(row);
    expect(c.contentIdentity).toBe(row.content_identity);
    expect(c.definingSource).toEqual(row.document.defining_source ?? null);
  } else {
    let caught: unknown;
    try {
      parse(row);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(errors[row.error as keyof typeof errors]);
    expect((caught as Error).message).toContain(row.diagnostic);
  }
});
it("source is immutable and does not add claim declarations or local ownership checking", () => {
  const absent = parse(vector.cases.find((c) => c.name === "absent") as Case);
  const present = parse(vector.cases.find((c) => c.name === "urn") as Case);
  expect(absent.contentIdentity).not.toBe(present.contentIdentity);
  expect(claimVocabulary(absent)).toEqual(claimVocabulary(present));
  expect(Object.isFrozen(present.definingSource)).toBe(true);
  expect(() => Object.assign(present.definingSource as object, { id: "urn:other:id" })).toThrow(TypeError);
  const doc = { ...(vector.cases.find((c) => c.name === "urn") as Case).document, contract: "other-source-test" };
  compileProfile(base, [present, parseDomainContract(stringify(doc), "other", base)]);
});
