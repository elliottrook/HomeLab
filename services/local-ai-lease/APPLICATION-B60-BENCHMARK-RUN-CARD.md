# Application-only B60 benchmark run card

Status: offline controller candidate. This is a separate lease mode from the
whole-host recovery drill and is not live authorization. The controller is
implemented at `scripts/local-ai/application_b60_controller.py`; its effects
remain disabled until a source-bound application receipt and the host-side
sidecar probes are installed.

The application-mode watchdog is a separate required component at
`scripts/local-ai/application_b60_watchdog.py`. The full-stop watchdog cannot
recover this lease's sidecar, ingress policy or temporary key.

## Preconditions

- The platform has produced a source-bound application-mode backup receipt;
  the full-stop receipt is not reusable.
- The application controller has passed its focused local tests and is using
  the exact allowlist below; this does not substitute for live host evidence.
- LXC110 `aster-llama.service` is active with the exact accepted b11429
  SYCL/Level-Zero binary, model and device identity.
- The host-attested receipt includes `exclusive_backend_claim=true`: LXC110's
  temporary ingress policy allows only the sidecar source address
  `192.168.70.10` to reach TCP 11435, with the prior policy checkpointed for
  restoration. Zero load at one instant is not sufficient evidence.
- LXC104 `aster-agent.service` and LXC116 `aster-speech.service` are stopped
  and quiesced; the current controller does not runtime-mask them. News and
  other inference consumers are quiesced.
- The named LXC104 sidecar has a pinned source digest, distinct unprivileged
  UID 1904, one worker, fixed non-public port 19104, test-only credentials, no privileged
  mounts/sockets, denied unauthorized network paths, and start time within the
  application lease.
- At least 35 minutes remain before the 04:15 restoration deadline: up to 20
  minutes for the frozen batch plus the 15-minute restoration reserve.

The exact host installation, denial probes and recovery sequence are in
[`A1-HOST-INSTALL-RUN-CARD.md`](A1-HOST-INSTALL-RUN-CARD.md).

The separate disabled-only platform installation gate is
[`APPLICATION-B60-DISABLED-INSTALL-RUN-CARD.md`](APPLICATION-B60-DISABLED-INSTALL-RUN-CARD.md).
It must be approved and completed before any application-only recovery drill;
it does not authorize that drill or a benchmark lease.

The next bounded recovery proposal is
[`APPLICATION-B60-DRILL-RUN-CARD.md`](APPLICATION-B60-DRILL-RUN-CARD.md).
It remains a separate approval from both the 03:15 full-stop drill and the
20-call A1 benchmark.

## Effects and evidence

1. Capture the platform checkpoint and application-mode receipt.
2. Stop only LXC104 `aster-agent.service` and LXC116
   `aster-speech.service`; never stop or mask LXC110 llama.cpp for this mode.
3. Start the already-installed sidecar only after the host observer validates
   its exact identity and isolation.
4. Run one bounded 20-request batch through the sidecar. The platform receipt
   records the sidecar observation, lease identity/generation, backend identity,
   source digest and watchdog deadline.
5. Stop the sidecar before restoration reserve, restore the checkpointed LXC110
   ingress policy and remove the temporary key. If the key effect was
   observed, the recovery path performs one planned `aster-llama.service`
   restart; the backend is unavailable only during that bounded restart.
   Verify production authentication and wrong-key denial, then start the two
   consumers and verify llama.cpp, device, model, auth and schedules.
   Recovery performs at most three tiny authenticated health generations (the
   exact backend check, production-auth check and post-consumer check); it
   makes no arbitrary model calls.

## Rollback

If any sidecar, network, receipt, watchdog or timing gate fails, make no
arbitrary model calls, stop the sidecar, restore the checkpointed LXC110
ingress policy, remove the temporary key, and perform only the planned backend
restart if the key effect was observed. Restore the two consumers, retain the
lease for reconciliation if any effect is uncertain, and report the failure.
This mode must never be represented as a full-stop lease.
