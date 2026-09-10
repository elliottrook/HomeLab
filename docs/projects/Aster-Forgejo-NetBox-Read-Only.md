# Aster Forgejo and NetBox Read-Only Integration

Status: graduated 2026-09-09

## Decision

Aster may answer bounded current-state questions about Forgejo and NetBox, but
it does not receive either API token and cannot connect to either service.
Credentials and raw responses remain on the source guests. Only strict,
content-minimized JSON reports cross into LXC 104.

```text
Forgejo LXC 108 loopback API -> strict Forgejo producer --+
                                                       +-> Proxmox validator/transport -> LXC 104 read-only reports -> Aster
NetBox LXC 111 loopback API  -> strict NetBox producer -+
```

This avoids a new inter-VLAN firewall path and makes the security boundary
independent of model behavior: the model cannot use a credential or construct
an arbitrary source request because neither exists in its guest.

## Authority

| Source | Identity | Effective authority |
|---|---|---|
| Forgejo | `aster-readonly` | Restricted account; no repository/organization creation; `read` collaborator on `jason/homelab` only; `read:issue`, `read:repository`, `read:user` token scopes |
| NetBox | `aster-readonly` | Active non-superuser with unusable password; one enabled object permission containing only `view`; token `write_enabled=false` |
| Aster | `aster` service account | Read only the two validated report files; no source credential and no direct source connection |

The one-time Forgejo administrator token used to establish the collaborator
and account restrictions was deleted immediately after provisioning and its
absence was verified. The pre-existing NetBox administrator token was not
reused or changed.

## Published data

Forgejo publishes only repository state and counts for `jason/homelab`, an
abbreviated commit identifier/timestamp, and latest action status/timestamp.
It excludes repository contents, diffs, commit messages and authors, issue and
pull-request text, and workflow logs.

NetBox publishes only approved inventory identity, status, role/type,
placement, primary IPv4 address, VLAN/prefix membership and aggregate counts.
It excludes descriptions, config contexts, custom fields, contacts, journal
and change records, secrets and any mutation capability.

Each schema rejects additional fields. Reports are capped at 128 KiB for
Aster, inventory collections at 256 items, and freshness at 15 minutes.

## Deployment and scheduling

- `aster-forgejo-report.service` runs unprivileged in LXC 108 and can reach
  only loopback under its systemd IP policy.
- `aster-netbox-report.service` runs unprivileged in LXC 111 with the same
  loopback-only policy.
- `aster-source-reports.timer` runs every five minutes on Proxmox. It invokes
  the two producers with `pct`, validates pulled files, and pushes only
  candidates that pass the schema. LXC 104 receives each report atomically as
  `root:aster` mode 0640.
- `aster-agent.service` sees `/var/lib/aster/source-reports` through a systemd
  `ReadOnlyPaths` restriction.

## Graduation evidence

- Local producer/reader/transport suite: 13/13 passed.
- Deployed Aster reader, routing and policy suite: 41/41 passed.
- Both source producer units completed successfully with mode-0600 output.
- Forgejo sanitized evidence covered one repository with 19 branches and no
  current action run; NetBox sanitized evidence counted 23 devices, 12 VMs,
  one site, one rack, seven VLANs and seven prefixes.
- Deliberate empty-payload write probes returned HTTP 403 for both identities,
  and before/after issue and device counts were unchanged.
- The live model graduation suite passed 4/4: Forgejo report use, NetBox report
  use, Forgejo write refusal and sensitive-field exclusion.
- Aster remained active and its unauthenticated health endpoint returned
  `status=ok` after restart.
- The accepted 26-source knowledge snapshot was built from clean HomeLab
  commit `a9d4a5c`, has SHA-256
  `227af3a7e4b46f93e1ea690e18205347a6b0bef1630141d6a34d78bde89fca4c`,
  and retrieves `project/Aster-Operations.md` first for the integration
  architecture query.

No Forgejo issue, NetBox object, firewall rule or source-service configuration
was changed by the acceptance tests.

## Failure and rollback

The integration fails closed. A missing, stale, malformed, incorrectly owned
or writable report returns `unavailable`; no fallback source call occurs.
Disable the Proxmox timer to suspend refresh. Restore the dated LXC 104 Aster
source rollback and remove its source-report drop-in to remove the readers.
Source-account/token revocation is deliberately separate and requires a
source-local administrative decision.
