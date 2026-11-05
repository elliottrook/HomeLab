# AsterTV v3 M8 — editable voice search and synchronized input

Date: 2026-11-05  
Scope: Aster Remote gateway/PWA and the Jen, Family and Bedroom outbound clients

## Outcome

Voice transcription now becomes an editable Search draft instead of firing an
immediate query. Terminal dictation punctuation (`. ! ? , ; :`) is removed only
from the end of a submitted search, so a recognized `Dark.` becomes `Dark`.
The user can correct or append text with the iPhone keyboard and then submit.

For Kodi text dialogs, the client consumes Kodi's documented
`Input.OnInputRequested` initial value and mirrors it through the already
authenticated owner/room session. The Remote displays that value, permits a
full-field update, and keeps the existing clear/backspace/cancel/enter actions.
The mirror is volatile only. Any input type containing `password` is reported
only as an active sensitive field: its title and value are forcibly empty at
the client and rejected by the gateway model if supplied.

## Recovery points

- Gateway/PWA:
  `/var/lib/aster/checkpoints/astertv-v3-m8-input-sync-20261105`
- Jen, Family and Bedroom, independently on each client:
  `/storage/.aster-checkpoints/astertv-v3-m8-input-sync-20261105`

## Validation

- 35 focused local tests, JavaScript syntax, Python parsing and `git diff
  --check` passed before deployment.
- Aster Agent restarted healthy; `/remote/` remained available and an
  unauthenticated session remained HTTP 401.
- Jen's existing slower graceful Kodi shutdown was allowed to complete; no
  force stop occurred and its checkpointed files were unchanged until shutdown
  finished.
- All three Kodi instances are active and idle with identical client service
  SHA-256 `1a4d52f3…cfbce` in both live and stable custody.
- Gateway module SHA-256 is `5bf83f5f…d389f`; live app JavaScript is
  `03e073d2…b320` and service-worker revision is `fdea1be8…54a7`.
- The gateway had the expected established room polls and none of the three
  current Kodi logs contained a Remote traceback.
- All Proxmox, LXC and client staging was removed after acceptance.

## Rollback/reinstall rehearsal

After explicit approval, Bedroom was rechecked idle and its accepted input-sync
client was restored to the exact checkpointed predecessor
`22e06499…207a`. Kodi restarted with the predecessor add-on enabled. The same
guarded operation then reinstalled `1a4d52f3…fbce` into live and stable custody,
rebuilt the stable manifest and restarted Kodi. The post-rehearsal three-room
Doctor probe passed and transient staging was removed. A rehearsal failure is
designed to restore the accepted input-sync version rather than leave the room
on its predecessor.

## Real-device acceptance still required

On the iPhone Remote, refresh/reopen once for shell v4. Speak `Search for Dark`,
confirm the field contains no final period, append or correct it, then submit.
Open a non-password Kodi text dialog containing an initial value, open More,
confirm the value appears, edit it and choose Update. A password dialog must
show only the private-field warning and no content.
