"""Cut 4's durable arms over the write boundary and the read of what it wrote.

Every test here runs against the certified engine on a real volume. What is new
compared with the portable tests is not the code under test but the claim: a
record **lands** at an address on disk, and it **reloads**, so "not refused" and
"the reader said nothing" are assertions about a read this cut actually runs.
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pytest
from authority import FULL
from durable_fixture import (
    ASSESSMENT,
    PROPOSITION,
    RAW,
    RULE,
    RUN,
    SPEC,
    mint_records,
    observed_dataset,
    pinned,
    slug,
)
from fixtures_cut4 import path_for, raw_write, reopen
from nodes.core.errors import ExecutionError
from profiles import BASE

from beliefs import stored
from beliefs.corpus import corpus_check
from beliefs.errors import BasisMissing, EligibilityUnmet, SemanticHashStale
from beliefs.root import GENESIS_PAYLOAD, init_corpus_root, metadata_root_for, open_corpus


class TestTheInitAct:
    def test_a_registered_root_carries_the_engines_chain(self, durable_root):
        assert (durable_root / ".#~chain").is_dir()

    def test_the_metadata_store_is_the_sibling_of_the_corpus_root(self, durable_root):
        assert metadata_root_for(durable_root).is_dir()
        assert metadata_root_for(durable_root).parent == durable_root.parent

    def test_registering_twice_on_a_matching_payload_is_idempotent(self, durable_root):
        init_corpus_root(durable_root, authority=FULL)  # the act is re-runnable, not a second genesis
        assert len(list((durable_root / ".#~chain").iterdir())) == 1

    def test_the_genesis_payload_is_what_was_registered(self, durable_root):
        entry = next(iter((durable_root / ".#~chain").iterdir()))
        encoded = base64.b64encode(GENESIS_PAYLOAD).decode("ascii")
        assert encoded in entry.read_text(encoding="utf-8")

    def test_a_write_against_an_unregistered_root_refuses(self, work_directory):
        unregistered = work_directory / "unregistered"
        unregistered.mkdir(parents=True, exist_ok=True)
        try:
            with pytest.raises(ExecutionError) as refused:
                open_corpus(unregistered, authority=FULL, profile=BASE).add(observed_dataset())
            # Init is an explicit act, not a fallback the add performs.
            assert (refused.value.index, refused.value.applied) == (None, 0)
            assert refused.value.__cause__ is not None
        finally:
            shutil.rmtree(unregistered, ignore_errors=True)
            shutil.rmtree(metadata_root_for(unregistered), ignore_errors=True)


class TestTheDurableMint:
    def test_a_minted_record_lands_at_its_address(self, durable_writer, durable_root):
        minted = durable_writer.add(observed_dataset())
        assert path_for(durable_root, minted.id).is_file()

    def test_a_minted_record_reloads_through_a_fresh_facade(self, durable_writer, durable_root):
        minted = durable_writer.add(observed_dataset())
        assert reopen(durable_root).get(minted.id).uid == minted.uid

    def test_the_created_file_carries_the_adapters_one_mode(self, durable_writer, durable_root):
        minted = durable_writer.add(observed_dataset())
        assert path_for(durable_root, minted.id).stat().st_mode & 0o777 == 0o644

    def test_every_mint_is_chained(self, durable_writer, durable_root):
        before = len(list((durable_root / ".#~chain").iterdir()))
        durable_writer.add(observed_dataset())
        # Chained but unanchored: the engine's registration append happens
        # inside every transaction regardless, and no anchor act exists in this
        # slice, so the tail grows without bound and its extent is unreported.
        assert len(list((durable_root / ".#~chain").iterdir())) > before


class TestW3Durably:
    def test_a_source_with_no_accepted_external_identifier_is_refused_before_it_lands(
        self, durable_writer, durable_root
    ):
        with pytest.raises(BasisMissing):
            durable_writer.add(stored.source_node("s1", title="A paper", identifiers={}))
        assert not path_for(durable_root, "source:s1").exists()

    def test_a_dataset_with_no_content_identity_is_refused_before_it_lands(self, durable_writer, durable_root):
        with pytest.raises(BasisMissing):
            durable_writer.add(stored.dataset_node("d1", title="DepMap", resources=[]))
        assert not path_for(durable_root, "dataset:d1").exists()

    def test_supplying_the_basis_afterwards_is_a_second_separate_mint(self, durable_writer, durable_root):
        with pytest.raises(BasisMissing):
            durable_writer.add(stored.source_node("s1", title="A paper", identifiers={}))
        second = durable_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
        assert reopen(durable_root).holds(second.id)


class TestG9DurablyMintedWithNoBytesHeld:
    def test_a_declared_dataset_is_minted_and_is_referenceable(self, durable_writer, durable_root):
        declared = durable_writer.add(stored.dataset_node("declared", title="DepMap 24Q2", resources=pinned()))
        durable_writer.add(
            stored.run_node("r9", title="r9", spec=SPEC, reads=[declared.id])
        )
        view = reopen(durable_root)
        # Addressable, referenceable, and resolved as a reference by this cut's
        # traversal — while its bytes are held nowhere and no holding check ran.
        assert view.holds(declared.id)
        assert view.resolve(declared.id) == declared.id
        assert [edge.relation.target for edge in view.inbound(declared.id)] == [declared.id]

    def test_no_heldness_is_stored_on_the_minted_record(self, durable_writer, durable_root):
        declared = durable_writer.add(stored.dataset_node("declared", title="DepMap 24Q2", resources=pinned()))
        facets = reopen(durable_root).get(declared.id).facets
        assert "held" not in facets and "held" not in facets[stored.DATASET_FACET]


class TestS7BothBoundariesDurably:
    def test_the_add_path_refuses_an_inadmissible_assesses_edge(self, durable_writer, durable_root):
        durable_writer.add(stored.run_node("r2", title="r2", spec=SPEC))  # no observes input
        durable_writer.add(stored.proposition_node("p2", title="p2", claim={"operator": "affects"}))
        with pytest.raises(EligibilityUnmet):
            durable_writer.add(
                stored.assessment_node(
                    "a2",
                    title="a2",
                    spec=SPEC,
                    run="run:r2",
                    proposition="proposition:p2",
                    outcome="supported",
                    interpretation_rule=RULE,
                )
            )
        assert not path_for(durable_root, "assessment:a2").exists()

    def test_the_corpus_check_reports_a_raw_written_violation(self, durable_writer, durable_root):
        durable_writer.add(stored.run_node("r2", title="r2", spec=SPEC))
        durable_writer.add(stored.proposition_node("p2", title="p2", claim={"operator": "affects"}))
        raw_write(
            durable_root,
            stored.assessment_node(
                "a2",
                title="a2",
                spec=SPEC,
                run="run:r2",
                proposition="proposition:p2",
                outcome="supported",
                interpretation_rule=RULE,
            ),
        )
        findings = corpus_check(reopen(durable_root), BASE)
        assert [(f.severity, f.code, f.ref) for f in findings] == [
            ("error", "eligibility-unmet", "assessment:a2")
        ]

    def test_the_check_is_silent_on_the_minted_corpus(self, durable_writer, durable_root):
        mint_records(durable_writer)
        assert corpus_check(reopen(durable_root), BASE) == ()


class TestS8TheNegative:
    """Write a corpus file with a raw filesystem call and assert the static
    check does **not** fire — the limit pinned, then read through the stale-hash
    check and the corpus check."""

    def test_a_raw_write_lands_a_node_no_capability_check_can_see(self, durable_writer, durable_root):
        mint_records(durable_writer)
        smuggled = stored.dataset_node("smuggled", title="smuggled", resources=pinned())
        raw_write(durable_root, smuggled)
        assert reopen(durable_root).holds(smuggled.id)

    def test_the_static_check_stays_silent_about_it(self, durable_writer, durable_root):
        # S8 is bounded to the capability, and this is the bound: nothing static
        # distinguishes a raw write to a corpus path from writing any other file.
        from test_capability_boundary import imported_modules, modules, names_of, parsed, relative

        raw_write(durable_root, stored.dataset_node("smuggled", title="smuggled", resources=pinned()))
        for module in modules():
            if relative(module) == "corpus.py":
                continue
            assert "Corpus" not in names_of(parsed(module))
            assert "nodes.core.corpus" not in imported_modules(parsed(module))

    def test_a_self_consistent_raw_write_passes_both_reads(self, durable_writer, durable_root):
        raw_write(durable_root, stored.dataset_node("smuggled", title="smuggled", resources=pinned()))
        view = reopen(durable_root)
        assert view.get("dataset:smuggled").id == "dataset:smuggled"  # the stale-hash check has nothing to say
        assert corpus_check(view, BASE) == ()  # and neither has the corpus check

    def test_a_raw_write_that_moved_the_fields_alone_is_refused_on_read(self, durable_writer, durable_root):
        stale = stored.dataset_node("stale", title="stale", resources=pinned())
        stale.facets[stored.DATASET_FACET]["resources"] = []  # fields moved, stamp did not
        raw_write(durable_root, stale)
        with pytest.raises(SemanticHashStale):
            reopen(durable_root).get(stale.id)

    def test_the_chain_records_transactions_and_not_the_filesystem_beneath_them(self, durable_writer, durable_root):
        before = len(list((durable_root / ".#~chain").iterdir()))
        raw_write(durable_root, stored.dataset_node("smuggled", title="smuggled", resources=pinned()))
        assert len(list((durable_root / ".#~chain").iterdir())) == before


class TestTheUncertifiedTupleFailsClosed:
    """The engine's fail-closed obligation, exercised as the engine's refusal
    and surfaced through §4's mapping. The fixture **errors** if `/dev/shm` is
    unavailable rather than requiring a privileged mount."""

    def test_a_write_on_an_uncertified_tuple_refuses(self):
        shm = Path("/dev/shm")
        if not shm.is_dir():
            raise AssertionError(
                "/dev/shm is unavailable, so the uncertified-tuple negative cannot run; "
                "this is an error and not a skip"
            )
        root = shm / f"science-uncertified-{id(self)}"
        try:
            with pytest.raises(Exception) as refused:
                init_corpus_root(root, authority=FULL)
            assert "allowlist" in str(refused.value) or "barrier-option" in str(refused.value)
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)

    def test_science_holds_no_tuple_data_of_its_own(self):
        import beliefs.root as composition_root

        source = Path(composition_root.__file__).read_text(encoding="utf-8")
        for forbidden in ("CERTIFIED_ALLOWLIST", "DurabilityAllowlist", "AllowlistEntry", "ext4"):
            assert forbidden not in source


class TestTheMintedRecordsReadBack:
    def test_the_assessment_reads_back_as_the_value_it_was_minted_from(self, minted_corpus):
        view = reopen(minted_corpus)
        value = stored.assessment_value(view.get(ASSESSMENT))
        assert (value.spec, value.run, value.proposition) == (SPEC, RUN, PROPOSITION)
        assert value.outcome == "supported"

    def test_the_observed_dataset_reads_back_with_its_facet(self, minted_corpus):
        assert stored.is_empirical_observation(reopen(minted_corpus).get(RAW))

    def test_the_run_reads_back_with_its_role_partitioned_inputs(self, minted_corpus):
        run = reopen(minted_corpus).get(RUN)
        assert stored.inputs_of(run, stored.OBSERVES) == (RAW,)
        assert stored.inputs_of(run, stored.READS) == ()

    def test_the_minted_corpus_reports_nothing(self, minted_corpus):
        assert corpus_check(reopen(minted_corpus), BASE) == ()

    def test_the_slug_helper_addresses_the_same_file_the_store_does(self, minted_corpus):
        assert path_for(minted_corpus, RAW).name == f"{slug(RAW)}.md"
