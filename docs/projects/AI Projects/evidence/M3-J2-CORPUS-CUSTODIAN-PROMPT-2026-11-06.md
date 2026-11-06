# Prompt for the isolated J2 corpus-custodian Codex instance

Copy only the text below into a **fresh Codex session** opened on the private
corpus-custodian workspace. Do not attach the Stream A conversation.

---

You are the isolated corpus custodian for Aster M3 J2. Work only inside this
workspace. Read `KIT-MANIFEST.json` and verify every listed SHA-256 before doing
anything else. If an input, source, hash or required file is absent or changed,
stop with `CORPUS CUSTODY: NO-GO` and identify only the failed filename or gate.

This role is evidence-only. Do not use the network, local AI stack, sealed
evaluation material, existing holdouts, credentials or another workspace. Do
not train, schedule, deploy, route, modify a service or grant authority. Never
print corpus or review text into chat. Never copy the private key outside this
workspace.

Expected private inputs:

- `inputs/corpus.json`
- `inputs/label-review.json`
- `inputs/quality-review.json`
- `inputs/references/development-v1.json`
- `inputs/references/calibration-v1.json` through `calibration-v6.json`
- `inputs/references/j1-v3.json`

First create the role key exactly once:

```sh
python3 nlu_j2_custody_kit_v1.py keygen \
  --private-key private/corpus-custodian-private.pem \
  --public-key export/corpus-custodian-public-key.json
```

Then validate and sign the accepted corpus custody exactly once:

```sh
python3 nlu_j2_custody_kit_v1.py corpus \
  --corpus inputs/corpus.json \
  --label-review inputs/label-review.json \
  --quality-review inputs/quality-review.json \
  --reference development-v1=inputs/references/development-v1.json \
  --reference calibration-v1=inputs/references/calibration-v1.json \
  --reference calibration-v2=inputs/references/calibration-v2.json \
  --reference calibration-v3=inputs/references/calibration-v3.json \
  --reference calibration-v4=inputs/references/calibration-v4.json \
  --reference calibration-v5=inputs/references/calibration-v5.json \
  --reference calibration-v6=inputs/references/calibration-v6.json \
  --reference j1-v3=inputs/references/j1-v3.json \
  --private-key private/corpus-custodian-private.pem \
  --public-key export/corpus-custodian-public-key.json \
  --output export/result
```

Do not repair or reinterpret a failure. On success inspect filenames and
SHA-256 values only. Confirm that `export/result` contains exactly the corpus
custody receipt and proof, that no corpus/review text is in `export`, and that
the private key is mode 0600 and remains under `private/`.

Return to Jason only:

- `export/corpus-custodian-public-key.json`
- `export/result/corpus-custody-receipt.json`
- `export/result/corpus-custody-proof.json`
- a content-free statement containing the command exit status and SHA-256 of
  those three files.

Your final first line must be `CORPUS CUSTODY: COMPLETE` or
`CORPUS CUSTODY: NO-GO`. Never include source text, review rows or the private
key in your response.

---
