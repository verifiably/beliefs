# Models, composites and aggregation: context for beliefs-8060d0

Compiled 2026-10-23 from three read-only investigations: the 2026-09-12 Claude Code
session that produced the estimand-typing and composite-claims designs (and its
follow-on sessions of 2026-09-15 and 2026-09-16), the two designs as built, and
proto-science's causal module and historical model designs. Pointers: `EST` =
docs/designs/2026-09-12-estimand-typing-design.md, `CMP` =
docs/designs/2026-09-12-composite-claims-design.md, `BP` =
docs/designs/2026-08-05-belief-policy-design.md, `KER` =
docs/designs/2026-08-02-epistemic-kernel-design.md (all in beliefs). `proto:` paths
are relative to the proto-science checkout.

## 1. What 2026-09-12 settled (agreed by the user, built)

- "Model" names three things, kept apart (CMP §1 :47-54; EST §12 :751-754). A single
  model layer was rejected because it re-merges them.
  - Structure: the `composite` kind in beliefs (built, cut 32, 2026-09-16).
  - Estimator: the spec's `method`; its product is the typed estimate and
    uncertainty (estimand typing built, cut 31, 2026-09-16).
  - Generator: simulation, permutation, bootstrap, fitting are runs; a fitted model
    is only ever a `reads` input (CMP :49-51). Simulation alone yields no
    assessment (KER :1342).
- Bayesian is an inference posture orthogonal to all three: estimation inside a
  spec is method; Bayesian aggregation is a successor belief policy.
- The "meta-model" is the kernel's typed dependency graph; no separate layer.
- A `dag` composite: explicit node set, members are causal-layer propositions read
  as directed edges, polarity is the edge's sign (the user's review correction),
  absence of an edge among declared nodes is the one assertion. Belief-inert; its
  reading is one row per member (belief, identification terms), never a scalar
  (CMP decisions 1-5; :569-570, :945-947). Only `dag`; cycles, structural and proxy
  members refuse.
- Estimand: contrast, measure and scale, reference, control (identification,
  conditioning); applicability beside it; estimate a finite decimal; uncertainty an
  interval at a level or a standard error; no p-value field.
  `commensurable` (key = estimand minus identification, per proposition) and
  `co_scoped` (equal applicability) are total and read by nothing yet (estimand.py
  :417-434).

## 2. Handed to `science`, never filed there

- Composite summary and ladder presentation over the rows: "belongs to the
  `science` surface" (CMP :575-578, limitation 7 :992).
- A scope comparison view of applicability against the claim's qualifiers
  (EST :108-110, :785-787).
- In the session only (assistant proposal, not in a design): generator tooling
  "lives in `science`", and a `next` that ranks hypothesized edges and assumptions no
  assessment bears on ("a `science` query, not a stored kind").
- Today science builds typed estimands in `spec` and nothing more: no composite
  command, reading, summary or ladder; `next` ranks propositions only; no
  simulation, fitting, export or identification tooling; no sci task for any of it.

## 3. Deferred, with or without an owner

| Item | Where it sits |
|---|---|
| Weights, constant scope, non-commensurable and not-co-scoped handling | beliefs-638318 (shelved); EST :571-574, :592-595 |
| Whether a policy may read composite structure | CMP limitation 1 |
| Adjustment sets, d-separation, Markov and faithfulness semantics | CMP limitation 8: "a later design", no owner |
| Relations between composites (sub-structure, refinement, agreement) | CMP limitation 9: definable, not defined |
| Latent nodes; `pag`, undirected, cyclic shapes; proxy and measurement edges | CMP limitations 4-6, later grammar versions, no owner |
| Model comparison, mediation, attenuation | higher-order moratorium, beliefs-9e1f60 (shelved) |
| Claims about a composite (fit, discovery posterior); simulation as evidence | non-empirical route, KER §11, open question, no task |
| Observation-first, weigh models by data | beliefs-8b26dc |
| measurement_model | slot only (EST limitation 1) |
| Fitted model never an `observes` input | prose only (CMP :49-51); no oracle row or code found |

## 4. Proto-science lessons

- The causal module never got past structure: script-text exporters to pgmpy
  (back-door adjustment sets only) and ChiRho (all-Normal toy SCM, one fixed
  do-query); no fitted parameters, no round trip, no result fed back into belief
  (proto: science/src/science_tool/causal/). It bit-rotted behind tests that could
  not fail (proto: docs/plans/2026-07-18-causal-tooling-gaps.md :39-82).
- Adjustment-set derivation was hand-rolled and wrong on first attempt in all three
  projects (proto: docs/plans/2026-07-18-statistics-skill-provenance-and-baygent-pull-design.md
  :27-33). The most useful causal result proto produced was an identification
  verdict: a corrected adjustment set and a not-identifiable finding.
- t034 permission ladder: an estimate may strengthen belief only with an identified
  identification payload and estimator diagnostics; a discovered or elicited graph
  never strengthens belief by assertion (proto: meta/evidence/t034-causal-graph-contract.md
  :173-185, :276-290).
- Elicitation and discovery as two routes to a model, with evidence moving a patch
  from prior to posterior (proto: docs/plans/historical/2026-06-06-knowledge-meta-model-and-substrate-design.md
  :85-99); L0-L4 ladder, meant to be derived but hand-authored in practice.
- Aggregation: best line per independence group and stance; ordinal ladder with a
  separate contested flag; scoped refutation (only an independent, strong,
  whole-claim dispute caps belief); adversarial sweep that shows a net only when its
  sign survives (proto: graph/belief.py; docs/plans/historical/2026-05-24-evidence-aggregation-phase2-design.md
  :64-77).
- Failures: metadata collapsed to defaults (of mm's 396 evidence lines, 383 weak, 228
  shared-source), so quality tables had nothing to separate; subjective logic over
  ordinal step scores (a category error, never swept); a stated continuous (0, 1)
  belief never calibrated; Bayesian-only result fields dropped hazard ratios,
  p-values and intervals (finding F11); log-odds framing, withdrawn in BP §3.1.
