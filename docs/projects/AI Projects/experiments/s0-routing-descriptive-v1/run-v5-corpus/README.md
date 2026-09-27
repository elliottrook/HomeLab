# V5 accepted-corpus attempt — failed/inconclusive

Date: 2026-09-26  
Result: **FAILED/INCONCLUSIVE; no routing result and no retry**

## Outcome

Jason approved the exact release-manifest-bound V5 window. The 23 remotely staged
files reproduced both manifests exactly. Fresh stopped VM122
`aster-s0-corpus-v1` passed the strict no-vNIC/no-agent configuration gate. Its
483,328-byte NoCloud ISO contains exactly `meta-data` and `user-data`, whose
extracted bytes match the reviewed sources.

The single offline boot reached `aster-s0-corpus.service`, but that unit exited
with an error before any `ASTER_S0_V1` record appeared. Cloud-init then powered the
guest off through the reviewed lifecycle. The 104,662-byte capture completed within
bounds, no host stop was required, and VMs118–122 are stopped. No retry occurred.

## Evidence and interpretation

- Release manifest:
  `1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.
- Seed ISO SHA-256:
  `f425e3bd7c330886d195a6d3e4d58b9a3950607c6ddb9d3103cbe58b4d0fa6fe`.
- Serial capture SHA-256:
  `d8dc426db310dfe2855007da0edebc96170abcb293b997d76bcf65ea4c944aa8`.
- Both copied receipt sets reproduce their remote indexes with zero mismatches.
- Protocol records: zero. Strict parser result: `incomplete protocol`.
- Precise service failure: **UNKNOWN / REQUIRES VERIFICATION**.
- Whether the worker read or partially evaluated any accepted row before failing:
  **UNKNOWN / REQUIRES VERIFICATION**. No usable result was exported.

A successful host capture and clean shutdown are transport/lifecycle evidence, not
a routing result. No engine metrics, comparison, model decision or promotion can be
inferred. The failed attempt remains part of the evidence history.

The raw capture remains on Proxmox and is not committed because it contains noisy
boot output and generated public SSH host-key material. Its digest, bounded size,
protocol count and selected non-sensitive failure lines are retained here.

## Next gate

VM122 remains stopped and retained. A bounded, read-only stopped-disk inspection
can determine the service status, artifact hashes, output-file presence and narrow
journal cause without rerunning guest code. That inspection requires separate
approval. It cannot authorize a corrected candidate, second boot, tuning, cleanup,
promotion or push.
