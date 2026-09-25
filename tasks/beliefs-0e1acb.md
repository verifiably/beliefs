---
id: beliefs-0e1acb
title: "De-duplicate live.py's coverage, capture, W8b and inbound code with open_world_view"
status: todo
priority: 3
size: s
complexity: mid
created: 2026-09-25T11:35:00Z
updated: 2026-09-25T13:46:35Z
depends: []
tags: [world]
agent: claude-code
---

## Notes

- 2026-09-25T11:35:08Z (main): From beliefs-cc0aea's Task 3 review (2026-09-25): world/live.py (branch design/live-query, merged with cut 41's discharge) repeats open_world_view's coverage block and refusal messages, capture loop, W8b message and inbound-edge construction word for word. Kept deliberately (live-query design §8): the view.py lines are pinned by live arms of cut 23 (W10d, W10e, W10g) and cut 27 (S9-a), and cut 41's arms need single-site targets in live.py. Sharing them means re-targeting those arms through the guards' _LIVE_SABOTAGES tables, plus cut 41's. A portable test pins live's refusal messages equal to the view's in the meantime.
- 2026-09-25T13:46:35Z (main): Also from cut 41's final review: live.py's W8b refusal text repeats open_world_view's (view.py) and, unlike the manifest and duplicate-carrier messages, has no equality pin (Z5-c matches 'W8b' only). The de-duplication removes the copy; until then, pin it or accept the gap.
