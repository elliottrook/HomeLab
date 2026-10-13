# A1 full-path test topology candidate — 2026-10-13

**Status: PROPOSAL / BLOCKED.** This is a deployment design for review, not a
live endpoint, credential grant or lease request. The benchmark remains
blocked until the platform owner proves independent recovery and the test
instance passes an isolation check. The obsolete B60 evening runner stays off.

## Question the topology must answer

The accepted host's light lease stops `aster-agent.service` in LXC 104. A
request sent straight to llama.cpp while that service is stopped measures only
the model backend. It cannot establish Aster's prompt, authentication,
application, tool-selection or end-to-end timing. Control and challenger must
therefore use the **same isolated Aster gateway path** during a verified lease,
with only the declared backend/profile changing. If this cannot be arranged
without production credentials or consumer interference, do not run the
full-path comparison; retain the direct-backend result as a separate control.

## Smallest candidate boundary

1. Run one temporary, single-worker Aster process outside LXC 104's production
   service lifecycle, preferably on the Mac mini under a dedicated unprivileged
   identity and loopback-only listener. This placement is a proposal; verify
   dependencies, network reachability and resource impact before adopting it.
   Do not bind a public interface or reuse the production service port.
2. Supply a minimal test environment: a distinct Aster API key, a distinct
   gateway ingress key, a test-only backend key, the candidate's reviewed
   backend URL, empty lab-operation enablement, no broker/approval socket,
   no OpenBao, Authentik or production credential mounts, and an empty
   temporary knowledge/state area. A missing required setting must fail
   closed; never fall back to a production default. The credential values stay
   in protected custody, outside Git, logs, model input and run metadata.
3. Put the `A1TestGateway` guard in front of that process. Only the 20 exact
   frozen serialized POST bodies may reach `/v1/chat/completions`; all other
   routes, methods, tools, repeated bodies and unrecognized credentials are
   rejected. The ingress key is consumed at the guard and replaced with the
   distinct inner test key. Configure an owner-only durable claim journal
   outside Git before the first request. Verify denial and restart behavior.
4. Send the frozen cases through the same client serialization and guarded
   Aster path for both control and challenger. Preserve request/result clocks,
   censored outcomes, fixed corpus/source/scorer hashes, model and runtime
   identity, cache/load state, and the one-attempt rule in private evidence.
   No real household context or connected tools enter this experiment.
5. Stop the test process before the lease restoration reserve. Prove the
   accepted Q4_K_M/SYCL model, exact unit/binary/device, authenticated
   generation, Aster and Speech health, backup/News schedules and normal
   consumer behavior from fresh independent observations before clearing the
   host lock. Keep the private journal and partial results if a run fails.

## Review gates before any installation

- Confirm whether a Mac-mini test process can reach only the leased candidate
  backend without competing with Companion, News or backup work; otherwise
  choose a separately isolated guest and document the extra host dependency.
- Confirm the actual Aster import/startup behavior with a fixture-only
  environment. The repository's ASGI fixture tests demonstrate a synthetic
  path, but no isolated live process has been started for this card.
- Confirm server-side tools and job workers cannot execute even if the model
  emits a tool call. `enabled_tools: []` is defense in depth, not the only
  authority boundary. The test identity must lack worker and broker grants.
- Pin the test process source, dependency set, credential-delivery method,
  listener, egress restriction, shutdown procedure, private journal custody,
  and rollback. A synthetic in-process guard test is not deployment proof.
- Obtain a **live**, same-night backup receipt, host lease/generation, armed
  independent watchdog and restoration reserve. The paused 03:15 automation
  may inspect those facts; clock time alone must not launch the benchmark.

Owner split: Stream A owns the frozen assistant workload, guard, scoring and
privacy bar. The platform owner owns the whole-host lease, watchdog, candidate
backend and restoration. B60 engineering owns candidate model/runtime
measurements. No lane can approve its own expansion of tool authority.
