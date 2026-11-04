# AsterTV-Jen low-spec baseline harness

This host-bound wrapper installs the accepted, credential-free AsterTV v2.0.7
release on `AsterTV-Jen` without changing the immutable release archive or
pretending the client is Family or Bedroom. It verifies the original promoter
hash, then selects the promoter's non-Family path so the client's existing
audio route is checkpointed and restored rather than replaced with Family's
Dolby/passthrough profile.

The release archive must remain
`astertv-v2.0.7-release-2026-10-31.tar.gz`, SHA-256
`e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`.
The wrapper is intentionally bound to the exact extraction path under
`/storage/.aster-staging` and to hostname `AsterTV-Jen`.

Credentials and `addon_data` are outside this baseline. Provision each backend
with a dedicated low-spec-client identity after the code baseline and rollback
gate pass; do not copy Family or Bedroom profile data.

`install_production_addons.py` installs the exact code-only Jellyfin/YouTube
dependency closure read from Family. Its 683-file canonical digest excludes
Python caches and covers every copied byte. The installer rejects symlinks,
unexpected directories, versions and pre-existing targets; checkpoints Kodi's
add-on database and GUI settings; restores them on failure; and activates the
Aster skin only after every dependency registers and enables successfully.

`install_reliability.py` is the host-bound M1 adapter for the existing v3
accepted-release guard. It pins the reviewed installer bytes, authorizes only
`AsterTV-Jen`, and leaves the Family/Bedroom installer allow-list unchanged.
The guard snapshots six of the seven Aster runtime add-ons and restores drift
before Kodi starts; it does not read or copy user profiles or backend tokens.
For the accepted v2.0.7 baseline it explicitly permits the absent
`plugin.video.astersearch` root: that v3-alpha component exists on production
clients but is not in the accepted v2 archive. The other six guarded roots
remain mandatory; accepting a later v3 candidate must refresh the baseline.

See `EVIDENCE-2026-11-04.md` for the measured qualification, backend boundary,
open screensaver defect and production-equivalence verdict reported to v3.
