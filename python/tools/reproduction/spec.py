"""Step 4: render the workflow, freeze the analysis spec, and mint its record.

Three facts fix this module's shape: the interpretation rule reads a
`ResultManifest` of output digests, not bytes, so the verdict is routed
through a canonical outcome file whose digest the rule maps; the staged
input keeps the held file's basename, so the Snakefile is rendered with it;
and the bundle keeps the code root's name, so the entrypoint is
`analysis/workflow/Snakefile`.
"""

from __future__ import annotations

import shutil
import sys
from decimal import Decimal
from functools import cache
from hashlib import sha256
from pathlib import Path

import yaml
from nodes.core.node import Node

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.recipe import ResultManifest
from beliefs.replay import EquivalenceImplementation
from beliefs.spec import Deterministic, FrozenSpec, RuleFixture, RuleImplementation, SpecDraft, SpecInput, freeze
from reproduction import findings, paths, state, world

CODE_ROOT = Path(__file__).with_name("analysis")  # bundle name: analysis/
TEMPLATE = Path(__file__).with_name("Snakefile.template")  # outside the code root: not bundled
SNAKEFILE = CODE_ROOT / "workflow" / "Snakefile"
ENTRYPOINT = "analysis/workflow/Snakefile"
TARGETS = ("outputs/stats.tsv", "outputs/outcome.txt")
OUTCOME_FILE = "outputs/outcome.txt"
INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"
EQUIVALENCE_RULE = "content-identity-equality/v1"
OUTCOME_DIGESTS = {
    "sha256:" + sha256((o + "\n").encode()).hexdigest(): o for o in ("supported", "refuted", "inconclusive")
}


def render_snakefile() -> bytes:
    target = yaml.safe_load(paths.TARGET.read_text())
    values = {
        "HELD_NAME": Path(state.load()["held_file"]).name,
        "VALUE_ROW": target["value_row"],
        "GROUP_SEPARATOR": target["group_separator"],
        "POSITIVE_LEVEL": target["positive_level"],
    }
    text = TEMPLATE.read_text()
    for key, value in values.items():
        text = text.replace("{" + key + "}", str(value))
    SNAKEFILE.parent.mkdir(parents=True, exist_ok=True)
    SNAKEFILE.write_bytes(text.encode())
    shutil.rmtree(CODE_ROOT / "__pycache__", ignore_errors=True)  # keep the bundle to its two files
    return SNAKEFILE.read_bytes()


def _interpret(manifest: ResultManifest) -> dict:
    return {"outcome": OUTCOME_DIGESTS[dict(manifest.outputs)[OUTCOME_FILE]]}


@cache
def interpretation() -> RuleImplementation:
    supported = next(d for d, o in OUTCOME_DIGESTS.items() if o == "supported")
    return RuleImplementation(
        identity="impl-outcome-file-1",
        evaluate=_interpret,
        fixtures=(
            RuleFixture(
                arguments=(ResultManifest(outputs=((OUTCOME_FILE, supported),)),), expected={"outcome": "supported"}
            ),
        ),
    )


@cache
def equivalence() -> EquivalenceImplementation:
    return EquivalenceImplementation(
        identity="impl-eq-1",
        evaluate=lambda a, b: "passed" if a == b else "failed",
        fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),),
    )


def held_rules() -> dict:
    return {INTERPRETATION_RULE: interpretation(), EQUIVALENCE_RULE: equivalence()}


def definition() -> WorkflowDefinition:
    return WorkflowDefinition(snakefile=SNAKEFILE.read_bytes(), family_streams={})


def draft() -> SpecDraft:
    st = state.load()
    target = yaml.safe_load(paths.TARGET.read_text())
    return SpecDraft(
        target=st["proposition_ref"],
        estimand=(
            f"difference in {target['value_row_symbol']} ({target['value_row']}) expression between the "
            f"{target['positive_level']} and the other level of the sample-id stage token in {target['dataset_id']}"
        ),
        method="two-group rank comparison (Mann-Whitney U, normal approximation), standard library",
        assumptions="independent samples; the stage is a two-level factor carried by each sample id",
        falsification="no difference at alpha 0.05, or a difference opposite the proposition's polarity",
        input_roles=(SpecInput(role="observes", dataset=st["dataset_address"]),),
        applicability=f"samples of {target['dataset_id']} whose ids carry a stage token and whose value is finite",
        interpretation_rule=INTERPRETATION_RULE,
        equivalence_rule=EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
    )


@cache
def frozen() -> FrozenSpec:
    return freeze(draft(), held_rules=held_rules())


def spec_record(spec: FrozenSpec) -> Node:
    """`analysis-spec` is a stored kind (stored.py's kinds table; the import
    path validates its facet) but the kernel exports no builder or reader for
    it. This node carries the frozen members and the identity so the record
    is on disk; that no kernel function restores a FrozenSpec from it is a
    finding (Task 11)."""
    facet = {
        "identity": spec.identity,
        "target": spec.target,
        "estimand": spec.estimand,
        "method": spec.method,
        "assumptions": spec.assumptions,
        "falsification": spec.falsification,
        "input_roles": [{"role": e.role, "dataset": e.dataset} for e in spec.input_roles],
        "applicability": spec.applicability,
        "interpretation_rule": spec.interpretation_rule,
        "equivalence_rule": spec.equivalence_rule,
        "parameters": {k: str(v) for k, v in spec.parameters.items()},
        "nondeterminism": spec.nondeterminism.projection(),
        "rule_bindings": [list(p) for p in spec.rule_bindings],
    }
    # A governed kind: the writer refuses an unstamped record.
    # `stamp_semantic_identity` is the one construction authority for the stamp.
    return stored.stamp_semantic_identity(
        Node(
            id=f"analysis-spec:{spec.identity}",
            kind="analysis-spec",
            title=f"spec {spec.identity[:12]}",
            facets={"analysis-spec": facet},
            relations=[],
        )
    )


def main() -> int:
    render_snakefile()
    spec = frozen()
    minted = world.open_writer().add(spec_record(spec))
    state.save(spec_identity=spec.identity, spec_ref=minted.id, held_name=Path(state.load()["held_file"]).name)
    findings.record(
        4,
        "design-gap",
        "build_assessment hands the interpretation rule a ResultManifest of digests, not output bytes; "
        "the verdict is routed through a canonical outcome file whose digest the rule maps",
        filed="computation design (where an interpretation rule reads content)",
    )
    findings.record(
        4,
        "design-gap",
        "analysis-spec is a stored kind with no kernel builder or reader; the spec record was hand-built",
        filed="computation design / stored.py (spec record builder and restore)",
    )
    print(f"frozen spec {spec.identity} targeting {spec.target}; record {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
