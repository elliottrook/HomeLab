# M3 J2 evaluation custodian — remote revision-3 prompt

Paste this into a different fresh Codex session on the MacBook. Do not resume
revisions 1 or 2, use the corpus session, or use subagents.

You are the isolated Aster M3 J2 sealed-evaluation custodian. Fail closed
without deleting anything if the local archive or destination below already
exists. Run:

```sh
test "$(hostname)" != "Jasons-Mac-mini.local"
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r3.tar.gz
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r3
scp -o BatchMode=yes jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-evaluation-custodian-20261106-r3.tar.gz /private/tmp/aster-j2-evaluation-custodian-20261106-r3.tar.gz
printf '%s  %s\n' 38ff8e6bd1a2d58134b676b819fc0ca7cd5c9096cb0f6e984f0281ab77d1527c /private/tmp/aster-j2-evaluation-custodian-20261106-r3.tar.gz | shasum -a 256 -c -
mkdir -m 700 /private/tmp/aster-j2-evaluation-custodian-20261106-r3
tar -C /private/tmp/aster-j2-evaluation-custodian-20261106-r3 --strip-components=1 -xzf /private/tmp/aster-j2-evaluation-custodian-20261106-r3.tar.gz
cd /private/tmp/aster-j2-evaluation-custodian-20261106-r3
```

Verify all thirteen files in `KIT-MANIFEST.json`, require exactly one file
under `inputs/`, then read and execute `PROMPT.md` exactly once. Never print or
return corpus/evaluation content. On success return only `export/` with:

```sh
scp -r -o BatchMode=yes export jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r3/evaluation-custodian/
```

Do not rerun after any custody command failure. Finish with `EVALUATION
CUSTODY: COMPLETE` or `EVALUATION CUSTODY: NO-GO`.
