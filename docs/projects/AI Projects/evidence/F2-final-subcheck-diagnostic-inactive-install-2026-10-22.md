# F2 final-subcheck diagnostic — inactive installation

## Result

Jason approved the reviewed one-file inactive installation. The installed
coordinator now matches platform commit
`1ca66cee2953c50563da90fe2071a70b62372c2c` and SHA-256
`98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425`
at root:root mode `0644`.

The previous coordinator SHA-256
`fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`
is preserved at
`/root/aster-f2-final-subcheck-rollback-1ca66cee/f2_scheduled_release_candidate.py`
in a root:root mode-`0700` directory as a mode-`0600` file.

## Validation and postcheck

- the pinned target-Linux focused coordinator suite passed 14/14 against the
  installed module;
- transferred candidate and test files were removed;
- recurring F2 timers remained disabled and inactive;
- the spent October 22 exact-date timer files remained absent;
- the lease controller remained ready with no cooperative state, lock or F2
  receipt;
- LXC104, LXC110 and LXC116 remained running;
- Aster Agent, accepted `aster-llama`, Speech, `pvescheduler` and `pvestatd`
  remained active; and
- no scan, observer, lease, receipt, service stop, model call or F3 action ran.

## Boundary

This installation improves the diagnostic class retained by a future final
failure. It does not reveal which subcheck failed on October 22 and does not
authorize a retry. A fresh exact-cycle card, independent review and separate
activation approval remain required.
