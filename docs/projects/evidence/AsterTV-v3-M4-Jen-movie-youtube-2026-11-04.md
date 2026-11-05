# AsterTV v3 M4 Jen Movie/YouTube evidence — 2026-11-04

## Result

The Jen-only Movie integration is retained and reboot-persistent. Movie rows
open the details page before playback; cast and related-title controls work
through the same G20 Select dispatcher as the rest of AsterTV; actor search
opens the exact local-library route and Back restores the owned Movie details
window. The candidate does not autoplay.

The full YouTube page was not enabled. An unsigned, exact Jellyfin trailer
route was tested successfully with the official YouTube 7.4.4 add-on, but the
add-on subsequently left a Sign In workflow when its account rails were
entered. That met the stream's identity stop condition. Jen was restored to a
disabled YouTube add-on with no `addon_data/plugin.video.youtube` directory,
and the Movie Trailer action now appears only when the official add-on is
independently enabled. No production or other-client YouTube state was copied.

## Boundary and baseline

- Target: `AsterTV-Jen` (`192.168.1.180`) only.
- Family and Bedroom were not contacted or changed.
- Accepted v2 guard baseline before the overlay: 528 files, clean.
- Kodi was idle before every install and playback mutation.
- Initial relevant hashes:
  - Movie XML: `42af9320…164a`
  - Movie controller: `406362f7…5c05ce`
  - live Select dispatcher: `6b60681b…7b44e`
  - runtime Select-dispatch overlay: `a3d6f119…325b508`
- Rollback checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m4-jen-movie`.

## Installed candidate

- Movie XML: `ec69ea07…164a`
- Movie controller: `bdb3384e…f201d`
- live Select dispatcher: `d72d8263…397e3`
- runtime Select-dispatch overlay: `0a0d8054…2cc3`
- runtime manifest: `92e60267…0707`
- strict trailer helper: `a94454d3…6888a`
- boot overlay: `astertv-v3-m4-jen.service`, ordered after
  `astertv-release-guard.service` and before `kodi.service`.

The accepted v2 baseline was not refreshed. At reboot the v2 guard restored
the seven protected files, then the M4 unit deterministically reapplied the
candidate before Kodi. This prevents both silent regression and accidental
promotion of an individual v3 milestone into the accepted v2 release.

## Live checks

1. A real library row for *The 39 Steps* opened custom window 1130 through
   `select_dispatch.py`; no player started.
2. The page populated 16 people and 14 related titles from the local Jellyfin-
   synchronized Kodi library.
3. Selecting Robert Donat opened
   `plugin://plugin.video.astersearch/?actor=Robert%20Donat` with heading
   `Robert Donat — Movie and TV credits available on AsterTV`.
4. Back restored *The 39 Steps* details and its ready state.
5. Selecting related title *Psycho* updated the same details page without
   starting playback.
6. The already-watched *Blue Crush 2* opened details, then Play created one
   internal video player; the test stopped it and confirmed an empty player
   list.
7. With YouTube disabled, `Movie.HasTrailer=false`; the account-backed Trailer
   surface is not offered.
8. In the bounded unsigned experiment, the exact Jellyfin route
   `plugin://plugin.video.youtube/play/?video_id=CI-YWRK0VPo` created one video
   player and stopped cleanly. Sanitized inspection showed one local default
   user, zero access tokens, zero refresh tokens and zero developer identities.
9. The later Sign In workflow caused an immediate rollback: the add-on database
   was restored, generated unsigned state was moved into the mode-0700
   checkpoint, the add-on is disabled, and its live data directory is absent.
10. A full reboot left Kodi active and idle, YouTube disabled/state absent,
    and all candidate hashes exact after guard-then-overlay ordering.

Two rapid development stop cycles hit the already-recorded low-spec Kodi
shutdown defect (segmentation fault/timeout while library services were
quiescing). No player was active; the release guard recovered the exact base.
A later normal restart and the final full reboot completed successfully. This
remains an M5/reliability input rather than authority to weaken shutdown or
guard behavior.

## Regression evidence

- Top-level AsterTV v3 tests: 37 passed.
- Accounts: 29 passed.
- Guest catalogue: 8 passed.
- Reliability: 11 passed.
- Low-spec (with sandbox-safe bytecode cache): 11 passed.
- Aster client: 15 passed.
- Total: 111 passed.
- `git diff --check`: clean.

## Open gate

YouTube page integration, personalized recommendations, Subscriptions, Watch
Later, search and Guest isolation remain open. They require a dedicated Jen
YouTube identity/account-data contract and an explicit decision about Guest
behavior. An unsigned trailer success is not evidence that signed-in rails are
safe, and the project must not reuse Family or Bedroom YouTube state.
