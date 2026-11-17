/**
 * Declared scope relations — the declaration mirror of `beliefs.contract.scope`.
 *
 * A scope relation is a reviewed commitment that two leaf scopes of one
 * applicability dimension select exactly the same cases (`equal`) or that the left
 * is properly contained in the right (`narrower`). This side parses, checks
 * succession and compiles the relation table with its endpoint checks, refusal
 * for refusal with Python. It implements no scope comparison: the comparison,
 * its checked reads and eligibility are Python-only.
 */

import { MalformedContract } from "./errors.js";
import type { IdentityValue } from "./identity/v1.js";

export const SUPPORTED_SCOPE_RELATIONS: readonly string[] = Object.freeze(["equal", "narrower"]);
export const SCOPE_GRAMMAR_VERSION = 1;

export interface ScopeGrammar {
  readonly version: number;
  readonly relations: readonly string[];
}

export type ScopeRelation = "equal" | "narrower";
export type TermScopeEndpoint = { readonly sort: string; readonly term: string };
export type RuleScopeEndpoint = { readonly rule: string; readonly classes: readonly [string] };
export type ScopeEndpoint = TermScopeEndpoint | RuleScopeEndpoint;

export interface ScopeRelationDecl {
  readonly name: string;
  readonly dimension: string;
  readonly relation: ScopeRelation;
  readonly left: ScopeEndpoint;
  readonly right: ScopeEndpoint;
  /** Outside the schema projection: retiring is a status change, never a redefinition. */
  readonly retired: boolean;
}

/** A relation qualified for one profile; `declaration` carries qualified dimension and sorts. */
export interface CompiledScopeRelation {
  readonly term: string;
  readonly contract: string;
  readonly declaration: ScopeRelationDecl;
}

type Projection = { [key: string]: IdentityValue };
const NAME = /^[a-z][a-z0-9-]*$/;
const RULE = /^classification-rule:[0-9a-f]{64}$/;
const FIELDS = ["dimension", "relation", "left", "right"];
const EDITORIAL = ["description", "retired"];

export function isTermEndpoint(endpoint: ScopeEndpoint): endpoint is TermScopeEndpoint {
  return "term" in endpoint;
}

function endpointProjection(endpoint: ScopeEndpoint): Projection {
  return isTermEndpoint(endpoint)
    ? { sort: endpoint.sort, term: endpoint.term }
    : { rule: endpoint.rule, classes: [...endpoint.classes] };
}

/** The immutable semantic projection compared under succession. */
export function scopeRelationSchema(decl: ScopeRelationDecl): Projection {
  return {
    dimension: decl.dimension,
    relation: decl.relation,
    left: endpointProjection(decl.left),
    right: endpointProjection(decl.right),
  };
}

/** The compiled projection: the qualified semantic fields plus retirement. */
export function scopeRelationProjection(relation: CompiledScopeRelation): Projection {
  return { ...scopeRelationSchema(relation.declaration), retired: relation.declaration.retired };
}

function record(value: unknown, where: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new MalformedContract(`${where}: expected a mapping`);
  }
  return value as Record<string, unknown>;
}

function identifier(value: unknown, where: string): string {
  if (typeof value !== "string" || value === "") throw new MalformedContract(`${where}: expected an identifier`);
  if (value.normalize("NFC") !== value) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not in NFC; normalize it where it enters.`);
  }
  return value;
}

function sameKeys(body: Record<string, unknown>, keys: readonly string[]): boolean {
  const present = Object.keys(body);
  return present.length === keys.length && keys.every((key) => Object.hasOwn(body, key));
}

function endpoint(value: unknown, where: string, sortReference: (value: unknown, where: string) => string) {
  const body = record(value, where);
  if (sameKeys(body, ["sort", "term"])) {
    return Object.freeze({
      sort: sortReference(body.sort, `${where}: sort`),
      term: identifier(body.term, `${where}: term`),
    });
  }
  if (sameKeys(body, ["rule", "classes"])) {
    if (typeof body.rule !== "string" || !RULE.test(body.rule)) {
      throw new MalformedContract(`${where}: a rule scope endpoint names a classification-rule id`);
    }
    if (!Array.isArray(body.classes) || body.classes.length !== 1) {
      throw new MalformedContract(`${where}: a rule scope endpoint names exactly one class`);
    }
    const classes = Object.freeze([identifier(body.classes[0], `${where}: classes[0]`)]) as readonly [string];
    return Object.freeze({ rule: body.rule, classes });
  }
  throw new MalformedContract(
    `${where}: an endpoint is exactly {sort, term} or {rule, classes}; interval, time-interval and union endpoints are not admitted`,
  );
}

/** Parse a domain's optional `scope_relations` table (absent is empty), mirroring Python. */
export function parseScopeRelations(
  value: unknown,
  where: string,
  options: {
    relations: readonly string[];
    dimensionReference: (value: unknown, where: string) => string;
    sortReference: (value: unknown, where: string) => string;
  },
): [string, ScopeRelationDecl][] {
  const table = value === undefined ? {} : record(value, where);
  const entries: [string, ScopeRelationDecl][] = [];
  for (const [name, bodyValue] of Object.entries(table)) {
    const at = `${where}.${name}`;
    if (!NAME.test(name)) throw new MalformedContract(`${at}: ${JSON.stringify(name)} is not an identifier`);
    const body = record(bodyValue, at);
    const unknown = Object.keys(body).filter((key) => !FIELDS.includes(key) && !EDITORIAL.includes(key));
    if (unknown.length > 0) {
      throw new MalformedContract(`${at}: unknown field(s) ${unknown.sort().join(", ")}; refused, never ignored`);
    }
    const missing = FIELDS.filter((key) => !Object.hasOwn(body, key));
    if (missing.length > 0) throw new MalformedContract(`${at}: missing field(s) ${missing.join(", ")}`);
    const relation = body.relation;
    if (typeof relation !== "string" || !options.relations.includes(relation)) {
      throw new MalformedContract(
        `${at}: relation ${JSON.stringify(relation)} is not one of the base contract's scope relations ${JSON.stringify(options.relations)}`,
      );
    }
    const retired = body.retired === undefined ? false : body.retired;
    if (typeof retired !== "boolean") throw new MalformedContract(`${at}: retired is true or false`);
    if (body.description !== undefined && typeof body.description !== "string") {
      throw new MalformedContract(`${at}: description is a string`);
    }
    const left = endpoint(body.left, `${at}: left`, options.sortReference);
    const right = endpoint(body.right, `${at}: right`, options.sortReference);
    if (isTermEndpoint(left) !== isTermEndpoint(right)) {
      throw new MalformedContract(`${at}: both endpoints have one form, term or rule`);
    }
    entries.push([
      name,
      Object.freeze({
        name,
        dimension: options.dimensionReference(body.dimension, `${at}: dimension`),
        relation: relation as ScopeRelation,
        left,
        right,
        retired,
      }),
    ]);
  }
  return entries;
}

/** One leaf scope as a comparable key: `term\u0000sort\u0000term` or `rule\u0000id\u0000class`. */
function atomKey(endpoint: ScopeEndpoint): string {
  return isTermEndpoint(endpoint)
    ? `term\u0000${endpoint.sort}\u0000${endpoint.term}`
    : `rule\u0000${endpoint.rule}\u0000${endpoint.classes[0]}`;
}

/**
 * Refuse a profile whose live scope relations are inconsistent, as Python's
 * `compile_scope_graphs` does: a strict relation inside an equality class, a strict
 * directed cycle, or equality or a strict path between two classes of one rule.
 * Retired relations contribute nothing. No comparison is exposed on this side.
 */
export function validateScopeGraphs(
  relations: readonly CompiledScopeRelation[],
  refuse: (message: string) => Error,
): void {
  const byDimension = new Map<string, CompiledScopeRelation[]>();
  for (const relation of [...relations].sort((a, b) => (a.term < b.term ? -1 : a.term > b.term ? 1 : 0))) {
    if (relation.declaration.retired) continue;
    const list = byDimension.get(relation.declaration.dimension) ?? [];
    list.push(relation);
    byDimension.set(relation.declaration.dimension, list);
  }
  for (const [dimension, members] of byDimension) {
    const parent = new Map<string, string>();
    const find = (atom: string): string => {
      let root = atom;
      while ((parent.get(root) ?? root) !== root) root = parent.get(root) as string;
      parent.set(atom, root);
      return root;
    };
    const atoms = new Set<string>();
    for (const relation of members) {
      for (const endpoint of [relation.declaration.left, relation.declaration.right]) atoms.add(atomKey(endpoint));
    }
    for (const relation of members) {
      if (relation.declaration.relation !== "equal") continue;
      const a = find(atomKey(relation.declaration.left));
      const b = find(atomKey(relation.declaration.right));
      if (a !== b) parent.set(a < b ? b : a, a < b ? a : b);
    }
    const edges = new Map<string, Set<string>>();
    for (const relation of members) {
      if (relation.declaration.relation !== "narrower") continue;
      const lower = find(atomKey(relation.declaration.left));
      const upper = find(atomKey(relation.declaration.right));
      if (lower === upper) throw refuse(`${relation.term}: a strict relation between scopes declared equal`);
      const set = edges.get(lower) ?? new Set<string>();
      set.add(upper);
      edges.set(lower, set);
    }
    const above = new Map<string, Set<string>>();
    for (const start of new Set([...atoms].map(find))) {
      const reached = new Set<string>();
      const pending = [...(edges.get(start) ?? [])];
      while (pending.length > 0) {
        const node = pending.pop() as string;
        if (reached.has(node)) continue;
        reached.add(node);
        pending.push(...(edges.get(node) ?? []));
      }
      if (reached.has(start)) throw refuse(`${dimension}: the active scope relations contain a strict cycle`);
      above.set(start, reached);
    }
    const byRule = new Map<string, string[]>();
    for (const atom of atoms) {
      const [form, rule] = atom.split("\u0000");
      if (form !== "rule") continue;
      byRule.set(rule, [...(byRule.get(rule) ?? []), atom]);
    }
    for (const [rule, classes] of byRule) {
      for (let i = 0; i < classes.length; i += 1) {
        for (let j = i + 1; j < classes.length; j += 1) {
          const a = find(classes[i]);
          const b = find(classes[j]);
          if (a === b || above.get(a)?.has(b) || above.get(b)?.has(a)) {
            throw refuse(`${dimension}: two classes of rule ${rule} are made equal or nested by scope relations`);
          }
        }
      }
    }
  }
}
