# AsterTV v3 M10 Jen page-latency evidence — 2026-11-06

## Scope and safety

This slice measures content-free page activation, bounded data readiness and
interface traffic on the low-spec `AsterTV-Jen` canary. It does not enumerate
titles, artwork URLs, household values or focused controls. It cannot open or
play media, and it fails closed if a player exists before or after any route.
The Cameras page is opened without starting its private feed.

Jason released the Jen display on 2026-11-06. Host identity, an idle player and
local Kodi JSON-RPC were rechecked before effects. The harness is streamed over
SSH and is neither installed nor retained on the appliance.

## Reusable gate

`services/kodi/astertv-v3/low-spec/measure_page_latency.py` covers Books, News,
Home, Music and Cameras, then verifies restoration to Media Home. The low-spec
envelope is:

- page activation no more than 250 ms;
- a declared completion signal no more than 2,000 ms;
- no more than 262,144 received and 65,536 transmitted bytes per route;
- no active player at any boundary; and
- an exact final Home window ID of `10000`.

Books, News and Music expose trustworthy completion signals. Home deliberately
debounces rapid refreshes and Cameras has no data load until live view is
requested, so those two routes measure activation and traffic only. Artwork
texture visibility, private camera-stream cost and speech latency remain
separate gates.

Kodi can interleave asynchronous notifications with TCP JSON-RPC replies. The
harness therefore decodes concatenated objects by response ID with a bounded
retry. It also requires a verified Home state after allowing late page workers
to settle. These controls were added after the first draft exposed, rather
than hid, both behaviours.

## Final two-pass result

Both passes succeeded and returned Jen to Home with zero active players.

| Page | Activation range | Data-ready range | Maximum received |
|---|---:|---:|---:|
| Books | 40.2–84.9 ms | 269.0–521.3 ms | 2,475 B |
| News | 33.5–39.3 ms | 96.0–96.7 ms | 414 B |
| Home | 78.7–79.0 ms | not asserted | 3,614 B |
| Music | 78.6–85.9 ms | 985.9–1,017.6 ms | 73,882 B |
| Cameras | 80.3–81.9 ms | not applicable | 2,102 B |

Every measured value is inside the declared low-spec envelope. Four focused
page-latency tests and four idle-sampler tests pass. The full integrated gate
passes 65 test files, 15 pages and 127 focus controls with no conformance or
operations-readiness gaps. Real artwork visibility, camera streaming, speech,
playback and the non-author physical walkthrough remain open.
