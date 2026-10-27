# AsterTV Version 2 — endurance evidence

Updated: 2026-10-27. Target: HP lab `AsterTV` (`192.168.1.140`).

## Bounded mixed-player soak

The final composed HP client passed six consecutive synthetic video/audio
cycles through Kodi in one native invocation. The harness:

- required Home with no active player before starting;
- verified the pinned private video and synthetic narration fixtures;
- opened, paused, resumed and naturally completed each video;
- opened, paused, resumed and explicitly stopped each audio sample;
- returned Home and required no active player after every cycle;
- wrote no library, watch-history or listening-progress field.

Harness SHA-256:
`5b1c400661e4fbad96b5479433e8231da9db92dcde92a0fabbbefaf33b430169`.

## Result

| Metric | Start | Peak/end | Post-run cooldown |
|---|---:|---:|---:|
| Kodi resident memory | 404,820 KiB | 664,700 KiB | approximately 628 MiB |
| CPU temperature | 41°C | 35°C | stable |
| Completed cycles | — | 6/6 | — |

Kodi retained playback caches after the first cycles but did not show
unbounded per-cycle growth: later samples ranged from 655,716 to 664,700 KiB.
The process did not restart, the run created no Kodi crash file, the inspected
log window contained no `ERROR`, `FATAL` or `EXCEPTION` line, and the player
returned idle on Home.

This is useful short-soak evidence, not a substitute for owner and household
use over days. Long-duration acceptance remains part of the finite release
walkthrough; any crash, stuck player or continuing memory growth during that
period must be treated as a release finding.
