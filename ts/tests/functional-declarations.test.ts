import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract } from "../src/errors.js";
import { compileProfile } from "../src/profile.js";

const read = (path: string) => readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8");
const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");
const rows = {
  "difference-of-means": {
    form: "contrast",
    arity: "two",
    response_transformation: "equivariant-affine",
    reversal: "negate",
    response_reversal: "negate",
    exchange: "not-applicable",
    ties: "not-applicable",
    output: "response-difference",
    domain: "real",
    null: "zero",
    increment: "linear",
    uncertainty: "exact",
    parameters: "not-applicable",
  },
  "ratio-of-means": {
    form: "contrast",
    arity: "two",
    response_transformation: "invariant-positive-scaling",
    reversal: "reciprocal",
    response_reversal: "not-applicable",
    exchange: "not-applicable",
    ties: "not-applicable",
    output: "dimensionless",
    domain: "positive",
    null: "one",
    increment: "none",
    uncertainty: "exact",
    parameters: "not-applicable",
  },
  "probability-of-superiority": {
    form: "contrast",
    arity: "two",
    response_transformation: "invariant-strictly-increasing",
    reversal: "complement",
    response_reversal: "complement",
    exchange: "not-applicable",
    ties: "midrank",
    output: "dimensionless",
    domain: "unit-interval",
    null: "half",
    increment: "none",
    uncertainty: "exact",
    parameters: "not-applicable",
  },
  "hodges-lehmann-shift": {
    form: "contrast",
    arity: "two",
    response_transformation: "equivariant-positive-affine",
    reversal: "negate",
    response_reversal: "not-applicable",
    exchange: "not-applicable",
    ties: "midrank",
    output: "response-difference",
    domain: "real",
    null: "zero",
    increment: "none",
    uncertainty: "exact",
    parameters: "not-applicable",
  },
  "log-odds-ratio": {
    form: "contrast",
    arity: "two",
    response_transformation: "fixed",
    reversal: "negate",
    response_reversal: "not-applicable",
    exchange: "not-applicable",
    ties: "not-applicable",
    output: "dimensionless",
    domain: "real",
    null: "zero",
    increment: "none",
    uncertainty: "exact",
    parameters: "not-applicable",
  },
  "spearman-correlation": {
    form: "association",
    arity: "two",
    response_transformation: "invariant-strictly-increasing",
    reversal: "not-applicable",
    response_reversal: "negate",
    exchange: "symmetric",
    ties: "midrank",
    output: "dimensionless",
    domain: "signed-unit-interval",
    null: "zero",
    increment: "not-applicable",
    uncertainty: "recompute",
    parameters: "not-applicable",
  },
  "transfer-entropy": {
    form: "association",
    arity: "two",
    response_transformation: "invariant-strictly-increasing",
    reversal: "not-applicable",
    response_reversal: "invariant",
    exchange: "directed",
    ties: "undefined",
    output: "dimensionless",
    domain: "nonnegative",
    null: "zero",
    increment: "not-applicable",
    uncertainty: "none",
    parameters: "not-applicable",
  },
  "peak-power-fraction": {
    form: "quantity",
    arity: "one",
    response_transformation: "none",
    reversal: "not-applicable",
    response_reversal: "not-applicable",
    exchange: "not-applicable",
    ties: "not-applicable",
    output: "dimensionless",
    domain: "unit-interval",
    null: "none",
    increment: "not-applicable",
    uncertainty: "none",
    parameters: "not-applicable",
  },
  arrhenius: {
    form: "law-parameters",
    arity: "not-applicable",
    response_transformation: "by-parameters",
    reversal: "not-applicable",
    response_reversal: "not-applicable",
    exchange: "not-applicable",
    ties: "not-applicable",
    output: "declared",
    domain: "not-applicable",
    null: "none",
    increment: "not-applicable",
    uncertainty: "exact",
    parameters: {
      Ea: {
        typing: "independent",
        domain: "real",
      },
      lnA: {
        typing: "response-log-level",
        domain: "real",
      },
    },
  },
} as const;
const document = () => parse(read("fixtures/contracts/testing.yaml"));
const contract = (value: unknown) => parseDomainContract(stringify(value), "<functional>", base);

describe("functional declarations", () => {
  it.each(Object.entries(rows))("parses and compiles %s", (name, row) => {
    const value = document();
    value.functionals = { [name]: row };
    const parsed = contract(value);
    expect(parsed.functionals[name]).toEqual(row);
    expect(compileProfile(base, [parsed]).functionals[`testing/${name}`].declaration).toEqual(row);
  });
  it.each(Object.keys(rows["difference-of-means"]))("requires property %s", (key) => {
    const value = document();
    const row = { ...rows["difference-of-means"] };
    Reflect.deleteProperty(row, key);
    value.functionals = { invalid: row };
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it.each([
    ["probability-of-superiority", { reversal: "negate" }],
    ["probability-of-superiority", { response_reversal: "negate" }],
    ["ratio-of-means", { domain: "real" }],
    ["peak-power-fraction", { reversal: "negate" }],
    ["spearman-correlation", { reversal: "invariant" }],
    ["spearman-correlation", { arity: "one" }],
    ["hodges-lehmann-shift", { response_reversal: "negate" }],
    ["difference-of-means", { response_reversal: "not-applicable" }],
    ["difference-of-means", { form: "rank-contrast" }],
    ["difference-of-means", { unknown: "value" }],
    ["difference-of-means", { output: "declared" }],
    ["difference-of-means", { arity: "one" }],
    ["difference-of-means", { exchange: "symmetric" }],
    ["arrhenius", { response_transformation: "fixed" }],
    ["arrhenius", { parameters: "not-applicable" }],
    ["arrhenius", { parameters: { p: { typing: "declared", domain: "real" } } }],
    ["arrhenius", { parameters: { p: { typing: "independent", domain: "not-applicable" } } }],
  ] as const)("refuses invalid %s properties %#", (name, changes) => {
    const value = document();
    value.functionals = { invalid: { ...rows[name], ...changes } };
    expect(() => contract(value)).toThrow(MalformedContract);
  });
  it("compiles the control tables and explicit declaration kinds", () => {
    const value = document();
    value.identification_classes = { observational: { licenses_layers: ["statistical"] } };
    value.designs = { independent: {} };
    value.selection_mechanisms = { cohort: {} };
    const profile = compileProfile(base, [contract(value)]);
    expect(profile.identificationClasses["testing/observational"].licensesLayers).toEqual(["statistical"]);
    expect(profile.designs["testing/independent"].contract).toBe("testing");
    expect(profile.selectionMechanisms["testing/cohort"].term).toBe("testing/cohort");
    expect(profile.estimands["bridge:testing/promotes"].kind).toBe("bridge");
    expect(profile.estimands["instantiation:testing/promotes"].kind).toBe("instantiation");
    expect(profile.instantiations["testing/promotes"].kind).toBe("instantiation");
  });
  it("refuses a roleless template at parse", () => {
    const value = {
      contract: "roleless",
      version: 1,
      lineage: "genesis",
      sorts: {},
      dimensions: {},
      templates: { empty: { roles: {}, sign_apt: false, layers: ["statistical"], forms: ["polar"] } },
    };
    expect(() => contract(value)).toThrow(MalformedContract);
  });
});
