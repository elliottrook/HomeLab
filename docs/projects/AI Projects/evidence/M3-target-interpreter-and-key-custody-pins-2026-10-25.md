# M3 target interpreter and key-custody pins — 2026-10-25

**State:** static execution pins complete; no model run authorized

Read-only inspection of LXC110 fixed the remaining M3 execution identities:

- command path: /usr/bin/python3
- resolved interpreter: /usr/bin/python3.13
- version: Python 3.13.5
- resolved interpreter SHA-256:
  889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9
- symlink custody: root:root mode 0777
- target custody: root:root mode 0755
- execution identity: root in LXC110, including group 991 (ollama)
- key-file custody: ollama:ollama mode 0600 at /etc/aster-llama-api-keys

The key file was not read, hashed, printed or copied. Root's existing group and
privilege boundary permits the runner to open it directly. The runner alone
reads the file; the key is not placed in argv, logs, evidence or model input.

The staged packet remains exact:

- directory: /var/lib/aster-nlu-calibration/nlu-calibration-v1
- directory custody: root:root mode 0700
- runner and inputs: root:root mode 0600
- runner SHA-256:
  b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11
- cases SHA-256:
  6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e
- release SHA-256:
  f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1
- development SHA-256:
  1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785
- run.json and attempt-journal.jsonl: absent

The staged runner's help/import boundary passed under the pinned interpreter
with bytecode writes disabled. No credential was accessed and no endpoint or
model request occurred.

These pins close M3's static command boundary. They do not bypass D4-first
ordering or the fresh F2/F3/F4/F5, effectful F6, recovery and model-call gates.
