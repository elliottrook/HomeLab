# AsterTV v3 page conformance audit

Date: 2026-11-05  
Scope: all 15 v3 synthetic pages and shared Aster design authority

The complete v3 page set was checked against the approved icon, focus,
artwork, layout and selection contracts. The durable audit covers every
focusable control and fails on missing/default focus, orphan controls, broken
directional targets, stone/limestone icons outside the side rail, discarded
blue tokens, nonstandard Search/top pills, missing plain top-rail compass
icons, or missing distinct Play/Resume/Trailer controls.

Results:

- 15/15 page XML files pass.
- 127 focusable controls have closed numeric navigation.
- Shared component fixtures, token/icon registry, stable button geometry,
  artwork selection language and generated outputs pass all 12 design tests.
- All 25 shared v3 page-language tests pass.
- The only observed navigation deviation was outside the page XML: Aster
  Remote Select bypassed the physical-remote dispatcher. It was corrected and
  installed identically on Family, Bedroom and Jen; see
  `AsterTV-v3-M8-remote-select-parity-2026-11-05.md`.

The new `audit_page_conformance.py` and unit gate are part of the release
surface so a later page or fleet composition cannot silently reintroduce these
classes of drift.

