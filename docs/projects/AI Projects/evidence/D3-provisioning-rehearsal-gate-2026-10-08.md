# D3 provisioning rehearsal — prepared, not executed remotely

## Completion record — supersedes prepared status

Jason approved the exact rehearsal. The 13-file archive hash matched the approval;
all destination paths were absent. Created only the specified root-owned staging
directories, verified the archive and per-file manifest, and ran the fictional
fixture suite in each installed runtime. Results:

| Environment | Runtime | Fixture tests | Identity preflight |
| --- | --- | --- | --- |
| Aster LXC 104 | Python 3.13.5 | 8 passed | Not invoked |
| OpenBao LXC 117 | Python 3.13.5 | 8 passed | Not invoked |
| Authentik server container on 106 | Python 3.14.7 | 8 passed | 21 existing applications checked; proposed names absent |

Each reported zero model calls, no real credentials used, no accounts created
and delegation disabled. The Authentik preflight count is now 21; all passed the
existing conservative binding checks. This updates the older count without
claiming a general Authentik security audit or checking every possible grant.

Removed exactly all 13 enumerated files and their staging directories on all
three targets; independent absence checks passed. No dependencies installed,
services restarted or production configuration changed. Aster, broker, approval
and OpenBao remain active. Corrected local Doctor against live state reports
healthy, with zero active requests and 37 historical outcomes. No push performed.

This approval is consumed. It proves runtime compatibility and mocked source-local
failure behavior, not actual credential creation or the complete cross-host
handoff. Continue local administrative-handoff and integration preparation before
requesting any real provisioning or private human ceremony.

## Changes and validation

Found that select followed by blocking readline did not bound a partial incoming
frame; a peer could send a prefix and stall indefinitely. Source-local receive
now uses a cumulative deadline and bounded reads, preserving coalesced frames.
Output has a bounded nonblocking write and restores descriptor mode. Controller
also requires exact vault stage order before accepting delivery or revocation.

Eight new source-local tests cover partial frame timeout, coalescing, disconnect,
blocked output, admin revocation on success/failure, uncertain revocation custody
retention and version rejection before admin access. Controller tests additionally
reject early credentials and reordered stages. All vault calls use mocks and all
credential values are fictional. This is not real provisioning proof.

193 delegation tests pass on isolated Python 3.12 with repository-pinned FastAPI
0.133.1, HTTPX 0.28.1 and Pydantic 2.13.4. The system Python 3.9 attempt had missing
dependencies and was not accepted. The eight-test standalone rehearsal also passes
on Python 3.9.6. No production dependencies were installed.

## Exact approval requested

Approve one bounded fictional-data rehearsal on existing LXC 104, LXC 117 and
Authentik's existing `authentik-server-1` container within LXC 106:

1. Recheck health, absent staging paths and the reviewed bundle hash.
2. Copy only the 13-file reviewed source/manifest bundle into newly created,
   root-owned mode-0700 staging directories, files mode 0600. No overwrite.
   LXC 104/117: `/var/tmp/aster-provision-rehearsal-20261008`.
   Authentik container: `/tmp/aster-provision-rehearsal-20261008`.
   Use owned SSH pipes; no guest dependency installation or service restart.
3. Verify exact manifest names/hashes before execution; compile sources and run
   `provision_rehearsal.run()` in each environment with bytecode writing disabled.
   In Authentik use its existing `ak shell` and `run(identity=True)` to additionally
   perform read-only ORM checks for unused names and existing access bindings.
   Root is for temporary file custody/runtime access, not authority to provision.
4. Emit only fixed result metadata, suppress startup/error details. On failure
   stop and retain uncertainty; never invoke identity/vault/gateway provisioning.
5. Remove only enumerated staged files/directories after tests, including fixture
   temporary files through their context managers. Recheck service health.

Local bundle: `/private/tmp/aster-provision-rehearsal-20261008.tar`.
SHA-256: `77c855dc871d3ccb8d338e0233692c6373414465d5eebf975592438ce8dfac5f`.
Contains the ten controller manifest sources plus `test_provision_node.py`,
`provision_rehearsal.py`, and their generated `rehearsal-manifest.json`.
Read-only preflight: Python 3.13.5 on 104/117, Python 3.14.7 in Authentik;
all proposed staging paths absent. Recheck immediately before execution.

No real credentials, recovery shares, Keychain access, new accounts, vault writes,
model calls, gateway activation, permission changes or Git push are included.
Risk is temporary source files and a bounded test process on live guests; existing
services remain running. Rollback is removal of exactly the staged files; no
production configuration is changed. If a path already exists, abort rather than
reusing or deleting it. Approval required because this writes files and executes
reviewed fixtures remotely (repository AGENTS.md).

## What follows

This rehearsal validates installed runtimes and the source-local failure paths,
not the complete cross-host private transfer. Finish bounded administrative
handoff/staging lifecycle and complete transfer rehearsal before requesting real
inactive-identity provisioning. No further human vault ceremony should open until
that complete procedure is ready. Delegation remains disabled throughout.
