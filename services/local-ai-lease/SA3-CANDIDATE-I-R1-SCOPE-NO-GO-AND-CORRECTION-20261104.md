# SA3 candidate-i R1 scope NO-GO and source correction — 2026-11-04

## Terminal result

Booking `aster-stream-a-sa3-candidate-i-20261104-1730-r1` claimed exactly at
17:30:00 and failed restored at 17:33:07 after 187 seconds. The authoritative
terminal is `no_go`, first failure phase `owner-transaction`, outer failure
code `OWNER_TRANSACTION_FAILED_RESTORED` and `production_restored=true`.

The retained stderr is root:root mode 0600, 1,630 bytes, SHA-256
`a7ccedf008f8d3a92ac32a4f980f0a74a0eda7e164f54ba8630e334864e3ad1c`.
Its existing bounded adapter projection identifies
`fixed candidate-i invocation mismatch`; no raw stderr, prompt, answer, case
identity or model response was read into shared evidence. No candidate result
file exists and R1 is spent.

Independent postchecks found the lease exactly ready, drain state/lock and
operation lock absent, candidate process/scope absent, LXC104/110/116 running,
Aster Agent, accepted `aster-llama.service`, Speech, pvescheduler and pvestatd
active, and Lab Hours dispatcher/Doctor timers active. Production impact was
the bounded transaction outage only; restoration completed and no model result
was accepted.

## Deterministic source defect

The candidate-i host adapter imported candidate-g's generic `scope_unit()` and
therefore supplied `aster-llama-sa3-<token>.scope`. The guest wrapper's fixed
candidate-i invocation requires `aster-llama-sa3-i-<token>.scope`. Every other
argument could be correct while this exact mismatch still failed before the
listener workload.

The source correction gives candidate-i its own fixed, validated scope-name
derivation and adds a cross-module regression proving the host command equals
the guest wrapper's exact result. Corrected adapter SHA-256 is
`80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6`;
the updated 36-pin release manifest is
`05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d`.

The focused correction, transaction, wrapper, current-manifest, full-runtime
and reserved-runner suite passes 48/48. A two-file reversible inactive installer
and deterministic bundle builder are source-ready. No installation, retry,
new booking, service restart, model/backend change, route or promotion is
authorized by this source milestone.
