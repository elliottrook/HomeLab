# B60 first-screen enforcement-source reconciliation — 2026-10-26

## Input and conclusion

B60 liaison commit `457ffa1a00bdd2066178ee942ae40d32f64b716f`
characterizes four real limitations in public preflight source
`47be1007…eb608`: past epochs, a ten-character non-date cycle, a claimed reserve
unconnected to deadline spacing, and arbitrary contract bytes can all return
non-authoritative `admitted:true`. B60 correctly retained
`live_effect_authorized:false`; this is not evidence that a deployed effect
accepted those inputs.

The exact live producer/controller is platform source commit
`b6dc186eef865924294b4e5cb1ef72d73c149733`, not the public preflight module:

- `full_aster_first_screen_controller.py` derives the Vancouver cycle from its
  clock, calls `collect_fixed_sources`, rereads fixed F2/F3 predecessor bytes,
  produces F4/F5 itself and rejects predecessor drift before effects;
- `full_aster_first_screen_admission.py` binds those exact four evidence byte
  digests, the generated lease identity/generation, frozen contract digest,
  staged artifact and accepted baseline identities;
- `LocalProxmoxFullDrainSourceProducer` and
  `LocalProxmoxFullDrainValidator` own live host/lease/source validation;
- `full_aster_first_screen_launch.py` starts the independent guardian before
  the owner scope; and
- the guardian rereads durable screen/full-drain state and uses the same
  mount-aware recovery identity.

The two-request first screen uses two fixed prompts and does not consume the
24-case private benchmark contract. The frozen contract applies to the later
matched 24-case screen. The workload-specific admission pins its immutable
digest; describing the public preflight as live authority would be incorrect.

## Corrections from the peer review

Stream A hardened the public preflight anyway. Candidate source SHA-256
`33408d610e107814fd92103e0ba2f11c6eb12b8c7d33a30fae9780ec8b580ab0`
now requires an explicit current epoch, parses and checks the accepted contract
semantics, requires a real Vancouver calendar date equal to the current cycle,
connects declared recovery reserve to deadline spacing and requires the exact
same-cycle 04:15 protected deadline. Twenty-nine focused full-Aster tests pass.
This remains source-only and grants no live authority.

Review of the actual live launcher found a separate issue: its 30/45-minute
deadlines were relative to process start, so a delayed timer start could exceed
04:15. Platform source candidate `6dbdea2c` closes that gap before any effect
and passes 9/9 focused tests. It is not installed. The October 27 effect is
therefore NO-GO until the new exact launcher is installed and accepted, or the
existing timer is disabled before 03:10.

## Claim boundaries

- The two-request first screen tests load, residency, sequential response
  structure and bounded restoration. It is not the 24-case benchmark.
- The 24-case screen can establish equal-or-better performance against its
  frozen gates; equal quality is not demonstrated improvement.
- Final qualification still requires the programme's repeated sessions and
  per-class sample counts; one 24-case pair cannot establish final p95.
- Transport completion remains distinct from reviewer-accepted useful-answer
  completion. Rejected answers stay in terminal timing and failure accounting.
