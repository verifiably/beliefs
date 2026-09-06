"""Cut 17: 8 selected + 1 labeled = 9 units, carried by the arms below."""

from n2_arms import Arm, Sabotage

_PERMIT, _CORPUS, _BOUNDARY = "permit.py", "corpus.py", "boundary.py"
_HOLDINGS, _REGISTRY, _ROOT = "holdings/boundary.py", "world/registry.py", "root.py"

_P = "test_permit.py"
_S = "test_permit_boundary.py"
_C = "test_corpus_write.py"
_I = "test_import_bundle.py"
_B = "test_boundary.py"
_H = "test_holdings_boundary.py"
_A = "acceptance/test_permit_acceptance.py"

CUT17_ARMS = (
    Arm(
        row="E1a",
        asserts="a missing family is refused on the family before any kind",
        sabotage=Sabotage(
            module=_PERMIT,
            before='        if family not in self.permit.act_families:\n            raise PermitExceeded(PermitFact("family", family), self.permit.summary())\n',
            after="",
        ),
        checks=(
            f"{_P}::TestE1AuthorityRequire::test_a_missing_family_is_refused_on_the_family_before_any_kind",
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_family_refuses_and_writes_nothing",
            "test_permit_entry_points.py::test_e1_the_family_is_refused_with_no_effect[world.registry.py.World._terminal]",
        ),
    ),
    Arm(
        row="E1b",
        asserts="a governed kind the permit lacks is named, in the caller's order",
        sabotage=Sabotage(
            module=_PERMIT,
            before="                permitted = kind in self.permit.kinds",
            after="                permitted = True",
        ),
        checks=(
            f"{_P}::TestE1AuthorityRequire::test_the_first_missing_kind_in_the_callers_order_is_named",
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_kind_names_the_kind",
        ),
    ),
    Arm(
        row="E1d",
        asserts="an ungoverned kind needs the flag and the corpus-write family",
        sabotage=Sabotage(
            module=_PERMIT,
            before='                permitted = self.permit.ungoverned and family == "corpus-write"',
            after="                permitted = True",
        ),
        checks=(
            f"{_P}::TestE1AuthorityRequire::test_an_ungoverned_kind_needs_the_flag_and_the_corpus_write_family",
            f"{_A}::test_e1_an_ungoverned_kind_mints_under_the_full_permit_and_refuses_under_a_governed_one",
        ),
    ),
    Arm(
        row="E1c",
        asserts="the corpus add path requires before it writes",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        self._authority.require("corpus-write", (node.kind,))\n        with self._operation:\n            self._require_pins_agree()\n            self._refuse_family_kinds(node)\n            self._refuse(node)',
            after='        with self._operation:\n            self._require_pins_agree()\n            self._refuse_family_kinds(node)\n            self._refuse(node)',
        ),
        checks=(
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_family_refuses_and_writes_nothing",
            f"{_S}::test_every_entry_point_requires_before_it_writes",
        ),
    ),
    Arm(
        row="E1r",
        asserts="the relocation add seam requires before it writes",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        self.authority.require("corpus-write", (node.kind,))\n        self._preflight_add_locked(node, provenance=provenance)\n        return self._corpus.add(node)',
            after='        self._preflight_add_locked(node, provenance=provenance)\n        result = self._corpus.add(node)\n        self.authority.require("corpus-write", (node.kind,))\n        return result',
        ),
        checks=(
            "test_permit_entry_points.py::test_e1_the_family_is_refused_with_no_effect[corpus.py.CorpusWriter._add_locked]",
        ),
    ),
    Arm(
        row="E2a",
        asserts="a writer over a port bound to another authority refuses construction",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        if operation_port is not None and operation_port.authority != authority:",
            after="        if False:",
        ),
        checks=(f"{_C}::TestE2AuthorityBindsOnceAtConstruction::test_a_port_bound_to_another_authority_refuses_construction",),
    ),
    Arm(
        row="E3a",
        asserts="a retraction naming another actor is refused",
        sabotage=Sabotage(
            module=_CORPUS,
            before='            if isinstance(facet, dict) and facet.get("actor") != self._authority.actor:',
            after="            if False:",
        ),
        checks=("test_retract.py::test_e3_a_retraction_naming_another_actor_is_refused",),
    ),
    Arm(
        row="E3b",
        asserts="a run closure naming another actor is refused through add",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        if named != self._authority.actor:",
            after="        if False:",
        ),
        checks=(f"{_C}::TestE3TheActorIsBound::test_a_run_closure_naming_another_actor_is_refused_through_add",),
    ),
    Arm(
        row="E3c",
        asserts="the run intent carries the port's actor",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before="    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
            after='    actor = "tester"\n    if type(spec) is not FrozenSpec:',
        ),
        checks=(f"{_B}::test_e3_the_run_intent_carries_the_ports_actor",),
    ),
    Arm(
        row="E4a",
        asserts="an ambiguous kind without a selected route is refused",
        sabotage=Sabotage(
            module=_PERMIT,
            before='                raise ValueError(f"{kind!r} admits more than one route; the declaration must select one")',
            after="                route = sorted(admissible)[0]",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_an_ambiguous_kind_must_select_a_route",),
    ),
    Arm(
        row="E4b",
        asserts="an inadmissible route is refused",
        sabotage=Sabotage(
            module=_PERMIT,
            before="                if route not in admissible:",
            after="                if False:",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_a_selected_route_must_be_admissible",),
    ),
    Arm(
        row="E4c",
        asserts="publishes() is refused while publish is not a family",
        sabotage=Sabotage(
            module=_PERMIT,
            before='        raise ValueError("publish is not an act family")',
            after="        return cls(WritePermit(frozenset(), frozenset()))",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_publishes_is_refused_while_publish_is_not_a_family",),
    ),
    Arm(
        row="E5a",
        asserts="coverage is subset inclusion on both dimensions",
        sabotage=Sabotage(
            module=_PERMIT,
            before="        required.permit.kinds <= ceiling.kinds\n        and required.permit.act_families <= ceiling.act_families",
            after="        required.permit.act_families <= ceiling.act_families",
        ),
        checks=(f"{_P}::TestE5Coverage::test_coverage_is_subset_inclusion_on_both_dimensions",),
    ),
    Arm(
        row="E6a",
        asserts="a displaced check is caught statically",
        sabotage=Sabotage(
            module=_HOLDINGS,
            before='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    ctx.authority.require("holdings", ("holdings-observation",))\n    token = secrets.token_hex(16)\n    from beliefs.corpus import require_pins_agree\n\n    with ctx.seam.corpus_lock(ctx.observer_root):\n        require_pins_agree(ctx.observer_root, ctx.profile)\n        intent = ctx.seam.append_intent(\n            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)\n        )\n    return token, intent',
            after='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    token = secrets.token_hex(16)\n    from beliefs.corpus import require_pins_agree\n\n    with ctx.seam.corpus_lock(ctx.observer_root):\n        require_pins_agree(ctx.observer_root, ctx.profile)\n        intent = ctx.seam.append_intent(\n            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)\n        )\n    ctx.authority.require("holdings", ("holdings-observation",))\n    return token, intent',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6b",
        asserts="a removed check is caught statically",
        sabotage=Sabotage(
            module=_REGISTRY,
            before='    authority.require("registry")\n    state.registry = _scan_registry(world_root)',
            after="    state.registry = _scan_registry(world_root)",
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6c",
        asserts="a conditional check is caught statically",
        sabotage=Sabotage(
            module=_ROOT,
            before='    authority.require("lifecycle")\n    root = config.world_root',
            after='    if config is not None:\n        authority.require("lifecycle")\n    root = config.world_root',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6d",
        asserts="an effect before the check is caught statically",
        sabotage=Sabotage(
            module=_ROOT,
            before='    authority.require("lifecycle")\n    root = config.world_root\n    if root.exists() and not root.is_dir():\n        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a world root")\n    root.mkdir(parents=True, exist_ok=True)',
            after='    root = config.world_root\n    root.mkdir(parents=True, exist_ok=True)\n    authority.require("lifecycle")\n    if root.exists() and not root.is_dir():\n        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a world root")',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6e",
        asserts="a widened run handler is caught statically",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before="    except PermitExceeded as exceeded:\n        return RunRefused(\"permit-exceeded\", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
            after="    except WriteRefused as exceeded:\n        return RunRefused(\"permit-exceeded\", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E7a",
        asserts="a permit violation on the run boundary appends no intent and mints no report",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before='        return RunRefused("permit-exceeded", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:',
            after='        refused = _refused("permit-exceeded", "absent", port.authority.actor, observer, started_at, detail=str(exceeded))\n        port.execute(_report_plan(refused.report))\n        return refused\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:',
        ),
        checks=(
            f"{_B}::test_e7_a_permit_lacking_run_refuses_with_no_intent_and_no_report",
            f"{_A}::test_e7_the_run_boundary_refuses_with_no_intent_through_a_real_port",
        ),
    ),
    Arm(
        row="E3r",
        asserts="an operation intent refuses an actor other than the bound actor",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        if intent_actor != self.authority.actor:\n            raise ActorMismatch(\n                f"the operation intent names actor {intent_actor!r}, not the bound {self.authority.actor!r}"\n            )\n',
            after="",
        ),
        checks=(
            "test_relocation.py::test_append_operation_intent_refuses_a_foreign_actor_before_append",
        ),
    ),
    Arm(
        row="E7b",
        asserts="a holdings act under a lacking permit leaves both chains unchanged",
        sabotage=Sabotage(
            module=_PERMIT,
            before='        if family not in ACT_FAMILIES:\n            raise ValueError(f"{family!r} is not an act family")\n        if family not in self.permit.act_families:',
            after='        if family not in ACT_FAMILIES:\n            raise ValueError(f"{family!r} is not an act family")\n        if family == "holdings":\n            return\n        if family not in self.permit.act_families:',
        ),
        checks=(
            f"{_H}::test_e1_a_permit_lacking_the_observation_kind_refuses_write_before_any_store_effect",
            f"{_A}::test_e7_a_holdings_act_refuses_with_the_store_and_observer_chains_unchanged",
        ),
    ),
    Arm(
        row="E7r",
        asserts="relocation requires both writers before either intent",
        sabotage=Sabotage(
            module="relocation.py",
            before='        destination.authority.require("corpus-write", (node.kind, "act-report"))\n        source.authority.require("corpus-write", (node.kind, "act-report"))',
            after='        source.authority.require("corpus-write", (node.kind, "act-report"))',
        ),
        checks=(
            f"{_A}::test_e1_relocation_refuses_before_either_intent_then_succeeds",
        ),
    ),
    Arm(
        row="E8a",
        asserts="one unpermitted member refuses the bundle whole before the intent",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        self._authority.require(\n            "corpus-write", (*(record.kind for record in bundle if type(record) is Node), "act-report")\n        )',
            after='        self._authority.require("corpus-write", ("act-report",))',
        ),
        checks=(
            f"{_I}::test_e8_one_unpermitted_member_refuses_the_bundle_before_the_intent",
            f"{_A}::test_e8_an_unpermitted_member_refuses_the_bundle_with_the_chain_unchanged",
        ),
    ),
    Arm(
        row="K1",
        asserts="H4u1 succeeded: an established finding is published or the act fails loudly",
        sabotage=Sabotage(
            module=_HOLDINGS,
            before='        ctx.seam.publish_fulfilling(ctx.observer_root, plan, intent)',
            after='        pass  # established finding silently dropped',
        ),
        checks=("test_holdings_boundary.py::test_publication_failure_after_an_established_outcome_raises",),
    ),
)

_UNIT_OF_LETTERED = {f"E{n}{letter}": f"E{n}" for n in range(1, 9) for letter in "abcdefr"}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {f"E{n}": 1 for n in range(1, 9)}
LABELED_UNITS: tuple[str, ...] = ("K1",)
CO_CITED: dict[str, tuple[str, ...]] = {"K1": ("test_holdings_boundary.py::test_publication_failure_after_an_established_outcome_raises",)}
