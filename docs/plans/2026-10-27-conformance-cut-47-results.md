# Conformance cut 47 — results

**Cut:** `../designs/2026-10-27-conformance-cut-47.md`.
**Freeze:** `d7d10a050c9975513fddd528f6a785d6f9981c78`; SHA-256 `8155c24eab0900c221f82a81928bc9d9a069ccee0a26f712e4f5fca19fc87c7f`.
**Declaration:** `python/tests/n2_arms_cut47.py`, committed at `feaf73b`; SHA-256 `8639a5df6bdb4b619f2c2e518125d2d6267a8389d6475a41c5ee9a0547566c8b`.
**Design:** `../superpowers/specs/2026-10-27-owned-replica-publication-design.md`, accepted at `deb8d99`.
**Plan:** `../superpowers/plans/2026-10-27-owned-replica-publication.md`, accepted at `69577b6`.
**Implementation and proof:** through `feaf73b`; status/accounting updates follow the successful run below.
**Task:** beliefs-7c612b. The task holds the full implementation review and its disposition; this record and all final status edits enter that review together.

## 1. What ran

The execution baseline `just test` passed 6,230 non-N2 Python tests, 46 standalone N2 tests and 155 TypeScript tests, with one Python skip. Durable tests ran on the certified kernel `7.2.2-arch1-1` and ext4 volume mounted `rw,noatime,data=ordered`; no capability refusal was waived.

Before the extended chain, the mechanical/Y17-s pilot passed seven checks, and writer-only local-v3 plus remote mark-only recovery passed two durable cases in 7.01 seconds. The complete new guard passed nine checks in 20.01 seconds: every named baseline resolved and all nine mutations were sound. The full cut-46 guard passed thirteen checks in 16.32 seconds, including all 36 sound mutations and the three retargets below. The recent-runner interface check passed one case, proving command/environment/cleanup/accounting shape without substituting for the real run.

The first full successor at `feaf73b` stopped after 31.547 seconds with exit 1 in its first phase: cut 6 had 22 passes and two baseline failures, both naming `test_git_is_not_an_identity_member`. N2's child environment retained the real home, exposing scratch Git commits to host global hooks. Isolating HOME/XDG configuration and disabling global/system Git configuration removed those failures. A standalone probe initially omitted the chain's certified-root variables and failed four historical durability baselines; with the same certified roots, all 24 cut-6 checks passed in 11.13 seconds. Neither probe weakened an assertion or changed a frozen pin. The failed original log is retained separately and is not discharge evidence. Harness isolation is tracked separately as beliefs-23f259; this cut changes no historical harness behavior.

The successor restarted at the same implementation revision after those observations. `TASK_TEST_HOME` names the empty task-owned test home under persistent task storage; uv resolves the installed frozen environment before HOME changes:

```sh
just --set one_cmd 'cd python && uv run --frozen env HOME="$TASK_TEST_HOME" XDG_CONFIG_HOME="$TASK_TEST_HOME/.config" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 python tools/cut47_acceptance.py' test-one -q
```

The recipe supplies `host-budget run`. Cut 47 chains only `cut46_acceptance.py`, preserving constant prefix depth, then runs `test_owned_replica_publication_acceptance.py` and `test_n2_cut47.py`. The runner uses main `.work/acceptance/cut47` on the certified volume and removes its per-run roots.

The invocation began at `2026-10-27T17:37:57.220460+00:00`, exited **0** at `2026-10-27T18:14:09.100115+00:00`, and took **2171.879 seconds**. All **78 pytest phases and 1,198 passing invocations** passed with no failure, error, skip or capability refusal. The 77 printed summaries report **2073.16 seconds** of pytest time and 1,189 passes; forwarded `-q` suppresses the final guard summary, whose nine passing dots and successful return establish its nine checks. That phase's time is excluded from the subtotal.

The exact log SHA-256 is `ef93d1794f7a51c4e913ba7de44cf90b6d037a97c693b0d8df70946643b15005`. The task retains the log and command/start/end/exit metadata as `cut47-runner.log` and `cut47-runner.json`; the first failed run is `cut47-runner-host-home.log` with SHA-256 `fc41584cb23a871a8b239f0ee83c54d0815c53f57765c55c0062b333e80171ed`.

## 2. Accounting

**9 arms, 9 declaration units, two exercised rows.** Y5 and Y17 amendments reclose; no guarantee row is newly closed. `owned-replica-publication` is discharged. `ACCOUNTING[47]` names this section and both complete rows; their freeze-time REOPENED entries are removed. The live total returns from 224 at freeze to **226 of 253 rows closed, 27 open**.

The recent-runner inventory carries `(cut47, 47, (9, 9, 2))` and checks the exact output:

```text
guarantee rows exercised: 2 (0 newly closed; Y5 and Y17 amendments reclosed)
```

| unit | check suffix | result |
|---|---|---|
| Y5-f | declaration_validation | resolved / sound |
| Y17-q | owned_replica | resolved / sound |
| Y17-r | explicit_scope | resolved / sound |
| Y17-s | captured_marker_veto | resolved / sound |
| Y17-t | refusal_order | resolved / sound |
| Y17-u | mixed_origins | resolved / sound |
| Y17-v | preview_matches_freeze | resolved / sound |
| Y17-w | scoped_ownership | resolved / sound |
| Y17-x | frozen_owned_marker | resolved / sound |

The full node IDs and exact sabotage text are frozen in the canonical declaration. Each unit has one independently named check; there are no co-citations.

## 3. Behavior, review points and evidence limits

The durable fixture extracts cut 46's existing replicate/export/restore/admit_arrival setup, then adds a separate Fresh-admitted write root. Real v2/v3 preview and publication preserve the source corpus identity and every admission/digest. Fifteen durable cases cover plain and scoped publication, unchanged intent/operations state on refusal, and frozen local/remote recovery. The existing attribution acceptance module still passes all fourteen cases.

P1 is absorbed through that shared fixture. P2's Y17-x sabotage changes `_expected_marker` from `attributions=a.snapshot.attributions` to:

```python
attributions=a.snapshot.attributions or ((a.snapshot.records[0][0], a.request.world_id, a.opened.intent.event_token),),
```

`test_y17_x_frozen_owned_marker` kills this invented origin through local reconstruction and remote reconstruction while the snapshot is present, for both v2 and v3. Remote mark-only recovery does not call `_expected_marker` and is additional durable evidence, not this mutation's killer.

P3's marker-present before-intent ordering is established by preparation's position before intent and by `test_ownership_refusals_before_intent` plus the durable refusal case. It has no dedicated mutation arm. Y17-v proves forwarding into the same preparation/frozen result; extending Y5 does not claim mutation proof of the new refusal's ordering.

Cut-46 canonical declarations and frozen bodies remain unchanged. Only live anchors Y17-a, Y17-g and Y17-i are retargeted around the new replica filter and attribution-call argument; their semantics and named assertions are retained. All 36 legacy mutations pass. Cut 40's live Y6-a anchor remains valid without changes. The plan's nonexistent `each_arm_targets` filter initially selected no tests; the actual `names_one_real_source_site` guard and later full guards supplied the required evidence.

Recovery never reclassifies ownership or reads origin sources to populate the marker. Existing coordination intent-position evidence still freezes its mount anchors, however. Successful source-deleted local v2/v3 and remote mark-only cases use a writer-only coordination resolver from the beginning while their world contains replica plus Fresh writer. Separate v2/v3 negative cases initially anchor the source, drop that mount at retry, and retain the existing `evidence-refused` / `mounts-changed` result with no binding. The initial idea that a fresh resolver alone permitted that retry was rejected by these tests. No recovery code or mount policy changed.

The captured-marker guard scans the whole captured holder tuple, even a marker absent from the world's index and selected records. Admission validation precedes that scan for every selected holder. Undeclared replicas keep existing release/pin refusals and exact forwarded origins. Ownership remains an explicit publisher claim, not authenticated authorship or a registry-provenance mutation.

## 4. Verification and review

Portable preparation/legacy attribution/scoped tests passed 144 cases after Task 2; scoped forwarding passed 24 after Task 3. Permit and composition boundaries passed 577 checks. The final pre-run fast gate passed **6,278 Python tests, one skip**, in 130.13 seconds; no affected TypeScript tests were selected. The baseline supplied the TypeScript coverage above. Precommit checks passed with zero pyright errors or warnings. The new runner's initial RED was a missing-module collection failure, not a behavioral mutation kill; all claimed kills are from subsequent passing baselines and sound audits.

After discharge edits, documentation/guide/recent-runner checks passed **45 cases in 1.33 seconds**. The required fast check passed **6,278 Python tests, one skip, in 82.16 seconds**, with no affected TypeScript tests selected. `just check`, `tasks check` and `git diff --check` passed. Live roadmap output reports **226 of 253 closed, 27 open**. Only the cut document's status line changed after its freeze; §§2–7 and canonical declarations remain pinned.

Implementation review is recorded on beliefs-7c612b before findings are acted on. The task's execution ledger retains every ruling, including fixture reuse, the recovery-anchor limit, evidence boundaries, navigation updates and isolated Git-test environment. No final evidence/status edit is exempt from the whole-branch review.

## 5. Remaining boundary

None for `owned-replica-publication`: Y5 and Y17 reclose at this amendment. L1 remains partial under `persistence-cut`, and T7 remains partial under `cross-root-publication`; the other ledger boundaries remain open and are not re-ranked here.

Science consumer wiring remains sci-9a7ce2: both preview and publish must supply `acceptance_inputs(ctx).own_roots`, with intended duplicate-carrier and single-write-mount preview refusals tested. sci-775e90 depends on that wiring and this kernel task and owns the live milestone rerun with an explicit assessment-query anchor. This cut changes no live mounts, installation configuration, science code, contract pin, registry admission or retry format. Kernel conformance does not claim the live milestone is fixed.
