# F4/F5 metadata-only authentication upgrade

**Date:** 2026-10-25

**Decision:** inactive installation **PASS**; F4/F5 effects remain **NO-GO**

The first source proposal was independently rejected because success from
`GET /v1/models` alone could not prove the key was accepted. The corrected
helper at platform tip `76072b38` requires the endpoint to return `401` with no
authorization, `401` with a fixed invalid bearer, then `200` with the real key
and the exact accepted model. It is GET-only, disables proxy inheritance,
refuses redirects and contains no inference body.

Jason approved the exact two-file inactive upgrade. LXC110 now has helper hash
`93e78f8a…82582`; Proxmox has trusted-observer hash `6091b557…18f5f`. Both are
root-owned mode-`0644` regular one-link files. The old pair is preserved in
root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/f4-f5-auth-metadata-76072b38-20261025`.

Target Linux passed 4/4 helper tests and 9/9 observer tests. The live
negative-control sequence passed and the installed observer returned only
`auth-metadata-ok`. No model request, service restart, receipt, lease or
scanner occurred; tonight's F2 timers remained active and unchanged.

This removes the false-authentication gap from future F4/F5 observation. It
does not create F4/F5 evidence or authorize a lease, F6 or candidate H. The F6
prepare-only runner's downstream helper pin has been corrected in local source
commit `d4473311` but remains an inactive installation dependency.
