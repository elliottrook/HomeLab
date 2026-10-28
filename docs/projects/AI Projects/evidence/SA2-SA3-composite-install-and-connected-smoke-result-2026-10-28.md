# SA2/SA3 composite install and connected smoke result — 2026-10-28

## Result

**PASS.** Jason approved the exact seven-file SA2/SA3 composite at source
commit `50cf72db25dd43eca4c2e671fc512e79b807d266`. The reviewed installer
completed and retained the four replaced predecessors in the root-only
checkpoint `/var/lib/aster/sa2-sa3-pre-composite-20261027`. It added the three
proposal modules and restarted only `aster-agent.service`.

The installed path then passed one isolated connected smoke test against the
accepted `qwen3.5-9b` service. The model proposed the remaining registered
`inference-server/status` observation, the gateway journaled exactly one
pending decision, and nothing consumed or executed it. The trusted decision
retained `authority=none` and `effect=none`.

## Installed boundary

All seven installed files were regular, one-link, `root:root` mode `0644`
files with the reviewed hashes:

| File | SHA-256 |
|---|---|
| `aster_agent.py` | `02a2001caee5204b6229f7f576dcc945227471ac531b852f0ab0f60ecb032f9b` |
| `doctor_incident_adapter.py` | `0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968` |
| `sysadmin_incident_store.py` | `5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328` |
| `sysadmin_registered_producer.py` | `3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a` |
| `sysadmin_proposal_boundary.py` | `121d61c12c2f33368176ec35bcc0047f075c1d21d4640749658bf509fce813ff` |
| `sysadmin_proposal_transport.py` | `9b4d98df78c69e360e2f59544a47152c7eefc58bcad7f33e74e917158c24e4fa` |
| `sysadmin_proposal_gateway.py` | `4a4d112e8dcb805f5cdead1cedbfca9229b57eb7066ce7b7a5164138c9a5bd9c` |

The deterministic release packet SHA-256 was
`ff07c5086ee3e5c2dde04a152927fa8ef68417b0d9814faf1261b2ec56c5f322`.
The reviewed installer SHA-256 was
`feb61c286df6bf86f6ca95185c22e82702d51fa01435f7443bb25927bb21dc6f`.

## Connected smoke

The first temporary execution refused before a model call because the runner
was outside its source tree and lacked an explicit installed-module search
path. Production was untouched and the trap removed its temporary files. The
corrected execution explicitly set `PYTHONPATH=/opt/aster-agent` and returned:

- status `complete`;
- decision count `1`, consumed count `0`;
- disposition `observe`, target `inference-server`, kind `status`;
- observation count `1`;
- authority `none`, effect `none`;
- accepted model idle and healthy after the call.

The reusable smoke runner and its regression test pass together with the
proposal gateway, transport and boundary suites: **25/25**. Synthetic state
lived only in a temporary mode-`0700` directory and was removed after the run.

## Postchecks and practical effect

- Aster Agent: active, PID `26953`, restart count `0`, `/health` returned exact
  service status `ok`.
- Accepted llama.cpp/SYCL service: active, unchanged PID `61089`, restart count
  `0`.
- Local AI lease: exactly `ready`.
- Temporary runner and database: absent.
- No observation producer, repair, route promotion or automatic handover ran.

This closes installation and first connected no-effect validation of the
candidate-E proposal gateway and fixed Doctor producer. The next main-project
gate is a bounded adaptive investigation that consumes only registered
read-only observations, with independent postchecks and no repair authority.
