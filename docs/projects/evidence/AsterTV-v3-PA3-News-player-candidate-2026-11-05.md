# AsterTV v3 PA3 — News player candidate

Date: 2026-11-05

Status: local v3 candidate; no appliance deployment

## Problem boundary

The v3 News browse page still handed narration to the inherited standalone v2
digest player. The observed playback surface did not make story progression or
the published media images useful. Family and Bedroom production were excluded
explicitly.

## Candidate

The new 1920×1080 player maps the existing, already fenced digest runtime onto
the approved AsterTV language:

- large current-story image, headline, source and summary;
- whole-briefing elapsed time, duration and progress;
- a five-row visible story rail with the published thumbnail on every row;
- automatic selection/following through the runtime's existing
  `selectItem(row)` and `publish(row)` behavior;
- gold current-but-unfocused story state and jade remote focus;
- compact semantic Previous, Play/Pause, Next and Stop icons using the approved
  Gold Rim focus and jade active treatment, plus Back to News;
- missing artwork falls back to the Aster News mark.

The list is deliberately limited to five visible images at once and uses no
decorative animation, preserving the Jen low-spec presentation ceiling without
making its 1080p/stereo media restriction a v3 platform rule.

The only controller transform exposes each story's already loaded `image` and
`source` on its Kodi list item. Feed acquisition, narration, audio caching,
timeline mapping, player ownership, failure fencing and stop/return behavior
remain unchanged.

## Synthetic review path

The v3 pilot News page (`F2`) now opens synthetic window 1204 from **Play from
beginning**. It contains no live feed or audio and demonstrates the playing
story, progress, story artwork rail, current context and focus treatment. The
runtime mapping is held separately under `services/kodi/astertv-v3/news_player/`.

The deterministic design authority includes
`services/kodi/astertv-design/generated/renders/pages/news-player.svg` with
status `candidate-v3-review`. The design-authority render and Kodi pilot now
use the same icon-only transport language as the accepted Movie and TV
surfaces; a fail-closed page audit rejects missing semantic icons or a return to
the legacy Previous/Pause/Next/Stop text buttons. It is not labelled accepted
until owner review.

## Verification

- Six focused News-player mapping and semantic-control tests pass.
- Twelve deterministic design-authority tests pass and all 29 generated files
  are current.
- Twenty-five shared-language/Kodi overlay tests pass, including the updated
  fail-closed inventory of 303 visible buttons.
- The 15-page conformance audit passes all 127 focusable controls with zero
  failures, including the new News semantic-control rule.
- All 44 focused News, conformance, design-authority and shared-language tests
  pass; both XML files parse and the symbolic focus graph is closed.

## Next gate

When a v3 test target is available, install only the synthetic pilot first and
review F2 → Play from beginning. After visual acceptance, the Fleet workflow
must resolve the exact non-production target, compose the current digest
runtime with the controller transform and XML, checkpoint it, verify idle
playback and exercise real story transitions. Production promotion is a later,
separate decision.
