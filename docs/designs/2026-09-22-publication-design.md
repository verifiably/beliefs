# Publication — the guarantee table

**Status:** banked 2026-09-22 with conformance cut 39's freeze; the Y table's
owner (`python/tests/test_designs_corpus.py` `TABLE_OWNERS`). Y1–Y4 are the
publication-records slice's (`../superpowers/specs/2026-09-22-publication-records-design.md`
§10); the publish act's slice appends its own rows here.

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
