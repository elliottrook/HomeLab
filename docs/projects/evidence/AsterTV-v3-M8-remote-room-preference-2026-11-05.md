# AsterTV v3 M8 — Remote last-room preference

Date: 2026-11-05

## Scope

Retain the last AsterTV selected in the Aster Remote PWA instead of returning to
the first authorized room whenever the app opens. This change is limited to the
gateway's static `app.js` and `sw.js`; it changes no room authority, credential,
command, television client, equipment bridge or playback state.

## Privacy and failure boundary

The browser stores only the opaque room ID under
`aster_remote_last_room_v1`. Search text, dictated text, Kodi input and all
credentials remain unpersisted. A stored value is accepted only after it
matches a room in the current authorized session. A removed or unauthorized
room therefore falls back to the first currently authorized room. Browsers
that deny local storage continue to work with the former default behavior.

## Deployment

Read-only preflight proved that the live files exactly matched the expected
predecessor:

- `app.js`: `c4b3b371c18a7b3f53dad298ad8440f303b47f8c9c96cafbbb5c4c364e0df52b`
- `sw.js`: `4011c0bd123a743937a6d9053ad44d1da15c7ac646ddc50cbf401b38cbd94968`

The bounded installer created checkpoint
`/var/lib/aster/checkpoints/astertv-v3-m8-remote-room-preference-20261105`,
atomically replaced only those two files and performed no service restart. The
v8 shell cache forces installed PWAs to acquire the new JavaScript. Accepted
live hashes are:

- `app.js`: `76a14595af2da756a72975eb02afe45cd21ac035d8b118dfc67a2635258e0762`
- `sw.js`: `9be36dd12a332cf22c71c3364479b23623b2a10abb07b8be0a5f8c27bc0f2bc8`

All transient staging was removed after validation.

## Verification

- JavaScript syntax checks passed for the application and service worker.
- Twenty-two focused static, room, reskin and transactional-installer tests
  passed.
- The public route serves `aster_remote_last_room_v1` and the v8 shell.
- The direct session route remains HTTP 403.
- The content-free Aster Remote Doctor passed the gateway and all three room
  identities, enabled clients, private key modes and stable/live manifests.

Physical reopen acceptance remains useful but is not required for rollback:
select a room other than Bedroom, close the installed PWA, reopen it and confirm
the same room is selected. Clearing Safari site data intentionally resets the
preference.

## Recovery

Run the dedicated installer with `--rollback` on `hermesagent`. It requires the
accepted live hashes, restores only the two checkpointed files and revalidates
their HTTP bytes plus the direct HTTP 403 authorization denial.
