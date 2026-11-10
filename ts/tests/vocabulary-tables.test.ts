import { readFileSync } from "node:fs";
import { expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, ProfileError } from "../src/errors.js";
import { compileProfile } from "../src/profile.js";
const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");
// biome-ignore lint/suspicious/noExplicitAny: authored YAML mutations exercise the parser boundary
const document = (): Record<string, any> => parse(read("fixtures/contracts/testing.yaml"));
const contract = (value: unknown) => parseDomainContract(stringify(value), "<vocabulary>", base);
it("reads vocabulary, pack tables and typed dimensions", () => {
  const parsed = contract(document());
  expect([
    Object.keys(parsed.procedureKinds).length,
    Object.keys(parsed.aggregationRules).length,
    Object.keys(parsed.assumptionKinds).length,
  ]).toEqual([5, 2, 4]);
  expect([Object.keys(parsed.measurements).length, Object.keys(parsed.aspects).length]).toEqual([5, 1]);
  expect(parsed.procedureKinds["model-specification"].fillsWithinModel).toBe(true);
  expect(parsed.assumptionKinds["proxy-validity"].particulars).toEqual(["record", "co_scope", "dimensions"]);
  const profile = compileProfile(base, [parsed]);
  expect(profile.admitsMeasurement("testing/entity", "testing/count")).toBe(true);
  expect(profile.admitsMeasurement("testing/cohort", "testing/score")).toBe(false);
  expect(profile.admitsMeasurement("testing/missing", "testing/count")).toBe(false);
  expect(profile.aspectSorts("testing/energy")).toEqual(["testing/energy-aspect"]);
  expect(profile.aspectSorts("testing/duration")).toEqual([]);
  expect(profile.dimensions["testing/follow-up"].restriction).toEqual({
    form: "interval",
    quantityKind: "testing/duration",
  });
});
it.each(["false", 0, null])("refuses a nonboolean fills_within_model %s", (value) => {
  const doc = document();
  doc.procedure_kinds.assay.fills_within_model = value;
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([[], ["record", "record"], [1], ["bad field"], "record"])("refuses malformed particulars %#", (value) => {
  const doc = document();
  doc.assumption_kinds["proxy-validity"].particulars = value;
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([
  { form: "term" },
  { form: "interval" },
  { form: "rule" },
  { form: "union" },
  { form: "union", of: { form: "union", of: { form: "time-interval" } } },
  { form: "term", sort: "entity" },
  { form: "time-interval", sort: "level" },
])("refuses malformed restriction %#", (restriction) => {
  const doc = document();
  doc.dimensions["follow-up"].restriction = restriction;
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([
  { form: "term", sort: "level" },
  { form: "interval", quantity_kind: "duration" },
  { form: "time-interval" },
  { form: "rule", classes: "level" },
  { form: "union", of: { form: "interval", quantity_kind: "duration" } },
])("compiles restriction %#", (restriction) => {
  const doc = document();
  doc.dimensions["follow-up"].restriction = restriction;
  expect(compileProfile(base, [contract(doc)]).dimensions["testing/follow-up"].restriction?.form).toBe(
    restriction.form,
  );
});
it("requires restriction exactly on applicability dimensions", () => {
  const doc = document();
  Reflect.deleteProperty(doc.dimensions["follow-up"], "restriction");
  expect(() => contract(doc)).toThrow(MalformedContract);
  Reflect.deleteProperty(doc.dimensions, "follow-up");
  doc.dimensions.population.restriction = { form: "time-interval" };
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it("folds pack declarations and resolves foreign references", () => {
  const testing = contract(document());
  const other = contract({
    contract: "other",
    version: 1,
    lineage: "genesis",
    sorts: {},
    dimensions: {},
    measurements: { "testing/entity": ["testing/score"] },
  });
  expect(compileProfile(base, [other, testing]).measurements["testing/entity"]).toEqual([
    "testing/abundance",
    "testing/count",
    "testing/score",
  ]);
  expect(compileProfile(base, [testing, other]).measurements).toEqual(
    compileProfile(base, [other, testing]).measurements,
  );
  const doc = document();
  doc.aspects.energy = ["missing"];
  expect(() => compileProfile(base, [contract(doc)])).toThrow(ProfileError);
});
it("refuses mismatched term restrictions inside union", () => {
  const doc = document();
  doc.dimensions["follow-up"].restriction = { form: "union", of: { form: "term", sort: "entity" } };
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it("refuses a newline in a particulars field name", () => {
  const doc = document();
  doc.assumption_kinds["proxy-validity"].particulars = ["record\n"];
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([
  ["procedure_kinds", "assay"],
  ["aggregation_rules", "sum"],
  ["assumption_kinds", "proxy-validity"],
])("refuses unsupported retirement on %s.%s", (table, name) => {
  const doc = document();
  doc[table][name].retired = true;
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([
  ["measurements", "entity", "count"],
  ["measurements", "entity", ["count", "count"]],
  ["aspects", "energy", ["level", "level"]],
  ["aspects", "energy", [null]],
])("refuses malformed pack values %#", (table, key, value) => {
  const doc = document();
  doc[table as string][key as string] = value;
  expect(() => contract(doc)).toThrow(MalformedContract);
});
it.each([
  ["measurements", "entity", ["missing"]],
  ["measurements", "missing", []],
  ["aspects", "missing", ["entity"]],
  ["aspects", "energy", ["missing"]],
])("resolves pack references at compile %#", (table, key, value) => {
  const doc = document();
  doc[table as string][key as string] = value;
  expect(() => compileProfile(base, [contract(doc)])).toThrow(ProfileError);
});
