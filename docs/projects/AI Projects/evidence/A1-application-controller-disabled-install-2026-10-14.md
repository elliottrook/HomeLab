# A1 application-only controller: disabled installation

Status: **installed and verified disabled; no lease or benchmark authorized**.

Jason approved only the frozen disabled-install card at platform commit
`2c925c3a9514d8382582ca46bc26579645a6c35c` (card SHA-256
`8e9827e31e5d1542fdc1ec64487de403475f280397090f72295f8ef8d8fdbd71`).
The preflight showed every candidate destination absent, candidate units
not-found/inactive, the host lease `ready`, and unchanged full-stop controller
and unit hashes. The source and staged copies of all 12 artifacts matched the
card before installation.

On Proxmox, the nine Python files, wrapper, service and timer were installed
root-owned at their card paths. Post-install hashes matched all 12 pinned
digests. Python and unit files are mode 0644; the wrapper is 0755. The
application state directory is root-owned mode 0700 and empty. Systemd
verification and daemon reload succeeded. Both new watchdog units are
**disabled and inactive**; the service has MainPID 0. The original full-stop
controller and unit hashes/states are unchanged, and the whole-host lease is
still `ready`.

Independent read-only postchecks found LXC104 Aster active, A1 sidecar inactive
with no port 19104 listener, LXC110 llama.cpp active, and LXC116 Speech active.
No application lease, key, firewall rule, backup schedule, service start or
model call was made. The temporary transfer staging was removed.

The root-owned mode-0600 host receipt is
`/root/aster-a1-disabled-install-2c925c3a.receipt.json` (SHA-256
`efe48b72342c25a3bbf8e6d56271721f04240024a8827d5076c6c629077ae59a`).
The preflight was captured in read-only SSH output before installation but was
not persisted on the host until the post-install receipt; the receipt states
this provenance limitation explicitly. Do not present it as an independently
timestamped pre-install host file.

The separate application recovery drill, trusted admission callback,
source-bound backup chain, and 20-request A1 benchmark remain held behind
their own reviewed gates. This receipt proves installation state only.
