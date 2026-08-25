# Prometheus and Grafana Observability Project

> Status: Proposed
>
> Project owner: Jason
>
> Last updated: 2026-08-24

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

- [ ] List the exact questions existing tools cannot answer.
- [ ] Select initial systems and metrics; start with no more than OPNsense,
  Proxmox, TrueNAS, Docker/Frigate and UPS power data if available.
- [ ] Define retention, scrape intervals, expected cardinality and storage budget.
- [ ] Identify which alerts, if any, are missing from current monitoring.
- [ ] Define three to five useful dashboards rather than importing a large
  unreviewed collection.
- [ ] Establish measurable keep/reject criteria for the pilot.

Completion gate: the project has specific observability questions, a bounded
data set and a storage/maintenance budget.

## Milestone 2 — Architecture and security design

- [ ] Select the host/guest, VLAN, address, CPU, RAM and storage allocation after
  reviewing current Proxmox capacity.
- [ ] Decide whether Prometheus and Grafana share one guest or use separate
  components; justify the maintenance trade-off.
- [ ] Select supported exporters/integrations for each target.
- [ ] Create read-only, least-privilege identities or tokens where required.
- [ ] Design firewall rules from the collector to explicit targets/ports.
- [ ] Keep management interfaces private to approved LAN/Tailscale users.
- [ ] Define backup, upgrade and rollback procedures before deployment.
- [ ] Record secrets only in protected runtime configuration.

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
