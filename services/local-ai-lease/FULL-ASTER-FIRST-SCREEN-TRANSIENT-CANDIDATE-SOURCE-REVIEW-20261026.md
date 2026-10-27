# Full-Aster first-screen transient candidate source review

Status: **SOURCE PASS / NOT INSTALLED / EFFECT NOT AUTHORIZED**

`scripts/local-ai/full_aster_first_screen_candidate.py` produces only fixed
command vectors. It has no CLI and performs no subprocess call. Its candidate
command is pinned to LXC110, the accepted b11429 SYCL binary and libraries, the
root-mounted Qwen3.6-35B-A3B Q4_K_M path, the existing `ollama` identity and
API-key file, one 8K slot, reasoning on, no draft model and `Restart=no`.

The companion stop/reset and accepted-baseline stop/start vectors are also
fixed to LXC110. Three focused tests pass. The module does not install a unit,
mount a file, restart LXC110, stop production, call a model or grant live
authority. It is one component of the later complete-Aster root transaction;
the mount-aware independent guardian and composition root remain required.
