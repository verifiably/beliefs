"""Cut 19's eleven frozen declaration units and their source sabotages.

One grouped unit per `J` row of `docs/designs/2026-09-05-conformance-cut-19.md`
§3 — eleven guarantee rows, counted once each in §4. Lettered arms (`J1a`,
`J8f`, …) normalize back to their unit through `unit_of`; the inventory is
`DECLARATION_UNITS` and nothing else.

Every `before` is copied from the landed source, not from the plan: the cut
was frozen before implementation and §8 records the mechanism amendment the
implementation landed (design §13 items 9–19). Where the freeze's arm list
named a superseded site, the arm below sabotages the site that carries the
same guarantee now — `_RoutedExecutor.commit_fulfilling` for the commit seam,
`CorpusWriter._operation` for the settling hold, `session/ledger.py` for the
ledger evidence reader — and the results record lists every substitution.

The checks are cut 19's own: `tests/acceptance/test_session_acceptance.py` on
the certified engine and volume, and the portable session modules beside it.
No arm borrows a prior cut's evidence, so `CO_CITED` is empty.
"""

from n2_arms import Arm, Sabotage

_CORPUS = "corpus.py"
_ROOT = "root.py"
_REPORT = "report.py"
_REDUCE = "intents/reduce.py"
_WRITER = "session/writer.py"
_LEDGER = "session/ledger.py"
_RECONCILE = "session/reconcile.py"
_SESSION = "session/__init__.py"

_A = "acceptance/test_session_acceptance.py"
_OPS = "test_operation_writes.py"
_CW = "test_corpus_write.py"
_SW = "test_session_writer.py"
_SL = "test_session_ledger.py"
_SR = "test_session_reconcile.py"
_PB = "test_permit_boundary.py"

_J1 = f"{_A}::test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration"
_J1R = f"{_A}::test_j1_refusals_append_nothing_of_their_own"
_J1U = f"{_A}::test_j1_a_refusal_on_a_root_left_unresolved_moves_the_head_only_by_settlement"
_J2 = f"{_A}::test_j2_a_failure_before_submission_leaves_an_intent_and_no_record"
_J2R = f"{_A}::test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed"
_J2C = f"{_A}::test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare"
_J2H = f"{_A}::test_j2_library_and_mixed_handles_settle_first"
_J2I = f"{_A}::test_j2_a_post_commit_index_failure_on_add_leaves_the_root_unresolved"
_J2L = f"{_A}::test_j2_a_ledger_write_failure_after_commit_leaves_the_registration_uncovered"
_J2F = f"{_A}::test_j2_a_ledger_fsync_failure_after_a_complete_act_line_ends_the_session"
_J3 = f"{_A}::test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session"
_J4 = f"{_A}::test_j4_every_intent_carries_the_session_actor"
_J5 = f"{_A}::test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock"
_J5L = f"{_SW}::test_the_session_lock_spans_the_act_so_no_claim_interleaves_with_a_commit"
_J6 = f"{_SW}::test_the_claim_table"
_J6A = f"{_SW}::test_an_abandoned_invocation_stays_open_and_never_blocks_a_fresh_claim"
_J6R = f"{_SW}::test_a_refusal_outcome_replays_whole_and_detached_from_every_caller"
_J7 = f"{_SL}::test_each_append_is_fsynced_once_and_lands_before_return"
_J7P = f"{_SL}::test_a_partial_write_ends_the_writer_and_preserves_the_bytes"
_J7L = f"{_SW}::test_a_ledger_failure_ends_the_session"
_J8 = f"{_A}::test_j8_reconciliation_over_the_real_root"
_J8P = f"{_SR}::test_the_views_pending_pairs_absent_from_entries_are_reported_without_an_intent"
_J8F = f"{_SR}::test_uncovered_committed_registration_with_no_open_invocation_is_foreign"
_J8U = f"{_SR}::test_unreadable_ledgers_are_findings_and_their_intents_read_outcome_unknown"
_J8H = f"{_A}::test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold"
_J8I = f"{_A}::test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write"
_J9 = f"{_A}::test_j9_lifecycle_and_the_refusing_configurations"
_J10 = f"{_A}::test_j10_a_session_write_is_indistinguishable_on_ordinary_read"
_J11 = f"{_A}::test_j11_a_writer_is_bound_to_one_invocation_durably"

DECLARATION_UNITS = tuple(f"J{n}" for n in range(1, 12))
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


# --- the commit seam's text, quoted once so the arms that reorder it agree ----
_PREFLIGHT = (
    "        try:\n"
    "            scope.port.preflight(plan)\n"
    "        except PlanRefusedError as caught:\n"
    "            raise PlanRefused(str(caught)) from caught\n"
)
_SUBMITTED = "        scope.submitted = True  # the refusals are behind us; the intent is the first effect\n"
_INTENT = (
    "        self._state.unresolved = True\n"
    "        token = secrets.token_hex(16)\n"
    "        intent_digest = scope.port.append_intent(\n"
    '            _encode_operation_intent("corpus-write", token, scope.authority.actor)\n'
    "        )\n"
)


CUT19_ARMS = (
    # --- J1: one intent and one fulfilling registration per scoped write -------
    Arm(
        row="J1a",
        asserts="the intent is the first effect: nothing is appended before the preflight has cleared",
        sabotage=Sabotage(
            module=_CORPUS,
            before=_PREFLIGHT + _SUBMITTED + _INTENT,
            after=_SUBMITTED + _INTENT + _PREFLIGHT,
        ),
        checks=(_J1R, _J1U),
    ),
    Arm(
        row="J1b",
        asserts="a fulfilling scope's one submission is committed by the seam, never by the plain executor",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        self.commit_fulfilling(scope, plan)\n",
            after="        self._inner.execute(plan)\n",
        ),
        checks=(_J1, _J3),
    ),
    Arm(
        row="J1c",
        asserts="a portless writer refuses every operation write before any body refusal",
        sabotage=Sabotage(
            module=_CORPUS,
            before=(
                "        if port is None:\n"
                '            raise OperationPortMissing("this corpus has no operation port; '
                'operation writes are session-mediated")\n'
            ),
            after="        if port is None:\n            pass\n",
        ),
        checks=(f"{_OPS}::test_a_writer_without_a_port_refuses_every_operation_before_any_refusal",),
    ),
    Arm(
        row="J1d",
        asserts="the preflight refusal reaches the caller as the kernel's `PlanRefused`, not the engine's type",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            raise PlanRefused(str(caught)) from caught\n",
            after="            raise\n",
        ),
        checks=(_J1R, f"{_OPS}::test_an_over_ceiling_record_is_plan_refused_before_the_intent"),
    ),
    Arm(
        row="J1e",
        asserts="`corpus-write` is a closed-set operation kind the intent record admits",
        sabotage=Sabotage(
            module=_REPORT,
            before='OPERATION_KINDS = ("acquisition", "audit", "consolidate", "corpus-write", '
            '"import", "move", "re-check", "run-attempt")',
            after='OPERATION_KINDS = ("acquisition", "audit", "consolidate", '
            '"import", "move", "re-check", "run-attempt")',
        ),
        checks=(_J1,),
    ),
    Arm(
        row="J1f",
        asserts="a `corpus-write` intent qualifies by its fulfilling registration in the reduction",
        sabotage=Sabotage(
            module=_REDUCE,
            before='    if intent.shape == "operation" and isinstance(value, OperationIntent) '
            'and value.kind == "corpus-write":\n',
            after='    if intent.shape == "operation" and isinstance(value, OperationIntent) '
            'and value.kind == "never":\n',
        ),
        checks=(_J1,),
    ),
    Arm(
        row="J1g",
        asserts="a preflight refusal is a refusal, not a post-submission `ExecutionError`",
        sabotage=Sabotage(
            module=_CORPUS,
            before=_PREFLIGHT + _SUBMITTED,
            after=_SUBMITTED + _PREFLIGHT,
        ),
        checks=(_J1R, f"{_OPS}::test_an_over_ceiling_record_is_plan_refused_before_the_intent"),
    ),
    Arm(
        row="J1h",
        asserts="the commit seam stays the write inventory's own row — the static boundary is closed both ways",
        sabotage=Sabotage(
            module=_CORPUS,
            before=(
                "        self.commit_fulfilling(scope, plan)\n"
                "\n"
                "    def commit_fulfilling(self, scope: _Fulfillment, plan: WritePlan) -> None:\n"
            ),
            after=(
                "        self.commit_fulfilment(scope, plan)\n"
                "\n"
                "    def commit_fulfilment(self, scope: _Fulfillment, plan: WritePlan) -> None:\n"
            ),
        ),
        checks=(f"{_PB}::test_the_inventory_is_closed_in_both_directions",),
    ),
    # --- J2: the unresolved root, and what a failure leaves behind -------------
    Arm(
        row="J2a",
        asserts="the settling hold clears `unresolved` only on a clean outermost exit",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            if exc_type is None and state.depth == 0:\n",
            after="            if state.depth == 0:\n",
        ),
        checks=(_J2R,),
    ),
    Arm(
        row="J2b",
        asserts="a fresh root state is unresolved until its first write settles it",
        sabotage=Sabotage(
            module=_CORPUS,
            before="    unresolved: bool = True\n",
            after="    unresolved: bool = False\n",
        ),
        checks=(
            (
                f"{_CW}::TestTheUnresolvedRoot::"
                "test_a_fresh_root_state_is_unresolved_and_the_first_write_settles_it"
            ),
        ),
    ),
    Arm(
        row="J2c",
        asserts="settlement runs the root's recovery before the rebuild",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            state.recover(state.corpus.store.root)\n",
            after="            pass\n",
        ),
        checks=(_J2C,),
    ),
    Arm(
        row="J2d",
        asserts="the root state binds the factory's recovery capability when it is built",
        sabotage=Sabotage(
            module=_CORPUS,
            before='                getattr(executor_factory, "recover", None),\n',
            after="                None,\n",
        ),
        checks=(_J2C, _J2H),
    ),
    Arm(
        row="J2e",
        asserts="the durable factory's `recover` resolves the engine's recovery for the root",
        sabotage=Sabotage(
            module=_ROOT,
            before="        target = Path(root)\n",
            after="        return\n        target = Path(root)\n",
        ),
        checks=(_J2C,),
    ),
    Arm(
        row="J2f",
        asserts="an ordinary submission marks the root unresolved before it delegates",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            self._state.unresolved = True\n            self._inner.execute(plan)\n",
            after="            self._inner.execute(plan)\n",
        ),
        checks=(
            (
                f"{_CW}::TestTheUnresolvedRoot::"
                "test_a_failed_submission_leaves_the_root_unresolved_and_the_next_write_recovers_first"
            ),
        ),
    ),
    Arm(
        row="J2g",
        asserts="the rebuild keeps the routed executor: the wrapper survives a reconstruction",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        corpus = Corpus(self._corpus.store.root, executor_factory=self._state.executors)\n",
            after="        corpus = Corpus(self._corpus.store.root, executor_factory=self._state.executor_factory)\n",
        ),
        checks=(
            (
                f"{_CW}::TestTheUnresolvedRoot::"
                "test_the_root_state_binds_the_factory_recover_and_wraps_its_executors"
            ),
        ),
    ),
    Arm(
        row="J2h",
        asserts="a failure after the submission is normalized to `ExecutionError`; one before it is not",
        sabotage=Sabotage(
            module=_CORPUS,
            before="                if scope.submitted:\n",
            after="                if False:\n",
        ),
        checks=(f"{_OPS}::test_a_post_submission_failure_on_the_twin_is_an_execution_error", _J2I),
    ),
    Arm(
        row="J2i",
        asserts="the seam marks the root unresolved before the intent, so a post-commit failure leaves it set",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        self._state.unresolved = True\n        token = secrets.token_hex(16)\n",
            after="        token = secrets.token_hex(16)\n",
        ),
        checks=(_J2R, _J2I),
    ),
    Arm(
        row="J2j",
        asserts="a failure before submission leaves the intent on the chain and no record",
        sabotage=Sabotage(
            module=_CORPUS,
            before=(
                "        intent_digest = scope.port.append_intent(\n"
                '            _encode_operation_intent("corpus-write", token, scope.authority.actor)\n'
                "        )\n"
            ),
            after='        intent_digest = "0" * 64\n',
        ),
        checks=(_J2,),
    ),
    # --- J3: the act-time refusal is the kernel's, under the requirement -------
    Arm(
        row="J3a",
        asserts="the scoped writer's effective permit is its requirement, never the session ceiling",
        sabotage=Sabotage(
            module=_WRITER,
            before="        writer = self._writer_factory(scoped_authority(required, self.actor))\n",
            after="        writer = self._writer_factory(Authority(self._ceiling, self.actor))\n",
        ),
        checks=(_J3,),
    ),
    Arm(
        row="J3b",
        asserts="`scoped` refuses an uncovered requirement before any writer exists",
        sabotage=Sabotage(
            module=_WRITER,
            before="        if not permit_covers(self._ceiling, required):\n",
            after="        if False:\n",
        ),
        checks=(f"{_SW}::test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists",),
    ),
    Arm(
        row="J3c",
        asserts="the twin judges the permit before it settles: the raw lock, not the settling hold",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        with writer._state.lock, writer._fulfilling() as scope:\n",
            after="        with writer._operation, writer._fulfilling() as scope:\n",
        ),
        checks=(f"{_OPS}::test_the_twin_judges_the_permit_before_it_settles",),
    ),
    # --- J4: every intent carries the session actor ----------------------------
    Arm(
        row="J4",
        asserts="the operation intent carries the bound authority's actor, which is the session's",
        sabotage=Sabotage(
            module=_CORPUS,
            before='            _encode_operation_intent("corpus-write", token, scope.authority.actor)\n',
            after='            _encode_operation_intent("corpus-write", token, "library")\n',
        ),
        checks=(_J4,),
    ),
    # --- J5: the act line, under the lock the commit held ----------------------
    Arm(
        row="J5a",
        asserts="every committed operation is ledgered as one `act` line",
        sabotage=Sabotage(
            module=_WRITER,
            before="            self._session._record_act(self._invocation, commit)\n",
            after="            pass\n",
        ),
        checks=(_J5, _J2L),
    ),
    Arm(
        row="J5b",
        asserts="the `act` line is appended while the thread still holds the lock the commit held",
        sabotage=Sabotage(
            module=_WRITER,
            before=(
                "            commit = perform()\n"
                "            self._session._record_act(self._invocation, commit)\n"
                "            return commit.record\n"
            ),
            after=(
                "            commit = perform()\n"
                "        self._session._record_act(self._invocation, commit)\n"
                "        return commit.record\n"
            ),
        ),
        checks=(_J5,),
    ),
    Arm(
        row="J5c",
        asserts="the session lock spans the act, so no claim interleaves between the commit and its line",
        sabotage=Sabotage(
            module=_WRITER,
            before="        with self._session._lock, _operation_lock_for(self._writer.root):\n",
            after="        with _operation_lock_for(self._writer.root):\n",
        ),
        checks=(_J5L,),
    ),
    # --- J6: the claim table ---------------------------------------------------
    Arm(
        row="J6a",
        asserts="a re-claim under a different command or digest is a mismatch",
        sabotage=Sabotage(
            module=_WRITER,
            before="            if entry.command != command or entry.input_digest != digest:\n",
            after="            if False:\n",
        ),
        checks=(_J6,),
    ),
    Arm(
        row="J6b",
        asserts="an abandoned invocation stays open and never blocks a fresh claim",
        sabotage=Sabotage(
            module=_WRITER,
            before="            entry = self._index.get(invocation)\n            if entry is None:\n",
            after=(
                "            entry = self._index.get(invocation)\n"
                "            if entry is None and self._current is not None:\n"
                '                raise SessionProtocolError(f"{self._current} is still open")\n'
                "            if entry is None:\n"
            ),
        ),
        checks=(_J6A,),
    ),
    Arm(
        row="J6c",
        asserts="the closed outcome replays whole, exactly as it was validated",
        sabotage=Sabotage(
            module=_WRITER,
            before="            self._index[invocation].outcome = validated\n",
            after='            self._index[invocation].outcome = {"done": []}\n',
        ),
        checks=(_J6R,),
    ),
    # --- J7: append, flush, fsync — then the index ------------------------------
    Arm(
        row="J7a",
        asserts="every append is fsynced before the call returns",
        sabotage=Sabotage(
            module=_LEDGER,
            before="            os.fsync(self._file.fileno())\n",
            after="            pass\n",
        ),
        checks=(_J7, _J2F),
    ),
    Arm(
        row="J7b",
        asserts="a failed append is terminal: the writer never appends again",
        sabotage=Sabotage(
            module=_LEDGER,
            before="            self._failed = True\n",
            after="            self._failed = False\n",
        ),
        checks=(_J7P,),
    ),
    Arm(
        row="J7c",
        asserts="the index learns a close only after the ledger holds it",
        sabotage=Sabotage(
            module=_WRITER,
            before=(
                '            self._ledger.append({"line": "invocation-close", '
                '"invocation": invocation, "outcome": validated})\n'
                "            self._index[invocation].outcome = validated\n"
                "            self._current = None\n"
            ),
            after=(
                "            self._index[invocation].outcome = validated\n"
                "            self._current = None\n"
                '            self._ledger.append({"line": "invocation-close", '
                '"invocation": invocation, "outcome": validated})\n'
            ),
        ),
        checks=(_J7L,),
    ),
    # --- J8: reconciliation — chains are truth, the ledger is evidence ---------
    Arm(
        row="J8a",
        asserts="a committed registration an act line covers is the only one reconciliation passes over",
        sabotage=Sabotage(
            module=_RECONCILE,
            before="                    if r.digest in acts:\n                        continue\n",
            after="                    if True:\n                        continue\n",
        ),
        checks=(_J8F, _J8),
    ),
    Arm(
        row="J8b",
        asserts="an uncovered registration under an open invocation is outcome-unknown, not foreign",
        sabotage=Sabotage(
            module=_RECONCILE,
            before="                    if unknown:\n",
            after="                    if False:\n",
        ),
        checks=(_J8,),
    ),
    Arm(
        row="J8c",
        asserts="an unreadable ledger is as unknown as an open invocation",
        sabotage=Sabotage(
            module=_RECONCILE,
            before="            unknown = reader is None or bool(open_invocations)\n",
            after="            unknown = bool(open_invocations)\n",
        ),
        checks=(_J8U,),
    ),
    Arm(
        row="J8d",
        asserts="the view's pending pairs outside its entries are reported, with no intent attached",
        sabotage=Sabotage(
            module=_RECONCILE,
            before="            if staged not in digests:\n",
            after="            if False:\n",
        ),
        checks=(_J8P,),
    ),
    Arm(
        row="J8e",
        asserts="reconciliation reads the chain detached: it resolves nothing and settles nothing",
        sabotage=Sabotage(
            module=_SESSION,
            before="            chains[corpus_id] = log_seam().inspect_detached(root)\n",
            after="            chains[corpus_id] = log_seam().inspect_registered(root)\n",
        ),
        checks=(_J8,),
    ),
    Arm(
        row="J8f",
        asserts="the sessions, the chains and the ledgers are read under one hold of every root's lock",
        sabotage=Sabotage(
            module=_SESSION,
            before="            stack.enter_context(_operation_lock_for(root))\n",
            after="            _operation_lock_for(root)\n",
        ),
        checks=(_J8I, _J8H),
    ),
    Arm(
        row="J8g",
        asserts="an unreadable ledger is evidence, never an exception out of the reconciliation read",
        sabotage=Sabotage(
            module=_LEDGER,
            before=(
                "    except OSError as caught:  # a directory in the file's place, a permission or "
                "device error: evidence, not an exception\n"
            ),
            after="    except FileExistsError as caught:\n",
        ),
        checks=(_J9,),
    ),
    # --- J9: the lifecycle and the refusing configurations ---------------------
    Arm(
        row="J9a",
        asserts="a session opens over exactly one corpus root",
        sabotage=Sabotage(
            module=_SESSION,
            before="    if len(world_config.corpus_roots) != 1:\n",
            after="    if False:\n",
        ),
        checks=(_J9,),
    ),
    Arm(
        row="J9b",
        asserts="a session opens over a registered, well-formed chain and refuses anything else",
        sabotage=Sabotage(
            module=_SESSION,
            before="    if type(view) is not WellFormedView:\n",
            after="    if False:\n",
        ),
        checks=(_J9,),
    ),
    # --- J10: indistinguishable on an ordinary read ----------------------------
    Arm(
        row="J10",
        asserts="a session write moves exactly the bytes the ordinary write moves, and no others",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        entry_digest = scope.port.execute_fulfilling(plan, intent_digest)\n",
            after=(
                '        plan = [*plan, CreateOp(f"act-report/n2-{token}.md", b"# n2\\n")]\n'
                "        entry_digest = scope.port.execute_fulfilling(plan, intent_digest)\n"
            ),
        ),
        checks=(_J10,),
    ),
    # --- J11: one writer, one invocation, durably ------------------------------
    Arm(
        row="J11a",
        asserts="a writer acts only under its own current invocation",
        sabotage=Sabotage(
            module=_WRITER,
            before="            if self._current != invocation:\n                raise SessionProtocolError(\n",
            after="            if self._current is None:\n                raise SessionProtocolError(\n",
        ),
        checks=(_J11,),
    ),
    Arm(
        row="J11b",
        asserts="currency is judged before the commit, so a bound writer's stale act moves nothing",
        sabotage=Sabotage(
            module=_WRITER,
            before="            self._session._require_current(self._invocation)\n",
            after="            pass\n",
        ),
        checks=(_J11,),
    ),
)
