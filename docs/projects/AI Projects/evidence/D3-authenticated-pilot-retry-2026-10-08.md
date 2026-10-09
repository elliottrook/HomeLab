# D3 — correct the pilot state-directory sandbox boundary

Status: APPROVED RETRY STOPPED AT CREDENTIAL CHECK; ROLLBACK VERIFIED.
Approval consumed. Original attempt and successful rollback are in
the [first pilot gate](D3-authenticated-pilot-gate-2026-10-08.md).

## Executed retry result

Jason approved. Revalidated retained files/state, exact worker fingerprint,
healthy original 35 paths, inactive identity, zero grants and password lifetime.
Installed the corrected drop-in, verified exactly the two intended write paths
with `ProtectSystem=strict` retained, and restarted once. Startup succeeded with
zero automatic restarts: health/Companion/pilot page 200, original 35 paths
preserved, 43 API paths total, private ledger and runtime credential metadata
verified. The state-directory correction is therefore supported by live evidence.

Activated only the exact worker user and ran the approved credential-path check
once. It failed with the intentionally generic `Credential path unconfirmed`.
No job was admitted and no connected worker/model process was started. Immediately
disabled the user and marked matching user/provider grants revoked; zero grants
existed. Removed only the corrected-hash pilot drop-in and performed the approved
rollback restart. Independently verified normal Aster health/Companion 200,
delegation 404, runtime credential absent and a read-only database count of zero
jobs. Retain the empty private ledger; do not delete it or recreate state.

Read-only diagnosis: the exact broker status check as Aster returns true; Mac
AuthentiK discovery returns 200; fixed-item Keychain metadata lookup succeeds in
both normal and worker environments without requesting the password. Sanitized
AuthentiK HTTP metadata shows one introspection request, HTTP 200, and no token
endpoint request in the inspected window. This suggests a failure before token
issuance but does not establish which local operation failed. The generic helper
error does not retain sufficient stage evidence. Do not guess, extend timeouts,
renew credentials or repeat live restarts to find out.

Next: [fixed-item private diagnostic](D3-keychain-read-diagnostic-2026-10-08.md).
The prospective retry scope below is retained as historical authorization only.

## Exact change and impact

The first startup failed before identity activation or job admission because the
service sandbox made the ledger path read-only. Correct only the pilot drop-in by
adding `ReadWritePaths=/var/lib/aster/delegation`. Keep `ProtectSystem=strict`,
`ProtectHome=yes`, existing read-only paths and existing notification write access.
Do not reset the write-path list or allow writes to the parent directory.
The new directory remains Aster-owned 0700 and is dedicated to pilot metadata.

Candidate source:
`services/aster-agent/delegation/deploy/aster-delegation-pilot.conf`.
Frozen local copy: `/private/tmp/aster-delegation-pilot-retry-20261008.conf`.
SHA-256: `3dc2e807b5bf5e509ed54e02c04d2641260e82059a01fd415c28775f6c9368b5`.
Local byte comparison verifies that removing this single added line reproduces
the original approved drop-in hash. No Python source changed, so the 237-test
result and worker manifest remain applicable; this is not a claim that the
corrected live sandbox has already passed. Do not repeat offline model tests.

## One bounded retry approval

1. Recheck restored service/35 paths, unchanged main source and all retained pilot
   module hashes from the first gate, public CA, private directory/specification,
   inactive exact identity, zero grants and credential expiry. State must still
   contain only `pilot-spec.json`; no admission or execution may have occurred.
   Recheck exact worker fingerprint. Stop on drift or expired credentials.
2. Create only absent
   `/etc/systemd/system/aster-agent.service.d/aster-delegation-pilot.conf` from
   this corrected candidate, root 0644. Retain the existing pilot checkpoint;
   do not overwrite/recreate it, recopy modules, recreate credentials or snapshots.
3. Validate unit, reload systemd and confirm the effective write-path list is
   exactly the existing notifications directory plus this private delegation
   directory, with `ProtectSystem=strict` retained. Restart Aster once; brief
   Companion interruption expected. Within 60 seconds require original routes
   preserved, health/Companion/pilot page 200 and correctly owned private ledger.
   On startup error, roll back immediately rather than waiting through retries.
4. Continue steps 5–10 of the original gate unchanged: exact worker activation,
   private credential-path check, one fixed Orion admission, one subscription
   turn, disable worker, revoke only its provider grants, verify cleanup and
   Jason-visible answer. Original job ID is usable only because independently
   verified state proves it was never admitted; this is not a replay exception.
5. On any failure, disable the worker/revoke matching grants if activated; remove
   only this corrected-hash pilot drop-in, reload and restart Aster once to
   restore the verified disabled configuration. Preserve any ledger, checkpoint
   and evidence; no automatic resubmission. Stop if rollback cannot be verified.

Original worker checksum remains
`24f7afcfd9011267ab8b7521bec170d1f0b5f021984bb96b51591be6f4220888`;
admission checksum remains
`2eddc20ea62d2db9bb7de313a55ce1814bc2a59971b8bbaea227bd29764b0781`.
One fictional turn, configured gpt-5.6-luna/medium reasoning, no tools, no personal
data, no paid fallback, no auto-retry and no Git push. The original scope and
remaining acceptance limits apply. Password expires October 9 at 19:02 Vancouver;
AppRole also has its original 24-hour lifetime. Renewal is not included.

This additional write exception and new deployment attempt require approval under
`AGENTS.md`'s immediate remote-write rule; the previous approval and its rollback
have been consumed. No new credentials or recovery ceremony are requested.
