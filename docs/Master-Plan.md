# 🌍 Project Mini Atlas

> **Build it well. Document it. Automate it. Enjoy it.**

Version: 2.0 (Enterprise Network)
Status: Implementation Phase
Last Updated: 2026-08-08

---

# 1. Mission

Project Mini Atlas is a long-term engineering project focused on building a secure, well-documented, enterprise-inspired HomeLab.

The lab serves two equally important purposes:

- A learning environment for enterprise networking, systems administration, automation, and infrastructure engineering.
- A reliable platform for self-hosted services that respects privacy, resilience, and maintainability.

Every component should be:

- Understandable
- Reproducible
- Secure
- Backed up
- Maintainable

Above all...

Project Mini Atlas should always be fun to build, explore, and improve.

---

# 2. Vision

Project Mini Atlas is more than a collection of computers and network equipment.

It is intended to become a complete infrastructure platform designed using professional engineering principles.

Every improvement should leave the environment:

- Better documented
- Easier to operate
- Easier to recover
- More secure
- More automated

---

# 3. Engineering Principles

The following principles guide every design decision.

## Design before deployment.

Configuration should follow documentation—not the other way around.

---

## Document the why, not just the how.

Future Jason should understand every important decision.

---

## Automate repetitive work.

If a task is performed more than once, consider automating it.

---

## Prefer open standards.

Avoid unnecessary vendor lock-in wherever practical.

---

## Security by default.

Every service begins with the minimum required access.

---

## Backups are only useful if they can be restored.

Every backup strategy should include restoration testing.

---

## Simple beats clever.

Choose the solution that is easiest to understand and maintain.

---

## Leave no mysteries.

No configuration should exist without documentation explaining why it exists.

---

## Measure before optimizing.

Collect evidence before changing working systems.

---

## Always keep it fun.

The HomeLab exists because building and learning are enjoyable.

Never add unnecessary complexity simply because it is possible.

---

# 4. Project Goals

Network

- Enterprise-style segmentation
- Reliable routing
- Secure wireless
- Simple management

Infrastructure

- High availability where practical
- Reliable storage
- Virtualization
- Centralized management

Operations

- Automated backups
- Health monitoring
- Documentation
- Version control

Learning

- Networking
- Linux
- Automation
- Infrastructure engineering
- Security

---

# 5. Architecture Overview

Internet

↓

OPNsense

↓

Arista Core

↓

Infrastructure Network

↓

Servers

↓

Storage

↓

Wireless

↓

Clients

↓

Tailscale Private Access

---

# 6. Core Components

Firewall

OPNsense

Core Switching

Arista DCS-7050TX

Virtualization

Proxmox

Storage

TrueNAS
Synology

Wireless

UniFi

Source Control

Forgejo — primary self-hosted remote
GitHub — synchronized off-site remote

Management

HomeLab Toolkit
Homepage Dashboard

Monitoring

HomeLab Doctor — functional health and failure-only reporting
Beszel — lightweight host and container history
Homepage — daily service view
Prometheus/Grafana — bounded long-term metrics and dashboards, complete and
retained (see `docs/projects/completed projects/Prometheus-Grafana-Observability.md`)

---

# 7. Operational Workflow

Every project follows the same lifecycle.

Plan

↓

Document

↓

Implement

↓

Validate

↓

Backup

↓

Commit to Git

↓

Tag Release

---

# 8. Success Criteria

Project Mini Atlas is considered successful when:

✓ Every device is documented.

✓ Every configuration is backed up.

✓ Every important decision has an Architecture Decision Record.

✓ Every network connection is understood.

✓ Every service is monitored.

✓ Recovery procedures have been tested.

✓ Documentation is always current.

---

# 9. Roadmap

Foundation
✅ Complete

Enterprise Network
✅ Complete

Dashboard
✅ Core Complete

Private Remote Access
✅ Complete

Forgejo
✅ Complete

Monitoring
✅ Core monitoring complete; Prometheus/Grafana is a separate enhancement

Automation
✅ Complete

Self-hosted Services
✅ Current application set operational; additional services are separate projects

Enhancement Project Portfolio
📅 Governed by `docs/projects/README.md`

---

# 10. Guiding Question

Before implementing any new feature ask:

Does this make Project Mini Atlas:

- More useful?
- More understandable?
- More secure?
- More maintainable?
- More enjoyable?

If the answer is no...

Don't build it.
