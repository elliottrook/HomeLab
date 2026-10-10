# Disposable VM V3b — isolation boundary gate passed

Date: 2026-09-26  
Result: **PASS for the invented-fixture boundary; accepted-corpus execution remains unauthorized**

## Outcome

The frozen V3b release was staged with every source hash matching release manifest
`825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.
The generated NoCloud ISO contains exactly `meta-data` and `user-data`, and its
extracted bytes match the reviewed sources. Fresh stopped VM121
`aster-s0-isolation-v2` passed the strict no-vNIC/no-agent configuration gate.

The single offline boot emitted exactly one complete `ASTER_S0_V1` envelope and
powered off without host intervention. The strict local parser accepted the exact
run and payload-manifest identity, canonical JSON, declared byte/chunk counts and
both result digests. The semantic validator accepted all ten required results:
environment allowlisting and clearing, fixed locale, unprivileged execution,
loopback-only interfaces, denied IPv4 and Unix socket creation, denied fork,
denied read of the planted non-secret canary, and denied system write.

## Evidence

- Seed ISO: 380,928 bytes; SHA-256
  `c8ad6005bfc221f522c4832208c6a869c936e5eddb885df4eab1f60375b07aae`.
- Serial capture: 104,695 bytes; SHA-256
  `5fbdb31fe58d9c2020bacca9953660dc137a5a3bbdbe081b0a83f056ecd65499`.
- Result: 364 canonical bytes; SHA-256
  `89725401c7447df1cf026b2211962096de4f13b63059a86f3243794e1950614b`.
- Payload-manifest identity:
  `73b4d01f94f9ab31919ba024320e70d8152fe6efdd03896ef1cdc086ff1ff63c`.
- Both copied receipt sets reproduce their remote evidence indexes with zero hash
  mismatches. VM121 is stopped and retained; VMs118–120 are also stopped.
- No accepted request, routing engine, model, credential or network device was
  present. No retry, cleanup or unrelated guest mutation occurred.

The raw serial capture remains on Proxmox and is not committed because it contains
noisy boot output and generated public SSH host-key material. Its bounded size,
digest, strict decode, canonical result and selected non-sensitive receipts are
retained here.

## V4 decision

**GO to prepare a separately immutable accepted-corpus candidate.** The evidence
supports the disposable no-vNIC VM as the S0 execution boundary for this next
experiment: fresh construction repeated, transport stayed bounded, and every
mandatory invented-fixture control produced positive evidence.

This is not authority to execute the accepted corpus. It does not establish router
quality, workload repeatability, operational scaling or production suitability.
The corpus artifact, runner, result schema, resource budget and one-run lifecycle
must be frozen and reviewed before a distinct execution approval. VM121 must not be
reused as that candidate, and no automatic transition or retry is allowed.
