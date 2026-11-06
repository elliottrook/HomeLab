# AsterTV Platform M7 Jen preflight — 2026-11-05

## Outcome

Jen completed the first compiled-composition migration and recovery rehearsal.
The accepted final composition is
`bccdac5a9e0dd1e5684649cf79d37e1e2f5a9a0714668da34d3556d5aec0eda1`;
its deterministic bundle is `astertv-jen-bccdac5a9e0d.tar.gz`, SHA-256
`1df94e922e44565de65c1b6fe5fce53dc6cf4ed34054e6341ed8439623e44b8b`.
The normalized install tree means migration did not replay historical
installers. Family and Bedroom were not changed.

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

The current verified deterministic Jen artifact is
`astertv-jen-3ac9aaaa87cc.tar.gz`, SHA-256
`1f7cf741887dbd7f1bd5b046450acfe6297adc062cfcae9eb480978965a62b9b`.
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

The second candidate start proved that guard isolation, checkpointing and file
installation were correct, but two superseded Movie/YouTube boot units remained
enabled. They rewrote three account-registry files and one YouTube helper after
the 124-file install, leaving 120 matches and four replacements. The contract
already declares the old units disabled and the composed unit enabled; the
runner simply had not applied or checkpointed typed systemd assertions. The
candidate again remained unaccepted, and the `r2` checkpoint restored all 124
paths, predecessor accepted state, guard enablement and Kodi service.

The runner now checkpoints every declared unit's enablement/activity, applies
only the exact systemd assertions in the guard contract, and restores the prior
unit state during rollback. Its focused assertion test raises the suite to
44/44 before a third attempt.

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
drift, secret output, unavailable required dependency, failed 1080p-media/stereo
preservation, regression or rollback failure. Bedroom and Family remain out of
scope.

Owner clarification during rehearsal: Jen's restriction applies to media
playback, not Kodi's GUI output. The native 3840×2160 GUI is allowed. The
acceptance gate is the Jen-only Jellyfin 1920-pixel/18 Mb/s policy, stereo and
passthrough disabled. The erroneous `display.output=1920x1080` assertion was
removed before any candidate acceptance. That GUI/media correction produced
the intermediate composition
`3ac9aaaa87cc503b83389578b1848df53048e8824ae68aa1e7fc2994b46ed5e3`.
The focused media-versus-GUI contract regression and absent-unit recovery gate
raise the fleet suite to 45/45.

The accepted snapshot later proved that the composition adds six declared
guarded paths, advancing the expected post-migration count from predecessor
528 to 534. That metadata-only arithmetic correction produces the final
composition recorded above.

## Completed rehearsal and recovery evidence

The approved bounded rehearsal used checkpoints
`astertv-platform-m7-jen-20261105-r4` through `r6`. The accepted candidate was
rebooted and then rolled back to its exact predecessor. Kodi recovered active,
stereo and passthrough-off remained unchanged, the composed unit was removed,
and the predecessor's two legacy units returned to their prior state. The
predecessor's known fourteen-file release-guard drift also returned, proving
that rollback restored state rather than silently retaining candidate bytes.

The same immutable payload was then reinstalled and accepted. A final
contract correction changed only metadata: the migration adds six declared
guarded paths to the 528-file predecessor, so the accepted total is 534 rather
than the originally estimated 532. The corrected bundle preflight found all
124 installed payloads matching with zero missing or replacement files before
acceptance.

Final source-local and post-reboot evidence:

- release guard: clean, 534 files, no restored drift;
- composition preflight: 124 matching, zero missing, zero replacement;
- boot writers: composed M4 unit enabled; both superseded M4/M4Y units disabled;
- Kodi: active after both reboot cycles;
- GUI: native 3840x2160 is intentionally allowed;
- media policy: selective, 18,000 kb/s, HEVC direct-play width 1920;
- audio: Kodi channel setting `1` (2.0 stereo), passthrough false;
- representative News MP3: PAPlayer reached `PrepareStream - Ready` after each
  reboot and stopped cleanly; and
- rollback: exact predecessor recovery followed by reinstall of the same
  immutable payload.

The first sanitized Doctor observation contains 124 live hashes/modes, 45 typed
assertions and 12 required dependency states. Jen classifies `clean` with no
payload, metadata, assertion, dependency, identity or composition mismatch.
Fleet Doctor remains `attention` by design because Bedroom and Family have not
yet supplied observations; this does not dilute Jen's result or invent health
for untouched appliances.

This is engineering acceptance, not owner acceptance. Physical navigation and
representative Jellyfin film/television playback on Jen remain an owner check.
