"""World resolution slice 2: the coreference attestation as a stored kind, its
capture, its seam, and its reduction (spec 2026-09-10-world-resolution-slice-2-design.md)."""

from __future__ import annotations

import pytest
from authority import ACTOR, FULL, lacking
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, WITH_BIOLOGY
from test_corpus_write import Recorder
from test_session_writer import DIGEST, make_session
from test_world_build import ALPHA, build, corpus_at, install_bindings, make_world
from test_world_derive import reduce_with
from test_world_receipts import corpora, hold_shipped, publish, world_over

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS, CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    CoreferenceEndpointRefused,
    ImportRefused,
    MalformedRecord,
    PermitExceeded,
    ValidationRefused,
    WriteRefused,
)
from beliefs.identity import v1
from beliefs.permit import RequiredCapabilities
from beliefs.session.writer import ScopedWriter
from beliefs.world import derive, registry, rules
from beliefs.world.view import open_world_view

LEFT = "dataset:left"
RIGHT = "dataset:right"
NFC = "caf\u00e9"      # precomposed e-acute
NFD = "cafe\u0301"     # e + combining acute: one string to every digest, two to Python
PINNED = [{"name": "d", "digest": "sha256:" + "1" * 64}]
ATTESTING = RequiredCapabilities.for_kinds({"dataset", "coreference-attestation"}, {})


def attestation(*, endpoints=(RIGHT, LEFT), stance=1, actor=ACTOR, grounds="the same bytes", token="event-1"):
    return stored.coreference_attestation_node(
        title="coreference", endpoints=endpoints, stance=stance, actor=actor, grounds=grounds, event_token=token
    )


@pytest.fixture()
def writer(request, tmp_path) -> CorpusWriter:
    Recorder.plans.clear()
    callspec = getattr(request.node, "callspec", None)
    root = tmp_path / callspec.id if callspec is not None else tmp_path
    w = CorpusWriter(root / "corpus", Recorder, authority=FULL, profile=BASE)
    w.add(stored.dataset_node("left", title="left", resources=PINNED))
    w.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
    return w


class TestTheSeam:
    def test_it_mints_and_touches_neither_endpoint(self, writer):
        before = {ref: writer.read_view.get(ref).model_dump() for ref in (LEFT, RIGHT)}
        minted = writer.attest_coreference(attestation())
        assert writer.read_view.get(minted.id).facets == minted.facets
        assert {ref: writer.read_view.get(ref).model_dump() for ref in (LEFT, RIGHT)} == before
        assert minted.relations == [] and writer.read_view.inbound(LEFT) == []

    def test_add_supersede_and_revise_refuse_the_kind(self, writer):
        with pytest.raises(WriteRefused, match="attest_coreference"):
            writer.add(attestation())
        with pytest.raises(WriteRefused, match="attest_coreference"):
            writer.supersede(attestation(), of=LEFT)
        with pytest.raises(WriteRefused, match="attest_coreference"):
            writer.revise(attestation())

    def test_the_permit_is_required_before_the_hold(self, tmp_path):
        w = CorpusWriter(tmp_path / "c", Recorder, authority=lacking(kinds=("coreference-attestation",)), profile=BASE)
        with pytest.raises(PermitExceeded):
            w.attest_coreference(attestation())

    def test_the_actor_is_bound(self, writer):
        with pytest.raises(ActorMismatch):
            writer.attest_coreference(attestation(actor="someone-else"))

    def test_a_raw_self_pair_reaches_its_own_refusal(self, writer):
        node = attestation()
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [LEFT, LEFT]
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(node)
        assert refused.value.reason == "self-pair" and refused.value.endpoint == LEFT

    def test_a_malformed_shape_is_a_validation_refusal(self, writer):
        node = attestation()
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["stance"] = 3
        with pytest.raises(ValidationRefused, match="coreference shape validation"):
            writer.attest_coreference(node)

    def test_the_controlled_rebuild_compares_id_facets_and_relations_and_accepts_a_fresh_uid(self, writer):
        node = attestation()
        node.relations.append(Relation(source=node.id, predicate="cites", target=LEFT))
        with pytest.raises(MalformedRecord, match="controlled stored shape"):
            writer.attest_coreference(node)
        assert writer.attest_coreference(attestation(token="fresh")).uid

    @pytest.mark.parametrize(
        ("endpoints", "reason", "endpoint"),
        [
            (("discussion:d", "discussion:e"), "inadmissible-kind", "discussion:d"),
            (("act-report:a", "act-report:b"), "inadmissible-kind", "act-report:a"),
            (
                ("coreference-attestation:a", "coreference-attestation:b"),
                "inadmissible-kind",
                "coreference-attestation:a",
            ),
            ((LEFT, "dataset:missing"), "unresolved", "dataset:missing"),
        ],
    )
    def test_the_endpoint_refusals_over_the_corpus_view(self, writer, endpoints, reason, endpoint):
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation(endpoints=endpoints))
        assert (refused.value.reason, refused.value.endpoint) == (reason, endpoint)

    def test_two_kinds_are_a_category_error(self, writer):
        writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation(endpoints=(LEFT, "source:s")))
        assert refused.value.reason == "kind-mismatch"

    def test_a_retired_address_does_not_resolve_exactly(self, writer):
        # A raw rename through the `nodes` handle: the seam under test is the
        # attestation's, and no kernel rename exists yet (slice 2b).
        writer._corpus.rename(LEFT, "dataset:left-2")
        assert writer.read_view.resolve(LEFT) == "dataset:left-2"
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(attestation())
        assert refused.value.reason == "unresolved" and refused.value.endpoint == LEFT

    def test_the_refusal_order_is_actor_then_self_pair_then_shape(self, writer):
        node = attestation(actor="someone-else")
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [LEFT, LEFT]
        with pytest.raises(ActorMismatch):
            writer.attest_coreference(node)


class TestTheSeamOverAWorldView:
    def test_a_pair_split_across_corpora_resolves_and_a_not_present_endpoint_names_its_corpus(self, tmp_path):
        left = stored.dataset_node("left", title="left", resources=PINNED)
        right = stored.dataset_node(
            "right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]
        )
        roots = corpora(tmp_path, {"a" * 32: (left,), "b" * 32: (right,)})
        world = world_over(tmp_path, roots)
        published = publish(world, ("a" * 32, "b" * 32), hold_shipped(world))
        view = open_world_view(world, published)
        w = CorpusWriter(roots["a" * 32], DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY)
        assert w.attest_coreference(attestation(), view=view).id
        (roots["b" * 32] / "corpus.yaml").unlink()
        absent = open_world_view(world, published)
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            w.attest_coreference(attestation(token="event-2"), view=absent)
        assert (refused.value.reason, refused.value.endpoint, refused.value.corpus_id) == (
            "unresolved",
            RIGHT,
            "b" * 32,
        )


class TestImport:
    def test_a_bundled_attestation_is_validated_and_resolved_over_the_union(self, tmp_path):
        # Import needs an operation port; `test_facet_seams.writer` builds the
        # port-backed writer and adopts a manifest, so use it rather than the
        # in-memory recorder above (which refuses with "no operation port").
        from test_facet_seams import IMPORT
        from test_facet_seams import writer as port_writer

        w = port_writer(tmp_path / "ported")
        w.add(stored.dataset_node("left", title="left", resources=PINNED))
        w.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
        good = attestation(actor="importer")
        w.import_bundle([good], **IMPORT)
        assert w.read_view.holds(good.id)
        bad = attestation(actor="importer", endpoints=(LEFT, "dataset:nowhere"), token="event-9")
        with pytest.raises(ImportRefused, match="dataset:nowhere"):
            w.import_bundle([bad], **IMPORT)
        malformed = attestation(actor="importer", token="event-8")
        malformed.facets[stored.COREFERENCE_ATTESTATION_FACET]["stance"] = 5
        with pytest.raises(ImportRefused, match=malformed.id):
            w.import_bundle([malformed], **IMPORT)


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


class TestTheSessionRoute:
    def test_attest_is_the_eighth_ledgered_route(self, tmp_path):
        session, _ = make_session(tmp_path)
        session.claim_invocation("A", "mint", DIGEST)
        writer = session.scoped(ATTESTING, "A")
        writer.add(stored.dataset_node("left", title="left", resources=PINNED))
        writer.add(stored.dataset_node("right", title="right", resources=[{"name": "d", "digest": "sha256:" + "2" * 64}]))
        minted = writer.attest_coreference(attestation(actor=writer.actor))
        acts = session.invocation_acts("A")
        assert acts[-1].record_ids == ((minted.uid, minted.id),)  # `_record_act` ledgers (uid, id) pairs

    def test_the_facade_surface_is_the_eight_methods(self):
        public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
        assert "attest_coreference" in public
