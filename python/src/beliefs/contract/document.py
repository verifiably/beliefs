"""Contract documents are loaded through one reader, which both languages share.

The TypeScript side reads contracts with the `yaml` package's YAML 1.2 core
schema (`ts/src/document.ts`); this reader is the Python half of that
agreement, and `fixtures/document-reading-v1.json` is the oracle both are
tested against. PyYAML's `SafeLoader` reads YAML 1.1, where `010` is 8, `yes`
is true and `1_000` is 1000, so its implicit resolvers are replaced here by the
YAML 1.2 core schema's:

- null: `~`, `null`, `Null`, `NULL` and the empty scalar;
- bool: `true`, `True`, `TRUE`, `false`, `False`, `FALSE`;
- int: decimal `[-+]?[0-9]+` (a leading zero is decimal), `0o` octal, `0x` hex;
- anything else plain is a string: `yes`, `on`, `0b11`, `1_000`, `12:30`,
  `2026-01-01` and `<<` (no merge keys) included.

Some readings the two languages cannot share are refused in both:

- a float (`24.0`, `1e3`, `.inf`): no contract field carries one, and
  JavaScript reads `24.0` as the integer 24;
- an integer outside ±(2^53 - 1), which a JavaScript number cannot hold exactly;
- an explicit tag (`!!str 10`, `!!binary ...`, `! x`), whose sets differ;
- a `%YAML` or `%TAG` directive, which would switch the TypeScript reader's
  schema;
- a mapping key that is not a string;
- a duplicate mapping key at any depth (PyYAML would keep the last) and a
  duplicate anchor name (PyYAML refuses one; the `yaml` package rebinds it).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar, cast

import yaml
from yaml.constructor import ConstructorError
from yaml.events import AliasEvent

from beliefs.errors import MalformedContract

__all__ = ["load_document", "parse_document"]

_NULL = "tag:yaml.org,2002:null"
_BOOL = "tag:yaml.org,2002:bool"
_INT = "tag:yaml.org,2002:int"
_FLOAT = "tag:yaml.org,2002:float"
_MAX_SAFE_INTEGER = 2**53 - 1
_PREFIXED_RADIX = {"0o": 8, "0x": 16}


class _Refused(yaml.YAMLError):
    """A reading the two languages do not share, refused in both."""


class _CoreLoader(yaml.SafeLoader):
    """PyYAML's safe loader with the YAML 1.2 core schema's implicit resolvers in
    place of its YAML 1.1 ones. The class's own table, so `SafeLoader` is
    untouched; `\\Z`, not `$`, since Python's `$` also matches before a trailing
    newline."""

    yaml_implicit_resolvers: ClassVar[dict[str | None, list[tuple[str, re.Pattern[str]]]]] = {}

    def compose_document(self) -> yaml.Node | None:
        event = self.peek_event()
        if getattr(event, "version", None) is not None or getattr(event, "tags", None):
            raise _Refused("a %YAML or %TAG directive is refused: the document is read under the YAML 1.2 core schema")
        return cast(yaml.Node | None, super().compose_document())

    def compose_node(self, parent: yaml.Node | None, index: int) -> yaml.Node | None:
        event = self.peek_event()
        if not isinstance(event, AliasEvent) and getattr(event, "tag", None) is not None:
            raise _Refused(f"an explicit tag {event.tag!r} is refused: a contract scalar is read by its plain form")
        return cast(yaml.Node | None, super().compose_node(parent, index))

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
        seen: set[str] = set()
        for key_node, _value in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"mapping key {key!r} is not a string",
                    key_node.start_mark,
                )
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark, f"duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return cast(dict[object, object], super().construct_mapping(node, deep=deep))

    def construct_core_int(self, node: yaml.ScalarNode) -> int:
        text = str(self.construct_scalar(node))
        # Not `int(text, 0)`: under the core schema a leading zero is decimal.
        radix = _PREFIXED_RADIX.get(text[:2])
        value = int(text, 10) if radix is None else int(text[2:], radix)
        if abs(value) > _MAX_SAFE_INTEGER:
            raise _Refused(f"the integer {text} is outside ±(2^53 - 1), which both readers hold exactly")
        return value

    def construct_core_float(self, node: yaml.ScalarNode) -> float:
        raise _Refused(f"the float {self.construct_scalar(node)!s} is refused: no contract field carries a float")


_CoreLoader.add_implicit_resolver(_NULL, re.compile(r"(?:~|null|Null|NULL|)\Z"), None)
_CoreLoader.add_implicit_resolver(_BOOL, re.compile(r"(?:true|True|TRUE|false|False|FALSE)\Z"), None)
_CoreLoader.add_implicit_resolver(_INT, re.compile(r"(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)\Z"), None)
_CoreLoader.add_implicit_resolver(
    _FLOAT,
    re.compile(
        r"(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)[eE][-+]?[0-9]+"
        r"|[-+]?(?:\.[0-9]+|[0-9]+\.[0-9]*)"
        r"|[-+]?\.(?:inf|Inf|INF)|\.nan|\.NaN|\.NAN)\Z"
    ),
    None,
)
_CoreLoader.add_constructor(_INT, _CoreLoader.construct_core_int)
_CoreLoader.add_constructor(_FLOAT, _CoreLoader.construct_core_float)


def parse_document(text: str, *, source: str) -> object:
    """Parse YAML text under the shared reading, refusing as `MalformedContract`."""
    try:
        return yaml.load(text, Loader=_CoreLoader)
    except _Refused as exc:
        raise MalformedContract(f"{source}: {exc}") from exc
    except ConstructorError as exc:
        problem = str(exc.problem or "")
        if "duplicate key" in problem or "is not a string" in problem:
            raise MalformedContract(f"{source}: {problem}; refused, never kept last") from exc
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc
    except yaml.YAMLError as exc:
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc


def load_document(path: Path, *, source: str) -> object:
    return parse_document(Path(path).read_text(encoding="utf-8"), source=source)
