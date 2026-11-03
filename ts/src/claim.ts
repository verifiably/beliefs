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
 *   run time, so the qualifiers are held in a frozen null-prototype record and
 *   the arguments in a frozen array.
 *
 * None of it reaches further than the profile it is handed, and the profile
 * reaches no further than the contracts it was compiled from — see `profile.ts`
 * and `contract.ts` for the rest of the chain.
 */

import {
  ArgumentSortMismatch,
  ArityMismatch,
  ClaimError,
  InadmissibleLayer,
  MalformedReferent,
  PolarityRefused,
  ProfileError,
  RestrictionSortMismatch,
  SubclassRefused,
  UndeclaredDimension,
  UnknownQuantifier,
  UntypedQualifier,
  UntypedReferent,
} from "./errors.js";
import { ProfileSpec, resolveOperator } from "./profile.js";

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

export interface ClaimParts {
  readonly operator: string;
  readonly args: readonly Referent[];
  readonly qualifiers: ReadonlyMap<string, Qualifier>;
  /** `null` when the operator has no sign to assert — `Polarity(op)` is then the unit type. */
  readonly polarity: string | null;
  readonly layer: string;
}

/** Dimension term identifier → qualifier. Frozen, with a null prototype so no inherited key can appear. */
export type QualifierRecord = Readonly<Record<string, Qualifier>>;

export class Claim {
  #minted = true;
  readonly operator: string;
  readonly args: readonly Referent[];
  readonly qualifiers: QualifierRecord;
  /** Always a tag, and the base contract's `sign_inapt_tag` where the operator has no sign. */
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
    this.args = Object.freeze([...parts.args]);
    // A `ReadonlyMap` is a compile-time fiction: the value is an ordinary `Map`,
    // and `Object.freeze` does not reach its entries — so a caller holding the
    // claim could delete a qualifier and move the claim's own identity. A frozen
    // record cannot be added to, deleted from, or reassigned at run time.
    const qualifiers: Record<string, Qualifier> = Object.create(null);
    for (const [dimension, qualifier] of parts.qualifiers) qualifiers[dimension] = qualifier;
    this.qualifiers = Object.freeze(qualifiers);
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

/**
 * The validated constructor. Every check here is profile-dependent, and each one
 * refuses distinctly — decode checks each ill-formed input in turn.
 *
 * The **profile is checked first, and by brand**. `ProfileSpec` was structurally
 * typed, so a hand-authored object could stand in for one — and a claim typed
 * against a forged profile is typed against nothing, with every operator, layer
 * and sort in it invented by whoever wrote the object. The contracts are the
 * normative SSOT; a profile that did not come from them is not a profile.
 *
 * Retirement is not among the checks: retirement lives in authoring, and this
 * implementation refuses a contract carrying a retired declaration outright
 * rather than half-enforcing an authoring boundary it does not own.
 */
export function buildClaim(profile: ProfileSpec, parts: ClaimParts): Claim {
  if (!ProfileSpec.is(profile)) {
    throw new ProfileError(
      "the profile was not compiled from contracts — use compileProfile(base, domains). A structurally " +
        "similar object would type a claim against declarations nobody authored.",
    );
  }
  const declaration = resolveOperator(profile, parts.operator);

  if (parts.args.length !== declaration.arity) {
    throw new ArityMismatch(
      `${parts.operator} has arity ${declaration.arity}; ${parts.args.length} argument(s) supplied. Every slot of Fin(arity(op)) is filled, and no slot is filled twice.`,
    );
  }
  parts.args.forEach((referent, index) => {
    if (!Referent.is(referent)) {
      throw new UntypedReferent(
        `slot ${index} of ${parts.operator} does not hold a Referent. A slot is typed Referent(s), and a bare term carries no sort to check against the one declared.`,
      );
    }
    if (referent.sort !== declaration.argSorts[index]) {
      throw new ArgumentSortMismatch(
        `slot ${index} of ${parts.operator} is declared ${declaration.argSorts[index]}; ${referent.term} is of sort ${referent.sort}. Inside the model these are different types, so this is not a rejected value but a term with no slot to occupy.`,
      );
    }
  });

  const permitted = new Set(declaration.dimensions);
  for (const [dimension, qualifier] of parts.qualifiers) {
    if (!Qualifier.is(qualifier)) {
      throw new UntypedQualifier(
        `the qualifier on ${dimension} is not a Qualifier. Structural typing is not enough: any object exposing \`quantifier\` and \`restriction\` would otherwise be stored inside a Claim and trusted as one.`,
      );
    }
    if (!permitted.has(dimension)) {
      throw new UndeclaredDimension(
        `${parts.operator} does not permit dimension ${dimension}; Dims(op) is declared per operator.`,
      );
    }
    if (!profile.claimGrammar.quantifiers.includes(qualifier.quantifier)) {
      throw new UnknownQuantifier(
        `quantifier ${qualifier.quantifier} on ${dimension} is outside the kernel's closed set.`,
      );
    }
    const restrictionSort = profile.dimensions[dimension]?.restrictionSort;
    if (qualifier.restriction.sort !== restrictionSort) {
      throw new RestrictionSortMismatch(
        `${dimension} restricts to sort ${restrictionSort}; ${qualifier.restriction.term} is of sort ` +
          `${qualifier.restriction.sort}.`,
      );
    }
  }

  const grammar = profile.claimGrammar;
  let tag: string;
  if (declaration.signApt) {
    if (parts.polarity === null) {
      throw new PolarityRefused(
        `${parts.operator} is sign-apt, so a polarity must be asserted. ${grammar.signInaptTag} is not among them: it says the operator has no sign to assert, which is a different fact from asserting none.`,
      );
    }
    if (!grammar.polarities.includes(parts.polarity)) {
      throw new PolarityRefused(`polarity ${parts.polarity} is outside the base contract's closed set.`);
    }
    tag = parts.polarity;
  } else {
    if (parts.polarity !== null) {
      throw new PolarityRefused(
        `${parts.operator} is sign-inapt: Polarity(op) is the unit type, so there is no polarity to supply — not even ${grammar.signInaptTag}, which the projection carries on the claim's behalf and an author never chooses.`,
      );
    }
    tag = grammar.signInaptTag;
  }

  if (!declaration.layers.includes(parts.layer)) {
    throw new InadmissibleLayer(`${parts.operator} does not admit layer ${parts.layer}.`);
  }

  return new Claim(MINT, { ...parts, polarity: tag });
}
