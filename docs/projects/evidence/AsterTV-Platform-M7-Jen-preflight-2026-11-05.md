# AsterTV Platform M7 Jen preflight — 2026-11-05

## Outcome

The first compiled-composition rehearsal is ready but has not changed Jen.
Read-only evidence resolves the exact target, proves the playback gate and
quantifies the owned-file delta. The release artifact now includes a normalized
install tree so migration never needs to replay historical installers.

## Target and safety evidence

- Target: `AsterTV-Jen` at the adopted lab address `192.168.1.180`.
- OS: LibreELEC 13 nightly `20261021-440640e`.
- Kodi: 22.0 RC1 (`21.90.901`), Git
  `01d4146d5d251a0118b99a1de0d713395c93bd46`.
- Kodi service: active/running.
- Playback: JSON-RPC `Player.GetActivePlayers` returned an empty list.
- Release guard: enabled; its last oneshot result is success/status 0.
- Storage: 120,782,556 KiB available on `/storage` (1% used).
- Recovery: `/storage/.aster-checkpoints` and both accepted/current and previous
  release manifests exist. A new rehearsal checkpoint is still mandatory.
- JSON-RPC is loopback-only on port 9090. No credential or private media data
  was queried or recorded.

## Exact desired delta

The Jen guard owns 124 installed payloads. A read-only hash comparison found:

- 98 already match the compiled composition;
- 18 are absent and will be new;
- 8 differ and will be checkpointed replacements; and
- no deletion of unregistered files is proposed.

The differing files are limited to the Home/Cameras display identity/apply
path and the reconciled TV-series presentation/runtime. New files are the
profile keymap, one Music runtime file, the TV v3 extension and visual assets,
and the composed Movie/YouTube boot/runtime tree. This matches the declared
overlay ownership and is not unexplained drift.

The verified deterministic Jen artifact is
`astertv-jen-0da4c6be132e.tar.gz`, SHA-256
`5e39bbc51920d8dc7e24c7dbe38601ff3274d31870dca98fc40810e52730d187`.
An independent repeat build was byte-identical. The bundle includes 124
hash-bound `install/storage/...` members and rejects path escape or duplicate
destinations. Generated binary bundles remain outside Git.

The bounded transaction runner has an offline checkpoint/apply/rollback
fixture. Candidate startup temporarily removes the predecessor guard's boot
edge so it cannot silently revert the candidate; acceptance snapshots the new
guarded state before restoring that edge. Any failed apply restores the
checkpoint and restarts Kodi.

## First rehearsal attempt and recovered guard interaction

The first authorized candidate start exposed a LibreELEC-specific lifecycle
interaction before acceptance: a runtime systemd mask did not prevent the
already-enabled guard from joining Kodi's start transaction. The predecessor
guard restored nine guarded files, so the candidate correctly remained
unaccepted. The transaction checkpoint then restored all 124 declared paths
and both accepted-state directories; Kodi returned active, the guard returned
enabled and the exact preflight delta returned to 77 matches, 17 missing and
30 replacements.

This was a successful stop-and-recovery test, not an accepted deployment. The
runner now removes the persistent guard boot edge and reloads systemd before
candidate startup, then restores that edge during accept or rollback. A focused
command-sequence regression raises the fleet suite to 43/43.

## Authorized rehearsal sequence when approved

1. Reconfirm hostname/build, playback idle and artifact hash.
2. Create a new checkpoint containing every existing owned destination plus an
   absent-path ledger, modes, hashes and the predecessor accepted manifest.
3. Stage and re-hash all 124 install members on Jen without touching live files.
4. Stop only Kodi, atomically replace the 26 changed/absent destinations, run
   `systemctl daemon-reload`, and start Kodi. Mutable account, credential,
   database, cache, history and camera paths remain excluded.
5. Collect the first timestamped sanitized observation and require clean
   payload/dependency/assertion state.
6. Validate startup, focus/navigation, Music, News, Movie/TV playback, Home,
   Cameras, Remote, Guest denial, 1080p output and stereo/no-passthrough.
7. Reboot once and repeat the guard, Doctor and representative playback gates.
8. Rehearse rollback to the new checkpoint, prove service recovery, then
   reinstall the same accepted artifact and collect a final clean observation.

Stop on active playback, identity/build mismatch, checkpoint failure, unknown
drift, secret output, unavailable required dependency, failed 1080p/stereo
preservation, regression or rollback failure. Bedroom and Family remain out of
scope.

## Authorization boundary

Everything recorded here was local or read-only. Creating the checkpoint,
copying the artifact, stopping/restarting Kodi, installing payloads, rebooting,
rolling back or reinstalling is a live Jen mutation and was not performed.
