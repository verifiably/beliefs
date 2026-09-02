"""Derive a workflow job's seed and write the matching claim."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import cast

from beliefs.errors import MalformedClosure, SeedClaimMalformed
from beliefs.recipe import job_key
from beliefs.spec import SEED_DERIVATION_V1, derive_seed

CLAIM_DIRECTORY = ".seeds"


def _roots(config: Mapping[str, object]) -> dict[str, int]:
    if config.get("seed_derivation_rule") != SEED_DERIVATION_V1:
        raise MalformedClosure(f"the rendered config names no {SEED_DERIVATION_V1} seed plan")
    rendered = config.get("seed_roots")
    if not isinstance(rendered, Mapping) or not rendered:
        raise MalformedClosure("the rendered config carries no seed roots")
    roots: dict[str, int] = {}
    for stream, value in rendered.items():
        text = value if type(value) is str else str(value)
        if not text.lstrip("-").isdigit():
            raise MalformedClosure(f"seed root for stream {stream!r} is not an integer: {text!r}")
        roots[str(stream)] = int(text)
    return roots


def record_digest_of(record: Mapping[str, object]) -> str:
    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def bind(config: Mapping[str, object]) -> Callable[[object, object, str], int]:
    """Bind the engine's config once at Snakefile load."""
    roots = _roots(config)

    def seed(rule: object, wildcards: object, stream: str) -> int:
        if stream not in roots:
            raise MalformedClosure(f"stream {stream!r} has no rendered root")
        pairs = tuple(sorted((str(key), str(value)) for key, value in dict(cast(Mapping[object, object], wildcards)).items()))
        key = job_key(str(rule), pairs)
        value = derive_seed(roots[stream], key, stream)
        record = {
            "rule": str(rule),
            "wildcards": dict(pairs),
            "job_key": key,
            "stream": stream,
            "seed": value,
        }
        directory = Path(CLAIM_DIRECTORY)
        directory.mkdir(exist_ok=True)
        path = directory / f"{record_digest_of(record)}.json"
        try:
            handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise SeedClaimMalformed(f"a claim for {key}/{stream} was already written") from error
        with os.fdopen(handle, "w", encoding="utf-8") as claim:
            json.dump(record, claim, sort_keys=True, separators=(",", ":"))
        return value

    return seed
