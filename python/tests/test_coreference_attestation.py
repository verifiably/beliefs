"""World resolution slice 2: the coreference attestation as a stored kind, its
capture, its seam, and its reduction (spec 2026-09-10-world-resolution-slice-2-design.md)."""

from __future__ import annotations

import pytest
from authority import ACTOR
from test_world_build import ALPHA, build, corpus_at, install_bindings, make_world
from test_world_derive import reduce_with

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.world import derive, registry, rules

LEFT = "dataset:left"
RIGHT = "dataset:right"
NFC = "caf\u00e9"      # precomposed e-acute
NFD = "cafe\u0301"     # e + combining acute: one string to every digest, two to Python


def attestation(*, endpoints=(RIGHT, LEFT), stance=1, actor=ACTOR, grounds="the same bytes", token="event-1"):
    return stored.coreference_attestation_node(
        title="coreference", endpoints=endpoints, stance=stance, actor=actor, grounds=grounds, event_token=token
    )


class TestTheKindIsGoverned:
    def test_the_kind_has_a_domain_and_one_required_covered_facet(self):
        assert stored.SEMANTIC_DOMAINS["coreference-attestation"] == stored.COREFERENCE_ATTESTATION_DOMAIN
        assert stored.COVERED_FACETS["coreference-attestation"] == (stored.COREFERENCE_ATTESTATION_FACET,)
        assert stored.WORLD_KINDS.index("coreference-attestation") == stored.WORLD_KINDS.index("act-report") - 1

    def test_the_endpoint_kinds_are_the_world_kinds_less_the_three_exclusions(self):
        assert set(stored.COREFERENCE_ENDPOINT_KINDS) == (
            set(stored.WORLD_KINDS) - {"coreference-attestation"} - set(EXCLUDED_MUTATION_KINDS)
        )
        assert stored.COREFERENCE_ENDPOINT_KINDS == (
            "proposition", "source-assertion", "assessment", "analysis-spec", "run",
            "verification", "dataset", "source", "retraction", "instrument-certification",
        )


class TestTheBuilder:
    def test_it_sorts_the_pair_digests_the_facet_and_carries_no_relations(self):
        node = attestation()
        assert node.kind == "coreference-attestation"
        assert node.facets[stored.COREFERENCE_ATTESTATION_FACET] == {
            "endpoints": [LEFT, RIGHT], "stance": 1, "actor": ACTOR,
            "grounds": "the same bytes", "event_token": "event-1",
        }
        # `_node` stamps every governed record; the facet set is exactly the two.
        assert set(node.facets) == {stored.COREFERENCE_ATTESTATION_FACET, "semantic-identity"}
        stamp = stored.stored_semantic_hash(node)
        assert stamp is not None
        assert len(stamp) == 64
        assert node.relations == []
        assert node.id == "coreference-attestation:" + v1.digest(
            stored.COREFERENCE_ATTESTATION_DOMAIN, node.facets[stored.COREFERENCE_ATTESTATION_FACET]
        )
        assert node.id == attestation(endpoints=(LEFT, RIGHT)).id

    def test_two_tokens_are_two_records(self):
        assert attestation(token="event-1").id != attestation(token="event-2").id

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"endpoints": (LEFT, LEFT)},
            {"endpoints": (LEFT,)},
            {"endpoints": (LEFT, "")},
            {"stance": 0},
            {"stance": 2},
            {"stance": True},
            {"grounds": ""},
            {"token": ""},
            {"grounds": NFD},
            {"endpoints": (LEFT, "dataset:" + NFD)},
        ],
    )
    def test_every_malformed_field_is_refused(self, kwargs):
        with pytest.raises(MalformedRecord):
            attestation(**kwargs)

    def test_an_empty_actor_is_the_actor_rule_s_own_error(self):
        with pytest.raises(ValueError):
            attestation(actor="")


class TestTheReader:
    def test_it_round_trips_the_builder(self):
        value = stored.coreference_attestation_value(attestation())
        assert value == stored.CoreferenceAttestation((LEFT, RIGHT), 1, ACTOR, "the same bytes", "event-1")

    @pytest.mark.parametrize(
        "edit",
        [
            lambda f: f.pop("event_token"),
            lambda f: f.update(extra=1),
            lambda f: f.update(endpoints=[RIGHT, LEFT]),
            lambda f: f.update(endpoints=[LEFT, LEFT]),
            lambda f: f.update(stance=-2),
            lambda f: f.update(stance=True),
            lambda f: f.update(grounds=NFD),
            lambda f: f.update(actor=""),
        ],
    )
    def test_every_malformed_facet_is_refused_naming_the_record(self, edit):
        node = attestation()
        edit(node.facets[stored.COREFERENCE_ATTESTATION_FACET])
        with pytest.raises(MalformedRecord, match=node.id):
            stored.coreference_attestation_value(node)

    def test_a_record_without_the_facet_is_refused(self):
        node = attestation()
        node.facets.clear()
        with pytest.raises(MalformedRecord):
            stored.coreference_attestation_value(node)


def endpoints_and(*attestations):
    """Two datasets and the attestations over them, as raw stored nodes."""
    return (
        stored.dataset_node("left", title="left", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]),
        stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]),
        *attestations,
    )


class TestTheRuleNormalizes:
    def test_the_unicode_fixture_ships_and_reduces_to_one_unit(self):
        bundle = next(b for b in rules.shipped_rule_bundles() if b.symbol == "reduce_coreference")
        assert any(name == "coreference.unicode.yaml" for name, _ in bundle.fixtures)

    def test_two_normalization_forms_of_one_grounds_are_one_unit(self):
        capture = {
            "coverage": ["corpus-a"],
            "records": [
                {
                    "corpus_id": "corpus-a", "address": f"coreference:{n}", "uid": f"uid-{n}",
                    "kind": "coreference-attestation", "deprecated_ids": [], "produces": [],
                    "retraction": None, "certification": None,
                    "coreference": {
                        "endpoints": ["address-a", "address-b"], "stance": 1, "actor": "alice",
                        "grounds": grounds, "event_token": f"event-{n}",
                    },
                }
                for n, grounds in ((1, NFC), (2, NFD))
            ],
        }
        produced = reduce_with("reduce_coreference", capture)
        assert produced == {"pairs": [{"endpoints": ["address-a", "address-b"], "balance": 1, "distinct_key_count": 1}]}


class TestTheCapturedValue:
    def test_non_nfc_text_is_refused(self):
        with pytest.raises(ValueError, match="NFC"):
            derive.CapturedCoreference(("a", "b"), 1, "alice", NFD, "event-1")


class TestTheCaptureLift:
    def test_a_stored_attestation_is_captured_and_reduced(self, tmp_path):
        alpha = corpus_at(tmp_path / "alpha", ALPHA, endpoints_and(attestation(), attestation(token="event-2")))
        world = make_world(tmp_path, alpha)
        world.admit(alpha, provenance=registry.Fresh())
        draft = build(world, (ALPHA,), install_bindings(world))
        captured = [r for r in draft.capture.corpora[0].records if r.kind == "coreference-attestation"]
        assert len(captured) == 2
        by_token = {}
        for record in captured:
            assert record.coreference is not None
            by_token[record.coreference.event_token] = record.coreference
        assert by_token == {
            token: derive.CapturedCoreference((LEFT, RIGHT), 1, ACTOR, "the same bytes", token)
            for token in ("event-1", "event-2")
        }
        assert dict(derive.coreference_map(draft.run("coreference-reduction")).pairs) == {(LEFT, RIGHT): (1, 1)}

    def test_grounds_rewritten_between_normalization_forms_is_refused_at_capture(self, tmp_path):
        from fixtures_cut4 import path_for

        node = attestation(grounds=NFC)
        alpha = corpus_at(tmp_path / "alpha", ALPHA, endpoints_and(node))
        path = path_for(alpha, node.id)
        text = path.read_text(encoding="utf-8")
        assert NFC in text and NFD not in text
        path.write_text(text.replace(NFC, NFD), encoding="utf-8")  # the probe: identity-equal bytes, reduction-distinct
        world = make_world(tmp_path, alpha)
        world.admit(alpha, provenance=registry.Fresh())
        with pytest.raises(MalformedRecord, match="NFC"):
            build(world, (ALPHA,), install_bindings(world))
