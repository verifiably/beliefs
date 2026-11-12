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
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml
from nodes.core.node import Node

from beliefs import rules, stored
from beliefs.adapter import WorkflowDefinition
from beliefs.dependencies import HeldRecords
from beliefs.replay import CONTENT_EQUALITY
from beliefs.spec import Deterministic, FrozenSpec, SpecDraft, SpecInput, freeze
from reproduction import paths, state, world

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


def code_root() -> Path:
    return paths.WORK / "bundle" / "analysis"


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
    bundle = code_root()
    (bundle / "workflow").mkdir(parents=True, exist_ok=True)
    for name in ("assoc.py", "labels.py"):
        shutil.copyfile(CODE_ROOT / name, bundle / name)
    (bundle / "workflow/Snakefile").write_bytes(text.encode())
    return text.encode()


def held_rules() -> dict:
    """The driver's identities, bound to the kernel's implementations.
    The record's spec identity is unchanged:
    `freeze` digests (rule identity, implementation identity) pairs, and both
    pairs are the ones the 2026-09-05 record carries.
    """
    return {INTERPRETATION_RULE: INTERPRETATION, EQUIVALENCE_RULE: EQUIVALENCE}


def definition() -> WorkflowDefinition:
    return WorkflowDefinition(snakefile=(code_root() / "workflow/Snakefile").read_bytes(), family_streams={})


RELOCATED_CLAUSE = (
    "prose applicability clause 'whose ids carry a stage token and whose value is finite' refused at retyping "
    "(no declared dimension); re-authored in `method` as estimator behaviour — the estimator refuses a non-finite "
    "value as malformed input, it does not exclude the sample — an authored judgment"
)


@dataclass(frozen=True)
class _HeldRecords:
    """The author's captured record reader; this empirical contrast has no eligibility lookups."""

    view: object

    def holds(self, id: str) -> bool:
        return self.view.holds(id)

    def read(self, id: str) -> Node:
        return self.view.get(id)

    def retraction_in_force(self, id: str) -> bool:
        return False

    def observation_held(self, digest: str) -> bool:
        return False

    def crosswalks(self, a: str, b: str) -> tuple[str, ...]:
        return ()


def _context():
    from beliefs.corpus import ReadView
    from reproduction import hold, type_target, vocabulary

    st = state.load()
    inputs = hold.recover_inputs()
    profile = vocabulary.profile()
    claim = type_target.typed(inputs, profile)
    records = cast(HeldRecords, _HeldRecords(ReadView.opened_at(paths.CORPUS_ROOT)))
    return st, inputs, profile, claim, vocabulary.snapshot(), records


def _draft(context) -> SpecDraft:
    from reproduction import type_target

    st, inputs, profile, claim, snapshot, records = context
    parser, estimator = type_target.implementation_digests(code_root())
    if (parser, estimator) != type_target.implementation_digests():
        raise RuntimeError("analysis bundle differs from the authored parser/estimator")
    estimand, applicability = type_target.estimand(
        inputs,
        profile=profile,
        claim=claim,
        records=records,
        snapshot=snapshot,
        assay_id=st["assay_ref"],
        grouping_rule_id=st["grouping_rule_ref"],
        parser_digest=parser,
        estimator_digest=estimator,
    )
    return SpecDraft(
        target=st["proposition_ref"],
        estimand=estimand,
        method="Engineering demonstration: gene RNA PD versus NDMM, unpaired half-tie probability of superiority; z/p diagnostics have no tie correction or computed interval.",
        assumptions="Source pairing is not modeled; independence and assay validation remain unestablished. The frozen procedure-validity assumption is conditional, not evidence.",
        falsification="No difference at alpha .05 or a difference opposite the selected positive orientation.",
        input_roles=(SpecInput(role="observes", dataset=st["dataset_address"], mode="observation"),),
        applicability=applicability,
        interpretation_rule=INTERPRETATION_RULE,
        equivalence_rule=EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
        registers=tuple(st["registers"]),
        standing="empirical",
        model=None,
    )


def draft() -> SpecDraft:
    return _draft(_context())


def frozen() -> FrozenSpec:
    context = _context()
    st, _, profile, claim, _, records = context
    return freeze(
        _draft(context),
        held_rules=held_rules(),
        rule_procedures={INTERPRETATION_RULE: st["estimator_ref"]},
        profile=profile,
        claim=claim,
        records=records,
    )


def spec_record(spec: FrozenSpec) -> Node:
    """The kernel's own builder."""
    return stored.analysis_spec_node(spec)


def main() -> int:
    render_snakefile()
    spec = frozen()
    minted = world.open_writer().add(spec_record(spec))
    state.save(spec_identity=spec.identity, spec_ref=minted.id, held_name=Path(state.load()["held_file"]).name)
    from beliefs.applicability import applicability_projection
    from beliefs.estimand import estimand_projection
    from beliefs.identity import v1

    target = yaml.safe_load(paths.TARGET.read_text())
    target.update(
        estimand=estimand_projection(spec.estimand),
        applicability=applicability_projection(spec.applicability),
        estimator_procedure=state.load()["estimator_ref"],
    )
    paths.TARGET.write_bytes(v1.encode(target))
    print(f"frozen spec {spec.identity} targeting {spec.target}; record {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
