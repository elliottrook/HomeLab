# AsterTV v2.0.7 release

The authoritative production release is
`dist/astertv-v2.0.7-production-2026-10-30-r18.tar.gz`. It is the reconciled
successor to the preserved r17 lab package and contains the exact Aster-owned
add-on snapshot accepted on the lab before production promotion.

The unpacked, reviewable final reconciliation is in `astertv-v2/reconciliation`.
It includes the bounded installer, hash-pinned payload, physical G20 keymap and
the focused Books/Music regression gate. Credentials and account tokens are not
included.

Run the complete preservation gate from the repository root:

```sh
PYTHONPYCACHEPREFIX=/tmp/astertv-pycache \
  python3 services/kodi/astertv-v2/validate_release.py
```

The gate fails if a payload byte, manifest hash, release archive, keymap route,
hero/fade invariant, stone-icon scope or dispatcher ordering changes. The
installer is lab-host-only, refuses active playback, checkpoints every changed
file, validates expected before/after hashes and restarts Kodi in a `finally`
path. Production promotion completed on 2026-10-30 from the immutable package;
the v1.1.1 add-on baseline remains in the production checkpoint for rollback.

## Physical OK regression fixed in r8

The G20 receiver emits Linux `KEY_SELECT`. Kodi resolves that through the named
`<select>` keyboard mapping, not only numeric key 353. r8 carries the named,
numeric, Enter and Return mappings and dispatches the active Books/Music page
before any stale TV-series preview property. On 2026-10-30 a physical G20 OK
press was verified at Podcasts window `11120`, focus `500`; it opened the
selected show's episode list without starting playback.

## Books resume activation fixed in r9

The clean lab rebuild retained the restricted Audiobookshelf client but omitted
the non-secret progress activation marker, leaving the installed resume-capable
service in playback-only mode. r9 carries a mode-0600, AsterTV-only marker bound
to the expected restricted account fingerprint; credentials remain separately
provisioned and are never packaged. The release gate also requires the real-book
reader to retain exact sentence sample timing and the pinned Aster pronunciation
cleanup. Word or connected-phrase highlighting must not be claimed or enabled
until a future real-book timing pipeline passes the exact measured timing gate.

## Shared header and rail repair in r16

Clock, Search and the floating stone side rail now use the Media page's shared
translucent gold trim wherever all three controls appear. News renders this
chrome after its hero/content layers so the upper rail icons are no longer
washed out; Books no longer uses a separate opaque Search gold. Media and Smart
Home were hash-verified as already conforming. Music retains its own header
because it does not expose the same three-control pattern.

## Books and Requests rail layering repair in r17

Books and the acquisition page now render the unchanged shared stone rail after
their page content groups. This prevents Books rows from drawing through an
expanded rail and prevents the Requests hero fade from washing out the upper
collapsed icons. Both collapsed and expanded states were captured directly on
the lab; Requests data, controls and routes are unchanged.

## Release reconciliation and production candidate in r18

The Requests/Seerr flow now opens recommendation artwork directly into a
separate details stage, permits direct multi-season selection, preserves focus
while toggling seasons and exposes one final Request control. The acquisition
page no longer has the obsolete intermediate Request button. Music uses the
Media-style gold Search, compact dark category group, shared gold clock and
floating stone rail; all category labels fit and the legacy green underline is
removed. The package installs the existing 1920x1080 AsterTV artwork as Kodi's
supported profile splash at `/storage/.kodi/media/Splash.png`.

The production promoter refuses active playback, validates all 577 snapshot
files, excludes credentials and `addon_data`, preserves production profile and
audio settings, checkpoints every replaced add-on plus keymap and splash, and
automatically restores the checkpoint if Kodi does not remain active.

See `dist/ASTER-V2-RECONCILIATION-20261030.md` for the full repair record and
`dist/ASTER-V2-PROMPT-RECONCILIATION-20261030.md` for the prompt-by-prompt audit.
