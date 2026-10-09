---
id: beliefs-940592
title: A store-less look route through the session
status: shelved
priority: 2
created: 2026-09-20T15:17:59Z
updated: 2026-10-09T11:32:17Z
depends: []
tags: [holdings, session]
agent: "claude-code/claude-opus-5[1m]"
---

url-retrieval design §13.6: acquire through the session needs a bound store because holdings_context does; a look-only acquisition over a store-less session is undesigned.

## Notes

- 2026-10-09T11:32:16Z (main): shelved: Wake when a caller must look at a URL or store location through a session opened with no store root: a science command that observes a location without materializing it, or an ActContext built for a look alone
- 2026-10-09T11:32:16Z (main): scope: shelved; holdings_context (src/session/writer.py:398) still refuses a store-less session and every route that uses it (acquire, recheck) needs the store; science-commons fetch composes look with a store write, so nothing asks for a look-only route; wake condition recorded by shelve
