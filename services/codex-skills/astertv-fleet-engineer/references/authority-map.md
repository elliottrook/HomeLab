# AsterTV authority map

Read only the rows relevant to the task.

| Question | Authority | Useful entry point |
|---|---|---|
| What should this appliance contain? | Git fleet contract | `services/kodi/astertv-fleet/devices/` and `desired/` |
| Which release bytes are accepted? | Private Forgejo release and hash | `services/kodi/astertv-fleet/releases/` |
| What is connected and where? | NetBox | Wiki device/peripheral page is presentation only |
| What is running now? | Sanitized live query | Record time and device identity |
| Which local difference is legitimate? | Profile/overlay plus decision evidence | `hardware/`, `peripherals/`, `overlays/` |
| Which HA actions exist? | HA registry plus reviewed room mapping | Wiki HA curriculum and bridge contract |
| Which traffic is allowed? | OPNsense live config plus reviewed reference | Wiki network/firewall curriculum |
| Where is a secret? | Existing custodian | Opaque `secret_refs`; never retrieve into Git/wiki |
| How is the UI intended to behave? | AsterTV design authority | `services/kodi/astertv-design/` |
| What was decided or tested? | Project evidence | `docs/projects/` and `docs/projects/evidence/` |

The Aster knowledge mirror is derived and non-authoritative. A screenshot,
conversation, old checkpoint, observed file, or wiki prose cannot override the
fleet contract or private release.

Required local checks normally begin with:

```sh
python3 services/kodi/astertv-fleet/compile_fleet.py
python3 services/kodi/astertv-fleet/build_release_plans.py
python3 -m unittest discover -s services/kodi/astertv-fleet/tests -p 'test_*.py'
```
