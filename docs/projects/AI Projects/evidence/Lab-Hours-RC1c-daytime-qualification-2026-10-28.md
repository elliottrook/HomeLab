# Lab Hours RC1c daytime qualification — 2026-10-28

Result: **PASS — unchanged full transaction completed twice**

Lab Hours is now independent of the F2–F5 backup-evidence chain. The October
27 candidate was extended to isolate the ongoing EPUB narration timer/worker.
Two failed attempts produced useful evidence and restored production: RC1 tried
to runtime-mask a static oneshot; RC1b stopped it but rejected systemd's
expected interrupted `failed` state after its process exited.

RC1c masks the EPUB timer, stops the worker, and proves `MainPID=0` plus
zero/unset tasks. Restoration starts the timer and restarts the worker without
blocking recovery; final validation rejects a failed worker.

| Pass | Declared start | Complete | Result |
|---|---|---|---|
| `lh-rc1c-p1-20261028` | 09:06:08 PDT | 09:08:09 PDT | `pilot-complete`, three requests, exit 0 |
| `lh-rc1c-p2-20261028` | 09:09:36 PDT | 09:11:37 PDT | `pilot-complete`, three requests, exit 0 |

Each pass armed a guardian, isolated Aster Agent, accepted llama/SYCL, Speech,
News, EPUB timer and worker, ran the fixed lab workload, removed the lab
process/listener, restored exact production and resumed EPUB.

Final checks: lease ready; no state/lock/operation lock/guardian/listener/lab
process; production authentication passed; Aster Agent, llama, Speech and News
active; News enabled; EPUB timer active/enabled and worker resumed.

Static evidence: 80 local tests, 73 installed Proxmox tests and 75 staged
exact-runner tests passed. The date-specific unit pair passed target
`systemd-analyze verify`. Root-owned failed/successful evidence and rollback
checkpoints remain on Proxmox.

The October 29 runner is independent of F2/F3/F4/F5 outcomes. It requires only
direct current-cycle Proxmox backup proof and a quiet host, runs once at 04:05
PDT, records a content-free first failure phase/class, and never retries.
