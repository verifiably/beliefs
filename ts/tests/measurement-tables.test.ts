import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, ProfileError } from "../src/errors.js";
import { compileProfile } from "../src/profile.js";

const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");
const fixture = read("fixtures/contracts/testing.yaml");
// biome-ignore lint/suspicious/noExplicitAny: authored YAML mutated at the parser boundary
type Document = Record<string, any>;
const document = (): Document => parse(fixture);
const contract = (value: Document) => parseDomainContract(stringify(value), "<measurement>", base);
const compile = (value: Document) => compileProfile(base, [contract(value)]);

describe("measurement declaration tables", () => {
  it.each([
    "1e9999999999999999999",
    "1e-9999999999999999999",
    "1e4097",
    "1e-4097",
    "1e+00004097",
    "1e-00004097",
    `1e${"9".repeat(5000)}`,
    `1e-${"9".repeat(5000)}`,
    "1".repeat(4097),
    `0.${"0".repeat(4095)}1`,
  ])("refuses oversized coefficients before numeric construction (%#)", (factor) => {
    const value = document();
    value.conversions["hour-to-second"].factor = factor;
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it.each([
    ["1e4096", 10n ** 4096n, 1n],
    ["1e-4096", 1n, 10n ** 4096n],
    ["1e+00004096", 10n ** 4096n, 1n],
    ["1e-00004096", 1n, 10n ** 4096n],
    [`1e${"0".repeat(5000)}1`, 10n, 1n],
    ["1".repeat(4096), BigInt("1".repeat(4096)), 1n],
    [`0.${"0".repeat(4094)}1e-4096`, 1n, 10n ** 8191n],
  ] as const)("preserves exact supported boundary coefficients (%#)", (factor, numerator, denominator) => {
    const value = document();
    value.conversions["hour-to-second"].factor = factor;
    expect(contract(value).conversions["hour-to-second"].factor).toEqual({ numerator, denominator, text: factor });
  });
  it("refuses a null monotone direction", () => {
    const value = document();
    value.transformations.logit.direction = null;
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it("resolves measurement references across contracts without activation-order dependence", () => {
    const value = document();
    value.units.second.external = { ucum: "s (release 2.2)", qudt: "unit:SEC (release 3.1)" };
    const testing = contract(value);
    const other = contract({
      contract: "other",
      version: 1,
      lineage: "genesis",
      sorts: {},
      dimensions: {},
      units: { tick: { symbol: "tick", quantity_kind: "testing/duration" } },
      conversions: {
        "tick-to-second": { from: "tick", to: "testing/second", kind: "multiplicative", factor: "0.5", exact: true },
      },
    });
    const profile = compileProfile(base, [other, testing]);
    expect(profile.units["other/tick"].quantityKind).toBe("testing/duration");
    expect(profile.conversions["other/tick-to-second"].toUnit).toBe("testing/second");
    expect(profile.conversions["other/tick-to-second"].factor).toEqual({ numerator: 1n, denominator: 2n, text: "0.5" });
    expect(profile.units).toEqual(compileProfile(base, [testing, other]).units);
    expect(testing.units.second.external).toEqual({ ucum: "s (release 2.2)", qudt: "unit:SEC (release 3.1)" });
    expect(Object.isFrozen(testing.units.second.external)).toBe(true);
  });
  it.each([{ unknown: "ref" }, { ucum: 1 }, { qudt: "" }, null])(
    "refuses malformed external unit references %s",
    (external) => {
      const value = document();
      value.units.second.external = external;
      expect(() => contract(value)).toThrow(MalformedContract);
    },
  );
  it.each([
    ["quantity_kinds", "duration"],
    ["units", "second"],
    ["constants", "avogadro"],
    ["conversions", "hour-to-second"],
    ["transformations", "identity"],
  ])("refuses unsupported retirement on %s.%s", (table, name) => {
    const value = document();
    value[table][name].retired = true;
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it("parses all fixture tables and preserves exact authored decimals", () => {
    const tables = contract(document());
    expect(
      [tables.quantityKinds, tables.units, tables.constants, tables.conversions, tables.transformations]
        .map(Object.keys)
        .map((x) => x.length),
    ).toEqual([10, 15, 1, 6, 8]);
    expect(tables.conversions["hour-to-second"].factor).toEqual({ numerator: 3600n, denominator: 1n, text: "3600" });
    expect(tables.constants.avogadro.value).toEqual({
      numerator: 602214076000000000000000n,
      denominator: 1n,
      text: "6.02214076E23",
    });
    expect(tables.transformations.identity.fixed).toBe(true);
    expect(tables.transformations.standardize.fixed).toBe(false);
    const profile = compile(document());
    expect(profile.units["testing/second"].quantityKind).toBe("testing/duration");
    expect(profile.constants["testing/avogadro"].unit).toBe("testing/per-mole");
    expect(profile.conversions["testing/electronvolt-to-kilojoule-per-mole"].constant).toBe("testing/avogadro");
    expect(profile.units["testing/second"].contract).toBe("testing");
    expect(Object.isFrozen(profile.units)).toBe(true);
    expect(Object.isFrozen(tables.quantityKinds.energy.dimension)).toBe(true);
  });

  it.each([
    ["units", "second", "quantity_kind"],
    ["constants", "avogadro", "unit"],
    ["conversions", "hour-to-second", "from"],
    ["conversions", "hour-to-second", "to"],
    ["conversions", "electronvolt-to-kilojoule-per-mole", "constant"],
  ])("refuses unresolved %s.%s.%s at compile", (table, name, field) => {
    const value = document();
    value[table][name][field] = "missing";
    expect(() => compile(value)).toThrow(ProfileError);
  });

  it("reconciles a constant by multiplication or division and requires it across kinds", () => {
    const value = document();
    const conversion = value.conversions["electronvolt-to-kilojoule-per-mole"];
    conversion.constant = undefined;
    expect(() => compile(value)).toThrow(ProfileError);
    conversion.constant = "avogadro";
    expect(compile(value).conversions["testing/electronvolt-to-kilojoule-per-mole"].constantRole).toBe("multiply");
    [conversion.from, conversion.to] = [conversion.to, conversion.from];
    expect(compile(value).conversions["testing/electronvolt-to-kilojoule-per-mole"].constantRole).toBe("divide");
    value.constants.avogadro.unit = "second";
    expect(() => compile(value)).toThrow(/dimensions do not reconcile/);
  });

  it.each(["tpm", "item", "unity"])("refuses a constant on nonphysical %s", (unit) => {
    const value = document();
    value.constants.avogadro.unit = unit;
    expect(() => compile(value)).toThrow(/dimensions do not reconcile/);
  });

  it("refuses a constant within a kind", () => {
    const value = document();
    value.conversions["hour-to-second"].constant = "avogadro";
    expect(() => compile(value)).toThrow(ProfileError);
  });

  it("refuses duplicate routes in either direction", () => {
    const value = document();
    value.conversions["second-to-hour"] = {
      from: "second",
      to: "hour",
      kind: "multiplicative",
      factor: "0.0002777777777777778",
      exact: false,
    };
    expect(() => compile(value)).toThrow(/pair/);
  });

  it.each([
    ["negate", "scale", null],
    ["negate", "offset", null],
    ["log2", "base", null],
    ["logit", "direction", null],
    ["logit", "fixed", null],
    ["identity", "fixed", false],
    ["negate", "fixed", false],
    ["log2", "fixed", false],
    ["identity", "scale", "1"],
    ["negate", "base", "2"],
    ["log2", "direction", "increasing"],
    ["logit", "direction", "sideways"],
    ["identity", "domain", "missing"],
  ])("refuses malformed %s.%s", (name, field, replacement) => {
    const value = document();
    if (replacement === null) delete value.transformations[name as string][field as string];
    else value.transformations[name as string][field as string] = replacement;
    expect(() => contract(value)).toThrow(MalformedContract);
  });

  it.each([
    ["conversions", "hour-to-second", "factor", "0"],
    ["conversions", "hour-to-second", "factor", "-1"],
    ["transformations", "negate", "scale", "0"],
    ["transformations", "log2", "base", "1"],
    ["transformations", "log2", "base", "0"],
    ["transformations", "log2", "base", "-2"],
    ["constants", "avogadro", "value", "0"],
  ])("refuses noninvertible %s.%s.%s=%s", (table, name, field, replacement) => {
    const value = document();
    value[table][name][field] = replacement;
    expect(() => contract(value)).toThrow(MalformedContract);
  });

  it.each([3600, 3.6, true, "NaN", "Infinity", "1/2", " 2", "1_000", "2\n"])(
    "refuses numeric or nondecimal coefficient %s",
    (replacement) => {
      const value = document();
      value.conversions["hour-to-second"].factor = replacement;
      expect(() => contract(value)).toThrow(MalformedContract);
    },
  );

  it.each([
    ["quantity_kinds", "duration", "dimension", { X: 1 }],
    ["quantity_kinds", "duration", "dimension", { T: true }],
    ["quantity_kinds", "duration", "dimension", { T: "1" }],
    ["conversions", "hour-to-second", "offset", "0"],
    ["conversions", "kelvin-to-celsius", "offset", null],
    ["conversions", "hour-to-second", "kind", "unknown"],
    ["conversions", "hour-to-second", "error", "-1"],
    ["constants", "avogadro", "exact", "true"],
    ["units", "second", "symbol", ""],
  ] as const)("refuses malformed %s.%s.%s", (table, name, field, replacement) => {
    const value = document();
    if (replacement === null) delete value[table][name][field];
    else value[table][name][field] = replacement;
    expect(() => contract(value)).toThrow(MalformedContract);
  });

  it("finds one declared conversion in either direction without inventing a route", () => {
    const profile = compile(document());
    const conversion = profile.conversions["testing/hour-to-second"];
    expect(profile.conversionBetween("testing/hour", "testing/second")).toBe(conversion);
    expect(profile.conversionBetween("testing/second", "testing/hour")).toBe(conversion);
    expect(profile.conversionBetween("testing/hour", "testing/kelvin")).toBeNull();
  });
});
