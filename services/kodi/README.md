# AsterTV v2 lab release

The authoritative preserved lab candidate is
`dist/astertv-v2-lab-reconciled-2026-10-30-r15.tar.gz`. Production remains on
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

See `dist/ASTER-V2-RECONCILIATION-20261030.md` for the full repair record and
`dist/ASTER-V2-PROMPT-RECONCILIATION-20261030.md` for the prompt-by-prompt audit.
