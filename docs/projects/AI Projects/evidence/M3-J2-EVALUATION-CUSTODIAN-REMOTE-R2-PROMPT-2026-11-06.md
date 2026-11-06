# M3 J2 evaluation custodian — MacBook remote revision-2 prompt

Copy the text below into a different fresh Codex session on the MacBook. The
failed revision-1 session is terminal evidence and must not be resumed.

---

You are the isolated sealed-evaluation custodian for Aster M3 J2. Do not use
subagents, the corpus-custodian session or any prior workspace. This is a fresh
revision-2 attempt. The Mac mini is only a source and content-free return
endpoint at `jelliott@192.168.1.206`.

Fail closed if this machine identifies as `Jasons-Mac-mini.local`, if either
revision-2 local destination already exists, if SSH is unavailable, or if the
archive hash differs. Do not delete or overwrite an existing destination.

Run exactly:

```sh
test "$(hostname)" != "Jasons-Mac-mini.local"
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r2.tar.gz
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r2
scp -o BatchMode=yes \
  jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-evaluation-custodian-20261106-r2.tar.gz \
  /private/tmp/aster-j2-evaluation-custodian-20261106-r2.tar.gz
printf '%s  %s\n' \
  60bcace51d33fcf6c3dd9716cfd7849f76d521f44456beb60ad1dd75653b6048 \
  /private/tmp/aster-j2-evaluation-custodian-20261106-r2.tar.gz | shasum -a 256 -c -
mkdir -m 700 /private/tmp/aster-j2-evaluation-custodian-20261106-r2
tar -C /private/tmp/aster-j2-evaluation-custodian-20261106-r2 \
  --strip-components=1 -xzf \
  /private/tmp/aster-j2-evaluation-custodian-20261106-r2.tar.gz
cd /private/tmp/aster-j2-evaluation-custodian-20261106-r2
```

Read `KIT-MANIFEST.json`; verify every listed file against its recorded
SHA-256; require exactly one regular file under `inputs/`; then read
`PROMPT.md` completely and perform it exactly once. Never print corpus or
evaluation text and never transfer `inputs/`, `private/`, the sealed evaluation
or the archive back to the Mac mini.

Only after `PROMPT.md` completes successfully, return the content-free export:

```sh
scp -r -o BatchMode=yes export \
  jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r2/evaluation-custodian/
```

If the final transfer fails, retain the local workspace unchanged and report
the transfer failure; do not rerun custody. Your final first line must be
`EVALUATION CUSTODY: COMPLETE` or `EVALUATION CUSTODY: NO-GO`.

---
