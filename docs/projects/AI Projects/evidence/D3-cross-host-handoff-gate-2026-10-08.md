# D3 complete owned-pipe handoff rehearsal

## Local implementation and evidence

The isolated OpenBao v5 test is complete; do not repeat it. This next experiment
addresses a different unresolved boundary: composing identity, vault, gateway and
Mac custody through the real controller's private pipes, stage acknowledgements,
disconnect handling and durable metadata journal.

Added `fixture_provision_peer.py`. It invokes the actual node protocol and vault
provisioner after replacing ALL external effects with fictional callbacks. Identity
creation is synthetic (no Authentik ORM), vault TLS/API/custody are mocked before
node invocation, gateway custody is a fake sink, and the Mac sink is memory-only.
Fictional strings are fixed and recognizable. Local temporary fixture admin files
are context-managed; only a fixed non-secret revocation receipt is retained.
No production admin file, secret, identity or Keychain item is opened.

Added local subprocess tests for successful complete handoff, gateway disconnect
and Mac sink failure. They use actual OS pipes and separate Python processes;
the compiler and external storage effects alone are replaced. Each verifies
process termination, precise success/failure journal boundary, revocation receipt
and absence of fictional secrets from the journal. A further test drives all
three cases through the new cross-host harness with local subprocess transports.
211 full local delegation tests pass. This is not yet SSH/container integration.

`cross_host_provision_rehearsal.py` defaults to public metadata. Explicit execution
requires the exact fingerprint and a fresh private local state directory. It runs
exactly three cases, verifies each reached its intended boundary, requires a
source-local fictional revocation receipt and stops on unexpected outcomes.
There is no retry. The CLI has a 600-second overall alarm; pipe reads/writes and
peer cleanup remain bounded. Alarm interruption unwinds owned-peer cleanup.

## Concrete approval scope

Approve ONE grouped rehearsal of these three cases across existing LXC 104,
LXC 117 and the existing `authentik-server-1` container inside LXC 106:

1. Recheck production readiness, manifest hashes and absent staging paths.
2. Create only `/opt/aster-provision-pipes-20261008` in each of the three target
   execution environments, root-owned mode 0700; copy the 14 reviewed files with
   mode 0600. No overwrite. Verify archive plus every manifest source hash.
3. Run the reviewed local harness once with all three cases: success, intentional
   gateway disconnect, intentional Mac sink failure. Each real SSH connection
   executes only `fixture_provision_peer`, with source hashes checked before import.
   Authentik uses `docker exec -u 0 ... python` for file access, NOT `ak shell` or
   any production ORM call. Bytecode writes disabled.
4. Verify expected controller/journal result and `fictional-admin-revoked` receipt
   on 117 for every case. Failure cases must stop at their exact intended boundary;
   an unrelated failure must not be counted as a successful negative test.
5. Remove only the 14 enumerated files and directories from each target and the
   three fixed `.receipt` files on 117. Check inventory before deletion and stop
   if unknown files exist. Verify staging absent and all peers gone; recheck vault
   and AI-PAM readiness. Retain only non-secret local journals/evidence.

No systemd units, dependencies, service restarts, model calls, real accounts,
actual vault API operations, encrypted-credential writes, Mac Keychain accesses,
permissions changes, real root ceremony, delegation activation or Git push.

Archive: `/private/tmp/aster-provision-pipes-20261008.tar` (71,680 bytes, 14 files).
Archive SHA-256:
`c7982e74de4a2f6b7d0f58cabfd9561c53b1b7dc7951c32db7f2e098d1f8841f`.
Harness fingerprint:
`f2f08208a5efd3e09bfae150b44ac3c6ac978bce86f36d076d3e7e5d54e11de1`.
Fresh local journal directory proposed:
`/private/tmp/aster-provision-pipe-results-20261008`.
Read-only preflight confirms all three remote staging paths absent.

Example execution AFTER approval and verified staging:

```sh
python3 services/aster-agent/delegation/cross_host_provision_rehearsal.py --run \
  --approved-sha256 f2f08208a5efd3e09bfae150b44ac3c6ac978bce86f36d076d3e7e5d54e11de1 \
  --directory /private/tmp/aster-provision-pipe-results-20261008
```

Risk: temporary source files and a few bounded lightweight Python/SSH processes
on live guests. Rollback is stopping only owned fixture processes and removing
enumerated files. Never alter production to make a fixture pass. Approval is
required under AGENTS.md for these remote file writes and process executions.

## Remaining before real provisioning

Keep delegation disabled. This test combines protocol behavior, not actual custody
effects; earlier isolated real-vault, encrypted-storage and Keychain tests are
separate evidence. Complete the human authenticated root-ceremony instructions,
source staging/custody ownership review and crash-reconciliation runbook before
asking for real inactive-identity provisioning. In particular, root cleanup after
abrupt death remains human-operated, and existing or uncertain runs cannot be
replayed. Do not open a human ceremony merely to keep a setup token waiting.
