# D3 — interrupted root recovery: candidate and bounded test

Status: local implementation tested; real-engine recovery test NOT RUN.
The previous normal two-share test passed and its approval is consumed.

## Change and evidence

`human_root_recovery.py` is a separate human-only recovery utility, not a
permission or tool for Aster. Its default prints only a fingerprint. Execution
requires an exact approved fingerprint, root and a private interactive terminal.
It uses the established two-share ceremony to obtain a fresh dedicated root,
lists accessor metadata privately, and accepts one explicit `REVOKE <accessor>`
selection. It never selects a target using age, name or list order.

Candidates must have the exact generated-root shape; the recovery session itself
is excluded. Selection is checked against the displayed inventory and unchanged
metadata before one revoke request. Absence from a subsequent authenticated
inventory confirms removal. The fresh recovery root is revoked on handled exits,
including cancellation and invalid selection. A timeout is not retried. A crash
can still interrupt cleanup: this is an operator recovery mechanism, not an
impossible guarantee of cleanup after arbitrary process or machine failure.

226 local tests pass. Seven new tests cover exact selection, self/unknown/fuzzy
selection rejection, changed metadata, unexpected token-bearing responses,
lost revoke responses, candidate filtering and keyboard interruption. No real
token/accessor inventory was inspected. Read-only preflight found staging absent
and the proposed unit not loaded, inactive, PID zero.

## Concrete approval scope

Approve one grouped recovery rehearsal on existing LXC 117:

1. Recheck healthy production vault and absent staging/unit.
2. Stage exactly the 11 manifest files under
   `/opt/aster-root-recovery-isolated-20261008`, root-owned directories 0755 and
   source files 0644, without overwriting. Verify archive and all member hashes.
3. Install only the reviewed runtime unit at
   `/run/systemd/system/aster-root-recovery-isolated.service`, reload unit metadata
   and start once, never enable it.
4. In a disposable in-memory vault, deliberately discard a completed final-share
   response. Verify that a root really exists despite the client failure. Test
   rejection of an invalid selection, then exact-target recovery and preservation
   of an unrelated fixture root. Verify both fresh recovery tokens revoked; finish
   the normal bootstrap and its existing revocation checks.
5. Capture allowlisted results, stop only the fixture if necessary, remove only
   the enumerated source files/directories and runtime unit, reload unit metadata,
   verify absence/PID zero and recheck production readiness. Unknown files stop
   deletion. A failed test is recorded and is not automatically retried.

Archive: `/private/tmp/aster-root-recovery-isolated-20261008.tar`

SHA-256: `ee9891d19faf02f2bbb03c38c2bc8687bf4de385326e986adf9d5462310d0168`

Manifest: `isolated_root_recovery_rehearsal.SOURCES`, 11 files.
Unit limits: private network and temporary directory namespaces; dynamic
unprivileged user; production vault/config/custody paths inaccessible; no
capabilities; no core dumps; 512 MiB RAM; no swap; 50% CPU; 128 tasks; 120-second
runtime limit; control-group termination. Existing OpenBao binary only.

No production tokens, shares, API calls, identity/policy changes, restarts, model
calls, Keychain access, delegation activation or Git push. Approval is needed
under AGENTS.md because temporary files and a service are created remotely.

## Recovery ownership and production runbook constraints

Accessor metadata is not proof of ownership. The fixture has a supervisor that
records its inventory before the injected fault and can prove which accessor is
new. That fixture oracle is explicitly NOT a production heuristic.

For production, retain an exact accessor as soon as a received root can be
identified privately. If the final response is lost before such evidence exists,
stop setup and establish the target through a separately authorized private
administrative review. Review the maintenance window, concurrent root ceremonies,
known standing administrator tokens and audit evidence. If attribution remains
uncertain, do not delete a plausible candidate. Jason must not be asked to guess
which identifier is safe to revoke. An approved administrative decision to retire
an identified token is distinct from claiming it belongs to the failed ceremony.

The private utility must not run in an agent-captured terminal. It does not expose
token IDs to its candidate display, persist root tokens, or change standing
human-ceremony policy. Accessors are administrative identifiers and should remain
in the private recovery record. No real run is authorized by this fixture gate.

After a pass, finish the real provisioning package, including an incident-specific
private recovery record and explicit handling of uncertain attribution. Do not
repeat passed primitives or add unrelated platform features.

## Primary-source basis

Reviewed on 2026-10-08:

- [OpenBao 2.6.4 token store](https://github.com/openbao/openbao/blob/v2.6.4/vault/token_store.go): generated-root metadata, accessor lookup suppresses token ID; exact-token accessor operations.
- [OpenBao 2.6.4 root generation](https://github.com/openbao/openbao/blob/v2.6.4/vault/generate_root.go): completion creates the root and removes the active ceremony state; cancelling the ceremony is not root revocation.
- [Token method](https://openbao.org/docs/auth/token/): standard token lifecycle API. Current documentation is 2.7.x; version-specific code and the proposed installed-engine test govern compatibility.

UNKNOWN until approved test: actual 2.6.4 lost-response recovery integration.
UNKNOWN: production root inventory and incident ownership. Neither was accessed.
