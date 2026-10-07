# AI-PAM Operational Reference

> Authority: current-with-exclusions
>
> Reviewed: 2026-09-26

## Narrow operational update — 2026-10-06

The approved LXC 104 approval-service update exposes exact request
`{"method":"automation.status"}` on `/run/homelab-broker/approval.sock` to its
configured Aster peer UID. It returns only the global-enabled boolean without
a human actor. Management/approval methods retain human identity requirements.
Socket permissions and switch value were unchanged; wrong-peer and actor-less
management requests were denied live. This does not enable Codex delegation.
See [deployment and recovery evidence](../projects/AI%20Projects/evidence/D3-broker-deployment-result-2026-10-06.md).
This narrow check does not revalidate the whole September 26 reference.

## Current service boundary

AI-PAM is the privileged-access control plane for AI-assisted HomeLab work. The
broker runs on Aster LXC 104 and exposes only peer-bound Unix sockets; it has no
general shell, arbitrary network target or secret-dump capability. OpenBao LXC
117 holds separate restricted service credentials and remains outside the AI
trust boundary. Authentik supplies human identity and fresh passkey
authentication for privileged approval.

The supported human control surface is Aster Companion. Version 0.2.2 provides
the approval inbox, deny/approve actions, AI-client lifecycle management,
service controls, history/audit views and the global AI-access kill switch.
Closing its final macOS window terminates the application so it can reopen
normally from the Dock or Applications. The installed Keychain item should be
set to **Always Allow** for that signed application; secret values are never
shown in the management UI.

## Authority and inventory

NetBox is authoritative for the existing `hermesagent` LXC 104 and `openbao`
LXC 117 interfaces and IP addresses. The broker is a Unix-socket service on
LXC 104, so it does not receive a separate IP, DNS name or NetBox device. The
existing private Aster Companion Homepage tile is the correct operator entry
point. Do not add direct OpenBao, broker or gateway tiles: none exposes a safe
human web-administration surface.

Forgejo is the authoritative repository. The broker's Forgejo Green reader and
Yellow safe-write path use separate minimum-scope identities and OpenBao paths.
The safe-write path can create one file only on a new `ai-pam/` branch; it does
not permit direct-main, destructive or arbitrary repository operations. GitHub
is the automatically synchronized protection mirror, not a second normal push
target.

## Safe operation and failure behavior

Green capabilities may run only within their recorded scope. Yellow requires
an explicit approval; Red additionally requires fresh passkey authentication.
Approvals are payload-bound, one-use and expire. New AI clients begin in
Probation and require tested promotion. Retired, suspended or revoked clients
must be denied.

The global kill switch denies new issuance while preserving direct human
administration. Broker, Authentik and OpenBao dependency outages fail closed.
Stopping AI-PAM must not remove human access to Forgejo, Authentik, OpenBao
recovery or normal HomeLab administration. OpenBao root/recovery material,
Authentik recovery credentials and passkey private material are Black and must
never enter Aster, an AI conversation, Git or routine logs.

## Monitoring, recovery and ownership

HomeLab Doctor checks the exact service/capability catalogue, global and agent
state, database integrity, expired active requests, required systemd units and
sockets, OpenBao TLS/seal state, Authentik discovery, rotation dates, audit
freshness, backup age and isolated-restore evidence. Its output is metadata
only. The existing Aster and OpenBao guest backups cover the deployed services;
the broker also retains root-only recovery checkpoints.

Restore order is network/DNS, OpenBao, broker state and policy, Authentik
integration, Companion/API, target integrations, then agents. OpenBao recovery
is human-operated: a restricted human root-ceremony AppRole starts a ceremony,
but two independent PGP-held recovery shares are still required. Temporary
bootstrap/root tokens used during deployment were revoked. Recovery material
must remain human-held and outside the Aster knowledge corpus.

The completed implementation and detailed evidence are in
`docs/projects/completed projects/homelab-credential-broker.md`. Current
commands and architecture are in `docs/reference/Aster-Operations.md` and
`ops/credential-broker/README.md`.
