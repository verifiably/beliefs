"""`state.json`: corpus refs, identities and paths only — never evidence.

Steps 11 and 12 (composite claims) add seven keys, all of that kind:

- `spine_ref` — the `h1-prognosis` spine proposition minted by `compose`;
- `composite_ref`, `composite_identity` — the composite's corpus ref and the
  content identity `build_composite` stamped it with;
- `composite_receipt` — the node receipt as `{node label: outcome tag}`, or
  `composite_refusal` in its place when `build_composite` refused;
- `reading_rows`, `reading_equal` — each member row as
  `{ref: (sign, answer class, identification)}`, and whether the second
  process's encoded reading is byte-equal to the first's;
- `cut31_corpus_state` — what the corpus state moved aside at recreation
  answers when it is opened read-only under the successor profile: the
  `audit_corpus` findings, its corpus id, its base pin and how many of its
  records the audit read.
"""

from __future__ import annotations

import json

from reproduction import paths


def load() -> dict:
    return json.loads(paths.STATE.read_text()) if paths.STATE.exists() else {}


def save(**fields: object) -> None:
    current = load()
    current.update(fields)
    paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    paths.STATE.write_text(json.dumps(current, indent=2, sort_keys=True))
