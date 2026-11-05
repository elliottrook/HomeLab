# AsterTV v3 M3 Jen broker/client evidence — 2026-11-04

## Outcome

The bounded `SA-M3-JEN` broker and client are retained on AsterTV-Jen. Aster
LXC 104 exposes a dedicated, independently revocable structured-intent route;
Jen holds its key at `/storage/.aster-private/astertv-broker.key` with mode
`0600`. The general whole-home Aster identity, arbitrary model tools, shell,
arbitrary Kodi JSON-RPC and arbitrary Home Assistant service calls are not
available through this route.

The retained client is `script.astertv.voice` 3.0.0. It uses the accepted
compact Aster command card for direct actions and the accepted large Aster
search treatment for browseable results. The active Jason registry gained only
the opaque `aster_tv` mapping and `aster_tv_commands` entitlement. Restricted
Guest retained only its dedicated `jellyfin_guest` mapping and cannot call the
broker.

## Checkpoints and rollback

- Aster pre-install: `/var/lib/aster/checkpoints/astertv-m3-pre-r2-20261104`
- Aster retained install: `/var/lib/aster/checkpoints/astertv-m3-retained-r3-20261104`
- Jen initial client: `/storage/.aster-checkpoints/astertv-v3-m3-jen-client-pre-r1-20261104`
- Jen rollback rehearsal source: `/storage/.aster-checkpoints/astertv-v3-m3-jen-client-pre-r2-20261104`
- Jen retained client: `/storage/.aster-checkpoints/astertv-v3-m3-jen-client-retained-r3-20261104`

The Aster route was installed, rolled back to HTTP 404 while the base Aster
service remained active, and reinstalled. The Jen r2 client was rolled back;
the prior registry had no `aster_tv` mapping and the accepted 528-file guard
remained clean. The same candidate was then reinstalled as retained r3.

## Tests and live proof

- 52 local client/account/contract/installer tests passed.
- Seven broker grammar/authentication/replay/audit tests passed inside Aster's
  own virtual environment.
- Live broker smoke proved wrong-key `401`, Guest `403`, valid Jason `200` and
  the expected `media.search` response without credential output.
- A synthetic `find dark` request loaded the large Aster dialog with real local
  art/results. View-all preserved `dark` and focused the matching full Search
  result.
- Selecting a synthetic TV result opened the accepted series/season page.
- `play 3rd Rock from the Sun` started the selected primary episode through the
  accepted series controller. It was stopped deliberately; both native queues
  were empty and no recovery fence existed.
- `play the news` started the current digest as Kodi audio through the accepted
  digest controller. It was stopped deliberately and no player remained.
- A private page command without its profile identity/entitlement is shown as
  unavailable and does not navigate. This was observed for Cameras because Jen
  has no Home Assistant identity.
- Final state: Kodi active and idle; `script.astertv.voice` enabled; Aster agent
  active with `astertv_with_delegation:app`; Jen release guard clean at 528
  files; private key mode `0600`.

## Deferred sub-gates

- No G20 microphone/receiver is attached to Jen. The browser-search key now
  resolves through the profile gate to `script.astertv.voice`, but an invocation
  without a captured utterance reports that capture is not connected. Synthetic
  text is the tested capture adapter.
- No exact Home Assistant alias and confirmation policy was approved. The
  broker has an empty live alias table; unknown aliases deny, and the client
  has no unrestricted HA credential. Camera/Home page navigation also remains
  denied until the profile receives a separately resolved HA identity.
- A selected movie preview hands off to the existing full Search page because
  the accepted movie controller admits detail pages only from its guarded
  library/search source. That guard was preserved rather than bypassed.

## Credential cleanup

Temporary copies were removed from the Mac, Proxmox and Jen staging. The live
Jen credential and Aster environment custody remain; no secret, raw profile
identifier, utterance or viewing history is stored in Git or emitted by the
broker audit log.
