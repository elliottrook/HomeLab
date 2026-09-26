# V1b/V2b execution approval gate

The release is ready for one bounded execution window. Approval would authorize:

1. create the exact reviewed seed-source directory and copy only the manifest-bound
   files listed in `release-manifest.json` to Proxmox;
2. create and verify `aster-s0-bootstrap-canary-002.iso`;
3. create stopped VM119 `aster-s0-fixture-v1` from the retained checksum-pinned
   image, with the configuration in `PREFLIGHT.md`;
4. stop for automatic configuration validation and proceed only if every V1b gate
   passes;
5. perform one V2b boot using `run-once-v2b.sh`, with no input, a 300-second and
   4-MiB capture limit, one deadline stop if needed, and no retry; and
6. retrieve, strictly parse and document the bounded evidence.

Approval would not authorize V3, accepted-corpus access, network attachment,
credential injection, VM118 modification, cleanup/destruction, service deployment
or any authority change. A V1b mismatch ends the window before boot. A V2b failure
leaves VM119 stopped and retained for review.
