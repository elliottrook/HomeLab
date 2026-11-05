# AsterTV v3 M5N Jen News-icon evidence — 2026-11-04

## Result

The Jen News page now places one plain Aster compass inside each of its four
existing News header pills: Daily Digest, Breaking News, Read briefing and
Refresh. Search, clock, the stone-icon side rail, page content and all digest
routes remain unchanged. The candidate is retained and restart-persistent on
`AsterTV-Jen` (`192.168.1.180`). Family, Bedroom and the News source service
were not contacted or changed.

## Boundary and recovery

- Exact admitted News base SHA-256:
  `960645920dc25fd709c0310b178057afaae16fa5260404110b03fda98669cd77`.
- Retained rendered News SHA-256:
  `f9c4b4b9483908eb06a15ee9f126a60caceeedd8b6908cbb7af786b68cce9074`.
- Checkpoint: `/storage/.aster-checkpoints/astertv-v3-m5n-jen`.
- Stable candidate and rollback tool: `/storage/.aster-v3/m5n`.
- Boot unit: `astertv-v3-m5n-jen.service`, after M4Y and before Kodi.
- The accepted v2 guard was not refreshed. It remains first in the boot chain;
  M4, M4Y and M5N deterministically reapply their isolated changes afterward.
- The transform admits exactly four pinned anchors and fails closed on an
  unknown file, missing compass asset, changed anchor or active player.

The first install attempt reached the checkpoint but failed closed because the
Refresh control has an additional right-focus element between its text offset
and upper focus edge. Kodi restarted with the exact unmodified base. The
transform was corrected to preserve that element explicitly, its resume path
was tested, and the same checkpoint then completed the install. This negative
result is retained because it proves anchor drift cannot produce a partial
accepted layout.

## Visual and navigation acceptance

- A 1920×1080 Kodi screenshot was inspected after installation. All four icons
  are contained by their pills, labels remain readable and the existing green
  focus/gold/cream/black-brown page language is preserved.
- Search deliberately remains text-only, matching the established Media-page
  search treatment. The side rail remains stone-icon-only.
- Actual remote actions traversed Daily Digest → Breaking News → Read briefing
  → Refresh, then Down reached the first story. Kodi reported the expected
  label at every focus step.
- XML equivalence tests prove the labels, `onclick` actions and left/right/up/
  down edges of all four original controls are unchanged.

## Playback and persistence

The full-digest action created one internal audio player. Media advanced for
six seconds at speed 1, then stopped to an empty active-player list. A Kodi
restart completed with `Result=success`, `NRestarts=0`, no segmentation or
corruption line, and no YouTube directory error. M5N reapplied successfully;
the live News hash and four-icon count remained exact. The signed-in YouTube
add-on also remained enabled for Jason, showing the prior milestone survived.

All 151 discoverable v3 regression tests pass: the previous 147 plus four M5N
transform, equivalence, fail-closed and lifecycle tests. The pinned live HEVC
harness is not a unit test and was not run. `git diff --check` is clean.

## Deliberate exclusions

This slice does not alter News content, article selection, reader/player code,
TTS, accounts or source services. eBook pronunciation/word timing and podcast
request submission remain separate M5 gates. Neither was started, so no local-
AI workload or Lab Hours reservation was required.
