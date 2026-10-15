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
