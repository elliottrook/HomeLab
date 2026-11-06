# SA4 live measurement and checkpoint-owner source — 2026-11-05

## Result

The production transaction path still had two deliberate source safeties that
would have blocked the accepted LXC 104 canary: both the no-follow measurement
owner and exclusive checkpoint owner were compiled for host `unconfigured`.
Their source is now bound to exactly `lxc104`, matching the sole compiled
production target.

The measurement owner can open only the registered production path through a
held `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` descriptor. It requires root:root mode
0644, one regular link, bounded size, stable path/descriptor identity and the
exact plan precondition digest. Its output still states no checkpoint, no
grant claim, zero repair effects and `preflight_eligible=false`.

The checkpoint owner accepts only that exact recent measurement, rereads the
unchanged target through a no-follow descriptor while holding its exclusive
owner lock, and can create only the compiled mode-0600 checkpoint path on the
same filesystem. It never claims a grant or changes the target, and its output
also remains preflight-ineligible. Invoking checkpoint creation is not part of
this source milestone.

The new source hashes are:

- measurement owner:
  `16644ee6dd42997bd07993ce0a850fc6620208e27b3c81ba03069f8ea91e5e2e`;
- checkpoint owner:
  `b0d8dff3bf7714cfc48e1dc5ea6e5e40db8ff815410c631e036880d79b307614`.

The inactive-install manifest pins both new hashes. Existing synthetic
descriptor, symlink, hardlink, mode, drift, exclusivity and stale-measurement
tests still pass, and new assertions require the committed host binding to be
exactly `lxc104`. The complete SA4 suite passes **97/97**.

## Boundary and next step

These source changes are not installed. No live measurement or checkpoint was
created. The next bounded step is a reversible two-file inactive installation
and installed read-only measurement proof. Checkpoint creation remains a later
transaction rehearsal gate, and no repair effect may run without the separate
exact immediate approval.

