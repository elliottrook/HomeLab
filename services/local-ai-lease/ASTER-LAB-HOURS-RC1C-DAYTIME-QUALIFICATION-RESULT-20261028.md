# Aster Lab Hours RC1c daytime qualification — 2026-10-28

Result: **PASS — unchanged full transaction completed twice**

This is evidence for the separate Aster Lab Hours project. It does not prove
or depend on F2, F3, F4 or F5. The current-cycle Proxmox backup was used only
as a direct recovery-source prerequisite.

## Defects exposed and corrected

The October 27 candidate already completed the five-consumer transaction
twice. October 28 added the ongoing EPUB narration compiler to the isolation
boundary. Two initial attempts failed closed:

1. `lh-rc1-p1-20261028` rejected runtime masking of the static EPUB worker
   service. Production restored and the attempt retained exit 1 evidence.
2. `lh-rc1b-p1-20261028` used an explicit stop, but treated systemd's expected
   interrupted oneshot `failed` state as an active worker. Production again
   restored and the attempt retained exit 1 evidence.

RC1c masks the EPUB timer, stops the static worker, and accepts quiescence only
when its state is `inactive` or `failed`, `MainPID=0`, and `TasksCurrent` is
zero/unset. Restoration starts the timer and restarts the worker without
blocking production recovery. The final validator requires the EPUB timer
active/enabled and rejects a failed worker.

## Verification

- local Python suite: 80/80 passed, including the exact-cycle runner;
- Proxmox Python 3.13 installed suite: 73/73 passed;
- Proxmox staged runner suite: 75/75 passed;
- exact service/timer passed `systemd-analyze verify`;
- both failed attempts cleared state/lock and passed production authentication;
- rollback checkpoints retain the October 27 baseline and each intermediate
  candidate.

## Accepted passes

| Pass | Declared start | Terminal output | Result |
|---|---|---|---|
| `lh-rc1c-p1-20261028` | 09:06:08 PDT | 09:08:09 PDT | `pilot-complete`, three requests, exit 0 |
| `lh-rc1c-p2-20261028` | 09:09:36 PDT | 09:11:37 PDT | `pilot-complete`, three requests, exit 0 |

Each pass independently armed a guardian, acquired the shared exclusion,
isolated Aster Agent, accepted llama/SYCL, Speech, both News timers, the EPUB
worker timer and active worker, ran the fixed authenticated three-request lab
workload, removed the lab process/listener, restored exact production and
resumed EPUB processing.

The final postcheck found the manual lease `ready`; no state, lock, operation
lock, lab listener, lab process or guardian; Aster Agent, accepted llama,
Speech and both News timers active; News timers enabled; EPUB worker timer
active/enabled and worker activating successfully; and production
authentication passing.

## Frozen RC1c and night gate

Relevant installed hashes:

| File | SHA-256 |
|---|---|
| `cooperative_lab_host_adapter.py` | `65151e7d7cb511c79afffa0544adb86ee9820e963330c0c5ae4a214e30f92d88` |
| `full_inference_lab_install_preflight.py` | `1ea2e37eb2ab8ea34251f4af1337cd2d7f94b00933eb60ff7433b6adbe6ca8d3` |
| `full_inference_lab_session.py` | `217cd468111b5e3fea280515a9ac7b9e5b77776c5510764c8b9ca8803ddf5b02` |
| `full_inference_lab_sources.py` | `920d2ed171d314a6cb346032651c24a7972e51b2a91c2bb2892dcd9419c50d48` |
| `full_inference_lab_validator.py` | `0c4a21d7894dd2c41d89aa00d2fa5969277991ff86febf8a89a61ac299966858` |

The approval-ready October 29 runner is independent of the evidence-stage
chain, refuses drift or a competing process, runs once at 04:05 PDT, and
retains a content-free terminal record with the first failure phase and class.
It never retries. Its packet hashes are:

- runner: `c9b044275a2fec51bc13419e66b408c0e71f9ec139085ebf88ea1f756d5575e0`
- service: `baaf93a6e4f6ca307d6a0bc4de905958de41243f20abddd63a4306cce967f82e`
- timer: `0bc8fc03699ce431cf6f9a013f0639c4681b16ba20f28b7fccfc60c7ec670cb7`
