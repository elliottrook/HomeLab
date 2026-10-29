# Aster Home v2 app icon family

The SVG masters in the private Brand Asset Library are the source of truth.
Runtime PNG and ICNS assets are exports. See the [UI style guide](HomeLab-UI-Style-Guide.md)
for the charcoal, jade, gold and warm-stone interface tokens.

## Masters and consumers

The masters live at
`/Users/jasonelliott/Documents/Brand Asset Library/brands/aster-home/working/2026-10-13-aster-home-v2-reconstruction/family-candidate-2026-10-14/SVG/`.

| Product | SVG master | Runtime assets |
|---|---|---|
| AsterAI | `01-aster.svg` | Native `AppIcon.icns`, native orb, `/companion` orb, favicon, touch icon and PWA icon |
| News Digest | `04-news-digest.svg` | Briefing 32px, 180px and 512px web icons; [source note](../../services/news-aggregator/ICON-SOURCE.md) |
| Media Acquisition Hub | `06-media-acquisition-hub.svg` | Unified Media Recommendations portal 32px, 180px and 512px icons |
| Photography Content Desk | `05-content-desk.svg` | Private Desk 32px, 180px and 512px icons |

SHA-256 of the three newly adopted masters:

| Master | SHA-256 |
|---|---|
| `01-aster.svg` | `f6a0f19ff9e5ac4728e04cf20c28e86f171d516ec403a1bc3df937c8a456c6a4` |
| `05-content-desk.svg` | `f1d8a197731c72868fb9287ea04c9104b4d862b0cca35b173a81ad50080a1d5c` |
| `06-media-acquisition-hub.svg` | `8565ce37dba39c9820df5600ae42789087e0d6ac940f98e37087516542aec90d` |

Each of these masters is a vector reconstruction with no embedded raster.
The application exports use the master with `viewBox="55 40 1140 1140"`,
an opaque `#D1C1AA` square backing rect, and an opaque PNG export. This
expands the approved limestone canvas to the actual image boundary without
adding a black or white band. Do not use transparent padding or browser
scaling of a 512px file for the 32px favicon. Preserve the original SVG
files in the asset library; only runtime derivatives are checked into apps.

## Verification

Inspect each icon at its delivered size, check dimensions and opacity, and
verify favicon, touch and manifest URLs through the private application route.
Keep service identities and authentication routes unchanged during visual
updates. The previous blue icons remain available in Git history for rollback.
