# Prometheus and Grafana Observability Project

> Status: Active — Milestone 2 architecture design
>
> Project owner: Jason
>
> Last updated: 2026-08-30

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
- [ ] Create read-only, least-privilege identities or tokens where required.
- [ ] Design firewall rules from the collector to explicit targets/ports.
- [ ] Keep management interfaces private to approved LAN/Tailscale users.
- [ ] Define backup, upgrade and rollback procedures before deployment.
- [ ] Record secrets only in protected runtime configuration.

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

Completion gate: placement, storage, credentials, firewall dependencies and
recovery are approved before installing software.

## Milestone 3 — Prometheus pilot

- [ ] Deploy a pinned, supported Prometheus release.
- [ ] Configure local storage retention and resource limits.
- [ ] Add targets one at a time and verify scrape health.
- [ ] Add recording rules only when they simplify a defined dashboard/query.
- [ ] Monitor cardinality, disk growth, scrape duration and target load.
- [ ] Prove that exporter or Prometheus failure does not affect target services.
- [ ] Back up configuration and validate a configuration restore.

Completion gate: selected metrics are collected reliably within the resource
budget and do not disturb production services.

## Milestone 4 — Grafana pilot

- [ ] Deploy a pinned, supported Grafana release on the approved private path.
- [ ] Configure Prometheus as the data source using protected credentials.
- [ ] Build or carefully adapt the approved bounded dashboards.
- [ ] Create an overview dashboard for capacity and anomaly investigation.
- [ ] Create focused dashboards for network, compute/storage and surveillance/AI
  only where the recorded requirements justify them.
- [ ] Validate time zone, units, labels and device naming against repository data.
- [ ] Back up provisioning, dashboard and data-source configuration without
  committing secrets.

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

- [ ] Add a Homepage link/widget only after Grafana is stable.
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
| 2026-08-30 | Milestone 2 | Live Proxmox capacity reviewed; LXC 109 placement and target integrations selected | In progress |
