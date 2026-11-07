# M3 K2 MacBook sealed wrapper boundary — 2026-11-06

## Outcome

The fixed MacBook custody wrapper for one future K2 sealed-evaluation
transaction is source-frozen. It was tested only with temporary synthetic
fixtures; it did not open the sealed input, contact the relay or make a model
request.

## Exact boundary

- wrapper: `scripts/aster-adaptive/nlu_k2_sealed_macbook_wrapper_v1.py`
- wrapper SHA-256: `e3880b4112f98333bcca3bca97a58850473e4df353a940f6c08dfa2d6866d2d2`
- focused test SHA-256: `3425ee07c39aea79526dc2df783f078e2e7c54c21353223c784943d872d23be2`
- fixed runtime root: `/private/tmp/aster-k2-sealed-runtime-v1`
- fixed attempt parent: `/private/tmp/aster-k2-sealed-attempts`
- private inputs: the exact R5 corpus and sealed evaluation already present on
  the MacBook, both mode 0600 with one regular link and expected owner

The wrapper validates nine exact MacBook runtime pins and both private input
digests before creating one mode-0700 attempt directory. It reads the
transaction relay nonce only from standard input, stores it temporarily in a
create-only mode-0600 file, runs the Swift shortlister once, runs the Python
evaluator once, verifies the returned content-free digests against mode-0600
records/metrics/journal files, and removes the nonce on every terminal path.

Child standard error is captured and never relayed. The wrapper prints only a
bounded content-free result or failure class. It has no B60 address, SSH
client, booking operation, tool authority, retry or route effect.

## Verification

- wrapper/preregistration/runner focused suite: 12/12 passed before the final
  preregistration refresh; combined source suite: 16/16 passed afterward
- Python syntax compilation: passed
- sealed evaluation access: false
- model requests: zero
- external mutation: none

## Preregistration refresh

Adding this fixed wrapper expands the sealed transaction runtime pins from ten
to eleven. The refreshed canonical preregistration SHA-256 is
`66ea288e456d4cef6e0143c882a5b647a9fab7170f0ef0e3bd6b1952463ff7cc`.
The earlier digest is superseded and must not be admitted by the platform.
