# The admission ramp — design

**Date:** 2026-08-09
**Status:** **Both gates complete 2026-08-09. The measurement is frozen (§5.1)
and the ruling is written (§6).** Gate 1 banked the instrument
(`python/tools/survey_admission.py`) and its tests
(`python/tests/test_admission_survey.py`) and settled the reconciliation §2.1
records. Gate 2 ran the instrument once, froze the unit-level artifact
(`2026-08-09-admission-ramp-survey.json`, 47 dataset records and 101 declared
resources), and wrote §6 downstream of those figures. The **§7 paper figures
remain reconnaissance** and are labelled at their site — they bear on F2 not at
all. The ruling **amends `W3`** and **`R23`**, **appends `G9`**, and rules the
**dataset basis projection** the address is derived from, taking the frozen
corpus to **139 rows** across eleven tables; §9 is the amendment table.
**Scope:** **closes F2 and conformance cut 1's open question 2** — how a corpus
with zero content-addressed inputs reaches a usable admitted set — narrowed to
the part that survives the recreate-not-migrate ruling: **externally sourced
input**. F2's premise did not survive the measurement: the surviving population
does not start at zero (§6.5).

## 1. What this owes, and what was already cut away

The review disposition record (`2026-08-05-review-disposition-and-conformance-cut-1.md`)
accepted F2 and left the obligation unowned. Its finding column reads
*"content-addressability is empty on day one and no ramp is designed"*, and its
disposition:

> 0 of 259 mm30 datasets carry a content hash, so kernel §2.2's *held* predicate
> and the eligibility gate admit nothing. New obligation: **the admission ramp** —
> how a corpus goes from zero held inputs to a usable admitted set. No banked
> document owns it

The gate it names is kernel §2.2: an input is **held** when we can produce its
exact bytes on demand and identify them by content hash. `G2b` refuses an
assessment over an unheld or unhashed input, and eligibility (kernel §3) needs
the held inputs *and* the processing closure above them.

**Most of F2's evidence no longer carries weight.** F2 was argued from *0 of 259
mm30 datasets carry a content hash*. The predecessor's content is to be
re-authored under the redesigned system rather than migrated — the clean-start
ruling, `2026-08-03-redesign-adoption-ledger.md` §0 — and a corpus authored
correctly content-addresses what it writes. That figure measures the
predecessor.

**What survives is what cannot be re-authored.** Published datasets and
third-party reference resources are external, and no authoring discipline makes
them held. That is the remaining question, and it is what this design measures
and rules.

Papers are external too, and are nonetheless **not** part of it: computation
§4.7's run-input rule puts them on the other side of the boundary (§2, §7 item
3). F2 is a question about run inputs, and every run input is a held dataset.

## 2. The population, and its denominators

The measured corpus is the predecessor's shared store — a record root, and a
sibling payload root holding materialized bytes under the same relative layout.
**Both roots are required arguments to the instrument** (§4); no path on any
particular machine appears in the code or in this document.

**Dataset records only.** The store also holds 274 `paper` records, and they are
**out of scope for this measurement**, on a rule rather than on convenience:
computation §4.7 states that *"every input to a run is a **held dataset**"*, and
a computation whose input is not held is acquisition, never a run. An individual
paper is a `source`; a literature corpus, if one is built, is a `dataset` and
would be measured as one. A paper census therefore measures **W3 addressability**
— whether a record has an accepted external identifier at all — and can bear on
F2 not at all. §7 records it as a separate measurement rather than dropping the
observation.

It is chosen over the eight project corpora for one reason: it is the artifact
most likely to be carried forward rather than re-authored, so a measurement of
it is not heritage.

**Datasets — the denominator is stated in three parts, because the third part is
the hard one.**

| part | count |
|---|---|
| dataset records | **47** |
| …declaring resources in a data package | **34**, declaring **101** resources between them |
| …declaring **no** resources at all | **13** |

The resource count is the parsed one, **corrected at Gate 1 from the 113 an
earlier draft carried** (§2.1).

Every one of the 34 declares at least one resource; the 13 carry no data package
whatsoever. **The unit of measurement is the declared resource** because the two
integrity axes are recorded per resource: a dataset can pin some of its resources
and not others, and a per-dataset unit would have to round that to a single value
in one direction or the other. **The 13 stay in the denominator** because they are
where the corpus's hardest cases sit. Every access-restricted or embargoed record
is among them: the sole `controlled` record, the sole `registration` record and
both `embargoed` records declare no resources at all. One of the 13 also has bytes
materialized in the payload root while declaring nothing, the mirror image of the
failure this design exists to name. A denominator of 34 would report the corpus as
better characterized than it is, by excluding precisely the records that
characterize it worst.

**A DOI, a PMID and a PMCID are external authority identifiers.** They identify a
work; they do not retrieve that work's exact bytes. This document never treats
one as a byte locator, in either measurement.

### 2.1 The reconciliation — settled at Gate 1

Two throwaway readings disagreed about the same corpus: one counted **113**
declared resources of which **90** carried a recorded hash, the other **85**
hashed with **27** of 28 resolved resources pinned. Reconciling them against a
real parse was Gate 1's first obligation, and the reconciliation is published
rather than quietly applied — the corpus survey found four instrument defects,
three of them in review, and each changed a reported number
(`2026-08-07-corpus-survey-and-vocabulary-admission-design.md` §2.1).

**Both readings were wrong, in different ways, and neither figure survives.**

| reading | claimed | cause | correct |
|---|---|---|---|
| `grep '^\s*path:'` | 113 declared resources | counts every `path` key at any depth | **101** |
| block-split on `name:` | 85 hashed, 27 of 28 pinned | only **13** of 101 resources carry a `name`, so most were folded into a neighbour's block and read that block's `hash` | **90** hashed |

The 12-line gap is fully accounted for rather than estimated: **113 = 101
`resources[].path` + 3 `sources[].path` + 9 `licenses[].path`.** The two
non-resource kinds are a dataset-level provenance URL and a license URL — neither
is a declared resource, and the second is not even a locator for anything the
corpus holds.

**A third figure fell with them.** An earlier draft justified the per-resource
unit with *"one record has 1 of its 4 resources present."* That record declares
**3** resources, not 4 — the fourth `path` was its license — and all three are
present. §2's justification now rests on the axes being recorded per resource,
which is true independently of what this corpus happens to contain.

**What Gate 1 did not publish.** Gate 1's runs were diagnostic and discardable;
the distribution across the three axes belonged to Gate 2's single frozen run and
is in §5.1. What this section settles is only the reconciliation above and the
denominator it corrects — and the frozen run confirmed both, reporting 47 records,
34 with a data package, 101 declared resources and 90 recorded digests.

### 2.2 Two boundaries, and the basis boundary comes first

An earlier draft of §6 put the whole question at the holding layer. That was
wrong, and it mattered: a record can fail to be a world entity **before** the
question of whether its bytes are in hand is reachable.

The world address ruling's generalized basis rule
(`2026-08-08-world-address-ruling.md` §3) binds all thirteen kinds (eleven
until 2026-08-10, twelve until 2026-08-11): every addressable entity carries
the basis declared for
its kind — intrinsic, or an
identifier from an accepted authority — and *"if that basis is missing, the
record is a project-scoped **curation note** — not a weakened world entity."*
`W3` is the refusal that enforces it, and it names both cases this measurement
meets: a `source` with no accepted external identifier, and — **as banked when
this section was written, before §6.4 amended it** — a `dataset` **holding no
content**. Its new clause is what makes the ordering bite — a curation
note **cannot be the target of a semantic reference**, so an unbased record is
not merely weaker, it is unreachable.

So there are two boundaries, and they compose in one direction only:

| boundary | question | owner | outcome if it fails |
|---|---|---|---|
| **basis** | does the record have a content identity at all? | `W3` | curation note, unreferenceable — an explicit second act, never a coercion |
| **holding** | are the exact bytes obtainable and pinned? | `G2b`, `R5` | declared and unheld — a world entity, authorable, not belief-eligible |

**A dataset with a recorded content identity and unavailable bytes clears the
first and fails the second.** That is the state the ramp exists to name. **A
dataset with no content basis fails the first**, and no amount of retrieval
rescues it, because nothing pins what would be retrieved.

**But that separation does not exist in the banked text yet, and W3 must be
amended for it to.** World §4.2 currently fuses the two boundaries into one
sentence:

> **Dataset, specifically.** Content identity means a dataset entity denotes
> *data we hold* … A descriptive stub naming a programme with no release pinned
> … holds no content, so it has no basis

Read as written, a content-addressed dataset whose bytes we do not hold **has no
basis** — so it is a curation note, and the ramp's new state is unreachable by
construction. `W3`'s dataset arm therefore narrows from **"holding no content"**
to **"having no content identity."** `W3` keeps ownership of the basis boundary;
what changes is where its dataset arm draws the line.

**The narrowing does not rescue the case §4.2 was arguing about.** A programme
named with no release pinned has no content *identity* either — nothing says
which bytes — so it is still refused, still a curation note, and §1.1's two
dataset rows are still not world datasets. The amendment separates two properties
that happened to coincide in every example §4.2 considered, and leaves its
conclusion standing. Amending a row's meaning mints a successor contract identity
under the retained id (`2026-08-03-normative-contract-design.md` §4); that cost is
now certain rather than contingent.

This is why the 13 cannot be dropped from the denominator: they are not a
smaller version of the 34's problem, they are a **different** problem, sitting at
the other boundary. Whether each of the 13 carries a content basis outside its
absent data package was left to the run rather than assumed here — and the run's
answer was **none of them** (§5.1), which makes all 13 curation notes and puts
the corpus's largest single gap at the boundary this section had to put first.

## 3. What is observed: three independent axes

Byte availability and record integrity are different questions, and one resource
can be interesting on either axis alone. They are therefore reported as
**independent axes**, so that no combination is unrepresentable — in particular
*bytes obtained but never pinned by a recorded hash*, and *bytes present locally
that disagree with the record*.

| axis | values |
|---|---|
| **byte observation** | `local` · `retrieved` · `retrieval-failed` · `byte-locator-untested` · `no-byte-locator` |
| **hash result** | `match` · `mismatch` · `absent` · `unchecked` |
| **byte-count result** | `match` · `mismatch` · `absent` · `unchecked` |

**A byte locator is defined narrowly: a locator that retrieves that declared
resource's exact bytes.** A study landing page does not qualify. An accession
does not qualify. A DOI does not qualify. The definition is what makes
`no-byte-locator` an honest bucket rather than an empty one, and it is the single
place where a generous reading would flatter the result most.

**Narrow is not the same as local.** A resource may declare its *path* as a URL,
in which case that URL is its byte locator — the resource is not stored beside
the record at all, and the path names the exact bytes remotely. Reading a
declared path as necessarily local was a defect the instrument shipped with and
Gate 1 caught: it reported every remotely declared resource in the corpus as
carrying no locator, which is the strictness the definition warns about running
in the wrong direction.

**`mismatch` is never folded into `retrieval-failed`.** A retrieval that succeeds
and disagrees with the record is not a network problem — it is a successful
observation that contradicts the record, and the recorded digest is the only
thing standing between *held* and *believed to be held*. Against 27 of 27 local
matches, a mismatch would be the most informative single result the run can
produce, and it must not be reported as a failure to look.

`unchecked` and `absent` are likewise distinct: one is a question not asked, the
other an answer the record cannot give.

**`byte-locator-untested` carries a reason and covers two different silences.**
No probe was run at all, or a probe was run and the locator was **refused at
preflight** — an unapproved scheme, a non-public destination, an unsafe local
path (§4). Both are questions not asked, which is why neither is
`retrieval-failed`; the reason distinguishes them, and a value without one is
unreportable.

## 4. The instrument

`python/tools/survey_admission.py`, on the pattern of its two predecessors
(`2026-08-07-corpus-survey-and-vocabulary-admission-design.md` §2 and
`2026-08-07-multi-corpus-typing-exercise.md` §1): **run by hand, against roots
outside this repository, never in CI, minting no conformance oracle.** The record
root, the payload root and the scratch root are all required arguments.

Five properties are load-bearing.

1. **A real parse, not a pattern match.** The 85-against-90 disagreement in §2.1
   came from regex block-scoping. Data packages are parsed as YAML, and the
   parsed reading is what the document reports.
2. **Every parse failure is counted and named, never skipped.** Every share is a
   fraction of a stated denominator, and dropping an unreadable record shrinks
   the denominator silently.
3. **The frozen artifact holds every unit-level observation, in two collections
   and a failure list.** One row per resource is not enough: the 13 records
   declaring nothing would contribute no rows at all and vanish from the artifact
   — the same deletion §2 refuses in the denominator.

   | collection | one row per | fields |
   |---|---|---|
   | **dataset records** | dataset record, all of them | data package `present` · `absent` · `unparseable`; declared-resource count; **basis evidence** (below); **payload files present under the record's payload directory that no declared resource claims** |
   | **declared resources** | declared resource | the three axes of §3 |
   | **parse failures** | unreadable file | path relative to its root, and the reason |

   Unmatched payload files are what make the mirror-image case visible: a record
   with **no data package and bytes on disk anyway** produces a dataset row with
   `absent`, a count of zero, and a non-empty unmatched list — while contributing
   nothing to the resource collection. That combination is a required test case
   (tests, below).

   **Basis evidence, recorded and never resolved — and split in two.** §2.2 makes
   the basis boundary the first question, and the artifact must be able to answer
   it for the 13, which package state, resource count and unmatched payloads
   cannot. Each dataset row therefore carries basis evidence in **two separate
   fields, because content basis and authority identity are different things**:

   | field | holds | bears on the basis boundary? |
   |---|---|---|
   | **declared resources with a digest** | a count | **yes** — a recorded digest is the only thing here that pins bytes |
   | **authority and provenance** | `origin`, `accessions`, `access.source_url`, `datapackage`, `derivation`, as stated | **no** — preserved as observations |

   An accession names a *work* at a registry, `origin` says where a dataset came
   from, a `source_url` names a page. None of them says which bytes. Merging them
   into one "states an identity field" flag makes every record in the corpus look
   based, including every record that declares nothing at all — which is the
   opposite of what the boundary is for.

   Two refusals bound the content-basis side, and they are the point of it:

   - **A basis is never derived from undeclared bytes.** Hashing an unmatched
     payload file would manufacture an identity the record does not claim — the
     fabricated-identity failure the generalized basis rule refuses outright,
     since *no fallback basis is derived at any point*.
   - **Whether per-resource digests collectively constitute a dataset's content
     identity is a ruling, not an inference.** If they do, the canonical
     derivation — which resources participate, in what order, folded how — must be
     ruled explicitly, because two defensible foldings give two different
     identities for the same dataset and the instrument has no authority to pick
     one. Until it is ruled, the artifact records the digests present and computes
     no dataset-level identity from them. **Ruled at Gate 2, in §6.2: they do
     fold, under one projection** — every declared resource's digest normalized to
     `<algorithm>:<hex>`, deduplicated, sorted, newline-joined and hashed. A
     dataset has a content identity when every declared resource is pinned, and
     that identity is a minted digest.

     **The instrument still computes no dataset address, and that is a choice
     worth stating.** The projection is a function of the declaration alone, so an
     address is derivable from the frozen artifact rather than needing to be baked
     into it — which keeps the ruling amendable without re-running a measurement.
     Refusing to guess the fold is what left it free to be made once, in argument,
     instead of settled by whichever measurement got there first.

     **What the ruling did change is what the artifact must carry.** The first
     freeze stored bare hex, and *derivable* was a claim it could not support: the
     projection folds `<algorithm>:<hex>` strings, and nothing in the file said
     which algorithm. The instrument now preserves the recorded digest
     algorithm-qualified, tags its own observations with the algorithm it computed,
     and **refuses** a `hash` field it cannot parse as `<algorithm>:<hex>` rather
     than assuming sha256 — that assumption is what lost the fact. §5.1 records
     the refreeze.

     **The instrument accepts `sha256:<64 hex>` and refuses every other digest,
     and that bound is its own rather than the profile's.** Which algorithms the
     profile accepts as pinning bytes is open (§6.2's algorithm residue) and is
     not a tool's to settle. Which one this tool can *check* is settled by its
     code: every observation it makes is a sha256, so parsing a correct `md5` pin
     and comparing it to one would report `mismatch` — the bytes said to
     contradict the record when in fact nothing compared them, the coverage error
     of `fb-2026-07-27-010` reappearing one layer down. A refusal names the tool's
     limit; a `mismatch` would blame the corpus for it. The width is checked for
     the same reason under the right prefix: `sha256:a` pins no bytes.

   The human-readable report **renders from that artifact** rather than being
   computed alongside it, so the prose and the data cannot drift and every figure
   in the document is re-derivable from one file.
4. **Probing is opt-in, bounded on both sides, and destroys nothing.** Retrieval
   runs only behind an explicit flag. *Local side:* bytes are written to the
   scratch root, hashed, and the instrument's own temporary files are deleted —
   only its own; the scratch root **refuses either corpus root, and any
   descendant of either, as its location.** *Network side*, because scratch
   safety bounds none of it:

   **A preflight refusal is not a retrieval failure.** A locator rejected before
   any request is issued was never attempted, and reporting it as
   `retrieval-failed` would record a refusal to look as a finding about the
   resource. Preflight refusals are **`byte-locator-untested`, carrying the
   refusal reason**; `retrieval-failed` is reserved for a request that was
   actually made and did not yield the bytes.

   *Refused at preflight → `byte-locator-untested`:*

   - any scheme outside the approved set, which is `https` alone, with the scheme
     named as the reason;
   - a destination resolving to a loopback, link-local, private or otherwise
     non-public address;
   - a declared local path that is **absolute**, that **traverses upward**, or
     that **escapes its root through a symlink** — resolved and compared against
     the root before any read.

   *Attempted and failed → `retrieval-failed`:*

   - a request that exceeds its **timeout**;
   - a response that exceeds its **streaming byte ceiling**, reported with the
     bound named — never a truncated body silently hashed;
   - any other transport or status failure.

   **Every redirect hop is revalidated** against the same preflight rules, since
   the first URL's approval says nothing about where it lands; a hop refused at
   preflight ends the attempt as `byte-locator-untested` with the hop named.

   > **Amended 2026-09-20 (URL retrieval, conformance cut 35 —
   > `../superpowers/specs/2026-09-19-url-retrieval-design.md`):** the
   > sentence above is superseded at the kernel. The instrument's vocabulary
   > was written before the act-report design reserved
   > `byte-locator-untested` for a locator act **for which no request
   > began**; a redirect hop arrives only after the first request was made,
   > so a hop refused at preflight is **`retrieval-failed`**, and the hop is
   > named by its **ordinal and refusal category only** — never by its bytes
   > or its host, which may carry a token (decision 6 there). The instrument
   > itself now runs on the kernel's transport (`NetworkProbe.fetch` is an
   > adapter over `beliefs.holdings.transport.retrieve`, keeping copies of
   > nothing), so it reports a refused hop the same way. Everything else in
   > this item — the approved scheme set, the non-public-address refusal, the
   > pinned resolution and fail-closed request, the timeout and the streaming
   > ceiling with no partial body hashed — is the kernel's boundary now,
   > with the timeout, ceiling and redirect bound recorded as explicit
   > instrument inputs on every entry.

   **The validated address is the one connected to, and the check fails closed.**
   Resolving a name, checking the result, and then letting the client resolve it
   again leaves the check decorative — the second answer can differ from the
   first, which is the whole of the rebinding attack. The instrument therefore
   pins the resolution it validated and connects to **that address**, while
   preserving hostname and TLS certificate validation against the original name.

   **If it cannot do both, it issues no request.** The locator is
   `byte-locator-untested`, with the inability to pin the validated address as its
   reason. Probing while announcing the check as unenforced would keep the
   exposure and merely document it — a disclosed hole is still a hole, and this
   corpus refuses rather than degrades. The cost of failing closed is a bucket of
   untested locators, which is a visible, recoverable measurement gap; the cost of
   failing open is a request the check was supposed to prevent.
5. **Every probe outcome is stamped with the time it ran.** Retrievability varies
   over time. An undated probe result asserted as a standing property is the same
   error the coreference ruling refused when it kept edge state out of an
   immutable epoch (`2026-08-08-world-address-ruling.md` §5.5).

**What discarding the bytes does and does not buy.** It means the run **does not
materialize either corpus root**. It does not keep a resource from being held:
kernel §2.2 is explicit that data outside the repository is held if
content-addressed and retrievable, so location is not the discriminator. A
matching probe is time-stamped evidence of retrievability. **How long that
evidence supports admission is a question for the ruling**, not a property the
instrument may assume.

**Tests.** `python/tests/test_admission_survey.py`, constructing synthetic record,
payload and scratch roots under `tmp_path`, following the lighter fixture pattern
of the existing suites. Committed fixture files are used only where they
materially improve readability. Every axis value is exercised — including
`mismatch` on both the hash and byte-count axes, and bytes-without-a-recorded-hash
— because those are the arms the real corpus may never produce, and an
unexercised arm is an unmeasured one.

Six cases are required rather than optional, because each is a shape the real
corpus may hold and no axis value alone expresses:

- **no data package, and undeclared payload bytes present** — the dataset row
  reads `absent` with a zero count and a non-empty unmatched list, and the
  resource collection gains nothing; assert also that **no basis is derived from
  those bytes**;
- **an unparseable data package** — a dataset row reading `unparseable` *and* a
  parse-failure row, never a silent skip that shrinks the denominator;
- **a declared resource whose bytes are present and whose recorded hash is
  absent** — obtained and unpinned, distinct from both `match` and `mismatch`;
- **a preflight refusal and a retrieval failure over the same resource** —
  assert the first is `byte-locator-untested` with its reason and the second is
  `retrieval-failed`, so the two are never collapsed;
- **a declared local path that escapes its root** — absolute, upward-traversing,
  and symlink-escaping variants each refused before any read;
- **a validated address that cannot be pinned** — assert the outcome is
  `byte-locator-untested` for that reason and that **no request is issued**, the
  fail-closed arm of §4. A test that only checks the reported value would pass
  against an implementation that fetched anyway.

## 5. Two gates, and the condition that pauses between them

**Gate 1 — bank the instrument. Complete 2026-08-09.** The instrument and its
tests are committed and passing, and every discrepancy between readings — the
85-against-90 among them — is reconciled, with the reconciliation written into
§2.1. Three earlier figures did not survive it, including the resource
denominator itself.

**Gate 1 permits exploratory runs against the real roots, and requires them.**
A disagreement between two readings of real data cannot be reconciled against
fixtures; only the corpus that produced it can settle it. What Gate 1 forbids is
not running the instrument but **publishing any figure from it as a
measurement**. Exploratory output is diagnostic, may be discarded, and is never
frozen.

**Gate 2 — one run, frozen, then rule. Complete 2026-08-09 (§5.1).** A single authoritative run. The frozen
record carries the unit-level artifact, the counts rendered from it, the run
date, the instrument's commit, and the identity of both roots. **Root identities
and relative paths only — never a machine-specific absolute path**, in the
artifact or in this document. The normative section is written only afterwards,
downstream of figures already fixed.

**Root identity, for a root that is not a repository.** The record root may be
under version control; the payload root is not, and has no commit to name. Its
identity is therefore **a digest over the sorted relative-path observations the
run actually used** — each relative path with the size and, where the run read
the bytes, the content digest — so that two runs over the same payload state
carry the same identity and nothing about where the root sits on any machine
enters it.

**What moves it, exactly** *(corrected 2026-08-09: this read "a changed or added
payload file changes it", which overstates the instrument's own bound)*. An added
or removed file moves it, as does any change to a file the run **read** — every
declared resource resolved locally. An **unmatched** payload file is enumerated
and never read, so it contributes a path and a size and no digest: a content
change to one that **preserves its size** does not move the identity. That is the
bound the instrument states in its own docstring, and it is a bound on this
document's root identities too — 45 files across four records are unmatched in
§5.1. The same construction is applied to the
record root, so the two are named the same way and neither depends on version
control being present.

**The pause condition.** If the measured distribution overturns the state model
the ruling is expected to rest on, the normative section is **not** written and
the finding comes back for a decision first. This remains one document either
way; a second document would add ceremony, not evidence.

### 5.1 The frozen run

One run, 2026-08-09, instrument at commit `ee9ba0c`. The unit-level
artifact is committed beside this document as
`2026-08-09-admission-ramp-survey.json`; every figure below renders from it, and
none is re-derived by hand.

**Refrozen once, and the reason is worth recording.** The first freeze, at
instrument commit `03165c0`, stripped the `sha256:` prefix and stored bare hex.
Every count below was identical, and the loss was still real: §6.2's projection
folds `<algorithm>:<hex>` strings, so an artifact holding bare hex yields no
dataset address without an outside assertion about which algorithm pinned the
bytes — either prose in this document or a re-reading of source roots the freeze
exists to make unnecessary. Both digests are now stored algorithm-qualified.
**Both root identities are byte-identical across the two freezes**, which is the
evidence that the re-run read the same corpus and not merely a similar one; the
only fields that moved are `recorded_hash` in 90 rows and `observed_hash` in 28.

| | |
|---|---|
| record root identity | `sha256:dc8b597f682bece65ba9dfc0ee9b3f5cbccb18b3e9f922333509c66f7514b495` |
| payload root identity | `sha256:06568c0fddb9d40d3db4b8d116abdbe4be12f1959871c59b851855872817c532` |
| probing | **not run** — see below |
| parse failures | **0** |

**The frozen run does not probe, and that is a decision rather than an
omission.** Three reasons, in order of weight.

1. **A frozen record must be re-derivable.** Everything above is reproducible
   from the two root identities and the instrument commit. A probe result is not:
   it is time-varying evidence, which is exactly why §4's fifth property stamps
   it. Folding one into the frozen record would make part of the record
   unreproducible by construction.
2. **The byte ceiling would misreport the largest resources.** The eleven
   untested locators total **36.6 GB**, and **three exceed the 512 MB streaming
   ceiling** — 21.3 GB, 9.9 GB and 5.4 GB. Under the run those three report
   `retrieval-failed`, which records *a bound this design chose* as a finding
   about the resource. That is the failure §3 refuses in the other direction.
3. **A probe is a request to a third party.** It belongs to a dated act of its
   own, not folded into a structural measurement of a local corpus.

Consequently all eleven byte locators report `byte-locator-untested`, with `no
probe was run` as the reason — the first of the two silences §3 distinguishes,
never the second. **A probe run remains available and would be a dated addendum
to this document, not a re-freeze**; §8 item 1 is the question it would inform.

**Dataset records — 47.**

| | count |
|---|---|
| data package `present` | **34** |
| data package `absent` | **13** |
| data package `unparseable` | **0** |
| declaring at least one **pinned** resource | **32** |
| stating authority or provenance only | **15** |
| carrying payload files no declared resource claims | **4** (45 files) |

**Declared resources — 101**, of which **90** carry a recorded digest and **101**
carry a recorded byte count. **All 90 digests are `sha256`**, and the artifact
says so itself: each is stored as `sha256:<lowercase hex>` exactly as the record
states it, so §6.2's projection is computable from the frozen file with no
appeal to this prose and no second reading of the corpus.

| axis | distribution |
|---|---|
| byte observation | `local` **28** · `retrieved` **0** · `retrieval-failed` **0** · `byte-locator-untested` **11** · `no-byte-locator` **62** |
| hash result | `match` **28** · `mismatch` **0** · `absent` **0** · `unchecked` **73** |
| byte-count result | `match` **28** · `mismatch` **0** · `absent` **0** · `unchecked` **73** |

**Five readings of that distribution, and the fourth was not predicted.**

**Zero mismatches, on both axes, over 28 of 28.** This is the strongest single
result the run could produce short of a mismatch, and it says the recorded
digests are load-bearing rather than decorative: every byte this corpus holds
locally agrees with what its record claims. §3 named a mismatch as the most
informative possible outcome; its absence is the second most informative.

**The two axes did not separate.** `absent` is **0** on both — no resource has
bytes present without a recorded digest. The pre-ruling §8 asked whether the run
makes that state *reachable in practice*: as observed it is **not instantiated**,
though it is one retrieval away through the eleven unpinned locators. §6.6 rules
what it is, and closes the question.

**Pinning is all-or-nothing in fact, though nothing enforces it.** Of the 34
records with a data package, **32 pin every declared resource and 2 pin none** —
`l1000-cmap` (10 resources) and `sciplex3` (1). **No record pins some and not
others.** §6.2 rules the boundary case anyway, and §6.2 says why the corpus's
silence on it is a bound rather than a confirmation.

**Observed holding is all-or-nothing too, and this was not predicted.** **Eight**
records have every declared resource present and matching **in this coverage** —
28 resources, 0.81 GB — and **26 have none**. **No record is partly observed.**
The eight are `assembly-registry`, `cptac-gbm-2021-proteogenomics`,
`cytoband-hg19`, `gene-crosswalk-hgnc`, `go`, `mondo`, `opentargets-associations`
and `reactome`: crosswalks, ontologies and one proteogenomics release. The other
26 declare **48.44 GB** unobserved here — **11.83 GB** of it pinned by a digest,
and the remaining 36.61 GB the unpinned locators of the paragraph above.

**"Unobserved here" is not "unheld."** The two roots are a **coverage**, and this
run looked in them and nowhere else. Kernel §2.2 puts heldness outside any one
checkout — data outside the repository is held if content-addressed and
retrievable — so a record whose bytes this run did not see may still be held
somewhere it did not look. Reading absence in a declared coverage as a finding of
absence is `fb-2026-07-27-010`'s error, which the coreference ruling refused by
answering `indeterminate` rather than `inactive`. §6.5 carries the distinction
into the ruling rather than rounding it away here.

This does **not** retroactively justify a per-dataset unit of measurement. §2's
justification was rewritten at Gate 1 to rest on the axes being per-resource in
principle, precisely so it would not depend on what this corpus happens to
contain — and what a per-dataset unit would round away is a property of the
population, not of the unit.

**The 13 that declare nothing.** All 13 carry `origin` and an
`access.source_url`; six also carry accessions. **None carries a digest**, and
none has any content-basis evidence at all. One of them, `mmrf-commpass`, carries
**4 payload files with no data package to claim them** — the mirror-image case §2
predicted from the outside, now observed. The other three unmatched-file records
have packages: `opentargets-associations` (31), `cptac-gbm-2021-proteogenomics`
(5) and `reactome` (5).

**The pause condition did not fire.** The distribution does not overturn the
state model §6 was expected to rest on; it populates it, and the majority state
is the one the ramp exists to name.

## 6. The ruling

The direction settled before measurement, and recorded here so the measurement
cannot be read as having discovered it: **`held` is not weakened.** The ramp
names the gap instead — a dataset may be *declared*, carrying its **content
identity** without its bytes, and a declared input is authorable but never
belief-eligible. This is the move the coreference ruling made with
`indeterminate`: name the unestablished state rather than let it read as absence.

**`declared` presupposes a basis and never substitutes for one.** Per §2.2, `W3`
decides first. A record with no content identity is a curation note and is
already unreferenceable; calling it *declared* would re-admit through the ramp
exactly what the basis rule refuses, and would make `declared` the fallback basis
the ruling forbids deriving. So the ramp's new state is available **only** to a
record that has already cleared `W3` — which is why the ordering is fixed here,
before the measurement, and not left to be inferred from the distribution.

Both paragraphs above were written before the run. Everything from here is
written after it.

### 6.1 Three states, and the order they are decided in

| state | the test it passes | standing |
|---|---|---|
| **curation note** | no content identity | not a dataset entity at all; **cannot be the target of a semantic reference** (`W3`, as amended) |
| **declared** | a content identity, without a matching observation of **every** declared resource | a world entity: addressable, authorable, referenceable — and **never belief-eligible** (`G2b` refuses it) |
| **held** | a content identity **and** a matching byte observation for **every** declared resource | belief-eligible, subject to the rest of kernel §3 |

**Held is quantified over the whole declaration**, and the quantifier is
load-bearing. §6.2 makes the declaration the identity, so a dataset one of whose
five resources has been observed is not four-fifths held — it is `declared`, and
an implementation promoting it on one match would admit an assessment over bytes
it never saw.

The order is `W3` first, then holding, exactly as §2.2 fixed it before the run.
The measurement did not choose this ordering and could not have: 15 of the 47
records fail the first test, and no quantity of retrieval reaches them.

**The state is derived, never stored.** Nothing writes `declared` or `held` onto
a record. Two reasons, and the second is a hard constraint rather than a
preference. Storing the state would make a record's content a function of what is
mounted where it was written — the stored-derived-value failure the coreference
ruling refused when it kept edge state out of an immutable epoch
(`2026-08-08-world-address-ruling.md` §5.5). And `R5` forbids it outright: belief
must not depend on artifact availability **in this checkout**, so heldness is a
property of whether a controlled copy is held *anywhere the system can produce
it*, not of the filesystem under the current process. §5.1's run therefore
observes one root's state and is **evidence about that root**, not the system's
answer about any dataset.

### 6.2 What a dataset's content identity is — the declaration, and the projection that addresses it

§4's second refusal left this open as a ruling the instrument had no authority to
make. **Ruled: a dataset has a content identity when its data package declares a
resource set and every declared resource carries a digest under an accepted
algorithm.** A resource whose digest is missing, or recorded under an algorithm
the profile does not accept, is unpinned, and one unpinned resource leaves the
dataset without a content identity.

**A fold is not optional, and an earlier draft of this section wrongly said it
was.** World §2.1's rule is that a world entity's stored address is
`kind:<basis-digest>`, derived from its identity basis (§4.2) — so declaring the basis
to be the resource set while minting no digest over it leaves the dataset with no
address, which is not a state the addressing scheme has. What the earlier draft
was right about is the *danger*: two defensible foldings give two identities, so
the projection has to be **ruled**, exactly once, rather than left to whichever
implementation gets there first.

> **The dataset basis projection.** Take the recorded digest of every declared
> resource, normalized to `<algorithm>:<lowercase hex>`. **Deduplicate**, **sort
> byte-wise**, join with `\n` and terminate with `\n`. UTF-8 encode. The
> **basis-digest** is the sha256 of those bytes, and the address is
> `dataset:sha256:<hex>`.

Four exclusions, each of which an implementation would otherwise be free to
decide differently:

- **Declared paths and names do not participate.** `R23`'s negative (a) already
  rules this for a produced dataset — byte-identical output under two logical
  names is **one** address, *"pinning that the address is not the manifest digest,
  which carries the name."* A declared dataset must answer the same way, or
  renaming a file re-identifies the dataset and the same bytes arriving by
  acquisition and by production take two addresses that `consolidate` (`W16`)
  could never merge.
- **Byte counts do not participate.** The digest already pins the bytes. Adding
  the size gives a second name for one fact, and correcting a mistyped `bytes`
  field would re-mint the address of a dataset whose content never moved.
- **Declaration order does not participate** — sorting removes it, on `W16`'s
  precedent that sorting an endpoint pair makes one identity of two authoring
  orders.
- **Repetition does not participate.** Two declared resources carrying the same
  digest are the same bytes, and a content identity answers *which bytes*, not
  *how many times they were listed*. The consequence is stated rather than
  hidden: a dataset declaring a file and a copy of it is addressed as the dataset
  declaring it once.

**Which digest algorithms are accepted is owed to the profile, and is a real
dependency of this projection.** Two implementations disagreeing about whether an
`md5`-recorded resource is pinned disagree about whether its dataset has an
identity at all. Nothing enumerates the accepted set today; every digest in the
measured corpus is `sha256`, and the projection's algorithm prefix is what makes
the set expressible when it is ruled.

**The instrument does not anticipate that ruling, and its refusal is not a vote
in it.** §4 records that it accepts `sha256:<64 hex>` and refuses the rest —
because sha256 is the only digest it computes, so it is the only one it can
compare a record against. An `md5`-recorded resource stops that survey; it does
not thereby become unpinned. The two questions look alike and are not: *what
pins bytes* is the profile's, *what this tool can check* is its author's, and
answering the first with the second is how a tool's limit gets recorded as a
property of a corpus.

**The empty declaration is unreachable, deliberately.** A dataset with no
declared resources has no content identity at all (above) and is a curation note,
so the projection is never applied to an empty set and `sha256` of the empty
string is never an address.

**This amends `R23`'s positive phrasing, and nothing else.** `R23` reads that a
produced dataset's address **is** the single output entry's content identity;
under a uniform projection it is the fold over a one-entry set, which is a
different digest. The alternative — making cardinality 1 a special case that
returns the resource's digest unfolded — puts a discontinuity inside an identity
function, which is precisely where two implementations diverge silently. Every
one of `R23`'s arms survives the change, including negative (a), which the
projection satisfies by excluding names. §9 tables it.

**The declaration is what fixes the extent**, which is why the rule is
all-or-nothing: a data package pinning 99 of its 100 declared resources does not
say which bytes the dataset is, and a hundredth resource is not a rounding error
in a content identity. Such a dataset is a curation note, and the repair is
explicit in both available directions — pin the last resource, or narrow the
declaration to what is pinned.

**That edge is ruled on argument, not on evidence, and the corpus cannot support
it.** §5.1 found 32 records pinning every resource and 2 pinning none, and **not
one pinning some**. The population is silent on exactly the case the rule is
strictest about. That silence is a bound on this ruling and is recorded as one:
if a partly-pinned dataset later argues that the whole should be reachable, this
paragraph is where the argument starts, and nothing here was measured against it.

**A byte count is not a content identity.** All 101 declared resources carry one,
including the 11 that carry no digest. The byte-count axis exists to catch a
record drifting from its bytes; it pins nothing, and a size is trivially
reproduced by content that is not the content.

### 6.3 Promotion is by verified observation — `G9`, the one new row

§6 pre-committed the test: a new row is added only for a property that is
**independently sabotage-able**, one an implementation could break while leaving
`G2b` and `R5` intact. The ramp has exactly one, and it is the transition the
ramp is *for*.

**Nothing in the banked corpus says how a dataset becomes held.** `G2b` *consumes*
heldness — point a run at an unheld input, assert refusal — and passes just as
well when heldness was established by a lie. `R5` tests the downward transition:
its negative (a) destroys the last held copy and asserts the input stops being
held. `R10` refuses a run whose input is a URL, and routes it to acquisition
without saying what acquisition must verify. `R23` mints a *produced* dataset's
basis at the execution boundary, which is the other half of the population.
**For an acquired external dataset, the upward transition is unowned.**

The sabotage is concrete: adopt *the declared path exists* as the promotion
predicate. `G2b` still refuses unheld inputs, `R5` still holds, `R10` still
refuses URLs, every banked test passes — and the corpus's content-addressing
guarantee is void, because nothing ever compared bytes to the digest that was
supposed to identify them.

> **`G9`.** A dataset reaches **held** only when **every** resource its
> declaration names has a byte observation whose digest matches the digest
> recorded for it. Declaration does not promote, presence does not promote, a
> proper subset does not promote, and no API accepts an authored `held`.

**The quantifier is the row's second job.** An earlier draft said *a* matching
observation, which promotes a five-resource dataset on one match and lets an
assessment run over four resources nobody looked at. §6.2 makes the whole
declaration the identity; `G9` has to be quantified over the same declaration or
the two rulings disagree about what the dataset is.

Its mutation test is written into the kernel's table (§9). Five of its six arms
carry the ruling; the sixth pins the limit — the row says nothing about *losing*
heldness, which is `R5`'s negative (a).

*Declaration does not promote:* author a dataset with a content
identity and no bytes, assert it is a world entity, that it reads `declared`, and
that `G2b` refuses it as an assessment input. *Presence does not promote:* supply
bytes whose digest **differs** from the recorded one and assert the dataset stays
`declared` with the mismatch reported — not promoted, and not reported as a
failure to retrieve. *A proper subset does not promote:* over a dataset declaring
three resources, supply matching bytes for two and assert it is **still
`declared`**; supply the third and assert **held** — the arm an implementation
quantifying existentially would fail while passing every other arm here.
*Location is not the discriminator:* hold matching bytes
outside the repository, content-addressed and retrievable, and assert **held**
all the same — kernel §2.2 is explicit, and a row read as requiring local storage
would break it. *Independence, asserted directly:* install the path-exists
predicate above and assert **`G9` fails while `G2b`, `R5` and `R10` pass**, in the
style `W14` uses against `W1`/`W2`.

`G9` is appended to the kernel table, whose rows are `G1`–`G8` as banked, taking
the frozen corpus from **138 rows to 139** across the same eleven tables.

### 6.4 What the amendment costs

`W3` is **amended, not confirmed**: its dataset arm narrows from *holding no
content* to *having no content identity* (§2.2). `W3` keeps the basis boundary and
keeps routing an unbased record to an explicit curation note; only where its
dataset arm draws the line moves, and its oracle's own §1.1 case is still refused,
since a programme with no release pinned has no content identity either.

Amending a row's meaning mints a **successor contract identity under the retained
id** (`2026-08-03-normative-contract-design.md` §4). That cost was called certain
before the run and is now incurred. `G2b` and `R5` are **confirmed unchanged** —
`G2b` is the refusal a declared input runs into, and `R5` already separates reach
from holding in both directions.

### 6.5 What this answers about F2 — and where its premise failed

F2 was accepted on the finding that *content-addressability is empty on day one*,
argued from *0 of 259 mm30 datasets carry a content hash*. §1 already discounted
that figure as a measurement of the predecessor. **The measurement now says the
premise is false for the population that survives.**

**Two of the three findings are about the corpus; the third is about the
coverage, and saying otherwise would be the error this ruling refuses
elsewhere.** The run looked in two roots. What it establishes there is not
symmetric across the three states, and the table says which is which.

| the corpus, ruled | records | resources | what the run establishes |
|---|---|---|---|
| **held in this coverage** | **8** | 28 (0.81 GB) | a **positive** fact, and coverage-independent: matching bytes were produced and hashed, so these are held wherever else they may or may not also sit |
| **based, unobserved in this coverage** | **24** | 62 (11.83 GB) | that they clear `W3` and that **this run saw no matching bytes**. Whether they are `declared` or held somewhere it did not look is **not** established |
| **curation note** — no content identity | **15** | 11 declared with no digest; the other 13 records declare nothing | a **positive** fact about the records themselves, needing no coverage: nothing in them says which bytes |

47 records and 101 resources, each counted once. The 45 unclaimed payload files
are **not** a fourth column: 41 of them sit under three *held* records and 4 under
one curation note, which is the point of §6.6's distinction.

**The middle row is a measurement of the coverage, not of the datasets.** Kernel
§2.2 puts heldness outside any one checkout, and §6.1 derives the state from the
system's record of verified holdings rather than from a filesystem — so a run
over two roots cannot conclude *unheld*, only *not observed here*. An earlier
draft of this section did conclude it, and called the 24 `declared` and in need of
an acquisition. That is the `fb-2026-07-27-010` error committed by the document
that quotes it: **a failure to look reported as a finding of absence.** The
corrected claim is narrower and still worth having.

**And the gap it exposes is the ruling's own residue.** The reason the run cannot
answer for the 24 is that **nothing in the system records a verified holding** —
if such a record existed, the question would be a lookup rather than a search.
§8 item 2 owns it, and this is the concrete cost of its absence: 24 of 47 records
whose state no measurement can currently determine.

The admitted set is not empty. It is **at least eight datasets**, and they are
exactly the kind a commons is built on: crosswalks, ontologies, and one release
with a published manifest.

So the ramp's answer to *how does a corpus reach a usable admitted set* is three
different answers to three different populations, and conflating them is what
made F2 look like one problem:

- **The 24 based-but-unobserved records need an acquisition *or* a holdings
  record** — and which one is not knowable today. They already carry content
  identities, so none of them needs a rule change: what promotes each is a
  matching observation of **every** resource it declares, and `G9` is what makes
  those observations the thing that promotes it. **How near an acquisition
  actually is, though, splits them.** Not one of their 62 declared resources
  carries a byte locator, so the route runs through the dataset's authority
  fields, and those are present for only **14** of the 24 — a `source_url`, in the
  four accession-bearing cases alongside an accession. The other **10** record
  neither, so nothing in them says where the bytes are: for those, an acquisition
  first requires authoring a locator, and a holdings record is the only route that
  does not. §8 item 1 records the consequence for probing.
- **The 15 without a content identity need authoring**, and no ramp reaches them.
  Retrieval cannot pin what nothing declares. This is a **basis** gap sitting at
  the other boundary, and it is the larger share of the corpus's real distance
  from admission — a result the pre-run framing, which put the whole question at
  the holding layer, would have reported as a holding gap.
- **`held` is not weakened, and did not need to be.** The gap is named, not
  narrowed: `declared` is a world entity that cannot reach belief.

F2 and conformance cut 1's open question 2 close here — on the state model, the
projection and `G9`, none of which depended on the middle row's ambiguity.

### 6.6 The unpinned locator, and what repairs it

Eleven resources across `l1000-cmap` and `sciplex3` declare a URL that retrieves
their exact bytes, and **no digest**. They are the one case where retrievability
and content identity come apart in the observed corpus, and they are worth ruling
because the tempting repair is the forbidden one.

**Retrieval does not rescue them.** Bytes obtained against no recorded digest are
bytes nothing says are the right ones — the state the pre-ruling §8 asked about,
which §5.1 found uninstantiated and which these eleven are one request away from.
**Ruled: that is not an admission state.** It is the interior of an
acquisition. `R10` already puts
a URL-input on the acquisition side of the boundary; an acquisition **ends** by
recording the digest of what it retrieved, and a resource that sits there
indefinitely is an unfinished acquisition, not a dataset in a third condition.
*(Amended 2026-08-11, the act-report design §3.3: "unfinished acquisition" is
now the acquisition operation intent's **unmatched** state under the three-valued
completion reading — unfinished, indeterminate, closed.)*
That question closes on this argument, and it closes on semantics, exactly as it
required — the observed frequency of zero decides nothing.

> **Amended 2026-09-20 (URL retrieval, cut 35):** under cut 29, every
> dataset id derives from its content identity, so a record "declared with a
> locator and no digest" is not a record this kernel can hold — the ramp's
> eleven have no stored declaration to pin. What they are is the
> **acquisition request** (`AcquisitionRequest`, a value: the locators, the
> optional expected digests, the bounds), and the **pin is the mint**: the
> `acquisition` operation looks, materializes where asked, and mints the
> dataset — its id derived from the digests it found — in the same
> transaction as its closing report, whose empirical-observation facet names
> the report through `retrieval`. An expectation that does not match what
> was found mints nothing and reports `mismatch`.

**The repair is an authoring act, and it is not the refusal §4 names.** Recording
the digest of bytes retrieved from a **declared** locator is the acquirer pinning
what the record already points at. Hashing one of the **45 unclaimed payload
files** would be something else entirely: manufacturing a declaration the record
never made, which is the fabricated basis the generalized basis rule refuses at
every point. The distinction is whether the record declared the resource, not
whether bytes were available — and `mmrf-commpass`, with four payload files and no
data package at all, is the case that makes the difference concrete.

### 6.7 What the ruling does not settle

The state is derived (§6.1) from the declaration and the system's record of
**verified holdings** — and **where that record lives is undesigned**. `G9` says
promotion requires a verified observation; it does not say where the observation
is kept, how it is re-checked, or what makes it stale. §8 item 2 carries it, and
§8 item 1 — how long a probe's evidence lasts — is the same question asked about
the remote half. §6.5's middle row is what the gap costs today: for 24 of 47
records, no measurement can currently say which state they are in.

*The record is designed: `2026-08-10-verified-holdings-record-design.md`.*

## 7. What this will not measure

1. **Closure completeness.** Most data-packaged datasets carry a recipe
   directory, which is a processing closure in all but name. Checking one against
   kernel §3.1's seven-part closure — spec hash, code, environment, parameters,
   held-input hashes, nondeterminism contract, output manifest — is a second
   measurement with its own instrument. Eligibility needs both; this design
   measures the input half only, and says so rather than implying the gate is
   closed.
2. **The eight project corpora.** Their external references are largely reachable
   through the commons, and measuring their records directly re-measures material
   the recreate-not-migrate ruling says will be re-authored.
3. **The paper census — a separate measurement, with no bearing on F2.** The 274
   `paper` records are a **W3 addressability** question: does a record carry an
   accepted external identifier, and is it therefore a `source` entity or a
   curation note? Reconnaissance finds **52** carrying one (all via `doi`, with
   `pmid` and `pmcid` appearing only alongside it) and **222** carrying only a
   bibliographic key — which would make the large majority curation notes,
   unreferenceable under §3 of the world address ruling. That is a real and
   probably uncomfortable finding, and it is **not this measurement's**:
   computation §4.7 makes every run input a held dataset, so no paper result can
   move F2 either way. It is named here so the observation is banked rather than
   lost, and so the instrument's schema is not bent to carry a population it
   should not report on.
4. **Whether an authority identifier resolves.** Presence is not resolution, in
   either measurement. Resolving DOIs measures registries, not this corpus.
5. **Anything about the successor's own corpora.** None exist yet. Every figure
   here describes the predecessor's shared store.

## 8. Open after the ruling

1. **How long a probe's evidence of retrievability lasts.** A timestamp is
   recorded; what admission may do with a six-month-old successful probe is
   undecided, and §6 does not decide it — `G9` says a matching observation
   promotes, not for how long the observation stands.

   **This run makes the question less concrete, not more, and an earlier draft
   claimed the opposite.** It said the 24 based-but-unobserved records each depend
   on a probe. They do not: **all 62 of their declared resources are
   `no-byte-locator`**, so no probe can be issued for any of them — what they need
   is a locator or a holdings record (item 2), and a probe is downstream of a
   locator that does not exist. The 11 probeable resources belong to exactly two
   records, `l1000-cmap` and `sciplex3`, and **neither has a basis** — they pin
   nothing, so a successful probe there records a digest for the first time, which
   §6.6 rules to be the interior of an acquisition rather than the verification of
   a declaration. Not one record in this corpus is one probe away from promoting.
   The question stands on the semantics of `G9` alone; the population supplies no
   instance of it.

   *Closed at the record layer 2026-08-10 — an observation stands until
   superseded; what remains is a possible recency-bearing **successor
   projection rule**, pinned in every derivation receipt with an explicit
   reference instant, and it is **not** a belief-policy parameter (the holdings
   design §4).*
2. **Where verified holdings are recorded.** New, and forced by §6.1: the state
   is derived from the declaration and the system's record of verified holdings,
   and that record is undesigned — where it lives, how it is re-checked, and what
   makes an entry stale. `R5` bounds it from one side (it cannot be a property of
   this checkout) and `G9` from the other (it cannot be authored). Nothing fills
   the middle.

   *Designed 2026-08-10 (`2026-08-10-verified-holdings-record-design.md`): the
   record is a world record in the observer's corpus, per-location, act-minted,
   superseded never expired, projected under a declared coverage.*
3. **The partly-pinned dataset.** §6.2 rules it a curation note on argument
   alone. The corpus pins all or none, 32 against 2, and so cannot corroborate or
   contradict the strictest edge of the rule it is the evidence for.

**Two questions closed rather than left open.** An earlier draft asked whether
papers are inputs at all; computation §4.7 answers it — every input to a run is a
held dataset, an individual paper is a `source`, and a literature corpus would be
a `dataset` measured as one (§7 item 3). And §8's second question — whether
bytes-without-a-recorded-hash is its own admission state — is **closed by §6.6**:
it is not a state but the interior of an acquisition, which ends by recording the
digest. That closure rests on the semantics, as the question demanded; the run's
count of zero instantiations decided nothing.

## 9. What this changes elsewhere

Applied in the same change as this document, on the world address ruling's
precedent: a ruling that leaves its amendments untabled leaves the corpus
disagreeing with itself.

| site | change |
|---|---|
| world addressing `W3` | the dataset arm narrows from *holding no content* to *having no content identity*, and gains a positive arm asserting that a content-addressed dataset with unheld bytes is **minted**; the `source` arm, the curation-note routing and the no-fallback negative are unchanged (§6.4) |
| world addressing §4.2, *Dataset, specifically* | the sentence fusing content identity with *data we hold* is split; the §1.1 conclusion stands on the narrowed test |
| world addressing §4.2, the identity-basis table | the `dataset` row's basis becomes the **§6.2 projection** rather than *"manifest/content hash"*, which named no canonical derivation and so gave two implementations two addresses for one dataset |
| epistemic kernel, `G` table | **`G9` appended** with its mutation test (§6.3) — the first row added to the kernel table since it was frozen — plus a paragraph below the table on why the corpus had no owner for the upward transition |
| computation **`R23`** | the positive phrasing *"the address **is** the single output entry's content identity"* becomes the **§6.2 projection over the output manifest's content identities**, so a produced dataset and an acquired one naming the same bytes take one address. Every arm survives, negative (a) included — the projection excludes names, which is what that arm asserts |
| computation §3, the `unknown`-closure argument | *"a `dataset` holding no content"* → *no content identity*, the same conflation in a citing document |
| adoption ledger, artifact 7 | the oracle inventory's kernel homes extend to **`G3`–`G9`** |
| formal model §2.1, the `dataset` player row | its **identities** cell said *"content identity (manifest/content hash)"* — the same underivable phrase as world §4.2's basis table, in the document that inventories what every player's identity is over. It now names the §6.2 projection and its four exclusions. Missing this row is what let the ruling read as complete while the model still licensed the fold it replaced |
| formal model, *Inherits* and §5.1–§5.2 | the inherited kernel range → **`G1`–`G9`**, and the classification gains a `G9` row. Its header counts are corrected in passing from *113 rows / 128 assertions / W (16)* to **117 / 135 / W (19)** — stale since the world address ruling added `W14`–`W16` on 2026-08-08 without moving the totals, and never having counted `W5a`, `W8a`, `W8b` |
| normative contract §4 | frozen-row count **138 → 139**, and the exact current inventory extends to **`G1`–`G9`** — without this the count guard passes while the contract excludes the row it counts |
| README | frozen-row count **→ 139**; the kernel row reads `G1`–`G9`; the design count **sixteen → eighteen** and its date range to 2026-08-09, both stale since 2026-08-08; this document's table entry stops calling the measurement ungated and unrun |
| guide `foundations.md` | the `held` section gains **`declared`** and `G9`; the kernel range → `G1`–`G9`; this design joins `sources` |
| guide `claims-and-belief.md` | the kernel range → `G1`–`G9` |
| guide `glossary.md` | **Declared** is added and **Held** cites it; this design joins `sources` |
| guide `contracts-and-adoption.md` | frozen-row count **→ 139**, with cut 1's own denominator of 126 untouched — `G9` is banked after the cut and is an acceptance criterion for a later slice; the open-edges pointer stops listing the admission ramp as open |
| guide `open-questions.md` | the admission-ramp entry moves out of the open list, replaced by the residue it left: where verified holdings are recorded |
| `python/tests/test_designs_corpus.py` | the guarantee inventory gains `G9`; a new guard binds the README's spelled-out design count to the number of documents, which was stale for a day with nothing to catch it; a second guards the frozen survey artifact's digests as algorithm-qualified, since a re-freeze by a changed instrument is how that fact would be lost again |
| `python/tools/survey_admission.py` | the recorded digest keeps its algorithm instead of being stripped to bare hex, observed digests are tagged with the algorithm the instrument computed, and a digest that is not `sha256:<64 hex>` is **refused** — rather than assumed to be sha256, or parsed and compared against a sha256 observation, which reports a tool's limit as a `mismatch` in the corpus. Gate 2 is refrozen; §5.1 records that both root identities came back byte-identical |

**Not amended, deliberately:** `G2b` and `R5`, which §6.4 confirms unchanged;
`R10`, which the ruling leans on and does not move; the world address ruling's own
*135 → 138* amendment table, which is a true statement about what that ruling did;
and cut 1's frozen denominator of 126, which `G9` post-dates.
