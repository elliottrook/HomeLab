# SA2 breadth installed retry NO-GO and grammar correction — 2026-10-29

## Installed result

Jason approved the one-file correction at source commit `e1b21006`. Stream A
preserved the exact installed predecessor in
`/var/lib/aster/sa2-boundary-pre-e1b21006-20261029`, installed the pinned file,
restarted only Aster Agent, and ran the four-source connected investigation.

The run accepted the NetBox and gateway-configuration decisions and then
failed closed on its third proposal. The model described the remaining source
as a “fixed sanitized journal aggregate.” The candidate still classified the
adjective `fixed` as a completed repair because its exception covered only a
short noun allowlist. No log producer ran, no terminal decision was accepted,
and every accepted decision retained authority `none` and effect `none`.

The installed file was rolled back immediately to SHA-256
`2050cd7e12b5207dce21c5087d4e643ffa85965376d415c0ed7ee673d9894515`.
Aster Agent restarted healthy with restart count zero, the accepted llama/SYCL
service was not restarted or changed, and the whole-host lease returned
`ready`. The V2 evidence publishers and four source adapters remain installed;
only their connected graduation gate is open.

## Grammar-based candidate

The replacement removes the evidence-noun allowlist. It first finds one of the
bounded action words and rejects it only when its preceding grammar forms an
action claim: a sentence-leading action, a first-person action, a passive
completion, or an action attached to a service/system/change subject. Explicit
`not` and `never` remain non-actions, while “not only … but also …” remains a
positive claim and fails closed.

This distinguishes descriptions such as “fixed public configuration identity,”
“fixed sanitized journal aggregate,” and “installed service identity” from
claims such as “the service was restarted,” “the service is now fixed,”
“Restarted the service,” and “We have deployed the correction.” The trusted
decision still hard-codes authority and effect to `none`; this change affects
only whether a bounded hypothesis sentence is accepted.

Exact candidate files:

| File | SHA-256 |
|---|---|
| `services/aster-agent/sysadmin_proposal_boundary.py` | `a904a1296bf27bb13c0c2a475f3c168f65dde1c53bfcd9e8d4dacacb67e17652` |
| `services/aster-agent/test_sysadmin_proposal_boundary.py` | `3a111c78919378aeb0ae9a2cae324ee3edbc7e6fd36cf1b348f3260be71abd39` |

Validation:

- 86/86 local sysadmin tests pass;
- 14/14 target-Linux proposal-boundary tests pass from a temporary path;
- three independent fresh-state connected runs completed four decisions and
  three consumed observations each;
- every run observed exactly NetBox/network `ok`, gateway/config `ok`,
  backup/backup `fail`, and gateway/log `ok`;
- every run ended `complete`, authority `none`, effect `none`, and a healthy
  idle model postcheck;
- the installed predecessor stayed in production throughout these temporary-
  path trials.

## Next bounded effect

The remaining release changes one file only. Preserve the current predecessor
in a new root-owned checkpoint, install the candidate hash above as root-owned
mode `0644`, restart only `aster-agent.service` once, then run one installed
four-source connected check and production postchecks. Roll back the file and
restart Aster once on any failure.

No model/backend change or restart, routing change, repair, tool grant,
Companion action, Lab Hours action, or Git push is included.

