# M1 independent approval ingress — inactive installation result

> Result: **PASS — installed but never started**
>
> Approved source: `523e7f76`
>
> Installation card: `M1-independent-ingress-inactive-install-card-2026-10-24.md`
>
> Target: Proxmox LXC 104

## Installed boundary

The approved bounded installation created dedicated user and group
`aster-approval` at UID/GID 1905 with no home and `/usr/sbin/nologin`. It copied
the two pinned Python modules and two no-`[Install]` systemd unit candidates,
then derived the five-key environment file locally from the existing hashed
approver-subject source. No subject value, token or credential was printed or
copied into this record.

| Target | SHA-256 |
|---|---|
| `/opt/aster-agent/approval_ingress.py` | `797d492e66748e103e8bbff67b9fb714d11a7229c5fb6fcb9b74d2e8d7772744` |
| `/opt/aster-agent/approval_ingress_service.py` | `e613587f8fb2bd82c4f92b4d1135ac15aa5acc4982feaf8f1b82428feb62eff8` |
| `/etc/systemd/system/aster-approval-ingress.service` | `04bdd7773e15a9dff8011870864066f0e88c446983ebaf53104fe00567d0c970` |
| `/etc/systemd/system/homelab-broker-approval-independent.service` | `b766d6fba2c2c040a60ae3775636a30d68c2ffc7dd885235c788b4b7b572b80b` |

The environment file is root:`aster-approval`, mode 0640. A content-free
validator confirmed exactly the approved issuer, audience, JWKS, private socket
and hashed-subject keys and a nonempty lowercase SHA-256 allowlist.

## Independent postcheck

- `systemd-analyze verify` passed both installed units.
- Both units are inactive, not enabled and have a zero main-process start
  timestamp. They have never run.
- Both modules imported under UID 1905 with bytecode creation disabled.
- Port 9121 has no listener or proxy route.
- Port 9120 and `homelab-broker`, `homelab-broker-approval` and `aster-agent`
  remained healthy.
- The existing approval socket retained its path, owner, group and mode.
- The broker database digest matched the root-only pre-install inventory; this
  installation created and consumed no approval or grant.
- Temporary Proxmox and LXC staging files were removed after validation.

`useradd` reported that fixed UID 1905 is above Debian's local
`SYS_UID_MAX=999`. That warning did not alter the requested UID, no-home or
nologin properties and is retained here rather than hidden.

## What this proves

The independent identity and fail-closed process artifacts can coexist on disk
without changing production traffic or authority. This closes the inactive
installation gate only.

It does not prove live Authentik token behavior, passkey-specific assurance,
proxy/firewall reachability, restart recovery or a safe authority cutover. The
old Aster-trusted approval socket remains the live path. Starting either new
unit, routing traffic to port 9121 or removing the old Aster access requires a
separate zero-overlap cutover card and approval.
