# AsterTV Version 2 release-readiness evidence

> Historical snapshot from 2026-10-27. The HP was subsequently reinstalled
> with LibreELEC 13/Kodi 22, v2 was pulled from production and v1.1.1 restored.
> Use [Current Resume](Aster-TV-Version-2-Current-Resume.md) and the current
> `services/kodi/releases/aster-home-v2.0.2-lab-candidate.json` for active gates.
> On 2026-10-29 the pinned code-only archive passed an isolated filesystem
> install and rollback rehearsal on macOS and the HP lab, including interrupted
> install recovery. Full clean-client Kodi/systemd activation remains open.

> Status: unattended engineering checks pass; owner, hardware and clean-install gates remain
> Date: 2026-10-27
> Scope: HP lab only; production unchanged

## Outcome

The finite readiness record reports all seven unattended engineering gate groups
passed. It does **not** label Version 2 release-ready or production-authorized:
four owner/hardware checks, one destructive clean-client rehearsal, the final
owner walkthrough and production promotion remain explicitly open.

This distinction is intentional. Successful automation is evidence for the
candidate; it is not a substitute for household acceptance, a physical voice
remote, a disposable clean LibreELEC target or the owner's production decision.

## Live prerequisite audit

A read-only audit of HP `192.168.1.140` confirmed:

- x86-64 LibreELEC 12.2.1;
- Kodi's service active with zero service restarts;
- official YouTube 7.4.4 and Jellyfin 2.2.0+py3;
- the loopback camera proxy enabled, active, ready and idle, with no fetched
  image retained in its status;
- both fixed read-only Books automounts enabled, active and mounted;
- Aster startup and screensaver add-ons present; and
- no failed systemd units.

The complete Kodi v2 suite also passes 1,338 tests under normal and optimized
Python, with the same one expected environment-dependent skip in each run.

No credential, account profile, watch history, listening progress or media
database was read. Kodi was not restarted and no live state was changed.

## Machine-readable boundary

`services/kodi/v2/hp_release_readiness.json` is validated by
`release_readiness.py`. A passed gate requires positive evidence and cannot
carry a blocker. Every open gate requires an explicit blocker. A gate marked
destructive cannot be represented as passed by this pre-release record, and a
promotion gate is mandatory.

The generated summary currently returns:

```json
{
  "engineering_checks_passed": true,
  "release_ready": false,
  "production_authorized": false
}
```

## Remaining gates

1. Test voice capture/search with the physical lab remote and a separately
   provisioned restricted speech identity.
2. Complete owner sofa-distance YouTube playback, Back and stop review.
3. Reconcile the reinstalled N95 host identity and capture the final composed
   client under representative playback.
4. Complete multi-day household beta use and the finite page-by-page review.
5. Run the ordered Bundle6 recipe on a disposable clean LibreELEC target,
   including Kodi discovery, systemd activation, separate restricted identity
   provisioning, verification and rollback.
6. Make a separate production-promotion decision.

The HP remains the lab candidate. BOSGAME production was not inspected or
modified by this work.
