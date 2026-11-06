# AsterTV v3 M11 media-lifecycle fallback reconciliation — 2026-11-06

## Outcome

V3 retains the four accepted smart-playlist routes from immutable V2 as its
fail-safe media lifecycle view:

| Route | SHA-256 |
| --- | --- |
| `tv-shows.xsp` | `098e7e05a83c1120e6cc72f1ddacc6551da07c498f1e60430c1b8c9f543e4248` |
| `movies.xsp` | `db53469dd147c0078467a3f2e55defdb7c98a7bf28160f19a3ab9bfd4dd4028f` |
| `archive-tv.xsp` | `769501ff18bdf64b79f0d47cbbd74351298f67a53999717081003b9c3912e069` |
| `archive-film.xsp` | `3cd56cdf45782cbc2a2cac87c18747802efddcbf21754274a67d705cbafc5d3d` |

Each remains tag-based (`Shows`, `Movies`, `Archive TV`, `Archive Movies`), so
movement between current and archive storage does not depend on a cached Kodi
database ID. The page and screensaver contracts continue to reference all four
named routes, and V3 ships no competing `.xsp` replacement.

The new regression fixture extracts and hashes the routes directly from the
immutable V2 release, checks all four screensaver bindings and fails if an
unapproved V3 playlist appears. This completes the fallback-preservation half
of the M11 reconciliation.

The later unified Media Lifecycle view remains an external handoff: it must
provide a validated artifact and stable Jellyfin/TVDB/IMDb identity contract
before it can replace these routes. Until then, V3 freeze and deployment keep
the four fail-safe playlists unchanged.
