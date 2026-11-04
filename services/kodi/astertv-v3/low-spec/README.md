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
gate pass; do not copy Family or Bedroom tokens. The helpers in this directory
implement the tested AsterTV-Jen provisioning path:

- `provision_jellyfin.py` uses Jellyfin Quick Connect to create a distinct
  device ID and access token for the existing production user. The companion
  `authorize_jellyfin.py` authorizes the displayed code with an already signed-
  in production session without printing either token.
- `issue_audiobookshelf_key.js` creates a named, per-device API key through the
  supported Audiobookshelf API; `install_audiobookshelf_key.py` installs it and
  the read-only catalogue settings on the client.
- `provision_seerr_identities.py` and `resume_seerr_identities.py` add a second,
  independently revocable client token to the existing request broker while
  preserving the production clients' token. They do not submit a request.
- `apply_home_delivery_low_spec.py` extends the existing Home Assistant forced-
  command publisher to the low-spec receiver. `allow_low_spec_access.py` and
  `allow_low_spec_nfs.py` make the exact firewall and read-only NFS additions.
- `enable_low_spec_runtime.py` extends only the accepted runtime host gates;
  `install_actor_search.py` installs the exact three-file production actor
  search add-on after the first Jellyfin sync is quiescent.

All client secrets are mode `0600`. Durable server-side secret custody is
outside this repository. YouTube authorization is deliberately separate, and
the television must not receive the general whole-home Aster API key: M3 first
needs a search-only identity and broker contract.

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
This qualification installed the exact three-file production actor-search
component after Jellyfin synchronization and refreshed the live AsterTV-Jen
baseline to 528 mandatory files; the current snapshot has no missing-root
exception.

See `EVIDENCE-2026-11-04.md` for measured qualification, backend and credential
proof, rollback evidence and the production-equivalence verdict reported to v3.
