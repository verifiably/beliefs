"""`state.json`: corpus refs, identities and paths only — never evidence."""

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
