# AsterTV v3 M10 Jen artwork-readiness evidence — 2026-11-06

## Scope

This standing-canary slice measures when artwork is bound into the active Aster
page on `AsterTV-Jen`. It uses Kodi boolean conditions only. It does not read or
emit titles, artwork URLs, viewing history, account data, image pixels or
screenshots. It fails closed on any active player and restores Media Home.

The reusable harness is
`services/kodi/astertv-v3/low-spec/measure_artwork_readiness.py`. It covers
Media, Books, News, Music and the signed-in YouTube Recommendations route. The
YouTube root is deliberately minimal and loads personal rows only on demand,
so Recommendations is the correct artwork-bearing route for this gate.

An artwork condition must remain true for 250 ms. This stability requirement
was added after the first draft exposed News briefly clearing its active image
during refresh. A final binding-count check prevents a transient condition
from being recorded as success.

## Two-pass result

| Page | Stable artwork-binding range | Maximum received traffic |
|---|---:|---:|
| Media | 284.6–299.7 ms | 1,303 B |
| Books | 287.2–339.6 ms | 1,148 B |
| News | 663.7–698.8 ms | 82,727 B |
| Music | 330.3–430.1 ms | 2,456 B |
| YouTube Recommendations | 787.7–820.9 ms | 2,751 B |

All ten routes passed the 6,000 ms binding budget and remained far below the
2 MiB receive and 256 KiB transmit ceilings. No Kodi player appeared and the
final window was Home (`10000`).

The complete local V3 gate then passed 68 test files, the immutable-v2 check,
the 93-file secret scan, all 15 pages and 127 controls, and the operations
integration check with no gaps.

This closes automated artwork-binding latency. It does not claim pixel-level
rendering, crop quality or visual design acceptance; those remain part of the
non-author physical walkthrough.
