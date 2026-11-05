# AsterTV v3 M8 Jen Remote installation — 2026-11-04

Target: Authentik LXC 106, Aster LXC 104 and `AsterTV-Jen` only
State: SA-M8-JEN2 installed and transport-validated; real iPhone acceptance pending

## Installed boundary

- Authentik provider `Aster Companion` remains a public client with the existing
  reauthentication/passkey and explicit-consent flows. Its two predecessor
  strict redirects were checkpointed at
  `/data/aster-checkpoints/aster-remote-redirect.json`; the only addition is
  strict authorization redirect `https://aster.elliottrook.com/remote/`.
- Aster Agent checkpoint
  `/var/lib/aster/checkpoints/astertv-v3-m8-jen` retains the exact predecessor
  wrapper and absence of the new module, static shell, environment and drop-in.
  The independently revocable Jen key and owner-to-room assignment are held only
  in mode-0640 `root:aster` environment custody. The separately checkpointed
  pre-header module is retained below that checkpoint at
  `post-install/aster_remote.py`.
- Jen checkpoint `/storage/.aster-checkpoints/astertv-v3-m8-jen` retains the
  exact `Addons33.db` bytes and predecessor absence of the add-on, key, stable
  source and unit. `astertv-v3-m8-jen.service` runs after M6 and before Kodi,
  reapplying only the manifest-bound `service.asterremote` add-on. The client
  key is mode 0600 under `/storage/.aster-private`.

The v2 release guard was not weakened or repinned. It restores its accepted
roots first; M4 through M8 then reapply their independently checkpointed v3
overlays in order. The M8 add-on is outside the guard's enumerated roots.

## Fail-safe evidence

Two implementation defects were detected without broadening scope:

1. Authentik rejected `save(update_fields=["redirect_uris"])` because its
   redirect list is a serialized property rather than a concrete Django field.
   The transaction rolled back; a read-only verify proved exactly the original
   two redirects remained. The corrected normal model-save path then installed
   and verified all three strict redirects.
2. Jen's first install found its private parent directory already present.
   The exception path disabled the not-yet-installed unit, restored the add-on
   database to its checkpoint hash, removed all four newly absent targets,
   restarted idle Kodi and deleted the transient input key. After changing only
   directory creation to `exist_ok=True`, the same checkpointed install passed.

The initial macOS archives also exposed AppleDouble `._` files during staging.
They were discarded before activation, rebuilt with metadata suppression and
re-audited to an exact intended file list.

## Validation

- 27 local static, installer, privacy, client and integration gates pass; both
  JavaScript files pass `node --check` and all Python/XML sources parse.
- Six protocol/header tests pass in Aster's pinned FastAPI/Pydantic runtime.
- Public `/remote/` returns HTTP 200 and `/v1/remote/session` without a token
  returns 401. Legacy `/companion` remains HTTP 200.
- The exact OIDC authorization request for `/remote/` enters the existing
  reauthentication flow. Token preflight permits only
  `https://aster.elliottrook.com` for the required POST/content-type exchange.
- The shell returns CSP with self-only scripts/styles/workers/assets, exact
  Authentik connect permission, no object/base/frame/form authority, plus
  microphone-only Permissions Policy, no-referrer, nosniff and frame denial.
- Aster Agent and Jen Kodi are active. Jen's add-on is enabled, playback is
  idle, no failed Jen units exist and Aster observes an established Jen-to-Aster
  TCP 9120 long poll after the header restart.
- The existing Companion route and non-M8 Aster service remained healthy. LXC
  104's unrelated pre-existing `homelab-bundle-health.service` failure was
  observed and left outside this milestone.
- Transient key inputs on the Mac, Proxmox, Aster `/run` and Jen `/run` were
  removed. No key, owner hash, token, typed text or media content entered Git or
  evidence output.

## Remaining gate

SA-M8-JEN3 needs Jason's real iPhone to complete passkey login, Add to Home
Screen, swipe/tap/hold, Back/Home/Play-Pause, direct search, symbols/paste,
active-Kodi-keyboard Send/Clear/Cancel/Enter, microphone permission, rotation,
sleep/reconnect and visible wrong-state/expiry behaviour. Volume, mute and power
remain disabled until M7 creates room-equipment authority.
