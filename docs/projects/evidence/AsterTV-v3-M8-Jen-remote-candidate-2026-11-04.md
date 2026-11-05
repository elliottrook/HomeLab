# AsterTV v3 M8 Jen Remote candidate — 2026-11-04

Target: repository candidate, then Aster LXC 104 and `AsterTV-Jen` only  
State: credential-free candidate complete; subsequently installed under
SA-M8-JEN2 (see `AsterTV-v3-M8-Jen-install-2026-11-04.md`)

## Architecture

- `https://aster.elliottrook.com/remote/` is an installable PWA shell using the
  existing private HTTPS host and Aster app icon.
- Browser authentication uses the existing `aster-companion` public OIDC
  client with PKCE and an additive strict `/remote/` redirect. The candidate
  keeps only the access token in `sessionStorage`; it requests no offline scope,
  stores no refresh token and clears the session on sign-out or HTTP 401.
- Browser commands are exact semantic records: room, enumerated action,
  optional bounded text and an idempotency identifier. The gateway enforces
  same origin, authenticated owner-to-room assignment, 15-second expiry,
  at-most-once dequeue, 32-command queue and burst/ten-second rate limits.
- AsterTV-Jen maintains an outbound long poll over the already-approved
  Jen-to-Aster TCP 9120 path using an independent client key. No browser token
  or new inbound client listener reaches Kodi.
- The Kodi service translates only navigation, context, Home, Play/Pause,
  accepted Search and active-virtual-keyboard actions. It cannot call shell,
  arbitrary JSON-RPC, Home Assistant, destructive library methods, volume,
  mute or power.
- Voice Search records at most 15 seconds in the foreground and sends it to the
  existing local `/voice/v1/stt` route. Only the returned transient text enters
  the semantic Search action; audio and text are not cached or logged by this
  candidate. It produces no speech.

## User experience

The shell follows the accepted AsterTV black/brown, cream, green and muted-gold
language rather than introducing the discarded blue palette. It includes:

- room and connected/current-page/playback state;
- a large swipe/tap/hold touchpad and accessible five-button directional pad;
- Back, Home, Play/Pause and context controls;
- direct Aster Search using the native iPhone keyboard or local voice input;
- separate active-Kodi-keyboard Send, Backspace, Clear, Cancel and Enter;
- safe-area, phone-width, keyboard and non-colour status treatments; and
- visibly disabled volume, mute and power controls explaining the M7 boundary.

The service worker caches only the static shell, CSS, JavaScript, manifest and
icon. It does not intercept or cache `/v1/`, `/voice/`, sessions, household
state, media data, camera images or typed text.

## Validation

- 5 FastAPI/Pydantic protocol tests passed inside LXC 104's pinned Aster venv,
  using only temporary credential-free source. They cover room/origin/identity
  denial, exact command shapes, independent client authentication,
  at-most-once delivery, idempotency, content-free state and absence of
  equipment/shell/general-RPC actions.
- 6 PWA static/privacy/style tests, 6 Kodi-client safety tests and 3 wrapper
  integration tests passed locally.
- `node --check` passes for both application and service-worker JavaScript.
- Python compile and XML parse checks pass; the candidate contains no key,
  subject hash, credential value or real typed/media content.

## Live gate and rollback plan

Before deployment, verify and checkpoint the live Authentik provider redirect
set, Aster wrapper/module/environment and Jen add-on/registry/release-guard
state. Generate the client key source-locally and transfer it without model or
Git output. Install only the additive redirect, router/static files and Jen
service, then validate wrong origin, wrong owner/room/client, expired/replayed
command, Kodi/bridge outage and foreground reconnect before real iPhone input.

Rollback removes only the `/remote/` redirect, remote router/static files and
Jen service/key, restoring exact predecessor hashes and service state. Existing
Companion, Aster intent, voice, Kodi, Family and Bedroom paths must remain
independently healthy throughout.
