# Aster Games operations

> Authority: live service state, NetBox, and the AsterTV v4 retro-gaming
> project record
>
> Review state: server infrastructure validated 2026-11-07; AsterTV client
> integration remains blocked by the v3 acceptance gate

Aster Games is the private server-side retro-library platform. It runs in
unprivileged Proxmox LXC 129 (`aster-games`) at `192.168.20.38` and stores the
canonical library on the quota-bounded TrueNAS `Media/Games` dataset. RomM is
the catalogue authority, ROMarr owns verification/import, and the Aster Games
broker exposes sanitized reads and pending proposals only.

The two browser interfaces are private and Authentik-protected:

- `https://games.elliottrook.com` — RomM catalogue and administration;
- `https://romarr.elliottrook.com` — ROMarr verification/import operations.

There is no public DNS record or public ingress. Direct UI ports accept only
the reverse proxy. The broker has no host listener. Do not expose a direct
port, enable device installation, or give an AsterTV appliance an upstream
administrative credential.

## Normal operating state

- RomM, ROMarr, MariaDB, Valkey, and the broker are healthy.
- RomM alone is enabled as ROMarr's library integration.
- Prowlarr and SABnzbd connection tests pass, but both entries and ROMarr
  automatic import remain disabled until a separately reviewed lawful-source
  workflow is accepted.
- The release gate reports `v4_client_work_allowed=false`.
- The canonical library is writable by ROMarr and read-only in RomM.
- Download staging is separate from the canonical library.
- Doctor output contains health, policy, and free-space state only. It must
  never contain titles, filenames, account data, paths below approved roots,
  tokens, or credentials.

Run the service-local semantic check from Proxmox:

```sh
ssh -o BatchMode=yes root@192.168.50.10 \
  "pct exec 129 -- python3 /opt/aster-games/ops/doctor.py"
```

A healthy result has `ok: true`, five healthy service checks, acceptable
library/state headroom, acquisition disabled, auto-import disabled, and the v4
client gate closed. Beszel supplies resource history; central HomeLab Doctor
owns alert delivery.

## Safe import boundary

Only material that the operator may lawfully use can enter staging. A file is
not trusted because a download completed. ROMarr must classify it against the
reviewed DAT set, reject ambiguity, avoid overwriting an existing canonical
file, and quarantine duplicates or failures. RomM scans the canonical library
only after verification/import succeeds.

The standing synthetic fixture is original CC0 test material. It exists only
to prove storage, DAT classification, duplicate quarantine/restore, RomM scan,
broker sanitization, backup, and recovery. Never copy its title into routine
monitoring or the derived Aster knowledge corpus.

## Backup and restore

The enabled Proxmox all-guests job protects LXC 129. Daily TrueNAS snapshots
retain canonical media state for 30 days. Application backup is separate:

```sh
ssh -o BatchMode=yes root@192.168.50.10 \
  "pct exec 129 -- /opt/aster-games/ops/backup_aster_games.sh \
  /srv/aster-games/backups/<new-id>"
```

The backup script quiesces RomM, ROMarr, and the broker; creates a consistent
MariaDB dump; protects RomM, ROMarr, broker, and DAT state; records exact image
and deployment identities; stores secret references rather than values; and
restarts the production stack. The output is root-only and checksum-manifested.
Do not call a backup complete unless its manifest verifies and Doctor is clean.

Recovery order is database, cache, RomM, ROMarr, then broker. Prove a candidate
backup in the no-egress disposable harness before production recovery. The
accepted 2026-11-07 proof matched aggregate database/proposal counts and a
sampled media checksum, refused overwrite, detected capacity/dependency/auth
failures, survived service restart, restored an exact pre-upgrade state, kept
Doctor content-silent, and destroyed its runtime afterward.

For production recovery, first disable acquisition and proposal clients, take
an exact state checkpoint, and preserve the current library snapshot. Restore
only mutually compatible application state and pinned images. Never roll back
the media dataset merely to repair application configuration.

## Update and rollback

1. Record the current image digests, deployment hashes, Doctor result, backup
   manifest, and TrueNAS snapshot.
2. Review upstream release notes and the Compose diff. Keep Prowlarr, SABnzbd,
   automatic import, device installation, proposal execution, and the v4 gate
   disabled.
3. Restore the backup into the disposable no-egress stack and run all recovery
   checks before changing production.
4. Change one service layer at a time in dependency order and rerun static
   validation, container health, service-local Doctor, ingress/auth checks, and
   the synthetic fixture checks.
5. On failure, stop proposal clients and acquisition, restore the exact
   configuration/database checkpoint and prior image pins, start in dependency
   order, and verify Doctor plus the sampled media checksum.

Do not use a floating image tag, unattended updater, or broad filesystem
permission rewrite.

## Credentials

Secrets are root-owned source-local files beneath `/etc/aster-games/secrets`.
They are not Git content and must not be printed into tickets, logs, shell
history, backups, or the wiki. Rotate one trust edge at a time:

1. take the application backup and a configuration checkpoint;
2. create a unique replacement at its owning service;
3. write it directly to the correct root-only source-local file;
4. restart only the dependent service and verify its bounded connection test;
5. revoke the old credential only after the new path passes;
6. verify Doctor and confirm no secret-bearing transfer artifact remains.

RomM client tokens must stay scoped to their consumer. Prowlarr and SABnzbd
credentials belong only to ROMarr. A future AsterTV device identity must be
unique, revocable, device-bound, and created only after the v3 gate and the
later client security review.

If a credential is exposed, disable the affected integration, rotate it at the
authority, replace the local file, restart the dependent service, validate,
and review bounded authentication logs. Do not paste the exposed value into an
incident record.

## Hard stops

Stop and require a new bounded decision for public exposure, real-content
acquisition automation, a failed or unavailable recovery checkpoint, an
ambiguous existing library, unexpected writes outside the approved roots,
credential leakage, material network/authority drift, or any AsterTV/Kodi/fleet
work before durable v3 deployment and owner-acceptance evidence opens the gate.
