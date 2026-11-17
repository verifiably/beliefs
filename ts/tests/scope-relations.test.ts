import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { claimVocabulary } from "../src/contract-succession.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { compileProfile } from "../src/profile.js";
import { scopeRelationProjection } from "../src/scope-relations.js";

const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
// biome-ignore lint/suspicious/noExplicitAny: shared normative documents are deliberately mutated in these tests
type Document = Record<string, any>;
interface Change {
  name?: string;
  path: string[];
  value?: unknown;
  delete?: boolean;
  outcome?: string;
}
const vector = JSON.parse(read("fixtures/scope-relations.json")) as {
  endpoint_contract: string;
  document: Document;
  identity: string;
  schema: Document;
  compiled: Document;
  local: { changes: Change[]; schema: Document; compiled: Document };
  parse_refusals: Change[];
  compile_refusals: Change[];
};
const baseText = read("contracts/science/CONTRACT.yaml");
const base = parseBaseContract(baseText, "base");
const testingText = read(vector.endpoint_contract);
const testing = () => parseDomainContract(testingText, "testing", base);
const scope = (document: Document) => parseDomainContract(stringify(document), "scope-relations", base);

function apply(document: Document, change: Change): Document {
  let target = document;
  for (const key of change.path.slice(0, -1)) target = target[key];
  const key = change.path.at(-1) as string;
  if (change.delete) delete target[key];
  else target[key] = structuredClone(change.value);
  return document;
}

function scopeVocabulary(document: Document): Document {
  const schema = Object.fromEntries(claimVocabulary(scope(document)));
  return Object.fromEntries(Object.entries(schema).filter(([key]) => key.startsWith("scope-relation:")));
}

function compiled(profile: ReturnType<typeof compileProfile>): Document {
  return Object.fromEntries(
    Object.entries(profile.scopeRelations).map(([term, relation]) => [term, scopeRelationProjection(relation)]),
  );
}

function errorName(run: () => unknown): string {
  try {
    run();
  } catch (error) {
    return (error as Error).name;
  }
  return "accepted";
}

describe("scope relation declarations", () => {
  it("parse to the shared semantic projection and content identity", () => {
    const contract = scope(structuredClone(vector.document));
    expect(contract.contentIdentity).toBe(vector.identity);
    expect(scopeVocabulary(structuredClone(vector.document))).toEqual(vector.schema);
    expect(Object.isFrozen(contract.scopeRelations["special-within-general"])).toBe(true);
    expect(contract.scopeRelations["special-within-general"].retired).toBe(false);
  });

  it("compile to the shared qualified projection", () => {
    const profile = compileProfile(base, [testing(), scope(structuredClone(vector.document))]);
    expect(compiled(profile)).toEqual(vector.compiled);
    expect(profile.scopeRelations["scope-relations/special-within-general"].contract).toBe("scope-relations");
    expect(compileProfile(base, [testing()]).scopeRelations).toEqual({});
  });

  it("qualify local references and carry retirement into the compiled table", () => {
    const document = parse(testingText) as Document;
    for (const change of vector.local.changes) apply(document, change);
    const contract = parseDomainContract(stringify(document), "testing", base);
    const schema = Object.fromEntries(
      [...claimVocabulary(contract)].filter(([key]) => key.startsWith("scope-relation:")),
    );
    expect(schema).toEqual(vector.local.schema);
    expect(compiled(compileProfile(base, [contract]))).toEqual(vector.local.compiled);
  });

  it.each(vector.parse_refusals)("refuses at parse: $name", (row) => {
    const document = apply(structuredClone(vector.document), row);
    expect(errorName(() => scope(document))).toBe(row.outcome);
  });

  it.each(vector.compile_refusals)("refuses at compile: $name", (row) => {
    const contract = scope(apply(structuredClone(vector.document), row));
    expect(errorName(() => compileProfile(base, [testing(), contract]))).toBe(row.outcome);
  });

  it("reads the base's closed scope grammar and refuses earlier generations", () => {
    expect(base.version).toBe(6);
    expect(base.scopeGrammar).toEqual({ version: 1, relations: ["equal", "narrower"] });
    const withTag = baseText.replace("relations: [equal, narrower]", "relations: [equal, narrower, within]");
    expect(errorName(() => parseBaseContract(withTag, "wider"))).toBe("MalformedContract");
    const v5 = read("python/tests/fixtures/science-v5.yaml");
    expect(errorName(() => parseBaseContract(v5, "v5"))).toBe("MalformedContract");
  });

  it("admits retirement, refuses redefinition and refuses un-retirement", () => {
    const genesis = scope(structuredClone(vector.document));
    const successor = (edit: (table: Document) => void, prior = genesis, version = 2) => {
      const document = structuredClone(vector.document);
      document.version = version;
      document.lineage = { successor: prior.contentIdentity };
      edit(document.scope_relations);
      return document;
    };
    const succeed = (document: Document, prior = genesis) =>
      parseDomainContract(stringify(document), "successor", base, prior);
    const retire = (table: Document) => {
      table["special-within-general"].retired = true;
    };
    const retired = succeed(successor(retire));
    expect(retired.scopeRelations["special-within-general"].retired).toBe(true);
    const redefine = successor((table) => {
      table["special-within-general"].relation = "equal";
    });
    expect(errorName(() => succeed(redefine))).toBe("SuccessionViolation");
    const unretired = successor(() => undefined, retired, 3);
    expect(errorName(() => succeed(unretired, retired))).toBe("SuccessionViolation");
  });
});

describe("declared scope graph consistency", () => {
  type GraphCase = { name: string; contracts: Document[]; outcome?: string };
  const graphs = vector as unknown as { graph_refusals: GraphCase[]; graph_accepts: GraphCase[] };
  const owners = ["scope-relations", "scope-relations-b", "scope-relations-c"];
  const contracts = (row: GraphCase) =>
    row.contracts.map((table, index) =>
      parseDomainContract(
        stringify({
          contract: owners[index],
          version: 1,
          lineage: "genesis",
          sorts: {},
          dimensions: {},
          scope_relations: table,
        }),
        owners[index],
        base,
      ),
    );

  it.each(graphs.graph_refusals)("refuses an inconsistent graph: $name", (row) => {
    const parsed = contracts(row);
    expect(errorName(() => compileProfile(base, [testing(), ...parsed]))).toBe(row.outcome);
  });

  it.each(graphs.graph_accepts)("compiles a consistent graph: $name", (row) => {
    const parsed = contracts(row);
    expect(errorName(() => compileProfile(base, [testing(), ...parsed]))).toBe("accepted");
  });
});
