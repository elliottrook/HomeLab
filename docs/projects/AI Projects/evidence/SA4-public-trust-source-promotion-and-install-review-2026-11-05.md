# SA4 public trust source promotion and install review — 2026-11-05

## Source result

Jason accepted the exact public identities from commit `0d5a49fd` for
source-only trust promotion. The canonical acceptance record has SHA-256
`3374e8edba5f3a4bc7050d5563f8e4d9f2d2e8168d03a173ff5e1e9a12873207`
and explicitly excludes live installation, signing, grants, checkpoints and
repairs.

The source custody slots now bind the accepted signer IDs, public JWKs and
digests with status `accepted-public-source`. The two authority registries each
contain exactly one accepted public key, and the observer registry contains
exactly one accepted public key. Callers still cannot nominate a key at
runtime. Every verifier continues to report zero maximum effects and cannot
make a repair eligible by signature validation alone.

The owner-acceptance digest is compiled into the custody source and covered by
a retained-record hash test. Unrelated synthetic signers continue to fail
against the exact source registries.

## Reversible install candidate

The source-only install plan fixes the current live empty-trust identities:

- authority source `cbc97617…6be6ee`;
- observer source `a1e99c3a…145b9d`; and
- empty custody slots `6e45ecad…e04816`.

It replaces only those three files and exclusively creates
`sa4_public_trust_candidate_v1.py`. The replacement hashes are:

- authority source `367bf1a1…a725d6`;
- observer source `ab58b635…2c355`;
- accepted custody slots `e1d9088a…b8d0d0`; and
- public trust material `3c1f02bb…35195e`.

Before replacement, it requires a root-owned mode-0700 checkpoint at
`/var/lib/aster/sa4/source-checkpoints/public-trust-v1`, with exact old files
copied mode 0600 and retained after success. Postchecks import the entire
installed module set and require authority counts 1+1, observer count 1, all
slot statuses accepted, zero effects and no service action. Any failed or
uncertain postcheck restores the exact checkpoint and removes the new file only
while its hash remains unchanged; otherwise it retains state and stops.

A fresh read-only LXC 104 check matched all three old hashes and found both the
new module and checkpoint path absent. The complete SA4 suite passes **82/82**.
No live file changed.

## Next gate

Installing these four public-source changes on LXC 104 is a remote mutation
and needs exact approval. It requires no booking, model, service, restart,
private-key access or signing ceremony. Installation makes the exact public
keys recognizable to the verifier code, but still grants no repair: no signed
approval/grant/receipt, one-use claim, checkpoint or effect is authorized.
