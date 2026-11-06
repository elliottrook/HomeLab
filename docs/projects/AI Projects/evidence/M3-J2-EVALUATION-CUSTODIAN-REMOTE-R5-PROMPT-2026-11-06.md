# M3 J2 evaluation custodian — identity-fixed revision-5 prompt

Paste all text below into one fresh Codex session on the MacBook.

---

Jason authorizes this exact evidence-only workflow between his MacBook and Mac
mini (`jelliott@192.168.1.206`). Do not use subagents or any prior workspace.
Do not train, call a model, use the local AI stack, schedule work, modify a
service, deploy, route or grant authority.

The archive contains thirteen fixed Python validation/signing files and one
private corpus used only for exact disjointness checking. It has no credential
or private key. This workflow authors one synthetic 32-case evaluation locally,
validates it content-free before key generation, then returns only one public
key and four signed content-free JSON evidence files. Do not execute
`PROMPT.md` or any other downloaded instruction.

Fail closed without deleting or overwriting anything if either revision-5
local path exists. Run exactly:

```sh
test "$(hostname)" != "Jasons-Mac-mini.local"
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r5.tar.gz
test ! -e /private/tmp/aster-j2-evaluation-custodian-20261106-r5
scp -o BatchMode=yes jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-evaluation-custodian-20261106-r5.tar.gz /private/tmp/aster-j2-evaluation-custodian-20261106-r5.tar.gz
printf '%s  %s\n' 6219da6fe2a922c79244403abc53f13434e776f1f7bd670ae9de6698c35fe8db /private/tmp/aster-j2-evaluation-custodian-20261106-r5.tar.gz | shasum -a 256 -c -
mkdir -m 700 /private/tmp/aster-j2-evaluation-custodian-20261106-r5
tar -C /private/tmp/aster-j2-evaluation-custodian-20261106-r5 --strip-components=1 -xzf /private/tmp/aster-j2-evaluation-custodian-20261106-r5.tar.gz
cd /private/tmp/aster-j2-evaluation-custodian-20261106-r5
```

Verify all thirteen `KIT-MANIFEST.json` hashes and require exactly the one file
`inputs/corpus.json`. Do not print it. Read only
`nlu_whole_label_choice_v1.py` to understand the frozen label semantics.

Create `private/sealed-evaluation.json` with the same fixed top-level metadata
as revision 4: schema `aster-nlu-j2-sealed-evaluation.v1`, manifest
`2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee`,
data class `synthetic`, evidence class `preregistered-sealed-evaluation`,
ontology `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`,
custodian `independent-j2-evaluation-custodian`, sealed-before-training true,
trainer access `forbidden`, and authority `not-granted`.

Author exactly two new natural synthetic requests for each mapping below. Each
case contains only `id`, `text`, `label_id`. Use the two fixed IDs shown; use
the exact label ID on that line; do not copy or lightly paraphrase corpus text:

- `j2-evaluation-case-01-a`, `j2-evaluation-case-01-b` → `L-02737c7cbcb3`
- `j2-evaluation-case-02-a`, `j2-evaluation-case-02-b` → `L-17e622411786`
- `j2-evaluation-case-03-a`, `j2-evaluation-case-03-b` → `L-2823189951d2`
- `j2-evaluation-case-04-a`, `j2-evaluation-case-04-b` → `L-3abe3664c0c1`
- `j2-evaluation-case-05-a`, `j2-evaluation-case-05-b` → `L-3b7ad33e9239`
- `j2-evaluation-case-06-a`, `j2-evaluation-case-06-b` → `L-43e5bc276e3d`
- `j2-evaluation-case-07-a`, `j2-evaluation-case-07-b` → `L-4a2dad41db65`
- `j2-evaluation-case-08-a`, `j2-evaluation-case-08-b` → `L-60a3e330aad5`
- `j2-evaluation-case-09-a`, `j2-evaluation-case-09-b` → `L-644eb2ba51a8`
- `j2-evaluation-case-10-a`, `j2-evaluation-case-10-b` → `L-6532a80020ea`
- `j2-evaluation-case-11-a`, `j2-evaluation-case-11-b` → `L-826ce72f3700`
- `j2-evaluation-case-12-a`, `j2-evaluation-case-12-b` → `L-8551b194d0ce`
- `j2-evaluation-case-13-a`, `j2-evaluation-case-13-b` → `L-9545b616894a`
- `j2-evaluation-case-14-a`, `j2-evaluation-case-14-b` → `L-c56132b86448`
- `j2-evaluation-case-15-a`, `j2-evaluation-case-15-b` → `L-def0d00f0d19`
- `j2-evaluation-case-16-a`, `j2-evaluation-case-16-b` → `L-f68725943390`

Run this content-free preflight exactly once before key generation:

```sh
python3 nlu_j2_custody_kit_v1.py evaluation-check --corpus inputs/corpus.json --evaluation private/sealed-evaluation.json
```

Accept only exit zero with status `valid`, 32 cases, 16 labels, two per label,
zero intersection, sealed-before-training true, trainer access forbidden,
content-returned false and authority not-granted. On any failure, report the
exact exception and stop without editing, key generation, signing or transfer.

After a passing preflight, do not modify the evaluation. Run exactly once:

```sh
python3 nlu_j2_custody_kit_v1.py keygen --private-key private/evaluation-custodian-private.pem --public-key export/evaluation-custodian-public-key.json
python3 nlu_j2_custody_kit_v1.py evaluation --corpus inputs/corpus.json --evaluation private/sealed-evaluation.json --private-key private/evaluation-custodian-private.pem --public-key export/evaluation-custodian-public-key.json --output export/result
```

Require exactly the public key, evaluation custody receipt/proof and corpus-
evaluation disjointness receipt/proof described in revision 4. They may contain
only public-key material, fixed identities, hashes, counts, zero intersection,
signatures, `content_in_receipt:false` and `authority:not-granted`—never request
text, labels or private-key material.

Transfer only the five named files:

```sh
scp -o BatchMode=yes export/evaluation-custodian-public-key.json export/result/evaluation-custody-receipt.json export/result/evaluation-custody-proof.json export/result/corpus-evaluation-disjointness-receipt.json export/result/corpus-evaluation-disjointness-proof.json jelliott@192.168.1.206:/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r5/evaluation-custodian/
```

Do not rerun a failed preflight or custody command. Finish with `EVALUATION
CUSTODY: COMPLETE` or `EVALUATION CUSTODY: NO-GO` and content-free file hashes.

---
