# AsterTV v3 brand-asset deployment — 2026-11-06

## Authorization and scope

Jason directed AsterTV to deploy the newly supplied assets and then resume the
next v3 milestone. This is the consumer acceptance record for the exact assets
below; it is not a global Aster Home release or permission to resize raster
artwork.

| Placement | Approved SVG source SHA-256 | Installed PNG SHA-256 |
|---|---|---|
| Aster Remote Apple touch icon, 180×180 | `7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada` | `36eb73e019be374fbf4cb2fdf2e16de14b30e0dc470cbc5b19fae63bc4ba8379` |
| Aster Remote PWA icon, 512×512 | `7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada` | `07880f3fb4e791b6383cabfe3c77a5218c184e84073c8cb89037e9b9c5a16074` |
| AsterTV Kodi splash, 1920×1080 | `747aab438334afc9b1e2a0dafa8608bd8b8d4aa5ed29af5697f22972b714d2e8` | `3658771b8ab771591839713cd497cc79a5a781d67463145fe2f23c3d541d4626` |

The splash was drawn directly from the approved SVG onto its fixed placement
canvas by `render_tv_splash.swift`. The Remote icons are independent direct SVG
exports at their exact consumer dimensions. No PNG was resized, repurposed or
used as a source.

## Remote deployment

The live Aster Agent predecessor was hash-pinned before mutation. A
checkpointed installer changed only the launcher manifest, service worker,
index references, two icon files and the two exact static routes. An initial
validation defect requested the nonexistent `/remote/index.html` route; both
attempts restored every predecessor file automatically before the validator
was corrected to test `/remote/`. The accepted installation retained checkpoint
`/var/lib/aster/checkpoints/astertv-v3-remote-brand-assets-20261106`.

Post-install validation proved:

- `aster-agent.service` active;
- HTTPS manifest returns the 512×512 Remote asset;
- both public asset routes return the exact registered hashes;
- direct internal session access still returns `403`; and
- `scripts/check-astertv-remote.py` reports the gateway, three room identities,
  clients and manifests healthy.

The existing Companion icon was not replaced.

## Appliance deployment

All targets were idle and on the exact predecessor splash hash
`912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce`
immediately before change. Promotion followed Jen → Bedroom → Family. Each
host created `/storage/.aster-checkpoints/astertv-v3-r5-splash-20261106`,
atomically replaced only `/storage/.kodi/media/Splash.png`, restarted Kodi and
validated idle JSON-RPC plus the installed hash.

| Target | Result | Device-specific preservation |
|---|---|---|
| AsterTV-Jen | Active and idle after canary | Returned healthy before wider promotion |
| AsterTV-Bedroom | Active at Home | ConnMan Wi-Fi files byte-identical; stereo plus AC3/EAC3 passthrough contract retained |
| AsterTV-Family | Active at Home | Dolby/HDR audio subset retained, including AC3/EAC3/TrueHD and disabled DTS/DTS-HD |

## Regression gates

- deterministic placement render reproduced all three output hashes;
- 14 design-system tests pass;
- 19 Remote/static/installer/splash tests pass;
- 51 fleet compiler/materialization/release tests pass;
- the complete M10 local gate passes 64 test files, 93 secret-scanned files and
  the 15-page/127-control conformance audit with zero failures;
- the Family recovery materialization now contains the Remote launcher exports
  so a later global composition cannot silently restore the old icon; and
- every raster remains registered against its exact SVG source, consumer,
  dimensions and no-resize rule.

No credential, account state, media metadata, network policy or source-service
configuration was added to the asset package.
