# SA2 gateway configuration identity producer boundary — 2026-10-28

## Result

**SOURCE-ONLY PASS; NOT DEPLOYED.** A fixed producer can now provide
content-free identity evidence for Aster Agent's public systemd unit and source
file. It cannot accept a path, read a secret-bearing environment file, execute
a subprocess, contact a service or change configuration.

## Boundary

The adapter opens exactly:

- `/etc/systemd/system/aster-agent.service`;
- `/opt/aster-agent/aster_agent.py`.

Both must be root-owned regular one-link files, non-writable by group/other and
no larger than 256 KiB. Links, missing files, unsafe custody, oversize input or
any read error produce one content-free `unavailable` observation.

For valid files the model-visible evidence contains only service
`aster-agent`, file count `2` and a 24-character combined digest. File bytes,
paths and individual hashes do not enter the incident. `state=ok` means only
that the registered identity was safely read; it does not assert conformity to
an approved release.

## Validation

- The combined config, NetBox, producer, investigation, selector,
  proposal-boundary and transport suite passes **56/56** locally.
- The same temporary candidate passes **56/56** under LXC104's application
  Python and installed dependencies.
- A read-only target compatibility check returned producer
  `aster-gateway-config-identity/v1`, pair `aster-gateway/config`, file count
  `2` and digest `42b04c30df330b0ef1b30cc0`.
- Temporary candidate files were removed. No service, model, route, incident
  database, configuration or schedule changed.

The adapter will be held with the source-only NetBox adapter for a combined
reviewed release. Backup and log evidence remain open.
