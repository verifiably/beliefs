---
id: beliefs-9dcc6f
title: "Dataset identity for time cuts, revised-in-place series and digest-less sources"
status: todo
priority: 3
size: m
complexity: high
process: planned
created: 2026-10-11T18:56:52Z
updated: 2026-10-11T18:56:52Z
depends: []
tags: [heliophysics]
source: sun-374ea3
agent: claude-code/claude-fable-5-1
---

From the sun phase-1 resource survey (findings.md in docs/reports/2026-10-10-phase-1-survey of the sun repository; quarry side filed separately). Heliophysics series are cut by interval a thousand overlapping ways (probes/jsoc/19, cdaweb/19, soar/16), several sources revise their files in place (SILSO monthly reissue with provisional rows, probes/silso/05, 06; OMNI values replaced as better data arrive, probes/omniweb/01; CDAW CME rows edited a year later, probes/cdaw-cme/06; SWPC lists rewritten for three days, probes/swpc-events/12), and of 15 data resources only SILSO publishes digests (probes/silso/08, verified). Questions for the acquisition operation: is one dataset per cut the right identity when cuts overlap; is a dated download of a revised-in-place file a version of one dataset or a new dataset; what does the act report record when the source publishes no expected digest (the computed sha256 and the download time, with no provenance check possible). Worked examples with the probe evidence are in the survey report.
