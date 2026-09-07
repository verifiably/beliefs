import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as errors from "../src/errors.js";
import { Decimal, digest, encode } from "../src/identity/v1.js";

const REPO_ROOT = new URL("../../", import.meta.url);
type Component =
  | { t: "null" }
  | { t: "bool"; v: boolean }
  | { t: "int"; v: string }
  | { t: "decimal"; v: string }
  | { t: "float"; v: string }
  | { t: "str"; v: string }
  | { t: "list"; v: Component[] }
  | { t: "obj"; v: Record<string, Component> };
interface Row {
  name: string;
  covers: string;
  domain: string;
  value: Component;
  canonical_bytes?: string;
  digest?: string;
  refusal?: string;
}
const fixture = JSON.parse(readFileSync(new URL("fixtures/identity-v1.json", REPO_ROOT), "utf-8")) as { vector: Row[] };

function rebuild(c: Component): unknown {
  switch (c.t) {
    case "null":
      return null;
    case "bool":
      return c.v;
    case "int":
      return BigInt(c.v);
    case "decimal":
      return new Decimal(c.v);
    case "float":
      return Number(c.v);
    case "str":
      return c.v;
    case "list":
      return c.v.map(rebuild);
    case "obj":
      return Object.fromEntries(Object.entries(c.v).map(([k, v]) => [k, rebuild(v)]));
  }
}

describe("science.identity.v1 parity fixture", () => {
  for (const row of fixture.vector.filter((r) => r.refusal === undefined)) {
    it(`${row.name}: bytes and digest agree`, () => {
      const value = rebuild(row.value);
      expect(new TextDecoder().decode(encode(value))).toBe(row.canonical_bytes);
      expect(digest(row.domain, value)).toBe(row.digest);
    });
  }
  for (const row of fixture.vector.filter((r) => r.refusal !== undefined)) {
    it(`${row.name}: refused as ${row.refusal}`, () => {
      const refusal = (errors as Record<string, unknown>)[row.refusal as string] as new () => Error;
      expect(refusal, `TypeScript has no ${row.refusal}`).toBeDefined();
      expect(() => encode(rebuild(row.value))).toThrow(refusal);
    });
  }
});
