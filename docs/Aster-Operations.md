# Aster Local Agent Operations

> Production since: 2026-08-31
> Scope: Lab VLAN 70 only; not a dependency for core HomeLab operation

## Service layout

| Component | Guest | Endpoint | Service |
|---|---|---|---|
| Aster API and browser UI | LXC 104 (`192.168.70.10`) | `http://192.168.70.10:9120` | `aster-agent.service` |
| llama.cpp Vulkan inference | LXC 110 (`192.168.70.12`) | `http://192.168.70.12:11435/v1` | `aster-llama.service` |

The browser page asks for the Aster bearer key and stores it in that browser's
local storage. The API key is stored only in `/etc/aster/aster.env` in LXC 104.
The separate inference key is stored in that file and in
`/etc/aster-llama.env` in LXC 110. Both files are root-owned, group-readable by
only the corresponding service account, and excluded from Git.

The OpenAI-compatible chat endpoint supports both normal JSON responses and
authenticated server-sent-event streaming. Streaming was added for Hermes
Desktop compatibility; the same bounded function routing and knowledge scope
apply before the upstream stream begins.

## Hermes Desktop compatibility

Hermes Desktop v0.21.0 can use Aster as an OpenAI-compatible custom endpoint:

- endpoint URL: `http://192.168.70.10:9120/v1`;
- provider ID: `aster-local`;
- model: `aster-qwen3.8-27b`;
- declared context: 65,536, which satisfies Hermes' client-side 64K minimum;
- model discovery and use-for-new-chats enabled.

The declared context is compatibility metadata only. llama.cpp still has one
8,192-token slot, so the current roughly 4,900-token Hermes startup prompt fits,
but a sufficiently long session or larger tool prompt may exceed the real slot.
Hermes completed three end-to-end test turns, including streaming, but each
required roughly 65–69 seconds because its full agent prompt was reevaluated.
Use the direct Aster UI for normal conversation speed; keep Hermes for workflows
where its desktop harness is worth the additional latency.

## Runtime configuration

- llama.cpp b10507 (`95c409c13`)
- `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`
- Vulkan, all model layers offloaded
- One 8,192-token slot
- Four CPU threads, batch 256, microbatch 128
- Flash attention; Q8 key/value cache
- Model reasoning disabled by default
- Automatic real-generation warm-up during service start

Systemd does not report `aster-llama.service` fully started until the model is
loaded and warm-up completes. This normally takes roughly 1–2 minutes. The
first real user request then avoids the otherwise roughly 28-second cold path.
The unit allows up to five minutes for startup, while the health and generation
steps inside the warm-up script are independently bounded. This prevents
systemd's 90-second default start timeout from killing a healthy model during a
slow real-generation warm-up.

## Functions and knowledge

Aster 1.0 exposes three allowlisted read-only functions:

- current time in an IANA timezone;
- Aster or inference health;
- keyword-ranked search of `/var/lib/aster/knowledge`.

These functions are selected from the current request and pre-executed before a
single model call. Knowledge retrieval returns up to four source-diverse results.
Current hardware inventory receives a strong present-state ranking preference,
but relevant operational and design records are not excluded from multi-part
answers. The Qwen model's native OpenAI function-call behavior was validated
separately, but Aster's production path is deliberately one-pass: it must not
emit or request follow-up tool calls. If the preloaded context is insufficient,
it says what is missing. There is no arbitrary shell, filesystem write, or
user-supplied network target.

The deployed knowledge directory is a curated snapshot, not a live Git mount.
Build it from the repository's explicit allowlist after material documentation
changes:

```sh
scripts/build-aster-knowledge-snapshot.sh /tmp/aster-knowledge.tar.gz
```

Copy the archive to Proxmox, replace `/var/lib/aster/knowledge` atomically in
LXC 104, and restore ownership to `aster:aster`. The builder includes
`docs/Aster-Operations.md` and does not copy Finder `._*` metadata. Never add
private backups, credentials or unreviewed external documents to the snapshot.

## Health and logs

From the Proxmox host:

```sh
pct exec 104 -- systemctl status aster-agent.service
pct exec 104 -- curl -sf http://192.168.70.10:9120/health
pct exec 104 -- journalctl -u aster-agent.service -n 100 --no-pager

pct exec 110 -- systemctl status aster-llama.service
pct exec 110 -- journalctl -u aster-llama.service -n 100 --no-pager
```

`lab doctor` checks both systemd services and the Aster health endpoint.

The B60 must be bound to the host `xe` driver before inference starts. Stale
DRM nodes can remain visible inside LXC 110 even when the host device is
unbound, in which case Mesa silently exposes `llvmpipe` and inference becomes
extremely slow. Verify both layers from Proxmox:

```sh
readlink /sys/bus/pci/devices/0000:04:00.0/driver
pct exec 110 -- vulkaninfo --summary
```

The host path must end in `/xe`, and `vulkaninfo` must list Intel BMG G21 as a
discrete GPU. If VM 105 is confirmed stopped and `04:00.0` is unbound, stop
`aster-llama.service`, bind `0000:04:00.0` through
`/sys/bus/pci/drivers/xe/bind`, then start the service. Do not rebind the device
while VM 105 is running.

## Restart and rollback

Restart the lightweight harness without reloading the model:

```sh
pct exec 104 -- systemctl restart aster-agent.service
```

Restarting inference reloads and warms the 27B model:

```sh
pct exec 110 -- systemctl restart aster-llama.service
```

To roll LXC 110 back to Ollama without removing Aster:

```sh
pct exec 110 -- systemctl disable --now aster-llama.service
pct exec 110 -- systemctl enable --now ollama.service
```

Hermes remains installed in LXC 104. Re-enabling it is a separate rollback
decision because its default provider expects Ollama on port 11434 and its full
prompt/tool configuration is substantially slower than Aster.

## Acceptance baseline

- First conversation after completed service warm-up: 4.75 seconds.
- Repeated simple conversation: approximately 3.6 seconds.
- Read-only time function after one-pass routing: approximately 10 seconds.
- Grounded current-hardware retrieval: approximately 24 seconds, with the
  answer correctly naming `docs/03-Hardware-Inventory.md`.
- Six earlier direct stability requests: HTTP 200 in 3.28–4.26 seconds.
- The 2026-09-01 multi-source acceptance prompt correctly identified both LXC
  roles, the exact Qwen3.8 model, llama.cpp/Vulkan, the VM 105 rollback path,
  the SYCL/BAR constraint, the first unfinished second-brain task and the stale
  Ollama wording in `docs/projects/Local-AI.md`.
- A focused checklist query returned the first three unchecked tasks in order
  from `docs/AI-Hermes-Second-Brain.md`, with no emitted tool-call markup.
- The focused checklist run processed 951 prompt tokens at 77.8 tokens/second
  and decoded at 4.9 tokens/second after B60-to-`xe` binding was restored.

These figures are single-user measurements. Inference intentionally has one
slot, so simultaneous requests queue instead of competing for the B60's memory.
