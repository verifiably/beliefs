# Publication — the guarantee table

**Status:** banked 2026-09-22 with conformance cut 39's freeze; Y1–Y4 closed at cut 39
(2026-09-23, `../plans/2026-09-23-conformance-cut-39-results.md`); Y5–Y10 banked with
conformance cut 40's freeze (`../superpowers/specs/2026-09-23-publish-act-local-design.md` §13) and
closed at cut 40 (2026-09-24, `../plans/2026-09-24-conformance-cut-40-results.md`); the Y table's
owner (`python/tests/test_designs_corpus.py` `TABLE_OWNERS`). Y1–Y4 are the
publication-records slice's (`../superpowers/specs/2026-09-22-publication-records-design.md`
§10), Y5–Y10 the local publish act's (`../superpowers/specs/2026-09-23-publish-act-local-design.md`
§13); the remote slice, cut 41, appends its own rows here.

The act is specified by the user and autonomy layer design §6.1
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`); the
records, the intent and the intent-position judgment by the slice spec above.
W17's intent-position arm stays in the world-addressing table and is read by
the same cut.

| row | guarantee |
|---|---|
| **Y1** | version 2 declares `publication` and `publication-binding`; a version-1 pin authorizes neither; every ordinary door (`add`, `import_bundle`, `mint_coordination`, `revise_coordination`) refuses both; neither enters a world-index map or moves a `belief_input_digest` |
| **Y2** | both records are byte-functions of the intent and the named arguments; `marker_consistent` refuses a marker whose uid, address or id disagrees with its own `event_token`, view and destination |
| **Y3** | the publish intent decodes by its domain and qualifies only by a `publish` report with its token; a malformed payload under the domain, and a bare domainless `publish` triple, are audit findings; every other kind's intent is byte-unchanged |
| **Y4** | step 8 is all-or-nothing: a binding revision never exists without its success report, a refusal writes its report alone, and every `PositionRefused` reason refuses with no binding; a remotely revealed attempt refused for any reason is an orphan in the next intent's `marker_tips`, retired once a shared publish carrying it closes |
| **Y5** | every step-0 refusal — `view-revised`, `selection-incomplete`, `empty-selection`, `closure-incomplete` (a composite's missing member included), `pins-disagree`, `coordination-unpinned`, `destination-unusable`, `operations-root-unusable`, and `evaluate_query`'s own — writes nothing: no intent, no file under the operations root |
| **Y6** | a retry never selects differently: population reads only the snapshot the request's digest names, written create-only before the request; a corpus that drifts after step 0 does not strand the retry; a request or snapshot that disagrees with its intent is `request-corrupt`, reported, terminal |
| **Y7** | staging resumes only from a true prefix; a hole, an extra, a byte mismatch or an unequal marker is `staging-corrupt`, reported, terminal; population is complete iff the marker is byte-equal to the factory's |
| **Y8** | the local reveal is `restore_root`'s grant on `<destination>/<corpus_id>` against the create-only sibling; a colliding sibling or a non-`validated` verdict is reported and binds nothing; a second publication to the same destination lands beside the first |
| **Y9** | a crash after any local step resumes exactly to one binding and one report; done iff this attempt's binding exists and the intent is `closed`; `indeterminate` and binding-without-report fail closed with nothing written; the terminal report carries the lifecycle entries in step order, and the next publish's step-0 fold reads every such report, successful or refused |
| **Y10** | a published corpus is admitted in a second world only through `admit_publication`, which refuses before any write a root with no marker, two markers, a malformed or inconsistent marker, a binding, or records other than the marker's selection |
