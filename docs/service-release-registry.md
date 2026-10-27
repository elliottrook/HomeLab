# HomeLab Service Release Registry

> Baseline: 2026-10-12
> Authority: the lifecycle standard defines environment/release semantics;
> NetBox and the current network baseline define observed placement; service
> references define operation; project records own promotion evidence.
> Owner: Jason

This registry records the current service-release baseline without implying
that a VLAN 70 service is production-ready. Every current service release is
`V1`; upstream versions, model builds, configuration revisions and experiment
runs remain separate identifiers. `Pending` fields are deliberate evidence
gaps, not inferred values.

| Service ID | Release | Current environment | Current placement | Target/disposition | Build/model reference | Configuration revision | Owner | Key dependencies / consumers | Backup and rollback | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| `local-ai-platform` | V1 | Lab/Beta | Aster 104 `.10`, llama.cpp 110 `.12`, Speech 116 `.14`, VLAN 70 | `ai-lab` plus `ai-prod`; target VLAN 20 | llama.cpp `b11429`; Qwen3.5 9B Q4_K_M; SYCL/Level Zero | Kokoro `bm_daniel`, `en-gb`, `0.95`; exact config revision pending | Jason | Aster, News and future approved consumers | Accepted current V1 manifest and guest/model archives; stopped Ollama VM 105 is retained only as historical rollback material | High |
| `news-aggregator` | V1 | Lab/Beta | LXC 114 `.13`, VLAN 70 | First production application promotion to VLAN 20 with private VLAN 50 ingress | Repository/build manifest pending | Current service config and feed set; revision pending | Jason | Local AI contract, Authentik/NPM, Doctor, Beszel, iPhone workflow | LXC 114 retained; application backup/restore and rollback manifest pending | High placement/health; medium artifact |
| `epub-narration-compiler` | V1 | Lab accepted | Monitor and recurring single-attempt worker in unprivileged LXC 116 `.14`; quota-bounded `Media/AsterReader` on TrueNAS `.40`; HP-only direct-launch Aster Books beta | Remain HP Lab; BOSGAME promotion is an optional separate project | M1 `4497558f`; M2 report `7692ef8d…88979b`; HP bundle `7f770e8c…dcd8`; measured 46.181 kbit/s mono Opus | `epub-narration-v1-hp-lab-2026-10-26`; `bm_daniel`, `en-gb`, `0.95`; exact sentence timing/content; monitor daily; one worker with a five-minute minimum inter-attempt delay and speech-service gate | Jason | Read-only Calibre EPUB library, Local AI voice contract, Doctor, protected configuration export, HP direct-launch beta | LXC snapshot `epub-narration-m3-pre-20261026`; exact-file compiler rollback; HP absent-state checkpoint; accepted dataset snapshot plus daily/14 days; media-free configuration export; source-driven regeneration | High; two final HP native passes and protected pilot-state export verified |
| `paperless` | V1 | Transitional production-facing | LXC 115 `.15`, VLAN 70, VLAN 50 ingress | Controlled application migration after News pilot | Existing deployment/reconstruction export; exact release pending | Protected Compose environment outside Git | Jason | Authentik/NPM, storage, OCR/summarization | Local/TrueNAS coverage; service reconstruction rollback | High placement; medium release |
| `authentik` | V1 | Production management/ingress | LXC 106 `.22`, VLAN 50 | Remain management/ingress | Exact image/build pending | Existing operational reference | Jason | NPM/Auth, private application routes | Guest/configuration backups; native recovery path | High |
| `reverse-proxy` | V1 | Production management/ingress | LXC 107 `.23`, VLAN 50 | Remain management/ingress | Exact image/build pending | Existing NPM/Auth configuration | Jason | Private DNS, certificates, Authentik | Guest/configuration backups; direct admin fallback | High |
| `docker-host` | V1 | Production applications | LXC 100 `.20`, VLAN 20 | Remain production application host; individual services retain records | Exact image/build pending | Compose/service files and protected runtime config | Jason | Homepage, media and utility containers | Guest archive and independent Homepage recovery | High |
| `monitoring` | V1 | Production observability | LXC 109 `.31`, VLAN 20 | Remain production observability | Prometheus 3.13.2 / Grafana 13.2.0 | Provisioned dashboards and scrape config; revision pending | Jason | Proxmox, TrueNAS, Frigate, NUT and service checks | Guest archive and protected configuration | High |
| `netbox` | V1 | Production inventory | LXC 111 `.32`, VLAN 20 | Remain inventory authority | NetBox 4.6 deployment; exact image record pending | `/opt/netbox` deployment and protected env files | Jason | Registry, IPAM, VM/service facts | Guest archive and reproducible deployment; isolated restore pending | High |
| `aster-wiki` | V1 | Production knowledge service | LXC 113 `.34`, VLAN 20 | Remain production knowledge service | Exact build pending | Wiki deployment/reference state | Jason | Human documentation and Aster mirror provenance | Guest archive and operational references | High |
| `backup-relay` | V1 | Production recovery service | LXC 112 `.33`, VLAN 20 | Remain recovery service | Exact build pending | Relay configuration outside Git | Jason | TrueNAS/off-site backup workflow | Protected recovery configuration and guest archive | High |
| `forgejo` | V1 | Production source control | LXC 108 `.30`, VLAN 20 | Remain authoritative Forgejo remote | Exact Forgejo version pending | Repository and service configuration | Jason | All repository projects and mirror | Guest archive; Forgejo mirror and isolated restore evidence | High |
| `home-assistant` | V1 | Production application | VM 103 `.11`, VLAN 20 | Remain production application | HA OS 18.2 | Native HA configuration/backup | Jason | IoT devices, HomeKit presentation | Native backup and VM archive | High |
| `media-acquisition-hub` | V1 | Production application | TrueNAS `.40`, VLAN 20; private VLAN 50 ingress | Remain production application; M6 refresh-quality maintenance deployed | Refresher image `sha256:ce2bf43978a…`; focused M6 milestone commit | Compose revision `484ee6d43212…` plus protected TrueNAS state/secrets | Jason | Jellyfin, Audiobookshelf, ARR services, Seerr, LazyLibrarian, Trakt and bounded public metadata providers | Protected configuration/state backup; checkpoint `20261014-m6-refresh-quality` and pre-M6 image/build tree | High except Audiobookshelf reader credential maintenance |
| `arr-stack` | V1 | Production application | TrueNAS `.40`, VLAN 20; private VLAN 50 ingress and direct application-address recovery | Remain production; controlled digest updates only | Sonarr 4.0.20.3014-ls326, Radarr 6.4.4.10685-ls318, Lidarr 3.1.0.4875-ls43, Prowlarr 2.6.5.5623-ls162, SABnzbd 5.1.3-ls274, Bazarr 1.6.2-ls366, Seerr 3.5.0, Profilarr 2.2.0; deployed images pinned by digest | 2026-10-17 remediation: exact Docker host policy, local health checks, `192.168.20.40` bindings, explicit local timezone and future-import naming | Jason | Jellyfin, Seerr, Profilarr, Aster sanitized report, video archiver and unified media workflows | Daily protected application/configuration export; recursive ZFS snapshots and root-private checkpoint `arr-remediation-20261017T0745Z`; prior image identities retained | High |

## Promotion procedure

1. Record the current V1 artifact, configuration revision, data boundary,
   dependencies, owner and rollback reference.
2. Build the same reviewed artifact in an isolated beta or disposable target.
3. Separate production credentials and durable state from lab material.
4. Capture a recovery checkpoint and validate health, resource envelope,
   ingress/authentication, DNS/firewall policy and monitoring.
5. Deploy to the target environment while retaining the lab instance until
   acceptance and rollback confidence are complete.
6. Reconcile NetBox, Beszel, Doctor, backups, operational references, wiki/
   mirror provenance and the user handover.
7. Perform the post-deployment intent and efficiency review required by the
   Project Creation Standard.

The procedure is a coordination record. It does not authorize a migration,
remote write, credential change or production cutover.

## Maintenance

Review the registry whenever a service is created, promoted, rolled back,
retired, renamed or materially reconfigured. A service-specific project must
replace every `Pending` field it relies on before graduation and must preserve
the distinction between current fact, transitional exception, target design,
service release, build revision and historical experiment.
