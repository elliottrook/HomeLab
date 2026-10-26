# Stream A evaluation composition — inactive install card V3

Status: **SOURCE AND TARGET PREFLIGHT PASS; FRESH EXPLICIT INSTALL APPROVAL REQUIRED**

Source commit: `b21a6227`  
Supersedes: the rolled-back `37452660` packet recorded at `770af438`

This card installs code only. It does not create a runtime wrapper or unit,
produce F3/F4/F5/admission evidence, arm F6, acquire a lease, stop a consumer,
read a completed private result, call a model, change F2, or invoke the D4/M3
composition.

## Corrected dependency boundary

The prior transaction rolled back because its import check exposed only the
composition directory, while the evidence loader deliberately reuses the
already installed, pinned F2/F4/archive-integrity modules in the parent
`/usr/local/libexec/local-ai-lease` directory. The host outcome verifier also
imported a schema constant from guest-only source.

V3 pins both installed module roots. It makes the host outcome verifier
dependency-closed and tests that its immutable schema remains equal to the
guest schema. The future runtime entrypoint must use exactly:

```text
PYTHONPATH=/usr/local/libexec/local-ai-lease/stream-a-evaluation:/usr/local/libexec/local-ai-lease
```

No arbitrary or environment-derived path is accepted.

## Exact installation packet

All host files target
`/usr/local/libexec/local-ai-lease/stream-a-evaluation/` as root:root regular
mode `0644` files:

| File | SHA-256 |
|---|---|
| `stream_a_evaluation_live_plan.py` | `0f8d7e558bff48d6be9f86da62041ccaa20aa6b18780b738756d1118f0bf0ef2` |
| `stream_a_evaluation_sequence.py` | `63eedd771d3cca25183e7f551b076c19d84e9c2855d9c7985e8cce445239aef1` |
| `stream_a_evaluation_effect_driver.py` | `06318de809a22321b254713a9af9b87aecfa150c1cfd298c164fcab16d961f0e` |
| `stream_a_evaluation_handlers.py` | `6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4` |
| `stream_a_evaluation_evidence_loader.py` | `836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01` |
| `stream_a_evaluation_host_outcome.py` | `a9584bf01fea83129b8efb9a4c315ab66a37369ee386319f5632222618742225` |
| `stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `stream_a_evaluation_runtime.py` | `7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210` |
| `stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |

Both LXC104 and LXC110 receive exactly:

| Target | Mode | SHA-256 |
|---|---:|---|
| `/usr/local/libexec/stream-a-evaluation-guest-outcome` | `0755` | `027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9` |
| `/usr/local/libexec/stream_a_evaluation_outcome_verifier.py` | `0644` | `9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1` |

## Required unchanged dependency pins

The transaction must re-read these existing root:root `0644`, one-link regular
files before and after installation. They are dependencies, not install
targets.

Composition root:

| File | SHA-256 |
|---|---|
| `evaluation_lease.py` | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` |
| `evaluation_lease_adapter.py` | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` |
| `evaluation_lease_watchdog.py` | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` |
| `stream_a_evaluation_watchdog.py` | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |
| `stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |

Parent root:

| File | SHA-256 |
|---|---|
| `f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |
| `pre_acquire_receipt.py` | `7c70b6c8097ec9b5b9d2dd6e980f59a6b15ebd8397fbf5acbced98a2e7cc2170` |
| `retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `f2_preflight_fixed_wrapper.py` | `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34` |
| `f2_preflight_snapshot.py` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` |
| `lease_contract.py` | `420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b` |
| `lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |

## Validation and transaction

A clean archive from `b21a6227` (SHA-256
`aaa0190099c1643224846310a468fe12ecae1bf25bd9c42638674f32621bdade`)
passed 96/96 tests on Proxmox. A temporary nine-file composition imported
successfully against the two exact installed dependency roots above and wrote
no bytecode. Nothing was installed during that proof.

The exact reviewed transaction is
`STREAM-A-EVALUATION-COMPOSITION-INACTIVE-INSTALL-TRANSACTION-V3-20261025.sh`,
mode `0755`, SHA-256
`b8cc35ea45278352fbee005fdc464a4bd3a1ec5fc877e323df7d7daa610d07eb`.
It is source-only in Git and is not installed as an executable on Proxmox.

The installation transaction must recheck the prior measured absences, the
observer baseline SHA-256 `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`,
all dependency pins, inactive F6 units, ready lease, absent state/locks,
healthy production and unchanged October 26 F2 timers. It must create a fresh
root-only checkpoint, run 96/96 from the clean archive, install the same 13
paths atomically, import through only the two fixed module roots, and require
the exact inert guest result in both guests with an empty `PYTHONPATH`.

On any mismatch, restore only the checkpointed observer, remove only the twelve
targets proven absent, and re-run the full postcheck. Preserve both rollback
checkpoints and the failure evidence. Do not retry the old packet.
