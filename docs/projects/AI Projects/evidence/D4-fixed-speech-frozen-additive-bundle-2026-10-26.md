# D4 fixed Aster Speech — frozen additive bundle

**Date:** 2026-10-26  
**Source:** `de7256dc4cfbcf5a668a9e1f2c5bb3182a26402b`  
**State:** frozen and target-tested; not installed

## Exact target shape

`services/aster-agent/deploy/fixed-speech-bundle-manifest.json` pins nine
root-owned mode-0644 additions in LXC104:

- six Python modules for catalogue validation, fixed Speech projection,
  capability, gateway and caller;
- two distinct disabled service units; and
- one sysusers file for `aster-speech-client` and
  `aster-speech-caller`.

Every final target is currently absent. The one shared installed dependency is
`/opt/aster-agent/sysadmin_investigation.py` at SHA-256
`bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe`.
The correction at source `de7256dc` reuses its existing `homelab-doctor`
status target, so no shared production file needs replacement.

The manifest requires both units to remain disabled and inactive. It excludes
service start/enable, broker restart, database enrollment, capability grant,
live read, model route/call, automatic routing, repair and Git push. Rollback
removes only exact candidate additions after confirming both units and sockets
are inactive.

## Frozen validation

The validator suite passes **4/4** and rejects source, target, dependency,
effect, unit or exclusion drift.

The complete 16,567-byte archive had SHA-256
`9d545700b51c9433fec4b396dd0d89cb3bd99d50c754912caac82d75ea724665`.
In isolated LXC104 staging:

- focused capability/caller/gateway tests passed **22/22**;
- manifest tests passed **4/4** and the validator passed;
- sysusers dry-run accepted the distinct proposed identities;
- both exact units passed `systemd-analyze verify`; and
- all host and guest staging paths were removed afterward.

Aster Agent remained active. No final path, identity, unit, socket, database,
grant or service state changed.

## Next gate

The next step is a bounded inactive installation: recheck all nine absences and
the dependency pin, checkpoint the absence set, copy only the exact files,
create only the two proposed identities, daemon-reload, and prove both units
remain disabled/inactive with no sockets or database rows. Activation,
registration, grant and any broker restart remain separate.
