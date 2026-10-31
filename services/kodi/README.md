# AsterTV v2.0.7 release

The authoritative production release is
`dist/astertv-v2.0.7-production-2026-10-31-r48.tar.gz`. It preserves the complete
accepted v2 snapshot and reconciles the production Search/movie-return, Aster
busy mark, Settings/screensaver, exclusive HDMI passthrough, HDR and Aster-style
Resume prompt fixes.

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
hero/fade invariant, stone-icon scope, dispatcher ordering or exclusive-HDMI
contract changes. The production promoter refuses active playback, checkpoints
every changed file and prior audio/service state, validates expected hashes and
restores add-ons, PulseAudio state and audio settings on rollback. The v1.1.1
add-on baseline remains in the production checkpoint for rollback.

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
files, excludes credentials and `addon_data`, preserves production profile,
checkpoints every replaced add-on plus keymap and splash, and automatically
restores the checkpoint if Kodi does not remain active. r19 also captures the
exact pre-deployment audio settings and reapplies/verifies them after Kodi is
ready, preventing Kodi 22's known early-start HDMI fallback from silently
replacing the audible HDMI 0 route.

See `dist/ASTER-V2-RECONCILIATION-20261030.md` for the full repair record and
`dist/ASTER-V2-PROMPT-RECONCILIATION-20261030.md` for the prompt-by-prompt audit.

## Production close-out in r46

Media and shared Search pills now dispatch directly under the G20 keymap. Search
opens native movie details, returns there after playback and returns to its
result cursor on Back. Kodi starts with PulseAudio inactive and both normal and
passthrough routes pinned to ALSA HDMI 0 before capability enumeration. Physical
production acceptance confirmed E-AC-3 raw passthrough (`AES0=0x06`), TV/receiver
Dolby indication and HDR10 signalling. The deterministic r46 archive SHA-256 is
`0ee3331bbdb9ef34196e08b057b1a535dfb1893322d9c985d771ded2281753eb`.

## Resume presentation reconciliation in r47

The residual Kodi full-screen stone Resume chooser is replaced by the accepted
Aster Skip Intro/Recap player language: the same bottom-right footprint, dark
green canvas, horizontal remote flow, typography and sage/ivory focus ring.
Kodi still owns the Resume and Start-from-beginning actions. The release gate
pins the geometry, palette, control orientation, family-manifest hash and
absence of the abandoned full-screen dimensions. The deterministic r47 archive
SHA-256 is
`d979a42fca62fac3dac00a456b4790229c5907f9636942cc4cee6ee46f1cd226`.

## Full-colour Genre artwork in r48

Media Genre posters no longer carry the translucent ivory overlay that made
them look washed out. Their artwork remains full colour and is distinguished
with a persistent thin sage edge and charcoal title ribbon; focus changes the
edge to gold and strengthens the ribbon. Panel IDs, preview sources, Browse
actions and directional navigation are unchanged and regression-pinned. The
deterministic r48 archive SHA-256 is
`76b8fc4a3171013250a5088b3ced777940d5cfb0637f3eeba9794a7be3e6ac5a`.
