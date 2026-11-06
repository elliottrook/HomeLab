# Mapping AsterTV design to Kodi

- Treat XML control IDs and directional targets as a graph, not incidental
  markup. Reject hidden targets, missing IDs, orphan controls and focus paths
  that disagree with the screen geometry.
- Keep service/data actions outside skin presentation when practical. A visual
  rework must not silently change playback, request, identity or network logic.
- Preserve action/back/return-focus behavior and the target's overlay ownership.
- Use actual art aspect ratios: cast is portrait, related films/television are
  landscape, albums are square, and ordinary movies are poster unless the page
  contract says otherwise.
- Bound labels at rest; reveal long titles by the accepted focused scrolling or
  wrapping rule without changing control dimensions.
- More than eight seasons use a clipped eight-row viewport and move the visible
  window; the season rail remains visually connected to the episode rail.
- Validate both rendered fixtures and Kodi XML/control behavior. Static images
  alone cannot prove OK, Back, scroll, return focus or dynamic list behavior.
- Never deploy from the design skill. Produce the tested candidate and invoke
  the fleet workflow for composition, checkpoint, promotion and rollback.
