# M1/D4 fixed Doctor inactive additive install result

**Date:** 2026-10-25  
**Corrected source:** Stream A commit `28d9d6be`  
**Result:** PASS — installed inert; no capability or model exposure

## Outcome

The corrected additive-only card installed the eight previously absent LXC104
files. `systemd-sysusers` created:

- `aster-doctor-caller` UID/GID 978, with only its primary static group; and
- `aster-doctor-client` GID 979, containing only `aster`.

Both unit files passed `systemd-analyze verify`. Both services are disabled and
inactive, both runtime sockets are absent, and no target was started or enabled.
The five Python files, two units and sysusers fragment match all eight pinned
SHA-256 values, ownership and modes.

An independent postcheck found Aster and `homelab-broker.service` still active
and enabled. Read-only database checks found zero fixed-Doctor agent, service,
capability, request or audit rows. Transfer archives, installer and root-only
staging directories were removed. No broker or Mac source was replaced; no
restart, enrollment, grant, live read, model route/call, B60 or F2/F6 change
occurred.

## Failed first attempt and recovery

The first approved attempt used `/etc/sysusers.d`, which does not exist on this
Debian/systemd 257 guest. It stopped before identity creation. Its rollback trap
removed the seven files already copied, and an independent recovery check proved
all eight targets and identities absent, sockets absent, staging removed and
production services healthy.

The corrected manifest uses `/usr/lib/sysusers.d`, pins the exact 12 target
paths and adds a regression that rejects the obsolete path. Seven focused
bundle/archive tests pass. The successful retry used archive SHA-256
`f57c1cf64f140c3bc64603402f6ea925bb34b559fc63ce41a5b19051f10feb81`.

## Remaining gates

The installed files are inert. Separate review and approval still precede:

1. deploying/validating the Mac producer pair;
2. checkpointing and replacing the two broker sources plus controlled broker
   restart;
3. activating the broker-private gateway and dedicated caller;
4. enrolling the one observer identity/service/Green capability/grant;
5. one fixed live read and recovery proof;
6. held-out usefulness acceptance; and
7. any Aster or connected-Codex model-route exposure.

The first live read is impossible until the producer sidecar, broker source,
services and enrollment are separately in place. This installation alone does
not advance model authority.
