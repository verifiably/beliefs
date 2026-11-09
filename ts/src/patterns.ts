/**
 * The portable identifier-class pattern subset.
 *
 * The same grammar as `python/src/beliefs/patterns.py`, walked over code points;
 * `fixtures/identifier-patterns-v1.json` is the agreement oracle for both.
 *
 *     pattern   := branch ( "|" branch )*
 *     branch    := piece*
 *     piece     := atom quantifier?
 *     atom      := literal | "." | class | "(?:" pattern ")" | escape
 *     escape    := "\" one of  \ . [ ] ( ) { } | * + ? ^ $
 *     literal   := any code point except  \ . [ ] ( ) { } | * + ? ^ $
 *     quantifier:= "*" | "+" | "?" | "{" digits "}" | "{" digits "," digits "}"
 *     class     := "[" "^"? classitem+ "]"
 *     classitem := classatom ( "-" classatom )?
 *     classatom := "\" one of  \ ] - ^   | any code point except  \ [ ] - ^
 *                  (and no doubled & ~ | inside a class: engines read them as set operations)
 *     digits    := [0-9]+, at most 65535
 */

import { MalformedContract } from "./errors.js";

const SPECIAL = new Set(Array.from("\\.[](){}|*+?^$"));
const CLASS_SPECIAL = new Set(Array.from("\\]-^"));
const DOUBLED = new Set(Array.from("&~|"));
const MAX_BOUND = 65535;
const QUANTIFIERS = new Set(Array.from("*+?"));

class Walk {
  readonly cps: string[];
  i = 0;

  constructor(
    pattern: string,
    readonly where: string,
  ) {
    this.cps = Array.from(pattern);
  }

  refuse(why: string): MalformedContract {
    return new MalformedContract(
      `${this.where}: pattern ${JSON.stringify(this.cps.join(""))} ${why} (at code point ${this.i})`,
    );
  }

  peek(): string | undefined {
    return this.cps[this.i];
  }

  pattern(depth: number): void {
    this.branch(depth);
    while (this.peek() === "|") {
      this.i += 1;
      this.branch(depth);
    }
  }

  branch(depth: number): void {
    for (;;) {
      const c = this.peek();
      if (c === undefined || c === "|") return;
      if (c === ")") {
        if (depth === 0) throw this.refuse("has an unmatched ')'");
        return;
      }
      this.piece();
    }
  }

  piece(): void {
    const c = this.peek() as string;
    if (c === "(") {
      if (this.cps.slice(this.i, this.i + 3).join("") !== "(?:") throw this.refuse("has a group other than '(?:'");
      this.i += 3;
      this.pattern(1);
      if (this.peek() !== ")") throw this.refuse("has an unmatched '('");
      this.i += 1;
    } else if (c === "[") {
      this.klass();
    } else if (c === "\\") {
      this.i += 1;
      const e = this.peek();
      if (e === undefined || !SPECIAL.has(e)) throw this.refuse("has an escape outside the portable subset");
      this.i += 1;
    } else if (QUANTIFIERS.has(c) || c === "{") {
      throw this.refuse("has a quantifier with nothing to quantify");
    } else if (SPECIAL.has(c) && c !== ".") {
      throw this.refuse(`has '${c}' outside the portable subset`);
    } else {
      this.i += 1;
    }
    this.quantifier();
  }

  quantifier(): void {
    const c = this.peek();
    if (c !== undefined && QUANTIFIERS.has(c)) {
      this.i += 1;
    } else if (c === "{") {
      this.i += 1;
      const low = this.digits();
      let high = low;
      if (this.peek() === ",") {
        this.i += 1;
        high = this.digits();
      }
      if (this.peek() !== "}") throw this.refuse("has a malformed '{...}' quantifier");
      this.i += 1;
      if (low > high) throw this.refuse("has a quantifier whose lower bound exceeds its upper");
    }
  }

  digits(): number {
    const start = this.i;
    for (let c = this.peek(); c !== undefined && c >= "0" && c <= "9"; c = this.peek()) this.i += 1;
    if (start === this.i) throw this.refuse("has a malformed '{...}' quantifier");
    const value = Number(this.cps.slice(start, this.i).join(""));
    if (value > MAX_BOUND) throw this.refuse(`has a repetition bound above ${MAX_BOUND}`);
    return value;
  }

  klass(): void {
    this.i += 1;
    if (this.peek() === "^") this.i += 1;
    let items = 0;
    for (;;) {
      const c = this.peek();
      if (c === undefined) throw this.refuse("has an unmatched '['");
      if (c === "]") break;
      const low = this.classatom();
      if (this.peek() === "-") {
        this.i += 1;
        const high = this.classatom();
        if ((low.codePointAt(0) as number) > (high.codePointAt(0) as number)) {
          throw this.refuse("has a range whose low code point exceeds its high");
        }
      }
      items += 1;
    }
    if (items === 0) throw this.refuse("has an empty character class");
    this.i += 1;
  }

  classatom(): string {
    const c = this.peek();
    if (c === undefined) throw this.refuse("has an unmatched '['");
    if (c === "\\") {
      this.i += 1;
      const e = this.peek();
      if (e === undefined || !CLASS_SPECIAL.has(e)) throw this.refuse("has an escape outside the portable subset");
      this.i += 1;
      return e;
    }
    if (DOUBLED.has(c) && this.cps[this.i + 1] === c) {
      throw this.refuse(`has '${c}${c}' in a character class, which engines read as a set operation`);
    }
    if (CLASS_SPECIAL.has(c) || c === "[") throw this.refuse(`has '${c}' unescaped in a character class`);
    this.i += 1;
    return c;
  }
}

/** Refuse a pattern outside the portable subset, naming `where`. */
export function checkPortablePattern(pattern: string, where: string): void {
  if (pattern.normalize("NFC") !== pattern) {
    throw new MalformedContract(`${where}: pattern ${JSON.stringify(pattern)} is not NFC`);
  }
  const walk = new Walk(pattern, where);
  walk.pattern(0);
  if (walk.peek() !== undefined) throw walk.refuse("has an unmatched ')'");
}

/** Check `pattern`, then compile it with the one fixed engine option set. */
export function compilePortable(pattern: string): RegExp {
  checkPortablePattern(pattern, "pattern");
  return new RegExp(`^(?:${pattern})$`, "su");
}

/**
 * A per-sort identifier class: a literal prefix and a portable pattern.
 *
 * The prefix is informational to the kernel. The only check is that the pattern
 * text begins with the prefix and that the prefix holds no pattern metacharacter;
 * the pattern as a whole may still admit terms without it.
 */
export class IdentifierClass {
  private readonly compiled: RegExp;

  constructor(
    readonly prefix: string,
    readonly pattern: string,
  ) {
    const where = `identifier class ${JSON.stringify(prefix)}`;
    if (prefix === "") throw new MalformedContract(`${where}: the prefix is empty`);
    if (Array.from(prefix).some((c) => SPECIAL.has(c))) {
      throw new MalformedContract(`${where}: the prefix contains a pattern metacharacter`);
    }
    checkPortablePattern(pattern, where);
    if (!pattern.startsWith(prefix)) {
      throw new MalformedContract(`${where}: the pattern does not begin with the prefix as literal text`);
    }
    this.compiled = compilePortable(pattern);
  }

  matches(term: string): boolean {
    return this.compiled.test(term.normalize("NFC"));
  }
}
