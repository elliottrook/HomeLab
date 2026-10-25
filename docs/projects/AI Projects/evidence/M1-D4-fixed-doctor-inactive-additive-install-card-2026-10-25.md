# M1/D4 fixed Doctor inactive additive install card

**Date:** 2026-10-25  
**Source:** Stream A commit `a37686d9`  
**Manifest SHA-256:** `ea56672fe1885508c015b0543d808e89559def45f9bbdb71108d1411d31fde0b`  
**Transfer candidate:** `/private/tmp/aster-fixed-doctor-v1-staging-v2.tar.gz`, 18,032 bytes, SHA-256 `ef730c8290ce7e36812ac776311a926077e14ec1404dba481b558e3384dee5ec`  
**State:** approval-ready; not executed

## Purpose and limit

Install only the eight currently absent LXC104 files needed for the fixed
Doctor caller and broker-private gateway, create their dedicated system
identity/group, verify the units, and leave both services disabled and inactive.

This card does **not** replace the two broker sources or two Mac producer
sources in the full target manifest. It does not restart the broker, load a
sidecar, enroll an AI-PAM agent/service/capability, create a grant, start or
enable a service, make a live read, expose an Aster/model route, call a model,
change F2/F6, or touch the B60.

## Fresh preconditions

Abort before writing if any check fails:

1. The archive size/digest and the embedded manifest/validator match the values
   above; the validator reports 12 files, four replacements and eight additions.
2. These eight final targets are still absent:
   - `/opt/aster-agent/fixed_doctor_caller.py`
   - `/opt/aster-agent/fixed_doctor_gateway.py`
   - `/opt/aster-agent/fixed_doctor_capability.py`
   - `/opt/aster-agent/doctor_model_projection.py`
   - `/opt/aster-agent/doctor_structured_incident_adapter.py`
   - `/etc/systemd/system/aster-fixed-doctor-caller.service`
   - `/etc/systemd/system/aster-fixed-doctor-gateway.service`
   - `/etc/sysusers.d/aster-fixed-doctor.conf`
3. `aster-doctor-caller` and `aster-doctor-client` are absent.
4. The three installed dependency hashes equal the manifest pins.
5. `aster-fixed-doctor-caller.service` and
   `aster-fixed-doctor-gateway.service` are not running or enabled; Aster and
   `homelab-broker.service` are healthy before the change.
6. No host maintenance, backup, F2 scan or whole-host lease is active. The
   operation does not need B60 exclusivity.

## Exact change

1. Transfer the pinned archive and re-run the embedded validator in a fresh
   root-only directory.
2. Install only the eight `rollback=remove` entries at their exact manifest
   paths, ownership and modes. Do not install any `rollback=restore` entry.
3. Run `systemd-sysusers` against only
   `/etc/sysusers.d/aster-fixed-doctor.conf`.
4. Run `systemctl daemon-reload` and `systemd-analyze verify` on the two exact
   units. Do not start or enable them.
5. Verify:
   - every installed SHA-256, owner, group and mode;
   - the static `aster-doctor-caller` account has only its primary group and
     the caller unit declares exactly `hlabroker-clients` and
     `aster-doctor-client` as runtime supplementary groups, with no approval or
     administrative group;
   - Aster is newly added only to `aster-doctor-client`; no other existing
     Aster group membership is changed by this installation;
   - both new units are disabled and inactive, and neither runtime socket exists;
   - the broker database still has no fixed-Doctor agent, service, capability,
     grant, request or audit row;
   - Aster, the broker and their existing sockets remain healthy; and
   - no model request or fixed-Doctor broker/audit event occurred.
6. Remove the transfer/staging files and retain only content-free validation
   evidence.

## Rollback

If any postcondition fails, while both new units are confirmed inactive:

1. remove only the eight newly installed files;
2. remove Aster from `aster-doctor-client`, delete `aster-doctor-caller`, then
   delete `aster-doctor-client` only if it has no remaining members/files;
3. run `systemctl daemon-reload`;
4. prove both unit names are not found, both runtime sockets are absent, the
   eight file targets are absent, and Aster/broker remain healthy; and
5. reconcile any uncertain identity or filesystem outcome before retrying.

No prior live file is replaced by this card, so there is no source restore.

## Success meaning

A pass proves only that the additive files and least-privilege identities can
reside safely on LXC104 while inert. Producer activation, broker source
replacement/restart, unit activation, AI-PAM enrollment, first live read,
held-out value proof and model-route exposure remain separate gates.
