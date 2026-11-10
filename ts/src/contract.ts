/**
 * Reading the contracts — for **typing only**.
 *
 * The contracts are the normative SSOT, so both implementations read the
 * same authored documents. Building the TypeScript profile from a Python-emitted
 * artifact would give the base contract a Python-privileged reading, which is
 * the arrangement a parity obligation exists to prevent.
 *
 * **What this side deliberately does not do**, because `ts/` is scoped to the
 * shared-encoding path and the parity fixture is the only
 * cross-implementation row:
 *
 * * no **contract content identity** and no **compiled profile identity** — compilation is
 *   Python-only, since it is not a shared encoding;
 * * no **succession validation**;
 * * no **retirement** semantics.
 *
 * The last two are not skipped, they are **refused**. A contract declaring a
 * predecessor, or carrying a retired declaration, is rejected with
 * `UncheckableContract`. Parsing past them would make this a second, weaker
 * reading of the normative source — which is worse than not reading it, because
 * it would look like agreement.
 *
 * **The parsed contracts are branded and deeply frozen**, and that is the root
 * of the trust chain rather than a detail of it. `compileProfile` promises that
 * a claim was typed against the normative source; if a structurally similar
 * object can stand in for a parsed contract, the profile's own brand proves only
 * that `compileProfile` ran, and the promise is empty one link further up. The
 * declarations below are frozen rather than branded: a declaration is reachable
 * only through a contract, so the contract's brand already governs how one gets
 * in, and the freeze is what stops an authored contract being *edited into*
 * after it is read.
 */

import { readDocument } from "./document.js";
import { MalformedContract, SubclassRefused, UncheckableContract, UnparsedContract } from "./errors.js";
import { IdentifierClass } from "./patterns.js";

const TAG_ENCODING = "science.identity.v1";
const NAME = /^[a-z][a-z0-9-]*$/;

const MINT = Symbol("science.contract.mint");

/**
 * A declaration table: local name → declaration.
 *
 * A frozen record with a null prototype, and **not** a `Map`. A `Map`'s entries
 * are beyond the reach of `Object.freeze`, so `ReadonlyMap` is a compile-time
 * fiction that erases to a fully mutable object — the same fiction already found
 * holding a claim's qualifiers. Nothing in this codebase may hold a table it
 * describes as immutable in one.
 */
export type DeclarationTable<T> = Readonly<Record<string, T>>;

function frozenTable<T>(entries: readonly (readonly [string, T])[]): DeclarationTable<T> {
  const table: Record<string, T> = Object.create(null);
  for (const [name, declaration] of entries) table[name] = declaration;
  return Object.freeze(table);
}

/** A role name the kernel admits on every operator; its referent is a record of `worldKind`. */
export interface ReservedRole {
  readonly worldKind: string;
}

export interface ClaimGrammar {
  readonly version: number;
  readonly quantifiers: readonly string[];
  readonly polarities: readonly string[];
  readonly signInaptTag: string;
  readonly layers: readonly string[];
  readonly forms: readonly string[];
  readonly roleCategories: readonly string[];
  readonly bindingKinds: readonly string[];
  readonly mappingTypes: readonly string[];
  readonly placements: readonly string[];
  readonly reservedRoles: Readonly<Record<string, ReservedRole>>;
}

export interface EstimandGrammar {
  readonly version: number;
  readonly contrastKinds: readonly string[];
  readonly scales: readonly string[];
  readonly uncertaintyKinds: readonly string[];
}

export interface CompositeGrammar {
  readonly version: number;
  readonly shapes: readonly string[];
}
const SUPPORTED_SHAPES: readonly string[] = ["dag"];
const SUPPORTED_CONTRAST_KINDS: readonly string[] = ["continuous", "levels"];
const SUPPORTED_SCALES: readonly string[] = ["additive", "multiplicative"];
const SUPPORTED_UNCERTAINTY_KINDS: readonly string[] = ["interval", "standard-error"];
/** The one claim-grammar version this implementation reads. */
const CLAIM_GRAMMAR_VERSION = 2;
/** The claim-grammar closed sets base v2 adds (design §8.1), mirrored from the Python
 * parser. Each must be declared exactly (ruling P2). The form tag `"null"` is a string;
 * a YAML null in any closed set is refused as a malformed tag. */
const SUPPORTED_FORMS: readonly string[] = ["polar", "null"];
const SUPPORTED_ROLE_CATEGORIES: readonly string[] = ["set", "temporal", "class", "pattern"];
const SUPPORTED_BINDING_KINDS: readonly string[] = [
  "release",
  "dataset",
  "scheme",
  "selection",
  "run-output",
  "world-kind",
];
const SUPPORTED_MAPPING_TYPES: readonly string[] = ["exact", "narrower", "broader", "contextual"];
const SUPPORTED_PLACEMENTS: readonly string[] = ["claim", "applicability"];
const SUPPORTED_RESERVED_ROLES: readonly string[] = ["within-model"];

export type FieldType = "string" | "integer" | "boolean" | "ref" | "locator" | "actor";
export interface FieldDecl {
  readonly name: string;
  readonly type: FieldType;
  readonly required: boolean;
  readonly kinds: readonly string[];
  readonly schemes: readonly string[];
}
export interface FacetDecl {
  readonly key: string;
  readonly shape: "reader" | "schema";
  readonly fields: DeclarationTable<FieldDecl>;
  readonly attachesTo: readonly string[];
}
export interface FacetUse {
  readonly required: boolean;
  readonly covered: boolean;
}
export interface KindDecl {
  readonly name: string;
  readonly role: "world" | "prose";
  readonly domain: string | null;
  readonly facets: DeclarationTable<FacetUse>;
}
export interface RelationDecl {
  readonly name: string;
  readonly group: "world" | "lifecycle";
  readonly sources: readonly string[];
  readonly targets: readonly string[];
  readonly sameKind: boolean;
}

/** `composes`' one signature: a composite composes
 * propositions, and nothing else composes anything. The Python parser's
 * `COMPOSES_SIGNATURE`, mirrored — both implementations refuse the same
 * documents with the same message. */
const COMPOSES_SIGNATURE: readonly [readonly string[], readonly string[]] = [["composite"], ["proposition"]];

const SEMANTIC_DOMAIN = /^science\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*\.v[1-9][0-9]*$/;
const FIELD_TYPES: readonly FieldType[] = ["string", "integer", "boolean", "ref", "locator", "actor"];
const FIELD_NAME = /^[a-z][a-z0-9_]*$/;

export class BaseContract {
  #minted = true;
  readonly name: string;
  readonly version: number;
  readonly claimGrammar: ClaimGrammar;
  readonly estimandGrammar: EstimandGrammar;
  readonly compositeGrammar: CompositeGrammar;
  readonly kinds: DeclarationTable<KindDecl>;
  readonly relations: DeclarationTable<RelationDecl>;
  readonly facets: DeclarationTable<FacetDecl>;

  constructor(
    token: symbol,
    parts: {
      version: number;
      claimGrammar: ClaimGrammar;
      estimandGrammar: EstimandGrammar;
      compositeGrammar: CompositeGrammar;
      kinds?: DeclarationTable<KindDecl>;
      relations?: DeclarationTable<RelationDecl>;
      facets?: DeclarationTable<FacetDecl>;
    },
  ) {
    if (new.target !== BaseContract) {
      throw new SubclassRefused("BaseContract is sealed: a subclass could stand in for a parsed contract");
    }
    if (token !== MINT) {
      throw new UnparsedContract(
        "BaseContract is parsed, never authored — use parseBaseContract(text, source). The contracts are the " +
          "normative SSOT; an authored one would let a claim be typed against a grammar nobody wrote down.",
      );
    }
    if (parts.kinds === undefined || parts.relations === undefined || parts.facets === undefined) {
      throw new UnparsedContract("BaseContract declarations are installed only by parseBaseContract(text, source)");
    }
    this.name = "science";
    this.version = parts.version;
    this.claimGrammar = Object.freeze({
      version: parts.claimGrammar.version,
      quantifiers: Object.freeze([...parts.claimGrammar.quantifiers]),
      polarities: Object.freeze([...parts.claimGrammar.polarities]),
      signInaptTag: parts.claimGrammar.signInaptTag,
      layers: Object.freeze([...parts.claimGrammar.layers]),
      forms: Object.freeze([...parts.claimGrammar.forms]),
      roleCategories: Object.freeze([...parts.claimGrammar.roleCategories]),
      bindingKinds: Object.freeze([...parts.claimGrammar.bindingKinds]),
      mappingTypes: Object.freeze([...parts.claimGrammar.mappingTypes]),
      placements: Object.freeze([...parts.claimGrammar.placements]),
      reservedRoles: frozenTable(
        Object.entries(parts.claimGrammar.reservedRoles).map(
          ([name, role]) => [name, Object.freeze({ worldKind: role.worldKind })] as const,
        ),
      ),
    });
    this.estimandGrammar = Object.freeze({
      version: parts.estimandGrammar.version,
      contrastKinds: Object.freeze([...parts.estimandGrammar.contrastKinds]),
      scales: Object.freeze([...parts.estimandGrammar.scales]),
      uncertaintyKinds: Object.freeze([...parts.estimandGrammar.uncertaintyKinds]),
    });
    this.compositeGrammar = Object.freeze({
      version: parts.compositeGrammar.version,
      shapes: Object.freeze([...parts.compositeGrammar.shapes]),
    });
    this.kinds = parts.kinds;
    this.relations = parts.relations;
    this.facets = parts.facets;
    Object.freeze(this);
  }

  /** Did this come from the authored document, or merely look as though it had? */
  static is(value: unknown): value is BaseContract {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

/**
 * What a sort's terms are checked against: **exactly one of six arms**, named by
 * `kind`, each carrying exactly its own fields. The arms are the base contract's
 * `binding_kinds`; a binding carrying another arm's field is refused, never read
 * as one of them. Every field is canonical (NFC) text, and the record-id fields
 * are `<kind>:` followed by 64 lowercase hex characters (ruling P4).
 */
export type SortBinding =
  | { readonly kind: "release"; readonly namespace: string; readonly release: string }
  | { readonly kind: "dataset"; readonly dataset: string }
  | { readonly kind: "scheme"; readonly scheme: string; readonly version: string }
  | {
      readonly kind: "selection";
      readonly dataset: string;
      readonly rule: string;
      readonly selected: string;
      readonly annotator: string;
    }
  | { readonly kind: "run-output"; readonly run: string; readonly dataset: string }
  | { readonly kind: "world-kind"; readonly worldKind: string };

export interface SortDecl {
  readonly name: string;
  readonly binding: SortBinding;
  /** `null` exactly when the binding is `world-kind`, whose class is the kernel's record-id grammar. */
  readonly identifierClass: IdentifierClass | null;
  readonly categories: readonly string[];
}

/**
 * A dimension, on exactly one side (`placement` is `claim` or `applicability`).
 * `appliesTo` lists operators, local or `<namespace>/<name>`, resolved at compile.
 */
export interface DimensionDecl {
  readonly name: string;
  readonly restrictionSort: string;
  readonly placement: string;
  readonly appliesTo: readonly string[];
}

/**
 * One role of a template. A `one` role holds one referent: its `min` and `max`
 * are both 1 and it admits no coefficient. A `many` role holds a multiset whose
 * size lies in `[min, max]` (`max` `null` is unbounded).
 */
export interface RoleDecl {
  readonly name: string;
  readonly arity: "one" | "many";
  readonly min: number;
  readonly max: number | null;
  readonly coefficients: boolean;
  readonly constraint: readonly string[];
}

/** A relation template: an operator issued as `<namespace>/<name>`. */
export interface TemplateDecl {
  readonly name: string;
  readonly roles: DeclarationTable<RoleDecl>;
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly forms: readonly string[];
  /** The roles a composite reads as cause and effect, or `null` for a template forming no edge. */
  readonly edge: { readonly cause: string; readonly effect: string } | null;
  readonly definition: string | null;
  readonly external: { readonly reference: string; readonly mapping: string } | null;
}

/** Which sorts may fill each role of a template. Its name is bookkeeping and never enters claim identity. */
export interface InstantiationDecl {
  readonly name: string;
  readonly template: string;
  readonly roles: Readonly<Record<string, readonly string[]>>;
}

/**
 * A bridging relation: an operator of its own, mapping (`narrower` or
 * `contextual`) to a template whose roles it inherits. `layers` `null` inherits
 * the template's.
 */
export interface BridgeDecl {
  readonly name: string;
  readonly template: string;
  readonly mapping: string;
  readonly roles: Readonly<Record<string, readonly string[]>>;
  readonly layers: readonly string[] | null;
}

/**
 * Which sorts fill the kernel's estimand structure for one instantiation or
 * bridge, keyed by the typed local address of its target, `instantiation:<name>`
 * or `bridge:<name>` (ruling P12): the two tables are separate namespaces and may
 * share a name. `levelSorts` is keyed by role name.
 */
export interface EstimandDecl {
  readonly target: string;
  readonly levelSorts: Readonly<Record<string, string>>;
  readonly measureSort: string;
  readonly identificationSort: string;
  readonly conditioningSort: string;
}

/** A duration convention: scalar fields, each a string or an integer, none validated yet (ruling P3). */
export interface DurationConventionDecl {
  readonly name: string;
  readonly fields: Readonly<Record<string, string | number>>;
}

export class DomainContract {
  #minted = true;
  readonly namespace: string;
  readonly version: number;
  readonly sorts: DeclarationTable<SortDecl>;
  readonly dimensions: DeclarationTable<DimensionDecl>;
  readonly templates: DeclarationTable<TemplateDecl>;
  readonly instantiations: DeclarationTable<InstantiationDecl>;
  readonly bridges: DeclarationTable<BridgeDecl>;
  /** Keyed by typed local target, `instantiation:<name>` or `bridge:<name>`. */
  readonly estimands: DeclarationTable<EstimandDecl>;
  readonly durationConventions: DeclarationTable<DurationConventionDecl>;
  readonly facets: DeclarationTable<FacetDecl>;

  /**
   * The base contract this domain was **typed against**.
   *
   * A domain's layer selections are checked once, here at parse time, and the
   * compiled operator then carries them as facts that nothing revalidates. So
   * parsing under one base and compiling under another needs no forgery at all —
   * both contracts are genuine, both parsers did their jobs — and produces a
   * claim standing on a layer the compiled base does not declare. The missing
   * check was never on either contract; it is **between** them, and this field
   * is what makes it possible.
   *
   * Held as the object, compared by reference. Python records the base's content
   * identity instead, since it computes one and this side deliberately does not do.
   * Reference equality is the **stricter** of the two — it also refuses
   * two separate parses of identical bytes — and strictness is the safe
   * direction for the reduced implementation: it can refuse what Python accepts,
   * never accept what Python refuses.
   */
  readonly base: BaseContract;

  constructor(
    token: symbol,
    parts: {
      namespace: string;
      version: number;
      sorts: DeclarationTable<SortDecl>;
      dimensions: DeclarationTable<DimensionDecl>;
      templates: DeclarationTable<TemplateDecl>;
      instantiations: DeclarationTable<InstantiationDecl>;
      bridges: DeclarationTable<BridgeDecl>;
      estimands: DeclarationTable<EstimandDecl>;
      durationConventions: DeclarationTable<DurationConventionDecl>;
      facets: DeclarationTable<FacetDecl>;
      base: BaseContract;
    },
  ) {
    if (new.target !== DomainContract) {
      throw new SubclassRefused("DomainContract is sealed: a subclass could stand in for a parsed contract");
    }
    if (token !== MINT) {
      throw new UnparsedContract(
        "DomainContract is parsed, never authored — use parseDomainContract(text, source, base). An authored " +
          "one would issue operators, sorts and dimensions that no document declares.",
      );
    }
    this.namespace = parts.namespace;
    this.version = parts.version;
    this.sorts = parts.sorts;
    this.dimensions = parts.dimensions;
    this.templates = parts.templates;
    this.instantiations = parts.instantiations;
    this.bridges = parts.bridges;
    this.estimands = parts.estimands;
    this.durationConventions = parts.durationConventions;
    this.facets = parts.facets;
    this.base = parts.base;
    Object.freeze(this);
  }

  static is(value: unknown): value is DomainContract {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

function mapping(value: unknown, where: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new MalformedContract(`${where}: expected a mapping, found ${JSON.stringify(value)}`);
  }
  return value as Record<string, unknown>;
}

function exactFields(value: Record<string, unknown>, required: string[], optional: string[], where: string): void {
  const permitted = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    // An unrecognized field is refused at load, never ignored — a contract
    // quietly accepting one would make the reader and the loader disagree about
    // what the document says.
    if (!permitted.has(key)) throw new MalformedContract(`${where}: unknown field ${JSON.stringify(key)}`);
  }
  for (const key of required) {
    if (!(key in value)) throw new MalformedContract(`${where}: missing field ${JSON.stringify(key)}`);
  }
}

function positiveInt(value: unknown, where: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 1) {
    throw new MalformedContract(`${where}: expected a positive integer, found ${JSON.stringify(value)}`);
  }
  return value;
}

function tag(value: unknown, where: string): string {
  if (typeof value !== "string" || !NAME.test(value)) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a tag; expected \`[a-z][a-z0-9-]*\``);
  }
  return value;
}

function closedSet(value: unknown, where: string): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new MalformedContract(`${where}: expected a non-empty list`);
  }
  const tags = value.map((entry, index) => tag(entry, `${where}[${index}]`));
  if (new Set(tags).size !== tags.length) throw new MalformedContract(`${where}: duplicate tag in a closed set`);
  return tags;
}

/** Exact equality with the set this implementation operates (ruling P2): wider and narrower both refuse. */
function requireOperated(declared: readonly string[], supported: readonly string[], where: string): void {
  const unoperable = [
    ...declared.filter((entry) => !supported.includes(entry)),
    ...supported.filter((entry) => !declared.includes(entry)),
  ].sort();
  if (unoperable.length > 0)
    throw new MalformedContract(
      `${where}: does not declare exactly the set this implementation operates; ${JSON.stringify(unoperable)} is not operable here`,
    );
}

function reservedRoles(
  value: unknown,
  kinds: DeclarationTable<KindDecl>,
  where: string,
): Readonly<Record<string, ReservedRole>> {
  const table = mapping(value, where);
  requireOperated(Object.keys(table), SUPPORTED_RESERVED_ROLES, where);
  const entries: [string, ReservedRole][] = [];
  for (const [name, entryValue] of Object.entries(table)) {
    const roleWhere = `${where}.${tag(name, where)}`;
    const entry = mapping(entryValue, roleWhere);
    exactFields(entry, ["world_kind"], [], roleWhere);
    const worldKind = tag(entry.world_kind, `${roleWhere}.world_kind`);
    const declared = Object.hasOwn(kinds, worldKind) ? kinds[worldKind] : undefined;
    if (declared === undefined || declared.role !== "world")
      throw new MalformedContract(
        `${roleWhere}.world_kind: ${JSON.stringify(worldKind)} is not a world kind this contract declares`,
      );
    entries.push([name, Object.freeze({ worldKind })]);
  }
  return frozenTable(entries);
}

function parseField(name: string, value: unknown, where: string): FieldDecl {
  if (!FIELD_NAME.test(name))
    throw new MalformedContract(`${where}: ${JSON.stringify(name)} is not a field identifier`);
  const body = mapping(value, where);
  exactFields(body, ["type", "required"], ["kinds", "schemes"], where);
  const type = body.type;
  if (typeof type !== "string" || !(FIELD_TYPES as readonly string[]).includes(type)) {
    throw new MalformedContract(`${where}: type ${JSON.stringify(type)} is not one of ${FIELD_TYPES.join(", ")}`);
  }
  if (typeof body.required !== "boolean") throw new MalformedContract(`${where}: required is a mandatory boolean`);
  if ("kinds" in body !== (type === "ref"))
    throw new MalformedContract(`${where}: kinds is required for type ref and refused for every other type`);
  if ("schemes" in body !== (type === "locator"))
    throw new MalformedContract(`${where}: schemes is required for type locator and refused for every other type`);
  return Object.freeze({
    name,
    type: type as FieldType,
    required: body.required,
    kinds: Object.freeze(type === "ref" ? closedSet(body.kinds, `${where}.kinds`) : []),
    schemes: Object.freeze(type === "locator" ? closedSet(body.schemes, `${where}.schemes`) : []),
  });
}

export function parseFacetDeclarations(
  value: unknown,
  where: string,
  namespace: string | null,
): DeclarationTable<FacetDecl> {
  const entries: [string, FacetDecl][] = [];
  for (const [local, bodyValue] of Object.entries(mapping(value, where))) {
    const facetWhere = `${where}.${local}`;
    const body = mapping(bodyValue, facetWhere);
    const key = namespace === null ? tag(local, facetWhere) : `${namespace}/${tag(local, facetWhere)}`;
    if ("description" in body && typeof body.description !== "string")
      throw new MalformedContract(`${facetWhere}: description is a string, never null`);
    let shape: "reader" | "schema";
    let attachesTo: readonly string[] = Object.freeze([]);
    if (namespace === null) {
      if (body.shape !== "reader" && body.shape !== "schema")
        throw new MalformedContract(`${facetWhere}: shape is reader or schema`);
      shape = body.shape;
      if (shape === "reader") {
        exactFields(body, ["shape", "reader"], ["description"], facetWhere);
        if (typeof body.reader !== "string" || body.reader === "")
          throw new MalformedContract(`${facetWhere}: a reader-shaped facet names its reader`);
        entries.push([key, Object.freeze({ key, shape, fields: frozenTable<FieldDecl>([]), attachesTo })]);
        continue;
      }
      exactFields(body, ["shape", "fields"], ["description"], facetWhere);
    } else {
      exactFields(body, ["attaches_to", "fields"], ["description"], facetWhere);
      shape = "schema";
      attachesTo = Object.freeze(closedSet(body.attaches_to, `${facetWhere}.attaches_to`));
    }
    const fields = frozenTable(
      Object.entries(mapping(body.fields, `${facetWhere}.fields`)).map(([name, fieldValue]) => [
        name,
        parseField(name, fieldValue, `${facetWhere}.fields.${name}`),
      ]),
    );
    entries.push([key, Object.freeze({ key, shape, fields, attachesTo })]);
  }
  return frozenTable(entries);
}

export function parseBaseContract(text: string, source: string): BaseContract {
  const document = mapping(readDocument(text, source), source);
  exactFields(
    document,
    ["contract", "version", "claim_grammar", "estimand_grammar", "composite_grammar", "kinds", "relations", "facets"],
    [],
    source,
  );
  if (document.contract !== "science") {
    throw new MalformedContract(
      `${source}: the base contract is named \`science\`, found ${JSON.stringify(document.contract)}`,
    );
  }
  const grammarDocument = mapping(document.claim_grammar, `${source}.claim_grammar`);
  exactFields(
    grammarDocument,
    [
      "version",
      "tag_encoding",
      "quantifiers",
      "polarities",
      "sign_inapt_tag",
      "forms",
      "layers",
      "role_categories",
      "binding_kinds",
      "mapping_types",
      "placements",
      "reserved_roles",
    ],
    [],
    `${source}.claim_grammar`,
  );
  const grammarVersion = positiveInt(grammarDocument.version, `${source}.claim_grammar.version`);
  if (grammarVersion !== CLAIM_GRAMMAR_VERSION)
    throw new MalformedContract(
      `${source}.claim_grammar.version: ${grammarVersion}, and this implementation reads claim grammar version ${CLAIM_GRAMMAR_VERSION} only`,
    );
  const operatedSet = (name: string, supported: readonly string[]): string[] => {
    const declared = closedSet(grammarDocument[name], `${source}.claim_grammar.${name}`);
    requireOperated(declared, supported, `${source}.claim_grammar.${name}`);
    return declared;
  };
  const forms = operatedSet("forms", SUPPORTED_FORMS);
  const roleCategories = operatedSet("role_categories", SUPPORTED_ROLE_CATEGORIES);
  const bindingKinds = operatedSet("binding_kinds", SUPPORTED_BINDING_KINDS);
  const mappingTypes = operatedSet("mapping_types", SUPPORTED_MAPPING_TYPES);
  const placements = operatedSet("placements", SUPPORTED_PLACEMENTS);
  if (grammarDocument.tag_encoding !== TAG_ENCODING) {
    throw new MalformedContract(
      `${source}.claim_grammar.tag_encoding: this implementation carries ${TAG_ENCODING}, ` +
        `the contract names ${JSON.stringify(grammarDocument.tag_encoding)}`,
    );
  }
  const polarities = closedSet(grammarDocument.polarities, `${source}.claim_grammar.polarities`);
  const signInaptTag = tag(grammarDocument.sign_inapt_tag, `${source}.claim_grammar.sign_inapt_tag`);
  if (polarities.includes(signInaptTag)) {
    // `inapt` and `unsigned` are different facts, and a projection that
    // cannot tell them apart has lost the distinction it exists to carry.
    throw new MalformedContract(
      `${source}.claim_grammar.sign_inapt_tag: ${JSON.stringify(signInaptTag)} is also an assertable polarity`,
    );
  }
  const compositeDocument = mapping(document.composite_grammar, `${source}.composite_grammar`);
  exactFields(compositeDocument, ["version", "shapes"], [], `${source}.composite_grammar`);
  const shapes = closedSet(compositeDocument.shapes, `${source}.composite_grammar.shapes`);
  for (const shape of shapes) {
    if (!SUPPORTED_SHAPES.includes(shape))
      throw new MalformedContract(
        `${source}.composite_grammar.shapes: ${JSON.stringify(shape)} is not a shape this implementation derives`,
      );
  }
  const compositeGrammar: CompositeGrammar = Object.freeze({
    version: positiveInt(compositeDocument.version, `${source}.composite_grammar.version`),
    shapes: Object.freeze(shapes),
  });
  const estimandDocument = mapping(document.estimand_grammar, `${source}.estimand_grammar`);
  exactFields(
    estimandDocument,
    ["version", "tag_encoding", "contrast_kinds", "scales", "uncertainty_kinds"],
    [],
    `${source}.estimand_grammar`,
  );
  if (estimandDocument.tag_encoding !== TAG_ENCODING) {
    throw new MalformedContract(
      `${source}.estimand_grammar.tag_encoding: this implementation carries ${TAG_ENCODING}, the contract names ${JSON.stringify(estimandDocument.tag_encoding)}`,
    );
  }
  const estimandGrammar: EstimandGrammar = {
    version: positiveInt(estimandDocument.version, `${source}.estimand_grammar.version`),
    contrastKinds: closedSet(estimandDocument.contrast_kinds, `${source}.estimand_grammar.contrast_kinds`),
    scales: closedSet(estimandDocument.scales, `${source}.estimand_grammar.scales`),
    uncertaintyKinds: closedSet(estimandDocument.uncertainty_kinds, `${source}.estimand_grammar.uncertainty_kinds`),
  };
  for (const [name, declared, supported] of [
    ["contrast_kinds", estimandGrammar.contrastKinds, SUPPORTED_CONTRAST_KINDS],
    ["scales", estimandGrammar.scales, SUPPORTED_SCALES],
    ["uncertainty_kinds", estimandGrammar.uncertaintyKinds, SUPPORTED_UNCERTAINTY_KINDS],
  ] as const) {
    requireOperated(declared, supported, `${source}.estimand_grammar.${name}`);
  }
  const facets = parseFacetDeclarations(document.facets, `${source}.facets`, null);
  const kindEntries: [string, KindDecl][] = [];
  for (const [name, bodyValue] of Object.entries(mapping(document.kinds, `${source}.kinds`))) {
    const where = `${source}.kinds.${name}`;
    const body = mapping(bodyValue, where);
    if (Object.keys(body).length > 0) exactFields(body, ["facets"], ["domain", "role"], where);
    const role = body.role === undefined ? "world" : body.role;
    if (role !== "world" && role !== "prose") throw new MalformedContract(`${where}: role is world or prose`);
    const facetBody = mapping("facets" in body ? body.facets : {}, `${where}.facets`);
    if (role === "prose" && (body.domain !== undefined || Object.keys(facetBody).some((key) => key !== "display")))
      throw new MalformedContract(`${where}: a prose kind carries no domain and no facet but display`);
    if (
      role === "world" &&
      Object.keys(body).length > 0 &&
      (typeof body.domain !== "string" || !SEMANTIC_DOMAIN.test(body.domain))
    )
      throw new MalformedContract(`${where}: a governed kind names a science.<kind>.v<n> domain`);
    const uses: [string, FacetUse][] = [];
    for (const [key, useValue] of Object.entries(facetBody)) {
      if (!(key in facets))
        throw new MalformedContract(`${where}.facets: ${JSON.stringify(key)} is not a declared facet`);
      const use = mapping(useValue, `${where}.facets.${key}`);
      exactFields(use, ["required", "covered"], [], `${where}.facets.${key}`);
      if (typeof use.required !== "boolean" || typeof use.covered !== "boolean")
        throw new MalformedContract(`${where}.facets.${key}: required and covered are booleans`);
      uses.push([key, Object.freeze({ required: use.required, covered: use.covered })]);
    }
    kindEntries.push([
      name,
      Object.freeze({
        name,
        role,
        domain: role === "world" && typeof body.domain === "string" ? body.domain : null,
        facets: frozenTable(uses),
      }),
    ]);
  }
  const kinds = frozenTable(kindEntries);
  const relationEntries: [string, RelationDecl][] = [];
  for (const [name, bodyValue] of Object.entries(mapping(document.relations, `${source}.relations`))) {
    const where = `${source}.relations.${name}`;
    const body = mapping(bodyValue, where);
    exactFields(body, ["group", "sources", "targets"], ["same_kind"], where);
    if (body.group !== "world" && body.group !== "lifecycle")
      throw new MalformedContract(`${where}: group is world or lifecycle`);
    const sources = Object.freeze(closedSet(body.sources, `${where}.sources`));
    const targets = Object.freeze(closedSet(body.targets, `${where}.targets`));
    for (const kind of [...sources, ...targets])
      if (!(kind in kinds)) throw new MalformedContract(`${where}: ${JSON.stringify(kind)} is not a declared kind`);
    const sameKind = body.same_kind === undefined ? false : body.same_kind;
    if (typeof sameKind !== "boolean") throw new MalformedContract(`${where}.same_kind: is a boolean`);
    if (sameKind) {
      const sourceSet = new Set(sources);
      const targetSet = new Set(targets);
      const equal = sourceSet.size === targetSet.size && [...sourceSet].every((kind) => targetSet.has(kind));
      if (!equal) throw new MalformedContract(`${where}.same_kind: requires sources and targets to be equal sets`);
    }
    if (name === "composes") {
      const [composesSources, composesTargets] = COMPOSES_SIGNATURE;
      const exact = (declared: readonly string[], one: readonly string[]) =>
        declared.length === one.length && declared.every((kind, index) => kind === one[index]);
      if (!exact(sources, composesSources) || !exact(targets, composesTargets))
        throw new MalformedContract(
          `${where}: composes is ${composesSources[0]} → ${composesTargets[0]}, one signature and no other; ` +
            `found ${JSON.stringify(sources)} → ${JSON.stringify(targets)}`,
        );
    }
    relationEntries.push([name, Object.freeze({ name, group: body.group, sources, targets, sameKind })]);
  }
  const relations = frozenTable(relationEntries);
  return new BaseContract(MINT, {
    version: positiveInt(document.version, `${source}.version`),
    claimGrammar: {
      version: grammarVersion,
      quantifiers: closedSet(grammarDocument.quantifiers, `${source}.claim_grammar.quantifiers`),
      polarities,
      signInaptTag,
      layers: closedSet(grammarDocument.layers, `${source}.claim_grammar.layers`),
      forms,
      roleCategories,
      bindingKinds,
      mappingTypes,
      placements,
      reservedRoles: reservedRoles(grammarDocument.reserved_roles, kinds, `${source}.claim_grammar.reserved_roles`),
    },
    estimandGrammar,
    compositeGrammar,
    kinds,
    relations,
    facets,
  });
}

// --- domain contracts -------------------------------------------------------------
//
// Mirrored from the Python parser (`beliefs.contract.domain`), refusal for
// refusal: both implementations read one document, and a case one refuses and
// the other reads is the divergence the parity obligation exists to prevent.
// The two places this side is narrower are named where they act: `refuseRetired`
// and the genesis-only lineage.

/** The v1 grammar's top-level tables, refused by name under base v2. */
const V1_FIELDS = ["operators", "edges"];
const ARITIES = ["one", "many"];
/** The form a sign-inapt template may not declare: a null claim asserts an effect absent, which only a signed relation has. */
const NULL_FORM = "null";
const BRIDGE_REFUSED_MAPPINGS = ["exact", "broader"];
const ESTIMAND_TARGET_KINDS = ["instantiation", "bridge"];
const ROLE_OPTIONAL = ["min", "max", "coefficients", "constraint"];

/** Each binding arm's fields, by their document spelling. */
const BINDING_ARMS: Readonly<Record<string, readonly string[]>> = Object.freeze({
  release: ["namespace", "release"],
  dataset: ["dataset"],
  scheme: ["scheme", "version"],
  selection: ["dataset", "rule", "selected", "annotator"],
  "run-output": ["run", "dataset"],
  "world-kind": ["world_kind"],
});

function refuseRetired(body: Record<string, unknown>, where: string): void {
  if ("retired" in body) {
    throw new UncheckableContract(
      `${where}: retirement is an authoring-boundary property and this implementation carries the shared-encoding path only. It refuses rather than reading past a rule it cannot enforce.`,
    );
  }
}

function declarations(value: unknown, where: string): Record<string, unknown> {
  const table = value === undefined ? {} : mapping(value, where);
  for (const name of Object.keys(table)) tag(name, `${where}: ${name}`);
  return table;
}

function shown(value: unknown): string {
  return value === undefined ? "undefined" : JSON.stringify(value);
}

/** Canonical identifier text: a non-empty string in NFC, as the Python side's `not_a_canonical_identifier`. */
function canonicalText(value: unknown, where: string): string {
  if (typeof value !== "string") {
    throw new MalformedContract(
      `${where}: ${shown(value)} is a ${value === null ? "null" : typeof value}, not a string.`,
    );
  }
  if (value === "") throw new MalformedContract(`${where}: the empty string is not an identifier.`);
  if (value.normalize("NFC") !== value) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not in NFC; normalize it where it enters.`);
  }
  return value;
}

function recordId(value: string, kind: string, where: string): string {
  if (!new RegExp(`^${kind}:[0-9a-f]{64}$`).test(value)) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} is not a ${kind} record id, \`${kind}:\` followed by 64 lowercase hex characters`,
    );
  }
  return value;
}

function bool(value: unknown, where: string): boolean {
  if (typeof value !== "boolean")
    throw new MalformedContract(`${where}: expected true or false, found ${shown(value)}`);
  return value;
}

function count(value: unknown, where: string, floor: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < floor) {
    throw new MalformedContract(`${where}: expected an integer of at least ${floor}, found ${shown(value)}`);
  }
  return value;
}

function noDuplicates(values: readonly string[], where: string): void {
  const seen = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) throw new MalformedContract(`${where}: ${JSON.stringify(value)} appears twice`);
    seen.add(value);
  }
}

/** A list drawn from one of the base contract's closed sets, without repeats. */
function closedList(
  value: unknown,
  allowed: readonly string[],
  where: string,
  what: string,
  empty: boolean,
): readonly string[] {
  if (!Array.isArray(value) || (!empty && value.length === 0)) {
    throw new MalformedContract(
      `${where}: expected a ${empty ? "" : "non-empty "}list of ${what}s, found ${shown(value)}`,
    );
  }
  value.forEach((item, index) => {
    if (typeof item !== "string" || !allowed.includes(item)) {
      throw new MalformedContract(
        `${where}[${index}]: ${shown(item)} is not a ${what} the base contract declares ${JSON.stringify(allowed)}. A domain selects from the base vocabulary and may not extend it.`,
      );
    }
  });
  noDuplicates(value, where);
  return Object.freeze([...value]);
}

/** A local name, or `<namespace>/<name>` naming another contract's declaration, deferred to compile. */
function reference(value: unknown, where: string, namespace: string, baseName: string, what: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new MalformedContract(`${where}: ${shown(value)} is not a ${what} reference`);
  }
  if (!value.includes("/")) return tag(value, where);
  const [foreign, ...rest] = value.split("/");
  const local = rest.join("/");
  tag(foreign, `${where}: namespace`);
  tag(local, `${where}: ${what}`);
  if (foreign === namespace) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names this contract's own namespace; a local ${what} is spelled by its local name ${JSON.stringify(local)} and nothing else`,
    );
  }
  if (foreign === baseName) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names the base contract, which declares no claim vocabulary; a ${what} is a domain's`,
    );
  }
  return value;
}

function requireBaseKind(kind: string, base: BaseContract, where: string): void {
  if (!Object.hasOwn(base.kinds, kind)) {
    throw new MalformedContract(
      `${where}: names ${JSON.stringify(kind)} records, a kind the base contract does not declare`,
    );
  }
}

/** One sort's `binding`: a mapping naming its arm by `kind` and carrying exactly that arm's fields. */
function parseBinding(value: unknown, where: string, base: BaseContract): SortBinding {
  const body = mapping(value, where);
  if (!("kind" in body)) throw new MalformedContract(`${where}: missing field "kind"; a binding names its arm`);
  const kind = body.kind;
  if (
    typeof kind !== "string" ||
    !base.claimGrammar.bindingKinds.includes(kind) ||
    !Object.hasOwn(BINDING_ARMS, kind)
  ) {
    throw new MalformedContract(
      `${where}: binding kind ${shown(kind)} is not one of the base contract's binding_kinds ${JSON.stringify(base.claimGrammar.bindingKinds)}`,
    );
  }
  const names = BINDING_ARMS[kind];
  // A field of another arm is an unknown field here: a binding carrying two
  // arms' fields is refused, never read as one of them.
  exactFields(body, ["kind", ...names], [], where);
  const text: Record<string, string> = Object.create(null);
  for (const name of names) text[name] = canonicalText(body[name], `${where}.${name}`);
  if (kind === "selection") requireBaseKind("classification-rule", base, `${where}.rule`);
  if (kind === "run-output") requireBaseKind("run", base, `${where}.run`);
  let binding: SortBinding;
  switch (kind) {
    case "release":
      binding = { kind, namespace: text.namespace, release: text.release };
      break;
    case "dataset":
      binding = { kind, dataset: recordId(text.dataset, "dataset", `${where}.dataset`) };
      break;
    case "scheme":
      binding = { kind, scheme: text.scheme, version: text.version };
      break;
    case "selection":
      binding = {
        kind,
        dataset: recordId(text.dataset, "dataset", `${where}.dataset`),
        rule: recordId(text.rule, "classification-rule", `${where}.rule`),
        selected: recordId(text.selected, "dataset", `${where}.selected`),
        annotator: text.annotator,
      };
      break;
    case "run-output":
      binding = {
        kind,
        run: recordId(text.run, "run", `${where}.run`),
        dataset: recordId(text.dataset, "dataset", `${where}.dataset`),
      };
      break;
    default: {
      const worldKind = text.world_kind;
      const declared = NAME.test(worldKind) && Object.hasOwn(base.kinds, worldKind) ? base.kinds[worldKind] : undefined;
      if (declared === undefined || declared.role !== "world") {
        throw new MalformedContract(
          `${where}: world_kind ${JSON.stringify(worldKind)} is not a world kind the base contract declares`,
        );
      }
      binding = { kind: "world-kind", worldKind };
    }
  }
  return Object.freeze(binding);
}

function parseIdentifierClass(value: unknown, where: string): IdentifierClass {
  const body = mapping(value, where);
  exactFields(body, ["prefix", "pattern"], [], where);
  const { prefix, pattern } = body;
  if (typeof prefix !== "string" || typeof pattern !== "string") {
    throw new MalformedContract(
      `${where}: prefix and pattern are strings, found ${shown(prefix)} and ${shown(pattern)}`,
    );
  }
  try {
    const identifierClass = new IdentifierClass(prefix, pattern);
    Object.freeze(identifierClass);
    return identifierClass;
  } catch (error) {
    if (error instanceof MalformedContract) throw new MalformedContract(`${where}: ${error.message}`);
    throw error;
  }
}

function parseSort(name: string, value: unknown, where: string, base: BaseContract): SortDecl {
  const body = mapping(value, where);
  exactFields(body, ["binding"], ["identifier_class", "categories", "retired"], where);
  refuseRetired(body, where);
  const binding = parseBinding(body.binding, `${where}.binding`, base);
  let identifierClass: IdentifierClass | null = null;
  if (binding.kind === "world-kind") {
    if ("identifier_class" in body) {
      throw new MalformedContract(
        `${where}: identifier_class is refused on a world-kind sort; its class is the kernel's record-id grammar, \`<kind>:\` followed by 64 lowercase hex`,
      );
    }
  } else {
    if (!("identifier_class" in body)) {
      throw new MalformedContract(
        `${where}: identifier_class is required on a ${JSON.stringify(binding.kind)} binding; it is what a term is checked against at claim construction`,
      );
    }
    identifierClass = parseIdentifierClass(body.identifier_class, `${where}.identifier_class`);
  }
  const categories = closedList(
    "categories" in body ? body.categories : [],
    base.claimGrammar.roleCategories,
    `${where}.categories`,
    "role category",
    true,
  );
  return Object.freeze({ name, binding, identifierClass, categories });
}

function parseRole(name: string, value: unknown, where: string, base: BaseContract): RoleDecl {
  const body = mapping(value, where);
  exactFields(body, ["arity"], ROLE_OPTIONAL, where);
  const arity = body.arity;
  if (arity !== "one" && arity !== "many") {
    throw new MalformedContract(`${where}: arity is \`one\` or \`many\`, found ${shown(arity)}`);
  }
  let min = 1;
  let max: number | null = 1;
  if (arity === "one") {
    for (const field of ["min", "max", "coefficients"]) {
      if (field in body) {
        throw new MalformedContract(
          `${where}: \`${field}\` is declared on a \`one\` role; min, max and coefficients apply to a \`many\` role only`,
        );
      }
    }
  } else {
    min = count("min" in body ? body.min : 1, `${where}.min`, 0);
    max = "max" in body ? count(body.max, `${where}.max`, Math.max(min, 1)) : null;
  }
  return Object.freeze({
    name,
    arity,
    min,
    max,
    coefficients: bool("coefficients" in body ? body.coefficients : false, `${where}.coefficients`),
    constraint: closedList(
      "constraint" in body ? body.constraint : [],
      base.claimGrammar.roleCategories,
      `${where}.constraint`,
      "role category",
      true,
    ),
  });
}

function parseEdge(
  value: unknown,
  where: string,
  roles: DeclarationTable<RoleDecl>,
  layers: readonly string[],
): { readonly cause: string; readonly effect: string } {
  const body = mapping(value, where);
  exactFields(body, ["cause", "effect"], [], where);
  if (!layers.includes("causal")) {
    throw new MalformedContract(`${where}: the template admits no causal layer, so it forms no edge`);
  }
  const { cause, effect } = body;
  for (const [position, role] of [
    ["cause", cause],
    ["effect", effect],
  ] as const) {
    if (typeof role !== "string" || !Object.hasOwn(roles, role)) {
      throw new MalformedContract(`${where}: ${position} ${shown(role)} is not a role this template declares`);
    }
  }
  if (cause === effect) {
    throw new MalformedContract(`${where}: cause and effect must be distinct roles, both are ${JSON.stringify(cause)}`);
  }
  return Object.freeze({ cause: cause as string, effect: effect as string });
}

function parseTemplate(name: string, value: unknown, where: string, base: BaseContract): TemplateDecl {
  const body = mapping(value, where);
  exactFields(
    body,
    ["roles", "sign_apt", "layers", "forms"],
    ["edge", "definition", "external", "description", "retired"],
    where,
  );
  refuseRetired(body, where);
  const grammar = base.claimGrammar;

  const roleEntries: [string, RoleDecl][] = [];
  for (const [roleName, roleBody] of Object.entries(mapping(body.roles, `${where}.roles`))) {
    const roleWhere = `${where}.roles.${roleName}`;
    tag(roleName, roleWhere);
    if (Object.hasOwn(grammar.reservedRoles, roleName)) {
      throw new MalformedContract(
        `${roleWhere}: ${JSON.stringify(roleName)} is a role the base contract reserves on every operator; no template may declare it`,
      );
    }
    roleEntries.push([roleName, parseRole(roleName, roleBody, roleWhere, base)]);
  }
  const roles = frozenTable(roleEntries);

  const signApt = bool(body.sign_apt, `${where}.sign_apt`);
  const layers = closedList(body.layers, grammar.layers, `${where}.layers`, "layer", false);
  const forms = closedList(body.forms, grammar.forms, `${where}.forms`, "form", false);
  if (forms.includes(NULL_FORM) && !signApt) {
    throw new MalformedContract(
      `${where}: forms includes "${NULL_FORM}" on a sign-inapt template. A null claim asserts an effect absent, which only a signed relation has.`,
    );
  }

  const edge = "edge" in body ? parseEdge(body.edge, `${where}.edge`, roles, layers) : null;

  let definition: string | null = null;
  if ("definition" in body) {
    if (typeof body.definition !== "string" || body.definition.trim() === "") {
      throw new MalformedContract(`${where}: definition is prose, found ${shown(body.definition)}`);
    }
    definition = body.definition;
  }

  let external: TemplateDecl["external"] = null;
  if ("external" in body) {
    const externalWhere = `${where}.external`;
    const reference = mapping(body.external, externalWhere);
    exactFields(reference, ["reference", "mapping"], [], externalWhere);
    const mappingType = reference.mapping;
    if (typeof mappingType !== "string" || !grammar.mappingTypes.includes(mappingType)) {
      throw new MalformedContract(
        `${externalWhere}: mapping ${shown(mappingType)} is not one of the base contract's mapping_types ${JSON.stringify(grammar.mappingTypes)}`,
      );
    }
    external = Object.freeze({
      reference: canonicalText(reference.reference, `${externalWhere}.reference`),
      mapping: mappingType,
    });
  }

  return Object.freeze({ name, roles, signApt, layers, forms, edge, definition, external });
}

function parseRoleSorts(
  value: unknown,
  where: string,
  resolve: (value: unknown, where: string) => string,
): Readonly<Record<string, readonly string[]>> {
  const entries: [string, readonly string[]][] = [];
  for (const [role, sorts] of Object.entries(mapping(value, where))) {
    const roleWhere = `${where}.${role}`;
    tag(role, roleWhere);
    if (!Array.isArray(sorts) || sorts.length === 0) {
      throw new MalformedContract(`${roleWhere}: expected a non-empty list of sorts, found ${shown(sorts)}`);
    }
    const listed = sorts.map((sort, index) => resolve(sort, `${roleWhere}[${index}]`));
    noDuplicates(listed, roleWhere);
    entries.push([role, Object.freeze(listed)]);
  }
  return frozenTable(entries);
}

function parseEstimandTarget(
  key: string,
  where: string,
  instantiations: DeclarationTable<InstantiationDecl>,
  bridges: DeclarationTable<BridgeDecl>,
): string {
  const separator = key.indexOf(":");
  const kind = separator < 0 ? "" : key.slice(0, separator);
  if (separator < 0 || !ESTIMAND_TARGET_KINDS.includes(kind)) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(key)} is not a typed target. An estimand declaration is keyed \`instantiation:<name>\` or \`bridge:<name>\`: the two tables are separate namespaces, and an untyped key cannot say which it names.`,
    );
  }
  const name = tag(key.slice(separator + 1), `${where}: ${kind} name`);
  const declared = kind === "instantiation" ? instantiations : bridges;
  if (!Object.hasOwn(declared, name)) {
    throw new MalformedContract(`${where}: ${JSON.stringify(name)} is not a ${kind} this contract declares`);
  }
  return key;
}

/**
 * The base contract is **authenticated**, not merely accepted.
 *
 * A parser that takes another parser's output and trusts it by shape has the
 * hole its own callers were closed against, one level in: the closed-set checks
 * below are worth exactly what the base contract handed to them is worth.
 *
 * References to another contract's declarations (`<namespace>/<name>`) are
 * checked for form here and resolved at compile, which is where the other
 * contract is.
 */
export function parseDomainContract(text: string, source: string, base: BaseContract): DomainContract {
  if (!BaseContract.is(base)) {
    throw new UnparsedContract(
      "the base contract was not parsed from its document — use parseBaseContract(text, source). A domain's " +
        "layers are checked against the base contract and against nothing else afterwards.",
    );
  }
  const document = mapping(readDocument(text, source), source);
  for (const section of ["kinds", "relations"]) {
    if (section in document)
      throw new MalformedContract(`${source}: a domain contract declares no ${section}; refused`);
  }
  const v1Fields = V1_FIELDS.filter((section) => section in document);
  if (v1Fields.length > 0) {
    throw new MalformedContract(
      `${source}: unknown field(s) ${v1Fields.join(", ")}; the v1 grammar's operators and edges are replaced by templates, instantiations and bridges under base v2, so a v1 document cannot parse by accident — refused, never ignored`,
    );
  }
  exactFields(
    document,
    ["contract", "version", "lineage", "sorts", "dimensions"],
    ["templates", "instantiations", "bridges", "duration_conventions", "estimands", "facets"],
    source,
  );

  if (document.lineage !== "genesis") {
    throw new UncheckableContract(
      `${source}.lineage: succession is validated against a declared predecessor, which this implementation does not carry. Only a genesis contract is readable here.`,
    );
  }
  const namespace = tag(document.contract, `${source}.contract`);
  if (namespace === "coordination") {
    throw new MalformedContract(`${source}: "coordination" is reserved for the coordination contract`);
  }
  if (namespace === base.name) {
    throw new MalformedContract(
      `${source}: ${JSON.stringify(namespace)} is the base contract's namespace. Operators are domain-issued without exception, and a base-issued operator would sit outside the closure walk every other operator goes through.`,
    );
  }
  const version = positiveInt(document.version, `${source}.version`);
  const grammar = base.claimGrammar;

  const sorts = frozenTable(
    Object.entries(declarations(document.sorts, `${source}.sorts`)).map(
      ([name, body]) => [name, parseSort(name, body, `${source}.sorts.${name}`, base)] as const,
    ),
  );

  const resolve = (value: unknown, where: string): string => {
    const resolved = reference(value, where, namespace, base.name, "sort");
    if (!resolved.includes("/") && !Object.hasOwn(sorts, resolved)) {
      throw new MalformedContract(`${where}: ${JSON.stringify(resolved)} is not a sort this contract declares`);
    }
    return resolved;
  };

  const dimensionEntries: [string, DimensionDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.dimensions, `${source}.dimensions`))) {
    const where = `${source}.dimensions.${name}`;
    const decl = mapping(body, where);
    exactFields(decl, ["restriction_sort", "placement", "applies_to"], ["retired"], where);
    refuseRetired(decl, where);
    const placement = decl.placement;
    if (typeof placement !== "string" || !grammar.placements.includes(placement)) {
      throw new MalformedContract(
        `${where}: placement ${shown(placement)} is not one of the base contract's placements ${JSON.stringify(grammar.placements)}`,
      );
    }
    if (!Array.isArray(decl.applies_to)) {
      throw new MalformedContract(`${where}: applies_to must be a list of operators, found ${shown(decl.applies_to)}`);
    }
    const appliesTo = decl.applies_to.map((item, index) =>
      reference(item, `${where}.applies_to[${index}]`, namespace, base.name, "operator"),
    );
    noDuplicates(appliesTo, `${where}.applies_to`);
    dimensionEntries.push([
      name,
      Object.freeze({
        name,
        restrictionSort: resolve(decl.restriction_sort, `${where}.restriction_sort`),
        placement,
        appliesTo: Object.freeze(appliesTo),
      }),
    ]);
  }
  const dimensions = frozenTable(dimensionEntries);

  const templates = frozenTable(
    Object.entries(declarations(document.templates, `${source}.templates`)).map(
      ([name, body]) => [name, parseTemplate(name, body, `${source}.templates.${name}`, base)] as const,
    ),
  );

  const instantiationEntries: [string, InstantiationDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.instantiations, `${source}.instantiations`))) {
    const where = `${source}.instantiations.${name}`;
    const decl = mapping(body, where);
    exactFields(decl, ["template", "roles"], ["description", "retired"], where);
    refuseRetired(decl, where);
    instantiationEntries.push([
      name,
      Object.freeze({
        name,
        template: reference(decl.template, `${where}.template`, namespace, base.name, "template"),
        roles: parseRoleSorts(decl.roles, `${where}.roles`, resolve),
      }),
    ]);
  }
  const instantiations = frozenTable(instantiationEntries);

  const bridgeEntries: [string, BridgeDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.bridges, `${source}.bridges`))) {
    const where = `${source}.bridges.${name}`;
    const decl = mapping(body, where);
    exactFields(decl, ["template", "mapping", "roles"], ["layers", "description", "retired"], where);
    refuseRetired(decl, where);
    if (Object.hasOwn(templates, name)) {
      throw new MalformedContract(
        `${where}: ${JSON.stringify(name)} is also a template of this contract. Templates and bridges are both operators, identified only as \`${namespace}/${name}\`, so the two would collide on one operator identifier.`,
      );
    }
    const mappingType = decl.mapping;
    if (typeof mappingType !== "string" || !grammar.mappingTypes.includes(mappingType)) {
      throw new MalformedContract(
        `${where}: mapping ${shown(mappingType)} is not one of the base contract's mapping_types ${JSON.stringify(grammar.mappingTypes)}`,
      );
    }
    if (BRIDGE_REFUSED_MAPPINGS.includes(mappingType)) {
      throw new MalformedContract(
        `${where}: mapping ${JSON.stringify(mappingType)} is refused on a bridge: an exact bridge is its template, and a broader one commits to less than the evidence form it bridges to. A bridge is narrower or contextual.`,
      );
    }
    bridgeEntries.push([
      name,
      Object.freeze({
        name,
        template: reference(decl.template, `${where}.template`, namespace, base.name, "template"),
        mapping: mappingType,
        roles: parseRoleSorts(decl.roles, `${where}.roles`, resolve),
        layers: "layers" in decl ? closedList(decl.layers, grammar.layers, `${where}.layers`, "layer", false) : null,
      }),
    ]);
  }
  const bridges = frozenTable(bridgeEntries);

  const facets = parseFacetDeclarations("facets" in document ? document.facets : {}, `${source}.facets`, namespace);

  const estimandEntries: [string, EstimandDecl][] = [];
  const estimandTable = "estimands" in document ? mapping(document.estimands, `${source}.estimands`) : {};
  for (const [key, body] of Object.entries(estimandTable)) {
    const where = `${source}.estimands.${key}`;
    const target = parseEstimandTarget(key, where, instantiations, bridges);
    const decl = mapping(body, where);
    exactFields(
      decl,
      ["level_sorts", "measure_sort", "identification_sort", "conditioning_sort"],
      ["description"],
      where,
    );
    const levelSorts: Record<string, string> = Object.create(null);
    for (const [role, sort] of Object.entries(mapping(decl.level_sorts, `${where}.level_sorts`))) {
      tag(role, `${where}.level_sorts key`);
      levelSorts[role] = resolve(sort, `${where}.level_sorts.${role}`);
    }
    estimandEntries.push([
      target,
      Object.freeze({
        target,
        levelSorts: Object.freeze(levelSorts),
        measureSort: resolve(decl.measure_sort, `${where}.measure_sort`),
        identificationSort: resolve(decl.identification_sort, `${where}.identification_sort`),
        conditioningSort: resolve(decl.conditioning_sort, `${where}.conditioning_sort`),
      }),
    ]);
  }
  const estimands = frozenTable(estimandEntries);

  const conventionEntries: [string, DurationConventionDecl][] = [];
  for (const [name, body] of Object.entries(
    declarations(document.duration_conventions, `${source}.duration_conventions`),
  )) {
    const where = `${source}.duration_conventions.${name}`;
    const fields: Record<string, string | number> = Object.create(null);
    for (const [field, scalar] of Object.entries(mapping(body, where))) {
      if (typeof scalar !== "string" && !(typeof scalar === "number" && Number.isInteger(scalar))) {
        throw new MalformedContract(`${where}: ${field} is a string or an integer, found ${shown(scalar)}`);
      }
      fields[field] = scalar;
    }
    conventionEntries.push([name, Object.freeze({ name, fields: Object.freeze(fields) })]);
  }
  const durationConventions = frozenTable(conventionEntries);

  return new DomainContract(MINT, {
    namespace,
    version,
    sorts,
    dimensions,
    templates,
    instantiations,
    bridges,
    estimands,
    durationConventions,
    facets,
    base,
  });
}
