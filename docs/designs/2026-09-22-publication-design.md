# Publication — the guarantee table

**Status:** banked 2026-09-22 with conformance cut 39's freeze; Y1–Y4 closed at cut 39
(2026-09-23, `../plans/2026-09-23-conformance-cut-39-results.md`); Y5–Y10 banked with
conformance cut 40's freeze (`../superpowers/specs/2026-09-23-publish-act-local-design.md` §13) and
closed at cut 40 (2026-09-24, `../plans/2026-09-24-conformance-cut-40-results.md`); the Y table's
owner (`python/tests/test_designs_corpus.py` `TABLE_OWNERS`). Y1–Y4 are the
publication-records slice's (`../superpowers/specs/2026-09-22-publication-records-design.md`
§10), Y5–Y10 the local publish act's (`../superpowers/specs/2026-09-23-publish-act-local-design.md`
§13); Y11–Y16 closed at cut 42 (2026-09-27, `../plans/2026-09-27-conformance-cut-42-results.md`), after banking at its freeze (`../superpowers/specs/2026-09-26-publish-act-remote-design.md` §10).

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
| **Y11** | a remote reveal is verified by the act, not the seam: the remote's enumeration of the publication's whole namespace must equal the local listing of every export-root file and the sibling, by name and SHA-256; a missing, extra or altered file is `transport-incomplete` (`listing-mismatch`), reported, terminal; a remote destination without a transport, or a local one with one, refuses before anything is written |
| **Y12** | the transport mark is written create-only after the export root validates and before the first `push`; once it exists a retry resumes at step 7 from the mark and never re-runs steps 1–6; a mark that fails to decode, or disagrees with its intent, the export root's manifest and chain, the sibling's identity or the export's marker, fails closed with nothing written |
| **Y13** | a transport the seam abandons, whose listing disagrees, or whose export root fails its evaluation against its own chain and sibling before `push` (a selected record missing or altered after the mark), closes the attempt with a report carrying `(corpus_id, marker)`; the fold reads it as a standing orphan that retires nothing, so the next publication's marker supersedes it and every orphan its intent named |
| **Y14** | a publish refuses `publish-unfinished` before its intent, writing nothing, while an `unfinished` attempt for the same `(view, destination)` has a transport mark; an unfinished attempt without a mark never blocks; once the blocking attempt is resumed to a close, the publish proceeds and its marker supersedes the resumed one |
| **Y15** | a crash at any remote step resumes to exactly one binding and one report whose entries run staging, export, reveal, transport, binding; a remote step-8 refusal carries `remotely_revealed: true` and is an orphan; step 9 keeps the export root, the mark, the request and the snapshot |
| **Y16** | a recipient admits a remote publication from a raw copy through `restore_root` against the transported artifact and `admit_publication`, and a copy missing any file never validates; `publication_tip` reads each held root alone, so publications sharing selected records are read side by side; it refuses a held root with a record it cannot read or decode (`capture-damaged`) and a corpus whose layout `admit_publication` would refuse, answers the one standing marker, `divergent-publication` for sibling markers, and the one tip again once a marker superseding both arrives |
