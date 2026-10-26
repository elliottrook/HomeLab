# M3 NLU complete-score failure boundary — 2026-10-25

> State: source correction complete; inactive installed packet still superseded

## Finding

The corrected live runner rejects a transport, endpoint or deadline failure
even when it occurs on case 60. The downstream scorer and journal validator
still accepted a separately supplied 60-record run containing one of those
failures when its terminal journal claimed `complete: true`. That disagreed
with the approved run card: only a malformed model response is retained as a
zero-score completed attempt; infrastructure uncertainty makes the run
incomplete and unscorable.

## Correction

The scorer now permits exactly one invalid completed-record shape:
`invalid_response` with `response_invalid`. Timeout, endpoint and transport
failures reject the score before any score artifact can be created. The
journal validator independently rejects the same impossible complete-run
claim. Three regressions cover the prohibited failure classes, while the
existing denominator test now uses a genuine invalid model response.

The refreshed eleven-file stage manifest pins:

- scorer SHA-256 `7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd`;
- journal validator SHA-256 `966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb`;
- stage validator SHA-256 `83c7ed1135e444d832518e95bc7df51c59d5cb1c3cc7041177f31fc8cb84c3c9`;
  and
- stage manifest SHA-256 `7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80`.

The dependency-free NLU suite passes 119 tests. No model request, lease,
service change, output artifact, threshold selection or routing action ran.
The LXC110 packet remains inactive, but its installed scorer, journal and
manifest are now obsolete. A bounded inactive replacement with rollback and
target-Linux tests is required before calibration.
