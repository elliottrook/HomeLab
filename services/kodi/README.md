# AsterTV v2 lab release

The authoritative preserved lab candidate is
`dist/astertv-v2-lab-reconciled-2026-10-30-r17.tar.gz`. Production remains on
the stable v1.1.1 release and is not changed by this record.

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
path. Promotion to production remains a separate owner-approved operation.

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

See `dist/ASTER-V2-RECONCILIATION-20261030.md` for the full repair record and
`dist/ASTER-V2-PROMPT-RECONCILIATION-20261030.md` for the prompt-by-prompt audit.
