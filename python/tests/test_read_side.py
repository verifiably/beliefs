"""The read side, portably: the one algorithm, its two adapters, the facade's
node-read path, and the §6.2 corpus check.

**These cannot claim cut-4 discharge and do not try to.** Every corpus here is
seeded by the raw-write fixture act and read back through a fresh facade, which
exercises the read code and nothing about durability. The arms that require a
record to have been *minted* through the add path into a durable root run under
the acceptance command, on the certified tuple, where they error rather than
skip.
"""

from __future__ import annotations

import inspect

import pytest
from fixtures_cut4 import raw_write, reopen
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import LineageAdjacency, RelationAdjacency, corpus_check, derived_from, lineage_snapshot
from beliefs.errors import SemanticHashMissing, SemanticHashStale
from beliefs.lineage import certify
from beliefs.traversal import LineageEntry, RelationEntry, closure

CITES = "cites"


def memo(slug: str, *, relations=()) -> Node:
    """A prose node with relations and no governed facet — the plain carrier for
    the relation fixtures, which are about edges and not about payload."""
    node_id = f"memo:{slug}"
    return Node(id=node_id, kind="memo", title=slug, relations=list(relations))


def cites(source: str, target: str, *, directed: bool = True, predicate: str = CITES) -> Relation:
    return Relation(source=source, predicate=predicate, target=target, directed=directed)


def seed(root, *nodes: Node):
    for node in nodes:
        raw_write(root, node)
    return reopen(root)


def relation_walk(view, start: str, predicate: str = CITES, direction: str = "outbound"):
    return closure(start, RelationAdjacency(view, predicate, direction))


class TestTheOneAlgorithmsSharedBehaviour:
    def test_a_chain_is_walked_transitively(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b")]),
            memo("b", relations=[cites("memo:b", "memo:c")]),
            memo("c"),
        )
        assert relation_walk(view, "memo:a").reached == ("memo:b", "memo:c")

    def test_a_diamond_reaches_each_node_once(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b"), cites("memo:a", "memo:c")]),
            memo("b", relations=[cites("memo:b", "memo:d")]),
            memo("c", relations=[cites("memo:c", "memo:d")]),
            memo("d"),
        )
        assert relation_walk(view, "memo:a").reached == ("memo:b", "memo:c", "memo:d")

    def test_a_cycle_terminates_and_does_not_readmit_the_start(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b")]),
            memo("b", relations=[cites("memo:b", "memo:a")]),
        )
        assert relation_walk(view, "memo:a").reached == ("memo:b",)

    def test_the_start_is_never_in_the_reached_set(self, tmp_path):
        # Start-excluding: substrate §5's inspected set writes the union out
        # because the walk does not, and a walk that quietly included its start
        # would make `{root} ∪ closure` a no-op nobody could see fail.
        view = seed(tmp_path, memo("a", relations=[cites("memo:a", "memo:a")]), memo("b"))
        assert relation_walk(view, "memo:a").reached == ()

    def test_an_unresolvable_step_is_skipped_and_reported_with_its_source_and_position(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:gone"), cites("memo:a", "memo:b")]),
            memo("b"),
        )
        walk = relation_walk(view, "memo:a")
        assert walk.reached == ("memo:b",)  # skipped, not fatal
        assert walk.unresolved == (
            RelationEntry(source="memo:a", position=0, predicate=CITES, target="memo:gone"),
        )

    def test_two_dangling_edges_from_different_sources_are_two_entries(self, tmp_path):
        # Without the source and the position, `X ─cites→ M` and `Y ─cites→ M`
        # produce one identical entry and two defects deduplicate into one.
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b"), cites("memo:a", "memo:gone")]),
            memo("b", relations=[cites("memo:b", "memo:gone")]),
        )
        walk = relation_walk(view, "memo:a")
        assert [
            (entry.source, entry.position) for entry in walk.unresolved if isinstance(entry, RelationEntry)
        ] == [("memo:a", 1), ("memo:b", 0)]


class TestTheRelationAdapter:
    def test_an_unrelated_predicate_is_not_followed(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b", predicate="mentions")]),
            memo("b"),
        )
        assert relation_walk(view, "memo:a").reached == ()

    def test_a_deprecated_ref_resolves_to_the_live_node(self, tmp_path):
        live = memo("b")
        live.deprecated_ids = ["memo:old"]
        view = seed(tmp_path, memo("a", relations=[cites("memo:a", "memo:old")]), live)
        assert relation_walk(view, "memo:a").reached == ("memo:b",)

    def test_an_undirected_relation_is_reached_from_its_stored_source(self, tmp_path):
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b", directed=False)]),
            memo("b"),
        )
        assert relation_walk(view, "memo:a").reached == ("memo:b",)

    def test_an_undirected_relation_is_not_reached_from_its_stored_target(self, tmp_path):
        # `directed` is read, never reinterpreted: walking an undirected edge
        # backwards invents an edge the author did not write.
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:b", directed=False)]),
            memo("b"),
        )
        assert relation_walk(view, "memo:b").reached == ()

    def test_nodes_exposes_no_transitive_operation(self):
        # A static reading of that package's surface, depending on nothing this
        # cut builds: the traversal was withdrawn from `nodes` and relocated, so
        # a transitive primitive reappearing there is a boundary violation.
        surface = [name for name in dir(Corpus) if not name.startswith("_")]
        assert [name for name in surface if "transitive" in name or "closure" in name] == []


class TestTheLineageAdapter:
    @staticmethod
    def basis(*routes, tag: str = "single"):
        return {"tag": tag, "routes": [dict(route) for route in routes]}

    @staticmethod
    def route(run: str, ancestor: str, transforms=()):
        return {"run": run, "ancestor": ancestor, "transforms": list(transforms)}

    def test_the_basis_chain_is_walked_as_a_facet(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node("c", title="c", basis=self.basis(self.route("run:r", "dataset:b"))),
            stored.dataset_node("b", title="b", basis=self.basis(self.route("run:r", "dataset:a"))),
            stored.dataset_node("a", title="a"),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
        )
        assert closure("dataset:c", LineageAdjacency(view)).reached == ("dataset:a", "dataset:b")

    def test_a_conflict_basis_yields_every_route(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node(
                "c",
                title="c",
                basis=self.basis(
                    self.route("run:r", "dataset:a"),
                    self.route("run:s", "dataset:b"),
                    tag="conflict",
                ),
            ),
            stored.dataset_node("a", title="a"),
            stored.dataset_node("b", title="b"),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
            stored.run_node("s", title="s", spec="analysis-spec:s"),
        )
        assert closure("dataset:c", LineageAdjacency(view)).reached == ("dataset:a", "dataset:b")

    def test_an_unresolvable_ancestor_is_reported_at_its_route_position(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node("c", title="c", basis=self.basis(self.route("run:r", "dataset:gone"))),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
        )
        assert closure("dataset:c", LineageAdjacency(view)).unresolved == (
            LineageEntry(dataset="dataset:c", route=0, position="ancestor", target="dataset:gone"),
        )

    def test_an_unresolvable_producing_run_is_told_apart_from_an_unresolvable_ancestor(self, tmp_path):
        # The distinction the relation adapter cannot express, and the one
        # substrate §5 step 2 decides on.
        view = seed(
            tmp_path,
            stored.dataset_node("c", title="c", basis=self.basis(self.route("run:gone", "dataset:a"))),
            stored.dataset_node("a", title="a"),
        )
        walk = closure("dataset:c", LineageAdjacency(view))
        assert walk.reached == ("dataset:a",)
        assert [entry.position for entry in walk.unresolved] == ["run"]

    def test_a_resolvable_producing_run_is_checked_and_not_walked_into(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node("c", title="c", basis=self.basis(self.route("run:r", "dataset:a"))),
            stored.dataset_node("a", title="a"),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
        )
        assert closure("dataset:c", LineageAdjacency(view)).reached == ("dataset:a",)

    def test_the_lineage_adapter_accepts_no_predicate_and_no_direction(self):
        parameters = set(inspect.signature(LineageAdjacency.__init__).parameters)
        assert parameters == {"self", "view"}
        assert {"predicate", "direction"} & parameters == set()

    def test_one_algorithm_serves_both_adapters(self, tmp_path):
        # Cycle-safety and start-exclusion are certified once because one
        # function performs both closures: the adapters supply steps, and
        # nothing in either of them decides when to stop.
        view = seed(
            tmp_path,
            memo("a", relations=[cites("memo:a", "memo:a")]),
            stored.dataset_node("c", title="c", basis=self.basis(self.route("run:r", "dataset:c"))),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
        )
        assert closure("memo:a", RelationAdjacency(view, CITES, "outbound")).reached == ()
        assert closure("dataset:c", LineageAdjacency(view)).reached == ()


def observed_dataset(slug="raw"):
    return stored.dataset_node(
        slug,
        title=slug,
        resources=[{"name": "matrix", "digest": "sha256:" + "ab" * 32}],
        empirical_observation={"boundary": "instrument"},
    )


def admissible_corpus(tmp_path, **run_kwargs):
    dataset = observed_dataset()
    run = stored.run_node("r1", title="r1", spec="analysis-spec:s1", **({"observes": [dataset.id]} | run_kwargs))
    assessment = stored.assessment_node(
        "a1",
        title="a1",
        spec="analysis-spec:s1",
        run=run.id,
        proposition="proposition:p1",
        outcome="supported",
        interpretation_rule="rule:threshold",
    )
    proposition = stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
    return seed(tmp_path, dataset, run, assessment, proposition)


class TestTheFacadesNodeReadPath:
    def test_a_stale_semantic_hash_is_refused_on_get(self, tmp_path):
        node = observed_dataset()
        node.facets[stored.DATASET_FACET]["resources"] = []  # fields moved, stamp did not
        view = seed(tmp_path, node)
        with pytest.raises(SemanticHashStale):
            view.get(node.id)

    def test_a_stale_semantic_hash_is_refused_when_a_traversal_resolves_the_node(self, tmp_path):
        node = observed_dataset()
        node.facets[stored.DATASET_FACET]["resources"] = []
        view = seed(tmp_path, node, memo("a", relations=[cites("memo:a", node.id)]))
        with pytest.raises(SemanticHashStale):
            relation_walk(view, "memo:a")

    def test_a_self_consistent_raw_write_is_not_refused(self, tmp_path):
        # The recorded-history bound, pinned: the hash agrees because the writer
        # computed it, and the store compares a state against itself.
        forged = observed_dataset()
        forged.facets[stored.DATASET_FACET]["resources"] = [{"name": "other", "digest": "sha256:" + "cd" * 32}]
        stored.stamp_semantic_identity(forged)
        view = seed(tmp_path, forged)
        assert view.get(forged.id).facets[stored.DATASET_FACET]["resources"][0]["name"] == "other"

    def test_an_unstamped_governed_record_is_refused_on_get(self, tmp_path):
        # Post-freeze strengthening (2026-08-18 review): a forger who omits the
        # stamp on a governed kind is statically detectable, and the
        # recorded-history bound covers only fields and stamp moved *together*.
        node = observed_dataset()
        del node.facets[stored.SEMANTIC_IDENTITY_FACET]
        view = seed(tmp_path, node)
        with pytest.raises(SemanticHashMissing):
            view.get(node.id)

    def test_an_unstamped_prose_node_is_not_refused(self, tmp_path):
        # Prose kinds carry no semantic domain; requiring a stamp there would
        # refuse every hand-authored memo in the corpus.
        view = seed(tmp_path, memo("a"))
        assert view.get("memo:a").kind == "memo"

    def test_iteration_does_not_refuse_so_the_check_can_report(self, tmp_path):
        node = observed_dataset()
        node.facets[stored.DATASET_FACET]["resources"] = []
        view = seed(tmp_path, node)
        assert [stored_node.id for stored_node in view.iter_stored()] == [node.id]


class TestTheCorpusCheck:
    def test_a_valid_record_is_reported_by_nothing(self, tmp_path):
        assert corpus_check(admissible_corpus(tmp_path)) == ()

    def test_an_assesses_edge_whose_run_has_no_observes_input_is_reported_eligibility_unmet(self, tmp_path):
        view = admissible_corpus(tmp_path, observes=[])
        findings = corpus_check(view)
        assert [(f.severity, f.code, f.ref, f.detail) for f in findings] == [
            ("error", "eligibility-unmet", "assessment:a1", "proposition:p1")
        ]

    def test_reads_inputs_confer_no_eligibility_in_any_quantity(self, tmp_path):
        view = admissible_corpus(tmp_path, observes=[], reads=["dataset:raw", "dataset:raw"])
        assert [f.code for f in corpus_check(view)] == ["eligibility-unmet"]

    def test_an_observes_input_without_the_empirical_observation_facet_is_reported(self, tmp_path):
        plain = stored.dataset_node("plain", title="plain", resources=[{"name": "x", "digest": "sha256:" + "ef" * 32}])
        view = seed(
            tmp_path,
            plain,
            stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[plain.id]),
            stored.assessment_node(
                "a1",
                title="a1",
                spec="analysis-spec:s1",
                run="run:r1",
                proposition="proposition:p1",
                outcome="supported",
                interpretation_rule="rule:threshold",
            ),
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"}),
        )
        assert [f.code for f in corpus_check(view)] == ["eligibility-unmet"]

    def test_an_unstamped_governed_record_is_reported_semantic_hash_missing(self, tmp_path):
        node = observed_dataset()
        del node.facets[stored.SEMANTIC_IDENTITY_FACET]
        view = seed(tmp_path, node)
        assert [(f.severity, f.code, f.ref, f.detail) for f in corpus_check(view)] == [
            ("error", "semantic-hash-missing", node.id, "unstamped")
        ]

    def test_an_unstamped_prose_node_is_reported_by_nothing(self, tmp_path):
        assert corpus_check(seed(tmp_path, memo("a"))) == ()

    def test_a_stale_node_is_reported_rather_than_raised(self, tmp_path):
        node = observed_dataset()
        node.facets[stored.DATASET_FACET]["resources"] = []
        view = seed(tmp_path, node)
        assert [(f.code, f.ref, f.detail) for f in corpus_check(view)] == [
            ("semantic-hash-stale", node.id, "mismatch")
        ]

    def test_a_raw_written_malformed_display_facet_is_reported(self, tmp_path):
        node = stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        node.facets[stored.DISPLAY_FACET] = {"display_statement": "shown", "extra": "not allowed"}
        raw_write(tmp_path, node)

        findings = corpus_check(reopen(tmp_path))

        assert [(finding.severity, finding.code) for finding in findings] == [
            ("error", "display-malformed")
        ]

    def test_a_raw_written_supersession_to_a_missing_target_is_reported(self, tmp_path):
        node = stored.proposition_node("new", title="new", claim={"operator": "affects"})
        node.relations.append(
            Relation(source=node.id, predicate=stored.SUPERSEDES, target="proposition:missing")
        )
        raw_write(tmp_path, node)

        findings = corpus_check(reopen(tmp_path))

        assert [(finding.severity, finding.code) for finding in findings] == [
            ("error", "supersession-target-missing")
        ]

    def test_findings_are_ordered_by_ref_then_code_then_detail(self, tmp_path):
        stale = observed_dataset()
        stale.facets[stored.DATASET_FACET]["resources"] = []
        admissible_corpus(tmp_path, observes=[])
        raw_write(tmp_path, stale)
        findings = corpus_check(reopen(tmp_path))
        assert [f.sort_key for f in findings] == sorted(f.sort_key for f in findings)
        assert {f.ref for f in findings} == {"assessment:a1", "dataset:raw"}


class TestTheSnapshotWalk:
    @staticmethod
    def basis(*routes, tag: str = "single"):
        return {"tag": tag, "routes": [dict(route) for route in routes]}

    def test_the_inspected_set_is_the_root_plus_its_closure(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node(
                "b",
                title="b",
                basis=self.basis({"run": "run:r", "ancestor": "dataset:a", "transforms": ["dataset:a"]}),
            ),
            stored.dataset_node("a", title="a"),
            stored.run_node("r", title="r", spec="analysis-spec:s", transforms=["dataset:a"], produces=["dataset:b"]),
        )
        snapshot = lineage_snapshot(view, ["dataset:b"])
        assert set(snapshot.producers) == {"dataset:a", "dataset:b"}
        assert certify(snapshot, ("dataset:b",), ("dataset:b",)).state == "shared-source"

    def test_a_conflict_tag_short_circuits_to_lineage_divergent(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node(
                "b",
                title="b",
                basis=self.basis(
                    {"run": "run:r", "ancestor": "dataset:a", "transforms": []},
                    {"run": "run:s", "ancestor": "dataset:a2", "transforms": []},
                    tag="conflict",
                ),
            ),
            stored.dataset_node("a", title="a"),
            stored.dataset_node("a2", title="a2"),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
            stored.run_node("s", title="s", spec="analysis-spec:s"),
        )
        certification = certify(lineage_snapshot(view, ["dataset:b"]), ("dataset:b",), ("dataset:other",))
        assert certification.state == "not-certified"
        assert certification.findings == ("lineage-divergent",)

    def test_an_unresolvable_basis_entry_yields_lineage_incomplete_and_no_certificate(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node(
                "b",
                title="b",
                basis=self.basis({"run": "run:r", "ancestor": "dataset:gone", "transforms": []}),
            ),
            stored.run_node("r", title="r", spec="analysis-spec:s"),
        )
        certification = certify(lineage_snapshot(view, ["dataset:b"]), ("dataset:b",), ("dataset:b",))
        assert certification.state == "not-certified"
        assert certification.findings == ("lineage-incomplete",)

    def test_an_unresolvable_entry_with_an_empty_closure_still_yields_incomplete(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node(
                "b",
                title="b",
                basis=self.basis({"run": "run:gone", "ancestor": "dataset:gone", "transforms": []}),
            ),
        )
        snapshot = lineage_snapshot(view, ["dataset:b"])
        assert certify(snapshot, ("dataset:b",), ("dataset:b",)).findings == ("lineage-incomplete",)


class TestTheDerivedFromView:
    def test_derived_from_resolves_as_a_view_over_produces_then_transforms(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node("out", title="out"),
            stored.dataset_node("in", title="in"),
            stored.run_node(
                "r", title="r", spec="analysis-spec:s", transforms=["dataset:in"], produces=["dataset:out"]
            ),
        )
        assert derived_from(view, "dataset:out").reached == ("dataset:in",)

    def test_no_derived_from_edge_is_stored_anywhere(self, tmp_path):
        view = seed(
            tmp_path,
            stored.dataset_node("out", title="out"),
            stored.dataset_node("in", title="in"),
            stored.run_node(
                "r", title="r", spec="analysis-spec:s", transforms=["dataset:in"], produces=["dataset:out"]
            ),
        )
        predicates = {
            relation.predicate for node in view.iter_stored() for relation in node.relations
        }
        assert "derived_from" not in predicates

    def test_independence_follows_the_stamped_basis_not_the_composition(self, tmp_path):
        # Basis and composition made to disagree by the fixture write: the run
        # transforms `in`, and the stamped basis names `other`. Independence
        # walks the basis, so the certification follows `other`.
        view = seed(
            tmp_path,
            stored.dataset_node(
                "out",
                title="out",
                basis={"tag": "single", "routes": [{"run": "run:r", "ancestor": "dataset:other", "transforms": []}]},
            ),
            stored.dataset_node("in", title="in"),
            stored.dataset_node("other", title="other"),
            stored.run_node(
                "r", title="r", spec="analysis-spec:s", transforms=["dataset:in"], produces=["dataset:out"]
            ),
        )
        assert derived_from(view, "dataset:out").reached == ("dataset:in",)
        snapshot = lineage_snapshot(view, ["dataset:out"])
        assert snapshot.bases["dataset:out"].routes[0].resolved_ancestor == "dataset:other"
