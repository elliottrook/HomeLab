# Full-Aster challenger first-screen effect card — 2026-10-26

## State

**SOURCE-COMPLETE / LIVE BLOCKED.** The artifact is staged, but this card does
not authorize a restart, mount, lease, service stop or model request.

The next test answers only whether the exact Qwen3.6-35B-A3B Q4_K_M artifact
loads safely on the accepted b11429/SYCL runtime, resides within bounds and
returns two structurally complete reasoning-on answers. It is not the 24-case
full-Aster comparison.

## Required fresh admission

All of these must pass in one same-cycle F6 transaction:

1. accepted same-date F2 three-archive result and verified F3 retained receipt;
2. same-date F4 pre-acquire and F5 metadata/auth evidence after the 03:00 pull;
3. exact staged artifact path, 20,419,565,568 bytes, SHA-256
   `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`,
   root:root mode 0400 and no existing guest mount;
4. exact accepted 9B model, b11429/SYCL runtime, unit, auth and schedule
   restoration manifest;
5. ready whole-host lease, no competing work, root-owned checkpoint and
   independently armed watchdog with enough measured restore reserve; and
6. an owner-approved restart/outage transaction. A 90-minute outage is an
   outer budget, not permission to consume it.

## Exact transaction shape

1. Capture current LXC 110 configuration, accepted service/unit/model/runtime
   hashes, guest/service health, consumer and schedule state.
2. Acquire the F6 lease and arm the independent watchdog before any consumer
   change.
3. Quiesce the registered B60 consumers through the F6 controller.
4. Add one `backup=0`, read-only LXC 110 mount for the single staged artifact
   and restart LXC 110. Revalidate mount read-only, artifact size/hash from the
   guest and exact accepted runtime. Do not copy the file into guest root.
5. Keep `aster-llama.service` stopped and start one transient candidate unit
   under the existing `ollama` identity, existing SYCL environment/device and
   existing authenticated local endpoint. Use one slot, 8K context, reasoning
   on, speculation off and no restart policy.
6. Stop immediately on load failure, GPU spill/OOM, device error, malformed or
   truncated first/second response, unexpected process, restart, lease loss or
   evidence failure. Never retry an uncertain request.
7. If startup/residency pass, send exactly two fictional synthetic requests,
   each with a 60-second limit. Retain only structure/status/timing/resource
   evidence; do not retain hidden reasoning.
8. Stop the transient candidate, remove its unit/runtime state, remove the
   temporary mount configuration and restart LXC 110 once into its original
   configuration.
9. Restore and independently verify the exact accepted 9B model/runtime,
   authenticated response, Aster Agent, Speech, News, guests, schedules,
   watchdog/lease cleanup and absence of candidate processes/mounts.

Any uncertain effect enters recovery and rejects the candidate result. The
watchdog owns recovery if the controller or session disappears.

## Timing and separation

The test runs only after the same-date 03:00 pull and F2–F5 acceptance, with a
hard completion/restoration deadline before the next protected production
reservation. It must not overlap backup, pull, maintenance, News or another
lease. It is not scheduled merely because this card exists.

Passing this two-request screen allows preparation of the matched 24-case
packet run. It does not approve that run, change production's model, enable
routing or grant tools.
