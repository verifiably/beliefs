"""Receipt validation: §7.5's four outcomes, decided in §8.2's order.

**What a receipt claims.** A receipt names a subject identity, the exact
`(rule_identity, implementation_identity)` that produced it, and the exact
captured corpus-state identity of every covered corpus. Validating one is
therefore a rebuild: run *that* implementation over corpora standing at *those*
states and compare the canonical subject projection with the one the epoch
published, byte for byte.

**The four outcomes, and the order they are decided in.** ``malformed`` first
and alone — it is a statement about the receipt document, and §7.5 settles it
before resolvability is ever asked, so no change to what a store holds or where
a corpus stands can move it. ``unresolvable`` second: the named binding is not
held here, or a named corpus does not presently stand at its named state.
``validated`` and ``refuted`` last, and only there, because they are the two
answers a rebuild can give.

**Two layers, and this module lives in the upper one.** The carrier layer
(`test_world_epoch.py`) refuses bytes it cannot read. A receipt that *parses*
and then violates §7.5's contract is not a carrier failure: it opens, reaches
the validator here, and evaluates as ``malformed``. Several arms below build
exactly such a carrier by repackaging a published epoch — recomputing the
packaging identity from the edited members, never asserting a digest literal —
and prove the outcome rather than a refusal.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from authority import FULL
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from test_world_build import (
    ALPHA,
    BETA,
    ChainHeads,
    corpus_at,
    install_bindings,
    sample_nodes,
    slug_for,
)

from beliefs import stored
from beliefs.world import derive, epoch, read, registry, rules

# --- the harness -------------------------------------------------------------
#
# Everything here composes the two published harnesses rather than restating
# them: `test_world_build` owns corpus construction and rule installation, and
# `epoch.build_epoch` owns publication. What this module adds is the one act
# neither has — *repackaging* a published epoch with edited members, which is
# how a contract-violating receipt reaches the validator inside a carrier that
# is otherwise perfectly well-formed.


def corpora(tmp_path: Path, placement: dict[str, tuple[Node, ...]], *, prefix: str = "corpus") -> dict[str, Path]:
    """One corpus root per entry, carrying exactly the nodes named for it."""
    return {
        corpus_id: corpus_at(tmp_path / f"{prefix}-{corpus_id[:6]}", corpus_id, nodes)
        for corpus_id, nodes in placement.items()
    }


def sample_corpora(tmp_path: Path, coverage: tuple[str, ...], *, prefix: str = "corpus") -> dict[str, Path]:
    return corpora(
        tmp_path,
        {corpus_id: sample_nodes(slug_for(corpus_id, coverage)) for corpus_id in coverage},
        prefix=prefix,
    )


def world_over(
    tmp_path: Path,
    roots: dict[str, Path],
    *,
    name: str = "world",
    world_id: str = "f" * 32,
    chain_head: ChainHeads | None = None,
    also_configured: tuple[Path, ...] = (),
) -> registry.World:
    """A world configured over `roots`, with every one of them admitted.

    `also_configured` adds roots the world can see but has not admitted — the
    seam the duplicate-carrier arms need, because a second root claiming an
    admitted `corpus_id` is a configuration fault rather than a second
    admission.
    """
    world = registry.World(
        registry.WorldConfig(tmp_path / name, world_id, (*roots.values(), *also_configured)),
        DefaultExecutor,
        chain_head=chain_head or ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
        authority=FULL,
    )
    for corpus_root in roots.values():
        world.admit(corpus_root, provenance=registry.Fresh())
    return world


def hold_shipped(world: registry.World) -> epoch.DerivationBindings:
    """Install the four shipped rules and name them as one build input."""
    held = install_bindings(world)
    return epoch.DerivationBindings(
        producer=held["producer"],
        retraction=held["retraction-enumeration"],
        certification=held["certification-enumeration"],
        coreference=held["coreference-reduction"],
    )


def publish(world: registry.World, coverage: tuple[str, ...], bindings: epoch.DerivationBindings) -> epoch.Epoch:
    return epoch.build_epoch(world, coverage=frozenset(coverage), bindings=bindings)


def published_world(
    tmp_path: Path, coverage: tuple[str, ...] = (ALPHA,)
) -> tuple[registry.World, epoch.DerivationBindings, dict[str, Path], epoch.Epoch]:
    """The ordinary starting point: one world, one published epoch over
    `coverage`, every rule held and every corpus standing where it stood."""
    roots = sample_corpora(tmp_path, coverage)
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    return world, bindings, roots, publish(world, coverage, bindings)


def document(published: epoch.Epoch, member: str) -> dict:
    """One member of a published epoch, parsed back to a plain document.

    Plain rather than the `Epoch`'s own deep-frozen view, because these are
    what the repackaging helper edits and re-dumps.
    """
    return yaml.safe_load(published.members[member].decode("utf-8"))


def repackage(world: registry.World, published: epoch.Epoch, changes: dict[str, object]) -> epoch.Epoch:
    """A second retained epoch, identical to `published` but for `changes`.

    The packaging identity is **recomputed** from the edited members with
    §6.2's own formula, so the carrier this returns is well-formed by
    construction and every arm below turns on the receipt contract rather than
    on a carrier failure. No digest is written down anywhere: controller ruling
    R3 forbids it, and a repackaging that hard-coded one would stop being a
    repackaging the first time a rule identity moved.
    """
    members = dict(published.members)
    for member, edited in changes.items():
        members[member] = yaml.safe_dump(edited, sort_keys=True, allow_unicode=True).encode("utf-8")
    packaging_identity = epoch.packaging_identity_of(members)
    directory = world.config.world_root / "epochs" / packaging_identity
    directory.mkdir(parents=True, exist_ok=True)
    for member, content in members.items():
        (directory / member).write_bytes(content)
    return read.open_epoch(world, packaging_identity)


TEST_RECEIPT_KINDS: tuple[derive.ReceiptKind, ...] = (
    "producer",
    "retraction-enumeration",
    "certification-enumeration",
    "coreference-reduction",
)
"""§7.5's four kinds, named as literals so the arms below type-check.

Not `epoch.RECEIPT_KINDS`, which is the differently-shaped member-to-kind
mapping this module also reads.

`epoch.DERIVATION_KINDS` stays the authority on which four there are and in
what order; `outcomes` asserts the two agree rather than trusting this copy.
"""


def outcomes(world: registry.World, published: epoch.Epoch) -> dict[str, str]:
    """Every receipt kind's outcome, in §6.1's member order."""
    assert TEST_RECEIPT_KINDS == epoch.DERIVATION_KINDS
    return {kind: read.validate_receipt(world, published, kind).outcome for kind in TEST_RECEIPT_KINDS}


PRODUCER_FOLD = '            producers.setdefault(dataset, set()).add(record["address"])\n'
PRODUCER_ARM = (
    '        if record["kind"] == "verification":\n'
    '            producers.setdefault(record["address"], set()).add(record["address"])\n'
)


def producer_successor(*, behavioural: bool) -> rules.RuleBundle:
    """A sibling implementation of the shipped producer rule.

    Same symbol and same fixture members, so it recomputes the *same* rule
    identity and installs as a second implementation of one rule rather than
    as a different rule. `behavioural` decides whether it computes anything
    differently: the extra arm folds in `verification` records, a kind no
    producer fixture carries, so the successor satisfies every normative
    fixture and still disagrees with its sibling on the sample corpus.
    """
    bundle = next(
        candidate
        for candidate in rules.shipped_rule_bundles()
        if candidate.symbol == "derive_producer_snapshot"
    )
    source = bundle.implementation.decode("utf-8")
    if behavioural:
        assert source.count(PRODUCER_FOLD) == 1
        source = source.replace(PRODUCER_FOLD, PRODUCER_FOLD + PRODUCER_ARM)
    else:
        source = source + "\n# A successor that changes nothing this rule computes.\n"
    return rules.RuleBundle(bundle.symbol, bundle.fixtures, source.encode("utf-8"))


def extra_node(corpus_root: Path, slug: str) -> None:
    """Move a corpus's state by adding one record to it."""
    from nodes.core.corpus import Corpus

    Corpus(corpus_root).add(stored.dataset_node(slug, title=f"dataset {slug}"))


# --- Step 1: the four outcomes ------------------------------------------------


class TestReceiptOutcomes:
    def test_receipt_resolution_quantifies_each_corpus_and_rule(self, tmp_path):
        """Validation is universally quantified over both named things.

        A validator that checked the first corpus state, or the first kind's
        binding, would pass every arm built from a one-corpus world and would
        be wrong in exactly the case an operator cares about. So this covers
        two corpora and moves each in turn, and unholds each kind's binding in
        turn, asserting that only the named thing changes its own answer.
        """
        world, bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        # Each rule in turn: unholding one kind's exact pair leaves the other
        # three resolving, because a receipt names its own binding.
        for kind, binding in (
            ("producer", bindings.producer),
            ("retraction-enumeration", bindings.retraction),
            ("certification-enumeration", bindings.certification),
            ("coreference-reduction", bindings.coreference),
        ):
            rules.remove_rule_binding(world, binding)
            assert outcomes(world, published) == {
                candidate: "unresolvable" if candidate == kind else "validated"
                for candidate in epoch.DERIVATION_KINDS
            }
            rules.install_rule_binding(
                world,
                next(
                    bundle
                    for bundle in rules.shipped_rule_bundles()
                    if rules.binding_for(bundle) == binding
                ),
            )
            assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        # Each corpus in turn: the second one moving is as unresolvable as the
        # first one moving, which a validator stopping at the first state would
        # not report.
        extra_node(roots[BETA], "moved-beta")
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")

    def test_removed_binding_makes_every_receipt_kind_unresolvable(self, tmp_path):
        """Unholding all four exact pairs strands all four receipts.

        `unresolvable` and not `refuted`: nothing was rebuilt, so nothing was
        contradicted. The receipts are untouched and the corpora stand exactly
        where they stood — what changed is only what this store can run.
        """
        world, bindings, _roots, published = published_world(tmp_path)
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        severed = [
            rules.remove_rule_binding(world, binding)
            for binding in (bindings.producer, bindings.retraction, bindings.certification, bindings.coreference)
        ]

        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")
        # Every one of the four was reported severed by the removal that did
        # it, so the store and the validator agree about what was lost.
        assert [len(report.severed_receipts) for report in severed] == [1, 1, 1, 1]

    def test_receipt_uses_named_binding_beside_successor(self, tmp_path):
        """The exact held implementation runs — never a sibling of its rule.

        A successor is installed beside the original: same symbol, same
        fixtures, so the same rule identity and a different implementation
        identity. Both are held at once, which is the only configuration in
        which "runs the exact pair" is distinguishable from "runs the rule".
        """
        world, bindings, _roots, published = published_world(tmp_path)
        successor = rules.install_rule_binding(world, producer_successor(behavioural=True))
        assert successor.rule_identity == bindings.producer.rule_identity
        assert successor.implementation_identity != bindings.producer.implementation_identity

        # The receipt names the original; the successor standing beside it in
        # the same store changes nothing.
        assert read.validate_receipt(world, published, "producer").outcome == "validated"

        # Point the same receipt at the successor and the same epoch refutes:
        # what ran is the pair the receipt named, and that pair reduces this
        # corpus to a different snapshot.
        receipt = document(published, "producer-receipt.yaml")
        receipt["implementation_identity"] = successor.implementation_identity
        renamed = repackage(world, published, {"producer-receipt.yaml": receipt})
        assert read.validate_receipt(world, renamed, "producer").outcome == "refuted"

        # And an epoch actually built with the successor validates against it,
        # so the refutation above is about which pair ran and not about the
        # successor being unrunnable.
        built = publish(
            world,
            (ALPHA,),
            epoch.DerivationBindings(
                producer=successor,
                retraction=bindings.retraction,
                certification=bindings.certification,
                coreference=bindings.coreference,
            ),
        )
        assert read.validate_receipt(world, built, "producer").outcome == "validated"
        assert built.members["producer-snapshot.yaml"] != published.members["producer-snapshot.yaml"]

    def test_bare_version_receipt_is_malformed_without_availability(self, tmp_path):
        """A receipt naming a rule but no exact implementation is malformed.

        §5.2 and §7.5 admit one shape of reference and one only: the exact
        `(rule_identity, implementation_identity)` pair. A bare rule version —
        the pair with its implementation half simply not written — is not a
        weaker reference to be resolved leniently, it is an unsound contract,
        and `RECEIPT_KEYS` says so by declaring the closed key set the document
        must carry.

        And it is malformed *without availability*: this world holds no rule at
        all by the time the question is asked, so `unresolvable` is the answer
        an availability-first validator would give.
        """
        world, bindings, _roots, published = published_world(tmp_path)
        receipt = document(published, "producer-receipt.yaml")
        del receipt["implementation_identity"]
        bare = repackage(world, published, {"producer-receipt.yaml": receipt})
        for binding in (bindings.producer, bindings.retraction, bindings.certification, bindings.coreference):
            rules.remove_rule_binding(world, binding)

        assert read.validate_receipt(world, bare, "producer").outcome == "malformed"
        # The kinds whose receipts are intact are unresolvable in this same
        # world, so the malformed verdict is the receipt's own and not a
        # property of the world it was asked in.
        assert outcomes(world, bare) == {
            "producer": "malformed",
            "retraction-enumeration": "unresolvable",
            "certification-enumeration": "unresolvable",
            "coreference-reduction": "unresolvable",
        }

    def test_receipt_well_formedness_precedes_availability(self, tmp_path, monkeypatch):
        """The malformed verdict is reached before availability is consulted.

        Not merely "the outcome is malformed in an unavailable world" — that
        much a validator could reach by consulting availability first and then
        overriding itself. The two seams every availability question must pass
        through are stubbed to fail the arm outright, so the assertion is that
        neither was ever called.
        """
        world, bindings, roots, published = published_world(tmp_path)

        malformed_documents = {
            # Keys outside the closed set the kind declares.
            "keys": dict(document(published, "producer-receipt.yaml"), invented="value"),
            # The discriminant disagreeing with the member holding it.
            "kind": dict(document(published, "producer-receipt.yaml"), kind="coreference-reduction"),
            # A value that is not a well-formed identity.
            "identity": dict(document(published, "producer-receipt.yaml"), subject="not-a-digest"),
        }
        unsorted = document(published, "producer-receipt.yaml")
        # Corpus states repeating a corpus_id, which is also unsorted.
        unsorted["corpus_states"] = unsorted["corpus_states"] * 2
        malformed_documents["states"] = unsorted

        for label, receipt in malformed_documents.items():
            broken = repackage(world, published, {"producer-receipt.yaml": receipt})
            assert read.validate_receipt(world, broken, "producer").outcome == "malformed", label

        # Now the ordering proof. Both availability seams raise, so any
        # validator that consulted either before deciding well-formedness
        # fails this arm rather than returning the wrong outcome.
        calls: list[str] = []

        def refuse_state(corpus_root):
            calls.append(f"state:{corpus_root}")
            raise AssertionError("availability was consulted before well-formedness")

        def refuse_binding(world_root, binding):
            calls.append(f"binding:{binding}")
            raise AssertionError("availability was consulted before well-formedness")

        def refuse_carriers(config, corpus_id):
            calls.append(f"carriers:{corpus_id}")
            raise AssertionError("availability was consulted before well-formedness")

        broken_carriers = [
            repackage(world, published, {"producer-receipt.yaml": receipt})
            for receipt in malformed_documents.values()
        ]
        # All three seams, not two. Resolving carriers is the *first* thing the
        # availability phase does per corpus, and it has an `unresolvable`
        # return of its own; a validator that counted carriers before reading
        # the receipt would still pass an arm that stubbed only the two later
        # seams, because this fixture has exactly one carrier.
        monkeypatch.setattr(registry, "corpus_state_identity", refuse_state)
        monkeypatch.setattr(registry, "_carrier_roots", refuse_carriers)
        monkeypatch.setattr(rules, "_locked_resolve_rule_binding", refuse_binding)
        for broken in broken_carriers:
            assert read.validate_receipt(world, broken, "producer").outcome == "malformed"
        assert calls == []
        monkeypatch.undo()

        # The same receipts in a world that has also lost every binding and
        # moved its corpus are still malformed, never unresolvable.
        for binding in (bindings.producer, bindings.retraction, bindings.certification, bindings.coreference):
            rules.remove_rule_binding(world, binding)
        extra_node(roots[ALPHA], "moved-alpha")
        for label, receipt in malformed_documents.items():
            broken = repackage(world, published, {"producer-receipt.yaml": receipt})
            assert read.validate_receipt(world, broken, "producer").outcome == "malformed", label

    def test_moved_corpus_state_makes_receipt_unresolvable(self, tmp_path):
        """A corpus that no longer stands where the receipt named is
        unresolvable — for every kind at once, because every kind names the
        same states.

        Unresolvable rather than refuted: the rebuild never ran. Refuting here
        would say the receipt was wrong about what it derived, when what
        actually happened is that the evidence it named is no longer reachable.
        """
        world, _bindings, roots, published = published_world(tmp_path)
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        extra_node(roots[ALPHA], "later")

        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")
        # A corpus with no present carrier at all is the same answer.
        (roots[ALPHA] / "corpus.yaml").unlink()
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")

    def test_retraction_omission_refutes_repackaged_epoch(self, tmp_path):
        """An enumeration that dropped a finding is refuted by the rebuild.

        The repackaged receipt is *internally* consistent — its subject
        identity is recomputed over the trimmed enumeration — so nothing about
        it is malformed. What refutes it is the corpus: rerunning the named
        implementation over the named state finds the retraction the published
        enumeration omitted.
        """
        world, _bindings, _roots, published = published_world(tmp_path)
        receipt = document(published, "retraction-receipt.yaml")
        assert receipt["enumeration"]["found"], "the sample corpus carries a retraction to omit"
        receipt["enumeration"] = dict(receipt["enumeration"], found=[])
        receipt["subject"] = derive.subject_identity("retraction-enumeration", receipt["enumeration"])

        omitted = repackage(world, published, {"retraction-receipt.yaml": receipt})

        assert read.validate_receipt(world, omitted, "retraction-enumeration").outcome == "refuted"
        # Only that kind: the other three receipts of the same carrier are
        # untouched and still validate.
        assert outcomes(world, omitted) == {
            "producer": "validated",
            "retraction-enumeration": "refuted",
            "certification-enumeration": "validated",
            "coreference-reduction": "validated",
        }

    def test_nonzero_coreference_balance_refutes_empty_coverage(self, tmp_path):
        """A published edge weight that the covered corpora do not support.

        The sample corpora carry no coreference attestation, so the reduction
        over this coverage is empty. An epoch republished carrying a pair with
        a nonzero balance — and a coreference receipt whose subject identity
        matches that map exactly, so the contract is sound — is refuted by the
        rebuild, which finds nothing to weigh. Populated refutations — an
        omitted attestation, a wrong balance over a real one — are cut 24's
        arms in `test_coreference_attestation.py` and its acceptance module.
        """
        world, _bindings, _roots, published = published_world(tmp_path)
        assert document(published, "coreference-map.yaml") == {"pairs": []}

        pairs = {"pairs": [{"endpoints": ["address-a", "address-b"], "balance": 2, "distinct_key_count": 2}]}
        receipt = dict(
            document(published, "coreference-receipt.yaml"),
            subject=derive.subject_identity("coreference-reduction", pairs),
        )
        claimed = repackage(
            world, published, {"coreference-map.yaml": pairs, "coreference-receipt.yaml": receipt}
        )

        assert read.validate_receipt(world, claimed, "coreference-reduction").outcome == "refuted"
        assert outcomes(world, claimed) == {
            "producer": "validated",
            "retraction-enumeration": "validated",
            "certification-enumeration": "validated",
            "coreference-reduction": "refuted",
        }

    def test_receipt_changes_when_location_states_move_but_snapshot_does_not(self, tmp_path):
        """The packaging/semantic split, at its sharpest.

        One dataset and the run producing it, in corpus ALPHA in the left world
        and in corpus BETA in the right, both epochs covering both corpora.
        Every captured corpus state differs, so every receipt identity differs.
        The producer snapshot declares stable `corpus_id` values and not states,
        so its projection — and therefore the belief input — is byte-identical.
        """
        dataset = stored.dataset_node("moved", title="dataset moved")
        run = stored.run_node(
            "moved", title="run moved", spec="analysis-spec:moved", produces=[dataset.id]
        )
        placements = {
            "left": {ALPHA: (dataset, run), BETA: ()},
            "right": {ALPHA: (), BETA: (dataset, run)},
        }
        built: dict[str, epoch.Epoch] = {}
        for side, placement in placements.items():
            roots = corpora(tmp_path, placement, prefix=side)
            world = world_over(tmp_path, roots, name=f"world-{side}")
            built[side] = publish(world, (ALPHA, BETA), hold_shipped(world))

        left, right = built["left"], built["right"]
        assert left.coverage != right.coverage
        assert [corpus_id for corpus_id, _state in left.coverage] == [
            corpus_id for corpus_id, _state in right.coverage
        ]
        # The subject is unmoved…
        assert left.members["producer-snapshot.yaml"] == right.members["producer-snapshot.yaml"]
        assert (
            left.receipts["producer-receipt.yaml"].subject_identity
            == right.receipts["producer-receipt.yaml"].subject_identity
        )
        # …and every receipt moved with the states.
        for member in epoch.RECEIPT_KINDS:
            assert left.receipts[member].identity != right.receipts[member].identity, member
            assert left.receipts[member].corpus_states != right.receipts[member].corpus_states, member
        assert left.packaging_identity != right.packaging_identity

    def test_rule_successor_mints_receipt_and_snapshot_only_on_subject_change(self, tmp_path):
        """A successor always mints a new receipt; it mints a new subject only
        when it computes a different one.

        The receipt identity digests the implementation identity, so *any*
        successor moves it — that is what makes a receipt a record of what ran.
        The producer snapshot digests the snapshot, so a successor that
        computes the same snapshot leaves the belief input exactly where it
        was. Both successors below install beside the original as siblings of
        one rule.
        """
        world, bindings, _roots, published = published_world(tmp_path)
        original = published.receipts["producer-receipt.yaml"]

        def republish(binding: rules.RuleBinding) -> epoch.Epoch:
            return publish(
                world,
                (ALPHA,),
                epoch.DerivationBindings(
                    producer=binding,
                    retraction=bindings.retraction,
                    certification=bindings.certification,
                    coreference=bindings.coreference,
                ),
            )

        cosmetic = republish(rules.install_rule_binding(world, producer_successor(behavioural=False)))
        behavioural = republish(rules.install_rule_binding(world, producer_successor(behavioural=True)))

        for successor in (cosmetic, behavioural):
            minted = successor.receipts["producer-receipt.yaml"]
            assert minted.identity != original.identity
            assert minted.implementation_identity != original.implementation_identity
            assert minted.rule_identity == original.rule_identity
            assert successor.packaging_identity != published.packaging_identity

        assert cosmetic.members["producer-snapshot.yaml"] == published.members["producer-snapshot.yaml"]
        assert (
            cosmetic.receipts["producer-receipt.yaml"].subject_identity == original.subject_identity
        )
        assert behavioural.members["producer-snapshot.yaml"] != published.members["producer-snapshot.yaml"]
        assert (
            behavioural.receipts["producer-receipt.yaml"].subject_identity != original.subject_identity
        )
        # All three epochs are retained and all three validate: a successor is
        # a sibling, never a replacement.
        for retained in (published, cosmetic, behavioural):
            assert read.validate_receipt(world, retained, "producer").outcome == "validated"

    def test_rule_conformance_and_two_worlds_agree_within_availability(self, tmp_path):
        """Two distinct world roots, each resolving the same binding from its
        own rules store over the same corpora, agree — and disagree exactly
        where availability differs.

        Not one world evaluated twice. Each world has its own world root, its
        own registry and its own `rules/` tree, and each installs the four
        shipped bundles independently; the bundles recompute the same
        identities from the same package content, which is *why* the receipt
        published by one resolves in the other. The epoch's bytes are copied
        across unchanged, so what is being compared is two stores' answers to
        one carrier.
        """
        roots = sample_corpora(tmp_path, (ALPHA,))
        left = world_over(tmp_path, roots, name="world-left", world_id="1" * 32)
        right = world_over(tmp_path, roots, name="world-right", world_id="2" * 32)
        assert left.config.world_root != right.config.world_root

        left_bindings = hold_shipped(left)
        right_bindings = hold_shipped(right)
        assert left_bindings == right_bindings  # conformance: one rule, two stores

        published = publish(left, (ALPHA,), left_bindings)
        shutil.copytree(
            left.config.world_root / "epochs" / published.packaging_identity,
            right.config.world_root / "epochs" / published.packaging_identity,
        )
        elsewhere = read.open_epoch(right, published.packaging_identity)
        assert elsewhere.members == published.members

        assert outcomes(left, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")
        assert outcomes(right, elsewhere) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        # "Within availability" is the whole qualification: unholding the pair
        # in one store moves that store's answer and no other's.
        rules.remove_rule_binding(right, right_bindings.producer)
        assert read.validate_receipt(right, elsewhere, "producer").outcome == "unresolvable"
        assert read.validate_receipt(left, published, "producer").outcome == "validated"

    def test_all_four_receipts_declare_one_state_map_and_consult_no_default(self, tmp_path):
        """Within one epoch the four receipts carry identical state maps, and
        no evaluator reaches an installed default to get them.

        The second half is structural rather than observed: the value each rule
        is handed comes from the frozen draft, which has no corpus root, no
        registry and no pointer on it, so there is nothing for a reducer to
        consult. The arm states it by naming the draft's fields.
        """
        world, bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))

        declared = {member: published.receipts[member].corpus_states for member in epoch.RECEIPT_KINDS}
        assert len(set(declared.values())) == 1
        assert next(iter(declared.values())) == published.coverage

        draft = epoch._capture_build_inputs(world, coverage=frozenset({ALPHA, BETA}), bindings=bindings.by_kind())
        assert draft.corpus_states == published.coverage
        # One projection value, handed to all four, carrying no path anywhere.
        supplied = draft.capture.rule_input()
        assert set(supplied) == {"coverage", "records"}
        assert not hasattr(draft, "carriers")
        assert not any("root" in field for field in draft.__dataclass_fields__)

    def test_validation_holds_the_world_lock_only_for_the_binding_resolution(self, tmp_path, monkeypatch):
        """The rule run and the corpus reads happen with the world lock free.

        `build_epoch` states the principle for the identical work: derivation
        happens before the lock is reacquired, "so nothing that could refuse or
        take time happens inside the critical section". Validation does the
        same work — one enumeration of every covered corpus, then loaded rule
        code over it — and every coreference edge query performs a validation,
        so holding the world lock across it would serialize every registry
        append and every rule install in this world behind one query.

        Observed at the three seams rather than argued: the lock is held while
        the rules store is read, because rule removal writes to that store
        under the same lock, and free for everything after.
        """
        world, _bindings, _roots, published = published_world(tmp_path)
        observed: dict[str, bool] = {}
        real_state = registry.corpus_state_identity
        real_resolve = rules._locked_resolve_rule_binding

        def watched_state(corpus_root):
            observed["corpus read"] = world._state.lock.locked()
            return real_state(corpus_root)

        def watched_resolve(world_root, binding):
            observed["binding resolution"] = world._state.lock.locked()
            held = real_resolve(world_root, binding)

            def watched_invoke(value):
                observed["rule run"] = world._state.lock.locked()
                return held.invoke(value)

            return rules._HeldRule(held.binding, held.symbol, held.source, watched_invoke)

        monkeypatch.setattr(registry, "corpus_state_identity", watched_state)
        monkeypatch.setattr(rules, "_locked_resolve_rule_binding", watched_resolve)

        assert read.validate_receipt(world, published, "producer").outcome == "validated"

        assert observed == {"binding resolution": True, "corpus read": False, "rule run": False}

    def test_unreadable_carrier_manifest_is_unresolvable_rather_than_an_exception(self, tmp_path):
        """A configured root claiming a manifest this world cannot read makes
        every named state unreachable, and that is an outcome.

        `registry._carrier_roots` refuses a malformed manifest rather than
        treating it as an absence — a root that claims something unreadable is
        a configuration fault — and that refusal reaches validation. It is
        converted here instead of propagating, because §8.4 makes an edge whose
        receipt is anything but ``validated`` ``indeterminate``, and a query
        that raised would leave the caller with nothing where the specification
        promises a state. `resolve_address` converts the same fault the other
        way, to `ResolutionRefused`, because §8.3 closes *its* answer set at
        three arms and names the malformed manifest as one of the refusals.
        """
        world, _bindings, roots, published = published_world(tmp_path)
        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "validated")

        (roots[ALPHA] / "corpus.yaml").write_bytes(b"corpus_id: []\n")

        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")
        producer = read.validate_receipt(world, published, "producer")
        assert ALPHA in producer.detail and "cannot read" in producer.detail

    def test_an_unknown_receipt_kind_is_refused_rather_than_answered(self, tmp_path):
        """§7.5 has four kinds. A fifth is a caller error, not an outcome."""
        world, _bindings, _roots, published = published_world(tmp_path)

        with pytest.raises(ValueError, match="receipt kind"):
            # A kind outside `ReceiptKind` on purpose: the arm exercises the
            # runtime refusal of a fifth kind.
            read.validate_receipt(world, published, "producer-snapshot")  # pyright: ignore[reportArgumentType]
