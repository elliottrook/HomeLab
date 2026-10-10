# HomeLab app icon family

## Purpose

Keep the native Aster Companion app, Aster web surfaces, and the News Digest
briefing visually consistent while preserving each product's identity.

The reusable visual tokens and preview classes are in
[`App-Icon-Family.css`](App-Icon-Family.css). It is a duplication aid for new
sizes and related surfaces; the PNG/ICNS source files remain authoritative for
runtime assets.

## Source assets

| Product | Git source | Runtime use |
|---|---|---|
| Aster Companion | [`docs/assets/aster-companion/aster-app-icon-concept-v2-compass.png`](../assets/aster-companion/aster-app-icon-concept-v2-compass.png) | `apps/AsterCompanion/Resources/AppIcon.icns`; Aster web favicon and PWA icon |
| News Digest | [`docs/assets/news-digest/news-digest-icon.png`](../assets/news-digest/news-digest-icon.png) | `/static/icon-512.png` plus the 32px favicon and 180px Apple touch icon |
| Unified Media Recommendations | [`docs/assets/unified-media/unified-media-recommendations-icon.png`](../assets/unified-media/unified-media-recommendations-icon.png) | Private portal source plus 32px favicon and 180px Apple touch icon |
| Photography Content Desk | [`docs/assets/tcf-content-desk/tcf-content-desk-icon-source.png`](../assets/tcf-content-desk/tcf-content-desk-icon-source.png) | Private desk favicon/app icon and Homepage tile; tracked 32px, 180px and 512px PNG derivatives |

The Aster source is the accepted compass/aster flower artwork. The News Digest
source is the deployed 512px document/news mark; its 32px and 180px variants
are retained because the live page already serves those exact sizes.

Unified Media Recommendations uses the same midnight canvas, electric blue /
violet glow, warm highlight and centered discovery motif. Its source and
runtime derivatives are tracked under
[`docs/assets/unified-media/`](../assets/unified-media/). The reusable web
interface rules are documented separately in the
[HomeLab UI Style Guide](HomeLab-UI-Style-Guide.md).

Photography Content Desk uses a dimensional photo stack and camera aperture as
its centered silhouette, with a warm-gold selection sparkle as the curation
cue. Its glass, pearlescent enamel, luminous blue edge and restrained
blue/violet/cream/gold palette follow the accepted Aster, News Digest and
Unified Media Recommendations standard. It belongs to the Aster operator-tool
family and deliberately does not reuse either public photography site's logo.

## Web integration contract

- Aster's root web app and `/companion` use `/aster-app-icon.png` for favicon
  and Apple touch icon metadata.
- The Companion manifest uses the same image with `any maskable` purpose.
- News Digest keeps `/static/icon-32.png` and `/static/icon-180.png`, adds the
  512px image to its manifest, and must not change its private route, auth, or
  service boundaries as part of an icon update.
- Unified Media Recommendations serves the 32px favicon, 180px Apple touch
  icon, and full-size source from its private portal; the icon update must not
  change its Authentik, request-adapter, or service boundaries.
- Runtime copies are generated from the Git sources; do not hand-edit a
  deployed PNG without bringing the resulting bytes back into Git.

## Verification

Check image dimensions and SHA-256 before deployment, then request each
favicon/manifest URL over the existing private HTTPS routes and confirm the
HTML references the intended files. A failed icon check is cosmetic and should
roll back only the icon files and metadata, not the application service.
