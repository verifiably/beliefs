/**
 * The error hierarchy, mirroring the Python side's shape for the surface this
 * implementation carries.
 *
 * One class has no Python counterpart and is the more important one:
 * `UncheckableContract`. `ts/` implements the **shared-encoding path** and not a
 * second system, so there are contract
 * features it cannot validate — succession, and retirement's authoring
 * semantics. It **refuses** those inputs rather than parsing past them. A
 * reduced parser that quietly accepted what the other implementation refuses
 * would be a second, weaker reading of the normative source, which is exactly
 * the divergence a parity obligation exists to prevent.
 */

export class ScienceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

export class IdentityError extends ScienceError {}

/** A value of a type the contract does not admit. */
export class UnsupportedValueType extends IdentityError {}

/** Null or undefined. Refused, never pruned: an absent member must differ from a present-and-empty one. */
export class NullRefused extends IdentityError {}

/**
 * A JavaScript `number`. Always refused, integers included.
 *
 * This is the Python side's `float` refusal wearing the other language's
 * spelling: `number` is an IEEE binary double, and `1` and `1.0` are the same
 * value, so the type would not survive the encoding. Integers arrive as
 * `bigint`, decimals as `Decimal`, and the caller owns the rounding.
 */
export class BinaryFloatRefused extends IdentityError {}

/** A decimal that is not finite, or whose text is not a decimal at all. */
export class MalformedDecimal extends IdentityError {}

/** An object key that is not a string. */
export class NonStringKey extends IdentityError {}

/** Two keys distinct before NFC normalization and identical after it. Refused, never merged. */
export class KeyCollision extends IdentityError {}

/** A string carrying an unpaired UTF-16 surrogate: no UTF-8 encoding, and no agreement about what it is. */
export class LoneSurrogate extends IdentityError {}

/** A digest domain that is not a well-formed, versioned domain name. */
export class MalformedDomain extends IdentityError {}

/**
 * A subclass of a type that must stay closed.
 *
 * The Python side's `sealed` in this language's spelling — and here it closes
 * only half the hole. A subclass cannot be *constructed* through `super`, but it
 * can still be *declared*, and `Object.create(Subclass.prototype)` never calls a
 * constructor at all. The private-field brand on each type is what closes the
 * other half.
 */
export class SubclassRefused extends ScienceError {}

export class ContractError extends ScienceError {}

/** A contract that is structurally wrong — an unknown field, a missing one, a value of the wrong shape. */
export class MalformedContract extends ContractError {}

/**
 * A contract object that no parser produced.
 *
 * The root of the trust chain. `ProfileSpec`'s brand says a profile came from
 * `compileProfile`; this one says what `compileProfile` was given came from the
 * authored documents. Without it the profile brand proves only that a function
 * ran, and a claim typed against a hand-authored contract is typed against
 * nothing — every operator, sort, layer and dimension in it invented by whoever
 * wrote the object, with the normative SSOT never opened.
 */
export class UnparsedContract extends ContractError {}

/**
 * A contract using a feature this implementation cannot check.
 *
 * Refused rather than ignored. `ts/` carries the shared encoding; succession
 * validation and retirement's authoring boundary are Python's, and a document
 * that depends on either is not one this side may claim to have read.
 */
export class UncheckableContract extends ContractError {}

/**
 * Two contracts, each genuine, that were not typed against one another.
 *
 * Distinct from `UnparsedContract` and worth its own name: nothing was forged,
 * no brand was bypassed, every parser did its job. A domain's layer selections
 * are checked once, at parse, against the base contract it was handed, and the
 * compiled operator then carries them as facts — so compiling it against a
 * *different* base yields a claim on a layer that base does not declare.
 *
 * The general shape, worth remembering because provenance checks do not catch
 * it: authenticating each input separately says nothing about whether they
 * **belong together**. The rule is narrower than *"every stage records its
 * inputs"*, and both halves of it matter. It applies to an artifact whose
 * **validity is conditional** on a particular upstream artifact — some check it
 * passed was taken against that one and is never retaken — and which **may later
 * be recombined independently**, so it can arrive somewhere holding a different
 * partner. Such a boundary must **either verify a recorded dependency or
 * revalidate the relation**; a stage that rechecks what it depends on, or whose
 * output never travels apart from its input, owes neither.
 */
export class ContractMismatch extends ContractError {}

export class ProfileError extends ScienceError {}

export class ClaimError extends ScienceError {}
export class UntypedReferent extends ClaimError {}
export class MalformedReferent extends ClaimError {}
export class DuplicateMember extends ClaimError {}
export class CoefficientRefused extends ClaimError {}
export class UntypedQualifier extends ClaimError {}
export class ArityMismatch extends ClaimError {}
export class ArgumentSortMismatch extends ClaimError {}
export class UndeclaredDimension extends ClaimError {}
export class RestrictionSortMismatch extends ClaimError {}
export class UnknownQuantifier extends ClaimError {}
export class PolarityRefused extends ClaimError {}
export class InadmissibleLayer extends ClaimError {}
