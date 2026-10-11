# M1 approval-socket lifecycle fault and candidate — 2026-10-10

**State:** live listener restored; durable unit change is a local candidate only. Stage2 remains HOLD. No new identity, approval power, credential access, policy grant or Codex tool was enabled.

## Verified observation

Read-only LXC 104 checks found `homelab-broker-approval.service` active under `hlabroker` with zero systemd restarts, but `/run/homelab-broker/approval.sock` absent. `ss -xlnp` still showed its process listening on a Unix socket named for that path. The main broker and its `mcp.sock` were active and present. The approval process had started at 12:48 PDT; the main broker restarted at 14:10 PDT. The runtime directory and `mcp.sock` dated to that later restart. The repository's two base unit files matched the live files byte-for-byte before this candidate.

**Architectural inference, supported by the sequence:** `homelab-broker.service` owns `RuntimeDirectory=homelab-broker`; by default systemd removes that directory when the unit stops. The approval service puts its socket inside the other unit's runtime directory but has only `After=`, which orders startup and does not propagate restarts. On the main broker's manual restart, the directory was recreated, removing the approval pathname while the independent approval process kept its old bound inode. This explains why `active` did not mean clients could reach it. The exact actor that requested the 14:10 restart was not established from the read-only journal.

The root cause is consistent with the official systemd definitions of [`RuntimeDirectoryPreserve=restart`](https://github.com/systemd/systemd/blob/main/man/systemd.exec.xml) and [`PartOf=`](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml). LXC 104 runs systemd 257; the candidate uses directives available in that release. This is a lifecycle dependency problem, not evidence that the policy accepted an improper approval.

Additional read-only boundary reconciliation found that Nginx Proxy Manager's active `aster.elliottrook.com` proxy host (`18.conf`) forwards its default location to Aster LXC 104 at `192.168.70.10:9120`; it has no dedicated approval location. An unauthenticated direct request to Aster's approvals endpoint returned 401. The live `broker_approvals.py` matches this branch's source hash, while live `broker_approval_service.py` differs by lacking the local-only `management.capability-revoke` handler. The candidate unit change must not be bundled with deploying that source difference or treated as Stage2 approval-ingress separation.

## Restorative action already taken

The approval service alone was restarted after confirming its pathname was absent and there was no reachable approval socket to interrupt. The path returned as a socket with mode `0660`, owner `hlabroker`, group `hlabroker-approvers`. Both broker services remained active with zero restarts. A connect-only probe as `aster` succeeded; the same probe as `hlabagent` failed with errno 13. No approval method was called, no request was consumed and no policy changed. This restored the documented listener, but a future main-broker restart could repeat the fault until the unit lifecycle is corrected.

## Local durable candidate

The tracked main-broker unit adds `RuntimeDirectoryPreserve=restart`, so a manual or automatic broker restart does not remove a directory also used by the approval listener. The tracked approval unit adds `PartOf=homelab-broker.service`, so explicit stop/restart operations propagate to the approval listener; its existing `After=` orders the restart. The base socket paths, UIDs, groups, modes, commands and broker policy remain unchanged. This is the smallest candidate for the observed failure. A separate owned runtime directory for approvals would provide cleaner component ownership but requires consumer-path and recovery changes and is not justified by this one incident without further evaluation.

Both candidate files were copied, with matching SHA-256 values, into a mode-0700 disposable directory on LXC 104. `systemd-analyze verify` under the installed systemd 257 returned success with no diagnostics. The two disposable files and directory were then removed. This validates unit syntax and dependencies, not live restart behavior. The current production unit files remain unchanged.

## Proposed deployment gate (not yet executed)

1. Recheck the two live unit hashes, both socket path permissions, service activity and that there is no in-flight approval operation. Preserve exact live unit copies outside Git on LXC 104.
2. Install only the two reviewed unit files; run `systemd-analyze verify`, reload unit definitions, and inspect effective `RuntimeDirectoryPreserve`, `PartOf`, `After`, UIDs and command lines before restart. Stop if any unplanned property changes.
3. In one bounded service window, restart the main broker. The approval service should restart automatically after it. Verify both active PIDs, both socket pathnames and permission modes, authorized/denied peer connections, and a non-consuming broker status read. Do not create or consume a production approval to test lifecycle.
4. Validate that Aster's ordinary health and Companion's read-only approval view remain available. Record interruption duration and any unexpected journal entries.
5. If either listener or the policy boundary fails, restore the exact saved units, reload and restart the two broker services in dependency order; verify their paths and permissions. Keep Stage2 on HOLD either way. Do not alter subject allowlists, passkey mapping or worker grants.

The staged candidate has not been deployed or exercised with a broker restart. It should not be described as proven until the restart and rollback gates are observed.
