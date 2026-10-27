# Full-inference daytime two-pass qualification — 2026-10-27

Result: **PASS — two complete drain/workload/restore transactions**

Jason authorized a disruptive daytime qualification using the completed current-cycle
backup rather than waiting for another overnight attempt. The qualification used the
existing full-inference pilot boundary and did not write an F2/F3 receipt or claim a
new backup. The October 27 00:30 Proxmox job and fresh 104/110/116 archives were the
fixed source evidence for both passes.

## Defects found and corrected

Repeated live attempts failed closed and exposed production-only mismatches before
the two accepted passes:

1. The manual lease helper now emits `{"state":"ready"}` while the pilot expected
   the former scalar `ready`. Source and final validation now accept only those two
   exact encodings.
2. The controller passed `/var/lib` to the host-exclusion primitive instead of the
   root-owned mode-0700 `/var/lib/local-ai-lab` directory. Acquire and resume now use
   the exact state root.
3. LXC systemd reports the persistent unit as enabled while a valid runtime mask is
   present. Controller, supervisor and guest workload now verify the exact
   `/run/systemd/system/<unit> -> /dev/null` boundary plus inactive state.
4. Re-entered recovery could reject a previously observed restore step after state
   changed. Safe fixed restore commands are now replayed when their current
   observation no longer matches.
5. The guest smoke launch omitted the pinned model alias that its readiness probe
   required. The launch now supplies `--alias aster-qwen3.5-9b`.
6. Host cancellation could leave the guest smoke scope running. Error recovery now
   stops the exact derived guest scope and proves listener/process/GPU absence before
   restoring production.
7. A collected owner scope returned `LoadState=not-found`, which the independent
   guardian did not recognize as fenced. The guardian now accepts that exact state.
8. The cold-load smoke bound increased from five to ten minutes, still inside the
   fixed 30-minute lab window and 15-minute restoration reserve.

The target passed 71 host tests and 5 LXC110 wrapper tests after the final correction.
The installed hashes match source:

| Installed artifact | SHA-256 |
|---|---|
| `cooperative_lab_host_adapter.py` | `068ea9b85e31116ec13f4f27b8b1207d46e3569aa35c95440c644cce969f515f` |
| `full_inference_lab_deadline_guardian.py` | `b7cbc3992868400b95e90cd783b26511e1c4f2a2f2b587b6f111c0a58dd4b96f` |
| `full_inference_lab_runtime.py` | `c4f131baec043511e525bb3babfa9a0b11236d4de1f399b2152c43f288cc79b9` |
| `full_inference_lab_session.py` | `02fe37d6ee0d6a88133b2998dcf1badeaa086fb6f0f36114a3c2fe3321857b40` |
| `full_inference_lab_sources.py` | `91daf38fa757f301524fb929ab2581abb0895d776d144fbb9da995ca09435266` |
| `full_inference_lab_supervisor.py` | `da5ac76fb48541a2661caa1cb4fe7f21d84334abb9ab935fb1aaaf72c4faba55` |
| `full_inference_lab_validator.py` | `18a09b74f276a4fa5cadd7270efa9922f14a026e77e00debe7a8b7ade8ed56a1` |
| `full_inference_lab_workload.py` | `b0ad8a6422d4290cd73568916de4e35ef05130e5b93aee22c629ce7560beb236` |
| LXC110 `aster-llama-lab-smoke` | `fec8b0a07a3d13a35a04eea80e460e4422de288ef69f9a2b18a00f3ebb228870` |

## Accepted passes

| Pass | Effect start | Complete | Result |
|---|---|---|---|
| 1 | 2026-10-27 08:47:31 PDT | 08:49:20 PDT | `pilot-complete`, three requests, exit 0 |
| 2 | 2026-10-27 08:50:39 PDT | 08:52:28 PDT | `pilot-complete`, three requests, exit 0 |

Each pass independently:

- armed a separate host-owned recovery guardian;
- held the shared host exclusion and durable drain lock;
- runtime-masked and stopped Aster Agent, Speech, accepted llama.cpp/SYCL and
  the two News timers;
- proved no unlisted render-node holder before the fixed loopback workload;
- started the accepted Qwen3.5-9B Q4_K_M model with the pinned b11429 SYCL
  binary on port 11436 and performed exactly three authenticated, tool-free requests;
- stopped and removed the derived lab scope and proved no listener or process remained;
- unmasked and restarted the accepted production stack;
- verified exact model, binary and unit hashes, authentication, sole GPU-holder
  identity, service/timer state and current-cycle backup source; and
- removed state and lock and stopped the guardian.

## Final state

The final independent postcheck found no drain state/lock, lab listener, lab process
or running guardian. Aster Agent, accepted `aster-llama.service`, Speech and both News
timers are active; both News timers are enabled. Production authentication succeeds.
The only render-node holder is the accepted b11429 llama server in LXC110's
`aster-llama.service` cgroup. Model, binary and unit hashes remain respectively
`cd76ec20…2a13`, `0404f751…e6c5` and `a4c75169…4cb3`.

The separately scheduled October 28 F2 prepare/final timers remain active and enabled
for 01:15/01:20 PDT. This qualification proves the daytime lab-hours transaction and
exact production restoration twice. It does not convert its current-cycle backup
observation into F2/F3 evidence and does not authorize a model change.
