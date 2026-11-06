# M3 J2 corpus custodian — MacBook remote revision-2 prompt

Copy the text below into one fresh Codex session on the MacBook. The failed
revision-1 session is terminal evidence and must not be resumed.

---

You are the isolated corpus custodian for Aster M3 J2. Do not use subagents or
any prior workspace. This is a fresh revision-2 attempt. The Mac mini is only a
source and content-free return endpoint at `jelliott@192.168.1.206`.

Fail closed if this machine identifies as `Jasons-Mac-mini.local`, if either
revision-2 local destination already exists, if SSH is unavailable, or if the
archive hash differs. Do not delete or overwrite an existing destination.

Run exactly:

```sh
test "$(hostname)" != "Jasons-Mac-mini.local"
test ! -e /private/tmp/aster-j2-corpus-custodian-20261106-r2.tar.gz
test ! -e /private/tmp/aster-j2-corpus-custodian-20261106-r2
scp -o BatchMode=yes \
  jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-corpus-custodian-20261106-r2.tar.gz \
  /private/tmp/aster-j2-corpus-custodian-20261106-r2.tar.gz
printf '%s  %s\n' \
  b0811a1f91c5c98c0553c6d30d8f7bf9efb0c831a3399fa9fcc25e5e836e1d30 \
  /private/tmp/aster-j2-corpus-custodian-20261106-r2.tar.gz | shasum -a 256 -c -
mkdir -m 700 /private/tmp/aster-j2-corpus-custodian-20261106-r2
tar -C /private/tmp/aster-j2-corpus-custodian-20261106-r2 \
  --strip-components=1 -xzf \
  /private/tmp/aster-j2-corpus-custodian-20261106-r2.tar.gz
cd /private/tmp/aster-j2-corpus-custodian-20261106-r2
```

Read `KIT-MANIFEST.json`; verify every listed file against its recorded
SHA-256; require exactly eleven regular files under `inputs/`; then read
`PROMPT.md` completely and perform it exactly once. Never print private input
text and never transfer `inputs/`, `private/` or the archive back to the Mac
mini.

Only after `PROMPT.md` completes successfully, return the content-free export:

```sh
scp -r -o BatchMode=yes export \
  jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r2/corpus-custodian/
```

If the final transfer fails, retain the local workspace unchanged and report
the transfer failure; do not rerun custody. Your final first line must be
`CORPUS CUSTODY: COMPLETE` or `CORPUS CUSTODY: NO-GO`.

---
