/**
 * The shared-encoding path, and nothing else.
 *
 * `science.identity.v1` and `π_claim` are the only surfaces two implementations
 * must agree on — the parity fixture is the one
 * cross-implementation row. Contract reading, profile resolution and the
 * validated constructor are here because a projection is of a *typed* claim, not
 * because `ts/` is a second system.
 */

export {
  buildClaim,
  Claim,
  type ClaimParts,
  canonicalMembers,
  Member,
  memberKey,
  Qualifier,
  Referent,
} from "./claim.js";
export {
  type BaseContract,
  type BridgeDecl,
  type ClaimGrammar,
  type DimensionDecl,
  type DomainContract,
  type DurationConventionDecl,
  type EstimandDecl,
  type FacetDecl,
  type FacetUse,
  type FieldDecl,
  type FieldType,
  type InstantiationDecl,
  type KindDecl,
  type RelationDecl,
  type RoleDecl,
  type SortBinding,
  type SortDecl,
  type TemplateDecl,
  parseBaseContract,
  parseDomainContract,
} from "./contract.js";
export * from "./errors.js";
export { checkDomain, compareByCodePoint, Decimal, digest, encode, type IdentityValue } from "./identity/v1.js";
export { IdentifierClass, checkPortablePattern, compilePortable } from "./patterns.js";
export {
  admitting,
  type CompiledBridge,
  type CompiledDimension,
  type CompiledDurationConvention,
  type CompiledEstimandDecl,
  type CompiledInstantiation,
  type CompiledOperator,
  type CompiledRole,
  type CompiledSort,
  type CompiledTemplate,
  claimDimensions,
  compileProfile,
  declarationAt,
  estimandDeclarations,
  ProfileSpec,
  resolveOperator,
  templateOf,
} from "./profile.js";
export { CLAIM_DOMAIN, type ClaimProjection, claimIdentity, projectClaim } from "./projection.js";
