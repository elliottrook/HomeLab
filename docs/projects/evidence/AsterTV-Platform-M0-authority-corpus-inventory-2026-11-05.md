# AsterTV platform M0 authority and corpus inventory

> Status: accepted read-only opening inventory
>
> Captured: 2026-11-05
>
> Scope: repository evidence plus identity-pinned, content-free live checks

This inventory is the migration input for the AsterTV fleet contract. It does
not make observed state authoritative, read credentials, inspect media history,
or change a client. The three active hosts answered through their previously
pinned Ed25519 identities; only hostname, LibreELEC build, recovery-unit state
and the accepted-manifest envelope were read.

## Authority and repository corpus

| Subject | Authority | Existing corpus | M1 destination |
|---|---|---|---|
| Appliance identity, interface, address, VLAN and placement | NetBox, reconciled against sanitized live facts | AsterTV v3 M0 evidence, Remote runbook and NetBox records | `fleet.yaml` membership plus hardware/peripheral profile references |
| Current runtime state | Sanitized live query | Hostname/build/guard checks and project evidence | `observed/` in a later Doctor milestone; never compiled as desired state |
| Desired software composition | Git fleet contract | v2 release, v3 project evidence, installers and accepted guards | Release/profile/overlay/device manifests compiled to `desired/` |
| Release bytes | Private Forgejo release and checked-in checksum | `services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz.sha256` | Immutable release record |
| Device exception | Accepted overlay record and decision evidence | v3 deploy/install code and milestone evidence | Named overlay with owner, compatibility, rollback and tests |
| Hardware/peripheral fact | NetBox plus measured qualification | M0 client baseline, low-spec handoff and M7 equipment evidence | Hardware and peripheral profiles |
| Secret value | Existing source-local custodian | Mode/identity/custody references only | Opaque `secret_refs`; values are forbidden |
| AsterTV design | Approved private Forgejo asset release and Git design records | Aster v2 asset guide/expansion handoff and accepted v2/v3 screens | M3 design authority; M1 records asset release references only |
| Human operating knowledge | Existing private `homelab-wiki` | MkDocs/Human Wiki Contract on LXC 113 | M2 additive AsterTV department; no parallel wiki |
| Reviewed current procedures | `homelab-reference` | Existing operational reference | Linked, not duplicated |
| Aster knowledge | Derived mirror | Existing LXC 113 collector/mirror | Regenerated only from accepted human pages |

The private wiki is currently healthy at the previously recorded Forgejo commit
`c9bd0114f3157cd128cd5ee2dda1c3f697fb90cb`. Its intake, provenance,
quarantine, content-addressed originals, daily collection and monthly health
architecture are the adopted publishing path. No wiki deployment was changed.

## Fleet snapshot

| Device | Lifecycle | Address | Measured class and output | 2026-11-05 live envelope | Desired migration |
|---|---|---|---|---|---|
| AsterTV Family | production | `192.168.1.157` | Intel N95/Alder Lake-N; TCL QM8L through Onkyo TX-RZ30; HDMI Dolby/HDR | Hostname matched; LibreELEC `nightly-20261021-440640e`; guard enabled; accepted manifest 533 files, observation digest `b821c2a2…e61d` | v2.0.7 base + Family HDMI/HDR/audio + current shared runtime + Remote + Family equipment bridge |
| AsterTV Bedroom | production | `192.168.1.140` | Intel i5-9500T/UHD 630; LG display; Wi-Fi; stereo | Hostname matched; same LibreELEC build; guard and Wi-Fi stability enabled; accepted manifest 535 files, digest `474c887d…f204` | v2.0.7 base + Bedroom stereo/Wi-Fi + current shared runtime + Remote |
| AsterTV Jen | lab | `192.168.1.180` | Intel i5-4570T/Haswell; qualified for 1080p-media/stereo, with native-resolution GUI permitted and no fleet-wide 4K playback parity | Hostname matched; same LibreELEC build; guard enabled; accepted manifest 528 files, digest `dfc51bc8…c3ff` | v2.0.7 base + low-spec profile + accepted Jen v3 overlays + Remote |
| AsterTV Guest | candidate | not assigned | Hardware and peripheral chain not yet selected | Not deployed; no address, identity, firewall path or credential exists | Candidate record only; compilation must not imply deployment |

The accepted guard manifest includes `accepted_at`, so its file digest is an
observation identifier rather than a deterministic composition identifier.
M1 therefore compiles a separate stable composition hash from canonical
source manifests. Family's current 533-file count is explained by the accepted
News/media-lifecycle and shared runtime repairs recorded in AsterTV v3; it is
not treated as unexplained drift.

## Releases, profiles and overlays

### Global release

- `astertv-v2.0.7-release-2026-10-31`, 577-file final snapshot.
- Archive SHA-256
  `e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`.
- Family and Bedroom share the payload while the target-aware promoter
  preserves different audio behavior. Jen was qualified from the same base.
- v1.1.1 is rollback history, not an active desired release.

### Reusable and device-specific components

| Component/difference | Current evidence | Owner/layer | Migration destination |
|---|---|---|---|
| Seven-root pre-Kodi accepted-state guard | `astertv-v3/reliability` | shared runtime | `release-guard-v1` overlay; M4 will broaden it to compiled composition |
| TV details, dynamic episodes, episode art/cache bounds, trailer and Digest entry repairs | `astertv-v3/deploy/tv-details` | shared presentation/runtime | `tv-details-v3` overlay |
| News idle/playlist lifecycle correction | `deploy/news-playback` | shared playback | `news-playback-v3` overlay |
| Jellyfin resume/Up Next and Intro Skipper compatibility | `deploy/media-lifecycle` | Family playback compatibility | `family-media-lifecycle` overlay |
| Immediate network-authorized PWA and outbound room clients | Aster Remote runbook/M8 evidence | shared service + per-device identity | `remote-client-v3` overlay plus external Remote integration |
| HDMI 0 passthrough, HDR and PulseAudio mask | final v2 release/Family evidence | Family profile | `family-dolby-hdr` peripheral/runtime overlay |
| Kodi Restart AsterTV control | v2 README/checkpointed repair | Family recovery UX | `family-kodi-restart` overlay |
| Wi-Fi power-save stability and literal host-bound guard | `deploy/bedroom-wifi` | Bedroom OS profile | `bedroom-wifi-stability` overlay |
| Stereo output contract | final v2 target-aware promoter | Bedroom profile | Bedroom peripheral profile |
| 1080p/stereo/Haswell limits | low-spec evidence | Jen hardware profile | `lenovo-m93p-low-spec` hardware profile; never global |
| Account/profile registry and Guest catalogue isolation | M2 Jen evidence | Jen application overlay | `jen-account-registry` and `jen-guest-catalogue` overlays |
| Capability-scoped Aster broker client | M3 evidence | Jen application overlay | `jen-aster-client` overlay plus broker integration ref |
| Movie/actor/trailer and household YouTube lifecycle | M4/M4Y evidence | Jen presentation/runtime | `jen-movie-youtube` overlay |
| News pill icon treatment | M5N evidence | Jen presentation | `jen-news-icons` overlay |
| Podcast request client | M5P evidence | Jen presentation/service client | `jen-podcast-requests` overlay |
| Separate Home and on-demand Cameras | M6 evidence | Jen presentation/runtime | `jen-home-cameras` overlay |
| Family receiver/TV power-volume-mute bridge | M7 evidence | external HA/gateway | `family-equipment-bridge` integration component |

Every row maps an accepted local difference to a reusable profile/overlay or a
named device exception. Historical installers remain evidence and recovery
tools; they do not become independent desired-state authorities.

## Units, identities and external integrations

| Boundary | Current unit/path | Secret handling | Contract disposition |
|---|---|---|---|
| Kodi recovery | `astertv-release-guard.service` on all active boxes | none | required shared overlay, literal host binding |
| Bedroom network | `astertv-wifi-stability.service` | none | Bedroom-only overlay |
| Remote client | `service.asterremote` outbound poll to TCP 9120 | independent mode-0600 client refs | shared overlay; per-device opaque identity ref |
| Aster broker client | Jen-only outbound/capability client | source-local ref | Jen overlay; no general tool authority |
| Home/camera delivery | restricted HA/Frigate forced-command paths | source-local keys | integration refs; no camera/account content in manifests |
| Jellyfin | catalogue, playback, people, watched/progress | independently revocable client/user refs | external integration; no password/token |
| YouTube | official Kodi add-on and local account session | client-local credential ref | external integration; Guest stays disabled until isolation proof |
| Seerr/ARR | request/discovery and downstream acquisition authority | restricted broker/client ref | external integration; no request mutation in M0/M1 |
| Audiobookshelf | audiobook/podcast catalogue and progress | restricted client ref | external integration |
| Calibre/narration | eBook catalogue and prepared narration readiness | read-only source refs | external integration |
| News Digest | feed/article/narration lifecycle | existing runtime authority | external integration; canonical Aster voice unchanged |
| Home Assistant | household state and reviewed semantic equipment actions | capability-scoped bridge refs | external integration |
| OPNsense/DNS/DHCP | network policy and reservations | source-local admin custody | referenced authority only |

The manifest model records identifiers such as `jellyfin-family-client` or
`remote-bedroom-client`, never credential bytes, hashes that could act as
credentials, account content or private media data.

## Recovery inventory

The active recovery classes are:

- final v2 release checkpoints:
  `/storage/.aster-checkpoints/astertv-v2.0.7-release-20261031-family` and
  `/storage/.aster-checkpoints/astertv-v2.0.7-release-20261031-bedroom`;
- Family playback checkpoints:
  `astertv-news-playback-AsterTV-Family-20261104-145456` and
  `astertv-media-lifecycle-AsterTV-Family-20261105-031033`, plus the matching
  Jellyfin Intro Skipper ZFS snapshot recorded by M7 evidence;
- Bedroom Wi-Fi/guard checkpoint documented in
  `deploy/bedroom-wifi/README.md`;
- Jen retained milestones for M2 accounts/Guest, M3 Aster client, M4/M4Y,
  M5N/M5P and M6 under `/storage/.aster-checkpoints/`;
- Remote gateway/client checkpoints under
  `/var/lib/aster/checkpoints/astertv-v3-m8-*` and
  `/storage/.aster-checkpoints/astertv-v3-m8-*`;
- Family bridge checkpoint
  `/var/lib/aster/checkpoints/astertv-v3-m7-family-bridge-20261105/` plus the
  recorded HA backup and OPNsense before/proof records.

Exact historical checkpoint names remain in their milestone evidence. M1
records the accepted rollback reference per active overlay rather than copying
checkpoint contents or treating old checkpoints as desired state.

## Asset inventory

- Original private release `aster-brand-v2-2026-10-14` is the immutable brand
  rollback authority.
- Expansion release `aster-brand-v2-expansion-2026-10-14` contains 174 entries;
  package SHA-256 is
  `e030b6104fbdffb44faf035471f8c55320c3869065046a1ff5f9f0433069c48e`.
- Approved contexts: limestone-backed icons only on the floating side rail;
  plain compass icons on pills/top navigation; runtime PNG/WebP exports from
  the verified private masters.
- Runtime assets in v2/v3 payloads are consumers, not a second design authority.

## Coverage and migration map

| System of record | Coverage now | M0 conclusion |
|---|---|---|
| NetBox | Active appliance identities/IP facts are adopted; Guest absent by design | Reconcile through API before later onboarding/migration; M1 does not write NetBox |
| `homelab-reference` | Holds reviewed current operations | Link from future wiki/device pages; do not duplicate changing facts |
| Human wiki | Infrastructure exists; no AsterTV department | M2 extends existing MkDocs navigation and collector only |
| Aster mirror | Derived and non-authoritative | Regenerate only after M2 human pages are accepted |
| HomeLab Doctor | Remote probe exists; composition drift is not yet modelled | M4 consumes deterministic desired manifests |
| Repository | Complete release/project/install evidence but no composition authority | M1 creates the authority and lifecycle document |

## M0 gate

All four fleet members have an explained lifecycle state. Each accepted active
difference has a release/profile/overlay/integration migration destination.
No unknown live identity, secret output or unexplained behavior blocks a
faithful desired-state representation. The remaining gaps—deterministic
composition identity, ownership conflict detection and compatibility
validation—are the explicit M1 deliverables, not live drift.

