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
