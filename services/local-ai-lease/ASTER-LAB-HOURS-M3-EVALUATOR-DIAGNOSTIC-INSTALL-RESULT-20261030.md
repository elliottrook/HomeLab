# M3 evaluator diagnostic installation result — 2026-10-30

Status: **INSTALLED INACTIVE; TARGET PROOF PASSED**

Platform source commit `d0ec71e1` was installed from deterministic archive
SHA-256 `97f5fc27e2dfceca155d87a5f6fa1dd8cfd46063cbe20e3474ba5381a4c3dc37`.
The former host files are retained root-only at
`/var/lib/local-ai-lab/checkpoints/m3-evaluator-d0ec71e1`.

Only six host pilot files and the two corresponding LXC110 guest files were
replaced. No service, timer, model, mount or workload was started. The installed
host manifest validates all 32 pins with zero mismatches. Host target tests pass
14/14 and the guest failure-projection/HTTP classification tests pass 4/4.
Both guest files are root-owned, one-link regular mode-`0644` files at their
pinned hashes.

Postcheck found the lease exactly ready, LXC104/110/116 running, Aster Agent,
accepted 9B llama.cpp/SYCL and Speech active, `pvescheduler` and `pvestatd`
active, no candidate mount, and no M3/35B candidate process. Production was not
restarted or disrupted.

This result authorizes no workload invocation or routing. A later run needs a
fresh authoritative Lab Hours booking and all live lease/shared-lock gates.
