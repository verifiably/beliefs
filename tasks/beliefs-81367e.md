---
id: beliefs-81367e
title: A recipient holding two overlapping publications cannot build an epoch (duplicate-location)
status: idea
priority: 2
created: 2026-09-27T13:50:26Z
updated: 2026-09-27T13:50:26Z
depends: []
tags: [publication]
source: beliefs-3ce305
agent: claude-code/claude-opus-5-5
---

Found in cut-42 spec review round 3. Publishing keeps selected records' addresses and uids, so every republication of one view shares records with its predecessor; derive.address_map refuses one canonical address held in two corpora (duplicate-location), so a recipient's epoch and world view fail once a second publication is admitted. publication_tip avoids it by reading held roots alone (publish-act-remote spec decision 9, §13 item 3), but every other world read does not. Decide whether retiring the superseded corpus removes it from the index, or the recipient must consolidate; this is the precondition for a recipient reading its world after a second publication.
