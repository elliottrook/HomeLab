# Full-Aster first challenger profile — 2026-10-26

## Result

**PASS — one exact first-screen profile is selected in source; it is not
downloaded, staged, loaded or admitted.**

The first proposed challenger is Qwen3.6-35B-A3B Q4_K_M, reasoning on and
speculation off, using the accepted llama.cpp b11429/SYCL binary for the first
compatibility screen. This follows the B60 owner's existing ranking: screen
ordinary inference before changing runtime, driver or adding speculation.

Exact public pins:

- source revision `995ad96eacd98c81ed38be0c5b274b04031597b0`;
- maintainer GGUF revision `baec3ebee244827cda0f4557eafa8b28f7545fa6`;
- file `Qwen3.6-35B-A3B-Q4_K_M.gguf`, 20,419,565,568 bytes;
- model SHA-256
  `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`;
- accepted SYCL binary SHA-256
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.

The bounded first screen is two sequential synthetic requests, one 8K slot,
60 seconds per request and stop on the first load, residency, structure,
truncation, restart or device failure. It is only an architecture/residency
screen. Passing it would not substitute for the matched 24-case Aster-path
comparison.

The profile retains the measured storage boundary: no guest-root copy, at
least 20 GiB host free after staging and a reviewed read-only host-backed path.
It caps GPU memory at 24 GiB and LXC host memory at 16 GiB. Because the 20.4 GB
artifact leaves little GPU headroom, actual load/workspace/KV residency is a
hard measured gate; file size alone is not a fit claim.

## Open effects

Artifact acquisition, target architecture compatibility, measured residency,
the owner-held packet, owner acceptance and the F6 effect transaction all
remain unresolved. The profile grants no authority. Downloading 20.4 GB,
adding a guest mount, stopping production, loading the model and running its
two requests are later bounded effects and are not authorized by this source
selection.

## Validation

- profile SHA-256:
  `d2c7fe5a9c30bf80c9c82809beff06fe6a01b51e0fa5e3207fc90a080703340a`;
- validator SHA-256:
  `8661fd391b5b1b8a49e3eabb1300c949b6740ef44fef92f8bc27f21f3ceec645`;
- tests SHA-256:
  `efa3167927ec729323a1e23746108cc80b15fd55e2d4bf9ecbf7d04b5968f6d6`;
- combined full-Aster source suite: 20/20 passed.

No model download, model call, private-data access, lease, service change,
restart, deployment, routing change or remote write occurred.
