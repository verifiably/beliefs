/**
 * The compiled runtime profile, in the reduced form the shared-encoding path
 * needs: **resolution**, and the declarations a claim is typed against.
 *
 * `ProfileSpec` resolves; contracts authorize (§7.5). This side does the
 * resolving — local names become term identifiers, because a claim's projection
 * carries term identifiers and a local name is not one — and nothing else. In
 * particular there is **no `compiled_identity` here**: §8 sites claim-schema
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
  type DeclarationTable,
  DomainContract,
  type FacetDecl,
  type KindDecl,
  type RelationDecl,
} from "./contract.js";
import { ContractMismatch, MalformedContract, ProfileError, SubclassRefused, UnparsedContract } from "./errors.js";

export interface CompiledOperator {
  readonly term: string;
  readonly arity: number;
  readonly argSorts: readonly string[];
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly dimensions: readonly string[];
}

export interface CompiledDimension {
  readonly term: string;
  readonly restrictionSort: string;
}

const MINT = Symbol("science.profile.mint");

/** Term identifier → compiled declaration. A frozen null-prototype record, for the reason `DeclarationTable` gives in `contract.ts`. */
export type ResolutionTable<T> = Readonly<Record<string, T>>;

export class ProfileSpec {
  #minted = true;
  readonly kinds: DeclarationTable<KindDecl>;
  readonly facets: DeclarationTable<FacetDecl>;
  readonly relations: DeclarationTable<RelationDecl>;
  readonly claimGrammar: ClaimGrammar;
  readonly operators: ResolutionTable<CompiledOperator>;
  readonly dimensions: ResolutionTable<CompiledDimension>;
  readonly sorts: readonly string[];

  constructor(
    token: symbol,
    parts: {
      kinds: DeclarationTable<KindDecl>;
      facets: DeclarationTable<FacetDecl>;
      relations: DeclarationTable<RelationDecl>;
      claimGrammar: ClaimGrammar;
      operators: ResolutionTable<CompiledOperator>;
      dimensions: ResolutionTable<CompiledDimension>;
      sorts: readonly string[];
    },
  ) {
    if (new.target !== ProfileSpec) {
      throw new SubclassRefused("ProfileSpec is sealed: a subclass could stand in for a compiled profile");
    }
    if (token !== MINT) {
      throw new ProfileError(
        "ProfileSpec is compiled, never authored — use compileProfile(base, domains). D §6 retired the " +
          "second per-kind source of truth; an authored profile would reintroduce it through the constructor.",
      );
    }
    // Snapshotted, not adopted, and this is the **only** place the tables are
    // frozen. `compileProfile` hands over ordinary mutable ones: putting the
    // freeze there as well would leave two places responsible for an invariant
    // this class is the one promising, and the copy here would then be
    // unreachable — defending against a caller the mint token makes impossible,
    // and untestable for the same reason.
    this.kinds = frozenTable(Object.entries(parts.kinds));
    this.facets = frozenTable(Object.entries(parts.facets));
    this.relations = frozenTable(Object.entries(parts.relations));
    this.claimGrammar = parts.claimGrammar;
    this.operators = frozenTable(Object.entries(parts.operators));
    this.dimensions = frozenTable(Object.entries(parts.dimensions));
    this.sorts = Object.freeze([...parts.sorts]);
    Object.freeze(this);
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

export function compileProfile(base: BaseContract, domains: readonly DomainContract[]): ProfileSpec {
  if (!BaseContract.is(base)) {
    throw new UnparsedContract(
      "the base contract was not parsed from its document — use parseBaseContract(text, source). A profile " +
        "compiled from an authored grammar would resolve claims against polarities and layers nobody declared.",
    );
  }
  // Mutable while they are being built, and frozen by the constructor — see
  // there for why the freeze lives in one place rather than both.
  const operators: Record<string, CompiledOperator> = Object.create(null);
  const dimensions: Record<string, CompiledDimension> = Object.create(null);
  const sorts: string[] = [];
  const sortOwners: Record<string, string> = Object.create(null);
  const facets: Record<string, FacetDecl> = Object.assign(Object.create(null), base.facets);
  const seen = new Set<string>();

  for (const contract of domains) {
    if (!DomainContract.is(contract)) {
      throw new UnparsedContract(
        "a domain contract was not parsed from its document — use parseDomainContract(text, source, base). " +
          "Operators are domain-issued (§7.1), and an authored contract issues them on no authority.",
      );
    }
    if (contract.base !== base) {
      // Provenance is not enough on its own: two contracts can each be entirely
      // genuine and still not belong together. This domain's layers were checked
      // at parse time against a different base, and nothing revalidates them
      // afterwards — so compiling it here would put a claim on a layer the base
      // in force does not declare, with nothing forged anywhere.
      throw new ContractMismatch(
        `domain contract ${JSON.stringify(contract.namespace)} was parsed against a different base contract than the one being compiled with. A domain selects its layers from the base vocabulary and may not extend it (§7.1); that check ran against another document, so nothing here can stand behind it.`,
      );
    }
    if (seen.has(contract.namespace)) {
      // Contributions in different namespaces compose; two to one namespace are
      // refused at compile, never resolved last-writer-wins (D §8).
      throw new ProfileError(`two contracts contribute to namespace ${JSON.stringify(contract.namespace)}`);
    }
    seen.add(contract.namespace);
    for (const [key, facet] of Object.entries(contract.facets)) {
      for (const kind of facet.attachesTo) {
        if (base.kinds[kind]?.role !== "world")
          throw new ProfileError(`${key}: attaches_to names ${kind}, not a world kind`);
      }
      facets[key] = facet;
    }
    for (const name of Object.keys(contract.sorts)) {
      const sort = term(contract.namespace, name);
      sorts.push(sort);
      sortOwners[sort] = contract.namespace;
    }
  }

  const resolveSort = (contract: DomainContract, name: string, where: string): string => {
    const resolved = name.includes("/") ? name : term(contract.namespace, name);
    if (!(resolved in sortOwners)) {
      const namespace = resolved.split("/")[0];
      throw new MalformedContract(
        `${contract.namespace}: ${where} names sort ${JSON.stringify(resolved)}, but no contract for namespace ${JSON.stringify(namespace)} is compiled into this profile`,
      );
    }
    return resolved;
  };

  for (const contract of domains) {
    for (const [name, declaration] of Object.entries(contract.dimensions)) {
      dimensions[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        restrictionSort: resolveSort(contract, declaration.restrictionSort, `dimensions.${name}: restriction_sort`),
      });
    }
    for (const [name, declaration] of Object.entries(contract.operators)) {
      // The declarations themselves are frozen here, where they are made. A
      // shallow freeze would leave `argSorts` writable, and rewriting one slot
      // re-types an operator that is otherwise entirely real.
      operators[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        arity: declaration.arity,
        argSorts: Object.freeze(
          declaration.argSorts.map((sort, slot) =>
            resolveSort(contract, sort, `operators.${name}: arg_sorts[${slot}]`),
          ),
        ),
        signApt: declaration.signApt,
        layers: Object.freeze([...declaration.layers]),
        dimensions: Object.freeze(declaration.dimensions.map((dimension) => term(contract.namespace, dimension))),
      });
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
  return new ProfileSpec(MINT, {
    kinds: base.kinds,
    relations: base.relations,
    facets,
    claimGrammar: base.claimGrammar,
    operators,
    dimensions,
    sorts,
  });
}

/**
 * Resolve an operator term identifier, or refuse.
 *
 * §7.4 row 4a: a claim naming an operator whose declaring contract is not in the
 * profile is a local, static failure, so it refuses here and nothing is minted.
 */
export function resolveOperator(profile: ProfileSpec, term: string): CompiledOperator {
  const operator = profile.operators[term];
  if (operator === undefined) {
    throw new ProfileError(
      `no operator ${JSON.stringify(term)} in this profile. Operators are domain-issued (§7.1); ` +
        `this profile resolves ${JSON.stringify(Object.keys(profile.operators).sort())}.`,
    );
  }
  return operator;
}
