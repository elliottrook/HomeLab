# AsterTV v3 M11 silent fleet revalidation — 2026-11-06

## Outcome

The content-free Aster Remote probe and the complete local v3 gate pass after a
false client-parity alarm was corrected. No playback, navigation, camera,
volume, mute, power, CEC, display or audio command was sent. No appliance,
gateway, account, credential, network or media state was changed by this
revalidation.

## Remote parity correction

The first probe reported Family client drift even though every deployed source
file matched stable custody. The sole extra file was Python's generated
`__pycache__/content_session.cpython-314.opt-1.pyc`. Runtime bytecode is neither
reviewed deployment input nor part of the stable add-on manifest, so treating
it as source drift made the health check depend on whether Python had imported
the module since boot.

Commit `ca9eb9615768179c51aabaa29638b037cc8609ef` now excludes `__pycache__`
members and `.pyc` files from both live and stable tree hashes. The focused
test suite also uses the current three-network room boundary and pins the
runtime-cache exclusion. Five focused tests pass.

The corrected live probe verifies:

- the Aster Agent Remote route and denial boundary;
- exact Family, Bedroom and Jen room identities;
- enabled client add-ons and private `0600` custody;
- source parity between live and stable add-on trees; and
- exact stable manifest parity on all three clients.

## Transient gateway observation

During the first full retry, Aster Agent was deliberately inactive rather than
crashed: systemd recorded a clean `SIGTERM` shutdown, zero automatic restarts
and no failed state. The service returned independently at
`2026-11-06 23:45:21 MST`. This workflow did not restart or alter it. After it
returned, the same full Remote probe passed.

The stop initiator was not attributable from the available sanitized journal,
so this evidence does not classify it as either a defect or an accepted
maintenance action. A repeated unexplained stop remains a reason to investigate
before promotion.

## Repository gate

The integrated local validator at `ca9eb961…609ef` reports
`pass-with-owner-acceptance-open`:

- 76 local test files pass;
- 93 candidate files pass the secret-pattern scan;
- 15 pages expose 127 focus controls with zero conformance failures;
- operations readiness passes with zero gaps; and
- the deterministic screensaver candidate remains
  `254ac8bd…5bc16`.

The only integrated external gate still open is the non-author physical
walkthrough.

Two fresh release-plan builds from the same checkout also produced byte-for-
byte identical 17-file output trees with tree digest
`eafb0ee6…ac9ce`. The four bundle hashes remain exactly those in the immutable
candidate:

- Bedroom `212ab281…8f7437`;
- Family `5eb17b3f…1efeed`;
- Jen `45ba989d…9da5f`; and
- non-deployable Guest `4d79b20a…201e0`.

## Silent client snapshot

A final content-free query found exact hostnames on Bedroom, Family and Jen.
Every client had:

- zero active players;
- active Kodi with zero restart count;
- the accepted release guard at `Result=success` / `ExecMainStatus=0`; and
- active Beszel with zero restart count.

This snapshot did not open a page, content item, camera or player and did not
send an AV/equipment action.

## Deliberately open

The committed composition observations are now more than 24 hours old, so the
fleet Doctor correctly reports all three as `stale`; it does not report drift.
Their timestamps were not advanced from partial checks or copied assertions.
A fresh formal observation must remeasure every declared payload, dependency
and assertion rather than convert this narrower health pass into current
composition evidence.

Bedroom equipment/volume acceptance, complete-composition deployment, reboot
and audible normal-use soak remain open. Family final promotion, the external
Media Lifecycle replacement-view handoff and the non-author walkthrough also
remain open.
