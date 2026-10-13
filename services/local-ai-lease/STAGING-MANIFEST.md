# Local AI lease recovery — staging review manifest

Status: offline review candidate; not installed, enabled, or authorized for a
live effect.

## Candidate identity

- Source commit: `fbdbb303`; this manifest is not a deployment authorization.
- Accepted live runtime: LXC 110, llama.cpp `b11429`, SYCL/Level Zero,
  Qwen3.5 9B Q4_K_M; live unit hash
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`; live
  binary hash
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.
- Fixed trusted sources: Proxmox `pvesh`, LXC 104/110/116 and 114 probes,
  TrueNAS `192.168.20.40` through batch-mode SSH, and the owner heartbeat.
- Fixed schedule identity: Proxmox `00:30`; TrueNAS guest `01:00`, LXC 110
  `02:00`, Mac `03:00`; News `06:15` and `17:15`.
- The host-local recovery executor is a separate entry point; without its
  explicit effect gate it only emits a content-free decision. The disabled
  systemd unit does not invoke it yet.

## Exact local candidate hashes

These SHA-256 values cover the source and disabled unit reviewed for staging:

| File | SHA-256 |
|---|---|
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` |
| `scripts/local-ai/lease_contract.py` | `8a8997bdf453a499ae60dc2f11a65da9e28e318044a194122a7635b545adf113` |
| `scripts/local-ai/lease_watchdog.py` | `044961c44a459ff422c0206f9338e3dc2943b469ae93eb544e14dfab944d0035` |
| `scripts/local-ai/lease_controller_candidate.py` | `a9b6d567ad450e680138931e648df22f76f0037fdede74719a8a315ea6a340df` |
| `scripts/local-ai/trusted_observer.py` | `5b129a79601dea0e0c338815d0ce81559e7f463d541fe342129e579dd08edaf1` |
| `scripts/local-ai/lease_watchdog_cli.py` | `e79521ae4cfacb61e1232df3b62cdfbb2d5181c0697770b8c1ff6c88c575990d` |
| `scripts/local-ai/lease_effect_runner.py` | `81eac0e15e86ea48ce267d1a03da74cfcbe408ad9c57c9eca832a9c8f8c2c662` |
| `scripts/local-ai/test_lease_effect_runner.py` | `f59eaa9048ff0cd1c93dc49462151350eee54c627d52466fdbbdf874562060b8` |
| `scripts/local-ai/lease_recovery_executor.py` | `db6efb158bedfbe92f02aa4573e6979d6016f19efef688f697bbcdfdb7feea85` |
| `scripts/local-ai/test_lease_recovery_executor.py` | `9e00a8724bddff2f41d6fee7fa97286ac0280556f1def69eb5c4010fff32076d` |
| `services/local-ai-lease/local-ai-lease-watchdog.service` | `abbe6fcd98b37d6ccb6065fc3a64492c56f37139812b4a60d37d54d55acaf5f5` |
| `services/local-ai-lease/local-ai-lease-watchdog.timer` | `4ef3217f40bfeca17cc0790c29a04ffa95d9b9a60a49aa97b26e4e8c58c84875` |

The values above describe the reviewed local payload and are not a deployment
authorization. The manifest itself is excluded from the hash table because
editing the table would necessarily change its own digest.

## Required staging facts before live review

- The accepted model artifact identity must include the exact SHA-256 of the
  deployed GGUF at `/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf`.
  The repository's Ollama blob digest is provenance only, not a substitute for
  the file digest checked by the observer.
- The fixed TrueNAS probe must be verified from the Proxmox owner context using
  batch-mode SSH to `root@192.168.20.40` and `midclt call rsynctask.query`.
  The historical `truenas` alias failure is not an acceptable restoration
  probe; transport failure remains schedule-unhealthy and fail-closed.

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
- Rollback is to disable the candidate timer, retain the lease lock, restore
  the saved controller/unit files and use the existing manual release path
  only after the production health and schedule checklist passes.

## One bounded live drill — future gate

The only proposed live drill is one attended, light service-drain window after
the backup chain completes and before `04:15`. It may stop and restore only the
three allowlisted Local AI service units; it may not reboot the host, enable a
timer, change schedules, alter credentials, modify firewall/DNS, or touch
unrelated guests. The operator must capture pre/post checkpoints and abort on
any failed probe. This drill requires separate explicit live authorization and
must not be inferred from this staging manifest.
