# AsterTV v3 M2 Jen synthetic-account evidence

Date: 2026-11-04

Target: `AsterTV-Jen` (`192.168.1.180`)

Authorization: `SA-M2-JEN` in `docs/projects/AsterTV-v3.md`

## Boundary

This milestone installs only `script.asterprofiles.v3lab` and its isolated
`addon_data` directory. It contains two labelled synthetic members and Guest.
All service mappings are synthetic, disabled and incapable of authenticating.
No real account, credential, production profile, Family or Bedroom state is an
input.

Jen's 1920x1080, 18 Mb/s, HDMI-stereo and no-passthrough limits remain in its
separate measured client-capability/playback policy. They are not included in
the account candidate and are not AsterTV v3-wide limits.

## Candidate and recovery

- accepted candidate: `astertv-v3-m2-jen-r6.tar.gz`
- SHA-256: `d21acdb380fc480232849eed85e77ce36e355a9773ecc8b36669f0d0610ef6c3`
- add-on: `script.asterprofiles.v3lab` version `0.2.0`
- retained checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-r6-20261104`
- first checkpoint and exercised rollback:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-20261104`
- checkpoint manifest SHA-256 for the first rollback:
  `1e0a429bfb125be1cd67916b2bd8e8378f4f188cd1c036490c134a3d771b6606`

The first candidate switched to Synthetic Member B, then was removed using the
checkpointed rollback. Kodi returned active, the isolated add-on and state were
absent, and the accepted v2 release guard remained clean before r2 installed.

## Passed gates

- target hostname, idle player and clean 528-file release guard checked before
  each install;
- candidate member allowlist, target identity and SHA checked before extraction;
- state created mode `0600` through atomic replace;
- direct switch to both Synthetic Member A and Synthetic Member B;
- visible Kodi Select dialog opened with three profiles;
- lower-level remote Down moved focus from Member A to Member B and Select
  activated Member B; Back closed the dialog without changing state;
- Kodi restart republished Member A automatically from persisted state;
- sign-out activated Guest;
- malformed JSON published `guest`, role `guest`, state
  `restricted-guest-fallback`, and logged only the exception class;
- the valid state was restored and the candidate was left signed out as Guest;
- Guest has no service mapping and only public catalogue, clock and read-only
  local-settings fixture entitlements;
- Kodi is active, no player is active and no failed systemd unit is present;
- accepted release manifest stayed
  `dfc51bc8a5002f4755bc0ed5d509a4b3dfb502af09efb03abf4938965d17c3ff`;
- Jen-only Jellyfin policy stayed
  `451f4d2173743f5fab93e8ace1a43f7182fb91d1909bdb51651ed87245a7d1d0`;
- release-guard verification reports 528 files and `outcome: clean`.

## Route enforcement and personalized-state protection

r6 adds a separate candidate keymap which wraps the accepted v2 dispatcher; it
does not edit that dispatcher. A pure access policy requires both the named
entitlement and an enabled service mapping before a private route can open.
Neither synthetic Member has an enabled mapping, so a role label alone cannot
unlock Jen's production-connected backends.

Live gates passed for:

- actual Kodi Select-key denial on Books through the loaded keymap;
- pre-action denial of Books, Home/Cameras, Music, Requests, personal YouTube,
  broad search, shared search and voice/Aster context;
- direct custom-window bypass attempts for Books, Home/Cameras, Music, search
  and Requests, each returned to the public News surface;
- non-admin Settings opening only the synthetic profile selector;
- both Guest and Synthetic Member A being redirected away from personalized
  Media Home because neither has an enabled Jellyfin mapping;
- Guest restart returning to News with the persisted Guest identity; and
- the accepted manifest, 528-file guard and Jen-only playback-policy hashes
  remaining unchanged.

The contract now explicitly denies Guest access to viewing history and personal
recommendations. Although `public_catalogue_browse` remains a desired Guest
capability, no existing v2 page is safe for it: Media Home contains Continue
Watching and personal recommendations, while the library exposes the existing
Jellyfin identity. r5 therefore fails closed until a guest-safe catalogue
adapter with an independently scoped mapping exists. The service stats the
atomic registry four times per second for responsive enforcement but reloads
and republishes it only when its timestamp or size changes.

## Remaining M2 gate

The synthetic registry, selector and route enforcement are functional. M2
still needs the adopted household account authority, physical recovery-admin
workflow, per-service real identity lifecycle and guest-safe catalogue adapter.
Until those are designed and separately authorized, r6 remains a retained Jen
candidate rather than a v3 account release.
