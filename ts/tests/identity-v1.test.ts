/**
 * `science.identity.v1`, TypeScript half — the rules a shared encoding lives or
 * dies by, tested on the side that gets them wrong by default.
 *
 * These mirror the Python suite. They are not redundant with the parity fixture:
 * the fixture pins the value contract only over the shapes `π_claim` uses —
 * strings, arrays and string-keyed objects — so integers, decimals, escapes and
 * the astral key-ordering rule are covered here and **nowhere across the two
 * languages**. A values-level parity fixture is owed.
 */

import { describe, expect, it } from "vitest";
import {
  BinaryFloatRefused,
  KeyCollision,
  LoneSurrogate,
  MalformedDecimal,
  MalformedDomain,
  NullRefused,
  UnsupportedValueType,
} from "../src/errors.js";
import { Decimal, checkDomain, digest, encode } from "../src/identity/v1.js";

const text = (value: unknown) => new TextDecoder().decode(encode(value));

// Written as escapes so this file stays ASCII and no tool can normalize the
// distinction away.
const E_ACUTE = "\u00e9";
const E_COMBINING = "e\u0301";

describe("keys sort by code point, never by UTF-16 code unit", () => {
  it("orders an astral key after a high BMP one", () => {
    // U+FF03 is a lone BMP code point; U+1F600 is astral and encodes in UTF-16
    // as the surrogate pair D83D DE00. By code point U+FF03 < U+1F600; by code
    // unit D83D < FF03, so the two orders disagree — and `Array.sort()` uses the
    // wrong one.
    const encoded = text({ "\u{1F600}": "astral", "\uff03": "bmp" });
    expect(encoded.indexOf("bmp")).toBeLessThan(encoded.indexOf("astral"));
  });

  it("is not the default JavaScript ordering", () => {
    const keys = ["\u{1F600}", "\uff03"];
    expect([...keys].sort()).toEqual(["\u{1F600}", "\uff03"]);
    const encoded = text(Object.fromEntries(keys.map((key) => [key, 1n])));
    expect(encoded.startsWith('{"\uff03"')).toBe(true);
  });

  it("orders plain keys the same way Python does", () => {
    expect(text({ b: 1n, a: 1n, C: 1n })).toBe('{"C":1,"a":1,"b":1}');
  });
});

describe("NFC normalization happens at encode time", () => {
  it("folds a decomposed string value into its composed form", () => {
    expect(text(E_COMBINING)).toBe(text(E_ACUTE));
    expect(text(E_COMBINING)).toBe(`"${E_ACUTE}"`);
  });

  it("refuses two keys that collide only after normalization", () => {
    expect(() => encode({ [E_ACUTE]: 1n, [E_COMBINING]: 2n })).toThrow(KeyCollision);
  });

  it("keeps the two distinct before normalization", () => {
    expect(E_ACUTE).not.toBe(E_COMBINING);
    expect(Array.from(E_COMBINING).length).toBe(2);
  });
});

describe("string escaping is pinned exactly", () => {
  it("escapes the two mandatory characters and nothing decorative", () => {
    expect(text('a"b\\c/d')).toBe('"a\\"b\\\\c/d"');
  });

  it("uses the short forms for the five C0 controls that have them", () => {
    expect(text("\b\t\n\f\r")).toBe('"\\b\\t\\n\\f\\r"');
  });

  it("uses lowercase \\u00xx for every other C0 control", () => {
    expect(text("\u0000\u001f")).toBe('"\\u0000\\u001f"');
  });

  it("never escapes non-ASCII", () => {
    expect(text("\u03b2")).toBe(`"\u03b2"`);
  });

  it("refuses a lone surrogate", () => {
    expect(() => encode("\uD83D")).toThrow(LoneSurrogate);
  });
});

describe("the numeric types keep their identity", () => {
  it("refuses a JavaScript number, integers included", () => {
    // The Python side's `float` refusal in this language's spelling: `1` and
    // `1.0` are one value, so the type would not survive the encoding.
    expect(() => encode(1)).toThrow(BinaryFloatRefused);
    expect(() => encode(1.5)).toThrow(BinaryFloatRefused);
  });

  it("encodes a bigint as an integer, with no point", () => {
    expect(text(42n)).toBe("42");
    expect(text(-42n)).toBe("-42");
  });

  it("gives a decimal exactly one spelling of zero, folding the negative", () => {
    expect(text(new Decimal("0"))).toBe("0.0");
    expect(text(new Decimal("-0.000"))).toBe("0.0");
  });

  it("always retains a fractional part and strips trailing zeros", () => {
    expect(text(new Decimal("12"))).toBe("12.0");
    expect(text(new Decimal("-0.500"))).toBe("-0.5");
    expect(text(new Decimal("1.10"))).toBe("1.1");
  });

  it("never emits exponent notation", () => {
    expect(text(new Decimal("1E+3"))).toBe("1000.0");
    expect(text(new Decimal("1.5e-3"))).toBe("0.0015");
  });

  it("refuses a non-finite or non-numeric decimal", () => {
    expect(() => new Decimal("NaN")).toThrow(MalformedDecimal);
    expect(() => new Decimal("Infinity")).toThrow(MalformedDecimal);
  });

  it("keeps an integer and a decimal apart", () => {
    expect(text(1n)).not.toBe(text(new Decimal("1")));
  });

  it("keeps a boolean and an integer apart", () => {
    expect(text(true)).toBe("true");
    expect(text(true)).not.toBe(text(1n));
  });
});

describe("the refusals", () => {
  it("refuses null and undefined rather than pruning them", () => {
    // An absent member must differ from a present-and-empty one, and pruning is
    // what makes `{"x": null}` and `{}` the same bytes.
    expect(() => encode(null)).toThrow(NullRefused);
    expect(() => encode({ x: undefined })).toThrow(NullRefused);
  });

  it("refuses a value type the contract does not admit", () => {
    expect(() => encode(new Map())).toThrow(UnsupportedValueType);
    expect(() => encode(new Date(0))).toThrow(UnsupportedValueType);
    expect(() => encode(Symbol("x"))).toThrow(UnsupportedValueType);
  });
});

describe("domains", () => {
  it("accepts a well-formed versioned domain", () => {
    expect(() => checkDomain("science.claim.v1")).not.toThrow();
    expect(() => checkDomain("science.identity.v1")).not.toThrow();
  });

  it("refuses one that could forge the separator or collide across versions", () => {
    for (const bad of ["science.claim", "claim.v1", "science.Claim.v1", "science.claim.v0", "science.claim.v1\nx"]) {
      expect(() => checkDomain(bad)).toThrow(MalformedDomain);
    }
  });

  it("separates the same bytes under two domains", () => {
    expect(digest("science.claim.v1", { a: "b" })).not.toBe(digest("science.profile.v1", { a: "b" }));
  });
});
