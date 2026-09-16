"""Cut 32 canonical declaration: the twenty-six composite-claim sabotages.

One arm per mechanism of the design's §10.3 and of the plan's Tasks 3–6, homed
by declaration unit exactly as the frozen cut document's §5 homes them. Each
`before` block is copied verbatim from the kernel tree Task 8 found, occurs
exactly once in the module it names, and each arm's `checks` name the
acceptance test of its own row — the row's unit is what the arm is an arm of,
so the check that must fail is the one that reads the whole row.

**U10 homes no arm**, and §5 lists none: its row is read from the mm30
reproduction's recorded state in a fresh process, and a source mutation that
moved it would be a mutation of the driver that already ran. The guard's
accounting test says so by name rather than by omission.
"""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U10")
_A = "acceptance/test_composite_acceptance.py"
UNIT_CHECKS = {
    "U1": f"{_A}::test_u1_grammar_kind_and_relations",
    "U2": f"{_A}::test_u2_edges_declared_and_never_redefined",
    "U3": f"{_A}::test_u3_form_classification_and_vocabulary_arms",
    "U4": f"{_A}::test_u4_belief_inert",
    "U5": f"{_A}::test_u5_identity",
    "U6": f"{_A}::test_u6_boundary_resolution_and_identity",
    "U7": f"{_A}::test_u7_audit_codes",
    "U8": f"{_A}::test_u8_reading_equals_the_wrapper",
    "U9": f"{_A}::test_u9_supersession",
    "U10": f"{_A}::test_u10_reproduction",
}
CO_CITED = ()
"""No cut-32 check is any prior cut's: `test_composite_acceptance.py` is this
cut's own module and no earlier arm names a node id in it."""


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-32 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT32_ARMS = (
    # --- U1: the base contract declares the grammar and the kind -----------
    _arm("U1-a", "The base contract carries `composite_grammar`; a document without one is refused at parse, never defaulted.",
         "contract/base.py",
         "    _exact_fields(root, _CONTRACT_FIELDS, source)\n",
         '    root.setdefault("composite_grammar", {"version": 1, "shapes": ["dag"]})  # the grammar made optional, defaulted ahead of the field check\n'
         "    _exact_fields(root, _CONTRACT_FIELDS, source)\n"),

    # --- U2: `edges:` is domain-issued, causal-bound, succession-governed --
    _arm("U2-a", "An `edges:` row names an operator with `causal` among its layers; a statistical operator forms no edge.",
         "contract/domain.py",
         '    if "causal" not in operator.layers:\n        raise MalformedContract(f"{where}: {name!r} admits no causal layer, so it forms no edge")\n',
         '    if False:  # the causal-layer requirement dropped\n        raise MalformedContract(f"{where}: {name!r} admits no causal layer, so it forms no edge")\n'),
    _arm("U2-b", "An edge declaration is claim vocabulary, so succession governs it.",
         "contract/domain.py",
         '            *((f"edge:{name}", decl) for name, decl in self.edges.items()),\n',
         "            *(),  # the edge declarations left out of the claim vocabulary\n"),

    # --- U3: form, classification and the vocabulary halves ----------------
    _arm("U3-a", "A member whose claim is asserted at another layer forms no edge in a dag, even where its operator declares one.",
         "composite.py",
         '        if claim.layer != "causal":\n            raise CompositeError("composite-member-layer", f"member {member}: layer {claim.layer!r} forms no edge in a dag; the inhabited fragment is the causal layer")\n',
         '        if False:  # any layer forms an edge\n            raise CompositeError("composite-member-layer", f"member {member}: layer {claim.layer!r} forms no edge in a dag; the inhabited fragment is the causal layer")\n'),
    _arm("U3-b", "Polarity is the edge's sign and never its presence: a negative member is an arrow, and a cycle through one is a cycle.",
         "composite.py",
         "        edges.append(Edge(cause=cause, effect=effect, sign=claim.polarity, member=member))\n",
         '        if claim.polarity != "negative":  # a negative member is not an arrow\n            edges.append(Edge(cause=cause, effect=effect, sign=claim.polarity, member=member))\n'),
    _arm("U3-c", "A node the consulted vocabulary excludes refuses; a node nothing was looked up for does not.",
         "composite.py",
         '    refused = [label for label, outcome in outcomes.items() if outcome.refuses]\n    if refused:\n        named = ", ".join(',
         '    refused = [label for label, outcome in outcomes.items() if outcome.performed]\n    if refused:\n        named = ", ".join('),
    _arm("U3-d", "A composite over no nodes asserts nothing and is refused by its own code.",
         "composite.py",
         '    if not listed:\n        raise CompositeError("composite-nodes-empty", "a composite over no nodes asserts nothing")\n',
         '    if False:  # the empty node set admitted\n        raise CompositeError("composite-nodes-empty", "a composite over no nodes asserts nothing")\n'),

    # --- U4: belief-inert by construction ----------------------------------
    _arm("U4-a", "A composite naming a proposition never enters that proposition's belief inputs; minting one moves no digest byte.",
         "evaluation.py",
         "    absent.extend(context.snapshot.not_present.items())\n",
         "    absent.extend(context.snapshot.not_present.items())\n"
         "    absent.extend(\n"
         "        (node.id, \"composite\")\n"
         "        for node in view.iter_stored()\n"
         '        if node.kind == "composite" and any(relation.target in set(proposition_refs) for relation in node.relations)\n'
         "    )  # the composites naming the proposition reach the belief inputs\n"),
    _arm("U4-b", "`assesses` keeps its one target kind in the shipped contract; a composite is not an assessable target.",
         "contracts/science/CONTRACT.yaml",
         "  assesses: { group: world, sources: [assessment], targets: [proposition] }\n",
         "  assesses: { group: world, sources: [assessment], targets: [proposition, composite] }\n"),
    _arm("U4-c", "An otherwise eligible assessment naming a composite is refused at the signature; the eligibility predicate alone admits it.",
         "corpus.py",
         '            if target.kind != "proposition":\n                raise SignatureRefused(\n',
         "            if False:  # the target's kind no longer checked\n                raise SignatureRefused(\n"),
    _arm("U4-d", "An `assesses` target that resolves nowhere refuses, so a later `composite:future` cannot establish the edge by arriving second.",
         "corpus.py",
         "            except RefError as caught:\n"
         "                # Not the eligibility predicate's to refuse: it reads the run and\n"
         "                # its observed datasets and never the target. An edge to a ref\n"
         "                # that resolves nowhere would let a later `composite:future`\n"
         "                # establish the forbidden edge by arriving second.\n"
         "                raise SignatureRefused(\n"
         '                    f"{node.id}: assesses-target-unresolvable: {relation.target} resolves to no record in this corpus"\n'
         "                ) from caught\n",
         "            except RefError:\n                continue  # an unresolvable assesses target admitted\n"),

    # --- U5: content identity over the covered facet -----------------------
    _arm("U5-a", "The node set is a member of the identity, so a node with no member moves it.",
         "composite.py",
         '    return v1.digest(COMPOSITE_DOMAIN, {"kind": "composite", "present": ["composite"], "facets": {"composite": facet.projection()}})\n',
         "    projection = facet.projection()\n"
         '    projection.pop("nodes")  # the node set dropped from the identity\n'
         '    return v1.digest(COMPOSITE_DOMAIN, {"kind": "composite", "present": ["composite"], "facets": {"composite": projection}})\n'),

    # --- U6: the boundary re-derives resolution and identity ---------------
    _arm("U6-a", "Every `composes` target is restored and its semantic identity compared with the facet's member at that position.",
         "corpus.py",
         "        refs = tuple(relation.target for relation in composes)\n"
         "        claims = composite_module.restore_members(\n"
         "            view, facet.members, refs, profile=self._profile, snapshot=composite_module.EMPTY_SNAPSHOT\n"
         "        )  # steps 2–3\n"
         "        composite_module.classify(self._profile, facet, claims)  # step 4\n",
         "        for relation in composes:  # form only: the member is looked up and never compared\n"
         "            view.get(relation.target)\n"),
    _arm("U6-b", "The facet and the relation set agree in cardinality, or the record is refused before anything is zipped.",
         "corpus.py",
         "        if len(composes) != len(facet.members) or any(relation.source != node.id for relation in composes):\n",
         "        if any(relation.source != node.id for relation in composes):\n"),

    # --- U7: the audit reports contradictions, not malformedness -----------
    _arm("U7-a", "`check_composite` runs in the corpus audit's own dispatch, so a raw-written composite is read there.",
         "audit.py",
         '            elif node.kind == "composite":\n                outcome = check_composite(view, node, profile=profile)\n',
         "            elif False:  # the composite arm dropped from the audit loop\n                outcome = check_composite(view, node, profile=profile)\n"),
    _arm("U7-b", "An unresolvable member is reported under its own code, never folded into `composite-malformed`.",
         "audit.py",
         '        if refused.code in ("composite-member-unresolvable", "composite-member-mismatch"):\n',
         '        if refused.code in ("composite-member-mismatch",):  # unresolvable folded into malformed\n'),

    # --- U8: the reading is a pure function of its named arguments ---------
    _arm("U8-a", "An unresolvable member refuses the reading; it is never dropped and never read as a beliefless row.",
         "composite.py",
         "    refs = tuple(r.target for r in composes)\n    claims = restore_members(view, facet.members, refs, profile=profile, snapshot=resolution)\n",
         "    refs = tuple(r.target for r in composes)\n"
         "    kept = tuple((m, r) for m, r in zip(facet.members, refs, strict=True) if view.holds(r))  # type: ignore[attr-defined]\n"
         "    facet = CompositeFacet(grammar=facet.grammar, shape=facet.shape, nodes=facet.nodes, members=tuple(m for m, _ in kept))\n"
         "    refs = tuple(r for _, r in kept)\n"
         "    claims = restore_members(view, facet.members, refs, profile=profile, snapshot=resolution)\n"),
    _arm("U8-b", "A member with no admitted assessment reads `{}`; an empty identification set is never defaulted to a term.",
         "composite.py",
         "            identification = tuple(sorted(terms))\n",
         '            identification = tuple(sorted(terms)) or ("identification:observational",)\n'),
    _arm("U8-c", "Availability is the caller's argument, never rebuilt from the corpus: withholding an observation reads the evaluator's own answer.",
         "composite.py",
         "    rows: list[MemberRow] = []\n    for member, member_ref in zip(facet.members, refs, strict=True):\n",
         "    from beliefs.dataset import ByteObservation as _ByteObservation\n"
         "    from beliefs.dataset import dataset_address as _dataset_address\n"
         "    from beliefs.stored import dataset_declaration as _dataset_declaration\n"
         "\n"
         "    _held: dict[str, tuple[_ByteObservation, ...]] = {}\n"
         "    for _node in view.iter_stored():  # type: ignore[attr-defined]\n"
         '        if _node.kind != "dataset":\n'
         "            continue\n"
         "        _declaration = _dataset_declaration(_node)\n"
         "        _address = _dataset_address(_declaration)\n"
         "        if _address is not None:\n"
         '            _held[_address] = tuple(_ByteObservation(digest=_r.digest, location="view://stored") for _r in _declaration.resources if _r.digest is not None)\n'
         "    availability = Availability(observations=_held, implementations=availability.implementations, fixtures=availability.fixtures)\n"
         "\n"
         "    rows: list[MemberRow] = []\n"
         "    for member, member_ref in zip(facet.members, refs, strict=True):\n"),
    _arm("U8-d", "The reading goes through the evaluator's own wrapper, so a member whose inputs sit in an absent corpus reads `unavailable-corpus-absent`.",
         "composite.py",
         "        answer, admission = evaluate_over_traced(\n"
         "            view,  # type: ignore[arg-type]\n"
         "            member_ref, availability=availability, context=context, profile=profile, resolution=resolution, binding=binding,\n"
         "        )\n",
         "        from dataclasses import replace as _replace\n"
         "\n"
         "        from beliefs.belief import evaluate_traced as _evaluate_traced\n"
         "        from beliefs.evaluation import gather as _gather\n"
         "\n"
         "        _inputs = _gather(view, member_ref, context=context, profile=profile, resolution=resolution, binding=binding)  # type: ignore[arg-type]\n"
         "        answer, admission = _evaluate_traced(\n"
         "            proposition=member_ref, records=_inputs.records(), availability=availability,\n"
         "            context=_replace(context, node_corpus=_inputs.node_corpus), binding=binding, profile=profile,\n"
         "        )  # the absent-corpus arm skipped\n"),
    _arm("U8-e", "The identification column reads the traced admission and never decides admission again for itself.",
         "composite.py",
         "                if value.identity() in admission.admitted:\n                    terms.add(value.estimand.control.identification.term)\n",
         "                from beliefs.admission import Admitted as _Admitted\n"
         "                from beliefs.admission import admit as _admit\n"
         "                from beliefs.corpus import run_value as _run_value\n"
         "                from beliefs.stored import typed_ref as _typed_ref\n"
         "\n"
         '                _own = _admit(value, _run_value(view, _typed_ref("run", value.run)), availability.observations, ())  # a second decision, per gathered assessment\n'
         "                if isinstance(_own, _Admitted):\n"
         "                    terms.add(value.estimand.control.identification.term)\n"),
    _arm("U8-f", "An answer the evaluator reaches through the gate carries the admission it rests on; only an answer given before it is `not-reached`.",
         "belief.py",
         '        return NoBelief("no-directional-outcome"), reached\n',
         '        return NoBelief("no-directional-outcome"), NotReached()\n'),
    _arm("U8-g", "Admission runs once per member, inside the evaluator; the reading never runs a second pass over the gathered records.",
         "composite.py",
         "            terms = set()\n",
         "            from beliefs import belief as _belief\n"
         "\n"
         "            _belief.admitted((), runs={}, observations=availability.observations, verifications=())  # a second admission pass\n"
         "            terms = set()\n"),

    # --- U9: same-kind succession on the shared path -----------------------
    _arm("U9-a", "The `same_kind` rule sits outside the `document_validated` shortcut, so an import bundle is held to it too.",
         "corpus.py",
         "        reading = self._view if view is None else view\n        self._refuse_supersedes_same_kind(node, view=reading)\n",
         "        reading = self._view if view is None else view\n        if not document_validated:\n            self._refuse_supersedes_same_kind(node, view=reading)\n"),
    _arm("U9-b", "`same_kind` on a relation whose sources and targets differ is refused at parse, in both implementations.",
         "contract/base.py",
         "        if same_kind and set(sources) != set(targets):\n",
         "        if False:  # the same_kind endpoint-set rule dropped\n"),
    _arm("U9-c", "A raw-written cross-kind `supersedes` edge is reported under its own audit code.",
         "audit.py",
         '        if target.kind != node.kind:\n            detail = f"a {node.kind!r} names a {target.kind!r} predecessor ({relation.target})"\n',
         '        if False:  # cross-kind succession no longer reported\n            detail = f"a {node.kind!r} names a {target.kind!r} predecessor ({relation.target})"\n'),
)
