# M3 private-category label boundary — offline correction

**Status:** source-only validation. No real interaction was collected, no
model or routing service was called, and no route, permission or cloud-egress
policy was promoted.

Two development-data validators required a personal/local-only label when
the required or optional capabilities named calendar, private context or
local join. They also protected the mixed category. A row categorized as
`calendar` or `personal` could nevertheless carry `public` sensitivity and
`public-only` cloud eligibility if its capability list omitted a private
capability. That is a metadata-contract inconsistency, not evidence of a
production leak. Both validators now require `personal` sensitivity and
`forbidden` cloud egress for `calendar`, `mixed` and `personal` categories,
independently of the capability list.
The draft label validator now also rejects optional capabilities on a
non-plan label, matching the S1 collection validator; an abstention cannot
carry a proposed tool list.

New negative synthetic cases cover calendar and personal categories without
private capabilities and optional tools attached to abstention. The focused
label-batch suite passed 19/19 and the S1
collection-validator suite passed 19/19. The S1 invented full-bundle fixture
now labels its calendar and personal strata according to the same boundary.
The previously accepted S1 batch metadata was checked without reading request
text: none of its calendar/personal rows had a conflicting sensitivity or
cloud label.

This validator cannot determine whether a supposedly public request contains
personal information, authenticate a human labeler or authorize collection.
Independent privacy review and measured routing evidence remain required
before any automatic handover or cloud promotion.
