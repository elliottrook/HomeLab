# F2 Proxmox sbin path correction — inactive installation card

Status: **ROOT CAUSE PROVEN; SOURCE AND DAYTIME REHEARSAL PASS; HOST REPLACEMENT NOT AUTHORIZED**

## Root cause

The installed observer launches its child with the intentionally fixed
environment `PATH=/usr/bin:/bin`. The production archive resolver invokes
`pvesm` by name, but Proxmox installs it at `/usr/sbin/pvesm`. Replaying the
child under the exact sanitized environment produces `FileNotFoundError`;
running the same fixed-source chain under root's ordinary path reaches all
three archives. This explains the October 27 four-second child failure with
zero rows without relying on archive contents or speculation.

Platform source commit: `18c7198efe0b1ad34887cf5c0d690116bebf20e2`

| Installed path | Required predecessor SHA-256 | Candidate SHA-256 |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858` | `ce2332a1136b0176bd576a1c5c7f8f4a5374c45ef6d470dcbf78ffd594d4157f` |
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34` | `e072e90770c145c1a5f9cc3d589eb0d70d91230290cd70f0f82820efe5e109d0` |
| `/usr/local/libexec/local-ai-lease/f2_daytime_no_scan_rehearsal.py` | `352576c0d79064727642d13ef11f3e4d9e61936bbf223275b89cc1685d56c5f7` | `20f3526735788cd25326c014ab855be1610be46164565c98243f195d1e94ff32` |

The correction keeps a fixed environment and adds only the standard Proxmox
system sbin paths: `/usr/sbin:/usr/bin:/sbin:/bin`. The wrapper's observer pin
is updated to the corrected candidate. Regression tests assert the exact child
environment and use a real `Popen.communicate()` process. Sixty focused F2
tests pass locally. The corrected staged rehearsal passed twice on Proxmox
against identical current-cycle identities for VMIDs 104, 110 and 116 with
`archive_scan=not-attempted` and `receipt_written=false`.

## Bounded inactive installation

After separate approval, the platform owner may:

1. require the three exact predecessor hashes and root-owned one-link mode
   `0644` custody;
2. preserve all three predecessors in a new root-only rollback directory;
3. replace only the three listed files, atomically, with exact root-owned
   one-link mode `0644` candidates;
4. run the 60-test target-Linux packet;
5. run the installed no-scan rehearsal twice and require identical complete
   three-archive projections; and
6. verify no `zstd`/F2 child, lease, lock or receipt, all F2 timers
   disabled/inactive, and healthy production services and guests.

Any hash, custody, test, rehearsal or postcheck mismatch restores all three
predecessors and stops. This card does not authorize an archive scan, receipt,
lease, service stop, restart, model call, timer activation, schedule change or
Git push. A fresh exact-cycle card and separate activation decision remain
required after successful installation.
