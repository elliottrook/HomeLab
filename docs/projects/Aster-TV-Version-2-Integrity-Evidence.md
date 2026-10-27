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
