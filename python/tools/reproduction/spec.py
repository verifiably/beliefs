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
from pathlib import Path

import yaml
from nodes.core.node import Node

from beliefs import rules, stored
from beliefs.adapter import WorkflowDefinition
from beliefs.replay import CONTENT_EQUALITY
from beliefs.spec import Deterministic, FrozenSpec, SpecDraft, SpecInput, freeze
from reproduction import findings, paths, state, world

CODE_ROOT = Path(__file__).with_name("analysis")  # bundle name: analysis/
TEMPLATE = Path(__file__).with_name("Snakefile.template")  # outside the code root: not bundled
SNAKEFILE = CODE_ROOT / "workflow" / "Snakefile"
ENTRYPOINT = "analysis/workflow/Snakefile"
TARGETS = ("outputs/stats.tsv", "outputs/outcome.txt")
OUTCOME_FILE = rules.OUTCOME_FILE
INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"
EQUIVALENCE_RULE = "content-identity-equality/v1"
OUTCOME_DIGESTS = {rules.outcome_digest(o): o for o in ("supported", "refuted", "inconclusive")}
INTERPRETATION = rules.OUTCOME_FILE_V1
EQUIVALENCE = CONTENT_EQUALITY


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


def held_rules() -> dict:
    """The driver's identities, bound to the kernel's implementations
    (session-routes design §5.2). The record's spec identity is unchanged:
    `freeze` digests (rule identity, implementation identity) pairs, and both
    pairs are the ones the 2026-09-05 record carries.
    """
    return {INTERPRETATION_RULE: INTERPRETATION, EQUIVALENCE_RULE: EQUIVALENCE}


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
    """The kernel's own builder (verification-publication design §7)."""
    return stored.analysis_spec_node(spec)


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
    print(f"frozen spec {spec.identity} targeting {spec.target}; record {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
