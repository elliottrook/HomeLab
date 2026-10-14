# Application-only B60 benchmark run card

Status: offline controller candidate. This is a separate lease mode from the
whole-host recovery drill and is not live authorization. The controller is
implemented at `scripts/local-ai/application_b60_controller.py`; its effects
remain disabled until a source-bound application receipt and the host-side
sidecar probes are installed.

## Preconditions

- The platform has produced a source-bound application-mode backup receipt;
  the full-stop receipt is not reusable.
- The application controller has passed its focused local tests and is using
  the exact allowlist below; this does not substitute for live host evidence.
- LXC110 `aster-llama.service` is active with the exact accepted b11429
  SYCL/Level-Zero binary, model and device identity.
- LXC104 `aster-agent.service` and LXC116 `aster-speech.service` are stopped
  and quiesced; News and other inference consumers are quiesced.
- The named LXC104 sidecar has a pinned source digest, distinct unprivileged
  UID, one worker, fixed non-public port, test-only credentials, no privileged
  mounts/sockets, denied unauthorized network paths, and start time within the
  application lease.
- At least 15 minutes remain before the 04:15 restoration deadline.

## Effects and evidence

1. Capture the platform checkpoint and application-mode receipt.
2. Stop/runtime-mask only LXC104 `aster-agent.service` and LXC116
   `aster-speech.service`; never stop or mask LXC110 llama.cpp for this mode.
3. Start the already-installed sidecar only after the host observer validates
   its exact identity and isolation.
4. Run one bounded 20-request batch through the sidecar. The platform receipt
   records the sidecar observation, lease identity/generation, backend identity,
   source digest and watchdog deadline.
5. Stop the sidecar before restoration reserve, unmask/start the two production
   consumers, and verify llama.cpp, device, model, auth and schedules.

## Rollback

If any sidecar, network, receipt, watchdog or timing gate fails, make zero model
calls, stop the sidecar, restore the two consumers, leave llama.cpp untouched,
retain the lease for reconciliation if any effect is uncertain, and report the
failure. This mode must never be represented as a full-stop lease.
