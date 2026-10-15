# A1 disabled helper upgrade: installation receipt

Status: **installed and verified disabled; live drill and benchmark remain blocked**.

Jason approved only the disabled helper packet from platform commit
`7b36ce64b3e4a20a635bf57e32b8af51c83459af`, card SHA-256
`21e786df191683186d6df7e55513c735d26713f379a545ce6b92ace264ecb87d`.
Before the change, the host lease was `ready`, the first A1 watchdog was
disabled/inactive, the four application lease/state paths were absent, and the
full-stop controller and units matched their previously recorded hashes.
The 24 packet sources matched their card hashes. Existing destination bytes
matched the first disabled-install receipt; the eight LXC110 helper
destinations and new Proxmox helpers/heartbeat units were absent.

The five changed Proxmox Python files and all newly named packet files were
installed at their exact destinations. Existing Proxmox bytes were copied to
`/root/aster-a1-pre-helper-upgrade-7b36ce64/` before replacement, with a
mode-0600 preflight manifest. The eight LXC110 helper files were installed
root-owned. All 24 destination hashes and modes matched the packet. Four
candidate systemd units passed `systemd-analyze verify` and are disabled and
inactive. The service `MainPID` values are `0`; inactive timers return an
empty `MainPID` property and have no next elapse. This distinction caused the
first verifier to stop *after file installation*; an independent corrected
postcheck completed successfully. The entrypoint's `plan` phase returned
`plan-only`; Proxmox and LXC110 target-Linux imports passed with bytecode
writes disabled.

The whole-host lease remained `ready`; the three full-stop files were
byte-identical. LXC104 `aster-agent` and AI-PAM broker, LXC110 `aster-llama`,
and LXC116 `aster-speech` remained active. The LXC110 key-file metadata stayed
`999:991:600`; no temporary key, key checkpoint, ingress checkpoint or
ingress rule exists. No listener appeared on port 19104. The application
lease, pre-lease marker and sidecar receipt remain absent. No model call,
service start, lease, key or firewall change was part of this operation.

The root-owned mode-0600 host receipt is
`/root/aster-a1-disabled-helper-upgrade-7b36ce64.receipt.json`, SHA-256
`6e5b9ebbea5df0dbac409c3ed766cd98bba6f94baf53d071ef156634c2687b82`.
The temporary transfer directory was removed after verification. The
pre-install state is retained in the protected rollback directory and receipt.
The effect-free `plan` wrapper created three Python bytecode cache files; their
timestamps matched this check, and those exact cache files and their empty
directory were removed. The installed source hashes were unaffected.

This is install evidence only. A live recovery drill still requires a
separate approved effect card, a current source-bound backup receipt, a
restricted admission identity, and measured exact recovery. The A1 sidecar
and 20-request full Aster-path benchmark remain unstarted.
