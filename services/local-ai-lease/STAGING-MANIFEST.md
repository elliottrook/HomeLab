# Local AI lease recovery — staging review manifest

Status: offline review candidate; not installed, enabled, or authorized for a
live effect.

## Candidate identity

- Source commit: `86e12eb6`; this manifest is not a deployment authorization.
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
  currently refuses all admission: `admission_gate.py` is only a candidate
  shape guard, not an authenticated source adapter. A light-drain drill cannot
  be reported as a full shared-lease admission test until same-night source
  adapters bind verified backup, News-quiescence and consumer-isolation
  evidence to the lease.
- Candidate source-receipt adapters now require the fixed backup chain,
  integrity receipt, same-night timing, exact consumer set, News quiescence and
  explicit no-new-start observation. They are tested contracts only; the live
  TrueNAS observer credential is transport-only and does not constitute a
  source adapter. The observer now has a second exact target for fixed-path
  LXC110 mirror metadata; arbitrary paths remain rejected.

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
| `scripts/local-ai/admission_gate.py` | `1f7969b4d734deb9b9295c5c536ff0d3d2bca44d5d284860baf76336c30caaba` |
| `scripts/local-ai/test_admission_gate.py` | `c97beaa8e0cbe0e447fc9292dc5e88c325ae818c4eab1efeb63c68e392539160` |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` |
| `scripts/local-ai/test_source_receipts.py` | `7c8abd7dc5c1a7ce0261da6b85940e1a0e4893b4fd07741a7e4f3ea60c7dd5f7` |
| `scripts/local-ai/test_trusted_observer.py` | `c0e585a8c32b361a670a585b1934cb0c02e65514ba3137652961675dd31f2405` |
| `scripts/local-ai/backup_receipt_adapter.py` | `8e88af72b36936057ad07bcdfd284fab65b673c6e9de339542408f3c348fe289` |
| `scripts/local-ai/test_backup_receipt_adapter.py` | `bc5812adb228e9336af2c82202fad8e4ea460736b68e9278d22b1ab90f5d5f73` |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `7bc97c6b7c470322a42b635cc3a0b6788d027d83f33191214682c3fad4f5caf0` |
| `scripts/local-ai/test_quiescence_receipt_adapter.py` | `4eb53b5b7105475e0f75e28210fd23f9e40624a46cc55f291dcea783d333e66e` |
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
  mirror metadata transport are therefore healthy, while archive-content and
  quiescence receipts remain separate gates.

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
