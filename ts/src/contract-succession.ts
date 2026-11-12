/** Canonical schema projections mirrored from contract/domain.py, excluding editorial prose. */
import type { DomainContract, RestrictionForm, RoleDecl } from "./contract.js";
import { type IdentityValue, compareByCodePoint } from "./identity/v1.js";

type Projection = { [key: string]: IdentityValue };
const sorted = (values: readonly string[]) => [...values].sort(compareByCodePoint);
const roles = (values: Readonly<Record<string, readonly string[]>>): Projection =>
  Object.fromEntries(Object.entries(values).map(([name, sorts]) => [name, sorted(sorts)]));

function restriction(value: RestrictionForm): Projection {
  switch (value.form) {
    case "term":
      return { form: value.form, sort: value.sort };
    case "interval":
      return { form: value.form, quantity_kind: value.quantityKind };
    case "rule":
      return { form: value.form, classes: value.classes };
    case "time-interval":
      return { form: value.form };
    case "union":
      return { form: value.form, of: restriction(value.of) };
  }
}

function role(value: RoleDecl): Projection {
  const result: Projection = {
    arity: value.arity,
    coefficients: value.coefficients,
    constraint: sorted(value.constraint),
  };
  if (value.arity === "many") {
    result.min = BigInt(value.min);
    if (value.max !== null) result.max = BigInt(value.max);
  }
  return result;
}

/** Fresh comparison values; no mutable Map is retained by a branded contract. */
export function claimVocabulary(contract: DomainContract): ReadonlyMap<string, IdentityValue> {
  const result = new Map<string, IdentityValue>();
  function add<T>(family: string, declarations: Readonly<Record<string, T>>, project: (value: T) => Projection) {
    for (const [name, value] of Object.entries(declarations)) result.set(`${family}:${name}`, project(value));
  }
  add("sort", contract.sorts, (d) => {
    const p: Projection = {
      binding:
        d.binding.kind === "world-kind" ? { kind: "world-kind", world_kind: d.binding.worldKind } : { ...d.binding },
      categories: sorted(d.categories),
    };
    if (d.identifierClass !== null)
      p.identifier_class = { prefix: d.identifierClass.prefix, pattern: d.identifierClass.pattern };
    return p;
  });
  add("dimension", contract.dimensions, (d) => {
    const p: Projection = {
      restriction_sort: d.restrictionSort,
      placement: d.placement,
      applies_to: sorted(d.appliesTo),
    };
    if (d.restriction !== null) p.restriction = restriction(d.restriction);
    return p;
  });
  add("template", contract.templates, (d) => {
    const p: Projection = {
      roles: Object.fromEntries(Object.entries(d.roles).map(([name, value]) => [name, role(value)])),
      sign_apt: d.signApt,
      layers: sorted(d.layers),
      forms: sorted(d.forms),
    };
    if (d.edge !== null) p.edge = { ...d.edge };
    if (d.external !== null) p.external = { ...d.external };
    return p;
  });
  add("instantiation", contract.instantiations, (d) => ({ template: d.template, roles: roles(d.roles) }));
  add("bridge", contract.bridges, (d) => {
    const p: Projection = { template: d.template, mapping: d.mapping, roles: roles(d.roles) };
    if (d.layers !== null) p.layers = sorted(d.layers);
    return p;
  });
  add("estimand", contract.estimands, (d) => ({
    forms: sorted(d.forms),
    conditioning_sorts: sorted(d.conditioningSorts),
  }));
  add("duration-convention", contract.durationConventions, (d) => ({ conversion: d.conversion }));
  add("functional", contract.functionals, (d) => ({
    ...d,
    parameters:
      d.parameters === "not-applicable"
        ? d.parameters
        : Object.fromEntries(
            Object.entries(d.parameters).map(([name, value]) => [name, { typing: value.typing, domain: value.domain }]),
          ),
  }));
  add("identification-class", contract.identificationClasses, (d) => ({ licenses_layers: sorted(d.licensesLayers) }));
  add("design", contract.designs, () => ({}));
  add("selection-mechanism", contract.selectionMechanisms, () => ({}));
  add("procedure-kind", contract.procedureKinds, (d) => ({ fills_within_model: d.fillsWithinModel }));
  add("aggregation-rule", contract.aggregationRules, () => ({}));
  add("assumption-kind", contract.assumptionKinds, (d) => ({
    collapses: d.collapses,
    particulars: sorted(d.particulars),
  }));
  add("measurement", contract.measurements, (d) => ({ quantity_kinds: sorted(d.quantityKinds) }));
  add("aspect", contract.aspects, (d) => ({ aspect_sorts: sorted(d.aspectSorts) }));
  add("quantity-kind", contract.quantityKinds, (d) => ({
    dimension:
      typeof d.dimension === "string"
        ? d.dimension
        : Object.fromEntries(Object.entries(d.dimension).map(([name, value]) => [name, BigInt(value)])),
  }));
  add("unit", contract.units, (d) => {
    const p: Projection = { symbol: d.symbol, quantity_kind: d.quantityKind, calendar: d.calendar };
    if (d.external !== null) p.external = { ...d.external };
    return p;
  });
  add("constant", contract.constants, (d) => ({ value: d.value.text, unit: d.unit, exact: d.exact }));
  add("conversion", contract.conversions, (d) => {
    const p: Projection = { from: d.fromUnit, to: d.toUnit, kind: d.kind, factor: d.factor.text, exact: d.exact };
    if (d.offset !== null) p.offset = d.offset.text;
    if (d.error !== null) p.error = d.error.text;
    if (d.constant !== null) p.constant = d.constant;
    return p;
  });
  add("transformation", contract.transformations, (d) => {
    const p: Projection = { kind: d.kind, fixed: d.fixed, domain: d.domain, invertible: d.invertible };
    for (const key of ["scale", "offset", "base"] as const) if (d[key] !== null) p[key] = d[key].text;
    if (d.direction !== null) p.direction = d.direction;
    return p;
  });
  return result;
}
