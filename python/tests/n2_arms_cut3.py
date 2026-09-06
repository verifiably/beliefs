"""Cut 3's selected arms, paired with the sabotage each must not survive.

Same doctrine as ``n2_arms.py`` (N2: every oracle row can fail), extended over
cut 3's selected rows. The deferred rows' doctrine stays exactly as the prior
cuts left it: this module neither changes their tables nor claims their arms.

Every ``before`` string below was reconciled against the final formatted merged
tree. Where a planning sketch no longer named the exact source, the replacement
is anchored to the current equivalent. Any inert candidate found by the harness
is replaced by an adjacent sabotage with the same semantic effect and recorded
in the task report, never silently accepted.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT3_ARMS"]


# --- G2a ---------------------------------------------------------------------

_G2a = [
    Arm(
        row="G2a",
        asserts="the boundary refuses before intent when no FrozenSpec is supplied",
        sabotage=Sabotage(
            module="boundary.py",
            before="    if type(spec) is not FrozenSpec:",
            after="    if False:",
        ),
        checks=(
            "test_boundary.py::test_g2a_a_run_naming_no_frozen_spec_is_refused_not_downgraded",
            "test_boundary.py::test_g2a_a_spec_frozen_mid_execution_is_refused_not_downgraded",
        ),
    ),
]


# --- G4 ----------------------------------------------------------------------

_G4 = [
    Arm(
        row="G4",
        asserts="an unreferenced successor to a recorded failed replay is refused",
        sabotage=Sabotage(
            module="spec.py",
            before=("    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:"),
            after="    if False:",
        ),
        checks=("test_spec.py::test_g4_an_unreferenced_successor_to_a_recorded_failed_replay_is_refused",),
    ),
]


# --- M2 ----------------------------------------------------------------------

_M2 = [
    Arm(
        row="M2",
        asserts="every role-partitioned input participates in the recipe and assessment identity path",
        sabotage=Sabotage(
            module="recipe.py",
            before='            "inputs": inputs,\n',
            after="",
        ),
        checks=(
            "test_recipe.py::test_m2_substituting_any_input_moves_the_assessment_identity_every_time",
            "test_recipe.py::test_r2_every_recipe_member_moves_the_run_address[inputs_content]",
        ),
    ),
    Arm(
        row="M2",
        asserts="an input outside the recipe shape's declared role partition is refused",
        sabotage=Sabotage(
            module="recipe.py",
            before="        if any(entry.role not in roles for entry in self.inputs):",
            after="        if False:",
        ),
        checks=("test_recipe.py::test_m2_an_input_no_declared_role_partition_covers_is_refused_not_ignored",),
    ),
]


# --- R1 ----------------------------------------------------------------------
# The clause is split by execution layer: the recipe arm disables value-level
# reconciliation; the boundary arm fabricates the missing output because
# build_manifest would otherwise refuse before RunClosure is reached.

_R1 = [
    Arm(
        row="R1",
        asserts="an incomplete closure is refused and no run value exists",
        sabotage=Sabotage(
            module="recipe.py",
            before="        if declared - supplied:",
            after="        if False:",
        ),
        checks=("test_recipe.py::test_r1_an_incomplete_closure_is_refused_and_no_run_value_exists",),
    ),
    Arm(
        row="R1",
        asserts="the boundary refuses rather than fabricating a missing declared output",
        sabotage=Sabotage(
            module="boundary.py",
            before=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs))"
            ),
            after=(
                "    for name in declared_outputs:\n"
                "        path = scratch / name\n"
                "        if not path.is_file():\n"
                "            path.parent.mkdir(parents=True, exist_ok=True)\n"
                "            path.touch()\n"
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs))"
            ),
        ),
        checks=("test_boundary.py::test_r21_manifest_missing_output_mints_no_run",),
    ),
    Arm(
        row="R1",
        asserts="unknown and attested placeholders are not representable as held run components",
        sabotage=Sabotage(
            module="recipe.py",
            before='    if value in ("", "unknown", "attested"):\n',
            after='    if value in ("", "unknown", "attested"):\n        return\n',
        ),
        checks=("test_recipe.py::test_r1_no_unknown_or_attested_component_is_representable",),
    ),
]


# --- R2 ----------------------------------------------------------------------

_R2 = [
    Arm(
        row="R2",
        asserts="the boundary policy is a recipe identity member",
        sabotage=Sabotage(
            module="recipe.py",
            before=(
                '            "boundary_policy": {\n'
                '                "identity": self.boundary_policy.identity,\n'
                '                "scope_rule": self.boundary_policy.scope_rule,\n'
                '                "capabilities": sorted(self.boundary_policy.capabilities),\n'
                "            },\n"
            ),
            after="",
        ),
        checks=("test_recipe.py::test_r2_every_recipe_member_moves_the_run_address[boundary_policy]",),
    ),
    Arm(
        row="R2",
        asserts="result and occurrence are run-address members, never recipe members",
        sabotage=Sabotage(
            module="recipe.py",
            before='                "occurrence": _occurrence_projection(self.occurrence),\n',
            after="",
        ),
        checks=("test_recipe.py::test_r2_the_result_and_each_occurrence_member_move_the_address",),
    ),
    Arm(
        row="R2",
        asserts="two executions remain distinct through their occurrence member",
        sabotage=Sabotage(
            module="recipe.py",
            before='                "occurrence": _occurrence_projection(self.occurrence),\n',
            after="",
        ),
        checks=("test_boundary.py::test_r3_two_executions_of_one_recipe_are_two_runs",),
    ),
]


# --- R3 ----------------------------------------------------------------------

_R3 = [
    Arm(
        row="R3",
        asserts="the boundary-minted event token separates otherwise identical executions",
        sabotage=Sabotage(
            module="boundary.py",
            before="    intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)",
            after='    intent = AssessmentRunIntent(spec.identity, "fixed-token", actor)',
        ),
        checks=("test_boundary.py::test_r3_identical_timestamp_actor_and_host_still_yield_distinct_addresses",),
    ),
]


# --- R4 ----------------------------------------------------------------------

_R4 = [
    Arm(
        row="R4",
        asserts="scope falls through to not-certified when no attested scope row matches",
        sabotage=Sabotage(
            module="replay.py",
            before='        return "independent-implementation"\n    return "not-certified"',
            after='        return "independent-implementation"\n    return "same-environment"',
        ),
        checks=(
            "test_replay.py::test_r4_negative_b_a_comment_change_is_not_certified_never_independent",
            "test_replay.py::test_r4_negative_c_a_different_spec_identity_is_not_certified",
        ),
    ),
    Arm(
        row="R4",
        asserts="independent implementation requires an explicit code-lineage certification",
        sabotage=Sabotage(
            module="replay.py",
            before="        and type(certification) is CodeLineageCertification\n",
            after="",
        ),
        checks=("test_replay.py::test_r4_independent_implementation_needs_all_four_conditions",),
    ),
]


# --- R5 ----------------------------------------------------------------------

_R5 = [
    Arm(
        row="R5",
        asserts="replay eligibility requires the corpus attribution holding the run",
        sabotage=Sabotage(
            module="replay.py",
            before=(
                "    return AVAILABLE if required <= resolvable_here and run.address() in attributions "
                "else NOT_AVAILABLE"
            ),
            after="    return AVAILABLE if required <= resolvable_here else NOT_AVAILABLE",
        ),
        checks=(
            "test_replay.py::test_r5_negative_b_removing_the_corpus_attribution_reads_not_available_never_an_unchanged_belief",
        ),
    ),
    Arm(
        row="R5",
        asserts="availability is absent from the belief-closure digest signature",
        sabotage=Sabotage(
            module="closure.py",
            before="    proposition: str,\n",
            after="    proposition: str,\n    availability: tuple = (),\n",
        ),
        checks=("test_replay.py::test_r5_g9_unreachable_bytes_with_a_held_copy_move_none_of_the_three",),
    ),
    Arm(
        row="R5",
        asserts="admission heldness is digest-based and never filtered to a local location",
        sabotage=Sabotage(
            module="admission.py",
            before="        supplied = observations.get(address, ()) if address is not None else ()",
            after=(
                "        supplied = tuple(observation for observation in observations.get(address, ()) "
                'if observation.location.startswith("repo://")) if address is not None else ()'
            ),
        ),
        checks=("test_replay.py::test_r5_g9_unreachable_bytes_with_a_held_copy_move_none_of_the_three",),
    ),
]


# --- R6 ----------------------------------------------------------------------

_R6 = [
    Arm(
        row="R6",
        asserts="an unavailable run cannot be replayed into a verification or state change",
        sabotage=Sabotage(
            module="replay.py",
            before="    recipe = run.recipe\n",
            after="    return AVAILABLE\n    recipe = run.recipe\n",
        ),
        checks=("test_replay.py::test_r6_an_unreplayable_run_creates_no_verification_and_changes_no_state",),
    ),
]


# --- R7 ----------------------------------------------------------------------

_R7 = [
    Arm(
        row="R7",
        asserts="an assessment spec with no target is refused",
        sabotage=Sabotage(
            module="spec.py",
            before="    if not draft.target:",
            after="    if False:",
        ),
        checks=("test_spec.py::test_r7_an_assessment_spec_with_no_target_is_refused",),
    ),
    Arm(
        row="R7",
        asserts="a dataset-production run cannot have an assesses descendant",
        sabotage=Sabotage(
            module="assess.py",
            before='    if run.recipe.shape == "dataset-production":',
            after="    if False:",
        ),
        checks=("test_assess.py::test_r7_a_dataset_production_run_with_an_assesses_descendant_is_refused",),
    ),
    Arm(
        row="R7",
        asserts="reads inputs never become observes inputs while bridging a closure to admission",
        sabotage=Sabotage(
            module="assess.py",
            before="                role=entry.role,\n",
            after='                role="observes" if entry.role == "reads" else entry.role,\n',
        ),
        checks=("test_assess.py::test_r7_zero_observes_inputs_admit_nothing_at_any_quantity_of_reads",),
    ),
]


# --- R8 ----------------------------------------------------------------------
# One minting defect, split by test module so neither check can hide the other.

_R8 = [
    Arm(
        row="R8",
        asserts="editing the equivalence rule mints a successor referencing the original spec",
        sabotage=Sabotage(
            module="spec.py",
            before="    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
            after="    return freeze(draft, held_rules=held_rules, supersedes=None)",
        ),
        checks=("test_spec.py::test_r8_editing_the_equivalence_rule_mints_a_successor_that_references",),
    ),
    Arm(
        row="R8",
        asserts="a post-result rule change remains a referencing successor, never an in-place choice",
        sabotage=Sabotage(
            module="spec.py",
            before="    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
            after="    return freeze(draft, held_rules=held_rules, supersedes=None)",
        ),
        checks=("test_verify.py::test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen",),
    ),
]


# --- R9 ----------------------------------------------------------------------

_R9 = [
    Arm(
        row="R9",
        asserts="missing, unreadable, and reader-failing outputs yield inconclusive",
        sabotage=Sabotage(
            module="replay.py",
            before=(
                "        except Exception:  # noqa: BLE001 — any artifact-reader or payload failure is inconclusive\n"
                '            return "inconclusive"'
            ),
            after=(
                "        except Exception:  # noqa: BLE001 — any artifact-reader or payload failure is inconclusive\n"
                '            return "failed"'
            ),
        ),
        checks=(
            "test_replay.py::test_r9_a_missing_output_yields_inconclusive",
            "test_replay.py::test_r9_an_unreadable_output_yields_inconclusive",
            "test_replay.py::test_r9_a_reader_error_yields_inconclusive",
        ),
    ),
]


# --- R10 ---------------------------------------------------------------------

_R10 = [
    Arm(
        row="R10",
        asserts="URL-valued inputs are acquisition requests and are refused before run intent",
        sabotage=Sabotage(
            module="boundary.py",
            before="    if any(_is_acquisition(address) for address in addresses):",
            after="    if False:",
        ),
        checks=("test_boundary.py::test_r10_a_url_valued_input_is_refused_as_a_run_input",),
    ),
]


# --- R11 ---------------------------------------------------------------------

_R11 = [
    Arm(
        row="R11",
        asserts="dataset-production equivalence is exact content equality, not an always-pass evaluator",
        sabotage=Sabotage(
            module="replay.py",
            before=(
                'DATASET_CONTENT_EQUALITY = EquivalenceImplementation("impl-dataset-eq-1", _manifest_equality, ())'
            ),
            after=(
                'DATASET_CONTENT_EQUALITY = EquivalenceImplementation("impl-dataset-eq-1", '
                'lambda original, replayed: "passed", ())'
            ),
        ),
        checks=("test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four",),
    ),
    Arm(
        row="R11",
        asserts="a dataset-production verification carries the production shape and no assessment edge",
        sabotage=Sabotage(
            module="verify.py",
            before="        verification_type = DatasetProductionVerification",
            after="        verification_type = AssessmentVerification",
        ),
        checks=("test_verify.py::test_r11_the_dataset_production_verification_carries_no_verifies_assessment_edge",),
    ),
]


# --- R12 ---------------------------------------------------------------------

_R12 = [
    Arm(
        row="R12",
        asserts="the boundary refuses a bare spec identity instead of a FrozenSpec value",
        sabotage=Sabotage(
            module="boundary.py",
            before="    if type(spec) is not FrozenSpec:",
            after="    if False:",
        ),
        checks=("test_boundary.py::test_r12_the_boundary_refuses_a_bare_spec_identity_string",),
    ),
]


# --- R13 ---------------------------------------------------------------------

_R13 = [
    Arm(
        row="R13",
        asserts="code capture digests every tracked and untracked file's bytes",
        sabotage=Sabotage(
            module="adapter.py",
            before="            rows.append((name, _file_digest(target)))",
            after='            rows.append((name, ""))',
        ),
        checks=(
            "test_adapter.py::test_r13_modifying_an_untracked_file_changes_code_identity",
            "test_adapter.py::test_r13_modifying_a_tracked_but_uncommitted_file_does_the_same",
        ),
    ),
]


# --- R14 ---------------------------------------------------------------------

_R14 = [
    Arm(
        row="R14",
        asserts="binary floats are refused at every run identity position",
        sabotage=Sabotage(
            module="identity/v1.py",
            before=(
                "    if isinstance(value, float):\n"
                "        raise BinaryFloatRefused(\n"
                '            f"at {path}: binary floats are refused at the boundary; '
                'supply a Decimal and own the rounding"\n'
                "        )"
            ),
            after="    if isinstance(value, float):\n        return str(value)",
        ),
        checks=("test_recipe.py::test_r14_binary_floats_are_refused_at_every_run_position",),
    ),
    Arm(
        row="R14",
        asserts="kind and version domains are hashed into every identity",
        sabotage=Sabotage(
            module="identity/v1.py",
            before='    return sha256(domain.encode("utf-8") + b"\\n" + encode(value)).hexdigest()',
            after="    return sha256(encode(value)).hexdigest()",
        ),
        checks=("test_recipe.py::test_r14_kind_domains_separate_and_v2_never_equals_v1",),
    ),
]


# --- R16 ---------------------------------------------------------------------

_R16 = [
    Arm(
        row="R16",
        asserts="an equivalence implementation can read exactly two result manifests and no occurrence",
        sabotage=Sabotage(
            module="replay.py",
            before=(
                "        if len(parameters) != 2 or any(\n"
                "            parameter.kind not in positional or parameter.default is not inspect.Parameter.empty\n"
                "            for parameter in parameters\n"
                "        ):"
            ),
            after="        if False:",
        ),
        checks=("test_replay.py::test_r16_no_equivalence_rule_can_read_an_occurrence",),
    ),
    Arm(
        row="R16",
        asserts="a recorded seed claim violating its plan is non-conforming and not certified",
        sabotage=Sabotage(
            module="replay.py",
            before="            if actual != expected:",
            after="            if False:",
        ),
        checks=("test_replay.py::test_r16_a_seed_violating_run_is_non_conforming_and_derives_not_certified",),
    ),
]


# --- R17 ---------------------------------------------------------------------
# Projection is checked independently at the value and execution boundaries.

_R17 = [
    Arm(
        row="R17",
        asserts="the projected recipe carries the frozen spec's parameters unchanged",
        sabotage=Sabotage(
            module="recipe.py",
            before="        parameters=spec.parameters,",
            after=('        parameters=dict(spec.parameters) | {"alpha": __import__("decimal").Decimal("0.5")},'),
        ),
        checks=("test_recipe.py::test_r17_the_projected_recipe_carries_the_spec_whole",),
    ),
    Arm(
        row="R17",
        asserts="the boundary renders configuration only from the unchanged projected members",
        sabotage=Sabotage(
            module="recipe.py",
            before="        parameters=spec.parameters,",
            after=('        parameters=dict(spec.parameters) | {"alpha": __import__("decimal").Decimal("0.5")},'),
        ),
        checks=("test_boundary.py::test_r17_the_boundary_renders_the_configuration_from_the_projected_members",),
    ),
    Arm(
        row="R17",
        asserts="an option-like workflow target is refused before argv construction",
        sabotage=Sabotage(
            module="adapter.py",
            before='        if target.startswith("-"):',
            after="        if False:",
        ),
        checks=("test_adapter.py::test_an_option_like_target_is_rejected_before_any_argv_is_built",),
    ),
]


# --- R18 ---------------------------------------------------------------------

_R18 = [
    Arm(
        row="R18",
        asserts="the verification basis names the evidence-bearing report identity exactly once",
        sabotage=Sabotage(
            module="verify.py",
            before='        "report": report.identity(),',
            after='        "report": "",',
        ),
        checks=(
            "test_verify.py::test_r18_two_certifications_yield_two_verification_addresses",
            "test_verify.py::test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once",
        ),
    ),
    Arm(
        row="R18",
        asserts="every boundary receipt field, including rendered configuration, is identity-bearing",
        sabotage=Sabotage(
            module="recipe.py",
            before='        "rendered_config": _pairs(receipt.rendered_config),\n',
            after="",
        ),
        checks=("test_verify.py::test_r18_mutating_any_receipt_field_moves_receipt_report_and_verification",),
    ),
    Arm(
        row="R18",
        asserts="the comparison report carries the two receipt identities, never the run addresses",
        sabotage=Sabotage(
            module="verify.py",
            before=(
                "        receipts=(original.occurrence.receipt.identity(), replayed.occurrence.receipt.identity()),"
            ),
            after="        receipts=(original.address(), replayed.address()),",
        ),
        checks=("test_verify.py::test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once",),
    ),
]


# --- R19 ---------------------------------------------------------------------

_R19 = [
    Arm(
        row="R19",
        asserts="only build_verification exposes a public path that mints verification carriers",
        sabotage=Sabotage(
            module="verify.py",
            before='    "build_verification",\n    "decode_verification",\n    "publication_node",\n]',
            after='    "build_verification",\n    "decode_verification",\n    "_mint_verification",\n    "publication_node",\n]',
        ),
        checks=("test_verify.py::test_r19_only_build_verification_mints_the_carriers",),
    ),
    Arm(
        row="R19",
        asserts="a mixed assessment and dataset-production run pair is refused",
        sabotage=Sabotage(
            module="verify.py",
            before="    if original.recipe.shape != replayed.recipe.shape:",
            after="    if False:",
        ),
        checks=("test_verify.py::test_r19_a_mixed_shape_pair_is_refused",),
    ),
    Arm(
        row="R19",
        asserts="the evaluator resolves through the original recipe's frozen logical-rule binding",
        sabotage=Sabotage(
            module="verify.py",
            before=(
                "        implementation_identity = dict(original.recipe.rule_bindings)[rule]\n"
                "        implementation = held_rules[implementation_identity]"
            ),
            after="        implementation_identity = rule\n        implementation = held_rules[rule]",
        ),
        checks=("test_verify.py::test_r19_the_evaluator_resolves_from_the_frozen_spec_and_rule_bindings",),
    ),
    Arm(
        row="R19",
        asserts="the verifies-to-assessment edge is derived from the frozen spec and original run",
        sabotage=Sabotage(
            module="verify.py",
            before="    return _mint_verification(assessment=derived.assessment, supersedes=None, **common)",
            after='    return _mint_verification(assessment="", supersedes=None, **common)',
        ),
        checks=("test_verify.py::test_r19_the_assessment_edge_is_derived_never_authored",),
    ),
]


# --- R20 ---------------------------------------------------------------------

_R20 = [
    Arm(
        row="R20",
        asserts="every declared seed stream has a total mapping to a declared root",
        sabotage=Sabotage(
            module="spec.py",
            before="        if unmapped:",
            after="        if False:",
        ),
        checks=("test_spec.py::test_r20_multi_root_plan_without_a_total_mapping_is_refused",),
    ),
    Arm(
        row="R20",
        asserts="stochastic-unseeded beside a bitwise rule is refused at freeze time",
        sabotage=Sabotage(
            module="spec.py",
            before=(
                "    if isinstance(draft.nondeterminism, StochasticUnseeded) and "
                "draft.equivalence_rule in BITWISE_EQUIVALENCE_RULES:"
            ),
            after="    if False:",
        ),
        checks=("test_spec.py::test_r20_unseeded_beside_a_bitwise_rule_is_caught_at_freeze",),
    ),
    Arm(
        row="R20",
        asserts="realized seeds are nested by semantic job and stream, never keyed by job alone",
        sabotage=Sabotage(
            module="spec.py",
            before="            if not isinstance(per_stream, Mapping):",
            after="            if False:",
        ),
        checks=("test_spec.py::test_r20_two_stream_two_root_seeds_cannot_be_keyed_by_job_alone",),
    ),
]


# --- R21 ---------------------------------------------------------------------

_R21 = [
    Arm(
        row="R21",
        asserts="a missing declared output is a manifest refusal, never a silently incomplete manifest",
        sabotage=Sabotage(
            module="boundary.py",
            before=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs))"
            ),
            after=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs if (scratch / name).is_file()))"
            ),
        ),
        checks=("test_boundary.py::test_r21_manifest_missing_output_mints_no_run",),
    ),
    Arm(
        row="R21",
        asserts="mint_run re-verifies every manifest digest against the bytes on disk",
        sabotage=Sabotage(
            module="boundary.py",
            before="        if _digest(_output_path(scratch, name)) != expected:",
            after="        if False:",
        ),
        checks=("test_boundary.py::test_r21_a_digest_disagreeing_with_the_bytes_on_disk_mints_no_run",),
    ),
    Arm(
        row="R21",
        asserts="the result manifest contains declared outputs only and excludes scratch intermediates",
        sabotage=Sabotage(
            module="boundary.py",
            before=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs))"
            ),
            after=(
                "    return ResultManifest(outputs=tuple((path.relative_to(scratch).as_posix(), _digest(path)) "
                'for path in scratch.rglob("*") if path.is_file()))'
            ),
        ),
        checks=("test_boundary.py::test_r21_intermediates_are_excluded_and_scratch_files_leave_the_manifest_equal",),
    ),
]


# --- R22 ---------------------------------------------------------------------

_R22 = [
    Arm(
        row="R22",
        asserts="an evaluator machinery failure records a finding, never an inconclusive assessment",
        sabotage=Sabotage(
            module="assess.py",
            before='        return AssessmentFinding(run=run_address, reason=f"evaluation-failed: {error}")',
            after=(
                '        return AssessmentValue(spec="", run=run_address, proposition="", '
                'outcome="inconclusive", interpretation_rule="")'
            ),
        ),
        checks=("test_assess.py::test_r22_a_failing_evaluator_produces_a_finding_never_inconclusive",),
    ),
    Arm(
        row="R22",
        asserts="assessment applicability derives from the frozen spec",
        sabotage=Sabotage(
            module="assess.py",
            before="            applicability=spec.applicability,",
            after='            applicability="everyone",',
        ),
        checks=("test_assess.py::test_r22_the_facet_derives_from_the_frozen_spec_and_the_manifest",),
    ),
    Arm(
        row="R22",
        asserts="an implementation returning the wrong fixture value is not the named rule",
        sabotage=Sabotage(
            module="spec.py",
            before="            if impl.evaluate(*fixture.arguments) != fixture.expected:",
            after="            if False:",
        ),
        checks=("test_spec.py::test_r22_a_fixture_failing_implementation_is_not_that_rule",),
    ),
    Arm(
        row="R22",
        asserts="the assessment outcome derives from the result and frozen interpretation rule",
        sabotage=Sabotage(
            module="assess.py",
            before="            outcome=outcome,",
            after='            outcome="supported",',
        ),
        checks=("test_assess.py::test_r22_the_derived_outcome_moves_only_with_the_result_or_the_rule",),
    ),
    Arm(
        row="R22",
        asserts="run identity is the last hop from recipe inputs into assessment identity",
        sabotage=Sabotage(
            module="record.py",
            before=(
                "        return v1.digest(ASSESSMENT_DOMAIN, "
                '{"spec": self.spec, "run": self.run, "proposition": self.proposition})'
            ),
            after=('        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "proposition": self.proposition})'),
        ),
        checks=("test_assess.py::test_r22_the_reach_arm_an_inline_exclusion_moves_the_digest_with_identical_facets",),
    ),
    Arm(
        row="R22",
        asserts="an inline exclusion certification is identity-bearing in the recipe input row",
        sabotage=Sabotage(
            module="recipe.py",
            before=(
                "            if entry.exclusion is not None:\n"
                '                row["exclusion"] = {\n'
                '                    "rationale": entry.exclusion.rationale,\n'
                '                    "attribution": entry.exclusion.attribution,\n'
                "                }\n"
            ),
            after="",
        ),
        checks=("test_assess.py::test_r22_the_reach_arm_an_inline_exclusion_moves_the_digest_with_identical_facets",),
    ),
    Arm(
        row="R22",
        asserts="the exclusion reach path begins at the recipe input projection",
        sabotage=Sabotage(
            module="recipe.py",
            before='            "inputs": inputs,\n',
            after="",
        ),
        checks=("test_recipe.py::test_r2_every_recipe_member_moves_the_run_address[inputs_exclusion]",),
    ),
]


# --- R23 ---------------------------------------------------------------------

_R23 = [
    Arm(
        row="R23",
        asserts="a produced dataset address projects deduplicated content identities, not logical names",
        sabotage=Sabotage(
            module="production.py",
            before=(
                "            resources=tuple(ResourceDeclaration(name=name, digest=digest) "
                "for name, digest in run.result.outputs)"
            ),
            after=(
                '            resources=tuple(ResourceDeclaration(name=name, digest=f"{name}:{digest}") '
                "for name, digest in run.result.outputs)"
            ),
        ),
        checks=(
            "test_production.py::test_r23_the_address_is_the_basis_projection_over_the_manifest",
            "test_production.py::test_r23_negative_a_byte_identical_output_under_two_logical_names_yields_one_address",
        ),
    ),
    Arm(
        row="R23",
        asserts="a replay adds an edge while preserving the first stamped basis unchanged",
        sabotage=Sabotage(
            module="production.py",
            before=(
                "    basis = prior or StampedBasis(\n"
                "        run=run_address,\n"
                '        transforms=tuple(sorted(value.content for value in run.recipe.inputs if value.role == "transforms")),\n'
                "    )\n"
                "    return MintedDataset(\n"
                "        address=address,\n"
                "        edge=ProducesEdge(run=run_address, dataset=address),\n"
                "        basis=basis,\n"
                "        stamped=prior is None,"
            ),
            after=(
                "    basis = StampedBasis(\n"
                "        run=run_address,\n"
                '        transforms=tuple(sorted(value.content for value in run.recipe.inputs if value.role == "transforms")),\n'
                "    )\n"
                "    return MintedDataset(\n"
                "        address=address,\n"
                "        edge=ProducesEdge(run=run_address, dataset=address),\n"
                "        basis=basis,\n"
                "        stamped=True,"
            ),
        ),
        checks=("test_production.py::test_r23_replay_cardinality_one_address_two_edges_nothing_mutated",),
    ),
]


# --- T1 ----------------------------------------------------------------------

_T1 = [
    Arm(
        row="T1",
        asserts="the act-report mint stays private to the boundary",
        sabotage=Sabotage(
            module="report.py",
            before='    "completion",\n]',
            after='    "completion",\n    "_mint_report",\n]',
        ),
        checks=("test_inertness.py::test_t1_no_construction_path_authors_an_act_report",),
    ),
]


# --- T2 ----------------------------------------------------------------------

_T2 = [
    Arm(
        row="T2",
        asserts="a dataset-production attempt opens a run-attempt operation intent",
        sabotage=Sabotage(
            module="boundary.py",
            before='    intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)',
            after='    intent = OperationIntent("acquisition", secrets.token_hex(16), actor)',
        ),
        checks=("test_boundary.py::test_t2_a_dataset_production_attempt_opens_the_operation_intent",),
    ),
    Arm(
        row="T2",
        asserts="a surviving pre-intent refusal publishes an unfulfilling act report",
        sabotage=Sabotage(
            module="boundary.py",
            before=("    registration = Registration(token, report.identity()) if intent is not None else None"),
            after=(
                "    report = None if intent is None else report\n"
                "    registration = Registration(token, report.identity()) if intent is not None else None"
            ),
        ),
        checks=("test_boundary.py::test_t2_a_missing_spec_refusal_publishes_an_unfulfilling_report",),
    ),
]


# --- T3 ----------------------------------------------------------------------

_T3 = [
    Arm(
        row="T3",
        asserts="an unreadable fulfillment pointer is indeterminate, never unfinished",
        sabotage=Sabotage(
            module="report.py",
            before="    return INDETERMINATE if unresolved else UNFINISHED",
            after="    return UNFINISHED",
        ),
        checks=(
            "test_report.py::test_t3_an_unreadable_fulfillment_pointer_reads_indeterminate_never_unfinished",
            "test_report.py::test_t3_deleting_a_report_moves_closed_to_indeterminate_not_unfinished",
        ),
    ),
]


# --- T4 ----------------------------------------------------------------------

_T4 = [
    Arm(
        row="T4",
        asserts="reports are invisible to both the belief projection and the belief module imports",
        sabotage=Sabotage(
            module="closure.py",
            before="    projection: dict[str, object] = {\n",
            after=(
                "    import gc\n"
                "    import beliefs.report\n"
                "\n"
                "    projection: dict[str, object] = {\n"
                '        "reports": [\n'
                "            value.identity()\n"
                "            for value in gc.get_objects()\n"
                "            if type(value) is beliefs.report.ActReport\n"
                "        ],\n"
            ),
        ),
        checks=(
            "test_inertness.py::test_t4_adding_and_removing_reports_leaves_belief_admission_and_eligibility_byte_unchanged",
            "test_inertness.py::test_t4_the_belief_modules_never_import_the_report_layer",
        ),
    ),
]


# --- T5 ----------------------------------------------------------------------

_T5 = [
    Arm(
        row="T5",
        asserts="byte-locator-untested is unspellable on a managed-mutation entry",
        sabotage=Sabotage(
            module="report.py",
            before="    ManagedMutationEntry: (PublishedObservation,),",
            after="    ManagedMutationEntry: (PublishedObservation, ByteLocatorUntested),",
        ),
        checks=("test_report.py::test_t5_byte_locator_untested_is_unspellable_on_a_managed_mutation_entry",),
    ),
]


# --- T6 ----------------------------------------------------------------------

_T6 = [
    Arm(
        row="T6",
        asserts="report entry order is identity-bearing",
        sabotage=Sabotage(
            module="report.py",
            before='                "entries": [_entry_facet(entry) for entry in self.entries],',
            after='                "entries": [_entry_facet(entry) for entry in sorted(self.entries, key=repr)],',
        ),
        checks=("test_report.py::test_t6_permuting_two_entries_moves_the_report_identity",),
    ),
    Arm(
        row="T6",
        asserts="an out-of-range report entry index is refused at the citing site",
        sabotage=Sabotage(
            module="report.py",
            before=(
                "    if type(report) is not ActReport or type(index) is not int or not 0 <= index < len(report.entries):\n"
                '        raise CitationRefused("citation index must be a zero-based unsigned entry position")\n'
                "    return report.entries[index]"
            ),
            after=(
                "    if type(report) is not ActReport or type(index) is not int:\n"
                '        raise CitationRefused("citation index must be a zero-based unsigned entry position")\n'
                "    index = min(max(index, 0), len(report.entries) - 1)\n"
                "    return report.entries[index]"
            ),
        ),
        checks=("test_report.py::test_t6_an_out_of_range_index_is_refused_at_the_citing_site",),
    ),
    Arm(
        row="T6",
        asserts="a verification embeds the resolved cited entry content, not only its report position",
        sabotage=Sabotage(
            module="verify.py",
            before=(
                "        embedded_citation = EmbeddedCitation(report_ref=published.identity(), "
                "index=index, content=_entry_facet(entry))"
            ),
            after=(
                "        embedded_citation = EmbeddedCitation(report_ref=published.identity(), "
                "index=index, content={})"
            ),
        ),
        checks=("test_verify.py::test_t6_r18_deleting_the_cited_report_leaves_the_verification_unchanged",),
    ),
]


# --- T8 ----------------------------------------------------------------------

_T8 = [
    Arm(
        row="T8",
        asserts="the minted event token separates reports with otherwise equal facets",
        sabotage=Sabotage(
            module="report.py",
            before='                "event_token": self.event_token,\n',
            after="",
        ),
        checks=("test_report.py::test_t8_equal_facets_with_distinct_event_tokens_are_two_reports",),
    ),
    Arm(
        row="T8",
        asserts="the ordered entries are an act-report identity member",
        sabotage=Sabotage(
            module="report.py",
            before='                "entries": [_entry_facet(entry) for entry in self.entries],\n',
            after="",
        ),
        checks=("test_report.py::test_t8_every_facet_member_moves_the_identity",),
    ),
]


# --- G9 ----------------------------------------------------------------------

_G9 = [
    Arm(
        row="G9",
        asserts="unresolvable required artifacts make replay eligibility not available",
        sabotage=Sabotage(
            module="replay.py",
            before=(
                "    return AVAILABLE if required <= resolvable_here and run.address() in attributions "
                "else NOT_AVAILABLE"
            ),
            after="    return AVAILABLE if run.address() in attributions else NOT_AVAILABLE",
        ),
        checks=("test_replay.py::test_r5_g9_unreachable_bytes_with_a_held_copy_move_none_of_the_three",),
    ),
    Arm(
        row="G9",
        asserts="availability is not authored into the closure digest",
        sabotage=Sabotage(
            module="closure.py",
            before="    proposition: str,\n",
            after="    proposition: str,\n    availability: tuple = (),\n",
        ),
        checks=("test_replay.py::test_r5_g9_unreachable_bytes_with_a_held_copy_move_none_of_the_three",),
    ),
    Arm(
        row="G9",
        asserts="heldness follows matching bytes independent of observation location",
        sabotage=Sabotage(
            module="admission.py",
            before="        supplied = observations.get(address, ()) if address is not None else ()",
            after=(
                "        supplied = tuple(observation for observation in observations.get(address, ()) "
                'if observation.location.startswith("repo://")) if address is not None else ()'
            ),
        ),
        checks=("test_replay.py::test_r5_g9_unreachable_bytes_with_a_held_copy_move_none_of_the_three",),
    ),
]


def _clause_arm(
    row: str,
    asserts: str,
    module: str,
    before: str,
    after: str,
    check: str,
) -> Arm:
    """Declare one selected assertion clause without repeating table plumbing."""
    return Arm(row=row, asserts=asserts, sabotage=Sabotage(module, before, after), checks=(check,))


# Clauses missed by the original seed matrix. Each entry maps one selected
# assertion to its named test and to a sabotage of the behavior that test owns.
_CLAUSE_ARMS = [
    _clause_arm(
        "G2a",
        "FrozenSpec values are minted through freeze or revise, never the ordinary dataclass API",
        "spec.py",
        '        raise TypeError("FrozenSpec values are minted by freeze or revise")',
        "        return None",
        "test_spec.py::test_frozen_specs_are_minted_only_by_freeze_and_revise",
    ),
    _clause_arm(
        "G2a",
        "an out-of-band execution has no boundary-mediated witness after a spec is frozen",
        "recipe.py",
        "    receipt: BoundaryReceipt\n",
        "    receipt: BoundaryReceipt\n    boundary_mediated: bool = True\n",
        "test_boundary.py::test_g2a_r12_an_out_of_band_run_with_a_spec_frozen_afterwards_is_undetectable",
    ),
    _clause_arm(
        "G4",
        "a referencing successor to a recorded failed replay is admitted",
        "spec.py",
        "    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:",
        "    if candidate.supersedes == superseded.identity:",
        "test_spec.py::test_g4_a_referencing_successor_is_admitted",
    ),
    _clause_arm(
        "G4",
        "a discarded failed attempt is undetectable from the supplied value state",
        "spec.py",
        "    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:",
        "    if candidate.supersedes != superseded.identity:",
        "test_spec.py::test_g4_a_discarded_failed_attempt_is_undetectable",
    ),
    _clause_arm(
        "R1",
        "a source note is a separate authored act before the held member is supplied",
        "record.py",
        '        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))',
        '        object.__setattr__(self, "relation", "attested")\n'
        '        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))',
        "test_recipe.py::test_r1_the_note_is_a_separate_act_and_the_member_is_then_supplied",
    ),
    _clause_arm(
        "R1",
        "a bare lockfile digest cannot stand in for an environment manifest",
        "recipe.py",
        "        if type(self.environment) is not EnvironmentManifest:",
        "        if False:",
        "test_recipe.py::test_r1_a_bare_lockfile_digest_is_refused_as_environment_identity",
    ),
    _clause_arm(
        "R2",
        "realized seeds and event tokens distinguish runs but never their recipes",
        "recipe.py",
        "        declared = set(self.recipe.invocation.declared_outputs)\n",
        '        object.__setattr__(self.recipe, "parameters", MappingProxyType({**self.recipe.parameters, '
        '"event_token": self.occurrence.event_token}))\n'
        "        declared = set(self.recipe.invocation.declared_outputs)\n",
        "test_recipe.py::test_r2_equal_recipes_despite_differing_seeds_and_event_tokens",
    ),
    _clause_arm(
        "R3",
        "two executions of one recipe retain equal recipe identities",
        "boundary.py",
        "        config = _render_config(recipe, definition)\n",
        '        recipe = __import__("dataclasses").replace(\n'
        '            recipe, parameters=dict(recipe.parameters) | {"event_token": intent.event_token}\n        )\n'
        "        config = _render_config(recipe, definition)\n",
        "test_boundary.py::test_r3_two_executions_of_one_recipe_are_two_runs",
    ),
    _clause_arm(
        "R4",
        "scope is derived and has no authored constructor parameter",
        "replay.py",
        "    certification: CodeLineageCertification | None,\n) -> str:",
        "    certification: CodeLineageCertification | None,\n    scope: str | None = None,\n) -> str:",
        "test_replay.py::test_r4_no_authored_scope_parameter_exists",
    ),
    _clause_arm(
        "R4",
        "equal recipes without a qualifying receipt derive same-environment",
        "replay.py",
        '        return "same-environment"',
        '        return "not-certified"',
        "test_replay.py::test_r4_equal_recipes_without_a_receipt_derive_same_environment",
    ),
    _clause_arm(
        "R4",
        "a hostname change alone remains same-environment",
        "replay.py",
        '        return "same-environment"',
        '        return "not-certified"',
        "test_replay.py::test_r4_negative_a_a_hostname_change_stays_same_environment",
    ),
    _clause_arm(
        "R6",
        "restored availability changes no state until a replay runs",
        "replay.py",
        "    return AVAILABLE if required <= resolvable_here and run.address() in attributions else NOT_AVAILABLE",
        "    return NOT_AVAILABLE",
        "test_replay.py::test_r6_restoring_availability_changes_nothing_until_a_replay_actually_runs",
    ),
    _clause_arm(
        "R8",
        "changing a seed root mints a successor spec",
        "spec.py",
        "    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
        "    successor = freeze(draft, held_rules=held_rules, supersedes=original.identity)\n"
        '    object.__setattr__(successor, "identity", original.identity)\n'
        "    return successor",
        "test_spec.py::test_r8_changing_a_root_seed_mints_a_successor_spec",
    ),
    _clause_arm(
        "R8",
        "editing the equivalence rule after a failing replay mints a new spec identity",
        "spec.py",
        "    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
        "    successor = freeze(draft, held_rules=held_rules, supersedes=original.identity)\n"
        '    object.__setattr__(successor, "identity", original.identity)\n'
        "    return successor",
        "test_verify.py::test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen",
    ),
    _clause_arm(
        "R8",
        "the original run closure still names the old spec after revision",
        "spec.py",
        "    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
        "    successor = freeze(draft, held_rules=held_rules, supersedes=original.identity)\n"
        "    for value in __import__('gc').get_objects():\n"
        "        if type(value).__name__ == 'Recipe' and getattr(value, 'spec_identity', None) == original.identity:\n"
        "            object.__setattr__(value, 'spec_identity', successor.identity)\n"
        "    return successor",
        "test_verify.py::test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen",
    ),
    _clause_arm(
        "R8",
        "the failing verification remains active after the spec revision",
        "verify.py",
        "    return tuple(verification for verification in verifications if verification.identity() not in superseded)",
        "    return ()",
        "test_verify.py::test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen",
    ),
    _clause_arm(
        "R8",
        "the replay is failing before any post-result rule revision",
        "replay.py",
        '    return "passed" if original == replayed else "failed"',
        '    return "passed"',
        "test_verify.py::test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen",
    ),
    _clause_arm(
        "R10",
        "an accession is refused and no fallback synthesizes a dataset",
        "boundary.py",
        '    return "://" in address or address.startswith("accession:")',
        '    return "://" in address',
        "test_boundary.py::test_r10_an_accession_is_refused_and_no_fallback_synthesizes_a_dataset",
    ),
    _clause_arm(
        "R11",
        "dataset-production verification accepts no tolerance parameter",
        "verify.py",
        "    citation: tuple[ActReport, int] | None = None,\n) -> RunVerification:",
        "    citation: tuple[ActReport, int] | None = None,\n    tolerance: object = None,\n) -> RunVerification:",
        "test_verify.py::test_r11_a_tolerance_on_a_dataset_production_replay_is_refused",
    ),
    _clause_arm(
        "R11",
        "a nondeterministic production replay yields a different dataset entity",
        "production.py",
        "    if address is None:",
        '    address = "dataset:fixed"\n    if address is None:',
        "test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four",
    ),
    _clause_arm(
        "R11",
        "the prior assessment remains bound to the run observing the prior dataset",
        "assess.py",
        "            run=run_address,",
        '            run="replayed-run",',
        "test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four",
    ),
    _clause_arm(
        "R11",
        "a production replay and verification move no existing belief",
        "verify.py",
        '    _require_str(epoch, "verification epoch")',
        '    _require_str(epoch, "verification epoch")\n'
        "    import beliefs.belief as belief_module\n"
        '    belief_module.OUTCOME_SIGNS = {"supported": -1, "refuted": 1, "inconclusive": 0}',
        "test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four",
    ),
    _clause_arm(
        "R12",
        "freezing a spec after an out-of-band run cannot reveal the ordering",
        "recipe.py",
        "    receipt: BoundaryReceipt\n",
        "    receipt: BoundaryReceipt\n    boundary_mediated: bool = True\n",
        "test_boundary.py::test_g2a_r12_an_out_of_band_run_with_a_spec_frozen_afterwards_is_undetectable",
    ),
    _clause_arm(
        "R14",
        "null, string-decimal, integer-decimal, normalized decimal, and normalized-key collisions stay distinct or refused",
        "identity/v1.py",
        '    if value is None:\n        raise NullRefused(f"at {path}: null is refused, not pruned")',
        '    if value is None:\n        return "null"',
        "test_recipe.py::test_r14_the_four_collisions_walked_at_the_recipe_position",
    ),
    _clause_arm(
        "R14",
        "NaN and infinities are refused at every identity position",
        "identity/v1.py",
        "    if not value.is_finite():",
        "    if False:",
        "test_recipe.py::test_r14_nan_and_infinity_are_refused_in_every_position",
    ),
    _clause_arm(
        "R16",
        "a seed-violating complete execution still mints a run",
        "boundary.py",
        "        realized_seeds = read_realized_seeds(scratch)\n",
        "        realized_seeds = read_realized_seeds(scratch)\n        if realized_seeds.seeds:\n"
        '            return _refused("seed-claim-refused", subject, actor, observer, started_at, intent)\n',
        "test_boundary.py::test_r16_a_seed_violating_execution_still_mints_a_run",
    ),
    _clause_arm(
        "R17",
        "project_recipe offers no caller path for projected members",
        "recipe.py",
        "    boundary_policy: BoundaryPolicy,\n) -> Recipe:",
        "    boundary_policy: BoundaryPolicy,\n    parameters: Mapping[str, object] | None = None,\n) -> Recipe:",
        "test_recipe.py::test_r17_projection_offers_no_caller_path_for_the_projected_members",
    ),
    _clause_arm(
        "R17",
        "project_recipe refuses a declared input that is not held",
        "recipe.py",
        "                content=held[entry.dataset],",
        '                content=held.get(entry.dataset, "sha256:" + "00" * 32),',
        "test_recipe.py::test_r17_projection_refuses_a_declared_input_that_is_not_held",
    ),
    _clause_arm(
        "R17",
        "invocations hold bindings rather than supplied values",
        "recipe.py",
        "    declared_outputs: tuple[str, ...]\n\n    def __post_init__",
        "    declared_outputs: tuple[str, ...]\n    values: tuple[str, ...] = ()\n\n    def __post_init__",
        "test_recipe.py::test_r17_invocation_holds_bindings_not_values",
    ),
    _clause_arm(
        "R17",
        "assessment execution has no caller path for inputs, parameters, or nondeterminism",
        "boundary.py",
        "    spec: object,\n    port: OperationPort,",
        "    spec: object,\n    inputs: tuple[RecipeInput, ...] = (),\n    port: OperationPort,",
        "test_boundary.py::test_r17_no_path_supplies_inputs_parameters_or_contract_on_an_assessment_run",
    ),
    _clause_arm(
        "R17",
        "seed shopping requires a successor spec and leaves the recorded run on the old identity",
        "spec.py",
        "    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
        "    successor = freeze(draft, held_rules=held_rules, supersedes=original.identity)\n"
        '    object.__setattr__(successor, "identity", original.identity)\n'
        "    return successor",
        "test_boundary.py::test_r17_seed_shopping_cannot_occur_at_all",
    ),
    _clause_arm(
        "R17",
        "a deleted or never-recorded attempt is undetectable from the held set",
        "boundary.py",
        "    registration = Registration(token, report.identity()) if intent is not None else None",
        "    report = None if intent is None else report\n"
        "    registration = Registration(token, report.identity()) if intent is not None else None",
        "test_boundary.py::test_r17_a_deleted_or_never_recorded_attempt_is_undetectable",
    ),
    _clause_arm(
        "R17",
        "dataset-production recipe members are authored directly at that boundary",
        "boundary.py",
        "def execute_production_run(\n    *,\n    inputs: tuple[RecipeInput, ...],\n    port: OperationPort,",
        "def execute_production_run(\n    *,\n    _inputs: tuple[RecipeInput, ...],\n    port: OperationPort,",
        "test_boundary.py::test_r17_negative_b_a_dataset_production_recipe_is_authored_directly",
    ),
    _clause_arm(
        "R18",
        "deleting an external certification leaves the embedded verification unchanged",
        "verify.py",
        '        ("certification", certification),',
        '        ("certification", None),',
        "test_verify.py::test_r18_deleting_the_external_certification_leaves_the_verification_unchanged",
    ),
    _clause_arm(
        "R18",
        "the comparison report carries both conformance results inline",
        "verify.py",
        "        original_conformance=conformance(original),",
        '        original_conformance="unreported",',
        "test_verify.py::test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once",
    ),
    _clause_arm(
        "R18",
        "the comparison report carries the exact certification claim inline",
        "verify.py",
        "        rule_bindings=((rule, implementation_identity),),\n        certification=certification,",
        "        rule_bindings=((rule, implementation_identity),),\n        certification=None,",
        "test_verify.py::test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once",
    ),
    _clause_arm(
        "R18",
        "the comparison report carries the exact resolved rule binding inline",
        "verify.py",
        "        rule_bindings=((rule, implementation_identity),),",
        "        rule_bindings=(),",
        "test_verify.py::test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once",
    ),
    _clause_arm(
        "R19",
        "the verification constructor has the selected closed parameter list",
        "verify.py",
        "    citation: tuple[ActReport, int] | None = None,\n) -> RunVerification:",
        "    citation: tuple[ActReport, int] | None = None,\n    evaluator: object = None,\n) -> RunVerification:",
        "test_verify.py::test_r19_the_constructor_list_is_closed",
    ),
    _clause_arm(
        "R20",
        "deterministic with a seed plan is unspellable",
        "spec.py",
        'class Deterministic:\n    """Carries nothing: the run claims no RNG dependence at all."""',
        'class Deterministic:\n    """Carries nothing: the run claims no RNG dependence at all."""\n\n    plan: object = None',
        "test_spec.py::test_r20_deterministic_with_a_plan_is_unspellable",
    ),
    _clause_arm(
        "R20",
        "stochastic-unseeded with a seed plan is unspellable",
        "spec.py",
        "class StochasticUnseeded:\n    rationale: str\n",
        "class StochasticUnseeded:\n    rationale: str\n    plan: object = None\n",
        "test_spec.py::test_r20_stochastic_unseeded_with_a_plan_is_unspellable",
    ),
    _clause_arm(
        "R20",
        "seeded without a seed plan is unspellable",
        "spec.py",
        "class Seeded:\n    plan: SeedPlan\n",
        "class Seeded:\n    plan: SeedPlan | None = None\n",
        "test_spec.py::test_r20_seeded_without_a_plan_is_unspellable",
    ),
    _clause_arm(
        "R20",
        "a stream root mapping may name declared roots only",
        "spec.py",
        "        if undeclared:",
        "        if False:",
        "test_spec.py::test_r20_a_mapped_root_must_be_declared",
    ),
    _clause_arm(
        "R20",
        "stochastic-unseeded with a nonempty rationale is freezable",
        "spec.py",
        "        if not self.rationale:",
        "        if True:",
        "test_spec.py::test_r20_stochastic_unseeded_with_a_rationale_is_freezable",
    ),
    _clause_arm(
        "R20",
        "the frozen spec names logical streams and no workflow family field",
        "spec.py",
        "    nondeterminism: Deterministic | Seeded | StochasticUnseeded\n\n    def __post_init__",
        "    nondeterminism: Deterministic | Seeded | StochasticUnseeded\n    family_streams: tuple[str, ...] = ()\n\n"
        "    def __post_init__",
        "test_spec.py::test_r20_the_spec_names_logical_streams_only_no_family_field_exists",
    ),
    _clause_arm(
        "R21",
        "the manifest is boundary-constructed with no supplied-manifest path",
        "boundary.py",
        "    spec: object,\n    port: OperationPort,",
        "    spec: object,\n    manifest: ResultManifest | None = None,\n    port: OperationPort,",
        "test_boundary.py::test_r21_the_manifest_is_constructed_by_the_boundary_and_no_supplied_path_exists",
    ),
    _clause_arm(
        "R21",
        "an undeclared manifest entry mints no run",
        "recipe.py",
        "        if supplied - declared:",
        "        if False:",
        "test_recipe.py::test_r21_an_undeclared_manifest_entry_mints_no_run",
    ),
    _clause_arm(
        "R21",
        "absolute and root-escaping output declarations are refused",
        "recipe.py",
        "            if PurePosixPath(output).is_absolute():",
        "            if False:",
        "test_recipe.py::test_r21_absolute_and_root_escaping_output_declarations_are_refused",
    ),
    _clause_arm(
        "R21",
        "duplicate logical output names are refused",
        "recipe.py",
        "        if len(set(names)) != len(names):",
        "        if False:",
        "test_recipe.py::test_r21_a_duplicate_logical_name_is_refused",
    ),
    _clause_arm(
        "R21",
        "a scheduling-only cores option leaves recipe identity unchanged",
        "boundary.py",
        "        config = _render_config(recipe, definition)\n",
        '        if cores != 1:\n            recipe = __import__("dataclasses").replace(\n'
        '                recipe, parameters=dict(recipe.parameters) | {"cores": cores}\n            )\n'
        "        config = _render_config(recipe, definition)\n",
        "test_boundary.py::test_r21_negative_a_a_scheduling_only_option_leaves_the_recipe_identity_unchanged",
    ),
    _clause_arm(
        "R21",
        "scratch mount differences remain receipt-only and leave recipe identity unchanged",
        "boundary.py",
        "        config = _render_config(recipe, definition)\n",
        '        recipe = __import__("dataclasses").replace(\n'
        '            recipe, parameters=dict(recipe.parameters) | {"scratch": str(scratch)}\n        )\n'
        "        config = _render_config(recipe, definition)\n",
        "test_boundary.py::test_r21_negative_c_two_differently_mounted_scratch_roots_yield_equal_recipe_identities",
    ),
    _clause_arm(
        "R21",
        "a disobeyed complete closure is a run while an incompletable closure is a refusal",
        "boundary.py",
        "        realized_seeds = read_realized_seeds(scratch)\n",
        "        realized_seeds = read_realized_seeds(scratch)\n        if realized_seeds.seeds:\n"
        '            return _refused("seed-claim-refused", subject, actor, observer, started_at, intent)\n',
        "test_boundary.py::test_r21_negative_e_the_two_failure_states_are_distinct",
    ),
    _clause_arm(
        "R22",
        "the assessment constructor accepts only a run and held resolution mappings",
        "assess.py",
        "    implementations: Mapping[str, RuleImplementation],\n) -> AssessmentValue | AssessmentFinding:",
        "    implementations: Mapping[str, RuleImplementation],\n    outcome: object = None,\n"
        ") -> AssessmentValue | AssessmentFinding:",
        "test_assess.py::test_r22_the_constructor_takes_only_a_run_ref",
    ),
    _clause_arm(
        "R22",
        "the evaluator resolves from the implementation binding frozen in the recipe",
        "assess.py",
        "        implementation_identity = dict(run.recipe.rule_bindings)[spec.interpretation_rule]",
        "        implementation_identity = spec.interpretation_rule",
        "test_assess.py::test_r22_the_evaluator_resolves_from_the_binding_frozen_in_the_recipe",
    ),
    _clause_arm(
        "R22",
        "a spec mapping key cannot substitute different frozen content",
        "assess.py",
        "        if type(spec) is not FrozenSpec or spec.identity != spec_identity:",
        "        if False:",
        "test_assess.py::test_r22_a_spec_mapping_key_cannot_substitute_a_different_frozen_spec",
    ),
    _clause_arm(
        "R22",
        "an implementation mapping key cannot substitute forged, mismatched, or nonconforming content",
        "assess.py",
        "        if (\n            type(implementation) is not RuleImplementation",
        "        if False and (\n            type(implementation) is not RuleImplementation",
        "test_assess.py::test_r22_an_implementation_mapping_key_cannot_substitute_unbound_content",
    ),
    _clause_arm(
        "R22",
        "narrowing applicability requires a successor spec and a new run",
        "spec.py",
        "    return freeze(draft, held_rules=held_rules, supersedes=original.identity)",
        "    return original",
        "test_assess.py::test_r22_negative_a_narrowing_applicability_needs_a_successor_spec_and_a_new_run",
    ),
    _clause_arm(
        "R22",
        "exchanging assessment facets while preserving their bags moves the keyed belief digest",
        "closure.py",
        "    assessment_facets = sorted((a.identity(), a.facet_digest()) for a in ours)",
        "    assessment_facets = list(zip(sorted(a.identity() for a in ours), "
        "sorted(a.facet_digest() for a in ours), strict=True))",
        "test_assess.py::test_r22_negative_b_exchanged_facets_move_the_belief_digest",
    ),
    _clause_arm(
        "R23",
        "the produces edge names the minting run and produced dataset",
        "production.py",
        "        edge=ProducesEdge(run=run_address, dataset=address),",
        '        edge=ProducesEdge(run="", dataset=address),',
        "test_production.py::test_r23_the_produces_edge_is_emitted_with_the_run",
    ),
    _clause_arm(
        "R23",
        "no produces edge can name output absent from the manifest",
        "production.py",
        "        edge=ProducesEdge(run=run_address, dataset=address),",
        '        edge=ProducesEdge(run=run_address, dataset="dataset:absent"),',
        "test_production.py::test_r23_no_edge_can_name_output_absent_from_the_manifest",
    ),
    _clause_arm(
        "R23",
        "no produced_by edge is reachable in either direction",
        "production.py",
        "    stamped: bool\n\n    def __post_init__",
        "    stamped: bool\n    produced_by: str | None = None\n\n    def __post_init__",
        "test_production.py::test_r23_no_produced_by_edge_is_reachable_in_either_direction",
    ),
    _clause_arm(
        "R23",
        "certified exclusion is inline and changing it mints a recipe rather than a run",
        "recipe.py",
        "            if entry.exclusion is not None:\n"
        '                row["exclusion"] = {\n'
        '                    "rationale": entry.exclusion.rationale,\n'
        '                    "attribution": entry.exclusion.attribution,\n'
        "                }\n",
        "",
        "test_production.py::test_r23_the_certified_exclusion_is_inline_and_mints_a_recipe_not_a_run",
    ),
    _clause_arm(
        "R23",
        "reclassifying an input role mints a different recipe",
        "recipe.py",
        "            inputs.append(row)",
        '            row.pop("role", None)\n'
        "            inputs.append(row)\n"
        '            inputs.sort(key=lambda value: (value["dataset"], value["content"]))',
        "test_production.py::test_r23_negative_h_reclassifying_an_inputs_role_mints_a_different_recipe",
    ),
    _clause_arm(
        "T1",
        "the private report constructor is reachable only from boundary and report modules",
        "assess.py",
        "from beliefs.recipe import RunClosure",
        "from beliefs.recipe import RunClosure\nfrom beliefs.report import _mint_report",
        "test_inertness.py::test_t1_the_constructor_is_reachable_only_from_the_boundary",
    ),
    _clause_arm(
        "T2",
        "a complete nonconforming execution mints a run rather than an act report",
        "boundary.py",
        "        realized_seeds = read_realized_seeds(scratch)\n",
        "        realized_seeds = read_realized_seeds(scratch)\n        if realized_seeds.seeds:\n"
        '            return _refused("seed-claim-refused", subject, actor, observer, started_at, intent)\n',
        "test_boundary.py::test_t2_negative_b_a_complete_non_conforming_execution_mints_a_run_never_an_act_report",
    ),
    _clause_arm(
        "T2",
        "a reconstructed-recipe mismatch closes its intent through a report registration",
        "boundary.py",
        '        result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)',
        '        return RunRefused("recipe-identity-mismatch", None, intent, None)',
        "test_replay.py::test_a_replay_refuses_a_reconstructed_recipe_mismatch",
    ),
    _clause_arm(
        "T2",
        "an assessment-run intent requires a nonempty frozen spec identity",
        "report.py",
        "        if not self.spec_identity:",
        "        if False:",
        "test_report.py::test_t2_the_assessment_run_intent_is_unspellable_without_a_spec_identity",
    ),
    _clause_arm(
        "T3",
        "an unmatched intent reads unfinished",
        "report.py",
        "    return INDETERMINATE if unresolved else UNFINISHED",
        "    return INDETERMINATE",
        "test_report.py::test_t3_an_unmatched_intent_reads_unfinished",
    ),
    _clause_arm(
        "T3",
        "a mapping cannot fabricate a missing fulfillment pointer",
        "report.py",
        "        if registration.pointer not in held:",
        "        if False:",
        "test_report.py::test_t3_a_mapping_cannot_fabricate_a_missing_fulfillment_pointer",
    ),
    _clause_arm(
        "T3",
        "a fulfilled intent reads closed",
        "report.py",
        "        if shapes.mismatch(decoded, evidence) is None:",
        "        if False:",
        "test_report.py::test_t3_a_fulfilled_intent_reads_closed",
    ),
    _clause_arm(
        "T3",
        "a nonqualifying pointer never matches an intent",
        "report.py",
        "        if shapes.mismatch(decoded, evidence) is None:",
        "        if True:",
        "test_report.py::test_t3_a_non_qualifying_pointer_never_matches",
    ),
    _clause_arm(
        "T3",
        "no status field is spellable on an operation record",
        "report.py",
        "    entries: tuple[Entry, ...]\n\n    def __init__",
        '    entries: tuple[Entry, ...]\n    status: str = "closed"\n\n    def __init__',
        "test_report.py::test_t3_no_status_field_is_spellable_on_any_record",
    ),
    _clause_arm(
        "T4",
        "no belief-bearing signature names a report",
        "closure.py",
        "    proposition: str,\n",
        "    proposition: str,\n    reports: tuple = (),\n",
        "test_inertness.py::test_t4_no_belief_bearing_signature_names_a_report",
    ),
    _clause_arm(
        "T5",
        "byte-locator-untested is unspellable on record-import entries",
        "report.py",
        "    RecordImportEntry: (ImportedRecords,),",
        "    RecordImportEntry: (ImportedRecords, ByteLocatorUntested),",
        "test_report.py::test_t5_byte_locator_untested_is_unspellable_on_a_record_import_entry",
    ),
    _clause_arm(
        "T5",
        "byte-locator-untested is unspellable on subject-evaluation entries",
        "report.py",
        "    SubjectEvaluationEntry: (EvaluationFinding,),",
        "    SubjectEvaluationEntry: (EvaluationFinding, ByteLocatorUntested),",
        "test_report.py::test_t5_byte_locator_untested_is_unspellable_on_a_subject_evaluation_entry",
    ),
    _clause_arm(
        "T6",
        "a report citation resolves to exactly the indexed entry",
        "report.py",
        "    return report.entries[index]",
        "    return report.entries[-1]",
        "test_report.py::test_t6_a_citation_resolves_to_exactly_one_entry",
    ),
    _clause_arm(
        "T6",
        "an out-of-range report citation is refused at the citing site",
        "report.py",
        "    if type(report) is not ActReport or type(index) is not int or not 0 <= index < len(report.entries):",
        "    if type(report) is not ActReport or type(index) is not int:",
        "test_verify.py::test_t6_an_out_of_range_citation_is_refused_at_the_citing_site",
    ),
    _clause_arm(
        "T8",
        "no ordinary API edits, supersedes, or deletes a report",
        "report.py",
        '    "completion",\n]',
        '    "completion",\n    "edit_report",\n]',
        "test_report.py::test_t8_no_ordinary_api_edits_supersedes_or_deletes_a_report",
    ),
]


CUT3_ARMS: tuple[Arm, ...] = tuple(
    _G2a
    + _G4
    + _M2
    + _R1
    + _R2
    + _R3
    + _R4
    + _R5
    + _R6
    + _R7
    + _R8
    + _R9
    + _R10
    + _R11
    + _R12
    + _R13
    + _R14
    + _R16
    + _R17
    + _R18
    + _R19
    + _R20
    + _R21
    + _R22
    + _R23
    + _T1
    + _T2
    + _T3
    + _T4
    + _T5
    + _T6
    + _T8
    + _G9
    + _CLAUSE_ARMS
)
