# AsterTV v3 M9 — Jen page-aware idle canary

Date: 2026-11-05

Target: AsterTV-Jen (`192.168.1.180`) only

Status: installed with section-aware branding and automated gates passed; owner
visual acceptance pending

## Authorization and preflight

Jason approved `SA-M9-JEN` and confirmed playback stopped/display free. The
immediate recheck matched hostname `AsterTV-Jen`, active Kodi, enabled/successful
`astertv-release-guard.service`, selected v2 screensaver `0.2.0`, absent v3
target and the exact three pinned v2 payload hashes. Kodi's web API remains
intentionally disabled, so the human idle confirmation was retained rather
than bypassed.

## Candidate and recovery

- deterministic candidate archive:
  `5623c09af3fd48157e70ccdf84528626dd6925473a2ee1737751683f10a1055a`
  (3,922 bytes, embedded `release=false` manifest);
- host-bound installer:
  `5b0bf1a5ac328abadab603588a9fdf8ddc5c34f633ce373435f65bb687bfa68d`;
- checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m9-jen-20261106T030453Z`;
- prior selection retained in the checkpoint:
  `screensaver.asterhome.v2lab`;
- installed selection: `screensaver.asterhome.v3`.

The installer stopped only Kodi, checkpointed `guisettings.xml`, `Addons33.db`
and the prior Kodi log, installed the five exact manifested files side-by-side,
enabled the new add-on, selected it and restarted Kodi. Any failure after the
first mutation restores the exact checkpoint, removes only the newly absent
v3 directory and restarts Kodi. The v2 add-on was neither changed nor deleted.

## Automated acceptance

- Kodi discovered `screensaver.asterhome.v3 v0.1.0` and remained active.
- Deployed `default.py`, `policy.py`, `service.py` and `AsterIdle.xml` hashes
  match the embedded manifest.
- Media, Music and neutral source pages each loaded the v3 `AsterIdle.xml` and
  woke through the normal input path without Python/Kodi errors.
- A synthetic `AsterHub.HomeTimerActive=true` on the Home window prevented a
  fourth player load (`before=3`, `after=3`), then was cleared immediately.
- The pre-Kodi release guard finished `Result=success`, `ExecMainStatus=0` and
  retained the side-by-side candidate as an unowned extra rather than changing
  its accepted baseline.
- Kodi RSS observed after the three paths was 529 MiB, 541 MiB and 550 MiB;
  `/storage` retained 114.9 GiB available.
- Add-on database retains enabled v2 and v3 rows; only v3 is selected.
- Family and Bedroom were not contacted or changed.

## Remaining acceptance

Owner review found the first canary's generic Media mark was wrong for Music
and other sections. The corrected candidate maps only the coarse page class to
the exact installed approved assets:

- Media → `27-aster-media-logo.png`;
- Books/Listening → `28-aster-books-logo.png`;
- Music → `29-aster-music-logo.png`;
- News → `30-aster-news-logo.png`;
- Home/Cameras → `aster-home-logo-512.png`;
- Settings, Requests and unknown → plain `aster-compass-128.png`.

The revised deterministic archive is 4,129 bytes at
`254ac8bdb8b49989e4157d42824e06ed7ced3bd25836e9d8fa412a295345bc16`.
Twelve focused tests pass. Atomic upgrade checkpoint
`/storage/.aster-checkpoints/astertv-v3-m9-branding-20261106T031300Z`
retains the generic canary; Kodi restarted, retained the v3 selection and
loaded the corrected Music presentation without error.

A final privacy-safe playback gate used a generated 15-second mono silent WAV
with SHA-256
`f7da44dea4aeab712f2a26d247d8bffc9985823aa97c45931670878ad8b6830f`.
While Kodi played it, an explicit screensaver activation left the v3 player
load count unchanged (`before=1`, `after=1`); playback was then stopped. The
missing-art contract is now pinned separately: both artwork surfaces start
hidden over solid black, the section logo remains visible, and artwork becomes
visible only after a non-empty local result. The already exercised neutral
path uses the same black/logo base.

Jen is left on that Music idle presentation for owner review. Confirm centred
album art, Aster Music branding, acceptable 18-second changes and mark movement. A
The remaining gate is owner confirmation of the corrected section logo,
acceptable 18-second changes, corner movement and wake return. Until then this
is a canary, not a release or promotion authority.

