# AsterTV v3 M8 Remote reskin — 2026-11-05

Target: private Aster Remote on Aster LXC 104  
State: installed; real iPhone visual acceptance pending

## Outcome

The authenticated Aster Remote shell now uses the owner-approved touch-first
AsterTV treatment:

- one AsterTV/Remote identity at the top and a clickable controlled-AsterTV
  selector at the bottom;
- a brown/black field with a stronger stone/cream centre that blends beneath
  the Search surface;
- an icon-only AsterTV primary-control rail for Back, Home, Play/Pause and More;
- a large borderless swipe/tap/hold navigation surface;
- Aster green/gold selected state and restrained stone surfaces; and
- a More sheet retaining the directional pad, Kodi keyboard input, explicit
  unavailable equipment controls and sign-out.

No command, authentication, room-assignment, voice, client, Kodi or equipment
authority changed. The existing short-lived browser session, British-English
voice profile, semantic command allowlist and owner-to-room boundary remain
unchanged.

## Recovery boundary

The live predecessor exactly matched commit `964582bd` before mutation. The
hash-bound installer saved its four static files at:

`/var/lib/aster/checkpoints/astertv-v3-m8-remote-reskin-20261105`

It then atomically replaced only `index.html`, `styles.css`, `app.js` and
`sw.js`. No service or Kodi restart occurred. Any install or HTTP validation
failure automatically restores the checkpoint.

Installed hashes:

- `index.html` — `66dd4cb297431268e52849e40c1bc9d710b5dfdf59fded06ce322d30107a1fba`
- `styles.css` — `fd6fe2d6dfb05ef78f56006150af5f6ec499110813bbf65f62928d6ff684ff43`
- `app.js` — `420e47015e9dd5fcfb1ef0934381597acbeb313d0375a56a1b3791693a673258`
- `sw.js` — `3c54a84f9294aec06a86189e750b3b850e02ea3ad88522f5a43e97e097285c58`

The service-worker shell cache advanced from `v1` to `v2`, so the installed
Home Screen app can replace the predecessor assets without retaining the old
face.

## Validation

- 19 focused static, privacy, original installer, header installer and reskin
  installer tests passed locally.
- Both JavaScript files passed `node --check`; Python parsed with a sandboxed
  bytecode cache; `git diff --check` passed.
- Live Aster Agent remained active throughout.
- The private HTTPS `/remote/` route returned the exact installed HTML hash and
  HTTP 200 with the established CSP, microphone-only Permissions Policy,
  no-referrer, nosniff and frame-denial headers.
- Unauthenticated `/v1/remote/session` remained HTTP 401.
- The live static file hashes match the local candidate exactly.
- All transient Proxmox and LXC staging files were removed.

The backend FastAPI protocol was not modified. Its previous pinned-runtime
acceptance remains applicable; the locally unavailable FastAPI import is not
represented as a new protocol run.

## Remaining acceptance

Jason should close and reopen the installed Aster Remote, then check the main
touch surface, icon-only primary controls, Search, More sheet and bottom room
selector. A second close/reopen may be needed only if iOS had the previous
service worker active during the first launch.

## Follow-up room-control layout — 2026-11-05

Jason accepted the touch-first reskin and requested the remaining lower-screen
space be used deliberately. The live follow-up now:

- uses the accepted plain Aster compass and AsterTV wordmark instead of the
  application/side-rail stone treatment;
- represents connectivity as a green/red dot with a non-visual status label;
- replaces the microphone glyph with the approved thin five-beam waveform,
  animated only while capture is active;
- removes the redundant current-page/playback line below the selected room;
- enlarges the stone/cream navigation field; and
- groups Volume Down, Mute and Volume Up together while separating Power as a
  distinct equipment action.

The four equipment controls are present but remain disabled and carry no
`data-action`; the M7 bridge has not been implemented or implied by this visual
change.

The first static-only attempt encountered the backend's deliberate exact asset
allowlist when the compass route returned 404. Its installer automatically
restored all four predecessor files; live hashes proved the rollback was exact.
The retained failed-attempt checkpoint is
`/var/lib/aster/checkpoints/astertv-v3-m8-remote-room-controls-20261105`.

After explicit approval for a brief Aster Agent restart, revision 2 jointly
checkpointed the backend and static shell at
`/var/lib/aster/checkpoints/astertv-v3-m8-remote-room-controls-20261105-r2`,
added only exact route `/remote/aster-compass.png`, installed the shell and
restarted Aster Agent. The final backend/static hashes match the repository;
Remote, Companion and the compass route return HTTP 200; unauthenticated session
remains 401; CSP and all other browser security headers are unchanged. Twenty-
four focused local tests pass. No Kodi or AsterTV client restarted, and all
transient staging files were removed.
