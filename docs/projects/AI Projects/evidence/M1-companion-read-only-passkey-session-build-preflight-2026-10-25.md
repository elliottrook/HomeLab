# M1 Companion read-only passkey session build preflight — 2026-10-25

> Result: **BUILD PASS; INSTALLATION NO-GO ON SIGNER CONTINUITY**
>
> Candidate source: `ab65be64`

## Build result

The complete native suite passed 61/61. The first app-bundle build stopped
before signing because Xcode 27's SwiftPM resource bundle now uses the standard
`Contents/Resources` layout while the build script accepted only the prior flat
layout. The corrected script accepts exactly those two known layouts and still
fails before signing if neither contains `AsterOrb.png`.

The corrected build completed with app registration disabled. `codesign
--verify --deep --strict` passed. The staged bundle is version 0.3.0/build 16;
its executable SHA-256 is
`49d535031655df4e6a5cdf58611857aab4382741d57cbb66ed0f506dcb68a258`.
The corrected build-script SHA-256 is
`a269d6470c857b3c4e1de8d2d8492fc109ed20adafa1ac44e1bb3bb3d61317e7`.

## Failed installation gate

The installed app is signed by **Aster Companion Local Signing 2026 R2** and
has designated certificate requirement prefix `5522e8b8…`. Its embedded public
certificate remains valid from October 13, 2026 through October 12, 2029.
The current Keychain exposes only the earlier valid signing identity **Aster
Companion Local Signing 2026**. The staged app therefore has designated
certificate requirement prefix `10b67a3b…`.

Installing that bundle could cause a new Keychain authorization prompt or lose
access to the current persisted Companion session. It could also make the R2
rollback dependent on another Keychain access-list decision. The candidate is
therefore **NO-GO for installation** despite its valid signature.

## Next safe action

Either restore the existing R2 private signing identity to the user Keychain
from its owner-held custody, or prepare a separately approved signer-transition
test that explicitly accepts the Keychain/session and rollback consequences.
Do not search for, export or recreate private signing material implicitly. No
app was installed, registered or launched by this build preflight.
