/**
 * Reading the contracts — for **typing only**.
 *
 * The contracts are the normative SSOT (D §6), so both implementations read the
 * same authored documents. Building the TypeScript profile from a Python-emitted
 * artifact would give the base contract a Python-privileged reading, which is
 * the arrangement a parity obligation exists to prevent.
 *
 * **What this side deliberately does not do**, because D §9 scopes `ts/` to the
 * shared-encoding path and formal model limitation 9 records M10 as the only
 * cross-implementation row:
 *
 * * no **contract content identity** and no **compiled profile identity** — §8
 *   sites compilation as Python-only, since it is not a shared encoding;
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

import { parse as parseYaml } from "yaml";
import { MalformedContract, SubclassRefused, UncheckableContract, UnparsedContract } from "./errors.js";

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

export interface ClaimGrammar {
  readonly version: number;
  readonly quantifiers: readonly string[];
  readonly polarities: readonly string[];
  readonly signInaptTag: string;
  readonly layers: readonly string[];
}

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
}

const SEMANTIC_DOMAIN = /^science\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*\.v[1-9][0-9]*$/;
const FIELD_TYPES: readonly FieldType[] = ["string", "integer", "boolean", "ref", "locator", "actor"];
const FIELD_NAME = /^[a-z][a-z0-9_]*$/;

export class BaseContract {
  #minted = true;
  readonly name: string;
  readonly version: number;
  readonly claimGrammar: ClaimGrammar;
  readonly kinds: DeclarationTable<KindDecl>;
  readonly relations: DeclarationTable<RelationDecl>;
  readonly facets: DeclarationTable<FacetDecl>;

  constructor(
    token: symbol,
    parts: {
      version: number;
      claimGrammar: ClaimGrammar;
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
          "normative SSOT (D §6); an authored one would let a claim be typed against a grammar nobody wrote down.",
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

export interface SortDecl {
  readonly name: string;
}

export interface DimensionDecl {
  readonly name: string;
  readonly restrictionSort: string;
}

export interface OperatorDecl {
  readonly name: string;
  readonly arity: number;
  readonly argSorts: readonly string[];
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly dimensions: readonly string[];
}

export class DomainContract {
  #minted = true;
  readonly namespace: string;
  readonly version: number;
  readonly sorts: DeclarationTable<SortDecl>;
  readonly dimensions: DeclarationTable<DimensionDecl>;
  readonly operators: DeclarationTable<OperatorDecl>;
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
   * identity instead, since it computes one and this side deliberately does not
   * (D §9). Reference equality is the **stricter** of the two — it also refuses
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
      operators: DeclarationTable<OperatorDecl>;
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
          "one would issue operators, sorts and dimensions that no document declares (§7.1).",
      );
    }
    this.namespace = parts.namespace;
    this.version = parts.version;
    this.sorts = parts.sorts;
    this.dimensions = parts.dimensions;
    this.operators = parts.operators;
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
    // D5: an unrecognized field is refused at load, never ignored — a contract
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

function sortReference(
  value: unknown,
  where: string,
  namespace: string,
  baseName: string,
  sorts: DeclarationTable<SortDecl>,
): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a sort reference`);
  }
  if (!value.includes("/")) {
    tag(value, where);
    if (!(value in sorts)) throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a declared sort`);
    return value;
  }
  const [foreign, local, ...rest] = value.split("/");
  if (rest.length > 0 || !NAME.test(foreign) || !NAME.test(local)) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a sort reference`);
  }
  if (foreign === namespace) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names this contract's own namespace; a local sort is spelled by its local name ${JSON.stringify(local)} and nothing else`,
    );
  }
  if (foreign === baseName) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names the base contract, which declares no claim vocabulary (§7.1); a slot sort is a domain's`,
    );
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
  const document = mapping(parseYaml(text), source);
  exactFields(document, ["contract", "version", "claim_grammar", "kinds", "relations", "facets"], [], source);
  if (document.contract !== "science") {
    throw new MalformedContract(
      `${source}: the base contract is named \`science\`, found ${JSON.stringify(document.contract)}`,
    );
  }
  const grammarDocument = mapping(document.claim_grammar, `${source}.claim_grammar`);
  exactFields(
    grammarDocument,
    ["version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"],
    [],
    `${source}.claim_grammar`,
  );
  if (grammarDocument.tag_encoding !== TAG_ENCODING) {
    throw new MalformedContract(
      `${source}.claim_grammar.tag_encoding: this implementation carries ${TAG_ENCODING}, ` +
        `the contract names ${JSON.stringify(grammarDocument.tag_encoding)}`,
    );
  }
  const polarities = closedSet(grammarDocument.polarities, `${source}.claim_grammar.polarities`);
  const signInaptTag = tag(grammarDocument.sign_inapt_tag, `${source}.claim_grammar.sign_inapt_tag`);
  if (polarities.includes(signInaptTag)) {
    // §7.5: `inapt` and `unsigned` are different facts, and a projection that
    // cannot tell them apart has lost the distinction it exists to carry.
    throw new MalformedContract(
      `${source}.claim_grammar.sign_inapt_tag: ${JSON.stringify(signInaptTag)} is also an assertable polarity`,
    );
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
    exactFields(body, ["group", "sources", "targets"], [], where);
    if (body.group !== "world" && body.group !== "lifecycle")
      throw new MalformedContract(`${where}: group is world or lifecycle`);
    const sources = Object.freeze(closedSet(body.sources, `${where}.sources`));
    const targets = Object.freeze(closedSet(body.targets, `${where}.targets`));
    for (const kind of [...sources, ...targets])
      if (!(kind in kinds)) throw new MalformedContract(`${where}: ${JSON.stringify(kind)} is not a declared kind`);
    relationEntries.push([name, Object.freeze({ name, group: body.group, sources, targets })]);
  }
  const relations = frozenTable(relationEntries);
  return new BaseContract(MINT, {
    version: positiveInt(document.version, `${source}.version`),
    claimGrammar: {
      version: positiveInt(grammarDocument.version, `${source}.claim_grammar.version`),
      quantifiers: closedSet(grammarDocument.quantifiers, `${source}.claim_grammar.quantifiers`),
      polarities,
      signInaptTag,
      layers: closedSet(grammarDocument.layers, `${source}.claim_grammar.layers`),
    },
    kinds,
    relations,
    facets,
  });
}

function refuseRetired(body: Record<string, unknown>, where: string): void {
  if ("retired" in body) {
    throw new UncheckableContract(
      `${where}: retirement is an authoring-boundary property (§7.3a) and this implementation carries the shared-encoding path only. It refuses rather than reading past a rule it cannot enforce.`,
    );
  }
}

function declarations(value: unknown, where: string): Record<string, unknown> {
  return value === undefined ? {} : mapping(value, where);
}

/**
 * The base contract is **authenticated**, not merely accepted.
 *
 * A parser that takes another parser's output and trusts it by shape has the
 * hole its own callers were closed against, one level in: the layer check below
 * is worth exactly what the base contract handed to it is worth.
 */
export function parseDomainContract(text: string, source: string, base: BaseContract): DomainContract {
  if (!BaseContract.is(base)) {
    throw new UnparsedContract(
      "the base contract was not parsed from its document — use parseBaseContract(text, source). A domain's " +
        "layers are checked against the base contract and against nothing else afterwards.",
    );
  }
  const document = mapping(parseYaml(text), source);
  for (const section of ["kinds", "relations"]) {
    if (section in document)
      throw new MalformedContract(`${source}: a domain contract declares no ${section}; refused`);
  }
  exactFields(document, ["contract", "version", "lineage"], ["sorts", "dimensions", "operators", "facets"], source);

  if (document.lineage !== "genesis") {
    throw new UncheckableContract(
      `${source}.lineage: succession is validated against a declared predecessor (§8.3), which this implementation does not carry. Only a genesis contract is readable here.`,
    );
  }
  const namespace = tag(document.contract, `${source}.contract`);
  const facets = parseFacetDeclarations("facets" in document ? document.facets : {}, `${source}.facets`, namespace);

  const sortEntries: [string, SortDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.sorts, `${source}.sorts`))) {
    const where = `${source}.sorts.${name}`;
    const sortBody = mapping(body, where);
    exactFields(sortBody, ["vocabulary"], ["retired"], where);
    refuseRetired(sortBody, where);
    sortEntries.push([tag(name, where), Object.freeze({ name })]);
  }
  const sorts = frozenTable(sortEntries);

  const dimensionEntries: [string, DimensionDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.dimensions, `${source}.dimensions`))) {
    const where = `${source}.dimensions.${name}`;
    const dimensionBody = mapping(body, where);
    exactFields(dimensionBody, ["restriction_sort"], ["retired"], where);
    refuseRetired(dimensionBody, where);
    const restrictionSort = sortReference(
      dimensionBody.restriction_sort,
      `${where}.restriction_sort`,
      namespace,
      base.name,
      sorts,
    );
    dimensionEntries.push([tag(name, where), Object.freeze({ name, restrictionSort })]);
  }
  const dimensions = frozenTable(dimensionEntries);

  const operatorEntries: [string, OperatorDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.operators, `${source}.operators`))) {
    const where = `${source}.operators.${name}`;
    const operatorBody = mapping(body, where);
    exactFields(
      operatorBody,
      ["arity", "arg_sorts", "sign_apt", "layers", "dimensions"],
      ["description", "retired"],
      where,
    );
    refuseRetired(operatorBody, where);
    const arity = positiveInt(operatorBody.arity, `${where}.arity`);
    if (!Array.isArray(operatorBody.arg_sorts) || operatorBody.arg_sorts.length !== arity) {
      // Every slot of Fin(arity(op)) is filled, and no slot twice (§6.2).
      throw new MalformedContract(`${where}.arg_sorts: expected exactly ${arity} sorts, one per slot`);
    }
    const argSorts = operatorBody.arg_sorts.map((entry, index) =>
      sortReference(entry, `${where}.arg_sorts[${index}]`, namespace, base.name, sorts),
    );
    if (typeof operatorBody.sign_apt !== "boolean") {
      throw new MalformedContract(`${where}.sign_apt: expected true or false`);
    }
    const layers = closedSet(operatorBody.layers, `${where}.layers`);
    for (const layer of layers) {
      if (!base.claimGrammar.layers.includes(layer)) {
        throw new MalformedContract(
          `${where}.layers: ${JSON.stringify(layer)} is not a layer the base contract declares`,
        );
      }
    }
    if (!Array.isArray(operatorBody.dimensions)) throw new MalformedContract(`${where}.dimensions: expected a list`);
    const permitted = operatorBody.dimensions.map((entry, index) => tag(entry, `${where}.dimensions[${index}]`));
    for (const dimension of permitted) {
      if (!(dimension in dimensions)) {
        throw new MalformedContract(`${where}.dimensions: ${JSON.stringify(dimension)} is not a declared dimension`);
      }
    }
    operatorEntries.push([
      tag(name, where),
      Object.freeze({
        name,
        arity,
        argSorts: Object.freeze(argSorts),
        signApt: operatorBody.sign_apt,
        layers: Object.freeze(layers),
        dimensions: Object.freeze(permitted),
      }),
    ]);
  }

  return new DomainContract(MINT, {
    namespace,
    version: positiveInt(document.version, `${source}.version`),
    sorts,
    dimensions,
    operators: frozenTable(operatorEntries),
    facets,
    base,
  });
}
