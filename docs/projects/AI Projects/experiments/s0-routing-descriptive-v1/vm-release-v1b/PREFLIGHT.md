# V1b/V2b release preflight

Observed: 2026-09-26T16:41:51-07:00
Status: **preflight passed; execution scripts prepared; no mutation authorized**

## Verified current state

- Proxmox is a healthy standalone node, not a Corosync cluster. PVE is 9.2.20 on
  kernel 7.0.14-19-pve; load was 0.61/0.76/0.94.
- Memory available was 48,981,213,184 bytes, above the 8-GiB gate. Swap use was
  3,227,648 bytes of 8,589,930,496.
- `local-lvm` was active with 664,145,554 KiB available; `local` was active with
  68,233,444 KiB available.
- The 25 most recent task records all had `endtime` and `status=OK`. An attempted
  `statusfilter=running` query was rejected by the API as unsupported and is not
  counted as evidence. A current VNC proxy for VM102 is visible in the active task
  ledger; no backup or migration task was observed.
- Current next ID is 119. VM119 configuration, name and release paths are absent.
- VM118 remains stopped. VMs 102/103 are running and VM105 is stopped. LXCs
  100/101/104/106-117 retain their recorded running states.
- The pinned image is 433,651,712 bytes and revalidated to SHA-512
  `a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c`.
- `SHA512SUMS` remains SHA-256
  `6e1f384b152ce4bc7c5f287b5559f18786de3036915e6e6c42b3fcb8dfd8709a`.
- The v1 seed source manifest is SHA-256
  `c5e4eb98bc7847e97969b9a853b3da4cf801bcbb5748e53ac2f9c9b6f82831bf`.

## Exact proposed mutation

V1b copies only the reviewed v1 seed source and release scripts to the existing S0
staging root, creates `aster-s0-bootstrap-canary-002.iso`, and creates stopped
VM119 `aster-s0-fixture-v1` with one vCPU, 1 GiB fixed RAM, an 8-GiB imported disk,
OVMF/q35, serial socket and no vNIC, agent, credentials, passthrough, shared
filesystem or automatic start. The stopped configuration must pass
`s0_vm_release.py` before V2b.

V2b performs one boot with a 300-second/4-MiB serial capture. It sends no serial
input. It issues one host stop only if the VM is still running after capture. It
never retries. Local parsing must accept exactly the new run/manifest identity
before success can be claimed.

## Failure and rollback

Any preflight or stopped-state mismatch stops before boot. Partial resources are
retained stopped for review; neither script destroys a VM, disk, ISO or evidence.
After boot, VM119 is forced stopped at the deadline and retained. VM118 and all
existing service guests are excluded from mutation. V3 and accepted-corpus access
remain prohibited.
