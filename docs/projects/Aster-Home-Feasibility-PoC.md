# Aster Home — EH-001: LibreELEC/Kodi feasibility experiment

> **Status:** Active — Stream A; M0 accepted 2026-10-13; M1 software test authorized
> **Owner:** Jason
> **Date:** 2026-10-13
> **Authorization:** Stream A requested for bounded, reversible proof of concept; operational execution remains subject to the actual environment, project-standard and platform safety gates.
> **Upstream:** `docs/Project-Creation-Standard.md`, `docs/Environment-and-Release-Lifecycle.md`, `AGENTS.md`
> **Primary artefact:** a YES / CONDITIONAL / NO software feasibility decision. Not a commitment to purchase hardware.

## 1. Purpose and desired outcome

Assess whether an **Aster Home** experience built on the integrated **LibreELEC operating system and bundled Kodi media centre** is feasible as a privately operated family audiovisual, music, household-management, intelligence and voice interface. Use existing Jellyfin, TrueNAS, Home Assistant and Aster services, not a parallel service stack.

The first and mandatory end-state is an evidence-backed **USE / CONDITIONAL USE / REJECT LibreELEC/Kodi** decision against household capabilities and costs. **If REJECT, recommend an alternative software trial and do not recommend buying a Kodi appliance.** If USE or CONDITIONAL USE, establish tested minimum, efficient target and premium hardware specifications and a ranked Canadian purchasing recommendation including dated prices, stock, source links, taxes/shipping, accessories, electricity and five-year total cost. **No purchase is authorized.**

The immediate household target is to replace the living-room/family-room Apple TV
with open-source hardware running this software path. The replacement need not
provide Apple streaming apps, Apple services, FaceTime or DRM streaming. It must
prove the household's Jellyfin, music, Home Assistant and Aster experience on
the existing 4K HDR television and 9.2-channel Dolby Atmos/DTS receiver. The
PoC proves a viable foundational path before any hardware recommendation or
purchase.

Long-term Aster Home vision: one private, extensible household interaction plane
across televisions, speaker satellites and mobile devices; replace fragmented
Apple TV/Alexa/smart-home interactions. The PoC proves a viable foundational
path rather than shipping that vision.

## 2. Current state and evidence

The project record was imported from the Jason-authorized GitHub staging branch `aster-home-eh001-feasibility` because no local or Forgejo-main copy existed. Forgejo remains canonical; GitHub is only a staging/handoff channel. M0 live evidence is recorded below and must supersede assumptions from the staging draft.

Repository evidence to reconcile:

- `docs/projects/Aster-Unified-Voice-Service.md`: existing canonical shared Aster voice; **do not build another TTS platform**. The repository standard requires Kokoro `kokoro-v1.0.fp16.onnx`, `bm_daniel`, `en-gb`, speed 0.95 unless a separately evidenced approved exception exists.
- `docs/projects/Pull-Based-Forgejo-Runner.md` and its runbook: completed bounded cloud-agent read and synthetic canary write only; not general project publication.
- Proxmox, Jellyfin/TrueNAS, Home Assistant, Aster brain and house network: inventory exact deployed versions, services, permissions, paths, and current loads from read-only live evidence.
- LibreELEC/Kodi actual release, supported x86 image/firmware, installation and KVM graphics limitations: verify upstream before selecting a test build.
- Physical M2 test device: Jason has nominated a Lenovo ThinkPad X390 Yoga with an
  8th-generation Intel Core i7 and 16 GB RAM. The exact machine type, CPU SKU,
  BIOS version and available display adapter remain to be recorded from the
  device. This is a test device only; no purchase or production reassignment is
  implied.

## 3. Scope and explicit exclusions

**In:** disposable and snapshotted **LibreELEC + Kodi together** in an isolated Proxmox guest; boot/upgrade/system services; Jellyfin media; read-only Home Assistant status/control mocks; Aster AI and canonical voice API integration; Kodi skin and add-on extensibility; network latency, playback, power and endpoint architecture study; decision documentation.

**Not in:** production replacement during the PoC, purchasing hardware before
the software decision, Apple streaming apps/services, DRM streaming, camera or
public feeds, storing microphones/audio/transcripts, exposing public APIs,
uncontrolled home-automation writes, editing or corrupting production media,
new broad VLAN access, bypassing AI-PAM, introducing a new speech platform,
long-lived privileged credentials or deploying a production appliance.

Allowed Stream A operational classes are **only** validated lab VM creation and removal, local snapshot/restore, isolated test code/skins/add-ons, synthetic fixtures, bounded read-only API tests and documented measurements, following read-only M0 and resource/backup check. Material new systems/network permissions or credential changes need a separate risk decision.

## 4. Authority model

| Fact/control | Owner |
| --- | --- |
| Project requirements, choices, evidence | HomeLab project record in Forgejo |
| Deployed guest and service facts | Live systems; NetBox for adopted inventory |
| Aster voice identity | HomeLab Project Creation Standard and Aster Unified Voice project |
| User identity and service authorization | Authentik/AI-PAM policy |
| Media catalogue and watched state | Jellyfin |
| Filesystem/media originals | TrueNAS |
| Home devices | Home Assistant with bounded entity/service policy |
| Derived summaries | Aster mirror (not authority) |
| GitHub | Mirror / explicit temporary handoff branch, not production source of truth |

## 5. Architecture and data flow

```text
Living room client: LibreELEC -> Kodi -> Aster Home skin/add-on
   | video/audio decoded locally; HDMI control on actual hardware
   +-> Jellyfin (catalogue and streaming) -> TrueNAS (media)
   +-> Aster private orchestration/API -> inference on existing Proxmox
   +-> Aster canonical speech service (STT/TTS) / voice capture with consent
   +-> Home Assistant (read-only state initially; narrow, approved commands later)
```

Compare **A: capable local mini-PC** versus **B: cheap, low-power hardware-decoding thin endpoint and Proxmox network brain**. Do **not** confuse thin client with 4K remote-desktop streaming; the local endpoint must decode protected/unprotected video when possible. Map network segments, TLS/authentication, ports and identity to real deployed endpoints only at M0.

### Aster Home presentation feasibility

The target presentation is feasible without changing Kodi core. Build
`skin.asterhome` as a normal skin add-on, with Aster textures, fonts, colours,
focus states, animations, navigation and custom windows. Kodi's skin engine
supports changing the layout and appearance of its standard windows, adding
custom windows, and filling containers from add-ons; that is sufficient for the
mockup's top navigation, hero area, Continue Watching, Recommended, audio
sections and Home Hub cards.

Keep the implementation split into four replaceable layers:

1. **Aster Home skin:** the TV-first visual system shown in the Kodi mockup;
   use fixed 16:9 layouts with resolution scaling rather than attempting to
   make Kodi behave like a responsive phone web app.
2. **Aster Home Kodi service/add-ons:** provide the home screen's aggregated
   items, news digest, podcasts, audiobooks, recommendation explanations and
   controlled actions. Jellyfin remains the media authority; this layer should
   request or display content rather than copy or mutate the media catalogue.
3. **Aster private aggregation/API:** gather read-only Home Assistant state,
   Aster/news/recommendation data and acquisition-request state, with narrow
   identities and explicit action allowlists. Acquisition should be a queued
   request/approval workflow, not an unrestricted download button in a skin.
4. **Home Assistant dashboard:** use a branded dashboard for the browser/tablet
   surface, while the Kodi skin renders a focused TV version of the same state.

The first Kodi Home Hub can therefore show room tiles, routines, climate,
security and air-quality cards like the reference image, but the skin alone
does not create those data sources or safely execute arbitrary house actions.
News, audiobook and podcast tiles are similarly achievable as presentation and
playback surfaces; feed ingestion, metadata normalization, progress sync and
recommendation logic belong in add-ons or the Aster service.

Do not fork Kodi core for the first implementation. A core fork would increase
upgrade and hardware-support risk and is unnecessary for this design. Revisit
that only if testing proves a missing renderer/input/media capability that a
skin, add-on or service cannot supply.

### Branding and licensing boundary

Home Assistant can be branded substantially through supported dashboards:
custom dashboards and views, themes, per-view/per-card themes, entity names and
icons, backgrounds, and custom cards. Aster logos, colours, typography and
tile layouts can reproduce the Home Hub direction. A full replacement of the
Home Assistant application shell would be a frontend fork and should not be
the default plan; custom cards and loaded resources also carry maintenance risk
when internal frontend APIs change.

The Aster skin should have its own repository-owned assets and a clear license.
Kodi's add-on guidance recommends a share-alike Creative Commons license for
skins and requires a license file for distributable add-ons; Kodi core changes
remain under Kodi's GPL-compatible licensing. We may take interaction and
layout inspiration from tvOS and Home Hub, but must not copy Apple's artwork,
logos, fonts or proprietary assets. Any third-party artwork or typeface needs
its own permission and attribution record.

### M3 implementation sequence

Start with a private `skin.asterhome` add-on under `services/kodi/` and validate
it on the existing Mac Kodi test before depending on the physical LibreELEC
endpoint:

1. **M3a — Visual shell:** 1920×1080 Home window, collapsed/revealing left
   rail, Home Hub palette, typography, focus treatment, hero, Continue Watching
   and Recommended rows, using disposable fixture data and repository-owned
   placeholder assets only.
2. **M3b — Jellyfin slice:** replace only the fixture media rows with the
   existing Jellyfin Kodi integration; prove focus, playback, resume and back
   navigation without changing Jellyfin or TrueNAS metadata.
3. **M3c — Home Hub read view:** add a narrow Aster service add-on that exposes
   sanitized Home Assistant state and renders rooms, routines, climate,
   security and air-quality cards; actions remain disabled or mocked initially.
4. **M3d — Personal media and digest:** add podcast, audiobook and news
   containers with a consistent card contract and playback handoff.
5. **M3e — Recommendations and acquisition:** display explanations and request
   actions from Aster's existing recommendation/acquisition services; use an
   explicit queue/approval boundary instead of direct unrestricted downloads.

Each slice must remain usable if the later service is unavailable. The first
implementation milestone is therefore a visual acceptance review, not a broad
integration build.

## 6. Privacy/security design

Local-first; separate low-privilege test identity, minimal read access and synthetic demonstrations; do not store service secrets in Git or agent prompts. No inbound internet exposure. No unrestricted Kodi HTTP/JSON-RPC access on a guest network. Home Assistant state read first; action calls require explicit action allowlist and an intentional human confirmation for safety-sensitive entities. Voice activation opt-in; no retained raw audio or transcripts by default. Existing canonical Aster speech policy applies to all spoken output.

## 7. Pre-start risk assessment

| Risk | Impact | Control / stop |
| --- | --- | --- |
| Proxmox resource/guest conflict | Production outage | Read-only capacity + unique guest ID check, quota, isolated VLAN, snapshot, stop on contention |
| Production metadata/media mutation | Data integrity | read-only credentials/mounts, synthetic catalogue where possible, separate Kodi profile |
| Voice/camera privacy leak | High | explicit microphone consent; no ambient streaming/logging; camera content excluded |
| Automation issues actual house command | High | read-only demonstration; mock actions; approved narrow operations only with separate gate |
| Network lateral movement | High | least-privilege flows, no broadened firewall without fresh approval |
| KVM GPU failure misread as bad software | Wrong decision | separate virtualized UI limits from bare-metal HDMI/decode test; mark unknown until validated |
| Unavailable DRM/streaming app | Product mismatch | hard requirement inventory and hardware/DRM testing; reject if unmet |
| Cloud Git staging diverges from Forgejo | Process / integrity | dedicated branch, no main push, operator reconciliation into Forgejo, hash and diff verification |
| AI-generated patch exceeds approved limits | Privilege escalation | strict scope, signed artifacts, human approval, no arbitrary remote execution |

M0 found no current production contention on the Proxmox host. The documented
household media baseline includes five Apple TVs, a living-room/family-room
Apple TV on the wired Trusted path, a downstairs Apple TV whose current wired
path is not confirmed, and validated Sonos/AirPlay/Home Assistant media paths.
The living-room/family-room endpoint is the primary comparison target. Jason
confirmed that the target TV is 4K with HDR and HDMI-CEC, and the receiver is
9.2-channel with Dolby Atmos and DTS. Dolby Vision is an Apple TV capability,
not a hard Kodi requirement; HDR10 is required. AirPlay is desirable but not
required because the TV and receiver provide it natively. The Home Assistant
direct port assumption is stale: the live VM reports port 80 and version
2026.9.1, while `192.168.20.11:8123` refused a connection.

The lifecycle standard was located in the active local
`Production-Service-Placement-and-Release-Registry` project workspace and
its local release-registry commits (`6a46bc78`, `c6d148d4`), with the expected
path `docs/Environment-and-Release-Lifecycle.md`. The Forgejo
`codex/release-registry-stream-a` ref was checked read-only at
`fc60e5a2c9eac8f311ce8e6c0a83b901fe55600b`; that ref contains the registry
project but not the lifecycle file, and Forgejo `main` also does not contain
it. No remote write was made. The located lifecycle standard and the Project
Creation Standard both govern this project; this branch records the provenance
gap until the lifecycle change is published by its owning project.

M0 is now accepted for the bounded software test. The accepted envelope is a
disposable, snapshotted/backup-covered guest, synthetic or read-only test data,
existing network segmentation, local rollback and no production credential,
firewall/VLAN broadening, or production deployment. Hardware purchasing is
deferred until after the software decision and is not authorized by this
milestone.

**Rollback:** stop/delete only a newly created disposable VM after confirming its exact ID and backup; remove temporary tokens, config and credentials. Never delete the last good copy.

## 8. Persistence and resumability

Record pinned versions, tested guest ID, source commits, upstream image checksum, sanitized configuration and exact test commands in milestone evidence. Save a snapshot prior to changes. On resume, re-read `AGENTS.md`, current standard, this project, Git history and live state; re-verify previous evidence. Store no secrets, raw voice or sensitive content.

## 9. Milestones and gates

- [x] **M0 — Read-only inventory and risk gate:** 2026-10-13 baseline gathered and accepted. Live Proxmox, guest, VLAN, media, HA, Aster, speech and backup evidence is recorded in the evidence log; household capabilities and the bounded software-test envelope are now explicit.
- [x] **M1 — Integrated boot:** 2026-10-13. VM 127 installed LibreELEC 12.2.1 with its bundled Kodi image, booted repeatedly from the installed target, and reached the LibreELEC splash on each clean boot. `std`, `qxl` and `virtio` KVM display profiles produced the same result: Kodi UI did not become visible and the installed guest's `.kodi/temp/kodi.log` remained empty. Gate result: **boot/install passed; KVM UI result inconclusive**. This is a virtualization limitation to carry into physical HDMI testing, not a software rejection; do not substitute Debian+Kodi as the primary test.
- [ ] **M2 — Audiovisual:** Jellyfin library/direct play, music, collections, remote navigation, codecs, subtitles and playback stability. M2 now has a physical endpoint candidate: boot the verified LibreELEC Generic x86_64 image from a disposable USB on the Lenovo X390 Yoga, without installing to or altering its internal drive. Use the X390's Thunderbolt 3/USB-C DisplayPort output with a known 4K60-capable HDMI adapter for the 4K path; its built-in HDMI 1.4b is limited to 4K24 and is not the production-path test. HDMI-CEC is now an optional appliance-integration test, not a software gate; prove a reliable local Bluetooth, IR or USB-HID control path instead. Gate: no media mutation; measurable direct-play, HDR10, audio passthrough, network and navigation results, with hardware limitations explicitly separated from software results.
- [ ] **M3 — Customization:** throwaway Aster-styled Kodi skin/add-on, Home Assistant **read** dashboard, mocked commands and Aster AI query. Gate: prove extensibility and upgrade compatibility without core fork if possible.
- [ ] **M4 — Voice/intelligence:** consume existing Aster voice service with opt-in mic/control, demonstrate speech/turn and timeout/fallback handling without new TTS implementation. Gate: privacy and canonical-voice compliance.
- [ ] **M5 — SOFTWARE GO/NO-GO:** issue `Aster-Home-EH-001-Feasibility-Decision.md` explicitly stating **USE / CONDITIONAL USE / REJECT**, weighted tests plus hard constraints and source-supported alternatives if rejected. **No hardware purchasing study is necessary after REJECT** beyond documenting what alternatives need testing.
- [ ] **M6 — Conditional hardware/pricing:** **only if USE/CONDITIONAL USE**. Compare powerful mini-PC and cheaper local-decoding thin endpoint; measure network/server/client CPU, RAM, codec support, 4K/HDR, control path (Bluetooth/IR/USB-HID and optional HDMI-CEC), audio passthrough, boot/recovery and wattage on available hardware; distinguish measured versus vendor claims. Price at least two viable products **per class** from Canadian retailers, with SKU, dated CAD offers/stock, sources, shipping/tax/accessories, support, 5-year TCO and ranked no-buy/reuse/buy choices. Gate: defensible minimum/efficient/premium specification and a specific recommended purchase or explicit defer.
- [ ] **M7 — Decision, recovery and handover:** reproduce key tests, verify independent rollback, update Doctor/Beszel/NetBox/wiki/operational references as applicable, apply the Aster internal style guide, produce non-technical user guide and final recommendation. No production deployment or order under this experiment.

### M2 physical X390 runbook

1. Record the exact Lenovo machine type, CPU SKU, BIOS version, RAM, internal
   storage health and battery/charger state. Do not update firmware as part of
   this test unless a separate hardware-risk decision is recorded.
2. Verify the pinned LibreELEC 12.2.1 Generic x86_64 image and checksum already
   recorded in this project. Write it to a dedicated USB stick only after the
   user identifies the removable target; never use the X390 internal disk.
3. Boot the X390 from USB through its UEFI boot menu. Preserve the existing OS
   and data as the rollback path. Use a USB keyboard/trackpad for first boot;
   Apple TV remote pairing is a later, separate compatibility test.
4. First test video and audio through the X390 Thunderbolt 3/USB-C display
   output, a confirmed 4K60 HDMI 2.0-capable adapter and the AVR. Record the
   negotiated resolution/refresh rate, TV HDR10 state, AVR input/audio format,
   Kodi dropped frames and buffering. Treat the built-in HDMI port as a
   separate 4K24 control test only.
5. Connect to the existing network without adding a VLAN, firewall rule or
   public route. Sign in manually with the least-privilege Jellyfin test
   identity; do not place credentials in the project record or logs.
6. Install only the Jellyfin Kodi integration needed for the trial, use a
   separate Kodi profile, disable watched-state/library writes initially and
   verify that playback does not mutate production Jellyfin or TrueNAS data.
7. Test Jellyfin direct play and fallback/transcode with representative video,
   HDR10, subtitles, music and the available DTS/Atmos-capable samples. Record
   whether the AVR receives the expected bitstream rather than inferring it
   from Kodi's selection screen.
8. Establish the control/observation path before the stress run. The user must
   physically boot the USB, select the LibreELEC target in UEFI and enable
   LibreELEC SSH from its local Services screen; then provide only the X390's
   LAN address and port, never a password or key. From SSH, collect read-only
   host/Kodi telemetry: version and kernel, CPU/RAM utilisation, thermal
   sensors, network link, Kodi log, DRM/audio messages, dropped-frame and
   buffering evidence, and playback soak snapshots. Keep the physical screen,
   TV HDR indicator and AVR front-panel format as the human-observed evidence;
   SSH is the repeatable measurement/control channel, not a replacement for
   verifying the actual display and receiver.
9. Run bounded real-workload tests rather than an artificial stress test first:
   idle baseline, Kodi navigation, Jellyfin catalogue access, 1080p direct
   play, 4K HEVC/HDR10, subtitles, music, audio passthrough and a 20–30 minute
   mixed playback soak. Escalate to a synthetic stress tool only if these
   results leave a specific capacity question; do not install unrelated tools
   into the test image merely to generate load.
10. Treat HDMI-CEC as optional rather than gating. If the display adapter does
   not expose it, record that as an adapter-path limitation and continue with a
   local control path. Prove the paths in this order: USB keyboard/trackpad for
   baseline; a standard Bluetooth HID remote or controller for pairing,
   reconnect and range; then a USB IR receiver with a standard MCE/RC6 remote
   or FLIRC-style keyboard-emulating receiver. Reuse of an Apple TV remote is
   a separate experiment: older Apple IR remotes may be mappable, while newer
   Siri remotes are Bluetooth devices whose pairing and button mapping must be
   demonstrated rather than assumed. Do not broaden network control or enable
   Kodi's unrestricted HTTP interface merely to obtain a remote.
11. Shut down, remove the USB and verify that the X390 boots its original OS.
   Preserve the LibreELEC USB as the repeatable rollback/test artifact. A
   persistent LibreELEC install or internal-disk replacement is outside this
   runbook and requires a new explicit risk decision.

Checkboxes cannot be marked complete without documented validation.

## 10. Evaluation and acceptance criteria

Predeclare household requirements and their severity (hard requirement vs
desirable). The current M0 requirement set is:

- **Hard:** reliable 4K playback; HDR10; a stable local control path using
  Bluetooth, IR or USB-HID; receiver-compatible Dolby Atmos/DTS passthrough;
  Jellyfin video and music; Home Assistant status and bounded control; Aster AI
  and canonical voice; stable everyday navigation; privacy and recoverability.
- **Desirable:** HDMI-CEC for TV/receiver power, input and remote integration;
  AirPlay through the endpoint, although the TV and receiver already provide it
  natively; reuse of the existing Apple TV remotes over Bluetooth or IR,
  subject to stability and pairing evidence; Dolby Vision; a FaceTime-like
  experience.
- **Not required:** DRM streaming, Apple streaming/apps/services or FaceTime.

Evaluate boot reliability, Kodi UI and customizability, Jellyfin parity, voice
turn delay, Home Assistant scope, network-loss handling, maintenance, remote
usability, privacy and the explicitly non-required DRM/streaming surface.
Separate quantitative thresholds agreed during M0 from unmeasured hypotheses.
A hard capability failure overrides good averaged scores.

Final decision is **USE**, **CONDITIONAL USE with listed blockers**, or **REJECT with alternative software plan**. If accepted, final report MUST contain best efficient hardware, Canadian purchase recommendation and price-source snapshots. No evidence means **inconclusive**, not automatic approval.

## 11. Observability, maintenance and backup

Measure boot/restarts, availability, guest resource usage, API latency, playback drops, network/capture failures, and update side effects. Use sanitized logs and bounded retention. Maintain guest backup/snapshot and isolated restore demonstration. Record Beszel coverage or reason for exclusion, Doctor scope and operator alert ownership.

## 12. Integration impact checklist

At completion report **change or N/A with reason** for: HomeLab Doctor; Beszel/Prometheus/alerting; backup/restore; NetBox VM and VLAN records; human wiki; Aster mirror; operational reference; repository/portfolio/changelog; diagrams/rack; Homepage; Authentik/AI-PAM identity and access broker; DNS/cert/firewall; automation; security inventory. No production changes solely for checklist compliance. Include AI administration posture (`ai-*` narrow identity or documented unsupported).

## 13. Graduation and close-out

Deliver: (1) software go/no-go decision, (2) hardware and live Canadian purchasing report **if** software passes, (3) repeatable experimental test guide and evidence/limitations, (4) bounded successor project proposed only after review, (5) operator-facing handover of UI and failure conditions. Confirm the post-test efficiency review, recovery and no-unintended production-impact evidence. Production graduation is outside this PoC.

## 14. Evidence log

| Date | Action | Result |
| --- | --- | --- |
| 2026-10-13 | Imported/reviewed the Jason-authorized staging project because no local or Forgejo-main copy existed. | Scope preserved; Forgejo remains canonical; no remote write performed. |
| 2026-10-13 | Reviewed `AGENTS.md` and `docs/Project-Creation-Standard.md`; traced `docs/Environment-and-Release-Lifecycle.md` through the active local Production Service Placement and Release Registry project and checked Forgejo refs read-only. | Lifecycle standard found in the owning local project workspace; not yet present in Forgejo `main` or the current Forgejo registry branch ref (`fc60e5a2`). Both standards govern this project; no remote write performed. |
| 2026-10-13 | Read-only Git baseline: detached worktree at `2b5b941e` (`origin/main`), clean status, `origin` is Forgejo HTTPS and `github` is the mirror remote. | No unrelated local changes; no push or remote mutation. |
| 2026-10-13 | Proxmox read-only baseline: `pve-manager/9.2.20`, kernel `7.0.14-23-pve`, 40 logical CPUs (Xeon E5-2698 v4), 78 GiB RAM with about 42 GiB available, local-lvm 24.51% used and backup storage 23.08% used. | Host capacity is presently adequate for a bounded disposable guest, subject to a pre-change resource gate. |
| 2026-10-13 | Enumerated guests: production LXC 100–117/124–126; production VM 102/103; stopped rollback VM 105; stopped disposable fixtures VM 118–123. | Candidate fixtures exist; do not reuse production guests. VM 118/120 configs have no vNIC and serial-only VGA, so they are not yet suitable for a Kodi UI test without a bounded candidate design. |
| 2026-10-13 | Read-only backup listing: fresh archives exist for VMs 118–123 at 00:48 and production HA VM 103 at 00:33; backup filesystem has 2.6 TiB free. | Recovery coverage is present for candidate fixtures and HA; archive integrity still needs a targeted pre-change check before M1. |
| 2026-10-13 | Live VLAN check from Arista: VLANs 1, 10, 20, 30, 40, 50, 60 and 70 active; Proxmox architecture remains Servers/Lab separated. | Existing segmentation is available; no new VLAN/firewall rule is authorized by M0. |
| 2026-10-13 | Read-only service probes: Jellyfin `/health` HTTP 200 at `192.168.20.40:8096`; Aster health HTTP 200 at `192.168.70.10:9120`; Aster Speech health HTTP 200 at `192.168.70.14:9130`; TrueNAS `25.10.5`, Media pool ONLINE with 16.3 TiB free. | Existing media and Aster dependencies respond; no production mutation performed. |
| 2026-10-13 | Home Assistant guest-agent checks: VM 103 network address `192.168.20.11`, guest HTTP port 80, version `2026.9.1`, update available `2026.10.1`; direct TCP 8123 refused, root HTTP 80 returned 200. | HA is live but the project’s direct-port assumption is stale; use the observed access path only after documenting read-only routing. |
| 2026-10-13 | Official upstream review: LibreELEC currently lists 12.2.1; its Generic x86_64 documentation confirms a supported x86_64 image, with GPU-dependent hardware decoding/HDR; Kodi upstream lists 21.3 Omega stable and 22.0 Piers prereleases. | M1 must pin a stable Generic x86_64 image and checksum, record bundled Kodi version, and avoid using a prerelease without a separate decision. KVM can test boot/software behavior but cannot establish physical HDMI, CEC, HDR or receiver compatibility. |
| 2026-10-13 | Read-only endpoint reconciliation: Arista Et17 reports `Family-Room-AppleTV`, connected, VLAN 10, full-duplex 1G, and dynamically learns MAC `c095.6d81.115d`; the two documented Apple TV IP probes did not answer ICMP. | The live switch path confirms the living-room endpoint is on Trusted VLAN 10; ICMP silence is not treated as service failure. No endpoint, VLAN or firewall change performed. |
| 2026-10-13 | Read-only recovery check: representative fresh fixture archives for VMs 118 and 123 passed `zstd -t`; both fixture configs remain stopped, 1 GiB, no-vNIC, serial-only systems. | Backup compression is readable, but these tiny fixtures are not yet an accepted Kodi UI target. |
| 2026-10-13 | Jason confirmed the household target and accepted the bounded software-test envelope. | **M0 accepted.** Primary target is living-room/family-room Apple TV replacement; hard requirements are 4K/HDR10/CEC/Atmos-DTS/Jellyfin/music/HA/Aster/stable navigation; hardware purchase is deferred until after the software decision. M1 may proceed with local rollback and no production/network-policy broadening. |
| 2026-10-13 | Downloaded official LibreELEC Generic x86_64 12.2.1; upstream gzip SHA-256 `85fcac13e046858a142a3161f45771073fa9d3b4a836e5fa4890c4f924a386b8`; local decompressed image SHA-256 `c7bbecf34ac82a1231555773a18c429da0ecf1683248dd4e0293e2ad3a478be5`; host copy matched the gzip hash. | Stable upstream image pinned and verified; no prerelease used. |
| 2026-10-13 | Created disposable Proxmox VM 127 (`aster-home-eh001-m1`): OVMF/q35, 2 vCPU, 2 GiB RAM, 8 GiB target disk, standard virtual display, no production data; installer disk retained only as unused rollback material. | Fresh guest identity avoided all existing S0 fixtures. Final guest is stopped with a single Lab VLAN 70 vNIC protected by the Proxmox VM firewall; no new firewall rule or cross-VLAN path was added. |
| 2026-10-13 | Verified pre-change and post-install checkpoints: `/mnt/backups/dump/vzdump-qemu-127-2026_10_13-11_18_44.vma.zst`, `...11_19_59.vma.zst`, `...11_26_19.vma.zst` and final `...11_30_18.vma.zst`; each selected archive passed remote `zstd -t`. | Local rollback is available; final stopped guest state is preserved for the next bounded milestone. |
| 2026-10-13 | Booted the image installer, installed to `/dev/sdb` (the separate 8 GiB target), detached the installer disk, and clean-booted from the installed target. | LibreELEC installer and installed boot path are repeatable in KVM; target disk has a valid GPT with 1 GiB EFI and 7 GiB Linux partitions, and `.config/boot.status` is `OK`. |
| 2026-10-13 | Captured virtual display evidence at 1280×800; tested `std`, `qxl` and `virtio` display profiles; read the installed guest filesystem read-only after stopping. | All profiles reached the LibreELEC splash but not a visible Kodi UI after extended waits; `.kodi/temp/kodi.log` and `.kodi/temp/kodi.old.log` were zero bytes. KVM cannot establish physical HDMI, CEC, HDR10, Atmos/DTS passthrough or Apple TV remote compatibility. **M1 complete with UI result inconclusive; carry this as a physical-endpoint test requirement.** |
| 2026-10-13 | Read-only Jellyfin checks: `/health` returned `Healthy`; `/System/Info/Public` returned Jellyfin `12.1.0`; representative TrueNAS media roots exposed 1080p VC-1/DTS-HD MA 5.1 remux, 1080p x264/x265/DDP 5.1 episodes and FLAC music. | Jellyfin is a live audiovisual dependency with suitable representative media, but no Kodi client playback or direct-play result is claimed until M2 has a usable UI/endpoint. No media, metadata or Jellyfin state was changed. |
| 2026-10-13 | Reconciled the hardware inventory for an audiovisual endpoint. | No spare HDMI-capable Kodi test endpoint is documented. The Proxmox B60 remains Aster-owned, the TrueNAS Arc A380 remains Jellyfin-owned, and the Lenovo ThinkCentre remains the production NUT host; none may be repurposed under this project. Physical M2 playback remains untested pending an available endpoint or a later, separately accepted hardware decision. |
| 2026-10-13 | Jason nominated the Lenovo ThinkPad X390 Yoga (8th-generation i7, 16 GB RAM) as the physical M2 test device. | The prior endpoint gap is resolved for a reversible USB-boot trial. Exact machine type/CPU/BIOS and adapter availability remain to be captured. No internal-drive install, firmware change, network-policy change or purchase is authorized by this record. |
| 2026-10-13 | Jason clarified that M2 must provide SSH control/observation so the endpoint can be measured under real playback load, not judged only from the TV picture. | The X390 runbook now separates user-required physical actions (USB boot, local SSH enablement, TV/AVR observation) from assistant-run read-only telemetry and bounded playback soak tests. No remote access is enabled by this record; the user must enable SSH locally after boot and provide only the endpoint address. |
| 2026-10-13 | Jason identified HDMI-CEC as unreliable on non-appliance USB-C/DisplayPort hardware and asked to use another control method. | CEC is downgraded from hard requirement to desirable integration. M2 must prove a stable local Bluetooth, IR or USB-HID path; Apple TV remote reuse remains an optional compatibility experiment and no hardware purchase is authorized yet. |
| 2026-10-13 | Jason supplied Aster Home TV and Home Hub reference mockups and asked whether the integrated experience can be built without a Kodi core rewrite or an unmaintainable Home Assistant fork. | Feasibility assessment: the TV presentation is achievable as a Kodi skin plus service/add-ons; Home Assistant branding is achievable through dashboards, themes, backgrounds and custom cards; aggregation, recommendation, acquisition workflow and safe house actions belong in the Aster service layer. Core/frontend forks are deferred unless a measured capability gap remains. |
| 2026-10-14 | Jason approved the Aster Home media-hub visual direction and asked how implementation should begin. | M3 is staged as a private `skin.asterhome` visual shell on Mac Kodi, then Jellyfin, Home Assistant read state, personal media/digest and finally controlled recommendation/acquisition actions. The first gate is visual acceptance with fixture data; no production service mutation or Kodi core fork is planned. |
| 2026-10-14 | Created the initial private `services/kodi/skin.asterhome` M3a source slice: Kodi add-on metadata, 1920×1080 Home window, Aster palette, collapsed/revealing rail, hero and two media containers, plus localized prototype strings. | XML is well-formed and the source is packaged for disposable Mac Kodi testing. The prototype uses Kodi video-library artwork as temporary content and has no production service writes; focus styling and repository-owned logo/textures remain to be validated and refined. |
| 2026-10-14 | Reproduced the Aster selection failure on Mac Kodi and read `/Users/jelliott/Library/Logs/kodi.log`: Kodi found `skin.asterhome` but reverted because the package lacked its standard startup windows and settings templates. Added Aster-owned startup/dialog/settings XML, explicit font definitions, media/font directory placeholders, corrected the conditional rail animation, and validated the 0.1.4 package on the running Kodi test. | M3a activation gate passed: Kodi now stays on `skin.asterhome` and renders the Aster Home ivory/hero/tile shell after restart. Remaining prototype work is visual polish (contrast, icons, tile treatment) and Jellyfin data wiring; no Kodi core or production service change was made. |
| 2026-10-14 | Read-only post-start evidence showed Kodi `21.3`, Jellyfin add-on `2.2.0+py3`, successful Jellyfin authentication/websocket connection and library initialization. The Aster Home rows are backed by the existing Jellyfin-populated Kodi video database paths; no Jellyfin server or media metadata was changed. | M3b foundation passed: the visual shell can consume the existing Jellyfin/Kodi library without a direct server credential or URL in the skin. Playback, resume and navigation acceptance remain part of the physical M2/M3b test rather than being claimed from this startup observation. |
| 2026-10-14 | Prepared the Home Assistant registry candidate offline. Added a dated laundry-only review map using the one alias documented by the operational reference (`light.laundry_laundry_main_lights` → `laundry lights`) and left rooms, timers and media empty. | Registry packaging is ready for review and local contract testing; no VM 103 snapshot, live registry query, HA configuration change, restart or output file was performed. Deployment remains gated on exact live-ID review, recovery checkpoint, `ha core check` and explicit deployment authorization. |
| 2026-10-14 | Added the user-supplied Aster v2 compass SVG as internal brand artwork, rasterized 128 px and 512 px Kodi textures, corrected the skin texture path to `special://skin/`, and restarted the disposable Mac Kodi test. | M3a visual asset gate passed: Aster compass renders in the Kodi header and the skin loads as `skin.asterhome` v0.1.5. Source XML, package integrity and the running Kodi load were validated; the 20 MB source SVG remains outside the add-on and has no embedded licence metadata. |
| 2026-10-14 | Reworked the Mac Kodi visual pass: split the hero into copy and full-art regions, changed media cards to poster-proportioned layouts, added a visible navigation rail and focus surface, and replaced missing prototype localization IDs with explicit labels. | The screen now presents the side menu, hero artwork, Play/More Info actions, Continue Watching and Recommended rows without the prior blank-heading/white-canvas failure. The rail remains visible temporarily; disappearing behavior is deferred until Kodi focus routing is reliable. |
| 2026-10-14 | Completed the M3a interaction pass on disposable Mac Kodi: mapped the rail trigger and menu buttons, added explicit left/up/down/right focus routes, and made the rail animate between its collapsed edge affordance and open menu. | Input acceptance passed: Left opens the rail, Right enters Home Hub, Down moves through menu items with the focus surface, Right returns to content and collapses the rail, and Left reopens it. The visual shell remains fixture/library-backed; no production service or Kodi core change was made. |
| 2026-10-14 | Tightened M3b presentation focus routing on disposable Mac Kodi by adding explicit Down/Up links between the Jellyfin-backed Continue Watching and Recommended rows, plus action-button Down links. | A live library item can be reached from the rail and Down now moves deterministically between both media rows; focused poster artwork remains fully visible. Actual playback, resume, HDR/audio and physical-control acceptance remain gated on the LibreELEC endpoint test. |
| 2026-10-14 | Added the optional empty `Timers.xml` manifest and reloaded the disposable Mac Kodi runtime as `skin.asterhome` v0.1.9. | The Aster skin loads successfully; the prior missing-timer-manifest warning is removed. Remaining log messages are host/Kodi-level media-key accessibility, audio-state and JSON-RPC warnings, not Aster skin load errors. |
| 2026-10-14 | Replaced the hero's fixture-bound title/synopsis/artwork with focus-aware Kodi skin variables that read the selected item from either Jellyfin-backed home row. | Mac Kodi validation passed: moving between rows updates the hero to the selected title, real synopsis, year/duration and matching artwork (for example `227` and `Runner`) without placeholder copy. Playback/resume acceptance remains reserved for the LibreELEC endpoint. |
| 2026-10-14 | Refined the dynamic hero synopsis for the Aster Home visual hierarchy: retained the selected item's live `Plot`, enabled multiline wrapping, added the local `font16` face, and constrained the synopsis surface to two lines. | Disposable Mac Kodi validation passed: the selected `227` item displays its real synopsis across two lines, with year metadata and Play/More Info controls remaining aligned below it. The `0.2.1` package remains a visual-shell milestone; physical playback/HDR/audio acceptance is still reserved for LibreELEC. |
| 2026-10-14 | Reshaped the Aster Home canvas toward the supplied Home Hub reference: reduced the collapsed rail to an icon-first strip, moved the brand/greeting/eyebrow copy left, widened the dynamic hero artwork, converted both media rows to landscape cards, and added Kodi-safe charcoal caption overlays with live `ListItem.PercentPlayed` labels. | Disposable Mac Kodi validation passed: Jellyfin-backed title, synopsis, artwork and metadata still render dynamically while the page now presents the intended rail/hero/card hierarchy. SVG transparency was rejected after Kodi reported unsupported `image/svg`; the shipped overlay is therefore a repository-owned raster PNG with its SVG source retained. The `0.3.0` package remains visual-only pending LibreELEC playback validation. |
| 2026-10-14 | Retrieved the owner-approved private Aster v2 family release from Forgejo, verified package SHA-256 `2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`, and installed only right-sized approved PNG exports in the skin. Replaced the assembled header mark with the approved horizontal logo, changed the collapsed rail to the tile-free compass export, made the hero eyebrow/metadata/time dynamic, removed card zoom in favour of the existing mint focus surface, and used the approved Home Hub/Media marks in the expanded rail. | Source provenance and the v2 adoption boundary are recorded in the skin README. The 0.4.0 source is XML-well-formed and remains a private, visual-only prototype; a full Kodi restart verified the branded expanded rail without label overlap. No SVG master or release ZIP was copied into Git, and LibreELEC playback/HDR/audio acceptance is still pending. |
| 2026-10-14 | Reworked the M3a composition around the approved media-hub render: the selected hero artwork now fills the upper canvas, the logo/copy/actions sit on a translucent approved-texture panel, and both media queues have layered module surfaces, card backplates and full-card mint focus plates. | Static XML validation passed and all changes remain confined to the private skin source. The visual gate still requires a refreshed Mac Kodi preview to inspect stretched texture treatment and hover states; no production service, Kodi core or LibreELEC endpoint change was made. |
| 2026-10-14 | Corrected the M3a queue and navigation composition after live Mac Kodi inspection: removed stretched rail textures from the queues, restored native-size charcoal caption boxes and mint focus surfaces, fixed the expanded rail z-order/icon spacing, and hid the media rows while the navigation mode is open. | Disposable Mac Kodi validation passed in both collapsed and expanded rail states, including focus movement between both media rows. XML and whitespace checks pass; the private skin is now v0.5.1. No production service, Kodi core or LibreELEC endpoint change was made. |

Artwork-size follow-up, 2026-10-14: compared Jason's Jellyfin HEIC reference
with Aster's running skin. The small visible artwork resulted from five
320×180 cards, portrait thumbnails cropped into landscape frames, and caption
boxes covering the lower image. Version 0.5.2 uses four 400×225 cards, prefers
landscape artwork with fanart/thumbnail fallbacks, and moves caption boxes
below the artwork. The hero height is reduced to 420px to fit both rows.
Live Mac Kodi checks verified matching landscape art, both rows, horizontal
scrolling, dynamic hero changes, and expanded navigation. XML and diff checks
passed. This is a local visual milestone; physical playback evidence remains
pending.

Visual follow-up, 2026-10-14 (v0.5.3): preserve full hero artwork using a fitted
right-hand image over a subdued backdrop, simplify repeated hero metadata to
the year, remove caption boxes, use black/ink captions, add rounded media and
panel corners, and replace percentage labels with resume bars. Brand artwork
is preserved; geometric masks are generated by the skin's reproducible
`tools/build_surfaces.py` script. Mac Kodi visual checks covered rounded
artwork and focus, fitted hero changes, empty bars, and filled bars with real
movie bookmarks (including Harry Potter at approximately 21%). The temporary
movie playlist was removed from the runtime configuration after verification.
The normal show-level TV row reports zero PercentPlayed, so its empty tracks
are accurate for that source; episode-level Continue Watching remains a data
integration follow-up. XML and diff validation pass.

Visual and resume-row follow-up, 2026-10-14 (v0.5.4): replaced the duplicate
hero backdrop/inset with one 1680×400 tile split into a solid charcoal half
and an artwork half. Kept rounded outside corners with a square centre join,
moved the year immediately after the genre in sage green, and restored square
side rails. Continue Watching now reads a packaged in-progress episode smart
playlist sorted by last played; captions append actual season and episode
numbers, the hero names the series, and its plot is episode-specific. Mac Kodi
displayed `Dark — S1 E4`, `The Newsroom — S1 E1`, `The Durrells — S1 E1`, and
`The Voice — S30 E3` with real resume bars. Expanded navigation hides the hero
surfaces to prevent overlap. Row opacity transitions preserve focusability;
the expanded-menu → Right → media-row round trip passed in live Kodi.
XML validation and `git diff --check` pass. No playback or library state was
modified. Remote synchronization remains pending explicit push approval.

Clock-pill refinement, 2026-10-14: reduced the hero clock surface to 150×44,
removed the decorative status dot, centred the time horizontally and vertically,
and inset the pill 24 skin pixels from the artwork's top and right edges.
Deployed to the Mac test skin and verified visually in live Kodi; XML validation
passes. This is a local-only milestone; remote synchronization remains pending.

Full-bleed hero trial, 2026-10-14 (v0.5.5): replaced the split tile with
1920×1080 artwork, a continuous left readability gradient and an ivory lower
fade behind the queues. Removed the bounded copy panel. Rounded green Play
and ivory More Info buttons now have sage selected fills and white focus rings;
Up from Continue Watching reaches Play, Right reaches More Info, Down returns.
Live Kodi visual checks passed for both focused buttons and the full-width
image; the corrected fade sits below navigation so the square rail is preserved.
Existing brand artwork and library/playback state remain unchanged. XML and
diff validation pass. Local commit only; remote synchronization is pending.
The split-hero design remains recoverable from local commit `529cc07d`.

Tile-corner correction, 2026-10-14: fixed artwork alpha masks to each 400×225
tile using Kodi's `scalediffuse="false"` attribute, and removed ivory inverse
corner overlays. Source-art cropping no longer crops the mask; the real hero
background shows through rounded corners. Applied to both rows, focused and
unfocused layouts. Live Kodi checks showed clean corners on Dark, The Newsroom,
The Durrells and the movie row, with resume bars and focus ring retained.
XML and diff checks pass. Remote synchronization remains pending approval.
Reference: https://kodi.wiki/view/Aspect_Ratio

Category-lane milestone, 2026-10-14 (v0.5.6): added TV Shows, Movies, Archive TV,
Archive Film and Collections as 280×56 pills in a distinct translucent lane.
Moved Continue Watching down 74 skin pixels; reduced cards to 320×180 to keep
five cards and both queues on screen, with properly fixed rounded masks.
Added the previously missing MyVideoNav tile browser. A clean Kodi restart was
needed to register the new native window; the initial missing-window/empty-view
failure was resolved. Reserved native control ID 2 is not used for Back.
Live category checks returned 66 Shows-tagged series, 71 Movies-tagged films,
135 Archive TV series, 976 Archive Movies films, and 123 nonempty movie sets.
Collections displays Kodi movie sets; it does not claim parity with arbitrary
Jellyfin collections. Keyboard lane focus and Escape return were verified;
no media playback, tags or server-side library contents were changed.
XML/diff validation passes. Existing approved branding is reused; neutral
compact masks are geometric UI assets. Side-rail utility glyph redesign remains
a separate visual follow-up. Local commit only; remote synchronization pending.
Reference: https://kodi.wiki/view/Smart_playlists/Rules_and_groupings

Header and portrait-browser milestone, 2026-10-14 (v0.5.7): moved the five
category pills into the header, away from Play/More Info, with 248×56 controls
and approved 128px TV/Film/Archive exports. The owner-supplied
`19-movie-collections.svg` was rendered directly to a 128px transparent PNG;
the source was not altered or recreated. Provenance, rendering recipe and hashes
are recorded in the skin's `media/category-icons-provenance.json`. The approved
family package SHA256 is
`2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`;
Collections source SHA256 is
`3f89124d6314320a56368b3f208efce9baf293f899c466e8f113cb5164598fcd`.

The native video browser now uses full-screen selected-media fanart, rounded
2:3 posters with two-line captions, and a separate left-hand search/filter lane.
Posters use existing library artwork (many already contain title graphics),
without promising title-bearing art for every item or changing server images.
Live Mac Kodi checks verified all header labels fit, portrait corners and wrapped
captions, dynamic hero metadata, native title filtering (TV: 66 → 2 for Dark →
66 after clearing), and reversible movie sort order. Added and visually checked
the Aster native on-screen keyboard; special keys fit inside its panel. Temporary
filter input was cleared, restoring all 71 Movies-tagged titles. Added a matching
media-details dialog and verified real poster/fanart/synopsis for Minions and
A Clockwork Orange. The browser More Info action initially failed with button
focus; returning focus to control 50 before Action(Info) resolved it and the
button was verified live. Parent-folder tiles now explicitly say Back.

Four offline geometry/asset tests, all skin XML validation and diff whitespace
checks pass. No core changes, service deployment, media playback, server library
or artwork writes occurred. Collections remains Kodi movie sets as documented
above. Local milestone only; remote synchronization requires fresh approval.

Hero balance and genre/score milestone, 2026-10-14 (v0.5.8): centred the home
hero block at skin y296 within the y100–492 lane; moved copy/actions together
35px, kept the synopsis to two visible lines, and enlarged the existing approved
logo within the header slot without recreating it. Category headers now use the
approved TV, Film, Archive TV, Archive Film or Collections icon as appropriate.
Read-only immutable SQLite inspection found default numeric scores for 1,047
movies, 201 series and 5,955 episodes. Added labelled `/10` scores and available
age classifications to home/category heroes, without claiming a specific rating
provider or substituting personal scores. Live home checks showed Reacher 8.1/10
and CA-18+, and The Newsroom 7.7/10 and TV-MA, with no overlap.

Added local genre-fragment and minimum-score controls for the four tagged
category roots. The Python helper composes Kodi smart-playlist rules, always
retaining the original category tag and AND semantics. Its only writes are
atomic, bounded generated XSP view files in the skin's profile addon_data;
no library metadata, media files, playback history, server, network or credentials
are touched. Existing prototype authorization covers this reversible local view
change. Added the standard Kodi Python dependency; no new service, speech,
network exposure, inventory, monitoring or identity integration is introduced.
Collections and nested season/episode lists deliberately do not offer these
category-root filters. Back/Escape remains available; rollback is `a58b2d77`.

Live validation: Movies 71 → Drama 22 → Drama with score ≥8: 6 → Clear: 71.
TV Shows 66 → score ≥8: 25 → Clear: 66. Active Genre/Score labels, native
keyboard prompts, TV/Film header icons, hero balance and final two-line synopsis
were visually checked after restart. Nine offline layout/filter tests cover
geometry, assets, category scope, XML escaping, inclusive rating boundary and
unknown-category rejection; XML/diff checks pass. Operator instructions are in
the skin README. Remote synchronization remains pending fresh approval.
Rule reference: https://kodi.wiki/view/Smart_playlists/Rules_and_groupings

### M3a hub navigation and destination pages — 2026-10-14

The private Kodi skin v0.6.0 now has a shared rail with Aster Media, Books,
Daily Digest, Aster Home, Music and Settings. Four custom 1080p pages reuse the
approved v2 logo, palette and application marks. The visual shell, focus routes
and return to the existing Media home were checked in the disposable Mac Kodi
installation. The hero assets are direct 512 px exports from the approved
`aster-brand-v2-2026-10-14` package; hashes are in the skin provenance manifest.
No artwork was redrawn and no Kodi core change was made.

The Music page read 25 real albums and covers through Kodi's local music
library. The **Play newest** action queried the first album's 15 songs, built
Kodi's audio playlist, and started its first track; the Jellyfin/Kodi playback
log confirmed an audio stream. The short manual test was stopped. That playback
changed the selected track's normal Jellyfin play history, as expected for a
real play test. Album rows are currently browsing only, with per-row playback
still open. Digest showed 21 fresh published chapters from the existing private
news service, and its **Listen** action opened the published MP3 decoder.
Per-chapter list activation has not passed an end-to-end check. The skin
performs no speech synthesis; it consumes the existing canonical-voice
recording. Invalid/stale metadata fails closed, and an already-open page checks
its generation time again before playback.

Books and Home pages display explicit read-only connection states for
Calibre-Web, Audiobookshelf, Home Assistant and Aster. They do not present fake
device values, access personal libraries, or enable household actions. The next
data milestone needs an agreed least-privilege, read-only identity and data
contract for those sources. It is not implied by this UI work. The release
lifecycle document referenced elsewhere in this project's history was not
present in the current checkout or sibling knowledge repositories; no release
promotion is claimed. This remains a local test add-on pending owner review and
fresh permission for any Forgejo push. Roll back to `d4b6944b` if needed.

### M3a Books/Home read-only feed preparation — 2026-10-14

The existing unified-media refresher writes a sanitized `library.json` that
includes Audiobookshelf titles, but the portal currently serves recommendations
and search, not that library snapshot. Its port 8787 is bound on the TrueNAS
LAN interface, so publishing the whole library through the portal without a
separate access decision would broaden personal-metadata exposure. Calibre
records are supported by its offline collector contract but are not confirmed
in the deployed library snapshot. The offline Home Assistant registry exporter
is disabled by default, records only reviewed aliases/presence, has no
timestamp envelope or HTTP route, and cannot supply the mockup's live
temperature, security or air-quality values. This is an evidence gap, not a
reason to display invented values.

Skin v0.6.1 now has bounded, opt-in local JSON readers for those existing
sanitized contracts. Files live only in the disposable Kodi profile's
`addon_data/skin.asterhome/feeds/` directory, are never created by the skin,
and fail closed if stale, malformed, oversized or absent. Synthetic tests cover
authority filtering, deduplication, stale data, alias-only Home display and
symlink/size rejection. No real feed was copied to Kodi, no service was
modified, and neither household actions nor acquisition requests are enabled.
The next gate is an explicitly reviewed protected publisher/delivery path,
followed by a separate live-state contract and exact Home Assistant entity
review. Do not repurpose the portal's unauthenticated LAN route or deploy the
offline HA integration without the project risk/rollback checks. This local
milestone follows `7bf22a7e`; no Forgejo push or release promotion occurred.

### M3a Books one-shot Mac pilot — 2026-10-14

Read-only SSH resolved the TrueNAS unified-media portal's `/data` mount to
`/mnt/Media/appdata/unified-media-shadow/portal-refresh`. The deployed
`library.json` was 2.3 MB and contained 46 `audiobookshelf/audiobook` records
and zero `calibre/ebook` records at the observed check. A manual pilot script
queries only those two authority/type pairs, projects only the four safe
fields on TrueNAS with `jq`, uses the source file's mtime as the envelope
timestamp, and atomically installs a mode-0600 feed in the disposable Mac Kodi
profile. No raw library snapshot, service credential or personal title was
committed. No TrueNAS, Home Assistant, firewall or portal configuration was
changed. This is a one-shot test, not a scheduled synchronization path.

Mac Kodi was restarted with skin v0.6.2. Visual inspection confirmed the
Books page shows `46 library titles · read-only snapshot` and the actual
audiobook rows. The About library control was corrected to distinguish an
available catalogue from unavailable playback/ebook connections. The local
feed expires after 24 hours; Refresh only reloads that file. Home remains
unconnected because the offline registry exporter has not been deployed and
does not provide live room/device values. A protected, recoverable publisher
and reviewed HA state contract are still required before either feed becomes
an unattended or production feature. No remote Git operation occurred.

### M3c Home Assistant read-only inventory gate — 2026-10-14

With VM 103 running, a direct read-only Proxmox guest-agent query inspected
only the entity IDs in Home Assistant's local registry. It counted 33 light,
22 switch, 115 sensor and 20 binary-sensor entries. Of the sensor IDs, three
contained `temperature`: hall, Jason's closet, and outside. None of the
sensor/binary-sensor IDs contained `humidity`, `air_quality`, `co2` or `aqi`.
This is an ID/name inventory, not a live state or hardware capability audit;
no entity values, secrets or full registry document were read into this task.
The existing exporter accepts light/switch, timer and media-player aliases
only; extending it to comfort readings needs a separate reviewed contract.

Proposed next pilot: an exact owner-reviewed allowlist of a few household
lights and, if desired, the hall and outside temperature sensors. Export only
sanitized aliases and bounded read-only values with a short validity window;
keep control and security/air-quality cards disabled. Before any VM 103 write,
take a recovery checkpoint, confirm current guest version/backup health,
review the exact allowlist and exporter code, then validate HA configuration
and rollback. Deployment and any data-delivery path need explicit
authorization; this inventory check granted neither.

### M3c Home pilot offline contract — 2026-10-14

Jason selected the laundry light and hall/outside temperature sensors for a
read-only pilot. The three exact entity IDs were present and enabled in the
live VM 103 registry at read-only inspection. Current values and units were
not inspected. The local exporter contract is now v2: it emits reviewed light
on/off and finite, bounded temperature values with °C/°F units. Missing,
unavailable, unknown or out-of-range readings are omitted, and a switch is
never labelled as a light. The Kodi Home reader accepts legacy alias-only v1
and v2 values, marks the two cases distinctly, and keeps controls disabled.
The skin source is v0.6.3; no HA integration/configuration or Home feed has
been installed. The deployment gate in
`services/home-assistant/aster_registry/REGISTRY-REVIEW.md` remains open,
including recovery checkpoint, exact source-local state/unit check,
`ha core check`, protected feed delivery, validation and rollback. No remote
Git operation occurred.

Subsequent pre-deployment read-only discovery corrected the offline-state
assumption above: VM 103 already runs the schema-v1 `aster_registry` custom
integration and has an active configuration block for the laundry light. Its
mode-0600 report is being refreshed and contains only the reviewed alias.
The deployed component hashes match the earlier v1 source/manifest, not the
new local v2 source; the existing Proxmox snapshot is
`aster-registry-pre-20261010`. The report is the Aster adaptive-computing
no-effect recording pilot's established source. That consumer's
`ProviderRegistrySnapshot` explicitly requires schema v1. Overwriting the
same component/output with v2 would be a material shared-contract change, so
the authorized deployment sequence was stopped before a fresh snapshot,
file copy, configuration edit or restart. The safe proposed route is a
separate Aster Home output/component that leaves v1 untouched, or a separately
reviewed consumer migration. The choice and its recovery plan need Jason's
approval before any VM 103 mutation. No remote Git operation occurred.

Books is a separate integration gap, not an empty design page. The one-shot
Mac test displayed 46 actual Audiobookshelf titles from the existing sanitized
unified-media snapshot. That snapshot contained no `calibre/ebook` records,
although the operational reference documents a separate Calibre library with
`metadata.db`. Its desktop Calibre deployment has no REST API and Kavita is
not deployed. Ebook catalogue support needs a deliberate read-only source
choice: a guarded `metadata.db` projection or a separately scoped reader
service. Audiobook *playback* also needs an authenticated, least-privilege
media route and a Kodi playback adapter; title/authority ID alone cannot open
audio. Continue-listening and resume are additional personal-state writes,
outside the current read-only snapshot. None of these gaps should be
represented by invented titles or a falsely working Play button.

### M3c isolated Home exporter preflight — 2026-10-14

After Jason approved an isolated sidecar, prepared
`services/home-assistant/aster_home_registry` locally under a distinct HA
domain and `/share/aster-home-registry/latest.json`. Its exact in-code allowlist
contains only the Laundry light and hall/outside temperatures. Local contract
tests pass, and the existing schema-v1 component/report are unchanged.
Read-only Recorder inspection on VM 103 found the latest Laundry light state
`on`, and both temperature entities `unavailable`, with recent history also
unavailable. Both sensors have valid Celsius units; this is a source-data
problem, not a unit mismatch. The sidecar would fail closed and show only the
light. Jason then approved using the available closet temperature as an
interim private-room reading. The exact allowlist was expanded to that sensor;
unavailable hall/outside readings remain fail-closed. No VM 103 or remote Git
write occurred in the initial preflight.

Camera expansion was separately requested. The original PoC excluded camera
content due to privacy risk. Read-only inventory found no Home Assistant
camera entities; Frigate VM 102 has one active `front_of_house` camera (5.1
camera FPS at observation). Its authenticated UI listens on 8971 and its
local API on 127.0.0.1:5000; another port-5000 listener exists on the VM's
Servers address. The initial Aster Home expansion is limited to a source/status
entry pointing the user to the authenticated Frigate app, without frames,
recordings, credentials, public ingress or a new Kodi camera stream. A live
preview requires separate access-path, privacy and failure-mode review before
implementation. No Frigate, firewall or HA camera integration was changed.

### M3c Home pilot deployment and Mac acceptance — 2026-10-14

Before writing VM 103, confirmed all four exact allowlisted entities present
and enabled, the sidecar domain/path absent, existing v1 output healthy, VM
running and local-lvm 25.43% used. Created Proxmox snapshot
`aster-home-pre-20261014` and a private mode-0600 copy of the HA YAML at
`/config/configuration.yaml.before-aster-home-20261014`. The Proxmox snapshot
emitted its known thin-pool overcommit warning; actual pool use was unchanged.
Copied only `aster_home_registry` files, verified all three SHA-256 hashes
against Git working source, appended only `aster_home_registry: {}`, passed
`ha core check`, and restarted Core only. The restart completed successfully,
HA HTTP returned 200, and the only integration-specific log line was HA's
generic custom-integration warning. Post-restart `ha core check` passed.

The new mode-0600 v2 report showed Laundry `on`, closet 16.6 °C and no
unavailable Hue values. The old mode-0600 v1 report retained its schema,
snapshot ID and Laundry alias. Both report mtimes advanced again at their
five-minute refresh. No household action or deliberate state transition was
made; event-trigger behavior is not claimed from this evidence. A manual
source-local projection of Frigate stats added only `front_of_house`
online/offline status, never imagery or credentials, to a ten-minute Mac Kodi
feed. The feed is mode 0600 and expires closed. Kodi skin v0.6.4 visibly
rendered the Laundry light, closet temperature and Front of house camera
status. The camera row is informational; Kodi does not open Frigate or a live
stream. The UI Refresh button reloads the local file only; rerun the manual
pilot script for a new source read.

Recovery remains checkpoint plus file-level removal of only the sidecar/YAML
key/output, followed by config check and Core-only restart. That rollback is
documented but not destructively rehearsed against production. No new VM,
network rule, credential, DNS, NetBox object, Beszel agent or HomeLab Doctor
check was created; those integrations are not authoritative for the manual
ten-minute Mac test. A persistent publisher or live camera integration would
need separate identity, monitoring, recovery and privacy review. No Forgejo
push or release promotion occurred.

### M3d limestone surface trial — 2026-10-14

Kodi skin v0.6.5 derives a subdued 280×56 rounded surface from the approved
Aster v2 core SVG's limestone layer, preserving its mineral detail without
redrawing the identity asset. The exact private release archive and SVG hashes
are checked before generation; the source archive stays outside Git. Unfocused
category/filter/secondary pills and small clock pills use the new texture;
solid sage focus and green primary controls remain unchanged. Mac Kodi was
restarted and the media-home render verified: rounded edges, text legibility
and material appearance held at the test window size. This is a local visual
trial, not LibreELEC or television acceptance. No remote push or service
change was made.

Skin v0.6.6 extends that material to the search/filter heading and replaces
the expanded rail's empty ivory backdrop with the selected hero artwork under
a dark readability layer. The normal hero copy and queues still hide while
the menu has focus. Mac Kodi visual inspection confirmed the full-height
artwork treatment with an expanded rail; offline layout tests cover the
conditional layers and filter surface. This remains a disposable Mac visual
test; no LibreELEC/TV playback or control capability is inferred.

Clock refinement, 2026-10-15 (v0.6.7): Jason rejected the stone clock. The
media and hub pages now use a dark translucent clock inset with a thin warm
outline, while category and filter controls retain limestone. Kodi's
`System.Time(HH:mm)` did not override the Mac profile's regional 12-hour
setting by itself; the test profile's `locale.use24hourclock` was changed from
`regional` to `24hours` through Kodi's local JSON-RPC settings API. The Mac
screen then showed `00:04` after midnight. Set the same per-profile Kodi
regional preference during LibreELEC setup; this is not a skin-bundled global
setting and has not been tested on the physical endpoint.

Hero-fade refinement, 2026-10-15 (v0.6.8): the Home, browse and video-info
hero gradients now resolve into a warm solid stone colour rather than ivory.
The Home canvas uses the same colour to avoid an edge at the lower media rows;
no limestone texture was added to the fade. Mac Kodi's media home was restarted
and visually checked with real Jellyfin artwork. This remains a local visual
trial only; no Forgejo push or physical-endpoint validation occurred.

Brand expansion import, 2026-10-15 (v0.6.9): retrieved the private immutable
`aster-brand-v2-expansion-2026-10-14` Forgejo release using existing local
credentials. Confirmed ZIP size 240,062,428 bytes and SHA-256
`e030b6104fbdffb44faf035471f8c55320c3869065046a1ff5f9f0433069c48e`,
then passed CRC and all 173 listed entry hashes. Imported 128px launcher/music
symbols and 512px product logos without redrawing them. Rail states now use
the Books, Music and Settings launcher marks; Media/Books/Music/Digest headers
use their matching stacked marks. Existing original-family marks remain where
the expansion supplies no replacement. Podcast and artist/song/playlist marks
are retained for future functional destinations, not linked prematurely.
Mac Kodi visual checks covered the expanded rail, Media landing and Books
page; no LibreELEC endpoint test, new integration, Forgejo push or release
promotion occurred. Previous 0.6.8 markup and exports remain recoverable in
Git; the disposable Mac add-on can be restored from that revision.

Kodi startup branding, 2026-10-15: Jason requested that the Kodi startup logo
be replaced with Aster Home. A separate 1920 × 1080 profile-level splash was
generated from the SHA-verified original-family 1254px Aster Home PNG, without
redrawing the logo or altering the Kodi application bundle. The Mac profile
had no existing splash override; `media/splash.png` was installed there and
Kodi was restarted. The profile file matches the versioned asset. Startup was
too fast to capture the transient splash in the UI check, so live visual
acceptance remains open. This does not change LibreELEC's earlier OS boot
screen or establish physical-device acceptance. Remove only the profile
override to revert; the bundled Kodi image was not overwritten.

Mac Kodi Dock icon, 2026-10-15: Jason confirmed this is the remaining icon
request, separate from the startup splash. The existing approved 512px Aster
compass icon with stone surround was converted to `kodi.icns` and installed in
the disposable `/tmp/Kodi-test.app` only. The prior `kodi.icns` was saved as
`/tmp/Kodi-test.original-kodi.icns` (SHA-256
`1973648d0af3c21f2dddfdccae8fbdb6034ce23ee5759e2a564a41ef2ae0500b`).
Finder visibly showed the Aster icon on the test app, and Kodi remained open
with the Aster skin. The Dock initially retained its old cached image despite
the correct saved app path. Restarting only Dock refreshed it, and Jason
confirmed the live Dock now shows the Aster icon. The repeatable installer
includes that refresh and rollback is documented in the skin README. The
production app, LibreELEC endpoint and startup splash are unchanged.

Music visual milestone, 2026-10-15 (skin v0.7.1): replaced the old vertical
Music list with a recent-albums tile landing and Album, Artist, Song and saved
Playlist browse pages. The five pages share a full-width fanart hero fading to
stone, approved music branding and square album tiles. Recently Added is the
Music landing, not a pill; Albums, Artists, Songs and Playlists form the pill
row. Selected art remains in the tile lane, with details over the hero. Browse
pages put search at the right. Album/artist/song search uses Kodi's full local
music index and shows at most 500 matches; saved playlists come from
`special://musicplaylists/`, with no fabricated examples. Missing covers use
approved square icons. Mac runtime checks saw 25 recently added albums, 1,295
albums, 1,122 artists and 16,454 songs; searching songs for Queen returned 161
matches from the full index, including beyond the initial 500-song page.
Playback is only on explicit selection. The final Mac redeployment and Kodi
restart confirmed the Music landing, Artists and Playlists layouts, the
approved square missing-art icon, the right-side search cluster, and the
honest empty-playlist state with no Play action. A selected artist opened its
filtered Albums page. Offline XML/metadata/query tests pass. Album, song and
saved-playlist playback have not been exercised in this revision, and no saved
playlists exist in the Mac profile. This is not LibreELEC/TV acceptance or a
new music service.
Rollback is the prior committed add-on revision and a Mac Kodi restart.

Books visual milestone, 2026-10-15 (skin v0.7.2): the Books landing now has
separate eBook, audiobook and podcast tile lanes. Three browse pages share the
Music-style hero hierarchy, approved category icons, 24-hour clock, rounded
tiles and right-side search. The existing one-shot sanitized feed supplies
46 audiobooks but no eBooks or podcasts; only real titles are rendered. The
source snapshot has no per-item added timestamp, cover, synopsis or playback
path, so the populated lane is truthfully labelled a catalogue snapshot rather
than Latest Added, missing art uses approved square icons, and the hero action
is informational only. No new source access, publisher, service or remote Git
write is part of this milestone. Synthetic feed/layout tests pass. The Mac
Kodi visual check now confirms the three separate landing lanes, wrapped
long audiobook hero titles, the 46-title audiobook browse grid, and working
title search (including a positive `Sandman` match and a distinct no-match
state). The eBook and podcast pages show honest not-connected states and no
action button; their search controls render without false catalogue results.
The layout was adjusted after live inspection to prevent the audiobook lane
from colliding with the Podcasts heading. The Mac test profile was left on
the Books landing with search cleared. Physical LibreELEC playback and TV
acceptance remain outside this visual milestone.
Rollback is the prior committed skin revision and a Kodi restart.

Books catalogue/cover pilot, 2026-10-15: read-only TrueNAS checks confirmed
505 Calibre `books` rows in the live `metadata.db`, while the existing
unified-media snapshot still carried 46 Audiobookshelf titles and no eBooks.
The bounded one-shot pilot now projects Calibre IDs/titles into the disposable
Mac Kodi feed. Live Mac visual QA showed `505 / 505 catalogue titles` on the
eBooks browse page; this is a catalogue display, not yet a connected reader,
date-ranked Latest Added lane or playback integration. Audiobookshelf's
read-only database yielded exact IDs and `coverPath` for all 46 titles. Those
paths use an old case/nesting convention, but all 46 resolve to JPEGs in the
current media mount after a fixed prefix translation. A separate one-shot
read-only copy placed the 46 verified, size-bounded JPEGs in the Mac profile's
private cache, keyed by opaque IDs. After the skin restart, visual QA showed
the real covers on the Books landing and larger portrait covers on the
Audiobooks browse grid. No audiobook files, credentials, cover paths or
Calibre filesystem paths enter the JSON feed; neither server nor services
were changed. The source is one-shot and the Calibre query uses SQLite
immutable read-only mode; a production publisher needs a consistent database
snapshot and an explicit refresh/retention design. At this checkpoint,
podcasts remained unconnected. Forgejo synchronization is pending specific
push approval.

eBook artwork and podcast preparation, 2026-10-15: Calibre's 505 indexed
books map to 501 source `cover.jpg` files. A bounded one-shot read-only
transfer placed those JPEGs in the disposable Mac Kodi cache by exact Calibre
ID; the other four retain the approved Aster icon. Kodi restart and direct
visual checks confirmed real artwork in both the Books landing and eBook
browse tiles. No eBook files or Calibre paths were exported to the skin feed;
reading remains unconnected. A prepared Audiobookshelf read-only query will
project only subscribed podcast IDs/titles after a Podcast library exists;
it currently returns zero and excludes feed URLs, episodes and credentials.
The Audiobookshelf official search supports finding shows; subscription and
download actions remain in the authenticated service, not the Kodi skin.
No spoken output is added.

Books card refinement, 2026-10-15: the shared square backplate was split by
media type. Calibre eBooks now use portrait 190×260 browse cards and 66×90
landing cards; Audiobookshelf covers retain square 260×260 and 90×90 cards.
The inner artwork keeps its aspect ratio, and the green focus surface follows
each card shape. Kodi was restarted and both browse pages, the landing rows,
and focused cards were visually checked. The 39 offline skin tests pass.

Podcast deployment preflight found material live/Compose drift: the running
Audiobookshelf container is bound to `192.168.20.40:30067`, mounts the
legacy Audiobooks path read-only, and mounts `/audiobooks` read-write; the
saved Compose file instead specified loopback `30077`, omitted the legacy
mount and declared `/audiobooks` read-only. Recreating from that file would
break the current endpoint and path compatibility. A `Media/appdata`
pre-change snapshot and a copy of the Compose file were verified. The empty
`/mnt/Media/media/podcasts` directory was created with `apps:apps` 0770.
An initial targeted Compose edit was restored byte-for-byte after drift was
detected; the container was not recreated at that point. Jason then explicitly
approved preserving all observed live settings in the revised change. The
targeted edit was reapplied, Compose's effective Audiobookshelf definition
was checked for the unchanged household port, read-write `/audiobooks`,
read-only legacy mount, and new read-write `/podcasts`, and only that service
was recreated. The first HTTP probe ran during startup and failed; logs then
showed a healthy listener, and a repeat probe returned HTTP 200. Database
`quick_check` returned `ok`; 46 audiobook items and all 46 cover paths were
still accessible after the restart.

Using Jason's signed-in Audiobookshelf web UI, a separate `Podcasts` library
was created with iTunes search and `/podcasts` as its only folder. Scheduled
library scans are disabled. The library view shows empty; read-only database
checks show one book library, one podcast library, 46 book items and zero
podcast items. The host podcast directory remains empty, and no show was
subscribed or episode downloaded. The one-shot Kodi feed was refreshed with
551 records (505 eBooks, 46 audiobooks, zero podcasts). Its empty-state copy
now points to Audiobookshelf discovery. The authenticated `Podcasts` → `Add`
page exposes a title search, RSS URL input and OPML import. Acquiring and
playing a selected podcast through Kodi is a later integration milestone;
the current Kodi page is a read-only catalogue, not a playback client.

Subscribed-podcast visual pilot and Media mark, 2026-10-15: Jason acquired five
podcast shows and five downloaded episodes per show in Audiobookshelf. A
read-only SQLite check confirmed 25 episodes with audio-file metadata. The
one-shot Kodi feed was refreshed to 556 titles: 505 eBooks, 46 audiobooks
and five podcast subscriptions. A bounded read-only cover transfer copied
the five JPEGs from `/podcasts` to Kodi's private cache by exact library-item
ID; the Books landing and Podcasts browse page visibly render all five. The
existing *In Our Time* episode “Thomas More's Utopia” was checked against its
downloaded file: path remained inside `/podcasts`, size matched Audiobookshelf
metadata (55,591,569 bytes), and first/last bytes were readable with an ID3
header. This is a file-integrity check, **not** decoded or audible playback.
No episode was copied to the Mac, and Kodi still has no episode selector or
authenticated streaming adapter. The Aster Media header mark was centered in
its 85–375 px gutter and enlarged from 160×107 to 240×160; the live Kodi
view shows it clear of the category pills and hero greeting. The 41 offline
skin tests pass. These Mac checks do not replace LibreELEC endpoint testing.

Books visual and access-path check, 2026-10-15: The disposable Mac skin now
renders real eBook jackets in full-bleed rounded portrait cards and real
audiobook/podcast covers in full-bleed rounded square cards, with ivory
fallback panels only where a cover is absent. Landing-row art is larger. The
Books, Music, Digest and Media product marks share the same 110,0 / 240×160
header slot (including Media details); Media hero copy starts below that slot.
The refreshed Kodi test visibly showed the larger Books mark, full-bleed
landing artwork and full-bleed Podcasts browse cards without white frames.
Forty-two offline skin tests pass. The existing Books feed still has only
sanitized catalogue IDs, titles and cached cover JPEGs. Activating a title
does not read an eBook or play audio: no ebook file or authenticated audio
stream is supplied by this feed. Live read-only service inspection found the
existing Calibre-Web Automated container has the Calibre library mounted and
Audiobookshelf is running, but neither supplies a Kodi playback/reader route
in this prototype. Before wiring controls, choose a bounded authenticated
Audiobookshelf audio route and decide whether eBooks should hand off to the
existing browser-based Calibre-Web reader or require a new Kodi-native reader.
Do not turn catalogue IDs into unprotected media URLs or export entire books
through the feed.

Books synopsis checkpoint, 2026-10-15: The one-shot disposable feed now
projects bounded, plain-text descriptions from Calibre comments and
Audiobookshelf book/podcast metadata. The Mac test feed contains 558 titles:
505 eBooks, 46 audiobooks, and seven subscribed podcasts. Descriptions are
available for 141 eBooks, 41 audiobooks and all seven podcasts; missing source
descriptions are not fabricated. The Books hero displays the selected synopsis,
and the About action opens a newly supplied Aster text-viewer dialog, verified
in the Mac Kodi UI. No file paths, audio payloads, credentials or full books
are added to the feed. The user approved audio connection and eBook reader
handoff; the selected implementation path is Kodi's official-repository
Audiobookshelf add-on plus existing Calibre-Web. No new server credential or
permission is approved by this checkpoint.

Books handoff checkpoint, 2026-10-15: Explicit hero actions now resolve only
validated IDs from the sanitized catalogue. "Read this book" opened a real
Calibre-Web title in the Mac's default browser, with its browser-reader
control present. On LibreELEC the action displays the authenticated reader
URL for handoff to a phone/tablet; the physical-device flow remains untested.
The official Audiobookshelf Kodi add-on was installed unconfigured in the
disposable Mac profile, but no account was signed in and playback is **not**
verified. Source review found it embeds its bearer token in artwork and media
URLs. Jason chose the safer-client route. Forty-seven offline tests pass;
full text viewer and eBook handoff passed the Mac UI check. No server setting,
credential or podcast subscription was changed in this handoff milestone.

Safe audio bridge design checkpoint, 2026-10-15: Aster's own Kodi add-on now
implements a loopback-only HTTP byte-range bridge and a private UNIX control
socket. The add-on requires a 0600 file with an API-capable HTTPS origin and a
dedicated Audiobookshelf key; neither is present in the repository or Mac
profile. Metadata is fetched by validated ID, file inodes are selected only
from returned Audiobookshelf book/podcast metadata, and the upstream credential
is sent only in an `Authorization` header. Kodi sees random expiring local
capabilities, not bearer tokens. The Mac has not yet tested the add-on against
the live Audiobookshelf server. Synthetic book, podcast and range tests pass.
On the disposable Mac Kodi profile, the add-on was detected but initially
disabled after a manual directory copy. It was enabled locally and Kodi then
reported the expected missing-private-configuration state. The Aster
"Listen in Kodi" action opened the branded listening window and displayed
the bridge-unavailable message; no token was supplied or audio played. An
unauthenticated request to the existing
`https://audiobooks.elliottrook.com/api/items/<id>` path returned HTTP 401
with valid TLS and no redirect, so no new proxy route appears necessary.
Remaining gates: authorize/provision a restricted credential without placing
it in the repository or chat; validate the API response and real episode/book
playback, pause/seek and network-loss handling on Mac and then LibreELEC. The
prototype does not yet sync progress or promise multi-file autoplay. No
service, firewall or SSO route was changed for this checkpoint.

Private-key handoff preparation, 2026-10-15: `configure_client.py` now accepts
the dedicated Audiobookshelf key only through a hidden interactive Terminal
prompt, creates the Mac Kodi config with restrictive permissions, and refuses
to overwrite an existing config. Three synthetic helper tests pass. Jason
must run this helper himself after creating the key; the key must not be sent
through chat or stored in Git. No credential was received or installed at this
checkpoint.

Private audio pilot, 2026-10-15: Jason installed the dedicated key via the
interactive helper; the Mac `client.json` is owner-only (0600), and the live
HTTPS API returned one audiobook with an audio file and one podcast with five
downloaded episodes. The original bridge failed to bind because its UNIX
socket pathname was 104 bytes on macOS; cleanup then hung on an unstarted
listener. A shorter socket name and partial-start cleanup regression test fixed
both. The restarted Mac Kodi test logged the bridge ready and displayed book
parts and podcast episodes. Selecting a book part opened Kodi's AAC decoder;
selecting a podcast episode opened its MP3 decoder. The live loopback bridge
returned HTTP 206 and exactly 32 requested bytes for
both media types; a synthetic upstream audio outage returned a generic 502
without the key. Audible output, Kodi-player seeking, resume, a real outage
and LibreELEC still need testing. Jellyfin's segment monitor logs Kodi's
temporary loopback capability URL, so the pilot's
current Kodi log was made 0600, and bridge startup now enforces that mode or
fails closed. The URL is not the Audiobookshelf key, but another local process
running as the Kodi user can still read it. The listening list briefly blanks
the selected row during playback; that is a remaining UI defect. No proxy,
firewall, server account or remote Git state was changed in this checkpoint.

Aster Books listening-page milestone, 2026-10-15: The Mac pilot's bare Kodi
audio list was replaced with an Aster-styled listening view. The plug-in
reuses the sanitized Books catalogue and local opaque cover cache to show a
book or podcast cover, parent and episode/part titles, and a bounded synopsis.
The page shows elapsed/total time, a progress bar, and Kodi transport actions
for pause/resume, 30-second skips and stop, with an Aster Books idle state
before selecting a part. XML validation and 57 local unit tests pass. In the
live Mac UI, an audiobook and a downloaded podcast episode opened with the
correct art and metadata; the time and progress display advanced. Pause
changed to Resume and held the audiobook clock, a forward seek advanced it,
and Stop ended audiobook and podcast playback. Audible output, backward seek,
resume after restart, Audiobookshelf progress synchronization, real network
failure, and LibreELEC/TV behavior remain unverified. Kodi still blanks the
focused episode/chapter list row while that item is actively playing (the
hero title remains visible); this cosmetic defect is retained for a later
focused Kodi-list investigation. No credentials or remote Git state changed.

Chapter navigation and selector checkpoint, 2026-10-15: The private bridge now
projects bounded Audiobookshelf `media.chapters` into selectable Kodi entries.
Single-file books use the chapter start directly; multi-file books require
aligned `media.tracks` timing and validated file inodes. If timing is absent or
inconsistent, the safe fallback is the former file-parts list. A read-only
sample of all 46 live audiobooks found chapter metadata in each, including
seven multi-file titles with aligned track counts. The first five single-file
samples and a multi-file sample mapped the same number of chapters as the
server supplied. Synthetic tests cover single-file offsets, cross-file offsets,
and the missing-track fallback. Each chapter uses a distinct local capability:
the initial shared-URL Mac pilot made Kodi jump to the final chapter's offset,
whereas a replay after assigning separate URLs started Opening Credits near
00:00. Selecting Chapter 1 showed its title, but a stable measured nonzero
seek position was not captured, so that behavior remains to verify. The
listening page's bottom selector now uses a rounded paper panel with numbered
ivory/green cards, chapter lengths, parent title, and a fallback row label
while Kodi is playing; the Mac pilot visually showed the revised layout.
XML validation, 60 local tests and whitespace checks pass. This is a chapter
*start* selector, not chapter-bounded playback; multi-file autoplay, audible
output, progress sync, and LibreELEC endpoint behavior remain unverified.
No server configuration or remote Git state changed.

Listening-page visual revision, 2026-10-15: The Mac Kodi pilot now uses a
distinct two-column page. The retained dark player panel sits on the left
with cover art, title, chapter, time/progress and transport controls. The
chapter/episode selector is an unboxed, scrollable text list on the right,
using the same small font as the previous synopsis and a narrow green focus
marker. Row dividers were subsequently removed and chapter spacing tightened
to fit twelve rows without changing type size. A live Mac screenshot verified the initial layout and
playback from Opening Credits advancing from 00:00 to 00:08 with controls
visible. Kodi still sometimes clears the active list row's item properties
when playback starts; a MusicPlayer-title fallback was added but needs a
fresh focused-row visual check after reload. No ABS/server changes or remote
Git operations were part of this revision.

Music album-player and playlist checkpoint, 2026-10-15 (skin v0.7.3):
The disposable Mac Kodi pilot now opens a dedicated two-column Aster Music
album page. A live `The Works` check displayed its cover and 15 ordered
tracks; Play album started audio and exposed elapsed time, progress and
transport controls. Selecting a track uses the ordered album queue. The
first pilot click exposed Kodi's custom-window lifecycle rule: selection
properties must be staged on the Home window until the player exists. That
was corrected and verified after restart. The original Playlists page
consulted only an empty Kodi-local `special://musicplaylists/` folder. The
Plex-to-Jellyfin migration record confirms hand-curated playlists moved to
Jellyfin. Aster now also enumerates the logged-in Jellyfin Kodi add-on's
playlist views, using its existing session without copying credentials.
The Mac pilot displayed 16 playlists and opening `Cardio Workout` showed
its tracks. Kodi-local playlists remain supported. Seven synthetic music
tests pass. These checks are Mac pilot evidence, not LibreELEC/TV acceptance;
no Jellyfin server or media files were changed. New source work remains local
pending separate push authorization.

Music shared-player checkpoint, 2026-10-15 (skin v0.7.4): Selecting an
album, song or saved playlist now opens the same Aster Music player instead
of immediately playing a song or handing a playlist to Kodi's generic view.
The Mac pilot showed a song with its cover and one-track list, a 13-track
Jellyfin playlist with ordered tracks, and a 10-track album. The song and
Jellyfin playlist both started audio in the shared player, with elapsed-time
progress and transport controls visible; album opening was rechecked after
the generalization. Playback remains deliberate (Play or track selection),
and the Jellyfin session remains owned by its Kodi add-on. Synthetic source
and queue tests pass. This is Mac-pilot evidence, not LibreELEC acceptance;
no server or media files were changed. The source change is local pending
fresh push authorization.

Digest player candidate, 2026-10-15 (skin v0.7.5, local only): Read-only
inspection of the published Aster News audio metadata and `/digest` page
matched 18 of 19 live chapters to story summaries and 15 to public image
URLs. The candidate uses these fields in a two-column player-like screen with
an unboxed chapter list, title/source/brief synopsis/art, and transport
controls. The Mac pilot rendered the 19-story list and the first story, but
the first synopsis overran its panel; a 160-character panel bound corrected
that in a second screenshot. Kodi launched its blank audio visualisation on
Listen; a one-shot return to the Digest window subsequently worked. A
persistent Python watcher proposed for automatic chapter
following caused macOS Kodi to segfault during Quit: the crash report's
LanguageInvoker stack ends in `xbmcgui.Window.setProperty` while the main
thread is cleaning up script threads. The Mac pilot's original `hub_data.py`
and Digest XML were restored from `/tmp/aster-digest-check.pltEOy/`; there is
no watcher installed in the pilot. The repository candidate removes the
persistent watcher and offers manual Refresh to synchronize the displayed
story to the player's elapsed time. A watcher-free Mac quit/relaunch was
clean and playback of the published MP3 was observed. Selecting chapter 2
produced a playback position past 1:02, but the left panel returned to story
1 as the window reloaded. The candidate now retains the requested chapter
across that reload until playback reaches its seek point; unit tests cover
this race, but a further visual check of its title/art and focus navigation
is required. The list's own click did not dispatch a script reliably, so a
separate **Play selected** button reads Kodi's retained list selection.
Automatic chapter following and live candidate acceptance remain open gates;
no LibreELEC claim, server change or remote Git operation follows from this
checkpoint. All 55 synthetic source tests pass, including art URL bounds and
chapter mapping.

Digest playback follow-up, 2026-10-15 (local candidate): The Mac pilot
confirmed that manual Refresh during playback changes the title, synopsis,
image and highlighted row to the story at the audio clock. Two starts from a
selected later chapter exposed independent Kodi startup races: the MP3 can
start after a fixed 750 ms wait, and a window onload refresh can run before
the seek. A polling-based attempt without windowed playback left Kodi on a
black audio visualisation, so it was not retained. The next candidate starts
the published MP3 with Kodi's documented `windowed=True` option, waits up to
five seconds for audio startup, uses the list control's selected item instead
of a focus-dependent infolabel for chapter offset, and retains the requested
story through the initial seek. All 55 source tests pass, but the Mac locked
before this exact candidate could be visually accepted. No server or remote
Git change was made; live chapter start and clean stop remain open checks.

Digest chapter seek investigation, 2026-10-16 (local candidate, not accepted):
The Mac pilot loaded the new 17-story edition. The list's `onclick` did not
dispatch reliably, so story selection remains separate from **Play selected**.
Reading the retained `Container(500).ListItem.Property(AsterStart)` from that
button displayed the selected second story's title, synopsis and wildfire
image. The published HTTP MP3 has `Accept-Ranges: bytes`, but Kodi's
`Player.Seek` reported an immediate position of 0:00 for a requested 1:02
chapter, despite `canseek=true`; the elapsed display advanced from the start.
That makes HTTP seek unsuitable for chapter playback in this pilot. The next
candidate caches the published MP3 under Kodi's local temporary directory,
bounded at 25 MiB and keyed to the digest generation timestamp. It checks
`Last-Modified` against the generation timestamp to reject an edition race,
waits for Kodi to report seekability, and stops audio if the verified seek
position is not within three seconds of the selected chapter. All 56 offline
source tests pass. The Mac locked before this local-file candidate could be
visually verified; selected chapter time, pause/stop and fresh-edition behavior
remain open gates. No server data or remote Git state changed.

Breaking News page, 2026-10-16 (skin v0.7.6, local candidate): Aster News now
has linked **Daily Digest** and **Breaking News** tabs. The new Kodi page reads
the existing private news service's server-rendered `/` view rather than
adding another API or changing the server. It accepts only bounded headline,
summary and outlet-label text, caps the page at 40 clusters, and fails closed
when the source is unavailable or malformed. Selection updates a large,
player-like reading panel; refresh never starts media and source links are not
exposed in the TV interface. Synthetic parser, navigation, geometry and asset
checks cover the candidate. Mac rendering, remote focus flow and a live feed
load remain the acceptance gate; LibreELEC remains untested. Roll back the
local milestone commit to remove the page. No production or remote Git state
changed.

Digest automatic story follow, 2026-10-17 (skin v0.7.7): Live
use confirmed that audio advanced while the panel remained on story one. The
fix uses Kodi's native, per-skin looping `AlarmClock` to invoke a
short one-shot synchronization every two seconds, only while the Digest page
is open. Each tick reads a bounded story snapshot already held in window
properties and the local player clock; it performs no network request, does
not access a live GUI control, and exits immediately. Page unload cancels the
alarm, and a current-window guard prevents a queued tick from touching the
closed custom window. This deliberately avoids the persistent Python watcher
whose shutdown-time window write previously crashed Kodi. The Mac test
followed multiple chapter boundaries with headline, synopsis, source and art
updates; leaving Digest stopped the alarm, and Kodi then stopped playback and
quit cleanly. The 58-test skin suite also covers boundary advancement and the
timer lifecycle. LibreELEC playback remains a later hardware validation gate.

Digest playback highlight, 2026-10-17 (skin v0.7.8): The same bounded active
story index now queues Kodi's supported `Control.SetFocus` built-in when a
chapter changes, keeping the green row highlight aligned with the headline,
synopsis, source and artwork without restoring unsafe direct list-control
access. A live Mac test started at the 8:02 story and crossed the 8:46 chapter
boundary: the panel advanced to the Brazilian Amazon story and the green
highlight advanced to its matching row. Stop removed the playback controls
without a stall. The 58-test suite passes and asserts the queued focus command;
LibreELEC playback remains a later hardware validation gate.

Books feed reconnection, 2026-10-17 (skin v0.7.9): The Books landing page
correctly routed to its three catalogue windows, but its sanitized snapshot had
expired. The one-shot publisher incorrectly used the upstream unified-media
file's modification time as the snapshot generation time, so an unchanged
library could not be republished as fresh. The publisher now records capture
time in `generated_at` and preserves upstream activity separately in
`source_updated_at`. A new read-only snapshot restored 558 records. Live Mac
validation showed all three landing rows and their linked pages populated with
505 eBooks, 46 audiobooks and 7 podcasts, including existing cached artwork and
synopses. No media, server configuration, credentials or remote Git state was
changed. All 59 offline skin tests pass, including the separated timestamp
contract; LibreELEC remains a later hardware validation gate.

Aster Home dashboard, 2026-10-17 (skin v0.8.0): The Home page now uses the
established Aster dashboard language rather than the generic hub list. It shows
fixed lighting, indoor-comfort, camera and read-only-home summary cards; a
large camera-status surface; a compact validated-entity list; a 24-hour clock;
and a square timer card with a central digital display and segmented circular
countdown treatment. The timer intentionally displays an inactive state until
an approved timer source publishes bounded countdown data. Camera content
remains inside authenticated Frigate: this page shows only the reviewed
`front_of_house` availability state and neither requests nor renders frames.
The Home publisher now records capture time independently from upstream report
activity, so an unchanged valid snapshot can be refreshed without appearing
stale. Live Mac validation displayed Laundry Lights `On`, Closet Temperature
`16.6°C`, and Front Of House `Online`; refresh completed without another page
failure. The observed Kodi crash report was confined to the macOS application
termination callback after a menu-initiated quit, not dashboard navigation or
refresh. The 60-test skin suite covers the projection, privacy-preserving
camera label, timer geometry and runtime asset references. No Home Assistant,
Frigate, network, credential or remote Git state was changed.

Timer scale and private camera-preview test, 2026-10-17 (skin v0.8.1): The
timer card remains 370 × 370 pixels while its circular face grows from 280 ×
280 to 340 × 340, leaving only the deliberate card inset. A bounded Mac-only
camera test used an SSH local forward from `127.0.0.1:15102` to Frigate's
existing loopback API; Frigate remained private and no credential, public
route or configuration change was introduced. Kodi first proved it could
decode the MJPEG stream, but its video player forced that path into the
full-screen window. The accepted dashboard implementation instead updates the
reviewed `front_of_house` latest JPEG every two seconds inside the camera card.
It starts only on **Live view**, stops on page exit or a second selection, and
expires after five minutes to bound exposure and image-cache growth. Live Mac
validation showed successive camera timestamps in place and confirmed the
refresh alarm stopped after leaving the page. The temporary SSH tunnel was
then closed. Production promotion still requires a monitored, least-privilege
per-client bridge and LibreELEC validation; this commit does not make the
manual Mac tunnel permanent.

Sixty-second timer dial refinement, 2026-10-17 (skin v0.8.2): The timer card
remains fixed at 370 × 370 pixels, while its dark dial expands to 360 × 360 and
the larger 56-pixel digital reader is mathematically centred on both axes. The
former twelve broad marks are replaced by sixty separately positioned radial
pills, one per second. Their muted layer preserves an honest inactive state;
their sage layer is already gated by the bounded `HomeTimerSecond` and
`HomeTimerActive` presentation properties so a later approved read-only timer
publisher can deplete the ring without another layout redesign. This milestone
does not create, start or claim an active household timer. Live Mac Kodi
validation showed the enlarged dial filling the existing card, all sixty pills
evenly spaced, and the `--:--` reader centred in both axes; Kodi loaded v0.8.2
and its custom Home window without a skin error. The 60-test suite also passed.

Home dashboard first-pass close-out, 2026-10-17 (skin v0.8.11): The
camera **Live view** action now shares the timer preset lane, top coordinate
and height. All six page clocks use one 24-hour charcoal pill with the same
subtle two-pixel gold outline first established on Aster Media. Search and
filter controls across media, music, books and the on-screen keyboard now use
the same quieter charcoal-and-gold language; limestone texture remains on
major navigation and primary actions rather than utility fields. This is a
skin-only, reversible presentation change with no service, media, camera,
Home Assistant, credential or network mutation. Live Mac Kodi validation
confirmed the aligned Home action lane, the outlined 24-hour clock on Media
and Home, and the new media search controls in focused and idle states. All 63
offline tests and every skin XML validation pass. LibreELEC remains a later
hardware gate.

Search-field legibility refinement, 2026-10-17 (skin v0.8.12):
Search entry text retains left alignment but gains a deliberate inset and
vertical centring. Utility-field borders use a stronger Aster-gold tint while
the shared clock outline remains quieter. The same treatment applies to the
library search field and on-screen keyboard entry without changing search
behaviour, data sources or navigation. Live Mac Kodi validation confirmed the
inset, vertical centring and stronger outline on the media library screen; all
63 offline tests and every skin XML validation pass.

Media genre discovery rail, 2026-10-17 (skin v0.8.13): The Media landing page
now places a third portrait rail beneath Recommended for You for Comedy,
Drama, Action, Sci-Fi, Documentary and Horror. Its upper edge deliberately
peeks into the initial viewport; focusing the rail lifts all three media lanes
to expose the full controls. Each tile selects a slightly washed poster at
random from a matching native Kodi movie or TV smart playlist, and opens the
corresponding complete genre playlist. An initial Python Home-load callback
failed its live gate with a Kodi 21.3 native segmentation fault in
`ControlList.reset()`; that unsafe cross-thread GUI mutation was removed before
commit. Preview and browsing now use only native, read-only Kodi containers.
This performs no metadata change, acquisition or network lookup. Offline and
live-Kodi validation then passed: the initial viewport showed only the poster
tops; Down lifted the three rails cleanly while hiding the hero copy; all six
labels and random posters rendered; and horizontal navigation into Horror
opened the complete 83-title Horror Movies view. Kodi remained stable. All 65
offline tests and every skin/playlist XML validation pass. LibreELEC remains a
later hardware gate.

Genre-caption alignment, 2026-10-17 (skin v0.8.14): The six genre titles move
out of the dark image overlays and sit directly beneath their portrait tiles
in Aster ink, matching the other media-poster grids. Their lower position stays
outside the initial viewport, preserving the intentional artwork-only peek;
the captions enter with the focused rail. This is a presentation-only change
with no library, playlist, service or network mutation. Live visual validation
confirmed all six captions beneath clean full-height portraits, the Comedy
focus ring, and the unchanged artwork-only peek. All 65 offline tests and every
skin/playlist XML validation pass; Kodi remained stable.

## 15. References

- `../Project-Creation-Standard.md`
- `../../AGENTS.md`
- `Aster-Unified-Voice-Service.md`
- `Pull-Based-Forgejo-Runner.md`
- `../runbooks/Pull-Based-Forgejo-Runner.md`
- `../design/HomeLab-UI-Style-Guide.md`
- Official Kodi: https://github.com/xbmc/xbmc
- Official LibreELEC: https://github.com/LibreELEC/LibreELEC.tv
- Kodi skin development: https://kodi.wiki/view/Skin_development_introduction
- Kodi add-on rules and licensing guidance: https://kodi.wiki/view/Add-on_rules
- Home Assistant dashboards: https://www.home-assistant.io/dashboards
- Home Assistant frontend themes: https://www.home-assistant.io/integrations/frontend/
- Home Assistant custom cards: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
