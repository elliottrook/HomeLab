# AsterTV v3 profile authority

This directory implements the Jen-only M2 profile-authority candidate. The
registry contains metadata and opaque subject references only; credentials
remain in their existing service-specific mode-`0600` custody.

`registry.py` validates an allowlisted JSON shape, rejects secret-bearing or
unknown fields, writes atomically with a mode-0600 previous copy, and falls
back to a restricted Guest view when state is absent or malformed. The
synthetic fixture remains the credential-free build/test seed. The live Jen
candidate contains recovery-admin Jason and restricted Guest. `identity_resolver.py`
enables a mapping in memory only when its opaque subject exactly matches the
existing Jellyfin/Audiobookshelf/Seerr custody. Drift fails closed per service.

`authority.py` rebuilds the registry from the local non-secret authority config
and resolved subjects. Missing or malformed state recovers to Jason plus Guest,
always active as Guest. Malformed input is validated away and is never promoted
to the previous copy. The selector exposes the recovery row without requiring
an implementation agent or a source service.

The Jen deployment must use a separately named state directory. Family,
Bedroom and the accepted v2 profile are not targets. The 1080p/stereo limits in
Jen's capability profile are not account defaults and do not appear here.

The candidate keymap wraps the accepted v2 Select dispatcher and the startup
service rejects direct private-window bypasses. Private routes require both an
entitlement and an enabled service mapping; role alone never grants access.
Profiles without a resolved Jellyfin mapping land on public News because v2 Media Home
contains personalized Continue Watching and recommendation state.
