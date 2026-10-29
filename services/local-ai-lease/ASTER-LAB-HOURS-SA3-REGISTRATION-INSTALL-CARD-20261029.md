# SA3 fixed registration — inactive installation card

Status: **source-complete candidate; installation is not performed by this card**

This candidate reconciles the reviewed SA3 source registration with the actual
working Proxmox Lab Hours baseline. It deliberately preserves the later
exclusive-capacity reservation behavior that was present on the host but absent
from the earlier source-registration commit.

## Exact five-file change

Under `/usr/local/libexec/local-ai-lease/full-inference-pilot`:

| Target | Existing SHA-256 | Installed SHA-256 | Mode |
|---|---|---|---|
| `lab_hours_workloads.py` | absent | `2780fcc7f7638a8d9987c79f2438d92fbc31c106ca67da81c994ca8ccb0402f1` | `0644` |
| `lab_hours_inactive_target.py` | absent | `f670077ec2be3001058c8a7f18b8da55e5f717422305c400afd97350bc7cefab` | `0644` |
| `lab_hours_reservations.py` | `f3f112c31c30776e94889d1a372b0584b9460007369fc7986a3c5f90e6c92322` | `f61c6b496fd6e378b6e144a2b13170c85392274e86127a29b03d0cf8f16415d2` | `0755` |
| `lab_hours_reserved_runner.py` | `6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2` | `79b3fb92ced17712f7f5dd8bd40517fbec27ef2b2494c47454fb8fdcd44bf27e` | `0755` |
| `lab_hours_release_manifest.json` | `b2c61494d572e17f3f1d4c71564f1b8c8f43728d9063c8d39e0c49e637593bed` | `7aa4a8c1d04d0e208b0cc732931592c94a6e49e18e3a1bdaf52c1532d7ff2c14` | `0644` |

The working booking CLI remains byte-identical at
`d035803e65e9384f671e625f266bab5a13e408eeb065e9007d82743f4c6eb793`.
The reconciled reservation module retains `reserved` state, `--exclusive`
capacity reservations, cancellation of unclaimed exclusive reservations and
the prohibition on dispatching an exclusive handoff through the fixed smoke
runner. It additionally admits only the fixed SA3 workload identity.

The registered runner derives guardian timing from the fixed registry. For the
SA3 identity it returns `WORKLOAD_RUNNER_UNAVAILABLE` before creating attempt
evidence, arming a guardian or draining production. The installed transaction
and listener hashes are included in the release manifest; the guest wrapper is
not incorrectly treated as a Proxmox file.

## Fixed bundle and transaction

The deterministic bundle is `aster-sa3-registration-v1.tar.gz`, SHA-256
`78a4fe9996e784814bc4130b8c849cc46e969f5a6e2511c8e2fb099a77b6ff54`.
It contains only the fixed installer and five source targets. The installer is
source-only unless `--apply` is passed. It requires the exact three replacement
baselines and two absent targets, validates every unchanged release-manifest
pin, checkpoints exact bytes/absence under the fresh root-only
`/var/lib/local-ai-lab/checkpoints/sa3-registration-v1`, installs atomically,
imports the complete registration closure and rolls back all five targets on
any failure or uncertainty.

The focused registry, reservations, runner, dispatcher, Doctor and installer
suite passes 23/23. The source hashes are:

```text
4d452007299bb9eb52fb1646531b7f3e93ae80215dac3ee0477196ca0cc26814  scripts/local-ai/sa3_registration_install.py
9b95dde3c9c25b6f775230366bfedcabaf11787fb9d69b3db391a5b8ac630892  scripts/local-ai/build_sa3_registration_bundle.py
dd557eeeb235dc6d8620ac8bbaa7863dc4707cec7e9755a71385ed0d08cafa9c  scripts/local-ai/test_sa3_registration_install.py
```

Installation would use fresh root-only incoming and stage paths named
`sa3-registration-v1`, verify the pinned archive and run:

```text
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B \
  /var/lib/local-ai-lab/staging/sa3-registration-v1/scripts/local-ai/sa3_registration_install.py \
  --source-root /var/lib/local-ai-lab/staging/sa3-registration-v1 --apply
```

This change creates no booking, reservation window, lease, operation lock,
model request, production drain, service/timer, schedule, restart, routing or
automatic promotion. A later model evaluation still requires an authoritative
ledger check, a fixed reservation and all runtime lease/lock gates.
