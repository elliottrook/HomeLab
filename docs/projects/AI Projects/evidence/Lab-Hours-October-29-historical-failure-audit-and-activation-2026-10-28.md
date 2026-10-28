# Lab Hours October 29 historical failure audit and activation — 2026-10-28

Decision: **TIMED TEST: GO — SCHEDULED / CONDITIONAL** for 04:05 PDT on
October 29.

Jason approved the test and directed Stream A to examine and mitigate every
daily failure before activation. Lab Hours RC1c remains independent of the
F2–F5 evidence chain. The audit nevertheless used every October 19–28 failure
to harden the host-owned wrapper.

| Prior cycle | Observed failure | October 29 mitigation |
|---|---|---|
| Oct 19 | Automation resumed after the invocation deadline. | Root-owned date-specific systemd timer; installed calendar independently verified; runner rejects starts outside 04:00–04:15 PDT. |
| Oct 20 | Preparation detail was overwritten and service output was suppressed. | Terminal evidence preserves first phase, exception class and a bounded specific failure code. |
| Oct 21 | Preflight required a future mirror and component windows disagreed. | Lab Hours reads no F2/F3/mirror artifact; its owner directly proves the completed current-cycle Proxmox job and fixed archives. One exact start window governs the wrapper. |
| Oct 22/24 | Final-guard failures collapsed to an unactionable generic class. | Pin, unit and process failures identify the exact bounded file/unit/marker. Owner and postcheck phases remain distinct. |
| Oct 23 | Reviewed packet never received activation before the window. | Jason explicitly approved this packet; installed timer is enabled, active and waiting with an independently read next-elapse value. |
| Oct 25 | Installed host-exclusion pin drifted. | All nine installed RC1c dependencies are rehashed before any effect; staged and installed packet hashes are frozen. |
| Oct 26 | Coordinator used an incompatible subprocess API hidden by a fake test. | The night wrapper uses the same real `subprocess.run` boundary as systemd; target-Proxmox tests ran against staged bytes. |
| Oct 27 | Coordinator discarded a bounded child projection before parsing it; sanitized PATH omitted `/usr/sbin`. | Lab Hours does not call the F2 observer. Its fixed commands are absolute; owner output is parsed before success is accepted. |
| Oct 28 | F2 and F3 passed, but F4/F5 had no scheduled owner and missed freshness/cutoff. | Lab Hours has its own installed one-shot owner at 04:05 and does not depend on F4/F5. An active F2–F5 or workload-transition service blocks effects rather than causing partial progression. |
| Oct 28 daytime RC1/RC1b | EPUB static-worker masking and interrupted-oneshot state were modelled incorrectly. | Unchanged RC1c explicitly stops the worker, proves zero PID/tasks, restores its timer and worker, and passed the full transaction twice. |

The wrapper was additionally corrected so disappearance of the durable drain
state is never treated as proof of recovery. After any owner failure and
guardian recovery it runs the complete production validator. It records
`production_restored=true` only if accepted model/binary/unit hashes,
authentication, Aster Agent, llama/SYCL, Speech, News, EPUB, lease and backup
proof all pass. There is no automatic retry.

Platform source commit `ccf6542c1df9762344d43003dcfcc303cfb6f6d3` passed 85
focused local tests. The revised runner also passed its four target-Proxmox
tests, Python compilation and clean `systemd-analyze verify` before install.

Installed hashes:

- runner: `848982b31c7a972bb67e5b4e7c16cc41c3e42c65f79495e3043ba1ffbfd32283`;
- service: `53b2a74b23a5bfea3619cf23dd6336a569d4c5ef2cb462b3f3dbd790a3a198cf`;
- timer: `0bc8fc03699ce431cf6f9a013f0639c4681b16ba20f28b7fccfc60c7ec670cb7`.

The timer reports enabled, active and waiting for October 29 04:05 PDT. The
attempt directory and all shared state/lock paths were absent; the lease was
exactly ready; Aster Agent, accepted llama/SYCL, Speech, News, EPUB,
`pvescheduler` and `pvestatd` were healthy. The scheduled diagnostic and
workload-transition services were inactive at activation. Their timers end
with workload resume at 03:50; any overrun or unexpected competing process at
04:05 makes Lab Hours fail closed before effects.

The remaining fresh runtime gates are the completed October 29 Proxmox backup
and fixed archive proof, unchanged installed hashes, a ready lease with no
state/lock, no competing exact-cycle/backup/evidence process, and a start by
04:15. The run interrupts Aster, llama, Speech, News and EPUB for the fixed
transaction and restores them. It changes no model, backend, credential, GPU
binding or backup schedule and performs no reboot.
