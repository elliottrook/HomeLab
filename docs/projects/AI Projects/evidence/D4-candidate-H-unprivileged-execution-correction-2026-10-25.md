# D4 candidate-H unprivileged execution correction — 2026-10-25

**State:** source-only corrected proposal; tests pass; not installed or authorized

## Finding corrected

The first descriptor launcher still started the candidate process as root. A
root child could reopen `/etc/aster/aster.env`, so environment exclusion alone
did not protect the service credential. That proposal is NO-GO and was never
installed or run.

The corrected proposal keeps the small opener privileged only long enough to
validate the frozen packet and interpreter, open the existing root:aster
mode-0640 credential file, extract one bounded value, create a pipe and start
the child. The child itself runs as a new fixed `aster-d4-eval` identity,
UID/GID 977, with an empty supplementary-group list and a non-login shell.
Read-only inspection on October 25 confirmed UID and GID 977 are unused in
LXC104 and that the credential remains root:aster mode 0640. Therefore the
child cannot reopen the credential file after the identity transition.

## Filesystem and process boundary

- `/var/lib/aster/d4-candidate-h` must be root:aster-d4-eval mode 0750.
- Its exact eleven frozen inputs must be root:aster-d4-eval mode 0640 with the
  recorded byte lengths and SHA-256 values.
- `/var/lib/aster/d4-candidate-h-output` must be an empty, non-symlink directory
  owned by aster-d4-eval:aster-d4-eval mode 0700.
- The durable journal is written only in that separate output directory. The
  unprivileged child cannot change the source packet.
- `subprocess.Popen` selects UID/GID 977, clears supplementary groups, applies
  umask 0077 and starts a separate session before exec.
- The child receives only the pipe descriptor number. Its environment is a
  small non-secret allowlist and does not contain `ASTER_LLAMA_API_KEY`.
- The root parent overwrites its mutable source and extracted buffers and
  closes every descriptor on all exits.

The proposed oneshot unit has no `[Install]` section. It uses
`NoNewPrivileges=yes`, a strict read-only system view, a private temporary
directory and devices, a 2,250-second service deadline, group-wide termination,
and a capability bound containing only `CAP_SETUID` and `CAP_SETGID`, which are
needed for the fixed identity transition. Only the dedicated output directory
is writable. The child inherits no capabilities after the UID change.

## Frozen source identities

| Source | SHA-256 |
| --- | --- |
| `scripts/deploy/launch_d4_candidate_h.py` | `71c07060a59a81923803fdd21cc14f218fc3c1c1f7f1797e1b1e75acdf4240eb` |
| `scripts/deploy/test_launch_d4_candidate_h.py` | `70d7fe9b696003fcbb4c0455fb572151a07114398ffd160350281270957ae1c2` |
| `services/aster-agent/systemd/aster-d4-eval.sysusers.conf` | `c4bfc0aa4446d77c252f9cd233842ac101e849ddeddf4347ad30d80298410c64` |
| `services/aster-agent/systemd/aster-d4-candidate-h.service` | `76c0ba89b26124b1e0fb74e3ddc761a001d937195c4d14ce0c3b5ab0d6b62450` |

The candidate-H run digest remains
`423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`.

Nine focused synthetic tests pass. They cover exact manifest binding, source
packet custody, unique fictional-key parsing, real pipe delivery, environment
exclusion, buffer clearing, private empty output custody, fixed sysusers
configuration, supplementary-group rejection, the exact Popen identity
transition and the bounded non-installable unit. The complete evaluation suite
also passes 168/168. Tests use only fictional credential bytes.

## Remaining gate

This is a source proposal, not a live authority. A separate reviewed inactive
installation must create the dedicated account, packet and output custody and
copy only the pinned launcher and unit. Target-Linux validation must prove the
account has only GID 977, cannot read `/etc/aster/aster.env`, can read the frozen
packet, can write only the output directory, and that a fictional descriptor
probe runs as UID/GID 977. It must leave the unit disabled and must not open the
real credential, start a model request or create a D4 journal. The actual D4
run remains separately gated by fresh F2/F3/F4/F5/F6 evidence and an exact
model-call approval.
