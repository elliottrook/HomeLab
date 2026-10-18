# Full-inference drain assessment — 2026-10-18

## Conclusion

The full-drain architecture is the better small candidate for real GPU
experimentation than preserving the production backend. It removes the direct
client-admission blocker by treating LXC110 itself as part of the drained
production inventory. It remains a prerequisite, not a usable workload
release.

Repository evidence supports the following, with limits:

- MacBook SSH administration to Proxmox was independently verified in the
  MacBook Administration Layer project.
- Aster's accepted recovery baseline is documented: `xe` host binding, VM105
  stopped without a persistent B60 mapping, LXC110 `aster-llama.service`,
  Qwen3.5-9B/SYCL/Level Zero and `scripts/check-aster-b60.sh`.
- Existing `lease_controller_candidate.py` already has an offline fixed
  104/110/116 drain and trusted-observer recovery shape.
- No current source-bound live checkpoint proves that the MacBook can launch a
  reviewed experiment through the admin path during a full drain. No workload
  is authorized by this assessment.

The exact smaller run card is
`COOPERATIVE-FULL-INFERENCE-DRAIN-RUN-CARD-20261018.md`. It preserves the
30+15 attended bound, excludes reboot/PCI rebind/fault injection, and requires
fresh baseline hashes and postchecks. A later usable-lab milestone needs a
named workload over the reviewed admin path, not a guessed direct client IP.
