/** The shared document reading, against the fixture Python also reads (`fixtures/document-reading-v1.json`). */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { readDocument } from "../src/document.js";
import { MalformedContract } from "../src/errors.js";

type Row = { name: string; text: string; value?: unknown; refused?: boolean };

const fixture = JSON.parse(
  readFileSync(new URL("../../fixtures/document-reading-v1.json", import.meta.url), "utf8"),
) as { domain: string; rows: Row[] };

/** The typed form a row writes its value in, so `10` and `"10"`, or `true` and `"true"`, stay apart. */
function typed(value: unknown): unknown {
  if (value === null) return { null: true };
  if (typeof value === "boolean") return { bool: value };
  if (typeof value === "number" && Number.isInteger(value)) return { int: value };
  if (typeof value === "string") return { str: value };
  if (Array.isArray(value)) return { seq: value.map(typed) };
  if (typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    return { map: Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([k, v]) => [k, typed(v)])) };
  }
  throw new Error(`the reader produced ${String(value)}, which no row expects`);
}

describe("document reading", () => {
  it("names its domain and each row says what it expects", () => {
    expect(fixture.domain).toBe("beliefs.document-reading.v1");
    for (const row of fixture.rows) expect("value" in row !== (row.refused === true)).toBe(true);
  });

  it.each(fixture.rows.filter((row) => "value" in row))("row $name", (row) => {
    expect(typed(readDocument(row.text, "<row>"))).toEqual(row.value);
  });

  it.each(fixture.rows.filter((row) => row.refused === true))("refused $name", (row) => {
    expect(() => readDocument(row.text, "<row>")).toThrow(MalformedContract);
  });
});
