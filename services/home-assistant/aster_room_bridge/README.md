# Aster Room Bridge candidate

This Home Assistant custom component is the outbound-only half of the M7 room
equipment bridge. It polls the private Aster gateway and translates only the
locally configured action allowlist into fixed `media_player` services and
entity IDs. The gateway cannot choose a Home Assistant service or entity.

Each room candidate is intentionally limited to fixed entities and an explicit
action allowlist. Family uses:

- TV power: `media_player.family_room_tv`;
- receiver volume/mute: `media_player.tx_rz30`;
- actions: explicit power on/off, volume up/down and mute on/off.

Bedroom uses its accepted LG webOS entity for both power and volume/mute. The
LG is expected to forward volume and mute through the existing HDMI ARC/eARC
SIMPLINK/CEC chain; this is not accepted until one bounded live step proves
fresh feedback, one audible transition and no duplicate CEC command.

The client key lives in a separate regular file with no group/other permission.
It is not placed in YAML, source, logs or the browser. Home Assistant initiates
all traffic to `/v1/remote/equipment/{poll,ack}`; the component opens no inbound
port and registers no general Home Assistant service.

The repository candidate also polls `/v1/remote/equipment/content` with that
same room-scoped identity. The response is a strict, 30-second content-free
observation containing only playback state, coarse class, Aster page,
screensaver state and ephemeral session/sequence metadata. It is retained only
in `hass.data` as current volatile state: the component creates no sensor,
event, recorder row or viewing-history log. Duplicate reads are idempotent;
stale, malformed, replayed or wrong-room observations fail closed. Family's
coordinated path and exact profile were accepted live on 2026-11-06; Bedroom
remains disabled pending its independent deployment gate.

Rolling upgrades preserve the accepted controls. A new Kodi client retries
once without the optional content envelope when the predecessor gateway rejects
it, then keeps that envelope disabled until service restart. A component that
finds the predecessor gateway's content endpoint absent disables content
polling while continuing the already accepted equipment poll. Other malformed
or unavailable content responses are isolated from power/volume/mute; they
never widen authority or produce a volume action.

Family's accepted profile is pinned in `profiles/family.json`. It may act only
at playback start or a real content-class transition, uses a maximum `0.02`
step, respects the exact `sun.sun` night/day states and latches a manual change
for the current session. Live acceptance proved bounded Movie ramp, app manual
override, gateway failure, Home Assistant restart priming, next-session reset,
zero recorder history and Dolby Atmos passthrough. The recovery record is
`services/kodi/astertv-fleet/releases/astertv-v3-family-content-volume-activation-2026-11-06.json`.

Candidate multi-room configuration (the final key paths and URL are
deployment-owned; the predecessor single-room mapping remains supported during
rolling upgrade):

```yaml
aster_room_bridge:
  rooms:
    - gateway_url: http://192.168.70.10:9120
      client_id: HA-Family
      room_id: family
      key_file: /config/.aster-private/aster-room-bridge-family.key
      power_entity: media_player.family_room_tv
      volume_entity: media_player.tx_rz30
      actions: &equipment_actions
        - equipment.power_on
        - equipment.power_off
        - equipment.volume_up
        - equipment.volume_down
        - equipment.mute_on
        - equipment.mute_off
    - gateway_url: http://192.168.70.10:9120
      client_id: HA-Bedroom
      room_id: bedroom
      key_file: /config/.aster-private/aster-room-bridge-bedroom.key
      power_entity: media_player.lg_webos_tv_oled55g4sub_dccqljr
      volume_entity: media_player.lg_webos_tv_oled55g4sub_dccqljr
      actions: *equipment_actions
```

Do not enable the Bedroom row or create its key until the gateway checkpoint,
exact Home-Assistant-to-gateway network path, configuration rollback and
restart recovery plan are all verified. Its TV-mediated CEC path still requires
independent physical acceptance before its controls are exposed.
