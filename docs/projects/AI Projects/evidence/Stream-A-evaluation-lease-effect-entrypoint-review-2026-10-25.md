# Stream A evaluation-lease effect-entrypoint review — 2026-10-25

> Decision: **REJECTED BEFORE INSTALLATION OR EFFECT**

## Reviewed source

- platform implementation: `c3b316ab27b770e3703cf6967e5b8665f489172c`;
- metadata pin follow-up: `d56084a5`;
- entrypoint SHA-256:
  `d42963fb84730aa3a6f9a8206c1626b1b526ec2b9ee4ac5456716ed7b4be8b97`;
- wrapper SHA-256:
  `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276`;
- card SHA-256:
  `7c07d33316bfefb30e722a384ad5fd1e833674a676762c41bfff54db8f78135f`.

A clean commit archive passed 30/30 evaluation-lease tests and compiled all
four Python modules. The disabled wrapper behavior and reported hashes
reproduced. Those checks did not cover four release-blocking cases.

## Failed boundaries

1. `evaluation_lease.py` still pins superseded M3 stage-manifest digest
   `357b4e3d…124a00`. The corrected packet installed in LXC110 is
   `69ffc589…72165`; an otherwise valid M3 outcome would fail the lease contract.
2. The deployment card requires the destination root and every target absent,
   then permits rollback removal of that root. The accepted four-file inactive
   library baseline already occupies that exact root. A correct upgrade must
   require those four exact files, add only the entrypoint and wrapper, and
   preserve the four files on rollback.
3. Only `acquire` enforces an exact intent key set. A direct regression probe
   showed `heartbeat` accepting an unexpected field. `restore` also accepted
   an unexpected field and converted the string `"false"` into recovery mode
   through `bool()`. Every phase needs an exact schema and literal types.
4. The intent loader accepted a regular mode-`0644` file. Effectful root input
   must be a root-owned, mode-`0600`, regular non-symlink file. The state path
   must also be fixed or allowlisted so the independent watchdog and recovery
   operator inspect the same durable state.

The platform owner received these exact findings and regression requirements.
No file was installed, no entrypoint was invoked on Proxmox, no lease or state
was created, no consumer changed and no model request ran. The accepted inert
four-file library installation remains unchanged.
