# App icon family

**Status:** Complete — Stream M; web and native Mac deployment validated

**Owner:** Jason

**Proposed:** 2026-10-04  
**Started:** 2026-10-04

## Purpose and desired outcome

Put the accepted Aster artwork and the deployed News Digest artwork under Git
control and make the native Aster app, Aster web app/Companion, and News Digest
briefing web app present the correct icon on desktop and mobile home screens.

## Current state and evidence

- The linked ChatGPT handoff identifies four intended artifacts: the native
  `AppIcon.icns`, Aster source image, News Digest source image, and an icon
  family guide.
- The native Aster `.icns` is already present and tracked at
  `apps/AsterCompanion/Resources/AppIcon.icns`.
- The accepted Aster source is tracked at
  `docs/assets/aster-companion/aster-app-icon-concept-v2-compass.png`.
- The follow-up handoff chats supplied the refined Aster flower and glowing
  folded-newspaper artwork; those now replace the earlier source PNGs.
- LXC 114's live News Digest service exposes `icon-32.png`, `icon-180.png`,
  and `icon-512.png`; their SHA-256 values are recorded in the evidence log.
- Aster's local web source currently points favicon and PWA metadata at the
  older orb asset. News Digest source code is deployed on LXC 114 and is not a
  tracked checkout in this repository.

## Scope and exclusions

In scope: icon source files, Aster native/web metadata, News Digest icon
metadata, the reusable family guide, validation, and a local Git commit.

Excluded: application behavior, authentication, DNS, firewall, service
topology, generated audio, database changes, remote Git synchronization, and
any unrelated working-tree changes.

## Authority model

Git is authoritative for the accepted source assets and Aster web source.
LXC 114 is the observed runtime source for the existing News Digest variants
until the News Digest application source is brought under the repository's
normal release path. The browser is used only for end-user metadata validation.

## Pre-start risk assessment

This is a low-blast-radius Stream M project. The changes are static files and
HTML/manifest metadata. No credentials or personal data are handled. The main
integrity risk is deploying the wrong image or losing the existing News Digest
variant; mitigate with SHA-256 checks and a file-only rollback. Availability
risk is limited to a service reload/restart if required; no restart is needed
for the local preparation. No firewall, DNS, storage, backup, or NetBox change
is expected. Remote deployment remains a separate approved change because the
repository rule requires confirmation immediately before a state-changing
remote command.

## Persistence, rollback, and milestones

1. [x] Capture the linked-chat handoff and current repository/runtime evidence.
2. [x] Add icon assets, duplication stylesheet, and design contract to Git;
   update Aster web source.
3. [x] Deploy only the static assets/metadata to LXC 104 and LXC 114 and
   validate private URLs.
4. [x] Install and verify the native Aster Companion release on the Mac.
5. [x] Commit the project record and synchronize `main` through Forgejo.

Rollback is to restore the prior Aster HTML/manifest references and the prior
News Digest icon files. The deployed News Digest bytes are retained in the
evidence log and the Aster source remains in Git.

## Validation and evaluation

- `file` and SHA-256 checks for every PNG.
- Aster unit/syntax checks plus a built native app check where available.
- Private HTTP checks for Aster favicon, Companion manifest, and News Digest
  favicon/touch/manifest URLs after deployment.
- Confirm no unrelated tracked or untracked user changes are included in the
  commit.

## Documentation and systems-of-record updates

The design guide is the reusable visual contract. This project records the
runtime ownership boundary and deployment evidence. No operational or backup
configuration changes are required for static icon assets.

## Evidence log

| Date | Action | Evidence | Result |
|---|---|---|---|
| 2026-10-04 | Read shared-chat handoff | Shared page named native Aster icon, Aster source, News Digest source, and family guide | Handoff recovered; News Digest source was absent from checkout |
| 2026-10-04 | Read LXC 114 runtime assets | `icon-32.png` `a3d8410f…387d5ca`; `icon-180.png` `492e517e…8fe1be`; `icon-512.png` `b2f31110…e65dab` | Existing deployed icon family captured without remote mutation |
| 2026-10-04 | Local preparation | Aster web metadata now references `/aster-app-icon.png`; source assets and guide added | Ready for separately approved deployment |
| 2026-10-04 | Follow-up asset handoff | Shared chats supplied refined Aster flower and folded-newspaper PNGs | Replaced stale source PNGs and generated News Digest 32/180px derivatives; rebuilt the native ICNS after clearing macOS provenance metadata from generated iconset files |
| 2026-10-04 | Runtime deployment | Aster LXC 104 restarted; Aster root/Companion HTML and manifest reference `/aster-app-icon.png`; News Digest LXC 114 UI restarted with 32/180/512px references | Live icon hashes match Git sources; private URL validation passed |
| 2026-10-04 | Mac completion | `/Applications/AsterCompanion.app` replaced atomically after preserving rollback copy; `codesign --verify --deep --strict` passed; Swift test suite passed 24/24 | Native app installed and Launch Services re-registered; ad-hoc signature remains expected on this Mac |
