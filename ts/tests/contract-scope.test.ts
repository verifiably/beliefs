/**
 * What this implementation refuses to read, and why refusing is the point.
 *
 * `ts/` carries the shared-encoding path (D §9), so there are contract features
 * it cannot validate: succession needs a declared predecessor and a two-contract
 * diff (§8.3), and retirement is an authoring-boundary rule (§7.3a) this side
 * has no authoring boundary to enforce.
 *
 * The failure mode this file exists to prevent is **quiet divergence**. A
 * reduced parser that skipped `lineage` and ignored `retired` would accept
 * documents the normative reading refuses, and would look like agreement — two
 * implementations reading one SSOT differently, with nothing to notice it. So
 * the unimplemented rules are refusals, not omissions.
 */

import { describe, expect, it } from "vitest";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { MalformedContract, UncheckableContract } from "../src/errors.js";
import { compileProfile } from "../src/profile.js";

const BASE = `
contract: science
version: 1
claim_grammar:
  version: 1
  tag_encoding: science.identity.v1
  quantifiers: [generic, universal, existential]
  polarities: [positive, negative, unsigned]
  sign_inapt_tag: inapt
  layers: [causal, structural]
kinds: {}
relations: {}
facets: {}
`;

const DOMAIN = `
contract: testing
version: 1
lineage: genesis
sorts:
  entity:
    vocabulary: { namespace: EX, release: "2026-01-01" }
dimensions:
  setting:
    restriction_sort: entity
operators:
  subtype-of:
    arity: 2
    arg_sorts: [entity, entity]
    sign_apt: false
    layers: [structural]
    dimensions: []
`;

const base = parseBaseContract(BASE, "<base>");

describe("the rules this implementation does not carry are refused, not skipped", () => {
  it("refuses a successor contract, because it cannot check succession", () => {
    const successor = DOMAIN.replace("lineage: genesis", "lineage: { successor: deadbeef }");
    expect(() => parseDomainContract(successor, "<domain>", base)).toThrow(UncheckableContract);
    expect(() => parseDomainContract(successor, "<domain>", base)).toThrow(/succession/);
  });

  it("refuses a retired declaration, because retirement lives in authoring", () => {
    const retired = DOMAIN.replace("    sign_apt: false", "    sign_apt: false\n    retired: true");
    expect(() => parseDomainContract(retired, "<domain>", base)).toThrow(UncheckableContract);
  });

  it("refuses a retired sort and a retired dimension too", () => {
    const sort = DOMAIN.replace(
      '    vocabulary: { namespace: EX, release: "2026-01-01" }',
      '    vocabulary: { namespace: EX, release: "2026-01-01" }\n    retired: true',
    );
    expect(() => parseDomainContract(sort, "<domain>", base)).toThrow(UncheckableContract);
    const dimension = DOMAIN.replace("    restriction_sort: entity", "    restriction_sort: entity\n    retired: true");
    expect(() => parseDomainContract(dimension, "<domain>", base)).toThrow(UncheckableContract);
  });

  it("reads a genesis contract with nothing retired", () => {
    const contract = parseDomainContract(DOMAIN, "<domain>", base);
    expect(contract.namespace).toBe("testing");
    expect("testing/subtype-of" in compileProfile(base, [contract]).operators).toBe(true);
  });
});

describe("the structural refusals both implementations share", () => {
  it("refuses an unknown field rather than ignoring it", () => {
    // D5: refused at load, never ignored — otherwise the reader and the loader
    // disagree about what the document says.
    expect(() => parseBaseContract(`${BASE}surprise: true\n`, "<base>")).toThrow(MalformedContract);
    expect(() => parseDomainContract(`${DOMAIN}surprise: true\n`, "<domain>", base)).toThrow(MalformedContract);
  });

  it("refuses a foreign tag encoding", () => {
    const foreign = BASE.replace("science.identity.v1", "science.identity.v2");
    expect(() => parseBaseContract(foreign, "<base>")).toThrow(/science.identity.v1/);
  });

  it("refuses a sign-inapt tag that is also an assertable polarity", () => {
    // §7.5: `inapt` and `unsigned` are different facts.
    const collided = BASE.replace("sign_inapt_tag: inapt", "sign_inapt_tag: unsigned");
    expect(() => parseBaseContract(collided, "<base>")).toThrow(/assertable polarity/);
  });

  it("refuses an operator whose arg_sorts do not fill every slot", () => {
    const short = DOMAIN.replace("arg_sorts: [entity, entity]", "arg_sorts: [entity]");
    expect(() => parseDomainContract(short, "<domain>", base)).toThrow(/one per slot/);
  });

  it("refuses a layer the base contract does not declare", () => {
    const unknown = DOMAIN.replace("layers: [structural]", "layers: [statistical]");
    expect(() => parseDomainContract(unknown, "<domain>", base)).toThrow(/not a layer/);
  });

  it("refuses two contracts contributing to one namespace", () => {
    const contract = parseDomainContract(DOMAIN, "<domain>", base);
    expect(() => compileProfile(base, [contract, contract])).toThrow(/one namespace|namespace/);
  });
});

describe("a cross-contract sort reference (biology pack design §4)", () => {
  const crossing = `
contract: crossing
version: 1
lineage: genesis
sorts:
  local:
    vocabulary: { namespace: EX, release: "2026-01-01" }
dimensions: {}
operators:
  affects-local-entity:
    arity: 2
    arg_sorts: [local, testing/entity]
    sign_apt: true
    layers: [causal]
    dimensions: []
`;
  it("defers a namespaced reference to compile and resolves it there", () => {
    const contract = parseDomainContract(crossing, "<crossing>", base);
    expect(contract.operators["affects-local-entity"].argSorts).toEqual(["local", "testing/entity"]);
    const testing = parseDomainContract(DOMAIN, "<domain>", base);
    const profile = compileProfile(base, [contract, testing]);
    expect(profile.operators["crossing/affects-local-entity"].argSorts).toEqual(["crossing/local", "testing/entity"]);
  });
  it("refuses an unresolved reference at compile, naming the sort and namespace", () => {
    const contract = parseDomainContract(crossing, "<crossing>", base);
    expect(() => compileProfile(base, [contract])).toThrow(MalformedContract);
    expect(() => compileProfile(base, [contract])).toThrow(
      /no compiled contract declares sort "testing\/entity" \(namespace "testing"\)/,
    );
  });
  it("uses the same diagnostic when the namespace is present but the sort is absent", () => {
    const contract = parseDomainContract(crossing.replace("testing/entity", "testing/missing"), "<crossing>", base);
    const testing = parseDomainContract(DOMAIN, "<domain>", base);
    expect(() => compileProfile(base, [contract, testing])).toThrow(
      /no compiled contract declares sort "testing\/missing" \(namespace "testing"\)/,
    );
  });
  it("refuses the contract's own namespace and the base's at parse", () => {
    const own = crossing.replace("testing/entity", "crossing/local");
    expect(() => parseDomainContract(own, "<crossing>", base)).toThrow(/own namespace/);
    const sci = crossing.replace("testing/entity", "science/local");
    expect(() => parseDomainContract(sci, "<crossing>", base)).toThrow(/declares no claim vocabulary/);
  });
  it("still refuses a bare undeclared name", () => {
    const bare = crossing.replace("testing/entity", "entity");
    expect(() => parseDomainContract(bare, "<crossing>", base)).toThrow(/not a declared sort/);
  });
});
