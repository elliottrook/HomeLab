# M1 independent approval ingress — inactive installation card

> Status: approval-ready; **not authorized or executed by this card**
>
> Source commit: `523e7f76`
>
> Target: Proxmox LXC 104 only

## Purpose

Stage the already tested independent approval-ingress candidate without changing
production traffic or authority. This installation creates the dedicated Unix
identity, copies two Python modules and two inactive systemd units, and creates a
root-managed configuration file by transforming the existing hashed-subject value
locally inside LXC 104. It does not print or export that value.

The current `homelab-broker-approval.service`, `aster-agent.service`, port 9120,
approval socket, Nginx Proxy Manager route and AI-PAM grants remain unchanged.
The new units have no `[Install]` section and must remain disabled and inactive.

## Fixed inputs

| Repository source | Target | SHA-256 |
|---|---|---|
| `services/aster-agent/approval_ingress.py` | `/opt/aster-agent/approval_ingress.py` | `797d492e66748e103e8bbff67b9fb714d11a7229c5fb6fcb9b74d2e8d7772744` |
| `services/aster-agent/approval_ingress_service.py` | `/opt/aster-agent/approval_ingress_service.py` | `e613587f8fb2bd82c4f92b4d1135ac15aa5acc4982feaf8f1b82428feb62eff8` |
| `services/aster-agent/delegation/deploy/aster-approval-ingress.service.candidate` | `/etc/systemd/system/aster-approval-ingress.service` | `04bdd7773e15a9dff8011870864066f0e88c446983ebaf53104fe00567d0c970` |
| `services/aster-agent/delegation/deploy/homelab-broker-approval-independent.service.candidate` | `/etc/systemd/system/homelab-broker-approval-independent.service` | `b766d6fba2c2c040a60ae3775636a30d68c2ffc7dd885235c788b4b7b572b80b` |

The dedicated identity is fixed at UID/GID 1905 after a fresh collision check.
The configuration target is `/etc/aster/approval-ingress.env`, owner
root:`aster-approval`, mode 0640. It contains only:

- the existing public Companion issuer;
- audience `aster-companion`;
- the issuer's public JWKS URL;
- `/run/homelab-broker-approval/approval.sock`; and
- `ASTER_APPROVAL_SUBJECT_HASHES`, transformed source-locally from the existing
  `ASTER_BROKER_APPROVER_SUBJECT_HASHES` value.

No token, clear subject, private key or credential is copied into Git, command
output or the operator record.

## Mandatory preconditions

Abort without changing anything if any condition fails:

1. LXC 104 is running and the three production services are active.
2. UID or GID 1905, user/group `aster-approval`, either target Python file,
   either target unit, or the target environment file already exists.
3. The source commit or any of the four source hashes differs.
4. The live Aster virtual environment does not contain the pinned FastAPI,
   HTTPX, PyJWT, Pydantic and Uvicorn versions already observed.
5. The existing broker approver environment does not contain exactly one
   nonempty, comma-separated set of lowercase SHA-256 hashes under
   `ASTER_BROKER_APPROVER_SUBJECT_HASHES`.
6. Port 9121 has a listener, a new route exists, or another maintenance task is
   changing LXC 104.

## Bounded installation

After an exact approval, preserve a root-only inventory of the absent targets and
current service/listener state. Create group and system user 1905 with no home and
`/usr/sbin/nologin`. Copy the four hash-pinned files with root ownership and mode
0644. Build the five-line environment file atomically at mode 0600, validate the
source hash syntax without printing it, then set root:`aster-approval` 0640.

Run `systemd-analyze verify` against both units and `daemon-reload`. Do **not**
start, enable or preset either unit. Do not alter the old approval service,
supplementary group database, NPM, firewall, Companion, Authentik or AI-PAM.

## Validation

The installation passes only if:

- all four target hashes match this card;
- UID/GID 1905 is unique and the identity has no login shell or home;
- the environment file has exactly the five approved keys, correct owner/mode,
  and a syntactically valid nonempty subject-hash set, without displaying values;
- both units verify, are disabled and inactive, and have never run;
- importing both new modules as `aster-approval` succeeds with bytecode disabled;
- port 9121 still has no listener;
- current port 9120 and all three production services remain healthy;
- the old approval socket retains its path, owner, group and mode; and
- no grant, approval request or database row is created or consumed.

## Rollback

Because every target must be absent at entry, rollback removes only the two new
unit files, two new Python files and new environment file, runs `daemon-reload`,
then removes user and group 1905 after proving neither process exists and no file
outside these targets is owned by the identity. Production units are not
restarted. Any unexpected pre-existing target or owned file stops rollback for
review rather than deleting it.

## Later gates excluded

This card does not authorize starting the units, changing the active approval
socket, removing Aster from `hlabroker-approvers`, adding port 9121 to NPM or the
firewall, sending a Companion approval, or granting a connected capability. A
separate cutover card must prove a zero-overlap identity transition, Yellow-only
behavior, Aster denial, verifier acceptance, execution-broker outage independence
and human SSH recovery.

