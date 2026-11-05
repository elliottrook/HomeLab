# SA3 candidate-i R2 result — 2026-11-04

## Transaction

Booking `aster-stream-a-sa3-candidate-i-20261104-1830-r2` claimed exactly at
18:30:00 PST and completed at 18:33:50 after 230 seconds. The authoritative
reservation is `complete` / `COMPLETE`; terminal state records 20 requests and
`production_restored=true`.

The retained result is root:root mode `0600`, one-link regular, 10,847 bytes,
with SHA-256
`d46e10eebbbb09d8eed7617ec976be6d0466976a770c0c66cf64da255f628b5f`.
Strict bounded reconciliation accepted 20 predictions, 14 model requests, six
deterministic no-transport abstentions, zero retries, zero errors, empty
effects, authority `none`, automatic routing `off` and a matching owner-receipt
digest.

## Restoration

The lease is `ready`; drain state, drain lock and shared operation lock are
absent; no candidate-i process or transient scope remains. LXC104/110/114/116,
Aster Agent, accepted 9B/SYCL llama, Speech, both News timers, Lab Hours
dispatcher/Doctor and Proxmox daemons are healthy. The EPUB scheduler remained
gated by the protected reservation and returned its registered temporary-
unavailable status rather than competing with R2.

## Quality disposition

Model-blind packet SHA-256 is
`d7018970d3a67e20c1daf0a3f110e045b91ca2d18c267f113070f65ee4471935`.
Three distinct complete responses were retained under the attempt. The frozen
conservative decision is **NO-GO** at 8/20 against the required 18/20, with
0/6 mandatory abstentions passing the complete intersection and zero
false-completion failures. Decision SHA-256 is
`0819a39c4df60d48fed5064278cea28becb666cd7e8b5547d0b4afb49c855ba7`.

Temporary review staging and the post-run key copy were removed after the
packet, responses and decision were retained under the root-custodied attempt.
R2 and candidate-i are spent. There is no retry, case-level tuning, route,
authority, tool grant, model/backend change or promotion.
