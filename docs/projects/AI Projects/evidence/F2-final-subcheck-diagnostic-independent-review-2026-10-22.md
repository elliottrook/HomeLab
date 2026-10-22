# F2 final-subcheck diagnostic — independent review

## Decision

The corrected source at platform commit
`1ca66cee2953c50563da90fe2071a70b62372c2c` is suitable for a separately
approved **inactive one-file installation**. This review authorizes no host
change, cycle activation, scan, receipt, lease, service stop, drill or F3.

## Review findings

- the coordinator source SHA-256 is
  `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425`;
- the focused-test SHA-256 is
  `5d07939244276d465636b01e97f34e14fd3797804fbbcd825dd545ae2fa52ddb`;
- the proposed current installed pin remains
  `fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`;
- final guard, observer launch, observer communication and nonzero observer
  exit now persist distinct content-free codes;
- timeout and projection failure codes retain their existing behavior;
- the first-failure and no-retry rules remain intact; and
- no child output, traceback, credential or unbounded error is retained.

The first platform card overstated test coverage for the observer communication
path. Independent review rejected that evidence. The platform owner added a
direct test which asserts `first_failure_phase=final` and
`failure_class=OBSERVER_COMMUNICATION_FAILED`, updated the test pin, and
reported 14/14 focused target-Linux passes plus 361 local passes with eight
expected skips. Stream A independently ran the focused suite from the pinned
platform checkout and observed 14/14 passing.

## Next gate

After exact approval, install only the pinned coordinator, preserve the current
bytes in the named root-only rollback checkpoint, rerun the 14 focused tests on
target Linux, and verify all F2 timers remain disabled/inactive with no scan,
lease, receipt or production change. Any source, installed-pin, custody or test
drift is a failed installation gate and requires rollback. A later live cycle
still needs a new exact-date card and separate approval.
