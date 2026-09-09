---
id: beliefs-fda0e5
title: "W8b at build: uid uniqueness is unchecked and a duplicate address is a ValueError, not a duplicate-location finding"
status: todo
priority: 2
size: m
created: 2026-09-09T12:01:40Z
updated: 2026-09-09T12:01:40Z
depends: []
tags: [world-read, conformance]
---

Measured 2026-09-09 on 197f517: epoch.build_epoch publishes two records at different addresses sharing one uid, and refuses one address held in two corpora with derive.address_map's bare ValueError instead of the duplicate-location finding W8b promises. Cut 23 does not select W8b; the view refuses uid ambiguity at open as its own half.
