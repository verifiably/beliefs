import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { claimVocabulary } from "../src/contract-succession.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, SuccessionViolation, UnparsedContract } from "../src/errors.js";
import { encode } from "../src/identity/v1.js";
import { compileProfile } from "../src/profile.js";

const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
// biome-ignore lint/suspicious/noExplicitAny: shared normative documents are deliberately mutated in these tests
type Document = Record<string, any>;
interface Case {
  name: string;
  previous: "genesis" | "added" | null;
  lineage: Document | string;
  changes: { path: string[]; value?: unknown; delete?: boolean }[];
  outcome: string;
  identity: string;
}
const vector = JSON.parse(read("fixtures/contract-succession.json")) as {
  genesis: Document;
  added: Document;
  genesis_identity: string;
  added_identity: string;
  genesis_schema: Document;
  families: string[];
  cases: Case[];
};
const baseText = read("contracts/science/CONTRACT.yaml");
const base = parseBaseContract(baseText, "base");
const genesis = () => parseDomainContract(stringify(vector.genesis), "genesis", base);

describe("additive contract succession", () => {
  it("computes the shared genesis identity from normative content", () => {
    expect(genesis().contentIdentity).toBe(vector.genesis_identity);
    expect(genesis().predecessor).toBeNull();
    const reordered = Object.fromEntries(Object.entries(vector.genesis).reverse());
    expect(parseDomainContract(`# presentation only\n${stringify(reordered)}`, "reordered", base).contentIdentity).toBe(
      vector.genesis_identity,
    );
  });

  it("matches every typed schema projection in the shared Python vector", () => {
    const schema = Object.fromEntries(claimVocabulary(genesis()));
    // JSON's integer leaves are converted only for comparing the frozen vector.
    const expected = JSON.parse(JSON.stringify(vector.genesis_schema), (_key, value) =>
      typeof value === "number" ? BigInt(value) : value,
    );
    expect(encode(schema)).toEqual(encode(expected));
    expect(new Set(Object.keys(schema).map((key) => key.split(":")[0]))).toEqual(new Set(vector.families));
  });

  it.each(vector.cases)("$name", (row) => {
    const prior = genesis();
    const added = parseDomainContract(stringify(vector.added), "added", base, prior);
    expect(added.contentIdentity).toBe(vector.added_identity);
    const document = structuredClone(vector[row.previous ?? "genesis"]);
    document.version += 1;
    document.lineage = row.lineage;
    for (const change of row.changes) {
      let target = document;
      for (const key of change.path.slice(0, -1)) target = target[key];
      const key = change.path.at(-1) as string;
      if (change.delete) delete target[key];
      else target[key] = change.value;
    }
    const predecessor = row.previous === null ? undefined : row.previous === "genesis" ? prior : added;
    const parse = () => parseDomainContract(stringify(document), row.name, base, predecessor);
    if (row.outcome === "accept") expect(parse().contentIdentity).toBe(row.identity);
    else {
      try {
        parse();
        throw new Error("accepted an invalid successor");
      } catch (error) {
        expect((error as Error).name).toBe(row.outcome);
      }
    }
  });

  it("accepts identical base content and refuses a different base on direct calls", () => {
    const prior = genesis();
    const sameBase = parseBaseContract(baseText, "same-base");
    expect(parseDomainContract(stringify(vector.added), "added", sameBase, prior).contentIdentity).toBe(
      vector.added_identity,
    );
    const differentBase = parseBaseContract(baseText.replace("version: 4", "version: 5"), "other-base");
    expect(() => parseDomainContract(stringify(vector.added), "added", differentBase, prior)).toThrow(/base/);
  });

  it("refuses an unparsed predecessor before trusting its fields", () => {
    const prior = { ...genesis() };
    // @ts-expect-error a structural copy cannot replace a branded contract
    expect(() => parseDomainContract(stringify(vector.added), "added", base, prior)).toThrow(UnparsedContract);
  });

  it.each(["2.0", "9007199254740992", "null"])("refuses noncanonical version %s", (version) => {
    const text = stringify(vector.genesis).replace(/^version: .*$/m, `version: ${version}`);
    expect(() => parseDomainContract(text, "invalid-number", base)).toThrow(MalformedContract);
  });
});

describe("permanent unit mappings", () => {
  it.each(["add", "remove", "change"])("refuses %s under the same unit id", (change) => {
    const document = parse(read("fixtures/contracts/series-time.yaml")) as Document;
    for (const [unit, code, local] of [
      ["second", "s", "SEC"],
      ["hour", "h", "HR"],
      ["hertz", "Hz", "HZ"],
    ]) {
      document.units[unit].external = {
        ucum: code,
        qudt: `http://qudt.org/vocab/unit/${local}`,
      };
    }
    if (change === "add") document.units.second.external = { ucum: "s" };
    const prior = parseDomainContract(stringify(document), "synthetic mapped units", base);
    expect(compileProfile(base, [prior]).units).toBeDefined();
    const successor = structuredClone(document);
    successor.version = 2;
    successor.lineage = { successor: prior.contentIdentity };
    if (change === "add") successor.units.second.external.qudt = "http://qudt.org/vocab/unit/SEC";
    if (change === "remove") successor.units.second.external = { ucum: "s" };
    if (change === "change") successor.units.second.external.ucum = "h";
    expect(() => parseDomainContract(stringify(successor), "changed synthetic mapping", base, prior)).toThrow(
      SuccessionViolation,
    );
  });
});
