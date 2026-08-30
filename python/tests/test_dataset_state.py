"""G9's selected arms — the upward transition, derived and never stored.

Deferred and deliberately absent here: the "minted as a world entity" clause
(W3's, needs the world boundary), the replay-eligibility third of R5's answer
(run boundary), and the three-check independence sabotage (needs R5 and R10 as
runnable checks). Cut 2 §4.2 records each.
"""

import dataclasses
import inspect

import pytest

from beliefs.dataset import (
    ByteObservation,
    CurationNote,
    DatasetDeclaration,
    Declared,
    Held,
    ResourceDeclaration,
    admission_state,
    dataset_address,
)
from beliefs.errors import MalformedRecord

D1 = "sha256:" + "11" * 32
D2 = "sha256:" + "22" * 32
D3 = "sha256:" + "33" * 32


def declaration(*digests: str | None) -> DatasetDeclaration:
    return DatasetDeclaration(
        resources=tuple(ResourceDeclaration(name=f"r{i}", digest=d) for i, d in enumerate(digests))
    )


def observed(*digests: str, location: str = "repo://data") -> tuple[ByteObservation, ...]:
    return tuple(ByteObservation(digest=d, location=location) for d in digests)


class TestTheBasisProjection:
    def test_the_address_is_the_ruled_fold(self):
        # dedupe, sort byte-wise, join and terminate with \n, utf-8, sha256.
        from hashlib import sha256

        expected = sha256((D1 + "\n" + D2 + "\n").encode("utf-8")).hexdigest()
        assert dataset_address(declaration(D2, D1)) == f"dataset:sha256:{expected}"

    def test_declared_names_and_order_do_not_participate(self):
        a = DatasetDeclaration(
            resources=(ResourceDeclaration(name="x", digest=D1), ResourceDeclaration(name="y", digest=D2))
        )
        b = DatasetDeclaration(
            resources=(ResourceDeclaration(name="renamed", digest=D2), ResourceDeclaration(name="z", digest=D1))
        )
        assert dataset_address(a) == dataset_address(b)

    def test_repetition_does_not_participate(self):
        assert dataset_address(declaration(D1, D1, D2)) == dataset_address(declaration(D1, D2))

    def test_one_unpinned_resource_leaves_no_content_identity(self):
        assert dataset_address(declaration(D1, None)) is None

    def test_an_unaccepted_algorithm_is_unpinned_not_an_error(self):
        # md5-recorded is unpinned under the accepted set; the dataset is a
        # curation note, not a refusal (ramp §6.2 — the profile's question,
        # not the tool's).
        assert dataset_address(declaration("md5:" + "ab" * 16)) is None

    def test_the_empty_declaration_is_unreachable(self):
        # sha256 of the empty string is never an address.
        assert dataset_address(declaration()) is None

    def test_a_malformed_digest_string_is_refused_at_construction(self):
        with pytest.raises(MalformedRecord):
            ResourceDeclaration(name="r", digest="sha256:NOTHEX")


class TestDeclarationDoesNotPromote:
    def test_a_content_identity_and_no_bytes_reads_declared(self):
        state = admission_state(declaration(D1), ())
        assert isinstance(state, Declared)

    def test_no_api_accepts_an_authored_held(self):
        # The state is derived, never stored: no field on any record carries it,
        # and the deriving function takes declaration + observations only.
        assert {f.name for f in dataclasses.fields(DatasetDeclaration)} == {"resources"}
        assert {f.name for f in dataclasses.fields(ResourceDeclaration)} == {"name", "digest"}
        params = inspect.signature(admission_state).parameters
        assert list(params) == ["declaration", "observations"]

    def test_an_observation_carries_no_timestamp(self):
        # Ramp §8 item 1 is open; a field would invite reading it (cut 2 §2.1).
        assert {f.name for f in dataclasses.fields(ByteObservation)} == {"digest", "location"}


class TestPresenceDoesNotPromote:
    def test_mismatching_bytes_leave_it_declared(self):
        state = admission_state(declaration(D1), observed(D2))
        assert isinstance(state, Declared)

    def test_the_mismatch_is_reported_as_a_mismatch(self):
        state = admission_state(declaration(D1), observed(D2))
        assert isinstance(state, Declared)
        outcomes = {f.declared: f for f in state.findings}
        assert outcomes[D1].outcome == "no-matching-observation-in-coverage"
        assert any(f.outcome == "mismatch" and D2 in f.observed for f in state.findings)

    def test_absence_in_a_coverage_is_not_unheld(self):
        # fb-2026-07-27-010 reached from the holding side: a failure to look is
        # not a finding of absence, so no finding may spell "unheld".
        state = admission_state(declaration(D1), ())
        assert isinstance(state, Declared)
        assert all("unheld" not in f.outcome for f in state.findings)


class TestAProperSubsetDoesNotPromote:
    def test_two_of_three_is_still_declared(self):
        assert isinstance(admission_state(declaration(D1, D2, D3), observed(D1, D2)), Declared)

    def test_the_third_promotes(self):
        assert isinstance(admission_state(declaration(D1, D2, D3), observed(D1, D2, D3)), Held)

    def test_removing_one_returns_it_to_declared(self):
        held = admission_state(declaration(D1, D2, D3), observed(D1, D2, D3))
        assert isinstance(held, Held)
        assert isinstance(admission_state(declaration(D1, D2, D3), observed(D1, D3)), Declared)

    def test_a_partly_pinned_dataset_is_a_curation_note_as_ruled(self):
        # The first partly-pinned instances anywhere (cut 2 §2.1 item 3): the
        # fixture exercises the ruled boundary; it does not corroborate the
        # ruling — ramp §6.2 is where a future argument starts.
        state = admission_state(declaration(D1, None), observed(D1))
        assert isinstance(state, CurationNote)


class TestLocationIsNotTheDiscriminator:
    def test_matching_bytes_outside_the_repository_read_held(self):
        state = admission_state(declaration(D1), observed(D1, location="https://archive.example/d1"))
        assert isinstance(state, Held)

    def test_unreachable_here_with_a_controlled_copy_leaves_both_halves_unchanged(self):
        # The digest half and the admission half of R5's answer (the
        # replay-eligibility third is the run boundary's — cut 2 §4.2). The
        # local copy gone, a far controlled copy remaining: still Held, and the
        # address cannot even see the change — it is a function of the
        # declaration alone, which the signature pins.
        decl = declaration(D1)
        assert isinstance(admission_state(decl, observed(D1, location="repo://data")), Held)
        assert isinstance(admission_state(decl, observed(D1, location="https://mirror.example/d1")), Held)
        assert list(inspect.signature(dataset_address).parameters) == ["declaration"]
