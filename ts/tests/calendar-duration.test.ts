import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, ProfileError } from "../src/errors.js";
import { compileProfile } from "../src/profile.js";

const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");
// biome-ignore lint/suspicious/noExplicitAny: authored YAML mutations exercise the parser boundary
const document = (): Record<string, any> => {
  const value = parse(read("fixtures/contracts/testing.yaml"));
  value.units["calendar-month"] = { symbol: "mo", quantity_kind: "duration", calendar: true };
  value.conversions["mean-month-to-second"] = {
    from: "calendar-month",
    to: "second",
    kind: "multiplicative",
    factor: "2629800",
    exact: true,
  };
  value.duration_conventions = { "mean-month": { conversion: "mean-month-to-second" } };
  return value;
};
const contract = (value: unknown) => parseDomainContract(stringify(value), "<calendar>", base);
const compile = (value: unknown) => compileProfile(base, [contract(value)]);

describe("explicit calendar duration conventions", () => {
  it("resolves typed metadata and excludes named conversions from ordinary lookup", () => {
    const value = document();
    const parsed = contract(value);
    const profile = compile(value);
    expect(parsed.units["calendar-month"].calendar).toBe(true);
    expect(parsed.units.second.calendar).toBe(false);
    expect(profile.units["testing/calendar-month"].calendar).toBe(true);
    expect(parsed.durationConventions["mean-month"]).toEqual({
      name: "mean-month",
      conversion: "mean-month-to-second",
    });
    expect(profile.durationConventions["testing/mean-month"]).toEqual({
      term: "testing/mean-month",
      conversion: "testing/mean-month-to-second",
      contract: "testing",
    });
    expect(profile.conversionBetween("testing/calendar-month", "testing/second")).toBeNull();
    expect(profile.conversionBetween("testing/second", "testing/calendar-month")).toBeNull();
    expect(profile.conversionBetween("testing/hour", "testing/second")).not.toBeNull();
  });
  it.each(["true", 1, null, []])("refuses a nonboolean calendar marker %#", (marker) => {
    const value = document();
    value.units["calendar-month"].calendar = marker;
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it.each([{ T: -1 }, { T: 1, L: 1 }, { T: 1, L: 0 }, "construct", "dimensionless"])(
    "requires exactly the physical time dimension %#",
    (dimension) => {
      const value = document();
      value.quantity_kinds.duration.dimension = dimension;
      expect(() => compile(value)).toThrow(ProfileError);
    },
  );
  it.each([
    { unit: "hours", length: 24 },
    {},
    { conversion: "mean-month-to-second", retired: false },
    { conversion: 1 },
  ])("rejects the provisional scalar shape and unsupported fields %#", (declaration) => {
    const value = document();
    value.duration_conventions["mean-month"] = declaration;
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it.each(["missing", "other/missing"])("refuses an undeclared conversion %s", (reference) => {
    const value = document();
    value.duration_conventions["mean-month"].conversion = reference;
    expect(() => compile(value)).toThrow(ProfileError);
  });
  it.each([
    { kind: "affine", offset: "0" },
    { exact: false },
    { error: "0" },
    { constant: "avogadro" },
    { from: "hour" },
    { to: "calendar-month" },
  ])("requires an exact multiplicative conversion with one calendar endpoint %#", (change) => {
    const value = document();
    Object.assign(value.conversions["mean-month-to-second"], change);
    expect(() => compile(value)).toThrow(ProfileError);
  });
  it("requires both endpoints to have the same quantity kind", () => {
    const value = document();
    value.quantity_kinds["other-duration"] = { dimension: { T: 1 } };
    value.units.second.quantity_kind = "other-duration";
    expect(() => compile(value)).toThrow(ProfileError);
  });
  it("does not infer calendar semantics from unit names", () => {
    const value = document();
    value.units["calendar-month"].calendar = false;
    value.duration_conventions = {};
    expect(compile(value).conversionBetween("testing/calendar-month", "testing/second")).not.toBeNull();
  });
  it("resolves a foreign convention conversion independent of activation order", () => {
    const testing = contract(document());
    const other = contract({
      contract: "other",
      version: 1,
      lineage: "genesis",
      sorts: {},
      dimensions: {},
      duration_conventions: { borrowed: { conversion: "testing/mean-month-to-second" } },
    });
    expect(compileProfile(base, [other, testing]).durationConventions["other/borrowed"].conversion).toBe(
      "testing/mean-month-to-second",
    );
  });
  it("preserves the contract grammar's own-qualified reference refusal", () => {
    const value = document();
    value.duration_conventions["mean-month"].conversion = "testing/mean-month-to-second";
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it("preserves unordered calendar conversion pair uniqueness", () => {
    const value = document();
    value.conversions.duplicate = { ...value.conversions["mean-month-to-second"] };
    expect(() => compile(value)).toThrow(ProfileError);
  });
  it("accepts only editorial definition and description beside the conversion", () => {
    const value = document();
    Object.assign(value.duration_conventions["mean-month"], {
      definition: "A fixed mean month.",
      description: "Editorial context.",
    });
    expect(contract(value).durationConventions["mean-month"]).toEqual({
      name: "mean-month",
      conversion: "mean-month-to-second",
    });
  });
});
