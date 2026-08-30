# Surveillance Expansion Project

> Status: One-camera baseline complete with trigger configuration; expansion proposed
>
> Project owner: Jason
>
> Last updated: 2026-08-30

## Purpose

Expand the existing Frigate deployment one camera at a time while preserving
camera isolation, recording continuity, usable retention and predictable
compute/storage capacity.

## Authoritative baseline

The operating configuration, streams, retention, NFS ordering, recovery and
troubleshooting procedures are documented in
[`docs/07-Surveillance.md`](../07-Surveillance.md).

The repeatable step-by-step procedure for onboarding each additional camera
(object tracking, zones, alert/detection triggers, staging/validation, known
tooling constraints) is documented in
[`docs/10-Camera-Onboarding-Runbook.md`](../10-Camera-Onboarding-Runbook.md).
Follow it for every camera covered by Milestone 3 below.

- [x] Frigate VM 102 runs at `192.168.20.10` on Servers VLAN 20.
- [x] The Reolink Duo 2V uses `192.168.60.10` on Cameras VLAN 60.
- [x] Frigate alone may reach camera TCP 80, 554 and 8000.
- [x] Recordings use the TrueNAS NFS dataset with reboot-safe mount ordering.
- [x] The Coral Edge TPU is passed through and reports approximately 10 ms
  inference.
- [x] The single-camera baseline is monitored, backed up and restore-capable.

## Scope

- Define coverage, privacy and retention requirements before purchasing cameras.
- Validate capacity before the second camera and after every addition.
- Keep each camera isolated on VLAN 60 with unique credentials.
- Add cameras to Frigate individually and prove recording/detection continuity.
- Add Home Assistant integration, dashboard tools or BirdNET only as bounded
  subprojects with explicit dependencies.

## Out of scope

- Broad camera access to Trusted, Servers or the Internet.
- Moving object detection from the Coral TPU without measured justification.
- Archiving all recordings off-site.
- Adding several cameras in one change window.
- Installing camera-management or AI tools before their security and resource
  requirements are known.

## Milestone 1 — Requirements and site plan

- [ ] List intended camera locations, coverage goals and privacy exclusions.
- [ ] Define required field of view, night performance, audio and weather rating
  for each location.
- [ ] Decide whether each location needs continuous recording, motion recording
  or live view only.
- [ ] Record cabling, PoE budget, switch port and physical mounting requirements.
- [ ] Select the next single camera and verify RTSP/ONVIF/Frigate compatibility.
- [ ] Record household privacy, notification and retention decisions.

Completion gate: the next camera has a justified purpose, supported model,
network path and documented privacy boundary before purchase or installation.

## Milestone 2 — Capacity and architecture checkpoint

- [ ] Measure current Frigate VM CPU/RAM, Coral inference, NFS throughput and
  daily storage growth during representative operation.
- [ ] Reconfirm available Proxmox memory after hardware maintenance.
- [ ] Reconfirm TrueNAS free capacity and estimate growth at the proposed stream
  settings and retention.
- [ ] Verify PoE capacity and the replacement-switch configuration.
- [ ] Decide main/substream resolution, codec, FPS and roles before deployment.
- [ ] Record the maximum camera count supported by the measured envelope.

Completion gate: compute, TPU, network, PoE and storage capacity safely support
one additional camera with documented headroom.

## Milestone 3 — Repeatable camera onboarding

Repeat this milestone separately for every camera. Step-by-step commands and
known tooling constraints are in
[`docs/10-Camera-Onboarding-Runbook.md`](../10-Camera-Onboarding-Runbook.md).

- [ ] Record model, serial, MAC, reserved address, location and switch port.
- [ ] Update firmware and create a unique non-administrator Frigate account where
  the camera supports it.
- [ ] Place the camera on VLAN 60 and confirm it cannot initiate access to other
  internal VLANs or the Internet unless explicitly required.
- [ ] Add only the required Frigate-to-camera ports to the firewall policy.
- [ ] Validate RTSP, ONVIF and management access from the authorized source.
- [ ] Add streams to go2rtc/Frigate without committing credentials to Git.
- [x] Validate detection dimensions, masks, zones and object classes —
  completed for `front_of_house` 2026-08-30: `objects.track` scoped to
  `person`/`car`, `driveway`/`porch`/`street` zones added, `review.alerts`
  scoped to `driveway`/`porch`. Validation also caught and fixed a deeper
  issue: object detection had produced zero events since this camera's
  original install (2026-08-09) — a runtime-only "Enable Detect" toggle that
  doesn't persist without MQTT. Fixed with an explicit `detect.enabled: true`
  in config; confirmed producing correctly-zoned events after a restart. See
  Evidence log and [07-Surveillance.md](../07-Surveillance.md). Still open
  for any future camera onboarded via the runbook above.
- [ ] Confirm live view, continuous/motion recording and event playback.
- [ ] Reboot the camera, Frigate VM and relevant storage path independently.
- [ ] Observe at least 24 hours of healthy recording before another camera.
- [ ] Update backups, monitoring, inventory, diagrams and rollback instructions.

Completion gate: the new camera is isolated, recoverable and stable for the
observation period with no regression to existing cameras.

## Milestone 4 — Home Assistant integration

- [ ] Decide whether camera entities and detection events provide a defined
  automation or notification benefit.
- [ ] If approved, deploy a shared MQTT broker with least-privilege credentials.
- [ ] Connect Frigate and Home Assistant without exposing camera credentials.
- [ ] Add only useful entities and notifications; avoid duplicating Frigate UI.
- [ ] Test broker, Frigate and Home Assistant restarts and failure behaviour.
- [ ] Back up and document the integration and its rollback path.

## Milestone 5 — Optional surveillance tools

- [x] Re-evaluate face recognition and license-plate recognition (LPR) as their
  own scoped, documented decision covering privacy, retention and consent
  before re-enabling. Both were found already enabled outside the documented
  process on 2026-08-30 (undocumented drift, likely from the Frigate setup
  wizard) and were disabled pending this evaluation.

  **Decision (2026-08-30):** re-enabled, deliberately, with the scope
  limitation understood and accepted. Purpose: distinguish known
  family/household members from strangers (face recognition), and recognize
  specific vehicles (LPR). Scope: initially wanted to restrict both to the
  `driveway`/`porch` zones only, excluding the public `street` zone —
  confirmed via Frigate's own documentation that neither feature supports
  zone restriction; both run at the camera level against the full frame.
  A hard privacy boundary (cropping the street out of the detect stream at
  the ffmpeg level, before Frigate ever sees it) was considered and rejected
  in favor of keeping full-frame `street` object detection. Frigate's
  built-in object/motion masks were also considered and rejected as a
  false privacy boundary — confirmed via documentation that object masks
  discard detections *after* the detector has already run, not before, so
  they don't reliably prevent enrichment from processing a masked region.
  **Net effect accepted:** both features process everyone visible in frame,
  including passersby and traffic on the public street with no connection to
  the property, not just driveway/porch. `semantic_search` remains enabled —
  a different feature (embedding-based search, not identity recognition) —
  and was not itself evaluated against this milestone's bar.
  Applied via `config.yaml` (`face_recognition.enabled: true`,
  `lpr.enabled: true`; backup: `config.yaml.before-facelpr-*`), restarted and
  confirmed healthy. Reference photos for known household members were added
  through Frigate's Face Library UI the same day, closing the follow-up.
- [ ] Evaluate BirdNET as a separate service with its own audio, privacy, compute
  and storage design before adding a dashboard card.
- [ ] Select camera-administration tools only after confirming compatibility and
  credential handling.
- [ ] Add Coral status only through a dependable read-only source that does not
  weaken Frigate isolation.
- [ ] Add Homepage cards only after the corresponding services exist and work.
- [ ] Revisit video-decoding acceleration only if measured CPU load justifies it.

## Milestone 6 — Final validation and hand-back

- [ ] Confirm retention cleanup matches the final capacity model.
- [ ] Confirm HomeLab Doctor, Beszel and alerts cover actionable failures.
- [ ] Verify the private Frigate configuration backup and VM archive mirror.
- [ ] Perform a representative configuration or VM restore validation.
- [ ] Update `docs/07-Surveillance.md`, addressing, firewall dependencies and the
  current baseline.
- [ ] Record final accepted risks and safe expansion limit.

## Definition of done

The expansion is complete when each intended camera is individually documented,
isolated, stable and recoverable; storage and compute remain within measured
limits; monitoring and retention work; and optional integrations have their own
validated security and rollback paths.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-16 | Single-camera baseline | Coral TPU, NFS restart and recording validation | Passed |
| 2026-08-30 | Milestone 3 (detection triggers) | `front_of_house` config staged, diffed, YAML-validated, backed up (`config.yaml.before-triggers-20260830-103233`), applied via human-run restart at 10:35:19 PDT; confirmed stable process tree and fresh recordings post-restart with no regression. Face recognition and LPR found already enabled outside the documented process; disabled and deferred to Milestone 5 as a scoped decision. | Passed |
| 2026-08-30 | Milestone 3 (detect.enabled fix) | Discovered `event`/`reviewsegment`/`regions` had zero rows total, back to the database's 2026-08-09 creation — motion detection, recording and the Coral TPU were all confirmed healthy via the debug overlay and system metrics, isolating the fault to a runtime-only "Enable Detect" UI toggle that doesn't persist without MQTT (`mqtt.enabled: false` here). Fixed with explicit `detect.enabled: true` in `config.yaml` (backup: `config.yaml.before-detectenabled-*`), confirmed surviving a restart and producing correctly-labeled, correctly-zoned `person`/`car` events. | Passed |
| 2026-08-30 | Record-stream fragmentation resolved | Root cause: camera's main stream is hardware-capped at a ~2s keyframe interval (confirmed via its native UI — only 1x/2x offered), which Frigate's default `segment_time: 10` couldn't reliably align with under `-c:v copy`. Fixed by setting `segment_time: 2` to match the camera's actual cadence via `ffmpeg.output_args.record`. Confirmed: segments now uniform (~720KB, tight band), and the previously-unplayable clip now plays cleanly. Full write-up: [07-Surveillance.md](../07-Surveillance.md#known-issues). | Passed |
| 2026-08-24 | Project split | Expansion removed from initial-build checklist | Complete |
