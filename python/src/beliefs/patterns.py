"""The portable identifier-class pattern subset.

A pattern is a small regular-expression subset that Python's ``re`` and
JavaScript's ``RegExp`` read identically. Both implementations walk the same
grammar (``ts/src/patterns.ts``) and are held to one agreement oracle,
``fixtures/identifier-patterns-v1.json``.

    pattern   := branch ( "|" branch )*
    branch    := piece*
    piece     := atom quantifier?
    atom      := literal | "." | class | "(?:" pattern ")" | escape
    escape    := "\\" one of  \\ . [ ] ( ) { } | * + ? ^ $
    literal   := any code point except  \\ . [ ] ( ) { } | * + ? ^ $
    quantifier:= "*" | "+" | "?" | "{" digits "}" | "{" digits "," digits "}"
    class     := "[" "^"? classitem+ "]"
    classitem := classatom ( "-" classatom )?
    classatom := "\\" one of  \\ ] - ^   | any code point except  \\ [ ] - ^
                 (and no doubled & ~ | inside a class: engines read them as set operations)
    digits    := [0-9]+, at most 65535

Engine options are fixed, never authored: ``re.DOTALL`` with ``fullmatch`` here,
the ``s`` and ``u`` flags with ``^(?:...)$`` in TypeScript. Terms are matched
after NFC normalization.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from beliefs.errors import MalformedContract

_SPECIAL = frozenset("\\.[](){}|*+?^$")
_CLASS_SPECIAL = frozenset("\\]-^")
_QUANTIFIERS = frozenset("*+?")
_DIGITS = frozenset("0123456789")
_DOUBLED = frozenset("&~|")
_MAX_BOUND = 65535


class _Walk:
    def __init__(self, pattern: str, where: str) -> None:
        self.cps = list(pattern)
        self.i = 0
        self.where = where

    def refuse(self, why: str) -> MalformedContract:
        return MalformedContract(f"{self.where}: pattern {''.join(self.cps)!r} {why} (at code point {self.i})")

    def peek(self) -> str | None:
        return self.cps[self.i] if self.i < len(self.cps) else None

    def pattern(self, depth: int) -> None:
        self.branch(depth)
        while self.peek() == "|":
            self.i += 1
            self.branch(depth)

    def branch(self, depth: int) -> None:
        while True:
            c = self.peek()
            if c is None or c == "|":
                return
            if c == ")":
                if depth == 0:
                    raise self.refuse("has an unmatched ')'")
                return
            self.piece()

    def piece(self) -> None:
        c = self.peek()
        assert c is not None
        if c == "(":
            if self.cps[self.i : self.i + 3] != ["(", "?", ":"]:
                raise self.refuse("has a group other than '(?:'")
            self.i += 3
            self.pattern(1)
            if self.peek() != ")":
                raise self.refuse("has an unmatched '('")
            self.i += 1
        elif c == "[":
            self.klass()
        elif c == "\\":
            self.i += 1
            e = self.peek()
            if e is None or e not in _SPECIAL:
                raise self.refuse("has an escape outside the portable subset")
            self.i += 1
        elif c in _QUANTIFIERS or c == "{":
            raise self.refuse("has a quantifier with nothing to quantify")
        elif c in _SPECIAL and c != ".":
            raise self.refuse(f"has {c!r} outside the portable subset")
        else:
            self.i += 1
        self.quantifier()

    def quantifier(self) -> None:
        c = self.peek()
        if c in _QUANTIFIERS:
            self.i += 1
        elif c == "{":
            self.i += 1
            low = self.digits()
            high = low
            if self.peek() == ",":
                self.i += 1
                high = self.digits()
            if self.peek() != "}":
                raise self.refuse("has a malformed '{...}' quantifier")
            self.i += 1
            if low > high:
                raise self.refuse("has a quantifier whose lower bound exceeds its upper")

    def digits(self) -> int:
        start = self.i
        while (c := self.peek()) is not None and c in _DIGITS:
            self.i += 1
        if start == self.i:
            raise self.refuse("has a malformed '{...}' quantifier")
        value = int("".join(self.cps[start : self.i]))
        if value > _MAX_BOUND:
            raise self.refuse(f"has a repetition bound above {_MAX_BOUND}")
        return value

    def klass(self) -> None:
        self.i += 1
        if self.peek() == "^":
            self.i += 1
        items = 0
        while True:
            c = self.peek()
            if c is None:
                raise self.refuse("has an unmatched '['")
            if c == "]":
                break
            low = self.classatom()
            if self.peek() == "-":
                self.i += 1
                high = self.classatom()
                if ord(low) > ord(high):
                    raise self.refuse("has a range whose low code point exceeds its high")
            items += 1
        if items == 0:
            raise self.refuse("has an empty character class")
        self.i += 1

    def classatom(self) -> str:
        c = self.peek()
        if c is None:
            raise self.refuse("has an unmatched '['")
        if c == "\\":
            self.i += 1
            e = self.peek()
            if e is None or e not in _CLASS_SPECIAL:
                raise self.refuse("has an escape outside the portable subset")
            self.i += 1
            return e
        if c in _CLASS_SPECIAL or c == "[":
            raise self.refuse(f"has {c!r} unescaped in a character class")
        if c in _DOUBLED and self.cps[self.i + 1 : self.i + 2] == [c]:
            raise self.refuse(f"has {c + c!r} in a character class, which engines read as a set operation")
        self.i += 1
        return c


def check_portable_pattern(pattern: str, *, where: str) -> None:
    """Refuse a pattern outside the portable subset, naming ``where``."""
    if unicodedata.normalize("NFC", pattern) != pattern:
        raise MalformedContract(f"{where}: pattern {pattern!r} is not NFC")
    walk = _Walk(pattern, where)
    walk.pattern(0)
    if walk.peek() is not None:
        raise walk.refuse("has an unmatched ')'")


def compile_portable(pattern: str) -> re.Pattern[str]:
    """Check ``pattern``, then compile it with the one fixed engine option."""
    check_portable_pattern(pattern, where="pattern")
    return re.compile(pattern, re.DOTALL)


@dataclass(frozen=True)
class IdentifierClass:
    """A per-sort identifier class: a literal ``prefix`` and a portable pattern.

    The prefix is informational to the kernel. The only check is that the
    pattern text begins with the prefix and that the prefix holds no pattern
    metacharacter; the pattern as a whole may still admit terms without it.
    """

    prefix: str
    pattern: str

    def __post_init__(self) -> None:
        where = f"identifier class {self.prefix!r}"
        if not self.prefix:
            raise MalformedContract(f"{where}: the prefix is empty")
        if any(c in _SPECIAL for c in self.prefix):
            raise MalformedContract(f"{where}: the prefix contains a pattern metacharacter")
        check_portable_pattern(self.pattern, where=where)
        if not self.pattern.startswith(self.prefix):
            raise MalformedContract(f"{where}: the pattern does not begin with the prefix as literal text")
        object.__setattr__(self, "_compiled", compile_portable(self.pattern))

    def matches(self, term: str) -> bool:
        compiled: re.Pattern[str] = object.__getattribute__(self, "_compiled")
        return compiled.fullmatch(unicodedata.normalize("NFC", term)) is not None
