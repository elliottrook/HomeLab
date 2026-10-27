# SA1/SA2 current incident modules release candidate — 2026-10-26

## Result

**SOURCE AND TARGET TEST PASS; LIVE RELEASE REQUIRES AN ASTER AGENT RESTART.**
After SA0 closed, the exact remaining source/live differences were reviewed.
Three modules form a coherent SA1/SA2 candidate: bounded incident state,
content-minimized reconnect presentation and typed read-only investigation.
The separate Lab Operations reconciliation method is not part of this packet.

## Candidate

| File | Deployed predecessor SHA-256 | Candidate SHA-256 |
|---|---|---|
| `sysadmin_incident_store.py` | `4e8a36a803c3d8e5eac362e4c17a0cadc1f4ae2accca05cc73283b646b8e5c4b` | `5a72b9f9c16ff66c64ac4d93d7f4f6ae9f3a7fe61d7a377efca237a95120e555` |
| `sysadmin_incident_stream.py` | `8aa8c572cbe3208b9b8c1a0ce34dfdab893a064ba79e7e5a87c7d8decca8d683` | `2154598ed14c7364a1ddc03b2c5f39ec1722b25b45de034e629965d46be78971` |
| `sysadmin_investigation.py` | `bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe` | `1f903f4a702d1548783990c38954d4e21a3688f83a062e42416183c7949481ed` |

The candidate adds strict persisted-record revalidation, private SQLite
custody, retention/quota enforcement, bounded presentation fields, protected
incident identifiers, and the fixed-Speech projection. It does not add a live
observation adapter, network discovery, shell execution, repair authority or
automatic routing.

## Newly closed resource defect

Target Python 3.13 emitted `ResourceWarning` for SQLite connections because a
connection context commits or rolls back but does not close the connection.
The store now wraps each connection in a context manager that always closes it.
A regression proves the connection is unusable after the context exits.

The focused local store/investigation/stream suite passes **26/26** with
`ResourceWarning` promoted to an error. A disposable root-only LXC104 packet,
using the installed application environment and current gateway composition,
passes **33/33** investigation, store, stream, gateway and Doctor-adapter tests
under the same warning policy. The temporary packet was removed. No running
file, process, model or service changed.

## Proposed bounded release

The installer `services/aster-agent/deploy/install_sa1_sa2_incident_modules.sh`
requires the exact current gateway and all three deployed predecessor hashes.
It preserves the three old modules under a fresh root-only checkpoint, imports
the candidate with the installed environment, atomically replaces only those
modules, restarts only `aster-agent.service`, and verifies health, zero restart
loop and exact hashes. Any failure restores all three predecessors and restarts
only Aster Agent.

The release does not enable a new adapter or automatic route. A later connected
SA2 observation still requires its registered target, caller, freshness and
effect gate. Broader SA1 completion still needs a bounded iterative loop and
representative reconnect/insufficient-evidence behavior.
