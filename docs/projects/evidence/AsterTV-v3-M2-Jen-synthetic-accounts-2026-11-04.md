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

- accepted candidate: `astertv-v3-m2-jen-r2.tar.gz`
- SHA-256: `d49ecc3361d8b5883e6df7f47ec6f7124e654cac04063f97f510b9bfbf28e17b`
- add-on: `script.asterprofiles.v3lab` version `0.1.1`
- retained checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-r2-20261104`
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

## Remaining M2 gate

The registry and selector are functional, but the normal Aster page router does
not yet consume the active-profile entitlements. The next bounded task is to
place the selector in the v3 settings/account flow and prove that Guest cannot
reach YouTube account state, requests, private books/listening, Home controls,
cameras or private Aster context through adversarial navigation. Until that
passes, this is a retained Jen candidate rather than a v3 account release.
