# SA3 Qwen operational-quality result

Status: **failed; Qwen rejected for the read-only operational pilot**

The fixed, tool-free local Qwen configuration completed one serial run against
the private 20-case operational-quality corpus. It returned valid structured
records, all required controls, and no effects on every case. It nevertheless
scored 0/20 complete passes: 11/20 outcomes matched, but none matched the exact
required diagnostic-check label. No unsafe effects were detected.

This rejects Qwen for the proposed read-only operational pilot. It may retain
only bounded, schema-enforced local uses already supported by separate evidence.
Do not rerun or tune against this corpus. Temporary files were removed from LXC
110 and its Proxmox host; no service or policy changed.
