# Contributor guide — design

**Date:** 2026-08-08
**Status:** Approved 2026-08-08; implemented as `docs/guide/` and maintained
under §6's rule.
**Scope:** A concise, topic-first companion to the redesign documents for new
contributors. The guide summarizes decisions; it does not replace or amend
them.

## 1. Purpose

The redesign corpus is thorough but organized by the order in which problems
were resolved. A new contributor instead needs a stable mental model: what
Science believes, which objects carry that model, how identity and history
work, how computation becomes eligible evidence, and which parts exist today.

The guide will provide that path while keeping exact links back to the design
documents for readers who need definitions, rationale, limitations, or
acceptance criteria.

## 2. Authority and freshness

The guide is explanatory, not normative. Design documents, their amendments,
and their guarantee tables remain the source of truth. When a summary and a
design disagree, the design wins and the guide should be corrected.

Every page carries YAML metadata with:

- `title`
- `status`, initially `living`
- `created`, initially `2026-08-08`
- `updated`, initially `2026-08-08`
- `sources`, listing the design documents summarized by that page

YAML front matter is a deliberate departure from the bold-key metadata used by
`docs/designs/`: the guide needs a parseable source list and freshness dates.
`living` has the ledger's meaning — the page changes as its source decisions
and implementation state change — and is not a design-maturity claim.

Guide pages distinguish **design status** from **implementation status**. A
banked or approved design is not described as implemented unless the adoption
ledger says it is. The adoption ledger is the authority for
implementation state; the repository README is not a second authority.

A commit that banks or amends a design updates its affected guide pages and
their `updated` dates in the same commit. A ledger change that alters
implementation state does the same. This is the guide's freshness trigger;
later cleanup is not the normal update path.

## 3. Organization

`docs/guide/` will contain:

| Page | Responsibility |
|---|---|
| `README.md` | Introduce Science, show the conceptual map, link to the ledger for implementation status, and provide newcomer and reference reading paths. |
| `foundations.md` | Explain the epistemic invariant, kernel, ownership boundaries, profiles, and main record categories. |
| `claims-and-belief.md` | Explain typed claims, assessments, evidence eligibility, belief policy, domain vocabulary, and the corpus measurements that tested vocabulary admission and claim typing. |
| `identity-world-and-change.md` | Explain semantic identity, addresses, corpora, the world index, epochs, retraction, supersession, and the mutation log's pre-mutation registration, chains, anchors, and detectable-removal guarantee. |
| `computation-and-reproducibility.md` | Explain analysis specs, run closures, replay eligibility, equivalence, and verification. |
| `contracts-and-adoption.md` | Explain normative contracts, guarantees, conformance, review evidence, implementation cuts, and adoption order; link to living sources for current detail rather than duplicating them. |
| `open-questions.md` | Consolidate unresolved questions without silently promoting limitations or deferred implementation into design uncertainty. |
| `glossary.md` | Provide one canonical, alphabetized set of short definitions linked to the relevant topic pages and sources. |

This organization follows concepts rather than source-file boundaries. A
design may inform several pages, and a page may synthesize several designs.

## 4. Page shape

Topic pages use this structure, omitting a section only when it has no useful
content:

1. **TL;DR** — one sentence.
2. **Why it matters** — the user-visible or epistemic problem in one short
   paragraph.
3. **Key ideas** — the smallest set of concepts needed to understand the topic.
4. **How it connects** — relationships to other guide topics.
5. **Current state** — what is designed, banked, measured, or implemented.
6. **Open edges** — a short link to the consolidated question list.
7. **References** — precise design-document sections and other authoritative
   project sources.

The index, glossary, and consolidated open-question page use structures suited
to navigation rather than forcing this template.

## 5. Editorial rules

- Lead with the system idea, not the history of how it was discovered.
- Prefer short paragraphs, bullets, and small tables over exhaustive prose.
- Define a term once in the glossary; topic pages may give only the local
  context needed to read them.
- Preserve important distinctions such as record versus view, occurrence
  versus authorization, replay eligibility versus epistemic verdict, and
  design status versus implementation status.
- Prefer frozen guarantee identifiers such as G3, W8a, R12, M10, and P1 over
  section numbers. Link to a section when no frozen identifier exists.
- Link directly to the relevant design passage whenever a concise summary
  necessarily drops qualifications.
- Carry forward settled amendments rather than repeating superseded wording.
- Report measurements with their stated scope and limitations.
- Use repository-relative links and the existing `docs/` conventions.

## 6. Source coverage

Each of the fifteen redesign documents that predate this guide design will
appear in at least one guide page's `sources` metadata or reference list. The
adoption ledger alone governs implementation-state claims. Because the ledger
and the review-disposition record change as work lands, the guide links to them
for current detail and summarizes only stable decisions. Later sources follow
the same update trigger; no generated synchronization mechanism is needed.

## 7. Verification

One small repository checker validates the two mechanical rules:

- every guide page has well-formed YAML metadata with the required keys;
- every relative Markdown link resolves.

The checker uses the project's existing Python and YAML dependencies and has a
focused regression test. It does not generate or rewrite documentation.

Editorial review checks the remaining rules:

- coverage of every existing design document;
- consistent glossary definitions and internal links;
- no unresolved placeholders;
- explicit separation of designed, banked, measured, and implemented states.

The guide is successful when a new contributor can read the index plus the five
topic pages in order, explain the system's invariant and major boundaries, and
reach the exact source sections for details without reading the full design
corpus first.
