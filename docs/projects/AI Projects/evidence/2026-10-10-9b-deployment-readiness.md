# Qwen3.5-9B deployment readiness

Date: 2026-10-10

Status: **bounded promotion design ready; persistent change not authorized**

## Live constraint

LXC 110 has a 64 GiB root disk with 21,066,375,168 bytes available. The
existing experiment rule requires at least 20 GiB of disk headroom, so simply
adding the exact 5,627,044,256-byte tested model would fail closed.

The active 27B model is stored as two symlinked Ollama blobs and remains the
production rollback source. A separate inactive Ollama `qwen3.5:9b` manifest
references a 6,594,462,816-byte blob
`sha256-dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c`.
`ollama.service` is inactive and disabled; reverse dependency and bounded
reference searches found no consumer of that manifest or blob.

Replacing only this unused, redownloadable Ollama artifact with the exact tested
Q4_K_M file would increase free space by 967,418,560 bytes before adding the
approximately 31 MiB b11429 runtime. It avoids deleting either accepted 27B
shard and keeps the root disk above the existing safety floor.

## Proposed bounded change

This is a proposal, not authorization:

1. Reconfirm backup/mirror, production hashes, health, `xe`, BMG G21, kernel
   state, disk/RAM/VRAM headroom and idle News workers.
2. Download the pinned 9B model and official b11429 Vulkan archive to tmpfs;
   require SHA-256
   `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`
   and `632c4e98feba2b94407a2130e3133e0c3aefb0ea1ab41337e926d8bfafdd0b74`.
3. Remove only the inactive Ollama 9B manifest and its uniquely referenced
   `dec52a...d37c` blob. Do not alter either 27B model shard or manifest.
4. Install b11429 and the exact tested 9B model under versioned paths, with
   root ownership and no writable access for the service identity.
5. Preserve the exact accepted 27B service unit as the immediate rollback,
   then atomically change only model/runtime paths while retaining the current
   bind, credential file, Vulkan, context, batching, Q4 K/V, reasoning-off and
   hardening settings.
6. Quiesce once, start 9B, and require hashes, service/endpoint/Aster health,
   authenticated synthetic generation, the deterministic household regression,
   post-policy analysis regression, `xe`, BMG G21, headroom and clean kernel
   logs.
7. On any failure, restore the exact 27B unit, quiesce, start once, and require
   the complete accepted-production validation. Do not retry a GPU/device
   failure automatically.

## Recovery and observation

The accepted 27B runtime, both model shards, promoted Q4 unit hash
`e2019cac...184` and retained Q8 unit hash `7e3e2d9a...013` remain unchanged.
The deleted legacy Ollama 9B blob is not a production rollback dependency and
can be reacquired from its manifest source if ever needed. Retain the exact 9B
installer inputs and new unit rollback copy until a finite observation closes.

Promotion must not expand the model's authority. Household execution stays
deterministic and fail-closed; consent/privacy and escalation routing stay in
policy; deep sysadmin analysis continues to use sanitized GPT-backend packets.
TTS remains a separate service and is unaffected.

## Authorization gate

Execution requires explicit approval because it deletes a persistent legacy
model artifact and changes the persistent production inference runtime/model.
No deletion, download, installation, unit change or restart was performed by
this readiness review.
