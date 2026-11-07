# AsterTV v3 M7 — Family content-volume profile

Date: 2026-11-06  
Room: Family  
State: owner-selected inputs; automation not enabled

## Accepted receiver targets

| User-facing class | Receiver level | Policy value |
|---|---:|---:|
| Movies | 60 | `0.60` |
| Television | 58 | `0.58` |
| YouTube | 45.5 | `0.455` |
| Music | 43 | `0.43` |
| News | 44 | `0.44` |
| Books | 44 | `0.44` |
| Audiobooks | 44 | `0.44` |
| Podcasts | 44 | `0.44` |
| Nighttime maximum | 60 | `0.60` |

The runtime contract has one `Book/Audiobook` class, so the identical Book and
Audiobook choices map to one `0.44` target. Podcast and News remain separate
classes but have the same target. The choices intentionally retain News,
Books, Audiobooks and Podcasts one point above Music.

## Safety interpretation

The nighttime value is a ceiling, not a forced level. At `0.60` it permits the
Movie target and does not lower any selected Family target. Unknown content,
stale/unavailable state, unchanged content class, paused/idle playback and a
manual override continue to produce no automatic action. Any future live
automation must retain the bounded ramp (maximum `0.05` per step), act only at
playback start or class transition, preserve Onkyo/Kodi passthrough, and latch
a physical/app volume change as a manual override for the current session.

## Remaining gate

These values are not deployed and do not authorize automatic receiver changes.
Before activation, the coordinated content-state rollout, exact manual-override
source, nighttime schedule, Home Assistant outage/stale/replay/duplicate tests,
restart recovery and live Dolby preservation must pass. Bedroom requires its
own independent profile and acceptance.
