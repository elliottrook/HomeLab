# AsterTV v4 Games design candidate

Status: **candidate — owner visual/interaction acceptance required**

This is design authority only. It creates no Kodi XML, add-on, emulator core,
controller mapping, fleet overlay, device identity, broker ingress, appliance
bundle, or live integration.

## Design direction

Games should feel like an Aster library, not a separate neon arcade frontend.
The candidate keeps the accepted charcoal, cream, champagne-gold, and jade
language. Restrained synthetic box art supplies the retro character. Dynamic
game artwork remains content rather than a reusable Aster interface asset.

The main page prioritizes household play state:

1. Continue playing when a resumable game exists.
2. Ready on this TV for installed games.
3. Browse platforms.
4. Your library.
5. Requests only when proposals exist.

The top filters are Library, Continue, Platforms, and Requests. Each pill uses
the exact approved 32×32 plain Aster compass export; current context uses gold.
Artwork focus is one continuous jade selection surface flowing from the narrow
top/side reveal into the deeper title area; it is not a separate title pill
plus border. The artwork keeps exactly the same position and size. Box art is
2:3, platform art is square, and missing art uses a quiet platform monogram.

The left edge now uses the official collapsed Aster side rail: 72 pixels wide,
native limestone-backed artwork, and the accepted Media, Books, News, Home,
Music, Requests, and Settings ordering. Games is added directly below Music
for v4, extending and re-centering the rail by one standard slot. Its current
temporary icon reuses the approved generic limestone-backed Aster mark; it must
be replaced when the dedicated Games icon is accepted.

## State-dependent primary action

| State | Primary action | Important behavior |
|---|---|---|
| Resumable | Resume | Start new remains secondary |
| Installed | Play | Save management is separate |
| Available | Install | Opens a facts-first confirmation |
| Absent | Request | Creates a pending proposal only |
| Pending | Request pending | Disabled and not focusable |
| Installing | Installing | Disabled; cancel is secondary |
| Unsupported | Not supported on this TV | Disabled; Why? explains recovery |
| Offline | Try again | Back to Home remains available |

Play, Resume, Install, and Request are intentionally different words and
states. The design never implies that catalogue presence guarantees local
compatibility.

## Remote behavior

- Entry restores the last exact item when possible. Otherwise it chooses the
  first resumable, installed, library, or platform item in that order.
- Horizontal rails clamp at their ends; they never wrap.
- Vertical movement chooses the nearest horizontal centre and remembers the
  previous position in each rail.
- Back returns dialog → detail → prior rail item → Home.
- Menu opens the action sheet only while a game tile has focus.
- Disabled actions are skipped and expose one concise, recoverable reason.
- The save-conflict dialog enters on Cancel so a directional mistake cannot
  overwrite either copy.

The machine-readable graphs cover the main page, installed/available/absent
detail variants, install and request confirmations, save conflict, and offline
recovery.

## Performance and accessibility

The fixtures use Jen's accepted low-spec ceiling: 1536 MiB total UI memory
budget, 256 MiB artwork cache, two prefetched rows, 1920 maximum artwork
dimension, seven visible box-art tiles, no animated background, and at most one
simultaneous fade. Reduced motion is zero-duration.

Body text is at least 24 px and metadata at least 20 px. Focus is communicated
by geometry/depth as well as color. Long titles use one ellipsized tile line and
two full detail lines. Error states provide one focused recovery action and a
route back to Home.

## Review fixtures

- Main page: `generated/renders/pages/games.svg`
- Focus: `generated/renders/pages/games-focus.svg`
- Empty: `generated/renders/pages/games-empty-library.svg`
- Offline: `generated/renders/pages/games-service-offline.svg`
- Missing art: `generated/renders/pages/games-missing-art.svg`
- Long title: `generated/renders/pages/games-long-title.svg`
- Detail: `generated/renders/pages/game-detail.svg`
- Install: `generated/renders/pages/game-install-dialog.svg`
- Request: `generated/renders/pages/game-request-dialog.svg`
- Save conflict: `generated/renders/pages/game-save-conflict-dialog.svg`

All fixtures are deterministic 1920×1080 SVGs using synthetic titles and art.

## Acceptance boundary

Owner acceptance may approve the visual hierarchy, terminology, focus model,
dialog behavior, and performance/accessibility envelope. It does not authorize
implementation or integration. The exact platform/core/controller support
matrix remains deferred until the post-v3 integration phase can test real
hardware and RetroPlayer behavior.
