# M1 independent ingress environment-lineage correction — 2026-10-24

## Finding

Review of the inactive independent-approval units found that the broker candidate
referenced `ASTER_BROKER_APPROVER_SUBJECT_HASHES` without loading an environment
file. The ingress candidate separately loaded `/etc/aster/approval-ingress.env`
and used `ASTER_APPROVAL_SUBJECT_HASHES`. Installing the pair unchanged could
therefore have left the broker with an empty or unresolved subject allowlist.
No live installation had occurred, so production was unaffected.

## Correction

The broker candidate now loads the same root-managed
`/etc/aster/approval-ingress.env` file as the ingress process and consumes the
same `ASTER_APPROVAL_SUBJECT_HASHES` value. This gives the two independent
processes one configuration lineage for the hashed allowed subject while keeping
the clear subject and token out of the unit files and repository.
The broker unit also declares `aster-approval` as its sole additional group so
it can read a root:`aster-approval` mode-0640 environment file and create the
mode-0660 approval socket for that group without changing the broker account's
global memberships.

Pinned candidate hashes after correction:

| Artifact | SHA-256 |
|---|---|
| `aster-approval-ingress.service.candidate` | `04bdd7773e15a9dff8011870864066f0e88c446983ebaf53104fe00567d0c970` |
| `homelab-broker-approval-independent.service.candidate` | `b766d6fba2c2c040a60ae3775636a30d68c2ffc7dd885235c788b4b7b572b80b` |
| `test_independent_approval_units.py` | `c436608f6fb8adc224d4beb26a4cf9df01014bcabae819595ef259230a941f73` |

## Validation

The static unit suite now includes a regression that requires both services to
load the same environment file, requires the broker command to use the ingress
subject-hash variable, and rejects the orphaned variable name. Six unit-shape
tests pass. The full focused approval path—factory configuration, JWT issuer and
audience checks, subject entitlement, socket peer binding, Yellow single-use and
Red passkey denial—passes 18/18 in a disposable environment built from the
service's pinned `requirements.txt`.

This remains an inactive source correction. No account, group, environment file,
unit, socket, listener, route, firewall rule, grant or approval changed. Exact
live identity, network/proxy, checkpoint, cutover and rollback review remains a
separate deployment gate.

