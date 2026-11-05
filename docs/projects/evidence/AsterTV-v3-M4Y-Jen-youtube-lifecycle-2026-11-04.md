# AsterTV v3 M4Y Jen YouTube/lifecycle evidence — 2026-11-04

## Result

The household YouTube identity and accepted M4 YouTube page are retained on
`AsterTV-Jen` (`192.168.1.180`). Jason can open the signed-in official YouTube
7.4.4 root, Subscriptions, Recommendations, Watch Later and Search. Guest has
no YouTube mapping or entitlement; switching to Guest disables the official
add-on and a direct private-route attempt is diverted to News.

The startup defect was concurrent private feed loading. Three unconditional
`<content>` providers requested Subscriptions, Recommendations and Watch Later
whenever the general Video/Media window opened. On the low-spec client these
requests competed with the official root and Python UI helpers, producing
missing-plugin errors and reproducible Kodi crashes. The retained design has
zero unconditional providers: the official root is one request, and each
personalized route is opened only by its selected pill. The root helper now
only waits for a stable official container and sets focus; it never reads a
second directory or mutates Kodi controls.

## Identity and privacy boundary

- Bedroom was used only as the read-only, owner-confirmed household identity
  source; Family was not contacted and neither source was changed or restarted.
- Only `access_manager.json`, `api_keys.json` and `settings.xml` were transferred
  directly to Jen. Values were never printed or written to Git.
- The three live files are root-owned mode `0600`; the live directory is mode
  `0700`.
- The local registry stores only
  `local:youtube:sha256:<opaque-user-id-hash>`. It contains no token, API key,
  client secret or account name.
- Jason has the `youtube` mapping and `personal_youtube` entitlement. Guest has
  neither. The official add-on is disabled whenever Guest is active and enabled
  again only after returning to Jason.
- The temporary staging directory was removed after reboot acceptance. Recovery
  remains available through the bounded pre-install checkpoint and the live
  add-on state; no second staging copy remains.
- A true Guest YouTube account is deliberately not claimed. YouTube 7.4.4 uses
  one userdata directory, so isolated Guest support requires a separate Kodi
  profile or credential-free adapter.

## Installed lifecycle

- Checkpoint: `/storage/.aster-checkpoints/astertv-v3-m4y-jen`.
- Stable candidate: `/storage/.aster-v3/m4y`.
- Boot unit: `astertv-v3-m4y-jen.service`, ordered after the M4 Movie overlay
  and before `kodi.service`.
- The accepted 528-file v2 guard runs first, restores its frozen baseline, M4
  reapplies Movie changes, and M4Y reapplies the YouTube/lifecycle changes.
- The installer accepts an exact interrupted/resumed overlay and exposes an
  explicit `--rollback` path pinned to the checkpoint and hostname.
- Kodi's stop override first returns to Home, waits for Aster-owned Movie,
  Series and Digest state to quiesce, then requests `Application.Quit`. It is
  bounded and retains systemd's existing TERM fallback; it never uses SIGKILL
  or starts an independent Kodi process.

## Live acceptance

1. A normal Kodi restart completed with `Result=success`, zero automatic
   restarts and no segmentation/corruption record. `Application.Quit` did not
   exit Kodi inside 25 seconds, so the recorded outcome was the bounded TERM
   fallback rather than a false graceful-success claim.
2. A full host reboot completed. The release guard restored 528 accepted files,
   M4 and M4Y ran in order, Kodi became active, and no systemd unit failed.
3. After reboot, the registry remained active as Jason; Jason retained the
   YouTube mapping/entitlement and Guest retained neither.
4. The three old startup content providers each counted zero. Ordinary startup
   produced no private YouTube `GetDirectory` or missing-plugin error.
5. The signed-in root opened and logged `AsterYouTubeRoot: signed-in root ready`.
   A serialized post-reboot Subscriptions request completed while Kodi remained
   active with `NRestarts=0`.
6. Before reboot, sequential Subscriptions, Recommendations and Watch Later
   requests each returned 51 items with thumbnails. No parallel request was
   used.
7. Search opened Kodi's keyboard. Cancelling an empty prompt leaves Kodi active
   but YouTube 7.4.4 logs an internal `bool.startswith` error; entered searches
   had already passed in the accepted page testing. The cancellation defect is
   recorded rather than treated as a startup failure.
8. Guest switching disabled the add-on. A direct Subscriptions route attempt
   landed on News; returning to Jason re-enabled the add-on.

## Rejected implementation and regression control

An initial helper attempted to populate the three personalized rails by calling
the official add-on concurrently and replacing Kodi control contents. That
reproduced the crash and was discarded. The final helper is guarded by tests
that reject `Files.GetDirectory`, `addItems`, token fields or execution outside
the exact YouTube root. The XML transform rejects missing anchors and removes
only the three pinned unconditional providers.

All 147 discoverable v3 regression tests pass. This includes 37 top-level
integration tests, 30 account tests, 15 Aster-client tests, 12 contract tests,
11 low-spec tests, 11 reliability tests, eight Guest-catalogue tests, eight M4
tests, seven Bedroom Wi-Fi tests, four candidate tests and four News-repair
tests. The target-pinned live HEVC harness is not a unit test and was not run on
the Mac workspace. The low-spec suite required only a sandbox-safe Python
bytecode-cache path.

## Residual constraint

Jen's Kodi 22 build still does not honor `Application.Quit` within the bounded
25-second window, so restart/reboot takes roughly 30 seconds while systemd uses
its normal TERM fallback. The material startup failure is fixed: the fallback
no longer coincides with concurrent private-feed workers, and both restart and
reboot completed without the prior teardown crash. A future Kodi/LibreELEC
upgrade should retest native quit latency; the fallback must remain bounded and
crash-evidenced until then.
