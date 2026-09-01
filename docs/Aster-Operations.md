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

## Functions and knowledge

Aster 1.0 exposes three allowlisted read-only functions:

- current time in an IANA timezone;
- Aster or inference health;
- keyword-ranked search of `/var/lib/aster/knowledge`.

These functions are selected from the current request and pre-executed before a
single model call. The Qwen model's native OpenAI function-call behavior was
validated separately, but obvious read-only functions use deterministic routing
to avoid an unnecessary second inference pass. There is no arbitrary shell,
filesystem write, or user-supplied network target.

The deployed knowledge directory is a curated snapshot, not a live Git mount.
Refresh it after material documentation changes by creating a new archive from
the selected repository files, copying it to Proxmox, extracting it into
`/var/lib/aster/knowledge`, and restoring ownership to `aster:aster`. Never add
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

These figures are single-user measurements. Inference intentionally has one
slot, so simultaneous requests queue instead of competing for the B60's memory.
