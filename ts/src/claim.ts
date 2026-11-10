/**
 * `Claim` — the typed claim, and the only route to one, on this side too.
 *
 * The requirement is that a `Claim` is opaque and reachable only through a
 * validated construction, so that the profile-dependent checks happen **once**
 * and no downstream reader re-validates. That requirement is the claim's, not
 * Python's. A TypeScript path that accepted an object shaped like a claim would
 * exercise the encoding and skip the constructor, and the parity run would then
 * compare a four-stage path against a three-stage one.
 *
 * Three things make "opaque" true here, and none of them is `instanceof`: that
 * operator asks whether a prototype is on the chain, which a value can be given
 * without any constructor ever having run on it.
 *
 * * a **private-field brand** on each type, installed only by its constructor;
 * * a **mint token** on `Claim`, so the constructor is unreachable from outside;
 * * **genuinely immutable storage** — `readonly` and `ReadonlyMap` are erased at
 *   run time, so the roles and the qualifiers are held in frozen null-prototype
 *   records, and each `many` role's members in a frozen array.
 *
 * None of it reaches further than the profile it is handed, and the profile
 * reaches no further than the contracts it was compiled from — see `profile.ts`
 * and `contract.ts` for the rest of the chain.
 */

import {
  ClaimError,
  CoefficientRefused,
  DimensionNotClaimSide,
  DuplicateMember,
  FormRefused,
  IdentifierClassMismatch,
  InadmissibleLayer,
  MalformedReferent,
  PolarityRefused,
  ProfileError,
  RestrictionSortMismatch,
  RoleRefused,
  SubclassRefused,
  UndeclaredDimension,
  UndeclaredSort,
  UninstantiatedTemplate,
  UnknownQuantifier,
  UntypedQualifier,
  UntypedReferent,
  WithinModelRefused,
} from "./errors.js";
import { compareByCodePoint } from "./identity/v1.js";
import {
  type CompiledRole,
  type CompiledSort,
  ProfileSpec,
  admitting,
  claimDimensions,
  resolveOperator,
  templateOf,
} from "./profile.js";

const MINT = Symbol("science.claim.mint");

/**
 * A bound referent: a term identifier together with the sort it came from.
 *
 * `term` is the one position in a claim that nothing downstream checks — every
 * other identifier is matched against the profile's tables, and a referent's
 * term is checked only for membership, which is decode's against a snapshot. So
 * the field invariant lives here, and the brand is what makes it worth anything.
 */
export class Referent {
  #minted = true;
  readonly sort: string;
  readonly term: string;

  constructor(sort: string, term: string) {
    if (new.target !== Referent) {
      throw new SubclassRefused(
        "Referent is sealed: a subclass could mint an unchecked value that still passes for one",
      );
    }
    requireIdentifier(sort, "a referent's sort");
    requireIdentifier(term, "a referent's term");
    this.sort = sort;
    this.term = term;
    Object.freeze(this);
  }

  /** The brand check. `instanceof` answers a question about prototypes, not about construction. */
  static is(value: unknown): value is Referent {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

/**
 * A referent with a positive integer coefficient: one entry of a `many` role.
 * Coefficients are `bigint` so they encode as integers under `encodeValue`.
 */
export class Member {
  #minted = true;
  readonly referent: Referent;
  readonly coefficient: bigint;

  constructor(referent: Referent, coefficient = 1n) {
    if (new.target !== Member) {
      throw new SubclassRefused("Member is sealed: a subclass could mint an unchecked value that still passes for one");
    }
    if (!Referent.is(referent)) {
      throw new UntypedReferent("a member's referent is not a Referent; a bare term carries no sort to check");
    }
    if (typeof coefficient !== "bigint" || coefficient < 1n) {
      throw new CoefficientRefused(
        `a member's coefficient is ${String(coefficient)}; it must be an integer of at least 1`,
      );
    }
    this.referent = referent;
    this.coefficient = coefficient;
    Object.freeze(this);
  }

  static is(value: unknown): value is Member {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

/** The canonical member key: NFC of sort and term, compared by code point. */
export function memberKey(referent: Referent): [string, string] {
  return [referent.sort.normalize("NFC"), referent.term.normalize("NFC")];
}

function compareKeys(a: [string, string], b: [string, string]): number {
  return compareByCodePoint(a[0], b[0]) || compareByCodePoint(a[1], b[1]);
}

/** Members sorted by `memberKey`; two sharing a key throw `DuplicateMember`. */
export function canonicalMembers(members: readonly Member[], where: string): readonly Member[] {
  for (const item of members) {
    if (!Member.is(item)) throw new UntypedReferent(`${where} holds a value that is not a Member`);
  }
  const keyed = members.map((member) => ({ member, key: memberKey(member.referent) }));
  keyed.sort((a, b) => compareKeys(a.key, b.key));
  for (let i = 1; i < keyed.length; i += 1) {
    if (compareKeys(keyed[i - 1].key, keyed[i].key) === 0) {
      throw new DuplicateMember(
        `${where} names ${JSON.stringify(keyed[i].key)} more than once; a role holds each referent once`,
      );
    }
  }
  return Object.freeze(keyed.map((entry) => entry.member));
}

/** One entry of the flat fragment: `d ↦ ⟨quantifier, restriction⟩`. */
export class Qualifier {
  #minted = true;
  readonly quantifier: string;
  readonly restriction: Referent;

  constructor(quantifier: string, restriction: Referent) {
    if (new.target !== Qualifier) {
      throw new SubclassRefused(
        "Qualifier is sealed: a subclass could mint an unchecked value that still passes for one",
      );
    }
    if (!Referent.is(restriction)) {
      throw new UntypedReferent("a qualifier's restriction is not a Referent; a bare term carries no sort to check");
    }
    this.quantifier = quantifier;
    this.restriction = restriction;
    Object.freeze(this);
  }

  static is(value: unknown): value is Qualifier {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

/** A role's filling: a `Referent` for a `one` role (and the reserved `within-model`), members for a `many` role. */
export type RoleFilling = Referent | readonly Member[];

export interface ClaimParts {
  readonly operator: string;
  /** Role name → its filling. A map, never a sequence: role names are the template's. */
  readonly roles: ReadonlyMap<string, RoleFilling>;
  readonly qualifiers: ReadonlyMap<string, Qualifier>;
  /** `polar` or `"null"`, from the template's declared set. */
  readonly form: string;
  /** `null` when there is no sign to assert — a sign-inapt operator, or a `"null"`-form claim. */
  readonly polarity: string | null;
  readonly layer: string;
}

/** Role name → filling. Frozen, with a null prototype, each `many` role's members a frozen array in canonical order. */
export type RoleRecord = Readonly<Record<string, RoleFilling>>;

/** Dimension term identifier → qualifier. Frozen, with a null prototype so no inherited key can appear. */
export type QualifierRecord = Readonly<Record<string, Qualifier>>;

export class Claim {
  #minted = true;
  /** The operator's term identifier — a template or a bridge, never a local name. */
  readonly operator: string;
  readonly roles: RoleRecord;
  readonly qualifiers: QualifierRecord;
  readonly form: string;
  /** Always a tag, and the base contract's `sign_inapt_tag` where there is no sign to assert. */
  readonly polarity: string;
  readonly layer: string;

  constructor(token: symbol, parts: ClaimParts & { polarity: string }) {
    if (new.target !== Claim) {
      throw new SubclassRefused("Claim is sealed: a subclass could mint an unchecked claim that still passes for one");
    }
    if (token !== MINT) {
      throw new ClaimError(
        "Claim is validated at construction — use buildClaim(profile, parts). A field-wise constructor " +
          "would put an unchecked claim downstream of the one boundary that checks, and every reader " +
          "that trusts a Claim unconditionally would then be wrong.",
      );
    }
    this.operator = parts.operator;
    // A `ReadonlyMap` is a compile-time fiction: the value is an ordinary `Map`,
    // and `Object.freeze` does not reach its entries — so a caller holding the
    // claim could delete a role or a qualifier and move the claim's own identity.
    // A frozen record cannot be added to, deleted from, or reassigned at run time.
    const roles: Record<string, RoleFilling> = Object.create(null);
    for (const [name, value] of parts.roles) roles[name] = Referent.is(value) ? value : Object.freeze([...value]);
    this.roles = Object.freeze(roles);
    const qualifiers: Record<string, Qualifier> = Object.create(null);
    for (const [dimension, qualifier] of parts.qualifiers) qualifiers[dimension] = qualifier;
    this.qualifiers = Object.freeze(qualifiers);
    this.form = parts.form;
    this.polarity = parts.polarity;
    this.layer = parts.layer;
    Object.freeze(this);
  }

  static is(value: unknown): value is Claim {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

function requireIdentifier(value: unknown, where: string): void {
  if (typeof value !== "string" || value === "") {
    throw new MalformedReferent(
      `${where} is ${JSON.stringify(value)}, not a term identifier. Every position in π_claim is an identifier, and a referent's fields are the only ones no downstream check would catch.`,
    );
  }
}

const ONE = "one";
const CLAIM_SIDE = "claim";
const NULL_FORM = "null";
/** The kernel's record-id grammar: a world kind's class. The kind is then compared with the binding's. */
const RECORD_ID = /^([a-z][a-z0-9-]*):[0-9a-f]{64}$/;

/**
 * The validated constructor: §5.6 steps 1–8, all but membership, in the order
 * and with the error class Python's `Claim._checked` uses for each.
 *
 * The **profile is checked first, and by brand**. A claim typed against a
 * forged profile is typed against nothing, with every operator, layer and sort
 * in it invented by whoever wrote the object. The contracts are the normative
 * SSOT; a profile that did not come from them is not a profile.
 *
 * Retirement is not among the checks: retirement lives in authoring, and this
 * implementation refuses a contract carrying a retired declaration outright
 * rather than half-enforcing an authoring boundary it does not own. Membership
 * is not either: it needs a resolution snapshot, which only the Python side
 * holds, so a referent bound to a `world-kind` sort is checked for record-id
 * syntax only.
 */
export function buildClaim(profile: ProfileSpec, parts: ClaimParts): Claim {
  if (!ProfileSpec.is(profile)) {
    throw new ProfileError(
      "the profile was not compiled from contracts — use compileProfile(base, domains). A structurally " +
        "similar object would type a claim against declarations nobody authored.",
    );
  }
  const grammar = profile.claimGrammar;
  const operator = parts.operator;

  // (1) The operator.
  const declaration = resolveOperator(profile, operator);
  const template = templateOf(profile, declaration);

  // (2) The roles present.
  const roles = parts.roles as unknown;
  if (!(roles instanceof Map)) {
    throw new RoleRefused(
      `the roles of a claim over ${operator} are not a mapping from role name to a referent or members. Roles are named, never positional.`,
    );
  }
  for (const name of roles.keys()) {
    if (typeof name !== "string") {
      throw new RoleRefused(`a role of a claim over ${operator} is named ${String(name)}, not a role name`);
    }
  }
  const declared = Object.keys(template.roles).sort(compareByCodePoint);
  const isReserved = (name: string) => Object.hasOwn(grammar.reservedRoles, name);
  const missing = declared.filter((name) => !roles.has(name));
  if (missing.length > 0) {
    throw new RoleRefused(
      `${operator} declares role(s) ${JSON.stringify(missing)} and the claim fills none of them; every declared role is filled (a \`many\` role with \`min: 0\` is filled by an empty list).`,
    );
  }
  const names = [...(roles as Map<string, unknown>).keys()].sort(compareByCodePoint);
  const undeclared = names.filter((name) => !Object.hasOwn(template.roles, name) && !isReserved(name));
  if (undeclared.length > 0) {
    throw new RoleRefused(
      `${operator} declares no role(s) ${JSON.stringify(undeclared)}; its roles are ${JSON.stringify(declared)}, ` +
        `and the kernel reserves ${JSON.stringify(Object.keys(grammar.reservedRoles).sort(compareByCodePoint))} on every operator.`,
    );
  }

  // (3) Each role's filling.
  const held = new Map<string, RoleFilling>();
  for (const name of names) {
    const value: unknown = roles.get(name);
    const where = `role ${name} of ${operator}`;
    const role = Object.hasOwn(template.roles, name) ? template.roles[name] : undefined;
    if (role === undefined || role.arity === ONE) {
      held.set(name, requireReferent(value, where));
    } else {
      held.set(name, members(value, role, where));
    }
  }

  // (4) Every referent: its sort is declared, its term is in the sort's class.
  for (const [name, value] of held) {
    const worldKind = isReserved(name) ? grammar.reservedRoles[name].worldKind : null;
    for (const referent of referentsOf(value))
      checkReferent(profile, referent, `role ${name} of ${operator}`, worldKind);
  }
  for (const [dimension, qualifier] of parts.qualifiers) {
    if (!Qualifier.is(qualifier)) {
      throw new UntypedQualifier(
        `the qualifier on ${dimension} is not a Qualifier. Structural typing is not enough: any object exposing \`quantifier\` and \`restriction\` would otherwise be stored inside a Claim and trusted as one.`,
      );
    }
    // The restriction needs no type check here: `Qualifier` owns that invariant.
    checkReferent(profile, qualifier.restriction, `the restriction on ${dimension}`, null);
  }

  // (5) Admission: some declaration lists every referent's sort for its role.
  const assignment = new Map<string, ReadonlySet<string>>();
  for (const [name, value] of held) {
    if (!isReserved(name)) assignment.set(name, new Set(referentsOf(value).map((referent) => referent.sort)));
  }
  if (admitting(profile, operator, assignment).length === 0) {
    if (declaration.kind === "bridge") {
      throw new UninstantiatedTemplate(
        `bridge ${operator} admits the role sorts ${routeSorts(declaration.roles)}; a claim with sorts ` +
          `${routeSorts(assignment)} is outside them. A bridge's own role sorts are its admitting declaration.`,
      );
    }
    throw new UninstantiatedTemplate(
      `no instantiation of ${operator} admits a claim with sorts ${routeSorts(assignment)}. Each role's referents must have sorts that one instantiation lists for that role.`,
    );
  }

  // (6) Qualifiers: claim-side dimensions applying to this operator.
  const applying = new Set(claimDimensions(profile, operator));
  for (const [dimension, qualifier] of parts.qualifiers) {
    if (!Object.hasOwn(profile.dimensions, dimension)) {
      throw new UndeclaredDimension(`no dimension ${dimension} in this profile.`);
    }
    const dimensionDecl = profile.dimensions[dimension];
    if (dimensionDecl.placement !== CLAIM_SIDE) {
      throw new DimensionNotClaimSide(
        `${dimension} is placed ${dimensionDecl.placement}: it restricts where an estimate applies, never what a claim says, so it is not a claim qualifier.`,
      );
    }
    if (!applying.has(dimension)) {
      throw new UndeclaredDimension(
        `${dimension} does not apply to ${operator}; the claim-side dimensions that do are ${JSON.stringify([...applying])}.`,
      );
    }
    if (!grammar.quantifiers.includes(qualifier.quantifier)) {
      throw new UnknownQuantifier(
        `quantifier ${qualifier.quantifier} on ${dimension} is outside the kernel's closed set ${JSON.stringify(grammar.quantifiers)}.`,
      );
    }
    if (qualifier.restriction.sort !== dimensionDecl.restrictionSort) {
      throw new RestrictionSortMismatch(
        `${dimension} restricts to sort ${dimensionDecl.restrictionSort}; ${qualifier.restriction.term} is of sort ` +
          `${qualifier.restriction.sort}.`,
      );
    }
  }

  // (7) The form, and the polarity it permits.
  if (!template.forms.includes(parts.form)) {
    throw new FormRefused(
      `${operator} admits form(s) ${JSON.stringify(template.forms)}; ${JSON.stringify(parts.form)} is not among ` +
        `them. "${NULL_FORM}" is admitted only where the template declares it, and only a sign-apt template may.`,
    );
  }
  let tag: string;
  if (parts.form === NULL_FORM) {
    if (parts.polarity !== null) {
      throw new PolarityRefused(
        `a "${NULL_FORM}"-form claim asserts an absent effect, which has no sign: there is no polarity to supply — not even ${grammar.signInaptTag}, which the projection carries on the claim's behalf.`,
      );
    }
    tag = grammar.signInaptTag;
  } else if (template.signApt) {
    if (parts.polarity === null) {
      throw new PolarityRefused(
        `${operator} is sign-apt, so a polar claim asserts a polarity — one of ${JSON.stringify(grammar.polarities)}. ${grammar.signInaptTag} is not among them: it says the operator has no sign to assert, which is a different fact from asserting none.`,
      );
    }
    if (!grammar.polarities.includes(parts.polarity)) {
      throw new PolarityRefused(
        `polarity ${parts.polarity} is outside the base contract's closed set ${JSON.stringify(grammar.polarities)}.`,
      );
    }
    tag = parts.polarity;
  } else {
    if (parts.polarity !== null) {
      throw new PolarityRefused(
        `${operator} is sign-inapt: Polarity(op) is the unit type, so there is no polarity to supply — not even ${grammar.signInaptTag}, which the projection carries on the claim's behalf and an author never chooses.`,
      );
    }
    tag = grammar.signInaptTag;
  }

  // (8) The layer: the template's, or a bridge's own narrowing.
  if (!declaration.layers.includes(parts.layer)) {
    throw new InadmissibleLayer(
      `${operator} admits layers ${JSON.stringify(declaration.layers)}; ${parts.layer} is not among them.`,
    );
  }

  return new Claim(MINT, { ...parts, roles: held, polarity: tag });
}

function requireReferent(value: unknown, where: string): Referent {
  if (!Referent.is(value)) {
    throw new UntypedReferent(
      `${where} does not hold a Referent. A \`one\` role holds a Referent, and a bare term carries no sort to check against the sorts the role admits.`,
    );
  }
  return value;
}

/**
 * A `many` role's filling, typed: an array of members within `[min, max]`,
 * coefficients of 1 unless the role admits others, in canonical member-key
 * order with no two sharing a key.
 */
function members(value: unknown, role: CompiledRole, where: string): readonly Member[] {
  if (!Array.isArray(value)) {
    throw new UntypedReferent(
      `${where} is a \`many\` role and does not hold an array; it holds Members, each a referent with its coefficient.`,
    );
  }
  for (const item of value) {
    if (!Member.is(item)) throw new UntypedReferent(`${where} holds a value that is not a Member`);
  }
  const items = value as readonly Member[];
  if (items.length < role.min || (role.max !== null && items.length > role.max)) {
    throw new RoleRefused(
      `${where} holds ${items.length} member(s); its declared member count is [${role.min}, ${role.max === null ? "∞" : role.max}].`,
    );
  }
  if (!role.coefficients) {
    for (const item of items) {
      if (item.coefficient !== 1n) {
        throw new CoefficientRefused(
          `${where} admits no coefficient but 1; ${item.referent.term} carries ${item.coefficient}.`,
        );
      }
    }
  }
  return canonicalMembers(items, where);
}

/**
 * Step (4) for one referent: a declared sort, the reserved world kind where one
 * is required, and a term in the sort's identifier class.
 */
function checkReferent(profile: ProfileSpec, referent: Referent, where: string, worldKind: string | null): void {
  if (!Object.hasOwn(profile.sorts, referent.sort)) {
    throw new UndeclaredSort(`${where}: no sort ${referent.sort} in this profile.`);
  }
  const sort = profile.sorts[referent.sort];
  if (worldKind !== null && !(sort.binding.kind === "world-kind" && sort.binding.worldKind === worldKind)) {
    throw new WithinModelRefused(
      `${where}: sort ${referent.sort} is bound by ${sort.binding.kind}; the role takes records of world kind ` +
        `${worldKind}, so its sort must bind by \`world-kind\` to ${worldKind}.`,
    );
  }
  if (!inClass(sort, referent.term)) {
    throw new IdentifierClassMismatch(
      `${where}: ${JSON.stringify(referent.term)} is outside the identifier class of ${referent.sort} ` +
        `(${classText(sort)}), after NFC normalization.`,
    );
  }
}

function inClass(sort: CompiledSort, term: string): boolean {
  if (sort.identifierClass !== null) return sort.identifierClass.matches(term);
  const binding = sort.binding;
  if (binding.kind !== "world-kind") {
    throw new ProfileError(`sort ${sort.term} declares no identifier class and is not bound to a world kind`);
  }
  // A sort bound to a world kind has the kernel's record-id grammar as its class.
  const match = RECORD_ID.exec(term.normalize("NFC"));
  return match !== null && match[1] === binding.worldKind;
}

function classText(sort: CompiledSort): string {
  if (sort.identifierClass !== null) return `pattern ${JSON.stringify(sort.identifierClass.pattern)}`;
  const binding = sort.binding;
  return binding.kind === "world-kind"
    ? `\`${binding.worldKind}:\` followed by 64 lowercase hex characters`
    : "no identifier class";
}

function referentsOf(value: RoleFilling): readonly Referent[] {
  return Referent.is(value) ? [value] : value.map((member) => member.referent);
}

function routeSorts(
  assignment: ReadonlyMap<string, ReadonlySet<string>> | Readonly<Record<string, readonly string[]>>,
): string {
  const entries: [string, readonly string[]][] =
    assignment instanceof Map
      ? [...assignment].map(([role, sorts]) => [role, [...sorts]])
      : Object.entries(assignment as Readonly<Record<string, readonly string[]>>);
  const shown: Record<string, string[]> = {};
  for (const [role, sorts] of entries.sort(([a], [b]) => compareByCodePoint(a, b))) {
    shown[role] = [...sorts].sort(compareByCodePoint);
  }
  return JSON.stringify(shown);
}
