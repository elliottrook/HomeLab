# Prometheus and Grafana Observability Project

> Status: Active — authenticated private URL, Doctor and backup integration complete; alert delivery pending
>
> Project owner: Jason
>
> Last updated: 2026-08-31

Checkpoint: `https://monitoring.elliottrook.com` is live through the private
reverse proxy and split DNS. Grafana offers admin-restricted Authentik sign-in
while retaining its local recovery login. HomeLab Doctor and protected backup
integration are complete, and an isolated restore test passed. Remaining work
is the two bounded UPS alert rules and notification destination, updating the
live DSM task body with the tracked LXC 109 filter, final documentation, and
the 30-day review schedule.

## Purpose

Add long-term, queryable infrastructure metrics and focused dashboards where
they provide value beyond HomeLab Doctor and Beszel. The project must remain
bounded and must not become a second, conflicting alerting authority.

## Inherited baseline

- [x] HomeLab Doctor provides functional checks, drift detection, certificate
  monitoring and failure-only scheduled reporting.
- [x] Beszel provides lightweight host/container history and sustained alerts.
- [x] Homepage provides the concise daily service view.
- [x] OPNsense, Proxmox, TrueNAS, Docker, Frigate and key services already have
  operational health coverage.

## Intended value

- Longer-term capacity and performance trends.
- Cross-system correlation for CPU, memory, storage, network and service load.
- Measured capacity planning for surveillance, storage and local AI.
- Historical evidence when intermittent issues are not captured by functional
  checks.

If those benefits cannot be achieved without excessive maintenance, credentials
or duplicate alerts, the correct outcome is to retain the existing tools.

## Out of scope

- Replacing HomeLab Doctor, Beszel or Homepage.
- A SIEM, centralized log platform or broad security analytics deployment.
- Scraping sensitive values or storing credentials in Git/dashboard JSON.
- Public Grafana or Prometheus exposure.
- Alerting on every transient metric fluctuation.

## Milestone 1 — Requirements and success measures

- [x] List the exact questions existing tools cannot answer.
- [x] Select initial systems and metrics; start with no more than OPNsense,
  Proxmox, TrueNAS, Docker/Frigate and UPS power data if available.
- [x] Define retention, scrape intervals, expected cardinality and storage budget.
- [x] Identify which alerts, if any, are missing from current monitoring.
- [x] Define three to five useful dashboards rather than importing a large
  unreviewed collection.
- [x] Establish measurable keep/reject criteria for the pilot.

### Questions the pilot must answer

1. Which host, guest, disk or network resource was saturated before and during
   an intermittent service problem that HomeLab Doctor only sees at test time?
2. At the current growth rate, when will important Proxmox, TrueNAS and Frigate
   storage cross 80%, 90% and exhaustion thresholds?
3. Do Frigate camera processing, recording I/O and detector load correlate with
   Proxmox or TrueNAS pressure?
4. How do UPS load, charge and estimated runtime change with the protected
   equipment online, and are the configured shutdown thresholds still
   appropriate as loads change?
5. Can one view correlate compute, storage and power history without replacing
   Beszel's host alerts or HomeLab Doctor's functional checks?

### Bounded pilot data set

| Target | Initial metrics | Boundary |
|---|---|---|
| Proxmox | Node CPU, memory, swap, load, storage usage and guest state/resource use | Prefer the supported API integration; no guest application secrets |
| TrueNAS | CPU, memory, pool/dataset capacity, disk health counters and network throughput | Read-only metrics path; no share contents or filenames |
| Docker/Frigate | Host/container resources plus Frigate processing, detector, camera and recording metrics | Pilot only the existing Docker host and Frigate VM |
| NUT server and three UPS units | Input state, charge, runtime, load, voltage and status | Export read-only values already exposed by NUT |

OPNsense is deferred from the first scrape set. It may be added after the pilot
is stable if a supported, least-privilege integration answers a specific WAN or
firewall capacity question that existing checks cannot answer.

### Retention and resource budget

- Default scrape interval: 30 seconds. Use 60 seconds for slow appliance/API
  integrations and only use 15 seconds where a defined Frigate investigation
  proves that 30 seconds is insufficient.
- Initial retention: 90 days, with a hard local Prometheus storage ceiling of
  20 GB.
- Initial scale target: fewer than 25 scrape targets and fewer than 100,000
  active time series. Investigate before raising either limit.
- Reassess measured ingestion rate, cardinality and disk growth after 7 and 30
  days. Retention may be reduced rather than expanding storage.
- Pilot guest budget: no more than 2 vCPU, 4 GB RAM and 32 GB storage unless
  Milestone 2 capacity evidence justifies a different allocation.

### Dashboard set

1. **Infrastructure overview** — availability context, CPU/memory pressure,
   storage headroom and UPS state across the pilot.
2. **Proxmox capacity** — node and guest saturation, memory/swap pressure and
   storage growth.
3. **TrueNAS storage** — pool/dataset headroom, disk indicators, throughput and
   latency where safely available.
4. **Frigate pipeline** — camera FPS, detection/processing latency, detector
   load, recording activity and related host/NFS pressure.
5. **Power resilience** — UPS load, battery charge/runtime, mains events and
   proximity to the documented shutdown thresholds.

Dashboards will be built or adapted selectively; unreviewed dashboard bundles
are not part of the pilot.

### Alerting boundary

No Alertmanager deployment is approved in Milestone 1. The only candidate
alerts are sustained conditions not already owned by Beszel or HomeLab Doctor,
such as forecast storage exhaustion or a persistent metrics-target failure.
Candidates must be mapped against existing alerts in Milestone 5 before they
are enabled.

### Keep/reject criteria

Keep the platform after the 30-day observation period only if all of the
following are true:

- At least three dashboards answer their named operational questions with real
  data and at least one historical investigation demonstrates value beyond
  Beszel and HomeLab Doctor.
- Prometheus remains within the approved CPU, memory, cardinality and storage
  budget without affecting monitored services.
- Routine care is no more than approximately 30 minutes per month, excluding
  planned upgrades and genuine incident investigation.
- Configuration, dashboards and data-source provisioning can be restored from
  the documented backup without committing credentials.
- Access remains private and no duplicate noisy alert path is introduced.

Reduce or remove the pilot if it exceeds the budget, creates fragile privileged
integrations, duplicates existing views without diagnostic value, or cannot be
restored cleanly.

Completion gate: the project has specific observability questions, a bounded
data set and a storage/maintenance budget.

## Milestone 2 — Architecture and security design

- [x] Select the host/guest, VLAN, address, CPU, RAM and storage allocation after
  reviewing current Proxmox capacity.
- [x] Decide whether Prometheus and Grafana share one guest or use separate
  components; justify the maintenance trade-off.
- [x] Select supported exporters/integrations for each target.
- [x] Create read-only, least-privilege identities or tokens where required.
- [x] Design firewall rules from the collector to explicit targets/ports.
- [x] Keep management interfaces private to approved LAN/Tailscale users.
- [x] Define backup, upgrade and rollback procedures before deployment.
- [x] Record secrets only in protected runtime configuration.

### Placement decision

The pilot will use a dedicated unprivileged Debian LXC rather than adding the
stack to the existing multi-service Docker guest. Prometheus, Grafana and the
small protocol-conversion exporters will share the one guest. At this scale,
separate guests add backup, patching and firewall overhead without providing a
meaningful failure-isolation benefit; Prometheus and Grafana will still run as
independent services with explicit resource limits.

| Setting | Decision |
|---|---|
| Proxmox guest | LXC 109, hostname `observability` |
| Network | Servers VLAN 20 on `vmbr0`, tagged VLAN 20 |
| Address | Provisionally `192.168.20.31/24`, gateway `192.168.20.1`; verify against OPNsense before creation |
| Resources | 2 vCPU, 4 GB RAM, 512 MB swap, 32 GB thin-provisioned root disk |
| Boot/security | Start at boot, unprivileged container, Proxmox firewall enabled |
| Service layout | Native systemd services; no nested Docker requirement |
| Prometheus budget | 90 days and 20 GB maximum local TSDB usage |

The 2026-08-30 read-only capacity review found 40 logical CPUs, approximately
14 GB currently available RAM, 7.9 GB free swap, 70 GB free on the Proxmox root
filesystem and approximately 731 GB free in `local-lvm`. The proposed guest fits
without increasing the Milestone 1 budget. VM 105 (`ollama`) was stopped during
the review; its 14 GB allocation means aggregate memory must be reassessed
before sustained simultaneous local-AI and observability load.

### Integration selection

| Source | Selected path | Security and maintenance boundary |
|---|---|---|
| Proxmox | `prometheus-pve-exporter` on LXC 109 querying the Proxmox HTTPS API | Dedicated API token for a user granted the read-only `PVEAuditor` role at `/`; token stored only in protected runtime configuration |
| TrueNAS | Native TrueNAS Graphite reporting exporter pushes to the official Prometheus `graphite_exporter` on LXC 109 | No TrueNAS API credential; permit only TrueNAS to the Graphite receiver and use a reviewed mapping to control metric names/cardinality |
| Frigate | Native Frigate `/api/metrics` Prometheus endpoint | Prefer the private direct path; use a dedicated read-only authentication mechanism if the installed Frigate configuration requires one |
| Linux host context | Official Prometheus `node_exporter`, initially only where PVE guest metrics and Frigate's native metrics leave a demonstrated gap | Do not deploy broadly or enable unnecessary collectors merely to duplicate Beszel |
| NUT/UPS | `DRuggeri/nut_exporter` on LXC 109 querying the existing NUT server | One explicit scrape per UPS; read-only NUT access only, with the exporter endpoint private |

TrueNAS's native Graphite export is preferred over installing unsupported
software on the appliance. Frigate's native endpoint is preferred over an
additional Frigate-specific exporter. Proxmox and NUT require maintained
community exporters because neither source exposes the selected data directly
in Prometheus format; both will be version-pinned and isolated on the collector
rather than installed on the monitored hosts.

### Preliminary network flow design

The final OPNsense and Proxmox firewall objects remain to be implemented and
validated. The intended minimum flows are:

| Source | Destination | Port | Purpose |
|---|---|---:|---|
| LXC 109 | Proxmox `192.168.50.10` | TCP 8006 | Read-only PVE API collection |
| LXC 109 | Frigate `192.168.20.10` | TCP 8971 | Native Frigate metrics |
| LXC 109 | NUT server `192.168.50.25` | TCP 3493 | Read-only UPS variables |
| TrueNAS `192.168.20.40` | LXC 109 | TCP 9109 | Native Graphite metrics push |
| Approved LAN/Tailscale administrators | LXC 109 | TCP 3000 | Private Grafana access |

Prometheus TCP 9090 and exporter ports will not be published through the public
reverse proxy. Administrative direct access remains private; a later Grafana
reverse-proxy/OIDC path is explicitly deferred to Milestone 6.

The implemented OPNsense rules permit only `192.168.20.31` to Proxmox TCP 8006
and NUT TCP 3493. Frigate's unauthenticated TCP 5000 API is published only for
metrics and is filtered in VM 102's Docker `DOCKER-USER` path: the collector is
accepted and every other source is dropped. TrueNAS Graphite input is further
constrained by a userspace TCP ingress that accepts only `192.168.20.40`; the
actual Graphite exporter and all other exporters listen on loopback.

The Proxmox exporter uses a dedicated `prometheus@pve` identity with only the
`PVEAuditor` role and a separate API token. The token exists only in
`/etc/prometheus/pve.yml` with protected ownership and in the protected
configuration backup. No token or password is committed to Git.

Upgrade procedure: create a fresh LXC snapshot/configuration backup, download a
specific supported release, verify its published checksum, validate the staged
configuration and restart one component at a time. Rollback is to reinstall the
previous pinned binary or Python environment and restore the protected config;
if the guest is damaged, restore the latest verified LXC archive. Exporter
failure is non-authoritative and must never trigger a target-service restart.

Completion gate: placement, storage, credentials, firewall dependencies and
recovery are approved before installing software.

## Milestone 3 — Prometheus pilot

- [x] Deploy a pinned, supported Prometheus release.
- [x] Configure local storage retention and resource limits.
- [x] Add targets one at a time and verify scrape health.
- [x] Add recording rules only when they simplify a defined dashboard/query.
- [x] Monitor cardinality, disk growth, scrape duration and target load.
- [x] Prove that exporter or Prometheus failure does not affect target services.
- [x] Back up configuration and validate a configuration restore.

Completion gate: selected metrics are collected reliably within the resource
budget and do not disturb production services.

### Initial deployment

On 2026-08-30, unprivileged Debian 13.6 LXC 109 (`observability`) was created on
Proxmox at `192.168.20.31` with the approved 2 vCPU, 4 GB RAM, 512 MB swap and
32 GB thin-provisioned disk allocation. It starts at boot and has the Proxmox
guest firewall flag enabled.

Prometheus 3.13.2 LTS was downloaded from the official release, verified against
the published SHA-256 checksum, installed as a dedicated unprivileged system
user and enabled as a hardened systemd service. Retention is limited by both
`90d` and `20GB`; whichever limit is reached first applies. The initial config
passed `promtool check config`, the readiness endpoint returned ready and the
first self-scrape target reported `health: up` at the configured 30-second
interval. Initial service memory use was approximately 76 MB and the guest root
filesystem was 4% used before production targets were added.

Targets were added and validated individually:

- Proxmox through `prometheus-pve-exporter` 3.9.0 and the read-only API token.
- `proxmox-ups`, `nas-ups` and `network-ups` through checksum-verified
  `nut_exporter` 3.3.0.
- Frigate through its native `/api/metrics` endpoint on the source-restricted
  internal API.
- TrueNAS through its native Graphite reporting exporter and checksum-verified
  official `graphite_exporter` 0.17.0. The report selection is bounded to
  system, memory, swap, disk, disk-space, network and ZFS charts at 30 seconds.

All seven scrape jobs, including Prometheus itself, reported healthy. The first
complete baseline contained 1,686 active series, only 92 of which came from the
bounded TrueNAS job. Prometheus TSDB usage was 4.8 MB; observed component RSS was
approximately 90 MB for Prometheus, 76 MB across the PVE exporter master/worker,
16 MB for the NUT exporter and 15 MB for the Graphite exporter. No recording
rule was added because the initial queries and future dashboards do not yet
justify one.

A controlled isolation test stopped Prometheus and every exporter while the
Proxmox API, Frigate authenticated endpoint, all three live NUT UPS statuses and
TrueNAS pools remained healthy. All scrape targets recovered after the
monitoring services restarted. Frigate also resumed fresh recording segments
after the one-time Compose restart needed to publish the restricted metrics
port.

The protected configuration archive is stored under
`~/lab/private-backups/observability/2026-08-30/` and was extracted into an
isolated temporary directory to validate its contents and permissions. LXC 109
is covered by the enabled all-guests nightly Proxmox job; its first snapshot
archive completed on 2026-08-30 and passed a complete Zstandard integrity test.

## Milestone 4 — Grafana pilot

- [x] Deploy a pinned, supported Grafana release on the approved private path.
- [x] Configure Prometheus as the data source using protected provisioning.
- [x] Build or carefully adapt the approved bounded dashboards.
- [x] Create an overview dashboard for capacity and anomaly investigation.
- [x] Create focused dashboards for network, compute/storage and surveillance/AI
  only where the recorded requirements justify them.
- [x] Validate time zone, units, labels and device naming against repository data.
- [x] Back up provisioning, dashboard and data-source configuration without
  committing secrets.

### Initial Grafana deployment

On 2026-08-30, checksum-verified Grafana OSS 13.2.0 was installed natively on
LXC 109 and bound only to the approved private address at
`http://192.168.20.31:3000`. Self-registration, usage reporting, update checks,
plugin administration and automatic plugin installation are disabled. Grafana
alerting is also disabled until the separate Milestone 5 duplication review.
The service is limited to one CPU and 768 MB RAM; steady-state service memory
after removing unused data-source plugins was approximately 170 MB.

Prometheus is the provisioned, non-editable default data source. The first
provisioned dashboard, **HomeLab Infrastructure Overview**, correlates all seven
scrape jobs with Proxmox node/guest pressure and storage utilization, TrueNAS
load, Frigate pipeline performance and the three UPS load, charge and runtime
series. Its 16 PromQL expressions were validated directly against the live
Prometheus API. The dashboard uses the browser's local time zone, 30-second
refresh and repository-aligned guest, camera and power-tier labels.

The protected archive
`~/lab/private-backups/observability/2026-08-30/observability-grafana-config-2026-08-30.tar.gz`
contains the Grafana database, provisioning, dashboard JSON, service override
and initial administrator recovery credential. It is mode 0600, passed archive
integrity testing and has SHA-256
`e7904b9f3a16c878500a88c7d843fb09de2d8f9c5daffe5ffae2bab6ab256921`.
No credential or Grafana runtime database is committed to Git.

The focused dashboard set was completed after the initial overview:

- **HomeLab Compute Storage and Network** correlates Proxmox host and guest CPU,
  memory, storage, disk throughput and network traffic with the bounded TrueNAS
  load and aggregate-network metrics.
- **HomeLab Frigate Surveillance and AI** covers camera, processing, detection
  and skipped FPS, Coral inference latency, process CPU/memory, event rate and
  recording-storage headroom.
- **HomeLab Power Resilience** compares all three UPS units by charge, runtime,
  load, input/output voltage, battery voltage and status.

TrueNAS's current bounded Graphite mapping does not expose pool-capacity or ZFS
metrics, so the compute/storage dashboard shows only the real TrueNAS load and
network series. Pool-capacity collection remains a defined gap rather than an
empty or misleading panel. All 53 PromQL expressions across the four dashboards
returned live data during validation. The refreshed protected backup is
`observability-grafana-config-2026-08-30-focused.tar.gz`, with SHA-256
`843abf7b4a2c28a43fe07da5af6e1e6ba7e5c510672e7769203328f1376b6838`.

Completion gate: each dashboard answers a defined operational question and does
not merely reproduce Beszel or Homepage.

## Milestone 5 — Alerting decision

- [ ] Map existing HomeLab Doctor and Beszel alerts to prevent duplication.
- [ ] Identify only missing, actionable sustained conditions.
- [ ] Decide whether Alertmanager is justified; do not deploy it by default.
- [ ] If deployed, test routing, grouping, inhibition, recovery notices and
  failure-only behaviour.
- [ ] Perform controlled threshold tests and restore production thresholds.
- [ ] Document the authoritative tool for every alert category.

Completion gate: alerts are actionable, non-duplicative and have a tested owner
and response procedure—or the documented decision is to add none.

## Milestone 6 — Integration, recovery and observation

- [x] Add a Homepage link/widget only after Grafana is stable. A link-only tile
  now opens the provisioned overview without adding dashboard polling or
  credentials during the observation period.
- [ ] Decide whether Authentik native OIDC is suitable while retaining a local
  recovery administrator and direct private fallback.
- [ ] Add service/certificate/backup checks to HomeLab Doctor only where needed.
- [ ] Validate backup and isolated restore of configuration and dashboards.
- [ ] Observe resource consumption and disk growth for at least 30 days.
- [ ] Compare outcomes with the keep/reject criteria from Milestone 1.
- [ ] Keep, reduce or remove the platform explicitly; clean up pilot rules and
  credentials if rejected.
- [ ] Update architecture, operations, backups, addressing and baseline documents.

## Definition of done

The project is complete when Prometheus/Grafana either provide clearly measured
operational value within a bounded resource and maintenance budget, with secure
access and proven recovery, or the pilot is cleanly removed and the documented
decision is to retain HomeLab Doctor and Beszel alone.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-24 | Project definition | Observability work separated from initial-build monitoring | Proposed |
| 2026-08-30 | Milestone 1 | Questions, pilot targets, budgets, dashboards and keep/reject criteria recorded | Complete |
| 2026-08-30 | Milestone 2 | Live capacity, placement, least-privilege identities, narrow network flows and recovery design validated | Complete |
| 2026-08-30 | Milestone 3 | Seven jobs healthy, 1,686 series, failure isolation passed, protected config and verified LXC backups created | Complete |
