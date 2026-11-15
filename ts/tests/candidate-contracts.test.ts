import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { SuccessionViolation, parseBaseContract, parseDomainContract } from "../src/index.js";

const read = (relative: string): string => readFileSync(new URL(`../../${relative}`, import.meta.url), "utf-8");
const oracle = JSON.parse(read("fixtures/candidate-contracts.json"));

// biome-ignore lint/suspicious/noExplicitAny: normative documents are deliberately mutated in these tests
type Document = Record<string, any>;
const GENERAL_PATH = "domains/general/DOMAIN.yaml";
const GENERAL_HISTORY =
  "domains/general/history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f/DOMAIN.yaml";
function parseGeneral(base: ReturnType<typeof parseBaseContract>) {
  const predecessor = parseDomainContract(read(GENERAL_HISTORY), GENERAL_HISTORY, base);
  return parseDomainContract(read(GENERAL_PATH), GENERAL_PATH, base, predecessor);
}

function derivedGeneral(base: ReturnType<typeof parseBaseContract>, mutate?: (document: Document) => void) {
  const predecessor = parseGeneral(base);
  const document = parse(read(GENERAL_PATH)) as Document;
  const rows = parse(read(oracle.general_successor.fragment_path)).rows;
  for (const [table, added] of Object.entries(rows)) document[table] = { ...document[table], ...(added as object) };
  document.version += 1;
  document.lineage = { successor: predecessor.contentIdentity };
  document.defining_source = { id: oracle.general_successor.source_id };
  mutate?.(document);
  return {
    predecessor,
    contract: () => parseDomainContract(stringify(document), "<candidate general successor>", base, predecessor),
  };
}

describe("unshipped candidate contracts", () => {
  const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");

  it("static geneses parse to the pinned identities", () => {
    for (const row of oracle.static) {
      expect(parseDomainContract(read(row.contract_path), row.contract_path, base).contentIdentity).toBe(
        row.contract_identity,
      );
    }
  });

  it("the successor derived from the shipped general document has the pinned identity", () => {
    const { predecessor, contract } = derivedGeneral(base);
    expect(predecessor.contentIdentity).toBe(oracle.general_successor.predecessor_identity);
    expect(contract().contentIdentity).toBe(oracle.general_successor.contract_identity);
  });

  it("dropping an existing general row refuses succession", () => {
    const { contract } = derivedGeneral(base, (document) =>
      Reflect.deleteProperty(document.designs, "independent-groups"),
    );
    expect(contract).toThrow(SuccessionViolation);
  });
});
