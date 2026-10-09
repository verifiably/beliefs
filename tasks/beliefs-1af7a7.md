---
id: beliefs-1af7a7
title: "URL locator canonicalization: IDNA hosts, empty and leading-zero ports, percent-encoded hosts"
status: shelved
priority: 2
created: 2026-09-20T15:17:59Z
updated: 2026-10-09T11:32:18Z
depends: []
tags: [holdings]
agent: "claude-code/claude-opus-5[1m]"
---

url-retrieval design §13.3: a non-ASCII host refuses at construction; an IDNA canonicalization rule is a profile amendment to holdings §2.

Joined 2026-10-09 by beliefs-27d500 item 13 (the cut-35 review's "spec §13 candidates", ledger `docs/plans/2026-09-20-url-retrieval-execution-ledger.md` line 37). The design's decision 1 is silent on these spellings, and the code picks an answer without a ruling. `src/holdings/records.py:175-181` canonicalizes `h:` and `h:0443` to the default authority and keeps a percent-encoded host as written. `src/intents/holdings.py:26-35` `_url` checks only the scheme, the authority, the absence of `@` and the character range, so it admits spellings the profile would canonicalize differently, and §13.9 says such an intent stays unmatched forever. All three are one decision: for each spelling, refuse or canonicalize, written as a holdings §2 profile amendment, and then make `_url` match the profile or record the gap.

## Notes

- 2026-10-09T11:32:16Z (main): shelved: Wake when a real dataset locator needs a non-ASCII host, an explicit or zero-padded port, or a percent-encoded host, or when a raw-written url intent goes unmatched because _url admitted a spelling the profile canonicalizes differently
- 2026-10-09T11:32:16Z (main): scope: shelved; retitled and joined by beliefs-27d500 item 13 (port and percent-encoded-host canonicalization, intents _url looser than the profile), one holdings §2 profile amendment; no dataset since cut 35 has needed any of these spellings; wake condition recorded by shelve
