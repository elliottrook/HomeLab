# AsterTV v3 promotion and rollback

Status: pre-graduation operator runbook  
Owner: AsterTV Fleet Engineering and Release Review  
Authority: fleet desired state, immutable candidate receipt and target-specific
accepted checkpoints

This runbook promotes the complete AsterTV v3 composition Bedroom first and
Family only after Bedroom acceptance. It does not authorize a deployment,
equipment command, content-volume change, reboot, release, tag or remote write.
Each live boundary still needs the project authorization recorded for that
target.

The committed `generated-release-plans` directory is plan-only evidence. It is
not a deployable payload and must never be copied to a television as if it were
a built release.

## Current candidate

The post-acceptance authority is:

- source reconciliation:
  `services/kodi/astertv-fleet/releases/astertv-v3-m11-post-acceptance-reconciliation-2026-11-06.json`;
- immutable predecessor/amendment chain ending at
  `astertv-v3-rc1-family-content-gateway-candidate-2026-11-06`;
- immutable v2.0.7 base SHA-256
  `e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`;
- Bedroom composition `eab64fd2…9bb3b7` and bundle
  `212ab281…8f7437`; and
- Family composition `a09ef2b5…a79411` and bundle
  `5eb17b3f…1efeed`.

Rebuild and verify the complete hashes from the machine-readable receipt at the
start of every promotion session. A new source commit may reproduce the same
composition bytes, but it does not replace the recorded receipt by implication.

## Hard stop conditions

Stop before mutation if any condition is true:

- target hostname, hardware/peripheral profile, SSH fingerprint or room is
  unknown or disagrees with NetBox/fleet authority;
- playback or a camera viewer is active;
- the display is not available for owner observation;
- the bundle, plan, guard, SBOM or immutable v2 artifact hash differs;
- the target has unexplained drift, a failed release guard or a required
  dependency is unavailable;
- the target-specific checkpoint cannot be created and read back;
- free space is insufficient for bundle, staging and checkpoint;
- a secret, mutable profile/account database or viewing/progress state appears
  inside the bundle;
- the room's audio/display preservation assertions cannot be observed;
- rollback has not been rehearsed for the same runner contract; or
- another room, Home Assistant, Aster, firewall or source service would need an
  unreviewed change.

Do not solve a stop condition by disabling host-key verification, widening a
firewall, copying a credential into Git, borrowing another room's profile or
hand-editing generated desired state.

## 1. Repository and bundle gate

Work from the accepted branch with a clean tree. Compile the fleet and run the
integrated gate:

```sh
python3 services/kodi/astertv-fleet/compile_fleet.py
python3 services/kodi/astertv-v3/m10/validate_local.py
```

Build twice into disposable directories with the immutable v2 artifact
available under `services/kodi/dist`:

```sh
python3 services/kodi/astertv-fleet/build_release_plans.py \
  --output /tmp/astertv-v3-build-1 \
  --artifact-root services/kodi/dist
python3 services/kodi/astertv-fleet/build_release_plans.py \
  --output /tmp/astertv-v3-build-2 \
  --artifact-root services/kodi/dist
```

Require byte-identical bundles and exact agreement with the reconciliation
receipt. Guest must still report `candidate-not-deployable`. Delete disposable
builds after the evidence record is complete; do not commit generated archives.

## 2. Read-only target preflight

Resolve exactly one target. Through the existing strict host-bound identity,
record only sanitized facts:

1. hostname, OS/Kodi build and appliance uptime;
2. zero active Kodi players and no camera viewer;
3. current composition/accepted-manifest status and release-guard result;
4. Kodi/Aster/Remote service state and restart counts;
5. checkpoint root availability and free space;
6. required dependencies and separately custodied mutable state;
7. room audio/display assertions; and
8. the exact bundle/composition hashes selected for that hostname.

For Bedroom, preserve Wi-Fi power-save disablement, stereo PCM, AC3/EAC3
passthrough and every existing account/credential. For Family, preserve HDMI 0,
Dolby/HDR, PulseAudio masking, account state, accepted standby/equipment bridge
and content-volume profile.

The Bedroom content-only rollout is accepted but intentionally narrower than
the full composition. Treat its omitted equipment helper and narrower manifest
as a known expected difference, not as evidence that the complete bundle is
already deployed.

## 3. Checkpoint and candidate apply

Transfer only the target bundle and the reviewed
`apply_composition_bundle.py` runner through the approved private route. Verify
their hashes on the appliance before use.

Run the runner's `preflight` action first. It validates the bundle/guard
contract, hostname and planned matching/missing/replaced files without changing
the appliance.

After a separately authorized live gate, use a unique target/date checkpoint
ID with `apply`. The runner:

- refuses active playback;
- checkpoints every owned destination plus accepted/previous guard state;
- records declared systemd state;
- stages and hash-verifies every payload;
- stops Kodi and removes the guard boot edge;
- installs only declared targets and reconciles only declared systemd
  assertions; and
- restores the checkpoint automatically if apply fails.

A successful `apply` result is `candidate-running`, not accepted. The release
guard deliberately remains unaccepted until validation completes. Do not leave
an unobserved candidate running or reboot it casually.

## 4. Candidate validation

Validate the target while the display is available:

- target hostname and exact installed payload hashes;
- candidate payloads against the bundle guard plus all required dependencies;
  the ordinary accepted-state Doctor may deliberately continue to describe
  the predecessor until the later `accept` action;
- Kodi Home, side rail, top pills, focus, Select and Back;
- Movie details/play/resume, TV season/episode, Music, Books, News, YouTube,
  Requests, Home, Cameras, Settings and Aster screensaver;
- Aster Remote room selection, navigation, search/voice/input and connection
  recovery;
- no unexpected dialogs, white screen, stale queue/recovery latch or page crash;
- no credential, title, input, transcript, frame or viewing-history leak; and
- no regression in the room audio/display contract.

Bedroom must additionally pass the owner-assisted physical equipment and volume
sequence before its complete composition is accepted:

1. capture exact Volume Down, Volume Up, Mute and Power input codes;
2. prove one LG command produces one ARC/eARC SIMPLINK/CEC transition with no
   duplicate step;
3. prove explicit power off/on and physical-remote recovery;
4. select Bedroom-specific content levels rather than reusing Family values;
5. prove bounded ramp, manual override, restart prime, unavailable dependency
   and next-session reset; and
6. confirm playback sound and supported passthrough remain correct.

## 5. Accept, reboot and soak

Only after candidate validation, run the runner's `accept` action with the same
checkpoint ID. It again refuses active playback, snapshots the accepted
host-bound state and restores the guard boot edge.

Then perform the target-specific reboot and normal-use soak:

- guard, Wi-Fi/monitoring and Kodi startup order;
- two complete production-path runs;
- Remote reconnect and last-room behavior;
- screensaver activate/wake;
- Movie, Television, Music, News and one listening path;
- restart counts, memory/temperature and error log;
- preserved account/progress state; and
- Bedroom sound or Family Dolby/HDR as applicable.

Record exact evidence and leave playback stopped at Aster Home.

## 6. Family promotion

Family promotion is a new live decision even after Bedroom passes. Obtain
explicit approval while Family is idle, repeat the complete preflight with the
Family bundle, retain a distinct Family checkpoint and validate the accepted
Family equipment/content-volume behavior in addition to the full page/playback
walkthrough.

Do not copy Bedroom's accepted state, Wi-Fi policy, audio assertions or
checkpoint to Family. Do not copy Family's volume targets, Onkyo mapping,
Dolby/HDR settings or physical key capture to Bedroom.

## Rollback

Rollback uses the original checkpoint ID and the runner's `rollback` action. It
stops Kodi, restores every predecessor file and accepted/previous guard
directory, restores declared systemd state, reenables the release guard and
starts Kodi.

After rollback, verify:

- checkpoint journal status is `rolled-back`;
- predecessor hashes and accepted manifest match;
- Kodi is active and idle at Aster Home;
- target audio/display, Wi-Fi and equipment recovery controls work;
- Remote reconnects;
- Doctor reports the last-known-good composition; and
- no staging file, temporary identity or changed source service remains.

Rollback of AsterTV code must not roll back media datasets, watch/progress data,
Home Assistant databases or another room. If rollback cannot restore the exact
predecessor, stop and use the immutable v2 archive plus the target's retained
recovery checkpoint.

## Completion record

For each target, record:

- authorization and display-idle confirmation;
- source commit, composition, bundle, plan, guard and SBOM hashes;
- checkpoint ID and protected recovery reference;
- preflight diff counts;
- validation and owner observations;
- accepted or rolled-back outcome;
- reboot/soak results;
- Doctor/Beszel/NetBox agreement;
- remaining deviations and expiry/review owner; and
- separately authorized Forgejo push and mirror verification.

The household workflow and recovery summary are in
[AsterTV v3 household guide](AsterTV-v3-User-Guide.md). The fleet authority and
immutable release mechanics are in `services/kodi/astertv-fleet/README.md` and
the private AsterTV wiki Build/Release and Backup/Recovery pages.
