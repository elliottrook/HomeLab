# AsterTV release and composition matrix

> Generated deterministically by `compile_fleet.py`; do not edit by hand.

| Device | State | Channel | Release | Hardware / output | Overlays | Composition |
|---|---|---|---|---|---|---|
| astertv-bedroom | production | production | `astertv-v2.0.7-2026-10-31` | Intel i5-9500T Bedroom appliance; stereo PCM with AC3/EAC3 passthrough; DTS/TrueHD/DTS-HD disabled | `release-guard-v1`<br>`remote-client-v3`<br>`bedroom-equipment-bridge`<br>`bedroom-physical-equipment-keys`<br>`bedroom-stereo`<br>`bedroom-wifi-stability`<br>`beszel-client-v1`<br>`tv-details-v3` | `df99481a5073` |
| astertv-family | production | production | `astertv-v2.0.7-2026-10-31` | Intel N95 Family appliance; Dolby passthrough and HDR | `release-guard-v1`<br>`beszel-client-v1`<br>`family-dolby-hdr`<br>`remote-client-v3`<br>`family-equipment-bridge`<br>`family-kodi-restart`<br>`family-media-lifecycle`<br>`family-physical-equipment-keys`<br>`news-playback-v3`<br>`tv-details-v3` | `8ba10827cec3` |
| astertv-guest | candidate / not deployed | unassigned | `astertv-v2.0.7-2026-10-31` | Guest hardware not selected; pending | none | `5ca63262bb49` |
| astertv-jen | lab | v3-lab | `astertv-v2.0.7-2026-10-31` | Lenovo M93p Jen low-spec appliance; native-display GUI; media playback capped at 1080p/18 Mb/s with stereo and no passthrough | `release-guard-v1`<br>`beszel-client-v1`<br>`jen-account-registry`<br>`jen-aster-client`<br>`jen-guest-catalogue`<br>`jen-home-cameras`<br>`jen-low-spec-runtime`<br>`tv-details-v3`<br>`jen-movie-youtube`<br>`news-playback-v3`<br>`jen-news-icons`<br>`jen-podcast-requests`<br>`remote-client-v3` | `34cccf847b91` |

## Boundaries

- Family retains its measured Dolby/HDR and equipment-control composition.
- Bedroom retains stereo PCM, AC3/EAC3 passthrough and Wi-Fi stability requirements.
- Jen's 1080p-media/stereo limit belongs only to its hardware profile; native GUI resolution is permitted.
- Guest is a compiled candidate with no address, identity, firewall path or deployment.
- Opaque secret references identify custody only; no value appears in an output.
