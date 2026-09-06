import { describe, expect, it } from "vitest";
import { parseBaseContract } from "../src/contract.js";

describe("document load refuses duplicate keys (design §3.7)", () => {
  it("refuses a duplicate top-level key rather than keeping the last", () => {
    const text = "contract: science\ncontract: science\nversion: 1\nclaim_grammar: {}\n";
    expect(() => parseBaseContract(text, "<dup>")).toThrow(/unique/i);
  });
});
