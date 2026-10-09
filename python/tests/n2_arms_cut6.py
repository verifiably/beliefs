"""Cut 6's 22 frozen world-registry arms and exact sabotages."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT6_ARMS"]


_KNOWN_ID_DISABLED = Sabotage(
    module="world.py",
    before="            if any(record.corpus_id == candidate.corpus_id for record in self._state.registry.admissions):",
    after="            if False:",
)

_REGISTERED_PATHS = "            registered_paths=tuple(dict.fromkeys(operation.path for operation in plan)),"


CUT6_ARMS = (
    Arm(
        row="X4",
        asserts="no public registry purge, replace, or delete operation is spellable",
        sabotage=Sabotage(
            module="world.py",
            before="    def registry(self) -> RegistryView:\n",
            after="    def purge(self) -> None:\n        pass\n\n    def registry(self) -> RegistryView:\n",
        ),
        checks=("test_world_registry.py::test_world_public_surface_has_no_registry_mutator",),
    ),
    Arm(
        row="X4",
        asserts="raw deletion of an admission remains undetected",
        sabotage=Sabotage(
            module="world.py",
            before="        for path in registry.iterdir():",
            after=(
                "        paths = tuple(registry.iterdir())\n"
                "        if not paths:\n"
                '            raise RegistryMalformed("empty registry")\n'
                "        for path in paths:"
            ),
        ),
        checks=("test_world_registry.py::test_raw_admission_deletion_is_undetected",),
    ),
    Arm(
        row="X5",
        asserts="a known id refuses fresh and replica-of admission provenance",
        sabotage=_KNOWN_ID_DISABLED,
        checks=("test_world_registry.py::test_known_id_refuses_fresh_and_replica_provenance",),
    ),
    Arm(
        row="X6",
        asserts="retirement is terminal and no act returns the corpus to live",
        sabotage=_KNOWN_ID_DISABLED,
        checks=("test_world_registry.py::test_retired_corpus_has_no_return_to_live_act",),
    ),
    Arm(
        row="X6",
        asserts="restoring one replica recomputes presence without another admission",
        sabotage=Sabotage(
            module="world.py",
            before="    return CorpusStatus(known, live, len(carriers) == 1, findings)",
            after="    return CorpusStatus(known, live, False, findings)",
        ),
        checks=("test_world_registry.py::test_replica_restoration_recomputes_presence_without_admission",),
    ),
    Arm(
        row="X6",
        asserts="status reduction is invariant under record order",
        sabotage=Sabotage(
            module="world.py",
            before="    live = known and not any(record.corpus_id == corpus_id for record in view.statuses)",
            after=("    live = known and (not view.statuses or view.statuses[-1].corpus_id != corpus_id)"),
        ),
        checks=("test_world_registry.py::test_status_reduction_is_record_order_invariant",),
    ),
    Arm(
        row="W13",
        asserts="fresh corpus ids are opaque and stable across moves and re-clones",
        sabotage=Sabotage(
            module="corpus.py",
            before="            manifest = CorpusManifest(2, secrets.token_hex(16), checked_profile)",
            after='            manifest = CorpusManifest(2, "0" * 32, checked_profile)',
        ),
        checks=("test_manifest.py::test_fresh_id_is_opaque_and_survives_root_moves_and_reclones",),
    ),
    Arm(
        row="W13",
        asserts="no ordinary API remints an existing corpus manifest",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            if manifest_path.exists() or manifest_path.is_symlink():\n"
                '                raise ManifestAlreadyPresent(f"{manifest_path}: manifest already present")'
            ),
            after=(
                "            if manifest_path.exists() or manifest_path.is_symlink():\n"
                "                manifest_path.unlink()"
            ),
        ),
        checks=("test_manifest.py::test_existing_manifest_refuses_remint",),
    ),
    Arm(
        row="W13",
        asserts="node content, produces relations, and facets move state while semantic identity stands",
        sabotage=Sabotage(
            module="world.py",
            before='            node_identity = v1.digest("science.node-content.v1", _lift_json(value))',
            after=(
                '            value.pop("relations", None)\n'
                '            value.pop("facets", None)\n'
                '            node_identity = v1.digest("science.node-content.v1", _lift_json(value))'
            ),
        ),
        checks=(
            "test_corpus_state.py::test_node_content_and_produces_relations_move_state_while_semantic_identity_stands",
        ),
    ),
    Arm(
        row="W13",
        asserts="reordering node relations moves corpus state",
        sabotage=Sabotage(
            module="world.py",
            before='        return ["array", [_lift_json(member) for member in value]]',
            after='        return ["array", [_lift_json(member) for member in sorted(value, key=repr)]]',
        ),
        checks=("test_corpus_state.py::test_relation_reordering_moves_state",),
    ),
    Arm(
        row="W13",
        asserts="filesystem and manifest-format changes are inert",
        sabotage=Sabotage(
            module="world.py",
            before='        "manifest": manifest_projection(manifest),\n        "nodes": sorted(members, key=lambda member: member["uid"]),',
            after=(
                '        "manifest": manifest_projection(manifest),\n'
                '        "raw_manifest": (Path(corpus_root) / "corpus.yaml").read_text(encoding="utf-8"),\n'
                '        "nodes": sorted(members, key=lambda member: member["uid"]),'
            ),
        ),
        checks=("test_corpus_state.py::test_filesystem_and_formatting_changes_are_inert",),
    ),
    Arm(
        row="W13",
        asserts="every semantic manifest member moves corpus state",
        sabotage=Sabotage(
            module="world.py",
            before='        "manifest": manifest_projection(manifest),',
            after='        "manifest": {"corpus_id": manifest.corpus_id},',
        ),
        checks=("test_corpus_state.py::test_every_semantic_manifest_member_moves_state",),
    ),
    Arm(
        row="W13",
        asserts="manifest damage refuses before digesting",
        sabotage=Sabotage(
            module="world.py",
            before=(
                "    if type(value) is not dict or set(value) != expected or "
                "any(type(key) is not str for key in value):"
            ),
            after="    if type(value) is not dict or any(type(key) is not str for key in value):",
        ),
        checks=("test_corpus_state.py::test_manifest_damage_refuses_before_digesting",),
    ),
    Arm(
        row="W13",
        asserts="git state is not a corpus-state identity member",
        sabotage=Sabotage(
            module="world.py",
            before='        "nodes": sorted(members, key=lambda member: member["uid"]),',
            after=(
                '        "git_head": __import__("subprocess").check_output('
                '["git", "rev-parse", "HEAD"], cwd=corpus_root, text=True).strip(),\n'
                '        "nodes": sorted(members, key=lambda member: member["uid"]),'
            ),
        ),
        checks=("test_corpus_state.py::test_git_is_not_an_identity_member",),
    ),
    Arm(
        row="labeled:admission-idempotency",
        asserts="an exact admission retry succeeds without a second file (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="world.py",
            before="                if admission_digest(record) == digest:",
            after="                if False:",
        ),
        checks=("test_world_registry.py::test_exact_admission_retry_is_success_without_second_file",),
    ),
    Arm(
        row="labeled:status-idempotency",
        asserts="exact status retries succeed and differing terminal acts refuse (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="world.py",
            before="                if status_digest(record) == digest:",
            after="                if False:",
        ),
        checks=("test_world_registry.py::test_status_retry_is_idempotent_and_differing_terminal_acts_refuse",),
    ),
    Arm(
        row="labeled:initialization-idempotency",
        asserts="world initialization recovers between genesis and mirror (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="root.py",
            before=(
                "    if _load_world_mirror(root) != config.world_id:\n"
                '        raise WorldIdMismatch(f"{mirror}: world_id does not match configuration")'
            ),
            after=(
                "    if _load_world_mirror(root) == config.world_id:\n"
                '        raise WorldIdMismatch(f"{mirror}: matching world_id refused")'
            ),
        ),
        checks=("acceptance/test_n2_cut6.py::test_world_initialization_recovers_between_genesis_and_mirror",),
    ),
    Arm(
        row="labeled:durable-mirror",
        asserts="the committed mirror registration names world.yaml (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="root.py",
            before=_REGISTERED_PATHS,
            after=(
                "            registered_paths=tuple(path for path in dict.fromkeys(operation.path for operation in plan) "
                'if path != "world.yaml"),'
            ),
        ),
        checks=("acceptance/test_n2_cut6.py::test_world_mirror_registration_names_world_yaml",),
    ),
    Arm(
        row="labeled:durable-manifest",
        asserts="the committed manifest registration names corpus.yaml (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="root.py",
            before=_REGISTERED_PATHS,
            after=(
                "            registered_paths=tuple(path for path in dict.fromkeys(operation.path for operation in plan) "
                'if path != "corpus.yaml"),'
            ),
        ),
        checks=("acceptance/test_n2_cut6.py::test_manifest_registration_names_corpus_yaml",),
    ),
    Arm(
        row="labeled:durable-registry",
        asserts="committed admission and status registrations name their registry paths (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="root.py",
            before=_REGISTERED_PATHS,
            after=(
                "            registered_paths=tuple(path for path in dict.fromkeys(operation.path for operation in plan) "
                'if not path.startswith("registry/")),'
            ),
        ),
        checks=("acceptance/test_n2_cut6.py::test_registry_registrations_name_each_record_path",),
    ),
    Arm(
        row="labeled:duplicate-carrier",
        asserts="duplicate carriers are reported as a distinct finding (world-registry specification §5.4 and §7)",
        sabotage=Sabotage(
            module="world.py",
            before="    if len(carriers) > 1:",
            after="    if False:",
        ),
        checks=("test_world_registry.py::test_duplicate_carriers_are_a_distinct_finding",),
    ),
    Arm(
        row="labeled:manifest-malformed",
        asserts="corpus check distinguishes a malformed manifest from an absent one (world-registry specification §8.1)",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "        except ManifestMalformed as refused:\n"
                "            findings.append(\n"
                "                Finding(\n"
                '                    severity="error",\n'
                '                    code="manifest-malformed",\n'
                '                    ref="corpus.yaml",\n'
                "                    detail=str(refused),\n"
                "                    message=str(refused),\n"
                "                )\n"
                "            )"
            ),
            after="        except ManifestMalformed:\n            pass",
        ),
        checks=("test_manifest.py::test_corpus_check_distinguishes_malformed_from_absent_manifest",),
    ),
)
