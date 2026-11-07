# M3 K2 sealed runtime — inactive installer source review 2026-11-06

Status: source-only and non-authorizing. The exact release archive was installed
and rolled back only inside a new disposable local test directory. It was not
transferred to the MacBook or installed in either fixed runtime root. No
booking, lease, listener, tunnel, model request, service stop or restart was
created.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/local-ai/m3_k2_sealed_runtime_inactive_install.py` | `245aa11d94653e87c1710a84addeca67f8f18d81ce30bd684e1d31d9bed89029` |
| `scripts/local-ai/test_m3_k2_sealed_runtime_inactive_install.py` | `4db3c16da2e00562c810a98137c0b0480ab1719781ee594553ae0cbd735e3eda` |

The installer imports the exact bundle contract from platform commit
`c1417aef`. It is inert unless exactly one of `--apply` or `--rollback` is
provided.

## Installation boundary

The same host-local primitive is intended to run separately on the Mac mini
and MacBook under their existing identities. Before writing, it validates the
outer bundle digest, exact archive members and metadata, non-authorizing
manifest, preregistration digest and all thirteen source pins. It then requires
the target, checkpoint and staging path to be absent; creates a private
mode-0700 checkpoint recording that the target was absent; creates every file
exclusively at mode 0600 in a private staging directory; atomically renames the
complete directory; and rereads every installed byte.

It does not start a process or service. A changed existing target, checkpoint,
archive, member, source or installed byte fails closed.

## Rollback boundary

Rollback is permitted only when the retained marker exactly matches the target
and bundle and every installed file still matches the archive. It removes only
the exact fourteen installed files and their now-empty target directory, then
requires the target to be absent. Any uncertain or changed target is retained
untouched, along with the checkpoint.

## Verification

- focused tests: 4/4 passed;
- syntax compilation: passed;
- exact 25,097-byte release archive: installed inactive and independently
  reread as 14 files inside a disposable private directory;
- exact disposable rollback: passed, target absent and checkpoint retained;
- fixed runtime roots changed: no;
- next gate: a restored passing development transaction, then a separately
  reviewed two-host inactive-install packet using this exact source and bundle.
