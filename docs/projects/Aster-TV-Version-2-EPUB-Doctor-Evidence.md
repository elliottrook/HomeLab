# AsterTV v2 — compiled EPUB Doctor evidence

Updated: 2026-10-27. Status: HP successor active and verified.

## Outcome

Settings → Diagnostics now includes a compact **Books narration** panel. It
reports whether the separately compiled EPUB reader is usable without offering
any repair action. The panel checks the exact reader activation and bundle pin,
both enabled/active automounts, the fixed host-restricted NFS sources, required
`ro,nosuid,nodev,noexec` options, every bounded ready pointer and each referenced
generation manifest hash. A failed title retains the existing Calibre fallback.

The check does not mount, remount, enable, restart or modify anything. It holds
no compiler, Calibre, NFS or service credential and cannot inspect compiler
queue/work/failure state.

## Recovery and regression evidence

- The immutable v6 diagnostics source pin is
  `c72d2bdb02733210c62792bba49862acdb5ef48e889a95f78cfe7794e6370827`.
- The exact family successor pin is
  `05662c68d173a8770ad06ce3ef7073e082601bd9c54919551891519b03484e0f`.
- The accepted HP stage is
  `/storage/.aster-staging/aster-epub-doctor2-candidate`; checkpoint
  `/storage/.aster-checkpoints/aster-epub-doctor2` retains the complete prior
  v5 component plus the original dispatcher, family manifest and Settings page.
- Isolated rehearsal passed install, verify, rollback and post-rollback verify.
  The first HP candidate safely reported unavailable because family composition
  had rewritten the separately pinned reader path; it was rolled back exactly.
  The corrected transformation preserves that external reader boundary and the
  failed checkpoint remains as evidence.
- The complete Kodi v2 suite passed 1,303 tests normally and with optimized
  Python, with the existing one platform-only skip.
- A bounded Kodi restart loaded the successor. Native Settings navigation opened
  the panel and reported `Ready`, two compiled publications, both publications
  read-only, and local narration. Exact post-restart verification passed, no
  player remained active and no new error/fatal event was logged.

Production remains unchanged. The final all-component release/recovery package
must include this accepted family successor and the existing compiled-reader
consumer installer; that release assembly remains a later milestone.
