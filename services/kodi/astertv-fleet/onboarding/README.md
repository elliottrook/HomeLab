# AsterTV plan-only onboarding

`plan_onboarding.py` turns a reviewed candidate request into a deterministic
operator plan. It has no SSH, HTTP, credential or mutation implementation.

```sh
python3 services/kodi/astertv-fleet/onboarding/plan_onboarding.py \
  services/kodi/astertv-fleet/onboarding/fixtures/guest-candidate.json \
  --output services/kodi/astertv-fleet/onboarding/generated/guest-plan.json
```

The planner refuses a non-candidate fleet member, an unknown device, literal
secret values, arbitrary commands, a claimed static address without an
authority reference, and control capabilities without an explicit allowlist.
An output is a proposal, never authorization or proof that NetBox, OPNsense,
Home Assistant, DNS/DHCP or the appliance changed.
