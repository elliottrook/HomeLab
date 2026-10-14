# Local AI lease recovery — staging review manifest

Status: offline review candidate; not installed, enabled, or authorized for a
live effect.

## Candidate identity

- Source commit: `752a1145`; this manifest is not a deployment authorization.
- Accepted live runtime: LXC 110, llama.cpp `b11429`, SYCL/Level Zero,
  Qwen3.5 9B Q4_K_M; live unit hash
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`; live
  binary hash
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`; exact
  dereferenced GGUF SHA-256
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`.
- Fixed trusted sources: Proxmox `pvesh`, LXC 104/110/116 and 114 probes,
  TrueNAS `192.168.20.40` through a dedicated batch-mode observer identity,
  and the owner heartbeat.
- TrueNAS host-key enrollment must be a bounded operator step: create a
  root-owned mode-0600 `/etc/local-ai-lab/truenas_known_hosts` containing only
  the verified `192.168.20.40` key. The cross-host fingerprint comparison is
  `SHA256:QBtPEVZCzn5suuM98WY2bGSSvdgOLZ5xpLd17Xu0Xbo`; the fixed probe uses
  strict host-key checking and never accepts a blind key.
- Fixed schedule identity: Proxmox `00:30`; TrueNAS guest `01:00`, LXC 110
  `02:00`, Mac `03:00`; News `06:15` and `17:15`.
- The host-local recovery executor is the disabled systemd unit's candidate
  `ExecStart`; without the unit being enabled it cannot run. Its explicit
  effect gate is retained in the candidate command line, while installation
  remains refused/disabled pending review.
- The shared Aster benchmark gate is separate from the effect controller and
  remains fail-closed. The fixed-command adapters are metadata/preflight
  collectors only; they do not own a trusted execution boundary and cannot
  authorize admission. A light-drain drill cannot be reported as a full
  shared-lease admission test until that boundary exists.
- Candidate source-receipt adapters now require the fixed backup chain,
  integrity receipt, same-night timing, exact consumer set, News quiescence and
  explicit no-new-start observation. The live TrueNAS observer credential is
  transport-only; the fixed collectors are preflight only and cannot attest
  admission. The observer now has a second exact target for fixed-path LXC110
  mirror metadata; arbitrary paths remain rejected. An offline verifier also
  defines the required content-free summary for the Mac pull at
  `/mnt/Recovery/configuration/mac/`; it is not live-wired until a separately
  authorized fixed-path observer extension exists.

## Exact local candidate hashes

These SHA-256 values cover the source and disabled unit reviewed for staging:

| File | SHA-256 |
|---|---|
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` |
| `scripts/local-ai/lease_contract.py` | `8a8997bdf453a499ae60dc2f11a65da9e28e318044a194122a7635b545adf113` |
| `scripts/local-ai/lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `scripts/local-ai/lease_controller_candidate.py` | `73419722580776b78b8ef405f9b65213b5cec9a23749d9bbf1fee958982af8e4` |
| `scripts/local-ai/trusted_observer.py` | `fdc64fc200b87d0faba64a02762df3197fc49366dd0bec12b491ed83fb1aa93f` |
| `scripts/local-ai/lease_watchdog_cli.py` | `e79521ae4cfacb61e1232df3b62cdfbb2d5181c0697770b8c1ff6c88c575990d` |
| `scripts/local-ai/lease_effect_runner.py` | `81eac0e15e86ea48ce267d1a03da74cfcbe408ad9c57c9eca832a9c8f8c2c662` |
| `scripts/local-ai/test_lease_effect_runner.py` | `f59eaa9048ff0cd1c93dc49462151350eee54c627d52466fdbbdf874562060b8` |
| `scripts/local-ai/lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |
| `scripts/local-ai/test_lease_recovery_executor.py` | `a5d5865831a77d465fbf336209ad4ae4d309b3b1e198c96a2e3f9b242e82ba4b` |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` |
| `scripts/local-ai/test_admission_gate.py` | `3b6f47a9283bc48114f53da654a26aee8cbcf2808eddf452d11440f58ffa580f` |
| `scripts/local-ai/source_receipts.py` | `51052b26ee52ca0e2b4b561f6d5e9f303aadd20badfa9856bd15f551427629a4` |
| `scripts/local-ai/test_source_receipts.py` | `7c8abd7dc5c1a7ce0261da6b85940e1a0e4893b4fd07741a7e4f3ea60c7dd5f7` |
| `scripts/local-ai/test_trusted_observer.py` | `c0e585a8c32b361a670a585b1934cb0c02e65514ba3137652961675dd31f2405` |
| `scripts/local-ai/backup_receipt_adapter.py` | `9bc07d567657deee07a757cb2518c078c37ef187d1922ff849d150313ec60a64` |
| `scripts/local-ai/test_backup_receipt_adapter.py` | `40486f9f3eb8d41ef0e5471cc8ce943ef0deaf1b994c742d280f6586312a0f4b` |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `7bc97c6b7c470322a42b635cc3a0b6788d027d83f33191214682c3fad4f5caf0` |
| `scripts/local-ai/test_quiescence_receipt_adapter.py` | `4eb53b5b7105475e0f75e28210fd23f9e40624a46cc55f291dcea783d333e66e` |
| `scripts/local-ai/fixed_source_adapters.py` | `64daf43291eec808e122c1e0fe844e614327049a907d36817fdbaacc46ac73e0` |
| `scripts/local-ai/test_fixed_source_adapters.py` | `f3d365763086f40652e2f57ee82ad14a0022a5104fe6cc2d5a54642fd89d3f46` |
| `scripts/local-ai/truenas_observer_contract.py` | `4151412e9b5638af625fd4f356c2e856c5a51f6c1de36c50103fa7d71f38f733` |
| `scripts/local-ai/test_truenas_observer_contract.py` | `e3c2f17a908b48e31416cc626a8a444f04f66b7a494d5f11bc50db47a1b73e24` |
| `scripts/local-ai/test_truenas_mac_pull_observer.py` | `f776c4b2e0ee90c6393bad3f359ec6d74695525b5ff5df4370cd384da95233a2` |
| `services/local-ai-lease/truenas_mac_pull_observer.py` | `3fc55573a6b0167ff7f06e43ea79cdc80f6274f63f6fc9a391887a32823e3991` |
| `services/local-ai-lease/aster-mac-pull-observer-root` | `d3c1577de35a7eb1cead7bb7c3bc8481fa88239a759f98f1bb204a843f8d3dbf` |
| `scripts/local-ai/source_receipt_boundary.py` | `bd055c61492f9d4072b25c4b699c4672b940e04436a511a07b7e73660b12a8b0` |
| `scripts/local-ai/test_source_receipt_boundary.py` | `f918dc7cd12fd33486ebd3d26053a5624cd2ce7b8387854a3ebcbccad9f726dc` |
| `services/local-ai-lease/STAGE-1-RUN-CARD.md` | `86daed04c47ad050a96ecd9d90dfcfc8ec78f4c053e1876dc52f41bcad21c1e8` |
| `services/local-ai-lease/local-ai-lease-recovery` | `46ddd8a031ecdeb2f227fadb18f5bc76ee9ad6042bf59d7056522c13ffe5b81c` |
| `services/local-ai-lease/local-ai-lease-watchdog.service` | `3041ed62efadcb1bcffe0c66e9c311933fc90c0cb101ea08f24b546fc9bc656d` |
| `services/local-ai-lease/local-ai-lease-watchdog.timer` | `9f09de46e3ee55d8f765e1f279d34632ea914c8c6506416f0455853ef538b744` |

The values above describe the reviewed local payload and are not a deployment
authorization. The manifest itself is excluded from the hash table because
editing the table would necessarily change its own digest.

## Required staging facts before live review

- The accepted model artifact identity must include the exact SHA-256 of the
  deployed GGUF at `/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf`.
  The live read-only measurement recorded the same digest as the repository's
  pinned Ollama blob. The observer gives this large file a dedicated finite
  30-second hash budget; other probes remain 5 seconds.
- The fixed TrueNAS probe must be verified from the Proxmox owner context using
  batch-mode SSH to `aster-schedule-observer@192.168.20.40` with
  `/etc/local-ai-lab/truenas_schedule_observer`, the pinned
  `/etc/local-ai-lab/truenas_known_hosts`, and `midclt call rsynctask.query`.
  The historical `truenas` alias and root SSH identity are not restoration
  probes. The dedicated account is forced-command bound; its only passwordless
  sudo target is the root-owned wrapper
  `/mnt/Media/.local-ai-lease/aster-schedule-observer-root`. The allowed query
  succeeded, the fixed LXC110 mirror listing matched the Proxmox artifact
  name and byte size, and alternate commands/paths were rejected. Schedule and
  mirror metadata transport are therefore healthy preflight evidence; task-
  specific same-day completion, archive provenance and quiescence remain
  separate gates.

## Recovery deadline and rollback

- Lab lease deadline: `04:15` local fixed-offset time.
- At deadline, new lab work stops and restoration begins immediately.
- No lease lock may be released until the fixed observer confirms the control
  plane, all previously active production services, GPU visibility, exact
  model/binary/unit identity, authenticated generation, and all six schedule
  points.
- Any timeout, ambiguous unit state, unmatched journal intent, missing backup
  receipt, schedule drift, or failed postcheck retains the lock and requires
  operator reconciliation.
- If the TrueNAS schedule receipt is unavailable, the executor may still
  restore the previously active local production services, but it must retain
  the lease lock and report degraded/unknown schedule state. No new root-to-
  root SSH grant is created merely to clear that postcheck; a separately
  approved least-privilege receipt or operator verification is required.
- Rollback is to disable the candidate timer, retain the lease lock, restore
  the saved controller/unit files and use the existing manual release path
  only after the production health and schedule checklist passes.

## Bounded live-drill plan — future gates

Stage 1 is a preliminary attended light service-drain test after the backup
chain completes and before `04:15`. It may stop and restore only the three
allowlisted Local AI service units; it may not reboot the host, enable a timer,
change schedules, alter credentials, modify firewall/DNS, or touch unrelated
guests. It proves the controller/effect boundary only, not timer-driven
independence.

Stage 2 is a separate, explicitly approved timer-independence drill. After
Stage 1 passes, the operator temporarily enables only the candidate timer for
one bounded window, induces one controlled owner-loss/lease-expiry condition,
observes the executor's recovery and postchecks, then disables the timer and
verifies the unit is inactive. It still may not reboot the host, change
schedules, alter credentials, modify firewall/DNS, or touch unrelated guests.
Both stages require pre/post checkpoints and abort on any failed probe; neither
stage is authorized by this manifest.
