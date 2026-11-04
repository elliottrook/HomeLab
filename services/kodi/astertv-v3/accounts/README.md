# AsterTV v3 synthetic profile registry

This directory implements only the credential-free M2 fixture approved for
the AsterTV-Jen lab candidate. It is deliberately independent of Kodi's real
profiles and every service credential.

`registry.py` validates an allowlisted JSON shape, rejects secret-bearing or
unknown fields, writes atomically with a mode-0600 previous copy, and falls
back to a restricted Guest view when state is absent or malformed. The
synthetic fixture contains two labelled members and Guest; its opaque subjects
cannot authenticate to any service.

The Jen deployment must use a separately named state directory. Family,
Bedroom and the accepted v2 profile are not targets. The 1080p/stereo limits in
Jen's capability profile are not account defaults and do not appear here.
