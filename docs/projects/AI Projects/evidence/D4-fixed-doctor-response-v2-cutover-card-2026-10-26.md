# D4 fixed Doctor response v2 cutover card — 2026-10-26

## Exact effect

Run `scripts/deploy/cutover_fixed_doctor_response_v2.sh` on Proxmox once. It
operates only in LXC104 and:

1. requires the inactive candidate and the live schema-1 predecessor to match
   their exact hashes;
2. requires the new response module to be absent;
3. checkpoints the live caller under
   `/root/aster-fixed-doctor-response-v2-pre-cutover` mode `0700`;
4. atomically replaces only `fixed_doctor_caller.py` and adds only
   `fixed_doctor_response.py`;
5. restarts only `aster-fixed-doctor-caller.service`;
6. calls the fixed socket once as the existing `aster` identity and requires a
   schema-2 deterministic answer with `authority: not-granted`; and
7. verifies `aster-agent.service` stayed active with an unchanged restart count.

The predecessor caller is
`aba9b11a…b9628a`; the candidate caller is `d1b567a8…cf9e48`; the
response module is `c7855a76…c70ff`.

## Rollback

Any failure after replacement restores the checkpointed caller, removes only
the newly added response module and restarts the fixed Doctor caller again.
The candidate directory and failed evidence remain available for diagnosis.

## Exclusions

No Aster Agent, inference, Speech, News, gateway or broker restart is included.
The card changes no capability grant, routing policy, model setting, systemd
unit, credential, firewall rule or OpenBao state. This exact caller-service
restart requires owner approval before execution.
