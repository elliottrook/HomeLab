# F2 host-exclusion pin correction — inactive install card

Status: source-only HOLD. This card authorizes no installation, activation,
retry, reschedule, scan, receipt, lease, service stop, model call, or F3.

## Exact October 25 failure

The final terminal state was `FINAL_GUARD_INSTALLED_PIN`. Read-only comparison
identified the mismatch:

| Path | Installed hash | Required/source hash |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` | same |
| Wrapper expected host-exclusion pin | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| Observer expected host-exclusion pin | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |

The installed host-exclusion bytes are already the repository-canonical
`b39680d5…` version. Only the wrapper and observer pin closure require change.

## Bounded source replacement

| Path | Current installed hash | Corrected source hash |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `0dbdbce56be6f72ada8df54dd28cfcda32f6494200ba97f4b40703496271ba9f` | `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34` |
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `27edca21a68dd9d575bbb6bd66a7b5787880f3bc590b8f6efe3457c40722aeb0` | `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858` |

Preserve both current files as root-only 0600 rollback checkpoints. Do not
replace host_exclusion.py. Validate the exact installed-path dependency closure
before any future replacement.

## Validation evidence

- Offline pin/observer/wrapper tests: 17 passed.
- Target Linux pin/observer/wrapper tests: 17/17 passed with temporary staging;
  staging files were removed.
- Full local suite: 362 passed, 8 expected skips.

After any separately approved replacement, re-read all pins and custody. No
timer activation or F2 rerun is part of this correction. A new exact-cycle
activation requires a separate date-specific card and approval.
