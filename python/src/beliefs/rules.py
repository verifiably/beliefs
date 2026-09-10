"""Reference rule implementations keyed by permanent kernel rule identity."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from types import MappingProxyType

from beliefs.recipe import ResultManifest
from beliefs.replay import CONTENT_EQUALITY, EquivalenceImplementation
from beliefs.spec import RuleFixture, RuleImplementation

__all__ = [
    "CONTENT_IDENTITY_RULE",
    "OUTCOMES",
    "OUTCOME_FILE",
    "OUTCOME_FILE_RULE",
    "OUTCOME_FILE_V1",
    "REFERENCE_RULES",
    "interpret_outcome_file",
    "outcome_digest",
]

OUTCOME_FILE = "outputs/outcome.txt"
OUTCOME_FILE_RULE = "beliefs/outcome-file/v1"
CONTENT_IDENTITY_RULE = "beliefs/content-identity-equality/v1"
OUTCOMES = ("supported", "refuted", "inconclusive")


def outcome_digest(outcome: str) -> str:
    """Return the digest of the canonical outcome line: the word and newline."""
    return "sha256:" + sha256((outcome + "\n").encode()).hexdigest()


_OUTCOME_BY_DIGEST: Mapping[str, str] = MappingProxyType({outcome_digest(outcome): outcome for outcome in OUTCOMES})


def interpret_outcome_file(manifest: ResultManifest) -> dict[str, str]:
    """Interpret the canonical outcome file named by a result manifest."""
    outputs = dict(manifest.outputs)
    if OUTCOME_FILE not in outputs:
        raise ValueError(f"the result manifest carries no {OUTCOME_FILE}")
    digest = outputs[OUTCOME_FILE]
    if digest not in _OUTCOME_BY_DIGEST:
        raise ValueError(f"{OUTCOME_FILE} digest {digest} is none of the canonical outcome lines")
    return {"outcome": _OUTCOME_BY_DIGEST[digest]}


def _manifest(outcome: str) -> ResultManifest:
    return ResultManifest(outputs=((OUTCOME_FILE, outcome_digest(outcome)),))


OUTCOME_FILE_V1 = RuleImplementation(
    identity="impl-outcome-file-1",
    evaluate=interpret_outcome_file,
    fixtures=tuple(RuleFixture(arguments=(_manifest(outcome),), expected={"outcome": outcome}) for outcome in OUTCOMES),
)

REFERENCE_RULES: Mapping[str, RuleImplementation | EquivalenceImplementation] = MappingProxyType(
    {OUTCOME_FILE_RULE: OUTCOME_FILE_V1, CONTENT_IDENTITY_RULE: CONTENT_EQUALITY}
)
