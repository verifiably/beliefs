"""Relabel arms and the measured R23 divergence arm (slice 3 design §7)."""

from __future__ import annotations

import shutil

import pytest
import yaml
from nodes.core.write_plan import DefaultExecutor
from test_relocation_rows import _belief_digest
from test_world_build import ALPHA, BETA, ChainHeads, sample_nodes, slug_for
from test_world_receipts import TEST_RECEIPT_KINDS, corpora, hold_shipped, publish, world_over
from test_world_view import chain_nodes

from beliefs import stored
from beliefs.corpus import lineage_snapshot
from beliefs.errors import CoverageUnknown, CoverageUnresolvable
from beliefs.lineage import certify, divergence_state, snapshot_projection
from beliefs.world import read, registry
from beliefs.world.view import open_world_view


class TestW13:
    def test_moving_renaming_and_remounting_a_root_changes_no_identity(self, tmp_path):
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        first = publish(world, coverage, bindings)
        before = (first.coverage, first.documents["producer-snapshot.yaml"], _belief_digest(first))

        for relocation in ("moved", "renamed-differently", "cloned"):
            target = tmp_path / relocation
            if relocation == "cloned":
                shutil.copytree(roots[BETA], target)
                shutil.rmtree(roots[BETA])  # the clone is mounted *instead*: two live carriers are X5's refusal
            else:
                roots[BETA].rename(target)
            roots[BETA] = target
            world = registry.World(
                registry.WorldConfig(world.config.world_root, world.config.world_id, tuple(roots.values())),
                DefaultExecutor,
                chain_head=ChainHeads(),
                corpus_executor_factory=DefaultExecutor,
                authority=world.authority,
            )
            again = publish(world, coverage, bindings)
            assert registry.load_manifest(target).corpus_id == BETA
            assert (again.coverage, again.documents["producer-snapshot.yaml"], _belief_digest(again)) == before

    def test_a_coordinated_forgery_is_undetected_and_reads_as_a_fork(self, tmp_path):
        from fixtures_cut6 import PINS

        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        published = publish(world, coverage, bindings)
        replica = tmp_path / "replica"
        shutil.copytree(roots[BETA], replica)  # a pre-edit replica, unmounted for now

        forged_id = "d" * 32
        forged_manifest = registry.CorpusManifest(2, forged_id, PINS)
        (roots[BETA] / "corpus.yaml").write_bytes(registry.manifest_bytes(forged_manifest))
        admission = registry.AdmissionRecord(forged_manifest, registry.Fresh(), "forger")
        record_dir = world.config.world_root / "registry"
        (record_dir / f"{registry.admission_digest(admission)}.yaml").write_bytes(
            yaml.safe_dump(registry.admission_projection(admission), sort_keys=True).encode("utf-8")
        )

        forged = publish(world, (ALPHA, forged_id), bindings)  # proceeds: nothing detects the coordinated act
        assert forged_id in dict(forged.coverage)
        status = world.status(forged_id)
        assert (status.known, status.live, status.present, status.findings) == (True, True, True, ())
        assert all(
            read.validate_receipt(world, published, kind).outcome == "unresolvable" for kind in TEST_RECEIPT_KINDS
        )  # states moved with the id

        roots[BETA] = replica
        world = registry.World(
            registry.WorldConfig(world.config.world_root, world.config.world_id, (roots[ALPHA], replica, tmp_path / "moved-forged")),
            DefaultExecutor,
            chain_head=ChainHeads(),
            corpus_executor_factory=DefaultExecutor,
            authority=world.authority,
        )
        assert all(
            read.validate_receipt(world, published, kind).outcome == "validated" for kind in TEST_RECEIPT_KINDS
        )  # the replica validates
        scan = registry._scan_registry(world.config.world_root)
        assert {a.manifest.corpus_id for a in scan.admissions} == {ALPHA, BETA, forged_id}  # two admissions, as a fork's registry reads
        assert not any(a.manifest.forked_from for a in scan.admissions if a.manifest.corpus_id == forged_id)  # and no assertion ties them

    def test_raw_deleting_an_admission_evades_nothing(self, tmp_path):
        """Cut 6 read the undetected half; the build's refusal is the other half."""
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        for record in (world.config.world_root / "registry").iterdir():
            if BETA in record.read_text(encoding="utf-8"):
                record.unlink()
        with pytest.raises(CoverageUnknown):
            publish(world, coverage, bindings)


class TestX5:
    def test_two_carriers_of_one_id_refuse_the_build_and_offer_no_repair(self, tmp_path):
        """The build arm (cut 7) re-read as X5's whole: refusal, reported, no merge."""
        coverage = (ALPHA,)
        roots = corpora(tmp_path, {ALPHA: sample_nodes("one")})
        twin = tmp_path / "twin"
        shutil.copytree(roots[ALPHA], twin)
        world = world_over(tmp_path, roots, also_configured=(twin,))
        bindings = hold_shipped(world)
        with pytest.raises(CoverageUnresolvable) as refused:
            publish(world, coverage, bindings)
        assert "exactly one configured carrier root" in str(refused.value)
        assert str(twin) in str(refused.value)
        assert not hasattr(world, "merge") and not hasattr(world, "consolidate")


class TestR23Divergence:
    def test_a_run_in_the_other_corpus_claiming_the_dataset_diverges_and_moves_the_digest(self, tmp_path):
        """Negative (e), cross-corpus: R2 in BETA claims D (held once, in ALPHA)
        from B by edges alone — no second D record (spec §7)."""
        d0, r1, d1, _r2, _d2 = chain_nodes()
        b = stored.dataset_node("b", title="b")
        r2 = stored.run_node("r2x", title="r2x", spec="s", transforms=[b.id], produces=[d1.id])
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {ALPHA: (d0, r1, d1), BETA: (b, r2)})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        published = publish(world, coverage, bindings)
        view = open_world_view(world, published)

        snapshot = lineage_snapshot(view, [d1.id])
        assert divergence_state(snapshot, d1.id) == "divergent"
        certification = certify(snapshot, (d1.id,), (d0.id,))
        assert certification.state == "not-certified" and "lineage-divergent" in certification.findings
        with_r2 = snapshot_projection(snapshot)

        roots_without = corpora(tmp_path / "without", {ALPHA: (d0, r1, d1), BETA: (b,)})
        world_without = world_over(tmp_path / "without", roots_without)
        published_without = publish(world_without, coverage, hold_shipped(world_without))
        without_r2 = snapshot_projection(lineage_snapshot(open_world_view(world_without, published_without), [d1.id]))
        assert with_r2 != without_r2  # the lineage member moves with the producer set
        assert _belief_digest(published) != _belief_digest(published_without)  # and so does kernel §5.1's digest: the snapshot covers the producer set
