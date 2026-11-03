/**
 * `π_claim` and `I_claim`, TypeScript half.
 *
 * The three load-bearing choices are the Python side's, and they are load-bearing
 * here for the same reasons — restated rather than cross-referenced, because a
 * reader of this file is checking it against the design, not against the other
 * implementation:
 *
 * * **arguments emit `term`, never `sort`** — the projection admits the referent
 *   identifier, and a sort is contract-declared, so carrying it would let a
 *   re-declaration re-project stored claims;
 * * **slots stay ordered, dimensions are not ordered here** — `science.identity.v1`
 *   sorts object keys at encode time, and sorting them again would be a second,
 *   silent canonicalization that could drift from the encoder's;
 * * **the polarity position is always present**, read from the claim's own tag,
 *   so no contract field decides the shape.
 *
 * And the signature: `projectClaim` takes a `Claim` and nothing else. A
 * `ProfileSpec` parameter would make it possible to fold a contract release into
 * `π_claim`, which is the named failure.
 */

import { Claim } from "./claim.js";
import { ClaimError } from "./errors.js";
import { digest } from "./identity/v1.js";

/**
 * The `tag_claim` version is the **projection's**: it moves when
 * π_claim's shape moves and nothing else moves it, so a grammar or corpus bump
 * cannot fork claims already written.
 */
export const CLAIM_DOMAIN = "science.claim.v1";

export interface ClaimProjection {
  readonly operator: string;
  readonly args: string[];
  readonly qualifiers: Record<string, { quantifier: string; restriction: string }>;
  readonly polarity: string;
  readonly layer: string;
}

export function projectClaim(claim: Claim): ClaimProjection {
  if (!Claim.is(claim)) {
    // The brand, not `instanceof`: an object given `Claim.prototype` satisfies
    // the latter without a constructor ever having run on it, and would arrive
    // here holding whatever its author put in it.
    throw new ClaimError("projectClaim takes a Claim built by buildClaim; this value never went through it");
  }
  const qualifiers: Record<string, { quantifier: string; restriction: string }> = {};
  for (const [dimension, qualifier] of Object.entries(claim.qualifiers)) {
    qualifiers[dimension] = { quantifier: qualifier.quantifier, restriction: qualifier.restriction.term };
  }
  return {
    operator: claim.operator,
    args: claim.args.map((referent) => referent.term),
    qualifiers,
    polarity: claim.polarity,
    layer: claim.layer,
  };
}

/** `I_claim` — the identity a claim keeps across every ontology release. */
export function claimIdentity(claim: Claim): string {
  return digest(CLAIM_DOMAIN, projectClaim(claim));
}
