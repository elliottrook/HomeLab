# Aster approval availability repair candidate

Prepared 2026-09-27. Not deployed or authorized. Incident record:
[Doctor, Aster and drift](../../../../docs/runbooks/Lab-Health-Review-2026-09-27.md).

## Exact bounded change proposed

LXC 104 only. Install the existing tested repository
`ops/credential-broker/broker_approval_service.py` as
`/opt/homelab-broker/broker_approval_service.py`, root:root 0644. Do not replace
broker core, transport, gateways or Aster source. Install the two files here as
`/etc/systemd/system/aster-agent.service.d/broker-approver.conf` and
`/etc/systemd/system/homelab-broker-approval.service.d/broker-approver.conf`.

Create root:root 0600 `/etc/aster/broker-approver.env` source-locally with:

```
ASTER_BROKER_APPROVER_SUBJECT_HASHES=<verified existing Jason lab owner hash>
ASTER_BROKER_PASSKEY_ACRS=
```

Do not copy a literal placeholder, publish the hash, infer another account,
change Authentik claims, or map generic MFA/default ACR to passkey assurance.
The existing lab owner matched five consumed approvals and two denials in the
production database. Reverify this equality, the explicit owner-only Companion
application binding and current issuer/subject derivation before installing.

Reload systemd and restart only approval and Aster services. Expected interruption:
brief Aster chat/approval interruption; no guest reboot or network change. This
restores owner-only inbox, management snapshot/history, Yellow approve/deny.
**Red approvals and management mutations remain denied** until the separately
reviewed M1 Stage2 passkey assurance gate passes. This is an explicitly degraded
interim mode, not Stage2 graduation or full management recovery.

## Preflight, recovery and validation

1. Obtain explicit approval for this bounded deployment and its limited outcome.
   Recheck live source hashes against `manifest.json`, no active lab job, no
   unexpired pending/approved broker requests and no concurrent deployment.
2. Stage and verify only this source and the two drop-ins. Stop approval, capture
   protected source/unit/config metadata and an online SQLite backup under
   `/var/lib/homelab-broker/rollback/approval-availability-<UTC>/`. Verify integrity
   and a disposable restored copy. No credentials leave the host; do not export
   request payloads or change/delete database rows.
3. Install atomically, reload and restart, waiting for actual socket/HTTP readiness.
   Preserve all existing supplemental groups, restrictions and unrelated drop-ins.
4. Check configured owner equality at both services, missing/other-owner denials,
   generic ACR denial for privileged mutations, no source drift in core/gateways,
   and existing Aster/notification/lab health. Use isolated fixtures for effectful
   tests; do not approve or revoke real requests as probes.
5. Jason verifies inbox and management views on the iPhone. A real signed-session
   test is required; fabricated claims and offline tests are not end-to-end proof.
6. On failure, keep approval service stopped and restore Aster's prior configuration
   (empty allowlist) if needed for chat availability. Preserve checkpoint and failed
   artifacts. Do not restore an old database or remove entitlement checks to reopen
   access. Human SSH remains available.

Validation already completed: 10 gateway approval tests; 10 candidate approval
service tests against **copies of the current live core and transport**. This
includes empty/wrong entitlement and fresh-assurance denials. No runtime mutation
was performed for these tests. Exact signed-session assurance remains unproven.
