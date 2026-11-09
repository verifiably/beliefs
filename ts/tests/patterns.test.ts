/** The portable identifier-pattern subset, against the fixture Python also reads. */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { MalformedContract } from "../src/errors.js";
import { IdentifierClass, checkPortablePattern, compilePortable } from "../src/patterns.js";

const fixture = JSON.parse(
  readFileSync(new URL("../../fixtures/identifier-patterns-v1.json", import.meta.url), "utf8"),
) as {
  rows: { name: string; pattern: string; term: string; matches: boolean }[];
  malformed: { name: string; pattern: string }[];
};

describe("identifier patterns", () => {
  it.each(fixture.rows)("row $name", (row) => {
    expect(compilePortable(row.pattern).test(row.term.normalize("NFC"))).toBe(row.matches);
  });

  it.each(fixture.malformed)("malformed $name", (row) => {
    expect(() => checkPortablePattern(row.pattern, "test")).toThrow(MalformedContract);
  });

  it("takes the prefix as literal text", () => {
    expect(new IdentifierClass("HGNC", "HGNC:[1-9][0-9]*").matches("HGNC:5")).toBe(true);
    expect(() => new IdentifierClass("HGNC", "[H]GNC:1")).toThrow(MalformedContract);
    expect(() => new IdentifierClass("H.", "H.:1")).toThrow(MalformedContract);
  });
});
