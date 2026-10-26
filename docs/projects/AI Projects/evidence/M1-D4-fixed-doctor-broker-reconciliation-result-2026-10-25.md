# M1/D4 fixed Doctor broker reconciliation — live result

**Date:** 2026-10-25
**Source:** Stream A commits `5ad9cbc5`, `9a2ad117`, `3fe573bd`, `93bd6049`
**Decision:** PASS; broker source gate complete; authority remains unenrolled

Jason approved the final corrected retry after two measured, fully recovered
NO-GO attempts. The first identified the wrong health-probe identity and an
incorrect SQLite rollback owner. The second identified a listener-readiness
race after systemd active state and socket creation. The final reviewed script
used registered client `hlabagent`, correct database custody and one bounded
successful-health loop shared by forward and rollback paths.

The final run completed successfully. LXC104 now has:

- `/opt/homelab-broker/broker_admin.py` SHA-256
  `e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa`,
  root:root mode `0700`;
- `/opt/homelab-broker/broker_service.py` SHA-256
  `c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e`,
  root:root mode `0644`;
- unchanged `broker_core.py` and systemd-unit hashes;
- a root-only rollback checkpoint at
  `/root/aster-fixed-doctor-broker-pre-20261025T1825PDT` containing both
  predecessors, a consistent SQLite backup and SHA-256 inventory.

Independent postchecks passed:

- broker and Aster Agent are active; broker `NRestarts=0`;
- `hlabagent` receives the ordinary content-free broker health response;
- broker database custody is `hlabroker:hlabroker` mode `0600` and
  `integrity_check` returns `ok`;
- Forgejo project-document capability metadata remains
  `forgejo-mcp-project-write`, Yellow, non-probationary and enabled;
- source routing still contains its dedicated socket and `create_file_batch`;
- fixed-Doctor agent, service, capability, grant and request counts are all
  zero;
- both fixed services remain disabled/inactive and both fixed sockets remain
  absent.

No enrollment, grant, fixed read, model call, Forgejo write, project-document
change, Companion change, schedule change or F2/F6/B60 action occurred. The
next separate gate is activation of the dedicated gateway/caller, enrollment
of exactly one Green observer grant and one bounded live fixed read, with
rollback to disabled services and zero fixed rows.
