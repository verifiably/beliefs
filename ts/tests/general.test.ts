/**
 * Explicit consumer activation and cross-language claim-identity parity over
 * `domains/general/DOMAIN.yaml` and `fixtures/contracts/general-consumer.yaml`.
 *
 * TypeScript reads source `DOMAIN.yaml` documents with `parseDomainContract` +
 * `compileProfile`; there is no TS package/resource loader, register reader,
 * `compiled_identity` calculation, or estimand implementation. Parity covers
 * canonical contract source bytes/digests, resolved declarations, checked claim
 * construction, symmetric `parties` member ordering, duplicate-after-NFC
 * refusal, and canonical claim projections, bytes and digests against
 * `fixtures/general-claim-identity-v2.json`.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  CLAIM_DOMAIN,
  DuplicateMember,
  Member,
  ProfileError,
  Qualifier,
  Referent,
  type RoleFilling,
  SuccessionViolation,
  buildClaim,
  claimIdentity,
  compileProfile,
  encode,
  parseBaseContract,
  parseDomainContract,
  projectClaim,
} from "../src/index.js";

const REPO_ROOT = new URL("../../", import.meta.url);

function read(relative: string): string {
  return readFileSync(new URL(relative, REPO_ROOT), "utf-8");
}

const GENERAL_PATH = "domains/general/DOMAIN.yaml";
const GENERAL_HISTORY =
  "domains/general/history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f/DOMAIN.yaml";

function parseGeneral(base: ReturnType<typeof parseBaseContract>) {
  const predecessor = parseDomainContract(read(GENERAL_HISTORY), GENERAL_HISTORY, base);
  return parseDomainContract(read(GENERAL_PATH), GENERAL_PATH, base, predecessor);
}

interface FixtureReferent {
  sort: string;
  term: string;
}

interface FixtureMember extends FixtureReferent {
  coefficient: number;
}

type FixtureRole = FixtureReferent | FixtureMember[];

interface FixtureProjection {
  operator: string;
  roles: Record<string, FixtureReferent | FixtureMember[]>;
  qualifiers: Record<string, { quantifier: string; restriction: FixtureReferent }>;
  form: string;
  polarity: string;
  layer: string;
}

interface FixtureRow {
  name: string;
  covers: string;
  claim: {
    operator: string;
    roles: Record<string, FixtureRole>;
    qualifiers: Record<string, { quantifier: string; restriction: FixtureReferent }>;
    form: string;
    polarity: string | null;
    layer: string;
  };
  projection: FixtureProjection;
  canonical_bytes: string;
  digest: string;
}

interface GeneralParityFixture {
  claim_domain: string;
  identity_contract: string;
  base_contract: string;
  domain_contracts: string[];
  profile_compiled_identity: string;
  vector: FixtureRow[];
}

function referent(value: FixtureReferent): Referent {
  return new Referent(value.sort, value.term);
}

function role(value: FixtureRole): RoleFilling {
  if (Array.isArray(value)) {
    return value.map((member) => new Member(referent(member), BigInt(member.coefficient)));
  }
  return referent(value);
}

function expectedProjection(row: FixtureProjection): unknown {
  const roles: Record<string, unknown> = {};
  for (const [name, value] of Object.entries(row.roles)) {
    roles[name] = Array.isArray(value)
      ? value.map((member) => ({ ...member, coefficient: BigInt(member.coefficient) }))
      : value;
  }
  return { ...row, roles };
}

describe("general contract explicit consumer activation", () => {
  const basePath = "contracts/science/CONTRACT.yaml";
  const generalPath = "domains/general/DOMAIN.yaml";
  const consumerPath = "fixtures/contracts/general-consumer.yaml";

  it("compiles base + general alone with zero sorts and zero instantiations", () => {
    const rawGeneral = read(generalPath);
    expect(rawGeneral).toBe(read("python/src/beliefs/domains/general/DOMAIN.yaml"));
    const base = parseBaseContract(read(basePath), basePath);
    const general = parseGeneral(base);
    expect(general.namespace).toBe("general");
    expect(general.version).toBe(2);

    const alone = compileProfile(base, [general]);
    expect(Object.keys(alone.sorts)).toEqual([]);
    expect(Object.keys(alone.instantiations)).toEqual([]);
    expect(Object.keys(alone.templates).sort()).toEqual([
      "general/changes-under-intervention",
      "general/covaries-with",
    ]);
    expect(Object.keys(alone.quantityKinds)).toEqual(["general/relative-abundance"]);
    expect(Object.keys(alone.transformations)).toEqual(["general/identity"]);
    expect(Object.keys(alone.functionals)).toEqual(["general/probability-of-superiority"]);
    expect(Object.keys(alone.identificationClasses)).toEqual(["general/observational"]);
    expect(Object.keys(alone.designs)).toEqual(["general/independent-groups"]);
    expect(Object.keys(alone.selectionMechanisms)).toEqual(["general/cohort-enrolment"]);
    expect(Object.keys(alone.procedureKinds).sort()).toEqual(["general/assay", "general/estimator"]);
  });

  it("refuses consumer compilation when general is omitted and succeeds when activated", () => {
    const base = parseBaseContract(read(basePath), basePath);
    const general = parseGeneral(base);
    const consumer = parseDomainContract(read(consumerPath), consumerPath, base);

    expect(() => compileProfile(base, [consumer])).toThrow(ProfileError);

    const profile = compileProfile(base, [general, consumer]);
    expect(Object.keys(profile.sorts).sort()).toEqual([
      "general-consumer/analyte",
      "general-consumer/stratum",
      "general-consumer/trait",
    ]);
    expect(profile.measurements["general-consumer/analyte"]).toEqual(["general/relative-abundance"]);
    expect(profile.admitsMeasurement("general-consumer/analyte", "general/relative-abundance")).toBe(true);
  });

  it("preserves party order-invariance and refuses duplicate-after-NFC members", () => {
    const base = parseBaseContract(read(basePath), basePath);
    const general = parseGeneral(base);
    const consumer = parseDomainContract(read(consumerPath), consumerPath, base);
    const profile = compileProfile(base, [general, consumer]);

    const sameFwd = buildClaim(profile, {
      operator: "general/covaries-with",
      roles: new Map([
        [
          "parties",
          [
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-b")),
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-a")),
          ],
        ],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: "positive",
      layer: "statistical",
    });
    const sameRev = buildClaim(profile, {
      operator: "general/covaries-with",
      roles: new Map([
        [
          "parties",
          [
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-a")),
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-b")),
          ],
        ],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: "positive",
      layer: "statistical",
    });
    expect(projectClaim(sameFwd)).toEqual(projectClaim(sameRev));
    expect(claimIdentity(sameFwd)).toBe(claimIdentity(sameRev));

    const crossFwd = buildClaim(profile, {
      operator: "general/covaries-with",
      roles: new Map([
        [
          "parties",
          [
            new Member(new Referent("general-consumer/stratum", "SYN:arm-high")),
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-a")),
          ],
        ],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: "positive",
      layer: "statistical",
    });
    const crossRev = buildClaim(profile, {
      operator: "general/covaries-with",
      roles: new Map([
        [
          "parties",
          [
            new Member(new Referent("general-consumer/analyte", "SYN:analyte-a")),
            new Member(new Referent("general-consumer/stratum", "SYN:arm-high")),
          ],
        ],
      ]),
      qualifiers: new Map(),
      form: "polar",
      polarity: "positive",
      layer: "statistical",
    });
    expect(projectClaim(crossFwd)).toEqual(projectClaim(crossRev));
    expect(claimIdentity(crossFwd)).toBe(claimIdentity(crossRev));

    expect(() =>
      buildClaim(profile, {
        operator: "general/covaries-with",
        roles: new Map([
          [
            "parties",
            [
              new Member(new Referent("general-consumer/analyte", "SYN:caf\u00e9")),
              new Member(new Referent("general-consumer/analyte", "SYN:cafe\u0301")),
            ],
          ],
        ]),
        qualifiers: new Map(),
        form: "polar",
        polarity: "positive",
        layer: "statistical",
      }),
    ).toThrow(DuplicateMember);
  });
});

describe("general cross-language claim parity vector", () => {
  it("reproduces every row in fixtures/general-claim-identity-v2.json", () => {
    const rawFixture = read("fixtures/general-claim-identity-v2.json");
    // biome-ignore lint/suspicious/noControlCharactersInRegex: enforce pure-ASCII storage
    expect(/^[\x00-\x7f]*$/.test(rawFixture)).toBe(true);

    const fixture = JSON.parse(rawFixture) as GeneralParityFixture;
    expect(fixture.claim_domain).toBe(CLAIM_DOMAIN);
    expect(fixture.identity_contract).toBe("science.identity.v1");
    expect(fixture.base_contract).toBe("contracts/science/CONTRACT.yaml");
    expect(fixture.domain_contracts).toEqual([
      "domains/general/DOMAIN.yaml",
      "fixtures/contracts/general-consumer.yaml",
    ]);

    const base = parseBaseContract(read(fixture.base_contract), fixture.base_contract);
    const profile = compileProfile(
      base,
      fixture.domain_contracts.map((path) =>
        path === GENERAL_PATH ? parseGeneral(base) : parseDomainContract(read(path), path, base),
      ),
    );

    const byName = new Map<string, FixtureRow>();
    for (const row of fixture.vector) {
      byName.set(row.name, row);
      const qualifiers = new Map<string, Qualifier>();
      for (const [dimension, entry] of Object.entries(row.claim.qualifiers)) {
        qualifiers.set(dimension, new Qualifier(entry.quantifier, referent(entry.restriction)));
      }
      const claim = buildClaim(profile, {
        operator: row.claim.operator,
        roles: new Map(Object.entries(row.claim.roles).map(([name, value]) => [name, role(value)])),
        qualifiers,
        form: row.claim.form,
        polarity: row.claim.polarity,
        layer: row.claim.layer,
      });
      const projected = projectClaim(claim);
      expect(projected).toEqual(expectedProjection(row.projection));
      expect(new TextDecoder().decode(encode(projected))).toBe(row.canonical_bytes);
      expect(claimIdentity(claim)).toBe(row.digest);
    }

    for (const [fwdName, revName] of [
      ["same-sort-parties-forward", "same-sort-parties-reversed"],
      ["cross-sort-parties-forward", "cross-sort-parties-reversed"],
    ] as const) {
      const fwd = byName.get(fwdName);
      const rev = byName.get(revName);
      expect(fwd).toBeDefined();
      expect(rev).toBeDefined();
      expect(fwd?.projection).toEqual(rev?.projection);
      expect(fwd?.canonical_bytes).toBe(rev?.canonical_bytes);
      expect(fwd?.digest).toBe(rev?.digest);
    }

    const decomposedRow = byName.get("parties-decomposed-referent");
    expect(decomposedRow).toBeDefined();
    const decomposedParties = decomposedRow?.projection.roles.parties as FixtureMember[];
    const nfdTerm = "SYN:cafe\u0301";
    expect(decomposedParties.some((m) => m.term === nfdTerm)).toBe(true);
    expect(decomposedRow?.canonical_bytes).not.toContain(nfdTerm);
    expect(decomposedRow?.canonical_bytes).toContain(nfdTerm.normalize("NFC"));
  });
});

describe("general procedure-validity successor", () => {
  it("pins both content identities and requires the exact predecessor", () => {
    const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "<base>");
    const previous = parseDomainContract(read(GENERAL_HISTORY), GENERAL_HISTORY, base);
    expect(previous.contentIdentity).toBe("cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f");
    const current = parseGeneral(base);
    expect(current.contentIdentity).toBe("e74a497975e4a536f1bcbef26de73558d8a528276f4754082c6dd2d399f447ee");
    expect(current.predecessor).toBe(previous.contentIdentity);
    const profile = compileProfile(base, [current]);
    expect(Object.keys(profile.assumptionKinds)).toEqual(["general/procedure-validity"]);
    expect(new Set(profile.assumptionKinds["general/procedure-validity"].particulars)).toEqual(
      new Set(["record", "co_scope", "dimensions"]),
    );
    expect(profile.assumptionKinds["general/procedure-validity"].collapses).toBe(
      "The named procedure's unknown validation domain or recorded scope gap is conditionally accepted for this target.",
    );
    expect(() => parseDomainContract(read(GENERAL_PATH), GENERAL_PATH, base)).toThrow(SuccessionViolation);
    expect(() => parseDomainContract(read(GENERAL_PATH), GENERAL_PATH, base, current)).toThrow(SuccessionViolation);
  });
});
