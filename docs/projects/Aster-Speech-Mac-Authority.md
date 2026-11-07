# Aster speech Mac authority

> **Status:** Pilot — Mac authority live; full OS-reboot recovery proof pending
>
> **Owner:** Jason
>
> **Started:** 2026-11-05
>
> **Authorization:** After listening to the full morning briefing rendered by
> Qwen3-TTS 1.7B on the M4, Jason directed Codex to update the stack and make
> the Mac authoritative. This authorizes the bounded Mac/LXC 128 promotion,
> tests and rollback described here. It does not authorize public ingress,
> broader firewall trust, unrelated Mac administration, model changes, remote
> Git writes, or removal of the accepted Kokoro/faster-whisper rollback.
>
> **Lab Hours exception:** On 2026-11-05, after being informed that the normal
> ledger cannot represent an indefinite always-on execution/recovery window,
> Jason explicitly approved a project-specific exception for this Mac-only
> speech service. The exception is limited to the M4's local Metal GPU, the two
> loopback model servers and their restricted tunnel. It does not cover the
> B60, Arc A380, central inference stack, experiments, batch jobs on another
> host, or any future shared-hardware placement; those remain subject to the
> ordinary ledger, reservation, lease and lock rules.

## Purpose and desired outcome

Make the M4 Mac mini the authoritative compute host for Aster TTS and STT.
Qwen3-TTS 1.7B replaces Kokoro as the selected production narrator because the
full briefing listening comparison was materially better. Whisper remains the
STT family. Existing client URLs, Authentik/API-key checks, Wyoming endpoint and
News identity do not change.

## Current state and evidence

- LXC 128 (`192.168.20.37`) is the authenticated Aster Voice gateway and runs
  Kokoro ONNX plus faster-whisper on CPU.
- The 1.7B Q8 candidate on the M4 rendered a 741.6-second real briefing in
  641.804 seconds (RTF 0.865) with no clipping. Jason preferred it clearly to
  the current briefing.
- The same M4 transcribed 22.48 seconds through whisper.cpp `base.en` in 6.35
  seconds (RTF 0.283) with all words correct.
- The Mac is an M4 with 10 GPU cores and 16 GB unified memory. The combined
  measured TTS/STT footprint has practical headroom, but the Mac has no UPS and
  currently reports automatic restart after power failure disabled.
- Server-VLAN traffic to the Mac client address is blocked. No broader firewall
  rule is needed because a reverse tunnel can originate from the Mac.

## Scope and exclusions

In scope: hash-pinned Mac artifacts; a login-persistent launchd service;
loopback-only Qwen and whisper servers; a key-restricted reverse SSH tunnel;
LXC-side Qwen/STT adapters; production route flip; News and Companion
regression; monitoring, runbook, Beszel/NetBox reconciliation; and rollback
proof.

Excluded: B60/Arc use, public listeners, DNS/NPM changes, a general server-to-
client firewall allow, voice biometrics, third-party speech APIs, deletion of
Kokoro/faster-whisper, automatic fallback that silently changes voice, and any
remote Git write.

## Authority model and architecture

Git plus the accepted artifact manifest own desired engine/build identity.
The Mac launchd service owns live model processes. LXC 128 remains the only
client-facing speech authority and owns authentication, request limits,
scheduling and metrics. NetBox owns device/IP facts. The Lab Hours ledger owns
admission for any scheduled workload covered by repository policy.

`clients -> LXC 128 authenticated API -> 127.0.0.1 reverse forwards -> Mac loopback Qwen/Whisper Metal`

The tunnel is initiated by the Mac using a dedicated restricted SSH identity.
The model servers never bind a LAN address. Interactive and batch TTS continue
through LXC scheduling; Qwen accepts one GPU request at a time. The accepted
seed is `20261104`, language is English and the voice is the synthetic Aster
reference used in the listening test.

## Privacy and security design

Audio and text remain on private hosts and are not retained after requests.
The tunnel private key and existing API keys stay outside Git with restrictive
modes. The LXC SSH key permits only the two reverse loopback forwards. Health
reports model identity but no submitted text/audio. Denied tests cover direct
LAN access, unapproved forwarding, invalid client credentials and over-limit
payloads.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| Mac power, logout or tunnel loss removes primary speech | launchd KeepAlive, SSH keepalive, gateway health, retained one-command LXC rollback | No UPS; FileVault/login can delay recovery after power loss |
| Unified-memory pressure | one Qwen batch, measured 5.57 GB TTS plus ~0.4 GB STT, bounded inputs and health restart | Other heavy Mac work can raise latency |
| Batch briefing starves conversation | existing interactive/batch scheduler and single-unit boundaries; verify latency during a batch | One in-flight utterance cannot be preempted |
| Model or binary drift changes output | exact SHA-256 validation before every start and fixed seed/reference | Upstream updates require a new promotion |
| Tunnel weakens segmentation | loopback-only reverse forwards and a dedicated restricted key; no firewall allow | LXC-local processes can reach forwarded loopback ports |
| Bad promotion interrupts household voice | checkpoint exact live files/env; stage adapters; two production-path passes; route flip last | Brief restart of LXC gateway is required |

No destructive or irreversible operation is planned. Abort on pin mismatch,
unknown host identity, broader network need, failed checkpoint, unhealthy model,
failed denied-path test, insufficient memory, schedule/ledger conflict, or
rollback failure.

## Persistence, milestones and rollback

- [x] M0: record Jason's listening decision, architecture and risk envelope.
- [x] M1: add hash manifest, Mac supervisor/LaunchAgent template and LXC clients.
- [x] M2: install immutable Mac artifacts and credentials; prove restart and
  loopback-only listeners.
- [x] M3: install restricted tunnel identity and stage LXC adapters without
  changing production routing.
- [x] M4: check the complete affected scheduled window in Lab Hours, checkpoint
  production, flip the route, and validate two TTS and STT production passes.
- [ ] M5: prove explicit rollback, restore Qwen authority, reconcile Doctor,
  Beszel, NetBox, wiki/reference/mirror and complete intent/efficiency review.

Rollback stops the Mac route in LXC 128, restores `ASTER_VOICE_RENDERER=onnx`
and local faster-whisper, restarts the gateway and validates health plus real
TTS/STT. The Mac service may then be stopped independently.

## Integration impact

- Doctor/monitoring: add authoritative backend identity, tunnel/model health and
  alert on gateway healthy-but-backend-wrong.
- Beszel: retain the existing Mac system and LXC 128 entries; verify both report.
- Backup: Git owns scripts/manifests; models are reproducible from pinned hashes;
  back up the launchd definition, restricted public key and opaque secret
  custody references. Audio is not backup state.
- NetBox: record the Mac-hosted speech service without changing IP ownership.
- Wiki/reference/mirror: update operating architecture and rollback after live
  validation; the mirror remains derived.
- DNS/certificates/firewall/Homepage: no change.
- Automation/schedules: the News timer remains owned by News. Any changed
  scheduled execution must pass the authoritative Lab Hours window check before
  activation.
- AI administration: no general AI admin API; human break-glass is launchctl on
  the Mac and systemd/env rollback in LXC 128.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-11-05 | Jason accepted the 1.7B full-briefing quality and directed that the Mac become authority. | Promotion decision recorded; prior experiment's no-promotion exclusion is superseded only by this bounded project. |
| 2026-11-05 | Read-only discovery confirmed LXC 128 gateway, blocked server-to-Mac path, loopback-capable upstream APIs, M4 resource headroom and no UPS. | Reverse tunnel selected; no firewall broadening. |
| 2026-11-05 | Added accepted SHA-256 manifest, fail-closed supervisor, voice registration, LaunchAgent template and loopback-only LXC clients. | Local staging complete; no production route changed. |
| 2026-11-05 | Installed the immutable payload in the Mac user Library, created a dedicated LXC 128 tunnel account whose key permits only reverse loopback ports 18140/18141, and ran the supervisor manually. Both model health checks passed through the tunnel; the Mac had no LAN listener; shell access and an unapproved port 18142 forward were denied. Qwen-to-Whisper returned “Aster Speech Authority Validation” after applying the existing Aster hotword prompt. | M2 functional/security staging passed. The manual service was stopped and production remained Kokoro. |
| 2026-11-05 | Attempted to install and enable the user LaunchAgent. The platform rejected the operation before execution because the repository Lab Hours rule requires an authoritative check covering the complete execution/recovery window, while an always-on authority has no finite end. | No LaunchAgent was installed or enabled. Persistent activation and every downstream route/schedule change are blocked until Jason explicitly decides a documented Lab Hours exception or supplies a finite reservation model. |
| 2026-11-05 | Jason explicitly approved the documented project-specific Lab Hours exception after the indefinite-window conflict and residual risk were explained. | Persistent Mac-only activation may proceed. B60, Arc and all other shared-stack work remain governed by normal Lab Hours admission. |
| 2026-11-05 | Enabled the user LaunchAgent, installed a restricted reverse-tunnel identity, checkpointed LXC 128, staged the tested adapters, and selected Qwen/Whisper with a reversible systemd drop-in. Health now reports `qwen3-tts-1.7b-base-q8-metal`, policy `2`, and `whisper.cpp-base.en-metal`. | The Mac is the live authoritative compute host; client URLs and authentication remain unchanged. |
| 2026-11-05 | The first News-path check exposed mismatched 64-character batch-key fingerprints. Reconciled News to the gateway's existing dedicated identity source-to-source with a root-only backup and no secret output. The real News client then returned 24 kHz Qwen audio before and after a Mac service restart. | Existing least-privilege News authentication restored; no new privilege or shared credential introduced. |
| 2026-11-05 | Removed the Mac drop-in, restarted LXC 128 and produced local Kokoro speech; restored the drop-in and completed two authenticated Qwen/Whisper passes. Restarted the Mac LaunchAgent and revalidated gateway plus News batch paths. | Rollback, restoration and service restart recovery passed. The first normal scheduled briefing remains the pilot acceptance gate. |
| 2026-11-05 | Replaced the stale VLAN-70/Kokoro Doctor probe with a current LXC 128 identity-aware check. Canonical health, authenticated Qwen synthesis, Wyoming, HTTPS, JWKS and OIDC all returned `ok`. Updated the Companion runbook, Local AI contract, portfolio and News post-graduation evidence. | Operational monitoring now detects a healthy-but-wrong backend as drift. Beszel/NetBox/mirror reconciliation and the first scheduled briefing remain before graduation. |
| 2026-11-06 | The first evening run exposed a stale lifecycle coupling: the B60 exclusive-session checkpoint stopped the combined News text-and-audio service after text generation, terminating Mac-backed narration even though it no longer competes for B60. Recovered the 17-story recording, then split narration into the independent static `news-aggregator-audio.service`; the B60-backed digest wrapper now queues it asynchronously. | B60 isolation may still quiesce News text generation, but it no longer owns or terminates narration already running on the Mac path. |
| 2026-11-06 | The first normal scheduled Mac/Qwen run completed successfully at 06:24 Pacific: 12 stories, 644.328 seconds, 4,332,284-byte valid 24 kHz mono MP3. Jason reported that the briefing did not work in the player. The page and file were current and byte ranges worked; the player still used stable `latest.mp3`/`latest.vtt` URLs, allowing mobile media-object caching across runs. Added the generation timestamp to both URLs, retained the underlying files, restarted only the UI, and verified a 206 range response whose bytes match the new MP3. | Rendering and publication were healthy; playback cache identity was the defect. Live page now uses a unique media URL per completed briefing. Awaiting Jason's playback acceptance before graduation. |
| 2026-11-06 | A Mac watchdog panic under extreme unified-memory pressure rebooted the host. The LaunchAgent returned, but both model executables failed because their only `LC_RPATH` entries referenced the deleted temporary build tree. Rebuilt the exact accepted Qwen revision `5916bf7c79dbb4e66fc059cdc507a79a23a28bb4` and Whisper `v1.9.5`, preserved the accepted executables apart from replacing their temporary runtime paths, and installed isolated hash-pinned GGML 0.27 and 0.26 library bundles under the durable authority root. Added a fail-closed dependency verifier and complete build provenance. | An unload/bootstrap cold start passed, local Qwen/Whisper health recovered, LXC 128 reported the exact accepted model identities, and canonical synthesis, Wyoming, HTTPS, JWKS and OIDC all passed. Qwen used about 4.8 GiB, Whisper about 0.21 GiB, memory stabilized at 24–29% free and swap remained zero. The pre-change payload is retained at `checkpoints/durable-runtime-20261106-1045`. Jason deferred an actual OS reboot, so reboot persistence is structurally fixed but the final reboot proof remains open. |

