# Stream A F6 current-packet card validator — 2026-10-25

Result: **OFFLINE VALIDATOR READY; EXISTING PLATFORM CARD REMAINS NO-GO**

Stream A converted the exact host/V3 identities from the 22:48 installed
snapshot and the final M3 coordination receipt into a machine-readable
requirements fixture. A follow-up read-only inventory expanded the fixture to
the complete 38-path boundary: nineteen host composition modules, trusted
observer, five wrappers, five systemd units, two guest outcome files,
candidate-H launcher/unit, metadata-auth helper and three final M3 files. The
validator also requires the final M3 runner, scorer, journal-validator and
eleven-file packet-manifest identities, and rejects the known superseded
restore-observer and intermediate M3 manifest hashes.

The follow-up inventory ran from 00:03 to 00:04 PDT on October 26, before the
00:30 backup window. It used content-free `sha256sum` reads on Proxmox and in
LXC104/LXC110 only. The full wrapper and unit hashes matched the abbreviated
snapshot values, including corrected owner-heartbeat service
`7bbb32a6…4f1e`; both guests matched outcome wrapper `027183c9…dcb9` and
verifier `94086234…58e1`; candidate-H, the three final M3 files and the
metadata-auth helper matched their accepted hashes. The first LXC104 query
used two incorrect guessed outcome filenames and returned only file-not-found;
the fixed paths from the V3 installation card were then read successfully.
No file was changed and no service was started.

Five focused tests pass: a complete synthetic card is accepted; a missing V3
path, missing final M3 manifest, superseded digest and unknown requirements
schema are rejected.

Running the validator against the current platform-owned candidate-H card
fails as expected. The card omits the V3 composition paths, omits all four
final M3 identities and retains the superseded restore-observer and original
M3 manifest. This agrees with the independent prose review and provides a
repeatable acceptance check for the replacement card.

After expanding the installed snapshot to use every full path and digest, the
validator accepts the snapshot plus the final M3 coordination receipt as one
composite requirements source. This proves that the frozen review inputs are
internally complete under the same check that rejects the stale live card.

This is an offline review tool. It does not attest that the installed host is
unchanged after the inventory, publish the requirements to the platform owner,
arm F6, create a lease, stop a consumer or call a model. A replacement card
must still distinguish the two guests that share outcome-file identities,
pass independent review, and bind fresh F3–F5 evidence before live approval is
requested.
