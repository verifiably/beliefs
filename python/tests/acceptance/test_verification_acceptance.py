"""Cut 21's durable arms: verification publication through an attended session
on the certified engine and volume (`docs/designs/2026-09-06-conformance-cut-21.md`
§3, V1, V2, V3 and V5). Every body mirrors its portable twin and additionally
reopens the corpus — a fresh process for V1 and V2 — so each assertion is
about bytes the engine committed."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from authority import FULL
from profiles import WITH_BIOLOGY
from test_evaluation import CLAIM_FACET
from test_session_acceptance import DIGEST, adopted, attended, chain, intents, registrations
from verification_fixtures import admission_over, forgeries, publish_corpus

from beliefs import stored
from beliefs.admission import Admitted
from beliefs.belief import Belief, NoBelief
from beliefs.permit import RequiredCapabilities
from beliefs.root import open_corpus
from beliefs.verification import INVALIDATED, active, lifecycle_state
from beliefs.verify import _mint_verification, publication_node

KINDS = RequiredCapabilities.for_kinds({"verification"}, {})  # [R8] runs, datasets and the assessment go through the library writer
TESTS = Path(__file__).resolve().parents[1]


def _fresh_process(script: str) -> dict:
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(TESTS), str(TESTS / "acceptance")])}
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, check=False)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _session_over(work_directory):
    root = adopted(work_directory, "corpus")
    session, _ = attended(work_directory, root)
    writer = session.scoped(KINDS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    return root, session, writer


def test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), claim=CLAIM_FACET)
        node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        library = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
        library.delete(stored.typed_ref("run", published.derived.original))
        library.delete(stored.typed_ref("run", published.derived.replayed))
    finally:
        session.close()
    report = _fresh_process(
        "import json; from authority import FULL; from profiles import WITH_BIOLOGY; from beliefs.root import open_corpus; from beliefs.verify import decode_verification\n"
        f"view = open_corpus({str(root)!r}, authority=FULL, profile=WITH_BIOLOGY).read_view; d = decode_verification(view.get({node.id!r}))\n"
        "assert not view.holds(f'run:{d.original}') and not view.holds(f'run:{d.replayed}')\n"
        "print(json.dumps({'identity': d.identity(), 'report': d.report.identity(), 'scope': d.scope, 'verdict': d.verdict, 'basis': json.dumps(d.basis(), default=lambda r: r.identity(), sort_keys=True)}))",
    )
    derived = published.derived
    assert report["identity"] == derived.identity() and report["report"] == derived.report.identity()
    assert (report["scope"], report["verdict"]) == (derived.scope, derived.verdict)
    assert report["basis"] == json.dumps(derived.basis(), default=lambda r: r.identity(), sort_keys=True)


def test_v2_and_v3_admission_over_the_corpus_and_the_belief_moves_with_the_record(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), claim=CLAIM_FACET)
        _, before = admission_over(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), published.proposition.id, published.original)
        assert isinstance(before, NoBelief)
        node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        verdict, belief = admission_over(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), published.proposition.id, published.original)
        assert isinstance(verdict, Admitted) and isinstance(belief, Belief)
        digest_here = belief.belief_input_digest
        writer.delete(node.id)
        _, after = admission_over(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), published.proposition.id, published.original)
        assert isinstance(after, NoBelief)
        writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
    finally:
        session.close()
    report = _fresh_process(
        "import json; from authority import FULL; from profiles import WITH_BIOLOGY; from beliefs.root import open_corpus; from verification_fixtures import admission_over\n"
        "from beliefs.runrecord import decode_run_closure\n"
        f"w = open_corpus({str(root)!r}, authority=FULL, profile=WITH_BIOLOGY); original = decode_run_closure(w.read_view.get({stored.typed_ref('run', published.derived.original)!r}))\n"
        f"verdict, belief = admission_over(w, {published.proposition.id!r}, original); print(json.dumps({{'digest': belief.belief_input_digest}}))",
    )
    assert report["digest"] == digest_here


def test_v3_a_superseding_failed_verification_invalidates_through_the_session(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), claim=CLAIM_FACET)
        derived = published.derived
        writer.add(publication_node(derived, assessment_ref=published.assessment.id))
        failed = _mint_verification(
            original=derived.original, replayed=derived.replayed, assessment=derived.assessment, rule=derived.rule,
            report=derived.report, scope_rule=derived.scope_rule, scope=derived.scope, verdict="failed",
            supersedes=derived.identity(),
        )
        successor = writer.add(publication_node(failed, assessment_ref=published.assessment.id))
    finally:
        session.close()
    view = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).read_view
    values = tuple(stored.verification_value(n) for n in view.iter_stored() if n.kind == "verification")
    assert lifecycle_state(values) == INVALIDATED and {v.ref for v in active(values)} == {successor.id}


def test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        library = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
        published = publish_corpus(library, claim=CLAIM_FACET)
        cases = forgeries(library, published)  # [R8] helper records first, then the baseline
        open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).read_view  # a settled, non-writing probe  # noqa: B018
        head_before = chain(root).tip
        intents_before, registrations_before = len(intents(root)), len(registrations(root))
        acts_before = len(session.invocation_acts("A"))
        for node, refusal, reason in cases:
            with pytest.raises(refusal, match=reason):
                writer.add(node)
            assert chain(root).tip == head_before, node.id
            assert len(session.invocation_acts("A")) == acts_before
            assert not (root / "verification" / f"{node.id.split(':', 1)[1]}.md").exists()
        writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        assert len(intents(root)) == intents_before + 1 and len(registrations(root)) == registrations_before + 1
        assert len(session.invocation_acts("A")) == acts_before + 1
    finally:
        session.close()
