# Stream A F6 current-packet card validator — 2026-10-25

Result: **OFFLINE VALIDATOR READY; EXISTING PLATFORM CARD REMAINS NO-GO**

Stream A converted the exact host/V3 identities from the 22:48 installed
snapshot and the final M3 coordination receipt into a machine-readable
requirements fixture. The validator requires all nineteen host composition
paths with their full SHA-256 values plus the final M3 runner, scorer, journal
validator and eleven-file packet-manifest identities. It also rejects the
known superseded restore-observer and intermediate M3 manifest hashes.

Five focused tests pass: a complete synthetic card is accepted; a missing V3
path, missing final M3 manifest, superseded digest and unknown requirements
schema are rejected.

Running the validator against the current platform-owned candidate-H card
fails as expected. The card omits the V3 composition paths, omits all four
final M3 identities and retains the superseded restore-observer and original
M3 manifest. This agrees with the independent prose review and provides a
repeatable acceptance check for the replacement card.

This is an offline review tool. It does not attest that the installed host is
unchanged after the snapshot, publish the requirements to the platform owner,
arm F6, create a lease, stop a consumer or call a model. A replacement card
must still pin the remaining wrappers, units and guest files described in the
installed snapshot, pass independent review, and bind fresh F3–F5 evidence
before live approval is requested.
