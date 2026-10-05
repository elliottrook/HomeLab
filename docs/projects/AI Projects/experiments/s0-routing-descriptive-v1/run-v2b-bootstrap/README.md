# Disposable VM V1b/V2b — bootstrap gate passed

Date: 2026-09-26
Result: **PASS for bootstrap/capture only; V3 remains unauthorized**

## Outcome

V1b created fresh stopped VM119 `aster-s0-fixture-v1` from the retained
checksum-pinned Debian image. Its generated NoCloud ISO contains exactly
`meta-data` and `user-data`, and extracted bytes match the reviewed source hashes.
The strict stopped-state validator accepted one vCPU, 1 GiB fixed RAM, an 8-GiB OS
disk, q35/OVMF, serial/seed devices, manual start, and no vNIC, guest agent,
credential, passthrough or shared filesystem.

The single V2b boot reached the corrected canary unit after the known two-minute
network wait. The unit succeeded, the outer lifecycle published one complete
three-record protocol envelope, and the guest powered off cleanly. A host stop was
not required. The strict local parser accepted the exact run and payload-manifest
identity, canonical JSON, declared length, sequence and SHA-256. The semantic
validator accepted the fixed result and confirmed `interfaces=["lo"]` and
`corpus_evaluated=false`.

## Evidence

- Seed ISO: 376,832 bytes; SHA-256
  `af8278b6fe270f3a45651a376c426284d51a894fff1820173615f04051cd2ee5`.
- Serial capture: 104,501 bytes; SHA-256
  `ddd74734c972dd553cbdca7830230fe6b28875d91db7d55bd0f2322e9da7acb1`.
- Result: 119 canonical bytes; SHA-256
  `59b9326cb92efe7e07553cea3ac6e827b0f5629c008fdf1e7e283a816d5ee9b4`.
- VM119 is stopped and retained. VM118 remains stopped. Existing VMs/LXCs retain
  their preflight states.
- `local-lvm` remained active with 662,979,510 KiB available after the run.

The raw capture remains on Proxmox and is not committed because it contains broad
boot noise and generated public SSH host keys. The bounded digest, parser result,
canonical result and selected non-sensitive receipts are retained here. The image
started SSH and generated host keys despite having no vNIC or injected login; this
remains hardening/efficiency evidence for later candidates, not a bootstrap-gate
failure.

## Decision

V2b proves that the fresh VM can bootstrap the reviewed seed, enforce the corrected
private-device unit, publish a digest-bound result over serial, report loopback-only
interfaces and shut down within the outer deadline. It does not prove execution of
the S0 router fixture, prohibited-operation controls, repeatability, model quality,
accepted-corpus handling or production suitability.

The next safe step is local preparation of a new-identity V3 candidate containing
only the invented fixture and explicit negative boundary tests. V3 execution needs
its own reviewed manifest and approval. No automatic transition or retry is allowed.
