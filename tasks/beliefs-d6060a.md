---
id: beliefs-d6060a
title: "What graphical-model practice offers the composite's deferred limits, and where each piece would live"
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-24T01:04:11Z
updated: 2026-10-24T02:19:31Z
depends: []
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: what explicit semantics and evidence boundaries does the built dag composite still need before science can use it to answer one causal question? The structure/estimator/generator separation, typed estimands and belief-inert composite rows are settled ([ref:composites], [ref:estimand]); do not re-derive them or treat the current graph as a complete causal inference model.

Where to start: the two designs' limitations and the corresponding composite.py and estimand.py implementation; the context report attached to beliefs-8060d0; science goal sci-35af80 and design task sci-4e0f7f. Compare established graphical-model practice, including d-separation and adjustment, to the actual represented semantics. Draw on Bareinboim/Pearl's data-fusion and transportability work for applicability, but do not require general transportability support for the first workflow.

Bound: a research report and ownership recommendation, not a kernel extension or successor belief-policy design. Prioritize the prerequisites for one observed-data DAG question. Address (a) a member claim's total/conditional effect evidence versus an arrow's directness relative to the node set; (b) deliberate absent-edge assertions versus incomplete sketches/unknown edges; (c) authored identification terms versus a computed verdict for a precise graph, query, observed-variable set and assumptions; (d) node-to-measurement bindings, units, time, population and selection, including what commensurable/co_scoped do not establish; and (e) which causal/Markov assumptions each proposed algorithm needs, treating faithfulness separately rather than assuming every operation needs it.

Retain the deferred questions: latent-node treatment; later PAG, undirected and cyclic shapes and proxy/measurement edges (composite limitations 4-6); sub-structure, refinement and agreement between composites (limitation 9); whether a successor belief policy may read structure (limitation 1); adjustment/d-separation semantics (limitation 8); and claims about a whole composite, such as fit or discovery posteriors. For the latter, distinguish diagnostic computation, governed storage of run outputs, and admission of higher-order/model-conditional claims; only the operation that needs new authority should be gated on the non-empirical route or K moratorium. Give recommendation-only treatment to richer shapes and other deferred work unless the first example requires them.

Expected result: [ref:graphical], with a concrete graph/query example, a prerequisite checklist for sci-4e0f7f, and a home for each remaining piece. Default to science for authoring, visualization, adjustment/identification tools and diagnostics; beliefs for meaning, identity, provenance, admission and necessary contract extensions; autonomy for priority/scheduling. Separate supported identification, no valid adjustment set, proven non-identifiability under stated assumptions, and unsupported/incomplete input. Failure to find an adjustment set is not a general non-identifiability proof. Preserve proto-science's lessons: execute and consume a tool result rather than merely export script text; use independently checked examples rather than hand-derived adjustment sets alone; a graph never strengthens belief by assertion. The first science workflow must not wait for beliefs-8060d0's aggregation synthesis or beliefs-638318.

Ideas it wakes: sci-4e0f7f consumes this report and already depends on this task; on completion add a result note there naming the committed report and concrete prerequisites. Also run tasks note sci-37f0c3 --no-reviewed with the diagnostic/admission findings before merging the result. The broader sensitivity and next ideas consume the first workflow later; do not make them prerequisites for this report.

## References

- composites (input, required, kind=spec): docs/designs/2026-09-12-composite-claims-design.md — dag composites and derived standing
- estimand (input, required, kind=spec): docs/designs/2026-09-12-estimand-typing-design.md — control.identification and applicability
- graphical (output, kind=report): docs/notes/graphical-model-mapping-report.md — the mapping

## Notes

- 2026-10-24T02:19:31Z (main): scope: rescoped; checked the built composite and estimand boundaries at db878fd and prioritized causal-workflow semantic prerequisites. Retained the deferred graphical-model questions while separating diagnostic computation/storage from higher-order admission. Science's design consumes the report without waiting for aggregation research.
