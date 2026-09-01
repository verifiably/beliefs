"""Cut 13's declared arms: 15 selected + 7 labeled = 22 units, 35 lettered arms.

Every sabotage is host-side (cut 13 §5 item 1): the sandbox's beliefs tree is
the closure's own copy, so probe.py is never sabotaged."""

from n2_arms import Arm, Sabotage

_BOUNDARY = "boundary.py"
_CONFINEMENT = "confinement.py"
_ADAPTER = "adapter.py"
_RECIPE = "recipe.py"
_REPLAY = "replay.py"
_VERIFY = "verify.py"
_RUNRECORD = "runrecord.py"

_ACCEPT = "acceptance/test_confinement_acceptance.py"
_QUALIFY_LINE = '        if qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):'
_CONTAINMENT = '    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.capabilities):\n        return False'
_REMOUNT = '    argv.extend(["--remount-ro", "/", "--chdir", OUTPUT_ROOT])'

CUT13_ARMS = (
    # --- R15 ---
    Arm("R15u1", "a bundled file edited after capture yields no run and the engine never starts",
        Sabotage(_BOUNDARY,
            before='    check_bundle_intact(bundle, code_identity)\n    inputs_before = fingerprint(output_root / "inputs")',
            after='    inputs_before = fingerprint(output_root / "inputs")'),
        (f"{_ACCEPT}::test_r15u1_a_bundled_file_edited_after_capture_yields_no_run_and_the_engine_never_starts",)),
    Arm("R15u2", "a bundled file edited after exit yields no run",
        Sabotage(_BOUNDARY,
            before='    check_closure_intact(bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=output_root / "inputs", inputs_fingerprint=inputs_before)',
            after='    pass'),
        (f"{_ACCEPT}::test_r15u2_a_bundled_file_edited_after_exit_yields_no_run",)),
    Arm("R15u3", "an undeclared file read fails closed",
        Sabotage(_CONFINEMENT,
            before=_REMOUNT,
            after='    argv.extend(["--ro-bind", "/etc", "/etc", "--remount-ro", "/", "--chdir", OUTPUT_ROOT])'),
        (f"{_ACCEPT}::test_r15u3_an_undeclared_file_read_fails_closed",)),
    Arm("R15u4", "an undeclared network connection fails closed",
        Sabotage(_CONFINEMENT,
            before='        "--unshare-all",',
            after='        "--unshare-user",\n        "--unshare-pid",\n        "--unshare-ipc",\n        "--unshare-uts",\n        "--unshare-cgroup",'),
        (f"{_ACCEPT}::test_r15u4_an_undeclared_network_connection_fails_closed",)),
    Arm("R15u5", "the receipt names the capabilities observed in force",
        Sabotage(_BOUNDARY,
            before='        capabilities=launched.capabilities,',
            after='        capabilities=(),'),
        (f"{_ACCEPT}::test_r15u5_the_receipt_names_the_capabilities_observed_in_force",)),
    Arm("R15u6", "a minimal run is valid and a minimal pair never derives clean-environment",
        Sabotage(_REPLAY, before=_QUALIFY_LINE, after='        if True:'),
        ("test_replay.py::test_r15_negative_a_minimal_pair_never_derives_clean_environment",
         f"{_ACCEPT}::test_r15u6_a_minimal_run_is_valid_and_a_minimal_pair_stays_same_environment")),
    # --- R4 ---
    Arm("R4u1", "the clean-environment row is reached by a confined pair through a qualifying receipt",
        Sabotage(_REPLAY,
            before='            return "clean-environment"',
            after='            return "not-certified"'),
        (f"{_ACCEPT}::test_r4u1_a_confined_pair_derives_clean_environment",
         f"{_ACCEPT}::test_end_to_end_a_passing_clean_environment_verification_admits_and_yields_belief",
         "test_replay.py::test_r4_the_clean_environment_row_is_reached_only_through_a_qualifying_receipt")),
    Arm("R4u2", "a receipt missing a required capability derives same-environment",
        Sabotage(_REPLAY, before=_CONTAINMENT, after='    if False:\n        return False'),
        ("test_replay.py::test_r4_negative_d_a_receipt_missing_a_required_capability_derives_same_environment",)),
    Arm("R4u3", "a policy providing every capability qualifies whatever its identity string",
        Sabotage(_REPLAY,
            before=_QUALIFY_LINE,
            after='        if replayed.recipe.boundary_policy.identity == "boundary-policy/confined-v1" and qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):'),
        ("test_replay.py::test_r4_negative_d_a_policy_qualifies_whatever_its_version_string",)),
    Arm("R4u4", "two incomparable policies are not ranked",
        Sabotage(_REPLAY, before=_CONTAINMENT, after='    if len(receipt.capabilities) < 2:\n        return False'),
        ("test_replay.py::test_r4_negative_d_two_incomparable_policies_are_not_ranked",)),
    # --- R9, R13, R16 ---
    Arm("R9u1", "admission does not follow an inconclusive verification",
        Sabotage(_VERIFY, before='        verdict=derived.verdict,', after='        verdict="passed",'),
        (f"{_ACCEPT}::test_r9u1_an_inconclusive_verification_admits_nothing",)),
    Arm("R13u1", "an import outside the bundle and the held environment is refused",
        # The confined request is routed through the minimal path, where the
        # outside module is reachable: the run mints instead of refusing.
        Sabotage(_BOUNDARY, before='        if boundary_policy == CONFINED_POLICY:', after='        if False:'),
        (f"{_ACCEPT}::test_r13u1_an_import_outside_the_closure_is_refused_under_confinement_and_minted_under_minimal",)),
    Arm("R16u1", "a not-certified pair with qualifying receipts admits nothing",
        Sabotage(_VERIFY, before='        scope=derived.scope,', after='        scope="clean-environment",'),
        (f"{_ACCEPT}::test_r16u1_a_not_certified_pair_admits_nothing",)),
    # --- R21 ---
    Arm("R21u1", "a write outside the output root fails closed",
        Sabotage(_CONFINEMENT, before=_REMOUNT, after='    argv.extend(["--chdir", OUTPUT_ROOT])'),
        (f"{_ACCEPT}::test_r21u1_a_write_outside_the_output_root_fails_closed",)),
    Arm("R21u2", "two differently mounted scratch roots yield equal recipes and clean-environment",
        Sabotage(_BOUNDARY,
            before='            environment_identity=snapshot.name,',
            after='            environment_identity=str(scratch),'),
        (f"{_ACCEPT}::test_r21u2_two_differently_mounted_scratch_roots_yield_equal_recipes_and_clean_environment",)),
    # --- K1: the policy match ---
    Arm("K1a", "the policy match is the entire definition",
        Sabotage(_RECIPE,
            before='        if (policy.identity, policy.scope_rule, frozenset(policy.capabilities)) == (known.identity, known.scope_rule, frozenset(known.capabilities)):',
            after='        if (policy.identity, frozenset(policy.capabilities)) == (known.identity, frozenset(known.capabilities)):'),
        ("test_confinement_values.py::test_k1_a_known_identity_with_another_scope_rule_is_unsupported",
         "test_boundary.py::test_k1_an_unsupported_policy_refuses_before_intent")),
    Arm("K1b", "a duplicate capability is unspellable",
        Sabotage(_RECIPE,
            before='        if len(set(self.capabilities)) != len(self.capabilities):\n            raise MalformedClosure("boundary policy capabilities name each capability once")',
            after='        if False:\n            raise MalformedClosure("boundary policy capabilities name each capability once")'),
        ("test_confinement_values.py::test_k1_a_duplicate_capability_is_unspellable",)),
    # --- K2: the snapshot ---
    Arm("K2a", "an existing mismatching snapshot refuses and is never rebuilt",
        Sabotage(_CONFINEMENT,
            before='    if target.exists():\n        verify_snapshot(target, captured)\n        return target',
            after='    if target.exists():\n        shutil.rmtree(target)'),
        ("test_confinement.py::test_k2_an_existing_mismatching_snapshot_refuses_and_is_never_rebuilt",)),
    Arm("K2b", "a concurrent winner is verified before it is reused",
        Sabotage(_CONFINEMENT,
            before='    except OSError:\n        shutil.rmtree(build, ignore_errors=True)\n        verify_snapshot(target, captured)',
            after='    except OSError:\n        shutil.rmtree(build, ignore_errors=True)'),
        ("test_confinement.py::test_k2_a_concurrent_winner_is_verified_and_reused_or_refused",)),
    # --- K3: receipt validation ---
    Arm("K3a", "a mount plan identity disagreeing with its mounts is malformed",
        Sabotage(_RECIPE,
            before='        if self.mount_plan_identity != mount_plan_identity(self.mounts):',
            after='        if False:'),
        ("test_confinement_values.py::test_k3_a_mount_plan_identity_disagreeing_with_its_mounts_is_malformed",)),
    Arm("K3b", "the confined members are all present or all absent",
        Sabotage(_RECIPE, before='        if present not in (0, 3):', after='        if False:'),
        ("test_confinement_values.py::test_k3_the_confined_members_are_all_present_or_all_absent",)),
    Arm("K3c", "the wire refuses a mount plan identity disagreeing with its mounts",
        Sabotage(_RUNRECORD,
            before='            _refuse("$.occurrence.receipt.instance.mount_plan_identity", "is not the digest of its own mounts")',
            after='            pass'),
        ("test_runrecord_confined.py::test_k3_a_wire_mount_plan_identity_disagreeing_with_its_mounts_is_refused",)),
    # --- K4: the domains ---
    Arm("K4a", "the minimal receipt projection is byte-stable under v1",
        Sabotage(_RECIPE,
            before='    if not receipt.confined:\n        return projection',
            after='    if False:\n        return projection'),
        ("test_confinement_values.py::test_k4_the_minimal_receipt_projection_is_byte_stable_under_v1",)),
    Arm("K4b", "a confined receipt makes a run.v2 run",
        Sabotage(_RECIPE,
            before='    return CONFINED_RUN_DOMAIN if confined else RUN_DOMAIN',
            after='    return RUN_DOMAIN'),
        ("test_confinement_values.py::test_k4_a_confined_receipt_makes_a_v2_run",
         "test_runrecord_confined.py::test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2")),
    Arm("K4c", "the wire recomputes under the domain the receipt shape names",
        Sabotage(_RUNRECORD,
            before='    address = v1.digest(run_domain_for(_is_confined_receipt(occurrence_view["receipt"])), parsed)',
            after='    address = v1.digest(run_domain_for(False), parsed)'),
        ("test_runrecord_confined.py::test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2",)),
    # --- K5: the join ---
    Arm("K5a", "admission_record carries supersedes",
        Sabotage(_VERIFY, before='        supersedes=derived.supersedes,', after='        supersedes=None,'),
        ("test_verify.py::test_k5_admission_record_carries_supersedes",)),
    Arm("K5b", "a production verification is refused by the join",
        Sabotage(_VERIFY,
            before='    if type(derived) is not AssessmentVerification:\n        raise NotAnAssessmentVerification(',
            after='    if False:\n        raise NotAnAssessmentVerification('),
        ("test_verify.py::test_k5_a_production_verification_is_refused_by_the_join",)),
    # --- K6: the gate ---
    Arm("K6a", "a namespace equal to the parent's refuses",
        Sabotage(_CONFINEMENT,
            before='    if missing := [name for name in NAMESPACES if name not in facts.distinct]:',
            after='    if False:'),
        ("test_confinement.py::test_k6_a_namespace_equal_to_the_parents_refuses",)),
    Arm("K6b", "a mount table unequal to the plan refuses",
        Sabotage(_CONFINEMENT, before='    if facts.mounts != plan.expected:', after='    if False:'),
        ("test_confinement.py::test_k6_a_mount_table_unequal_to_the_plan_refuses",)),
    Arm("K6c", "an environment unequal to the declared set refuses",
        Sabotage(_CONFINEMENT, before='    if dict(environ) != dict(environment):', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    Arm("K6d", "a routable network refuses",
        Sabotage(_CONFINEMENT, before='    if network["ipv4"] != "ENETUNREACH":', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    Arm("K6e", "a loader map unequal to the capture refuses",
        Sabotage(_CONFINEMENT, before='    if set(reported) != set(expected):', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    # --- K7: closure refusals ---
    Arm("K7a", "a SONAME collision is refused",
        Sabotage(_ADAPTER,
            before='                    if known != canonical:',
            after='                    if False:'),
        ("test_closure_capture.py::test_k7_a_soname_collision_is_refused",
         "test_closure_capture.py::test_k7_a_soname_collision_between_two_registered_roots_is_refused")),
    Arm("K7b", "a symlink escaping the closure is refused",
        Sabotage(_ADAPTER,
            before='            if target_root is None:\n                raise ClosureUnsupported(f"symlink {located} -> {target!r} escapes the closure")',
            after='            if target_root is None:\n                target_root = root'),
        ("test_closure_capture.py::test_k7_a_symlink_escaping_the_closure_is_refused",)),
    Arm("K7c", "a mixed .pth is refused",
        Sabotage(_ADAPTER, before='            if imports and paths:', after='            if False:'),
        ("test_closure_capture.py::test_k7_a_mixed_pth_is_refused",)),
)

_UNIT_OF_LETTERED = {
    "K1a": "K1", "K1b": "K1",
    "K2a": "K2", "K2b": "K2",
    "K3a": "K3", "K3b": "K3", "K3c": "K3",
    "K4a": "K4", "K4b": "K4", "K4c": "K4",
    "K5a": "K5", "K5b": "K5",
    "K6a": "K6", "K6b": "K6", "K6c": "K6", "K6d": "K6", "K6e": "K6",
    "K7a": "K7", "K7b": "K7", "K7c": "K7",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"R15": 6, "R4": 4, "R9": 1, "R13": 1, "R16": 1, "R21": 2}
LABELED_UNITS: tuple[str, ...] = tuple(f"K{number}" for number in range(1, 8))

#: No cut-13 arm cites a prior cut's check.
CO_CITED: dict[str, tuple[str, ...]] = {}
