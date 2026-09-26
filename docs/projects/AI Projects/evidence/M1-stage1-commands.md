# Stage 1 exact operator commands — NOT EXECUTED

These commands are a reviewable production change, not standing authorization.
Use only after Jason approves this exact Stage 1 deployment and AI-PAM confirms
an immediately current quiescent window. Do not use while its remote test/rollback
workflow is active. Do not approve, consume, deny or revoke that workflow's
requests here. No Git push is included.

## Release identity

- Local archive: `/private/tmp/aster-m1-stage1-20260925.tar.gz`
- Archive SHA-256: `13bc0fe0d9ef2b3cc75e0746d818e8c5f0190042204166cb91ce6848b5a14a2b`
- Manifest SHA-256: `abd8a018435d37894d9777c75ae09f2dc53d6d44e656bddeaee8a8dff09b075d`
- Target: LXC104 via Proxmox `192.168.50.10`.
- Install only `/opt/homelab-broker/broker_core.py` and `broker_service.py`.
- Restart only `homelab-broker.service` and `homelab-broker-approval.service`.
- Preserve the existing M6 read/write gateways, units, credentials, grants,
  Authentik configuration and Companion source.

The archive contains only the manifest, two candidate sources, the three Stage 1
regression modules, the retained-approval verifier, the preflight module/test and
`apply-m1-stage1.sh`. Verify the hashes on every transfer hop. If the local archive
is regenerated, record its new archive digest before requesting deployment;
never silently substitute another bundle under this approval.

## 1. Transfer and verify (after approval)

On the Mac, verify the local archive and ensure the remote destination is absent:

```sh
shasum -a 256 /private/tmp/aster-m1-stage1-20260925.tar.gz
ssh -o BatchMode=yes root@192.168.50.10 'test ! -e /root/aster-m1-stage1-20260925.tar.gz'
scp -o BatchMode=yes /private/tmp/aster-m1-stage1-20260925.tar.gz root@192.168.50.10:/root/aster-m1-stage1-20260925.tar.gz
ssh -o BatchMode=yes root@192.168.50.10 'sha256sum /root/aster-m1-stage1-20260925.tar.gz'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- test ! -e /var/tmp/aster-m1-stage1-20260925.tar.gz'
ssh -o BatchMode=yes root@192.168.50.10 'pct push 104 /root/aster-m1-stage1-20260925.tar.gz /var/tmp/aster-m1-stage1-20260925.tar.gz --user root --group root --perms 0600'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- sha256sum /var/tmp/aster-m1-stage1-20260925.tar.gz'
```

Compare each returned digest to the exact approved digest before continuing.
Abort on an existing destination; do not delete or overwrite it blindly.

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- mkdir -m 0700 /var/tmp/aster-m1-stage1-20260925'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- tar -xzf /var/tmp/aster-m1-stage1-20260925.tar.gz -C /var/tmp/aster-m1-stage1-20260925'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- sha256sum /var/tmp/aster-m1-stage1-20260925/manifest.json'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- python3 /var/tmp/aster-m1-stage1-20260925/stage1_preflight.py --release /var/tmp/aster-m1-stage1-20260925'
```

The preflight opens SQLite read-only and does not instantiate `BrokerStore`.
Expired pending/approved rows are counted but left unchanged. Any **unexpired**
authorization blocks rollout. This does not by itself prove no external action
is in flight; owner coordination and the script's immediate socket check are
also required.

## 2. Apply the approved change

Read [the installer](../../../../ops/credential-broker/setup/apply-m1-stage1.sh)
and confirm its hash matches the manifest. It checks connected broker sockets,
then stops the two entrypoints, captures a protected SQLite/source checkpoint,
verifies a second isolated restore, runs 45 staged tests plus legacy approval
compatibility, installs two sources and migrates as `hlabroker`. Terminal counts
must be preserved. No stale request is approved or backfilled. It then starts
both services and asserts a registered-peer health response.

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- sh /var/tmp/aster-m1-stage1-20260925/apply-m1-stage1.sh --approved-stage1-window'
```

The flag documents the operator's decision; it is not permission to skip the
approval gate. The command is not authorized by the existence of this document.
Expected interruption is brief (target under two minutes, not a measured SLO).
If a post-maintenance step fails, the failure trap leaves both broker entrypoints
stopped. Aster chat and household functions are not restarted, but AI-PAM calls
may remain unavailable until corrected. The operator must accept that tradeoff.

## 3. Verify, then observe

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- systemctl show homelab-broker homelab-broker-approval forgejo-mcp-gateway forgejo-mcp-write-gateway --property=Id,ActiveState,SubState,MainPID,NRestarts'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- sha256sum /opt/homelab-broker/broker_core.py /opt/homelab-broker/broker_service.py /opt/homelab-broker/broker_approval_service.py'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- stat -c "%a %U %G %n" /run/homelab-broker/mcp.sock /run/homelab-broker/approval.sock /var/lib/homelab-broker/broker.db'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- runuser -u hlabagent -- /usr/local/bin/homelab-broker-client "{\"method\":\"capabilities.list\"}"'
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- curl --silent --output /dev/null --write-out "%{http_code}\n" http://192.168.70.10:9120/v1/companion/approvals'
```

Require candidate core/transport hashes, unchanged approval hash, both services
active, expected socket owners/mode0660, DB owner `hlabroker`/mode0600, a successful
catalogue response, and unauthenticated HTTP401. Use a denied-peer socket check
with the existing `hlabagent` identity only if its separate approval connection
is rejected; do not submit a real approval payload. Retain only boolean/status
results. Do not run a write or create a new approval request as a smoke test.

Observe service states/restart counters/health for ten minutes in bounded polls,
with a user update at least each minute. Abort on a new restart, database lock
failure, denial regression or collateral gateway/Companion failure. Preserve
counts and sanitized evidence, never unfiltered credentials or request content.
Ten minutes is an initial operational observation, not full M1 graduation.

## 4. Recovery

At any failed post-install verification:

```sh
ssh -o BatchMode=yes root@192.168.50.10 'pct exec 104 -- systemctl stop homelab-broker-approval.service homelab-broker.service'
```

Retain the failed files/DB and the installer-reported checkpoint under
`/var/lib/homelab-broker/rollback/m1-stage1-<UTC timestamp>/`. Human SSH remains the
recovery route. Do not blindly restore the backup DB (it can predate a consumed
authorization) or start old vulnerable code with active grants. Prepare a corrected
restrictive bundle, or separately review restoring source while leaving both
broker services stopped. Do not remove backups or change target-side state.

If validation failed before any source replacement, confirm original hashes and
no uncertain target outcome before considering restart of the unchanged services;
that recovery decision must be recorded. No automatic unsafe restart is scripted.
