# Aster TV Version 2 — Runtime integrity evidence

## 2026-10-26 — HP family manifest reconciliation 2

The HP lab client stopped opening grouped Search after the accepted Acquisition
Hub and Media top-rail changes advanced `1080i/Home.xml`. A read-only live audit
proved that the active family manifest still described the older Home file:

- predecessor family manifest SHA-256: `de5a22f20d6f4be2da5cdde22a7eb0159bb284feb33b315d8b9080518c8424c0`;
- expected Home SHA-256: `39b10fcac446626d3decd89e22cd8dda95b5ee50f9b5de489cb5f67f579a0834`;
- accepted active Home SHA-256: `4c118dd42c3d97c1899a0dcbdce8e6ab42b22d3f309c09802f1a861fac9f830d`;
- component mismatches: none; and
- other guarded skin mismatches: none.

The repair advances only the family metadata for that exact accepted Home file.
The second-generation installer verifies before mutation that Home is the sole
predecessor mismatch, pins its own installer and native deployment wrapper,
retains the prior family manifest in a new recovery checkpoint, and verifies
every component and skin reference after the atomic replacement. It refuses an
extra component or skin mismatch before creating the checkpoint.

HP activation evidence:

- immutable stage: `/storage/.aster-staging/aster-family-manifest2`;
- stage manifest pin: `cd72221201cb54a12eeb4f61b8da56b1246028d56bc2c7d22f824ea1604224fc`;
- recovery checkpoint: `/storage/.aster-checkpoints/aster-family-manifest2`;
- resulting family manifest SHA-256: `c865df1863d8511a6685f491588746cfd255854ccc96ada4d2fbcf7b6dd66247`;
- independent install and verify results: passed;
- post-install component mismatches: none;
- post-install skin mismatches: none; and
- active playback during the operation: none.

Grouped Search then opened through its ordinary
`RunScript(script.asterruntime,aster-global-search-ui22,default)` route at native
window `11127`. A 4K screenshot is retained outside the repository at
`/private/tmp/aster-search-reconciled.png`; Search rendered its Library and
Catalogue tabs and the grouped media categories. It returned to Home with no
new Kodi `ERROR` or `FATAL` line.

The focused reconciliation suite passes six tests in normal and optimized
Python. The complete Kodi v2 suite passes 1,222 tests in both modes, with the
existing single Mac-only Pillow skip.

This evidence also identifies a release-composition rule: any future package
that changes `Home.xml` must derive and install a matching successor family
manifest from the exact active predecessor. Historical candidate manifests
must never be restored as payload alongside a later Home composition.

## 2026-10-26 — Current family recovery capture

The family recovery builder now includes a separate verified copy of every
skin file named by the active family manifest. Previously it validated all
twelve references but copied only the eight launcher files owned by its
rollback installer. The four Search dependencies now travel with the recovery
capture and are reconstructed and checked in the isolated rehearsal. Existing
rollback ownership remains eight launcher files; this change does not enlarge
the installer's write targets.

The current HP capture contains 67 runtime files, eight current/predecessor
launcher pairs, all twelve guarded skin dependencies and the current/predecessor
Jellyfin idle-callback guard. The runtime/component/shared hashes and all
guarded skin references match. No profile, credential, catalogue database,
listening progress, camera image or cache enters the capture.

- HP build and rehearsal root:
  `/storage/.aster-staging/aster-family-recovery-current1`;
- bundle manifest SHA-256:
  `dc77517df6e91cb4b0697593c7f0b5354f0bfa13327e7857a9cf1d81a2c3a1b6`;
- retained private archive on HP: `family-recovery-current1.tar.gz` (156 KiB);
- archive SHA-256:
  `d64ca7f6d5e51f3372c24e2c1925aed8d958610fa19b62aece815a9150ebcb9f`;
- Mac copy: `/private/tmp/aster-family-recovery-current1.tar.gz`;
- separate Mac rehearsal:
  `/private/tmp/aster-family-recovery-current1-verify/rehearsal`.

Both HP and Mac independently reconstructed the bundle and passed verification.
Thirteen focused recovery tests pass normally and with optimized Python,
including rejection of a changed Search dependency. This is a verified family
runtime recovery capture, not the whole-appliance production package: Music,
Books, acquisition, sound, idle, Reader, external services and hardware settings
retain their existing separate checkpoints. Kodi was not restarted or modified.

Search routing review confirmed that the existing **Search catalogue** route
provides typed Seerr title search, while the Acquisition Hub provides discovery
suggestions and explicit request actions. The existing routes are retained;
replacing typed catalogue search with a suggestion feed would remove accepted
functionality. The next safe work is checking ordinary search/navigation and
the common landing focus/rotation contract against this captured family.
