/**
 * The shared-encoding path, and nothing else (D §9).
 *
 * `science.identity.v1` and `π_claim` are the only surfaces two implementations
 * must agree on — formal model limitation 9 records M10 as the one
 * cross-implementation row. Contract reading, profile resolution and the
 * validated constructor are here because a projection is of a *typed* claim, not
 * because `ts/` is a second system.
 */

export { buildClaim, Claim, type ClaimParts, Qualifier, Referent } from "./claim.js";
export {
  type BaseContract,
  type ClaimGrammar,
  type FacetDecl,
  type FacetUse,
  type FieldDecl,
  type FieldType,
  type KindDecl,
  type RelationDecl,
  type DomainContract,
  parseBaseContract,
  parseDomainContract,
} from "./contract.js";
export * from "./errors.js";
export { checkDomain, compareByCodePoint, Decimal, digest, encode, type IdentityValue } from "./identity/v1.js";
export { type CompiledOperator, compileProfile, ProfileSpec, resolveOperator } from "./profile.js";
export { CLAIM_DOMAIN, type ClaimProjection, claimIdentity, projectClaim } from "./projection.js";
