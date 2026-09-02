"""Cut 14: 29 selected units, 29 lettered arms; no labeled or intent-position unit."""

from n2_arms import Arm, Sabotage

_COORDINATION = "coordination.py"
_QUERY = "view_query.py"
_CORPUS = "corpus.py"
_PROFILE = "profile.py"
_DOMAIN = "contract/domain.py"
_EPOCH = "world/epoch.py"
_ACCEPT = "acceptance/test_coordination_acceptance.py"

_UNIT_OF_LETTERED = {
    "W11a": "W11u1",
    "W11b": "W11u2",
    "W12a": "W12u1",
    "W13a": "W13u1",
    **{f"W17{letter}": f"W17u{number}" for number, letter in enumerate("abcdefghijklmn", 1)},
    **{f"W18{letter}": f"W18u{number}" for number, letter in enumerate("abcdefghijk", 1)},
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED[row]


ROW_UNITS = {"W11": 2, "W12": 1, "W13": 1, "W17": 14, "W18": 11}
LABELED_UNITS: tuple[str, ...] = ()
CO_CITED: dict[str, tuple[str, ...]] = {}

CUT14_ARMS = (
    Arm(
        "W11a",
        "view queries reject coordination addresses by tier before lookup",
        Sabotage(
            _QUERY,
            before='    if (\n        separator != ":"\n        or kind not in stored.WORLD_KINDS\n        or not local\n        or value.startswith("coord:")\n    ):\n        raise ValueError(f"view query {where} must be a world-tier address")',
            after='    if False:\n        raise ValueError(f"view query {where} must be a world-tier address")',
        ),
        (f"{_ACCEPT}::test_w11a_view_queries_reject_coordination_addresses",),
    ),
    Arm(
        "W11b",
        "coordination reference fields reject world addresses before lookup",
        Sabotage(_CORPUS, before="        CoordinationAddress.parse(value)", after="        pass"),
        (f"{_ACCEPT}::test_w11b_coordination_fields_reject_world_addresses",),
    ),
    Arm(
        "W12a",
        "project rename leaves project identity and subordinate resolution unchanged",
        Sabotage(
            _CORPUS,
            before="        revisions = tuple(revision for revision in self._revisions() if revision.address == address.unpinned())",
            after="        revisions = tuple(revision for revision in self._revisions() if revision.address == address.unpinned() and revision.node.title == address.project)",
        ),
        (f"{_ACCEPT}::test_w12_renaming_a_project_preserves_every_subordinate_address",),
    ),
    Arm(
        "W13a",
        "project identity is independent of corpus identity and mount",
        Sabotage(
            _CORPUS,
            before='            project_identity = secrets.token_hex(16) if kind == "project" else project.project',
            after='            project_identity = __import__("beliefs.world", fromlist=["load_manifest"]).load_manifest(self._corpus.store.root).corpus_id if kind == "project" else project.project',
        ),
        (f"{_ACCEPT}::test_w13_project_identity_is_independent_of_corpus_identity_and_mount",),
    ),
    Arm(
        "W17a",
        "genesis names zero predecessors",
        Sabotage(
            _CORPUS,
            before="            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())",
            after='            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=("project:" + "0" * 32 + "." + "0" * 32,))',
        ),
        (f"{_ACCEPT}::test_w17a_genesis_names_zero_predecessors",),
    ),
    Arm(
        "W17b",
        "ordinary family doors refuse coordination kinds including note",
        Sabotage(
            _CORPUS,
            before='        if node.kind in COORDINATION_KINDS:\n            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")',
            after='        if False:\n            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")',
        ),
        (f"{_ACCEPT}::test_w17b_every_ordinary_door_refuses_coordination",),
    ),
    Arm(
        "W17c",
        "import refuses a coordination member and names it",
        Sabotage(
            _CORPUS,
            before='            if record.kind in COORDINATION_KINDS:\n                raise ImportRefused(f"{record.id}: coordination records are replicated with their corpus, never imported", member=record.id)',
            after='            if False:\n                raise ImportRefused(f"{record.id}: coordination records are replicated with their corpus, never imported", member=record.id)',
        ),
        (f"{_ACCEPT}::test_w17c_import_refuses_and_names_the_coordination_member",),
    ),
    Arm(
        "W17d",
        "the coordination door refuses every world kind",
        Sabotage(
            _CORPUS,
            before='        if kind in stored.WORLD_KINDS:\n            raise CoordinationKindUnsupported(f"{kind!r} is a world kind, not a coordination kind")',
            after='        if False:\n            raise CoordinationKindUnsupported(f"{kind!r} is a world kind, not a coordination kind")',
        ),
        (f"{_ACCEPT}::test_w17d_coordination_door_refuses_world_kinds",),
    ),
    Arm(
        "W17e",
        "an already-minted revision pair refuses before planning",
        Sabotage(
            _CORPUS,
            before="            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())\n            self._refuse_already_minted(candidate)",
            after="            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())",
        ),
        ("test_coordination_write.py::test_w17e_an_already_minted_revision_pair_refuses_before_plan",),
    ),
    Arm(
        "W17f",
        "every supplied predecessor stands at commit",
        Sabotage(
            _CORPUS,
            before='            if predecessor_ids - {revision.node.uid for revision in standing}:\n                raise PredecessorNotStanding("every supplied predecessor must be a standing tip at commit")',
            after='            if False:\n                raise PredecessorNotStanding("every supplied predecessor must be a standing tip at commit")',
        ),
        (f"{_ACCEPT}::test_w17f_a_superseded_predecessor_refuses_at_commit",),
    ),
    Arm(
        "W17g",
        "kind and address continuity are checked before standing",
        Sabotage(
            _CORPUS,
            before='                if predecessor.node.kind != kind or predecessor.address != address:\n                    raise PredecessorMismatch(f"revision {predecessor.node.uid} belongs to {predecessor.node.kind} {predecessor.address}, not {kind} {address}")',
            after='                if False:\n                    raise PredecessorMismatch(f"revision {predecessor.node.uid} belongs to {predecessor.node.kind} {predecessor.address}, not {kind} {address}")',
        ),
        (f"{_ACCEPT}::test_w17g_continuity_refuses_a_standing_predecessor_of_another_address_or_kind",),
    ),
    Arm(
        "W17h",
        "siblings refuse with sorted tips independent of mount order",
        Sabotage(
            _CORPUS,
            before='        if len(tips) > 1:\n            return CoordinationRefused("divergent-view", tuple(revision.node.uid for revision in tips))',
            after='        if False:\n            return CoordinationRefused("divergent-view", tuple(revision.node.uid for revision in tips))',
        ),
        (f"{_ACCEPT}::test_w17h_siblings_refuse_with_sorted_tips_independent_of_mount_order",),
    ),
    Arm(
        "W17i",
        "one revision over every tip repairs divergence and retains siblings",
        Sabotage(
            _COORDINATION,
            before="        for predecessor in revision.predecessors",
            after="        for predecessor in revision.predecessors[:1]",
        ),
        (f"{_ACCEPT}::test_w17i_all_tip_repair_restores_resolution_and_retains_siblings",),
    ),
    Arm(
        "W17j",
        "a raw supersession cycle has zero tips and an audit finding",
        Sabotage(_CORPUS, before="        if revisions and not standing_tips(revisions):", after="        if False:"),
        (f"{_ACCEPT}::test_w17j_a_raw_cycle_has_no_tip_and_an_audit_finding",),
    ),
    Arm(
        "W17k",
        "a malformed coordination facet is reported and excluded from tips",
        Sabotage(
            _CORPUS,
            before="                if coordination_facet_malformed(node):\n                    continue",
            after="                if False:\n                    continue",
        ),
        (f"{_ACCEPT}::test_w17k_a_malformed_facet_is_reported_and_excluded",),
    ),
    Arm(
        "W17l",
        "a subordinate under a missing project refuses",
        Sabotage(
            _CORPUS,
            before='        if resolved_project is None:\n            raise ProjectNotResolvable(f"{project}: project does not resolve")',
            after='        if False:\n            raise ProjectNotResolvable(f"{project}: project does not resolve")',
        ),
        (f"{_ACCEPT}::test_w17l_a_subordinate_under_a_missing_project_refuses",),
    ),
    Arm(
        "W17m",
        "a subordinate under a divergent project names every project tip",
        Sabotage(
            _CORPUS,
            before='        if isinstance(resolved_project, CoordinationRefused):\n            raise ProjectNotResolvable(f"{project}: project is divergent", tips=resolved_project.tips)',
            after='        if False:\n            raise ProjectNotResolvable(f"{project}: project is divergent", tips=resolved_project.tips)',
        ),
        (f"{_ACCEPT}::test_w17m_a_subordinate_under_a_divergent_project_names_the_project_tips",),
    ),
    Arm(
        "W17n",
        "every edit is a new whole revision and retains the predecessor",
        Sabotage(
            _CORPUS,
            before="            new_revision_identity = secrets.token_hex(16)",
            after="            new_revision_identity = next(iter(predecessor_ids))",
        ),
        (f"{_ACCEPT}::test_w17n_every_edit_is_a_new_whole_revision",),
    ),
    Arm(
        "W18a",
        "an undeclared coordination kind authorizes no mint",
        Sabotage(
            _CORPUS,
            before='        kind_spec = profile.coordination_kinds.get(kind)\n        if kind_spec is None:\n            raise ValidationRefused(f"{kind!r} is not declared by the mounted coordination contract")',
            after="        kind_spec = profile.coordination_kinds.get(kind) or next(iter(profile.coordination_kinds.values()))",
        ),
        (
            f"{_ACCEPT}::test_w18a_an_undeclared_kind_mints_nothing",
            "test_coordination_write.py::test_an_earlier_contract_version_authorizes_nothing_added_later",
        ),
    ),
    Arm(
        "W18b",
        "an ill-formed query refuses at mint",
        Sabotage(
            _CORPUS,
            before='        query = parse_view_query(content["query"])',
            after='        query = parse_view_query({"version": "science.view-query.v1", "clauses": []})',
        ),
        (f"{_ACCEPT}::test_w18b_malformed_query_refuses",),
    ),
    Arm(
        "W18c",
        "a query kind outside the pinned literal vocabulary refuses",
        Sabotage(
            _CORPUS,
            before='        if query.world_kinds() - profile.coordination_query_kinds:\n            raise ValidationRefused("view query names a world kind outside the coordination contract vocabulary")',
            after='        if False:\n            raise ValidationRefused("view query names a world kind outside the coordination contract vocabulary")',
        ),
        ("test_coordination_write.py::test_w18c_a_query_kind_outside_the_contract_refuses",),
    ),
    Arm(
        "W18d",
        "a query relation outside the pinned literal vocabulary refuses",
        Sabotage(
            _CORPUS,
            before='        if query.relations() - profile.coordination_query_relations:\n            raise ValidationRefused("view query names a relation outside the coordination contract vocabulary")',
            after='        if False:\n            raise ValidationRefused("view query names a relation outside the coordination contract vocabulary")',
        ),
        ("test_coordination_write.py::test_w18d_a_query_relation_outside_the_contract_refuses",),
    ),
    Arm(
        "W18e",
        "a syntactically valid unresolved query anchor is accepted",
        Sabotage(
            _CORPUS,
            before="        return query",
            after='        if query.addresses():\n            raise ValidationRefused("view query address does not resolve")\n        return query',
        ),
        (f"{_ACCEPT}::test_w18e_an_unresolved_anchor_is_accepted",),
    ),
    Arm(
        "W18f",
        "the compiler refuses query vocabulary outside kernel inventories",
        Sabotage(
            _PROFILE,
            before='        if unknown_kinds or unknown_relations:\n            raise ProfileError("coordination query vocabulary is outside the kernel inventory")',
            after='        if False:\n            raise ProfileError("coordination query vocabulary is outside the kernel inventory")',
        ),
        (
            "test_profile.py::test_coordination_compile_refuses_unknown_query_kind",
            "test_profile.py::test_coordination_compile_refuses_unknown_query_relation",
        ),
    ),
    Arm(
        "W18g",
        "editorial and lineage edits move contract identity but not compiled identity",
        Sabotage(
            _PROFILE,
            before="    return contract.schema_projection()",
            after='    return {**contract.schema_projection(), "contract": contract.content_identity}',
        ),
        ("test_profile.py::test_coordination_editorial_edits_do_not_recompile",),
    ),
    Arm(
        "W18h",
        "coordination schema edits move compiled identity",
        Sabotage(_PROFILE, before="    return contract.schema_projection()", after="    return {}"),
        ("test_profile.py::test_coordination_schema_edits_recompile",),
    ),
    Arm(
        "W18i",
        "coordination moves packaging identity but enters no world map",
        Sabotage(_EPOCH, before="        if node.kind in stored.WORLD_KINDS", after="        if True"),
        (f"{_ACCEPT}::test_w18i_coordination_moves_epoch_identity_not_world_maps_or_belief_input",),
    ),
    Arm(
        "W18j",
        "an activated coordination pin never enters a belief input digest",
        Sabotage(
            "consulted.py",
            before='    consulted: dict[str, str] = {BASE_NAMESPACE: base_identities.pop()}',
            after='    consulted: dict[str, str] = {BASE_NAMESPACE: base_identities.pop()}\n    if "coordination" in pins[corpora[0]].domains:\n        consulted["coordination"] = pins[corpora[0]].domains["coordination"]',
        ),
        ("test_belief.py::test_w18j_a_coordination_pin_never_enters_the_belief_input_digest",),
    ),
    Arm(
        "W18k",
        "a domain contract cannot claim the coordination namespace",
        Sabotage(
            _DOMAIN,
            before='    if namespace == "coordination":\n        raise MalformedContract(f"{source}: \'coordination\' is reserved for the coordination contract")',
            after='    if False:\n        raise MalformedContract(f"{source}: \'coordination\' is reserved for the coordination contract")',
        ),
        ("test_domain_contract.py::test_a_domain_contract_cannot_claim_the_coordination_namespace",),
    ),
)
