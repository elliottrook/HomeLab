# AsterTV v3 M7 — Bedroom disabled-first deployment preparation

Date: 2026-11-06 (America/Vancouver)  
Target: `AsterTV-Bedroom` / `192.168.1.140`  
Outcome: deterministic candidate and rollback runner complete; no live effect

## Fresh read-only client check

Bedroom again identified itself as `AsterTV-Bedroom`. Kodi was active with zero
restarts. Both the live and stable Remote service are the accepted predecessor
`c28bf36e9b99159b1ee5bf22ae4d83d90b0c53a557de2c236e6d1b05cfba5d49`;
neither tree contains `content_session.py`. No file, add-on, service, display or
playback state was changed.

## Candidate closure

The non-deploying candidate now contains all immutable code required for the
disabled-first sequence:

| Owner | File | SHA-256 |
|---|---|---|
| Aster Agent | `aster_remote.py` | `a804c06732b291275de830dcb0f8188ade5fc4fc3d0a557a86a742d1557cf1b3` |
| Home Assistant | `contract.py` | `2c927737a82312c4fa9707d980a9c2bb3b92ff974d8cbce929c52249d87be82a` |
| Bedroom Remote | `service.py` | `b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3` |
| Bedroom Remote | `content_session.py` | `a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb` |
| transient runner | `install_bedroom_publisher.py` | `c3980a7256d7109a14d5d7149b3925e991464b584708853af7a779e50dc83455` |
| transient runner | `install_aster_identity.py` | `2f4bc465b8b589743152cc3609f38a4b464dfac340093efd8972a109eb888ce8` |

The gateway input is Family's exact accepted live gateway `715b172a…73a`, not
the broader repository source. This preserves its accepted voice route and all
existing Family behavior while removing only the non-empty-action requirement.

The canonical materialization manifest is
`6852bc3ead1f50606c9d7f5942cc9df2b6abf5024420e7710cee946b76ffcee2`.

The Aster-side runner also pins the live `aster.env` predecessor
`038c8a1042a10678f7f3f920529fee37c2c2bfe42f4ba61b77519fcffd5dc4fc`.
It accepts a private mode-0600 transient key, preserves the exact `HA-Family`
identity and six actions, adds only `HA-Bedroom` with `actions: []`, and proves
the new identity through a content read that must return 204 before any Bedroom
publisher exists. Any failure restores the gateway and environment, removes
the new key, restarts the accepted service and deletes the transient input.

The read-only Home Assistant preflight pins live configuration
`f84f240070f0cb7c1d1e9a46732cd2d9fe833217cafe9d183102bb0d1d547cfd`
and accepted contract `ea42ebed…434f`. Its current Family-only block exactly
matches the accepted enabled profile. The effect step must convert that block
to `rooms`, preserve every Family value, add Bedroom with `actions: []` and no
`content_volume`, pass `ha core check`, then restart Core under its separate
configuration/component checkpoint. That live transformation is deliberately
not inferred or executed by the repository candidate.
It declares `deployment_authorized: false`, `equipment_actions: []`, excludes
credentials/configuration/live state, and fixes the order as Aster gateway,
Home Assistant content-only room, then Bedroom publisher.

## Client rollback runner

The Bedroom-only runner:

- rejects every hostname except `AsterTV-Bedroom`, non-root execution, active
  playback, changed source hashes, changed predecessor hashes, a pre-existing
  `content_session.py` or reused checkpoint;
- checkpoints live/stable service bytes and the stable manifest before change;
- disables only `service.asterremote`, updates both live and stable copies,
  recomputes the stable tree manifest and re-enables the add-on without
  restarting Kodi;
- verifies both installed files and enabled state; and
- on any exception restores both accepted service copies, removes only the two
  newly introduced session files, restores the exact manifest and re-enables
  the accepted add-on.

Offline success and synthetic enable-failure rehearsals both pass. The failure
rehearsal proves exact predecessor restoration and removal of the newly created
file.

## Regression gates

- Bedroom content candidate/installers: 9/9 passed.
- Home Assistant bridge: 20/20 passed.
- Remote client: 38/38 passed.
- Fleet/release: 54/54 passed.
- Fleet compile: three deployed appliances and one non-deployed Guest;
  composition hashes unchanged.

## Remaining effect gate

The next step is a live, checkpointed disabled-first rollout. It still needs a
fresh owner release of the Bedroom display and immediate authorization because
it will create a private room identity, update two shared services and reload
the Bedroom Remote add-on. The rollout must stop before any effect if playback
is active, any predecessor/hash differs, a checkpoint cannot be verified, the
exact HA-to-gateway path is absent, or rollback cannot be proved.

No equipment action or content-volume profile is part of that rollout. Bedroom
LG/CEC controls remain an independent later milestone.
