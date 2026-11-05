# Aster Room Bridge candidate

This Home Assistant custom component is the outbound-only half of the M7 room
equipment bridge. It polls the private Aster gateway and translates only the
locally configured action allowlist into fixed `media_player` services and
entity IDs. The gateway cannot choose a Home Assistant service or entity.

The Family candidate is intentionally limited to:

- TV power: `media_player.family_room_tv`;
- receiver volume/mute: `media_player.tx_rz30`;
- actions: explicit power on/off, volume up/down and mute on/off.

The client key lives in a separate regular file with no group/other permission.
It is not placed in YAML, source, logs or the browser. Home Assistant initiates
all traffic to `/v1/remote/equipment/{poll,ack}`; the component opens no inbound
port and registers no general Home Assistant service.

Candidate configuration (the final key path and URL are deployment-owned):

```yaml
aster_room_bridge:
  gateway_url: http://192.168.70.10:9120
  client_id: HA-Family
  room_id: family
  key_file: /config/.aster-private/aster-room-bridge.key
  power_entity: media_player.family_room_tv
  volume_entity: media_player.tx_rz30
  actions:
    - equipment.power_on
    - equipment.power_off
    - equipment.volume_up
    - equipment.volume_down
    - equipment.mute_on
    - equipment.mute_off
```

Do not install this directory or create its key until the gateway checkpoint,
exact Home-Assistant-to-gateway network path, configuration rollback and
restart recovery plan are all verified. Bedroom remains unconfigured until its
audio equipment is identified and independently accepted.
