"""Frozen cut-43 declaration: nine units, nine sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "J12-a",
    "J12-b",
    "J12-c",
    "J13-a",
    "J13-b",
    "J14-a",
    "J15-a",
    "J15-b",
    "J15-c",
)
UNIT_CHECKS = {
    "J12-a": "acceptance/test_session_mounts_acceptance.py::test_j12_a_a_write_root_outside_the_configured_roots_refuses_durably",
    "J12-b": "acceptance/test_session_mounts_acceptance.py::test_j12_b_a_mount_set_other_than_the_configured_roots_refuses_durably",
    "J12-c": "acceptance/test_session_mounts_acceptance.py::test_j12_c_the_session_writes_the_named_root_and_only_it_durably",
    "J13-a": "test_mount.py::test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin",
    "J13-b": "test_mount.py::test_an_available_unpinned_document_is_never_activated",
    "J14-a": "acceptance/test_session_mounts_acceptance.py::test_j14_a_coordination_resolves_over_every_mount_durably",
    "J15-a": "acceptance/test_session_mounts_acceptance.py::test_j15_a_a_session_never_writes_a_read_mount_durably",
    "J15-b": "test_session_reconcile.py::test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there",
    "J15-c": "test_session_reconcile.py::test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-43 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT43_ARMS = (
    _arm(
        "J12-a",
        "session/__init__.py",
        "A write root outside the configured roots refuses before creating a session.",
        "    if write_root not in world_config.corpus_roots:",
        "    if False:",
    ),
    _arm(
        "J12-b",
        "session/__init__.py",
        "The mount keys resolve to exactly the configured roots, without aliases.",
        "        if len(set(resolved)) != len(resolved) or set(resolved) != configured:",
        "        if False:",
    ),
    _arm(
        "J12-c",
        "session/__init__.py",
        "The session writes the explicitly selected root.",
        "    root = write_root",
        "    root = world_config.corpus_roots[0]",
    ),
    _arm(
        "J13-a",
        "mount.py",
        "A mount activates the exact content identity its manifest pins.",
        "        match = next((c for c in candidates if c.content_identity == identity), None)",
        "        match = next(iter(candidates), None)",
    ),
    _arm(
        "J13-b",
        "mount.py",
        "Available contracts never activate without a manifest pin.",
        "    return compile_profile(base, domains, coordination=coordination)",
        "    return compile_profile(base, [*domains, *(d for d in documents if d.namespace not in {m.namespace for m in domains})], coordination=coordination)",
    ),
    _arm(
        "J14-a",
        "session/__init__.py",
        "Coordination resolves over every mounted corpus.",
        "    resolver = _mount_resolver(mounted)",
        "    resolver = _mount_resolver({root: mounted[root]} if mounted is not None else None)",
    ),
    _arm(
        "J15-a",
        "session/__init__.py",
        "A session never writes a read mount.",
        "    def writer_factory(authority: Authority) -> CorpusWriter:\n        return CorpusWriter(",
        "    def writer_factory(authority: Authority) -> CorpusWriter:\n        root = next(r for r, p in (mounted or {}).items() if r != write_root and p.compiled_identity == profile.compiled_identity)\n        return CorpusWriter(",
    ),
    _arm(
        "J15-b",
        "session/reconcile.py",
        "A registration is covered only by an act naming its corpus.",
        "            acts: set[str] = {act.entry for act in reader.acts() if act.corpus == corpus_id} if reader is not None else set()",
        "            acts: set[str] = {act.entry for act in reader.acts()} if reader is not None else set()",
    ),
    _arm(
        "J15-c",
        "session/reconcile.py",
        "An act is verified only by a registration held in its named corpus.",
        "            if act.corpus in well_formed and (act.corpus, act.entry) not in committed_pairs:",
        "            if act.corpus in well_formed and act.entry not in {digest for _, digest in committed_pairs}:",
    ),
)
