# AsterTV v3 wish list

This is a design backlog, not an authorization to deploy v3 changes. Items move
into implementation only after their behaviour, privacy boundary and regression
checks are agreed.

## Screensavers and idle presentation

- Support multiple Aster idle presentations inside one globally selected Kodi
  screensaver. Kodi chooses only one screensaver add-on; Aster should dispatch
  internally from the last active page.
- Media presentation: balanced random fanart from TV Shows, Movies, Archive TV
  and Archive Movies, with the AsterTV logo at bottom right.
- Music presentation: random album artwork from the Music library, with the
  AsterTV logo at bottom right.
- Define neutral fallbacks for Books, News, Home, Settings and unknown pages.
- Never show cameras, household status, credentials, account information,
  clocks or sound in an idle presentation.
- Retain burn-in protection, immediate wake, active-playback suppression and
  active/expired Home-timer suppression across every presentation.
- Cache or prefetch artwork through Kodi's image layer and fail closed to a
  black Aster-branded screen when art is unavailable.

## Low-spec release qualification

- Add a third, deliberately constrained test client for release qualification.
- Tentative hardware arriving 2026-11-01: fourth-generation Intel Core i5,
  8 GB RAM and 240 GB SSD; confirm the exact CPU, graphics and output ports
  before provisioning.
- Install the accepted v2 release without copying Family or Bedroom credentials,
  then provision only dedicated test access.
- Measure cold boot, page transitions, artwork loading, 1080p playback,
  screensaver memory use and recovery after sleep/reboot before using it as a
  supported low-spec baseline.
