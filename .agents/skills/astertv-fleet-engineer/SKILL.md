---
name: astertv-fleet-engineer
description: Plan, audit, build, repair, onboard, release, or recover an AsterTV appliance and its Kodi, LibreELEC, Jellyfin, Home Assistant, peripheral, and network composition. Use for fleet/device operations; do not use for presentation-only design work.
---

# AsterTV Fleet Engineer

Resolve the exact appliance before proposing a change. AsterTV is one global
release plus hardware/peripheral profiles and approved overlays; Family,
Bedroom, Jen, and Guest are not interchangeable installations.

## Start with authority

1. Read the repository `AGENTS.md` and the active project record.
2. Read `services/kodi/astertv-fleet/README.md`, compile the fleet, and open the
   target's generated desired composition and release plan.
3. Read the existing HomeLab Wiki AsterTV Start Here, target device page, and
   only the operation curriculum relevant to the task.
4. Use NetBox for adopted hardware/network facts, sanitized live queries for
   current state, the Git fleet contract for desired state, and private Forgejo
   releases for immutable bytes. Report disagreements; never choose silently.

For path and precedence details, read [authority map](references/authority-map.md).

## Work in the owning layer

- Diagnose read-only unless the request includes a change.
- Compile before editing. Preserve the target's audio, display, network,
  performance, identity, equipment-control, and recovery contracts.
- Put global behavior in the release, reusable differences in profiles, and a
  one-device exception in a named overlay with owner, compatibility, tests,
  rollback and review/expiry.
- Never copy a live hotfix into desired state without first classifying its
  owner and proving that it belongs.
- Treat Jen's 1080p/stereo ceiling as Jen-only. Guest remains non-deployed until
  its hardware, identity, address, network, and acceptance gates are resolved.
- Keep secret values source-local. Git/wiki/manifests may contain only opaque
  custody references.

## Effects and releases

Before any live effect, use the [deployment gates](references/deployment-gates.md).
The skill does not grant authorization. A plan, approved Stream A, or prior
push does not waive the repository's immediate confirmation requirement for a
new push or remote mutation.

For a release or repair, show the resolved device composition and diff; require
identity, idle playback, checkpoint, artifact hash, compatibility, relevant
tests, health and rollback. Stop on unknown identity, unexplained drift,
broader network need, secret output, active playback, missing checkpoint, or
failed rollback. Apply one authority at a time and validate both allowed and
denied network paths.

Finish by recompiling every active composition, adding a regression fixture for
the defect, updating evidence/resume state, and distinguishing local commit,
remote push, publication, deployment, and owner acceptance.
