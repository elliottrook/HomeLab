# AsterTV v3 low-spec client handoff

> Complete with sanitized evidence only. Do not include passwords, API keys,
> tokens, private library history, camera images or raw secret-bearing config.

## Identity and immutable baseline

- Client name / address / NetBox IDs:
- Hardware model, CPU, GPU, RAM, storage, network and display chain:
- LibreELEC / Kodi exact versions and build hashes:
- Installed AsterTV release/archive/commit/manifests and hashes:
- Accepted release-guard manifest hash and guarded file count:
- Checkpoints and tested rollback path:

## Measured capability envelope

- Boot time and idle/navigation memory:
- H.264 / HEVC / VP9 / AV1 decode paths and maximum accepted samples:
- 1080p and compressed-4K results; explicitly excluded media classes:
- Audio devices, channel layout, passthrough formats and observed result:
- UI/artwork/navigation latency and temperature/throttle evidence:
- Network path, throughput/latency and persistence after reboot:

## Feature matrix

For Media, TV seasons/episodes, Movies/details/trailers/cast search, YouTube,
Music, eBooks/TTS, Audiobooks, Podcasts, Requests, News, Home, Cameras, Voice,
screensaver and Settings record:

- pass / constrained / fail / not tested;
- exact entry route and physical-remote result;
- backend identity class (name/hash only, never value);
- restart/repeat/Back/focus result;
- observed resource cost and known workaround;
- whether the limitation is hardware, upstream service, current v2 defect or
  test-environment absence.

## Changes made by the handing-off agent

- Local commits and uncommitted paths:
- Live files/services changed, exact hashes and checkpoints:
- Source-service/network/identity changes and their rollback:
- Tests run and exact pass/fail counts:
- Temporary access/artifacts removed or deliberately retained:
- Forgejo/GitHub synchronization state:

## Open limitations and release recommendation

- Must-fix blockers:
- Acceptable low-spec reductions:
- Features that must remain identical across all profiles:
- Recommended `client-capability-profile` values:
- Required retests on Family and Bedroom:
- Next safe action and any required Stream M approval:

## Handoff acceptance gate

The receiving agent must reconcile this report against live read-only evidence,
Git state, the accepted manifest and the project decision register. Conflicts
stop reconciliation; they are not silently resolved. Receipt ends the bounded
pre-handoff Stream A envelope and does not authorize a deployment.
