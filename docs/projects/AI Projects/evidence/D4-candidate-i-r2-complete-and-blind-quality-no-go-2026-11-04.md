# D4 candidate-i R2 complete and blind-quality NO-GO — 2026-11-04

## Runtime result

The distinct booking
`aster-stream-a-sa3-candidate-i-20261104-1830-r2` claimed exactly at
18:30:00 PST and completed at 18:33:50 after 230 seconds. The authoritative
ledger is `complete` / `COMPLETE`; the exact terminal binds the registered
workload, 20 cases and `production_restored=true`.

The root-custodied result is a root:root mode-0600 one-link regular file of
10,847 bytes with SHA-256
`d46e10eebbbb09d8eed7617ec976be6d0466976a770c0c66cf64da255f628b5f`.
Independent strict parsing and canonical-byte comparison accepted exactly 20
predictions, 14 model requests, six deterministic no-transport abstentions,
zero retries, zero errors, empty effects, authority `none` and automatic
routing `off`. The retained owner receipt names the same result digest.

## Restoration and coexistence

The lease returned exactly `ready`; drain state, drain lock and shared
operation lock are absent; no candidate-i process or transient scope remains.
LXC104/110/114/116 are running. Aster Agent, the accepted 9B/SYCL llama
service, Speech, both News timers, Lab Hours dispatcher/Doctor and Proxmox
control daemons are healthy.

The EPUB scheduler timer remains active. Its scheduled probes returned the
registered temporary-unavailable status while the Lab Hours reservation was
protected, so EPUB did not enter or compete with the transaction; its later
booked exclusive work remains outside this window. That fail-closed deferral
is expected coexistence, not a candidate or production failure.

## Independent blind decision

The frozen reconciliation produced model-identity-blind packet SHA-256
`d7018970d3a67e20c1daf0a3f110e045b91ca2d18c267f113070f65ee4471935`.
It excluded model identity, answer keys, transport flags, finish reasons,
latency and runtime metadata. Three fresh reviewers received only that packet
and returned complete 20-row responses. All three initially copied the
underlying packet digest into the blind-packet binding field; each reviewer
then changed only that one field to the exact blind-packet digest, leaving all
judgments unchanged. The retained response file SHA-256 values are:

- reviewer 1: `31b6d1af215dd7d75dcdb48579ad6b934a59e9f38d478b394d6619120325e183`;
- reviewer 2: `1ad6ff2af576330ae33c3d31925e9434970aecc3900d87a13bd7478958195858`;
- reviewer 3: `13a6e5b8e20e5d7da4bf38282c2fe74ce6224f618b704ba49f5a07913478a505`.

The exact conservative decision is **NO-GO**: **8/20** cases passed every
deterministic and three-reviewer dimension against the frozen **18/20** floor;
**0/6** mandatory abstentions passed the complete intersection; and there were
zero false-completion failures. Decision SHA-256 is
`0819a39c4df60d48fed5064278cea28becb666cd7e8b5547d0b4afb49c855ba7`.

The result, blind packet, three responses and decision remain under the
root-custodied attempt directory. Temporary host review staging, including the
post-run answer-key copy, was removed after retention. No prompt, answer,
answer key, case identity or per-case judgment is copied into shared evidence.

Candidate-i is spent and must not be retried or tuned against case-level
failures. This runtime success proves the transaction and restoration path,
not investigation quality. D4 remains open; any successor must be materially
new and preregistered against an untouched evaluation boundary. No route,
repair authority, tool grant, model/backend change or promotion follows.
