"""Cut 4's fixture acts.

Three acts do this cut's construction work, and only the first is portable:

* the **raw filesystem write** — §4.2.1's untrusted import. A fixture act and
  never a slice operation: it is how S7's corpus-check half, S8's negative,
  R19(d)/(e)'s read-side nondetection, R22's at-the-address forgery and R23's
  basis/composition disagreement are built at all. Nothing in `beliefs` writes
  this way;
* the **durable mint** through the add path on the certified tuple, walked back
  out through the read surface after reload — the acceptance command's;
* the **uncertified-tuple refusal** — also the acceptance command's.

**A raw write is invisible to a live corpus**, which indexes at construction.
Every assertion about one reads through a **fresh** facade, which is what
`reopen` is for: reconstruction from disk is the recovery posture the seam
names, and it is the read this cut actually runs.
"""

from __future__ import annotations

from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.ids import NodeId
from nodes.core.node import Node

from beliefs.corpus import ReadView

__all__ = ["path_for", "raw_write", "reopen"]


def path_for(root: Path, node_id: str) -> Path:
    """Where the substrate keeps a node — the store's own rule, restated here
    because a raw write by definition does not go through the store."""
    parsed = NodeId.parse(node_id)
    return Path(root) / parsed.kind / f"{parsed.slug.replace(':', '__')}.md"


def raw_write(root: Path, node: Node) -> Path:
    """Write a node with a plain filesystem call, behind every boundary.

    Nothing static distinguishes this from writing any other file, which is
    exactly what S8's negative pins: the capability boundary is complete over
    the paths that go through `nodes` at all, and this one does not.
    """
    target = path_for(root, node.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(node_to_markdown(node), encoding="utf-8")
    return target


def reopen(root: Path) -> ReadView:
    """A fresh read facade over what is on disk right now."""
    return ReadView.opened_at(Path(root))
