"""Contract documents are loaded through one loader that refuses duplicate
mapping keys at every depth (facet-contracts design §3.7).

PyYAML's `safe_load` keeps the *last* of two equal keys, so a duplicate facet,
field, kind or relation declaration would vanish before compilation reached
D8's collision check. The TypeScript side's `yaml` parser refuses duplicates by
default; this loader is the Python half of that agreement.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from yaml.constructor import ConstructorError

from beliefs.errors import MalformedContract

__all__ = ["load_document", "parse_document"]


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
        seen: set[str] = set()
        for key_node, _value in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark, f"mapping key {key!r} is not a string", key_node.start_mark
                )
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark, f"duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return cast(dict[object, object], super().construct_mapping(node, deep=deep))


def parse_document(text: str, *, source: str) -> object:
    """Parse YAML text, refusing duplicate keys and parser errors as `MalformedContract`."""
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    except ConstructorError as exc:
        problem = str(exc.problem or "")
        if "duplicate key" in problem or "is not a string" in problem:
            raise MalformedContract(f"{source}: {problem}; refused, never kept last (§3.7)") from exc
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc
    except yaml.YAMLError as exc:
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc


def load_document(path: Path, *, source: str) -> object:
    return parse_document(Path(path).read_text(encoding="utf-8"), source=source)
