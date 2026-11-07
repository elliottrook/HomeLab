# M3 K2 sealed runtime bundle — 2026-11-06

## Outcome

The complete content-free K2 sealed-path source is packaged as one
deterministic inactive archive. It contains no corpus, sealed evaluation,
credential, booking, result or executable effect.

## Exact bundle

- builder: `scripts/aster-adaptive/build_nlu_k2_sealed_runtime_bundle_v1.py`
- builder SHA-256: `27796c98f845fbedd4bca302e3ea357c3172aa700da79eaa656bf98e1e651af9`
- focused test SHA-256: `4a549bea86440c48bf4924b6d49e55ef5c813e1b23b481db32e80036f0b94ffa`
- output: `/private/tmp/aster-k2-sealed-runtime-v1.tar.gz`
- archive SHA-256: `3b7e7cf40b08808cb94721a5778a1474e35a4d8f8d30c7dac858a37dc6e6aed6`
- archive bytes: 25,097
- source files: 13 plus one canonical manifest
- preregistration SHA-256:
  `4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1`

The manifest pins the 12 executable runtime sources plus the non-authorizing
preregistration source. Every member has normalized uid/gid, empty names,
mtime zero and mode 0600. Gzip metadata is normalized, and two independent
in-memory builds are byte-identical. The create operation is exclusive and
mode 0600.

## Verification

- deterministic bundle tests: 3/3 passed
- archive listing: exactly `runtime/MANIFEST.json` and the 13 named sources
- private inputs included: false
- effect authorized: false
- authority: not granted
- archive deployed or transferred: no

Platform commit `c1417aef` adds an independent fail-closed archive validator.
It reads the exact bundle without extraction and pins the outer archive,
canonical member set and metadata, manifest authority fields, preregistration
digest and all thirteen source digests. Its focused tests pass 4/4, syntax
compilation passes and validation of the exact archive returns 13 sources,
`private_inputs_included=false`, `effect_authorized=false` and
`authority=not-granted`.

## Remaining gate

The archive is only a review/staging candidate. Its identity and content are
now independently bound, but a reversible inactive installer remains open.
No host may unpack or activate it for an effect unless the K2 development gate
is a restored pass and the later workload has its own admissible Lab Hours
booking.
