/**
 * The compiled runtime profile, in the reduced form the shared-encoding path
 * needs: **resolution**, and the declarations a claim is typed against.
 *
 * `ProfileSpec` resolves; contracts authorize. This side does the
 * resolving — local names become term identifiers, because a claim's projection
 * carries term identifiers and a local name is not one — and nothing else. In
 * particular there is **no `compiled_identity` here**: claim-schema
 * compilation as Python-only, on the ground that compilation is not a shared
 * encoding and no parity obligation reaches it. Computing one here would be a
 * second implementation of something no row requires, and two implementations of
 * an identity nobody compares is how the identity drifts.
 *
 * **It is a branded class, not an interface.** A structurally typed profile can
 * be hand-authored, and a claim typed against a hand-authored profile is typed
 * against nothing: every operator, sort, layer and dimension in it was invented
 * by whoever wrote the object, and the contracts — the normative SSOT — were
 * never opened. The private field below is installed only by `compileProfile`,
 * so "this came from the contracts" is a runtime fact rather than a shape.
 *
 * A brand is only ever as good as what the minting function checks, and this one
 * was once worth nothing: `compileProfile` accepted structurally typed contracts,
 * so the brand certified that a function had run rather than that the documents
 * had been read. The contracts carry brands of their own (`contract.ts`), and
 * they are checked here. **Trust does not begin at a compiled artifact — it
 * begins at the authored document, and every link between has to hold.**
 *
 * Everything below is also **genuinely immutable**, which `readonly` is not:
 * `readonly`, `ReadonlyMap` and `ReadonlySet` are erased at run time, and both a
 * `Map`'s entries and a `Set`'s members are beyond the reach of `Object.freeze`.
 * A profile that could be edited after minting would carry a brand attesting to
 * a compilation whose result no longer exists.
 */

import {
  BaseContract,
  type ClaimGrammar,
  type CompositeGrammar,
  type ConstantDecl,
  type ConversionDecl,
  type DeclarationTable,
  DomainContract,
  type EstimandGrammar,
  type FacetDecl,
  type KindDecl,
  type QuantityDimension,
  type QuantityKindDecl,
  type RelationDecl,
  type RestrictionForm,
  type SortBinding,
  type TransformationDecl,
  type UnitDecl,
} from "./contract.js";
import { ContractMismatch, MalformedContract, ProfileError, SubclassRefused, UnparsedContract } from "./errors.js";
import type { IdentifierClass } from "./patterns.js";

export interface CompiledSort {
  readonly term: string;
  readonly binding: SortBinding;
  readonly identifierClass: IdentifierClass | null;
  /** Sorted: a set held as an array, since a `Set` cannot be frozen. */
  readonly categories: readonly string[];
}

export type CompiledRestrictionForm = RestrictionForm;
export interface CompiledProcedureKind {
  readonly term: string;
  readonly fillsWithinModel: boolean;
  readonly contract: string;
}
export interface CompiledAggregationRule {
  readonly term: string;
  readonly contract: string;
}
export interface CompiledAssumptionKind {
  readonly term: string;
  readonly collapses: string;
  readonly particulars: readonly string[];
  readonly contract: string;
}
export interface CompiledMeasurements {
  readonly sort: string;
  readonly quantityKinds: readonly string[];
  readonly contract: string;
}
export interface CompiledAspects {
  readonly quantityKind: string;
  readonly aspectSorts: readonly string[];
  readonly contract: string;
}

export interface CompiledDimension {
  readonly term: string;
  readonly restrictionSort: string;
  readonly restriction: CompiledRestrictionForm | null;
  readonly placement: string;
  /** The operator terms (templates and bridges) a claim over which may carry this dimension, sorted. */
  readonly appliesTo: readonly string[];
}

export interface CompiledRole {
  readonly name: string;
  readonly arity: "one" | "many";
  readonly min: number;
  readonly max: number | null;
  readonly coefficients: boolean;
  /** Sorted role categories a filling sort must declare. */
  readonly constraint: readonly string[];
}

/** A template, under its operator term `<namespace>/<name>`. Its external reference activates nothing and is not compiled. */
export interface CompiledTemplate {
  readonly kind: "template";
  readonly term: string;
  readonly roles: ResolutionTable<CompiledRole>;
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly forms: readonly string[];
  readonly edge: { readonly cause: string; readonly effect: string } | null;
}

/** An instantiation with its template and every listed sort resolved to term identifiers (each role's sorted). */
export interface CompiledInstantiation {
  readonly term: string;
  readonly template: string;
  readonly roles: Readonly<Record<string, readonly string[]>>;
}

/**
 * A bridging relation, an operator of its own. Its roles are its template's, and
 * `layers` is the effective set: the declared narrowing, or the template's layers
 * when it declares none.
 */
export interface CompiledBridge {
  readonly kind: "bridge";
  readonly term: string;
  readonly template: string;
  readonly mapping: string;
  readonly roles: Readonly<Record<string, readonly string[]>>;
  readonly layers: readonly string[];
}

/** An operator a claim names: a template or a bridge, both `<namespace>/<name>`. */
export type CompiledOperator = CompiledTemplate | CompiledBridge;

/**
 * An `estimands:` entry with every sort resolved to a term identifier, under the
 * compiled typed address of its target (`instantiation:<namespace>/<name>` or
 * `bridge:<namespace>/<name>`). `levelSorts` is keyed by role name.
 */
export interface CompiledEstimandDecl {
  readonly target: string;
  readonly levelSorts: Readonly<Record<string, string>>;
  readonly measureSort: string;
  readonly identificationSort: string;
  readonly conditioningSort: string;
}

export interface CompiledDurationConvention {
  readonly term: string;
  readonly conversion: string;
  readonly contract: string;
}

export type CompiledQuantityKind = Omit<QuantityKindDecl, "name"> & {
  readonly term: string;
  readonly contract: string;
};
export type CompiledUnit = Omit<UnitDecl, "name"> & { readonly term: string; readonly contract: string };
export type CompiledConstant = Omit<ConstantDecl, "name"> & { readonly term: string; readonly contract: string };
export type CompiledConversion = Omit<ConversionDecl, "name"> & {
  readonly term: string;
  readonly contract: string;
  readonly constantRole: "multiply" | "divide" | null;
};
export type CompiledTransformation = Omit<TransformationDecl, "name"> & {
  readonly term: string;
  readonly contract: string;
};

/** The placement of a dimension a claim's qualifiers may carry; `applicability` is the estimand grammar's. */
const CLAIM_PLACEMENT = "claim";

const MINT = Symbol("science.profile.mint");

/** Term identifier → compiled declaration. A frozen null-prototype record, for the reason `DeclarationTable` gives in `contract.ts`. */
export type ResolutionTable<T> = Readonly<Record<string, T>>;

export class ProfileSpec {
  #minted = true;
  readonly kinds: DeclarationTable<KindDecl>;
  readonly facets: DeclarationTable<FacetDecl>;
  readonly relations: DeclarationTable<RelationDecl>;
  readonly claimGrammar: ClaimGrammar;
  readonly estimandGrammar: EstimandGrammar;
  readonly compositeGrammar: CompositeGrammar;
  readonly sorts: ResolutionTable<CompiledSort>;
  readonly dimensions: ResolutionTable<CompiledDimension>;
  readonly templates: ResolutionTable<CompiledTemplate>;
  readonly instantiations: ResolutionTable<CompiledInstantiation>;
  readonly bridges: ResolutionTable<CompiledBridge>;
  /** Keyed by the compiled typed address of each declaration's target. */
  readonly estimands: ResolutionTable<CompiledEstimandDecl>;
  readonly durationConventions: ResolutionTable<CompiledDurationConvention>;
  readonly procedureKinds: ResolutionTable<CompiledProcedureKind>;
  readonly aggregationRules: ResolutionTable<CompiledAggregationRule>;
  readonly assumptionKinds: ResolutionTable<CompiledAssumptionKind>;
  readonly measurements: ResolutionTable<readonly string[]>;
  readonly measurementDeclarations: readonly CompiledMeasurements[];
  readonly aspectDeclarations: readonly CompiledAspects[];
  readonly quantityKinds: ResolutionTable<CompiledQuantityKind>;
  readonly units: ResolutionTable<CompiledUnit>;
  readonly constants: ResolutionTable<CompiledConstant>;
  readonly conversions: ResolutionTable<CompiledConversion>;
  readonly transformations: ResolutionTable<CompiledTransformation>;
  /**
   * The admission index: template term → the typed addresses
   * `instantiation:<namespace>/<name>` of every instantiation of it across the
   * activated contracts, sorted. Built from the contract set alone, so no answer
   * read from it depends on activation order.
   */
  readonly admission: ResolutionTable<readonly string[]>;

  constructor(
    token: symbol,
    parts: {
      kinds: DeclarationTable<KindDecl>;
      facets: DeclarationTable<FacetDecl>;
      relations: DeclarationTable<RelationDecl>;
      claimGrammar: ClaimGrammar;
      estimandGrammar: EstimandGrammar;
      compositeGrammar: CompositeGrammar;
      sorts: ResolutionTable<CompiledSort>;
      dimensions: ResolutionTable<CompiledDimension>;
      templates: ResolutionTable<CompiledTemplate>;
      instantiations: ResolutionTable<CompiledInstantiation>;
      bridges: ResolutionTable<CompiledBridge>;
      estimands: ResolutionTable<CompiledEstimandDecl>;
      durationConventions: ResolutionTable<CompiledDurationConvention>;
      procedureKinds: ResolutionTable<CompiledProcedureKind>;
      aggregationRules: ResolutionTable<CompiledAggregationRule>;
      assumptionKinds: ResolutionTable<CompiledAssumptionKind>;
      measurements: ResolutionTable<readonly string[]>;
      measurementDeclarations: readonly CompiledMeasurements[];
      aspectDeclarations: readonly CompiledAspects[];
      quantityKinds: ResolutionTable<CompiledQuantityKind>;
      units: ResolutionTable<CompiledUnit>;
      constants: ResolutionTable<CompiledConstant>;
      conversions: ResolutionTable<CompiledConversion>;
      transformations: ResolutionTable<CompiledTransformation>;
      admission: ResolutionTable<readonly string[]>;
    },
  ) {
    if (new.target !== ProfileSpec) {
      throw new SubclassRefused("ProfileSpec is sealed: a subclass could stand in for a compiled profile");
    }
    if (token !== MINT) {
      throw new ProfileError(
        "ProfileSpec is compiled, never authored — use compileProfile(base, domains). The contracts retired the " +
          "second per-kind source of truth; an authored profile would reintroduce it through the constructor.",
      );
    }
    // Snapshotted, not adopted, and this is the **only** place the tables are
    // frozen. `compileProfile` hands over ordinary mutable ones: putting the
    // freeze there as well would leave two places responsible for an invariant
    // this class is the one promising, and the copy here would then be
    // unreachable — defending against a caller the mint token makes impossible,
    // and untestable for the same reason. The entries themselves are frozen
    // where they are made.
    this.kinds = frozenTable(Object.entries(parts.kinds));
    this.facets = frozenTable(Object.entries(parts.facets));
    this.relations = frozenTable(Object.entries(parts.relations));
    this.claimGrammar = parts.claimGrammar;
    this.estimandGrammar = parts.estimandGrammar;
    this.compositeGrammar = parts.compositeGrammar;
    this.sorts = frozenTable(Object.entries(parts.sorts));
    this.dimensions = frozenTable(Object.entries(parts.dimensions));
    this.templates = frozenTable(Object.entries(parts.templates));
    this.instantiations = frozenTable(Object.entries(parts.instantiations));
    this.bridges = frozenTable(Object.entries(parts.bridges));
    this.estimands = frozenTable(Object.entries(parts.estimands));
    this.durationConventions = frozenTable(Object.entries(parts.durationConventions));
    this.procedureKinds = frozenTable(Object.entries(parts.procedureKinds));
    this.aggregationRules = frozenTable(Object.entries(parts.aggregationRules));
    this.assumptionKinds = frozenTable(Object.entries(parts.assumptionKinds));
    this.measurements = frozenTable(Object.entries(parts.measurements));
    this.measurementDeclarations = Object.freeze([...parts.measurementDeclarations]);
    this.aspectDeclarations = Object.freeze([...parts.aspectDeclarations]);
    this.quantityKinds = frozenTable(Object.entries(parts.quantityKinds));
    this.units = frozenTable(Object.entries(parts.units));
    this.constants = frozenTable(Object.entries(parts.constants));
    this.conversions = frozenTable(Object.entries(parts.conversions));
    this.transformations = frozenTable(Object.entries(parts.transformations));
    this.admission = frozenTable(Object.entries(parts.admission));
    Object.freeze(this);
  }

  admitsMeasurement(sort: string, quantityKind: string): boolean {
    return this.measurements[sort]?.includes(quantityKind) ?? false;
  }
  aspectSorts(quantityKind: string): readonly string[] {
    return sorted(
      new Set(
        this.aspectDeclarations.filter((row) => row.quantityKind === quantityKind).flatMap((row) => row.aspectSorts),
      ),
    );
  }
  /** The declared noncalendar route joining a unit pair, in either authored direction. */
  conversionBetween(aUnit: string, bUnit: string): CompiledConversion | null {
    return (
      Object.values(this.conversions).find(
        (conversion) =>
          !this.units[conversion.fromUnit].calendar &&
          !this.units[conversion.toUnit].calendar &&
          ((conversion.fromUnit === aUnit && conversion.toUnit === bUnit) ||
            (conversion.fromUnit === bUnit && conversion.toUnit === aUnit)),
      ) ?? null
    );
  }

  /** The brand check: did this profile come from `compileProfile`, or merely look like it had? */
  static is(value: unknown): value is ProfileSpec {
    return typeof value === "object" && value !== null && #minted in value;
  }
}

function frozenTable<T>(entries: readonly (readonly [string, T])[]): ResolutionTable<T> {
  const table: Record<string, T> = Object.create(null);
  for (const [key, value] of entries) table[key] = value;
  return Object.freeze(table);
}

function term(namespace: string, name: string): string {
  return `${namespace}/${name}`;
}

/** A local name namespaced into `contract`; a `<namespace>/<name>` reference as written. */
function localTerm(contract: DomainContract, reference: string): string {
  return reference.includes("/") ? reference : term(contract.namespace, reference);
}

function sorted(values: Iterable<string>): readonly string[] {
  return Object.freeze([...values].sort());
}

export function compileProfile(base: BaseContract, domains: readonly DomainContract[]): ProfileSpec {
  if (!BaseContract.is(base)) {
    throw new UnparsedContract(
      "the base contract was not parsed from its document — use parseBaseContract(text, source). A profile " +
        "compiled from an authored grammar would resolve claims against polarities and layers nobody declared.",
    );
  }
  const facets: Record<string, FacetDecl> = Object.assign(Object.create(null), base.facets);
  const seen = new Map<string, DomainContract>();

  for (const contract of domains) {
    if (!DomainContract.is(contract)) {
      throw new UnparsedContract(
        "a domain contract was not parsed from its document — use parseDomainContract(text, source, base). " +
          "Operators are domain-issued, and an authored contract issues them on no authority.",
      );
    }
    if (contract.base !== base) {
      // Provenance is not enough on its own: two contracts can each be entirely
      // genuine and still not belong together. This domain's layers were checked
      // at parse time against a different base, and nothing revalidates them
      // afterwards — so compiling it here would put a claim on a layer the base
      // in force does not declare, with nothing forged anywhere.
      throw new ContractMismatch(
        `domain contract ${JSON.stringify(contract.namespace)} was parsed against a different base contract than the one being compiled with. A domain selects its layers from the base vocabulary and may not extend it; that check ran against another document, so nothing here can stand behind it.`,
      );
    }
    if (seen.has(contract.namespace)) {
      // Contributions in different namespaces compose; two to one namespace are
      // refused at compile, never resolved last-writer-wins.
      throw new ProfileError(`two contracts contribute to namespace ${JSON.stringify(contract.namespace)}`);
    }
    seen.set(contract.namespace, contract);
    for (const [key, facet] of Object.entries(contract.facets)) {
      for (const kind of facet.attachesTo) {
        if (base.kinds[kind]?.role !== "world")
          throw new ProfileError(`${key}: attaches_to names ${kind}, not a world kind`);
      }
      facets[key] = facet;
    }
  }
  for (const [key, facet] of Object.entries(facets)) {
    for (const [name, field] of Object.entries(facet.fields)) {
      for (const kind of field.kinds) {
        if (!(kind in base.kinds))
          throw new ProfileError(`${key}: field ${name} names kind ${kind}, not in the compiled inventory`);
      }
    }
  }

  // Built in dependency order — sorts and templates first, from every contract,
  // since a declaration may name another contract's — and over the contracts in
  // namespace order, so nothing resolved later depends on activation order.
  const contracts = [...seen.keys()].sort().map((namespace) => seen.get(namespace) as DomainContract);

  // Mutable while they are being built, and frozen by the constructor — see
  // there for why the table freeze lives in one place rather than both.
  const sorts: Record<string, CompiledSort> = Object.create(null);
  const templates: Record<string, CompiledTemplate> = Object.create(null);
  const bridges: Record<string, CompiledBridge> = Object.create(null);
  const dimensions: Record<string, CompiledDimension> = Object.create(null);
  const instantiations: Record<string, CompiledInstantiation> = Object.create(null);
  const estimands: Record<string, CompiledEstimandDecl> = Object.create(null);
  const durationConventions: Record<string, CompiledDurationConvention> = Object.create(null);

  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.sorts)) {
      sorts[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        binding: decl.binding,
        identifierClass: decl.identifierClass,
        categories: sorted(decl.categories),
      });
    }
    for (const [name, decl] of Object.entries(contract.templates)) {
      const roles: [string, CompiledRole][] = Object.entries(decl.roles).map(([roleName, role]) => [
        roleName,
        Object.freeze({
          name: role.name,
          arity: role.arity,
          min: role.min,
          max: role.max,
          coefficients: role.coefficients,
          constraint: sorted(role.constraint),
        }),
      ]);
      templates[term(contract.namespace, name)] = Object.freeze({
        kind: "template",
        term: term(contract.namespace, name),
        roles: frozenTable(roles),
        signApt: decl.signApt,
        layers: decl.layers,
        forms: decl.forms,
        edge: decl.edge,
      });
    }
  }

  const quantityKinds: Record<string, CompiledQuantityKind> = Object.create(null);
  const units: Record<string, CompiledUnit> = Object.create(null);
  const constants: Record<string, CompiledConstant> = Object.create(null);
  const conversions: Record<string, CompiledConversion> = Object.create(null);
  const transformations: Record<string, CompiledTransformation> = Object.create(null);
  const resolveMeasurement = (
    contract: DomainContract,
    reference: string,
    table: ResolutionTable<unknown>,
    where: string,
  ): string => {
    const resolved = localTerm(contract, reference);
    if (!Object.hasOwn(table, resolved))
      throw new ProfileError(`${contract.namespace}: ${where} names ${resolved}, which no activated contract declares`);
    return resolved;
  };
  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.quantityKinds)) {
      quantityKinds[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        dimension: decl.dimension,
        contract: contract.namespace,
      });
    }
  }
  const procedureKinds: Record<string, CompiledProcedureKind> = Object.create(null);
  const aggregationRules: Record<string, CompiledAggregationRule> = Object.create(null);
  const assumptionKinds: Record<string, CompiledAssumptionKind> = Object.create(null);
  const measurementDeclarations: CompiledMeasurements[] = [];
  const aspectDeclarations: CompiledAspects[] = [];
  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.procedureKinds)) {
      const resolved = term(contract.namespace, name);
      procedureKinds[resolved] = Object.freeze({
        term: resolved,
        fillsWithinModel: decl.fillsWithinModel,
        contract: contract.namespace,
      });
    }
    for (const name of Object.keys(contract.aggregationRules)) {
      const resolved = term(contract.namespace, name);
      aggregationRules[resolved] = Object.freeze({ term: resolved, contract: contract.namespace });
    }
    for (const [name, decl] of Object.entries(contract.assumptionKinds)) {
      const resolved = term(contract.namespace, name);
      assumptionKinds[resolved] = Object.freeze({
        term: resolved,
        collapses: decl.collapses,
        particulars: decl.particulars,
        contract: contract.namespace,
      });
    }
    for (const decl of Object.values(contract.measurements))
      measurementDeclarations.push(
        Object.freeze({
          sort: resolveMeasurement(contract, decl.sort, sorts, "measurements sort"),
          quantityKinds: sorted(
            decl.quantityKinds.map((ref) =>
              resolveMeasurement(contract, ref, quantityKinds, "measurements quantity kind"),
            ),
          ),
          contract: contract.namespace,
        }),
      );
    for (const decl of Object.values(contract.aspects))
      aspectDeclarations.push(
        Object.freeze({
          quantityKind: resolveMeasurement(contract, decl.quantityKind, quantityKinds, "aspects quantity kind"),
          aspectSorts: sorted(decl.aspectSorts.map((ref) => resolveMeasurement(contract, ref, sorts, "aspects sort"))),
          contract: contract.namespace,
        }),
      );
  }
  const measurements: Record<string, readonly string[]> = Object.create(null);
  for (const row of measurementDeclarations)
    measurements[row.sort] = sorted(new Set([...(measurements[row.sort] ?? []), ...row.quantityKinds]));
  const compileRestriction = (contract: DomainContract, decl: RestrictionForm): CompiledRestrictionForm => {
    switch (decl.form) {
      case "term":
        return Object.freeze({
          form: "term",
          sort: resolveMeasurement(contract, decl.sort, sorts, "restriction sort"),
        });
      case "interval":
        return Object.freeze({
          form: "interval",
          quantityKind: resolveMeasurement(contract, decl.quantityKind, quantityKinds, "restriction quantity kind"),
        });
      case "rule":
        return Object.freeze({
          form: "rule",
          classes: resolveMeasurement(contract, decl.classes, sorts, "restriction classes"),
        });
      case "time-interval":
        return Object.freeze({ form: "time-interval" });
      case "union": {
        const of = compileRestriction(contract, decl.of);
        if (of.form === "union") throw new ProfileError("nested union restriction");
        return Object.freeze({ form: "union", of });
      }
    }
  };

  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.units)) {
      units[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        symbol: decl.symbol,
        quantityKind: resolveMeasurement(contract, decl.quantityKind, quantityKinds, `units.${name}: quantity_kind`),
        external: decl.external,
        calendar: decl.calendar,
        contract: contract.namespace,
      });
    }
  }
  for (const unit of Object.values(units)) {
    const dimension = quantityKinds[unit.quantityKind].dimension;
    if (unit.calendar && (typeof dimension === "string" || Object.keys(dimension).length !== 1 || dimension.T !== 1)) {
      throw new ProfileError(`${unit.term}: a calendar unit requires physical dimension exactly {T: 1}`);
    }
  }
  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.constants)) {
      constants[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        value: decl.value,
        unit: resolveMeasurement(contract, decl.unit, units, `constants.${name}: unit`),
        exact: decl.exact,
        contract: contract.namespace,
      });
    }
  }
  const pairs = new Set<string>();
  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.conversions)) {
      const where = `conversions.${name}`;
      const fromUnit = resolveMeasurement(contract, decl.fromUnit, units, `${where}: from`);
      const toUnit = resolveMeasurement(contract, decl.toUnit, units, `${where}: to`);
      const pair = JSON.stringify([fromUnit, toUnit].sort());
      if (pairs.has(pair)) throw new ProfileError(`${where}: two conversions join the same unit pair`);
      pairs.add(pair);
      const constant =
        decl.constant === null ? null : resolveMeasurement(contract, decl.constant, constants, `${where}: constant`);
      const fromKind = units[fromUnit].quantityKind;
      const toKind = units[toUnit].quantityKind;
      let role: "multiply" | "divide" | null = null;
      if (fromKind === toKind) {
        if (constant !== null) throw new ProfileError(`${where}: conversion within a kind refuses a constant`);
      } else {
        if (constant === null) throw new ProfileError(`${where}: conversion between quantity kinds needs a constant`);
        role = constantRole(
          quantityKinds[fromKind].dimension,
          quantityKinds[toKind].dimension,
          quantityKinds[units[constants[constant].unit].quantityKind].dimension,
          where,
        );
      }
      conversions[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        fromUnit,
        toUnit,
        kind: decl.kind,
        factor: decl.factor,
        offset: decl.offset,
        exact: decl.exact,
        error: decl.error,
        constant,
        constantRole: role,
        contract: contract.namespace,
      });
    }
    for (const [name, decl] of Object.entries(contract.transformations)) {
      const { name: _name, ...fields } = decl;
      transformations[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        ...fields,
        contract: contract.namespace,
      });
    }
  }

  const resolveSort = (contract: DomainContract, name: string, where: string): string => {
    const resolved = localTerm(contract, name);
    if (!Object.hasOwn(sorts, resolved)) {
      const namespace = resolved.split("/")[0];
      throw new MalformedContract(
        `${contract.namespace}: ${where} names sort ${JSON.stringify(resolved)}, but no compiled contract declares sort ${JSON.stringify(resolved)} (namespace ${JSON.stringify(namespace)}). A cross-contract sort resolves at compile or refuses; nothing here can stand behind an undeclared sort.`,
      );
    }
    return resolved;
  };

  const resolveTemplate = (contract: DomainContract, reference: string, where: string): CompiledTemplate => {
    const resolved = localTerm(contract, reference);
    if (!Object.hasOwn(templates, resolved)) {
      throw new ProfileError(
        `${contract.namespace}: ${where} names template ${JSON.stringify(resolved)}, which no activated contract declares. An instantiation or bridge of an undeclared template has no roles to fill, so it refuses at compile.`,
      );
    }
    return templates[resolved];
  };

  /**
   * Resolve the sorts listed per role, after checking the role names match the
   * template's exactly and every listed sort declares the categories the role's
   * constraint requires.
   */
  const compileRoleSorts = (
    contract: DomainContract,
    roles: Readonly<Record<string, readonly string[]>>,
    template: CompiledTemplate,
    where: string,
  ): Readonly<Record<string, readonly string[]>> => {
    const declared = Object.keys(template.roles).sort();
    const lacking = Object.keys(roles)
      .filter((role) => !Object.hasOwn(template.roles, role))
      .sort();
    if (lacking.length > 0) {
      throw new ProfileError(
        `${contract.namespace}: ${where} names role(s) ${lacking.join(", ")}, which ${JSON.stringify(template.term)} does not declare; its roles are ${JSON.stringify(declared)}`,
      );
    }
    const omitted = declared.filter((role) => !Object.hasOwn(roles, role));
    if (omitted.length > 0) {
      throw new ProfileError(
        `${contract.namespace}: ${where} omits role(s) ${omitted.join(", ")} of ${JSON.stringify(template.term)}; every role lists the sorts that may fill it`,
      );
    }
    const resolved: [string, readonly string[]][] = [];
    for (const [role, listed] of Object.entries(roles)) {
      const terms = sorted(new Set(listed.map((sort) => resolveSort(contract, sort, `${where}.${role}`))));
      const required = template.roles[role].constraint;
      for (const sortTerm of terms) {
        const missing = required.filter((category) => !sorts[sortTerm].categories.includes(category));
        if (missing.length > 0) {
          throw new ProfileError(
            `${contract.namespace}: ${where}.${role} lists ${JSON.stringify(sortTerm)}, which does not declare the role categor(ies) ${JSON.stringify(missing)} that ${JSON.stringify(template.term)}'s role ${JSON.stringify(role)} requires`,
          );
        }
      }
      resolved.push([role, terms]);
    }
    return frozenTable(resolved);
  };

  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.bridges)) {
      const where = `bridges.${name}`;
      const template = resolveTemplate(contract, decl.template, `${where}: template`);
      let layers = template.layers;
      if (decl.layers !== null) {
        const wider = decl.layers.filter((layer) => !template.layers.includes(layer));
        if (wider.length > 0) {
          throw new ProfileError(
            `${contract.namespace}: ${where}: layers ${JSON.stringify(wider)} are outside ${JSON.stringify(template.term)}'s layers ${JSON.stringify(template.layers)}. A bridge may narrow its template's layers, never widen them.`,
          );
        }
        layers = decl.layers;
      }
      bridges[term(contract.namespace, name)] = Object.freeze({
        kind: "bridge",
        term: term(contract.namespace, name),
        template: template.term,
        mapping: decl.mapping,
        roles: compileRoleSorts(contract, decl.roles, template, `${where}: roles`),
        layers,
      });
    }
  }

  for (const contract of contracts) {
    for (const [name, decl] of Object.entries(contract.dimensions)) {
      const where = `dimensions.${name}`;
      const restrictionSort = resolveSort(contract, decl.restrictionSort, `${where}: restriction_sort`);
      const appliesTo = decl.appliesTo.map((reference) => {
        // A local name resolves against this contract only, even when another
        // activated contract declares the same local name.
        const resolved = localTerm(contract, reference);
        if (!Object.hasOwn(templates, resolved) && !Object.hasOwn(bridges, resolved)) {
          throw new ProfileError(
            `${contract.namespace}: ${where}: applies_to names ${JSON.stringify(resolved)}, which is no operator (template or bridge) an activated contract declares`,
          );
        }
        return resolved;
      });
      dimensions[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        restrictionSort,
        restriction: decl.restriction ? compileRestriction(contract, decl.restriction) : null,
        placement: decl.placement,
        appliesTo: sorted(new Set(appliesTo)),
      });
    }
    for (const [name, decl] of Object.entries(contract.instantiations)) {
      const where = `instantiations.${name}`;
      const template = resolveTemplate(contract, decl.template, `${where}: template`);
      instantiations[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        template: template.term,
        roles: compileRoleSorts(contract, decl.roles, template, `${where}: roles`),
      });
    }
  }

  for (const contract of contracts) {
    for (const decl of Object.values(contract.estimands)) {
      const where = `estimands.${decl.target}`;
      const separator = decl.target.indexOf(":");
      const kind = decl.target.slice(0, separator);
      const targetTerm = term(contract.namespace, decl.target.slice(separator + 1));
      // The parser admits only a target this contract declares, so both lookups hold.
      const target = kind === "instantiation" ? instantiations[targetTerm] : bridges[targetTerm];
      const template = templates[target.template];
      const levelSorts: Record<string, string> = Object.create(null);
      for (const [role, sort] of Object.entries(decl.levelSorts)) {
        if (!Object.hasOwn(template.roles, role)) {
          throw new ProfileError(
            `${contract.namespace}: ${where}: level_sorts names role ${JSON.stringify(role)}, which ${JSON.stringify(template.term)} does not declare; its roles are ${JSON.stringify(Object.keys(template.roles).sort())}`,
          );
        }
        levelSorts[role] = resolveSort(contract, sort, `${where}: level_sorts.${role}`);
      }
      const address = `${kind}:${targetTerm}`;
      estimands[address] = Object.freeze({
        target: address,
        levelSorts: Object.freeze(levelSorts),
        measureSort: resolveSort(contract, decl.measureSort, `${where}: measure_sort`),
        identificationSort: resolveSort(contract, decl.identificationSort, `${where}: identification_sort`),
        conditioningSort: resolveSort(contract, decl.conditioningSort, `${where}: conditioning_sort`),
      });
    }
    for (const [name, decl] of Object.entries(contract.durationConventions)) {
      const conventionTerm = term(contract.namespace, name);
      const conversionTerm = resolveMeasurement(
        contract,
        decl.conversion,
        conversions,
        `duration_conventions.${name}: conversion`,
      );
      const conversion = conversions[conversionTerm];
      const source = units[conversion.fromUnit];
      const target = units[conversion.toUnit];
      if (
        conversion.kind !== "multiplicative" ||
        !conversion.exact ||
        conversion.error !== null ||
        conversion.constant !== null ||
        source.calendar === target.calendar ||
        source.quantityKind !== target.quantityKind
      ) {
        throw new ProfileError(
          `${conventionTerm}: a duration convention requires an exact multiplicative conversion joining one calendar and one noncalendar unit of the same quantity kind, without error or constant`,
        );
      }
      durationConventions[conventionTerm] = Object.freeze({
        term: conventionTerm,
        conversion: conversionTerm,
        contract: contract.namespace,
      });
    }
  }

  const admission: Record<string, readonly string[]> = Object.create(null);
  for (const templateTerm of Object.keys(templates)) {
    admission[templateTerm] = sorted(
      Object.values(instantiations)
        .filter((instantiation) => instantiation.template === templateTerm)
        .map((instantiation) => `instantiation:${instantiation.term}`),
    );
  }

  return new ProfileSpec(MINT, {
    kinds: base.kinds,
    relations: base.relations,
    facets,
    claimGrammar: base.claimGrammar,
    estimandGrammar: base.estimandGrammar,
    compositeGrammar: base.compositeGrammar,
    sorts,
    dimensions,
    templates,
    instantiations,
    bridges,
    estimands,
    durationConventions,
    procedureKinds,
    aggregationRules,
    assumptionKinds,
    measurements,
    measurementDeclarations,
    aspectDeclarations,
    quantityKinds,
    units,
    constants,
    conversions,
    transformations,
    admission,
  });
}

function constantRole(
  source: QuantityDimension,
  target: QuantityDimension,
  constant: QuantityDimension,
  where: string,
): "multiply" | "divide" {
  if (typeof source !== "string" && typeof target !== "string" && typeof constant !== "string") {
    const dimensions = new Set([...Object.keys(source), ...Object.keys(target), ...Object.keys(constant)]);
    if ([...dimensions].every((key) => (source[key] ?? 0) + (constant[key] ?? 0) === (target[key] ?? 0)))
      return "multiply";
    if ([...dimensions].every((key) => (source[key] ?? 0) - (constant[key] ?? 0) === (target[key] ?? 0)))
      return "divide";
  }
  throw new ProfileError(`${where}: dimensions do not reconcile through the declared constant`);
}

/**
 * Resolve an operator term identifier — a template or a bridge — or refuse.
 *
 * A claim naming an operator whose declaring contract is not in the
 * profile is a local, static failure, so it refuses here and nothing is minted.
 * Templates and bridges share one identity position, and a contract may not
 * declare both under one name, so at most one table holds `term`.
 */
export function resolveOperator(profile: ProfileSpec, term: string): CompiledOperator {
  if (Object.hasOwn(profile.templates, term)) return profile.templates[term];
  if (Object.hasOwn(profile.bridges, term)) return profile.bridges[term];
  throw new ProfileError(
    `no operator ${JSON.stringify(term)} in this profile. Operators (templates and bridges) are domain-issued; ` +
      `this profile resolves ${JSON.stringify([...Object.keys(profile.templates), ...Object.keys(profile.bridges)].sort())}.`,
  );
}

/** The template whose roles, sign aptness, forms and edge `operator` has: itself, or a bridge's template. */
export function templateOf(profile: ProfileSpec, operator: CompiledOperator): CompiledTemplate {
  if (operator.kind === "template") return operator;
  if (!Object.hasOwn(profile.templates, operator.template)) {
    throw new ProfileError(
      `bridge ${JSON.stringify(operator.term)} maps to ${JSON.stringify(operator.template)}, not in this profile`,
    );
  }
  return profile.templates[operator.template];
}

/**
 * The typed addresses of the declarations admitting a claim over `operator`
 * whose roles carry the sorts in `assignment`.
 *
 * For a template, the instantiations (from the admission index, in its order)
 * whose sort set for every role contains every sort the claim puts in that role;
 * for a bridge, the bridge itself when its own sort sets do. A reserved role
 * (`within-model`) is admitted on every operator by the kernel, so it reaches no
 * declaration; a role the template does not declare refuses. No authoring flag:
 * this side refuses `retired` at parse, so no declaration here is retired.
 */
export function admitting(
  profile: ProfileSpec,
  operator: string,
  assignment: ReadonlyMap<string, ReadonlySet<string>>,
): readonly string[] {
  const declared = resolveOperator(profile, operator);
  const template = templateOf(profile, declared);
  const roles: [string, ReadonlySet<string>][] = [];
  for (const [role, sorts] of assignment) {
    if (Object.hasOwn(profile.claimGrammar.reservedRoles, role)) continue;
    if (!Object.hasOwn(template.roles, role)) {
      throw new ProfileError(
        `${JSON.stringify(operator)} declares no role ${JSON.stringify(role)}; its roles are ${JSON.stringify(Object.keys(template.roles).sort())}`,
      );
    }
    roles.push([role, sorts]);
  }
  const routes: readonly (readonly [string, CompiledInstantiation | CompiledBridge])[] =
    declared.kind === "bridge"
      ? [[`bridge:${declared.term}`, declared]]
      : profile.admission[declared.term].map((address) => [address, declarationAt(profile, address)] as const);
  return Object.freeze(
    routes
      .filter(([, route]) =>
        roles.every(([role, sorts]) => [...sorts].every((sort) => route.roles[role].includes(sort))),
      )
      .map(([address]) => address),
  );
}

/**
 * The estimand declarations at the typed addresses `admitting`, in the order
 * given. An admitting declaration with no estimand declaration contributes none.
 * Every address must be a declaration of `operator`: an instantiation of it, or
 * the bridge itself.
 */
export function estimandDeclarations(
  profile: ProfileSpec,
  operator: string,
  admitting: readonly string[],
): readonly CompiledEstimandDecl[] {
  const declared = resolveOperator(profile, operator);
  const found: CompiledEstimandDecl[] = [];
  for (const address of admitting) {
    const target = declarationAt(profile, address);
    const owner = address.startsWith("bridge:") ? target.term : target.template;
    if (owner !== declared.term) {
      throw new ProfileError(
        `${JSON.stringify(address)} is a declaration of ${JSON.stringify(owner)}, not of operator ${JSON.stringify(operator)}`,
      );
    }
    if (Object.hasOwn(profile.estimands, address)) found.push(profile.estimands[address]);
  }
  return Object.freeze(found);
}

/**
 * Dereference a typed address, `instantiation:<namespace>/<name>` or
 * `bridge:<namespace>/<name>`. The tables stay keyed by term: the kind before
 * the first `:` says which one to read.
 */
export function declarationAt(profile: ProfileSpec, address: string): CompiledInstantiation | CompiledBridge {
  const separator = address.indexOf(":");
  if (separator < 0) {
    throw new ProfileError(
      `${JSON.stringify(address)} is not a typed address; expected \`instantiation:<namespace>/<name>\` or \`bridge:<namespace>/<name>\``,
    );
  }
  const kind = address.slice(0, separator);
  const target = address.slice(separator + 1);
  if (kind === "instantiation") {
    if (!Object.hasOwn(profile.instantiations, target))
      throw new ProfileError(`no instantiation ${JSON.stringify(target)} in this profile`);
    return profile.instantiations[target];
  }
  if (kind === "bridge") {
    if (!Object.hasOwn(profile.bridges, target))
      throw new ProfileError(`no bridge ${JSON.stringify(target)} in this profile`);
    return profile.bridges[target];
  }
  throw new ProfileError(
    `${JSON.stringify(address)}: ${JSON.stringify(kind)} is not an addressable declaration; expected instantiation or bridge`,
  );
}

/**
 * The claim-side dimensions whose `applies_to` names `operator`, sorted: the
 * dimensions a claim over it may carry as qualifiers, wherever they are declared.
 */
export function claimDimensions(profile: ProfileSpec, operator: string): readonly string[] {
  const operatorTerm = resolveOperator(profile, operator).term;
  return sorted(
    Object.entries(profile.dimensions)
      .filter(([, dimension]) => dimension.placement === CLAIM_PLACEMENT && dimension.appliesTo.includes(operatorTerm))
      .map(([name]) => name),
  );
}
