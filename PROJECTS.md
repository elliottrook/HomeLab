# Jason's HomeLab Roadmap

> Last Updated: 2026-08-10

---

# Current Release

Version 1.3.0

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
- [x] Lab VLAN 70 design

Implementation

- [x] VLAN trunk infrastructure
- [x] Trusted VLAN 10 retained during migration
- [x] VLAN Lab infrastructure
- [x] VLAN IoT
- [x] VLAN Cameras
- [x] VLAN Servers infrastructure
- [x] VLAN Management infrastructure
- [x] Guest Wi-Fi

Validation

- [x] DHCP for all routed VLANs
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
- [x] Frigate dashboard and SSH launch links
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

# Phase 8 — Surveillance 🚧

- [x] Cameras VLAN 60
- [x] Reolink Duo 2V PoE isolated at `192.168.60.10`
- [x] Frigate VM deployed on Servers VLAN 20
- [x] Selective Frigate-to-camera firewall access
- [x] TrueNAS NFS recording storage
- [x] Reboot-safe NFS and Frigate startup ordering
- [x] Continuous recording validated
- [ ] Hardware-accelerated video decoding
- [ ] Dedicated object-detection accelerator
- [ ] Additional cameras and final retention sizing

---

# Deferred Projects

## Local AI / GPU Acceleration

- [ ] Evaluate local LLM deployment on Proxmox after the current project concludes
- [ ] Evaluate NVIDIA Tesla P40 24 GB as the value-oriented GPU option
- [ ] Verify Dell Precision 5810 PCIe clearance, PSU capacity and GPU power connections before purchase
- [ ] Design active cooling/airflow for a passively cooled datacenter GPU
- [ ] Test local model performance with the planned 48 GB system RAM
- [ ] Keep Frigate object detection on a dedicated TPU/accelerator where practical, reserving GPU capacity for local AI and advanced Frigate workloads

---

# Future Ideas

- UPS Integration
- Remote Environmental Sensors
- PXE Boot Server
- Internal Certificate Authority
- IPv6
- Kubernetes Lab
