# Jason's HomeLab Roadmap

> Last Updated: 2026-08-08

---

# Current Release

Version 1.2.1

Current Focus:
🟢 Enterprise Network Implementation

---

# Phase 1 — Foundation ✅ COMPLETE

Infrastructure

- [x] OPNsense Firewall
- [x] Arista Core Switch
- [x] Proxmox Server
- [x] TrueNAS
- [x] Synology
- [x] UniFi Controller

Operations

- [x] Git Repository
- [x] HomeLab Toolkit
- [x] SSH Key Authentication
- [x] Infrastructure Backups
- [x] lab doctor

---

# Phase 2 — Enterprise Network 🚧

Status: In Progress

Planning

- [x] Validated current-state baseline
- [x] IP address baseline
- [x] Guest and IoT firewall policy
- [x] Active switch port map
- [x] Rack Diagram

Implementation

- [x] VLAN trunk infrastructure
- [x] Trusted VLAN 10 retained during migration
- [ ] VLAN Lab
- [x] VLAN IoT
- [ ] VLAN Cameras
- [x] Guest Wi-Fi

Validation

- [x] DHCP for trusted, IoT and Guest networks
- [x] DNS and split DNS
- [x] Inter-VLAN routing through OPNsense
- [x] IoT and Guest firewall isolation
- [x] WAN and VLAN performance testing

---

# Phase 3 — HomeLab Dashboard ✅ CORE COMPLETE

- [x] Homepage deployed
- [x] Internal `home.internal` DNS name
- [x] Quick links to infrastructure and applications
- [x] SSH launch links for Proxmox, Docker LXC, OPNsense and TrueNAS
- [x] Pi-hole dashboard tile and single-client DNS-filtering pilot
- [x] Private remote access through Tailscale
- [x] Remote SSH validated through the Tailscale subnet route
- [ ] Device Status
- [ ] Backup Status
- [ ] Resource Monitoring

---

# Phase 4 — Forgejo

- [ ] Deploy Forgejo
- [ ] Migrate HomeLab Repository
- [ ] SSH Authentication
- [ ] Daily Backup

---

# Phase 5 — Monitoring

- [ ] Prometheus
- [ ] Grafana
- [ ] Alerting
- [ ] Historical Metrics
- [ ] Pi-hole DNS redundancy and network-wide rollout

---

# Phase 6 — Automation

- [ ] Nightly Backups
- [ ] Configuration Drift Detection
- [ ] Automatic Reports
- [ ] Certificate Monitoring

---

# Phase 7 — Services

- [ ] Jellyfin
- [ ] Immich
- [ ] Paperless-ngx
- [ ] Wiki
- [ ] Home Assistant

---

# Future Ideas

- UPS Integration
- Remote Environmental Sensors
- PXE Boot Server
- Internal Certificate Authority
- IPv6
- Kubernetes Lab
