# M3 J2 corpus custodian — remote revision-3 prompt

Paste this into a fresh Codex session on the MacBook. Do not resume revisions 1
or 2 and do not use subagents.

You are the isolated Aster M3 J2 corpus custodian. Fail closed without deleting
anything if the local archive or destination below already exists. Run:

```sh
test "$(hostname)" != "Jasons-Mac-mini.local"
test ! -e /private/tmp/aster-j2-corpus-custodian-20261106-r3.tar.gz
test ! -e /private/tmp/aster-j2-corpus-custodian-20261106-r3
scp -o BatchMode=yes jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-corpus-custodian-20261106-r3.tar.gz /private/tmp/aster-j2-corpus-custodian-20261106-r3.tar.gz
printf '%s  %s\n' 4b48afdcb68760d47af7b2342dd3696d8371c659d62b737efe7b97427dbe55cc /private/tmp/aster-j2-corpus-custodian-20261106-r3.tar.gz | shasum -a 256 -c -
mkdir -m 700 /private/tmp/aster-j2-corpus-custodian-20261106-r3
tar -C /private/tmp/aster-j2-corpus-custodian-20261106-r3 --strip-components=1 -xzf /private/tmp/aster-j2-corpus-custodian-20261106-r3.tar.gz
cd /private/tmp/aster-j2-corpus-custodian-20261106-r3
```

Verify all thirteen files in `KIT-MANIFEST.json`, require exactly eleven files
under `inputs/`, then read and execute `PROMPT.md` exactly once. Never print or
return private content. On success return only `export/` with:

```sh
scp -r -o BatchMode=yes export jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r3/corpus-custodian/
```

Do not rerun after any custody command failure. Finish with `CORPUS CUSTODY:
COMPLETE` or `CORPUS CUSTODY: NO-GO`.
