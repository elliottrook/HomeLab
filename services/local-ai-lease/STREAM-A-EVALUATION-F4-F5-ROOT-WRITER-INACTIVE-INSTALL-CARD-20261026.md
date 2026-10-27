# Stream A F4/F5 root writer inactive installation card

Status: **REVIEWED CANDIDATE / INACTIVE INSTALLATION NOT YET AUTHORIZED**

Source: `codex/f4-f5-root-writer` at
`bef95f8c9a3f1d83cd7c5277dff21971ff18bdd4`.

This card installs three new files. It does not invoke the writer, create F4,
F5 or admission evidence, acquire a lease, create a lock, stop or restart a
service, enable a timer, call a model, or change any schedule.

## Exact new files

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/stream_a_evaluation_f4_f5_transaction.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_f4_f5_transaction.py` | 0644 | `db4066d05ec37e27c1301a4bf79f35c7d418aa797bca49f43d8f33326c0cbbaa` |
| `scripts/local-ai/stream_a_evaluation_f4_f5_root.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_f4_f5_root.py` | 0644 | `d57e95c196a079bce6460b5d2cca514d27a27db1c39fdfa815ec0a365c5b3d18` |
| `services/local-ai-lease/stream-a-evaluation-evidence` | `/usr/local/sbin/stream-a-evaluation-evidence` | 0755 | `7685d5896931b8c684a00ed4428192a58dd7a503464160a5c27fa48b12c56685` |

Read-only inspection on October 26 found all three targets absent. The
whole-host lease was exactly `ready`; whole-host and evaluation lease, lock and
operation-lock files were absent; and the F4, F5 and admission targets were
absent.

## Installed dependency pins

The inactive transaction must require these existing regular, one-link,
root-owned mode-`0644` dependencies without replacing them:

| Installed path | SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| `/usr/local/libexec/local-ai-lease/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `/usr/local/libexec/local-ai-lease/lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `/usr/local/libexec/local-ai-lease/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `/usr/local/libexec/local-ai-lease/trusted_observer.py` | `6091b5572764abf3675d9140e760083a1482fee8abfef8fc763fb72853618f5f` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |

The new source does not import or replace the installed `lease_contract.py`,
`pre_acquire_receipt.py`, or `stream_a_evaluation_evidence_loader.py`; their
installed revisions differ from the development branch and are outside this
change.

## Inactive transaction

1. Recheck the three targets are absent, all dependency hashes and custody
   match, the whole-host lease is exactly ready, and no whole-host/evaluation
   lease or lock exists.
2. Recheck F4, F5 and admission do not exist. Stop for review if any target or
   runtime evidence is present; never delete it under this card.
3. Copy only the three hash-pinned files through temporary files in their
   target directories, set the stated owner/mode, and publish with no-replace
   links.
4. Run `sh -n` on the wrapper. With the two fixed installed Python roots in
   `PYTHONPATH`, import both new modules using `python3 -B` and run the root
   writer, transaction, admission, evidence-loader, fixed-source, trusted-
   observer, F2, F3 and retained-integrity tests from a temporary source tree.
   Do not invoke the installed wrapper without an argument. Its argument
   rejection may be checked because it exits before Python is executed.
5. Recheck exact target hashes/custody, unchanged dependency hashes, lease
   `ready`, absent lease/locks and absent F4/F5/admission. Recheck the three
   Aster production services and fixed News/backup schedules remain healthy.

## Rollback

On any failed hash, custody, import, test or postcheck, remove only the three
new targets after proving they still match this card. Leave all dependencies
and runtime evidence untouched. Recheck lease, production and schedules. An
unexpected evidence file, changed new target, lease/lock, service transition
or schedule drift is an uncertain state requiring reconciliation rather than
automatic deletion.

Successful inactive installation authorizes no evidence production. A later
approval must name one bounded invocation after a completed same-cycle F2/F3
and 03:00 pull. F6 remains a further, separate restart/effect gate.
