---
name: astertv-design-engineer
description: Design, review, mock up, or implement AsterTV pages, artwork tiles, buttons, rails, dialogs, focus behavior, icons, and Kodi skin mappings. Use for television and Aster Remote presentation work; hand deployment to the fleet workflow.
---

# AsterTV Design Engineer

Use the design authority rather than reconstructing accepted behavior from a
live screen or conversation.

## Load the relevant contract

Read `services/kodi/astertv-design/tokens.json`, the relevant component/page in
`catalogue.json`, its generated fixture, asset-index entry, and focus contract.
For a Kodi implementation, also read the mapped XML and the target hardware's
performance budget. Private Forgejo masters are asset authority; screenshots
are evidence, not source assets.

For visual invariants and acceptance states, read
[component acceptance](references/component-acceptance.md). For XML/control
work, read [Kodi mapping](references/kodi-mapping.md).

## Design workflow

1. Identify whether the request changes an accepted pattern or creates a
   candidate. Preserve user-accepted choices unless the user asks to revisit.
2. Build privacy-safe 1920x1080 rest/focus/error/long-content fixtures before
   touching Kodi. Include low-resolution or missing artwork where relevant.
3. Define the complete remote focus graph: entry, directional neighbors,
   activation, Back/Menu, return focus, scrolling, first/last and dynamic rules.
4. Check text-safe hero space, artwork ratio/mask, readable titles, contrast,
   coarse viewing distance, reduced motion, and the Jen performance ceiling.
5. Update tokens/catalogue/schemas/generator/tests and regenerate the pattern
   library. New patterns require owner acceptance; do not label them accepted
   merely because tests pass.
6. Map the accepted design to Kodi without changing service behavior. Hand any
   device installation or release to the Fleet Engineer workflow.

## Non-negotiable contexts

- Limestone-backed compass icons appear only on the floating side rail or
  launcher. Top rails, pills, controls and the Remote use plain icons.
- Resting artwork has no selection box. Focus adds narrow jade top/sides and a
  deeper title treatment; it must not resize the tile.
- Pills keep the same contour and dimensions in every state. Focus sharpens the
  champagne-gold rim and adds jade without moving text or neighbors.
- Current-but-unfocused context is gold only; green means focus/action.
- Heroes blend from brown/charcoal toward cream without a hard split and keep a
  readable text-safe area.
- Play, Resume and Trailer are distinct semantic icons. Disabled actions are
  not focusable and explain a recoverable reason.

Finish with generated fixtures, focus validation, Kodi XML tests where
applicable, hardware-class checks, an acceptance boundary, and a concise handoff
that names what changed and what did not.
