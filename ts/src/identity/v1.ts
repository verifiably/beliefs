/**
 * `science.identity.v1` — the canonical value contract, TypeScript half.
 *
 * The same contract the Python implementation carries. This is one of exactly two things
 * `ts/` exists for; the other is `π_claim`.
 *
 * Three rules below are where two implementations of "canonical JSON" diverge,
 * and all three are pinned by the contract rather than left to
 * each language's defaults:
 *
 * * **String escaping is exact.** `JSON.stringify` is not the specification —
 *   it agrees here by accident today and is not contractually bound to.
 * * **Object keys sort by code point, never by UTF-16 code unit.** This is the
 *   one JavaScript gets wrong by default: `Array.prototype.sort` compares UTF-16
 *   code units, and the two orders disagree above U+FFFF.
 * * **NFC normalization happens at encode time**, on both keys and string
 *   values, so a decomposed identifier and its composed form digest alike.
 */

import { createHash } from "node:crypto";
import {
  BinaryFloatRefused,
  KeyCollision,
  LoneSurrogate,
  MalformedDecimal,
  MalformedDomain,
  NonStringKey,
  NullRefused,
  UnsupportedValueType,
} from "../errors.js";

/** `science.<kind>.v<n>`, checked rather than assumed — a domain carrying a newline would forge the separator. */
const DOMAIN = /^science\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*\.v[1-9][0-9]*$/;

const SHORT_ESCAPE = new Map<number, string>([
  [0x08, "\\b"],
  [0x09, "\\t"],
  [0x0a, "\\n"],
  [0x0c, "\\f"],
  [0x0d, "\\r"],
]);

const DECIMAL = /^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/;

/**
 * An exact decimal, held as text.
 *
 * JavaScript has no decimal type, and the one it does have is refused
 * (`BinaryFloatRefused`). Constructing one from text keeps the caller's
 * significant digits intact and their rounding theirs, which is the whole
 * reason for refusing binary floats.
 */
export class Decimal {
  readonly text: string;

  constructor(text: string) {
    if (typeof text !== "string" || !DECIMAL.test(text)) {
      throw new MalformedDecimal(
        `${JSON.stringify(text)} is not a decimal; expected digits with an optional sign, point and exponent`,
      );
    }
    this.text = text;
  }
}

export type IdentityValue = string | boolean | bigint | Decimal | IdentityValue[] | { [key: string]: IdentityValue };

export function checkDomain(domain: string): void {
  if (!DOMAIN.test(domain)) {
    throw new MalformedDomain(
      `${JSON.stringify(domain)} is not a well-formed identity domain; expected \`science.<kind>.v<n>\`, lowercase, with a positive version`,
    );
  }
}

/**
 * Order two strings by **code point**.
 *
 * `[a, b].sort()` compares UTF-16 code units and is wrong above U+FFFF: an
 * astral character encodes as a surrogate pair beginning at U+D83D, which sorts
 * below U+FF03 by code unit and above it by code point. Iterating with `for…of`
 * yields code points, so the comparison below is the required one.
 */
export function compareByCodePoint(left: string, right: string): number {
  const a = Array.from(left);
  const b = Array.from(right);
  const shared = Math.min(a.length, b.length);
  for (let index = 0; index < shared; index += 1) {
    const x = a[index].codePointAt(0) as number;
    const y = b[index].codePointAt(0) as number;
    if (x !== y) return x < y ? -1 : 1;
  }
  return a.length - b.length;
}

function encodeString(value: string, path: string): string {
  const normalized = value.normalize("NFC");
  const out: string[] = ['"'];
  for (const char of normalized) {
    const codePoint = char.codePointAt(0) as number;
    if (codePoint >= 0xd800 && codePoint <= 0xdfff) {
      throw new LoneSurrogate(
        `at ${path}: U+${codePoint.toString(16).toUpperCase().padStart(4, "0")} is an unpaired surrogate and has no UTF-8 encoding`,
      );
    }
    if (char === '"') out.push('\\"');
    else if (char === "\\") out.push("\\\\");
    else if (SHORT_ESCAPE.has(codePoint)) out.push(SHORT_ESCAPE.get(codePoint) as string);
    else if (codePoint < 0x20) out.push(`\\u${codePoint.toString(16).padStart(4, "0")}`);
    // Everything else is literal UTF-8. Non-ASCII is never escaped, and `/` is
    // never escaped: both are optional in JSON, and an option is a place two
    // implementations can differ.
    else out.push(char);
  }
  out.push('"');
  return out.join("");
}

function encodeDecimal(value: Decimal, path: string): string {
  const match = DECIMAL.exec(value.text);
  if (match === null) throw new MalformedDecimal(`at ${path}: ${value.text} is not a decimal`);
  const [, sign, whole, fractionPart, exponentPart] = match;

  // Expand any exponent into plain notation first: `format(value, "f")` on the
  // Python side never emits exponent notation, so neither may this.
  const digits = whole + (fractionPart ?? "");
  let pointAt = whole.length + Number(exponentPart ?? "0");
  let expanded = digits;
  if (pointAt <= 0) {
    expanded = "0".repeat(1 - pointAt) + digits;
    pointAt += 1 - pointAt;
  } else if (pointAt > digits.length) {
    expanded = digits + "0".repeat(pointAt - digits.length);
  }
  const integer = expanded.slice(0, pointAt).replace(/^0+(?=\d)/, "");
  const fraction = expanded.slice(pointAt).replace(/0+$/, "");

  // One spelling of zero, which also folds negative zero. Two spellings of one
  // value would break well-definedness even though neither collides.
  if (/^0*$/.test(integer) && fraction === "") return "0.0";
  return `${sign === "-" ? "-" : ""}${integer}.${fraction === "" ? "0" : fraction}`;
}

function isPlainObject(value: object): boolean {
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function encodeValue(value: unknown, path: string): string {
  if (value === null || value === undefined) {
    throw new NullRefused(`at ${path}: null is refused, not pruned`);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    throw new BinaryFloatRefused(
      `at ${path}: a JavaScript number is an IEEE binary double and is refused at the boundary; supply a bigint for an integer or a Decimal for a decimal, and own the rounding`,
    );
  }
  if (typeof value === "bigint") return value.toString();
  if (typeof value === "string") return encodeString(value, path);
  if (value instanceof Decimal) return encodeDecimal(value, path);
  if (Array.isArray(value)) return `[${value.map((item, index) => encodeValue(item, `${path}[${index}]`)).join(",")}]`;
  if (typeof value === "object" && isPlainObject(value)) return encodeObject(value as Record<string, unknown>, path);
  throw new UnsupportedValueType(
    `at ${path}: ${Object.prototype.toString.call(value)} is not an identity value; admissible are string, boolean, bigint, Decimal, array and plain object`,
  );
}

function encodeObject(value: Record<string, unknown>, path: string): string {
  const normalized = new Map<string, unknown>();
  for (const key of Reflect.ownKeys(value)) {
    if (typeof key !== "string") {
      throw new NonStringKey(`at ${path}: object key ${String(key)} is a symbol, not a string`);
    }
    const normalizedKey = key.normalize("NFC");
    if (normalized.has(normalizedKey)) {
      throw new KeyCollision(
        `at ${path}: keys ${JSON.stringify(key)} and an earlier key are distinct before NFC normalization ` +
          `and identical after it (${JSON.stringify(normalizedKey)}); refused, never merged`,
      );
    }
    normalized.set(normalizedKey, value[key]);
  }
  const parts = Array.from(normalized.keys())
    .sort(compareByCodePoint)
    .map((key) => `${encodeString(key, path)}:${encodeValue(normalized.get(key), `${path}.${key}`)}`);
  return `{${parts.join(",")}}`;
}

/** Canonical bytes for an identity value, or a refusal. */
export function encode(value: unknown): Uint8Array {
  return new TextEncoder().encode(encodeValue(value, "$"));
}

/** `sha256(domain + "\n" + canonical bytes)`, hex, domain-separated per kind. */
export function digest(domain: string, value: unknown): string {
  checkDomain(domain);
  const hash = createHash("sha256");
  hash.update(new TextEncoder().encode(`${domain}\n`));
  hash.update(encode(value));
  return hash.digest("hex");
}
