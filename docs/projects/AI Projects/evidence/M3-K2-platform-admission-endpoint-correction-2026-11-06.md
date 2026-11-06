# M3 K2 platform-admission endpoint correction — 2026-11-06

## Result

Platform-owner review rejected the first K2 source release candidate before
installation or effect. The development runner was pinned only to the accepted
production endpoint, but the registered Lab Hours full-drain controller masks
that service and uses a private loopback listener during the exclusive
transaction. The unchanged packet therefore could not have run under its
declared controls.

The corrected runner accepts exactly two fixed endpoints: the accepted
production endpoint for inert/source validation and
`http://127.0.0.1:11436/v1/chat/completions` for the booked full-drain guest
transaction. Arbitrary endpoints remain rejected. The preregistration and
runtime manifest now state `booked-full-drain-restore-required` rather than the
incompatible `service_restart=forbidden` claim. This authorizes no model or
backend change; the same accepted model, binary and unit hashes remain pinned,
and production restoration is mandatory.

## Corrected identities

- preregistration source SHA-256:
  `f3e633ac81d32bd63fb53e5a51339787cab1e66ee65f56874c012132a32f4f6a`
- development runner SHA-256:
  `d5c9ef87bd49185466a12e7b53eab741d0f0dc40ce92c2977389dd2b0e5e3785`
- runtime manifest SHA-256:
  `619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88`

The focused correction suite passes 13/13. No B60 request, booking, lease,
service change, model call, installation, route effect or sealed-evaluation
access occurred.
