# AsterTV Version 2 production promotion

- Date: 2026-10-27
- Production client: `AsterTVProd` (`192.168.1.157`)
- Lab client retained: `AsterTV` (`192.168.1.140`)
- Result: AsterTV 2.0.0 promoted to production

> Superseded 2026-10-28: Jason reported a player skip recap/intro/outro
> regression and requested v2 withdrawal. Production was rolled back to the
> v1.1.1 add-ons and remote keymap with user databases and account state
> preserved. See [current resume](Aster-TV-Version-2-Current-Resume.md).

## Outcome

The accepted HP V2 candidate is active on the BOSGAME production client. The
production successor keeps the same feature family while replacing the lab-only
hostname fences with an explicit two-client allow-list. Kodi databases, watch
state, audio/passthrough settings, display settings, media and playlists were
preserved.

The YouTube migration copied only the HP API configuration, OAuth account state
and add-on settings over SSH. Cache databases and viewing history were excluded.
The official add-on subsequently reported the account as fully logged in. No
credential value or account token was printed or committed.

## Recovery

The production client retains three private recovery layers:

- full pre-V2 profile/configuration checkpoint at
  `/storage/backup/astertv-v2-preproduction-20261027/profile-config-v1.1.1.tar.gz`;
- focused pre-production-successor runtime checkpoint at
  `/storage/backup/astertv-v2-preproduction-20261027/production-compat-before/runtime.tar.gz`;
- the pre-transfer production YouTube files under
  `/storage/backup/astertv-v2-preproduction-20261027/youtube-profile-before-hp-transfer`.

All are private on-box files and their archive/checksum checks passed. The
production payload SHA-256 is recorded in
`services/kodi/releases/aster-home-v2.0.0.json`.

## Integration correction

TrueNAS NFS shares 10 and 11 now admit both Aster clients, and remain read-only:

- `/mnt/Media/AsterReader/ready`
- `/mnt/Media/AsterReader/generations`

The production automounts were exercised after the change. Both mounted
successfully, the Books feed was refreshed, and the Books landing smoke then
passed. No writable reader export was granted to either TV client.

## Validation evidence

- 1,362 local V2 tests passed; one established skip remains.
- Kodi and the Books refresh timer are active; no systemd unit is failed.
- Eight runtime component manifests, the Music manifest and skin hashes match.
- EPUB reader bundle, consumer and activation hashes match.
- Media navigation smoke passed with no playback or queue residue.
- Books navigation smoke passed with no playback or queue residue.
- Music reported ready with 12 hero recommendations and 25 tile items.
- YouTube reported `User is fully logged in` after the bounded migration.

The old Search intermediate-window and Music control-118 assertions were
retired during close-out. Current contract checks follow the semantic Seerr
catalogue route (native window 11132) and the Music hero actions instead of
obsolete pilot focus assumptions. A single subscription-specific YouTube
RSS request returned HTTP 404; this did not invalidate API credentials or login.

## Operator handover

Normal operation is unchanged: start AsterTV, use the side rail to move among
Media, Books, Music, News, Home and Settings, and use the page-specific Search
or YouTube entry. YouTube uses the migrated household sign-in. Books uses the
same shared-household progress model as the lab client.

If a release-wide regression appears, stop Kodi before restoring an on-box
checkpoint. Restore the focused runtime checkpoint for a production-successor
problem; restore the full v1.1.1 checkpoint only for a complete V2 rollback.
Do not copy checkpoint contents off-box or expose the YouTube profile files.
