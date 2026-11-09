import { describe, expect, it } from "vitest";
import { Member, Referent, canonicalMembers, memberKey } from "../src/claim.js";
import { CoefficientRefused, DuplicateMember } from "../src/errors.js";

const COMPOSED = "é".normalize("NFC");
const DECOMPOSED = "é".normalize("NFD");
const m = (term: string) => new Member(new Referent("x", term));

describe("members", () => {
  it("sorts by the NFC key", () => {
    expect(COMPOSED).not.toBe(DECOMPOSED);
    expect(canonicalMembers([m(COMPOSED), m("z")], "role").map((x) => x.referent.term)).toEqual(["z", COMPOSED]);
    expect(canonicalMembers([m(DECOMPOSED), m("z")], "role").map((x) => x.referent.term)).toEqual(["z", DECOMPOSED]);
    expect(memberKey(new Referent("x", COMPOSED))).toEqual(memberKey(new Referent("x", DECOMPOSED)));
  });

  it("refuses a duplicate by key", () => {
    expect(() => canonicalMembers([m(COMPOSED), m(DECOMPOSED)], "role")).toThrow(DuplicateMember);
  });

  it("sorts astral characters by code point, not code unit", () => {
    const bmp = "Ａ";
    const astral = "\u{1f600}";
    expect([astral, bmp].sort()).toEqual([astral, bmp]);
    expect(canonicalMembers([m(astral), m(bmp)], "role").map((x) => x.referent.term)).toEqual([bmp, astral]);
  });

  it("refuses bad coefficients", () => {
    const r = new Referent("x", "a");
    for (const bad of [0n, -1n, 1, "1", true] as unknown[]) {
      expect(() => new Member(r, bad as bigint)).toThrow(CoefficientRefused);
    }
  });

  it("keeps the spelling and defaults the coefficient", () => {
    const out = canonicalMembers([m(DECOMPOSED)], "role");
    expect(out[0].referent.term).toBe(DECOMPOSED);
    expect(out[0].coefficient).toBe(1n);
  });
});
