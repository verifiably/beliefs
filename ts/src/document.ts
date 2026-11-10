/**
 * Contract documents are read through one reader, which both languages share.
 *
 * This side reads with the `yaml` package's YAML 1.2 core schema; the Python
 * reader (`beliefs.contract.document`) replaces PyYAML's YAML 1.1 resolvers
 * with the same schema, and `fixtures/document-reading-v1.json` is the oracle
 * both are tested against. Under the core schema `010` is 10, `0o10` is 8,
 * `0x10` is 16, only `true`/`false` (in three spellings) are booleans, and
 * `yes`, `on`, `0b11`, `1_000`, `12:30`, `2026-01-01` and `<<` are strings.
 *
 * Some readings the two languages cannot share are refused here as in Python:
 *
 * - a float (`24.0`, `1e3`, `.inf`): no contract field carries one, and a
 *   JavaScript number cannot tell `24.0` from `24`, which Python can;
 * - an integer outside the safe range ±(2^53 - 1), which a number cannot hold
 *   exactly, and one whose digit run (after any sign or `0o`/`0x` prefix) is
 *   longer than 16 characters, leading zeros included;
 * - an explicit tag (`!!str 10`, `!!binary ...`, `! x`), whose sets differ;
 * - a `%YAML` or `%TAG` directive, which would switch this reader's schema;
 * - a mapping key that is not a string (a JavaScript object would stringify it);
 * - a duplicate mapping key, and a duplicate anchor name (PyYAML refuses one,
 *   this package would rebind it).
 */

import { isAlias, isScalar, parseDocument, visit } from "yaml";
import type { Node as YamlNode } from "yaml";
import { MalformedContract } from "./errors.js";

/** The core schema's integer forms; any other number the package resolves is a float. */
const CORE_INT = /^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$/;
/** As Python, which must bound the run before `int()`: past its digit limit `int()` raises outside the refusal family. */
const MAX_DIGIT_RUN = 16;
const DEFAULT_TAG_HANDLES: Readonly<Record<string, string>> = { "!!": "tag:yaml.org,2002:" };

export function readDocument(text: string, source: string): unknown {
  const document = parseDocument(text, { version: "1.2", schema: "core", uniqueKeys: true });
  const [error] = document.errors;
  if (error !== undefined) throw new MalformedContract(`${source}: not well-formed YAML: ${error.message}`);
  const [warning] = document.warnings;
  if (warning !== undefined) throw new MalformedContract(`${source}: not well-formed YAML: ${warning.message}`);
  const handles = Object.entries(document.directives?.tags ?? {});
  if (
    document.directives?.yaml.explicit ||
    handles.length !== Object.keys(DEFAULT_TAG_HANDLES).length ||
    handles.some(([handle, prefix]) => DEFAULT_TAG_HANDLES[handle] !== prefix)
  ) {
    throw new MalformedContract(
      `${source}: a %YAML or %TAG directive is refused: the document is read under the YAML 1.2 core schema`,
    );
  }
  const anchors = new Set<string>();
  const refuse = (message: string): never => {
    throw new MalformedContract(`${source}: ${message}`);
  };
  visit(document, {
    Node(_key, node: YamlNode) {
      if (isAlias(node)) return;
      if (node.tag !== undefined) refuse(`an explicit tag ${JSON.stringify(node.tag)} is refused`);
      if (node.anchor !== undefined) {
        if (anchors.has(node.anchor)) refuse(`the anchor ${JSON.stringify(node.anchor)} is defined twice`);
        anchors.add(node.anchor);
      }
      if (isScalar(node) && typeof node.value === "number") {
        const written = node.source === undefined ? String(node.value) : String(node.source);
        if (!CORE_INT.test(written)) refuse(`the float ${written} is refused: no contract field carries a float`);
        const digits = /^0[ox]/.test(written) ? written.slice(2) : written.replace(/^[-+]/, "");
        if (digits.length > MAX_DIGIT_RUN)
          refuse(`the integer ${written.slice(0, 24)}… has a digit run longer than ${MAX_DIGIT_RUN} characters`);
        if (!Number.isSafeInteger(node.value))
          refuse(`the integer ${written} is outside ±(2^53 - 1), which both readers hold exactly`);
      }
    },
    Pair(_key, pair) {
      const key = pair.key;
      if (!isScalar(key) || typeof key.value !== "string") {
        refuse(`mapping key ${String(isScalar(key) ? key.value : key)} is not a string; refused`);
      }
    },
  });
  return document.toJS();
}
