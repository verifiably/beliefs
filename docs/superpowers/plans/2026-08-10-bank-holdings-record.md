# Banking the Verified-Holdings Record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply §8's amendment set of `docs/designs/2026-08-10-verified-holdings-record-design.md` across the corpus, so the design banks and the three pre-banking corpus-suite failures resolve.

**Architecture:** Pure documentation-and-guards propagation — no runtime code. Each task edits one document cluster to match one group of §8 rows, verified by the corpus suite (`python/tests/test_designs_corpus.py`) and the guide checker (`python/tools/check_guide.py`). The suite goes fully green only at the final task, which extends the guards themselves; every earlier task must leave exactly the three known failures (README count, README table, guide citation) and no new ones.

**Tech Stack:** Markdown, pytest, `python/tools/check_guide.py`.

## Global Constraints

- The spec is `docs/designs/2026-08-10-verified-holdings-record-design.md` **§8** ("What this changes elsewhere"). Every §8 row must be traceable to exactly one task below; the "Not amended, deliberately" list (G9, R5, R10, cut 2's frozen selection) means those sites are **not** touched.
- Work on branch `holdings-record` in the worktree `.worktrees/holdings-record`. **Do not push.**
- Conventional commits. **No AI-attribution trailer or footer** on any commit.
- No absolute user paths (`/home/...`, `/mnt/...`) in any doc or comment.
- Banked designs are amended **in place with dated notes** citing this design — the corpus precedent is the italic `*(restated 2026-08-09 …)*` style (see the formal model's dataset row for the shape). The cut-2 document is **frozen: Status append only** — one sentence, nothing else in that file changes.
- **Historical statements stay untouched.** The world address ruling's "an eleventh kernel kind", "taking the kernel to eleven kinds" (its lines ~7, ~19, ~233, ~272, ~550, ~622) record what that ruling did and are correct. Ramp/cut-2 statements of "139 rows across eleven tables" record what was true at their writing and are equally untouched. Only the sites enumerated in a task change.
- Guarantee ids are never renamed or renumbered. The new table is `H`, rows `H1`–`H4`, owner `2026-08-10-verified-holdings-record-design.md`.
- Verification commands (run from `python/`, always in the frozen `uv` environment — never ambient `python`): `uv run --frozen pytest tests/test_designs_corpus.py -q` and `uv run --frozen python tools/check_guide.py; echo "exit=$?"` (exit 0 = pass; it prints nothing on success). Also `git diff --check` from the repo root before every commit. The final task closes with the full gates from `python/README.md`: `uv run --frozen pytest -q`, `uv run --frozen ruff check .`, `uv run --frozen pyright src`.
- Line numbers below are approximate anchors — locate each edit by the quoted text, not the number.

---

### Task 1: Kernel kind count → twelve across the exact inventory

§8 row: *"epistemic kernel, kind inventory"* — the count sites are amended as an **exact inventory, not a sweep**. This task covers every non-guide count site (the two guide sites are Task 7's), plus the kernel's one live **table**-count pointer: §10's "Where they stand" note, which counts the unnumbered table-bearing designs and must gain the holdings record (H).

**Files:**
- Modify: `docs/designs/2026-08-02-epistemic-kernel-design.md` (§4.4, ~line 915)
- Modify: `docs/designs/2026-08-04-domain-extension-boundary-design.md` (~lines 34, 271)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (docket note, ~line 59)
- Modify: `docs/designs/2026-08-09-admission-ramp-design.md` (§2.2, ~line 146)
- Modify: `docs/designs/2026-08-08-world-address-ruling.md` (§3, ~line 122)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: the twelve-kind claim later tasks may cite. Task 3 renames the formal-model §2.1 heading; Task 7 fixes the guide's anchor link to it.

- [ ] **Step 1: Kernel §4.4.** In the accounting table's first row, change the destination cell header

  `**Kernel (8; 10 since 2026-08-03; 11 since 2026-08-08)**`

  to

  `**Kernel (8; 10 since 2026-08-03; 11 since 2026-08-08; 12 since 2026-08-10)**`

  and in the same cell's kinds list, after "`coreference-attestation` (world address ruling §5.1)", extend the parenthetical list so it ends:

  `… and `coreference-attestation` (world address ruling §5.1), then `holdings-observation` (verified-holdings record design §2, 2026-08-10), which absorb nothing`

  (i.e. the existing "which absorb nothing" clause now covers four appended kinds; keep it as the closing words).

- [ ] **Step 2: Domain extension, two clauses.** At ~line 34, change

  `(the eleven kernel kinds — ten until 2026-08-08)`

  to

  `(the twelve kernel kinds — ten until 2026-08-08, eleven until 2026-08-10)`

  At ~line 271, change

  ``` `science` owns the eleven kernel kinds (kernel §4.2; ten until 2026-08-08), ```

  to

  ``` `science` owns the twelve kernel kinds (kernel §4.2; ten until 2026-08-08, eleven until 2026-08-10), ```

- [ ] **Step 3: Adoption-ledger docket note.** At ~line 59, change

  `the kernel is **eleven kinds**, not ten —`

  to

  `the kernel is **eleven kinds**, not ten (twelve since 2026-08-10 — `holdings-observation`, the verified-holdings record design §2) —`

  This preserves the note's record of what the world ruling itself did while carrying the current count.

- [ ] **Step 4: Ramp §2.2.** At ~line 146, change

  `(`2026-08-08-world-address-ruling.md` §3) binds all eleven kinds: every`

  to

  `(`2026-08-08-world-address-ruling.md` §3) binds all twelve kinds (eleven until 2026-08-10): every`

- [ ] **Step 5: World ruling §3.** At ~line 122, change

  `Two clauses carry over unchanged from §4.2 and now bind all eleven kinds: the`

  to

  `Two clauses carry over unchanged from §4.2 and now bind all twelve kinds (eleven at this ruling; `holdings-observation` joined 2026-08-10): the`

- [ ] **Step 6: Kernel §10 table pointer.** In §10's `> **Where they stand**` note (~line 1345), three phrase edits in one sentence pair:

  `**Five later designs have no number in this list at all**` → `**Six later designs have no number in this list at all**`

  `the formal model and claim calculus (M), and the belief policy (P).` → `the formal model and claim calculus (M), the belief policy (P), and the verified-holdings record (H) *(amended 2026-08-10, the verified-holdings record design §8)*.`

  `Six numbered sub-problems plus those five is where the eleven frozen tables come from;` → `Six numbered sub-problems plus those six is where the twelve frozen tables come from;`

  Re-wrap the paragraph to the file's hard-wrap width after editing.

- [ ] **Step 7: Verify.** From `python/`: `uv run --frozen pytest tests/test_designs_corpus.py -q` → exactly the three known failures, no new ones. `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0. From repo root: `git diff --check` → clean.

- [ ] **Step 8: Commit.**

```bash
git add docs/designs/2026-08-02-epistemic-kernel-design.md docs/designs/2026-08-04-domain-extension-boundary-design.md docs/designs/2026-08-03-redesign-adoption-ledger.md docs/designs/2026-08-09-admission-ramp-design.md docs/designs/2026-08-08-world-address-ruling.md
git commit -m "docs(designs): take the kernel to twelve kinds and twelve tables across the exact inventory"
```

---

### Task 2: The tamper-evident log amendment

§8 row: *"tamper-evident log design | one amendment, applied across every site it names."* Read that row **in full** in the holdings design before starting — it is the specification; this task locates each site and states the insertion. Every insertion carries a dated citation of the form `*(amended 2026-08-10, the verified-holdings record design §8)*` — one per edited block, placed where the corpus's existing dated notes sit (end of the amended sentence or cell).

**Files:**
- Modify: `docs/designs/2026-08-03-tamper-evident-log-design.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the store-subject anchor carriers and L-row arms that Task 4's ledger text and the holdings design already cite.

- [ ] **Step 1: §3 root inventory + genesis union.** Anchor: `One chain per engine root: every corpus, and the world root itself` (~line 112). Extend that sentence to name the managed payload-store root (per the §8 row: the store root is a third chain-bearing root kind). Anchor: `**Genesis** is minted at root registration, as a discriminated union:` (~line 134). Add the third arm to the union — `store(store_id, forked_from?)` — minted at store initialization, preserved verbatim by replica and restore, a configuration/genesis mismatch refusing exactly as `world(world_id)` does, `forked_from` present iff a writable copy was minted by the fork act (holdings §2: replicas are read-only carriers; a writable fork is a new genesis, the corpus-fork precedent).

- [ ] **Step 2: Registered surface.** Anchor: `**The registered surface is one projection, used three times.**` (~line 157). Append the store instantiation: for a managed payload store the projection is every path in the store's payload namespace, excluding engine bookkeeping (the reserved log path and the engine's metadata) — never "the paths acts happen to mutate"; a raw-created payload file is inside the surface and replay refutes it, exactly as for a raw-created record.

- [ ] **Step 3: Intent union.** Anchor: `consumer named today is the **assessment-run intent**` (~line 205). Extend: the union gains the **holdings intent**, appended by every store-dereferencing act — mutating or re-check — before it acts (holdings §3); payload: canonical location, act kind, boundary-minted `event_token` (reused, never a second attempt id), actor.

- [ ] **Step 4: §5 anchor carriers.** Anchor: the registry log-head record clause `(**corpus subjects only**, a `world` subject on a registry record is never an anchor, §5/L11)` — appears in §6 step 2 (~line 354) and wherever §5 defines the registry carrier (~lines 272–332; grep `registry log-head`). The registry record's subject union gains `store(store_id)` beside `corpus(corpus_id)` — no self-anchoring arises, the registry lives in the world root and a store root is not it, the L11 concern stays confined to the `world` subject. The explicit anchor act names stores as it names corpora. **Epoch head members stay `corpus | world`** — state this where epoch members are defined, so a store subject in an epoch stays unconstructible.

- [ ] **Step 5: §6 verifier clauses.** Anchor: `the act names which corpus or world it verifies` (~line 349) → gains the store subject (corpus, world, or store). Anchor: the carrier-eligibility clause `a registry log-head record (**corpus subjects only**, …)` (~line 354) → becomes corpus-or-store subjects, the `world`-subject refusal standing untouched.

- [ ] **Step 6: §6 qualification + fulfills.** Anchor: the qualification reduction (§6; grep `fulfills`). State: a qualifying fulfillment of a holdings intent is a committed registration publishing a holdings observation for the intent's location carrying its `event_token`, under the same reduction — a non-qualifying pointer never matches, an unresolved one proves nothing. And the `fulfills` construction rule restated: the boundary constructs the link from its own holdings intent; no caller-supplied path.

- [ ] **Step 7: L4 store arm.** Anchor: the L4 row (~line 508). Append the arm: delete or replace a store's chain while its store-subject registry record is in the observer set → **refuted**, the subject binding associating the anchor by `store_id`, never by elimination.

- [ ] **Step 8: L7 both intent kinds.** Anchor: the L7 row (~line 513). Its guarantee now quantifies over both intent kinds, arms instantiated for the holdings shape: a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between intent append and mutation reads attempt-without-recorded-outcome.

- [ ] **Step 9: L10 store instantiation.** Anchor: the L10 row (~line 516). Append the arms exactly as the holdings design's §8 row states them (copy the arm list from the holdings design — it is normative): replica act → same genesis, chain unchanged; a claim-only destination directory may be exposed first as reserved, surface- and snapshot-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp; kill inside that window → metadata-less hence read-only, never a writable twin; cooperative mutation on any existing root not granted writability → refused, with recorded root creation the sole pre-grant write exception and the fork act the only writable exit; fork act → the new `store(store_id, forked_from)` genesis durable before the writability grant; kill between them → still a read-only replica; copy any store tree without its engine metadata and cold-bootstrap it → read-only and unresolvable for holdings reads; restore two metadata-less copies of one `store_id` on two hosts → both read-only, a write refused, fork the sole writable exit; an interrupted copy (genesis + chain, payload missing) → restore verification never `validated`, verdict preserved, root unserviceable, no `absent` minted; a restore with an empty store-anchored observer set → unresolvable, replay not reached (L9's bound); assembled branches → sibling-malformed (L3); both divergent heads co-anchored → refuted (L9); verified separately after a common anchored head → each validates, the tails L5's residue — the pinned surviving-observer negative.

- [ ] **Step 10: §9 ownership split.** Anchor: `## 9. The `atoms` seam — obligations by repo` (~line 459). In the **science-side** obligations, append: the boundary writes holdings intents and constructs their `fulfills`, on the `atoms` intent API as built. Add the note: the **log's** `atoms` machinery changes nothing, though `atoms` is not wholly unchanged — holdings §3's read command, mutating-command post-state capture, §2's replica/restore/fork commands with the fail-closed writer state, and the payload-store root kind are separate, named adoption obligations (holdings §7 item 7; adoption ledger artifact 4).

- [ ] **Step 11: Verify + commit.** Same checks as Task 1 Step 6 (three known failures only; guide checker exit 0; `git diff --check` clean).

```bash
git add docs/designs/2026-08-03-tamper-evident-log-design.md
git commit -m "docs(designs): apply the holdings amendment across the tamper-evident log"
```

---

### Task 3: World addressing §4.2 row + formal model

§8 rows: *"world addressing §4.2, the identity-basis table"*, *"formal model §2.1"*, *"formal model, tables"*.

**Files:**
- Modify: `docs/designs/2026-08-02-world-addressing-design.md` (§4.2 identity-basis table; last row is `coreference-attestation`, ~line 333)
- Modify: `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` (§2.1 heading ~line 138, lead ~line 140, player table ~lines 146–158; §5.1 count block ~line 867; §5.2 after the **D** block ~line 1035)

**Interfaces:**
- Consumes: nothing.
- Produces: the renamed §2.1 heading anchor `#21-rec--world-records-the-twelve-kernel-kinds`, which Task 7's foundations link must match exactly (derive the anchor from the final heading text — lowercase, punctuation dropped, spaces to hyphens).

- [ ] **Step 1: Identity-basis row.** In world addressing §4.2's table, append after the `coreference-attestation` row:

  `| `holdings-observation` | content identity of the §2 canonical facet under **`science.holdings-observation.v1`** — every field participating, the minted **event token** among them on the `retraction` shape's precedent, `supersedes` hashing as its deduplicated sequence sorted by canonical reference bytes — added 2026-08-10, verified-holdings record design §2 | the `coreference-attestation` precedent: the event token keeps two genuinely distinct observation *events* distinct however the clock reads; the sorted `supersedes` encoding gives one predecessor set one identity, since `science.identity.v1` refuses sets |`

- [ ] **Step 2: Formal model §2.1 heading and lead.** Change the heading

  `### 2.1 `Rec` — world records (the eleven kernel kinds)`

  to

  `### 2.1 `Rec` — world records (the twelve kernel kinds)`

  and the lead sentence `All eleven` → `All twelve` (same sentence, ~line 140). Add a dated note at the end of the lead paragraph: `*(Extended 2026-08-10: `holdings-observation` joined — the verified-holdings record design §2, §8.)*`

- [ ] **Step 3: Formal model player row.** Append to the §2.1 table, after the `coreference-attestation` row:

  `| `holdings-observation` | minted by an act — a pure dereference or a managed mutation recording its captured post-state (holdings design §3) — under whatever orchestration (acquisition, audit, a move, deletion) runs it; added 2026-08-10 | content identity over the §2 facet under `science.holdings-observation.v1` — location, outcome, `expected`, observer, instrument, minted **event token**, `observed_at`, `supersedes` as a deduplicated sorted reference sequence | append-only; revised by **supersession only** — a later record names its predecessors; never expired by age | reads the bytes it dereferenced; produces the active/blocked sets and coverage projection the dataset admission state derives from | admission (heldness under a declared coverage) → belief transitively | `observed_at` (recorded, never read by a derivation); location of the *record*; everything in belief | holdings design §2–§5; **H1–H4** |`

- [ ] **Step 4: Formal model §5.1 count.** After the existing corrected-count note (`*(Corrected 2026-08-09. …)*`, ~line 868), append a sibling note:

  `*(Extended 2026-08-10: the verified-holdings record design banked **H (4)** — the classified inventory is now **121 rows** across ten tables. The assertion count moves with H's arms; the classification is per assertion, as ever.)*`

  Count H's assertions from the rows in Step 5 (H1: 3, H2: 6, H3: 3, H4: 3 → 15; 135 + 15 = 150) and state `150 assertions` in the note **after verifying** the 135 baseline still holds in the text.

- [ ] **Step 5: Formal model §5.2 H block.** After the **D — domain extension boundary** block (~line 1035), append (classes use §5.1's taxonomy; `†` marks §5.4's proposed labels, as the existing blocks do):

  ```markdown
  **H — verified holdings record** *(added 2026-08-10, the verified-holdings record design §6)*

  | id | assertions | classes |
  |---|---|---|
  | H1 | a holdings observation is minted only by an act that dereferenced and **established** its outcome — back-filling `found` from a directory listing or a source stream's digest is unmintable / a hash outside the consistent-read boundary established no stable state, and raw concurrent mutation stays the out-of-band bound / `absent` is established by a post-delete look that answered, never inferred from a return code | RF† / RF† + **DL** / **FC** |
  | H2 | active-ness is walked per location over a checked DAG, never ordered by `observed_at` / disagreeing heads block the location rather than any outcome winning / acyclicity is validated on every walk / an unmatched or qualification-unresolved mutating intent leaves its location unsettled, blocking as itself / every agreeing head stays active under coalescence / an algorithm-mixed `found` pair blocks as `incommensurable`, forced into neither box | **OInv** / **FC** / **WF** / **WD** + **FC** / **CS** / **FC** |
  | H3 | "whatever is checked out" is not a coverage — enumeration is by declared stable identity / a receipt the bound rule over the named inputs does not reproduce is `refuted`, an absent input `unresolvable`, a receipt naming corpora-not-states `malformed` / the log chain heads are coherently captured, committed inputs, never read ambiently | RF† / **WD** + **FC** / **WD** |
  | H4 | an act records every outcome it established or **fails** — never a transient report and a dropped record / an inconclusive attempt reports through its own channel and never mints `absent` / a mutating act runs inside its intent–fulfillment ordering or fails | **FC** / RF† / EO† |
  ```

  Each row follows the G9 precedent — one row, `/`-separated assertion arms, one class group per arm. Before committing, cross-check each row's arm count against the H table's sabotage arms in the holdings design §6 (H1: 3, H2: 6, H3: 3, H4: 3) and against the class groups; H2's six arms are compressed into six clauses above.

- [ ] **Step 6: Verify + commit.** Same checks (three known failures only; guide checker exit 0; diff-check clean). The suite's `test_every_guarantee_range_names_rows_that_exist` will now see `H1`–`H4` mentions — confirm no new failure appears.

```bash
git add docs/designs/2026-08-02-world-addressing-design.md docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md
git commit -m "docs(designs): add holdings-observation to world addressing and the formal model"
```

---

### Task 4: Adoption ledger + normative contract

§8 rows: *"adoption ledger, artifact 4"*, *"adoption ledger, artifact 7"*, *"normative contract §4"*.

**Files:**
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (artifact 4 row ~line 48; artifact 7 row ~line 51)
- Modify: `docs/designs/2026-08-03-normative-contract-design.md` (§4's exact inventory — grep `P1–P9` or `G1, G2a` in that file; also the §11 "first cut" note at ~line 698 if it quotes the live count — it says "eleven tables and 139 rows as of 2026-08-09")

**Interfaces:**
- Consumes: Task 2's tamper-log wording (the ledger text cites the same commands).
- Produces: nothing later tasks read.

- [ ] **Step 1: Artifact 4 row.** In the artifact 4 (`atoms` A7–A8) row's state cell, append (adapting the holdings design's own artifact-4 §8 row text, which is normative):

  `**Holdings prerequisite (2026-08-10, verified-holdings record design §3, §7 item 7), under authority §12.2's Plan B:** the coordinator read command (dereference-and-hash under the private lease); post-state capture on the mutating commands — the post-write hash, the post-delete absence check, and `MoveNoClobber`'s dual-location result (source absence plus destination hash from the one effect), each returned before the lease releases, the two-intent move orchestration over that result staying the science boundary's; the replica, restore, and fork commands under the fail-closed writer state — writability granted only by initialization and the fork, a metadata-less store root cold-bootstrapping read-only and unresolvable for holdings reads, the restore command admitting a copy to read-only service only on a `validated` verdict from the log's verification act over the store subject and an explicit observer set of eligible store anchors, never granting writability; and the root-model amendment — §12.2 keys science's engine root on a corpus root, and the managed payload store arrives as a second root kind, an `atoms` project root whose genesis carries the store identity. A5b's boundary is preserved throughout: the coordinator acts on the consumer's behalf, and no consumer ever receives a `Lease`.`

- [ ] **Step 2: Artifact 7 row.** In the oracle-inventory cell that runs `… L1–L13; D1–D10; M1–M13; P1–P9 (…)`, extend the enumeration with `; **H1–H4** (added 2026-08-10, the verified-holdings record design §6 — the H table joins the suite on the same rule that added N, L and D)`.

- [ ] **Step 3: Normative contract §4.** Locate §4's exact table inventory (the enumeration the artifact-7 row mirrors). Extend it to include `H1–H4` with the same dated citation, taking its stated totals to **twelve tables and 143 rows**. Then update the §11 "first cut" note's live-count sentence: `eleven tables and 139 rows as of 2026-08-09, D, M and P having arrived since` → `twelve tables and 143 rows as of 2026-08-10, D, M, P and H having arrived since` (keep the rest of the sentence).

- [ ] **Step 4: Verify + commit.** Same checks (three known failures only).

```bash
git add docs/designs/2026-08-03-redesign-adoption-ledger.md docs/designs/2026-08-03-normative-contract-design.md
git commit -m "docs(designs): record the holdings prerequisite and the H table in the ledger and contract"
```

---

### Task 5: Admission ramp closure notes

§8 rows: *"admission ramp §8 item 2"*, *"admission ramp §8 item 1"*, *"admission ramp §6.7"*.

**Files:**
- Modify: `docs/designs/2026-08-09-admission-ramp-design.md` (§8 items 1–2 ~lines 955–980; §6.7 ~lines 915–924)

**Interfaces:** none.

- [ ] **Step 1: §8 item 2.** At the end of item 2 (`**Where verified holdings are recorded.** … Nothing fills the middle.`), append:

  `*Designed 2026-08-10 (`2026-08-10-verified-holdings-record-design.md`): the record is a world record in the observer's corpus, per-location, act-minted, superseded never expired, projected under a declared coverage.*`

- [ ] **Step 2: §8 item 1.** At the end of item 1 (after `…the population supplies no instance of it.`), append:

  `*Closed at the record layer 2026-08-10 — an observation stands until superseded; what remains is a possible recency-bearing **successor projection rule**, pinned in every derivation receipt with an explicit reference instant, and it is **not** a belief-policy parameter (the holdings design §4).*`

- [ ] **Step 3: §6.7 pointer.** At the end of the §6.7 paragraph (after `…no measurement can currently say which state they are in.`), append one line:

  `*The record is designed: `2026-08-10-verified-holdings-record-design.md`.*`

- [ ] **Step 4: Verify + commit.** Same checks (three known failures only).

```bash
git add docs/designs/2026-08-09-admission-ramp-design.md
git commit -m "docs(designs): close ramp §8 items 1-2 at the record layer and point §6.7 at the holdings design"
```

---

### Task 6: Cut-2 Status append

§8 row: *"conformance cut 2 | **Status append only**"*. One sentence; nothing else in the file changes.

**Files:**
- Modify: `docs/designs/2026-08-09-conformance-cut-2.md` (the `**Status.**` block, lines ~3–14)

**Interfaces:** none.

- [ ] **Step 1:** First, read cut 2's §10 item 1 and confirm it is the open question the holdings design closes ("where verified holdings are recorded" named as the most consequential open question). Then append to the end of the Status paragraph:

  `*Status append 2026-08-10: the design §10 item 1 named as the most consequential open question landed — `2026-08-10-verified-holdings-record-design.md`.*`

  If §10 item 1 is numbered or phrased differently, adjust the citation to name the actual item — the sentence must point at the right anchor, not a guessed one.

- [ ] **Step 2: Verify + commit.** Same checks; additionally `git diff docs/designs/2026-08-09-conformance-cut-2.md` must show **only** the Status addition.

```bash
git add docs/designs/2026-08-09-conformance-cut-2.md
git commit -m "docs(designs): append the cut-2 status note for the holdings design"
```

---

### Task 7: Guide propagation

§8 rows: *"guide `open-questions.md`"*, *"guide `glossary.md`"*, *"guide `foundations.md`"*, *"guide `contracts-and-adoption.md`"*. This task makes `test_the_guide_cites_every_design` pass.

**Files:**
- Modify: `docs/guide/open-questions.md` (~lines 152–190)
- Modify: `docs/guide/glossary.md` (~lines 77–86)
- Modify: `docs/guide/foundations.md` (frontmatter `sources:`; held section ~line 40; kind inventory ~lines 74–90; References ~line 155)
- Modify: `docs/guide/contracts-and-adoption.md` (~lines 85–95; Open edges ~line 147)

**Interfaces:**
- Consumes: Task 3's renamed formal-model heading anchor (foundations' References link must match it).

- [ ] **Step 1: open-questions.md — replace the holdings entry.** Replace the whole `- **Where verified holdings are recorded.** …` bullet (through `…stores nothing.` and its three link lines) with:

  ```markdown
  - **Recency and corroboration — the holdings record's residue.** The
    verified-holdings record design (2026-08-10) closed where verified
    holdings are recorded: a world record in the observer's corpus,
    per-location, act-minted, superseded never expired, projected under a
    declared coverage. What remains open is smaller: whether anything ever
    discounts an old observation — a possible recency-bearing **successor
    projection rule**, pinned in every derivation receipt with an explicit
    reference instant, and never a belief-policy parameter — and the
    partly-pinned rule's empirical corroboration, which the ramp holds as
    evidence-not-design.
    ([holdings design](../designs/2026-08-10-verified-holdings-record-design.md),
    [what stayed open](../designs/2026-08-10-verified-holdings-record-design.md#7-what-this-unblocks-and-what-stays-open))
  ```

  Before writing the second link, confirm the design's §7 heading anchor by reading its actual heading text; adjust the fragment to match.

- [ ] **Step 2: open-questions.md — the third-cut entry.** In `- **The third conformance cut.**`, change

  `run capture waits on where verified holdings are recorded, world persistence on `atoms` A7–A8 and the`

  to

  `run capture's holdings prerequisite was designed 2026-08-10 (unblocked by the holdings design), world persistence waits on `atoms` A7–A8 and the`

- [ ] **Step 3: glossary.md.** After the **Held** entry, insert (alphabetical order — `Holdings observation` follows `Held`):

  ```markdown
  - **Holdings observation** — A world record of what one act found at one
    canonical location: `found` with an algorithm-qualified digest, or
    `absent` where a completed dereference answered. Act-minted, append-only,
    revised only by supersession, never expired by age; heldness is derived
    from the active observations under a declared coverage.
    ([holdings design](../designs/2026-08-10-verified-holdings-record-design.md))
  ```

  Amend **Held**: after `Distinct from **declared**, which has the identity and not the bytes.` add `Derived from active **holdings observations** under a declared coverage since 2026-08-10.` Amend **Declared**: after `…has measured its own coverage.` add `The route out is a matching holdings observation (G9).`

- [ ] **Step 4: foundations.md.** Four edits:
  1. Frontmatter `sources:` list gains `  - ../designs/2026-08-10-verified-holdings-record-design.md`.
  2. The held section (~line 40): after `…an accession alone is not.`, append: `Since 2026-08-10, heldness is derived: an artifact is held under a declared coverage when an active **holdings observation** — a world record minted by an act that dereferenced and hashed — matches its declared digest. The record is superseded, never expired; no age or clock participates in the derivation.`
  3. The kind inventory: heading `### The eleven world-record kinds` → `### The twelve world-record kinds`; lead `The formal inventory contains eleven kernel kinds:` → `The formal inventory contains twelve kernel kinds:`; in the table's `Materials` row, change kinds to `` `dataset`, `source`, `holdings-observation` `` and extend the purpose cell with `; and record, act-by-act, what was found at each held location`.
  4. References (~line 155): update the formal-model link text and anchor: `[Formal model: the eleven kinds and M1–M13](…#21-rec--world-records-the-eleven-kernel-kinds)` → `[Formal model: the twelve kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-twelve-kernel-kinds)` — the fragment must match Task 3's final heading exactly.

- [ ] **Step 5: contracts-and-adoption.md.** Three edits:
  1. ~Line 88: change `The corpus now holds 139 rows across eleven frozen tables: the belief policy's P1–P9 banked the day the cut was drawn, and the admission ramp appended G9 on 2026-08-09 while narrowing W3's dataset arm.` to `The corpus now holds 143 rows across twelve frozen tables: the belief policy's P1–P9 banked the day the cut was drawn, the admission ramp appended G9 on 2026-08-09 while narrowing W3's dataset arm, and the verified-holdings record design banked H1–H4 on 2026-08-10.`
  2. ~Line 101–103: the cut-2 paragraph still claims the holdings location is open. Recast it historically — it was open at the freeze and was designed 2026-08-10, the cut's frozen selection unchanged. Change

     `verified-holdings observations enter as supplied arguments precisely because where they are recorded is still undesigned, no arm reads an observation's timestamp,`

     to

     `verified-holdings observations enter as supplied arguments precisely because where they are recorded had not yet been designed at the freeze (designed 2026-08-10, the verified-holdings record design; the frozen selection is unchanged), no arm reads an observation's timestamp,`

     Re-wrap to the file's hard-wrap width.
  3. Open edges (~line 147): where the section points at the open-questions page, ensure the holdings question is referenced as its **residue** (recency projection rule + corroboration), consistent with Step 1's rewritten entry — if the section lists specific open items, move the holdings line to the residue phrasing; if it only links to `open-questions.md#contracts-and-adoption`, no edit is needed beyond confirming.

- [ ] **Step 6: Verify.** From `python/`: `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0. `uv run --frozen pytest tests/test_designs_corpus.py -q` → now exactly **two** failures (the README pair); `test_the_guide_cites_every_design` passes. `git diff --check` clean.

- [ ] **Step 7: Commit.**

```bash
git add docs/guide/open-questions.md docs/guide/glossary.md docs/guide/foundations.md docs/guide/contracts-and-adoption.md
git commit -m "docs(guide): propagate the holdings record across the guide"
```

---

### Task 8: Corpus guards, README, and the Status flip

§8 rows: *"README"*, *"`python/tests/test_designs_corpus.py`"* — plus the user rule that a landed design's Status is corrected in the same change. This task takes the suite fully green.

**Files:**
- Modify: `python/tests/test_designs_corpus.py` (GUARANTEE_TABLES ~line 50; TABLE_OWNERS ~line 65; the `_ROW` regex ~line 88 and `_ROW_RANGE` regex ~line 108; the `eleven frozen tables` assertion ~line 200)
- Modify: `README.md` (count sentence ~line 20; row-total sentence ~line 59; design table ~lines 36–45)
- Modify: `docs/designs/2026-08-10-verified-holdings-record-design.md` (Status header, lines 4–7)

**Interfaces:**
- Consumes: everything — this is the gate that proves the other seven tasks landed.

- [ ] **Step 1: Extend the guards (the failing test comes first).** In `GUARANTEE_TABLES`, after the `"P"` entry add:

  ```python
  "H": ("H1", "H2", "H3", "H4"),
  ```

  In `TABLE_OWNERS`, after the `"P"` entry add:

  ```python
  "H": "2026-08-10-verified-holdings-record-design.md",
  ```

  Update the dict's leading comment `The eleven frozen guarantee tables` → `The twelve frozen guarantee tables`.

  **Extend the row parsers — without this the H rows are invisible to the suite.** Both regex character classes exclude `H`: `_ROW` (~line 88) is how the completeness test finds a table's rows in its owner document, and `_ROW_RANGE` (~line 108) is how span labels like `H1–H4` get validated against rows that exist. Change `[GSWRCXNLDMP]` → `[GSWRCXNLDMPH]` in **both**:

  ```python
  _ROW = re.compile(r"^\|\s*\*{0,2}([GSWRCXNLDMPH][0-9]+[a-z]?)\*{0,2}\s*\|", re.MULTILINE)
  ```

  ```python
  _ROW_RANGE = re.compile(r"\b([GSWRCXNLDMPH])([0-9]+[a-z]?)–\1?([0-9]+[a-z]?)\b")
  ```

  Then make the table-count assertion machinery-driven instead of a second hardcoded word: replace

  ```python
  assert "eleven frozen tables" in readme, f"the README does not state that the rows sit in {tables} tables"
  ```

  with

  ```python
  table_words = {11: "eleven", 12: "twelve", 13: "thirteen"}
  assert f"{table_words[tables]} frozen tables" in readme, (
      f"the README does not state that the rows sit in {tables} tables"
  )
  ```

- [ ] **Step 2: Run the suite to see the guards bite.** `uv run --frozen pytest tests/test_designs_corpus.py -q` → the row-total test now demands `143 rows` and `twelve frozen tables`; the README tests still fail. Expected: 3 failures (row total, design count, design table), guide test green — the completeness test finds `H1`–`H4` in the holdings design via the extended `_ROW` and passes.

- [ ] **Step 3: README.** Four edits:
  1. ~Line 20: `Nineteen documents in `docs/designs/`: …` → `Twenty documents in `docs/designs/`: …` and in the same sentence `2026-08-02 through 2026-08-09` → `2026-08-02 through 2026-08-10`.
  2. Design table: after the `2026-08-09-conformance-cut-2.md` row, append:

     `| `2026-08-10-verified-holdings-record-design.md` | where verified holdings are recorded: a per-location world record in the observer's corpus, act-minted, superseded never expired, projected under a declared coverage — H1–H4 |`
  3. ~Lines 59–60: the row-total sentence spans a hard-wrap **and carries the table list**, which gains H. `There are **139 rows** across **eleven frozen tables** (G, S, W, R, C, X, N, L, D, M, P).` → `There are **143 rows** across **twelve frozen tables** (G, S, W, R, C, X, N, L, D, M, P, H).` (H appends last, matching the guard's insertion order; keep the hard-wrap.)
  4. ~Lines 68–69: the cut-2 sentence still claims the holdings location is open. Change

     `whose verified-holdings observations enter as supplied arguments because where they are recorded remains an open design.`

     to

     `whose verified-holdings observations enter as supplied arguments because where they are recorded was, at the freeze, an open design — closed 2026-08-10 by the verified-holdings record design.`

     Re-wrap to the file's hard-wrap width; the following sentence (`Its slice landed 2026-08-09: …`) stands unchanged.

- [ ] **Step 4: Status flip.** In the holdings design's Status header, change

  `**Status:** design, approved in session. The amendment set of §8 applies in the banking commit; nothing here is implemented, and no conformance arm is claimed —`

  to

  `**Status:** banked 2026-08-10; §8's amendment set applied in the banking change. Nothing here is implemented, and no conformance arm is claimed —`

  (the rest of the header sentence stands unchanged).

- [ ] **Step 5: Full verification.** From `python/`, in the frozen `uv` environment — this is the full gate set from `python/README.md`, not just the corpus tests:
  - `uv run --frozen pytest -q` → **the whole suite passes**.
  - `uv run --frozen ruff check .` → clean.
  - `uv run --frozen pyright src` → clean.
  - `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0.
  - From the repo root: `git diff --check` → clean.
  - Sweep for stragglers: `rg -n "eleven frozen tables|139 rows across eleven" README.md docs/guide/` → no hits; `rg -n "eleven kernel kinds" docs/guide/ docs/designs/2026-08-04-domain-extension-boundary-design.md` → no hits (historical "eleven kinds" statements in the world ruling and ramp §-history remain, by design); `rg -n "remains an open design|still undesigned" README.md docs/guide/` → no hits (the holdings location is now designed, and both recast claims say "had not yet been designed at the freeze" — wording chosen so this sweep stays clean).

- [ ] **Step 6: Commit.**

```bash
git add python/tests/test_designs_corpus.py README.md docs/designs/2026-08-10-verified-holdings-record-design.md
git commit -m "docs: bank the verified-holdings record and extend the corpus guards to twelve tables"
```

---

## Completion criteria

1. Every §8 row of the holdings design maps to a landed edit (Tasks 1–8); the "Not amended, deliberately" sites are untouched.
2. The full gates pass in the frozen environment: `uv run --frozen pytest -q` fully green, `uv run --frozen ruff check .` clean, `uv run --frozen pyright src` clean, `uv run --frozen python tools/check_guide.py` exit 0; `git diff --check` clean; worktree clean.
3. Nothing pushed. The branch is then ready for `superpowers:finishing-a-development-branch` (base: `main`).
