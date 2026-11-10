/**
 * `π_claim` and `I_claim`, TypeScript half.
 *
 * The load-bearing choices are the Python side's, and they are load-bearing here
 * for the same reasons — restated rather than cross-referenced, because a reader
 * of this file is checking it against the contract, not against the other
 * implementation:
 *
 * * **every referent emits `sort` and `term`** — under templates the operator and
 *   the terms no longer fix the sorts, so one term over two sorts would otherwise
 *   collide. The sort enters as its *identifier*; its binding is the contract's
 *   and never enters, so re-declaring a binding re-projects nothing;
 * * **roles are a map by name, never a sequence** — a `one` role projects as a
 *   referent object, a `many` role as its members in canonical member-key order
 *   (the claim already holds them so), each carrying `coefficient` even when it
 *   is 1, and an empty role as `[]`;
 * * **neither roles nor dimensions are ordered here** — `science.identity.v1`
 *   sorts object keys at encode time, and sorting them again would be a second,
 *   silent canonicalization that could drift from the encoder's;
 * * **the form and polarity positions are always present**, read from the
 *   claim's own values, so no contract field decides the shape.
 *
 * And the signature: `projectClaim` takes a `Claim` and nothing else. A
 * `ProfileSpec` parameter would make it possible to fold a contract release into
 * `π_claim`, which is the named failure.
 */

import { Claim, type Member, Referent, type RoleFilling } from "./claim.js";
import { ClaimError } from "./errors.js";
import { digest } from "./identity/v1.js";

/**
 * The `tag_claim` version is the **projection's**: it moves when π_claim's
 * shape moves and nothing else moves it. v2 replaced positional `args` (terms
 * only) with roles by name, every referent carrying its sort, and added the form
 * position.
 */
export const CLAIM_DOMAIN = "science.claim.v2";

export interface ProjectedReferent {
  readonly sort: string;
  readonly term: string;
}

/** A `many` role's member. `coefficient` is a `bigint` so it encodes as an integer. */
export interface ProjectedMember extends ProjectedReferent {
  readonly coefficient: bigint;
}

export interface ClaimProjection {
  readonly operator: string;
  readonly roles: Record<string, ProjectedReferent | ProjectedMember[]>;
  readonly qualifiers: Record<string, { quantifier: string; restriction: ProjectedReferent }>;
  readonly form: string;
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
  const roles: Record<string, ProjectedReferent | ProjectedMember[]> = {};
  for (const [name, value] of Object.entries(claim.roles)) roles[name] = projectRole(value);
  const qualifiers: Record<string, { quantifier: string; restriction: ProjectedReferent }> = {};
  for (const [dimension, qualifier] of Object.entries(claim.qualifiers)) {
    qualifiers[dimension] = { quantifier: qualifier.quantifier, restriction: projectReferent(qualifier.restriction) };
  }
  return {
    operator: claim.operator,
    roles,
    qualifiers,
    form: claim.form,
    polarity: claim.polarity,
    layer: claim.layer,
  };
}

/** `I_claim` — the identity a claim keeps across every ontology release. */
export function claimIdentity(claim: Claim): string {
  return digest(CLAIM_DOMAIN, projectClaim(claim));
}

function projectReferent(referent: Referent): ProjectedReferent {
  return { sort: referent.sort, term: referent.term };
}

function projectMember(member: Member): ProjectedMember {
  return { ...projectReferent(member.referent), coefficient: member.coefficient };
}

function projectRole(value: RoleFilling): ProjectedReferent | ProjectedMember[] {
  return Referent.is(value) ? projectReferent(value) : value.map(projectMember);
}
