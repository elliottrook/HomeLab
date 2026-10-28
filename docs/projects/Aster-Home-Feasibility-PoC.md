# Aster Home — EH-001: LibreELEC/Kodi feasibility experiment

> **Status:** Active — Stream A; the BOSGAME E3 Neo internal NVMe now runs the pinned LibreELEC 13 nightly/Kodi 22 baseline with Aster Home v1.0.4, synchronized Jellyfin media/music libraries, approved AsterTV startup branding and prior 4K60 HEVC HDR10/AV1 playback evidence; main-TV HDR/receiver passthrough, YouTube playback, Books/Home/Digest client-state migration, soak and destructive recovery gates remain open
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
- [ ] **M2 — Audiovisual:** Jellyfin library/direct play, music, collections, remote navigation, codecs, subtitles and playback stability. M2 is running on the owner-purchased HP ProDesk 400 G5 Desktop Mini with LibreELEC 12.2.1 installed to its explicitly authorised internal Samsung NVMe. Validate the actual HDMI path through the television and receiver, and separate endpoint, adapter/cable, sink and software limitations. HDMI-CEC is optional rather than gating; prove a reliable local Bluetooth, IR or USB-HID control path instead. Gate: no media-file mutation; measurable direct-play, HDR10, receiver audio passthrough, network and navigation results, with hardware limitations explicitly separated from software results.
- [x] **M3 — Customization:** 2026-10-17. Owner accepted Aster Home skin v1.0.0 as the first private production candidate. The normal Mac Kodi path now covers the Media/Jellyfin interface, playback OSD, Music, Books/Audiobooks/Podcasts, Digest/Breaking News, Home status/camera pilot/timer, settings, sounds and watch state without a Kodi core fork. Deterministic private release packaging, checksums, install order and rollback are recorded in `services/kodi/skin.asterhome/RELEASE.md`. Physical LibreELEC compatibility remains M2 rather than being inferred from Mac acceptance.
- [ ] **M4 — Voice/intelligence:** consume existing Aster voice service with opt-in mic/control, demonstrate speech/turn and timeout/fallback handling without new TTS implementation. Gate: privacy and canonical-voice compliance.
- [ ] **M5 — SOFTWARE GO/NO-GO:** issue `Aster-Home-EH-001-Feasibility-Decision.md` explicitly stating **USE / CONDITIONAL USE / REJECT**, weighted tests plus hard constraints and source-supported alternatives if rejected. **No hardware purchasing study is necessary after REJECT** beyond documenting what alternatives need testing.
- [ ] **M6 — Conditional hardware/pricing:** **only if USE/CONDITIONAL USE**. Compare powerful mini-PC and cheaper local-decoding thin endpoint; measure network/server/client CPU, RAM, codec support, 4K/HDR, control path (Bluetooth/IR/USB-HID and optional HDMI-CEC), audio passthrough, boot/recovery and wattage on available hardware; distinguish measured versus vendor claims. Price at least two viable products **per class** from Canadian retailers, with SKU, dated CAD offers/stock, sources, shipping/tax/accessories, support, 5-year TCO and ranked no-buy/reuse/buy choices. Gate: defensible minimum/efficient/premium specification and a specific recommended purchase or explicit defer.
- [ ] **M7 — Decision, recovery and handover:** reproduce key tests, verify independent rollback, update Doctor/Beszel/NetBox/wiki/operational references as applicable, apply the Aster internal style guide, produce non-technical user guide and final recommendation. No production deployment or order under this experiment.

### M2 physical HP ProDesk runbook

1. Reconfirm the recorded HP model, CPU, RAM, internal NVMe identity and
   LibreELEC version. Firmware changes remain outside this test unless a
   separate hardware-risk decision is recorded.
2. Retain the verified LibreELEC 12.2.1 Generic x86_64 image, its recorded
   checksum and the removable installer as the bare-metal recovery path. The
   owner-authorised internal Samsung NVMe install is now the appliance target;
   Windows and its recovery partitions are intentionally no longer rollback.
3. Preserve a hash-checked clean Kodi-profile checkpoint before client
   integration. Use SSH public-key authentication with password login disabled;
   do not record client or service credentials in project evidence.
4. Install the deterministic Aster release bundle and official dependencies,
   then select the Aster skin and 24-hour regional clock. Keep Estuary available
   as the interface rollback path.
5. Connect to the existing network without adding a VLAN, firewall rule or
   public route. Authenticate the Jellyfin integration interactively and sync
   the approved libraries; verify library counts and populated Aster rails
   without changing media files.
6. Test the HP's physical display output first at the sink and then through the
   intended AVR path. Record EDID, negotiated resolution/refresh modes, HDR10
   state, available audio devices, AVR input/format, Kodi dropped frames and
   buffering. A missing 4K60 or audio mode must be attributed to the endpoint,
   adapter/cable, sink or receiver path rather than assumed to be Kodi.
7. Test Jellyfin direct play and fallback/transcode with representative 1080p,
   4K HEVC/HDR10, subtitles, music and available DTS/Atmos samples. Confirm the
   actual server decision and receiver format rather than inferring support
   from a Kodi settings screen.
8. Collect read-only host/Kodi telemetry during each workload: OS/Kodi version,
   CPU/GPU/RAM utilisation, thermal sensors, link state, logs, DRM/audio state,
   dropped frames and buffering. Keep TV HDR indicators and AVR front-panel
   formats as human-observed evidence; SSH measurement does not replace them.
9. Run bounded real workloads first: idle baseline, Aster navigation, Jellyfin
   catalogue access, 1080p playback, 4K HEVC/HDR10, subtitles, music, receiver
   passthrough and a 20–30 minute mixed playback soak. Add a synthetic stress
   tool only if a specific capacity question remains.
10. Treat HDMI-CEC as optional. Prove USB keyboard control as the baseline,
   followed by the purchased Bluetooth/USB-HID remote for pairing, mapping,
   voice input where supported, reboot reconnection, idle reconnection and
   range. Apple TV remote reuse remains a separate compatibility experiment.
11. Reboot from the internal NVMe repeatedly, verify Aster and integrations
   recover without manual repair, then prove Estuary fallback, profile restore
   and reinstall from the retained release bundle. The verified LibreELEC
   installer remains the last-resort clean rebuild path.

Checkboxes cannot be marked complete without documented validation.

### M2/M6 comparative endpoint campaign — 2026-10-22

The owner has selected three complementary physical roles instead of treating
one successful PC as proof of a hardware class:

1. **BOSGAME E3 Neo / Intel N95 / 16 GB / 512 GB** — install the immutable
   Aster Home v1.0.3 candidate, qualify it as the likely production living-room
   endpoint, and complete the selected remote test. Intel specifies the N95's
   integrated UHD Graphics and HDMI capability at up to 4096x2160 at 60 Hz;
   the actual BOSGAME connector, firmware, EDID path, LibreELEC driver and sink
   must still prove that mode. LibreELEC documents Alder Lake under Generic
   x86-64, but model-specific boot success must not be inferred from the CPU.
2. **HP ProDesk 400 G5 Desktop Mini / i5-9500T / 16 GB** — preserve the
   measured v1 baseline and use it as the recoverable Aster Home 2 development
   and physical visual-validation client. Source-deployed v2 work belongs here,
   not on the BOSGAME production candidate.
3. **Older Lenovo mini PC** — after recording its exact model, CPU/GPU, RAM,
   storage, firmware and display outputs, install the same v1 release and run
   the same measurements to establish a truthful low-cost bedroom-client
   floor. Do not simplify the skin, lower the test workload or change server
   behavior only for this endpoint; otherwise results are not comparable.

The BOSGAME begins with a non-destructive LibreELEC USB boot. Capture DMI,
firmware, storage, network, Bluetooth, audio, DRM/EDID and available display
modes before any internal installation. Confirm cold boot, restart, Ethernet,
Wi-Fi if needed, Bluetooth and 4K output from removable media first. Erasing or
repartitioning its internal 512 GB SSD requires a separate explicit target
confirmation after those checks. If stable LibreELEC 12.2.1 fails to boot, save
the failure evidence and make a separate version decision; do not silently
substitute a nightly image or a different operating system.

After the hardware gate, deploy only the checksum-verified v1.0.3 release ZIPs
and official dependencies, then reproduce the established client state without
copying secrets into Git or benchmark evidence. Give each endpoint a unique
hostname and profile checkpoint. Authenticate Jellyfin interactively, publish
the bounded Aster feeds, keep Estuary available, and verify that no v2 source
overlay or HP-specific profile drift reached the BOSGAME or Lenovo.

Run one common matrix on all three systems:

- cold boot and Kodi-ready time; restart recovery; idle and loaded temperature,
  memory, CPU/GPU, network and storage state;
- 1080p H.264/HEVC, 4K HEVC SDR, high-bitrate 4K 10-bit HEVC HDR10, subtitles,
  music, audiobook/podcast and Digest playback, with Jellyfin direct-play or
  transcode decision recorded;
- negotiated resolution/refresh, colourspace/HDR evidence, decoder identity,
  dropped/skipped frames, cache and buffering at start, five minutes and after
  a 20-minute soak;
- Aster page-load/focus behavior using the same populated libraries, including
  rapid rail navigation and artwork loading, with crashes and Kodi errors
  counted rather than described only as “smooth”;
- the G20BTS Plus pairing path, every required key, Back behavior, wake/idle
  reconnect, reboot reconnect, usable range and microphone/voice-search input;
  distinguish Bluetooth, USB-HID receiver and IR behavior rather than treating
  them as interchangeable; and
- measured wall power when a meter is available, plus fan/noise observations,
  recovery media, Estuary fallback and profile restore.

Use the BOSGAME result for the efficient production recommendation, the HP for
v2 development headroom, and the Lenovo result for a bedroom minimum only if
it passes the same hard playback, control, recovery and stability gates. A
slower catalogue load may be acceptable for a bedroom tier; dropped playback,
buffering, unreliable remote reconnection, missing HDR10 where required, or an
unrecoverable boot path is not.

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
| 2026-10-22 | Captured the BOSGAME E3 Neo pre-LibreELEC baseline over temporary Windows SSH without changing storage, firmware or boot state. | The client identifies as BOSGAME Ecolite Series with Intel N95 (4 cores), 16 GB RAM, Intel UHD Graphics and AMI BIOS `DNB20T V1.01` dated 2025-10-09. Windows drove the attached LG HDR 4K display at 3840x2160 60 Hz; Intel I226-V Ethernet linked at 1 Gbps and Realtek 8822CE Wi-Fi/Bluetooth were present. Disk 0 is the 476.9 GiB KingFast NVMe containing Windows; disk 1 is the 115.5 GiB Kingston DataTraveler whose `LIBREELEC` 1 GiB FAT partition confirms the retained 12.2.1 installer. The next non-destructive gate requires a second disposable USB target; the internal NVMe remains out of scope until a separate explicit erase decision. |
| 2026-10-22 | Deployed the remote-first UI focus milestone to the HP over a full skin checkpoint; validated same-column Media movement, immediate selected side rail, compact centred category pills, stronger focused cards, post-load Music/Books selection and full-Digest playback from the opening. | All 79 skin tests, XML parsing, Python compilation and `git diff --check` passed; Kodi remained active with no new skin error or traceback. Full Digest queued and prepared its complete audio, Music opened its selected album player, and the Books eBook handoff opened the bounded Calibre-Web destination. |
| 2026-10-22 | Added remote power-button sleep/wake to the v2 programme. | Short press is intended to pause/persist and request supported suspend; shutdown remains explicit. Each hardware client must pass repeated USB-wake, HDMI, audio, network, Kodi/Jellyfin state and power tests or expose the honest Display off fallback. The immutable v1.0.3 keymap is unchanged. |
| 2026-10-22 | Defined a three-endpoint comparison after the owner purchased a BOSGAME E3 Neo N95 and nominated the HP for v2 lab work plus an older Lenovo for the low-cost floor. | The BOSGAME will receive a non-destructive stable-LibreELEC hardware gate before any separately authorized internal install, then immutable v1.0.3 and the selected G20S Pro Plus remote. All three systems use one playback, UI, telemetry, recovery and control matrix; no lighter workload may manufacture a Lenovo pass. |
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

Seven-across genre rail, 2026-10-17 (skin v0.8.15): Family is added after
Horror as the seventh genre. Every lane narrows from 280 to 240 pixels and its
poster from 250 × 375 to 210 × 315, retaining the exact 2:3 ratio while fitting
seven evenly across the existing content width. Family uses the same native
random-preview and complete-browse smart-playlist pattern. Live validation on
the disposable macOS Kodi client confirmed that all seven tiles and their
below-poster labels fit across the page, Kodi remained stable, and selecting
Family opened the complete 129-title Family Movies view. All 65 offline tests
and every skin/playlist XML validation pass. This remains a read-only skin
change.

Genre-focus background transition, 2026-10-17 (skin v0.8.16): focusing any of
the seven genre tiles now dissolves the full-screen hero artwork over 220 ms,
revealing the same plain Aster stone colour already established by the hero's
bottom fade. The transition is reversible when focus returns to the upper
media lanes, keeping the genre captions legible without changing the initial
hero composition. Live validation on the disposable macOS Kodi client
confirmed the hero fully dissolves on genre focus, all seven names remain
clear against the warm stone field, the artwork returns when focus moves back
to Recommended for You, and Kodi remains stable.

Active-rail heading treatment, 2026-10-17 (skin v0.8.17): the portrait rail now
has a dedicated Genre heading. Continue Watching, Recommended for You and
Genre use Aster ink while idle and change to ivory only when their respective
rail has focus. Tile captions remain ink in both states so the focus treatment
belongs to each rail rather than each individual title. Live validation showed
Continue Watching in ivory while active with the other headings in ink, then
Genre in ivory after navigation with every genre caption still in ink. Moving
the portrait lane down reserved clean space for the new heading and removed
the initial overlap with the final Recommended caption; Kodi remained stable.

Rail-heading contrast refinement, 2026-10-17 (skin v0.8.18): live review found
that the v0.8.17 ivory active state did not work against the lighter stone
field. Continue Watching, Recommended for You and Genre now remain Aster ink
in every focus state; existing tile focus rings provide the navigation cue.
Live validation on the disposable macOS Kodi client confirmed the permanent
ink treatment remains legible on both the hero fade and plain stone field.

Combined genre browser, 2026-10-17 (skin v0.8.19; companion plug-in v0.1.0):
Kodi's native smart playlists cannot combine Movies and TV Shows, so the seven
single-class genre destinations are replaced by a small read-only Aster video
plug-in. It queries both existing Kodi library collections through JSON-RPC,
filters the selected indexed genre, merges and alphabetizes results in memory,
plays movie paths already held by Kodi, and opens TV shows through their native
season nodes. It performs no Kodi, Jellyfin or media-file writes. The landing
page retains the native one-item preview playlists.

Live validation on the disposable macOS Kodi client enabled the separately
installed companion and confirmed that Comedy opens one 455-title result made
from 399 movies and 56 TV shows. The same path opened Sci-Fi as a 271-title
combined result, and selecting `3rd Rock from the Sun` opened its native seven
season entries with the action correctly changing from Play to Browse. Movie
selection remained playable through Kodi's indexed Jellyfin path. No plug-in
errors were recorded in Kodi's log during either combined-library traversal.

Settings and UI-sound refinement, 2026-10-17 (skin v0.8.20; UI sounds v0.1.0):
Kodi's settings landing and category windows now use a restrained Aster shell:
dark identity column, warm layered work surface, rounded rows, sage focus and
gold accents while preserving Kodi's required settings-control IDs. Live Mac
checks covered the landing page plus Interface and Services navigation; 69
skin-layout tests, four video-plug-in tests and all XML validation passed.

The separate `resource.uisounds.asterhome` add-on replaces Kodi's sustained
cursor swish with original sub-100 ms stereo PCM clicks. Left and Right are
weighted toward their travel direction; Up and Down use centred high/low pitch
cues because a stereo UI sound has no vertical axis. Kodi's UI-sound contract
maps actions to WAV files but exposes neither focused-control coordinates nor
runtime pan, so exact tile-position audio would require a Kodi core change and
is deliberately out of scope. The add-on was installed, enabled and selected
in the disposable Mac profile after preserving the add-on database and GUI
settings. Kodi then loaded
`resource://resource.uisounds.asterhome/sounds.xml`; directional navigation
remained functional. Three sound-pack tests verify mapping, format, duration
and channel weighting. No media, service, network or production setting was
changed.

Official support-add-on milestone, 2026-10-17 (skin v0.8.23): The disposable
Mac Kodi profile now has the official Omega versions of Keymap Editor, Backup,
Log Viewer for Kodi and CU LRC Lyrics plus their previously absent required
Python modules. Exact versions and the official mirror index are recorded in
`services/kodi/official-addons.lock`; no unofficial repository was enabled.
The pre-change add-on database and GUI settings are retained under
`/tmp/aster-kodi-addon-checkpoint-20261017`. Kodi rediscovered the packages,
all nine requested add-on/module records are enabled, and a clean restart
reported no dependency or skin-load error. Aster Settings exposes the four
tools as Remote controls, Backup & restore, Diagnostics and Lyrics, with each
entry hidden when its add-on is absent. Backup has no cloud destination or
schedule configured, and no key mapping has been written before the physical
remote is available.

Live launch checks exposed four Kodi dialog contracts required by these tools.
`DialogSelect`, `DialogConfirm`, `DialogContextMenu` and
`DialogAddonSettings` now use Aster's dimmed charcoal, limestone and sage
language while retaining Kodi's required control IDs. Log Viewer opened both
the selector and local text reader; Keymap Editor reached its edit screen
without saving a map; CU LRC Lyrics opened its settings; and a media context
menu rendered correctly. A clean 0.8.23 restart reported no missing-window or
add-on exception. The disposable macOS build still logs its pre-existing media
key accessibility warning, which is not a skin or add-on failure.

The separately reviewed Home Assistant Weather add-on was not installed. It
would require placing a Home Assistant server address and credential in Kodi,
while this project deliberately gives Kodi only an expiring, field-bounded
Aster projection. Forecast data will instead extend that existing projection
after the candidate Home Assistant weather entity and allowed fields are
verified; this preserves the no-HA-credential-on-Kodi boundary.

Read-only discovery then confirmed one enabled MET entity,
`weather.forecast_home`. Its Recorder state provides the reviewed fields needed
for a current-weather card: condition, bounded temperature/unit and humidity.
The local schema-v3 implementation adds only those fields to the isolated Home
exporter and Aster dashboard; it rejects unknown conditions, non-Celsius/
Fahrenheit units, out-of-range values and extra entities. It deliberately does
not call `weather.get_forecasts` or export pressure, wind, attribution,
coordinates or credentials. Jason approved the bounded production deployment
on 2026-10-17. The two live Python files were preserved beside the component as
`.before-weather-20261017` rollback copies; only the hash-matched schema-v3
initializer and contract were promoted. `ha core check` passed before and
after a Core-only restart, and Home Assistant returned HTTP 200.

The resulting mode-0600 private report contained Laundry `on`, closet 16.9 °C
and one current-weather object (`sunny`, 15.9 °C, 60% humidity), with no
forecast, pressure, wind, location, endpoint or credential fields. Kodi skin
v0.8.24 and a fresh one-shot mode-0600 projection visibly rendered the weather
card alongside the existing light, temperature and camera cards. Kodi logged
the skin at v0.8.24 with no skin or feed exception; its pre-existing macOS
media-key accessibility warning remains unrelated. Home Assistant logged only
the expected generic custom-integration warning for this component; older
Apple TV setup-delay, Sonos and MET connectivity warnings are unchanged and
outside this deployment.

Video playback controls, 2026-10-17 (skin v0.8.25): live reproduction showed
that Jellyfin video playback itself worked, but Aster supplied neither Kodi's
`VideoOSD` skin contract nor a useful seek overlay. Full-screen playback
therefore had no visible, focusable controls. Aster now provides a TV-scaled
charcoal-and-gold control surface with dynamic title, series/episode context,
elapsed/total time, progress, previous/next, ten-second back, thirty-second
forward, pause/resume, stop and information actions. It also supplies the
minimal full-screen window contract and an Aster seek-progress overlay.

The disposable macOS client loaded both new windows without a skin exception.
Kodi's standard OSD action visibly opened the panel over a real Jellyfin
episode, left/right focus moved from Pause to the thirty-second control, and
activating it advanced the displayed time from 00:10:48 to 00:11:37 including
normal playback elapsed during the observation. Playback was then stopped.
All 73 skin tests, complete XML parsing and whitespace validation passed. The
pre-change installed skin is retained at
`/private/tmp/asterhome-kodi-osd-pre-20261017` for local rollback.

Playback stream controls, 2026-10-17 (skin v0.8.26): the OSD now adds a
secondary remote-first row for Audio, Subtitles and Quality, backed by an
Aster-styled implementation of Kodi's runtime settings dialog. A live
Jellyfin episode exposed its DD+ 5.1 audio stream and passthrough control, 35
subtitle streams plus enable/offset controls, and its active H.264 1920x1080
video stream. The Quality control opens Kodi's resolution selector when the
player publishes adaptive alternatives; for a direct-play Jellyfin file such
as this test, Kodi publishes one stream, so it instead exposes the current
resolution and video processing controls rather than inventing a transcode
ladder.

The previously inert Info control was repaired with an Aster full-screen
information contract. Live playback visibly opened the episode title,
series/episode/year, elapsed and total time, two-line synopsis and progress
overlay. Subtitle, audio, video and information dialogs all loaded without a
skin exception, and playback was stopped after validation. All 73 skin tests,
complete XML parsing and whitespace validation passed. The pre-change
installed skin is retained at
`/private/tmp/asterhome-kodi-stream-controls-pre-20261017` for local rollback.

Information-button correction, 2026-10-17 (skin v0.8.27): follow-up testing
identified that the earlier evidence invoked Kodi's global Info action rather
than activating the visible OSD button. The OSD button now explicitly closes
the controls and opens `fullscreeninfo`; navigating from Pause across to Info
and pressing that exact control visibly opened the Aster playback synopsis.
The Media landing-page More Info button was also corrected to return focus to
the selected media container before invoking its information action. Pressing
that exact button opened the selected episode's Aster detail page with title,
artwork and synopsis. Playback was stopped after the test.

Watch-state badges, 2026-10-17 (skin v0.8.28): Aster now projects Kodi's own
watched state onto the Media landing rails and TV/movie library cards. A small
background-free sage dot identifies an unwatched movie or episode, a sage
check identifies a fully watched title or series, and TV-show/season cards
show their live `UnWatchedEpisodes` total. Resumable items retain only the
existing progress bar, avoiding the contradictory combination of partial
progress and a watched check.

The disposable macOS client visually confirmed numeric badges including 1,
2, 3, 10, 13, 18 and 36 across the TV Shows grid, plus a watched-series check.
The landing page showed precise standalone dots on unwatched recommendations
and no watched mark over in-progress episodes. The implementation uses the
skin's 1920x1080 design canvas; Kodi scales that 16:9 canvas to the configured
output resolution. The pre-change installed skin remains available at
`/private/tmp/asterhome-kodi-watch-badges-pre-20261017` for local rollback.
All 74 skin tests, four bridge tests, complete XML parsing, Kodi-log inspection
and whitespace validation passed.

Version 1 production-candidate preparation, 2026-10-17: Jason accepted the
complete skin design and requested that it be called version 1 and prepared
for production while the hardware test remains pending. The skin and its three
private support components now identify as v1.0.0. Add-on metadata no longer
describes the accepted interface as a prototype, and the skin publishes its
approved Aster icon. A private release guide records install order, client
state, credential boundaries, 1080p-to-4K scaling, rollback and the exact
physical production gate.

The deterministic release builder produced four independently installable
ZIPs and a per-file manifest under the ignored local build directory
`services/kodi/dist/aster-home-v1.0.0/`. Independent tests confirmed repeatable
archive hashes, matching internal add-on IDs/versions, exclusion of tests,
build/pilot tools, SVG sources and caches, and refusal to overwrite a non-empty
output directory. The compact tracked release record is
`services/kodi/releases/aster-home-v1.0.0.json`. This milestone completes M3,
not M2/M5/M7: the release remains a production candidate until LibreELEC,
4K/HDR10, receiver passthrough, remote reconnect, resource and rollback tests
pass on the physical endpoint.

The installation rehearsal preserved all four prior disposable-client add-ons
under `/private/tmp/aster-home-v1-predeploy-20261017`, installed the generated
ZIP contents, and restarted Kodi. JSON-RPC and the Kodi log independently
reported the skin, genre plugin, Audiobookshelf bridge and UI-sound resource
enabled at v1.0.0; the skin and sound resource loaded without a dependency or
skin error, and the complete Media home artwork populated after normal library
refresh. Final validation passed 74 skin tests, four genre-plugin tests, 13
audio-bridge tests, three deterministic-package tests, 48 XML parses, all four
ZIP CRC checks, archive/manifest hash verification and whitespace validation.

YouTube v1 scope addition, 2026-10-19: Jason chose YouTube as the final v1
feature and deferred Blu-ray to a separate v2 decision. This remains within
the approved Stream A Kodi scope. The bounded change affects only the private
skin, release metadata and the disposable/physical Kodi clients; it creates no
new inbound network path and does not alter Jellyfin, media files or household
services. YouTube necessarily sends searches, playback and signed-in activity
to Google. Its API key, OAuth client secret, account session and history are
therefore client-private state and are excluded from Git and the release ZIP.
Rollback is the preceding v1 skin archive or Estuary fallback. Abort promotion
if the official add-on breaks skin loading, requires credentials in tracked
files, or cannot sustain the physical endpoint's agreed playback tests.

The skin now requires official Kodi Omega `plugin.video.youtube` 7.4.4 and
places YouTube between Music and Settings in both rail states. Selection opens
the add-on's maintained root catalogue; Aster's video browser recognizes its
folder path, heading and official installed icon without vendoring or
recreating YouTube artwork. The deterministic manifest declares the official
external dependency, while account provisioning remains a per-client install
step. Blu-ray code, optical-drive handling and DRM work are explicitly absent
from v1. Offline validation passed 75 skin tests, four genre-plugin tests, 13
audio-bridge tests, three package tests, complete XML parsing, deterministic
archive comparison and Git whitespace checks. Live sign-in, subscriptions,
1080p60/2160p60, dropped-frame and HDR behaviour remain part of the physical
LibreELEC gate rather than being claimed from the Mac layout check.

The disposable Mac deployment was checkpointed at
`/private/tmp/aster-youtube-predeploy-20261019`. Official Omega packages for
YouTube 7.4.4, InputStream Adaptive 21.5.25, InputStream Helper 0.8.6 and
PySocks 1.7.0 were installed from `mirrors.kodi.tv`; Kodi's database and
JSON-RPC independently reported all four enabled, and the updated Aster skin
loaded without a missing dependency or skin exception. Activating the exact
YouTube plugin URI reached its first-run setup wizard and created only local
add-on state. No API/OAuth credential or Google account was entered. The Mac
locked before visual rail inspection, so wizard choices, account sign-in and
playback remain an owner-present acceptance step rather than a completed
claim. A logged loopback-listener error on the locked Mac pilot must also be
rechecked after the wizard selects its default loopback HTTP setting; it does
not justify broadening the listener or opening a firewall path.

Post-unlock validation, 2026-10-21: the original temporary test app had been
partially purged and its replacement became stuck in macOS `dyld` after the
app icon modification required an ad-hoc signature. The stalled process was
terminated, the modified bundle was preserved at
`/private/tmp/Kodi-test-aster-icon-adhoc-20261021.app`, and an intact signed
copy from the mounted Kodi image was launched as
`/private/tmp/Kodi-test-fresh-20261021.app`. The existing profile, Aster skin
and add-ons were unaffected. Kodi reopened Aster Home, exposed its loopback
JSON-RPC listener, and the YouTube rail route rendered the official add-on's
13-item root catalogue in the Aster video browser. Opening Trending then
failed closed at the add-on's documented personal API-key requirement. This
confirms the navigation and skin integration but not Google Data API access,
account sign-in or playback. No Google credential was created, entered or
stored. The add-on's separate broadcast-address probe still logs macOS error
49 while its service continues; this does not justify a broader listener or
firewall change and remains a physical-client recheck.

YouTube playback follow-up, 2026-10-21: a selected item reached
InputStream Adaptive but failed because YouTube 7.4.4's HTTP helper attempted
to discover its client address by connecting a UDP socket to port zero.
macOS 26.6.2 returns error 49 for that probe, after which the add-on advertised
Kodi's stale `192.168.1.206` address even though the helper was listening only
on `127.0.0.1:50152`. A client-local compatibility change now returns the
configured address directly when the configured listener is explicitly
loopback (`127.0.0.1` or `::1`). The original installed file is preserved as
`http_server.py.pre-aster-macos-loopback-20261021` beside the add-on source.
After restarting Kodi, the listener remained bound only to `127.0.0.1`, the
generated manifest used `http://127.0.0.1:50152/`, InputStream Adaptive parsed
the VOD manifest, opened H.264 video, and sustained visible playback with the
Aster OSD. Playback was then stopped through Kodi JSON-RPC. The add-on also
logged a non-fatal `Please sign in` response from its first player client before
falling back successfully. This pilot-only compatibility change is outside the
release ZIP, may be overwritten by a YouTube add-on update, and is not assumed
necessary on LibreELEC; the physical endpoint must still test the unmodified
official add-on first.

### M2 HP ProDesk physical endpoint preparation — 2026-10-22

The physical endpoint changed from the non-destructive Lenovo X390 USB trial
to an owner-purchased HP ProDesk 400 G5 Desktop Mini intended for the Aster
Home appliance role. Read-only SSH inventory identified an Intel Core
i5-9500T (six cores), 16 GB RAM, Intel UHD Graphics 630, UEFI firmware with
Secure Boot enabled, Realtek gigabit Ethernet and a 256 GB Samsung
`MZVLB256HBHQ-000H1` NVMe system disk. The approved install target is that
NVMe device, serial `0025_3882_01C0_76BC.`. The owner explicitly authorized
erasing its Windows installation, BitLocker state, recovery partitions and
all other internal-disk data. This supersedes the X390 runbook's prohibition
on internal installation for this named HP endpoint only.

The owner also explicitly authorized erasing the attached 124 GB Kingston
DataTraveler 3.0, serial `6B00A94048C9`, to create the installer and declined
a backup of its 170 photo files because they were copies. LibreELEC Generic
x86_64 12.2.1 and the Aster Home v1 release bundle were transferred to
`C:\Aster-Staging`; the compressed image, official creator and Aster manifest
matched their recorded SHA-256 values after transfer. The official LibreELEC
USB-SD Creator required the current Microsoft-signed x64 Visual C++ v14
runtime, which was installed only on the disposable Windows environment.

The creator wrote the Generic image to the identity-checked Kingston. The
result has the expected GPT layout: a 1 GiB FAT `LIBREELEC` partition followed
by the 32 MiB installer partition. Windows mounted the writable FAT partition
and changed filesystem metadata, so the whole raw-device hash no longer equals
the immutable source image. Payload-level validation passed instead: the FAT
volume is healthy and its bundled `KERNEL.md5` and `SYSTEM.md5` both match the
written `KERNEL` and `SYSTEM` files exactly. This is sufficient to proceed to
the physical UEFI boot; installation to the Samsung NVMe has not yet begun.

The physical install subsequently passed those gates. The owner selected only
the named Samsung NVMe in the LibreELEC installer, removed the USB installer,
and the HP booted LibreELEC 12.2.1 from the internal disk. The first-run wizard
completed with hostname `AsterTV`. SSH was converted from the temporary
first-run password to public-key-only access, and the default password path was
disabled. A clean-profile recovery archive was created before add-on setup at
`/storage/.aster-checkpoints/kodi-fresh-profile-20261022.tgz`, SHA-256
`b375656fe99f46db730cba0c0df190ec00ff6d27e4949ec5a1a64d1e64689e4`.

### M2 HP ProDesk Aster/Jellyfin baseline — 2026-10-22

The hash-verified Aster Home v1.0.0 release bundle was installed on the clean
LibreELEC client together with its declared official dependencies. The Aster
skin and Aster UI sounds are active, the regional clock is 24-hour, and the
client is set to `America/Vancouver`. A physical 3840x2160 screenshot confirms
that the 1920x1080 Aster design canvas scales and renders on the Intel UHD 630
endpoint. A generic Kodi selection-dialog defect discovered during first-run
library selection had no remote route from the list to the confirmation button;
the source and deployed skin now add deterministic Up/Down focus links and a
selected-item marker. XML validation passed. This endpoint correction must be
included in the next deterministic release build rather than retained as
client-only drift.

The official Jellyfin repository v1.0.0 and Jellyfin for Kodi v2.2.0+py3 were
installed. The owner completed interactive authentication to the existing
Jellyfin 12.1.0 server as the `jason` account; no credential is recorded here.
Add-on playback mode and all approved video, music and collection libraries
were selected. Initial sync completed in 6 minutes 33 seconds. The final Kodi
databases contained 1,049 movies, 134 TV shows, 5,002 episodes, 17,095 songs,
1,331 albums and 1,043 artists. Reloading the skin after the one-time import
populated the Aster hero, Continue Watching and Recommended rails with live
Jellyfin-backed artwork and metadata at 3840x2160.

Read-only display inventory identifies an LG 4K HDR sink. Its EDID advertises
HDR static metadata type 1, PQ and BT.2020, but the current physical path offers
3840x2160 only through 30 Hz (plus 29.97/25/24/23.976), while 1920x1080 offers
60 Hz. This is a path limitation to isolate with the intended television/AVR
connection; it is not evidence that LibreELEC or UHD 630 cannot produce 4K60.
The current bench sink exposes PCH analog and Bluetooth but no HDMI passthrough
device, so receiver Dolby/DTS/Atmos acceptance is explicitly still untested.
At library-sync load the client used about 640 MiB of 16 GiB RAM, with observed
thermal readings around 46 C CPU and 33 C secondary, leaving the 232.7 GiB
storage volume effectively empty.

Bounded playback then proved the client path rather than library presence only.
A 1080p HEVC/AAC 5.1 film used Jellyfin's static direct-stream path with Intel
VAAPI decoding and no server transcode. A 3840x2160 10-bit HEVC HDR10 title at
about 83 Mb/s also used static direct stream and VAAPI. Kodi changed the DRM
connector colourspace from Default to BT.2020 YCC; the current sink must still
confirm its HDR indicator because the connector does not expose a readable HDR
metadata property. With refresh-rate adjustment changed from Off to **On start
/ stop**, 23.976 fps playback switched the display from 3840x2160p30 to the
advertised 3840x2160p23.98 mode and restored p30 after stop. Kodi's debug
overlay recorded video queue 99%, zero dropped frames, two startup skips and
one packet correction in the short high-bitrate sample. The same item exposed
TrueHD 7.1, AC3, E-AC3 and PGS choices; JSON-RPC selection of AC3 5.1 and a PGS
subtitle succeeded, and the Aster OSD rendered Audio, Subtitles, Quality and
transport controls at 4K. Current playback still decodes audio locally because
the bench path lacks HDMI audio. Definitive TV HDR10 indication, receiver
passthrough, selected-remote operation and destructive recovery drills remain
the M2 gates.

The physical selection-dialog fix is released reproducibly rather than left as
endpoint drift. Aster Home v1.0.1 bumps the four private bundle components in
lockstep, preserves v1.0.0 as an immutable prior artifact, and records the new
manifest and archive hashes in
`services/kodi/releases/aster-home-v1.0.1.json`. Two independent package builds
are byte-identical, all four ZIP CRC checks pass, all 75 skin tests pass, and
the video plugin, audio bridge and packaging suites pass. The complete v1.0.1
bundle was transferred to the endpoint, verified against the release hashes
and installed over a recovery checkpoint containing all four v1.0.0 add-on
directories and `Addons33.db`. Kodi reports all four v1.0.1 components enabled,
and the populated Aster interface and Jellyfin authentication survived the
upgrade.

The Jellyfin client initially displayed a startup warning because its optional
Kodi Sync Queue setting defaults on while that server plugin is not installed.
The endpoint's client setting is now explicitly off, with its previous settings
file retained at
`/storage/.aster-checkpoints/jellyfin-settings-pre-disable-kodisyncqueue-20261022.xml`.
This avoids adding a new server component during endpoint qualification; normal
server-event and manual library synchronization remain available. A clean Kodi
restart produced no Sync Queue 404, warning or error. A subsequent full endpoint
reboot also recovered without intervention: Kodi became active, all four Aster
components remained at v1.0.1, Jellyfin reported the retained user authenticated
and reopened its websocket, and the startup log contained no warning or error.
The host returned with about 15.3 GB of 16 GB RAM available, a 34 C CPU reading
and the 232.7 GB storage volume effectively empty. Estuary/profile restoration
and clean reinstall remain the destructive recovery drills still to prove.

A sustained high-bitrate playback gate then ran the same approximately 83 Mb/s
3840x2160 10-bit HEVC HDR10 title for 20 minutes. Every one-minute sample
reported speed 1 with monotonically advancing playback and cache positions;
the final Kodi process labels remained `ff-hevc-vaapi`, 3840x2160, 23.976 fps
and 99% cache. A three-second pause/resume cycle at minute 15 returned directly
to speed 1. Temperature stayed between 36 C and 38 C, Kodi RSS ended around
479 MB, and the host retained about 14.6 GB available RAM. The Ethernet counter
advanced by 10.35 GB during a measured 15-minute subsection with zero receive
or transmit errors. No buffer, stall, decoder or playback error occurred after
the one-time start transition. Stopping playback restored the GUI from the
native 23.976 mode to 3840x2160p30. The disconnected audio path continued to
emit the already-known ALSA sink warning and is not treated as an AVR result.
The sanitized endpoint sample log remains at
`/storage/downloads/aster-soak-20261022.log`.

The non-destructive interface fallback path also passed. Kodi changed from
Aster Home v1.0.1 to the retained Estuary skin, opened Estuary's Home window
and accepted an input action. It then changed back to `skin.asterhome` without
a restart, returned to Aster's Home window and retained the active Jellyfin
websocket. This proves that a skin-level failure does not strand the endpoint.
Another full endpoint reboot then retained Aster as the selected skin, started
Kodi, re-authenticated Jellyfin and reopened its websocket with no startup or
Sync Queue warning. Repeated cold boot is therefore closed. Restoring the full
clean-profile archive remains a separate destructive drill.

### M2 non-YouTube page and media sweep — 2026-10-22

The complete non-YouTube page sweep used live Kodi JSON-RPC state, bounded
playback and the client log rather than library presence alone. A TV series
opened its seven-entry season level and 139-episode all-seasons level; the
selected episode exposed series, season, episode, title, duration and synopsis,
then direct-played with the correct `S01E01` identity. Music exposed 25 recent
albums, 499 of 17,095 songs, 500 of 1,042 artists and 16 Jellyfin playlists.
An album opened its 13-track player and played; an individual song opened and
played; a Jellyfin playlist opened with 18 tracks and played; and artist
selection correctly filtered the album page. Each playback was stopped without
altering source media.

The refreshed Books snapshot exposed 558 records: 505 eBooks, 46 audiobooks
and seven podcast series. All three pages displayed real synopsis data and
cached art; an eBook produced the safe Calibre-Web reader handoff. Audiobook
and podcast playback could not complete because
`audiobooks.elliottrook.com` resolves internally to `192.168.50.23`, and the
client subnet cannot establish TCP/443 to that private reverse proxy. The
loopback audio bridge and private configuration are present and fail closed;
no TLS bypass, bearer URL, firewall broadening or alternate credential path was
introduced. A narrow reviewed network path remains a production prerequisite.

Daily Digest loaded 21 current stories and played its cached 18:56 MP3. The
physical client revealed that Kodi's absolute-time MP3 seek landed near 22
seconds for a requested 47.291-second chapter and then fell back near the
beginning. Percentage seek on the same verified duration landed at 49 seconds.
Aster Home v1.0.2 therefore converts the bounded chapter offset to a percentage,
verifies the resulting position and preserves the selected-story panel while
the normal two-second synchronization resumes. After deployment, story two
started at 54 seconds including startup time, audio remained active, and both
the active index and title matched story two. Breaking News independently
loaded 40 current story clusters.

The refreshed Home feed exposed one approved light, temperature, weather and
online camera status; the dashboard reported values ready. A one-minute local
timer counted from `01:00` to `00:58` with the expected 60-pip state and was
stopped cleanly. Camera UI state started and stopped correctly, but image fetch
failed because its URL remains the disposable Mac-only
`127.0.0.1:15102` tunnel. A production camera proxy/route is required; stale
or invented imagery was not substituted. Settings opened under Aster and Kodi
remained active. The only error-severity line in the final page sweep was the
Jellyfin player's benign “not playing any file” message after a deliberate
stop; there was no Kodi or skin crash.

The v1.0.2 deterministic release bumps the four private bundle components in
lockstep and records hashes in
`services/kodi/releases/aster-home-v1.0.2.json`. Offline validation passed 76
skin tests, four video-plugin tests, 13 audio-bridge tests, three UI-sound tests,
three packaging tests and `git diff --check`. Archive hashes matched after
transfer. The endpoint retained its per-client feeds and private bridge config,
all four components report enabled at v1.0.2, and the packaged Digest fix passed
the same physical story-two playback check. The pre-upgrade checkpoint is
`/storage/.aster-checkpoints/aster-v1.0.1-pre-v1.0.2-20261022.tgz`.
One final full endpoint reboot then returned Kodi with Aster v1.0.2 active,
Jellyfin authenticated and its websocket open, no active player and no startup
warning/error. The idle endpoint reported 14.6 GB available RAM and 34 C.

The evidence-backed v2 design review is recorded separately at
`docs/design/Aster-Home-v2-Recommendations.md`. Its priorities are a purpose-
built series/season/episode screen, global focus/search consistency, listening
queues and controls inspired by Plexamp/Audible, and a Home Assistant-style
section grid.

### M2 G20S Pro Plus receiver and control baseline — 2026-10-22

The owner connected the G20S Pro Plus USB receiver to the HP endpoint. It
enumerated as HAOBO Technology USB composite device `4842:0001`, exposing a
keyboard event device, a mouse/air-mouse event device and a 16 kHz mono USB
audio capture device. The receiver initially produced no key events, then
completed its own wireless handshake without a LibreELEC or Kodi change; the
owner confirmed that the remote began working normally.

Bounded Kodi and direct libinput capture mapped the required controls end to
end. Up, Down, Left, Right, Home, Volume Up, Volume Down, Mute and Play/Pause
arrive as their expected keyboard/media keys. The receiver reports OK as
mouse-left and Back as mouse-right, a known G20S Linux behavior that makes the
default Kodi interaction pointer-dependent. The narrow profile-level
`g20s-pro-plus.xml` compatibility map changes only those two buttons: OK uses
the bounded Aster Select dispatcher described below and Back remains Kodi Back,
with OK opening the OSD during full-screen playback. The owner turned
off air-mouse mode and confirmed that D-pad focus, OK and Back then behaved
correctly. The source and rollback guidance are retained under
`services/kodi/remote/`.

The endpoint rebooted and returned to active Kodi in about 16 seconds. Its USB
receiver re-enumerated automatically, although Linux assigned different event
numbers after boot; identity therefore follows USB vendor/product and device
name rather than a fixed `/dev/input/event*` path. Kodi restarted again after
keymap deployment and retained correct physical control. The microphone button
arrives as Linux scancode `0x246`, but Kodi assigns it no action. The USB
microphone can be opened through
LibreELEC's PulseAudio compatibility layer; an initial 5.6-second test WAV was
nearly silent. A subsequent 7.9-second press-to-talk sample had approximately
ten times the RMS level and a 4,137 peak. The existing Aster STT service
successfully transcribed the requested phrase as “Faster, find science fiction
movies”; only the leading wake word “Aster” was misheard. The temporary capture
source was unloaded, Kodi debug logging was disabled, and every temporary audio
copy was removed after the test.

The endpoint can reach the existing canonical Aster speech service directly at
`192.168.70.14:9130`; its unauthenticated health route returned HTTP 200. The
public reverse-proxy route timed out from this client and is unnecessary for
the private design. Voice search therefore remains an M4 client/authentication
integration, not a microphone, firewall or new-speech-platform requirement.
Least-privilege service authentication, button-triggered capture, transcript
routing, extended-idle reconnection and usable-range tests remain open. No
credential, firewall rule, persistent audio source or retained voice recording
was created by this baseline.

### Remote-first focus and activation refinement — 2026-10-22

The physical G20 trial exposed several focus-graph defects that were less
obvious with a mouse. Media's horizontal rows remembered independent item
positions, so moving vertically could jump to an unrelated tile; entering the
collapsed navigation rail stopped on its reveal chevron; and script-populated
Music and Books rows could miss Kodi's initial focus because their controls
were still empty when the window opened. The source and HP candidate now carry
the visible column between Continue Watching and Recommended, map each visible
Recommended position to the matching Genre choice, and map Genre back to the
nearest visible Recommended position. Entering the rail immediately selects
the current app route, while Music and Books explicitly establish the first
valid row selection after population.

The same milestone reduces Media's five library controls from 248 × 56 to
210 × 46, centres their wording, and retains the approved section icons.
Focused landscape cards and the portrait library grid now grow within their
layout cell, add a bounded shadow and use the sage focus ring; Music's selected
cover receives the same treatment. Daily Digest adds a separate **Play full
digest** action, makes it the initial action, and presents an opening state
before normal story synchronization begins. Story-specific playback remains a
separate action.

Before deployment, the complete previous skin directory was archived at
`/storage/.kodi/addons/skin.asterhome-checkpoints/pre-ui-nav-20261022.tar.gz`,
SHA-256
`e2084e84168a128f26db62f90adc6c88ac39aede554df00e4484499ce5ac8093`.
All 79 offline skin tests, XML parsing, Python compilation and
`git diff --check` passed. Live 3840 × 2160 captures confirmed the compact
labelled controls, enlarged Media/Music/library focus, selected Aster Media
rail entry and selected first eBook. The Music activation handler opened the
album player, the Books handler opened the bounded Calibre-Web handoff, and
full-Digest audio reached Kodi's queued/ready state before being stopped.
Kodi remained active and the post-test log contained no new skin error,
traceback or crash. No media, server, credential, network or remote Git state
changed.

### G20 OK activation hotfix — 2026-10-22

Physical use found that Kodi's normal Select action opened native TV and movie
items but did nothing on Music, Books and Digest rows populated through
`xbmcgui.ControlList.addItems`. Those items deliberately carry no direct media
path, and Kodi 21 did not dispatch the list-level skin `onclick`. The centre OK
button was therefore the correct control but had no action to invoke. The
separate Music hero action was also misleading: moving up to reach it changed
the selected album whenever the grid had more than one row, so it was removed.

The G20 can present OK as mouse-left or keyboard Return depending on its active
mode and wireless handshake; a debug capture on the production candidate
confirmed Return (`scancode 0x1c`) after the initial mouse-mode observation.
Both forms of OK now call a small bounded Select dispatcher. It
recognizes only the known Aster custom-window list controls for Music, the
Music player track list, Books and Digest stories and invokes their existing
activation handlers. Every other window and control is passed to Kodi's normal
Select action, while full-screen video and visualization mappings remain
unchanged. Music's grid now moves directly to its section tabs when leaving the
top row rather than offering the removed hero action.

The previous deployed skin tools, Music include and keymap are recoverable from
`/storage/.kodi/addons/skin.asterhome-checkpoints/pre-select-hotfix-20261022.tar.gz`,
SHA-256
`a03866592298b30d5cf82d0c309803da9a89c2eed0278507817287b9fda994bb`.
All 83 skin-tool tests, XML parsing and `git diff --check` passed. The endpoint
loaded the revised skin and keymap after a Kodi restart; invoking the exact
dispatcher used by OK on a populated Music tile opened
`custom_1121_albumplayer.xml` without a Python exception. A subsequent physical
G20 Return/OK press was logged as
`RunScript(special://skin/tools/select_dispatch.py)` and the owner confirmed
that the selected album opened. Debug logging was then disabled. The tile-focus
treatment deployed with the hotfix replaces the ambiguous lower shadow with a
contrasting ivory outer keyline and Aster-green inner ring across the Media
home rows, portrait library grid and Music grid while retaining the modest
size lift. These accepted changes are included in the immutable v1.0.3
deployment bundle, together with the separately installed and checksum-recorded
G20 profile keymap.

### Aster Home v1.0.3 deployment package — 2026-10-22

The owner authorized packaging and pushing the physically accepted HP
candidate for deployment to the BOSGAME production client. Version 1.0.3 bumps
the skin and all three private companion add-ons in lockstep. Its deterministic
bundle is under `services/kodi/dist/aster-home-v1.0.3/`; the source-controlled
release record is `services/kodi/releases/aster-home-v1.0.3.json`. The package
contains the four independently installable add-on ZIPs plus
`g20s-pro-plus.xml` as an explicit client file whose manifest target is
`userdata/keymaps/g20s-pro-plus.xml`. Profile state is therefore not mutated by
an add-on install, while the remote dependency can no longer be omitted from a
production-client handoff.

Manifest SHA-256 is
`4dc5a71855eaf0398e473de262e3a7a392e6d57a27ff75093ab699110f6aa47a`.
Archive SHA-256 values are `a62b6955...abcda` for the video companion,
`532ecd90...bcf90` for the audio companion, `cad5ad1c...b638` for UI sounds
and `20079850...24904` for the skin; the complete hashes and byte counts are in
the release record. The keymap SHA-256 is
`43f4d53fc5ae5dab269b587539950fb3894e937114074d6744ee9b259e5118db`.
Two independent builds were byte-identical. All 83 skin tests, four video-
plugin tests, 13 audio-bridge tests, three UI-sound tests and three packaging
tests passed, as did XML parsing and `git diff --check`.

This package is ready for the separately observed BOSGAME deployment gate; it
is not a claim that the BOSGAME has passed HDR10, receiver passthrough, remote
reconnection, camera/Audiobookshelf production routing or recovery validation.

### First v2 visual milestone — shared lightweight players — 2026-10-22

Jason authorized carrying the compact OSD language across every Aster player
and reducing heavy main-page chrome. A new shared player include now provides
compact transport, primary, secondary and Back focus treatments: unfocused
controls have no tile and focus receives a thin sage/gold ring. Video retains
all ten accepted controls and replaces its 1800 × 370 panel with a full-width
lower-edge gradient. Music, audiobook/podcast and Digest players retain their
existing actions, progress and content lists while replacing their enclosing
cards with open gradients. Music/Books page tabs, Media category controls,
search/filter containers and secondary Digest actions were also lightened;
primary actions and actual search fields retain explicit affordance.

Physical review immediately caught that fully transparent Media/Music/Books
navigation pills lost grouping and contrast over bright or detailed hero art.
The deployed correction gives those shared controls a translucent charcoal
backplate with ivory copy and retains the green focused state. Live 4K captures
of populated Media and Music pages confirmed consistent contrast without
restoring the former limestone/stone weight.

### Physical startup branding — 2026-10-22

The approved repository-owned 1920x1080 Aster Home startup image was installed
on the HP ProDesk in both supported layers: Kodi's profile override at
`/storage/.kodi/media/splash.png` and LibreELEC's OEM boot override at
`/flash/oemsplash.png`. Neither location had a prior override. A recovery record
was created at `/storage/.aster-checkpoints/aster-splash-pre-20261022/`; both
deployed files matched repository SHA-256
`738b96b4639c25634ad6639e3e2be9c9985e3f3d5606e8599e0804bea20d85e3`.
The boot partition was returned to read-only before reboot.

A full endpoint reboot returned host `AsterTV`, Kodi active and Aster Home
v1.0.2 loaded with no startup warning or fatal error. The two splash checksums
still matched after boot and `/flash` remained read-only. HP's logo is
firmware/POST output before LibreELEC owns the display; this milestone does not
modify firmware. A repeatable installer and rollback boundary are documented
in the skin README. LibreELEC's lookup order and `oemsplash.png` mechanism were
verified against its official init source and bootsplash documentation.

### HP main-TV HDMI audio recovery — 2026-10-22

After moving the HP to the main TCL television path, Kodi continued to open
the ProDesk's Conexant analogue output. Read-only diagnosis separated this
from Kodi configuration: DRM reported `card0-HDMI-A-1` connected and decoded a
valid 512-byte TCL `Beyond TV` EDID with LPCM, AC-3, E-AC-3, MAT/TrueHD,
DTS and DTS-HD descriptors, but ALSA created no HDMI PCM or ELD. The Intel
Kabylake HDMI codec existed and logged `HDMI: pin NID 0x5 not registered`;
codec pin 0x5 was active but its firmware default connectivity was `N/A`.

The persistent, narrowly scoped override
`services/kodi/libreelec/modprobe.d/aster-hp-hdmi.conf` sets
`snd_hda_codec_hdmi.enable_all_pins=1`. The deployed copy is
`/storage/.config/modprobe.d/aster-hp-hdmi.conf`, SHA-256
`fe53916c33af27ab8ae8491adf4108f88a1587495abd05631ba79146d1091935`.
The pre-change checkpoint is
`/storage/.config/modprobe.d/checkpoints/pre-aster-hdmi-20261022-130037/`.
After reboot the parameter read `Y`; ALSA exposed HDMI devices 3, 7 and 8;
HDMI 0 resolved to `Beyond TV`; and ELD 2.0 reported `monitor_present 1`,
`eld_valid 1` with ten audio descriptors.

Kodi's normal and passthrough device selectors were then changed to
`ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH`, with passthrough deliberately left
disabled until the receiver test. The pre-change Kodi checkpoint is
`/storage/.kodi/userdata/checkpoints/pre-hdmi-audio-20261022-130159/`.
Kodi subsequently opened
`hdmi:CARD=PCH,DEV=0,AES0=0x04,AES1=0x82,AES2=0x00,AES3=0x00` without fallback.
This proves device creation and sink selection; audible output and receiver
passthrough remain physical acceptance checks.

Jason then confirmed normal playback audio reached the main-TV path. Kodi now
prefers correctly tagged English audio and retains its default-stream
preference within that language. English selection therefore falls back safely
when no English stream exists, but cannot correct absent or incorrect source
language tags.

The video OSD's Audio action was also corrected. Audio now follows Info in the
ordinary left/right focus chain, the last secondary control wraps to Previous,
and Audio opens Kodi's focused audio-stream selector directly rather than the
larger audio-settings dialog. The endpoint checkpoint covering the prior OSD
and `guisettings.xml` is
`/storage/.kodi/addons/skin.asterhome.checkpoints/20261022-130837-audio-osd-passthrough/`.
All 83 skin regression tests and XML parsing passed before deployment. Manual
English-track selection and receiver-format indication remain physical
acceptance checks.

The initial physical check confirmed preferred-English selection, remote
navigation to the OSD Audio selector, ordinary playback audio and Dolby-path
passthrough. A subsequent DTS-HD MA 7.1 direct-stream test exposed a downstream
failure: Kodi opened the raw eight-channel passthrough stream successfully,
but the receiver produced no sound and the HDMI/eARC chain then remained mute
for direct two-channel PCM until the receiver was rebooted. Direct ALSA stereo
tests and an HP reboot did not recover the sink; rebooting the receiver did.
The ELD capability claim is therefore not sufficient evidence that this
TV/eARC/receiver route is stable for DTS passthrough.

The recovery profile retains the 7.1 decoded-PCM layout and enables only AC-3,
E-AC-3 and MAT/TrueHD passthrough. DTS and DTS-HD passthrough are disabled so
Kodi decodes those sources to multichannel PCM; AC-3 transcoding remains off.
The known-good stereo rollback is checkpointed at
`/storage/.kodi/userdata/checkpoints/pre-hybrid-audio-20261022-133213/`.
Dolby-format indication and DTS-to-multichannel-PCM playback remain physical
acceptance checks. M2's separate HDR indication, mixed-format soak, recovery
and production-client gates also remain open.

### Mixed Continue Watching repair — 2026-10-22

Playback diagnosis confirmed that Kodi and Jellyfin were recording resume
bookmarks correctly, including recently stopped movies. The Aster home rail
was nevertheless bound to an episode-only smart playlist, so films could never
appear and the result looked like a general tracking failure. The rail now uses
the read-only Aster media plug-in to merge resumable movies and episodes, order
them by `lastplayed`, retain their resume point and expose the original playable
library path. Media-type-specific JSON-RPC property sets avoid Kodi 21 rejecting
episode requests, and resume metadata is applied through Kodi 21's supported
`InfoTagVideo` API.

The endpoint was checkpointed at
`/storage/.kodi/addons/aster-checkpoints/20261022-133953-continue-watching`.
After deployment Kodi registered `plugin.video.asterhome` v1.0.3 and restarted
with the mixed directory loaded without plug-in, directory or focus errors.
Six media-library unit tests and 26 targeted skin-layout tests passed. A final
physical confirmation that the expected movie and episode cards are visible
remains useful but is not required to prove that resume data is being recorded.

### HP production-path CEC probe — 2026-10-22

A read-only probe on the production-connected HP confirmed that the active
`card0-HDMI-A-1` path carries HDMI video/audio, EDID and connector hot-plug
state, but exposes no operating-system CEC endpoint. There is no `/dev/cec*`
device or `/sys/class/cec` adapter, no CEC kernel module/device was registered,
`cec-ctl --list-devices` returned none, and libCEC 7.1.1 reported
`Found devices: NONE`. Kodi consequently has no libCEC peripheral to bind to.
The connected USB devices were the G20 receiver, Logitech Bolt receiver and
Intel Bluetooth; no Pulse-Eight adapter was present.

This is a hardware-path result rather than a Kodi mapping defect: CEC traffic
may exist elsewhere between the television and receiver, but the HP native
HDMI port cannot send or receive it through LibreELEC. The accepted G20 USB-HID
path remains the production control method. If CEC power/input integration is
later judged valuable, test a supported USB-to-CEC adapter as an optional v2
accessory; do not make it a v1 production dependency.

Current Pulse-Eight guidance rules out an inline deployment for Aster's target:
the adapter is specified inline for 4K60 4:2:0 8-bit, while HDR10 is outside
spec and high-bitrate TrueHD/Atmos is identified as unreliable. The HP is
currently driving the TCL `Beyond TV` at 4096×2160/24 Hz and direct playback
switches to 4096×2160/23.976 Hz; the EDID advertises HDR-capable deep colour,
4K60/120 modes and the receiver audio formats. Preserve that accepted media
path. A future trial should use the vendor's two-cable method: native HP HDMI
directly to the existing TCL input for video/audio, plus a spare HP DisplayPort
through DP-to-HDMI and the USB-CEC adapter to a spare TCL HDMI input for CEC
only. This topology is expected to expose TV/receiver standby, active source,
volume/mute and compatible remote commands, subject to physical testing of the
specific TCL/eARC/receiver bus and HP USB suspend behavior.

All skin XML parsed, `git diff --check` passed, and 76 skin, four video-plugin
and 13 audio-bridge tests passed. Before deployment, the physical endpoint's
affected XML was checkpointed at
`/storage/.kodi/addons/skin.asterhome.checkpoints/20261022-player-ui/`.
LibreELEC loaded the revised includes and custom windows after repeated Kodi
restarts without a warning, error or crash. Live 3840 × 2160 captures verified
the open Music landing page, Music player, populated Digest page and video OSD;
bounded Jellyfin playback confirmed the new OSD title, timeline, initial
Play/Pause focus and all control labels render over moving video. This is a
source-deployed visual candidate, not a new release package or completion of
the remaining v2 recommendations.

### BOSGAME production deployment and Jellyfin recovery — 2026-10-22

The BOSGAME E3 Neo production candidate was installed with LibreELEC 12.2.1
and Kodi 21.3 on its internal 512 GB NVMe after the owner explicitly approved
overwriting Windows. Its hostname is `AsterTVProd`; the observed deployment
address is `192.168.1.157`. The pre-Aster profile checkpoint is
`/storage/.aster-checkpoints/20261022-pre-aster-v1.0.3.tar.gz` with SHA-256
`91e6fa86607d789eb884e13e6f0e1d642637bf6641a0d2a28b8da5cd6301b868`.
The four Aster v1.0.3 components, startup artwork, G20 profile and official
YouTube and Jellyfin add-ons were installed. The system presents the Aster skin
at 3840×2160/60 Hz and exposes the LG HDR display's HDMI audio capabilities.

The first Jellyfin setup attempt exposed a production keymap defect. The G20
Select mappings called `special://skin/tools/select_dispatch.py`, so switching
to Estuary for recovery made Return, Enter and left-click invoke a script that
did not exist in the active skin. Jellyfin's custom first-run dialog then
became unusable and two forced restarts coincided with complete endpoint
unresponsiveness. No i915, NVMe, OOM, watchdog or filesystem fault was recorded;
the failure followed the dialog/input path. Recovery stopped Kodi during boot,
quarantined both the keymap and Jellyfin add-on, and restarted cleanly.

Authentication was completed without exposing a password: a Jellyfin Quick
Connect request was initiated directly from the production endpoint, approved
by the owner, exchanged locally, validated against `/Users/Me`, and saved only
in Jellyfin's protected profile data. Jellyfin then reported `User is
authenticated` and opened its websocket. Add-on playback and all five eligible
libraries plus Collections were selected; the initial full synchronization
completed cleanly across Archive Movies, Archive TV, Movies, Music, Shows and
Collections. The server currently returns 404 for the optional Kodi Sync Queue
settings endpoint; initial synchronization and websocket operation are proven,
while server-side Sync Queue compatibility remains a follow-up check.

The production keymap now uses the stable dispatcher path
`special://home/addons/skin.asterhome/tools/select_dispatch.py`. This preserves
Select behavior when Estuary or another recovery skin is active. XML validation
passed, the corrected map loaded after restart, Aster Home v1.0.3 loaded, and
Jellyfin reauthenticated with its websocket open. The immutable v1.0.3 bundle
still contains the original keymap and must not be used for another deployment
without this corrective overlay or a superseding release package.

### BOSGAME LibreELEC 12 failure and LibreELEC 13 live recovery — 2026-10-22

The internal LibreELEC 12.2.1/Kodi 21.3 installation on the BOSGAME E3 Neo was
not production-stable. The whole endpoint repeatedly became unresponsive within
roughly 40 seconds, including local input, ICMP and SSH. The failure reproduced
with Estuary, third-party add-ons disabled and Kodi stopped. Immediately before
one lock the load average rose above 38,000 while memory remained available;
there was no corresponding OOM, NVMe, filesystem, i915 reset or watchdog
evidence. Firmware also emitted unresolved ACPI `\_SB.UBTC.RUCC` errors. Adding
`intel_idle.max_cstate=1` to both internal boot configurations and disabling the
firmware's master C-state control did not resolve the lock.

The retained Kingston installer was copied to both the Mac and HP before it was
reused. The Mac backup is
`/tmp/Kingston-LibreELEC-12.2.1-installer-backup.tgz`, SHA-256
`f0e15dc736570017390a855ccaba2019c4319a1b17eab68e227ff98f36fee5f3`;
the HP retains the same archive under `/storage/`. The USB was then written and
read back byte-for-byte with official Generic x86-64 LibreELEC 13 nightly
`20261021-440640e`; the raw-image SHA-256 is
`5a01c84f31c613bbc942d6cb663f57838e0e34738bff299aa508cd9b808cb52a`.
The first write exposed an HP USB-port/automount path problem; changing ports,
temporarily masking only the two udevil mount units and rewriting produced an
exact readback. The BOSGAME booted this media in `live` mode as `AsterTVTest`,
leaving the internal NVMe untouched.

LibreELEC 13 uses Linux 7.3.0 and Kodi 22.0 on this image. The live system
remained responsive for more than an hour with low load and about 14.4 GB of
available memory. Deep-idle C6/C8/C10 counters continued to advance, including
substantial C10 use, which indicates that the newer kernel handles this
platform without the unsuccessful C-state restriction. No GPU reset or new
kernel error occurred during the trial.

Bounded playback passed at 3840x2160/60 Hz with 10-bit output for official
Jellyfin Creative Commons HEVC 10-bit SDR, HEVC HDR10 and AV1 10-bit SDR
samples, each at 40 Mbit/s.

The exact Aster Home v1.0.3 four-component bundle and official YouTube 7.4.4
were then staged into the disposable live profile. All 83 local Aster skin
tests and `git diff --check` passed before transfer, and remote package hashes
matched the local artifacts. Kodi registered the sideloaded packages disabled,
so its add-on database was checkpointed and the four Aster entries were enabled
before activation. Kodi 22 then loaded `skin.asterhome` v1.0.3 at 4K60. The
post-load observation showed no XML failure, Python traceback, GPU reset,
memory pressure or rising load, and manual navigation remained responsive.

This is a compatibility and stability pass for the pinned nightly, not approval
to erase or rewrite the BOSGAME internal NVMe. A production install requires a
fresh explicit destructive authorization, preservation of the live recovery
USB and deployment of the corrected stable-dispatcher keymap rather than the
uncorrected immutable v1.0.3 keymap.

### AsterTV production startup lockup — 2026-10-22

The separately approved `AsterTV` production lockup was retrieved from the
private Forgejo release `aster-brand-v2-tv-2026-10-22` and used without
redrawing or substitution. The release ZIP matched published SHA-256
`6a888ef158f9272f56e73c84494b20c7d7190a6e474deed403e6c72b474c95b0`;
the selected 1254 px PNG matched
`f54e9e3da5b03b99e0fd2fc25ca903b8bdc6fe0893612a893cbe21b31b9c412e`.
The checksum-pinned builder composed the lockup on the existing 1920x1080
dark-green startup canvas, producing repository and deployed SHA-256
`912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce`.

On `AsterTVProd`, both `/flash/oemsplash.png` and
`/storage/.kodi/media/splash.png` were replaced with that same image so the
LibreELEC and Kodi startup stages retain one identity. The previous Aster Home
pair remains at
`/storage/.aster-checkpoints/aster-startup-branding-20261022-203418/` and
matches its prior SHA-256
`738b96b4639c25634ad6639e3e2be9c9985e3f3d5606e8599e0804bea20d85e3`.
After a controlled reboot Kodi returned active, both deployed hashes persisted,
and `/flash` was read-only. No library, playback, remote-control or firmware
state was changed by this branding cutover.

### BOSGAME unattended audit and v1.0.4 package — 2026-10-22

An unattended-safe audit confirmed the internally installed LibreELEC 13
nightly `20261021-440640e`, Kodi 22 RC1 and Aster Home v1.0.3 remained active
after the branding reboot. The endpoint renders through Intel ADL-N graphics
to the attached LG HDR 4K sink and has 467 GB free in `/storage`. Jellyfin
re-authenticated after controlled Kodi restarts and reopened its websocket.
Read-only database counts were 1,049 movies, 208 shows, 6,157 episodes, 129
sets, 1,043 artists, 1,334 albums and 17,113 songs. The count changes from the
earlier sync record are normal library updates rather than a new local import.

A scripted shell-navigation sweep opened Books, Digest, Home, Music, Albums,
Artists, Songs, Playlists, eBooks, Audiobooks, Podcasts, the music player and
Breaking News, then returned to Home. Kodi did not crash. Script-populated
lists emitted transient initial-focus warnings during the artificial one-second
sweep; their post-population focus path remains covered by tests and requires
normal-speed owner review rather than being claimed visually from this run.
The audit exposed missing client state rather than code failures: this profile
has no `books.json` or `home.json`, no Audiobookshelf `client.json`, and no
music playlist files. Accordingly Books/Home use their bounded unavailable
states, Audiobookshelf playback is not ready, and Playlists is empty. Digest
and Home household data, credentials and personal playlists were not copied
from another endpoint during the unattended test.

The approved AsterTV splash changed the packaged skin, so immutable v1.0.3 was
not rewritten. The four add-ons were versioned to 1.0.4 and a deterministic
local bundle plus release record were generated. Validation passed 83 skin,
6 media-plugin, 13 private audio-bridge, 3 UI-sound and 3 packaging tests. The
live endpoint remains on v1.0.3 until the v1.0.4 install and rollback checkpoint
are exercised as a separate bounded deployment. After diagnostics, Kodi was
restarted cleanly, its loopback JSON-RPC listener had no retained connections,
Jellyfin reported `User is authenticated`, and the websocket reopened.
The six v1.0.4 artifacts were staged without activation under
`/storage/.aster-staging/aster-home-v1.0.4/`; remote SHA-256 readback matched
the release record for every file and Kodi remained active.

An additional device-side verification opened every staged ZIP, passed its CRC
test, matched the archive and every packaged-file SHA-256 against the manifest,
parsed each `addon.xml`, confirmed all four add-on IDs at version 1.0.4, and
parsed the staged G20 keymap XML. Before any activation, the running v1.0.3
add-on directories and working G20 keymap were archived and read-tested at
`/storage/.aster-checkpoints/aster-v1.0.3-pre-v1.0.4-20261022.tar.gz` (SHA-256
`6ca70eb38aa1ed338636dde10b4ddbb5f5e8ee57347fac2dfda435f2a0af6756`,
4.4 MB). A second read-only comparison opened the archive and matched all 156
files byte-for-byte to the running v1.0.3 installation. The BOSGAME has 467 GB
free in `/storage`; this checkpoint does not
include household feed data, credentials, media databases or watched state.
The endpoint was deliberately left running v1.0.3 pending an attended visual
promotion and rollback test.

The attended promotion installed all four v1.0.4 components, preserved the
working keymap and restarted Kodi cleanly. Jellyfin reauthenticated and opened
its websocket without an XML, Python or startup error, and the owner accepted
the rendered home view. Physical capture then proved that this G20 receiver's
centre button emits Linux `KEY_SELECT` (code 353), a mode not covered by the
first v1.0.4 keymap. Adding the explicit Select route restored Music album
activation. A second defect was isolated to the Music player: its track list
is control 50, while the dispatcher incorrectly checked Back control 9000.
Correcting that ID restored direct track selection, which the owner verified.
The deterministic v1.0.4 package was rebuilt so the release keymap and skin
contain both tested corrections; the superseded local build was retained only
in `/tmp` during validation and is not a release artefact.

The same attended pass confirmed episode playback, the lightweight OSD, both
audio and subtitle selectors, and full-Digest playback. Selecting an individual
Digest story initially exposed a player-readiness race: Kodi reported a newly
opened cached VBR MP3 as seekable before its demuxer had stabilized, then reset
some accepted percentage seeks to the beginning. The final handler uses Kodi's
documented absolute-time seek object, reuses the current briefing player when
possible, and waits for a newly opened player to advance before seeking. The
owner verified both a cold single-story start and selecting a second story
while the briefing was already playing. The final deterministic v1.0.4 package
and staged device copy include this correction.

A normal-speed automated sweep subsequently loaded Books, Digest, Home, Music,
Albums, Artists, Songs, Playlists, eBooks, Audiobooks, Podcasts and Breaking
News with the expected custom window and a usable focused control where data
was available. Kodi stayed active. A clean Kodi restart then reloaded the
v1.0.4 keymap and skin, reauthenticated Jellyfin, reopened its websocket,
opened a Music album, started a selected track and stopped playback. The
post-restart log contained no XML, Python, Kodi error or traceback, and the
three live corrected-file hashes matched the final package source.

### BOSGAME stop playback on player exit — 2026-10-23

Owner testing established that explicit Stop saved Tow to Continue Watching,
whereas Back left video playing behind the library. The G20 fullscreen
right-click/Back mapping explicitly used `Fullscreen`. Reopening that same
playing Jellyfin item could seek it to zero and fail plugin resolution, after
which Jellyfin received a zero resume position. These observations explain the
reported workflow failure; the separate intermittent receiver-volume jump is
unresolved and further investigation was deferred at the owner's request.

After explicit deployment approval, changed fullscreen video and visualisation
Back inputs to Stop and added conditional `PlayerControl(Stop)` unload actions
to VideoFullScreen, MyMusicNav (Books listening), the Music player and Digest.
Player dialogs retain their existing dismissal behavior. Prior files are
recoverable at
`AsterTVProd:/storage/.aster-checkpoints/stop-on-player-exit-20261023/`.
All five deployed hashes match source; deployed XML parsed successfully, 26
layout checks passed, and Kodi restarted, loaded the G20 keymap and authenticated
Jellyfin. The owner then confirmed the Tow resume/Back test worked: Back stopped
playback and preserved the updated Continue Watching position. Exit behavior on
Music, Books listening and Digest still needs a physical regression pass.
This is a source-tracked hotfix on the BOSGAME; the immutable v1.0.4 release
bundle has not been republished. Packaging determinism checks passed, but the
tracked-release comparison correctly fails until a new release records the
changed files. The HP did not receive this hotfix.

### BOSGAME Books and private audio provisioning — 2026-10-23

Owner explicitly approved catalogue/covers deployment, secure reuse of the
existing restricted audio configuration and an exact BOSGAME HTTPS rule.
The fresh source export contains 505 Calibre eBooks, 46 Audiobookshelf
audiobooks and seven subscribed podcasts. All 558 records passed the deployed
feed reader, and 554 existing JPEG covers matched their catalogue IDs.
Installed under `AsterTVProd:/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/`.
Books remains a read-only catalogue and external Calibre-Web reader handoff;
the LibreELEC endpoint displays the reader URL for another device.

The prior connection timeout was an ingress firewall deny. Added only rule
`feb35a23-036b-494a-9d37-a61509de25ff`, LAN sequence 3091, TCP
`192.168.1.157` to `192.168.50.23:443`. OPNsense checkpoint:
`/conf/backup/config-before-aster-books-20261023-205452.xml`.
After filter reload, the exact rule appears in live pf output and the BOSGAME
receives certificate-validated HTTPS 200 from Audiobookshelf. Calibre-Web
returns its expected authentication redirect over the same existing HTTPS
gateway. No other client, backend or public access rule was added.

Reused the owner's approved existing Audiobookshelf configuration through SSH
without printing its key or persisting it locally. Verified account `jason`
is active, type `user`, with upload/update/delete disabled and download enabled.
It is an existing shared user identity, not a newly created per-device identity.
The BOSGAME config is mode 0600 beneath a 0700 profile; no credential entered
Git. Setup checkpoint directory:
`/storage/.aster-checkpoints/books-setup-20261023/` (prior audio profile was empty).
Kodi restarted and logged `Aster Books Audio: loopback bridge ready`.
Read-only bridge probes resolved 36 audiobook chapter entries and seven podcast
episode entries; each first entry returned HTTP 206 and 4096 requested audio
bytes. Receiver-audible playback, chapter selection and Books Back-to-stop
remain owner acceptance checks. The bridge still does not synchronize listening
progress back to Audiobookshelf.

Remaining operational gap: Books is a manually published snapshot with a
24-hour freshness limit. This deployment did not create a recurring publisher;
the catalogue needs an approved refresh workflow before unattended acceptance.
Do not extend timestamps on old data or remove freshness checks to conceal
that gap. To refresh manually, use the existing source exporter with its
destination redirected to a private staging directory, validate with
`book_catalogue`, then publish the new `books.json` to the endpoint. Covers
remain cached separately. To roll back provisioning, stop Kodi, move the new
feed/audio profile files into a recovery directory, remove only the recorded
firewall UUID and reload filters, then restart Kodi. Preserve shared source
libraries and the HP configuration.

### Books chapter entry-focus correction prepared — 2026-10-23

Owner reported a chapter-selection dialog asking to choose a book. Live Kodi
inspection found Music window 10502 initially selected its `..` parent entry;
activating that entry requested the add-on root without an action/item ID and
raised the dialog. Owner subsequently confirmed actual chapter playback works.
Prepared `books_player.py` to wait for list population and focus entry 1 only
when entry 0 is the Books parent. Updated Select dispatch to route the Books
parent to Books home and the visible Back button to the same destination.
Existing chapter selections and native selection of playable entries are
preserved. Three focused tests, four Select-dispatch tests and 26 layout tests
pass. Prior deployed navigation files are checkpointed at
`/storage/.aster-checkpoints/books-chapter-focus-20261023/`.
Automatic approval review rejected code deployment because `continue` was not
accepted as the repository's immediate remote-write confirmation. No focus-fix
code was deployed at that stage. The owner subsequently explicitly approved
deployment and unattended follow-up testing.

The first live focus check found the initial implementation returned before
Kodi activated window 10502. Corrected it to wait for window activation and
directory population and use native `SetFocus(50,1,absolute)` rather than a
Python ControlList wrapper. Deployed after the owner's approval, preserving
the recorded checkpoint. Live checks now show Opening Credits at position 1;
selecting it activates Kodi's audio player. Selecting Chapter 2 starts at
12:01 with playback speed 1. A podcast opens on its first actual episode,
starts playback and advances to 00:02. Back leaves no active player for both
types. The owner also confirmed Music and News stop on exit. Receiver-audible
output is not inferred from these unattended player-state checks. Kodi remains
active; transient native-list initial-focus messages remain in its log.

Prepared a new immutable local v1.0.5 candidate and tracked release record,
containing stop-on-exit, the G20 Back mapping and Books focus fixes. The old
v1.0.4 record is preserved. All 111 checks pass: 86 skin/tools, 13 audio bridge,
six video plugin, three sound pack and three deterministic packaging checks.
Local artifacts are under `services/kodi/dist/aster-home-v1.0.5/`; the release
record contains archive and manifest hashes. BOSGAME remains version-labelled
1.0.4 with the tested source hotfixes; a full v1.0.5 package promotion was not
performed. HP is unchanged. No push was authorized or performed.

On asking whether audiobook/podcast progress is saved, the owner was informed
explicitly that the current bridge does not save/restore listening progress.
Resume currently means choosing a chapter manually; selecting a chapter starts
at its boundary and a podcast starts at its beginning. Cross-device resume
through Audiobookshelf remains unimplemented and must not be claimed from the
successful stop-on-exit tests. Catalogue refresh and listening-progress sync
remain the next substantive tasks.

### Pre-production beta scope decision — 2026-10-23

Owner accepts leaving the v1 eBook handoff/catalogue as-is because the useful
large-screen reader/TTS experience is deferred to v2. YouTube API provisioning
and playback tests are explicitly deferred until the owner has time; do not
claim YouTube passed. A subscription video downloader is undecided and is
excluded from the v3 roster; research alone does not authorize implementation.

Near-term beta follow-up is normal-use stability, cold-start/remote reconnect
after the latest hotfixes, and consolidating the tested BOSGAME hotfixes into
the prepared v1.0.5 release and current recovery checkpoint before promotion.
The shared Books feed still expires after 24 hours, including audiobook and
podcast catalogue entries, so waiving eBook usefulness does not resolve that
operational limitation if audio browsing is expected to remain available.
Listening progress sync is accepted as v2 work. Camera production routing and
formal display/receiver/recovery gates remain separately documented; normal
use acceptance must not be represented as comprehensive hardware certification.

### Family beta consolidation and catalogue refresh — 2026-10-23

The owner requested the remaining catalogue-refresh and release/recovery work,
then explicitly approved v1.0.5 deployment, a six-hour refresh timer and a brief
Kodi stop for a verified private backup. No HP v2 deployment was authorized or
performed by this change.

Added a bounded `refresh_books.py` client and LibreELEC systemd oneshot/timer.
It uses the existing 0600 Audiobookshelf configuration and HTTPS access, reads
accessible audio libraries with pagination, sanitizes IDs/titles/descriptions,
validates the complete feed and atomically publishes it. It downloads missing
bounded JPEG covers only, never book/audio content. The owner-accepted frozen
Calibre entries are retained with their original `ebook_snapshot_at`; new audio
capture time is recorded separately. Redirects are rejected so the bearer
credential cannot follow a login/cross-origin redirect. An unexpectedly empty,
incomplete, oversized or invalid response fails before replacing the old feed.
A single-instance lock prevents overlapping refreshes. The timer starts after
boot and every six hours; failures leave the last good feed unchanged and are
visible through systemd Result/journal and the last-success status file.

All 115 checks passed: 90 skin/tools, 13 bridge, six media plugin, three sound
pack and three deterministic packaging checks. Before promotion, device-side
archive CRCs, every packaged file hash and all client-file hashes passed.
The only differences from the running hotfix baseline were four add-on version
descriptors and the new refresh tool. All 151 release files matched after
installation, and Kodi JSON-RPC reports all four enabled add-ons at 1.0.5.
Two refresh executions both yielded 46 audiobooks, seven podcasts, 505 retained
eBooks and zero missing audio covers. The timer is enabled, its next execution
is scheduled and the service reports success. Kodi restarted with Jellyfin
authenticated and the private audio bridge ready, without startup errors.

Pre-promotion backup:
`/storage/.aster-checkpoints/aster-v1.0.5-prepromotion-20261023/kodi-profile-config-and-boot.tar.gz`,
SHA-256 `5a3d34c754968f4f628125b9943722761f65c798a1bf39cff5d38ab62ddc5e1a`;
2,943 archived regular files matched their stopped-source bytes.
Working v1.0.5 recovery backup:
`/storage/.aster-checkpoints/aster-v1.0.5-accepted-20261023/kodi-profile-config-and-boot.tar.gz`,
SHA-256 `9ee417f6afae3f73d3b5cf2cbfa5fffa3560df4c66fe72c6a62a19a237c49c0f`;
2,955 archived regular files matched source. Includes Kodi add-ons/userdata,
private credentials, remote mappings, LibreELEC service/network configuration,
SSH authorization and boot config/branding. It excludes source media and the
OS disk image. A partial first attempt using incompatible BusyBox tar multiple
`-C` semantics was retained as `failed-busybox-backup.tar.gz` and is not a
recovery candidate; the accepted backup was recreated and verified with Python.

The accepted 157,437,807-byte archive and checksum are also stored outside Git
at `/Users/jelliott/lab/private-backups/aster-tv/bosgame/2026-10-23-v1.0.5/`.
The Mac copy is mode 0600 under private directories and its checksum matches
the endpoint. Both backups contain secrets and must not be published or added
to Git. This is archive-integrity/file-match evidence, not a destructive restore
drill or proof of cold-boot recovery. The retained installer and pinned OS
baseline remain prerequisites for a replacement-disk restore.

Operator handover: family beta can continue on BOSGAME v1.0.5. Back stops
playback and movie/episode resume is available through Jellyfin; audiobook and
podcast listening-progress sync remains accepted v2 work. Books audio catalogue
refresh no longer depends on the Mac. YouTube tests are deferred, eBook TTS is
v2, and the downloader is excluded from the v3 roster. A future cold-start and
remote/receiver reconnect check remains owner-observed. The HP is the nominated
v2 lab endpoint and should not receive production changes automatically.

Integration impact: no new network/DNS/authentication access, household identity
or media authority was introduced. The new endpoint-local job uses the existing
restricted account and is covered by the profile backup; operational health is
currently handed to systemd plus `refresh-status.json`, with no new centralized
Doctor/Beszel alert claimed. NetBox/addressing, rack and Homepage facts are
unchanged. No push was performed.

### HP baseline alignment and v2 scope hold - 2026-10-23

The owner requested HP alignment to Aster v1.0.5, then a feature-development
hold while reviewing a printable v2 list. No formal v2 project was started.
The six-page review inventory is `../../output/pdf/aster-v2-scope-review.pdf`.
After the owner selects the scope, only obvious corrective defects from the
v1.0.5 family beta may be automatically added; new ideas require a later list
or explicit scope-change approval. The HP is the future lab endpoint, not a
reason to begin v2 before review. No push was requested or performed.

HP `192.168.1.140` (`AsterTV`) was reachable on LibreELEC 12.2.1 / Kodi 21.3.
Its prior Aster versions were mixed: skin, Books audio and sound pack 1.0.2,
media plugin 1.0.3. Staged the unchanged accepted v1.0.5 artifacts; validated
archive integrity, all manifest hashes and paths before mutation. Stopped Kodi
for a private profile/config/SSH/boot-branding checkpoint and verified all
3,506 regular archive members against the stopped source. Checkpoint:
`/storage/.aster-checkpoints/aster-v1.0.5-prepromotion-20261023/kodi-profile-config-and-boot.tar.gz`,
SHA-256 `0cf823e3960509eaca5cc4012d795903da835ec3bbb2341b76f31e0d53ccb302`.
It contains credentials and is not a release artifact or Git content. No
destructive restore drill is claimed.

An off-device copy is retained outside Git under the private Mac directory
`/Users/jelliott/lab/private-backups/aster-tv/hp/2026-10-23-v1.0.5/`; its
SHA-256 matches the device checkpoint. Archive and checksum permissions are
0600 and the destination directory is 0700.

Installed all four add-ons and the packaged keymap/refresh units without
altering the OS, firmware, Jellyfin identity or audio settings. All 151
packaged files match and all four add-on descriptors report 1.0.5. Kodi is
active; logs show Jellyfin authentication and the private Books loopback
bridge ready. Kodi 21 logs an unsupported keyboard `select` key name in the
shared keymap (the map also has Enter/mouse handling); physical remote parity
is not claimed from file verification alone. Retain this compatibility finding
as a beta follow-up rather than silently changing the immutable package.

HP HTTPS to `audiobooks.elliottrook.com` / `192.168.50.23:443` times out.
The BOSGAME allow rule is source-specific and does not authorize the HP.
Requested a separate bounded source `192.168.1.140` TCP/443 permission; no
firewall mutation was performed at this checkpoint. Refresh units are staged
but activation is pending access approval/validation. The existing last-good
catalogue is preserved. Thus release-file parity is verified; functional
Audiobookshelf/network parity is not yet claimed.

### HP audiobook/podcast access parity approved and validated - 2026-10-23

The owner explicitly approved bringing HP audiobook/podcast access to the
production unit's level. Rechecked the existing BOSGAME source-specific rule
and created only HP LAN IPv4 TCP `192.168.1.140` to `192.168.50.23:443`, sequence
3092, UUID `d8c1a44e-e726-4442-99e2-2093f209799e`. This permits the private HTTPS
gateway, not only one hostname at layer 3; application authorization remains
the existing restricted Audiobookshelf identity. No subnet-wide access,
direct non-TLS service path, camera permission or new identity was added.

OPNsense private configuration checkpoint was byte-verified before mutation:
`/conf/backup/config-before-aster-hp-books-20261023-220349.xml` (host timestamp).
Filter reload returned OK; the effective pf rules contain the exact source,
destination, TCP/443 and UUID. HP HTTPS now returns HTTP 200 with certificate
verification enabled. Rollback is to remove only this UUID and reload filters,
not overwrite unrelated subsequent firewall changes from the full checkpoint.

Started the already-packaged `aster-books-refresh.service`, then enabled its
timer. Two service executions succeeded, with 53 audio items (46 audiobooks,
seven podcasts), 505 retained eBooks and zero missing audio covers. Last
success was `2026-10-23T22:04:04+00:00`; the active/enabled timer schedules its
next six-hour run around 21:04 Pacific on 23 October. The existing private
client configuration remained unchanged; no secrets were printed or copied.

Exercised the running Kodi loopback audio bridge, resolving an actual
audiobook to 36 chapter entries and a podcast to seven episode entries.
Fetched the first and last entry of each using bounded 4,096-byte range
requests: all four returned HTTP 206 with matching Content-Range and actual
audio/mp4 or audio/mpeg bytes. No capability URLs were logged, no source media
was retained, and no Kodi navigation or active playback state was changed.
This proves metadata and range-stream delivery, not an owner-observed audible
listening test. The first diagnostic used the normalized catalogue field names
against the raw feed and selected no items; correcting the diagnostic to use
`media_type`/`authority_id` passed without changing production code.

HP Aster v1.0.5 now has the same configured Audiobookshelf access/refresh path
as BOSGAME. Listening progress synchronization is still the accepted v2 gap,
not a v1 claim. Unit result/status files and journal remain the bounded local
health handoff; no new central Beszel agent, service host, addressing, DNS,
certificate, Homepage link, public exposure or speech implementation was
introduced. Existing profile backups and the OPNsense checkpoint cover the
affected configuration. All v2 feature work remains on hold for scope review.

## 15. References

- `../Project-Creation-Standard.md`
- `../../AGENTS.md`
- `Aster-Unified-Voice-Service.md`
- `Pull-Based-Forgejo-Runner.md`
- `../runbooks/Pull-Based-Forgejo-Runner.md`
- `../design/HomeLab-UI-Style-Guide.md`
- Official Kodi: https://github.com/xbmc/xbmc
- Official LibreELEC: https://github.com/LibreELEC/LibreELEC.tv
- LibreELEC Generic x86-64 hardware guidance: https://wiki.libreelec.tv/hardware/intel-x86-64-generic
- Intel N95 specifications: https://www.intel.com/content/www/us/en/products/sku/231800/intel-processor-n95-6m-cache-up-to-3-40-ghz/specifications.html
- LibreELEC boot init splash lookup: https://github.com/LibreELEC/LibreELEC.tv/blob/master/packages/sysutils/busybox/scripts/init
- LibreELEC custom bootsplash: https://wiki.libreelec.tv/how-to/change-bootscreen
- Kodi skin development: https://kodi.wiki/view/Skin_development_introduction
- Kodi UI-sound mapping: https://kodi.wiki/view/Sounds.xml
- Kodi add-on rules and licensing guidance: https://kodi.wiki/view/Add-on_rules
- Home Assistant dashboards: https://www.home-assistant.io/dashboards
- Home Assistant frontend themes: https://www.home-assistant.io/integrations/frontend/
- Home Assistant custom cards: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
- `../design/Aster-Home-v2-Recommendations.md`
