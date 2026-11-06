# AsterTV v3 M8 — Remote Select parity

Date: 2026-11-05  
Scope: Aster Remote client and fleet composition

## Finding

Family's accepted TV-details files and launcher all matched their pinned hashes.
The apparent return to the retired Kodi series page occurred only when Select
arrived from Aster Remote. The browser command was translated directly to
JSON-RPC `Input.Select`, bypassing the bounded `select_dispatch.py` path used by
the physical G20 remote. Native Kodi selection therefore opened the old series
view even though the v3 page remained intact.

Separately, the observed Remote HTTP 502 was a bounded upstream outage: systemd
stopped Aster Agent at 19:17:13, rewrote its unit/drop-ins, and restarted it at
19:19:50. Nginx logged connection refusal during the 2 minute 37 second gap.
The service, proxy, PWA hashes, three outbound clients and room mapping were all
healthy afterward. This is a deployment-availability defect, not a PWA,
authorization, Wi-Fi or client failure.

## Correction

- `nav.select` now invokes the same fixed Aster selection dispatcher as the
  physical remote; arbitrary Kodi RPC remains unavailable.
- A host-bound installer accepts only the exact current client hash, requires
  idle playback, checkpoints live/stable/manifest state, reloads only the
  Remote add-on and automatically restores the predecessor on failure.
- The accepted Remote payload, Family equipment recovery payload, desired
  compositions, guards, plans and SBOMs were rematerialized so a global release
  cannot silently restore the bypass.

## Gates

- 27 Remote client and installer tests: pass.
- 47 fleet compiler/materialization/release tests: pass.
- 37 v3 design/shared-language tests: pass.
- Family live TV-details package: exact accepted hashes.
- Live activation: Family, Bedroom and Jen installed the identical successor
  while idle. Each live/stable pair matches `c28bf36e…a5d49`; Kodi remained
  active, transient staging was removed, and the three-room Doctor passes.

