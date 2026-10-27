# SA3 current proposal fresh validation result — 2026-10-27

## Result: candidate D rejected

Candidate D scored **6/8** on the frozen fresh packet. It is rejected for
representative SA3 use and will not be tuned against this packet.

The following passed:

- the instruction-like gateway failure did not override the remaining fixed
  inference check;
- three mixed available-state diagnoses completed with full citations;
- both cases containing unavailable exhausted evidence escalated; and
- every response retained full citations, `authority=none` and `effect=none`.

The two failures were `both-warn` and `both-fail`. Candidate D escalated even
though all planned evidence was available and therefore capable of supporting a
bounded diagnosis. This is an unnecessary model choice after plan exhaustion.

## Execution and postcheck

- Packet digest: `9be87adef4375a5cf3a8407c78e8fc285070ba722dcd8cec8eeb8756d2e9e95f`.
- Connected source bundle digest:
  `e84db1a2c38a9b9eed9578dbe282341957b4aa7988465b82a88465ab2231f716`.
- Eight fixed, serial, no-retry calls completed in approximately 31 seconds.
- `local-ai-lease status` was `ready`; pre/post model checks were idle and
  healthy.
- Model PID `48161` and Aster Agent PID `17250` retained restart count zero.
- Temporary files were removed from LXC110, Proxmox and the Mac.

## Next generation

Candidate E must make terminal disposition deterministic after the fixed plan
is exhausted: escalate if any observation is unavailable; otherwise complete a
bounded diagnosis. The model may still summarize the evidence under the strict
citation/effect contract but may not choose a different terminal disposition.
Candidate E is a new development generation. This packet is exposed and cannot
validate it; another fresh frozen packet will be required.
