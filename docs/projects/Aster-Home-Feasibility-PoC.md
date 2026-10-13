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
- [ ] **M2 — Audiovisual:** Jellyfin library/direct play, music, collections, remote navigation, codecs, subtitles and playback stability. Gate: no media mutation; measurable results and hard blockers.
- [ ] **M3 — Customization:** throwaway Aster-styled Kodi skin/add-on, Home Assistant **read** dashboard, mocked commands and Aster AI query. Gate: prove extensibility and upgrade compatibility without core fork if possible.
- [ ] **M4 — Voice/intelligence:** consume existing Aster voice service with opt-in mic/control, demonstrate speech/turn and timeout/fallback handling without new TTS implementation. Gate: privacy and canonical-voice compliance.
- [ ] **M5 — SOFTWARE GO/NO-GO:** issue `Aster-Home-EH-001-Feasibility-Decision.md` explicitly stating **USE / CONDITIONAL USE / REJECT**, weighted tests plus hard constraints and source-supported alternatives if rejected. **No hardware purchasing study is necessary after REJECT** beyond documenting what alternatives need testing.
- [ ] **M6 — Conditional hardware/pricing:** **only if USE/CONDITIONAL USE**. Compare powerful mini-PC and cheaper local-decoding thin endpoint; measure network/server/client CPU, RAM, codec support, 4K/HDR, HDMI-CEC, audio passthrough, boot/recovery and wattage on available hardware; distinguish measured versus vendor claims. Price at least two viable products **per class** from Canadian retailers, with SKU, dated CAD offers/stock, sources, shipping/tax/accessories, support, 5-year TCO and ranked no-buy/reuse/buy choices. Gate: defensible minimum/efficient/premium specification and a specific recommended purchase or explicit defer.
- [ ] **M7 — Decision, recovery and handover:** reproduce key tests, verify independent rollback, update Doctor/Beszel/NetBox/wiki/operational references as applicable, apply the Aster internal style guide, produce non-technical user guide and final recommendation. No production deployment or order under this experiment.

Checkboxes cannot be marked complete without documented validation.

## 10. Evaluation and acceptance criteria

Predeclare household requirements and their severity (hard requirement vs
desirable). The current M0 requirement set is:

- **Hard:** reliable 4K playback; HDR10; HDMI-CEC; receiver-compatible Dolby
  Atmos/DTS passthrough; Jellyfin video and music; Home Assistant status and
  bounded control; Aster AI and canonical voice; stable everyday navigation;
  privacy and recoverability.
- **Desirable:** AirPlay through the endpoint, although the TV and receiver
  already provide native AirPlay; reuse of the existing Apple TV remotes over
  Bluetooth, subject to stability and pairing evidence; Dolby Vision; a
  FaceTime-like experience.
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

## 15. References

- `../Project-Creation-Standard.md`
- `../../AGENTS.md`
- `Aster-Unified-Voice-Service.md`
- `Pull-Based-Forgejo-Runner.md`
- `../runbooks/Pull-Based-Forgejo-Runner.md`
- `../design/HomeLab-UI-Style-Guide.md`
- Official Kodi: https://github.com/xbmc/xbmc
- Official LibreELEC: https://github.com/LibreELEC/LibreELEC.tv
