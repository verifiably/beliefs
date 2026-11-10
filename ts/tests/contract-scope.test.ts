/**
 * What this implementation refuses to read, and why refusing is the point.
 *
 * `ts/` carries the shared-encoding path, so there are contract features
 * it cannot validate: succession needs a declared predecessor and a two-contract
 * diff, and retirement is an authoring-boundary rule this side
 * has no authoring boundary to enforce.
 *
 * The failure mode this file exists to prevent is **quiet divergence**. A
 * reduced parser that skipped `lineage` and ignored `retired` would accept
 * documents the normative reading refuses, and would look like agreement — two
 * implementations reading one SSOT differently, with nothing to notice it. So
 * the unimplemented rules are refusals, not omissions.
 *
 * The domain grammar's own refusals are mirrored from the Python parser
 * (`python/tests/test_domain_contract.py`), one case each, against the shared
 * `fixtures/contracts/testing.yaml` mutated in place.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parse, stringify } from "yaml";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, ProfileError, UncheckableContract } from "../src/errors.js";
import { IdentifierClass } from "../src/patterns.js";
import { compileProfile } from "../src/profile.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const read = (relative: string) => readFileSync(new URL(relative, REPO_ROOT), "utf-8");

const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "contracts/science/CONTRACT.yaml");
const TESTING = read("fixtures/contracts/testing.yaml");
const CROSSING = read("fixtures/contracts/crossing.yaml");
const HEX = (digit: string) => digit.repeat(64);

// biome-ignore lint/suspicious/noExplicitAny: a YAML document mutated by path, as the Python tests mutate a dict
type Document = Record<string, any>;

/** The testing document, edited by `edit`, as YAML text. */
function mutated(edit: (document: Document) => void, text: string = TESTING): string {
  const document = parse(text) as Document;
  edit(document);
  return stringify(document);
}

const parseTesting = (text: string) => parseDomainContract(text, "<testing>", base);

describe("the rules this implementation does not carry are refused, not skipped", () => {
  it("refuses a successor contract, because it cannot check succession", () => {
    const successor = TESTING.replace("lineage: genesis", "lineage: { successor: deadbeef }");
    expect(successor).not.toBe(TESTING);
    expect(() => parseTesting(successor)).toThrow(UncheckableContract);
    expect(() => parseTesting(successor)).toThrow(/succession/);
  });

  it.each([
    ["sorts", "entity"],
    ["dimensions", "population"],
    ["templates", "affects"],
    ["instantiations", "affects-entity-outcome"],
    ["bridges", "promotes"],
  ])("refuses a retired declaration in %s, because retirement lives in authoring", (table, name) => {
    const retired = mutated((document) => {
      document[table][name].retired = true;
    });
    expect(() => parseTesting(retired)).toThrow(UncheckableContract);
  });

  it.each([
    ["sorts", "entity"],
    ["dimensions", "population"],
  ])("still refuses a description on %s as an unknown field", (table, name) => {
    const described = mutated((document) => {
      document[table][name].description = "editorial";
    });
    expect(() => parseTesting(described)).toThrow(MalformedContract);
    expect(() => parseTesting(described)).toThrow(/unknown field "description"/);
  });

  it("reads a genesis contract with nothing retired", () => {
    const contract = parseTesting(TESTING);
    expect(contract.namespace).toBe("testing");
    expect("testing/affects" in compileProfile(base, [contract]).templates).toBe(true);
  });
});

describe("the v2 testing document", () => {
  const contract = parseTesting(TESTING);

  it("parses with every table", () => {
    expect(Object.keys(contract.sorts)).toEqual([
      "entity",
      "outcome",
      "method",
      "level",
      "measure",
      "identification",
      "cohort",
      "event",
      "product",
      "procedure-spec",
      "population",
    ]);
    expect(Object.keys(contract.dimensions)).toEqual(["population", "setting", "follow-up"]);
    expect(Object.keys(contract.templates)).toEqual(["affects", "correlates-with", "transforms", "measured-by"]);
    expect(Object.keys(contract.instantiations)).toEqual([
      "affects-entity-outcome",
      "affects-entity-entity",
      "correlates-entity-outcome",
      "correlates-event-product",
      "transforms-entities",
      "measured-by-entity-method",
      "promotes",
    ]);
    expect(Object.keys(contract.bridges)).toEqual(["promotes"]);
    expect(Object.keys(contract.estimands)).toEqual([
      "instantiation:affects-entity-outcome",
      "instantiation:affects-entity-entity",
      "instantiation:correlates-event-product",
      "bridge:promotes",
      "instantiation:promotes",
    ]);
    expect(contract.durationConventions.day).toEqual({ name: "day", fields: { unit: "hours", length: 24 } });
    expect(Object.keys(contract.facets).sort()).toEqual(["testing/annotation", "testing/axis"]);
  });

  it("reads each of the six binding arms", () => {
    expect(contract.sorts.entity.binding).toEqual({ kind: "release", namespace: "EX", release: "2026-01-01" });
    expect(contract.sorts.method.binding).toEqual({ kind: "scheme", scheme: "EX", version: "1" });
    expect(contract.sorts.cohort.binding).toEqual({ kind: "dataset", dataset: `dataset:${HEX("0")}` });
    expect(contract.sorts.event.binding).toEqual({
      kind: "selection",
      dataset: `dataset:${HEX("1")}`,
      rule: `classification-rule:${HEX("2")}`,
      selected: `dataset:${HEX("3")}`,
      annotator: "EX-annotator",
    });
    expect(contract.sorts.product.binding).toEqual({
      kind: "run-output",
      run: `run:${HEX("4")}`,
      dataset: `dataset:${HEX("5")}`,
    });
    expect(contract.sorts["procedure-spec"].binding).toEqual({ kind: "world-kind", worldKind: "procedure" });
  });

  it("reads identifier classes and categories", () => {
    const entity = contract.sorts.entity;
    expect(entity.identifierClass).toBeInstanceOf(IdentifierClass);
    expect([entity.identifierClass?.prefix, entity.identifierClass?.pattern]).toEqual(["EX", "EX:[a-z0-9\\-]+"]);
    expect(entity.categories).toEqual(["set"]);
    expect(contract.sorts.outcome.categories).toEqual([]);
    expect(contract.sorts.cohort.identifierClass?.pattern).toBe("EX:.+");
    expect(contract.sorts["procedure-spec"].identifierClass).toBeNull();
  });

  it("reads dimensions on one side, with the operators they apply to", () => {
    expect(contract.dimensions.population).toEqual({
      name: "population",
      restrictionSort: "cohort",
      placement: "claim",
      appliesTo: ["affects", "correlates-with", "promotes"],
    });
    expect(contract.dimensions["follow-up"].placement).toBe("applicability");
  });

  it("reads templates with their roles, forms and edge", () => {
    const affects = contract.templates.affects;
    expect(affects.roles.cause).toEqual({
      name: "cause",
      arity: "one",
      min: 1,
      max: 1,
      coefficients: false,
      constraint: [],
    });
    expect([affects.signApt, affects.layers, affects.forms]).toEqual([
      true,
      ["causal", "statistical"],
      ["polar", "null"],
    ]);
    expect(affects.edge).toEqual({ cause: "cause", effect: "effect" });
    expect([affects.definition, affects.external]).toEqual([null, null]);
    expect(contract.templates["correlates-with"].roles.parties).toEqual({
      name: "parties",
      arity: "many",
      min: 2,
      max: 2,
      coefficients: false,
      constraint: [],
    });
    const transforms = contract.templates.transforms;
    expect(transforms.roles.inputs).toMatchObject({ arity: "many", min: 1, max: null, coefficients: true });
    expect(transforms.roles.facilitators).toMatchObject({ arity: "many", min: 0, max: null, coefficients: false });
    expect(transforms.edge).toEqual({ cause: "inputs", effect: "outputs" });
    expect(contract.templates["measured-by"].edge).toBeNull();
  });

  it("reads instantiations, the bridge and the typed estimand keys", () => {
    expect(contract.instantiations["affects-entity-entity"]).toEqual({
      name: "affects-entity-entity",
      template: "affects",
      roles: { cause: ["entity"], effect: ["entity", "outcome"] },
    });
    expect(contract.bridges.promotes).toEqual({
      name: "promotes",
      template: "affects",
      mapping: "narrower",
      roles: { cause: ["entity"], effect: ["outcome"] },
      layers: ["causal"],
    });
    expect(contract.estimands["bridge:promotes"]).toEqual({
      target: "bridge:promotes",
      levelSorts: { cause: "level" },
      measureSort: "measure",
      identificationSort: "identification",
      conditioningSort: "entity",
    });
    expect(contract.estimands["instantiation:promotes"].levelSorts).toEqual({ subject: "level" });
    expect(contract.estimands["instantiation:promotes"].measureSort).toBe("outcome");
  });

  it("reads a definition and an external reference", () => {
    const text = mutated((document) => {
      document.templates.affects.definition = "A change in the cause changes the effect.";
      document.templates.affects.external = { reference: "RO:0002410", mapping: "contextual" };
    });
    const affects = parseTesting(text).templates.affects;
    expect(affects.definition).toBe("A change in the cause changes the effect.");
    expect(affects.external).toEqual({ reference: "RO:0002410", mapping: "contextual" });
  });

  it("holds every declaration frozen", () => {
    for (const value of [
      contract.sorts,
      contract.sorts.event,
      contract.sorts.event.binding,
      contract.sorts.entity.categories,
      contract.dimensions.population.appliesTo,
      contract.templates,
      contract.templates.affects.roles,
      contract.templates.affects.roles.cause,
      contract.templates.affects.roles.cause.constraint,
      contract.templates.affects.layers,
      contract.templates.affects.forms,
      contract.templates.affects.edge,
      contract.instantiations["affects-entity-entity"].roles,
      contract.instantiations["affects-entity-entity"].roles.effect,
      contract.bridges.promotes.layers,
      contract.estimands["bridge:promotes"].levelSorts,
      contract.durationConventions.day.fields,
    ]) {
      expect(Object.isFrozen(value)).toBe(true);
    }
  });
});

describe("the domain grammar's refusals, mirrored from the Python parser", () => {
  const refuses = (edit: (document: Document) => void, pattern: RegExp) => {
    const text = mutated(edit);
    expect(() => parseTesting(text)).toThrow(MalformedContract);
    expect(() => parseTesting(text)).toThrow(pattern);
  };

  it.each(["operators", "edges"])("refuses the v1 field %s, unknown under base v2", (section) => {
    refuses(
      (document) => {
        document[section] = {};
      },
      new RegExp(`unknown field.*${section}`),
    );
  });

  it("refuses kinds and relations in a domain contract", () => {
    expect(() => parseTesting(`${TESTING}\nkinds: {}\n`)).toThrow(/declares no kinds/);
    expect(() => parseTesting(`${TESTING}\nrelations: {}\n`)).toThrow(/declares no relations/);
  });

  it("refuses the base and coordination namespaces", () => {
    refuses((document) => {
      document.contract = "science";
    }, /domain-issued without exception/);
    refuses((document) => {
      document.contract = "coordination";
    }, /reserved/);
  });

  it("refuses a role named within-model, which the base reserves", () => {
    refuses((document) => {
      document.templates.affects.roles["within-model"] = { arity: "one" };
    }, /within-model/);
  });

  it.each(["exact", "broader"])("refuses an %s bridge", (mapping) => {
    refuses((document) => {
      document.bridges.promotes.mapping = mapping;
    }, new RegExp(mapping));
  });

  it("refuses a bridge mapping outside the base set", () => {
    refuses((document) => {
      document.bridges.promotes.mapping = "equivalent";
    }, /mapping_types/);
  });

  it("refuses an edge on a template without the causal layer", () => {
    refuses((document) => {
      document.templates.affects.layers = ["statistical"];
    }, /causal/);
  });

  it.each([
    [{ cause: "cause", effect: "cause" }],
    [{ cause: "cause", effect: "outcome" }],
    [{ cause: "agent", effect: "effect" }],
    [{ cause: "cause" }],
    [{ cause: "cause", effect: "effect", sign: "+" }],
    [{ cause: 0, effect: 1 }],
  ])("refuses the malformed edge %j", (edge) => {
    refuses((document) => {
      document.templates.affects.edge = edge;
    }, /edge/);
  });

  it.each(["min", "max"])("refuses %s on a one role", (field) => {
    refuses(
      (document) => {
        document.templates.affects.roles.cause[field] = 1;
      },
      new RegExp(`${field}.*\`one\``),
    );
  });

  it.each([true, false])("refuses coefficients: %s on a one role", (value) => {
    refuses((document) => {
      document.templates.affects.roles.cause.coefficients = value;
    }, /coefficients.*`one`/);
  });

  it.each([
    [{ arity: "several" }],
    [{ arity: 2 }],
    [{ arity: "many", min: -1 }],
    [{ arity: "many", min: true }],
    [{ arity: "many", min: 3, max: 2 }],
    [{ arity: "many", max: 0 }],
    [{ arity: "many", coefficients: "yes" }],
    [{ arity: "many", constraint: ["subset"] }],
    [{ arity: "many", constraint: ["set", "set"] }],
    [{ arity: "many", position: 0 }],
    [{}],
  ])("refuses the malformed role %j", (role) => {
    refuses((document) => {
      document.templates["correlates-with"].roles.parties = role;
    }, /roles\.parties/);
  });

  it.each([[["polar", "conditional"]], [[]], [["polar", "polar"]], [["polar", null]], ["polar"]])(
    "refuses the form list %j",
    (forms) => {
      refuses((document) => {
        document.templates.affects.forms = forms;
      }, /forms/);
    },
  );

  it('refuses "null" among the forms of a sign-inapt template', () => {
    refuses((document) => {
      document.templates.transforms.forms = ["polar", "null"];
    }, /null/);
  });

  it.each([[[]], [["teleological"]], [["causal", "causal"]]])("refuses the layer list %j", (layers) => {
    refuses((document) => {
      document.templates.affects.layers = layers;
    }, /layers/);
  });

  it("refuses a bridge layer outside the base set", () => {
    refuses((document) => {
      document.bridges.promotes.layers = ["teleological"];
    }, /layers/);
  });

  it.each([
    [{ reference: "RO:0002410", mapping: "equivalent" }],
    [{ reference: "", mapping: "exact" }],
    [{ reference: "RO:0002410" }],
  ])("refuses the malformed external reference %j", (external) => {
    refuses((document) => {
      document.templates.affects.external = external;
    }, /external/);
  });

  it.each(["estimand", null, 1])("refuses the placement %j", (placement) => {
    refuses((document) => {
      document.dimensions.population.placement = placement;
    }, /placement/);
  });

  it.each(["placement", "applies_to", "restriction_sort"])("requires a dimension's %s", (field) => {
    refuses((document) => {
      Reflect.deleteProperty(document.dimensions.population, field);
    }, /missing field/);
  });

  it("refuses an operator listed twice in applies_to", () => {
    refuses((document) => {
      document.dimensions.setting.applies_to = ["affects", "affects"];
    }, /twice/);
  });

  it.each([[["subset"]], [["set", "set"]], ["set"], [[null]]])("refuses the category list %j", (categories) => {
    refuses((document) => {
      document.sorts.entity.categories = categories;
    }, /categories/);
  });

  it("refuses an identifier class on a world-kind sort", () => {
    refuses((document) => {
      document.sorts["procedure-spec"].identifier_class = { prefix: "EX", pattern: "EX:.+" };
    }, /identifier_class/);
  });

  it.each(["entity", "cohort", "method", "event", "product"])("requires an identifier class on %s", (sort) => {
    refuses((document) => {
      Reflect.deleteProperty(document.sorts[sort], "identifier_class");
    }, /identifier_class/);
  });

  it("refuses a pattern that is not NFC", () => {
    refuses((document) => {
      document.sorts.entity.identifier_class = { prefix: "EX", pattern: "EX:cafe\u0301" };
    }, /NFC/);
  });

  it.each([
    [{ prefix: "EX", pattern: "OTHER:[a-z]+" }],
    [{ prefix: "EX", pattern: "EX:\\d+" }],
    [{ prefix: "EX", pattern: 5 }],
    [{ prefix: "EX" }],
    [{ prefix: "EX", pattern: "EX:.+", flags: "i" }],
  ])("refuses the malformed identifier class %j", (identifierClass) => {
    refuses((document) => {
      document.sorts.entity.identifier_class = identifierClass;
    }, /identifier_class/);
  });

  it("refuses the v1 vocabulary field on a sort", () => {
    refuses((document) => {
      document.sorts.entity.vocabulary = { namespace: "EX", release: "1" };
    }, /unknown field "vocabulary"/);
  });

  const selection = (overrides: Document) => ({
    kind: "selection",
    dataset: `dataset:${HEX("0")}`,
    rule: `classification-rule:${HEX("0")}`,
    selected: `dataset:${HEX("0")}`,
    annotator: "EX",
    ...overrides,
  });

  it.each([
    [{ kind: "ontology", namespace: "EX", release: "1" }, /kind/],
    [{ namespace: "EX", release: "1" }, /kind/],
    [{ kind: "release", namespace: "EX", release: "1", dataset: `dataset:${HEX("0")}` }, /unknown field/],
    [{ kind: "dataset", dataset: `dataset:${HEX("0")}`, release: "1" }, /unknown field/],
    [{ kind: "release", namespace: "EX" }, /missing field/],
    [{ kind: "release", namespace: "EX", release: "" }, /empty string/],
    [{ kind: "release", namespace: "cafe\u0301", release: "1" }, /NFC/],
    [{ kind: "release", namespace: "EX", release: 2026 }, /not a string/],
    [{ kind: "scheme", scheme: "EX", version: null }, /not a string/],
    [{ kind: "dataset", dataset: HEX("0") }, /dataset:/],
    [{ kind: "dataset", dataset: `dataset:${HEX("A")}` }, /dataset:/],
    [{ kind: "dataset", dataset: `sha256:${HEX("0")}` }, /dataset:/],
    [selection({ rule: `procedure:${HEX("0")}` }), /classification-rule:/],
    [selection({ selected: "dataset:abc" }), /dataset:/],
    [{ kind: "run-output", run: `dataset:${HEX("0")}`, dataset: `dataset:${HEX("0")}` }, /run:/],
    [{ kind: "run-output", run: `run:${HEX("0")}`, dataset: `run:${HEX("0")}` }, /dataset:/],
    [`dataset:${HEX("0")}`, /mapping/],
  ])("refuses the malformed binding %j", (binding, pattern) => {
    refuses((document) => {
      document.sorts.entity.binding = binding;
    }, pattern);
  });

  it.each(["nowhere", "classification-ruled", "discussion"])("refuses world_kind: %s", (worldKind) => {
    refuses((document) => {
      document.sorts["procedure-spec"].binding = { kind: "world-kind", world_kind: worldKind };
    }, /world kind/);
  });

  it.each([
    "promotes",
    "operator:promotes",
    "bridge:affects-entity-outcome",
    "instantiation:nowhere",
    "template:affects",
    "instantiation:testing/promotes",
    "instantiation:",
  ])("refuses the estimand key %s, which names no declaration of its kind", (key) => {
    const text = mutated((document) => {
      document.estimands[key] = structuredClone(document.estimands["bridge:promotes"]);
    });
    expect(() => parseTesting(text)).toThrow(MalformedContract);
  });

  it("names the typed target an untyped estimand key lacks", () => {
    refuses((document) => {
      document.estimands.promotes = structuredClone(document.estimands["bridge:promotes"]);
    }, /typed target/);
  });

  it("refuses a bridge named like a template, naming the operator collision", () => {
    refuses((document) => {
      document.bridges.affects = structuredClone(document.bridges.promotes);
    }, /both operators/);
  });

  it("admits the same local name across separate tables", () => {
    // The sort and the dimension `population`, the instantiation and the bridge `promotes`.
    const contract = parseTesting(TESTING);
    expect(["population" in contract.sorts, "population" in contract.dimensions]).toEqual([true, true]);
    expect(["promotes" in contract.instantiations, "promotes" in contract.bridges]).toEqual([true, true]);
  });

  it.each([true, null, ["hours"], { x: 1 }])("refuses the duration-convention field %j", (value) => {
    refuses((document) => {
      document.duration_conventions.day.length = value;
    }, /string or an integer/);
  });

  it("refuses a float duration-convention field at the document reader, as Python does", () => {
    refuses((document) => {
      document.duration_conventions.day.length = 1.5;
    }, /the float 1\.5 is refused/);
  });

  it.each(["templates", "instantiations", "bridges", "estimands", "duration_conventions"])(
    "reads a contract without %s",
    (section) => {
      const text = mutated((document) => {
        Reflect.deleteProperty(document, section);
        if (["templates", "instantiations", "bridges"].includes(section)) {
          // The estimands and dimensions name them; drop those too.
          Reflect.deleteProperty(document, "estimands");
          for (const dimension of Object.values(document.dimensions) as Document[]) dimension.applies_to = [];
          if (section === "templates") Reflect.deleteProperty(document, "bridges");
        }
      });
      const table = section === "duration_conventions" ? "durationConventions" : section;
      expect(parseTesting(text)[table as "templates"]).toEqual({});
    },
  );
});

describe("the structural refusals both implementations share", () => {
  it("refuses an unknown field rather than ignoring it", () => {
    // Refused at load, never ignored — otherwise the reader and the loader
    // disagree about what the document says.
    expect(() => parseTesting(`${TESTING}\nsurprise: true\n`)).toThrow(MalformedContract);
  });

  it("refuses two contracts contributing to one namespace", () => {
    const contract = parseTesting(TESTING);
    expect(() => compileProfile(base, [contract, contract])).toThrow(ProfileError);
    expect(() => compileProfile(base, [contract, contract])).toThrow(/namespace/);
  });
});

describe("a cross-contract reference", () => {
  const crossing = () => parseDomainContract(CROSSING, "<crossing>", base);

  it("defers a namespaced reference to compile and resolves it there", () => {
    const contract = crossing();
    expect(contract.instantiations["affects-local-entity"]).toEqual({
      name: "affects-local-entity",
      template: "testing/affects",
      roles: { cause: ["testing/entity"], effect: ["local-entity"] },
    });
    expect(contract.dimensions.scope.restrictionSort).toBe("testing/cohort");
    const profile = compileProfile(base, [contract, parseTesting(TESTING)]);
    const instantiation = profile.instantiations["crossing/affects-local-entity"];
    expect(instantiation.template).toBe("testing/affects");
    expect(instantiation.roles).toEqual({ cause: ["testing/entity"], effect: ["crossing/local-entity"] });
    expect(profile.dimensions["crossing/scope"].restrictionSort).toBe("testing/cohort");
    expect(profile.dimensions["crossing/scope"].appliesTo).toEqual(["testing/affects"]);
  });

  it("refuses an unresolved sort at compile, naming the sort and namespace", () => {
    expect(() => compileProfile(base, [crossing()])).toThrow(MalformedContract);
    expect(() => compileProfile(base, [crossing()])).toThrow(
      /no compiled contract declares sort "testing\/cohort" \(namespace "testing"\)/,
    );
  });

  it("uses the same diagnostic when the namespace is present but the sort is absent", () => {
    const text = mutated((document) => {
      document.dimensions = {};
      document.estimands = {};
      document.instantiations["affects-local-entity"].roles.cause = ["testing/missing"];
    }, CROSSING);
    const contract = parseDomainContract(text, "<crossing>", base);
    expect(() => compileProfile(base, [contract, parseTesting(TESTING)])).toThrow(
      /no compiled contract declares sort "testing\/missing" \(namespace "testing"\)/,
    );
  });

  it("refuses the contract's own namespace and the base's at parse", () => {
    const own = CROSSING.replace("cause: [testing/entity]", "cause: [crossing/local-entity]");
    expect(own).not.toBe(CROSSING);
    expect(() => parseDomainContract(own, "<crossing>", base)).toThrow(/own namespace/);
    const sci = CROSSING.replace("cause: [testing/entity]", "cause: [science/entity]");
    expect(() => parseDomainContract(sci, "<crossing>", base)).toThrow(/declares no claim vocabulary/);
    const template = CROSSING.replace("template: testing/affects", "template: crossing/affects");
    expect(() => parseDomainContract(template, "<crossing>", base)).toThrow(/own namespace/);
  });

  it("still refuses a bare undeclared sort", () => {
    const bare = CROSSING.replace("cause: [testing/entity]", "cause: [entity]");
    expect(() => parseDomainContract(bare, "<crossing>", base)).toThrow(/not a sort this contract declares/);
  });
});
